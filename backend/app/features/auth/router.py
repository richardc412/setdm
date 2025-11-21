from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.features.auth.dependencies import get_current_active_user
from app.features.auth.models import User
from app.features.auth.mock_db import create_user, get_user
from app.features.auth.schemas import Token, UserCreate, UserResponse
from app.features.auth.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["authentication"])


def authenticate_user(username: str, password: str) -> User | None:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username to authenticate
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If username or email already exists
    """
    try:
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create the user in the mock database
        user = create_user(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )
        
        return UserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Login endpoint to obtain JWT access token.
    
    Args:
        form_data: OAuth2 password request form with username and password
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from dependency
        
    Returns:
        Current user information
    """
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        disabled=current_user.disabled,
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (stateless JWT, so just a placeholder).
    
    In a real application with JWT, logout would typically involve:
    - Token blacklisting
    - Clearing client-side stored tokens
    - Token revocation lists
    
    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}

