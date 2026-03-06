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


class CurveControlPointRequest(BaseModel):
    """A single control point on the depth curve."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"x": 0.5, "y": 0.5},
        }
    )

    x: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Input depth value (normalized 0-1)",
    )
    y: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Output depth value (normalized 0-1)",
    )


class DepthCurveRequest(BaseModel):
    """Depth curve configuration for non-linear depth mapping.

    Allows artistic control over 3D effect strength by adjusting
    how input depth values map to output depth values.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "preset": "s_curve",
                "control_points": [
                    {"x": 0.0, "y": 0.0},
                    {"x": 0.25, "y": 0.15},
                    {"x": 0.5, "y": 0.5},
                    {"x": 0.75, "y": 0.85},
                    {"x": 1.0, "y": 1.0},
                ],
            },
        }
    )

    enabled: bool = Field(
        default=False,
        description="Whether depth curve adjustment is enabled",
    )
    preset: Optional[str] = Field(
        default=None,
        description="Preset curve name: linear, s_curve, contrast_boost, soft_curve, inverse_s, shadow_lift, highlight_compress",
    )
    control_points: list[CurveControlPointRequest] = Field(
        default_factory=lambda: [
            CurveControlPointRequest(x=0.0, y=0.0),
            CurveControlPointRequest(x=1.0, y=1.0),
        ],
        description="Control points defining the curve (ignored if preset is set)",
    )

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
    depth_curve: Optional[DepthCurveRequest] = Field(
        default=None,
        description="Depth curve adjustment for non-linear depth mapping",
    )


class SubmitJobRequest(BaseModel):
    """Request to submit a new conversion job.

    This schema defines the structure for submitting a video conversion job.
    The job will be added to the processing queue and executed based on priority.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "input_file_id": "550e8400-e29b-41d4-a716-446655440000",
                "output_filename": "my_vacation_video_3d.mp4",
                "priority": "normal",
                "config": {
                    "stereo_format": "side_by_side",
                    "depth_model": "midas_small",
                    "use_gpu": True,
                    "quality_preset": "balanced",
                    "output_codec": "libx264",
                    "output_crf": 23,
                    "extra_options": {"temporal_smoothing": True},
                },
                "callback_url": "https://example.com/webhook/video-complete",
            },
            "examples": [
                {
                    "description": "Basic job with default settings",
                    "value": {
                        "input_file_id": "550e8400-e29b-41d4-a716-446655440000",
                        "priority": "normal",
                    },
                },
                {
                    "description": "High priority VR video conversion",
                    "value": {
                        "input_file_id": "550e8400-e29b-41d4-a716-446655440000",
                        "output_filename": "vr_video_3d.mp4",
                        "priority": "urgent",
                        "config": {
                            "stereo_format": "vr",
                            "depth_model": "dpt_large",
                            "use_gpu": True,
                            "quality_preset": "quality",
                        },
                    },
                },
                {
                    "description": "Fast conversion with callback",
                    "value": {
                        "input_file_id": "550e8400-e29b-41d4-a716-446655440000",
                        "priority": "high",
                        "config": {
                            "stereo_format": "anaglyph",
                            "depth_model": "midas_small",
                            "quality_preset": "fast",
                        },
                        "callback_url": "https://myapp.com/api/video-callback",
                    },
                },
            ],
        }
    )

    input_file_id: str = Field(
        ...,
        description="Unique identifier of the uploaded input file (UUID format)",
        min_length=1,
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    output_filename: Optional[str] = Field(
        default=None,
        description="Custom output filename. If not provided, will be auto-generated as '{input_name}_3d.mp4'. "
        "Path separators are automatically removed for security.",
        examples=["my_vacation_3d.mp4"],
    )
    priority: JobPriorityRequest = Field(
        default=JobPriorityRequest.NORMAL,
        description="Job priority level. Higher priority jobs are processed first.",
    )
    config: JobConfigRequest = Field(
        default_factory=JobConfigRequest,
        description="Job configuration options for video conversion.",
    )
    callback_url: Optional[str] = Field(
        default=None,
        description="Optional webhook URL that will receive a POST request when the job completes. "
        "The callback payload includes job status, output file ID, and any error details.",
        examples=["https://example.com/webhook/video-complete"],
    )
    scheduled_at: Optional[datetime] = Field(
        default=None,
        description="Optional UTC timestamp when the job should start processing. "
        "If not provided, the job will start immediately (subject to queue availability).",
        examples=["2024-01-15T14:30:00Z"],
    )
    depends_on: Optional[list[str]] = Field(
        default=None,
        description="Optional list of job IDs that must complete successfully before this job can start. "
        "This creates a dependency chain, useful for sequential processing pipelines.",
        examples=[["job_abc123", "job_def456"]],
    )

    @field_validator("output_filename")
    @classmethod
    def validate_output_filename(cls, v: Optional[str]) -> Optional[str]:
        """Validate output filename format.

        Removes path separators for security to prevent directory traversal attacks.
        """
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
    """Response after successful file upload.

    Contains the file ID which should be used in subsequent job submission requests.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "vacation_video.mp4",
                "file_size_bytes": 52428800,
                "content_type": "video/mp4",
                "upload_time": "2024-01-15T10:30:00Z",
                "message": "File uploaded successfully",
            }
        }
    )

    file_id: str = Field(
        ...,
        description="Unique file identifier (UUID). Use this ID when submitting conversion jobs.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    filename: str = Field(
        ...,
        description="Original filename as uploaded.",
        examples=["vacation_video.mp4"],
    )
    file_size_bytes: int = Field(
        ...,
        description="File size in bytes.",
        examples=[52428800, 104857600],
    )
    content_type: Optional[str] = Field(
        None,
        description="Detected MIME content type based on file extension.",
        examples=["video/mp4", "video/x-msvideo"],
    )
    upload_time: datetime = Field(
        ...,
        description="UTC timestamp when the file was uploaded.",
    )
    message: str = Field(
        default="File uploaded successfully",
        description="Success message.",
    )

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
    """Full job details response.

    Contains complete information about a conversion job including status,
    progress, timing information, and result (when completed).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job_abc123",
                "status": "completed",
                "priority": "normal",
                "input_filename": "vacation_video.mp4",
                "output_filename": "vacation_video_3d.mp4",
                "progress": 1.0,
                "current_stage": "complete",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": "2024-01-15T10:45:30Z",
                "elapsed_time_seconds": 925.5,
                "estimated_remaining_seconds": None,
                "retry_count": 0,
                "result": {
                    "success": True,
                    "output_file_id": "out_xyz789",
                    "output_filename": "vacation_video_3d.mp4",
                    "error_message": None,
                    "error_type": None,
                    "frames_processed": 1500,
                    "processing_time_seconds": 925.5,
                },
                "config": {
                    "stereo_format": "side_by_side",
                    "depth_model": "midas_small",
                    "use_gpu": True,
                },
            }
        }
    )

    job_id: str = Field(
        ...,
        description="Unique job identifier.",
        examples=["job_abc123"],
    )
    status: JobStatusResponse = Field(
        ...,
        description="Current job status. Possible values: pending, queued, preparing, running, paused, completed, failed, cancelled, retrying, skipped.",
    )
    priority: JobPriorityRequest = Field(
        ...,
        description="Job priority level.",
    )
    input_filename: str = Field(
        ...,
        description="Original input video filename.",
        examples=["vacation_video.mp4"],
    )
    output_filename: Optional[str] = Field(
        None,
        description="Output 3D video filename.",
        examples=["vacation_video_3d.mp4"],
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Processing progress from 0.0 (not started) to 1.0 (complete).",
        examples=[0.0, 0.5, 0.75, 1.0],
    )
    current_stage: str = Field(
        default="",
        description="Current processing stage (e.g., 'extracting_frames', 'depth_estimation', 'stereo_generation', 'encoding').",
        examples=["depth_estimation"],
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the job was created.",
    )
    started_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when processing started. Null if not yet started.",
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when processing completed. Null if still running.",
    )
    elapsed_time_seconds: Optional[float] = Field(
        None,
        description="Elapsed processing time in seconds. Null if not yet started.",
        examples=[125.5, 925.0],
    )
    estimated_remaining_seconds: Optional[float] = Field(
        None,
        description="Estimated remaining time in seconds. Null if unknown or job is complete.",
        examples=[60.0, 120.5],
    )
    retry_count: int = Field(
        default=0,
        description="Number of automatic retry attempts made.",
        ge=0,
    )
    result: Optional[JobResultResponse] = Field(
        None,
        description="Job result details. Only present when job is completed.",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Job configuration used for processing.",
    )
    scheduled_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the job is scheduled to start. "
        "Null if the job starts immediately.",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="List of job IDs that this job depends on. "
        "All dependencies must complete successfully before this job can run.",
    )
    dependent_jobs: list[str] = Field(
        default_factory=list,
        description="List of job IDs that depend on this job. "
        "These jobs will be notified when this job completes.",
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




class GPUStatusResponse(BaseModel):
    """GPU status information for health check."""

    available: bool = Field(default=False, description="Whether GPU is available")
    device_name: Optional[str] = Field(None, description="GPU device name")
    device_count: int = Field(default=0, description="Number of available GPUs")
    memory_used_mb: float = Field(default=0.0, description="GPU memory used in MB")
    memory_free_mb: float = Field(default=0.0, description="GPU memory free in MB")
    memory_total_mb: float = Field(default=0.0, description="Total GPU memory in MB")
    memory_utilization_percent: float = Field(default=0.0, description="GPU memory utilization percentage")
    compute_capability: Optional[str] = Field(None, description="GPU compute capability")


class SystemMemoryResponse(BaseModel):
    """System memory information for health check."""

    total_mb: float = Field(..., description="Total system memory in MB")
    available_mb: float = Field(..., description="Available system memory in MB")
    used_mb: float = Field(..., description="Used system memory in MB")
    utilization_percent: float = Field(..., description="Memory utilization percentage")


class QueueHealthResponse(BaseModel):
    """Queue health information for health check."""

    running: bool = Field(..., description="Whether the queue is running")
    paused: bool = Field(default=False, description="Whether the queue is paused")
    total_jobs: int = Field(default=0, description="Total jobs in queue")
    pending_jobs: int = Field(default=0, description="Pending jobs waiting to process")
    running_jobs: int = Field(default=0, description="Currently running jobs")
    completed_jobs: int = Field(default=0, description="Successfully completed jobs")
    failed_jobs: int = Field(default=0, description="Failed jobs")
    queue_depth: int = Field(default=0, description="Current queue depth (pending + running)")
    success_rate_percent: float = Field(default=0.0, description="Job success rate percentage")


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComprehensiveHealthResponse(BaseModel):
    """Comprehensive health check response with detailed system status."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "uptime_seconds": 3600.5,
                "timestamp": "2024-01-15T10:30:00Z",
                "gpu": {
                    "available": True,
                    "device_name": "NVIDIA RTX 3090",
                    "memory_utilization_percent": 45.5,
                },
                "memory": {"utilization_percent": 60.0},
                "queue": {"running": True, "total_jobs": 10, "running_jobs": 2},
                "checks": {"queue": True, "gpu": True, "memory": True},
            }
        }
    )

    status: HealthStatus = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    gpu: GPUStatusResponse = Field(..., description="GPU status")
    memory: SystemMemoryResponse = Field(..., description="System memory status")
    queue: QueueHealthResponse = Field(..., description="Queue status")
    checks: dict[str, bool] = Field(
        default_factory=dict,
        description="Individual component check results",
    )



class HealthCheckResponse(BaseModel):
    """Health check response (basic/simplified).

    For comprehensive health monitoring with GPU memory, system memory,
    and queue statistics, use ComprehensiveHealthResponse instead.
    """

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


# ============================================================================
# Crash Report Models
# ============================================================================


class CrashTypeResponse(str, Enum):
    """Types of crashes that can be detected."""

    UNCAUGHT_EXCEPTION = "uncaught_exception"
    SIGNAL_RECEIVED = "signal_received"
    MANUAL_REPORT = "manual_report"
    OOM_ERROR = "oom_error"
    GPU_ERROR = "gpu_error"
    TIMEOUT_ERROR = "timeout_error"
    PROCESSING_ERROR = "processing_error"


class CrashSeverityResponse(str, Enum):
    """Severity levels for crash reports."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActiveJobInfoResponse(BaseModel):
    """Information about an active job at crash time."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    input_file: Optional[str] = Field(None, description="Input file path")
    output_file: Optional[str] = Field(None, description="Output file path")
    progress_percent: float = Field(default=0.0, description="Progress percentage")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    started_at: Optional[str] = Field(None, description="Job start time")
    frames_processed: int = Field(default=0, description="Frames processed")
    total_frames: int = Field(default=0, description="Total frames")
    error_message: Optional[str] = Field(None, description="Error message if any")


class GPUInfoResponse(BaseModel):
    """GPU state at crash time."""

    available: bool = Field(default=False, description="GPU availability")
    device_name: Optional[str] = Field(None, description="GPU device name")
    memory_used_mb: float = Field(default=0.0, description="Memory used in MB")
    memory_total_mb: float = Field(default=0.0, description="Total memory in MB")
    memory_utilization_percent: float = Field(default=0.0, description="Memory utilization")


class MemoryInfoResponse(BaseModel):
    """System memory state at crash time."""

    total_mb: float = Field(default=0.0, description="Total memory in MB")
    available_mb: float = Field(default=0.0, description="Available memory in MB")
    used_mb: float = Field(default=0.0, description="Used memory in MB")
    utilization_percent: float = Field(default=0.0, description="Memory utilization")


class ProcessInfoResponse(BaseModel):
    """Process state at crash time."""

    pid: int = Field(default=0, description="Process ID")
    cpu_percent: float = Field(default=0.0, description="CPU usage percentage")
    memory_rss_mb: float = Field(default=0.0, description="RSS memory in MB")
    num_threads: int = Field(default=1, description="Number of threads")
    uptime_seconds: float = Field(default=0.0, description="Process uptime")


class SystemStateResponse(BaseModel):
    """Complete system state captured at crash time."""

    timestamp: str = Field(..., description="Timestamp of state capture")
    uptime_seconds: float = Field(default=0.0, description="Application uptime")
    platform_system: str = Field(default="", description="Operating system")
    platform_python_version: str = Field(default="", description="Python version")
    gpu: GPUInfoResponse = Field(default_factory=GPUInfoResponse, description="GPU state")
    memory: MemoryInfoResponse = Field(default_factory=MemoryInfoResponse, description="Memory state")
    process: ProcessInfoResponse = Field(default_factory=ProcessInfoResponse, description="Process state")
    active_jobs: list[ActiveJobInfoResponse] = Field(default_factory=list, description="Active jobs")
    queue_stats: dict[str, Any] = Field(default_factory=dict, description="Queue statistics")
    app_version: str = Field(default="", description="Application version")


class CrashReportResponse(BaseModel):
    """Complete crash report with all captured data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2024-01-15T10:30:00Z",
                "crash_type": "uncaught_exception",
                "severity": "high",
                "exception_type": "RuntimeError",
                "exception_message": "CUDA out of memory",
                "exception_traceback": "Traceback...",
                "recovered": False,
            }
        }
    )

    report_id: str = Field(..., description="Unique crash report identifier")
    created_at: str = Field(..., description="Timestamp when crash was reported")
    crash_type: CrashTypeResponse = Field(..., description="Type of crash")
    severity: CrashSeverityResponse = Field(..., description="Severity level")
    exception_type: str = Field(default="", description="Exception class name")
    exception_message: str = Field(default="", description="Exception message")
    exception_traceback: str = Field(default="", description="Full traceback")
    exception_module: str = Field(default="", description="Exception module")
    signal_number: Optional[int] = Field(None, description="Signal number if signal-based")
    signal_name: Optional[str] = Field(None, description="Signal name if signal-based")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    user_message: Optional[str] = Field(None, description="User-provided message")
    system_state: Optional[SystemStateResponse] = Field(None, description="System state at crash")
    log_excerpts: list[str] = Field(default_factory=list, description="Recent log lines")
    recovered: bool = Field(default=False, description="Whether crash was recovered")
    recovery_action: Optional[str] = Field(None, description="Recovery action taken")


class CrashReportSummaryResponse(BaseModel):
    """Lightweight summary of a crash report for listing."""

    report_id: str = Field(..., description="Crash report identifier")
    created_at: str = Field(..., description="When crash was reported")
    crash_type: CrashTypeResponse = Field(..., description="Type of crash")
    severity: CrashSeverityResponse = Field(..., description="Severity level")
    exception_type: str = Field(default="", description="Exception type")
    exception_message: str = Field(default="", description="Exception message (truncated)")
    recovered: bool = Field(default=False, description="Whether crash was recovered")


class CrashReportListResponse(BaseModel):
    """List of crash report summaries with metadata."""

    reports: list[CrashReportSummaryResponse] = Field(default_factory=list, description="Crash report summaries")
    total_count: int = Field(default=0, description="Total number of reports")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Items per page")


class ManualCrashReportRequest(BaseModel):
    """Request to create a manual crash report."""

    message: str = Field(..., description="Description of the issue", min_length=1)
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")
    tags: Optional[list[str]] = Field(None, description="Tags for categorization")
    severity: CrashSeverityResponse = Field(
        default=CrashSeverityResponse.MEDIUM,
        description="Severity level",
    )

__all__ = [
    # Enums
    "JobStatusResponse",
    "JobPriorityRequest",
    "StereoFormat",
    "DepthModel",
    "HealthStatus",
    # Request models
    "CurveControlPointRequest",
    "DepthCurveRequest",
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
    "ComprehensiveHealthResponse",
    "GPUStatusResponse",
    "SystemMemoryResponse",
    "QueueHealthResponse",
    "APIInfoResponse",
    # Crash report models
    "CrashTypeResponse",
    "CrashSeverityResponse",
    "ActiveJobInfoResponse",
    "GPUInfoResponse",
    "MemoryInfoResponse",
    "ProcessInfoResponse",
    "SystemStateResponse",
    "CrashReportResponse",
    "CrashReportSummaryResponse",
    "CrashReportListResponse",
    "ManualCrashReportRequest",
]
