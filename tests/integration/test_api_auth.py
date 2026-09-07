"""Integration tests for authentication API endpoints.

Tests cover:
- User registration (/api/v1/auth/register)
- User login (/api/v1/auth/login)
- Token refresh (/api/v1/auth/refresh)
- Get current user (/api/v1/auth/me)
- Logout (/api/v1/auth/logout)
- Role-based access control
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from video2d3d.web.exceptions import register_exception_handlers

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def temp_db() -> Generator[Path, None, None]:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_auth.db"
        yield db_path


@pytest.fixture
def app(temp_db: Path) -> Generator[FastAPI, None, None]:
    """Create test FastAPI app with auth router."""
    # Reset database module state
    import video2d3d.web.auth.database as db_module
    import video2d3d.web.auth.jwt_service as jwt_module

    db_module._engine = None
    db_module._session_factory = None
    jwt_module._auth_config = None

    # Initialize database with temp path
    db_module.init_database(temp_db)

    # Create app with auth router
    from fastapi import FastAPI

    from video2d3d.web.auth.router import router as auth_router

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

    yield app

    # Cleanup
    db_module._engine = None
    db_module._session_factory = None
    jwt_module._auth_config = None


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


class TestRegisterEndpoint:
    """Tests for POST /auth/register endpoint."""

    def test_register_success(self, client: TestClient) -> None:
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["username"] == "testuser"

    def test_register_duplicate_username(self, client: TestClient) -> None:
        """Test registration with duplicate username fails."""
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": "user1@example.com",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )

        # Second registration with same username
        response = client.post(
            "/auth/register",
            json={
                "email": "user2@example.com",
                "username": "testuser",  # Same username
                "password": "SecurePass456",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.json().get("detail", response.json().get("message", "")).lower()

    def test_register_duplicate_email(self, client: TestClient) -> None:
        """Test registration with duplicate email fails."""
        # First registration
        client.post(
            "/auth/register",
            json={
                "email": "same@example.com",
                "username": "user1",
                "password": "SecurePass123",
            },
        )

        # Second registration with same email
        response = client.post(
            "/auth/register",
            json={
                "email": "same@example.com",  # Same email
                "username": "user2",
                "password": "SecurePass456",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json().get("detail", response.json().get("message", "")).lower()

    def test_register_invalid_email(self, client: TestClient) -> None:
        """Test registration with invalid email fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "notanemail",
                "username": "testuser",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_weak_password(self, client: TestClient) -> None:
        """Test registration with weak password fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "weak",  # Too short, no uppercase, no digit
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_username_too_short(self, client: TestClient) -> None:
        """Test registration with too short username fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "ab",  # Too short
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_username_too_long(self, client: TestClient) -> None:
        """Test registration with too long username fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "a" * 51,  # Too long
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_username_invalid_characters(self, client: TestClient) -> None:
        """Test registration with invalid username characters fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "user@name!",  # Invalid characters
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    @pytest.fixture
    def registered_user(self, client: TestClient) -> dict:
        """Create a registered user for login tests."""
        response = client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "SecurePass123",
            },
        )
        return response.json()

    def test_login_with_username(self, client: TestClient, registered_user: dict) -> None:
        """Test login with username succeeds."""
        response = client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "loginuser"

    def test_login_with_email(self, client: TestClient, registered_user: dict) -> None:
        """Test login with email succeeds."""
        response = client.post(
            "/auth/login",
            json={
                "username": "login@example.com",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client: TestClient, registered_user: dict) -> None:
        """Test login with wrong password fails."""
        response = client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        """Test login with non-existent user fails."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "SomePassword123",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_returns_user_info(self, client: TestClient, registered_user: dict) -> None:
        """Test login returns user information."""
        response = client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "SecurePass123",
            },
        )
        data = response.json()
        assert data["user"]["email"] == "login@example.com"
        assert data["user"]["username"] == "loginuser"
        assert data["user"]["role"] == "user"
        assert data["user"]["is_active"] is True


class TestRefreshEndpoint:
    """Tests for POST /auth/refresh endpoint."""

    @pytest.fixture
    def tokens(self, client: TestClient) -> dict:
        """Register a user and return tokens."""
        response = client.post(
            "/auth/register",
            json={
                "email": "refresh@example.com",
                "username": "refreshuser",
                "password": "SecurePass123",
            },
        )
        return response.json()

    def test_refresh_success(self, client: TestClient, tokens: dict) -> None:
        """Test token refresh succeeds."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different
        assert data["access_token"] != tokens["access_token"]

    def test_refresh_invalid_token(self, client: TestClient) -> None:
        """Test refresh with invalid token fails."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_access_token_fails(self, client: TestClient, tokens: dict) -> None:
        """Test refresh with access token instead of refresh token fails."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["access_token"]},  # Wrong token type
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    @pytest.fixture
    def auth_headers(self, client: TestClient) -> dict:
        """Register a user and return auth headers."""
        response = client.post(
            "/auth/register",
            json={
                "email": "me@example.com",
                "username": "meuser",
                "password": "SecurePass123",
            },
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_me_success(self, client: TestClient, auth_headers: dict) -> None:
        """Test getting current user info succeeds."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["username"] == "meuser"
        assert data["role"] == "user"

    def test_me_no_token(self, client: TestClient) -> None:
        """Test getting current user without token fails."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_invalid_token(self, client: TestClient) -> None:
        """Test getting current user with invalid token fails."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_refresh_token_fails(self, client: TestClient) -> None:
        """Test getting current user with refresh token fails."""
        # Register and get tokens
        register_response = client.post(
            "/auth/register",
            json={
                "email": "me2@example.com",
                "username": "meuser2",
                "password": "SecurePass123",
            },
        )
        refresh_token = register_response.json()["refresh_token"]

        # Try to access /me with refresh token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    @pytest.fixture
    def auth_headers(self, client: TestClient) -> dict:
        """Register a user and return auth headers."""
        response = client.post(
            "/auth/register",
            json={
                "email": "logout@example.com",
                "username": "logoutuser",
                "password": "SecurePass123",
            },
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_logout_success(self, client: TestClient, auth_headers: dict) -> None:
        """Test logout succeeds."""
        response = client.post("/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

    def test_logout_no_token(self, client: TestClient) -> None:
        """Test logout without token fails."""
        response = client.post("/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRoleBasedAccess:
    """Tests for role-based access control."""

    def test_user_role_in_response(self, client: TestClient) -> None:
        """Test registered user gets 'user' role."""
        response = client.post(
            "/auth/register",
            json={
                "email": "role@example.com",
                "username": "roleuser",
                "password": "SecurePass123",
            },
        )
        data = response.json()
        assert data["user"]["role"] == "user"

    def test_user_role_is_lowercase(self, client: TestClient) -> None:
        """Test user role is lowercase in response."""
        response = client.post(
            "/auth/register",
            json={
                "email": "role2@example.com",
                "username": "roleuser2",
                "password": "SecurePass123",
            },
        )
        data = response.json()
        assert data["user"]["role"] == "user"


class TestTokenExpiration:
    """Tests for token expiration in responses."""

    def test_token_response_has_expires_in(self, client: TestClient) -> None:
        """Test token response includes expires_in."""
        response = client.post(
            "/auth/register",
            json={
                "email": "expire@example.com",
                "username": "expireuser",
                "password": "SecurePass123",
            },
        )
        data = response.json()
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation of auth endpoints."""

    def test_auth_endpoints_in_openapi(self, app: FastAPI) -> None:
        """Test auth endpoints are in OpenAPI schema."""
        openapi = app.openapi()
        paths = openapi["paths"]

        assert "/auth/register" in paths
        assert "/auth/login" in paths
        assert "/auth/refresh" in paths
        assert "/auth/me" in paths
        assert "/auth/logout" in paths

    def test_auth_endpoints_have_auth_tag(self, app: FastAPI) -> None:
        """Test auth endpoints have Authentication tag."""
        openapi = app.openapi()

        register_tags = openapi["paths"]["/auth/register"]["post"]["tags"]
        assert "Authentication" in register_tags


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_login_case_insensitive_username(self, client: TestClient) -> None:
        """Test login is case-insensitive for username."""
        # Register with mixed case
        client.post(
            "/auth/register",
            json={
                "email": "case@example.com",
                "username": "TestUser",
                "password": "SecurePass123",
            },
        )

        # Login with lowercase
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",  # lowercase
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_login_case_insensitive_email(self, client: TestClient) -> None:
        """Test login is case-insensitive for email."""
        # Register
        client.post(
            "/auth/register",
            json={
                "email": "Case@Example.com",
                "username": "emailuser",
                "password": "SecurePass123",
            },
        )

        # Login with lowercase email
        response = client.post(
            "/auth/login",
            json={
                "username": "case@example.com",  # lowercase
                "password": "SecurePass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    def test_username_normalized_to_lowercase(self, client: TestClient) -> None:
        """Test username is normalized to lowercase on registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "normalize@example.com",
                "username": "MixedCase",
                "password": "SecurePass123",
            },
        )
        data = response.json()
        assert data["user"]["username"] == "mixedcase"

    def test_email_normalized_to_lowercase(self, client: TestClient) -> None:
        """Test email is normalized to lowercase on registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "UPPER@EXAMPLE.COM",
                "username": "loweruser",
                "password": "SecurePass123",
            },
        )
        data = response.json()
        assert data["user"]["email"] == "upper@example.com"
