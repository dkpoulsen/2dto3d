"""Batch video processing queue module.

This module provides batch processing capabilities for video conversion:
- VideoJobQueue: Priority queue for managing multiple video jobs
- VideoBatchProcessor: Processor for running multiple jobs sequentially or in parallel
- FolderMonitor: Automatic monitoring of directories for new video files
- FileDiscovery: Pattern-based file discovery with wildcard support
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

__all__ = [
    # Config
    "BatchQueueConfig",
    "FileDiscoveryConfig",
    "FolderWatcherConfig",
    # Models
    "BatchJob",
    "BatchJobResult",
    "BatchQueueStats",
    "JobPriority",
    "JobStatus",
    # Exceptions
    "BatchQueueError",
    "FileDiscoveryError",
    "FolderWatcherError",
    "JobAlreadyExistsError",
    "JobNotFoundError",
    "JobValidationError",
    "QueueFullError",
    "QueueNotRunningError",
    "StatePersistenceError",
    # File Discovery
    "FileDiscovery",
    "discover_videos",
    # Folder Watcher
    "FolderWatcher",
    "WATCHDOG_AVAILABLE",
]
