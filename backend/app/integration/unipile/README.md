# Unipile Integration

This module provides integration with the Unipile API for managing chats and messages across multiple messaging platforms (WhatsApp, LinkedIn, Slack, Twitter, Messenger, Instagram, Telegram).

## Configuration

Add the following environment variables to your `.env` file:

```env
UNIPILE_DSN=https://api1.unipile.com:13111
UNIPILE_API_KEY=your_api_key_here
```

## Usage

### Option 1: Using the API Endpoint

The integration exposes a REST API endpoint that you can call from your frontend or other services:

```
GET /api/unipile/chats
```

#### Query Parameters:

- `unread` (boolean, optional): Filter for unread/read chats only
- `cursor` (string, optional): Cursor for pagination
- `before` (string, optional): Filter items created before datetime (ISO 8601 UTC format: `2025-12-31T23:59:59.999Z`)
- `after` (string, optional): Filter items created after datetime (ISO 8601 UTC format: `2025-12-31T23:59:59.999Z`)
- `limit` (integer, optional): Limit number of items (1-250)
- `account_type` (string, optional): Filter by provider (`WHATSAPP`, `LINKEDIN`, `SLACK`, `TWITTER`, `MESSENGER`, `INSTAGRAM`, `TELEGRAM`)
- `account_id` (string, optional): Filter by account ID (comma-separated list)

#### Example Requests:

```bash
# Get all chats
curl http://localhost:8000/api/unipile/chats

# Get only unread chats with limit
curl http://localhost:8000/api/unipile/chats?unread=true&limit=50

# Get chats from LinkedIn only
curl http://localhost:8000/api/unipile/chats?account_type=LINKEDIN

# Get chats with pagination
curl http://localhost:8000/api/unipile/chats?limit=100&cursor=abc123
```

#### Response Format:

```json
{
  "object": "ChatList",
  "items": [
    {
      "object": "Chat",
      "id": "chat_123",
      "account_id": "acc_456",
      "account_type": "LINKEDIN",
      "provider_id": "provider_789",
      "name": "John Doe",
      "timestamp": "2025-11-21T10:30:00.000Z",
      "unread_count": 3,
      "unread": true
    }
  ],
  "cursor": "next_page_cursor_or_null"
}
```

### Option 2: Using the Python Client Directly

You can also use the Unipile client directly in your Python code:

```python
from app.integration.unipile import list_all_chats, get_unipile_client

# Using the convenience function
async def get_chats():
    response = await list_all_chats(unread=True, limit=50)
    for chat in response.items:
        print(f"Chat: {chat.name}, Unread: {chat.unread_count}")

# Using the client directly for more control
async def get_chats_advanced():
    client = get_unipile_client()
    response = await client.list_all_chats(
        account_type="LINKEDIN",
        limit=100
    )
    return response
```

### Option 3: Using in FastAPI Dependencies

You can use the client in your FastAPI route dependencies:

```python
from fastapi import APIRouter, Depends
from app.integration.unipile import get_unipile_client, UnipileClient

router = APIRouter()

@router.get("/my-chats")
async def my_chats(
    client: UnipileClient = Depends(get_unipile_client)
):
    chats = await client.list_all_chats(limit=10)
    return chats
```

---

## Listing Messages from a Chat

### Option 1: Using the API Endpoint

Get messages from a specific chat:

```
GET /api/unipile/chats/{chat_id}/messages
```

#### Path Parameters:

- `chat_id` (string, required): The id of the chat related to requested messages

#### Query Parameters:

- `cursor` (string, optional): Cursor for pagination
- `before` (string, optional): Filter items created before datetime (ISO 8601 UTC format: `2025-12-31T23:59:59.999Z`)
- `after` (string, optional): Filter items created after datetime (ISO 8601 UTC format: `2025-12-31T23:59:59.999Z`)
- `limit` (integer, optional): Limit number of items (1-250)
- `sender_id` (string, optional): Filter messages from a specific sender

#### Example Requests:

```bash
# Get all messages from a chat
curl http://localhost:8000/api/unipile/chats/abc123/messages

# Get recent messages with limit
curl http://localhost:8000/api/unipile/chats/abc123/messages?limit=50

# Get messages from a specific sender
curl http://localhost:8000/api/unipile/chats/abc123/messages?sender_id=sender123

# Get messages with pagination
curl http://localhost:8000/api/unipile/chats/abc123/messages?limit=100&cursor=xyz789

# Get messages in a date range
curl "http://localhost:8000/api/unipile/chats/abc123/messages?after=2025-11-01T00:00:00.000Z&before=2025-11-30T23:59:59.999Z"
```

#### Response Format:

```json
{
  "object": "MessageList",
  "items": [
    {
      "object": "Message",
      "id": "msg_123",
      "account_id": "acc_456",
      "chat_id": "chat_789",
      "chat_provider_id": "provider_chat_id",
      "provider_id": "provider_msg_id",
      "sender_id": "sender_123",
      "sender_attendee_id": "attendee_456",
      "text": "Hello, how are you?",
      "timestamp": "2025-11-21T10:30:00.000Z",
      "is_sender": 1,
      "attachments": [],
      "reactions": [
        {
          "value": "👍",
          "sender_id": "sender_789",
          "is_sender": false
        }
      ],
      "seen": 1,
      "seen_by": {},
      "hidden": 0,
      "deleted": 0,
      "edited": 0,
      "is_event": 0,
      "delivered": 1,
      "behavior": 0,
      "original": "Hello, how are you?"
    }
  ],
  "cursor": "next_page_cursor_or_null"
}
```

### Option 2: Using the Python Client Directly

You can also use the Unipile client directly in your Python code:

```python
from app.integration.unipile import list_chat_messages, get_unipile_client

# Using the convenience function
async def get_messages():
    chat_id = "your_chat_id_here"
    response = await list_chat_messages(chat_id=chat_id, limit=50)
    for message in response.items:
        sender = "You" if message.is_sender == 1 else message.sender_id
        print(f"{sender}: {message.text or '[attachment]'}")

# Using the client directly for more control
async def get_messages_advanced():
    client = get_unipile_client()
    chat_id = "your_chat_id_here"
    response = await client.list_chat_messages(
        chat_id=chat_id,
        limit=100,
        sender_id="specific_sender_id"
    )
    return response

# Pagination example
async def get_all_messages(chat_id: str):
    all_messages = []
    cursor = None
    
    while True:
        response = await list_chat_messages(
            chat_id=chat_id,
            cursor=cursor,
            limit=250
        )
        all_messages.extend(response.items)
        
        if not response.cursor:
            break
        cursor = response.cursor
    
    return all_messages
```

---

## Sending Messages

### Option 1: Using the API Endpoint

Send a message to a chat with optional attachments:

```
POST /api/unipile/chats/{chat_id}/messages
Content-Type: multipart/form-data
```

#### Path Parameters:

- `chat_id` (string, required): The id of the chat where to send the message

#### Form Data Parameters:

- `text` (string, optional): The message text
- `account_id` (string, optional): An account_id can be specified to prevent the user from sending messages in chats not belonging to the account
- `thread_id` (string, optional): Optional and for Slack's messaging only. The id of the thread to send the message in
- `quote_id` (string, optional): The id of a message to quote/reply to
- `voice_message` (file, optional): A file to send as voice message (WhatsApp & LinkedIn). We recommend usage of .m4a format for LinkedIn. For Instagram and Telegram you need to use attachment field
- `video_message` (file, optional): A file to send as video message (LinkedIn)
- `attachments` (array of files, optional): List of files to attach
- `typing_duration` (string, optional): (WhatsApp only) Set a duration in milliseconds to simulate a typing status for that duration before sending the message

#### Example Requests:

```bash
# Send a simple text message
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "text=Hello, how are you?"

# Send a message with quote/reply
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "text=I agree!" \
  -F "quote_id=msg_456"

# Send a message with file attachments
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "text=Here are the files" \
  -F "attachments=@document.pdf" \
  -F "attachments=@image.jpg"

# Send a voice message (WhatsApp/LinkedIn)
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "voice_message=@voice_note.m4a"

# Send a video message (LinkedIn)
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "text=Check this out!" \
  -F "video_message=@video.mp4"

# Send to Slack thread
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "text=Reply to thread" \
  -F "thread_id=slack_thread_123"

# Send with typing simulation (WhatsApp)
curl -X POST http://localhost:8000/api/unipile/chats/abc123/messages \
  -F "text=Hello!" \
  -F "typing_duration=3000"
```

#### Response Format (201 Created):

```json
{
  "object": "MessageSent",
  "message_id": "msg_789"
}
```

### Option 2: Using the Python Client Directly

You can also use the Unipile client directly in your Python code:

```python
from app.integration.unipile import send_message, get_unipile_client

# Send a simple text message
async def send_text_message():
    response = await send_message(
        chat_id="abc123",
        text="Hello, how are you?"
    )
    print(f"Message sent: {response.message_id}")

# Send a message with quote/reply
async def send_reply():
    response = await send_message(
        chat_id="abc123",
        text="I agree!",
        quote_id="msg_456"
    )
    print(f"Reply sent: {response.message_id}")

# Send a message with attachments
async def send_with_attachments():
    with open("document.pdf", "rb") as f1, open("image.jpg", "rb") as f2:
        attachments = [
            ("document.pdf", f1, "application/pdf"),
            ("image.jpg", f2, "image/jpeg"),
        ]
        response = await send_message(
            chat_id="abc123",
            text="Here are the files",
            attachments=attachments
        )
        print(f"Message sent: {response.message_id}")

# Send a voice message (WhatsApp/LinkedIn)
async def send_voice():
    with open("voice_note.m4a", "rb") as f:
        voice_msg = ("voice_note.m4a", f, "audio/m4a")
        response = await send_message(
            chat_id="abc123",
            voice_message=voice_msg
        )
        print(f"Voice message sent: {response.message_id}")

# Send with typing simulation (WhatsApp)
async def send_with_typing():
    response = await send_message(
        chat_id="abc123",
        text="Hello!",
        typing_duration="3000"  # 3 seconds
    )
    print(f"Message sent: {response.message_id}")

# Using the client directly for more control
async def send_message_advanced():
    client = get_unipile_client()
    response = await client.send_message(
        chat_id="abc123",
        text="Message sent using client directly."
    )
    return response
```

### Error Responses

The endpoint may return the following error responses:

- **401 Unauthorized**: Disconnected account
- **403 Forbidden**: Feature not subscribed
- **404 Not Found**: Account, chat or thread not found
- **415 Unsupported Media Type**: The media has been rejected by the provider
- **422 Unprocessable Entity**: Message couldn't pass validation
- **429 Too Many Requests**: The provider cannot accept any more requests at the moment
- **500 Internal Server Error**: Unexpected error or provider error
- **503 Service Unavailable**: Network down on server side
- **504 Gateway Timeout**: Request timed out

## Data Model

### Chat Fields

The integration returns simplified chat objects with only the essential fields:

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always "Chat" |
| `id` | string | Unique chat identifier |
| `account_id` | string | Account identifier |
| `account_type` | string | Platform type (WHATSAPP, LINKEDIN, etc.) |
| `provider_id` | string | Provider-specific identifier |
| `name` | string or null | Chat name or contact name |
| `timestamp` | string or null | Last message timestamp (ISO 8601) |
| `unread_count` | integer | Number of unread messages |
| `unread` | boolean | Whether chat has unread messages (derived from unread_count) |

### Message Fields

The message objects contain the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always "Message" |
| `id` | string | Unique message identifier |
| `account_id` | string | Account identifier |
| `chat_id` | string | Chat identifier |
| `chat_provider_id` | string | Provider-specific chat identifier |
| `provider_id` | string | Provider-specific message identifier |
| `sender_id` | string | Sender identifier |
| `sender_attendee_id` | string | Sender attendee identifier |
| `text` | string or null | Message text content |
| `timestamp` | string | Message timestamp (ISO 8601) |
| `is_sender` | integer | 0 = received, 1 = sent |
| `attachments` | array | List of attachment objects (images, videos, files, etc.) |
| `reactions` | array | List of reaction objects |
| `seen` | integer | 0 = not seen, 1 = seen |
| `seen_by` | object | Dictionary of users who have seen the message |
| `hidden` | integer | 0 = visible, 1 = hidden |
| `deleted` | integer | 0 = not deleted, 1 = deleted |
| `edited` | integer | 0 = not edited, 1 = edited |
| `is_event` | integer | 0 = regular message, 1 = event message |
| `delivered` | integer | 0 = not delivered, 1 = delivered |
| `behavior` | integer or null | Message behavior type |
| `original` | string | Original message content |
| `quoted` | object or null | Quoted/replied-to message |
| `event_type` | integer or null | Event type (if is_event = 1) |
| `replies` | integer or null | Number of replies |
| `reply_by` | array or null | List of user IDs who replied |
| `parent` | string or null | Parent message ID (for threaded replies) |
| `subject` | string or null | Message subject (for email-like messages) |
| `message_type` | string or null | Type (MESSAGE, INVITATION, INMAIL, etc.) |
| `attendee_type` | string or null | Attendee type (MEMBER, ORGANIZATION, OTHER) |
| `attendee_distance` | integer or null | LinkedIn connection distance (1-4, -1) |
| `sender_urn` | string or null | LinkedIn URN |
| `reply_to` | object or null | Reply-to message reference |

### MessageSent Response

When sending a message, the API returns a MessageSent response:

| Field | Type | Description |
|-------|------|-------------|
| `object` | string | Always "MessageSent" |
| `message_id` | string or null | The Unipile ID of the newly sent message |

### Attachment Types

Messages can contain various types of attachments:

- **Image Attachment** (`type: "img"`): Images and stickers
- **Video Attachment** (`type: "video"`): Videos and GIFs
- **Audio Attachment** (`type: "audio"`): Audio files and voice notes
- **File Attachment** (`type: "file"`): Generic file attachments
- **LinkedIn Post** (`type: "linkedin_post"`): LinkedIn post references
- **Video Meeting** (`type: "video_meeting"`): Video meeting links

Each attachment type has common fields:
- `id`: Attachment identifier
- `type`: Attachment type
- `unavailable`: Whether the attachment is available
- `file_size`: Size in bytes (optional)
- `mimetype`: MIME type (optional)
- `url`: Download URL (optional)
- `url_expires_at`: URL expiration timestamp (optional)

And type-specific fields (e.g., `width`/`height` for images/videos, `file_name` for files, `duration` for audio, etc.).

## Error Handling

The integration handles various error scenarios:

- **Configuration errors**: Missing `UNIPILE_DSN` or `UNIPILE_API_KEY`
- **Network errors**: Connection issues, timeouts
- **API errors**: 401 Unauthorized, 403 Forbidden, 500 Internal Server Error, etc.

All errors are properly propagated with meaningful error messages.

## Installation

The integration requires `httpx` for making HTTP requests. Install it by running:

```bash
uv sync
```

This will install all dependencies from `pyproject.toml`, including `httpx>=0.27.0`.

## Testing

To test the integration:

1. Ensure your `.env` file has valid Unipile credentials
2. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Visit `http://localhost:8000/docs` to see the interactive API documentation
4. Try the `/api/unipile/chats` endpoint with different parameters

## Advanced Features

### Pagination

The API supports cursor-based pagination. To get all chats:

```python
async def get_all_chats():
    all_chats = []
    cursor = None
    
    while True:
        response = await list_all_chats(cursor=cursor, limit=250)
        all_chats.extend(response.items)
        
        if not response.cursor:
            break
        cursor = response.cursor
    
    return all_chats
```

### Filtering by Multiple Accounts

You can filter by multiple account IDs using a comma-separated list:

```python
response = await list_all_chats(account_id="acc_123,acc_456,acc_789")
```

### Date Filtering

Filter chats by creation date using ISO 8601 format:

```python
# Get chats created after a specific date
response = await list_all_chats(after="2025-11-01T00:00:00.000Z")

# Get chats created in a specific date range
response = await list_all_chats(
    after="2025-11-01T00:00:00.000Z",
    before="2025-11-30T23:59:59.999Z"
)
```

