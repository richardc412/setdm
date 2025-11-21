# Unipile Integration

This module provides integration with the Unipile API for managing chats across multiple messaging platforms (WhatsApp, LinkedIn, Slack, Twitter, Messenger, Instagram, Telegram).

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

