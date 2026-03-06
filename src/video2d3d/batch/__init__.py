"""Batch video processing queue module.

This module provides comprehensive batch processing capabilities:
- Job queue management with priorities
- Folder monitoring for automatic job creation
- Wildcard pattern matching for file discovery
- Progress tracking and callbacks
- State persistence and recovery
- Adaptive batch sizing based on system resources
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

# Adaptive batch sizing
from video2d3d.batch.adaptive_sizer import (
    AdaptiveBatchConfig,
    AdaptiveBatchSizer,
    AdjustmentReason,
    BatchSizeCallback,
    BatchSizeHistory,
    create_adaptive_sizer,
    adaptive_batch_sizer_context,
)

__all__ = [
    # Core queue components
    "BatchVideoQueue",
    "BatchQueueConfig",
    "FileDiscoveryConfig",
    "FolderWatcherConfig",
    # Job models
    "BatchJob",
    "BatchJobResult",
    "BatchQueueStats",
    "JobPriority",
    "JobStatus",
    # File discovery
    "FileDiscovery",
    "discover_videos",
    # Folder watching
    "FolderWatcher",
    "WATCHDOG_AVAILABLE",
    # Exceptions
    "BatchQueueError",
    "JobNotFoundError",
    "JobAlreadyExistsError",
    "QueueFullError",
    "QueueNotRunningError",
    "JobValidationError",
    "FileDiscoveryError",
    "FolderWatcherError",
    "StatePersistenceError",
    # Adaptive batch sizing
    "AdaptiveBatchConfig",
    "AdaptiveBatchSizer",
    "AdjustmentReason",
    "BatchSizeCallback",
    "BatchSizeHistory",
    "create_adaptive_sizer",
    "adaptive_batch_sizer_context",
]
