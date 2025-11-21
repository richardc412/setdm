"""Database models for chats and messages."""
from datetime import datetime
from typing import Any

from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatModel(Base):
    """
    Chat model for storing Instagram/Messaging chats.
    Maps to Unipile Chat object with additional local fields.
    """
    __tablename__ = "chats"

    # Primary key - from Unipile
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Core Unipile fields
    account_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String, nullable=False)
    provider_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[str | None] = mapped_column(String, nullable=True)  # ISO 8601 from Unipile
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Local fields for our app
    is_read: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Relationship to messages
    messages: Mapped[list["MessageModel"]] = relationship(
        "MessageModel", 
        back_populates="chat",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ChatModel(id={self.id}, name={self.name}, is_read={self.is_read})>"


class MessageModel(Base):
    """
    Message model for storing chat messages.
    Maps to Unipile Message object.
    """
    __tablename__ = "messages"

    # Primary key - from Unipile
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Foreign key to chat
    chat_id: Mapped[str] = mapped_column(
        String, 
        ForeignKey("chats.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Core Unipile fields
    account_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    chat_provider_id: Mapped[str] = mapped_column(String, nullable=False)
    provider_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    sender_id: Mapped[str] = mapped_column(String, nullable=False)
    sender_attendee_id: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False, index=True)  # ISO 8601
    is_sender: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 or 1
    
    # Complex fields stored as JSON
    attachments: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    reactions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    seen_by: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    quoted: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    reply_to: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Integer flags from Unipile
    seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hidden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    edited: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_event: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Optional Unipile fields
    behavior: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reply_by: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    parent: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    message_type: Mapped[str | None] = mapped_column(String, nullable=True)
    attendee_type: Mapped[str | None] = mapped_column(String, nullable=True)
    attendee_distance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sender_urn: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Local timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to chat
    chat: Mapped["ChatModel"] = relationship("ChatModel", back_populates="messages")

    def __repr__(self) -> str:
        return f"<MessageModel(id={self.id}, chat_id={self.chat_id}, timestamp={self.timestamp})>"


class ChatAttendeeModel(Base):
    """
    Chat attendee model for storing profile information.
    Caches attendee data including profile pictures.
    """
    __tablename__ = "chat_attendees"

    # Primary key - from Unipile
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Core Unipile fields
    account_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_self: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 or 1
    hidden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Profile information
    picture_url: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Instagram specifics stored as JSON
    specifics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<ChatAttendeeModel(id={self.id}, name={self.name}, provider_id={self.provider_id})>"


# Create indexes for common queries
Index("idx_messages_chat_timestamp", MessageModel.chat_id, MessageModel.timestamp)
Index("idx_chats_account_updated", ChatModel.account_id, ChatModel.updated_at)
Index("idx_attendees_provider", ChatAttendeeModel.provider_id)

