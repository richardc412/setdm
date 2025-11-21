from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""

    username: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""

    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str


class UserResponse(UserBase):
    """User response schema (without password)."""

    disabled: bool = False

    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """User schema including hashed password."""

    hashed_password: str
    disabled: bool = False


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str
    password: str

