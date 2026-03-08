"""Integration tests for notification API endpoints.

Tests cover:
- List notifications endpoint
- Get notification counts endpoint
- Get single notification endpoint
- Mark notifications as read endpoint
- Mark all as read endpoint
- Dismiss notifications endpoint
- Delete notification endpoint
- Clear all notifications endpoint
- Webhook management endpoints
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.notification_manager import NotificationManager
from video2d3d.web.notification_models import NotificationType, WebhookConfig
from video2d3d.web.routers import notifications as notifications_router


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create temp storage path."""
    return tmp_path / "notifications.json"


@pytest.fixture
def notification_manager(temp_storage_path: Path) -> Generator[NotificationManager, None, None]:
    """Create a fresh NotificationManager for testing."""
    manager = NotificationManager(
        storage_path=temp_storage_path,
        max_notifications=100,
    )
    yield manager
    manager.shutdown()


@pytest.fixture
def app(notification_manager: NotificationManager) -> Generator[FastAPI, None, None]:
    """Create test FastAPI app with notifications router."""
    app = FastAPI()

    with patch(
        "video2d3d.web.routers.notifications.get_notification_manager",
        return_value=notification_manager,
    ):
        app.include_router(notifications_router.router, prefix="/api/notifications")
        yield app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


class TestListNotifications:
    """Tests for list notifications endpoint."""

    def test_list_empty(self, client: TestClient) -> None:
        """Test listing notifications when empty."""
        response = client.get("/api/notifications/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["notifications"] == []
        assert data["total_count"] == 0
        assert data["unread_count"] == 0

    def test_list_with_notifications(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test listing notifications when present."""
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job Done",
            message="Job completed successfully",
        )

        response = client.get("/api/notifications/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["total_count"] == 1
        assert data["unread_count"] == 1

    def test_list_pagination(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test pagination parameters."""
        for i in range(25):
            notification_manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        response = client.get("/api/notifications/?page=1&page_size=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["notifications"]) == 10
        assert data["total_count"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_filter_by_type(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test filtering by notification type."""
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Completed",
            message="Done",
        )
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Failed",
            message="Error",
        )

        response = client.get("/api/notifications/?notification_type=job_completed")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["notification_type"] == "job_completed"

    def test_list_filter_by_job_id(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test filtering by job ID."""
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job A",
            message="Done",
            job_id="job-a",
        )
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job B",
            message="Done",
            job_id="job-b",
        )

        response = client.get("/api/notifications/?job_id=job-a")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["job_id"] == "job-a"

    def test_list_exclude_read(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test excluding read notifications."""
        n1 = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        notification_manager.mark_as_read([n1.notification_id])
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )

        response = client.get("/api/notifications/?include_read=false")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["title"] == "Job 2"


class TestGetNotificationCounts:
    """Tests for notification counts endpoint."""

    def test_counts_empty(self, client: TestClient) -> None:
        """Test counts when empty."""
        response = client.get("/api/notifications/count")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["unread"] == 0
        assert data["dismissed"] == 0

    def test_counts_with_notifications(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test counts with notifications."""
        n1 = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        notification_manager.mark_as_read([n1.notification_id])
        n2 = notification_manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )
        notification_manager.dismiss([n2.notification_id])
        notification_manager.create_notification(
            notification_type=NotificationType.JOB_STARTED,
            title="Job 3",
            message="Started",
        )

        response = client.get("/api/notifications/count")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert data["unread"] == 1
        assert data["dismissed"] == 1


class TestGetNotification:
    """Tests for get single notification endpoint."""

    def test_get_notification(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test getting a single notification."""
        notification = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job Done",
            message="Completed successfully",
            job_id="job-123",
        )

        response = client.get(f"/api/notifications/{notification.notification_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["notification_id"] == notification.notification_id
        assert data["title"] == "Job Done"
        assert data["job_id"] == "job-123"

    def test_get_notification_not_found(self, client: TestClient) -> None:
        """Test getting non-existent notification."""
        response = client.get("/api/notifications/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestMarkNotificationsAsRead:
    """Tests for mark as read endpoint."""

    def test_mark_as_read(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test marking notifications as read."""
        n1 = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job 1",
            message="Done",
        )
        n2 = notification_manager.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job 2",
            message="Failed",
        )

        response = client.post(
            "/api/notifications/mark-read",
            json={"notification_ids": [n1.notification_id, n2.notification_id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 2
        assert "marked" in data["message"].lower()

    def test_mark_as_read_empty_list(self, client: TestClient) -> None:
        """Test marking empty list."""
        response = client.post(
            "/api/notifications/mark-read",
            json={"notification_ids": []},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 0


class TestMarkAllAsRead:
    """Tests for mark all as read endpoint."""

    def test_mark_all_as_read(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test marking all notifications as read."""
        for i in range(5):
            notification_manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        response = client.post("/api/notifications/mark-all-read")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 5

        counts = notification_manager.get_notifications()
        assert counts[2] == 0

    def test_mark_all_as_read_when_empty(self, client: TestClient) -> None:
        """Test marking all as read when no notifications."""
        response = client.post("/api/notifications/mark-all-read")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 0


class TestDismissNotifications:
    """Tests for dismiss endpoint."""

    def test_dismiss(self, client: TestClient, notification_manager: NotificationManager) -> None:
        """Test dismissing notifications."""
        n1 = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job",
            message="Done",
        )

        response = client.post(
            "/api/notifications/dismiss",
            json={"notification_ids": [n1.notification_id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 1
        assert "dismissed" in data["message"].lower()

    def test_dismiss_multiple(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test dismissing multiple notifications."""
        ids = []
        for i in range(3):
            n = notification_manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )
            ids.append(n.notification_id)

        response = client.post(
            "/api/notifications/dismiss",
            json={"notification_ids": ids},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated_count"] == 3


class TestDeleteNotification:
    """Tests for delete notification endpoint."""

    def test_delete_notification(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test deleting a notification."""
        notification = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job",
            message="Done",
        )

        response = client.delete(f"/api/notifications/{notification.notification_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        deleted = notification_manager.get_notification(notification.notification_id)
        assert deleted is None

    def test_delete_notification_not_found(self, client: TestClient) -> None:
        """Test deleting non-existent notification."""
        response = client.delete("/api/notifications/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestClearAllNotifications:
    """Tests for clear all endpoint."""

    def test_clear_all(self, client: TestClient, notification_manager: NotificationManager) -> None:
        """Test clearing all notifications."""
        for i in range(5):
            notification_manager.create_notification(
                notification_type=NotificationType.JOB_COMPLETED,
                title=f"Job {i}",
                message=f"Message {i}",
            )

        response = client.delete("/api/notifications/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        notifications, total, _ = notification_manager.get_notifications()
        assert total == 0


class TestWebhookManagement:
    """Tests for webhook management endpoints."""

    def test_add_webhook(self, client: TestClient) -> None:
        """Test adding webhook configuration."""
        response = client.post(
            "/api/notifications/webhooks",
            json={
                "url": "https://example.com/webhook",
                "secret": "secret123",
                "events": ["job_completed", "job_failed"],
                "enabled": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["url"] == "https://example.com/webhook"

    def test_list_webhooks(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test listing webhook configurations."""
        config = WebhookConfig(
            url="https://example.com/hook",
            secret="secret",
        )
        notification_manager.add_webhook_config(config)

        response = client.get("/api/notifications/webhooks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com/hook"

    def test_remove_webhook(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test removing webhook configuration."""
        config = WebhookConfig(url="https://example.com/hook")
        notification_manager.add_webhook_config(config)

        response = client.delete("/api/notifications/webhooks?url=https://example.com/hook")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_remove_webhook_not_found(self, client: TestClient) -> None:
        """Test removing non-existent webhook."""
        response = client.delete("/api/notifications/webhooks?url=https://nonexistent.com/hook")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestNotificationResponseFormat:
    """Tests for notification response format."""

    def test_response_includes_all_fields(
        self, client: TestClient, notification_manager: NotificationManager
    ) -> None:
        """Test response includes all expected fields."""
        notification = notification_manager.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Test Title",
            message="Test message content",
            priority="high",
            job_id="job-abc",
            data={"key": "value"},
        )

        response = client.get(f"/api/notifications/{notification.notification_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "notification_id" in data
        assert "notification_type" in data
        assert "title" in data
        assert "message" in data
        assert "priority" in data
        assert "job_id" in data
        assert "data" in data
        assert "read" in data
        assert "dismissed" in data
        assert "created_at" in data
        assert "expires_at" in data

        assert data["notification_type"] == "job_completed"
        assert data["priority"] == "high"
        assert data["data"] == {"key": "value"}
