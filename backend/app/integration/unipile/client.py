from typing import Optional, BinaryIO
import httpx
from app.core.config import get_settings
from .schemas import (
    ChatListResponse,
    Chat,
    MessageListResponse,
    Message,
    ChatAttendeeListResponse,
    MessageSentResponse,
    WebhookCreateRequest,
    WebhookCreatedResponse,
    WebhookListResponse,
)


class UnipileClient:
    """
    Client for interacting with the Unipile API.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Unipile client.

        Args:
            base_url: The base URL for the Unipile API (DSN)
            api_key: The API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }

    async def list_all_chats(
        self,
        unread: Optional[bool] = None,
        cursor: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        account_type: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> ChatListResponse:
        """
        List all chats from Unipile API.

        Args:
            unread: Filter for unread/read chats only
            cursor: Cursor for pagination
            before: Filter items created before datetime (ISO 8601 UTC)
            after: Filter items created after datetime (ISO 8601 UTC)
            limit: Limit number of items (1-250)
            account_type: Filter by provider (WHATSAPP, LINKEDIN, etc.)
            account_id: Filter by account ID (comma-separated list)

        Returns:
            ChatListResponse containing simplified chat objects

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        # Build query parameters
        params = {}
        if unread is not None:
            params["unread"] = str(unread).lower()
        if cursor:
            params["cursor"] = cursor
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        if account_type:
            params["account_type"] = account_type
        if account_id:
            params["account_id"] = account_id

        url = f"{self.base_url}/api/v1/chats"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Extract only the fields we care about
            filtered_items = []
            for item in data.get("items", []):
                chat = Chat(
                    object=item.get("object"),
                    id=item.get("id"),
                    account_id=item.get("account_id"),
                    account_type=item.get("account_type"),
                    provider_id=item.get("provider_id"),
                    name=item.get("name"),
                    timestamp=item.get("timestamp"),
                    unread_count=item.get("unread_count", 0),
                    unread=item.get("unread_count", 0) > 0,
                )
                filtered_items.append(chat)

            return ChatListResponse(
                object=data.get("object"),
                items=filtered_items,
                cursor=data.get("cursor"),
            )

    async def list_chat_messages(
        self,
        chat_id: str,
        cursor: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        sender_id: Optional[str] = None,
    ) -> MessageListResponse:
        """
        List all messages from a specific chat.

        Args:
            chat_id: The id of the chat related to requested messages
            cursor: Cursor for pagination
            before: Filter items created before datetime (ISO 8601 UTC)
            after: Filter items created after datetime (ISO 8601 UTC)
            limit: Limit number of items (1-250)
            sender_id: Filter messages from a specific sender

        Returns:
            MessageListResponse containing message objects

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        # Build query parameters
        params = {}
        if cursor:
            params["cursor"] = cursor
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        if sender_id:
            params["sender_id"] = sender_id

        url = f"{self.base_url}/api/v1/chats/{chat_id}/messages"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Parse messages
            messages = []
            for item in data.get("items", []):
                message = Message(**item)
                messages.append(message)

            return MessageListResponse(
                object=data.get("object"),
                items=messages,
                cursor=data.get("cursor"),
            )

    async def list_chat_attendees(
        self,
        chat_id: str,
    ) -> ChatAttendeeListResponse:
        """
        List all attendees from a chat.

        Args:
            chat_id: The id of the chat related to requested attendees

        Returns:
            ChatAttendeeListResponse containing attendee information including picture_url

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = f"{self.base_url}/api/v1/chats/{chat_id}/attendees"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return ChatAttendeeListResponse(**data)

    async def send_message(
        self,
        chat_id: str,
        text: Optional[str] = None,
        account_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        quote_id: Optional[str] = None,
        voice_message: Optional[tuple[str, BinaryIO, str]] = None,
        video_message: Optional[tuple[str, BinaryIO, str]] = None,
        attachments: Optional[list[tuple[str, BinaryIO, str]]] = None,
        typing_duration: Optional[str] = None,
    ) -> MessageSentResponse:
        """
        Send a message in a chat.

        Args:
            chat_id: The id of the chat where to send the message
            text: The message text
            account_id: An account_id can be specified to prevent the user from sending messages in chats not belonging to the account
            thread_id: Optional and for Slack's messaging only. The id of the thread to send the message in
            quote_id: The id of a message to quote/reply to
            voice_message: A file to send as voice message (filename, file object, mimetype)
            video_message: A file to send as video message (filename, file object, mimetype)
            attachments: List of files to attach (filename, file object, mimetype)
            typing_duration: (WhatsApp only) Duration in milliseconds to simulate typing

        Returns:
            MessageSentResponse containing the message_id

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = f"{self.base_url}/api/v1/chats/{chat_id}/messages"

        # Build form data
        data = {}
        if text:
            data["text"] = text
        if account_id:
            data["account_id"] = account_id
        if thread_id:
            data["thread_id"] = thread_id
        if quote_id:
            data["quote_id"] = quote_id
        if typing_duration:
            data["typing_duration"] = typing_duration

        # Build files dictionary
        files = {}
        if voice_message:
            files["voice_message"] = voice_message
        if video_message:
            files["video_message"] = video_message
        if attachments:
            # For multiple files with same key, httpx expects list of tuples
            files["attachments"] = attachments

        # Remove Content-Type from headers for multipart/form-data
        # httpx will set it automatically with boundary
        headers = {k: v for k, v in self.headers.items() if k.lower() != "content-type"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                data=data,
                files=files if files else None,
                timeout=30.0,
            )
            response.raise_for_status()
            response_data = response.json()

            return MessageSentResponse(**response_data)

    async def create_webhook(
        self,
        request_url: str,
        source: str = "messaging",
        name: Optional[str] = None,
        format: str = "json",
        account_ids: Optional[list[str]] = None,
        enabled: bool = True,
        events: Optional[list[str]] = None,
    ) -> WebhookCreatedResponse:
        """
        Create a webhook in Unipile.

        Args:
            request_url: The URL where Unipile will send webhook events
            source: The webhook source type (default: "messaging")
            name: Optional name for the webhook
            format: Data format - "json" or "form" (default: "json")
            account_ids: Optional list of account IDs to target
            enabled: Whether the webhook is enabled (default: True)
            events: List of events to subscribe to (default: ["message_received"])

        Returns:
            WebhookCreatedResponse containing the webhook_id

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = f"{self.base_url}/api/v1/webhooks"

        # Set default events if not provided
        if events is None:
            events = ["message_received"]

        webhook_data = WebhookCreateRequest(
            request_url=request_url,
            source=source,
            name=name,
            format=format,
            account_ids=account_ids,
            enabled=enabled,
            events=events,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=webhook_data.model_dump(exclude_none=True),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return WebhookCreatedResponse(**data)

    async def list_webhooks(self) -> WebhookListResponse:
        """
        List all webhooks configured in Unipile.

        Returns:
            WebhookListResponse containing list of webhooks

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = f"{self.base_url}/api/v1/webhooks"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            return WebhookListResponse(**data)

    async def delete_webhook(self, webhook_id: str) -> dict:
        """
        Delete a webhook from Unipile.

        Args:
            webhook_id: The ID of the webhook to delete

        Returns:
            Response dict from Unipile

        Raises:
            httpx.HTTPStatusError: If the API returns an error status
            httpx.RequestError: If there's a network/connection error
        """
        url = f"{self.base_url}/api/v1/webhooks/{webhook_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()


def get_unipile_client() -> UnipileClient:
    """
    Factory function to create a UnipileClient instance with settings from config.

    Returns:
        Configured UnipileClient instance

    Raises:
        ValueError: If UNIPILE_DSN or UNIPILE_API_KEY are not configured
    """
    settings = get_settings()

    if not settings.unipile_dsn:
        raise ValueError("UNIPILE_DSN is not configured in environment variables")

    if not settings.unipile_api_key:
        raise ValueError("UNIPILE_API_KEY is not configured in environment variables")

    return UnipileClient(
        base_url=settings.unipile_dsn,
        api_key=settings.unipile_api_key,
    )


async def list_all_chats(
    unread: Optional[bool] = None,
    cursor: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    account_type: Optional[str] = None,
    account_id: Optional[str] = None,
) -> ChatListResponse:
    """
    Convenience function to list all chats using the configured client.

    This is a wrapper around UnipileClient.list_all_chats() that automatically
    initializes the client with settings from the environment.

    Args:
        unread: Filter for unread/read chats only
        cursor: Cursor for pagination
        before: Filter items created before datetime (ISO 8601 UTC)
        after: Filter items created after datetime (ISO 8601 UTC)
        limit: Limit number of items (1-250)
        account_type: Filter by provider (WHATSAPP, LINKEDIN, etc.)
        account_id: Filter by account ID (comma-separated list)

    Returns:
        ChatListResponse containing simplified chat objects

    Example:
        ```python
        from app.integration.unipile import list_all_chats

        # Get all chats
        response = await list_all_chats()

        # Get only unread chats with limit
        response = await list_all_chats(unread=True, limit=50)

        # Get chats from specific account type
        response = await list_all_chats(account_type="LINKEDIN")
        ```
    """
    client = get_unipile_client()
    return await client.list_all_chats(
        unread=unread,
        cursor=cursor,
        before=before,
        after=after,
        limit=limit,
        account_type=account_type,
        account_id=account_id,
    )


async def list_chat_messages(
    chat_id: str,
    cursor: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    limit: Optional[int] = None,
    sender_id: Optional[str] = None,
) -> MessageListResponse:
    """
    Convenience function to list messages from a chat using the configured client.

    This is a wrapper around UnipileClient.list_chat_messages() that automatically
    initializes the client with settings from the environment.

    Args:
        chat_id: The id of the chat related to requested messages
        cursor: Cursor for pagination
        before: Filter items created before datetime (ISO 8601 UTC)
        after: Filter items created after datetime (ISO 8601 UTC)
        limit: Limit number of items (1-250)
        sender_id: Filter messages from a specific sender

    Returns:
        MessageListResponse containing message objects

    Example:
        ```python
        from app.integration.unipile import list_chat_messages

        # Get all messages from a chat
        response = await list_chat_messages(chat_id="abc123")

        # Get messages with pagination
        response = await list_chat_messages(chat_id="abc123", limit=50)

        # Get messages from a specific sender
        response = await list_chat_messages(chat_id="abc123", sender_id="sender123")
        ```
    """
    client = get_unipile_client()
    return await client.list_chat_messages(
        chat_id=chat_id,
        cursor=cursor,
        before=before,
        after=after,
        limit=limit,
        sender_id=sender_id,
    )


async def send_message(
    chat_id: str,
    text: Optional[str] = None,
    account_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    quote_id: Optional[str] = None,
    voice_message: Optional[tuple[str, BinaryIO, str]] = None,
    video_message: Optional[tuple[str, BinaryIO, str]] = None,
    attachments: Optional[list[tuple[str, BinaryIO, str]]] = None,
    typing_duration: Optional[str] = None,
) -> MessageSentResponse:
    """
    Convenience function to send a message in a chat using the configured client.

    This is a wrapper around UnipileClient.send_message() that automatically
    initializes the client with settings from the environment.

    Args:
        chat_id: The id of the chat where to send the message
        text: The message text
        account_id: An account_id can be specified to prevent the user from sending messages in chats not belonging to the account
        thread_id: Optional and for Slack's messaging only. The id of the thread to send the message in
        quote_id: The id of a message to quote/reply to
        voice_message: A file to send as voice message (filename, file object, mimetype)
        video_message: A file to send as video message (filename, file object, mimetype)
        attachments: List of files to attach (filename, file object, mimetype)
        typing_duration: (WhatsApp only) Duration in milliseconds to simulate typing

    Returns:
        MessageSentResponse containing the message_id

    Example:
        ```python
        from app.integration.unipile import send_message

        # Send a simple text message
        response = await send_message(chat_id="abc123", text="Hello!")

        # Send a message with attachments
        with open("image.jpg", "rb") as f:
            response = await send_message(
                chat_id="abc123",
                text="Check this out!",
                attachments=[("image.jpg", f, "image/jpeg")]
            )
        ```
    """
    client = get_unipile_client()
    return await client.send_message(
        chat_id=chat_id,
        text=text,
        account_id=account_id,
        thread_id=thread_id,
        quote_id=quote_id,
        voice_message=voice_message,
        video_message=video_message,
        attachments=attachments,
        typing_duration=typing_duration,
    )

