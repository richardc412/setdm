from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path
from .client import list_all_chats, list_chat_messages
from .schemas import ChatListResponse, MessageListResponse


router = APIRouter(prefix="/api/unipile", tags=["Unipile Integration"])


@router.get("/chats", response_model=ChatListResponse)
async def get_all_chats(
    unread: Optional[bool] = Query(
        None,
        description="Filter for unread/read chats only"
    ),
    cursor: Optional[str] = Query(
        None,
        description="Cursor for pagination"
    ),
    before: Optional[str] = Query(
        None,
        description="Filter items created before datetime (ISO 8601 UTC)",
        pattern=r"^[1-2]\d{3}-[0-1]\d-[0-3]\dT\d{2}:\d{2}:\d{2}.\d{3}Z$"
    ),
    after: Optional[str] = Query(
        None,
        description="Filter items created after datetime (ISO 8601 UTC)",
        pattern=r"^[1-2]\d{3}-[0-1]\d-[0-3]\dT\d{2}:\d{2}:\d{2}.\d{3}Z$"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=250,
        description="Limit number of items (1-250)"
    ),
    account_type: Optional[str] = Query(
        None,
        description="Filter by provider",
        pattern="^(WHATSAPP|LINKEDIN|SLACK|TWITTER|MESSENGER|INSTAGRAM|TELEGRAM)$"
    ),
    account_id: Optional[str] = Query(
        None,
        description="Filter by account ID (comma-separated list)"
    ),
) -> ChatListResponse:
    """
    List all chats from Unipile API.

    This endpoint proxies the Unipile API's `/api/v1/chats` endpoint
    and returns simplified chat objects with only the essential fields.

    **Query Parameters:**
    - `unread`: Filter for unread/read chats only
    - `cursor`: Cursor for pagination
    - `before`: Filter items created before datetime (ISO 8601 UTC)
    - `after`: Filter items created after datetime (ISO 8601 UTC)
    - `limit`: Limit number of items (1-250)
    - `account_type`: Filter by provider (WHATSAPP, LINKEDIN, SLACK, etc.)
    - `account_id`: Filter by account ID (comma-separated list)

    **Returns:**
    - `ChatListResponse` with simplified chat objects

    **Example:**
    ```
    GET /api/unipile/chats?unread=true&limit=50
    ```
    """
    try:
        response = await list_all_chats(
            unread=unread,
            cursor=cursor,
            before=before,
            after=after,
            limit=limit,
            account_type=account_type,
            account_id=account_id,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chats from Unipile: {str(e)}"
        )


@router.get("/chats/{chat_id}/messages", response_model=MessageListResponse)
async def get_chat_messages(
    chat_id: str = Path(
        ...,
        description="The id of the chat related to requested messages"
    ),
    cursor: Optional[str] = Query(
        None,
        description="Cursor for pagination"
    ),
    before: Optional[str] = Query(
        None,
        description="Filter items created before datetime (ISO 8601 UTC)",
        pattern=r"^[1-2]\d{3}-[0-1]\d-[0-3]\dT\d{2}:\d{2}:\d{2}.\d{3}Z$"
    ),
    after: Optional[str] = Query(
        None,
        description="Filter items created after datetime (ISO 8601 UTC)",
        pattern=r"^[1-2]\d{3}-[0-1]\d-[0-3]\dT\d{2}:\d{2}:\d{2}.\d{3}Z$"
    ),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=250,
        description="Limit number of items (1-250)"
    ),
    sender_id: Optional[str] = Query(
        None,
        description="Filter messages from a specific sender"
    ),
) -> MessageListResponse:
    """
    List all messages from a specific chat.

    This endpoint proxies the Unipile API's `/api/v1/chats/{chat_id}/messages` endpoint
    and returns message objects from the specified chat.

    **Path Parameters:**
    - `chat_id`: The id of the chat related to requested messages

    **Query Parameters:**
    - `cursor`: Cursor for pagination
    - `before`: Filter items created before datetime (ISO 8601 UTC)
    - `after`: Filter items created after datetime (ISO 8601 UTC)
    - `limit`: Limit number of items (1-250)
    - `sender_id`: Filter messages from a specific sender

    **Returns:**
    - `MessageListResponse` with message objects

    **Example:**
    ```
    GET /api/unipile/chats/abc123/messages?limit=50
    ```
    """
    try:
        response = await list_chat_messages(
            chat_id=chat_id,
            cursor=cursor,
            before=before,
            after=after,
            limit=limit,
            sender_id=sender_id,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch messages from Unipile: {str(e)}"
        )


@router.get("/chats/{chat_id}/attendees")
async def list_chat_attendees(
    chat_id: str,
):
    """
    List all attendees from a chat.
    
    Returns profile information including picture_url for each attendee.
    Useful for displaying profile pictures in the frontend.
    
    Args:
        chat_id: The id of the chat
        
    Returns:
        ChatAttendeeListResponse with attendee information
    """
    try:
        client = get_unipile_client()
        response = await client.list_chat_attendees(chat_id)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch attendees from Unipile: {str(e)}"
        )

