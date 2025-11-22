"""Autopilot service for automatically replying to chats."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.crud import (
    create_pending_message,
    get_chat_by_id,
    get_latest_message,
    get_messages_by_chat,
)
from app.db.models import MessageModel
from app.integration.unipile import send_message
from app.services.ai_assistant import generate_sales_response, AISuggestionError
from app.services.realtime import broadcast_new_message

logger = logging.getLogger(__name__)


async def maybe_send_autopilot_reply(
    db: AsyncSession,
    incoming_message: Optional[MessageModel],
) -> None:
    """
    Automatically reply to a chat if Autopilot is enabled.
    """
    if not incoming_message:
        return
    
    if incoming_message.is_sender == 1:
        return  # Only respond to inbound messages
    
    chat = await get_chat_by_id(db, incoming_message.chat_id)
    if not chat:
        return
    
    if chat.is_ignored or chat.assist_mode != "autopilot":
        return
    
    # Ensure we're reacting to the most recent inbound message (avoid double-texting)
    latest_message = await get_latest_message(db, chat.id)
    if not latest_message or latest_message.id != incoming_message.id:
        return
    
    settings = get_settings()
    autopilot_prompt = (settings.autopilot_prompt or "").strip()
    if not autopilot_prompt:
        logger.warning("Autopilot prompt is empty; skipping auto reply for chat %s", chat.id)
        return
    
    history_limit = settings.openai_history_limit
    messages = await get_messages_by_chat(
        db,
        chat_id=chat.id,
        limit=history_limit,
        order_desc=False,
    )
    
    try:
        suggestion = await generate_sales_response(
            chat,
            messages,
            autopilot_prompt,
            history_limit=history_limit,
        )
    except AISuggestionError as exc:
        logger.warning("Failed to generate autopilot reply for chat %s: %s", chat.id, exc)
        return
    except Exception as exc:
        logger.exception("Unexpected error generating autopilot reply for chat %s", chat.id)
        return
    
    try:
        send_response = await send_message(
            chat_id=chat.id,
            text=suggestion,
            account_id=chat.account_id,
        )
    except Exception as exc:
        logger.error("Failed to send autopilot reply for chat %s: %s", chat.id, exc)
        return
    
    message_id = send_response.message_id or f"autopilot-{uuid4()}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        await create_pending_message(
            db=db,
            message_id=message_id,
            chat_id=chat.id,
            text=suggestion,
            timestamp=timestamp,
        )
    except Exception as exc:
        logger.warning(
            "Autopilot reply sent but failed to enqueue pending message %s: %s",
            message_id,
            exc,
        )
    
    # Broadcast a realtime event so the UI reflects the AI response immediately.
    fake_message = MessageModel(
        id=message_id,
        chat_id=chat.id,
        account_id=chat.account_id,
        chat_provider_id=chat.provider_id,
        provider_id=message_id,
        sender_id="self",
        sender_attendee_id="self",
        text=suggestion,
        timestamp=timestamp,
        is_sender=1,
        attachments=[],
        reactions=[],
        seen=0,
        seen_by={},
        hidden=0,
        deleted=0,
        edited=0,
        is_event=0,
        delivered=1,
        behavior=None,
        original=suggestion,
    )
    fake_message.created_at = datetime.utcnow()
    
    await broadcast_new_message(fake_message)

