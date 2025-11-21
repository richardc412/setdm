"""Authentication module for OAuth2 + JWT."""

from app.features.auth.router import router as auth_router
from app.features.auth.dependencies import get_current_active_user, get_current_user

__all__ = ["auth_router", "get_current_active_user", "get_current_user"]

