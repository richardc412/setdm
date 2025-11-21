# Persistence Layer Architecture

Visual overview of the PostgreSQL persistence layer implementation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│                         (app/main.py)                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Lifespan Event Handler (Startup)                 │  │
│  │  1. Initialize database tables                            │  │
│  │  2. Sync all chats from Unipile                          │  │
│  │  3. Sync messages for each chat (incremental)            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
│   API Layer  │    │  Sync Service    │   │  Database    │
│   (router)   │    │  (message_sync)  │   │  (SQLAlchemy)│
└──────────────┘    └──────────────────┘   └──────────────┘
        │                     │                     │
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │ CRUD Layer   │    │  Unipile     │
            │ (db/crud.py) │    │  Client      │
            └──────────────┘    └──────────────┘
                    │                   │
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │ PostgreSQL   │    │  Unipile API │
            │   Database   │    │  (External)  │
            └──────────────┘    └──────────────┘
```

## Request Flow

### 1. Startup Sync Flow

```
Application Startup
       │
       ├─► init_db()
       │   └─► Create tables if not exist
       │
       └─► sync_all_chat_messages()
           │
           ├─► sync_all_chats()
           │   ├─► UnipileClient.list_all_chats()
           │   │   └─► GET /api/v1/chats
           │   │
           │   └─► For each chat:
           │       ├─► get_or_create_chat()
           │       │   └─► INSERT or UPDATE in DB
           │       │
           │       └─► Check if needs message sync:
           │           ├─► New chat? → No (skip on startup)
           │           ├─► Timestamp changed? → Yes (sync!)
           │           └─► Otherwise → No (skip)
           │
           └─► For chats that need sync only:
               └─► sync_chat_messages()
                   ├─► get_latest_message_timestamp()
                   │   └─► SELECT MAX(timestamp) FROM messages
                   │
                   ├─► UnipileClient.list_chat_messages(after=timestamp)
                   │   └─► GET /api/v1/chats/{id}/messages?after=X
                   │
                   ├─► For each message:
                   │   └─► create_message()
                   │       └─► Check if provider_id exists
                   │           ├─► Exists: Skip (dedupe)
                   │           └─► New: INSERT into DB
                   │
                   └─► If new messages from others:
                       └─► mark_chat_as_unread()

       ⚡ Optimization: Chats with no changes are skipped!
```

### 2. API Request Flow (Get Chats)

```
GET /api/chats?is_read=false
       │
       ├─► router.list_chats()
       │   └─► get_all_chats(is_read=False)
       │       └─► SELECT * FROM chats WHERE is_read=false
       │
       └─► Return ChatListResponse
           └─► [ChatResponse, ...]
```

### 3. API Request Flow (Get Messages)

```
GET /api/chats/{chat_id}/messages
       │
       ├─► router.list_chat_messages()
       │   ├─► get_chat_by_id()
       │   │   └─► SELECT * FROM chats WHERE id=X
       │   │
       │   ├─► get_messages_by_chat()
       │   │   └─► SELECT * FROM messages WHERE chat_id=X
       │   │       ORDER BY timestamp DESC LIMIT Y OFFSET Z
       │   │
       │   └─► get_message_count_by_chat()
       │       └─► SELECT COUNT(*) FROM messages WHERE chat_id=X
       │
       └─► Return MessageListResponse
           └─► {items: [...], total: N}
```

### 4. API Request Flow (Manual Sync)

```
POST /api/chats/{chat_id}/sync
       │
       ├─► router.sync_chat()
       │   └─► sync_chat_messages(chat_id, full_sync=False)
       │       └─► [Same as startup sync for single chat]
       │
       └─► Return SyncResponse
           └─► {success: true, stats: {...}}
```

## Database Schema

```
┌─────────────────────────────────────────────────────────┐
│                      chats                               │
├─────────────────────────────────────────────────────────┤
│ id (PK)                      STRING                      │
│ account_id                   STRING     [indexed]        │
│ account_type                 STRING                      │
│ provider_id (UNIQUE)         STRING     [indexed]        │
│ name                         STRING                      │
│ timestamp                    STRING                      │
│ unread_count                 INTEGER                     │
│ is_read                      BOOLEAN    [indexed]        │
│ created_at                   DATETIME                    │
│ updated_at                   DATETIME                    │
└─────────────────────────────────────────────────────────┘
                               │
                               │ 1:N
                               │
┌─────────────────────────────────────────────────────────┐
│                     messages                             │
├─────────────────────────────────────────────────────────┤
│ id (PK)                      STRING                      │
│ chat_id (FK)                 STRING     [indexed]        │
│ account_id                   STRING     [indexed]        │
│ chat_provider_id             STRING                      │
│ provider_id (UNIQUE)         STRING     [indexed]        │
│ sender_id                    STRING                      │
│ sender_attendee_id           STRING                      │
│ text                         TEXT                        │
│ timestamp                    STRING     [indexed]        │
│ is_sender                    INTEGER    (0 or 1)         │
│ attachments                  JSON       []               │
│ reactions                    JSON       []               │
│ seen_by                      JSON       {}               │
│ quoted                       JSON       (optional)       │
│ reply_to                     JSON       (optional)       │
│ seen, hidden, deleted...     INTEGER    flags            │
│ created_at                   DATETIME                    │
└─────────────────────────────────────────────────────────┘

Indexes:
- idx_messages_chat_timestamp: (chat_id, timestamp)
- idx_chats_account_updated: (account_id, updated_at)
```

## Data Flow

### Message Deduplication

```
New message from Unipile
       │
       ├─► create_message(message_data)
       │   │
       │   ├─► SELECT * FROM messages WHERE provider_id = X
       │   │
       │   ├─► If exists:
       │   │   └─► Return None (skip)
       │   │
       │   └─► If not exists:
       │       └─► INSERT INTO messages
       │           └─► Return MessageModel
       │
       └─► Continue processing
```

### Read/Unread Tracking

```
Sync discovers new messages
       │
       ├─► For each new message:
       │   │
       │   ├─► Check is_sender field
       │   │
       │   ├─► If is_sender == 0 (received):
       │   │   └─► Mark has_new_unread = True
       │   │
       │   └─► If is_sender == 1 (sent):
       │       └─► No action
       │
       └─► After all messages:
           │
           └─► If has_new_unread:
               └─► mark_chat_as_unread()
                   └─► UPDATE chats SET is_read=false
```

### Incremental Sync Strategy

```
First Sync (no messages in DB):
┌────────────────────────────────────────────┐
│ Unipile: [msg1, msg2, msg3, ..., msg100]  │
│     ↓                                      │
│ DB: Store all 100 messages                 │
│ Last timestamp: 2025-11-21T10:30:00Z       │
└────────────────────────────────────────────┘

Second Sync (incremental):
┌────────────────────────────────────────────┐
│ Get last timestamp: 2025-11-21T10:30:00Z   │
│     ↓                                      │
│ Unipile.list_messages(after="2025-11...")  │
│     ↓                                      │
│ Unipile: [msg101, msg102] (only new)      │
│     ↓                                      │
│ DB: Store 2 new messages                   │
│ Last timestamp: 2025-11-21T11:45:00Z       │
└────────────────────────────────────────────┘
```

## Module Dependencies

```
┌──────────────────────────────────────────────────────────┐
│                     app/main.py                          │
│  - FastAPI app initialization                            │
│  - CORS configuration                                    │
│  - Lifespan event handlers                              │
│  - Router registration                                   │
└──────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌────────────────┐
│ app/features │  │ app/services/   │  │ app/db/        │
│ /chats/      │  │ message_sync.py │  │                │
│ router.py    │  │                 │  │ base.py        │
│ schemas.py   │  │ - sync_all_chats│  │ models.py      │
│              │  │ - sync_messages │  │ crud.py        │
└──────────────┘  └─────────────────┘  └────────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼
┌──────────────────┐              ┌────────────────────┐
│ app/integration/ │              │ app/core/          │
│ unipile/         │              │ config.py          │
│ client.py        │              │                    │
│ schemas.py       │              │ - Settings         │
└──────────────────┘              │ - get_settings()   │
                                  └────────────────────┘
```

## API Endpoints Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    /api/chats                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GET  /                    List all chats                   │
│       ?is_read=bool        Filter by read status            │
│       &account_id=str      Filter by account                │
│       &limit=int           Pagination limit                 │
│       &offset=int          Pagination offset                │
│                                                              │
│  GET  /{chat_id}           Get single chat details          │
│                                                              │
│  GET  /{chat_id}/messages  Get messages for chat            │
│       ?limit=int           Pagination limit                 │
│       &offset=int          Pagination offset                │
│       &order_desc=bool     Sort order (newest first)        │
│                                                              │
│  POST /{chat_id}/mark-read Mark chat as read                │
│                                                              │
│  POST /{chat_id}/sync      Sync messages for chat           │
│       ?full_sync=bool      Full or incremental              │
│                                                              │
│  POST /sync                Sync all chats and messages      │
│       ?account_id=str      Filter by account                │
│       &full_sync=bool      Full or incremental              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Dependency Injection

```python
async def list_chats(db: AsyncSession = Depends(get_db)):
    # db session automatically managed
    chats = await get_all_chats(db)
    return chats
```

### 2. Repository Pattern (CRUD)

```python
# High-level operations in router
chats = await get_all_chats(db, is_read=False)

# Low-level SQL in crud.py
async def get_all_chats(...):
    query = select(ChatModel).where(...)
    return await db.execute(query)
```

### 3. Service Layer

```python
# Business logic in services/message_sync.py
async def sync_chat_messages(db, chat_id, full_sync):
    # 1. Get last timestamp
    # 2. Fetch from Unipile
    # 3. Dedupe and store
    # 4. Update read status
    return stats
```

### 4. Async Context Manager (DB Session)

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## Error Handling Strategy

```
┌────────────────────────────────────────────────┐
│           Error Handling Levels                 │
├────────────────────────────────────────────────┤
│                                                 │
│  1. Router Level (router.py)                   │
│     - Catch all exceptions                     │
│     - Return HTTPException with status codes   │
│     - Log errors                               │
│                                                 │
│  2. Service Level (message_sync.py)            │
│     - Try-catch around API calls               │
│     - Continue processing other chats on error │
│     - Track errors in stats                    │
│     - Log detailed error messages              │
│                                                 │
│  3. CRUD Level (crud.py)                       │
│     - Database constraint handling             │
│     - Return None for not found                │
│     - Let SQLAlchemy raise for serious errors  │
│                                                 │
│  4. Startup Level (main.py)                    │
│     - Continue app startup if sync fails       │
│     - Log warning                              │
│     - App remains operational                  │
│                                                 │
└────────────────────────────────────────────────┘
```

## Performance Optimizations

1. **Database Indexes**

   - `chat_id + timestamp` for message queries
   - `account_id + updated_at` for chat filtering
   - `provider_id` unique index for deduplication
   - `is_read` for filtering unread chats

2. **Async Operations**

   - Non-blocking database queries
   - Concurrent HTTP requests possible
   - Efficient resource utilization

3. **Incremental Sync**

   - Only fetch new messages after last timestamp
   - Minimizes API calls and data transfer
   - Faster sync times after initial sync

4. **Pagination**

   - Limit/offset for large result sets
   - Cursor-based pagination from Unipile
   - Prevents memory issues with large datasets

5. **Connection Pooling**
   - SQLAlchemy connection pool
   - Reuse database connections
   - Better performance under load

## Security Considerations

- **SQL Injection**: Prevented by SQLAlchemy ORM
- **Input Validation**: Pydantic schemas validate all inputs
- **Environment Variables**: Sensitive data not hardcoded
- **Database Credentials**: Stored in .env (git-ignored)
- **Future**: Add authentication middleware to protect endpoints

---

**Note**: This architecture is designed to be:

- **Scalable**: Can add webhooks, caching, message queues
- **Maintainable**: Clear separation of concerns
- **Testable**: Each layer can be tested independently
- **Extensible**: Easy to add new features
