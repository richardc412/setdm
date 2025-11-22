"""Webhook endpoint for receiving Unipile events."""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.integration.unipile.schemas import WebhookMessagePayload, Message
from app.db.crud import (
    get_or_create_chat,
    create_message,
    update_chat_timestamp,
    mark_chat_as_unread,
    get_chat_by_id,
)
from app.services.realtime import broadcast_new_message
from app.services.autopilot import maybe_send_autopilot_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/unipile/messages")
async def receive_message_webhook(request: Request):
    """
    Webhook endpoint for receiving message events from Unipile.
    
    This endpoint is called by Unipile when a message_received event occurs.
    It processes the incoming message and saves it to the database.
    
    Returns:
        200 OK response to acknowledge receipt
    """
    try:
        # Parse the webhook payload
        body = await request.json()
        logger.info(f"Received webhook payload: {body}")
        
        # Validate payload against schema
        try:
            payload = WebhookMessagePayload(**body)
        except Exception as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            # Return 200 anyway to prevent Unipile from retrying
            return {"status": "error", "message": "Invalid payload format"}
        
        # Process the message
        async with AsyncSessionLocal() as db:
            await process_webhook_message(db, payload)
        
        logger.info(f"Successfully processed webhook message: {payload.message_id}")
        return {"status": "success", "message_id": payload.message_id}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        # Return 200 to prevent Unipile from retrying on our internal errors
        return {"status": "error", "message": "Internal processing error"}


async def process_webhook_message(db: AsyncSession, payload: WebhookMessagePayload):
    """
    Process a webhook message payload and save to database.
    
    Args:
        db: Database session
        payload: Validated webhook payload
    """
    # First, ensure the chat exists
    # We need to fetch or create a basic chat record
    chat = await get_chat_by_id(db, payload.chat_id)
    
    if not chat:
        # Create a minimal chat object from webhook data
        from app.integration.unipile.schemas import Chat
        
        chat_data = Chat(
            object="Chat",
            id=payload.chat_id,
            account_id=payload.account_id,
            account_type=payload.account_type,
            provider_id=payload.provider_chat_id,
            name=payload.sender.name if payload.sender else None,
            timestamp=payload.timestamp,
            unread_count=1,
            unread=True,
        )
        
        await get_or_create_chat(db, chat_data)
        logger.info(f"Created new chat from webhook: {payload.chat_id}")
    
    # Convert webhook payload to Message schema
    # Note: Webhook provides simplified data, so we'll use defaults for missing fields
    # Use provider_id as sender_id to ensure consistency with chat_attendees table
    message_data = Message(
        object="Message",
        id=payload.message_id,
        account_id=payload.account_id,
        chat_id=payload.chat_id,
        chat_provider_id=payload.provider_chat_id,
        provider_id=payload.provider_message_id,
        sender_id=payload.sender.provider_id if payload.sender and payload.sender.provider_id else (payload.sender.id if payload.sender else ""),
        sender_attendee_id=payload.sender.id if payload.sender else "",
        text=payload.message,
        timestamp=payload.timestamp,
        is_sender=0,  # Webhooks are triggered for received messages, so is_sender=0
        attachments=payload.attachments or [],
        reactions=[],
        seen=0,
        seen_by={},
        hidden=0,
        deleted=0,
        edited=0,
        is_event=payload.is_event or 0,
        delivered=1,
        behavior=None,
        original=payload.message or "",
        quoted=payload.quoted,
        message_type=payload.message_type,
    )
    
    # Create the message (will skip if duplicate)
    created_message = await create_message(db, message_data)
    
    if created_message:
        logger.info(f"Created new message from webhook: {payload.message_id}")
        
        # Update chat timestamp
        await update_chat_timestamp(db, payload.chat_id, payload.timestamp)
        
        # Mark chat as unread (since this is a received message)
        await mark_chat_as_unread(db, payload.chat_id)
        
        logger.info(f"Updated chat {payload.chat_id} with new message")
        
        # Broadcast to realtime subscribers
        await broadcast_new_message(created_message)
        
        # Trigger Autopilot if enabled for this chat
        await maybe_send_autopilot_reply(db, created_message)
    else:
        logger.info(f"Message {payload.message_id} already exists, skipping")

