from datetime import datetime
from typing import Optional


class User:
    """User model for authentication."""

    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        disabled: bool = False,
        created_at: Optional[datetime] = None,
    ):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.full_name = full_name
        self.disabled = disabled
        self.created_at = created_at or datetime.now()

    def dict(self):
        """Convert user to dictionary."""
        return {
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "disabled": self.disabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

