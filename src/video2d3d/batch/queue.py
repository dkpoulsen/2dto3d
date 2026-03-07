"""Batch video processing queue manager.

This module provides the main BatchVideoQueue class that orchestrates
batch video processing with job management, folder watching, and progress tracking.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from video2d3d.batch.config import BatchQueueConfig, FileDiscoveryConfig, FolderWatcherConfig
from video2d3d.batch.exceptions import (
    CircularDependencyError,
    DependencyFailedError,
    JobAlreadyExistsError,
    JobNotFoundError,
    QueueNotRunningError,
    StatePersistenceError,
)
from video2d3d.batch.file_discovery import FileDiscovery
from video2d3d.batch.folder_watcher import FolderWatcher
from video2d3d.batch.models import (
    BatchJob,
    BatchJobResult,
    BatchQueueStats,
    JobPriority,
    JobStatus,
)
from video2d3d.utils.logger import get_logger, log_exception

if TYPE_CHECKING:
    from video2d3d.utils.config import Config


class BatchVideoQueue:
    """Manages batch video processing queue with job lifecycle management.

    This class provides:
    - Job queue management (add, remove, prioritize)
    - Concurrent job processing with configurable parallelism
    - Folder monitoring for automatic job creation
    - Progress tracking and callbacks
    - State persistence for recovery
    - Comprehensive error handling and retries
    """

    def __init__(
        self,
        config: BatchQueueConfig | None = None,
        processor: Callable[[Path, Path], BatchJobResult] | None = None,
    ) -> None:
        self.config = config or BatchQueueConfig()
        self._processor = processor
        self._logger = get_logger("batch_queue")

        self._jobs: dict[str, BatchJob] = {}
        self._job_queue: list[str] = []
        self._running_jobs: set[str] = set()
        self._lock = threading.RLock()
        self._queue_lock = threading.Lock()

        self._executor: ThreadPoolExecutor | None = None
        self._running = False
        self._paused = False
        self._process_thread: threading.Thread | None = None
        self._save_thread: threading.Thread | None = None

        self._file_discovery = FileDiscovery(self.config.file_discovery)
        self._folder_watcher: FolderWatcher | None = None

        self._progress_callbacks: list[Callable[[BatchJob], None]] = []
        self._completion_callbacks: list[Callable[[BatchJob], None]] = []
        self._error_callbacks: list[Callable[[BatchJob, Exception], None]] = []
        self._dependency_callbacks: list[Callable[[BatchJob, str], None]] = []  # job, dependency_status

        self._completed_jobs: set[str] = set()  # Job IDs that completed successfully
        self._state_dirty = False
        self._shutdown_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def job_count(self) -> int:
        with self._lock:
            return len(self._jobs)

    @property
    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for j in self._jobs.values() if j.status.is_waiting)

    @property
    def running_count(self) -> int:
        with self._lock:
            return len(self._running_jobs)

    def _validate_dependencies(
        self,
        job_id: str,
        depends_on: list[str],
    ) -> None:
        """Validate job dependencies.

        Args:
            job_id: The job being added.
            depends_on: List of job IDs this job depends on.

        Raises:
            JobNotFoundError: If a dependency job doesn't exist.
            CircularDependencyError: If a circular dependency is detected.
            DependencyFailedError: If a dependency has failed or been cancelled.
        """
        for dep_id in depends_on:
            if dep_id not in self._jobs:
                raise JobNotFoundError(job_id=dep_id)

            dep_job = self._jobs[dep_id]

            # Check if dependency has already failed or been cancelled
            if dep_job.status == JobStatus.FAILED:
                raise DependencyFailedError(job_id, dep_id, "failed")
            if dep_job.status == JobStatus.CANCELLED:
                raise DependencyFailedError(job_id, dep_id, "cancelled")

            # Check for circular dependencies
            if self._would_create_cycle(job_id, dep_id):
                raise CircularDependencyError(job_id, dep_id)

    def _would_create_cycle(self, job_id: str, dependency_id: str) -> bool:
        """Check if adding this dependency would create a cycle.

        A cycle exists if the new job depends on a job that (directly or
        indirectly) depends on the new job.

        Args:
            job_id: The job being added.
            dependency_id: The job that job_id wants to depend on.

        Returns:
            True if adding this dependency would create a cycle.
        """
        # Check if dependency_id directly depends on job_id
        # (this can happen if we're re-adding a job)
        dep_job = self._jobs.get(dependency_id)
        if dep_job and job_id in dep_job.depends_on:
            return True

        # BFS to check if any of dependency_id's dependencies depend on job_id
        # Using deque for O(1) popleft operation
        visited: set[str] = set()
        to_check = deque(dep_job.depends_on) if dep_job else deque()

        while to_check:
            current_id = to_check.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)

            current_job = self._jobs.get(current_id)
            if current_id == job_id:
                return True

            if current_job:
                to_check.extend(current_job.depends_on)

        return False
    def add_job(
        self,
        input_path: Path,
        output_path: Path | None = None,
        priority: JobPriority | None = None,
        config: dict | None = None,
        source: str = "manual",
        scheduled_at: datetime | None = None,
        depends_on: list[str] | None = None,
    ) -> BatchJob:
        """Add a new job to the queue.

        Args:
            input_path: Path to the input video file.
            output_path: Path to the output file (optional, auto-generated if not provided).
            priority: Job priority level.
            config: Job-specific configuration.
            source: Source of the job (manual, api, folder_watcher, etc.).
            scheduled_at: When the job should start (None = immediate).
            depends_on: List of job IDs that must complete before this job can run.

        Returns:
            The created BatchJob instance.

        Raises:
            FileNotFoundError: If input file doesn't exist.
            JobNotFoundError: If a dependency job doesn't exist.
            CircularDependencyError: If a circular dependency is detected.
            DependencyFailedError: If a dependency has failed or been cancelled.
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Validate and normalize depends_on parameter
        depends_on = depends_on or []
        if not isinstance(depends_on, list):
            raise TypeError("depends_on must be a list of job IDs")
        for dep_id in depends_on:
            if not isinstance(dep_id, str):
                raise TypeError(f"Dependency ID must be a string, got {type(dep_id).__name__}")

        # Validate dependencies
        with self._lock:
            # Create a temporary job_id for validation
            temp_job_id = str(uuid.uuid4())
            self._validate_dependencies(temp_job_id, depends_on)

        if output_path is None:
            output_path = self.config.get_output_path(input_path)

        if self.config.skip_existing and output_path.exists():
            self._logger.info(f"Skipping {input_path}, output already exists")
            job = BatchJob(
                input_path=input_path,
                output_path=output_path,
                priority=priority or self.config.default_priority,
                config=config or {},
                source=source,
                scheduled_at=scheduled_at,
                depends_on=depends_on,
            )
            job.mark_skipped("Output file already exists")
            with self._lock:
                self._jobs[job.job_id] = job
            return job

        job = BatchJob(
            input_path=input_path,
            output_path=output_path,
            priority=priority or self.config.default_priority,
            max_retries=self.config.max_retries,
            config=config or {},
            source=source,
            scheduled_at=scheduled_at,
            depends_on=depends_on,
        )

        # Register reverse dependencies
        with self._lock:
            for dep_id in depends_on:
                if dep_id in self._jobs:
                    self._jobs[dep_id].dependent_jobs.append(job.job_id)

        with self._lock:
            self._jobs[job.job_id] = job
            self._enqueue_job(job.job_id)

        self._logger.info(f"Added job {job.job_id}: {input_path}")
        self._state_dirty = True

        if self.config.auto_start and not self._running:
            self.start()

        return job
    def add_jobs_from_pattern(
        self,
        pattern: str,
        base_dir: Path | None = None,
        priority: JobPriority | None = None,
    ) -> list[BatchJob]:
        """Add jobs for files matching a wildcard pattern."""
        jobs = []
        for file_path in self._file_discovery.discover_by_wildcard(pattern, base_dir):
            try:
                job = self.add_job(file_path, priority=priority, source="pattern")
                jobs.append(job)
            except Exception as e:
                self._logger.error(f"Failed to add job for {file_path}: {e}")
        return jobs

    def add_jobs_from_directory(
        self,
        directory: Path,
        recursive: bool = True,
        priority: JobPriority | None = None,
    ) -> list[BatchJob]:
        """Add jobs for all video files in a directory."""
        config = FileDiscoveryConfig(
            patterns=self.config.file_discovery.patterns,
            recursive=recursive,
        )
        discovery = FileDiscovery(config)
        jobs = []

        for file_path in discovery.discover(directory):
            try:
                job = self.add_job(file_path, priority=priority, source="directory")
                jobs.append(job)
            except Exception as e:
                self._logger.error(f"Failed to add job for {file_path}: {e}")

        return jobs

    def add_jobs_from_list(
        self,
        file_list: list[Path] | list[str],
        priority: JobPriority | None = None,
    ) -> list[BatchJob]:
        """Add jobs from a list of file paths."""
        jobs = []
        for file_path in file_list:
            try:
                job = self.add_job(
                    Path(file_path),
                    priority=priority,
                    source="list",
                )
                jobs.append(job)
            except Exception as e:
                self._logger.error(f"Failed to add job for {file_path}: {e}")
        return jobs

    def get_job(self, job_id: str) -> BatchJob | None:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def get_all_jobs(self, status: JobStatus | None = None) -> list[BatchJob]:
        """Get all jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self._jobs.values())
            if status:
                jobs = [j for j in jobs if j.status == status]
            return sorted(jobs, key=lambda j: (-j.priority.value, j.created_at))

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job.status.is_terminal:
                return False

            job.mark_cancelled()
            if job_id in self._job_queue:
                self._job_queue.remove(job_id)

            self._logger.info(f"Cancelled job {job_id}")
            self._state_dirty = True
            return True

    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if not job.is_retryable:
                return False

            job.increment_retry()
            self._enqueue_job(job_id)
            self._logger.info(f"Retrying job {job_id} (attempt {job.retry_count})")
            self._state_dirty = True
            return True

    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the queue."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job.status == JobStatus.RUNNING:
                return False

            del self._jobs[job_id]
            if job_id in self._job_queue:
                self._job_queue.remove(job_id)

            self._logger.info(f"Removed job {job_id}")
            self._state_dirty = True
            return True

    def clear_completed(self) -> int:
        """Remove all completed jobs."""
        count = 0
        with self._lock:
            to_remove = [job_id for job_id, job in self._jobs.items() if job.status.is_terminal]
            for job_id in to_remove:
                del self._jobs[job_id]
                count += 1

        if count > 0:
            self._logger.info(f"Cleared {count} completed jobs")
            self._state_dirty = True

        return count

    def get_stats(self) -> BatchQueueStats:
        """Get queue statistics."""
        with self._lock:
            jobs = list(self._jobs.values())
            total_frames = 0
            total_time = 0.0
            completed_count = 0

            for job in jobs:
                if job.result:
                    total_frames += job.result.frames_processed
                    total_time += job.result.processing_time_seconds
                if job.status == JobStatus.COMPLETED:
                    completed_count += 1

            return BatchQueueStats(
                total_jobs=len(jobs),
                pending_jobs=sum(1 for j in jobs if j.status.is_waiting),
                running_jobs=len(self._running_jobs),
                completed_jobs=completed_count,
                failed_jobs=sum(1 for j in jobs if j.status == JobStatus.FAILED),
                cancelled_jobs=sum(1 for j in jobs if j.status == JobStatus.CANCELLED),
                skipped_jobs=sum(1 for j in jobs if j.status == JobStatus.SKIPPED),
                total_frames_processed=total_frames,
                total_processing_time=total_time,
                average_processing_time=total_time / completed_count
                if completed_count > 0
                else 0.0,
            )

    def start(self) -> None:
        """Start processing the queue."""
        if self._running:
            return

        self._running = True
        self._paused = False
        self._shutdown_event.clear()

        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_jobs)

        self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._process_thread.start()

        if self.config.save_state:
            self._save_thread = threading.Thread(target=self._state_save_loop, daemon=True)
            self._save_thread.start()

        if self.config.folder_watcher.enabled:
            self._start_folder_watcher()

        self._logger.info(f"Queue started with {self.config.max_concurrent_jobs} workers")

    def stop(self, wait: bool = True) -> None:
        """Stop processing the queue."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        if self._folder_watcher:
            self._folder_watcher.stop()

        if wait:
            for job_id in list(self._running_jobs):
                self.cancel_job(job_id)

        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None

        if self._process_thread:
            self._process_thread.join(timeout=5.0)

        if self._save_thread:
            self._save_thread.join(timeout=5.0)

        if self.config.save_state:
            self._save_state()

        self._logger.info("Queue stopped")

    def pause(self) -> None:
        """Pause queue processing."""
        self._paused = True
        self._logger.info("Queue paused")

    def resume(self) -> None:
        """Resume queue processing."""
        self._paused = False
        self._logger.info("Queue resumed")

    def on_progress(self, callback: Callable[[BatchJob], None]) -> None:
        """Register a progress callback."""
        self._progress_callbacks.append(callback)

    def on_completion(self, callback: Callable[[BatchJob], None]) -> None:
        """Register a completion callback."""
        self._completion_callbacks.append(callback)

    def on_error(self, callback: Callable[[BatchJob, Exception], None]) -> None:
        """Register an error callback."""
        self._error_callbacks.append(callback)

    def on_dependency(self, callback: Callable[[BatchJob, str], None]) -> None:
        """Register a dependency status callback.

        The callback receives the job and a status string:
        - "dependencies_met": All dependencies completed, job is ready to run
        - "dependency_failed": A dependency has failed
        - "dependency_cancelled": A dependency was cancelled
        """
        self._dependency_callbacks.append(callback)
    def set_processor(self, processor: Callable[[Path, Path], BatchJobResult]) -> None:
        """Set the video processor function."""
        self._processor = processor

    def _enqueue_job(self, job_id: str) -> None:
        """Add job to processing queue (priority-sorted)."""
        with self._queue_lock:
            if job_id not in self._job_queue:
                self._job_queue.append(job_id)
                self._job_queue.sort(
                    key=lambda jid: -self._jobs[jid].priority.value,
                )

    def _get_next_job(self) -> BatchJob | None:
        """Get the next job to process.

        Jobs are selected based on:
        1. Priority (higher priority first)
        2. Scheduled time (must have passed)
        3. Dependencies (must all be completed)
        """
        with self._queue_lock:
            # Try to find a job that's ready to run
            skipped_jobs = []
            while self._job_queue:
                job_id = self._job_queue.pop(0)
                job = self._jobs.get(job_id)

                if not job or not job.status.is_waiting:
                    continue

                # Check scheduled time
                if not job.is_scheduled_time_reached:
                    # Job is scheduled for later, put it back at the end
                    skipped_jobs.append(job_id)
                    continue

                # Check dependencies
                if not job.check_dependencies_met(self._completed_jobs):
                    # Dependencies not met, skip for now
                    skipped_jobs.append(job_id)
                    pending_deps = job.get_pending_dependencies(self._completed_jobs)
                    self._logger.debug(
                        f"Job {job_id} waiting for dependencies: {pending_deps}"
                    )
                    continue

                # Job is ready to run
                # Put back any skipped jobs at the front of the queue
                if skipped_jobs:
                    self._job_queue = skipped_jobs + self._job_queue
                return job

            # No ready jobs, put skipped jobs back
            if skipped_jobs:
                self._job_queue = skipped_jobs

        return None

    def _process_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            if self._paused:
                time.sleep(0.5)
                continue

            if self.running_count >= self.config.max_concurrent_jobs:
                time.sleep(0.5)
                continue

            job = self._get_next_job()
            if not job:
                time.sleep(0.5)
                continue

            self._submit_job(job)

    def _submit_job(self, job: BatchJob) -> None:
        """Submit a job for processing."""
        if not self._executor:
            return

        with self._lock:
            self._running_jobs.add(job.job_id)

        job.mark_started()
        self._state_dirty = True

        future = self._executor.submit(self._process_job, job)
        future.add_done_callback(lambda f: self._job_completed(job.job_id, f))

        self._logger.info(f"Started job {job.job_id}: {job.input_path}")

    def _process_job(self, job: BatchJob) -> BatchJobResult:
        """Process a single job."""
        result = BatchJobResult()

        try:
            if not self._processor:
                raise RuntimeError("No processor configured")

            if not job.output_path:
                job.output_path = self.config.get_output_path(job.input_path)

            job.output_path.parent.mkdir(parents=True, exist_ok=True)

            start_time = time.time()
            result = self._processor(job.input_path, job.output_path)
            result.processing_time_seconds = time.time() - start_time

        except Exception as e:
            log_exception(f"Job {job.job_id} failed", exception=e)
            result.success = False
            result.error_message = str(e)
            result.error_type = type(e).__name__

        return result

    def _job_completed(self, job_id: str, future: Future[BatchJobResult]) -> None:
        """Handle job completion."""
        with self._lock:
            self._running_jobs.discard(job_id)
            job = self._jobs.get(job_id)

        if not job:
            return

        try:
            result = future.result()
            job.mark_completed(result)

            if result.success:
                self._logger.info(f"Job {job_id} completed successfully")
                for callback in self._completion_callbacks:
                    try:
                        callback(job)
                    except Exception as e:
                        self._logger.error(f"Completion callback error: {e}")
            else:
                self._logger.error(f"Job {job_id} failed: {result.error_message}")

                if self.config.retry_failed and job.is_retryable:
                    self.retry_job(job_id)

                for callback in self._error_callbacks:
                    try:
                        callback(job, Exception(result.error_message or "Unknown error"))
                    except Exception as e:
                        self._logger.error(f"Error callback error: {e}")

        except Exception as e:
            log_exception(f"Job {job_id} failed with exception", exception=e)
            job.mark_failed(e)

        self._state_dirty = True

        # Track completed jobs and handle dependent jobs
        if job.status == JobStatus.COMPLETED:
            self._completed_jobs.add(job_id)
            self._notify_dependent_jobs(job)

    def _notify_dependent_jobs(self, completed_job: BatchJob) -> None:
        """Notify jobs that depend on a completed job.

        Args:
            completed_job: The job that just completed successfully.
        """
        if not completed_job.dependent_jobs:
            return

        self._logger.debug(
            f"Notifying {len(completed_job.dependent_jobs)} dependent jobs of {completed_job.job_id}"
        )

        for dep_job_id in completed_job.dependent_jobs:
            dep_job = self._jobs.get(dep_job_id)
            if not dep_job:
                self._logger.warning(
                    f"Dependent job {dep_job_id} not found (may have been removed)"
                )
                continue

            # Check if all dependencies are now met
            if dep_job.check_dependencies_met(self._completed_jobs):
                self._logger.info(
                    f"Job {dep_job_id} dependencies met after {completed_job.job_id} completed, ready to run"
                )
                # Call any dependency callbacks
                for callback in self._dependency_callbacks:
                    try:
                        callback(dep_job, "dependencies_met")
                    except Exception as e:
                        self._logger.error(f"Dependency callback error: {e}")
            else:
                pending = dep_job.get_pending_dependencies(self._completed_jobs)
                self._logger.debug(
                    f"Job {dep_job_id} still waiting for dependencies: {pending}"
                )

    def _start_folder_watcher(self) -> None:
        """Start folder monitoring."""
        self._folder_watcher = FolderWatcher(
            config=self.config.folder_watcher,
            callback=self._on_new_file,
            file_discovery=self._file_discovery,
        )
        self._folder_watcher.start()

    def _on_new_file(self, file_path: Path) -> None:
        """Handle new file detected by folder watcher."""
        try:
            self.add_job(file_path, source="folder_watcher")
        except Exception as e:
            self._logger.error(f"Failed to add job for new file {file_path}: {e}")

    def _state_save_loop(self) -> None:
        """Periodically save queue state."""
        while self._running and self.config.save_state:
            if self._shutdown_event.wait(self.config.state_save_interval):
                break

            if self._state_dirty:
                self._save_state()

    def _save_state(self) -> None:
        """Save queue state to disk."""
        state_file = self.config.state_file
        if not state_file:
            state_file = Path("logs/batch_queue_state.json")

        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)

            with self._lock:
                state = {
                    "jobs": [job.to_dict() for job in self._jobs.values()],
                    "saved_at": datetime.now().isoformat(),
                    "config": self.config.to_dict(),
                }

            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)

            self._state_dirty = False
            self._logger.debug(f"State saved to {state_file}")

        except Exception as e:
            log_exception("Failed to save state", exception=e)
            raise StatePersistenceError(
                f"Failed to save state: {e}",
                state_file=str(state_file),
            ) from e

    def load_state(self, state_file: Path | None = None) -> int:
        """Load queue state from disk."""
        state_file = state_file or self.config.state_file
        if not state_file:
            state_file = Path("logs/batch_queue_state.json")

        if not state_file.exists():
            return 0

        try:
            with open(state_file) as f:
                state = json.load(f)

            loaded_count = 0
            for job_data in state.get("jobs", []):
                try:
                    job = BatchJob.from_dict(job_data)
                    if not job.status.is_terminal:
                        job.status = JobStatus.PENDING
                        with self._lock:
                            self._jobs[job.job_id] = job
                            self._enqueue_job(job.job_id)
                        loaded_count += 1
                except Exception as e:
                    self._logger.warning(f"Failed to load job: {e}")

            self._logger.info(f"Loaded {loaded_count} jobs from state")
            return loaded_count

        except Exception as e:
            log_exception("Failed to load state", exception=e)
            raise StatePersistenceError(
                f"Failed to load state: {e}",
                state_file=str(state_file),
            ) from e

    def __enter__(self) -> BatchVideoQueue:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.stop()


__all__ = ["BatchVideoQueue"]
