"""Pydantic schemas for REST API request/response models.

This module defines all the data models used by the FastAPI endpoints
for validation, serialization, and documentation generation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobStatusResponse(str, Enum):
    """Job status values for API responses."""

    PENDING = "pending"
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class JobPriorityRequest(str, Enum):
    """Job priority levels for API requests."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class StereoFormat(str, Enum):
    """Available 3D output formats."""

    SIDE_BY_SIDE = "side_by_side"
    ANAGLYPH = "anaglyph"
    INTERLACED = "interlaced"
    VR = "vr"


class DepthModel(str, Enum):
    """Available depth estimation models."""

    MIDAS_SMALL = "midas_small"
    MIDAS_HYBRID = "midas_hybrid"
    DPT_LARGE = "dpt_large"
    DPT_HYBRID = "dpt_hybrid"


# ============================================================================
# Request Models
# ============================================================================


class JobConfigRequest(BaseModel):
    """Configuration options for a video conversion job."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stereo_format": "side_by_side",
                "depth_model": "midas_small",
                "use_gpu": True,
                "quality_preset": "balanced",
                "output_codec": "libx264",
                "output_crf": 23,
                "extra_options": {},
            }
        }
    )

    stereo_format: StereoFormat = Field(
        default=StereoFormat.SIDE_BY_SIDE,
        description="Output 3D format",
    )
    depth_model: DepthModel = Field(
        default=DepthModel.MIDAS_SMALL,
        description="Depth estimation model to use",
    )
    use_gpu: bool = Field(
        default=True,
        description="Whether to use GPU acceleration",
    )
    quality_preset: str = Field(
        default="balanced",
        description="Quality preset: fast, balanced, or quality",
    )
    output_codec: str = Field(
        default="libx264",
        description="Output video codec",
    )
    output_crf: int = Field(
        default=23,
        ge=0,
        le=51,
        description="CRF quality value (0-51, lower is better)",
    )
    extra_options: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing options",
    )


class SubmitJobRequest(BaseModel):
    """Request to submit a new conversion job."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "input_file_id": "550e8400-e29b-41d4-a716-446655440000",
                "output_filename": "my_video_3d.mp4",
                "priority": "normal",
                "config": {
                    "stereo_format": "side_by_side",
                    "depth_model": "midas_small",
                    "use_gpu": True,
                },
                "callback_url": "https://example.com/callback",
            }
        }
    )

    input_file_id: str = Field(
        ...,
        description="ID of the uploaded input file",
        min_length=1,
    )
    output_filename: Optional[str] = Field(
        default=None,
        description="Custom output filename (optional)",
    )
    priority: JobPriorityRequest = Field(
        default=JobPriorityRequest.NORMAL,
        description="Job priority level",
    )
    config: JobConfigRequest = Field(
        default_factory=JobConfigRequest,
        description="Job configuration options",
    )
    callback_url: Optional[str] = Field(
        default=None,
        description="URL to POST completion notification",
    )

    @field_validator("output_filename")
    @classmethod
    def validate_output_filename(cls, v: Optional[str]) -> Optional[str]:
        """Validate output filename format."""
        if v is not None:
            # Remove path separators for security
            v = v.replace("/", "_").replace("\\", "_")
        return v


class SubmitBatchRequest(BaseModel):
    """Request to submit multiple conversion jobs."""

    input_file_ids: list[str] = Field(
        ...,
        description="List of uploaded input file IDs",
        min_length=1,
    )
    priority: JobPriorityRequest = Field(
        default=JobPriorityRequest.NORMAL,
        description="Priority for all jobs",
    )
    config: JobConfigRequest = Field(
        default_factory=JobConfigRequest,
        description="Configuration for all jobs",
    )


# ============================================================================
# Response Models
# ============================================================================


class UploadResponse(BaseModel):
    """Response after successful file upload."""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_type: Optional[str] = Field(None, description="Detected content type")
    upload_time: datetime = Field(..., description="Upload timestamp")
    message: str = Field(default="File uploaded successfully")


class JobResultResponse(BaseModel):
    """Result details for a completed job."""

    success: bool = Field(..., description="Whether job succeeded")
    output_file_id: Optional[str] = Field(None, description="ID of output file")
    output_filename: Optional[str] = Field(None, description="Output filename")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Error type if failed")
    frames_processed: int = Field(default=0, description="Number of frames processed")
    processing_time_seconds: float = Field(
        default=0.0,
        description="Total processing time",
    )


class JobResponse(BaseModel):
    """Full job details response."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusResponse = Field(..., description="Current job status")
    priority: JobPriorityRequest = Field(..., description="Job priority")
    input_filename: str = Field(..., description="Input video filename")
    output_filename: Optional[str] = Field(None, description="Output filename")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Processing progress (0.0 to 1.0)",
    )
    current_stage: str = Field(default="", description="Current processing stage")
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    elapsed_time_seconds: Optional[float] = Field(
        None,
        description="Elapsed processing time",
    )
    estimated_remaining_seconds: Optional[float] = Field(
        None,
        description="Estimated remaining time",
    )
    retry_count: int = Field(default=0, description="Number of retry attempts")
    result: Optional[JobResultResponse] = Field(
        None,
        description="Job result (when completed)",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Job configuration",
    )


class JobListResponse(BaseModel):
    """Response for job listing endpoint."""

    jobs: list[JobResponse] = Field(..., description="List of jobs")
    total_count: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Number of items per page")


class SubmitJobResponse(BaseModel):
    """Response after job submission."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusResponse = Field(..., description="Initial job status")
    message: str = Field(default="Job submitted successfully")
    status_url: str = Field(..., description="URL to check job status")


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""

    total_jobs: int = Field(default=0, description="Total jobs in queue")
    pending_jobs: int = Field(default=0, description="Jobs waiting to process")
    running_jobs: int = Field(default=0, description="Currently running jobs")
    completed_jobs: int = Field(default=0, description="Successfully completed jobs")
    failed_jobs: int = Field(default=0, description="Failed jobs")
    cancelled_jobs: int = Field(default=0, description="Cancelled jobs")
    skipped_jobs: int = Field(default=0, description="Skipped jobs")
    total_frames_processed: int = Field(default=0, description="Total frames processed")
    total_processing_time_seconds: float = Field(default=0.0)
    average_processing_time_seconds: float = Field(default=0.0)
    success_rate_percent: float = Field(default=0.0, description="Success rate")


class CancelJobResponse(BaseModel):
    """Response after job cancellation."""

    job_id: str = Field(..., description="Job identifier")
    cancelled: bool = Field(..., description="Whether cancellation succeeded")
    message: str = Field(default="Job cancelled")


class RetryJobResponse(BaseModel):
    """Response after job retry request."""

    job_id: str = Field(..., description="Job identifier")
    retried: bool = Field(..., description="Whether retry was initiated")
    retry_count: int = Field(default=0, description="Current retry count")
    message: str = Field(default="Job queued for retry")


class DownloadInfoResponse(BaseModel):
    """Information about a downloadable file."""

    file_id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME content type")
    download_url: str = Field(..., description="URL to download the file")
    created_at: datetime = Field(..., description="File creation time")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[dict[str, Any]] = Field(
        None,
        description="Additional error details",
    )
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime")
    queue_running: bool = Field(..., description="Whether queue is processing")
    gpu_available: bool = Field(default=False, description="GPU availability")


class APIInfoResponse(BaseModel):
    """API information response."""

    name: str = Field(default="2Dto3D Video Converter API")
    version: str = Field(..., description="API version")
    description: str = Field(
        default="REST API for converting 2D videos to 3D using deep learning",
    )
    endpoints: dict[str, str] = Field(
        default_factory=lambda: {
            "jobs": "/api/v1/jobs",
            "upload": "/api/v1/upload",
            "download": "/api/v1/download",
            "health": "/api/v1/health",
            "queue": "/api/v1/queue",
        },
    )
    supported_formats: list[str] = Field(
        default_factory=lambda: ["mp4", "avi", "mov", "mkv", "webm"],
    )
    supported_models: list[str] = Field(
        default_factory=lambda: [
            "midas_small",
            "midas_hybrid",
            "dpt_large",
            "dpt_hybrid",
        ],
    )


__all__ = [
    # Enums
    "JobStatusResponse",
    "JobPriorityRequest",
    "StereoFormat",
    "DepthModel",
    # Request models
    "JobConfigRequest",
    "SubmitJobRequest",
    "SubmitBatchRequest",
    # Response models
    "UploadResponse",
    "JobResultResponse",
    "JobResponse",
    "JobListResponse",
    "SubmitJobResponse",
    "QueueStatsResponse",
    "CancelJobResponse",
    "RetryJobResponse",
    "DownloadInfoResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "APIInfoResponse",
]
