"""Pydantic schemas for chats API."""
from typing import Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


AssistMode = Literal["manual", "ai-assisted", "autopilot"]


class ChatResponse(BaseModel):
    """Response model for a chat."""
    id: str
    account_id: str
    account_type: str
    provider_id: str
    name: Optional[str] = None
    timestamp: Optional[str] = None
    unread_count: int
    is_read: bool
    is_ignored: bool
    assist_mode: AssistMode
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatListResponse(BaseModel):
    """Response model for list of chats."""
    items: list[ChatResponse]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    chat_id: str
    account_id: str
    provider_id: str
    sender_id: str
    sender_attendee_id: str
    text: Optional[str] = None
    timestamp: str
    is_sender: int
    attachments: list[Any]
    reactions: list[dict[str, Any]]
    seen: int
    hidden: int
    deleted: int
    edited: int
    is_event: int
    delivered: int
    sent_by_autopilot: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response model for list of messages."""
    items: list[MessageResponse]
    total: int
    limit: int
    offset: int


class MarkReadRequest(BaseModel):
    """Request model for marking chat as read."""
    pass  # No body needed, just POST to endpoint


class SyncResponse(BaseModel):
    """Response model for sync operations."""
    success: bool
    message: str
    stats: dict[str, Any]


class GenerateResponseRequest(BaseModel):
    """Request payload for AI-generated suggestions."""
    prompt: str = Field(..., min_length=1, description="Instruction or goal for the AI assistant")
    history_limit: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description="Override for number of historical messages to include",
    )


class GenerateResponsePayload(BaseModel):
    """Response payload for AI-generated suggestions."""
    suggestion: str
    prompt: str


class UpdateAssistModeRequest(BaseModel):
    """Request payload for changing a chat's assist/autopilot mode."""
    assist_mode: AssistMode


