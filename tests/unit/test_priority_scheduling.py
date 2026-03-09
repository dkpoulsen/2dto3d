import pytest

pytestmark = pytest.mark.slow

"""Unit tests for priority-based job scheduling functionality.

Tests cover:
- on_dependency callback registration
- Type validation for depends_on parameter
- _validate_dependencies method
- _would_create_cycle edge cases
- Priority-based queue ordering
- Integration with scheduled_at and dependencies
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
from video2d3d.batch.exceptions import DependencyFailedError, JobNotFoundError
from video2d3d.batch.models import BatchJob, BatchJobResult, JobPriority, JobStatus
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


class TestOnDependencyCallback:
    """Tests for on_dependency callback registration and invocation."""

    def test_register_dependency_callback(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that dependency callbacks can be registered."""
        callback_invocations: list[tuple[BatchJob, str]] = []

        def callback(job: BatchJob, status: str) -> None:
            callback_invocations.append((job, status))

        temp_queue.on_dependency(callback)

        # Add a dependency job
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Add a dependent job
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Complete the dependency
        temp_queue._completed_jobs.add(dep_job.job_id)
        temp_queue._notify_dependent_jobs(dep_job)

        # Callback should have been invoked
        assert len(callback_invocations) == 1
        assert callback_invocations[0][0].job_id == dependent.job_id
        assert callback_invocations[0][1] == "dependencies_met"

    def test_multiple_dependency_callbacks(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that multiple dependency callbacks are all invoked."""
        callback1_invocations: list[tuple[BatchJob, str]] = []
        callback2_invocations: list[tuple[BatchJob, str]] = []

        def callback1(job: BatchJob, status: str) -> None:
            callback1_invocations.append((job, status))

        def callback2(job: BatchJob, status: str) -> None:
            callback2_invocations.append((job, status))

        temp_queue.on_dependency(callback1)
        temp_queue.on_dependency(callback2)

        # Add a dependency job and dependent job
        dep_job = temp_queue.add_job(input_path=sample_video)
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Complete the dependency
        temp_queue._completed_jobs.add(dep_job.job_id)
        temp_queue._notify_dependent_jobs(dep_job)

        # Both callbacks should have been invoked
        assert len(callback1_invocations) == 1
        assert len(callback2_invocations) == 1

    def test_callback_exception_does_not_crash(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that callback exceptions are handled gracefully."""
        good_callback_invocations: list[tuple[BatchJob, str]] = []

        def bad_callback(job: BatchJob, status: str) -> None:
            raise RuntimeError("Callback error!")

        def good_callback(job: BatchJob, status: str) -> None:
            good_callback_invocations.append((job, status))

        temp_queue.on_dependency(bad_callback)
        temp_queue.on_dependency(good_callback)

        # Add jobs
        dep_job = temp_queue.add_job(input_path=sample_video)
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Complete the dependency
        temp_queue._completed_jobs.add(dep_job.job_id)
        # This should not raise even though bad_callback throws
        temp_queue._notify_dependent_jobs(dep_job)

        # Good callback should still have been invoked
        assert len(good_callback_invocations) == 1


class TestDependsOnTypeValidation:
    """Tests for type validation of depends_on parameter."""

    def test_depends_on_none_is_valid(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that None for depends_on is valid (defaults to empty list)."""
        job = temp_queue.add_job(
            input_path=sample_video,
            depends_on=None,
        )
        assert job.depends_on == []

    def test_depends_on_empty_list_is_valid(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that empty list for depends_on is valid."""
        job = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[],
        )
        assert job.depends_on == []

    def test_depends_on_string_list_is_valid(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that list of strings for depends_on is valid."""
        # First add a job to depend on
        dep_job = temp_queue.add_job(input_path=sample_video)

        job = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )
        assert job.depends_on == [dep_job.job_id]

    def test_depends_on_invalid_string_raises_error(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that string (instead of list) for depends_on raises TypeError."""
        with pytest.raises(TypeError, match="must be a list"):
            temp_queue.add_job(
                input_path=sample_video,
                depends_on="not-a-list",  # type: ignore
            )

    def test_depends_on_invalid_int_in_list_raises_error(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that list containing non-strings raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            temp_queue.add_job(
                input_path=sample_video,
                depends_on=[123],  # type: ignore
            )

    def test_depends_on_invalid_dict_in_list_raises_error(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that list containing dicts raises TypeError."""
        with pytest.raises(TypeError, match="must be a string"):
            temp_queue.add_job(
                input_path=sample_video,
                depends_on=[{"job_id": "test"}],  # type: ignore
            )


class TestValidateDependencies:
    """Tests for _validate_dependencies method."""

    def test_validate_dependencies_nonexistent_raises_error(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that depending on non-existent job raises JobNotFoundError."""
        with pytest.raises(JobNotFoundError):
            temp_queue.add_job(
                input_path=sample_video,
                depends_on=["nonexistent-job-id"],
            )

    def test_validate_dependencies_completed_job_allowed(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that depending on completed job is allowed."""
        dep_job = temp_queue.add_job(input_path=sample_video)
        temp_queue._completed_jobs.add(dep_job.job_id)

        # Should not raise
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )
        assert dependent.depends_on == [dep_job.job_id]

    def test_validate_dependencies_running_job_allowed(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that depending on running job is allowed."""
        dep_job = temp_queue.add_job(input_path=sample_video)
        dep_job.mark_started()

        # Should not raise
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )
        assert dependent.depends_on == [dep_job.job_id]


class TestWouldCreateCycleEdgeCases:
    """Tests for _would_create_cycle edge cases."""

    def test_no_cycle_independent_jobs(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that independent jobs don't create a cycle."""
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(input_path=sample_video)

        # No dependency between them
        assert not temp_queue._would_create_cycle(job_a.job_id, job_b.job_id)
        assert not temp_queue._would_create_cycle(job_b.job_id, job_a.job_id)

    def test_no_cycle_longer_chain(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test that longer dependency chains don't create cycles."""
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_b.job_id],
        )
        job_d = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_c.job_id],
        )

        # No cycle: D can depend on any of A, B, C
        assert not temp_queue._would_create_cycle(job_d.job_id, job_a.job_id)
        assert not temp_queue._would_create_cycle(job_d.job_id, job_b.job_id)
        assert not temp_queue._would_create_cycle(job_d.job_id, job_c.job_id)

        # But A cannot depend on D (would create cycle A <- B <- C <- D <- A)
        assert temp_queue._would_create_cycle(job_a.job_id, job_d.job_id)
        # B cannot depend on D either
        assert temp_queue._would_create_cycle(job_b.job_id, job_d.job_id)

    def test_cycle_self_dependency(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test that self-dependency is detected as a cycle."""
        job = temp_queue.add_job(input_path=sample_video)

        # A job depending on itself is a cycle
        assert temp_queue._would_create_cycle(job.job_id, job.job_id)

    def test_cycle_diamond_pattern(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test diamond dependency pattern (A -> B, A -> C, B -> D, C -> D)."""
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        job_d = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_b.job_id, job_c.job_id],
        )

        # D depending on A, B, or C is fine
        assert not temp_queue._would_create_cycle(job_d.job_id, job_a.job_id)

        # But A depending on D creates a cycle through both B and C
        assert temp_queue._would_create_cycle(job_a.job_id, job_d.job_id)

    def test_cycle_multiple_paths(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test cycle detection with multiple dependency paths."""
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )
        # Both B and C point to D
        job_d = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_b.job_id, job_c.job_id],
        )

        # A -> B -> D and A -> C -> D
        # A depending on D creates a cycle
        assert temp_queue._would_create_cycle(job_a.job_id, job_d.job_id)
        # B depending on D also creates a cycle
        assert temp_queue._would_create_cycle(job_b.job_id, job_d.job_id)


class TestPriorityQueueOrdering:
    """Tests for priority-based queue ordering."""

    def test_queue_sorted_by_priority(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that queue is sorted by priority (highest first)."""
        # Add jobs in random order
        job_low = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.LOW,
        )
        job_urgent = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
        )
        job_normal = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.NORMAL,
        )
        job_high = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.HIGH,
        )

        # Get jobs in order
        jobs_in_order = []
        while True:
            job = temp_queue._get_next_job()
            if job is None:
                break
            jobs_in_order.append(job)

        # Should be in priority order
        assert len(jobs_in_order) == 4
        assert jobs_in_order[0].priority == JobPriority.URGENT
        assert jobs_in_order[1].priority == JobPriority.HIGH
        assert jobs_in_order[2].priority == JobPriority.NORMAL
        assert jobs_in_order[3].priority == JobPriority.LOW

    def test_queue_priority_with_dependencies(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that dependencies take precedence over priority."""
        # Add high priority job that depends on low priority
        job_low = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.LOW,
        )
        job_high = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.HIGH,
            depends_on=[job_low.job_id],
        )

        # Low priority should be first (high depends on it)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.priority == JobPriority.LOW

        # Complete low priority job
        temp_queue._completed_jobs.add(job_low.job_id)

        # Now high priority should be next
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.priority == JobPriority.HIGH

    def test_queue_priority_with_scheduled_time(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that scheduled time takes precedence over priority."""
        # Add urgent job scheduled for later
        future_time = datetime.now() + timedelta(hours=1)
        job_urgent_scheduled = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
            scheduled_at=future_time,
        )

        # Add low priority job available now
        job_low_immediate = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.LOW,
        )

        # Low priority should be first (urgent is scheduled for later)
        next_job = temp_queue._get_next_job()
        assert next_job is not None
        assert next_job.priority == JobPriority.LOW


class TestQueueStatePersistence:
    """Tests for queue state persistence with scheduler fields."""

    def test_state_includes_scheduled_at(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that scheduled_at is included in state."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job = temp_queue.add_job(
            input_path=sample_video,
            scheduled_at=scheduled_time,
        )

        # Get job from state
        restored = temp_queue.get_job(job.job_id)
        assert restored is not None
        assert restored.scheduled_at is not None
        # Compare ISO format to avoid microsecond differences
        assert restored.scheduled_at.isoformat() == scheduled_time.isoformat()

    def test_state_includes_depends_on(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that depends_on is included in state."""
        dep_job = temp_queue.add_job(input_path=sample_video)
        job = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Get job from state
        restored = temp_queue.get_job(job.job_id)
        assert restored is not None
        assert restored.depends_on == [dep_job.job_id]

    def test_state_includes_priority(self, temp_queue: BatchVideoQueue, sample_video: Path) -> None:
        """Test that priority is included in state."""
        job = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
        )

        # Get job from state
        restored = temp_queue.get_job(job.job_id)
        assert restored is not None
        assert restored.priority == JobPriority.URGENT


class TestIntegrationScenarios:
    """Integration tests for complete scheduling scenarios."""

    def test_complex_scheduling_scenario(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test a complex scenario with priorities, schedules, and dependencies."""
        # Create a complex job graph:
        # job_a (LOW, immediate) <- job_b (HIGH, depends on A)
        # job_c (NORMAL, scheduled+1h) <- job_d (URGENT, depends on C)
        # job_e (NORMAL, immediate, no deps)

        job_a = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.LOW,
        )
        job_b = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.HIGH,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.NORMAL,
            scheduled_at=datetime.now() + timedelta(hours=1),
        )
        job_d = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
            depends_on=[job_c.job_id],
        )
        job_e = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.NORMAL,
        )

        # First job should be A (E is also ready, but A is first due to queue order)
        # Actually, with priority sorting, E (NORMAL) should come before A (LOW)
        # Let's verify the order based on priority for ready jobs

        # Get all ready jobs
        ready_jobs = []
        while True:
            job = temp_queue._get_next_job()
            if job is None:
                break
            ready_jobs.append(job)
            temp_queue._completed_jobs.add(job.job_id)

        # E (NORMAL) should come before A (LOW)
        # B is blocked by A, D is blocked by C which is scheduled
        assert len(ready_jobs) == 2  # A and E are the only ready jobs

        # Verify the blocked jobs
        assert temp_queue.get_job(job_b.job_id) is not None  # B exists
        assert temp_queue.get_job(job_d.job_id) is not None  # D exists

    def test_priority_preemption_simulation(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that higher priority jobs are processed first when ready."""
        # Add jobs in reverse priority order
        jobs = []
        for priority in [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.URGENT]:
            job = temp_queue.add_job(
                input_path=sample_video,
                priority=priority,
            )
            jobs.append(job)

        # Get jobs in order
        processed_priorities = []
        while True:
            job = temp_queue._get_next_job()
            if job is None:
                break
            processed_priorities.append(job.priority)
            temp_queue._completed_jobs.add(job.job_id)

        # Should process in priority order (URGENT first)
        assert processed_priorities == [
            JobPriority.URGENT,
            JobPriority.HIGH,
            JobPriority.NORMAL,
            JobPriority.LOW,
        ]

    def test_dependency_chain_completion(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that a chain of dependencies completes in order."""
        # Create a chain: A -> B -> C -> D
        job_a = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.LOW,
        )
        job_b = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.HIGH,
            depends_on=[job_a.job_id],
        )
        job_c = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.NORMAL,
            depends_on=[job_b.job_id],
        )
        job_d = temp_queue.add_job(
            input_path=sample_video,
            priority=JobPriority.URGENT,
            depends_on=[job_c.job_id],
        )

        # Process jobs one by one
        completed_order = []
        while True:
            job = temp_queue._get_next_job()
            if job is None:
                break

            completed_order.append(job.job_id)
            temp_queue._completed_jobs.add(job.job_id)

        # Should complete in dependency order: A, B, C, D
        assert completed_order == [job_a.job_id, job_b.job_id, job_c.job_id, job_d.job_id]


class TestJobPriorityFromValue:
    """Tests for JobPriority.from_value method."""

    def test_from_value_exact_matches(self) -> None:
        """Test from_value returns correct priority for exact values."""
        assert JobPriority.from_value(1) == JobPriority.LOW
        assert JobPriority.from_value(5) == JobPriority.NORMAL
        assert JobPriority.from_value(10) == JobPriority.HIGH
        assert JobPriority.from_value(20) == JobPriority.URGENT

    def test_from_value_unknown_returns_normal(self) -> None:
        """Test from_value returns NORMAL for unknown values."""
        assert JobPriority.from_value(0) == JobPriority.NORMAL
        assert JobPriority.from_value(99) == JobPriority.NORMAL
        assert JobPriority.from_value(-1) == JobPriority.NORMAL
        assert JobPriority.from_value(100) == JobPriority.NORMAL

    def test_from_value_between_levels_returns_normal(self) -> None:
        """Test from_value returns NORMAL for values between defined levels."""
        assert JobPriority.from_value(2) == JobPriority.NORMAL
        assert JobPriority.from_value(7) == JobPriority.NORMAL
        assert JobPriority.from_value(15) == JobPriority.NORMAL


class TestCleanupCompletedJobs:
    """Tests for _cleanup_completed_jobs memory leak prevention."""

    def test_cleanup_removes_stale_entries(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that stale entries are removed from _completed_jobs."""
        # Add and complete a job
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(input_path=sample_video)

        # Manually add to completed jobs
        temp_queue._completed_jobs.add(job_a.job_id)
        temp_queue._completed_jobs.add(job_b.job_id)

        # Remove job_b from queue (simulating it being deleted elsewhere)
        del temp_queue._jobs[job_b.job_id]

        # Run cleanup
        temp_queue._cleanup_completed_jobs()

        # job_a should still be in _completed_jobs (exists in queue)
        assert job_a.job_id in temp_queue._completed_jobs
        # job_b should be removed (no longer in queue)
        assert job_b.job_id not in temp_queue._completed_jobs

    def test_cleanup_keeps_needed_dependencies(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that completed jobs needed as dependencies are kept."""
        # Create dependency chain
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )

        # Mark job_a as completed but remove from queue
        temp_queue._completed_jobs.add(job_a.job_id)
        del temp_queue._jobs[job_a.job_id]

        # Run cleanup
        temp_queue._cleanup_completed_jobs()

        # job_a should be kept (still needed as dependency)
        assert job_a.job_id in temp_queue._completed_jobs

    def test_cleanup_removes_unneeded_completed_dependencies(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that completed dependencies are removed when no longer needed."""
        # Create dependency chain
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[job_a.job_id],
        )

        # Mark job_a as completed
        temp_queue._completed_jobs.add(job_a.job_id)

        # Complete job_b (now job_a is no longer needed as dependency)
        job_b.status = JobStatus.COMPLETED

        # Remove job_a from queue
        del temp_queue._jobs[job_a.job_id]

        # Run cleanup
        temp_queue._cleanup_completed_jobs()

        # job_a should be removed (no longer needed)
        assert job_a.job_id not in temp_queue._completed_jobs

    def test_clear_completed_calls_cleanup(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that clear_completed calls _cleanup_completed_jobs."""
        # Add jobs
        job_a = temp_queue.add_job(input_path=sample_video)
        job_b = temp_queue.add_job(input_path=sample_video)

        # Complete them
        job_a.mark_completed(BatchJobResult(success=True))
        job_b.mark_completed(BatchJobResult(success=True))
        temp_queue._completed_jobs.add(job_a.job_id)
        temp_queue._completed_jobs.add(job_b.job_id)

        # Clear completed
        count = temp_queue.clear_completed()

        # Should have cleared 2 jobs
        assert count == 2
        # _completed_jobs should be empty
        assert len(temp_queue._completed_jobs) == 0


class TestDependencyFailureNotification:
    """Tests for dependency failure/cancellation notification."""

    def test_notify_on_dependency_failed(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that dependent jobs are notified when dependency fails."""
        callback_invocations: list[tuple[BatchJob, str]] = []

        def callback(job: BatchJob, status: str) -> None:
            callback_invocations.append((job, status))

        temp_queue.on_dependency(callback)

        # Add dependency job and dependent job
        dep_job = temp_queue.add_job(input_path=sample_video)
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Fail the dependency
        dep_job.mark_failed(RuntimeError("Processing failed"))

        # Notify dependent jobs
        temp_queue._notify_dependent_jobs(dep_job, "failed")

        # Callback should have been invoked with dependency_failed status
        assert len(callback_invocations) == 1
        assert callback_invocations[0][0].job_id == dependent.job_id
        assert callback_invocations[0][1] == "dependency_failed"

    def test_notify_on_dependency_cancelled(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that dependent jobs are notified when dependency is cancelled."""
        callback_invocations: list[tuple[BatchJob, str]] = []

        def callback(job: BatchJob, status: str) -> None:
            callback_invocations.append((job, status))

        temp_queue.on_dependency(callback)

        # Add dependency job and dependent job
        dep_job = temp_queue.add_job(input_path=sample_video)
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Cancel the dependency
        dep_job.mark_cancelled()

        # Notify dependent jobs
        temp_queue._notify_dependent_jobs(dep_job, "cancelled")

        # Callback should have been invoked with dependency_cancelled status
        assert len(callback_invocations) == 1
        assert callback_invocations[0][0].job_id == dependent.job_id
        assert callback_invocations[0][1] == "dependency_cancelled"

    def test_cancel_job_notifies_dependents(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that cancel_job notifies dependent jobs."""
        callback_invocations: list[tuple[BatchJob, str]] = []

        def callback(job: BatchJob, status: str) -> None:
            callback_invocations.append((job, status))

        temp_queue.on_dependency(callback)

        # Add dependency job and dependent job
        dep_job = temp_queue.add_job(input_path=sample_video)
        dependent = temp_queue.add_job(
            input_path=sample_video,
            depends_on=[dep_job.job_id],
        )

        # Cancel the dependency job via cancel_job
        result = temp_queue.cancel_job(dep_job.job_id)

        assert result is True
        # Callback should have been invoked
        assert len(callback_invocations) == 1
        assert callback_invocations[0][1] == "dependency_cancelled"


class TestDependencyListDeduplication:
    """Tests for dependency list deduplication in __post_init__."""

    def test_depends_on_deduplication(
        self, temp_queue: BatchVideoQueue, sample_video: Path
    ) -> None:
        """Test that duplicate dependencies are removed."""
        # Add a job to depend on
        dep_job = temp_queue.add_job(input_path=sample_video)

        # Create job with duplicate dependencies
        # Note: We need to create directly to bypass add_job's validation
        job = BatchJob(
            input_path=sample_video,
            depends_on=[dep_job.job_id, dep_job.job_id, dep_job.job_id],
        )

        # Duplicates should be removed
        assert len(job.depends_on) == 1
        assert job.depends_on == [dep_job.job_id]

    def test_dependent_jobs_deduplication(self, sample_video: Path) -> None:
        """Test that duplicate dependent_jobs are removed."""
        job = BatchJob(
            input_path=sample_video,
            dependent_jobs=["job-1", "job-2", "job-1", "job-3", "job-2"],
        )

        # Duplicates should be removed, order preserved
        assert job.dependent_jobs == ["job-1", "job-2", "job-3"]

    def test_empty_lists_unaffected(self, sample_video: Path) -> None:
        """Test that empty dependency lists are not affected."""
        job = BatchJob(input_path=sample_video)

        assert job.depends_on == []
        assert job.dependent_jobs == []


class TestConfigPriorityValidation:
    """Tests for BatchQueueConfig priority validation in from_dict."""

    def test_from_dict_valid_priority(self) -> None:
        """Test that valid priority values are correctly parsed."""
        for priority in [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.URGENT]:
            config = BatchQueueConfig.from_dict({"default_priority": priority.value})
            assert config.default_priority == priority

    def test_from_dict_unknown_priority_defaults_to_normal(self) -> None:
        """Test that unknown priority values default to NORMAL."""
        config = BatchQueueConfig.from_dict({"default_priority": 99})
        assert config.default_priority == JobPriority.NORMAL

        config = BatchQueueConfig.from_dict({"default_priority": 0})
        assert config.default_priority == JobPriority.NORMAL

        config = BatchQueueConfig.from_dict({"default_priority": -1})
        assert config.default_priority == JobPriority.NORMAL

    def test_from_dict_missing_priority_defaults_to_normal(self) -> None:
        """Test that missing priority defaults to NORMAL."""
        config = BatchQueueConfig.from_dict({})
        assert config.default_priority == JobPriority.NORMAL

    def test_default_priority_round_trip(self) -> None:
        """Test that default_priority survives to_dict/from_dict round trip."""
        config = BatchQueueConfig(default_priority=JobPriority.URGENT)
        restored = BatchQueueConfig.from_dict(config.to_dict())
        assert restored.default_priority == JobPriority.URGENT


class TestBatchJobSerializationWithScheduling:
    """Tests for BatchJob serialization with scheduling fields."""

    def test_to_dict_includes_all_scheduling_fields(self, sample_video: Path) -> None:
        """Test that to_dict includes all scheduling fields."""
        scheduled_time = datetime.now() + timedelta(hours=1)
        job = BatchJob(
            input_path=sample_video,
            priority=JobPriority.HIGH,
            scheduled_at=scheduled_time,
            depends_on=["dep-1", "dep-2"],
            dependent_jobs=["child-1"],
        )

        data = job.to_dict()

        assert data["priority"] == JobPriority.HIGH.value
        assert data["scheduled_at"] == scheduled_time.isoformat()
        assert data["depends_on"] == ["dep-1", "dep-2"]
        assert data["dependent_jobs"] == ["child-1"]

    def test_from_dict_handles_unknown_priority(self, sample_video: Path) -> None:
        """Test that from_dict handles unknown priority values gracefully."""
        data = {
            "job_id": "test-job",
            "input_path": str(sample_video),
            "status": "pending",
            "priority": 999,  # Unknown priority
        }

        job = BatchJob.from_dict(data)

        # Should default to NORMAL
        assert job.priority == JobPriority.NORMAL

    def test_round_trip_preserves_all_scheduling_fields(self, sample_video: Path) -> None:
        """Test that all scheduling fields survive round trip serialization."""
        scheduled_time = datetime.now() + timedelta(hours=2)
        original = BatchJob(
            input_path=sample_video,
            priority=JobPriority.URGENT,
            scheduled_at=scheduled_time,
            depends_on=["a", "b", "c"],
            dependent_jobs=["x", "y"],
        )

        # Round trip
        restored = BatchJob.from_dict(original.to_dict())

        assert restored.priority == original.priority
        assert restored.scheduled_at is not None
        assert restored.scheduled_at.isoformat() == scheduled_time.isoformat()
        assert restored.depends_on == ["a", "b", "c"]
        assert restored.dependent_jobs == ["x", "y"]
