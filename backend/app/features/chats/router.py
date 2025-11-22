"""API router for chats and messages."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.crud import (
    get_all_chats,
    get_chat_by_id,
    get_messages_by_chat,
    mark_chat_as_read,
    ignore_chat,
    unignore_chat,
    get_message_count_by_chat,
    get_attendee_by_provider_id,
    upsert_attendee,
    get_pending_messages,
)
from app.services.message_sync import sync_chat_messages, sync_all_chat_messages
from app.integration.unipile.client import get_unipile_client
from app.features.chats.schemas import (
    ChatResponse,
    ChatListResponse,
    MessageResponse,
    MessageListResponse,
    SyncResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=ChatListResponse)
async def list_chats(
    is_read: Optional[bool] = Query(None, description="Filter by read/unread status"),
    is_ignored: Optional[bool] = Query(None, description="Filter by ignored status (default: exclude ignored)"),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    limit: int = Query(100, ge=1, le=250, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all chats from the database.
    
    Query parameters:
    - is_read: Filter by read (true) or unread (false) status. Omit for all chats.
    - is_ignored: Filter by ignored status. By default, ignored chats are excluded. Set to true to get only ignored chats.
    - account_id: Filter by specific account ID
    - limit: Maximum number of results (1-250)
    - offset: Number of results to skip (for pagination)
    
    Returns:
    - List of chats with metadata
    """
    try:
        chats = await get_all_chats(
            db,
            account_id=account_id,
            is_read=is_read,
            is_ignored=is_ignored,
            limit=limit,
            offset=offset,
        )
        
        # Convert to response models
        chat_responses = [ChatResponse.model_validate(chat) for chat in chats]
        
        return ChatListResponse(
            items=chat_responses,
            total=len(chat_responses),  # Note: This is count in current page, not total
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error fetching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch chats: {str(e)}")


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific chat by ID.
    
    Path parameters:
    - chat_id: Chat ID
    
    Returns:
    - Chat details
    """
    try:
        chat = await get_chat_by_id(db, chat_id)
        
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        return ChatResponse.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat: {str(e)}")


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def list_chat_messages(
    chat_id: str,
    limit: int = Query(100, ge=1, le=250, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    order_desc: bool = Query(True, description="Order by timestamp descending (newest first)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get messages for a specific chat.
    
    Path parameters:
    - chat_id: Chat ID
    
    Query parameters:
    - limit: Maximum number of results (1-250)
    - offset: Number of results to skip (for pagination)
    - order_desc: Order by timestamp descending (true = newest first, false = oldest first)
    
    Returns:
    - List of messages for the chat
    """
    try:
        # Check if chat exists
        chat = await get_chat_by_id(db, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        # Get synced messages
        synced_messages = await get_messages_by_chat(
            db,
            chat_id=chat_id,
            limit=limit,
            offset=offset,
            order_desc=order_desc,
        )
        
        # Get pending messages for this chat
        pending_messages = await get_pending_messages(
            db,
            chat_id=chat_id,
            status="pending",
        )
        
        # Merge pending and synced messages
        # Filter out pending messages that already exist in synced
        synced_ids = {msg.id for msg in synced_messages}
        unique_pending = [p for p in pending_messages if p.message_id not in synced_ids]
        
        # Convert pending messages to MessageResponse format
        pending_responses = []
        for pending_msg in unique_pending:
            pending_responses.append(MessageResponse(
                id=pending_msg.message_id,
                account_id="",  # Not available in pending
                chat_id=pending_msg.chat_id,
                provider_id=pending_msg.message_id,
                sender_id="self",
                sender_attendee_id="self",
                text=pending_msg.text,
                timestamp=pending_msg.timestamp,
                is_sender=1,
                attachments=[],
                reactions=[],
                seen=0,
                hidden=0,
                deleted=0,
                edited=0,
                is_event=0,
                delivered=1,
                created_at=pending_msg.created_at,
            ))
        
        # Merge synced and pending messages
        synced_responses = [MessageResponse.model_validate(msg) for msg in synced_messages]
        all_messages = synced_responses + pending_responses
        
        # Sort by timestamp
        all_messages.sort(key=lambda m: m.timestamp, reverse=order_desc)
        
        # Get total count (synced + unique pending)
        total_count = await get_message_count_by_chat(db, chat_id)
        total_with_pending = total_count + len(unique_pending)
        
        return MessageListResponse(
            items=all_messages,
            total=total_with_pending,
            limit=limit,
            offset=offset,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages for chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


@router.post("/{chat_id}/mark-read", response_model=ChatResponse)
async def mark_chat_read(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a chat as read.
    
    Path parameters:
    - chat_id: Chat ID
    
    Returns:
    - Updated chat details
    """
    try:
        chat = await mark_chat_as_read(db, chat_id)
        
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        return ChatResponse.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking chat {chat_id} as read: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark chat as read: {str(e)}")


@router.post("/{chat_id}/ignore", response_model=ChatResponse)
async def ignore_chat_endpoint(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Ignore a chat.
    
    Path parameters:
    - chat_id: Chat ID
    
    Returns:
    - Updated chat details
    """
    try:
        chat = await ignore_chat(db, chat_id)
        
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        return ChatResponse.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ignoring chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ignore chat: {str(e)}")


@router.post("/{chat_id}/unignore", response_model=ChatResponse)
async def unignore_chat_endpoint(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Unignore a chat.
    
    Path parameters:
    - chat_id: Chat ID
    
    Returns:
    - Updated chat details
    """
    try:
        chat = await unignore_chat(db, chat_id)
        
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        return ChatResponse.model_validate(chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unignoring chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unignore chat: {str(e)}")


@router.post("/{chat_id}/sync", response_model=SyncResponse)
async def sync_chat(
    chat_id: str,
    full_sync: bool = Query(False, description="Perform full sync (all messages) instead of incremental"),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger message sync for a specific chat.
    
    Path parameters:
    - chat_id: Chat ID
    
    Query parameters:
    - full_sync: If true, syncs all messages. If false (default), syncs only new messages.
    
    Returns:
    - Sync statistics
    """
    try:
        # Check if chat exists
        chat = await get_chat_by_id(db, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        # Perform sync
        stats = await sync_chat_messages(db, chat_id, full_sync=full_sync)
        
        return SyncResponse(
            success=True,
            message=f"Successfully synced chat {chat_id}",
            stats=stats,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync chat: {str(e)}")


@router.post("/sync", response_model=SyncResponse)
async def sync_all_chats(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    full_sync: bool = Query(False, description="Perform full sync (all messages) instead of incremental"),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger sync for all chats and their messages.
    
    Query parameters:
    - account_id: Optional account ID to filter chats
    - full_sync: If true, syncs all messages. If false (default), syncs only new messages.
    
    Returns:
    - Sync statistics
    
    Warning: This operation can take a long time if you have many chats with many messages.
    """
    try:
        stats = await sync_all_chat_messages(db, account_id=account_id, full_sync=full_sync)
        
        return SyncResponse(
            success=True,
            message="Successfully synced all chats",
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Error syncing all chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync chats: {str(e)}")


@router.get("/{chat_id}/attendee/{provider_id}")
async def get_chat_attendee(
    chat_id: str,
    provider_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get attendee information including profile picture.
    
    First checks the database cache, if not found, fetches from Unipile and caches it.
    
    Path parameters:
    - chat_id: Chat ID
    - provider_id: Provider ID of the attendee (e.g., Instagram user ID)
    
    Returns:
    - Attendee information including picture_url
    """
    try:
        # Try to get from cache first
        attendee = await get_attendee_by_provider_id(db, provider_id)
        
        if attendee:
            # Return cached data
            return {
                "id": attendee.id,
                "provider_id": attendee.provider_id,
                "name": attendee.name,
                "picture_url": attendee.picture_url,
                "profile_url": attendee.profile_url,
                "is_self": attendee.is_self,
            }
        
        # Not in cache, fetch from Unipile
        client = get_unipile_client()
        response = await client.list_chat_attendees(chat_id)
        
        # Find the specific attendee
        for attendee_data in response.items:
            if attendee_data.provider_id == provider_id:
                # Cache it
                cached_attendee = await upsert_attendee(db, attendee_data)
                
                return {
                    "id": cached_attendee.id,
                    "provider_id": cached_attendee.provider_id,
                    "name": cached_attendee.name,
                    "picture_url": cached_attendee.picture_url,
                    "profile_url": cached_attendee.profile_url,
                    "is_self": cached_attendee.is_self,
                }
        
        raise HTTPException(status_code=404, detail=f"Attendee {provider_id} not found in chat {chat_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attendee {provider_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch attendee: {str(e)}")

