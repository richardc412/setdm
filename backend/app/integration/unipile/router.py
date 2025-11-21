from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from .client import list_all_chats
from .schemas import ChatListResponse


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

