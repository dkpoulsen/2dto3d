"""Jobs router for managing video conversion jobs.

This module provides endpoints for:
- Submitting conversion jobs
- Checking job status
- Listing jobs
- Cancelling jobs
- Retrying failed jobs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status

from video2d3d.batch.models import JobPriority, JobStatus
from video2d3d.utils.config import get_config
from video2d3d.utils.logger import get_logger
from video2d3d.web.exceptions import (
    FileNotFoundError,
    JobNotCancellableError,
    JobNotFoundError,
    JobNotRetryableError,
    QueueNotRunningError,
    ValidationError,
)
from video2d3d.web.schemas import (
    CancelJobResponse,
    ErrorResponse,
    JobListResponse,
    JobPriorityRequest,
    JobResponse,
    JobResultResponse,
    JobStatusResponse,
    QueueStatsResponse,
    RetryJobResponse,
    SubmitBatchRequest,
    SubmitJobRequest,
    SubmitJobResponse,
    ThumbnailFrameResponse,
    ThumbnailGridResponse,
)
from video2d3d.web.state import app_state
from video2d3d.web.utils import (
    SUPPORTED_VIDEO_EXTENSIONS,
    find_file_by_id,
    validate_file_id,
)

logger = get_logger("web.jobs")

router = APIRouter()

# Configuration
_config = get_config()
API_PREFIX = _config.web_api.prefix

# Thumbnail grid defaults
DEFAULT_THUMBNAIL_COUNT = 24
DEFAULT_FPS = 30.0
DEFAULT_TOTAL_FRAMES = 0
THUMBNAIL_COUNT_MIN = 1
THUMBNAIL_COUNT_MAX = 100


def priority_to_model(priority: JobPriorityRequest) -> JobPriority:
    """Convert API priority enum to batch model priority."""
    mapping = {
        JobPriorityRequest.LOW: JobPriority.LOW,
        JobPriorityRequest.NORMAL: JobPriority.NORMAL,
        JobPriorityRequest.HIGH: JobPriority.HIGH,
        JobPriorityRequest.URGENT: JobPriority.URGENT,
    }
    return mapping[priority]


def status_to_response(status: JobStatus) -> JobStatusResponse:
    """Convert batch model status to API response status."""
    mapping = {
        JobStatus.PENDING: JobStatusResponse.PENDING,
        JobStatus.QUEUED: JobStatusResponse.QUEUED,
        JobStatus.PREPARING: JobStatusResponse.PREPARING,
        JobStatus.RUNNING: JobStatusResponse.RUNNING,
        JobStatus.PAUSED: JobStatusResponse.PAUSED,
        JobStatus.COMPLETED: JobStatusResponse.COMPLETED,
        JobStatus.FAILED: JobStatusResponse.FAILED,
        JobStatus.CANCELLED: JobStatusResponse.CANCELLED,
        JobStatus.RETRYING: JobStatusResponse.RETRYING,
        JobStatus.SKIPPED: JobStatusResponse.SKIPPED,
    }
    return mapping.get(status, JobStatusResponse.PENDING)


def job_to_response(job) -> JobResponse:
    """Convert batch job to API response model.

    Args:
        job: BatchJob instance.

    Returns:
        JobResponse model instance.
    """
    # Convert result if present
    result_response = None
    if job.result:
        result_response = JobResultResponse(
            success=job.result.success,
            output_file_id=str(job.result.output_path.stem) if job.result.output_path else None,
            output_filename=job.result.output_path.name if job.result.output_path else None,
            error_message=job.result.error_message,
            error_type=job.result.error_type,
            frames_processed=job.result.frames_processed,
            processing_time_seconds=job.result.processing_time_seconds,
        )

    # Determine output filename
    output_filename = None
    if job.output_path:
        output_filename = job.output_path.name

    return JobResponse(
        job_id=job.job_id,
        status=status_to_response(job.status),
        priority=JobPriorityRequest(job.priority.name.lower()),
        input_filename=job.input_path.name,
        output_filename=output_filename,
        progress=job.progress,
        current_stage=job.current_stage,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        elapsed_time_seconds=job.elapsed_time,
        estimated_remaining_seconds=job.estimated_remaining_time,
        retry_count=job.retry_count,
        result=result_response,
        config=job.config,
        scheduled_at=job.scheduled_at,
        depends_on=getattr(job, "depends_on", None),
        dependent_jobs=getattr(job, "dependent_jobs", []),
    )


def find_uploaded_file(file_id: str) -> Path:
    """Find an uploaded file by ID.

    Args:
        file_id: Unique file identifier.

    Returns:
        Path to the uploaded file.

    Raises:
        ValidationError: If file_id is invalid.
        FileNotFoundError: If file doesn't exist.
    """
    # Validate file_id to prevent path traversal
    if not validate_file_id(file_id):
        logger.warning(f"Invalid file_id for job: {file_id}")
        raise ValidationError(
            message="Invalid file ID format",
            field="file_id",
            value=file_id,
        )

    file_path = find_file_by_id(
        app_state.upload_dir,
        file_id,
        extensions=SUPPORTED_VIDEO_EXTENSIONS,
    )

    if not file_path:
        raise FileNotFoundError(file_id=file_id)

    return file_path


@router.post(
    "/",
    response_model=SubmitJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a conversion job",
    description="Submit a new video conversion job to the processing queue.",
    responses={
        201: {"description": "Job submitted successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Input file not found"},
        503: {"model": ErrorResponse, "description": "Queue not running"},
    },
)
async def submit_job(request: SubmitJobRequest) -> SubmitJobResponse:
    """Submit a new conversion job.

    Args:
        request: Job submission request with file ID and options.

    Returns:
        Job submission response with job ID.

    Raises:
        FileNotFoundError: If input file doesn't exist.
        QueueNotRunningError: If queue is not running.
    """
    if not app_state.queue:
        raise QueueNotRunningError()

    if not app_state.queue.is_running:
        raise QueueNotRunningError()

    # Find input file
    input_path = find_uploaded_file(request.input_file_id)

    # Generate output path
    if request.output_filename:
        output_filename = request.output_filename
        # Ensure it has an extension
        if not Path(output_filename).suffix:
            output_filename += ".mp4"
    else:
        # Generate output filename
        output_filename = f"{input_path.stem}_3d.mp4"

    output_path = app_state.output_dir / output_filename

    # Build job configuration
    job_config = {
        "stereo_format": request.config.stereo_format.value,
        "depth_model": request.config.depth_model.value,
        "use_gpu": request.config.use_gpu,
        "quality_preset": request.config.quality_preset,
        "output_codec": request.config.output_codec,
        "output_crf": request.config.output_crf,
        **request.config.extra_options,
    }

    # Add depth curve config if provided
    if request.config.depth_curve:
        job_config["depth_curve"] = request.config.depth_curve.model_dump()

    # Add depth focus config if provided
    if request.config.depth_focus:
        job_config["depth_focus"] = request.config.depth_focus.model_dump()

    # Add callback URL if provided
    # Add callback URL if provided
    if request.callback_url:
        job_config["callback_url"] = request.callback_url

    # Submit job to queue
    job = app_state.queue.add_job(
        input_path=input_path,
        output_path=output_path,
        priority=priority_to_model(request.priority),
        config=job_config,
        source="api",
        scheduled_at=request.scheduled_at,
        depends_on=request.depends_on,
    )

    logger.info(f"Submitted job {job.job_id} for file {input_path.name}")

    return SubmitJobResponse(
        job_id=job.job_id,
        status=status_to_response(job.status),
        message="Job submitted successfully",
        status_url=f"{API_PREFIX}/jobs/{job.job_id}",
    )


@router.post(
    "/batch",
    response_model=list[SubmitJobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit multiple jobs",
    description="Submit multiple conversion jobs at once.",
    responses={
        201: {"description": "Jobs submitted successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "One or more input files not found"},
    },
)
async def submit_batch(request: SubmitBatchRequest) -> list[SubmitJobResponse]:
    """Submit multiple conversion jobs.

    Args:
        request: Batch submission request with file IDs.

    Returns:
        List of job submission responses.

    Raises:
        FileNotFoundError: If any input file doesn't exist.
        QueueNotRunningError: If queue is not running.
    """
    if not app_state.queue or not app_state.queue.is_running:
        raise QueueNotRunningError()

    responses = []

    for file_id in request.input_file_ids:
        # Create individual job request
        job_request = SubmitJobRequest(
            input_file_id=file_id,
            priority=request.priority,
            config=request.config,
        )

        # Submit job
        response = await submit_job(job_request)
        responses.append(response)

    return responses


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job status",
    description="Get the current status and details of a conversion job.",
    responses={
        200: {"description": "Job details"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_job(job_id: str) -> JobResponse:
    """Get job details by ID.

    Args:
        job_id: Unique job identifier.

    Returns:
        Job details.

    Raises:
        JobNotFoundError: If job doesn't exist.
    """
    if not app_state.queue:
        raise QueueNotRunningError()

    job = app_state.queue.get_job(job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    return job_to_response(job)


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List jobs",
    description="List all jobs, optionally filtered by status.",
)
async def list_jobs(
    status: JobStatusResponse | None = None,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> JobListResponse:
    """List jobs with optional filtering.

    Args:
        status: Filter by job status (optional).
        page: Page number for pagination.
        page_size: Number of items per page.

    Returns:
        Paginated list of jobs.
    """
    if not app_state.queue:
        return JobListResponse(
            jobs=[],
            total_count=0,
            page=page,
            page_size=page_size,
        )

    # Get all jobs
    # Convert status filter if provided
    status_filter = None
    if status:
        status_mapping = {
            JobStatusResponse.PENDING: JobStatus.PENDING,
            JobStatusResponse.QUEUED: JobStatus.QUEUED,
            JobStatusResponse.PREPARING: JobStatus.PREPARING,
            JobStatusResponse.RUNNING: JobStatus.RUNNING,
            JobStatusResponse.PAUSED: JobStatus.PAUSED,
            JobStatusResponse.COMPLETED: JobStatus.COMPLETED,
            JobStatusResponse.FAILED: JobStatus.FAILED,
            JobStatusResponse.CANCELLED: JobStatus.CANCELLED,
            JobStatusResponse.RETRYING: JobStatus.RETRYING,
            JobStatusResponse.SKIPPED: JobStatus.SKIPPED,
        }
        status_filter = status_mapping.get(status)

    jobs = app_state.queue.get_all_jobs(status=status_filter)

    # Convert to response models
    job_responses = [job_to_response(job) for job in jobs]

    # Paginate
    total_count = len(job_responses)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_jobs = job_responses[start_idx:end_idx]

    return JobListResponse(
        jobs=paginated_jobs,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{job_id}/cancel",
    response_model=CancelJobResponse,
    summary="Cancel a job",
    description="Cancel a pending or running job.",
    responses={
        200: {"description": "Job cancelled"},
        400: {"model": ErrorResponse, "description": "Job cannot be cancelled"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def cancel_job(job_id: str) -> CancelJobResponse:
    """Cancel a job.

    Args:
        job_id: Unique job identifier.

    Returns:
        Cancellation response.

    Raises:
        JobNotFoundError: If job doesn't exist.
        JobNotCancellableError: If job cannot be cancelled.
    """
    if not app_state.queue:
        raise QueueNotRunningError()

    job = app_state.queue.get_job(job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    # Check if job can be cancelled
    if job.status.is_terminal:
        raise JobNotCancellableError(
            job_id=job_id,
            status=job.status.value,
            reason="Job has already completed",
        )

    # Cancel the job
    success = app_state.queue.cancel_job(job_id)

    if not success:
        raise JobNotCancellableError(
            job_id=job_id,
            status=job.status.value,
        )

    logger.info(f"Cancelled job {job_id}")

    return CancelJobResponse(
        job_id=job_id,
        cancelled=True,
        message="Job cancelled successfully",
    )


@router.post(
    "/{job_id}/retry",
    response_model=RetryJobResponse,
    summary="Retry a failed job",
    description="Retry a failed job.",
    responses={
        200: {"description": "Job queued for retry"},
        400: {"model": ErrorResponse, "description": "Job cannot be retried"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def retry_job(job_id: str) -> RetryJobResponse:
    """Retry a failed job.

    Args:
        job_id: Unique job identifier.

    Returns:
        Retry response.

    Raises:
        JobNotFoundError: If job doesn't exist.
        JobNotRetryableError: If job cannot be retried.
    """
    if not app_state.queue:
        raise QueueNotRunningError()

    job = app_state.queue.get_job(job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    # Check if job can be retried
    if not job.is_retryable:
        raise JobNotRetryableError(
            job_id=job_id,
            status=job.status.value,
            reason="Job is not in a retryable state or max retries exceeded",
        )

    # Retry the job
    success = app_state.queue.retry_job(job_id)

    if not success:
        raise JobNotRetryableError(
            job_id=job_id,
            status=job.status.value,
        )

    # Get updated job
    job = app_state.queue.get_job(job_id)

    logger.info(f"Retrying job {job_id}")

    return RetryJobResponse(
        job_id=job_id,
        retried=True,
        retry_count=job.retry_count if job else 0,
        message="Job queued for retry",
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a job",
    description="Remove a completed, failed, or cancelled job from the queue.",
    responses={
        204: {"description": "Job removed"},
        400: {"model": ErrorResponse, "description": "Job cannot be removed"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def remove_job(job_id: str) -> None:
    """Remove a job from the queue.

    Args:
        job_id: Unique job identifier.

    Raises:
        JobNotFoundError: If job doesn't exist.
        HTTPException: If job is running and cannot be removed.
    """
    if not app_state.queue:
        raise QueueNotRunningError()

    job = app_state.queue.get_job(job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    # Cannot remove running jobs
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove a running job. Cancel it first.",
        )

    # Remove the job
    success = app_state.queue.remove_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove job",
        )

    logger.info(f"Removed job {job_id}")


@router.get(
    "/stats/queue",
    response_model=QueueStatsResponse,
    summary="Get queue statistics",
    description="Get statistics about the job queue.",
)
async def get_queue_stats() -> QueueStatsResponse:
    """Get queue statistics.

    Returns:
        Queue statistics.
    """
    if not app_state.queue:
        return QueueStatsResponse()

    stats = app_state.queue.get_stats()

    return QueueStatsResponse(
        total_jobs=stats.total_jobs,
        pending_jobs=stats.pending_jobs,
        running_jobs=stats.running_jobs,
        completed_jobs=stats.completed_jobs,
        failed_jobs=stats.failed_jobs,
        cancelled_jobs=stats.cancelled_jobs,
        skipped_jobs=stats.skipped_jobs,
        total_frames_processed=stats.total_frames_processed,
        total_processing_time_seconds=stats.total_processing_time,
        average_processing_time_seconds=stats.average_processing_time,
        success_rate_percent=stats.success_rate,
    )


@router.get(
    "/{job_id}/thumbnails",
    response_model=ThumbnailGridResponse,
    summary="Get thumbnail grid for a job",
    description="Get a grid of thumbnails showing frames at different timestamps with their depth maps.",
    responses={
        200: {"description": "Thumbnail grid data"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_thumbnail_grid(
    job_id: str,
    count: int | None = Query(
        default=DEFAULT_THUMBNAIL_COUNT,
        ge=THUMBNAIL_COUNT_MIN,
        le=THUMBNAIL_COUNT_MAX,
        description="Number of thumbnails",
    ),
    start_frame: int | None = Query(default=None, ge=0, description="Start frame index"),
    end_frame: int | None = Query(default=None, ge=0, description="End frame index"),
) -> ThumbnailGridResponse:
    """Get thumbnail grid data for a job.

    Returns evenly distributed frame thumbnails with original frames and depth maps
    for quick quality assessment.

    Args:
        job_id: Unique job identifier.
        count: Number of thumbnails to return (evenly distributed).
        start_frame: Optional start frame index.
        end_frame: Optional end frame index.

    Returns:
        ThumbnailGridResponse with thumbnail frames.

    Raises:
        JobNotFoundError: If job doesn't exist.
    """
    if not app_state.queue:
        raise QueueNotRunningError()

    job = app_state.queue.get_job(job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    # Get video metadata from job (use constants for defaults)
    total_frames = getattr(job, "total_frames", DEFAULT_TOTAL_FRAMES) or DEFAULT_TOTAL_FRAMES
    fps = getattr(job, "fps", DEFAULT_FPS) or DEFAULT_FPS
    duration_seconds = total_frames / fps if fps > 0 else 0.0

    # Calculate frame indices for thumbnails
    effective_start = start_frame or 0
    effective_end = end_frame or total_frames
    frame_range = effective_end - effective_start

    if frame_range <= 0 or count <= 0:
        return ThumbnailGridResponse(
            job_id=job_id,
            thumbnails=[],
            total_frames=total_frames,
            duration_seconds=duration_seconds,
        )

    # Distribute frames evenly across the range
    step = frame_range / count if count > 0 else 1
    frame_indices = [int(effective_start + i * step) for i in range(count)]
    frame_indices = [idx for idx in frame_indices if idx < total_frames]

    # Build thumbnail response
    thumbnails = []
    base_url = f"{API_PREFIX}/jobs/{job_id}"

    for frame_idx in frame_indices:
        timestamp = frame_idx / fps if fps > 0 else 0.0
        thumbnails.append(
            ThumbnailFrameResponse(
                frame_index=frame_idx,
                timestamp=round(timestamp, 3),
                original_url=f"{base_url}/frames/{frame_idx}/original",
                depth_map_url=f"{base_url}/frames/{frame_idx}/depth-map",
                confidence_score=None,  # Would be populated from actual depth processing
                validation_status="pending",  # Would be populated from validation state
            )
        )

    return ThumbnailGridResponse(
        job_id=job_id,
        thumbnails=thumbnails,
        total_frames=total_frames,
        duration_seconds=round(duration_seconds, 2),
    )


__all__ = ["router"]
