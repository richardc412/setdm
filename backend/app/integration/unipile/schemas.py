from typing import Optional, Any, Union
from pydantic import BaseModel, field_validator


# Chat Attendee Types

class InstagramSpecifics(BaseModel):
    """Instagram-specific attendee data."""
    provider: str  # "INSTAGRAM"
    public_identifier: str
    relationship_status: dict[str, bool]


class ChatAttendee(BaseModel):
    """
    Chat attendee model containing profile information.
    """
    object: str  # "ChatAttendee"
    id: str
    account_id: str
    provider_id: str
    name: str
    is_self: int  # 0 or 1
    hidden: Optional[int] = None  # 0 or 1
    picture_url: Optional[str] = None
    profile_url: Optional[str] = None
    specifics: Optional[InstagramSpecifics] = None


class ChatAttendeeListResponse(BaseModel):
    """
    Response model for list attendees endpoint.
    """
    object: str  # "ChatAttendeeList"
    items: list[ChatAttendee]
    cursor: Optional[Any] = None


class Chat(BaseModel):
    """
    Simplified Chat model containing only the essential fields.
    """
    object: str
    id: str
    account_id: str
    account_type: str
    provider_id: str
    name: Optional[str] = None
    timestamp: Optional[str] = None
    unread_count: int
    unread: Optional[bool] = None


class ChatListResponse(BaseModel):
    """
    Response model for list all chats endpoint.
    """
    object: str
    items: list[Chat]
    cursor: Optional[str] = None


# Message Attachment Types

class AttachmentSize(BaseModel):
    """Size dimensions for image/video attachments."""
    width: float
    height: float


class ImageAttachment(BaseModel):
    """Image attachment."""
    type: str  # "img"
    id: str
    unavailable: bool
    size: AttachmentSize
    sticker: bool
    file_size: Optional[float] = None
    mimetype: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[float] = None


class VideoAttachment(BaseModel):
    """Video attachment."""
    type: str  # "video"
    id: str
    unavailable: bool
    size: AttachmentSize
    gif: bool
    file_size: Optional[float] = None
    mimetype: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[float] = None


class AudioAttachment(BaseModel):
    """Audio attachment."""
    type: str  # "audio"
    id: str
    unavailable: bool
    voice_note: bool
    duration: Optional[float] = None
    file_size: Optional[float] = None
    mimetype: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[float] = None


class FileAttachment(BaseModel):
    """File attachment."""
    type: str  # "file"
    id: str
    unavailable: bool
    file_name: str
    file_size: Optional[float] = None
    mimetype: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[float] = None


class LinkedInPostAttachment(BaseModel):
    """LinkedIn post attachment."""
    type: str  # "linkedin_post"
    id: str
    unavailable: bool
    file_size: Optional[float] = None
    mimetype: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[float] = None


class VideoMeetingAttachment(BaseModel):
    """Video meeting attachment."""
    type: str  # "video_meeting"
    id: str
    unavailable: bool
    starts_at: Optional[float] = None
    expires_at: Optional[float] = None
    time_range: Optional[float] = None
    file_size: Optional[float] = None
    mimetype: Optional[str] = None
    url: Optional[str] = None
    url_expires_at: Optional[float] = None


# Union type for all attachment types
Attachment = Union[
    ImageAttachment,
    VideoAttachment,
    AudioAttachment,
    FileAttachment,
    LinkedInPostAttachment,
    VideoMeetingAttachment,
]


class Reaction(BaseModel):
    """Message reaction."""
    value: str
    sender_id: str
    is_sender: bool


class QuotedMessage(BaseModel):
    """Quoted/replied-to message."""
    provider_id: str
    sender_id: str
    text: Optional[str] = None
    attachments: list[Any]  # Can contain same attachment types


class ReplyTo(BaseModel):
    """Reply-to message reference."""
    id: str
    provider_id: str
    timestamp: str
    sender_attendee_id: str
    sender_id: str
    text: Optional[str] = None


class Message(BaseModel):
    """
    Message model containing essential message fields.
    """
    object: str  # "Message"
    id: str
    account_id: str
    chat_id: str
    chat_provider_id: str
    provider_id: str
    sender_id: str
    sender_attendee_id: str
    text: Optional[str] = None
    timestamp: str
    is_sender: int  # 0 or 1
    attachments: list[Any]  # List of attachment objects
    reactions: list[Reaction]
    seen: int  # 0 or 1
    seen_by: dict[str, Any]
    hidden: int  # 0 or 1
    deleted: int  # 0 or 1
    edited: int  # 0 or 1
    is_event: int  # 0 or 1
    delivered: int  # 0 or 1
    behavior: Optional[int] = None
    original: str
    
    # Optional fields
    quoted: Optional[QuotedMessage] = None
    event_type: Optional[int] = None
    replies: Optional[int] = None
    reply_by: Optional[list[str]] = None
    parent: Optional[str] = None
    subject: Optional[str] = None
    message_type: Optional[str] = None
    attendee_type: Optional[str] = None
    attendee_distance: Optional[int] = None
    sender_urn: Optional[str] = None
    reply_to: Optional[ReplyTo] = None


class MessageListResponse(BaseModel):
    """
    Response model for list chat messages endpoint.
    """
    object: str  # "MessageList"
    items: list[Message]
    cursor: Optional[Any] = None


# Send Message Types

class SendMessageRequest(BaseModel):
    """
    Request model for sending a message in a chat.
    """
    text: Optional[str] = None
    account_id: Optional[str] = None
    thread_id: Optional[str] = None
    quote_id: Optional[str] = None
    typing_duration: Optional[str] = None


class MessageSentResponse(BaseModel):
    """
    Response model for send message endpoint.
    """
    object: str  # "MessageSent"
    message_id: Optional[str] = None
    
    @field_validator('message_id', mode='before')
    @classmethod
    def normalize_message_id(cls, v):
        """
        Normalize message_id: convert list to string if needed.
        Unipile sometimes returns message_id as a list with a single element.
        """
        if isinstance(v, list) and len(v) > 0:
            return v[0]
        return v

