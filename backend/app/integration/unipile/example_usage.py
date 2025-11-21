"""
Example usage of the Unipile integration.

This file demonstrates how to use the Unipile client in various scenarios.
"""

from .client import list_all_chats, list_chat_messages, send_message, get_unipile_client


async def example_get_all_chats():
    """Get all chats without any filters."""
    response = await list_all_chats()
    print(f"Total chats: {len(response.items)}")
    for chat in response.items:
        print(f"- {chat.name} ({chat.account_type}): {chat.unread_count} unread")


async def example_get_unread_chats():
    """Get only unread chats."""
    response = await list_all_chats(unread=True, limit=50)
    print(f"Unread chats: {len(response.items)}")
    for chat in response.items:
        print(f"- {chat.name}: {chat.unread_count} unread messages")


async def example_get_linkedin_chats():
    """Get chats from LinkedIn only."""
    response = await list_all_chats(account_type="LINKEDIN")
    print(f"LinkedIn chats: {len(response.items)}")
    for chat in response.items:
        print(f"- {chat.name}: Last message at {chat.timestamp}")


async def example_pagination():
    """Demonstrate pagination to get all chats."""
    all_chats = []
    cursor = None
    page = 1

    while True:
        print(f"Fetching page {page}...")
        response = await list_all_chats(cursor=cursor, limit=100)
        all_chats.extend(response.items)

        if not response.cursor:
            break

        cursor = response.cursor
        page += 1

    print(f"Total chats fetched: {len(all_chats)}")
    return all_chats


async def example_date_filtering():
    """Filter chats by date range."""
    response = await list_all_chats(
        after="2025-11-01T00:00:00.000Z",
        before="2025-11-30T23:59:59.999Z",
    )
    print(f"Chats in November 2025: {len(response.items)}")


async def example_multiple_accounts():
    """Filter by multiple account IDs."""
    account_ids = "acc_123,acc_456,acc_789"
    response = await list_all_chats(account_id=account_ids)
    print(f"Chats from specified accounts: {len(response.items)}")


async def example_using_client_directly():
    """Use the UnipileClient directly for more control."""
    client = get_unipile_client()

    # Get unread LinkedIn chats
    response = await client.list_all_chats(
        account_type="LINKEDIN",
        unread=True,
        limit=25,
    )

    print(f"Unread LinkedIn chats: {len(response.items)}")
    for chat in response.items:
        print(f"- {chat.name}: {chat.unread_count} unread")


async def example_error_handling():
    """Demonstrate error handling."""
    try:
        response = await list_all_chats(limit=500)  # Invalid: limit > 250
    except Exception as e:
        print(f"Error: {e}")

    try:
        # This will fail if credentials are not set
        client = get_unipile_client()
        await client.list_all_chats()
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"API error: {e}")


# ============================================================================
# MESSAGE EXAMPLES
# ============================================================================


async def example_get_all_messages_from_chat():
    """Get all messages from a specific chat."""
    chat_id = "your_chat_id_here"
    response = await list_chat_messages(chat_id=chat_id)
    print(f"Total messages: {len(response.items)}")
    for message in response.items:
        sender = "You" if message.is_sender == 1 else message.sender_id
        print(f"- {sender}: {message.text or '[attachment]'}")


async def example_get_recent_messages():
    """Get recent messages with a limit."""
    chat_id = "your_chat_id_here"
    response = await list_chat_messages(chat_id=chat_id, limit=50)
    print(f"Recent messages: {len(response.items)}")
    for message in response.items:
        print(f"- [{message.timestamp}] {message.text or '[no text]'}")


async def example_filter_messages_by_sender():
    """Get messages from a specific sender in a chat."""
    chat_id = "your_chat_id_here"
    sender_id = "sender_id_here"
    response = await list_chat_messages(chat_id=chat_id, sender_id=sender_id)
    print(f"Messages from {sender_id}: {len(response.items)}")
    for message in response.items:
        print(f"- {message.text}")


async def example_message_pagination():
    """Demonstrate pagination to get all messages from a chat."""
    chat_id = "your_chat_id_here"
    all_messages = []
    cursor = None
    page = 1

    while True:
        print(f"Fetching page {page}...")
        response = await list_chat_messages(chat_id=chat_id, cursor=cursor, limit=100)
        all_messages.extend(response.items)

        if not response.cursor:
            break

        cursor = response.cursor
        page += 1

    print(f"Total messages fetched: {len(all_messages)}")
    return all_messages


async def example_messages_date_filtering():
    """Filter messages by date range."""
    chat_id = "your_chat_id_here"
    response = await list_chat_messages(
        chat_id=chat_id,
        after="2025-11-01T00:00:00.000Z",
        before="2025-11-30T23:59:59.999Z",
    )
    print(f"Messages in November 2025: {len(response.items)}")


async def example_process_message_attachments():
    """Process messages with attachments."""
    chat_id = "your_chat_id_here"
    response = await list_chat_messages(chat_id=chat_id)

    for message in response.items:
        if message.attachments:
            print(f"Message {message.id} has {len(message.attachments)} attachment(s)")
            for attachment in message.attachments:
                if isinstance(attachment, dict):
                    att_type = attachment.get("type", "unknown")
                    print(f"  - {att_type} attachment")


async def example_get_messages_with_reactions():
    """Get messages and display their reactions."""
    chat_id = "your_chat_id_here"
    response = await list_chat_messages(chat_id=chat_id)

    for message in response.items:
        if message.reactions:
            reactions_str = ", ".join([r.value for r in message.reactions])
            print(f"{message.text or '[no text]'} - Reactions: {reactions_str}")


async def example_using_client_for_messages():
    """Use the UnipileClient directly to get messages."""
    client = get_unipile_client()
    chat_id = "your_chat_id_here"

    # Get recent messages with limit
    response = await client.list_chat_messages(
        chat_id=chat_id,
        limit=25,
    )

    print(f"Recent 25 messages: {len(response.items)}")
    for message in response.items:
        sender = "You" if message.is_sender == 1 else "Other"
        print(f"- [{sender}] {message.text or '[attachment]'}")


# ============================================================================
# SEND MESSAGE EXAMPLES
# ============================================================================


async def example_send_simple_text_message():
    """Send a simple text message to a chat."""
    chat_id = "your_chat_id_here"
    response = await send_message(
        chat_id=chat_id,
        text="Hello! This is a test message."
    )
    print(f"Message sent successfully. Message ID: {response.message_id}")


async def example_send_message_with_quote():
    """Send a message that quotes/replies to another message."""
    chat_id = "your_chat_id_here"
    message_to_quote_id = "message_id_to_quote"
    
    response = await send_message(
        chat_id=chat_id,
        text="I agree with this!",
        quote_id=message_to_quote_id
    )
    print(f"Reply sent. Message ID: {response.message_id}")


async def example_send_message_with_attachments():
    """Send a message with file attachments."""
    chat_id = "your_chat_id_here"
    
    # Open files and send
    with open("document.pdf", "rb") as f1, open("image.jpg", "rb") as f2:
        attachments = [
            ("document.pdf", f1, "application/pdf"),
            ("image.jpg", f2, "image/jpeg"),
        ]
        
        response = await send_message(
            chat_id=chat_id,
            text="Here are the files you requested.",
            attachments=attachments
        )
        print(f"Message with attachments sent. Message ID: {response.message_id}")


async def example_send_voice_message():
    """Send a voice message (WhatsApp & LinkedIn)."""
    chat_id = "your_chat_id_here"
    
    with open("voice_note.m4a", "rb") as f:
        voice_msg = ("voice_note.m4a", f, "audio/m4a")
        
        response = await send_message(
            chat_id=chat_id,
            voice_message=voice_msg
        )
        print(f"Voice message sent. Message ID: {response.message_id}")


async def example_send_video_message():
    """Send a video message (LinkedIn)."""
    chat_id = "your_chat_id_here"
    
    with open("video.mp4", "rb") as f:
        video_msg = ("video.mp4", f, "video/mp4")
        
        response = await send_message(
            chat_id=chat_id,
            text="Check out this video!",
            video_message=video_msg
        )
        print(f"Video message sent. Message ID: {response.message_id}")


async def example_send_whatsapp_with_typing():
    """Send a WhatsApp message with typing simulation."""
    chat_id = "your_chat_id_here"
    
    response = await send_message(
        chat_id=chat_id,
        text="This message will appear after typing simulation.",
        typing_duration="3000"  # 3 seconds
    )
    print(f"Message sent with typing simulation. Message ID: {response.message_id}")


async def example_send_message_to_slack_thread():
    """Send a message to a Slack thread."""
    chat_id = "your_chat_id_here"
    thread_id = "slack_thread_id"
    
    response = await send_message(
        chat_id=chat_id,
        text="Reply to the thread!",
        thread_id=thread_id
    )
    print(f"Message sent to Slack thread. Message ID: {response.message_id}")


async def example_send_with_account_restriction():
    """Send a message with account_id restriction."""
    chat_id = "your_chat_id_here"
    account_id = "your_account_id"
    
    response = await send_message(
        chat_id=chat_id,
        text="This message is sent with account restriction.",
        account_id=account_id
    )
    print(f"Message sent. Message ID: {response.message_id}")


async def example_using_client_to_send_message():
    """Use the UnipileClient directly to send a message."""
    client = get_unipile_client()
    chat_id = "your_chat_id_here"
    
    response = await client.send_message(
        chat_id=chat_id,
        text="Message sent using client directly."
    )
    
    print(f"Message sent. Message ID: {response.message_id}")


async def example_send_message_error_handling():
    """Demonstrate error handling when sending messages."""
    chat_id = "invalid_chat_id"
    
    try:
        response = await send_message(
            chat_id=chat_id,
            text="This will likely fail."
        )
        print(f"Message sent: {response.message_id}")
    except Exception as e:
        print(f"Failed to send message: {e}")


# Example of how to use in a FastAPI route
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.integration.unipile import list_all_chats, list_chat_messages, send_message

router = APIRouter()

@router.get("/my-unread-chats")
async def get_my_unread_chats():
    try:
        response = await list_all_chats(unread=True, limit=50)
        return {
            "total": len(response.items),
            "chats": response.items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/{chat_id}/messages")
async def get_messages(chat_id: str, limit: int = 50):
    try:
        response = await list_chat_messages(chat_id=chat_id, limit=limit)
        return {
            "total": len(response.items),
            "messages": response.items,
            "cursor": response.cursor
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/{chat_id}/send")
async def send_chat_message(
    chat_id: str,
    text: str = Form(...),
    attachments: list[UploadFile] = File(None)
):
    try:
        attachment_tuples = None
        if attachments:
            attachment_tuples = [
                (att.filename, att.file, att.content_type)
                for att in attachments
            ]
        
        response = await send_message(
            chat_id=chat_id,
            text=text,
            attachments=attachment_tuples
        )
        return {
            "success": True,
            "message_id": response.message_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

