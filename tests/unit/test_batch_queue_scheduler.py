"""Unit tests for batch video queue scheduler functionality.

Tests cover:
- Job scheduling with scheduled_at times
- Job dependencies (depends_on, dependent_jobs)
- Circular dependency detection
- Dependency failed/cancelled handling
- _get_next_job scheduling logic
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.config import BatchQueueConfig
from video2d3d.batch.exceptions import (
    DependencyFailedError,
    JobNotFoundError,
)
from video2d3d.batch.models import JobPriority, JobStatus
from video2d3d.batch.queue import BatchVideoQueue


@pytest.fixture
def temp_queue(tmp_path: Path) -> Generator[BatchVideoQueue, None, None]:
    """Create a temporary queue for testing."""
    config = BatchQueueConfig(
        output_directory=tmp_path / "output",
        state_file=tmp_path / "state.json",
        auto_start=False,
    )
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output").mkdir(parents=True, exist_ok=True)

    with patch("video2d3d.batch.queue.get_logger"):
        queue = BatchVideoQueue(config)
        yield queue


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Create a sample video file for testing."""
    video_path = tmp_path / "input" / "test.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"fake video content")
    return video_path


class TestAddJobWithScheduler:
    """Tests for add_job with scheduler parameters."""

    def test_add_job_with_scheduled_at(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test adding a job with scheduled_at time."""
        scheduled_time = datetime.now() + timedelta(hours=1)

        job = temp_queue.add_job(
            input_path=sample_video,
            scheduled_at=scheduled_time,
        )

        assert job.scheduled_at == scheduled_time
        assert job.status == JobStatus.PENDING

    def test_add_job_with_immediate_schedule(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test adding a job with no scheduled_at (immediate)."""
        job = temp_queue.add_job(
            input_path=sample_video,
            scheduled_at=None,
        )

        assert job.scheduled_at is None
        assert job.is_scheduled_time_reached is True

    def test_add_job_with_single_dependency(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test adding a job with a single dependency."""
        # First, add the dependency job
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Now add a job that depends on it
        dependent_job = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        assert dependent_job.depends_on == [dep_job.job_id]
        assert dep_job.job_id in dependent_job.depends_on

    def test_add_job_with_multiple_dependencies(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test adding a job with multiple dependencies."""
        # Add dependency jobs
        dep1 = temp_queue.add_job(input_path=sample_video)
        dep2 = temp_queue.add_job(input_path=sample_video)
        dep3 = temp_queue.add_job(input_path=sample_video)

        # Add dependent job
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep1.job_id, dep2.job_id, dep3.job_id],
        )

        assert len(dependent.depends_on) == 3
        assert dep1.job_id in dependent.depends_on
        assert dep2.job_id in dependent.depends_on
        assert dep3.job_id in dependent.depends_on

    def test_add_job_dependency_not_found(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test adding a job with non-existent dependency raises error."""
        with pytest.raises(JobNotFoundError):
            temp_queue.add_job(
                input_path=sample_video,
                depends_on=["nonexistent-job-id"],
            )

    def test_add_job_with_priority(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test adding a job with priority."""
        job = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
        )

        assert job.priority == JobPriority.URGENT


class TestDependencyReverseTracking:
    """Tests for reverse dependency tracking (dependent_jobs)."""

    def test_dependent_jobs_updated(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test that dependent_jobs is updated when dependency is added."""
        # Add dependency job
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Add dependent job
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Check that dep_job has dependent_jobs updated
        dep_job_refreshed = temp_queue.get_job(dep_job.job_id)
        assert dep_job_refreshed is not None
        assert dependent.job_id in dep_job_refreshed.dependent_jobs

    def test_multiple_dependent_jobs(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test that multiple dependent jobs are tracked."""
        # Add dependency job
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Add multiple dependent jobs
        dep1 = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )
        dep2 = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Check that dep_job has both in dependent_jobs
        dep_job_refreshed = temp_queue.get_job(dep_job.job_id)
        assert dep_job_refreshed is not None
        assert dep1.job_id in dep_job_refreshed.dependent_jobs
        assert dep2.job_id in dep_job_refreshed.dependent_jobs


class TestCircularDependencyDetection:
    """Tests for circular dependency detection."""

    def test_direct_circular_dependency(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test detection of direct circular dependency (A -> B -> A)."""
        # Add job A
        job_a = temp_queue.add_job(input_path=sample_video)

        # Add job B that depends on A
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )

        # A circular dependency would occur if A tried to depend on B,
        # since B already depends on A. Test the internal cycle detection.
        # Note: add_job doesn't allow reusing existing job_ids, so we test
        # _would_create_cycle directly.
        assert temp_queue._would_create_cycle(job_a.job_id, job_b.job_id)

    def test_indirect_circular_dependency(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test detection of indirect circular dependency (A -> B -> C -> A)."""
        # Create chain: A -> B -> C
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_b.job_id],
        )

        # Try to add job D that creates cycle: D -> A -> B -> C -> D
        # First update A to depend on D (which would make A depend on C indirectly)
        # This is tested via would_create_cycle
        assert temp_queue._would_create_cycle(job_c.job_id, job_a.job_id)


class TestDependencyFailedValidation:
    """Tests for dependency failed/cancelled validation."""

    def test_dependency_failed_raises_error(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that depending on a failed job raises DependencyFailedError."""
        # Add job and mark it as failed
        job = temp_queue.add_job(input_path=sample_video)
        job.mark_failed(ValueError("Test failure"))

        # Try to add a job that depends on the failed job
        with pytest.raises(DependencyFailedError) as exc_info:
            temp_queue.add_job(
                input_path=sample_video,
                depends_on=[job.job_id],
            )

        assert exc_info.value.dependency_status == "failed"

    def test_dependency_cancelled_raises_error(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that depending on a cancelled job raises DependencyFailedError."""
        # Add job and mark it as cancelled
        job = temp_queue.add_job(input_path=sample_video)
        job.mark_cancelled()

        # Try to add a job that depends on the cancelled job
        with pytest.raises(DependencyFailedError) as exc_info:
            temp_queue.add_job(
                input_path=sample_video,
                depends_on=[job.job_id],
            )

        assert exc_info.value.dependency_status == "cancelled"


class TestGetNextJobScheduler:
    """Tests for _get_next_job with scheduler logic."""

    def test_get_next_job_respects_scheduled_time(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that _get_next_job skips jobs with future scheduled_at."""
        # Add job scheduled for future
        future_time = datetime.now() + timedelta(hours=1)
        future_job = temp_queue.add_job(
            input_path=sample_video,
            scheduled_at=future_time,
        )

        # Add immediate job
        immediate_job = temp_queue.add_job(input_path=sample_video)

        # Get next job should return immediate job
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == immediate_job.job_id

    def test_get_next_job_scheduled_time_reached(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that _get_next_job returns job when scheduled time is reached."""
        # Add job scheduled for past
        past_time = datetime.now() - timedelta(hours=1)
        scheduled_job = temp_queue.add_job(
            input_path=sample_video,
            scheduled_at=past_time,
        )

        # Get next job should return this job
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == scheduled_job.job_id

    def test_get_next_job_waits_for_dependencies(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that _get_next_job skips jobs with unmet dependencies."""
        # Add dependency job (not completed)
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Add dependent job
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Get next job should return dependency job, not dependent
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == dep_job.job_id

    def test_get_next_job_dependency_met(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that _get_next_job returns job when dependencies are met."""
        # Add dependency job and mark as completed
        dep_job = temp_queue.add_job(input_path=sample_video)
        temp_queue._completed_jobs.add(dep_job.job_id)

        # Add dependent job
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Get next job should return dependent job since dependency is met
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == dependent.job_id

    def test_get_next_job_respects_priority_with_scheduler(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that _get_next_job respects priority even with scheduler fields."""
        # Add normal priority job
        normal_job = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.NORMAL,
        )

        # Add urgent priority job
        urgent_job = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
        )

        # Get next job should return urgent job first
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == urgent_job.job_id


class TestNotifyDependentJobs:
    """Tests for _notify_dependent_jobs functionality."""

    def test_notify_dependent_jobs_on_completion(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that dependent jobs are notified when dependency completes."""
        # Add dependency job
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Add dependent job
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Initially dependent job should not be ready
        assert not dependent.check_dependencies_met(temp_queue._completed_jobs)

        # Mark dependency as completed and track it
        temp_queue._completed_jobs.add(dep_job.job_id)

        # Now dependent should have dependencies met
        assert dependent.check_dependencies_met(temp_queue._completed_jobs)


class TestSchedulerIntegration:
    """Integration tests for scheduler functionality."""

    def test_job_chain_scheduling(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test a chain of jobs with dependencies executes in order."""
        # Create chain: job_a -> job_b -> job_c
        job_a = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.NORMAL,
        )
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_b.job_id],
        )

        # First job should be job_a (no dependencies)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == job_a.job_id

        # Complete job_a
        temp_queue._completed_jobs.add(job_a.job_id)

        # Next should be job_b (depends on job_a, now met)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == job_b.job_id

        # Complete job_b
        temp_queue._completed_jobs.add(job_b.job_id)

        # Next should be job_c (depends on job_b, now met)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == job_c.job_id

    def test_scheduled_and_dependency_combined(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test job with both scheduled time and dependency."""
        # Add dependency job
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Add job with both scheduled time and dependency
        scheduled_time = datetime.now() - timedelta(hours=1)  # Past time
        combined = temp_queue.add_job(
            input_path=sample_video,
            scheduled_at=scheduled_time,
            depends_on=[dep_job.job_id],
        )

        # Initially should not be ready (dependency not met)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == dep_job.job_id

        # Complete dependency
        temp_queue._completed_jobs.add(dep_job.job_id)

        # Now combined job should be ready (scheduled time reached + dependency met)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.job_id == combined.job_id
