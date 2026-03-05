"""Batch video processing queue module.

This module provides comprehensive batch processing capabilities:
- Job queue management with priorities
- Folder monitoring for automatic job creation
- Wildcard pattern matching for file discovery
- Progress tracking and callbacks
- State persistence and recovery
"""

from video2d3d.batch.config import BatchQueueConfig, FileDiscoveryConfig, FolderWatcherConfig
from video2d3d.batch.exceptions import (
    BatchQueueError,
    FileDiscoveryError,
    FolderWatcherError,
    JobAlreadyExistsError,
    JobNotFoundError,
    JobValidationError,
    QueueFullError,
    QueueNotRunningError,
    StatePersistenceError,
)
from video2d3d.batch.file_discovery import FileDiscovery, discover_videos
from video2d3d.batch.folder_watcher import FolderWatcher, WATCHDOG_AVAILABLE
from video2d3d.batch.models import (
    BatchJob,
    BatchJobResult,
    BatchQueueStats,
    JobPriority,
    JobStatus,
)

from video2d3d.batch.queue import BatchVideoQueue

__all__ = [
    "BatchVideoQueue",
    "BatchQueueConfig",
    "FileDiscoveryConfig",
    "FolderWatcherConfig",
    "BatchJob",
    "BatchJobResult",
    "BatchQueueStats",
    "JobPriority",
    "JobStatus",
    "FileDiscovery",
    "discover_videos",
    "FolderWatcher",
    "WATCHDOG_AVAILABLE",
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
