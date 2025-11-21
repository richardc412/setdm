"""Example router demonstrating protected routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User

router = APIRouter(prefix="/api", tags=["protected-examples"])


@router.get("/public")
async def public_endpoint():
    """
    This endpoint is PUBLIC - anyone can access it.
    No authentication required.
    """
    return {
        "message": "This is a public endpoint",
        "public": True,
        "authentication_required": False,
    }


@router.get("/protected")
async def protected_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    This endpoint is PROTECTED - requires authentication.
    
    The current_user dependency will:
    1. Check for Bearer token in Authorization header
    2. Validate the JWT token
    3. Fetch the user from the database
    4. Verify the user is active (not disabled)
    5. Return the user object or raise 401 error
    """
    return {
        "message": f"Hello, {current_user.username}!",
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
        },
        "protected": True,
    }


@router.get("/profile")
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get the current user's profile."""
    return {
        "profile": current_user.dict(),
    }


@router.post("/data")
async def create_user_data(
    data: dict,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create data for the current user.
    This demonstrates a POST endpoint that requires authentication.
    """
    return {
        "message": "Data created successfully",
        "created_by": current_user.username,
        "data": data,
    }


@router.get("/admin-only")
async def admin_only_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    This endpoint checks if the user has admin privileges.
    You can add custom logic for role-based access control.
    """
    # Example: Check if user is admin (you'd implement this in your User model)
    if current_user.username != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "message": "Welcome admin!",
        "admin_data": "Sensitive admin information",
    }

