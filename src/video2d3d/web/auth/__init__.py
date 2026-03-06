"""Authentication module for 2Dto3D API.

This module provides JWT-based authentication with:
- User registration and login
- Access and refresh tokens
- Role-based access control (user/admin)
- SQLite database for user storage

Usage:
    from video2d3d.web.auth import (
        router,
        get_current_user,
        require_roles,
        UserRole,
    )

    # Add auth router to your FastAPI app
    app.include_router(router, prefix="/auth", tags=["Authentication"])

    # Protect an endpoint with authentication
    @app.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        return {"user": user.username}

    # Require admin role
    @app.get("/admin")
    async def admin_route(user = Depends(require_roles(UserRole.ADMIN))):
        return {"message": "Admin access granted"}
"""

from video2d3d.web.auth.database import (
    UserModel,
    get_session,
    init_database,
)
from video2d3d.web.auth.jwt_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_auth_config,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    hash_password,
    verify_password,
)
from video2d3d.web.auth.router import (
    get_current_user,
    get_current_user_optional,
    require_roles,
    router,
)
from video2d3d.web.auth.schemas import (
    AuthConfig,
    TokenPayload,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
)

__all__ = [
    # Router and dependencies
    "router",
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
    # Schemas
    "UserRole",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenPayload",
    "AuthConfig",
    # Database
    "UserModel",
    "init_database",
    "get_session",
    # JWT Service
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
