"""Rate limiting middleware for FastAPI.

This module provides rate limiting functionality using slowapi (based on limits).
It supports:
- Configurable rate limits per endpoint type
- IP-based whitelisting
- In-memory or Redis storage backends
- Rate limit headers in responses

Constants:
    UNKNOWN_IP: Default IP string when client IP cannot be determined
    UNKNOWN_LIMIT: Default limit string when limit info is unavailable
    DEFAULT_RATE_LIMIT_MESSAGE: Standard error message for rate limit exceeded
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Request, Response

# Constants for rate limiting (defined before imports that reference them)
UNKNOWN_IP = "unknown"
UNKNOWN_LIMIT = "unknown"
DEFAULT_RATE_LIMIT_MESSAGE = "Rate limit exceeded. Please slow down your requests."

try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None  # type: ignore
    RateLimitExceeded = Exception  # type: ignore
    SlowAPIMiddleware = None  # type: ignore

    def get_remote_address(request: Request) -> str:  # type: ignore
        """Fallback function when slowapi is not available."""
        return UNKNOWN_IP

from video2d3d.utils.config import get_config
from video2d3d.utils.logger import get_logger
from video2d3d.web.exceptions import RateLimitExceededError

logger = get_logger("web.rate_limit")

def get_client_ip(request: Request) -> str:
    """Get client IP address from request.

    Checks X-Forwarded-For header first for reverse proxy scenarios,
    falls back to direct client IP.

    Args:
        request: FastAPI request object.

    Returns:
        Client IP address as string.
    """
    # Check for X-Forwarded-For header (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client address
    return get_remote_address(request)


def create_limiter() -> Optional[Limiter]:
    """Create and configure the rate limiter.

    Returns:
        Configured Limiter instance, or None if rate limiting is disabled.
    """
    config = get_config()
    rate_limit_config = config.web_api.rate_limit

    if not rate_limit_config.enabled:
        logger.info("Rate limiting is disabled")
        return None

    # Create whitelist set for exempt IPs
    whitelist = set(rate_limit_config.whitelist_ips) if rate_limit_config.whitelist_ips else set()

    def get_rate_limit_key(request: Request) -> str:
        """Get rate limit key for the request.

        Whitelisted IPs get a special key that effectively has no limits.

        Args:
            request: FastAPI request object.

        Returns:
            Rate limit key string.
        """
        client_ip = get_client_ip(request)

        # Check whitelist
        if client_ip in whitelist:
            # Return a unique key that won't hit any limits
            return f"whitelisted:{client_ip}"

        return client_ip

    if not SLOWAPI_AVAILABLE:
        logger.warning("slowapi package not installed, rate limiting is disabled")
        return None

    limiter = Limiter(
        key_func=get_rate_limit_key,
        default_limits=[f"{rate_limit_config.requests_per_minute}/minute"],
        storage_uri=rate_limit_config.storage_uri,
        headers_enabled=True,  # Include rate limit info in response headers
    )

    logger.info(
        f"Rate limiter initialized: {rate_limit_config.requests_per_minute} req/min (default), "
        f"{rate_limit_config.requests_per_hour} req/hour (via decorator), "
        f"storage={rate_limit_config.storage_uri}"
    )

    return limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors.

    Converts slowapi's RateLimitExceeded to our custom RateLimitExceededError.

    Args:
        request: FastAPI request object.
        exc: RateLimitExceeded exception from slowapi.

    Returns:
        JSON response with rate limit error details.
    """
    from video2d3d.web.schemas import ErrorResponse

    # Extract limit info from the exception
    limit = str(exc.detail) if exc.detail else UNKNOWN_LIMIT

    # Calculate retry-after from the rate limit
    retry_after: Optional[int] = None
    if hasattr(exc, "headers") and exc.headers:
        retry_after_str = exc.headers.get("Retry-After")
        if retry_after_str:
            try:
                retry_after = int(retry_after_str)
            except ValueError:
                logger.warning(f"Invalid Retry-After header value: {retry_after_str}")

    client_ip = get_client_ip(request)
    logger.warning(f"Rate limit exceeded for {client_ip}: {limit}")

    error_response = ErrorResponse(
        error="rate_limit_exceeded",
        message=DEFAULT_RATE_LIMIT_MESSAGE,
        detail={
            "limit": limit,
            "retry_after": retry_after,
        },
        request_id=getattr(request.state, "request_id", None),
    )

    from fastapi.responses import JSONResponse
    from fastapi import status

    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.model_dump(exclude_none=True),
    )

    # Add rate limit headers
    if hasattr(exc, "headers") and exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value

    return response


def setup_rate_limiting(app: FastAPI) -> Optional[Limiter]:
    """Set up rate limiting middleware for the FastAPI app.

    Args:
        app: FastAPI application instance.

    Returns:
        Limiter instance if rate limiting is enabled, None otherwise.
    """
    limiter = create_limiter()

    if limiter is None:
        return None

    # Set the limiter on the app state
    app.state.limiter = limiter

    # Register custom exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Add SlowAPI middleware
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting middleware configured")

    return limiter


def get_limiter() -> Optional[Limiter]:
    """Get the global limiter instance.

    Returns:
        Limiter instance if configured, None otherwise.
    """
    from video2d3d.web.state import app_state

    # Check if app has limiter in state using getattr with default
    return getattr(app_state, "limiter", None)


# Rate limit decorators for different endpoint types
def limit_upload(limiter: Optional[Limiter] = None):
    """Decorator for upload endpoints with stricter rate limits.

    Args:
        limiter: Limiter instance. If None, creates new one.

    Returns:
        Rate limit decorator.
    """
    config = get_config()
    rate_limit_config = config.web_api.rate_limit

    if limiter is None:
        limiter = get_limiter()

    if limiter is None:
        # Return a no-op decorator if rate limiting is disabled
        def decorator(func):
            return func

        return decorator

    return limiter.limit(f"{rate_limit_config.upload_requests_per_minute}/minute")


def limit_api(limiter: Optional[Limiter] = None):
    """Decorator for general API endpoints with standard rate limits.

    Args:
        limiter: Limiter instance. If None, creates new one.

    Returns:
        Rate limit decorator.
    """
    config = get_config()
    rate_limit_config = config.web_api.rate_limit

    if limiter is None:
        limiter = get_limiter()

    if limiter is None:
        # Return a no-op decorator if rate limiting is disabled
        def decorator(func):
            return func

        return decorator

    # Combine per-minute and per-hour limits
    return limiter.limit(
        f"{rate_limit_config.requests_per_minute}/minute;{rate_limit_config.requests_per_hour}/hour"
    )


__all__ = [
    "create_limiter",
    "setup_rate_limiting",
    "get_client_ip",
    "get_limiter",
    "limit_upload",
    "limit_api",
    "rate_limit_exceeded_handler",
]
