"""Message synchronization service for syncing with Unipile API."""
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.integration.unipile.client import get_unipile_client
from app.db.crud import (
    get_or_create_chat,
    get_latest_message_timestamp,
    create_message,
    update_chat_timestamp,
    mark_chat_as_unread,
    get_message_count_by_chat,
)

logger = logging.getLogger(__name__)


async def sync_all_chats(db: AsyncSession, account_id: Optional[str] = None) -> dict:
    """
    Sync all chats from Unipile API to local database.
    Fetches chats and creates/updates them in the database.
    
    This function handles pagination automatically and syncs all available chats.
    
    Args:
        db: Database session
        account_id: Optional account ID to filter chats
        
    Returns:
        Dictionary with sync statistics:
        {
            "chats_synced": int,
            "chats_created": int,
            "chats_updated": int,
            "chats_with_new_messages": list[str],  # Chat IDs that need message sync
        }
    """
    client = get_unipile_client()
    stats = {
        "chats_synced": 0,
        "chats_created": 0,
        "chats_updated": 0,
        "chats_with_new_messages": [],
    }
    
    cursor = None
    
    try:
        while True:
            # Fetch chats from Unipile
            response = await client.list_all_chats(
                cursor=cursor,
                account_id=account_id,
                limit=100,  # Max items per request
            )
            
            logger.info(f"Fetched {len(response.items)} chats from Unipile")
            
            # Process each chat
            for chat_data in response.items:
                # Check if chat exists
                from app.db.crud import get_chat_by_id
                existing_chat = await get_chat_by_id(db, chat_data.id)
                
                # Check if chat needs message sync
                needs_sync = False
                
                if not existing_chat:
                    # New chat - always sync
                    needs_sync = True
                    stats["chats_created"] += 1
                else:
                    # Existing chat - check if we need to sync
                    # Sync if: timestamp changed OR chat has no messages yet
                    if chat_data.timestamp and chat_data.timestamp != existing_chat.timestamp:
                        needs_sync = True
                    else:
                        # Check if chat has any messages
                        message_count = await get_message_count_by_chat(db, chat_data.id)
                        if message_count == 0:
                            needs_sync = True
                    stats["chats_updated"] += 1
                
                # Create or update chat
                await get_or_create_chat(db, chat_data)
                
                # Track chats that need message sync
                if needs_sync:
                    stats["chats_with_new_messages"].append(chat_data.id)
                
                stats["chats_synced"] += 1
            
            # Check if there are more pages
            if response.cursor:
                cursor = response.cursor
            else:
                break  # No more pages
        
        logger.info(f"Chat sync completed: {stats['chats_synced']} total, {len(stats['chats_with_new_messages'])} need message sync")
        return stats
        
    except Exception as e:
        logger.error(f"Error syncing chats: {str(e)}")
        raise


async def sync_chat_messages(
    db: AsyncSession,
    chat_id: str,
    full_sync: bool = False,
) -> dict:
    """
    Sync messages for a specific chat from Unipile API.
    
    By default, performs incremental sync by fetching only messages
    created after the last stored message timestamp.
    
    Args:
        db: Database session
        chat_id: Chat ID to sync messages for
        full_sync: If True, syncs all messages. If False (default), 
                   syncs only new messages since last sync.
        
    Returns:
        Dictionary with sync statistics:
        {
            "messages_fetched": int,
            "messages_created": int,
            "new_unread_messages": int,
            "latest_timestamp": str or None,
        }
    """
    client = get_unipile_client()
    stats = {
        "messages_fetched": 0,
        "messages_created": 0,
        "new_unread_messages": 0,
        "latest_timestamp": None,
    }
    
    try:
        # Get last message timestamp for incremental sync
        after_timestamp = None
        if not full_sync:
            after_timestamp = await get_latest_message_timestamp(db, chat_id)
            if after_timestamp:
                logger.info(f"Performing incremental sync for chat {chat_id} after {after_timestamp}")
        
        cursor = None
        latest_timestamp = None
        has_new_unread = False
        
        while True:
            # Fetch messages from Unipile
            response = await client.list_chat_messages(
                chat_id=chat_id,
                cursor=cursor,
                after=after_timestamp,
                limit=100,  # Max items per request
            )
            
            logger.info(f"Fetched {len(response.items)} messages for chat {chat_id}")
            stats["messages_fetched"] += len(response.items)
            
            # Process each message
            for message_data in response.items:
                # Try to create message (will return None if duplicate)
                created_message = await create_message(db, message_data)
                
                if created_message:
                    stats["messages_created"] += 1
                    
                    # Track if there are new messages from other users (not sender)
                    if message_data.is_sender == 0:
                        has_new_unread = True
                        stats["new_unread_messages"] += 1
                    
                    # Track latest timestamp
                    if not latest_timestamp or message_data.timestamp > latest_timestamp:
                        latest_timestamp = message_data.timestamp
            
            # Check if there are more pages
            if response.cursor:
                cursor = response.cursor
            else:
                break  # No more pages
        
        # Update chat timestamp if we got new messages
        if latest_timestamp:
            await update_chat_timestamp(db, chat_id, latest_timestamp)
            stats["latest_timestamp"] = latest_timestamp
        
        # Mark chat as unread if there are new messages from others
        if has_new_unread:
            await mark_chat_as_unread(db, chat_id)
            logger.info(f"Marked chat {chat_id} as unread ({stats['new_unread_messages']} new messages)")
        
        logger.info(f"Message sync completed for chat {chat_id}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error syncing messages for chat {chat_id}: {str(e)}")
        raise


async def sync_all_chat_messages(
    db: AsyncSession,
    account_id: Optional[str] = None,
    full_sync: bool = False,
) -> dict:
    """
    Sync messages for all chats.
    
    First syncs all chats, then syncs messages only for chats with new messages.
    
    Args:
        db: Database session
        account_id: Optional account ID to filter chats
        full_sync: If True, performs full sync for all messages.
                   If False (default), performs incremental sync.
        
    Returns:
        Dictionary with sync statistics:
        {
            "chats_synced": int,
            "chats_checked_for_messages": int,
            "chats_skipped": int,
            "total_messages_created": int,
            "total_unread_messages": int,
            "chats_with_errors": int,
        }
    """
    # First, sync all chats
    chat_stats = await sync_all_chats(db, account_id)
    
    overall_stats = {
        "chats_synced": chat_stats["chats_synced"],
        "chats_checked_for_messages": 0,
        "chats_skipped": 0,
        "total_messages_created": 0,
        "total_unread_messages": 0,
        "chats_with_errors": 0,
    }
    
    # Get list of chat IDs that need message sync
    chats_to_sync = chat_stats["chats_with_new_messages"]
    
    if full_sync:
        # If full sync requested, sync all chats
        from app.db.crud import get_all_chats
        all_chats = await get_all_chats(db, account_id=account_id, limit=1000)
        chats_to_sync = [chat.id for chat in all_chats]
        logger.info(f"Full sync requested - will sync messages for all {len(chats_to_sync)} chats")
    else:
        logger.info(f"Incremental sync - will sync messages for {len(chats_to_sync)} chats with new messages")
        overall_stats["chats_skipped"] = chat_stats["chats_synced"] - len(chats_to_sync)
    
    # Sync messages only for chats that need it
    for chat_id in chats_to_sync:
        try:
            message_stats = await sync_chat_messages(db, chat_id, full_sync=full_sync)
            overall_stats["total_messages_created"] += message_stats["messages_created"]
            overall_stats["total_unread_messages"] += message_stats["new_unread_messages"]
            overall_stats["chats_checked_for_messages"] += 1
        except Exception as e:
            logger.error(f"Failed to sync messages for chat {chat_id}: {str(e)}")
            overall_stats["chats_with_errors"] += 1
            continue
    
    logger.info(f"Full sync completed: {overall_stats}")
    return overall_stats


async def quick_sync_all_chats(db: AsyncSession, account_id: Optional[str] = None) -> dict:
    """
    Quick sync that only fetches chat list and updates metadata,
    without syncing all messages.
    
    Useful for checking for new chats or updated chat info.
    
    Args:
        db: Database session
        account_id: Optional account ID to filter chats
        
    Returns:
        Dictionary with sync statistics
    """
    return await sync_all_chats(db, account_id)

