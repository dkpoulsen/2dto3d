"""Unit tests for notification manager service.

Tests cover:
- Notification CRUD operations
- Notification filtering and pagination
- Job event handlers
- Webhook management
- Storage persistence
- Singleton management
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.notification_manager import (
    DEFAULT_EXPIRY_HOURS,
    DEFAULT_MAX_NOTIFICATIONS,
    DEFAULT_WEBHOOK_EXECUTOR_WORKERS,
    DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
    NotificationManager,
    get_notification_manager,
    init_notification_manager,
)
from video2d3d.web.notification_models import (
    EmailConfig,
    NotificationPriority,
    NotificationType,
    WebhookConfig,
)


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create a temporary storage path."""
    return tmp_path / "notifications.json"


@pytest.fixture
def manager(temp_storage_path: Path) -> Generator[NotificationManager, None, None]:
    """Create a fresh NotificationManager for testing."""
    mgr = NotificationManager(
        storage_path=temp_storage_path,
        max_notifications=100,
        default_expiry_hours=168,
    )
    yield mgr
    mgr.shutdown()


@pytest.fixture
def mock_job() -> MagicMock:
    """Create a mock BatchJob for testing."""
    job = MagicMock()
    job.job_id = "test-job-123"
    job.input_path = Path("/input/video.mp4")
    job.output_path = Path("/output/video_3d.mp4")
    job.progress = 0.5
    job.current_stage = "Processing"
    job.retry_count = 1
    job.max_retries = 3
    job.is_retryable = True
    job.metadata = {}

    # Mock result
    result = MagicMock()
    result.output_path = Path("/output/video_3d.mp4")
    result.frames_processed = 100
    result.processing_time_seconds = 10.5
    result.error_message = None
    result.error_type = None
    job.result = result

    return job


class TestNotificationManagerInit:
    """Tests for NotificationManager initialization."""

    def test_default_initialization(self, temp_storage_path: Path) -> None:
        """Test default initialization."""
        manager = NotificationManager(storage_path=temp_storage_path)
        assert manager._max_notifications == DEFAULT_MAX_NOTIFICATIONS
        assert manager._default_expiry_hours == DEFAULT_EXPIRY_HOURS
        assert manager._storage_path == temp_storage_path

    def test_custom_initialization(self, temp_storage_path: Path) -> None:
        """Test custom initialization parameters."""
        manager = NotificationManager(
            storage_path=temp_storage_path,
            max_notifications=50,
            default_expiry_hours=24,
            webhook_executor_workers=4,
        )
        assert manager._max_notifications == 50
        assert manager._default_expiry_hours == 24

    def test_no_storage_path(self) -> None:
        """Test initialization without storage path."""
        manager = NotificationManager()
        assert manager._storage_path is None


class TestNotificationCRUD:
    """Tests for notification CRUD operations."""

    def test_create_notification(self, manager: NotificationManager) -> None:
        """Test creating a notification."""
        notification = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job Done",
            message="Your job completed successfully",
            priority=NotificationPriority.HIGH,
            job_id="job-123",
            data={"output": "video.mp4"},
        )

        assert notification.notification_id != ""
        assert notification.notification_type == NotificationType.JOB_COMPLETED
        assert notification.title == "Job Done"
        assert notification.message == "Your job completed successfully"
        assert notification.priority == NotificationPriority.HIGH
        assert notification.job_id == "job-123"
        assert notification.data == {"output": "video.mp4"}
        assert notification.read is False
        assert notification.dismissed is False
        assert notification.expires_at is not None

    def test_create_notification_custom_expiry(self, manager: NotificationManager) -> None:
        """Test creating notification with custom expiry."""
        notification = manager.create_notification(
            notification_type=NotificationType.JOB_PROGRESS,
            title="Progress",
            message="50%",
            expires_in_hours=1,
        )

        assert notification.expires_at is not None
        # Should expire approximately 1 hour from now
        expected_expiry = datetime.utcnow() + timedelta(hours=1)
        delta = abs((notification.expires_at - expected_expiry).total_seconds())
        assert delta < 5  # Within 5 seconds

    def test_create_notification_no_expiry(self, manager: NotificationManager) -> None:
        """Test creating notification with no expiry (0 hours)."""
        notification = manager.create_notification(
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Alert",
            message="System alert",
            expires_in_hours=0,
        )

        assert notification.expires_at is None

    def test_get_notification(self, manager: NotificationManager) -> None:
        """Test getting a notification by ID."""
        created = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Test",
            message="Test message",
        )

        retrieved = manager.get_notification(created.notification_id)
        assert retrieved is not None
        assert retrieved.notification_id == created.notification_id
        assert retrieved.title == "Test"

    def test_get_notification_not_found(self, manager: NotificationManager) -> None:
        """Test getting non-existent notification."""
        retrieved = manager.get_notification("non-existent-id")
        assert retrieved is None

    def test_get_notification_expired(self, manager: NotificationManager) -> None:
        """Test getting expired notification returns None."""
        # Create notification that's already expired
        notification = manager.create_notification(
            notification_type=NotificationType.JOB_PROGRESS,
            title="Progress",
            message="Test",
        )
        # Manually expire it
        notification.expires_at = datetime.utcnow() - timedelta(hours=1)

        retrieved = manager.get_notification(notification.notification_id)
        assert retrieved is None

    def test_get_notifications_empty(self, manager: NotificationManager) -> None:
        """Test getting notifications when empty."""
        notifications, total, unread = manager.get_notifications()
        assert notifications == []
        assert total == 0
        assert unread == 0

    def test_get_notifications_multiple(self, manager: NotificationManager) -> None:
        """Test getting multiple notifications."""
        # Create several notifications
        for i in range(5):
            manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        notifications, total, unread = manager.get_notifications()
        assert len(notifications) == 5
        assert total == 5
        assert unread == 5  # All unread

    def test_get_notifications_include_read(self, manager: NotificationManager) -> None:
        """Test filtering by read status."""
        # Create and mark one as read
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        manager.mark_as_read([n1.notification_id])

        manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )

        # Include read
        notifications, total, _ = manager.get_notifications(include_read=True)
        assert len(notifications) == 2

        # Exclude read
        notifications, total, _ = manager.get_notifications(include_read=False)
        assert len(notifications) == 1
        assert notifications[0].title == "Job 2"

    def test_get_notifications_include_dismissed(self, manager: NotificationManager) -> None:
        """Test filtering by dismissed status."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        manager.dismiss([n1.notification_id])

        manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )

        # Exclude dismissed (default)
        notifications, _, _ = manager.get_notifications(include_dismissed=False)
        assert len(notifications) == 1

        # Include dismissed
        notifications, _, _ = manager.get_notifications(include_dismissed=True)
        assert len(notifications) == 2

    def test_get_notifications_filter_by_type(self, manager: NotificationManager) -> None:
        """Test filtering by notification type."""
        manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Completed",
            message="Done",
        )
        manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Failed",
            message="Error",
        )

        notifications, _, _ = manager.get_notifications(
            notification_type=NotificationType.JOB_COMPLETED
        )
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_COMPLETED

    def test_get_notifications_filter_by_job_id(self, manager: NotificationManager) -> None:
        """Test filtering by job ID."""
        manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job A",
            message="Done",
            job_id="job-a",
        )
        manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job B",
            message="Done",
            job_id="job-b",
        )

        notifications, _, _ = manager.get_notifications(job_id="job-a")
        assert len(notifications) == 1
        assert notifications[0].job_id == "job-a"

    def test_get_notifications_pagination(self, manager: NotificationManager) -> None:
        """Test pagination."""
        # Create 25 notifications
        for i in range(25):
            manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        # Page 1
        notifications, total, _ = manager.get_notifications(page=1, page_size=10)
        assert len(notifications) == 10
        assert total == 25

        # Page 2
        notifications, total, _ = manager.get_notifications(page=2, page_size=10)
        assert len(notifications) == 10

        # Page 3
        notifications, total, _ = manager.get_notifications(page=3, page_size=10)
        assert len(notifications) == 5

    def test_get_notifications_sorted_by_created_at_desc(
        self, manager: NotificationManager
    ) -> None:
        """Test notifications are sorted by created_at descending."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="First",
            message="First",
        )
        n2 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Second",
            message="Second",
        )
        n3 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Third",
            message="Third",
        )

        notifications, _, _ = manager.get_notifications()
        # Newest first
        assert notifications[0].notification_id == n3.notification_id
        assert notifications[1].notification_id == n2.notification_id
        assert notifications[2].notification_id == n1.notification_id

    def test_get_unread_count(self, manager: NotificationManager) -> None:
        """Test getting unread count."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )

        assert manager.get_unread_count() == 2

        manager.mark_as_read([n1.notification_id])
        assert manager.get_unread_count() == 1

    def test_mark_as_read(self, manager: NotificationManager) -> None:
        """Test marking notifications as read."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        n2 = manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )

        updated = manager.mark_as_read([n1.notification_id, n2.notification_id])
        assert updated == 2

        assert manager.get_notification(n1.notification_id).read is True
        assert manager.get_notification(n2.notification_id).read is True

    def test_mark_as_read_already_read(self, manager: NotificationManager) -> None:
        """Test marking already-read notifications."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job",
            message="Done",
        )
        manager.mark_as_read([n1.notification_id])

        # Mark again - should return 0 (already read)
        updated = manager.mark_as_read([n1.notification_id])
        assert updated == 0

    def test_mark_as_read_empty_list(self, manager: NotificationManager) -> None:
        """Test marking empty list."""
        updated = manager.mark_as_read([])
        assert updated == 0

    def test_mark_all_as_read(self, manager: NotificationManager) -> None:
        """Test marking all notifications as read."""
        for i in range(5):
            manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        updated = manager.mark_all_as_read()
        assert updated == 5
        assert manager.get_unread_count() == 0

    def test_dismiss(self, manager: NotificationManager) -> None:
        """Test dismissing notifications."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job",
            message="Done",
        )

        updated = manager.dismiss([n1.notification_id])
        assert updated == 1

        notification = manager.get_notification(n1.notification_id)
        assert notification.dismissed is True

    def test_dismiss_already_dismissed(self, manager: NotificationManager) -> None:
        """Test dismissing already-dismissed notifications."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job",
            message="Done",
        )
        manager.dismiss([n1.notification_id])

        updated = manager.dismiss([n1.notification_id])
        assert updated == 0

    def test_delete_notification(self, manager: NotificationManager) -> None:
        """Test deleting a notification."""
        n1 = manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job",
            message="Done",
        )

        deleted = manager.delete_notification(n1.notification_id)
        assert deleted is True
        assert manager.get_notification(n1.notification_id) is None

    def test_delete_notification_not_found(self, manager: NotificationManager) -> None:
        """Test deleting non-existent notification."""
        deleted = manager.delete_notification("non-existent-id")
        assert deleted is False

    def test_clear_all(self, manager: NotificationManager) -> None:
        """Test clearing all notifications."""
        for i in range(5):
            manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        count = manager.clear_all()
        assert count == 5

        notifications, total, _ = manager.get_notifications()
        assert total == 0


class TestJobEventHandlers:
    """Tests for job event handlers."""

    def test_on_job_started(self, manager: NotificationManager, mock_job: MagicMock) -> None:
        """Test job started handler."""
        manager.on_job_started(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_STARTED
        assert notifications[0].job_id == "test-job-123"
        assert "started" in notifications[0].message.lower()

    def test_on_job_completed(self, manager: NotificationManager, mock_job: MagicMock) -> None:
        """Test job completed handler."""
        manager.on_job_completed(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_COMPLETED
        assert notifications[0].job_id == "test-job-123"
        assert "completed" in notifications[0].message.lower()

    def test_on_job_failed(self, manager: NotificationManager, mock_job: MagicMock) -> None:
        """Test job failed handler."""
        mock_job.result.error_message = "Processing timeout"

        manager.on_job_failed(mock_job, Exception("Processing timeout"))

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_FAILED
        assert notifications[0].priority == NotificationPriority.HIGH
        assert "failed" in notifications[0].message.lower()

    def test_on_job_failed_no_error(
        self, manager: NotificationManager, mock_job: MagicMock
    ) -> None:
        """Test job failed handler without exception."""
        mock_job.result.error_message = "Unknown error"

        manager.on_job_failed(mock_job, None)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_FAILED

    def test_on_job_cancelled(self, manager: NotificationManager, mock_job: MagicMock) -> None:
        """Test job cancelled handler."""
        manager.on_job_cancelled(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_CANCELLED

    def test_on_job_retrying(self, manager: NotificationManager, mock_job: MagicMock) -> None:
        """Test job retrying handler."""
        manager.on_job_retrying(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_RETRYING
        assert "retry" in notifications[0].message.lower()

    def test_on_job_progress_milestone(
        self, manager: NotificationManager, mock_job: MagicMock
    ) -> None:
        """Test job progress handler at milestone (25%, 50%, 75%)."""
        mock_job.progress = 0.25

        manager.on_job_progress(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1
        assert notifications[0].notification_type == NotificationType.JOB_PROGRESS
        assert "25%" in notifications[0].message

    def test_on_job_progress_not_milestone(
        self, manager: NotificationManager, mock_job: MagicMock
    ) -> None:
        """Test job progress handler at non-milestone progress."""
        mock_job.progress = 0.30

        manager.on_job_progress(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 0  # No notification for non-milestone

    def test_on_job_progress_already_notified(
        self, manager: NotificationManager, mock_job: MagicMock
    ) -> None:
        """Test job progress doesn't notify twice for same milestone."""
        mock_job.progress = 0.50
        mock_job.metadata = {}  # Fresh metadata

        manager.on_job_progress(mock_job)
        assert mock_job.metadata.get("notified_50") is True

        # Second call with same progress
        manager.on_job_progress(mock_job)

        notifications, _, _ = manager.get_notifications()
        assert len(notifications) == 1  # Only one notification


class TestWebhookManagement:
    """Tests for webhook management."""

    def test_add_webhook_config(self, manager: NotificationManager) -> None:
        """Test adding webhook configuration."""
        config = WebhookConfig(
            url="https://example.com/webhook",
            secret="secret123",
        )
        manager.add_webhook_config(config)

        configs = manager.get_webhook_configs()
        assert len(configs) == 1
        assert configs[0].url == "https://example.com/webhook"

    def test_remove_webhook_config(self, manager: NotificationManager) -> None:
        """Test removing webhook configuration."""
        config = WebhookConfig(url="https://example.com/webhook")
        manager.add_webhook_config(config)

        removed = manager.remove_webhook_config("https://example.com/webhook")
        assert removed is True

        configs = manager.get_webhook_configs()
        assert len(configs) == 0

    def test_remove_webhook_config_not_found(self, manager: NotificationManager) -> None:
        """Test removing non-existent webhook configuration."""
        removed = manager.remove_webhook_config("https://nonexistent.com/hook")
        assert removed is False


class TestEmailManagement:
    """Tests for email configuration management."""

    def test_add_email_config(self, manager: NotificationManager) -> None:
        """Test adding email configuration."""
        config = EmailConfig(recipient_email="user@example.com")
        manager.add_email_config(config)

        configs = manager.get_email_configs()
        assert len(configs) == 1
        assert configs[0].recipient_email == "user@example.com"


class TestStorageOperations:
    """Tests for storage persistence."""

    def test_save_to_storage(self, manager: NotificationManager, temp_storage_path: Path) -> None:
        """Test saving notifications to storage."""
        manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Test",
            message="Test message",
        )

        # Storage should be saved
        assert temp_storage_path.exists()

        with open(temp_storage_path) as f:
            data = json.load(f)

        assert "notifications" in data
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["title"] == "Test"

    def test_load_from_storage(self, temp_storage_path: Path) -> None:
        """Test loading notifications from storage."""
        # Create a storage file
        data = {
            "notifications": [
                {
                    "notification_id": "loaded-notification",
                    "notification_type": "job_completed",
                    "title": "Loaded Notification",
                    "message": "This was loaded from storage",
                    "priority": "normal",
                    "job_id": None,
                    "data": {},
                    "read": False,
                    "dismissed": False,
                    "created_at": datetime.utcnow().isoformat(),
                    "expires_at": None,
                }
            ],
            "webhook_configs": [],
            "email_configs": [],
            "saved_at": datetime.utcnow().isoformat(),
        }

        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(data, f)

        # Create manager that loads from storage
        manager = NotificationManager(storage_path=temp_storage_path)

        try:
            notification = manager.get_notification("loaded-notification")
            assert notification is not None
            assert notification.title == "Loaded Notification"
        finally:
            manager.shutdown()

    def test_load_webhook_configs_from_storage(self, temp_storage_path: Path) -> None:
        """Test loading webhook configs from storage."""
        data = {
            "notifications": [],
            "webhook_configs": [
                {
                    "url": "https://example.com/hook",
                    "secret": "secret",
                    "events": ["job_completed", "job_failed"],
                    "enabled": True,
                }
            ],
            "email_configs": [],
            "saved_at": datetime.utcnow().isoformat(),
        }

        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(data, f)

        manager = NotificationManager(storage_path=temp_storage_path)
        try:
            configs = manager.get_webhook_configs()
            assert len(configs) == 1
            assert configs[0].url == "https://example.com/hook"
        finally:
            manager.shutdown()

    def test_load_expired_notifications_excluded(self, temp_storage_path: Path) -> None:
        """Test expired notifications are excluded when loading."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        data = {
            "notifications": [
                {
                    "notification_id": "expired-notification",
                    "notification_type": "job_completed",
                    "title": "Expired",
                    "message": "This is expired",
                    "priority": "normal",
                    "job_id": None,
                    "data": {},
                    "read": False,
                    "dismissed": False,
                    "created_at": past_time.isoformat(),
                    "expires_at": past_time.isoformat(),  # Already expired
                }
            ],
            "webhook_configs": [],
            "email_configs": [],
            "saved_at": datetime.utcnow().isoformat(),
        }

        temp_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_storage_path, "w") as f:
            json.dump(data, f)

        manager = NotificationManager(storage_path=temp_storage_path)
        try:
            notification = manager.get_notification("expired-notification")
            assert notification is None  # Should not be loaded
        finally:
            manager.shutdown()

    def test_no_storage_path_no_save(self) -> None:
        """Test manager without storage path doesn't save."""
        manager = NotificationManager()
        try:
            manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title="Test",
                message="Test",
            )
            # Should not raise or fail
        finally:
            manager.shutdown()


class TestMaxNotifications:
    """Tests for max notification limit."""

    def test_enforce_max_notifications(self, temp_storage_path: Path) -> None:
        """Test that max notification limit is enforced."""
        manager = NotificationManager(
            storage_path=temp_storage_path,
            max_notifications=5,
        )
        try:
            # Create more than max
            for i in range(10):
                manager.create_notification(
                    notification_type=NotificationType.JOB_COMPLETED,
                    title=f"Job {i}",
                    message=f"Message {i}",
                )

            notifications, total, _ = manager.get_notifications()
            assert total == 5  # Should be capped at max
        finally:
            manager.shutdown()

    def test_oldest_removed_first(self, temp_storage_path: Path) -> None:
        """Test that oldest notifications are removed first."""
        manager = NotificationManager(
            storage_path=temp_storage_path,
            max_notifications=3,
        )
        try:
            # Create 5 notifications
            ids = []
            for i in range(5):
                n = manager.create_notification(
                    notification_type=NotificationType.JOB_COMPLETED,
                    title=f"Job {i}",
                    message=f"Message {i}",
                )
                ids.append(n.notification_id)

            notifications, _, _ = manager.get_notifications()
            # Should have last 3 (newest)
            remaining_ids = {n.notification_id for n in notifications}
            assert ids[2] in remaining_ids  # Job 2
            assert ids[3] in remaining_ids  # Job 3
            assert ids[4] in remaining_ids  # Job 4
            assert ids[0] not in remaining_ids  # Job 0 removed
            assert ids[1] not in remaining_ids  # Job 1 removed
        finally:
            manager.shutdown()


class TestSingleton:
    """Tests for singleton management."""

    def test_get_notification_manager_singleton(self) -> None:
        """Test get_notification_manager returns singleton."""
        # Reset singleton
        import video2d3d.web.notification_manager as nm

        nm._notification_manager = None

        manager1 = get_notification_manager()
        manager2 = get_notification_manager()

        assert manager1 is manager2

        # Cleanup
        manager1.shutdown()
        nm._notification_manager = None

    def test_init_notification_manager_replaces_singleton(self) -> None:
        """Test init_notification_manager replaces existing singleton."""
        import video2d3d.web.notification_manager as nm

        # Create initial
        nm._notification_manager = None
        manager1 = get_notification_manager()

        # Initialize new one
        manager2 = init_notification_manager()

        # Should be different instance
        assert manager1 is not manager2

        # Cleanup
        manager2.shutdown()
        nm._notification_manager = None


class TestConstants:
    """Tests for module constants."""

    def test_constants_defined(self) -> None:
        """Test constants have expected values."""
        assert DEFAULT_WEBHOOK_TIMEOUT_SECONDS == 30
        assert DEFAULT_WEBHOOK_EXECUTOR_WORKERS == 2
        assert DEFAULT_MAX_NOTIFICATIONS == 1000
        assert DEFAULT_EXPIRY_HOURS == 168  # 7 days


class TestShutdown:
    """Tests for manager shutdown."""

    def test_shutdown_saves_storage(
        self, manager: NotificationManager, temp_storage_path: Path
    ) -> None:
        """Test shutdown saves to storage."""
        manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Test",
            message="Test",
        )

        manager.shutdown()

        # Storage should exist
        assert temp_storage_path.exists()

    def test_shutdown_no_storage(self) -> None:
        """Test shutdown without storage path."""
        manager = NotificationManager()
        # Should not raise
        manager.shutdown()
