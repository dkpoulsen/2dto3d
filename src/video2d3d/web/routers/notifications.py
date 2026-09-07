"""API endpoints for notification management.

This module provides REST API endpoints for:
- Listing and filtering notifications
- Marking notifications as read
- Dismissing notifications
- Managing webhook and email configurations
"""

from fastapi import APIRouter, HTTPException, Query, status

from video2d3d.web.notification_manager import get_notification_manager
from video2d3d.web.notification_models import (
    DismissRequest,
    DismissResponse,
    MarkReadRequest,
    MarkReadResponse,
    Notification,
    NotificationCountResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationType,
    WebhookConfig,
)

router = APIRouter(tags=["Notifications"])


def _notification_to_response(notification: Notification) -> NotificationResponse:
    """Convert Notification domain model to API response."""
    """Convert Notification domain model to API response."""
    return NotificationResponse(
        notification_id=notification.notification_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        priority=notification.priority,
        job_id=notification.job_id,
        data=notification.data,
        read=notification.read,
        dismissed=notification.dismissed,
        created_at=notification.created_at,
        expires_at=notification.expires_at,
    )


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications",
    description="Get all notifications with optional filtering and pagination.",
)
async def list_notifications(
    include_read: bool = Query(True, description="Include read notifications"),
    include_dismissed: bool = Query(False, description="Include dismissed notifications"),
    notification_type: NotificationType | None = Query(
        None, description="Filter by notification type"
    ),
    job_id: str | None = Query(None, description="Filter by job ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> NotificationListResponse:
    """List notifications with optional filtering."""
    manager = get_notification_manager()
    notifications, total_count, unread_count = manager.get_notifications(
        include_read=include_read,
        include_dismissed=include_dismissed,
        notification_type=notification_type,
        job_id=job_id,
        page=page,
        page_size=page_size,
    )

    return NotificationListResponse(
        notifications=[_notification_to_response(n) for n in notifications],
        total_count=total_count,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/count",
    response_model=NotificationCountResponse,
    summary="Get notification counts",
    description="Get total, unread, and dismissed notification counts.",
)
async def get_notification_counts() -> NotificationCountResponse:
    """Get notification counts."""
    manager = get_notification_manager()
    notifications, total, unread = manager.get_notifications(
        include_read=True,
        include_dismissed=True,
    )

    dismissed = sum(1 for n in notifications if n.dismissed)
    unread = sum(1 for n in notifications if not n.read and not n.dismissed)

    return NotificationCountResponse(
        total=total,
        unread=unread,
        dismissed=dismissed,
    )


# Webhook management endpoints


@router.post(
    "/webhooks",
    status_code=status.HTTP_201_CREATED,
    summary="Add webhook configuration",
    description="Add a new webhook configuration for notifications.",
)
async def add_webhook(config: WebhookConfig) -> dict:
    """Add a webhook configuration."""
    manager = get_notification_manager()
    manager.add_webhook_config(config)
    return {"message": "Webhook configuration added", "url": config.url}


@router.get(
    "/webhooks",
    response_model=list[WebhookConfig],
    summary="List webhook configurations",
    description="Get all webhook configurations.",
)
async def list_webhooks() -> list[WebhookConfig]:
    """List all webhook configurations."""
    manager = get_notification_manager()
    return manager.get_webhook_configs()


@router.delete(
    "/webhooks",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove webhook configuration",
    description="Remove a webhook configuration by URL.",
)
async def remove_webhook(url: str = Query(..., description="Webhook URL to remove")) -> None:
    """Remove a webhook configuration."""
    manager = get_notification_manager()
    removed = manager.remove_webhook_config(url)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook configuration for {url} not found",
        )


__all__ = ["router"]
@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Get notification",
    description="Get a specific notification by ID.",
)
async def get_notification(notification_id: str) -> NotificationResponse:
    """Get a specific notification."""
    manager = get_notification_manager()
    notification = manager.get_notification(notification_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )

    return _notification_to_response(notification)


@router.post(
    "/mark-read",
    response_model=MarkReadResponse,
    summary="Mark notifications as read",
    description="Mark one or more notifications as read.",
)
async def mark_notifications_as_read(request: MarkReadRequest) -> MarkReadResponse:
    """Mark notifications as read."""
    manager = get_notification_manager()
    updated_count = manager.mark_as_read(request.notification_ids)

    return MarkReadResponse(
        updated_count=updated_count,
        message=f"Marked {updated_count} notifications as read",
    )


@router.post(
    "/mark-all-read",
    response_model=MarkReadResponse,
    summary="Mark all notifications as read",
    description="Mark all notifications as read.",
)
async def mark_all_notifications_as_read() -> MarkReadResponse:
    """Mark all notifications as read."""
    manager = get_notification_manager()
    updated_count = manager.mark_all_as_read()

    return MarkReadResponse(
        updated_count=updated_count,
        message=f"Marked {updated_count} notifications as read",
    )


@router.post(
    "/dismiss",
    response_model=DismissResponse,
    summary="Dismiss notifications",
    description="Dismiss one or more notifications.",
)
async def dismiss_notifications(request: DismissRequest) -> DismissResponse:
    """Dismiss notifications."""
    manager = get_notification_manager()
    updated_count = manager.dismiss(request.notification_ids)

    return DismissResponse(
        updated_count=updated_count,
        message=f"Dismissed {updated_count} notifications",
    )


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification",
    description="Delete a specific notification.",
)
async def delete_notification(notification_id: str) -> None:
    """Delete a notification."""
    manager = get_notification_manager()
    deleted = manager.delete_notification(notification_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all notifications",
    description="Delete all notifications.",
)
async def clear_all_notifications() -> None:
    """Clear all notifications."""
    manager = get_notification_manager()
    manager.clear_all()


