"""CRUD operations for chats and messages."""
import logging
from typing import Optional, Sequence
from datetime import datetime, timedelta

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatModel, MessageModel, ChatAttendeeModel, PendingMessageModel
from app.integration.unipile.schemas import Chat, Message


logger = logging.getLogger(__name__)


async def get_or_create_chat(
    db: AsyncSession,
    chat_data: Chat,
) -> ChatModel:
    """
    Get existing chat or create new one.
    Updates timestamp and name if chat exists and data is newer.
    
    Args:
        db: Database session
        chat_data: Chat data from Unipile API
        
    Returns:
        ChatModel instance
    """
    # Try to get existing chat
    result = await db.execute(
        select(ChatModel).where(ChatModel.id == chat_data.id)
    )
    chat = result.scalar_one_or_none()
    
    if chat:
        # Update existing chat if timestamp is newer
        if chat_data.timestamp and (not chat.timestamp or chat_data.timestamp > chat.timestamp):
            chat.timestamp = chat_data.timestamp
            chat.updated_at = datetime.utcnow()
        
        # Update name if provided
        if chat_data.name:
            chat.name = chat_data.name
        
        # Update unread_count
        chat.unread_count = chat_data.unread_count
        
        await db.commit()
        await db.refresh(chat)
    else:
        # Create new chat
        chat = ChatModel(
            id=chat_data.id,
            account_id=chat_data.account_id,
            account_type=chat_data.account_type,
            provider_id=chat_data.provider_id,
            name=chat_data.name,
            timestamp=chat_data.timestamp,
            unread_count=chat_data.unread_count,
            is_read=True,  # Default to read, will be updated during message sync
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
    
    return chat


async def get_chat_by_id(
    db: AsyncSession,
    chat_id: str,
) -> Optional[ChatModel]:
    """
    Get chat by ID.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        ChatModel instance or None if not found
    """
    result = await db.execute(
        select(ChatModel).where(ChatModel.id == chat_id)
    )
    return result.scalar_one_or_none()


async def get_all_chats(
    db: AsyncSession,
    account_id: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_ignored: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[ChatModel]:
    """
    Get all chats with optional filtering.
    
    Args:
        db: Database session
        account_id: Filter by account ID
        is_read: Filter by read/unread status
        is_ignored: Filter by ignored status (default: False to exclude ignored chats)
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of ChatModel instances
    """
    query = select(ChatModel).order_by(desc(ChatModel.updated_at))
    
    # Apply filters
    filters = []
    if account_id:
        filters.append(ChatModel.account_id == account_id)
    if is_read is not None:
        filters.append(ChatModel.is_read == is_read)
    # By default, exclude ignored chats unless explicitly requested
    if is_ignored is None:
        filters.append(ChatModel.is_ignored == False)
    elif is_ignored is not None:
        filters.append(ChatModel.is_ignored == is_ignored)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()


async def update_chat_timestamp(
    db: AsyncSession,
    chat_id: str,
    timestamp: str,
) -> Optional[ChatModel]:
    """
    Update chat's last message timestamp.
    
    Args:
        db: Database session
        chat_id: Chat ID
        timestamp: ISO 8601 timestamp
        
    Returns:
        Updated ChatModel instance or None if not found
    """
    chat = await get_chat_by_id(db, chat_id)
    if chat:
        chat.timestamp = timestamp
        chat.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(chat)
    return chat


async def mark_chat_as_read(
    db: AsyncSession,
    chat_id: str,
) -> Optional[ChatModel]:
    """
    Mark chat as read.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        Updated ChatModel instance or None if not found
    """
    chat = await get_chat_by_id(db, chat_id)
    if chat:
        chat.is_read = True
        chat.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(chat)
    return chat


async def mark_chat_as_unread(
    db: AsyncSession,
    chat_id: str,
) -> Optional[ChatModel]:
    """
    Mark chat as unread.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        Updated ChatModel instance or None if not found
    """
    chat = await get_chat_by_id(db, chat_id)
    if chat:
        chat.is_read = False
        chat.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(chat)
    return chat


async def ignore_chat(
    db: AsyncSession,
    chat_id: str,
) -> Optional[ChatModel]:
    """
    Mark chat as ignored.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        Updated ChatModel instance or None if not found
    """
    chat = await get_chat_by_id(db, chat_id)
    if chat:
        chat.is_ignored = True
        chat.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(chat)
    return chat


async def unignore_chat(
    db: AsyncSession,
    chat_id: str,
) -> Optional[ChatModel]:
    """
    Mark chat as not ignored.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        Updated ChatModel instance or None if not found
    """
    chat = await get_chat_by_id(db, chat_id)
    if chat:
        chat.is_ignored = False
        chat.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(chat)
    return chat


async def get_message_by_id(
    db: AsyncSession,
    message_id: str,
) -> Optional[MessageModel]:
    """
    Get a message by its ID.
    
    Args:
        db: Database session
        message_id: Message ID to look up
        
    Returns:
        MessageModel instance or None if not found
    """
    result = await db.execute(
        select(MessageModel).where(MessageModel.id == message_id)
    )
    return result.scalar_one_or_none()


async def create_message(
    db: AsyncSession,
    message_data: Message,
) -> Optional[MessageModel]:
    """
    Create a new message if it doesn't already exist.
    Uses provider_id for deduplication.
    
    Args:
        db: Database session
        message_data: Message data from Unipile API
        
    Returns:
        MessageModel instance or None if message already exists
    """
    # Check if message already exists by provider_id
    result = await db.execute(
        select(MessageModel).where(MessageModel.provider_id == message_data.provider_id)
    )
    existing_message = result.scalar_one_or_none()
    
    if existing_message:
        return None  # Message already exists, skip
    
    # Resolve sender_id: use attendee's provider_id if available
    resolved_sender_id = message_data.sender_id
    if message_data.sender_attendee_id:
        attendee = await get_attendee_by_id(db, message_data.sender_attendee_id)
        if attendee and attendee.provider_id:
            resolved_sender_id = attendee.provider_id
    
    # Check if this message exists in pending_messages to correctly set is_sender
    # Unipile sometimes returns is_sender=0 for messages we sent, so we need to override it
    is_sender_value = message_data.is_sender
    pending_check = await db.execute(
        select(PendingMessageModel).where(PendingMessageModel.message_id == message_data.id)
    )
    pending_message = pending_check.scalar_one_or_none()
    if pending_message:
        # This is a message we sent - override is_sender to 1
        is_sender_value = 1
        logger.info(f"Message {message_data.id} found in pending queue, setting is_sender=1")
    
    # Convert Pydantic models to dicts for JSON fields
    attachments = [att if isinstance(att, dict) else att.model_dump() for att in message_data.attachments]
    reactions = [r.model_dump() for r in message_data.reactions]
    
    # Create new message
    message = MessageModel(
        id=message_data.id,
        chat_id=message_data.chat_id,
        account_id=message_data.account_id,
        chat_provider_id=message_data.chat_provider_id,
        provider_id=message_data.provider_id,
        sender_id=resolved_sender_id,
        sender_attendee_id=message_data.sender_attendee_id,
        text=message_data.text,
        timestamp=message_data.timestamp,
        is_sender=is_sender_value,
        attachments=attachments,
        reactions=reactions,
        seen_by=message_data.seen_by,
        quoted=message_data.quoted.model_dump() if message_data.quoted else None,
        reply_to=message_data.reply_to.model_dump() if message_data.reply_to else None,
        seen=message_data.seen,
        hidden=message_data.hidden,
        deleted=message_data.deleted,
        edited=message_data.edited,
        is_event=message_data.is_event,
        delivered=message_data.delivered,
        behavior=message_data.behavior,
        original=message_data.original,
        event_type=message_data.event_type,
        replies=message_data.replies,
        reply_by=message_data.reply_by,
        parent=message_data.parent,
        subject=message_data.subject,
        message_type=message_data.message_type,
        attendee_type=message_data.attendee_type,
        attendee_distance=message_data.attendee_distance,
        sender_urn=message_data.sender_urn,
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    return message


async def get_messages_by_chat(
    db: AsyncSession,
    chat_id: str,
    limit: int = 100,
    offset: int = 0,
    order_desc: bool = True,
) -> Sequence[MessageModel]:
    """
    Get messages for a specific chat.
    
    Args:
        db: Database session
        chat_id: Chat ID
        limit: Maximum number of results
        offset: Number of results to skip
        order_desc: Order by timestamp descending (newest first)
        
    Returns:
        List of MessageModel instances
    """
    order = desc(MessageModel.timestamp) if order_desc else MessageModel.timestamp
    
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.chat_id == chat_id)
        .order_by(order)
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


async def get_latest_message_timestamp(
    db: AsyncSession,
    chat_id: str,
) -> Optional[str]:
    """
    Get the timestamp of the latest message in a chat.
    Used for incremental syncing.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        ISO 8601 timestamp string or None if no messages
    """
    result = await db.execute(
        select(MessageModel.timestamp)
        .where(MessageModel.chat_id == chat_id)
        .order_by(desc(MessageModel.timestamp))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_message_count_by_chat(
    db: AsyncSession,
    chat_id: str,
) -> int:
    """
    Get total message count for a chat.
    
    Args:
        db: Database session
        chat_id: Chat ID
        
    Returns:
        Message count
    """
    result = await db.execute(
        select(func.count(MessageModel.id))
        .where(MessageModel.chat_id == chat_id)
    )
    return result.scalar_one()


async def upsert_attendee(
    db: AsyncSession,
    attendee_data: any,
) -> ChatAttendeeModel:
    """
    Create or update a chat attendee.
    
    Args:
        db: Database session
        attendee_data: ChatAttendee data from Unipile API
        
    Returns:
        ChatAttendeeModel instance
    """
    # Try to get existing attendee
    result = await db.execute(
        select(ChatAttendeeModel).where(ChatAttendeeModel.id == attendee_data.id)
    )
    attendee = result.scalar_one_or_none()
    
    # Convert specifics to dict if it exists
    specifics_dict = attendee_data.specifics.model_dump() if attendee_data.specifics else None
    
    if attendee:
        # Update existing attendee
        attendee.name = attendee_data.name
        attendee.picture_url = attendee_data.picture_url
        attendee.profile_url = attendee_data.profile_url
        attendee.specifics = specifics_dict
        attendee.hidden = attendee_data.hidden
        attendee.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(attendee)
    else:
        # Create new attendee
        attendee = ChatAttendeeModel(
            id=attendee_data.id,
            account_id=attendee_data.account_id,
            provider_id=attendee_data.provider_id,
            name=attendee_data.name,
            is_self=attendee_data.is_self,
            hidden=attendee_data.hidden,
            picture_url=attendee_data.picture_url,
            profile_url=attendee_data.profile_url,
            specifics=specifics_dict,
        )
        db.add(attendee)
        await db.commit()
        await db.refresh(attendee)
    
    return attendee


async def get_attendee_by_id(
    db: AsyncSession,
    attendee_id: str,
) -> Optional[ChatAttendeeModel]:
    """
    Get attendee by their internal ID.
    
    Args:
        db: Database session
        attendee_id: Internal attendee ID
        
    Returns:
        ChatAttendeeModel instance or None if not found
    """
    result = await db.execute(
        select(ChatAttendeeModel).where(ChatAttendeeModel.id == attendee_id)
    )
    return result.scalar_one_or_none()


async def get_attendee_by_provider_id(
    db: AsyncSession,
    provider_id: str,
) -> Optional[ChatAttendeeModel]:
    """
    Get attendee by provider ID.
    
    Args:
        db: Database session
        provider_id: Provider ID (e.g., Instagram user ID)
        
    Returns:
        ChatAttendeeModel instance or None if not found
    """
    result = await db.execute(
        select(ChatAttendeeModel).where(ChatAttendeeModel.provider_id == provider_id)
    )
    return result.scalar_one_or_none()


async def get_attendees_by_account(
    db: AsyncSession,
    account_id: str,
) -> Sequence[ChatAttendeeModel]:
    """
    Get all attendees for an account.
    
    Args:
        db: Database session
        account_id: Account ID
        
    Returns:
        List of ChatAttendeeModel instances
    """
    result = await db.execute(
        select(ChatAttendeeModel)
        .where(ChatAttendeeModel.account_id == account_id)
        .order_by(ChatAttendeeModel.name)
    )
    return result.scalars().all()


# =============================================================================
# Pending Message CRUD Operations
# =============================================================================


async def create_pending_message(
    db: AsyncSession,
    message_id: str,
    chat_id: str,
    text: Optional[str],
    timestamp: str,
) -> PendingMessageModel:
    """
    Create a pending message after successful send to Unipile.
    
    Args:
        db: Database session
        message_id: Message ID from Unipile response
        chat_id: Chat ID
        text: Message text content
        timestamp: ISO 8601 timestamp
        
    Returns:
        PendingMessageModel instance
    """
    pending_message = PendingMessageModel(
        message_id=message_id,
        chat_id=chat_id,
        text=text,
        timestamp=timestamp,
        status="pending",
        sync_attempts=0,
    )
    db.add(pending_message)
    await db.commit()
    await db.refresh(pending_message)
    return pending_message


async def get_pending_messages(
    db: AsyncSession,
    chat_id: Optional[str] = None,
    older_than_seconds: Optional[int] = None,
    status: str = "pending",
) -> Sequence[PendingMessageModel]:
    """
    Get pending messages, optionally filtered by chat and age.
    
    Args:
        db: Database session
        chat_id: Optional chat ID to filter by
        older_than_seconds: Only get messages older than this many seconds
        status: Status filter (default: 'pending')
        
    Returns:
        List of PendingMessageModel instances
    """
    query = select(PendingMessageModel).where(PendingMessageModel.status == status)
    
    if chat_id:
        query = query.where(PendingMessageModel.chat_id == chat_id)
    
    if older_than_seconds is not None:
        cutoff_time = datetime.utcnow() - timedelta(seconds=older_than_seconds)
        query = query.where(PendingMessageModel.created_at <= cutoff_time)
    
    query = query.order_by(PendingMessageModel.created_at)
    
    result = await db.execute(query)
    return result.scalars().all()


async def mark_pending_as_synced(
    db: AsyncSession,
    message_id: str,
) -> Optional[PendingMessageModel]:
    """
    Mark a pending message as synced.
    
    Args:
        db: Database session
        message_id: Message ID to mark as synced
        
    Returns:
        Updated PendingMessageModel or None if not found
    """
    result = await db.execute(
        select(PendingMessageModel).where(PendingMessageModel.message_id == message_id)
    )
    pending_message = result.scalar_one_or_none()
    
    if pending_message:
        pending_message.status = "synced"
        pending_message.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(pending_message)
    
    return pending_message


async def increment_sync_attempts(
    db: AsyncSession,
    message_id: str,
    max_attempts: int = 3,
) -> Optional[PendingMessageModel]:
    """
    Increment sync attempts for a pending message.
    Mark as failed if max attempts reached.
    
    Args:
        db: Database session
        message_id: Message ID
        max_attempts: Maximum attempts before marking as failed
        
    Returns:
        Updated PendingMessageModel or None if not found
    """
    result = await db.execute(
        select(PendingMessageModel).where(PendingMessageModel.message_id == message_id)
    )
    pending_message = result.scalar_one_or_none()
    
    if pending_message:
        pending_message.sync_attempts += 1
        pending_message.updated_at = datetime.utcnow()
        
        if pending_message.sync_attempts >= max_attempts:
            pending_message.status = "failed"
        
        await db.commit()
        await db.refresh(pending_message)
    
    return pending_message


async def delete_synced_pending_messages(
    db: AsyncSession,
    older_than_hours: int = 24,
) -> int:
    """
    Delete synced pending messages older than specified hours.
    Cleanup job to prevent table bloat.
    
    Args:
        db: Database session
        older_than_hours: Delete synced messages older than this many hours
        
    Returns:
        Number of deleted messages
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
    
    result = await db.execute(
        select(PendingMessageModel)
        .where(
            and_(
                PendingMessageModel.status == "synced",
                PendingMessageModel.updated_at <= cutoff_time
            )
        )
    )
    messages_to_delete = result.scalars().all()
    
    for message in messages_to_delete:
        await db.delete(message)
    
    await db.commit()
    return len(messages_to_delete)

