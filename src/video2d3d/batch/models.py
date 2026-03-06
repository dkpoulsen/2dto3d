"""Data models for batch video processing queue.

This module defines the core data structures for managing batch video processing jobs:
- JobStatus: Enum representing the lifecycle states of a job
- BatchJob: Represents a single video conversion job in the queue
- BatchJobResult: Contains the result of a completed job
- BatchQueueStats: Statistics about the queue state
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class JobStatus(Enum):
    """Lifecycle states for a batch job."""

    PENDING = "pending"  # Job is waiting to be processed
    QUEUED = "queued"  # Job is in the queue but not started
    PREPARING = "preparing"  # Job is being prepared (validation, etc.)
    RUNNING = "running"  # Job is currently being processed
    PAUSED = "paused"  # Job is paused (can be resumed)
    COMPLETED = "completed"  # Job finished successfully
    FAILED = "failed"  # Job failed with error
    CANCELLED = "cancelled"  # Job was cancelled by user
    RETRYING = "retrying"  # Job is being retried after failure
    SKIPPED = "skipped"  # Job was skipped (e.g., already processed)

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state (job won't change)."""
        return self in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.SKIPPED,
        )

    @property
    def is_active(self) -> bool:
        """Check if the job is currently active (running or preparing)."""
        return self in (JobStatus.RUNNING, JobStatus.PREPARING, JobStatus.RETRYING)

    @property
    def is_waiting(self) -> bool:
        """Check if the job is waiting to be processed."""
        return self in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PAUSED)


class JobPriority(Enum):
    """Priority levels for batch jobs."""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


@dataclass
class BatchJobResult:
    """Result of a completed batch job.

    Attributes:
        success: Whether the job completed successfully.
        output_path: Path to the output file (if successful).
        error_message: Error message (if failed).
        error_type: Type of exception (if failed).
        frames_processed: Number of frames processed.
        processing_time_seconds: Total processing time.
        metadata: Additional result metadata.
    """

    success: bool = False
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    frames_processed: int = 0
    processing_time_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "frames_processed": self.frames_processed,
            "processing_time_seconds": self.processing_time_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchJobResult:
        """Create result from dictionary."""
        return cls(
            success=data.get("success", False),
            output_path=Path(data["output_path"]) if data.get("output_path") else None,
            error_message=data.get("error_message"),
            error_type=data.get("error_type"),
            frames_processed=data.get("frames_processed", 0),
            processing_time_seconds=data.get("processing_time_seconds", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class BatchJob:
    """Represents a single video conversion job in the batch queue.

    This is the core data structure for tracking individual video processing jobs.
    Each job has a unique ID, tracks its status, progress, and results.

    Attributes:
        job_id: Unique identifier for this job.
        input_path: Path to the input video file.
        output_path: Path where the output should be written.
        status: Current status of the job.
        priority: Job priority (higher = processed first).
        created_at: When the job was created.
        started_at: When processing started.
        completed_at: When processing completed.
        scheduled_at: When the job should start (None = immediate).
        progress: Current progress (0.0 to 1.0).
        current_stage: Current processing stage description.
        retry_count: Number of retry attempts.
        max_retries: Maximum number of retries allowed.
        result: Result of the job (when completed).
        config: Job-specific configuration overrides.
        metadata: Additional job metadata.
        source: Source of the job (manual, folder_watcher, pattern, etc.).
        depends_on: Job IDs this job depends on (must complete first).
        dependent_jobs: Job IDs that depend on this job.
    """

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_path: Path = field(default_factory=lambda: Path("."))
    output_path: Optional[Path] = None
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None  # When the job should start (None = immediate)
    progress: float = 0.0
    current_stage: str = ""
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[BatchJobResult] = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = "manual"  # manual, folder_watcher, pattern, api
    depends_on: list[str] = field(default_factory=list)  # Job IDs this job depends on
    dependent_jobs: list[str] = field(default_factory=list)  # Job IDs that depend on this job

    def __post_init__(self) -> None:
        """Validate and normalize job data."""
        if isinstance(self.input_path, str):
            self.input_path = Path(self.input_path)
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)

    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds since job started."""
        if self.started_at is None:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def is_retryable(self) -> bool:
        """Check if job can be retried."""
        return self.status == JobStatus.FAILED and self.retry_count < self.max_retries

    @property
    def estimated_remaining_time(self) -> Optional[float]:
        """Estimate remaining time based on progress."""
        if self.progress <= 0 or self.started_at is None:
            return None
        elapsed = self.elapsed_time or 0
        if elapsed <= 0:
            return None
        estimated_total = elapsed / self.progress
        return estimated_total - elapsed

    @property
    def is_scheduled_time_reached(self) -> bool:
        """Check if the scheduled start time has been reached."""
        if self.scheduled_at is None:
            return True
        return datetime.now() >= self.scheduled_at

    @property
    def has_dependencies(self) -> bool:
        """Check if this job has dependencies."""
        return len(self.depends_on) > 0

    def check_dependencies_met(self, completed_job_ids: set[str]) -> bool:
        """Check if all dependencies have been completed.

        Args:
            completed_job_ids: Set of job IDs that have completed successfully.

        Returns:
            True if all dependencies are met or there are no dependencies.
        """
        if not self.depends_on:
            return True
        return all(dep_id in completed_job_ids for dep_id in self.depends_on)

    def get_pending_dependencies(self, completed_job_ids: set[str]) -> list[str]:
        """Get list of dependency job IDs that haven't completed yet.

        Args:
            completed_job_ids: Set of job IDs that have completed successfully.

        Returns:
            List of job IDs that this job is still waiting on.
        """
        return [dep_id for dep_id in self.depends_on if dep_id not in completed_job_ids]

    def mark_started(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
        self.progress = 0.0

    def mark_completed(self, result: BatchJobResult) -> None:
        """Mark job as completed with result."""
        self.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED
        self.completed_at = datetime.now()
        self.progress = 1.0
        self.result = result

    def mark_failed(self, error: Exception) -> None:
        """Mark job as failed with error."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.result = BatchJobResult(
            success=False,
            error_message=str(error),
            error_type=type(error).__name__,
        )

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()

    def mark_skipped(self, reason: str) -> None:
        """Mark job as skipped."""
        self.status = JobStatus.SKIPPED
        self.completed_at = datetime.now()
        self.result = BatchJobResult(
            success=False,
            error_message=reason,
            metadata={"skip_reason": reason},
        )

    def increment_retry(self) -> bool:
        """Increment retry count and check if more retries allowed.

        Returns:
            True if retry is allowed, False if max retries exceeded.
        """
        if self.retry_count >= self.max_retries:
            return False
        self.retry_count += 1
        self.status = JobStatus.RETRYING
        self.completed_at = None
        self.started_at = None
        self.progress = 0.0
        return True

    def update_progress(self, progress: float, stage: str = "") -> None:
        """Update job progress.

        Args:
            progress: Progress value (0.0 to 1.0).
            stage: Current processing stage description.
        """
        self.progress = max(0.0, min(1.0, progress))
        if stage:
            self.current_stage = stage

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "input_path": str(self.input_path),
            "output_path": str(self.output_path) if self.output_path else None,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result.to_dict() if self.result else None,
            "config": self.config,
            "metadata": self.metadata,
            "source": self.source,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "depends_on": self.depends_on,
            "dependent_jobs": self.dependent_jobs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchJob:
        """Create job from dictionary."""
        result = None
        if data.get("result"):
            result = BatchJobResult.from_dict(data["result"])

        return cls(
            job_id=data["job_id"],
            input_path=Path(data["input_path"]),
            output_path=Path(data["output_path"]) if data.get("output_path") else None,
            status=JobStatus(data["status"]),
            priority=JobPriority(data.get("priority", 5)),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            progress=data.get("progress", 0.0),
            current_stage=data.get("current_stage", ""),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            result=result,
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            source=data.get("source", "manual"),
            scheduled_at=datetime.fromisoformat(data["scheduled_at"])
            if data.get("scheduled_at")
            else None,
            depends_on=data.get("depends_on", []),
            dependent_jobs=data.get("dependent_jobs", []),
        )


@dataclass
class BatchQueueStats:
    """Statistics about the batch queue state.

    Attributes:
        total_jobs: Total number of jobs in queue.
        pending_jobs: Number of pending jobs.
        running_jobs: Number of currently running jobs.
        completed_jobs: Number of completed jobs.
        failed_jobs: Number of failed jobs.
        cancelled_jobs: Number of cancelled jobs.
        total_frames_processed: Total frames processed across all jobs.
        total_processing_time: Total processing time in seconds.
        average_processing_time: Average processing time per job.
    """

    total_jobs: int = 0
    pending_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    skipped_jobs: int = 0
    total_frames_processed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        finished = self.completed_jobs + self.failed_jobs
        if finished == 0:
            return 0.0
        return (self.completed_jobs / finished) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "total_jobs": self.total_jobs,
            "pending_jobs": self.pending_jobs,
            "running_jobs": self.running_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "cancelled_jobs": self.cancelled_jobs,
            "skipped_jobs": self.skipped_jobs,
            "total_frames_processed": self.total_frames_processed,
            "total_processing_time": self.total_processing_time,
            "average_processing_time": self.average_processing_time,
            "success_rate": self.success_rate,
        }


__all__ = [
    "JobStatus",
    "JobPriority",
    "BatchJob",
    "BatchJobResult",
    "BatchQueueStats",
]
