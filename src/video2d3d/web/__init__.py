"""Web API module for 2Dto3D Video Converter.

This module provides a REST API for:
- Video file upload
- Conversion job submission
- Job status tracking
- Result file download

Usage:
    from video2d3d.web import create_app, app

    # Use default app
    from video2d3d.web.app import app

    # Or create custom app
    app = create_app(title="Custom API", version="1.0.0")

Running the server:
    uvicorn video2d3d.web.app:app --host 0.0.0.0 --port 8000

    Or using CLI:
    video2d3d serve --host 0.0.0.0 --port 8000
"""

from video2d3d.web.app import app, create_app
from video2d3d.web.exceptions import (
    APIError,
    FileNotFoundError,
    FileSizeExceededError,
    FileUploadError,
    JobNotCancellableError,
    JobNotFoundError,
    JobNotRetryableError,
    ProcessingError,
    QueueNotRunningError,
    UnsupportedFormatError,
    ValidationError,
)
from video2d3d.web.schemas import (
    APIInfoResponse,
    CancelJobResponse,
    DepthModel,
    DownloadInfoResponse,
    ErrorResponse,
    HealthCheckResponse,
    JobConfigRequest,
    JobListResponse,
    JobPriorityRequest,
    JobResponse,
    JobResultResponse,
    JobStatusResponse,
    QueueStatsResponse,
    RetryJobResponse,
    StereoFormat,
    SubmitBatchRequest,
    SubmitJobRequest,
    SubmitJobResponse,
    UploadResponse,
)
from video2d3d.web.state import app_state

__all__ = [
    # App
    "app",
    "create_app",
    "app_state",
    # Exceptions
    "APIError",
    "FileNotFoundError",
    "FileSizeExceededError",
    "FileUploadError",
    "JobNotCancellableError",
    "JobNotFoundError",
    "JobNotRetryableError",
    "ProcessingError",
    "QueueNotRunningError",
    "UnsupportedFormatError",
    "ValidationError",
    # Schemas
    "APIInfoResponse",
    "CancelJobResponse",
    "DepthModel",
    "DownloadInfoResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "JobConfigRequest",
    "JobListResponse",
    "JobPriorityRequest",
    "JobResponse",
    "JobResultResponse",
    "JobStatusResponse",
    "QueueStatsResponse",
    "RetryJobResponse",
    "StereoFormat",
    "SubmitBatchRequest",
    "SubmitJobRequest",
    "SubmitJobResponse",
    "UploadResponse",
]
