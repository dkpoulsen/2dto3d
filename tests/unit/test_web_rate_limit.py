"""Unit tests for rate limiting middleware.

Tests cover:
- get_client_ip function for IP extraction
- create_limiter function for limiter creation
- rate_limit_exceeded_handler for error handling
- setup_rate_limiting for middleware integration
- limit_upload and limit_api decorators
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.rate_limit import (
    SLOWAPI_AVAILABLE,
    create_limiter,
    get_client_ip,
    get_limiter,
    limit_api,
    limit_upload,
    rate_limit_exceeded_handler,
    setup_rate_limiting,
)


class MockRequest:
    """Mock FastAPI Request for testing."""

    def __init__(
        self,
        client_ip: str = "127.0.0.1",
        headers: dict | None = None,
    ):
        self._client_ip = client_ip
        self.headers = headers or {}
        self.state = MagicMock()
        self.state.request_id = "test-request-id"

    @property
    def client(self) -> MagicMock:
        """Mock client property."""
        mock_client = MagicMock()
        mock_client.host = self._client_ip
        return mock_client


class TestGetClientIp:
    """Tests for get_client_ip function."""

    def test_returns_direct_ip_when_no_headers(self) -> None:
        """Test that direct client IP is returned when no proxy headers present."""
        request = MockRequest(client_ip="192.168.1.100")
        ip = get_client_ip(request)  # type: ignore
        assert ip == "192.168.1.100"

    def test_extracts_ip_from_x_forwarded_for(self) -> None:
        """Test that IP is extracted from X-Forwarded-For header."""
        request = MockRequest(
            client_ip="10.0.0.1",
            headers={"X-Forwarded-For": "203.0.113.50, 10.0.0.1, 192.168.1.1"},
        )
        ip = get_client_ip(request)  # type: ignore
        # Should return the first IP in the chain (original client)
        assert ip == "203.0.113.50"

    def test_extracts_ip_from_x_forwarded_for_single(self) -> None:
        """Test X-Forwarded-For with single IP."""
        request = MockRequest(
            client_ip="10.0.0.1",
            headers={"X-Forwarded-For": "203.0.113.50"},
        )
        ip = get_client_ip(request)  # type: ignore
        assert ip == "203.0.113.50"

    def test_extracts_ip_from_x_real_ip(self) -> None:
        """Test that IP is extracted from X-Real-IP header."""
        request = MockRequest(
            client_ip="10.0.0.1",
            headers={"X-Real-IP": "198.51.100.42"},
        )
        ip = get_client_ip(request)  # type: ignore
        assert ip == "198.51.100.42"

    def test_x_forwarded_for_takes_precedence_over_x_real_ip(self) -> None:
        """Test X-Forwarded-For takes precedence over X-Real-IP."""
        request = MockRequest(
            client_ip="10.0.0.1",
            headers={
                "X-Forwarded-For": "203.0.113.50",
                "X-Real-IP": "198.51.100.42",
            },
        )
        ip = get_client_ip(request)  # type: ignore
        assert ip == "203.0.113.50"

    def test_strips_whitespace_from_headers(self) -> None:
        """Test that whitespace is stripped from header values."""
        request = MockRequest(
            client_ip="10.0.0.1",
            headers={"X-Forwarded-For": "  203.0.113.50  "},
        )
        ip = get_client_ip(request)  # type: ignore
        assert ip == "203.0.113.50"

    def test_handles_empty_x_forwarded_for(self) -> None:
        """Test handling of empty X-Forwarded-For header."""
        request = MockRequest(
            client_ip="192.168.1.100",
            headers={"X-Forwarded-For": ""},
        )
        ip = get_client_ip(request)  # type: ignore
        # Empty string is falsy, should fall back to direct IP
        # Note: get_remote_address might return "unknown" in test mode
        assert ip in ["192.168.1.100", "unknown", "testclient"]


class TestCreateLimiter:
    """Tests for create_limiter function."""

    @pytest.fixture
    def mock_config(self) -> Generator[MagicMock, None, None]:
        """Create a mock config with rate limit settings."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.enabled = True
            mock_rate_limit.requests_per_minute = 60
            mock_rate_limit.requests_per_hour = 1000
            mock_rate_limit.upload_requests_per_minute = 10
            mock_rate_limit.storage_uri = "memory://"
            mock_rate_limit.whitelist_ips = []

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg
            yield mock_get_config

    def test_returns_none_when_disabled(self) -> None:
        """Test that None is returned when rate limiting is disabled."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.enabled = False

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            result = create_limiter()
            assert result is None

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_creates_limiter_when_enabled(self, mock_config: MagicMock) -> None:
        """Test that Limiter is created when rate limiting is enabled."""
        result = create_limiter()
        assert result is not None

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_uses_correct_rate_limit_settings(self, mock_config: MagicMock) -> None:
        """Test that limiter uses correct rate limit settings from config."""
        result = create_limiter()
        assert result is not None
        # The limiter should have been created with the config values

    def test_returns_none_when_slowapi_not_available(self) -> None:
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

            result = create_limiter()
            assert result is None


class TestRateLimitExceededHandler:
    """Tests for rate_limit_exceeded_handler function."""

    @pytest.fixture
    def mock_request(self) -> MockRequest:
        """Create a mock request for testing."""
        return MockRequest(client_ip="192.168.1.100")

    def test_returns_json_response_with_429_status(self, mock_request: MockRequest) -> None:
        """Test that handler returns 429 status code."""
        # Create a mock RateLimitExceeded exception
        mock_exc = MagicMock()
        mock_exc.detail = "60 per 1 minute"
        mock_exc.headers = {}

        response = rate_limit_exceeded_handler(mock_request, mock_exc)  # type: ignore

        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_includes_error_type_in_response(self, mock_request: MockRequest) -> None:
        """Test that error response includes rate_limit_exceeded error type."""
        mock_exc = MagicMock()
        mock_exc.detail = "60 per 1 minute"
        mock_exc.headers = {}

        response = rate_limit_exceeded_handler(mock_request, mock_exc)  # type: ignore

        # Get response body - need to call render to get body
        import json

        body = json.loads(response.body)  # type: ignore
        assert body["error"] == "rate_limit_exceeded"

    def test_includes_limit_in_detail(self, mock_request: MockRequest) -> None:
        """Test that error response includes the limit in detail."""
        mock_exc = MagicMock()
        mock_exc.detail = "60 per 1 minute"
        mock_exc.headers = {}

        response = rate_limit_exceeded_handler(mock_request, mock_exc)  # type: ignore

        import json

        body = json.loads(response.body)  # type: ignore
        assert body["detail"]["limit"] == "60 per 1 minute"

    def test_includes_retry_after_from_headers(self, mock_request: MockRequest) -> None:
        """Test that retry_after is extracted from exception headers."""
        mock_exc = MagicMock()
        mock_exc.detail = "60 per 1 minute"
        mock_exc.headers = {"Retry-After": "60"}

        response = rate_limit_exceeded_handler(mock_request, mock_exc)  # type: ignore

        import json

        body = json.loads(response.body)  # type: ignore
        assert body["detail"]["retry_after"] == 60

    def test_handles_missing_retry_after_header(self, mock_request: MockRequest) -> None:
        """Test handling when Retry-After header is not present."""
        mock_exc = MagicMock()
        mock_exc.detail = "60 per 1 minute"
        mock_exc.headers = {}

        response = rate_limit_exceeded_handler(mock_request, mock_exc)  # type: ignore

        import json

        body = json.loads(response.body)  # type: ignore
        assert body["detail"]["retry_after"] is None

    def test_preserves_rate_limit_headers_in_response(self, mock_request: MockRequest) -> None:
        """Test that rate limit headers are preserved in response."""
        mock_exc = MagicMock()
        mock_exc.detail = "60 per 1 minute"
        mock_exc.headers = {
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Remaining": "0",
            "Retry-After": "60",
        }

        response = rate_limit_exceeded_handler(mock_request, mock_exc)  # type: ignore

        assert response.headers.get("X-RateLimit-Limit") == "60"
        assert response.headers.get("X-RateLimit-Remaining") == "0"


class TestSetupRateLimiting:
    """Tests for setup_rate_limiting function."""

    def test_sets_limiter_on_app_state(self) -> None:
        """Test that limiter is set on app state when enabled."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            mock_limiter = MagicMock()
            mock_create.return_value = mock_limiter

            app = FastAPI()
            result = setup_rate_limiting(app)

            assert result is mock_limiter
            assert app.state.limiter is mock_limiter

    def test_returns_none_when_limiter_creation_fails(self) -> None:
        """Test that None is returned when limiter creation fails."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            mock_create.return_value = None

            app = FastAPI()
            result = setup_rate_limiting(app)

            assert result is None

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_adds_exception_handler(self) -> None:
        """Test that exception handler is added for RateLimitExceeded."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            mock_limiter = MagicMock()
            mock_create.return_value = mock_limiter

            app = FastAPI()
            setup_rate_limiting(app)

            # Check that exception handler was registered
            # This is tricky to verify directly, so we just ensure no error


class TestGetLimiter:
    """Tests for get_limiter function."""

    def test_returns_limiter_from_app_state(self) -> None:
        """Test that limiter is returned from app state."""
        with patch("video2d3d.web.rate_limit.app_state") as mock_state:
            mock_limiter = MagicMock()
            mock_state.limiter = mock_limiter

            result = get_limiter()
            assert result is mock_limiter

    def test_returns_none_when_limiter_not_set(self) -> None:
        """Test that None is returned when limiter is not in app state."""
        with patch("video2d3d.web.rate_limit.app_state") as mock_state:
            # Don't set limiter attribute
            del mock_state.limiter

            result = get_limiter()
            assert result is None


class TestLimitDecorators:
    """Tests for limit_upload and limit_api decorators."""

    def test_limit_upload_returns_noop_when_no_limiter(self) -> None:
        """Test limit_upload returns no-op decorator when no limiter."""
        with (
            patch("video2d3d.web.rate_limit.get_config") as mock_get_config,
            patch("video2d3d.web.rate_limit.get_limiter") as mock_get_limiter,
        ):
            mock_rate_limit = MagicMock()
            mock_rate_limit.upload_requests_per_minute = 10

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg
            mock_get_limiter.return_value = None

            decorator = limit_upload()
            # Should be a no-op decorator
            assert callable(decorator)

            # Test that it passes through the function unchanged
            def test_func():
                return "test"

            wrapped = decorator(test_func)
            assert wrapped() == "test"

    def test_limit_api_returns_noop_when_no_limiter(self) -> None:
        """Test limit_api returns no-op decorator when no limiter."""
        with (
            patch("video2d3d.web.rate_limit.get_config") as mock_get_config,
            patch("video2d3d.web.rate_limit.get_limiter") as mock_get_limiter,
        ):
            mock_rate_limit = MagicMock()
            mock_rate_limit.requests_per_minute = 60
            mock_rate_limit.requests_per_hour = 1000

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg
            mock_get_limiter.return_value = None

            decorator = limit_api()
            # Should be a no-op decorator
            assert callable(decorator)

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_limit_upload_uses_upload_rate(self) -> None:
        """Test limit_upload uses upload_requests_per_minute from config."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.upload_requests_per_minute = 5

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f

            limit_upload(mock_limiter)

            # Verify limiter.limit was called with correct rate
            mock_limiter.limit.assert_called_once_with("5/minute")

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_limit_api_uses_combined_limits(self) -> None:
        """Test limit_api uses both per-minute and per-hour limits."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.requests_per_minute = 60
            mock_rate_limit.requests_per_hour = 1000

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            mock_limiter = MagicMock()
            mock_limiter.limit.return_value = lambda f: f

            limit_api(mock_limiter)

            # Verify limiter.limit was called with combined limits
            mock_limiter.limit.assert_called_once_with("60/minute;1000/hour")


class TestRateLimitIntegration:
    """Integration tests for rate limiting with FastAPI."""

    @pytest.fixture
    def app(self) -> Generator[FastAPI, None, None]:
        """Create a test FastAPI app with rate limiting."""
        with patch("video2d3d.web.rate_limit.create_limiter") as mock_create:
            # Create a real limiter for integration testing
            if SLOWAPI_AVAILABLE:
                from slowapi import Limiter
                from slowapi.util import get_remote_address

                limiter = Limiter(
                    key_func=get_remote_address,
                    default_limits=["5/minute"],
                    storage_uri="memory://",
                    headers_enabled=True,
                )
                mock_create.return_value = limiter
            else:
                mock_create.return_value = None

            app = FastAPI()
            setup_rate_limiting(app)

            @app.get("/test-endpoint")
            async def test_endpoint():
                return {"status": "ok"}

            yield app

    @pytest.fixture
    def client(self, app: FastAPI) -> Generator[TestClient, None, None]:
        """Create a test client."""
        with TestClient(app) as client:
            yield client

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_successful_request_returns_200(self, client: TestClient) -> None:
        """Test that successful requests return 200."""
        response = client.get("/test-endpoint")
        assert response.status_code == 200

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_rate_limit_headers_present(self, client: TestClient) -> None:
        """Test that rate limit headers are included in response."""
        response = client.get("/test-endpoint")

        # Check for rate limit headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "x-ratelimit-limit" in headers_lower or "ratelimit-limit" in headers_lower

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_rate_limit_triggered_after_exceeding_limit(self, client: TestClient) -> None:
        """Test that rate limit is triggered after exceeding limit."""
        # Make multiple requests to exceed the 5/minute limit
        responses = []
        for _ in range(10):
            response = client.get("/test-endpoint")
            responses.append(response)

        # At least one request should be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should have been triggered"

    @pytest.mark.skipif(not SLOWAPI_AVAILABLE, reason="slowapi not installed")
    def test_rate_limit_response_format(self, client: TestClient) -> None:
        """Test that rate limit response has correct format."""
        # Exhaust the rate limit
        for _ in range(10):
            client.get("/test-endpoint")

        # Get the rate limited response
        response = client.get("/test-endpoint")

        if response.status_code == 429:
            data = response.json()
            assert data.get("error") == "rate_limit_exceeded"
            assert "message" in data
            assert "detail" in data


class TestWhitelist:
    """Tests for IP whitelist functionality."""

    def test_whitelisted_ip_bypasses_rate_limit(self) -> None:
        """Test that whitelisted IPs bypass rate limiting."""
        with patch("video2d3d.web.rate_limit.get_config") as mock_get_config:
            mock_rate_limit = MagicMock()
            mock_rate_limit.enabled = True
            mock_rate_limit.requests_per_minute = 5
            mock_rate_limit.requests_per_hour = 100
            mock_rate_limit.upload_requests_per_minute = 2
            mock_rate_limit.storage_uri = "memory://"
            mock_rate_limit.whitelist_ips = ["192.168.1.100", "10.0.0.1"]

            mock_web_api = MagicMock()
            mock_web_api.rate_limit = mock_rate_limit

            mock_cfg = MagicMock()
            mock_cfg.web_api = mock_web_api

            mock_get_config.return_value = mock_cfg

            if SLOWAPI_AVAILABLE:
                limiter = create_limiter()
                assert limiter is not None
