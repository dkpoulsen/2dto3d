"""Authentication router for user registration, login, and token management.

This module provides endpoints for:
- User registration
- User login (token generation)
- Token refresh
- Getting current user info
"""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from video2d3d.utils.logger import get_logger
from video2d3d.web.auth.database import UserModel
from video2d3d.web.auth.jwt_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_auth_config,
    get_user_by_id,
)
from video2d3d.web.auth.schemas import (
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
)
from video2d3d.web.schemas import ErrorResponse
from video2d3d.web.rate_limit import limit_auth

logger = get_logger("web.auth.router")

router = APIRouter()

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


# ============================================================================
# Authentication Dependencies
# ============================================================================


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
) -> UserModel:
    """Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request header.

    Returns:
        Authenticated UserModel.

    Raises:
        HTTPException: 401 if not authenticated or token invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise credentials_exception

    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(payload.sub)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
) -> Optional[UserModel]:
    """Dependency to optionally get the current authenticated user.

    Returns None if not authenticated, instead of raising an exception.

    Args:
        credentials: HTTP Bearer credentials from request header.

    Returns:
        Authenticated UserModel or None.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None or payload.type != "access":
        return None

    user = get_user_by_id(payload.sub)
    if user is None or not user.is_active:
        return None

    return user


def require_roles(*required_roles: UserRole):
    """Dependency factory to require specific roles.

    Args:
        required_roles: Roles that are allowed to access the endpoint.

    Returns:
        Dependency function that validates user role.

    Example:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: UserModel = Depends(require_roles(UserRole.ADMIN))
        ):
            return {"message": "Admin access granted"}
    """

    async def role_checker(
        user: UserModel = Depends(get_current_user),
    ) -> UserModel:
        user_role = UserRole(user.role)
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in required_roles]}",
            )
        return user

    return role_checker


# ============================================================================
# Helper Functions
# ============================================================================


def user_to_response(user: UserModel) -> UserResponse:
    """Convert a UserModel to UserResponse.

    Args:
        user: UserModel instance.

    Returns:
        UserResponse schema instance.
    """
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        role=UserRole(user.role),
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )


def create_token_response(user: UserModel) -> TokenResponse:
    """Create a TokenResponse for a user.

    Args:
        user: UserModel instance.

    Returns:
        TokenResponse with access and refresh tokens.
    """
    role = UserRole(user.role)
    config = get_auth_config()

    access_token = create_access_token(
        user_id=user.user_id,
        username=user.username,
        role=role,
    )

    refresh_token = create_refresh_token(
        user_id=user.user_id,
        username=user.username,
        role=role,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=config.access_token_expire_minutes * 60,
        user=user_to_response(user),
    )


# ============================================================================
# Authentication Endpoints
# ============================================================================


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account and return authentication tokens.",
    responses={
        201: {"description": "User created successfully"},
        400: {"model": ErrorResponse, "description": "Username or email already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
@limit_auth()
async def register(request: Request, user_data: UserCreate) -> TokenResponse:
    """Register a new user.

    Args:
        user_data: User registration data.

    Returns:
        TokenResponse with access and refresh tokens.

    Raises:
        HTTPException: 400 if username or email already exists.
    """
    try:
        user = create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            role=UserRole.USER,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    logger.info(f"New user registered: {user.username}")

    return create_token_response(user)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate a user and return JWT tokens.",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
    )
@limit_auth()
async def login(request: Request, credentials: UserLogin) -> TokenResponse:
    """Authenticate a user and return tokens.

    Args:
        credentials: User login credentials.

    Returns:
        TokenResponse with access and refresh tokens.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = authenticate_user(
        username_or_email=credentials.username,
        password=credentials.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User logged in: {user.username}")

    return create_token_response(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use a refresh token to get a new access token.",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
    },
)
@limit_auth()
async def refresh_token(
    http_request: Request,
    token_request: TokenRefreshRequest,
) -> TokenResponse:
    """Refresh an access token using a refresh token.

    Args:
        http_request: FastAPI request object (for rate limiting).
        token_request: Refresh token request.

    Returns:
        New TokenResponse with fresh tokens.

    Raises:
        HTTPException: 401 if refresh token is invalid.
    """
    payload = decode_token(token_request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    logger.info(f"Token refreshed for user: {user.username}")

    return create_token_response(user)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "User information"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
) -> UserResponse:
    """Get current user information.

    Args:
        current_user: Currently authenticated user.

    Returns:
        UserResponse with user information.
    """
    return user_to_response(current_user)


@router.post(
    "/logout",
    summary="User logout",
    description="Logout the current user (client should discard tokens).",
    responses={
        200: {"description": "Logout successful"},
    },
)
async def logout(
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """Logout the current user.

    Note: Since JWT tokens are stateless, actual logout is handled client-side
    by discarding the tokens. This endpoint exists for API consistency and
    potential future token blacklisting.

    Args:
        current_user: Currently authenticated user.

    Returns:
        Success message.
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}


# Export dependencies for use in other modules
__all__ = [
    "router",
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
]
