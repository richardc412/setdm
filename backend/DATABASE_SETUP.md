# Database Setup Guide

This guide explains how to set up and use the PostgreSQL persistence layer for Instagram messages.

## Overview

The application uses PostgreSQL with SQLAlchemy (async) to store:

- **Chats**: Instagram conversation metadata
- **Messages**: Individual messages within each chat

Messages are automatically synced from Unipile on application startup and can be manually synced via API endpoints.

## Prerequisites

1. **PostgreSQL 12+** installed and running
2. **Python dependencies** installed (see Installation section)

## Installation

### 1. Install PostgreSQL

**macOS (using Homebrew):**

```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database

Connect to PostgreSQL and create a database:

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE setdm_db;
CREATE USER setdm_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE setdm_db TO setdm_user;

# Exit psql
\q
```

### 3. Install Python Dependencies

From the backend directory:

```bash
uv sync
```

This will install:

- `sqlalchemy>=2.0.0` - ORM for database operations
- `asyncpg>=0.29.0` - Async PostgreSQL driver
- `alembic>=1.13.0` - Database migrations (for future use)
- `greenlet>=3.0.0` - Required by SQLAlchemy for async operations

### 4. Configure Environment Variables

Create a `.env` file in the `backend/` directory (copy from `ENV.example`):

```bash
cp ENV.example .env
```

Edit `.env` and set your database connection:

```env
DATABASE_URL=postgresql+asyncpg://setdm_user:your_secure_password@localhost:5432/setdm
DEBUG=true  # Set to false in production
```

## Database Schema

### ChatModel Table (`chats`)

Stores Instagram chat/conversation metadata:

| Column         | Type            | Description                       |
| -------------- | --------------- | --------------------------------- |
| `id`           | String (PK)     | Chat ID from Unipile              |
| `account_id`   | String          | Account that owns this chat       |
| `account_type` | String          | Provider type (e.g., "INSTAGRAM") |
| `provider_id`  | String (Unique) | Chat ID from provider             |
| `name`         | String          | Chat/contact name                 |
| `timestamp`    | String          | Last message timestamp (ISO 8601) |
| `unread_count` | Integer         | Unread message count from Unipile |
| `is_read`      | Boolean         | Local read/unread tracking        |
| `created_at`   | DateTime        | When chat was first synced        |
| `updated_at`   | DateTime        | Last update timestamp             |

### MessageModel Table (`messages`)

Stores individual messages:

| Column                                             | Type            | Description                                  |
| -------------------------------------------------- | --------------- | -------------------------------------------- |
| `id`                                               | String (PK)     | Message ID from Unipile                      |
| `chat_id`                                          | String (FK)     | References `chats.id`                        |
| `provider_id`                                      | String (Unique) | Message ID from provider (for deduplication) |
| `sender_id`                                        | String          | Sender's user ID                             |
| `text`                                             | Text            | Message text content                         |
| `timestamp`                                        | String          | Message timestamp (ISO 8601)                 |
| `is_sender`                                        | Integer         | 1 if current user sent, 0 if received        |
| `attachments`                                      | JSON            | Array of attachment objects                  |
| `reactions`                                        | JSON            | Array of reaction objects                    |
| `seen`, `hidden`, `deleted`, `edited`, `delivered` | Integer         | Message flags (0 or 1)                       |
| ...                                                | ...             | Additional Unipile fields                    |

## How It Works

### Startup Sync

When the application starts (`main.py` lifespan event):

1. **Initialize Database**: Creates tables if they don't exist
2. **Sync All Chats**: Fetches chat list from Unipile, creates/updates in DB
3. **Smart Message Sync**: Only syncs messages for chats that:
   - Have a newer timestamp (new messages)
   - Are new chats (first sync)
   - Have no messages in DB yet
4. **Mark Unread**: If new messages are from others (not the current user), marks chat as unread

**Optimization**: Chats with unchanged timestamps are skipped, minimizing API calls!

### Incremental Syncing

The system uses **incremental syncing** to minimize API calls:

- On first run: Syncs all messages for all chats
- On subsequent runs: Only syncs messages created after the last stored message timestamp
- Uses the `after` parameter in Unipile API calls

### Deduplication

Messages are deduplicated using the `provider_id` field:

- Before inserting, checks if a message with that `provider_id` exists
- Skips insert if duplicate found
- Database enforces uniqueness via unique constraint

### Read/Unread Logic

- **Default**: New chats start as `is_read=True`
- **Automatic Unread**: When syncing, if any new message has `is_sender=0` (received), chat is marked `is_read=False`
- **Manual Read**: Frontend calls `POST /api/chats/{chat_id}/mark-read` when user opens chat

## API Endpoints

All endpoints are under `/api/chats`:

### Get All Chats

```http
GET /api/chats?is_read=false&limit=100&offset=0
```

**Query Parameters:**

- `is_read` (optional): Filter by read status (true/false)
- `account_id` (optional): Filter by account ID
- `limit` (default: 100): Max results
- `offset` (default: 0): Pagination offset

**Response:**

```json
{
  "items": [
    {
      "id": "chat_123",
      "account_id": "acc_456",
      "name": "John Doe",
      "timestamp": "2025-11-21T10:30:00Z",
      "is_read": false,
      "unread_count": 3,
      ...
    }
  ],
  "total": 50,
  "limit": 100,
  "offset": 0
}
```

### Get Chat Messages

```http
GET /api/chats/{chat_id}/messages?limit=50&offset=0&order_desc=true
```

**Query Parameters:**

- `limit` (default: 100): Max results
- `offset` (default: 0): Pagination offset
- `order_desc` (default: true): Newest first (true) or oldest first (false)

**Response:**

```json
{
  "items": [
    {
      "id": "msg_789",
      "chat_id": "chat_123",
      "text": "Hello!",
      "timestamp": "2025-11-21T10:30:00Z",
      "is_sender": 0,
      "attachments": [],
      ...
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Mark Chat as Read

```http
POST /api/chats/{chat_id}/mark-read
```

**Response:**

```json
{
  "id": "chat_123",
  "is_read": true,
  ...
}
```

### Sync Single Chat

```http
POST /api/chats/{chat_id}/sync?full_sync=false
```

**Query Parameters:**

- `full_sync` (default: false): If true, syncs all messages. If false, incremental sync.

**Response:**

```json
{
  "success": true,
  "message": "Successfully synced chat chat_123",
  "stats": {
    "messages_fetched": 5,
    "messages_created": 3,
    "new_unread_messages": 2,
    "latest_timestamp": "2025-11-21T10:30:00Z"
  }
}
```

### Sync All Chats

```http
POST /api/chats/sync?full_sync=false&account_id=acc_456
```

**Query Parameters:**

- `full_sync` (default: false): If true, syncs all messages
- `account_id` (optional): Filter by account ID

**Response:**

```json
{
  "success": true,
  "message": "Successfully synced all chats",
  "stats": {
    "chats_synced": 10,
    "total_messages_created": 45,
    "total_unread_messages": 12,
    "chats_with_errors": 0
  }
}
```

## Usage Examples

### Frontend Integration

**Fetch unread chats:**

```typescript
const response = await fetch("http://localhost:8000/api/chats?is_read=false");
const data = await response.json();
console.log(`You have ${data.items.length} unread chats`);
```

**Get messages for a chat:**

```typescript
const chatId = "chat_123";
const response = await fetch(
  `http://localhost:8000/api/chats/${chatId}/messages?limit=50`
);
const data = await response.json();
console.log(`Chat has ${data.total} messages`);
```

**Mark chat as read when user opens it:**

```typescript
const chatId = "chat_123";
await fetch(`http://localhost:8000/api/chats/${chatId}/mark-read`, {
  method: "POST",
});
```

**Manually trigger sync:**

```typescript
const response = await fetch("http://localhost:8000/api/chats/sync", {
  method: "POST",
});
const data = await response.json();
console.log(data.stats);
```

## Running the Application

Start the FastAPI server:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup, you'll see logs like:

```
INFO - Starting up application...
INFO - Initializing database tables...
INFO - Database tables initialized successfully
INFO - Starting message sync from Unipile...
INFO - Fetched 10 chats from Unipile
INFO - Fetched 50 messages for chat chat_123
INFO - Message sync completed successfully: {...}
```

## Troubleshooting

### Database Connection Error

**Error:** `could not connect to server: Connection refused`

**Solution:**

1. Check if PostgreSQL is running: `pg_isready`
2. Start PostgreSQL: `brew services start postgresql@15` (macOS)
3. Verify connection string in `.env`

### Tables Not Created

**Error:** `relation "chats" does not exist`

**Solution:**
The app auto-creates tables on startup. If this fails:

1. Check database permissions
2. Verify `DATABASE_URL` is correct
3. Check logs for specific errors

### Sync Fails on Startup

**Error:** `Failed to sync messages on startup`

**Solution:**

1. Check Unipile API credentials in `.env`
2. Verify Unipile DSN is accessible
3. Application will continue running, but data won't be synced

### Duplicate Key Error

**Error:** `duplicate key value violates unique constraint`

**Solution:**
This shouldn't happen due to deduplication logic. If it does:

1. Check if you're manually inserting data
2. Verify `provider_id` uniqueness
3. The CRUD functions handle this automatically

## Future Enhancements

- **Webhooks**: Add real-time sync via Unipile webhooks (already architected to support this)
- **Alembic Migrations**: Use Alembic for schema versioning and migrations
- **Message Search**: Add full-text search on message content
- **Attachment Storage**: Download and store attachments locally
- **Read Receipts**: Track message read status per recipient

## Architecture Notes

### Why PostgreSQL?

- **Relational data**: Chats have messages (one-to-many)
- **JSON support**: Store complex fields (attachments, reactions) as JSON
- **ACID compliance**: Ensure data integrity
- **Performance**: Efficient indexing for queries by timestamp, read status, etc.

### Why Async SQLAlchemy?

- **Non-blocking**: Works with FastAPI's async nature
- **Performance**: Handle multiple concurrent requests efficiently
- **Modern**: Uses SQLAlchemy 2.0 with native async support

### Sync Strategy

The sync strategy balances API efficiency with data freshness:

1. **On Boot**: Full sync ensures data is up-to-date
2. **Incremental**: Subsequent syncs use `after` timestamp to minimize API calls
3. **Manual Sync**: API endpoints allow on-demand sync for specific chats
4. **Ready for Webhooks**: Architecture supports adding webhooks for real-time updates without major refactoring

---

**Questions?** Check the code comments in:

- `app/db/base.py` - Database configuration
- `app/db/models.py` - Table definitions
- `app/db/crud.py` - Database operations
- `app/services/message_sync.py` - Sync logic
- `app/features/chats/router.py` - API endpoints
