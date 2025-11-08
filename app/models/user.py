"""User model for authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "password": "SecurePass123!"
            }
        }
    )


class UserLogin(BaseModel):
    """User login request."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "SecurePass123!"
            }
        }
    )


class UserResponse(BaseModel):
    """User response (without password)."""

    id: str = Field(alias="_id")
    username: str
    email: EmailStr
    phone: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "username": "johndoe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "is_active": True,
                "created_at": "2025-11-07T10:00:00Z"
            }
        }
    )


class User(BaseModel):
    """User model (internal, with password)."""

    id: str = Field(alias="_id")
    username: str
    email: EmailStr
    phone: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "_id": "507f1f77bcf86cd799439011",
                    "username": "johndoe",
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "is_active": True,
                    "created_at": "2025-11-07T10:00:00Z"
                }
            }
        }
    )


class TokenData(BaseModel):
    """JWT token payload data."""

    user_id: str
    username: str
    exp: Optional[datetime] = None


