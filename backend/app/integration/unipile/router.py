from typing import Optional
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Path, File, Form, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .client import list_all_chats, list_chat_messages, send_message, get_unipile_client
from .schemas import ChatListResponse, MessageListResponse, MessageSentResponse
from app.db.base import get_db
from app.db.crud import create_pending_message

logger = logging.getLogger(__name__)


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


@router.post("/chats/{chat_id}/messages", response_model=MessageSentResponse, status_code=201)
async def send_message_in_chat(
    chat_id: str = Path(
        ...,
        description="The id of the chat where to send the message"
    ),
    text: Optional[str] = Form(
        None,
        description="The message text"
    ),
    account_id: Optional[str] = Form(
        None,
        description="An account_id can be specified to prevent the user from sending messages in chats not belonging to the account"
    ),
    thread_id: Optional[str] = Form(
        None,
        description="Optional and for Slack's messaging only. The id of the thread to send the message in"
    ),
    quote_id: Optional[str] = Form(
        None,
        description="The id of a message to quote/reply to"
    ),
    voice_message: Optional[UploadFile] = File(
        None,
        description="(Whatsapp & Linkedin) A file to send as voice message. We recommend usage of .m4a format for Linkedin. For Instagram and Telegram you need to use attachment field"
    ),
    video_message: Optional[UploadFile] = File(
        None,
        description="(Linkedin) A file to send as video message"
    ),
    attachments: Optional[list[UploadFile]] = File(
        None,
        description="List of files to attach"
    ),
    typing_duration: Optional[str] = Form(
        None,
        description="(WhatsApp only) Set a duration in milliseconds to simulate a typing status for that duration before sending the message"
    ),
    db: AsyncSession = Depends(get_db),
) -> MessageSentResponse:
    """
    Send a message in a chat.

    This endpoint proxies the Unipile API's POST `/api/v1/chats/{chat_id}/messages` endpoint
    to send a message with optional attachments.

    **Path Parameters:**
    - `chat_id`: The id of the chat where to send the message

    **Form Data:**
    - `text`: The message text
    - `account_id`: Optional account_id to restrict message sending
    - `thread_id`: Optional thread_id for Slack
    - `quote_id`: Optional message_id to quote/reply to
    - `voice_message`: Optional voice message file
    - `video_message`: Optional video message file
    - `attachments`: Optional list of file attachments
    - `typing_duration`: Optional typing simulation duration (WhatsApp only)

    **Returns:**
    - `MessageSentResponse` with the message_id

    **Example:**
    ```
    POST /api/unipile/chats/abc123/messages
    Content-Type: multipart/form-data

    text=Hello World!
    ```
    """
    try:
        # Prepare file tuples if files are provided
        voice_msg_tuple = None
        if voice_message:
            voice_msg_tuple = (
                voice_message.filename or "voice_message",
                voice_message.file,
                voice_message.content_type or "application/octet-stream",
            )

        video_msg_tuple = None
        if video_message:
            video_msg_tuple = (
                video_message.filename or "video_message",
                video_message.file,
                video_message.content_type or "application/octet-stream",
            )

        attachment_tuples = None
        if attachments:
            attachment_tuples = [
                (
                    att.filename or f"attachment_{i}",
                    att.file,
                    att.content_type or "application/octet-stream",
                )
                for i, att in enumerate(attachments)
            ]

        response = await send_message(
            chat_id=chat_id,
            text=text,
            account_id=account_id,
            thread_id=thread_id,
            quote_id=quote_id,
            voice_message=voice_msg_tuple,
            video_message=video_msg_tuple,
            attachments=attachment_tuples,
            typing_duration=typing_duration,
        )
        
        # Add message to pending queue for batch processing
        try:
            if response.message_id:
                await create_pending_message(
                    db=db,
                    message_id=response.message_id,
                    chat_id=chat_id,
                    text=text,
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                )
                logger.info(f"Added message {response.message_id} to pending queue for chat {chat_id}")
            else:
                logger.warning(f"Message sent to chat {chat_id} but no message_id returned")
        except Exception as queue_error:
            # Log but don't fail the request if queuing fails
            logger.error(f"Failed to queue message for chat {chat_id}: {str(queue_error)}")
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message via Unipile: {str(e)}"
        )

