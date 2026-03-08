"""JWT authentication service.

This module provides functions for:
- Password hashing and verification
- JWT token creation and validation
- User authentication utilities
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from video2d3d.utils.logger import get_logger
from video2d3d.web.auth.database import UserModel, get_session
from video2d3d.web.auth.schemas import AuthConfig, TokenPayload, UserRole

logger = get_logger("web.auth.jwt_service")

# Password hashing context
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Default auth configuration - should be overridden by environment
_auth_config: Optional[AuthConfig] = None


def get_auth_config() -> AuthConfig:
    """Get authentication configuration from environment or defaults."""
    global _auth_config
    if _auth_config is None:
        _auth_config = AuthConfig(
            secret_key=os.environ.get(
                "JWT_SECRET_KEY",
                "change-me-in-production-use-environment-variable",
            ),
            algorithm=os.environ.get("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
            refresh_token_expire_days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        )
    return _auth_config


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        Hashed password string.
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Stored password hash.

    Returns:
        True if password matches, False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    username: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's unique identifier.
        username: User's username.
        role: User's role.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT access token.
    """
    config = get_auth_config()

    if expires_delta is None:
        expires_delta = timedelta(minutes=config.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "type": "access",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, config.secret_key, algorithm=config.algorithm)


def create_refresh_token(
    user_id: str,
    username: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: User's unique identifier.
        username: User's username.
        role: User's role.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT refresh token.
    """
    config = get_auth_config()

    if expires_delta is None:
        expires_delta = timedelta(days=config.refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "type": "refresh",
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, config.secret_key, algorithm=config.algorithm)


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token.

    Args:
        token: Encoded JWT token.

    Returns:
        TokenPayload if valid, None if invalid or expired.
    """
    config = get_auth_config()

    try:
        payload = jwt.decode(
            token,
            config.secret_key,
            algorithms=[config.algorithm],
        )
        return TokenPayload(
            sub=payload["sub"],
            username=payload["username"],
            role=UserRole(payload["role"]),
            exp=(
                datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                if "exp" in payload
                else None
            ),
            iat=(
                datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
                if "iat" in payload
                else None
            ),
            type=payload.get("type", "access"),
        )
    except JWTError as e:
        logger.debug(f"Token decode error: {e}")
        return None


def authenticate_user(username_or_email: str, password: str) -> Optional[UserModel]:
    """Authenticate a user by username/email and password.

    Args:
        username_or_email: Username or email address.
        password: Plain text password.

    Returns:
        UserModel if authentication successful, None otherwise.
    """
    session = get_session()

    try:
        # Try to find user by username or email
        user = (
            session.query(UserModel)
            .filter(
                (UserModel.username == username_or_email.lower())
                | (UserModel.email == username_or_email.lower())
            )
            .first()
        )

        if user is None:
            logger.debug(f"User not found: {username_or_email}")
            return None

        if not user.is_active:
            logger.debug(f"User account is inactive: {username_or_email}")
            return None

        if not verify_password(password, user.hashed_password):
            logger.debug(f"Invalid password for user: {username_or_email}")
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        session.commit()

        return user

    finally:
        session.close()


def get_user_by_id(user_id: str) -> Optional[UserModel]:
    """Get a user by ID.

    Args:
        user_id: User's unique identifier.

    Returns:
        UserModel if found, None otherwise.
    """
    session = get_session()

    try:
        return session.query(UserModel).filter(UserModel.user_id == user_id).first()
    finally:
        session.close()


def get_user_by_username(username: str) -> Optional[UserModel]:
    """Get a user by username.

    Args:
        username: Username to search for.

    Returns:
        UserModel if found, None otherwise.
    """
    session = get_session()

    try:
        return session.query(UserModel).filter(UserModel.username == username.lower()).first()
    finally:
        session.close()


def get_user_by_email(email: str) -> Optional[UserModel]:
    """Get a user by email.

    Args:
        email: Email to search for.

    Returns:
        UserModel if found, None otherwise.
    """
    session = get_session()

    try:
        return session.query(UserModel).filter(UserModel.email == email.lower()).first()
    finally:
        session.close()


def create_user(
    email: str,
    username: str,
    password: str,
    role: UserRole = UserRole.USER,
) -> UserModel:
    """Create a new user.

    Args:
        email: User's email address.
        username: User's username.
        password: Plain text password.
        role: User's role (default: USER).

    Returns:
        Created UserModel.

    Raises:
        ValueError: If username or email already exists.
    """
    session = get_session()

    try:
        # Check if username or email already exists
        existing = (
            session.query(UserModel)
            .filter((UserModel.username == username.lower()) | (UserModel.email == email.lower()))
            .first()
        )

        if existing:
            if existing.username == username.lower():
                raise ValueError("Username already registered")
            else:
                raise ValueError("Email already registered")

        # Create new user
        user = UserModel(
            email=email.lower(),
            username=username.lower(),
            hashed_password=hash_password(password),
            role=role.value,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        logger.info(f"Created new user: {username} with role {role.value}")

        return user

    finally:
        session.close()


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "authenticate_user",
    "get_user_by_id",
    "get_user_by_username",
    "get_user_by_email",
    "create_user",
    "get_auth_config",
]
