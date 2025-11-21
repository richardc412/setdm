"""
Example usage of the Unipile integration.

This file demonstrates how to use the Unipile client in various scenarios.
"""

from .client import list_all_chats, get_unipile_client


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


# Example of how to use in a FastAPI route
"""
from fastapi import APIRouter, HTTPException
from app.integration.unipile import list_all_chats

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
"""

