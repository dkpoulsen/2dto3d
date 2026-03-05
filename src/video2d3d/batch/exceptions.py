"""Exceptions for batch video processing queue."""


class BatchQueueError(Exception):
    """Base exception for batch queue errors."""

    pass


class JobNotFoundError(BatchQueueError):
    """Raised when a job is not found in the queue."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class JobAlreadyExistsError(BatchQueueError):
    """Raised when trying to add a duplicate job."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job already exists: {job_id}")


class QueueFullError(BatchQueueError):
    """Raised when the queue is at capacity."""

    def __init__(self, max_size: int) -> None:
        self.max_size = max_size
        super().__init__(f"Queue is full (max size: {max_size})")


class QueueNotRunningError(BatchQueueError):
    """Raised when trying to process jobs on a stopped queue."""

    def __init__(self) -> None:
        super().__init__("Queue is not running")


class JobValidationError(BatchQueueError):
    """Raised when job validation fails."""

    def __init__(self, message: str, input_path: str | None = None) -> None:
        self.input_path = input_path
        super().__init__(message)


class FileDiscoveryError(BatchQueueError):
    """Raised when file discovery fails."""

    def __init__(self, message: str, path: str | None = None) -> None:
        self.path = path
        super().__init__(message)


class FolderWatcherError(BatchQueueError):
    """Raised when folder watching fails."""

    def __init__(self, message: str, watch_path: str | None = None) -> None:
        self.watch_path = watch_path
        super().__init__(message)


class StatePersistenceError(BatchQueueError):
    """Raised when state save/load fails."""

    def __init__(self, message: str, state_file: str | None = None) -> None:
        self.state_file = state_file
        super().__init__(message)


__all__ = [
    "BatchQueueError",
    "JobNotFoundError",
    "JobAlreadyExistsError",
    "QueueFullError",
    "QueueNotRunningError",
    "JobValidationError",
    "FileDiscoveryError",
    "FolderWatcherError",
    "StatePersistenceError",
]
