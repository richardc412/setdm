"""Batch processor for pending messages."""
import logging
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.db.crud import (
    get_pending_messages,
    mark_pending_as_synced,
    increment_sync_attempts,
    get_message_by_id,
    delete_synced_pending_messages,
)
from app.services.message_sync import sync_chat_messages

logger = logging.getLogger(__name__)


async def process_pending_messages():
    """
    Process pending messages that are at least 10 seconds old.
    
    This function:
    1. Fetches pending messages older than 10 seconds
    2. Groups them by chat_id for efficient batch processing
    3. Syncs each chat once
    4. Marks messages as synced or increments retry counter
    5. Cleans up old synced messages
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get pending messages older than 10 seconds
            pending_messages = await get_pending_messages(
                db,
                older_than_seconds=10,
                status="pending"
            )
            
            if not pending_messages:
                logger.debug("No pending messages to process")
                return
            
            logger.info(f"Processing {len(pending_messages)} pending messages")
            
            # Group messages by chat_id for efficient batching
            messages_by_chat = defaultdict(list)
            for pending_msg in pending_messages:
                messages_by_chat[pending_msg.chat_id].append(pending_msg)
            
            # Process each chat once
            for chat_id, messages in messages_by_chat.items():
                try:
                    logger.info(f"Syncing chat {chat_id} ({len(messages)} pending messages)")
                    
                    # Sync the chat to fetch new messages from Unipile
                    await sync_chat_messages(db, chat_id, full_sync=False)
                    
                    # Check which pending messages are now synced
                    for pending_msg in messages:
                        # Check if message exists in messages table
                        synced_message = await get_message_by_id(db, pending_msg.message_id)
                        
                        if synced_message:
                            # Message successfully synced
                            await mark_pending_as_synced(db, pending_msg.message_id)
                            logger.info(f"Message {pending_msg.message_id} successfully synced")
                        else:
                            # Message not synced yet, increment attempts
                            updated = await increment_sync_attempts(db, pending_msg.message_id)
                            if updated and updated.status == "failed":
                                logger.warning(
                                    f"Message {pending_msg.message_id} marked as failed "
                                    f"after {updated.sync_attempts} attempts"
                                )
                            else:
                                logger.debug(
                                    f"Message {pending_msg.message_id} not synced yet, "
                                    f"attempt {updated.sync_attempts if updated else 'unknown'}"
                                )
                
                except Exception as e:
                    logger.error(f"Error processing chat {chat_id}: {str(e)}")
                    # Continue with other chats even if one fails
                    continue
            
            # Cleanup: Delete synced messages older than 24 hours
            deleted_count = await delete_synced_pending_messages(db, older_than_hours=24)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old synced pending messages")
        
        except Exception as e:
            logger.error(f"Error in pending message processor: {str(e)}")
            raise

