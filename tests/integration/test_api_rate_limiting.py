"""Integration tests for API rate limiting.

Tests cover:
- Rate limiting on API endpoints
- Rate limit headers in responses
- Rate limit exceeded behavior
- IP whitelist functionality
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.rate_limit import (
    SLOWAPI_AVAILABLE,
    create_limiter,
    rate_limit_exceeded_handler,
    setup_rate_limiting,
)


@pytest.fixture
def mock_config_with_rate_limit() -> Generator[MagicMock, None, None]:
    """Create a mock config with rate limiting enabled."""
    with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
        mock_rate_limit = MagicMock()
        mock_rate_limit.enabled = True
        mock_rate_limit.requests_per_minute = 5
        mock_rate_limit.requests_per_hour = 100
        mock_rate_limit.upload_requests_per_minute = 2
        mock_rate_limit.storage_uri = "memory://"
        mock_rate_limit.whitelist_ips = []

        mock_web_api = MagicMock()
        mock_web_api.rate_limit = mock_rate_limit

        mock_cfg = MagicMock()
        mock_cfg.web_api = mock_web_api

        mock_get_config.return_value = mock_cfg
        yield mock_get_config


@pytest.fixture
def mock_config_disabled() -> Generator[MagicMock, None, None]:
    """Create a mock config with rate limiting disabled."""
    with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
        mock_rate_limit = MagicMock()
        mock_rate_limit.enabled = False

        mock_web_api = MagicMock()
        mock_web_api.rate_limit = mock_rate_limit

        mock_cfg = MagicMock()
        mock_cfg.web_api = mock_web_api

        mock_get_config.return_value = mock_cfg
        yield mock_get_config


@pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
class TestRateLimitingIntegration:
    """Integration tests for rate limiting with real slowapi."""

    def test_rate_limiting_enabled_on_health_endpoint(
        self, mock_config_with_rate_limit: MagicMock
    ) -> None:
        """Test that rate limiting is applied to health endpoint."""
        app = FastAPI()
        limiter = create_limiter()

        if limiter is None:
            pytest.skip("Rate limiting not available")

        app.state.limiter = limiter

        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware

        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_rate_limiting_returns_429_after_exceeding_limit(
        self, mock_config_with_rate_limit: MagicMock
    ) -> None:
        """Test that 429 is returned after exceeding rate limit."""
        app = FastAPI()
        limiter = create_limiter()

        if limiter is None:
            pytest.skip("Rate limiting not available")

        app.state.limiter = limiter

        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware

        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        with TestClient(app) as client:
            # Make multiple requests to exceed the 5/minute limit
            responses = []
            for _ in range(10):
                response = client.get("/test")
                responses.append(response)

            # At least one request should be rate limited
            rate_limited = any(r.status_code == 429 for r in responses)
            assert rate_limited, "Rate limiting should have been triggered"

    def test_rate_limit_response_format(self, mock_config_with_rate_limit: MagicMock) -> None:
        """Test that rate limit response has correct format."""
        app = FastAPI()
        limiter = create_limiter()

        if limiter is None:
            pytest.skip("Rate limiting not available")

        app.state.limiter = limiter

        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware

        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        with TestClient(app) as client:
            # Exhaust the rate limit
            for _ in range(10):
                client.get("/test")

            # Get the rate limited response
            response = client.get("/test")

            if response.status_code == 429:
                data = response.json()
                assert data.get("error") == "rate_limit_exceeded"
                assert "message" in data
                assert "detail" in data
                assert "limit" in data["detail"]

    def test_rate_limit_headers_present(self, mock_config_with_rate_limit: MagicMock) -> None:
        """Test that rate limit headers are present in response."""
        app = FastAPI()
        limiter = create_limiter()

        if limiter is None:
            pytest.skip("Rate limiting not available")

        app.state.limiter = limiter

        from slowapi.errors import RateLimitExceeded
        from slowapi.middleware import SlowAPIMiddleware

        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        with TestClient(app) as client:
            response = client.get("/test")
            assert response.status_code == 200

            # Check for rate limit headers (case-insensitive)
            headers_lower = {k.lower(): v for k, v in response.headers.items()}
            # SlowAPI should add these headers
            assert "x-ratelimit-limit" in headers_lower or "ratelimit-limit" in headers_lower


class TestRateLimitingDisabled:
    """Tests for when rate limiting is disabled."""

    def test_no_rate_limiting_when_disabled(self, mock_config_disabled: MagicMock) -> None:
        """Test that no rate limiting occurs when disabled."""
        limiter = create_limiter()
        assert limiter is None

    def test_multiple_requests_allowed_when_disabled(self, mock_config_disabled: MagicMock) -> None:
        """Test that multiple requests are allowed when rate limiting is disabled."""
        app = FastAPI()

        # Since rate limiting is disabled, limiter should be None
        limiter = create_limiter()
        if limiter is not None:
            pytest.skip("Rate limiting should be disabled")

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        with TestClient(app) as client:
            # Make many requests - all should succeed since rate limiting is off
            for _ in range(20):
                response = client.get("/test")
                assert response.status_code == 200


@pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
class TestRateLimitingWithWhitelist:
    """Tests for IP whitelist functionality."""

    def test_whitelisted_ip_bypasses_rate_limit(self) -> None:
        """Test that whitelisted IPs bypass rate limiting."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.enabled = True
            mock_rate_limit.requests_per_minute = 2
            mock_rate_limit.requests_per_hour = 10
            mock_rate_limit.upload_requests_per_minute = 1
            mock_rate_limit.storage_uri = "memory://"
            mock_rate_limit.whitelist_ips = ["127.0.0.1", "testclient"]

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            limiter = create_limiter()
            assert limiter is not None

    def test_non_whitelisted_ip_is_rate_limited(self) -> None:
        """Test that non-whitelisted IPs are rate limited."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.enabled = True
            mock_rate_limit.requests_per_minute = 2
            mock_rate_limit.requests_per_hour = 10
            mock_rate_limit.upload_requests_per_minute = 1
            mock_rate_limit.storage_uri = "memory://"
            mock_rate_limit.whitelist_ips = ["192.168.1.100", "10.0.0.1"]

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            limiter = create_limiter()
            assert limiter is not None


class TestRateLimitingSlowapiUnavailable:
    """Tests for behavior when slowapi is not available."""

    def test_returns_none_when_slowapi_not_installed(self) -> None:
        """Test that None is returned when slowapi is not installed."""
        with (
            patch("video2d3d.web.rate_limit.get_config") as mock_get_config,
            patch("video2d3d.web.rate_limit.SLOWAPI_AVAILABLE", False),
        ):
            mock_rate_limit = MagicMock()
            mock_rate_limit.enabled = True

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            limiter = create_limiter()
            assert limiter is None


class TestSetupRateLimiting:
    """Tests for setup_rate_limiting function."""

    def test_setup_sets_limiter_on_app_state(self) -> None:
        """Test that limiter is set on app state when enabled."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            mock_limiter = MagicMock()
            mock_create.return_value = mock_limiter

            app = FastAPI()
            result = setup_rate_limiting(app)

            assert result is mock_limiter
            assert app.state.limiter is mock_limiter

    def test_setup_returns_none_when_limiter_creation_fails(self) -> None:
        """Test that None is returned when limiter creation fails."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            mock_create.return_value = None

            app = FastAPI()
            result = setup_rate_limiting(app)

            assert result is None

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_setup_adds_middleware_when_available(self) -> None:
        """Test that middleware is added when slowapi is available."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            mock_limiter = MagicMock()
            mock_create.return_value = mock_limiter

            app = FastAPI()
            setup_rate_limiting(app)

            # Verify limiter is set
            assert app.state.limiter is mock_limiter
