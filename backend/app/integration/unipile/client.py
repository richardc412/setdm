from typing import Optional
import httpx
from app.core.config import get_settings
from .schemas import ChatListResponse, Chat, MessageListResponse, Message


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

