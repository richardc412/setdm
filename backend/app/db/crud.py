"""CRUD operations for chats and messages."""
from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatModel, MessageModel, ChatAttendeeModel
from app.integration.unipile.schemas import Chat, Message


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
    limit: int = 100,
    offset: int = 0,
) -> Sequence[ChatModel]:
    """
    Get all chats with optional filtering.
    
    Args:
        db: Database session
        account_id: Filter by account ID
        is_read: Filter by read/unread status
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
        sender_id=message_data.sender_id,
        sender_attendee_id=message_data.sender_attendee_id,
        text=message_data.text,
        timestamp=message_data.timestamp,
        is_sender=message_data.is_sender,
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

