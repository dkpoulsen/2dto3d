"""Unit tests for JWT authentication service.

Tests cover:
- Password hashing and verification
- JWT token creation (access and refresh)
- JWT token decoding and validation
- Token expiration handling
- User authentication
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

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
from video2d3d.web.auth.schemas import UserRole

if TYPE_CHECKING:
    pass


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self) -> None:
        """Test hash_password returns a string."""
        hashed = hash_password("testpassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_is_bcrypt(self) -> None:
        """Test hash_password produces bcrypt hash."""
        hashed = hash_password("testpassword")
        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")

    def test_hash_password_different_each_time(self) -> None:
        """Test hash_password produces different hashes for same password."""
        password = "testpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Due to salt, hashes should be different
        assert hash1 != hash2

    def test_verify_password_correct(self) -> None:
        """Test verify_password with correct password."""
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """Test verify_password with incorrect password."""
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self) -> None:
        """Test verify_password with empty password."""
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password("", hashed) is False

    def test_hash_password_unicode(self) -> None:
        """Test hash_password handles unicode characters."""
        password = "pässwörd123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_long(self) -> None:
        """Test hash_password handles long passwords."""
        password = "a" * 100
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestTokenCreation:
    """Tests for JWT token creation."""

    def test_create_access_token_returns_string(self) -> None:
        """Test create_access_token returns a string."""
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_returns_string(self) -> None:
        """Test create_refresh_token returns a string."""
        token = create_refresh_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_three_parts(self) -> None:
        """Test access token has JWT structure (3 parts)."""
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_refresh_token_has_three_parts(self) -> None:
        """Test refresh token has JWT structure (3 parts)."""
        token = create_refresh_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_tokens_are_unique(self) -> None:
        """Test different users get different tokens."""
        token1 = create_access_token(
            user_id="user-1",
            username="user1",
            role=UserRole.USER,
        )
        token2 = create_access_token(
            user_id="user-2",
            username="user2",
            role=UserRole.USER,
        )
        assert token1 != token2

    def test_create_access_token_with_custom_expiry(self) -> None:
        """Test access token with custom expiry."""
        custom_delta = timedelta(hours=1)
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
            expires_delta=custom_delta,
        )
        # Should not raise
        payload = decode_token(token)
        assert payload is not None

    def test_create_refresh_token_with_custom_expiry(self) -> None:
        """Test refresh token with custom expiry."""
        custom_delta = timedelta(days=30)
        token = create_refresh_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
            expires_delta=custom_delta,
        )
        # Should not raise
        payload = decode_token(token)
        assert payload is not None

    def test_create_token_admin_role(self) -> None:
        """Test token creation with admin role."""
        token = create_access_token(
            user_id="admin-123",
            username="adminuser",
            role=UserRole.ADMIN,
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.role == UserRole.ADMIN


class TestTokenDecoding:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_access_token(self) -> None:
        """Test decoding a valid access token."""
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == "user-123"
        assert payload.username == "testuser"
        assert payload.role == UserRole.USER
        assert payload.type == "access"

    def test_decode_valid_refresh_token(self) -> None:
        """Test decoding a valid refresh token."""
        token = create_refresh_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == "user-123"
        assert payload.type == "refresh"

    def test_decode_invalid_token_returns_none(self) -> None:
        """Test decoding invalid token returns None."""
        result = decode_token("invalid.token.here")
        assert result is None

    def test_decode_malformed_token_returns_none(self) -> None:
        """Test decoding malformed token returns None."""
        result = decode_token("not-a-jwt")
        assert result is None

    def test_decode_empty_token_returns_none(self) -> None:
        """Test decoding empty string returns None."""
        result = decode_token("")
        assert result is None

    def test_decode_token_has_expiry(self) -> None:
        """Test decoded token has expiration time."""
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.exp is not None
        assert payload.exp > datetime.now(timezone.utc)

    def test_decode_token_has_issued_at(self) -> None:
        """Test decoded token has issued-at time."""
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.iat is not None
        assert payload.iat <= datetime.now(timezone.utc)

    def test_decode_token_wrong_secret_returns_none(self) -> None:
        """Test decoding token with wrong secret returns None."""
        # Create token with default config
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )

        # Try to decode with different secret
        with patch.dict(
            os.environ,
            {"JWT_SECRET_KEY": "different-secret-key"},
        ):
            # Need to reset the cached config
            import video2d3d.web.auth.jwt_service as jwt_module

            jwt_module._auth_config = None

            result = decode_token(token)
            # Should fail because secret is different
            assert result is None

            # Reset for other tests
            jwt_module._auth_config = None


class TestAuthConfig:
    """Tests for auth configuration."""

    def test_get_auth_config_returns_config(self) -> None:
        """Test get_auth_config returns AuthConfig instance."""
        # Reset cached config
        import video2d3d.web.auth.jwt_service as jwt_module

        jwt_module._auth_config = None

        config = get_auth_config()
        assert config is not None
        assert config.secret_key is not None
        assert config.algorithm is not None

        # Reset for other tests
        jwt_module._auth_config = None

    def test_get_auth_config_from_environment(self) -> None:
        """Test get_auth_config reads from environment."""
        import video2d3d.web.auth.jwt_service as jwt_module

        jwt_module._auth_config = None

        with patch.dict(
            os.environ,
            {
                "JWT_SECRET_KEY": "test-secret-key",
                "JWT_ALGORITHM": "HS512",
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
                "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "14",
            },
        ):
            config = get_auth_config()
            assert config.secret_key == "test-secret-key"
            assert config.algorithm == "HS512"
            assert config.access_token_expire_minutes == 60
            assert config.refresh_token_expire_days == 14

        # Reset
        jwt_module._auth_config = None

    def test_get_auth_config_cached(self) -> None:
        """Test get_auth_config returns cached config."""
        import video2d3d.web.auth.jwt_service as jwt_module

        jwt_module._auth_config = None

        config1 = get_auth_config()
        config2 = get_auth_config()
        assert config1 is config2

        # Reset
        jwt_module._auth_config = None


class TestUserFunctions:
    """Tests for user CRUD functions (with mocked database)."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Create a mock user model."""
        user = MagicMock()
        user.user_id = "user-123"
        user.email = "test@example.com"
        user.username = "testuser"
        user.role = "user"
        user.is_active = True
        user.hashed_password = hash_password("SecurePass123")
        return user

    def test_authenticate_user_success(self, mock_user: MagicMock) -> None:
        """Test authenticate_user with valid credentials."""
        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = authenticate_user("testuser", "SecurePass123")
            assert result is not None
            assert result.user_id == "user-123"

    def test_authenticate_user_wrong_password(self, mock_user: MagicMock) -> None:
        """Test authenticate_user with wrong password."""
        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = authenticate_user("testuser", "wrongpassword")
            assert result is None

    def test_authenticate_user_not_found(self) -> None:
        """Test authenticate_user with non-existent user."""
        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_get_session.return_value = mock_session

            result = authenticate_user("nonexistent", "password")
            assert result is None

    def test_authenticate_user_inactive(self, mock_user: MagicMock) -> None:
        """Test authenticate_user with inactive user."""
        mock_user.is_active = False

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = authenticate_user("testuser", "SecurePass123")
            assert result is None

    def test_authenticate_user_with_email(self, mock_user: MagicMock) -> None:
        """Test authenticate_user with email instead of username."""
        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = authenticate_user("test@example.com", "SecurePass123")
            assert result is not None


class TestGetUserFunctions:
    """Tests for user lookup functions."""

    def test_get_user_by_id_found(self) -> None:
        """Test get_user_by_id finds user."""
        mock_user = MagicMock()
        mock_user.user_id = "user-123"

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = get_user_by_id("user-123")
            assert result is not None
            assert result.user_id == "user-123"

    def test_get_user_by_id_not_found(self) -> None:
        """Test get_user_by_id returns None if not found."""
        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_get_session.return_value = mock_session

            result = get_user_by_id("nonexistent")
            assert result is None

    def test_get_user_by_username_found(self) -> None:
        """Test get_user_by_username finds user."""
        mock_user = MagicMock()
        mock_user.username = "testuser"

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = get_user_by_username("testuser")
            assert result is not None
            assert result.username == "testuser"

    def test_get_user_by_email_found(self) -> None:
        """Test get_user_by_email finds user."""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user
            mock_get_session.return_value = mock_session

            result = get_user_by_email("test@example.com")
            assert result is not None
            assert result.email == "test@example.com"


class TestCreateUser:
    """Tests for user creation function."""

    def test_create_user_success(self) -> None:
        """Test create_user creates user successfully."""
        mock_user = MagicMock()
        mock_user.user_id = "user-123"
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock(
                side_effect=lambda u: setattr(u, "user_id", "user-123")
            )
            mock_get_session.return_value = mock_session

            result = create_user(
                email="new@example.com",
                username="newuser",
                password="SecurePass123",
            )
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_create_user_duplicate_username(self) -> None:
        """Test create_user rejects duplicate username."""
        existing_user = MagicMock()
        existing_user.username = "existinguser"

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = existing_user
            mock_get_session.return_value = mock_session

            with pytest.raises(ValueError) as exc_info:
                create_user(
                    email="new@example.com",
                    username="existinguser",
                    password="SecurePass123",
                )
            assert "Username already registered" in str(exc_info.value)

    def test_create_user_duplicate_email(self) -> None:
        """Test create_user rejects duplicate email."""
        existing_user = MagicMock()
        existing_user.email = "existing@example.com"
        existing_user.username = "different"

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = existing_user
            mock_get_session.return_value = mock_session

            with pytest.raises(ValueError) as exc_info:
                create_user(
                    email="existing@example.com",
                    username="newuser",
                    password="SecurePass123",
                )
            assert "Email already registered" in str(exc_info.value)

    def test_create_user_hashes_password(self) -> None:
        """Test create_user hashes the password."""
        created_user = None

        def capture_user(user):
            nonlocal created_user
            created_user = user

        with patch("video2d3d.web.auth.jwt_service.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add = MagicMock(side_effect=capture_user)
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock()
            mock_get_session.return_value = mock_session

            create_user(
                email="new@example.com",
                username="newuser",
                password="SecurePass123",
            )

            # Password should be hashed, not plain text
            assert created_user is not None
            assert created_user.hashed_password != "SecurePass123"
            assert created_user.hashed_password.startswith("$2b$")


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_access_token_expires(self) -> None:
        """Test access token has proper expiration."""
        token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        payload = decode_token(token)
        assert payload is not None

        # Token should expire in the future
        assert payload.exp is not None
        assert payload.exp > datetime.now(timezone.utc)

        # But within reasonable time (default 30 mins + some buffer)
        max_expiry = datetime.now(timezone.utc) + timedelta(minutes=35)
        assert payload.exp < max_expiry

    def test_refresh_token_expires_later_than_access(self) -> None:
        """Test refresh token expires later than access token."""
        access_token = create_access_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )
        refresh_token = create_refresh_token(
            user_id="user-123",
            username="testuser",
            role=UserRole.USER,
        )

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        assert access_payload is not None
        assert refresh_payload is not None

        # Refresh should expire later
        assert refresh_payload.exp > access_payload.exp
