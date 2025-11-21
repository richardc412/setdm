from typing import Optional

from app.features.auth.models import User
from app.features.auth.security import get_password_hash

# Mock database using a dictionary
# In production, this would be replaced with actual database queries
fake_users_db: dict[str, User] = {}


def init_mock_db():
    """Initialize the mock database with some default users."""
    # Create a demo user
    demo_user = User(
        username="demo",
        email="demo@example.com",
        hashed_password=get_password_hash("demo123"),
        full_name="Demo User",
        disabled=False,
    )
    fake_users_db["demo"] = demo_user
    
    # Create an admin user
    admin_user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        disabled=False,
    )
    fake_users_db["admin"] = admin_user


def get_user(username: str) -> Optional[User]:
    """
    Get a user from the mock database by username.
    
    Args:
        username: Username to search for
        
    Returns:
        User object if found, None otherwise
    """
    return fake_users_db.get(username)


def get_user_by_email(email: str) -> Optional[User]:
    """
    Get a user from the mock database by email.
    
    Args:
        email: Email to search for
        
    Returns:
        User object if found, None otherwise
    """
    for user in fake_users_db.values():
        if user.email == email:
            return user
    return None


def create_user(username: str, email: str, hashed_password: str, full_name: Optional[str] = None) -> User:
    """
    Create a new user in the mock database.
    
    Args:
        username: Username for the new user
        email: Email for the new user
        hashed_password: Hashed password for the new user
        full_name: Optional full name for the new user
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If username or email already exists
    """
    if username in fake_users_db:
        raise ValueError("Username already exists")
    
    if get_user_by_email(email):
        raise ValueError("Email already exists")
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        disabled=False,
    )
    fake_users_db[username] = user
    return user


def user_exists(username: str) -> bool:
    """
    Check if a user exists in the mock database.
    
    Args:
        username: Username to check
        
    Returns:
        True if user exists, False otherwise
    """
    return username in fake_users_db


# Initialize the mock database on import
init_mock_db()

