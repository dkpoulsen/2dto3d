"""Unit tests for authentication schemas (Pydantic models).

Tests cover:
- UserRole enum validation
- UserCreate validation (email, username, password)
- UserLogin validation
- UserResponse serialization
- TokenResponse structure
- Field validators
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError as PydanticValidationError

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

if TYPE_CHECKING:
    pass


class TestUserRole:
    """Tests for UserRole enum."""

    def test_user_role_values(self) -> None:
        """Test UserRole enum values."""
        assert UserRole.USER.value == "user"
        assert UserRole.ADMIN.value == "admin"

    def test_user_role_from_string(self) -> None:
        """Test UserRole can be created from string."""
        assert UserRole("user") == UserRole.USER
        assert UserRole("admin") == UserRole.ADMIN

    def test_user_role_invalid_value(self) -> None:
        """Test UserRole rejects invalid values."""
        with pytest.raises(ValueError):
            UserRole("superadmin")


class TestUserCreate:
    """Tests for UserCreate model."""

    def test_valid_user_create(self) -> None:
        """Test valid user creation data."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePass123",
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "SecurePass123"

    def test_email_validation_valid(self) -> None:
        """Test valid email formats are accepted."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@test-domain.org",
        ]
        for email in valid_emails:
            user = UserCreate(
                email=email,
                username="testuser",
                password="SecurePass123",
            )
            assert user.email == email

    def test_email_validation_invalid(self) -> None:
        """Test invalid email formats are rejected."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
        ]
        for email in invalid_emails:
            with pytest.raises(PydanticValidationError):
                UserCreate(
                    email=email,
                    username="testuser",
                    password="SecurePass123",
                )

    def test_username_validation_valid(self) -> None:
        """Test valid username formats are accepted."""
        valid_usernames = [
            "simple",
            "with_underscore",
            "with-hyphen",
            "MixedCase",
            "user123",
            "abc",
            "a_valid-user_name",
        ]
        for username in valid_usernames:
            user = UserCreate(
                email="test@example.com",
                username=username,
                password="SecurePass123",
            )
            # Should be lowercased
            assert user.username == username.lower()

    def test_username_validation_invalid_characters(self) -> None:
        """Test username with invalid characters is rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="user@name!",
                password="SecurePass123",
            )
        assert "alphanumeric" in str(exc_info.value).lower()

    def test_username_validation_too_short(self) -> None:
        """Test username below minimum length is rejected."""
        with pytest.raises(PydanticValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="SecurePass123",
            )

    def test_username_validation_too_long(self) -> None:
        """Test username above maximum length is rejected."""
        with pytest.raises(PydanticValidationError):
            UserCreate(
                email="test@example.com",
                username="a" * 51,
                password="SecurePass123",
            )

    def test_password_validation_valid(self) -> None:
        """Test valid passwords are accepted."""
        valid_passwords = [
            "Password123",
            "Abcdefg1",
            "UPPER123lower",
            "Mix3dCase",
        ]
        for password in valid_passwords:
            user = UserCreate(
                email="test@example.com",
                username="testuser",
                password=password,
            )
            assert user.password == password

    def test_password_validation_too_short(self) -> None:
        """Test password below minimum length is rejected."""
        with pytest.raises(PydanticValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="Pass1",  # 5 chars, too short
            )

    def test_password_validation_no_uppercase(self) -> None:
        """Test password without uppercase letter is rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="lowercase123",
            )
        assert "uppercase" in str(exc_info.value).lower()

    def test_password_validation_no_lowercase(self) -> None:
        """Test password without lowercase letter is rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="UPPERCASE123",
            )
        assert "lowercase" in str(exc_info.value).lower()

    def test_password_validation_no_digit(self) -> None:
        """Test password without digit is rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="NoDigitsHere",
            )
        assert "digit" in str(exc_info.value).lower()

    def test_username_is_lowercased(self) -> None:
        """Test username is automatically lowercased."""
        user = UserCreate(
            email="test@example.com",
            username="TestUser",
            password="SecurePass123",
        )
        assert user.username == "testuser"


class TestUserLogin:
    """Tests for UserLogin model."""

    def test_valid_user_login(self) -> None:
        """Test valid login credentials."""
        login = UserLogin(
            username="testuser",
            password="SecurePass123",
        )
        assert login.username == "testuser"
        assert login.password == "SecurePass123"

    def test_login_with_email(self) -> None:
        """Test login with email address."""
        login = UserLogin(
            username="test@example.com",
            password="SecurePass123",
        )
        assert login.username == "test@example.com"

    def test_login_required_fields(self) -> None:
        """Test username and password are required."""
        with pytest.raises(PydanticValidationError) as exc_info:
            UserLogin()
        assert "username" in str(exc_info.value)

        with pytest.raises(PydanticValidationError) as exc_info:
            UserLogin(username="testuser")
        assert "password" in str(exc_info.value)


class TestUserResponse:
    """Tests for UserResponse model."""

    def test_valid_user_response(self) -> None:
        """Test valid user response."""
        now = datetime.utcnow()
        response = UserResponse(
            user_id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=now,
            last_login=now,
        )
        assert response.user_id == "user-123"
        assert response.email == "test@example.com"
        assert response.username == "testuser"
        assert response.role == UserRole.USER
        assert response.is_active is True
        assert response.created_at == now
        assert response.last_login == now

    def test_user_response_defaults(self) -> None:
        """Test UserResponse default values."""
        now = datetime.utcnow()
        response = UserResponse(
            user_id="user-123",
            email="test@example.com",
            username="testuser",
            created_at=now,
        )
        assert response.role == UserRole.USER
        assert response.is_active is True
        assert response.last_login is None

    def test_user_response_admin_role(self) -> None:
        """Test UserResponse with admin role."""
        now = datetime.utcnow()
        response = UserResponse(
            user_id="admin-123",
            email="admin@example.com",
            username="adminuser",
            role=UserRole.ADMIN,
            created_at=now,
        )
        assert response.role == UserRole.ADMIN

    def test_user_response_serialization(self) -> None:
        """Test UserResponse JSON serialization."""
        now = datetime.utcnow()
        response = UserResponse(
            user_id="user-123",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=now,
            last_login=None,
        )
        data = response.model_dump()
        assert data["user_id"] == "user-123"
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["role"] == UserRole.USER.value
        assert data["is_active"] is True


class TestTokenRefreshRequest:
    """Tests for TokenRefreshRequest model."""

    def test_valid_token_refresh_request(self) -> None:
        """Test valid token refresh request."""
        request = TokenRefreshRequest(refresh_token="some-refresh-token")
        assert request.refresh_token == "some-refresh-token"

    def test_token_refresh_required(self) -> None:
        """Test refresh_token is required."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TokenRefreshRequest()
        assert "refresh_token" in str(exc_info.value)


class TestTokenPayload:
    """Tests for TokenPayload model."""

    def test_valid_token_payload(self) -> None:
        """Test valid token payload."""
        payload = TokenPayload(
            sub="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        assert payload.sub == "user-123"
        assert payload.username == "testuser"
        assert payload.role == UserRole.USER
        assert payload.type == "access"

    def test_token_payload_with_timestamps(self) -> None:
        """Test token payload with exp/iat timestamps."""
        now = datetime.utcnow()
        payload = TokenPayload(
            sub="user-123",
            username="testuser",
            role=UserRole.USER,
            exp=now,
            iat=now,
        )
        assert payload.exp == now
        assert payload.iat == now

    def test_token_payload_refresh_type(self) -> None:
        """Test token payload with refresh type."""
        payload = TokenPayload(
            sub="user-123",
            username="testuser",
            role=UserRole.USER,
            type="refresh",
        )
        assert payload.type == "refresh"


class TestTokenResponse:
    """Tests for TokenResponse model."""

    def test_valid_token_response(self) -> None:
        """Test valid token response."""
        now = datetime.utcnow()
        user = UserResponse(
            user_id="user-123",
            email="test@example.com",
            username="testuser",
            created_at=now,
        )
        response = TokenResponse(
            access_token="access-token",
            refresh_token="refresh-token",
            token_type="bearer",
            expires_in=3600,
            user=user,
        )
        assert response.access_token == "access-token"
        assert response.refresh_token == "refresh-token"
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.user.user_id == "user-123"

    def test_token_response_default_token_type(self) -> None:
        """Test token_response defaults to bearer token type."""
        now = datetime.utcnow()
        user = UserResponse(
            user_id="user-123",
            email="test@example.com",
            username="testuser",
            created_at=now,
        )
        response = TokenResponse(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_in=3600,
            user=user,
        )
        assert response.token_type == "bearer"


class TestAuthConfig:
    """Tests for AuthConfig model."""

    def test_auth_config_defaults(self) -> None:
        """Test AuthConfig default values."""
        config = AuthConfig()
        assert config.secret_key == "change-me-in-production"
        assert config.algorithm == "HS256"
        assert config.access_token_expire_minutes == 30
        assert config.refresh_token_expire_days == 7

    def test_auth_config_custom_values(self) -> None:
        """Test AuthConfig with custom values."""
        config = AuthConfig(
            secret_key="my-super-secret-key",
            algorithm="HS512",
            access_token_expire_minutes=60,
            refresh_token_expire_days=14,
        )
        assert config.secret_key == "my-super-secret-key"
        assert config.algorithm == "HS512"
        assert config.access_token_expire_minutes == 60
        assert config.refresh_token_expire_days == 14


class TestModelEdgeCases:
    """Tests for edge cases in auth models."""

    def test_user_create_min_length_username(self) -> None:
        """Test minimum length username (3 chars)."""
        user = UserCreate(
            email="test@example.com",
            username="abc",
            password="SecurePass123",
        )
        assert user.username == "abc"

    def test_user_create_max_length_username(self) -> None:
        """Test maximum length username (50 chars)."""
        long_username = "a" * 50
        user = UserCreate(
            email="test@example.com",
            username=long_username,
            password="SecurePass123",
        )
        assert user.username == long_username

    def test_user_create_min_length_password(self) -> None:
        """Test minimum length password (8 chars)."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="Aa1bcdef",  # 8 chars with upper, lower, digit
        )
        assert user.password == "Aa1bcdef"

    def test_user_create_max_length_password(self) -> None:
        """Test maximum length password (128 chars)."""
        long_password = "Aa1" + "b" * 125  # 128 chars with upper, lower, digit
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password=long_password,
        )
        assert user.password == long_password

    def test_user_response_inactive_user(self) -> None:
        """Test UserResponse for inactive user."""
        now = datetime.utcnow()
        response = UserResponse(
            user_id="user-123",
            email="test@example.com",
            username="testuser",
            is_active=False,
            created_at=now,
        )
        assert response.is_active is False
