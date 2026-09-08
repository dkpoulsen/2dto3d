"""Unit tests for batch video processing models.

Tests cover:
- JobStatus enum and its properties
- JobPriority enum
- BatchJobResult dataclass
- BatchJob dataclass
- BatchQueueStats dataclass
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.models import BatchJob, BatchJobResult, BatchQueueStats, JobPriority, JobStatus


@pytest.fixture
def mock_logger() -> Generator[None, None, None]:
    """No-op fixture kept for test signature compatibility; models do not log."""
    yield


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self) -> None:
        """Test all status values are correctly defined."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.PREPARING.value == "preparing"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.PAUSED.value == "paused"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.RETRYING.value == "retrying"
        assert JobStatus.SKIPPED.value == "skipped"

    def test_is_terminal_true(self) -> None:
        """Test terminal states return True."""
        terminal_states = [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.SKIPPED,
        ]
        for status in terminal_states:
            assert status.is_terminal is True

    def test_is_terminal_false(self) -> None:
        """Test non-terminal states return False."""
        non_terminal_states = [
            JobStatus.PENDING,
            JobStatus.QUEUED,
            JobStatus.PREPARING,
            JobStatus.RUNNING,
            JobStatus.PAUSED,
            JobStatus.RETRYING,
        ]
        for status in non_terminal_states:
            assert status.is_terminal is False

    def test_is_active_true(self) -> None:
        """Test active states return True."""
        active_states = [
            JobStatus.RUNNING,
            JobStatus.PREPARING,
            JobStatus.RETRYING,
        ]
        for status in active_states:
            assert status.is_active is True

    def test_is_active_false(self) -> None:
        """Test non-active states return False."""
        non_active_states = [
            JobStatus.PENDING,
            JobStatus.QUEUED,
            JobStatus.PAUSED,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.SKIPPED,
        ]
        for status in non_active_states:
            assert status.is_active is False

    def test_is_waiting_true(self) -> None:
        """Test waiting states return True."""
        waiting_states = [
            JobStatus.PENDING,
            JobStatus.QUEUED,
            JobStatus.PAUSED,
        ]
        for status in waiting_states:
            assert status.is_waiting is True

    def test_is_waiting_false(self) -> None:
        """Test non-waiting states return False."""
        non_waiting_states = [
            JobStatus.RUNNING,
            JobStatus.PREPARING,
            JobStatus.RETRYING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.SKIPPED,
        ]
        for status in non_waiting_states:
            assert status.is_waiting is False


class TestJobPriority:
    """Tests for JobPriority enum."""

    def test_priority_values(self) -> None:
        """Test priority values are correctly ordered."""
        assert JobPriority.LOW.value == 1
        assert JobPriority.NORMAL.value == 5
        assert JobPriority.HIGH.value == 10
        assert JobPriority.URGENT.value == 20

    def test_priority_ordering(self) -> None:
        """Test priorities can be compared."""
        assert JobPriority.LOW.value < JobPriority.NORMAL.value
        assert JobPriority.NORMAL.value < JobPriority.HIGH.value
        assert JobPriority.HIGH.value < JobPriority.URGENT.value

    def test_from_value_valid(self) -> None:
        """Test from_value returns correct priority for valid values."""
        assert JobPriority.from_value(1) == JobPriority.LOW
        assert JobPriority.from_value(5) == JobPriority.NORMAL
        assert JobPriority.from_value(10) == JobPriority.HIGH
        assert JobPriority.from_value(20) == JobPriority.URGENT

    def test_from_value_invalid_returns_normal(self) -> None:
        """Test from_value returns NORMAL for invalid/unknown values."""
        # Unknown values
        assert JobPriority.from_value(0) == JobPriority.NORMAL
        assert JobPriority.from_value(99) == JobPriority.NORMAL
        assert JobPriority.from_value(-1) == JobPriority.NORMAL
        assert JobPriority.from_value(100) == JobPriority.NORMAL

    def test_from_value_between_levels(self) -> None:
        """Test from_value returns NORMAL for values between defined levels."""
        # Values between defined levels
        assert JobPriority.from_value(2) == JobPriority.NORMAL
        assert JobPriority.from_value(7) == JobPriority.NORMAL
        assert JobPriority.from_value(15) == JobPriority.NORMAL


class TestBatchJobResult:
    """Tests for BatchJobResult dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        result = BatchJobResult()
        assert result.success is False
        assert result.output_path is None
        assert result.error_message is None
        assert result.error_type is None
        assert result.frames_processed == 0
        assert result.processing_time_seconds == 0.0
        assert result.metadata == {}

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        result = BatchJobResult(
            success=True,
            output_path=Path("/output/video.mp4"),
            frames_processed=100,
            processing_time_seconds=10.5,
            metadata={"key": "value"},
        )
        assert result.success is True
        assert result.output_path == Path("/output/video.mp4")
        assert result.frames_processed == 100
        assert result.processing_time_seconds == 10.5
        assert result.metadata == {"key": "value"}

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        result = BatchJobResult(
            success=True,
            output_path=Path("/output/video.mp4"),
            error_message=None,
            error_type=None,
            frames_processed=100,
            processing_time_seconds=10.5,
            metadata={"key": "value"},
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["output_path"] == "/output/video.mp4"
        assert data["frames_processed"] == 100
        assert data["processing_time_seconds"] == 10.5
        assert data["metadata"] == {"key": "value"}

    def test_to_dict_none_path(self) -> None:
        """Test to_dict with None output_path."""
        result = BatchJobResult()
        data = result.to_dict()
        assert data["output_path"] is None

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        data = {
            "success": True,
            "output_path": "/output/video.mp4",
            "error_message": None,
            "error_type": None,
            "frames_processed": 100,
            "processing_time_seconds": 10.5,
            "metadata": {"key": "value"},
        }
        result = BatchJobResult.from_dict(data)
        assert result.success is True
        assert result.output_path == Path("/output/video.mp4")
        assert result.frames_processed == 100
        assert result.processing_time_seconds == 10.5
        assert result.metadata == {"key": "value"}

    def test_from_dict_missing_fields(self) -> None:
        """Test from_dict with missing fields uses defaults."""
        data = {}
        result = BatchJobResult.from_dict(data)
        assert result.success is False
        assert result.output_path is None
        assert result.frames_processed == 0

    def test_roundtrip_serialization(self) -> None:
        """Test to_dict and from_dict roundtrip."""
        original = BatchJobResult(
            success=True,
            output_path=Path("/output/video.mp4"),
            frames_processed=100,
            processing_time_seconds=10.5,
            metadata={"key": "value"},
        )
        data = original.to_dict()
        restored = BatchJobResult.from_dict(data)
        assert restored.success == original.success
        assert restored.output_path == original.output_path
        assert restored.frames_processed == original.frames_processed
        assert restored.processing_time_seconds == original.processing_time_seconds


class TestBatchJob:
    """Tests for BatchJob dataclass."""

    def test_default_values(self, mock_logger: None) -> None:
        """Test default values are set correctly."""
        job = BatchJob()
        assert job.job_id != ""  # Auto-generated UUID
        assert job.input_path == Path(".")
        assert job.output_path is None
        assert job.status == JobStatus.PENDING
        assert job.priority == JobPriority.NORMAL
        assert job.progress == 0.0
        assert job.current_stage == ""
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.result is None
        assert job.config == {}
        assert job.metadata == {}
        assert job.source == "manual"

    def test_custom_values(self, mock_logger: None) -> None:
        """Test custom values are set correctly."""
        job = BatchJob(
            input_path=Path("/input/video.mp4"),
            output_path=Path("/output/video_3d.mp4"),
            priority=JobPriority.HIGH,
            max_retries=5,
            source="folder_watcher",
        )
        assert job.input_path == Path("/input/video.mp4")
        assert job.output_path == Path("/output/video_3d.mp4")
        assert job.priority == JobPriority.HIGH
        assert job.max_retries == 5
        assert job.source == "folder_watcher"

    def test_post_init_string_paths(self, mock_logger: None) -> None:
        """Test __post_init__ converts string paths to Path."""
        job = BatchJob(
            input_path="/input/video.mp4",
            output_path="/output/video_3d.mp4",
        )
        assert isinstance(job.input_path, Path)
        assert isinstance(job.output_path, Path)

    def test_elapsed_time_not_started(self, mock_logger: None) -> None:
        """Test elapsed_time returns None when not started."""
        job = BatchJob()
        assert job.elapsed_time is None

    def test_elapsed_time_running(self, mock_logger: None) -> None:
        """Test elapsed_time returns value when running."""
        job = BatchJob()
        job.started_at = datetime.now() - timedelta(seconds=10)
        elapsed = job.elapsed_time
        assert elapsed is not None
        assert elapsed >= 10

    def test_elapsed_time_completed(self, mock_logger: None) -> None:
        """Test elapsed_time is fixed when completed."""
        job = BatchJob()
        job.started_at = datetime.now() - timedelta(seconds=10)
        job.completed_at = datetime.now() - timedelta(seconds=5)
        assert job.elapsed_time is not None
        assert 4.9 < job.elapsed_time < 5.1

    def test_is_retryable_failed_within_limit(self, mock_logger: None) -> None:
        """Test is_retryable returns True for failed job within retry limit."""
        job = BatchJob(status=JobStatus.FAILED, retry_count=1, max_retries=3)
        assert job.is_retryable is True

    def test_is_retryable_failed_at_limit(self, mock_logger: None) -> None:
        """Test is_retryable returns False when at max retries."""
        job = BatchJob(status=JobStatus.FAILED, retry_count=3, max_retries=3)
        assert job.is_retryable is False

    def test_is_retryable_not_failed(self, mock_logger: None) -> None:
        """Test is_retryable returns False for non-failed job."""
        job = BatchJob(status=JobStatus.COMPLETED)
        assert job.is_retryable is False

    def test_estimated_remaining_time_not_started(self, mock_logger: None) -> None:
        """Test estimated_remaining_time returns None when not started."""
        job = BatchJob()
        assert job.estimated_remaining_time is None

    def test_estimated_remaining_time_zero_progress(self, mock_logger: None) -> None:
        """Test estimated_remaining_time returns None with zero progress."""
        job = BatchJob()
        job.started_at = datetime.now()
        job.progress = 0.0
        assert job.estimated_remaining_time is None

    def test_estimated_remaining_time_with_progress(self, mock_logger: None) -> None:
        """Test estimated_remaining_time calculates correctly."""
        job = BatchJob()
        job.started_at = datetime.now() - timedelta(seconds=10)
        job.progress = 0.5  # 50% done after 10 seconds
        estimated = job.estimated_remaining_time
        assert estimated is not None
        # Should be approximately 10 seconds remaining
        assert 9 < estimated < 11

    def test_mark_started(self, mock_logger: None) -> None:
        """Test mark_started sets correct status."""
        job = BatchJob()
        job.mark_started()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert job.progress == 0.0

    def test_mark_completed_success(self, mock_logger: None) -> None:
        """Test mark_completed with success."""
        job = BatchJob()
        result = BatchJobResult(success=True, frames_processed=100)
        job.mark_completed(result)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.progress == 1.0
        assert job.result == result

    def test_mark_completed_failure(self, mock_logger: None) -> None:
        """Test mark_completed with failure."""
        job = BatchJob()
        result = BatchJobResult(success=False, error_message="Test error")
        job.mark_completed(result)
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert job.result == result

    def test_mark_failed(self, mock_logger: None) -> None:
        """Test mark_failed sets correct status and result."""
        job = BatchJob()
        error = ValueError("Test error")
        job.mark_failed(error)
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert job.result is not None
        assert job.result.success is False
        assert job.result.error_message == "Test error"
        assert job.result.error_type == "ValueError"

    def test_mark_cancelled(self, mock_logger: None) -> None:
        """Test mark_cancelled sets correct status."""
        job = BatchJob()
        job.mark_cancelled()
        assert job.status == JobStatus.CANCELLED
        assert job.completed_at is not None

    def test_mark_skipped(self, mock_logger: None) -> None:
        """Test mark_skipped sets correct status and result."""
        job = BatchJob()
        job.mark_skipped("File already exists")
        assert job.status == JobStatus.SKIPPED
        assert job.completed_at is not None
        assert job.result is not None
        assert job.result.success is False
        assert job.result.error_message == "File already exists"
        assert job.result.metadata.get("skip_reason") == "File already exists"

    def test_increment_retry_success(self, mock_logger: None) -> None:
        """Test increment_retry when retries remaining."""
        job = BatchJob(status=JobStatus.FAILED, retry_count=0, max_retries=3)
        result = job.increment_retry()
        assert result is True
        assert job.retry_count == 1
        assert job.status == JobStatus.RETRYING
        assert job.completed_at is None
        assert job.started_at is None
        assert job.progress == 0.0

    def test_increment_retry_at_limit(self, mock_logger: None) -> None:
        """Test increment_retry returns False at max retries."""
        job = BatchJob(status=JobStatus.FAILED, retry_count=3, max_retries=3)
        result = job.increment_retry()
        assert result is False
        assert job.retry_count == 3  # Unchanged

    def test_update_progress(self, mock_logger: None) -> None:
        """Test update_progress sets progress correctly."""
        job = BatchJob()
        job.update_progress(0.5, "Processing frames")
        assert job.progress == 0.5
        assert job.current_stage == "Processing frames"

    def test_update_progress_clamped_low(self, mock_logger: None) -> None:
        """Test update_progress clamps to 0."""
        job = BatchJob()
        job.update_progress(-0.5)
        assert job.progress == 0.0

    def test_update_progress_clamped_high(self, mock_logger: None) -> None:
        """Test update_progress clamps to 1."""
        job = BatchJob()
        job.update_progress(1.5)
        assert job.progress == 1.0

    def test_to_dict(self, mock_logger: None) -> None:
        """Test to_dict serialization."""
        now = datetime.now()
        job = BatchJob(
            job_id="test-job-id",
            input_path=Path("/input/video.mp4"),
            output_path=Path("/output/video_3d.mp4"),
            status=JobStatus.RUNNING,
            priority=JobPriority.HIGH,
            created_at=now,
            progress=0.5,
            current_stage="Processing",
            retry_count=1,
            max_retries=3,
            source="manual",
        )
        data = job.to_dict()
        assert data["job_id"] == "test-job-id"
        assert data["input_path"] == "/input/video.mp4"
        assert data["output_path"] == "/output/video_3d.mp4"
        assert data["status"] == "running"
        assert data["priority"] == 10
        assert data["progress"] == 0.5
        assert data["current_stage"] == "Processing"
        assert data["source"] == "manual"

    def test_from_dict(self, mock_logger: None) -> None:
        """Test from_dict deserialization."""
        now = datetime.now()
        data = {
            "job_id": "test-job-id",
            "input_path": "/input/video.mp4",
            "output_path": "/output/video_3d.mp4",
            "status": "running",
            "priority": 10,
            "created_at": now.isoformat(),
            "started_at": now.isoformat(),
            "completed_at": None,
            "progress": 0.5,
            "current_stage": "Processing",
            "retry_count": 1,
            "max_retries": 3,
            "result": None,
            "config": {"key": "value"},
            "metadata": {},
            "source": "manual",
        }
        job = BatchJob.from_dict(data)
        assert job.job_id == "test-job-id"
        assert job.input_path == Path("/input/video.mp4")
        assert job.output_path == Path("/output/video_3d.mp4")
        assert job.status == JobStatus.RUNNING
        assert job.priority == JobPriority.HIGH
        assert job.progress == 0.5
        assert job.config == {"key": "value"}

    def test_from_dict_with_result(self, mock_logger: None) -> None:
        """Test from_dict with result deserialization."""
        data = {
            "job_id": "test-job-id",
            "input_path": "/input/video.mp4",
            "status": "completed",
            "priority": 5,
            "created_at": datetime.now().isoformat(),
            "progress": 1.0,
            "result": {
                "success": True,
                "output_path": "/output/video_3d.mp4",
                "frames_processed": 100,
            },
        }
        job = BatchJob.from_dict(data)
        assert job.result is not None
        assert job.result.success is True
        assert job.result.frames_processed == 100

    def test_roundtrip_serialization(self, mock_logger: None) -> None:
        """Test to_dict and from_dict roundtrip."""
        original = BatchJob(
            job_id="test-job-id",
            input_path=Path("/input/video.mp4"),
            output_path=Path("/output/video_3d.mp4"),
            status=JobStatus.RUNNING,
            priority=JobPriority.HIGH,
            progress=0.5,
            config={"key": "value"},
        )
        data = original.to_dict()
        restored = BatchJob.from_dict(data)
        assert restored.job_id == original.job_id
        assert restored.input_path == original.input_path
        assert restored.output_path == original.output_path
        assert restored.status == original.status
        assert restored.priority == original.priority
        assert restored.progress == original.progress
        assert restored.config == original.config


class TestBatchQueueStats:
    """Tests for BatchQueueStats dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        stats = BatchQueueStats()
        assert stats.total_jobs == 0
        assert stats.pending_jobs == 0
        assert stats.running_jobs == 0
        assert stats.completed_jobs == 0
        assert stats.failed_jobs == 0
        assert stats.cancelled_jobs == 0
        assert stats.skipped_jobs == 0
        assert stats.total_frames_processed == 0
        assert stats.total_processing_time == 0.0
        assert stats.average_processing_time == 0.0

    def test_success_rate_no_jobs(self) -> None:
        """Test success_rate returns 0 with no finished jobs."""
        stats = BatchQueueStats()
        assert stats.success_rate == 0.0

    def test_success_rate_all_completed(self) -> None:
        """Test success_rate returns 100 when all completed."""
        stats = BatchQueueStats(completed_jobs=10, failed_jobs=0)
        assert stats.success_rate == 100.0

    def test_success_rate_half_failed(self) -> None:
        """Test success_rate returns 50 when half failed."""
        stats = BatchQueueStats(completed_jobs=5, failed_jobs=5)
        assert stats.success_rate == 50.0

    def test_success_rate_custom(self) -> None:
        """Test success_rate calculation with custom values."""
        stats = BatchQueueStats(completed_jobs=7, failed_jobs=3)
        assert stats.success_rate == 70.0

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        stats = BatchQueueStats(
            total_jobs=100,
            pending_jobs=20,
            running_jobs=5,
            completed_jobs=70,
            failed_jobs=3,
            cancelled_jobs=2,
            skipped_jobs=5,
            total_frames_processed=7000,
            total_processing_time=350.0,
            average_processing_time=5.0,
        )
        data = stats.to_dict()
        assert data["total_jobs"] == 100
        assert data["pending_jobs"] == 20
        assert data["running_jobs"] == 5
        assert data["completed_jobs"] == 70
        assert data["failed_jobs"] == 3
        assert data["total_frames_processed"] == 7000
        assert data["success_rate"] == pytest.approx(95.89, rel=0.01)


class TestBatchJobScheduler:
    """Tests for BatchJob scheduler properties and methods."""

    def test_scheduled_at_none(self, mock_logger: None) -> None:
        """Test scheduled_at defaults to None (immediate execution)."""
        job = BatchJob()
        assert job.scheduled_at is None

    def test_scheduled_at_custom(self, mock_logger: None) -> None:
        """Test scheduled_at can be set to a specific time."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job = BatchJob(scheduled_at=scheduled_time)
        assert job.scheduled_at == scheduled_time

    def test_is_scheduled_time_reached_none(self, mock_logger: None) -> None:
        """Test is_scheduled_time_reached returns True when no schedule."""
        job = BatchJob()
        assert job.is_scheduled_time_reached is True

    def test_is_scheduled_time_reached_future(self, mock_logger: None) -> None:
        """Test is_scheduled_time_reached returns False for future time."""
        job = BatchJob(scheduled_at=datetime.now() + timedelta(hours=1))
        assert job.is_scheduled_time_reached is False

    def test_is_scheduled_time_reached_past(self, mock_logger: None) -> None:
        """Test is_scheduled_time_reached returns True for past time."""
        job = BatchJob(scheduled_at=datetime.now() - timedelta(hours=1))
        assert job.is_scheduled_time_reached is True

    def test_has_dependencies_empty(self, mock_logger: None) -> None:
        """Test has_dependencies returns False when no dependencies."""
        job = BatchJob()
        assert job.has_dependencies is False

    def test_has_dependencies_with_deps(self, mock_logger: None) -> None:
        """Test has_dependencies returns True when dependencies exist."""
        job = BatchJob(depends_on=["job_123"])
        assert job.has_dependencies is True

    def test_depends_on_default_empty(self, mock_logger: None) -> None:
        """Test depends_on defaults to empty list."""
        job = BatchJob()
        assert job.depends_on == []
        assert isinstance(job.depends_on, list)

    def test_dependent_jobs_default_empty(self, mock_logger: None) -> None:
        """Test dependent_jobs defaults to empty list."""
        job = BatchJob()
        assert job.dependent_jobs == []
        assert isinstance(job.dependent_jobs, list)

    def test_check_dependencies_met_no_deps(self, mock_logger: None) -> None:
        """Test check_dependencies_met returns True when no dependencies."""
        job = BatchJob()
        assert job.check_dependencies_met(set()) is True
        assert job.check_dependencies_met({"job_123"}) is True

    def test_check_dependencies_met_partial(self, mock_logger: None) -> None:
        """Test check_dependencies_met returns False with partial completion."""
        job = BatchJob(depends_on=["job_1", "job_2"])
        assert job.check_dependencies_met({"job_1"}) is False
        assert job.check_dependencies_met(set()) is False

    def test_check_dependencies_met_all(self, mock_logger: None) -> None:
        """Test check_dependencies_met returns True when all completed."""
        job = BatchJob(depends_on=["job_1", "job_2"])
        assert job.check_dependencies_met({"job_1", "job_2"}) is True
        assert job.check_dependencies_met({"job_1", "job_2", "job_3"}) is True

    def test_get_pending_dependencies_no_deps(self, mock_logger: None) -> None:
        """Test get_pending_dependencies returns empty list when no deps."""
        job = BatchJob()
        assert job.get_pending_dependencies(set()) == []
        assert job.get_pending_dependencies({"job_1"}) == []

    def test_get_pending_dependencies_partial(self, mock_logger: None) -> None:
        """Test get_pending_dependencies returns uncompleted dependencies."""
        job = BatchJob(depends_on=["job_1", "job_2", "job_3"])
        assert set(job.get_pending_dependencies({"job_1"})) == {"job_2", "job_3"}
        assert set(job.get_pending_dependencies(set())) == {"job_1", "job_2", "job_3"}

    def test_get_pending_dependencies_all(self, mock_logger: None) -> None:
        """Test get_pending_dependencies returns empty list when all completed."""
        job = BatchJob(depends_on=["job_1", "job_2"])
        assert job.get_pending_dependencies({"job_1", "job_2"}) == []

    def test_to_dict_with_scheduler_fields(self, mock_logger: None) -> None:
        """Test to_dict includes scheduler fields."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job = BatchJob(
            job_id="test-job-id",
            input_path=Path("/input/video.mp4"),
            scheduled_at=scheduled_time,
            depends_on=["job_1", "job_2"],
        )
        data = job.to_dict()
        assert "scheduled_at" in data
        assert data["scheduled_at"] == scheduled_time.isoformat()
        assert data["depends_on"] == ["job_1", "job_2"]
        assert "dependent_jobs" in data
        assert data["dependent_jobs"] == []

    def test_to_dict_with_dependent_jobs(self, mock_logger: None) -> None:
        """Test to_dict includes dependent_jobs field."""
        job = BatchJob(
            dependent_jobs=["waiting_job_1", "waiting_job_2"],
        )
        data = job.to_dict()
        assert data["dependent_jobs"] == ["waiting_job_1", "waiting_job_2"]

    def test_from_dict_with_scheduler_fields(self, mock_logger: None) -> None:
        """Test from_dict parses scheduler fields correctly."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        data = {
            "job_id": "test-job-id",
            "input_path": "/input/video.mp4",
            "status": "pending",
            "priority": 5,
            "created_at": datetime.now().isoformat(),
            "scheduled_at": scheduled_time.isoformat(),
            "depends_on": ["job_1", "job_2"],
            "dependent_jobs": ["waiting_job"],
        }
        job = BatchJob.from_dict(data)
        assert job.scheduled_at is not None
        # Compare ISO strings since microseconds might differ
        assert job.scheduled_at.isoformat() == scheduled_time.isoformat()
        assert job.depends_on == ["job_1", "job_2"]
        assert job.dependent_jobs == ["waiting_job"]

    def test_from_dict_scheduler_fields_optional(self, mock_logger: None) -> None:
        """Test from_dict handles missing scheduler fields."""
        data = {
            "job_id": "test-job-id",
            "input_path": "/input/video.mp4",
            "status": "pending",
            "priority": 5,
            "created_at": datetime.now().isoformat(),
        }
        job = BatchJob.from_dict(data)
        assert job.scheduled_at is None
        assert job.depends_on == []
        assert job.dependent_jobs == []

    def test_roundtrip_scheduler_fields(self, mock_logger: None) -> None:
        """Test roundtrip serialization preserves scheduler fields."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        original = BatchJob(
            job_id="test-job-id",
            input_path=Path("/input/video.mp4"),
            scheduled_at=scheduled_time,
            depends_on=["job_1"],
            dependent_jobs=["waiting_job"],
        )
        data = original.to_dict()
        restored = BatchJob.from_dict(data)
        assert restored.scheduled_at is not None
        assert restored.scheduled_at.isoformat() == scheduled_time.isoformat()
        assert restored.depends_on == ["job_1"]
        assert restored.dependent_jobs == ["waiting_job"]


# Mark as slow test
import pytest

pytestmark = pytest.mark.slow
