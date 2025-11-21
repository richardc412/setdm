# Protecting Routes in FastAPI

This guide shows you how to protect API endpoints using the authentication system.

## Quick Start

To protect any FastAPI route, add the `get_current_active_user` dependency:

```python
from typing import Annotated
from fastapi import Depends
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User

@app.get("/protected")
async def protected_route(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return {"message": f"Hello {current_user.username}!"}
```

## Available Dependencies

### 1. `get_current_user`

Returns the current user from the JWT token. Does NOT check if user is active.

```python
from app.features.auth.dependencies import get_current_user

@app.get("/endpoint")
async def my_endpoint(
    current_user: Annotated[User, Depends(get_current_user)]
):
    # User might be disabled
    return {"user": current_user.username}
```

### 2. `get_current_active_user` ⭐ RECOMMENDED

Returns the current user AND verifies they are active (not disabled).

```python
from app.features.auth.dependencies import get_current_active_user

@app.get("/endpoint")
async def my_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    # User is guaranteed to be active
    return {"user": current_user.username}
```

## Examples

### Public vs Protected Routes

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User

router = APIRouter()

# PUBLIC - No authentication
@router.get("/public")
async def public_endpoint():
    return {"message": "Anyone can access this"}

# PROTECTED - Authentication required
@router.get("/protected")
async def protected_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return {
        "message": f"Hello {current_user.username}!",
        "email": current_user.email
    }
```

### GET Request with Auth

```python
@router.get("/my-data")
async def get_my_data(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Fetch data for the authenticated user."""
    return {
        "user": current_user.username,
        "data": ["item1", "item2", "item3"]
    }
```

### POST Request with Auth

```python
from pydantic import BaseModel

class CreateItemRequest(BaseModel):
    name: str
    description: str

@router.post("/items")
async def create_item(
    item: CreateItemRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create an item for the authenticated user."""
    return {
        "message": "Item created",
        "item": item.dict(),
        "created_by": current_user.username
    }
```

### PUT/PATCH Request with Auth

```python
@router.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item: CreateItemRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update an item (authentication required)."""
    return {
        "message": "Item updated",
        "item_id": item_id,
        "updated_by": current_user.username
    }
```

### DELETE Request with Auth

```python
@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete an item (authentication required)."""
    return {
        "message": "Item deleted",
        "item_id": item_id,
        "deleted_by": current_user.username
    }
```

## Advanced: Role-Based Access Control (RBAC)

### Custom Permission Dependency

Create a custom dependency for admin-only routes:

```python
from fastapi import HTTPException, status

async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Dependency that requires admin privileges."""
    # Check if user is admin (implement your own logic)
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Use it in routes
@router.get("/admin/users")
async def list_all_users(
    admin_user: Annotated[User, Depends(get_current_admin_user)]
):
    """Admin-only endpoint."""
    return {"message": "List of all users", "admin": admin_user.username}
```

### Multiple Permission Levels

```python
# Add to your User model or create a separate permissions system
def check_permission(user: User, required_permission: str) -> bool:
    """Check if user has required permission."""
    # Implement your permission logic
    permissions = {
        "admin": ["read", "write", "delete", "admin"],
        "demo": ["read", "write"],
    }
    user_permissions = permissions.get(user.username, ["read"])
    return required_permission in user_permissions

# Use in routes
@router.delete("/important-data/{id}")
async def delete_important_data(
    id: int,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    if not check_permission(current_user, "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete"
        )
    return {"message": f"Deleted {id}"}
```

## Protecting Entire Routers

You can add authentication to an entire router:

```python
from fastapi import APIRouter, Depends
from app.features.auth.dependencies import get_current_active_user

# All routes in this router will require authentication
router = APIRouter(
    prefix="/protected-section",
    tags=["protected"],
    dependencies=[Depends(get_current_active_user)]
)

@router.get("/endpoint1")
async def endpoint1():
    # Already protected by router dependency
    return {"message": "Protected endpoint 1"}

@router.get("/endpoint2")
async def endpoint2():
    # Already protected by router dependency
    return {"message": "Protected endpoint 2"}

# If you need access to current_user in these routes:
@router.get("/endpoint3")
async def endpoint3(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return {"message": f"Hello {current_user.username}"}
```

## Testing Protected Routes

### Using cURL

```bash
# 1. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo123" \
  | grep -o '"access_token":"[^"]*"' \
  | cut -d'"' -f4)

# 2. Use token in protected endpoint
curl http://localhost:8000/api/protected \
  -H "Authorization: Bearer $TOKEN"
```

### Using Python requests

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    data={"username": "demo", "password": "demo123"}
)
token = response.json()["access_token"]

# Call protected endpoint
response = requests.get(
    "http://localhost:8000/api/protected",
    headers={"Authorization": f"Bearer {token}"}
)
print(response.json())
```

### Using HTTPie

```bash
# Login
http -f POST localhost:8000/auth/login username=demo password=demo123

# Protected endpoint
http GET localhost:8000/api/protected \
  "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Error Responses

### 401 Unauthorized

Returned when token is missing, invalid, or expired:

```json
{
  "detail": "Not authenticated"
}
```

or

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

Returned when user lacks required permissions:

```json
{
  "detail": "Admin access required"
}
```

### 400 Bad Request

Returned when user account is disabled:

```json
{
  "detail": "Inactive user"
}
```

## Best Practices

### 1. Always Use `get_current_active_user`

Unless you specifically need to allow disabled users, use `get_current_active_user`:

```python
# ✅ GOOD - Checks if user is active
current_user: Annotated[User, Depends(get_current_active_user)]

# ❌ AVOID - Doesn't check active status
current_user: Annotated[User, Depends(get_current_user)]
```

### 2. Consistent Naming

Use consistent parameter names:

```python
# ✅ GOOD
async def endpoint(current_user: Annotated[User, Depends(get_current_active_user)]):
    pass

# ❌ AVOID mixing names
async def endpoint1(user: Annotated[User, Depends(get_current_active_user)]):
    pass
    
async def endpoint2(current_user: Annotated[User, Depends(get_current_active_user)]):
    pass
```

### 3. Document Auth Requirements

Use OpenAPI documentation:

```python
@router.get(
    "/protected",
    summary="Get protected data",
    description="Requires authentication. Returns user-specific data.",
    responses={
        200: {"description": "Success"},
        401: {"description": "Not authenticated"},
    }
)
async def protected_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return {"data": "protected"}
```

### 4. Validate Resource Ownership

Check if the user owns the resource they're trying to access:

```python
@router.get("/items/{item_id}")
async def get_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    item = get_item_from_db(item_id)
    
    # Verify ownership
    if item.owner_username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't own this item"
        )
    
    return item
```

## Accessing User Information

The `current_user` object has the following attributes:

```python
current_user.username        # str: Username
current_user.email          # str: Email address
current_user.full_name      # str | None: Full name
current_user.disabled       # bool: Is user disabled?
current_user.hashed_password # str: Hashed password (don't return this!)
current_user.created_at     # datetime: Account creation time
```

## Example: Complete Protected Feature

Here's a complete example of a protected feature module:

```python
# app/features/posts/router.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User

router = APIRouter(prefix="/posts", tags=["posts"])

class CreatePostRequest(BaseModel):
    title: str
    content: str

# In-memory storage (replace with database)
posts_db = []

@router.post("/")
async def create_post(
    post_data: CreatePostRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Create a new post (authentication required)."""
    post = {
        "id": len(posts_db) + 1,
        "title": post_data.title,
        "content": post_data.content,
        "author": current_user.username,
    }
    posts_db.append(post)
    return post

@router.get("/")
async def list_posts():
    """List all posts (public endpoint)."""
    return posts_db

@router.get("/my-posts")
async def list_my_posts(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """List current user's posts (authentication required)."""
    return [p for p in posts_db if p["author"] == current_user.username]

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Delete a post (must be owner)."""
    post = next((p for p in posts_db if p["id"] == post_id), None)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post["author"] != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )
    
    posts_db.remove(post)
    return {"message": "Post deleted"}
```

## Summary

1. **Import the dependency**: `from app.features.auth.dependencies import get_current_active_user`
2. **Add to route parameters**: `current_user: Annotated[User, Depends(get_current_active_user)]`
3. **Use user data**: Access `current_user.username`, `current_user.email`, etc.
4. **Test with token**: Include `Authorization: Bearer <token>` header

That's it! Your routes are now protected. 🔒

