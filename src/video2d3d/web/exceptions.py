"""API exception classes and handlers for FastAPI.

This module defines custom exception classes for the REST API
and FastAPI exception handlers to convert them to proper HTTP responses.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "api_error",
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.detail = detail or {}
        super().__init__(message)


class FileNotFoundError(APIError):
    """Raised when a requested file is not found."""

    def __init__(
        self,
        file_id: str,
        message: str = "File not found",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="file_not_found",
            detail={"file_id": file_id},
        )
        self.file_id = file_id


class JobNotFoundError(APIError):
    """Raised when a requested job is not found."""

    def __init__(
        self,
        job_id: str,
        message: str = "Job not found",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="job_not_found",
            detail={"job_id": job_id},
        )
        self.job_id = job_id


class ValidationError(APIError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> None:
        detail = {}
        if field:
            detail["field"] = field
        if value is not None:
            detail["value"] = str(value)
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="validation_error",
            detail=detail,
        )


class FileUploadError(APIError):
    """Raised when file upload fails."""

    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        detail = {}
        if filename:
            detail["filename"] = filename
        if reason:
            detail["reason"] = reason
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="file_upload_error",
            detail=detail,
        )


class FileSizeExceededError(APIError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(
        self,
        max_size_mb: int,
        actual_size_mb: float,
    ) -> None:
        super().__init__(
            message=f"File size exceeds maximum allowed size of {max_size_mb}MB",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_type="file_too_large",
            detail={
                "max_size_mb": max_size_mb,
                "actual_size_mb": actual_size_mb,
            },
        )


class UnsupportedFormatError(APIError):
    """Raised when an unsupported file format is uploaded."""

    def __init__(
        self,
        format: str,
        supported_formats: list[str],
    ) -> None:
        super().__init__(
            message=f"Unsupported file format: {format}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="unsupported_format",
            detail={
                "format": format,
                "supported_formats": supported_formats,
            },
        )


class QueueNotRunningError(APIError):
    """Raised when trying to perform an operation on a stopped queue."""

    def __init__(
        self,
        message: str = "Processing queue is not running",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="queue_not_running",
        )


class JobNotRetryableError(APIError):
    """Raised when trying to retry a job that cannot be retried."""

    def __init__(
        self,
        job_id: str,
        status: str,
        reason: str = "Job is not in a retryable state",
    ) -> None:
        super().__init__(
            message=reason,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="job_not_retryable",
            detail={"job_id": job_id, "status": status},
        )


class JobNotCancellableError(APIError):
    """Raised when trying to cancel a job that cannot be cancelled."""

    def __init__(
        self,
        job_id: str,
        status: str,
        reason: str = "Job cannot be cancelled in its current state",
    ) -> None:
        super().__init__(
            message=reason,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="job_not_cancellable",
            detail={"job_id": job_id, "status": status},
        )


class ProcessingError(APIError):
    """Raised when video processing fails."""

    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> None:
        detail = {}
        if job_id:
            detail["job_id"] = job_id
        if stage:
            detail["stage"] = stage
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="processing_error",
            detail=detail,
        )


class RateLimitExceededError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: str,
        retry_after: Optional[int] = None,
        message: str = "Rate limit exceeded",
    ) -> None:
        detail = {"limit": limit}
        if retry_after:
            detail["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_type="rate_limit_exceeded",
            detail=detail,
        )


# ============================================================================
# Exception Handlers
# ============================================================================


async def api_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    """Handle APIError exceptions and return JSON response."""
    from video2d3d.web.schemas import ErrorResponse

    error_response = ErrorResponse(
        error=exc.error_type,
        message=exc.message,
        detail=exc.detail if exc.detail else None,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTPException and return standardized JSON response."""
    from video2d3d.web.schemas import ErrorResponse

    error_response = ErrorResponse(
        error="http_error",
        message=str(exc.detail),
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    from video2d3d.web.schemas import ErrorResponse

    errors = exc.errors()
    error_messages = [f"{e['loc'][-1]}: {e['msg']}" for e in errors]

    error_response = ErrorResponse(
        error="validation_error",
        message="; ".join(error_messages),
        detail={"errors": errors},
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(exclude_none=True),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    # Log the actual exception for debugging
    import traceback

    from video2d3d.web.schemas import ErrorResponse

    traceback.print_exc()

    error_response = ErrorResponse(
        error="internal_error",
        message="An unexpected error occurred",
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(exclude_none=True),
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""
    from pydantic import ValidationError as PydanticValidationError

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


__all__ = [
    # Exception classes
    "APIError",
    "FileNotFoundError",
    "JobNotFoundError",
    "ValidationError",
    "FileUploadError",
    "FileSizeExceededError",
    "UnsupportedFormatError",
    "QueueNotRunningError",
    "JobNotRetryableError",
    "JobNotCancellableError",
    "ProcessingError",
    "RateLimitExceededError",
    # Handlers
    "register_exception_handlers",
]
