"""Pydantic schemas for notification system.

This module defines the data models for in-app notifications,
email notifications, and webhook callbacks.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationType(str, Enum):
    """Types of notifications supported by the system."""

    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_RETRYING = "job_retrying"
    SYSTEM_ALERT = "system_alert"
    WEBHOOK_FAILED = "webhook_failed"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# Domain Model (internal)
# ============================================================================


class Notification:
    """In-memory notification model with serialization support.

    This class represents a single notification in the system.
    It can be converted to/from dictionary for persistence.
    """

    def __init__(
        self,
        notification_id: str | None = None,
        notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
        title: str = "",
        message: str = "",
        priority: NotificationPriority = NotificationPriority.NORMAL,
        job_id: str | None = None,
        data: dict[str, Any] | None = None,
        read: bool = False,
        dismissed: bool = False,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        self.notification_id = notification_id or str(uuid.uuid4())
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.priority = priority
        self.job_id = job_id
        self.data = data or {}
        self.read = read
        self.dismissed = dismissed
        self.created_at = created_at or datetime.now(UTC)
        self.expires_at = expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert notification to dictionary for serialization."""
        return {
            "notification_id": self.notification_id,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "job_id": self.job_id,
            "data": self.data,
            "read": self.read,
            "dismissed": self.dismissed,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Notification:
        """Create notification from dictionary."""
        return cls(
            notification_id=data.get("notification_id"),
            notification_type=NotificationType(data.get("notification_type", "system_alert")),
            title=data.get("title", ""),
            message=data.get("message", ""),
            priority=NotificationPriority(data.get("priority", "normal")),
            job_id=data.get("job_id"),
            data=data.get("data", {}),
            read=data.get("read", False),
            dismissed=data.get("dismissed", False),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            ),
        )

    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at


# ============================================================================
# API Request Models
# ============================================================================


class WebhookConfig(BaseModel):
    """Configuration for webhook notifications."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/webhook",
                "secret": "webhook_secret_key",
                "events": ["job_completed", "job_failed"],
                "enabled": True,
            }
        }
    )

    url: str = Field(..., description="Webhook URL to send POST requests to")
    secret: str | None = Field(None, description="Secret key for HMAC signature")
    events: list[NotificationType] = Field(
        default_factory=lambda: [NotificationType.JOB_COMPLETED, NotificationType.JOB_FAILED],
        description="Event types to trigger webhook",
    )
    enabled: bool = Field(default=True, description="Whether webhook is active")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is a valid HTTP/HTTPS URL."""
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        if not parsed.netloc:
            raise ValueError("URL must have a valid host")
        return v


class EmailConfig(BaseModel):
    """Configuration for email notifications."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recipient_email": "user@example.com",
                "events": ["job_completed", "job_failed"],
                "enabled": True,
            }
        }
    )

    recipient_email: str = Field(..., description="Email address to send notifications to")
    events: list[NotificationType] = Field(
        default_factory=lambda: [NotificationType.JOB_COMPLETED, NotificationType.JOB_FAILED],
        description="Event types to trigger email",
    )
    enabled: bool = Field(default=True, description="Whether email notifications are active")

    @field_validator("recipient_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format using a simple regex pattern."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email address format")
        return v


class NotificationPreferences(BaseModel):
    """User preferences for notifications."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "in_app_enabled": True,
                "email_enabled": False,
                "webhook_enabled": False,
                "email_config": None,
                "webhook_config": None,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "08:00",
            }
        }
    )

    in_app_enabled: bool = Field(default=True, description="Enable in-app notifications")
    email_enabled: bool = Field(default=False, description="Enable email notifications")
    webhook_enabled: bool = Field(default=False, description="Enable webhook notifications")
    email_config: EmailConfig | None = Field(None, description="Email configuration")
    webhook_config: WebhookConfig | None = Field(None, description="Webhook configuration")
    quiet_hours_start: str | None = Field(
        None, description="Start of quiet hours (HH:MM format, no notifications)"
    )
    quiet_hours_end: str | None = Field(None, description="End of quiet hours (HH:MM format)")


# ============================================================================
# API Response Models
# ============================================================================


class NotificationResponse(BaseModel):
    """Response model for a single notification."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notification_id": "550e8400-e29b-41d4-a716-446655440000",
                "notification_type": "job_completed",
                "title": "Job Completed",
                "message": "Your video conversion job has completed successfully.",
                "priority": "normal",
                "job_id": "job_abc123",
                "data": {"output_file": "video_3d.mp4"},
                "read": False,
                "dismissed": False,
                "created_at": "2024-01-15T10:30:00Z",
                "expires_at": None,
            }
        }
    )

    notification_id: str = Field(..., description="Unique notification identifier")
    notification_type: NotificationType = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Priority level"
    )
    job_id: str | None = Field(None, description="Associated job ID if applicable")
    data: dict[str, Any] = Field(default_factory=dict, description="Additional data payload")
    read: bool = Field(default=False, description="Whether notification has been read")
    dismissed: bool = Field(default=False, description="Whether notification has been dismissed")
    created_at: datetime = Field(..., description="When notification was created")
    expires_at: datetime | None = Field(None, description="When notification expires")


class NotificationListResponse(BaseModel):
    """Response model for notification listing."""

    notifications: list[NotificationResponse] = Field(
        default_factory=list, description="List of notifications"
    )
    total_count: int = Field(default=0, description="Total number of notifications")
    unread_count: int = Field(default=0, description="Number of unread notifications")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Items per page")


class NotificationCountResponse(BaseModel):
    """Response model for notification counts."""

    total: int = Field(default=0, description="Total notifications")
    unread: int = Field(default=0, description="Unread notifications")
    dismissed: int = Field(default=0, description="Dismissed notifications")


class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""

    notification_ids: list[str] = Field(..., description="List of notification IDs to mark as read")


class MarkReadResponse(BaseModel):
    """Response after marking notifications as read."""

    updated_count: int = Field(..., description="Number of notifications updated")
    message: str = Field(default="Notifications marked as read")


class DismissRequest(BaseModel):
    """Request to dismiss notifications."""

    notification_ids: list[str] = Field(..., description="List of notification IDs to dismiss")


class DismissResponse(BaseModel):
    """Response after dismissing notifications."""

    updated_count: int = Field(..., description="Number of notifications dismissed")
    message: str = Field(default="Notifications dismissed")


class WebhookPayload(BaseModel):
    """Payload sent to webhook endpoints."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_type": "job_completed",
                "timestamp": "2024-01-15T10:30:00Z",
                "job_id": "job_abc123",
                "data": {
                    "status": "completed",
                    "output_file": "video_3d.mp4",
                    "processing_time_seconds": 125.5,
                },
            }
        }
    )

    event_type: NotificationType = Field(..., description="Type of event that triggered webhook")
    timestamp: datetime = Field(..., description="When event occurred")
    job_id: str | None = Field(None, description="Associated job ID")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")


__all__ = [
    # Enums
    "NotificationType",
    "NotificationPriority",
    # Domain model
    "Notification",
    # Request models
    "WebhookConfig",
    "EmailConfig",
    "NotificationPreferences",
    # Response models
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationCountResponse",
    "MarkReadRequest",
    "MarkReadResponse",
    "DismissRequest",
    "DismissResponse",
    "WebhookPayload",
]
