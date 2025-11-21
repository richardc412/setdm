# Webhook Setup Guide

This guide explains how to set up webhooks for real-time message ingestion from Unipile.

## Overview

The webhook system allows your application to receive real-time notifications when new messages arrive, instead of polling the Unipile API. When a message is received on any connected account (Instagram, WhatsApp, LinkedIn, etc.), Unipile will send a POST request to your webhook endpoint with the message data.

## Architecture

1. **Webhook Registration**: On application startup, the system automatically registers a webhook with Unipile
2. **Message Reception**: Unipile sends POST requests to your webhook endpoint when messages are received
3. **Database Storage**: The webhook endpoint processes the payload and saves messages to the database
4. **Future: SSE Push**: Messages can be pushed to the frontend via Server-Sent Events (not yet implemented)

## Configuration

### 1. Set the Webhook Base URL

Add the `WEBHOOK_BASE_URL` environment variable to your `.env` file:

```bash
# For local development with ngrok
WEBHOOK_BASE_URL=https://abc123.ngrok.io

# For production
WEBHOOK_BASE_URL=https://yourdomain.com
```

### 2. Local Development with ngrok

For local testing, you need to expose your localhost to the internet:

1. Install ngrok: https://ngrok.com/
2. Start your FastAPI server: `cd backend && uvicorn app.main:app --reload`
3. In another terminal, start ngrok: `ngrok http 8000`
4. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
5. Add it to your `.env` file as `WEBHOOK_BASE_URL`
6. Restart your application

### 3. Production Deployment

In production, set `WEBHOOK_BASE_URL` to your actual domain:

```bash
WEBHOOK_BASE_URL=https://api.yourdomain.com
```

## How It Works

### Startup Sequence

When the application starts (`main.py`):

1. Database tables are initialized
2. Webhook manager checks if a webhook already exists in Unipile
3. If no webhook exists, one is created pointing to: `{WEBHOOK_BASE_URL}/api/webhooks/unipile/messages`
4. The webhook ID is logged for reference
5. Initial message sync is performed
6. Background scheduler starts for pending message processing

### Webhook Endpoint

**Endpoint**: `POST /api/webhooks/unipile/messages`

**Triggered by**: Unipile when a `message_received` event occurs

**Process**:
1. Receives and validates the webhook payload
2. Ensures the chat exists (creates if necessary)
3. Converts webhook payload to internal Message schema
4. Saves message to database (skips if duplicate)
5. Updates chat timestamp
6. Marks chat as unread
7. Returns 200 OK to acknowledge receipt

### Webhook Payload Example

```json
{
  "account_id": "acc_123",
  "account_type": "INSTAGRAM",
  "chat_id": "chat_456",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "message_id": "msg_789",
  "message": "Hello, this is a test message",
  "sender": {
    "id": "user_123",
    "provider_id": "instagram_user_123",
    "name": "John Doe",
    "picture_url": "https://..."
  },
  "provider_chat_id": "instagram_chat_456",
  "provider_message_id": "instagram_msg_789",
  "attachments": [],
  "is_event": 0
}
```

## Webhook Configuration

The webhook is configured with the following settings:

- **Source**: `messaging`
- **Events**: `["message_received"]`
- **Format**: `json`
- **Enabled**: `true`
- **Account IDs**: All accounts (not filtered)

## Monitoring

Check the application logs for webhook-related messages:

```bash
# Successful webhook creation
INFO - Webhook created successfully: ID=webhook_abc123

# Webhook already exists
INFO - Webhook already exists: ID=webhook_abc123, URL=https://..., enabled=True

# Webhook message received
INFO - Received webhook payload: {...}
INFO - Successfully processed webhook message: msg_789
INFO - Created new message from webhook: msg_789
INFO - Updated chat chat_456 with new message
```

## Troubleshooting

### Webhook Not Created

**Symptom**: Log shows "WEBHOOK_BASE_URL is not configured"

**Solution**: Set `WEBHOOK_BASE_URL` in your `.env` file and restart the application

### Webhook Messages Not Received

**Symptom**: Messages appear in Unipile but not in your database

**Possible causes**:
1. `WEBHOOK_BASE_URL` is not publicly accessible
2. Firewall blocking incoming requests
3. ngrok tunnel expired (for local dev)
4. Webhook was deleted from Unipile dashboard

**Solution**:
1. Verify `WEBHOOK_BASE_URL` is correct and accessible from the internet
2. Check firewall settings
3. Restart ngrok and update `.env` if using local development
4. Check Unipile dashboard to verify webhook exists

### Duplicate Messages

**Symptom**: Same message appears multiple times

**Solution**: The system automatically prevents duplicates using the message's unique `provider_id`. If you see duplicates, check database constraints.

## Manual Webhook Management

The webhook is automatically managed on startup, but you can also manage it via the Unipile dashboard:

1. Go to https://app.unipile.com
2. Navigate to Webhooks section
3. View, edit, or delete webhooks

## Testing

To test the webhook:

1. Ensure your application is running with `WEBHOOK_BASE_URL` configured
2. Send a message to one of your connected accounts (Instagram, WhatsApp, etc.)
3. Check application logs for webhook processing messages
4. Verify the message appears in your database
5. Check the frontend to see if the message appears in the chat

## Future: SSE Implementation

The webhook infrastructure is designed to support Server-Sent Events (SSE) for pushing messages to the frontend in real-time. This will be implemented in a future update.

**Planned flow**:
1. Webhook receives message
2. Message saved to database
3. SSE broadcaster notifies all connected clients
4. Frontend receives and displays new message instantly

## API Reference

### Webhook Manager Functions

Located in `app/services/webhook_manager.py`:

- `ensure_webhook_exists()`: Creates webhook if it doesn't exist
- `list_webhooks()`: List all configured webhooks
- `delete_webhook(webhook_id)`: Delete a specific webhook

### Webhook Schemas

Located in `app/integration/unipile/schemas.py`:

- `WebhookCreateRequest`: Request to create a webhook
- `WebhookCreatedResponse`: Response after creating a webhook
- `WebhookMessagePayload`: Incoming webhook data structure
- `WebhookListResponse`: Response when listing webhooks

## Security Considerations

1. The webhook endpoint returns 200 OK for all requests (even errors) to prevent Unipile from retrying
2. Payloads are validated against Pydantic schemas
3. Database operations use existing CRUD functions with proper error handling
4. Future: Consider adding webhook signature verification for production

## Additional Resources

- Unipile Webhook Documentation: https://docs.unipile.com/webhooks
- Unipile Dashboard: https://app.unipile.com
- ngrok Documentation: https://ngrok.com/docs

