from typing import Optional
from pydantic import BaseModel


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

