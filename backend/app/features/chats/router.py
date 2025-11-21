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
    get_message_count_by_chat,
    get_attendee_by_provider_id,
    upsert_attendee,
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
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    limit: int = Query(100, ge=1, le=250, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all chats from the database.
    
    Query parameters:
    - is_read: Filter by read (true) or unread (false) status. Omit for all chats.
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
        
        # Get messages
        messages = await get_messages_by_chat(
            db,
            chat_id=chat_id,
            limit=limit,
            offset=offset,
            order_desc=order_desc,
        )
        
        # Get total count
        total_count = await get_message_count_by_chat(db, chat_id)
        
        # Convert to response models
        message_responses = [MessageResponse.model_validate(msg) for msg in messages]
        
        return MessageListResponse(
            items=message_responses,
            total=total_count,
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

