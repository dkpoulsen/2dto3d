"""Authentication schemas for request/response models.

This module defines Pydantic models for user registration, login,
token management, and user information.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    """User role types for role-based access control."""

    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model with common fields."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username",
        examples=["johndoe"],
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format.
        
        Username must contain only alphanumeric characters, underscores, or hyphens.
        """
        # Check each character is valid
        for char in v:
            if not (char.isalnum() or char == "_" or char == "-"):
                raise ValueError(
                    "Username must contain only alphanumeric characters, underscores, or hyphens"
                )
        return v.lower()


class UserCreate(UserBase):
    """Request model for user registration."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength.
        
        Requirements:
        - At least 8 characters (handled by Field min_length)
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Request model for user login."""

    username: str = Field(
        ...,
        description="Username or email address",
        examples=["johndoe", "user@example.com"],
    )
    password: str = Field(
        ...,
        description="User password",
    )


class UserResponse(UserBase):
    """Response model for user information."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "username": "johndoe",
                "role": "user",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-01-16T14:20:00Z",
            }
        },
    )

    user_id: str = Field(..., description="Unique user identifier")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: datetime | None = Field(default=None, description="Last login timestamp")


class TokenResponse(BaseModel):
    """Response model for JWT token."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "role": "user",
                },
            }
        }
    )

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str = Field(..., description="Subject (user ID)")
    username: str = Field(..., description="Username")
    role: UserRole = Field(..., description="User role")
    exp: datetime | None = Field(default=None, description="Expiration time")
    iat: datetime | None = Field(default=None, description="Issued at time")
    type: str = Field(default="access", description="Token type (access/refresh)")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing",
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )


__all__ = [
    "UserRole",
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenPayload",
    "AuthConfig",
]
