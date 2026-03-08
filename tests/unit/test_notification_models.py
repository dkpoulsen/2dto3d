"""Unit tests for notification system models.

Tests cover:
- NotificationType enum
- NotificationPriority enum
- Notification domain model
- WebhookConfig Pydantic model
- EmailConfig Pydantic model
- NotificationPreferences Pydantic model
- API request/response models
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.notification_models import (
    DismissRequest,
    DismissResponse,
    EmailConfig,
    MarkReadRequest,
    MarkReadResponse,
    Notification,
    NotificationCountResponse,
    NotificationListResponse,
    NotificationPreferences,
    NotificationPriority,
    NotificationResponse,
    NotificationType,
    WebhookConfig,
    WebhookPayload,
)


class TestNotificationType:
    """Tests for NotificationType enum."""

    def test_all_types_defined(self) -> None:
        """Test all notification types are defined."""
        assert NotificationType.JOB_COMPLETED.value == "job_completed"
        assert NotificationType.JOB_FAILED.value == "job_failed"
        assert NotificationType.JOB_CANCELLED.value == "job_cancelled"
        assert NotificationType.JOB_STARTED.value == "job_started"
        assert NotificationType.JOB_PROGRESS.value == "job_progress"
        assert NotificationType.JOB_RETRYING.value == "job_retrying"
        assert NotificationType.SYSTEM_ALERT.value == "system_alert"
        assert NotificationType.WEBHOOK_FAILED.value == "webhook_failed"

    def test_from_string_valid(self) -> None:
        """Test creating type from valid string."""
        assert NotificationType("job_completed") == NotificationType.JOB_COMPLETED
        assert NotificationType("job_failed") == NotificationType.JOB_FAILED
        assert NotificationType("system_alert") == NotificationType.SYSTEM_ALERT

    def test_from_string_invalid(self) -> None:
        """Test creating type from invalid string raises error."""
        with pytest.raises(ValueError):
            NotificationType("invalid_type")


class TestNotificationPriority:
    """Tests for NotificationPriority enum."""

    def test_all_priorities_defined(self) -> None:
        """Test all priority levels are defined."""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"

    def test_from_string_valid(self) -> None:
        """Test creating priority from valid string."""
        assert NotificationPriority("low") == NotificationPriority.LOW
        assert NotificationPriority("normal") == NotificationPriority.NORMAL
        assert NotificationPriority("high") == NotificationPriority.HIGH
        assert NotificationPriority("urgent") == NotificationPriority.URGENT


class TestNotification:
    """Tests for Notification domain model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        notification = Notification()
        assert notification.notification_id != ""  # Auto-generated UUID
        assert notification.notification_type == NotificationType.SYSTEM_ALERT
        assert notification.title == ""
        assert notification.message == ""
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.job_id is None
        assert notification.data == {}
        assert notification.read is False
        assert notification.dismissed is False
        assert notification.created_at is not None
        assert notification.expires_at is None

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        created = datetime.utcnow()
        expires = created + timedelta(hours=24)

        notification = Notification(
            notification_id="test-notification-id",
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job Completed",
            message="Your job has finished successfully",
            priority=NotificationPriority.HIGH,
            job_id="job-123",
            data={"output_file": "video_3d.mp4"},
            read=True,
            dismissed=False,
            created_at=created,
            expires_at=expires,
        )

        assert notification.notification_id == "test-notification-id"
        assert notification.notification_type == NotificationType.JOB_COMPLETED
        assert notification.title == "Job Completed"
        assert notification.message == "Your job has finished successfully"
        assert notification.priority == NotificationPriority.HIGH
        assert notification.job_id == "job-123"
        assert notification.data == {"output_file": "video_3d.mp4"}
        assert notification.read is True
        assert notification.dismissed is False
        assert notification.created_at == created
        assert notification.expires_at == expires

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        created = datetime.utcnow()
        notification = Notification(
            notification_id="test-id",
            notification_type=NotificationType.JOB_FAILED,
            title="Job Failed",
            message="Error occurred",
            priority=NotificationPriority.URGENT,
            job_id="job-456",
            data={"error": "timeout"},
            read=True,
            dismissed=True,
            created_at=created,
            expires_at=None,
        )

        data = notification.to_dict()

        assert data["notification_id"] == "test-id"
        assert data["notification_type"] == "job_failed"
        assert data["title"] == "Job Failed"
        assert data["message"] == "Error occurred"
        assert data["priority"] == "urgent"
        assert data["job_id"] == "job-456"
        assert data["data"] == {"error": "timeout"}
        assert data["read"] is True
        assert data["dismissed"] is True
        assert data["created_at"] == created.isoformat()
        assert data["expires_at"] is None

    def test_to_dict_with_expires_at(self) -> None:
        """Test serialization with expires_at set."""
        created = datetime.utcnow()
        expires = created + timedelta(hours=1)
        notification = Notification(
            notification_id="test-id",
            created_at=created,
            expires_at=expires,
        )

        data = notification.to_dict()

        assert data["expires_at"] == expires.isoformat()

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        created = datetime.utcnow()
        expires = created + timedelta(hours=24)

        data = {
            "notification_id": "test-id",
            "notification_type": "job_completed",
            "title": "Done",
            "message": "Success",
            "priority": "normal",
            "job_id": "job-789",
            "data": {"frames": 100},
            "read": False,
            "dismissed": False,
            "created_at": created.isoformat(),
            "expires_at": expires.isoformat(),
        }

        notification = Notification.from_dict(data)

        assert notification.notification_id == "test-id"
        assert notification.notification_type == NotificationType.JOB_COMPLETED
        assert notification.title == "Done"
        assert notification.message == "Success"
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.job_id == "job-789"
        assert notification.data == {"frames": 100}
        assert notification.read is False
        assert notification.dismissed is False
        assert notification.created_at == created
        assert notification.expires_at == expires

    def test_from_dict_missing_fields(self) -> None:
        """Test deserialization with missing fields uses defaults."""
        data = {
            "notification_id": "test-id",
        }

        notification = Notification.from_dict(data)

        assert notification.notification_id == "test-id"
        assert notification.notification_type == NotificationType.SYSTEM_ALERT
        assert notification.title == ""
        assert notification.message == ""
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.job_id is None
        assert notification.data == {}
        assert notification.read is False
        assert notification.dismissed is False
        assert notification.created_at is None
        assert notification.expires_at is None

    def test_from_dict_none_dates(self) -> None:
        """Test deserialization handles None dates."""
        data = {
            "notification_id": "test-id",
            "created_at": None,
            "expires_at": None,
        }

        notification = Notification.from_dict(data)

        assert notification.created_at is None
        assert notification.expires_at is None

    def test_is_expired_no_expiry(self) -> None:
        """Test is_expired returns False when no expiry set."""
        notification = Notification()
        assert notification.is_expired is False

    def test_is_expired_future(self) -> None:
        """Test is_expired returns False for future expiry."""
        notification = Notification(expires_at=datetime.utcnow() + timedelta(hours=1))
        assert notification.is_expired is False

    def test_is_expired_past(self) -> None:
        """Test is_expired returns True for past expiry."""
        notification = Notification(expires_at=datetime.utcnow() - timedelta(hours=1))
        assert notification.is_expired is True

    def test_roundtrip_serialization(self) -> None:
        """Test to_dict and from_dict roundtrip."""
        original = Notification(
            notification_id="test-id",
            notification_type=NotificationType.JOB_PROGRESS,
            title="Progress Update",
            message="50% complete",
            priority=NotificationPriority.LOW,
            job_id="job-123",
            data={"progress": 0.5},
            read=False,
            dismissed=False,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        data = original.to_dict()
        restored = Notification.from_dict(data)

        assert restored.notification_id == original.notification_id
        assert restored.notification_type == original.notification_type
        assert restored.title == original.title
        assert restored.message == original.message
        assert restored.priority == original.priority
        assert restored.job_id == original.job_id
        assert restored.data == original.data
        assert restored.read == original.read
        assert restored.dismissed == original.dismissed


class TestWebhookConfig:
    """Tests for WebhookConfig Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = WebhookConfig(url="https://example.com/webhook")
        assert config.url == "https://example.com/webhook"
        assert config.secret is None
        assert NotificationType.JOB_COMPLETED in config.events
        assert NotificationType.JOB_FAILED in config.events
        assert config.enabled is True

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        config = WebhookConfig(
            url="https://example.com/hook",
            secret="my-secret",
            events=[NotificationType.JOB_STARTED, NotificationType.JOB_COMPLETED],
            enabled=False,
        )
        assert config.url == "https://example.com/hook"
        assert config.secret == "my-secret"
        assert config.events == [NotificationType.JOB_STARTED, NotificationType.JOB_COMPLETED]
        assert config.enabled is False

    def test_model_dump(self) -> None:
        """Test serialization."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            secret="secret123",
            events=[NotificationType.JOB_FAILED],
            enabled=True,
        )
        data = config.model_dump()

        assert data["url"] == "https://example.com/webhook"
        assert data["secret"] == "secret123"
        assert NotificationType.JOB_FAILED in data["events"]
        assert data["enabled"] is True

    def test_model_validation_missing_url(self) -> None:
        """Test validation fails without URL."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            WebhookConfig()  # type: ignore


class TestEmailConfig:
    """Tests for EmailConfig Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = EmailConfig(recipient_email="user@example.com")
        assert config.recipient_email == "user@example.com"
        assert NotificationType.JOB_COMPLETED in config.events
        assert NotificationType.JOB_FAILED in config.events
        assert config.enabled is True

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        config = EmailConfig(
            recipient_email="admin@example.com",
            events=[NotificationType.JOB_FAILED, NotificationType.SYSTEM_ALERT],
            enabled=False,
        )
        assert config.recipient_email == "admin@example.com"
        assert config.events == [NotificationType.JOB_FAILED, NotificationType.SYSTEM_ALERT]
        assert config.enabled is False


class TestNotificationPreferences:
    """Tests for NotificationPreferences Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        prefs = NotificationPreferences()
        assert prefs.in_app_enabled is True
        assert prefs.email_enabled is False
        assert prefs.webhook_enabled is False
        assert prefs.email_config is None
        assert prefs.webhook_config is None
        assert prefs.quiet_hours_start is None
        assert prefs.quiet_hours_end is None

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        webhook = WebhookConfig(url="https://example.com/hook")
        email = EmailConfig(recipient_email="user@example.com")

        prefs = NotificationPreferences(
            in_app_enabled=False,
            email_enabled=True,
            webhook_enabled=True,
            email_config=email,
            webhook_config=webhook,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        )

        assert prefs.in_app_enabled is False
        assert prefs.email_enabled is True
        assert prefs.webhook_enabled is True
        assert prefs.email_config == email
        assert prefs.webhook_config == webhook
        assert prefs.quiet_hours_start == "22:00"
        assert prefs.quiet_hours_end == "08:00"


class TestNotificationResponse:
    """Tests for NotificationResponse Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        now = datetime.utcnow()
        response = NotificationResponse(
            notification_id="test-id",
            notification_type=NotificationType.JOB_COMPLETED,
            title="Done",
            message="Success",
            created_at=now,
        )

        assert response.notification_id == "test-id"
        assert response.notification_type == NotificationType.JOB_COMPLETED
        assert response.title == "Done"
        assert response.message == "Success"
        assert response.priority == NotificationPriority.NORMAL
        assert response.job_id is None
        assert response.data == {}
        assert response.read is False
        assert response.dismissed is False
        assert response.created_at == now
        assert response.expires_at is None


class TestNotificationListResponse:
    """Tests for NotificationListResponse Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        response = NotificationListResponse()
        assert response.notifications == []
        assert response.total_count == 0
        assert response.unread_count == 0
        assert response.page == 1
        assert response.page_size == 50

    def test_with_notifications(self) -> None:
        """Test with notifications."""
        now = datetime.utcnow()
        notifications = [
            NotificationResponse(
                notification_id=f"notif-{i}",
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message="Done",
                created_at=now,
            )
            for i in range(3)
        ]

        response = NotificationListResponse(
            notifications=notifications,
            total_count=10,
            unread_count=5,
            page=2,
            page_size=20,
        )

        assert len(response.notifications) == 3
        assert response.total_count == 10
        assert response.unread_count == 5
        assert response.page == 2
        assert response.page_size == 20


class TestNotificationCountResponse:
    """Tests for NotificationCountResponse Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        response = NotificationCountResponse()
        assert response.total == 0
        assert response.unread == 0
        assert response.dismissed == 0

    def test_custom_values(self) -> None:
        """Test custom values."""
        response = NotificationCountResponse(total=100, unread=25, dismissed=10)
        assert response.total == 100
        assert response.unread == 25
        assert response.dismissed == 10


class TestMarkReadRequest:
    """Tests for MarkReadRequest Pydantic model."""

    def test_valid_request(self) -> None:
        """Test valid request."""
        request = MarkReadRequest(notification_ids=["id1", "id2", "id3"])
        assert request.notification_ids == ["id1", "id2", "id3"]

    def test_empty_list(self) -> None:
        """Test empty list is allowed."""
        request = MarkReadRequest(notification_ids=[])
        assert request.notification_ids == []


class TestMarkReadResponse:
    """Tests for MarkReadResponse Pydantic model."""

    def test_default_message(self) -> None:
        """Test default message."""
        response = MarkReadResponse(updated_count=5)
        assert response.updated_count == 5
        assert response.message == "Notifications marked as read"

    def test_custom_message(self) -> None:
        """Test custom message."""
        response = MarkReadResponse(updated_count=3, message="Custom message")
        assert response.updated_count == 3
        assert response.message == "Custom message"


class TestDismissRequest:
    """Tests for DismissRequest Pydantic model."""

    def test_valid_request(self) -> None:
        """Test valid request."""
        request = DismissRequest(notification_ids=["id1"])
        assert request.notification_ids == ["id1"]


class TestDismissResponse:
    """Tests for DismissResponse Pydantic model."""

    def test_default_message(self) -> None:
        """Test default message."""
        response = DismissResponse(updated_count=2)
        assert response.updated_count == 2
        assert response.message == "Notifications dismissed"


class TestWebhookPayload:
    """Tests for WebhookPayload Pydantic model."""

    def test_valid_payload(self) -> None:
        """Test valid payload."""
        now = datetime.utcnow()
        payload = WebhookPayload(
            event_type=NotificationType.JOB_COMPLETED,
            timestamp=now,
            job_id="job-123",
            data={"status": "completed", "output_file": "video.mp4"},
        )

        assert payload.event_type == NotificationType.JOB_COMPLETED
        assert payload.timestamp == now
        assert payload.job_id == "job-123"
        assert payload.data == {"status": "completed", "output_file": "video.mp4"}

    def test_default_values(self) -> None:
        """Test default values."""
        now = datetime.utcnow()
        payload = WebhookPayload(
            event_type=NotificationType.JOB_FAILED,
            timestamp=now,
        )

        assert payload.job_id is None
        assert payload.data == {}

    def test_model_dump_json(self) -> None:
        """Test JSON serialization."""
        now = datetime.utcnow()
        payload = WebhookPayload(
            event_type=NotificationType.JOB_COMPLETED,
            timestamp=now,
            job_id="job-123",
            data={"key": "value"},
        )

        json_str = payload.model_dump_json()
        assert "job_completed" in json_str
        assert "job-123" in json_str
