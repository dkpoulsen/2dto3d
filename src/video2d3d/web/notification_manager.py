"""Notification manager service for handling job notifications.

This module provides the NotificationManager class that manages
in-app notifications, email notifications, and webhooks.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Optional import for webhook support
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None  # type: ignore[assignment]
    REQUESTS_AVAILABLE = False

from video2d3d.utils.logger import get_logger, log_exception

from .notification_models import (
    EmailConfig,
    Notification,
    NotificationPriority,
    NotificationType,
    WebhookConfig,
    WebhookPayload,
)

if TYPE_CHECKING:
    from video2d3d.batch.models import BatchJob
logger = get_logger("notification_manager")


# ============================================================================
# Constants
# ============================================================================

DEFAULT_WEBHOOK_TIMEOUT_SECONDS = 30
DEFAULT_WEBHOOK_EXECUTOR_WORKERS = 2
DEFAULT_MAX_NOTIFICATIONS = 1000
DEFAULT_EXPIRY_HOURS = 168  # 7 days


class NotificationManager:
    """Manages notifications for job events and system alerts.

    This class provides:
    - In-app notification storage and retrieval
    - Webhook dispatch for external integrations
    - Email notification support (pluggable)
    - Thread-safe notification management
    """

    def __init__(
        self,
        storage_path: Path | None = None,
        max_notifications: int = DEFAULT_MAX_NOTIFICATIONS,
        default_expiry_hours: int = DEFAULT_EXPIRY_HOURS,
        webhook_executor_workers: int = DEFAULT_WEBHOOK_EXECUTOR_WORKERS,
    ) -> None:
        self._notifications: dict[str, Notification] = {}
        self._lock = threading.RLock()
        self._max_notifications = max_notifications
        self._default_expiry_hours = default_expiry_hours
        self._storage_path = storage_path
        self._webhook_executor = ThreadPoolExecutor(max_workers=webhook_executor_workers)
        self._webhook_configs: list[WebhookConfig] = []
        self._email_configs: list[EmailConfig] = []
        self._logger = logger

        if storage_path:
            self._load_from_storage()

    # =========================================================================
    # Notification CRUD Operations
    # =========================================================================

    def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        job_id: str | None = None,
        data: dict[str, Any] | None = None,
        expires_in_hours: int | None = None,
    ) -> Notification:
        """Create a new notification.

        Args:
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message body.
            priority: Priority level.
            job_id: Associated job ID (if applicable).
            data: Additional data payload.
            expires_in_hours: Hours until expiration (None uses default).

        Returns:
            The created Notification instance.
        """
        expiry_hours = expires_in_hours or self._default_expiry_hours
        expires_at = datetime.now(UTC) + timedelta(hours=expiry_hours) if expiry_hours > 0 else None

        notification = Notification(
            notification_id=str(uuid.uuid4()),
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            job_id=job_id,
            data=data or {},
            created_at=datetime.now(UTC),
            expires_at=expires_at,
        )

        with self._lock:
            self._notifications[notification.notification_id] = notification
            self._cleanup_expired()
            self._enforce_max_notifications()

        self._save_to_storage()
        self._logger.info(f"Created notification {notification.notification_id}: {title}")

        return notification

    def get_notification(self, notification_id: str) -> Notification | None:
        """Get a notification by ID."""
        with self._lock:
            notification = self._notifications.get(notification_id)
            if notification and not notification.is_expired:
                return notification
            return None

    def get_notifications(
        self,
        include_read: bool = True,
        include_dismissed: bool = False,
        notification_type: NotificationType | None = None,
        job_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Notification], int, int]:
        """Get notifications with filtering and pagination.

        Args:
            include_read: Include read notifications.
            include_dismissed: Include dismissed notifications.
            notification_type: Filter by type (None = all).
            job_id: Filter by job ID (None = all).
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (notifications list, total count, unread count).
        """
        with self._lock:
            # Filter notifications
            filtered = []
            unread_count = 0

            for notification in self._notifications.values():
                if notification.is_expired:
                    continue
                if notification.dismissed and not include_dismissed:
                    continue
                if notification.read and not include_read:
                    continue
                if notification_type and notification.notification_type != notification_type:
                    continue
                if job_id and notification.job_id != job_id:
                    continue

                filtered.append(notification)
                if not notification.read:
                    unread_count += 1

            # Sort by created_at descending (newest first)
            filtered.sort(key=lambda n: n.created_at, reverse=True)

            total_count = len(filtered)

            # Paginate
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated = filtered[start_idx:end_idx]

            return paginated, total_count, unread_count

    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        with self._lock:
            return sum(
                1
                for n in self._notifications.values()
                if not n.read and not n.is_expired and not n.dismissed
            )

    def mark_as_read(self, notification_ids: list[str]) -> int:
        """Mark notifications as read.

        Args:
            notification_ids: List of notification IDs to mark.

        Returns:
            Number of notifications updated.
        """
        updated = 0
        with self._lock:
            for nid in notification_ids:
                notification = self._notifications.get(nid)
                if notification and not notification.read:
                    notification.read = True
                    updated += 1

        if updated > 0:
            self._save_to_storage()
            self._logger.debug(f"Marked {updated} notifications as read")

        return updated

    def mark_all_as_read(self) -> int:
        """Mark all notifications as read.

        Returns:
            Number of notifications updated.
        """
        updated = 0
        with self._lock:
            for notification in self._notifications.values():
                if not notification.read:
                    notification.read = True
                    updated += 1

        if updated > 0:
            self._save_to_storage()

        return updated

    def dismiss(self, notification_ids: list[str]) -> int:
        """Dismiss notifications.

        Args:
            notification_ids: List of notification IDs to dismiss.

        Returns:
            Number of notifications dismissed.
        """
        updated = 0
        with self._lock:
            for nid in notification_ids:
                notification = self._notifications.get(nid)
                if notification and not notification.dismissed:
                    notification.dismissed = True
                    updated += 1

        if updated > 0:
            self._save_to_storage()

        return updated

    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification.

        Args:
            notification_id: ID of notification to delete.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            if notification_id in self._notifications:
                del self._notifications[notification_id]
                self._save_to_storage()
                return True
            return False

    def clear_all(self) -> int:
        """Clear all notifications.

        Returns:
            Number of notifications cleared.
        """
        with self._lock:
            count = len(self._notifications)
            self._notifications.clear()
            self._save_to_storage()
            return count

    # =========================================================================
    # Job Event Handlers
    # =========================================================================

    def on_job_started(self, job: BatchJob) -> None:
        """Handle job started event."""
        self.create_notification(
            notification_type=NotificationType.JOB_STARTED,
            title="Job Started",
            message=f"Video conversion job '{job.input_path.name}' has started processing.",
            priority=NotificationPriority.NORMAL,
            job_id=job.job_id,
            data={
                "input_file": str(job.input_path),
                "output_file": str(job.output_path) if job.output_path else None,
            },
        )

    def on_job_progress(self, job: BatchJob) -> None:
        """Handle job progress event (only for significant milestones)."""
        # Only create progress notifications at 25%, 50%, 75%
        progress_percent = int(job.progress * 100)
        milestones = [25, 50, 75]

        if progress_percent in milestones and not job.metadata.get(f"notified_{progress_percent}"):
            job.metadata[f"notified_{progress_percent}"] = True
            self.create_notification(
                notification_type=NotificationType.JOB_PROGRESS,
                title="Job Progress",
                message=f"Job '{job.input_path.name}' is {progress_percent}% complete.",
                priority=NotificationPriority.LOW,
                job_id=job.job_id,
                data={
                    "progress": job.progress,
                    "stage": job.current_stage,
                },
                expires_in_hours=1,  # Progress notifications expire quickly
            )

    def on_job_completed(self, job: BatchJob) -> None:
        """Handle job completed event."""
        result = job.result
        output_file = str(result.output_path) if result and result.output_path else "unknown"

        self.create_notification(
            notification_type=NotificationType.JOB_COMPLETED,
            title="Job Completed",
            message=f"Video conversion job '{job.input_path.name}' completed successfully.",
            priority=NotificationPriority.NORMAL,
            job_id=job.job_id,
            data={
                "output_file": output_file,
                "frames_processed": result.frames_processed if result else 0,
                "processing_time_seconds": result.processing_time_seconds if result else 0,
            },
        )

        # Trigger webhooks
        self._dispatch_webhooks(
            NotificationType.JOB_COMPLETED,
            job.job_id,
            {
                "status": "completed",
                "output_file": output_file,
                "frames_processed": result.frames_processed if result else 0,
                "processing_time_seconds": result.processing_time_seconds if result else 0,
            },
        )

    def on_job_failed(self, job: BatchJob, error: Exception | None = None) -> None:
        """Handle job failed event."""
        error_message = (
            str(error) if error else (job.result.error_message if job.result else "Unknown error")
        )

        self.create_notification(
            notification_type=NotificationType.JOB_FAILED,
            title="Job Failed",
            message=f"Video conversion job '{job.input_path.name}' failed: {error_message[:100]}",
            priority=NotificationPriority.HIGH,
            job_id=job.job_id,
            data={
                "error_message": error_message,
                "error_type": job.result.error_type if job.result else "Unknown",
                "retry_count": job.retry_count,
                "can_retry": job.is_retryable,
            },
        )

        # Trigger webhooks
        self._dispatch_webhooks(
            NotificationType.JOB_FAILED,
            job.job_id,
            {
                "status": "failed",
                "error_message": error_message,
                "error_type": job.result.error_type if job.result else "Unknown",
                "retry_count": job.retry_count,
            },
        )

    def on_job_cancelled(self, job: BatchJob) -> None:
        """Handle job cancelled event."""
        self.create_notification(
            notification_type=NotificationType.JOB_CANCELLED,
            title="Job Cancelled",
            message=f"Video conversion job '{job.input_path.name}' was cancelled.",
            priority=NotificationPriority.NORMAL,
            job_id=job.job_id,
            data={
                "progress": job.progress,
            },
        )

    def on_job_retrying(self, job: BatchJob) -> None:
        """Handle job retrying event."""
        self.create_notification(
            notification_type=NotificationType.JOB_RETRYING,
            title="Job Retrying",
            message=f"Video conversion job '{job.input_path.name}' is being retried (attempt {job.retry_count}/{job.max_retries}).",
            priority=NotificationPriority.NORMAL,
            job_id=job.job_id,
            data={
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
            },
        )

    # =========================================================================
    # Webhook Management
    # =========================================================================

    def add_webhook_config(self, config: WebhookConfig) -> None:
        """Add a webhook configuration."""
        with self._lock:
            self._webhook_configs.append(config)
        self._logger.info(f"Added webhook config: {config.url}")

    def remove_webhook_config(self, url: str) -> bool:
        """Remove a webhook configuration by URL."""
        with self._lock:
            for i, config in enumerate(self._webhook_configs):
                if config.url == url:
                    del self._webhook_configs[i]
                    self._logger.info(f"Removed webhook config: {url}")
                    return True
            return False

    def get_webhook_configs(self) -> list[WebhookConfig]:
        """Get all webhook configurations."""
        with self._lock:
            return list(self._webhook_configs)

    def _dispatch_webhooks(
        self,
        event_type: NotificationType,
        job_id: str | None,
        data: dict[str, Any],
    ) -> None:
        """Dispatch webhooks for an event (async)."""
        configs = self.get_webhook_configs()

        for config in configs:
            if not config.enabled:
                continue
            if event_type not in config.events:
                continue

            # Submit to thread pool for async execution
            self._webhook_executor.submit(
                self._send_webhook,
                config,
                event_type,
                job_id,
                data,
            )

    def _send_webhook(
        self,
        config: WebhookConfig,
        event_type: NotificationType,
        job_id: str | None,
        data: dict[str, Any],
    ) -> None:
        """Send a webhook POST request."""
        if not REQUESTS_AVAILABLE:
            self._logger.warning(
                f"Cannot send webhook to {config.url}: 'requests' package not installed"
            )
            return

        payload = WebhookPayload(
            event_type=event_type,
            timestamp=datetime.now(UTC),
            job_id=job_id,
            data=data,
        )

        try:
            headers = {"Content-Type": "application/json"}

            # Add HMAC signature if secret is configured
            if config.secret:
                payload_bytes = payload.model_dump_json().encode("utf-8")
                signature = hmac.new(
                    config.secret.encode("utf-8"),
                    payload_bytes,
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            response = requests.post(  # type: ignore[union-attr]
                config.url,
                data=payload.model_dump_json(),
                headers=headers,
                timeout=DEFAULT_WEBHOOK_TIMEOUT_SECONDS,
            )

            if response.ok:
                self._logger.debug(f"Webhook sent successfully to {config.url}")
            else:
                self._logger.warning(f"Webhook failed to {config.url}: {response.status_code}")
                # Create notification about failed webhook
                self.create_notification(
                    notification_type=NotificationType.WEBHOOK_FAILED,
                    title="Webhook Failed",
                    message=f"Webhook to {config.url} failed with status {response.status_code}",
                    priority=NotificationPriority.HIGH,
                    data={"url": config.url, "status_code": response.status_code},
                )

        except Exception as e:
            log_exception(f"Failed to send webhook to {config.url}", exception=e)

    # =========================================================================
    # Email Notification Support
    # =========================================================================

    def add_email_config(self, config: EmailConfig) -> None:
        """Add an email configuration."""
        with self._lock:
            self._email_configs.append(config)
        self._logger.info(f"Added email config for: {config.recipient_email}")

    def get_email_configs(self) -> list[EmailConfig]:
        """Get all email configurations."""
        with self._lock:
            return list(self._email_configs)

    # =========================================================================
    # Storage Operations
    # =========================================================================

    def _save_to_storage(self) -> None:
        """Save notifications to storage file using atomic write."""

        if not self._storage_path:
            return

        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            with self._lock:
                data = {
                    "notifications": [
                        n.to_dict() for n in self._notifications.values() if not n.is_expired
                    ],
                    "webhook_configs": [c.model_dump() for c in self._webhook_configs],
                    "email_configs": [c.model_dump() for c in self._email_configs],
                    "saved_at": datetime.now(UTC).isoformat(),
                }

            # Atomic write: write to temp file, then rename
            temp_path = self._storage_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            temp_path.replace(self._storage_path)

        except Exception as e:
            log_exception("Failed to save notifications to storage", exception=e)

    def _load_from_storage(self) -> None:
        """Load notifications from storage file."""
        if not self._storage_path or not self._storage_path.exists():
            return

        try:
            with open(self._storage_path) as f:
                data = json.load(f)

            with self._lock:
                # Load notifications
                for n_data in data.get("notifications", []):
                    try:
                        notification = Notification.from_dict(n_data)
                        if not notification.is_expired:
                            self._notifications[notification.notification_id] = notification
                    except Exception as e:
                        self._logger.warning(f"Failed to load notification: {e}")

                # Load webhook configs
                for wc_data in data.get("webhook_configs", []):
                    try:
                        self._webhook_configs.append(WebhookConfig(**wc_data))
                    except Exception as e:
                        self._logger.warning(f"Failed to load webhook config: {e}")

                # Load email configs
                for ec_data in data.get("email_configs", []):
                    try:
                        self._email_configs.append(EmailConfig(**ec_data))
                    except Exception as e:
                        self._logger.warning(f"Failed to load email config: {e}")

            self._logger.info(f"Loaded {len(self._notifications)} notifications from storage")

        except Exception as e:
            log_exception("Failed to load notifications from storage", exception=e)

    def _cleanup_expired(self) -> None:
        """Remove expired notifications."""
        expired_ids = [nid for nid, n in self._notifications.items() if n.is_expired]
        for nid in expired_ids:
            del self._notifications[nid]

        if expired_ids:
            self._logger.debug(f"Cleaned up {len(expired_ids)} expired notifications")

    def _enforce_max_notifications(self) -> None:
        """Enforce maximum notification count by removing oldest."""
        if len(self._notifications) <= self._max_notifications:
            return

        # Sort by created_at and remove oldest
        sorted_notifications = sorted(
            self._notifications.values(),
            key=lambda n: n.created_at,
        )

        to_remove = len(self._notifications) - self._max_notifications
        for notification in sorted_notifications[:to_remove]:
            del self._notifications[notification.notification_id]

        self._logger.debug(f"Removed {to_remove} old notifications to enforce max limit")

    def shutdown(self) -> None:
        """Shutdown the notification manager."""
        self._save_to_storage()
        self._webhook_executor.shutdown(wait=True)
        self._logger.info("Notification manager shutdown complete")


# Singleton instance
_notification_manager: NotificationManager | None = None
_notification_manager_lock = threading.Lock()


def get_notification_manager() -> NotificationManager:
    """Get the singleton NotificationManager instance."""
    global _notification_manager

    with _notification_manager_lock:
        if _notification_manager is None:
            # Default storage path
            storage_path = Path("logs/notifications.json")
            _notification_manager = NotificationManager(storage_path=storage_path)

        return _notification_manager


def init_notification_manager(
    storage_path: Path | None = None,
    max_notifications: int = DEFAULT_MAX_NOTIFICATIONS,
) -> NotificationManager:
    global _notification_manager

    with _notification_manager_lock:
        if _notification_manager is not None:
            _notification_manager.shutdown()

        _notification_manager = NotificationManager(
            storage_path=storage_path,
            max_notifications=max_notifications,
        )
        return _notification_manager


__all__ = [
    "NotificationManager",
    "get_notification_manager",
    "init_notification_manager",
]
