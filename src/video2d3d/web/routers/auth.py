"""Authentication router module.

Re-exports the JWT authentication router from the web.auth package so it
can be imported consistently alongside the other routers:

    from video2d3d.web.routers import auth

    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
"""

from __future__ import annotations

from video2d3d.web.auth.router import (
    get_current_user,
    require_roles,
    router,
)

__all__ = ["router", "get_current_user", "require_roles"]
