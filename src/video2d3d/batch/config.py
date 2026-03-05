"""Configuration for batch video processing queue.

This module provides configuration classes for the batch queue system:
- BatchQueueConfig: Main configuration for the queue
- FileDiscoveryConfig: Configuration for file discovery patterns
- FolderWatcherConfig: Configuration for folder monitoring
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from video2d3d.batch.models import JobPriority


@dataclass
class FileDiscoveryConfig:
    """Configuration for file discovery and pattern matching.

    Attributes:
        patterns: Glob patterns for matching video files.
        exclude_patterns: Patterns to exclude from matching.
        recursive: Search directories recursively.
        case_sensitive: Whether pattern matching is case-sensitive.
        max_depth: Maximum directory depth for recursive search.
        follow_symlinks: Whether to follow symbolic links.
        min_file_size_mb: Minimum file size in MB.
        max_file_size_mb: Maximum file size in MB.
    """

    patterns: list[str] = field(
        default_factory=lambda: ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm"]
    )
    exclude_patterns: list[str] = field(default_factory=list)
    recursive: bool = True
    case_sensitive: bool = False
    max_depth: int = 10
    follow_symlinks: bool = False
    min_file_size_mb: float = 0.0
    max_file_size_mb: float = 0.0  # 0 = no limit

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary."""
        return {
            "patterns": self.patterns,
            "exclude_patterns": self.exclude_patterns,
            "recursive": self.recursive,
            "case_sensitive": self.case_sensitive,
            "max_depth": self.max_depth,
            "follow_symlinks": self.follow_symlinks,
            "min_file_size_mb": self.min_file_size_mb,
            "max_file_size_mb": self.max_file_size_mb,
        }


@dataclass
class FolderWatcherConfig:
    """Configuration for folder monitoring.

    Attributes:
        enabled: Whether folder watching is enabled.
        watch_paths: List of paths to watch for new files.
        poll_interval_seconds: Polling interval for file system checks.
        use_inotify: Use inotify for efficient file watching (Linux only).
        stable_time_seconds: Time to wait for file to be stable before processing.
        process_existing: Process existing files when watcher starts.
        recursive: Watch directories recursively.
    """

    enabled: bool = False
    watch_paths: list[Path] = field(default_factory=list)
    poll_interval_seconds: float = 2.0
    use_inotify: bool = True
    stable_time_seconds: float = 5.0
    process_existing: bool = True
    recursive: bool = True

    def __post_init__(self) -> None:
        """Normalize paths."""
        self.watch_paths = [Path(p) if isinstance(p, str) else p for p in self.watch_paths]

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "watch_paths": [str(p) for p in self.watch_paths],
            "poll_interval_seconds": self.poll_interval_seconds,
            "use_inotify": self.use_inotify,
            "stable_time_seconds": self.stable_time_seconds,
            "process_existing": self.process_existing,
            "recursive": self.recursive,
        }


@dataclass
class BatchQueueConfig:
    """Main configuration for the batch video processing queue.

    Attributes:
        max_concurrent_jobs: Maximum number of jobs to process simultaneously.
        default_priority: Default priority for new jobs.
        auto_start: Automatically start processing when jobs are added.
        retry_failed: Automatically retry failed jobs.
        max_retries: Maximum number of retries per job.
        retry_delay_seconds: Delay between retries.
        job_timeout_seconds: Timeout for individual jobs.
        output_directory: Directory for output files.
        output_naming_pattern: Pattern for naming output files.
        preserve_directory_structure: Keep input directory structure in output.
        skip_existing: Skip files that already have output.
        save_state: Save queue state to disk for recovery.
        state_file: Path to state file.
        state_save_interval: How often to save state (seconds).
        file_discovery: File discovery configuration.
        folder_watcher: Folder watcher configuration.
        progress_update_interval: How often to update progress (seconds).
        error_callback_url: URL to POST errors to (optional).
        completion_callback_url: URL to POST completion to (optional).
    """

    max_concurrent_jobs: int = 1
    default_priority: JobPriority = JobPriority.NORMAL
    auto_start: bool = True
    retry_failed: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 5.0
    job_timeout_seconds: float = 3600.0  # 1 hour
    output_directory: Optional[Path] = None
    output_naming_pattern: str = "{name}_3d{ext}"
    preserve_directory_structure: bool = False
    skip_existing: bool = True
    save_state: bool = True
    state_file: Optional[Path] = None
    state_save_interval: float = 30.0
    file_discovery: FileDiscoveryConfig = field(default_factory=FileDiscoveryConfig)
    folder_watcher: FolderWatcherConfig = field(default_factory=FolderWatcherConfig)
    progress_update_interval: float = 1.0
    error_callback_url: Optional[str] = None
    completion_callback_url: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize paths and validate configuration."""
        if self.output_directory and isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)
        if self.state_file and isinstance(self.state_file, str):
            self.state_file = Path(self.state_file)

        # Validate concurrent jobs
        if self.max_concurrent_jobs < 1:
            raise ValueError("max_concurrent_jobs must be at least 1")
        if self.max_concurrent_jobs > 16:
            import warnings

            warnings.warn(
                f"max_concurrent_jobs ({self.max_concurrent_jobs}) is high. "
                "Consider using a lower value to avoid resource issues."
            )

    def get_output_path(self, input_path: Path, base_output_dir: Optional[Path] = None) -> Path:
        """Generate output path for an input file.

        Args:
            input_path: Path to the input file.
            base_output_dir: Override output directory.

        Returns:
            Path where the output should be written.
        """
        output_dir = base_output_dir or self.output_directory or input_path.parent

        # Generate output filename
        name = input_path.stem
        ext = input_path.suffix
        output_name = self.output_naming_pattern.format(name=name, ext=ext)

        # Preserve directory structure if configured
        if self.preserve_directory_structure and self.output_directory:
            # Try to maintain relative path structure
            try:
                relative = input_path.relative_to(self.output_directory)
                output_dir = self.output_directory / relative.parent
            except ValueError:
                pass

        return output_dir / output_name

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary."""
        return {
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "default_priority": self.default_priority.value,
            "auto_start": self.auto_start,
            "retry_failed": self.retry_failed,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "job_timeout_seconds": self.job_timeout_seconds,
            "output_directory": str(self.output_directory) if self.output_directory else None,
            "output_naming_pattern": self.output_naming_pattern,
            "preserve_directory_structure": self.preserve_directory_structure,
            "skip_existing": self.skip_existing,
            "save_state": self.save_state,
            "state_file": str(self.state_file) if self.state_file else None,
            "state_save_interval": self.state_save_interval,
            "file_discovery": self.file_discovery.to_dict(),
            "folder_watcher": self.folder_watcher.to_dict(),
            "progress_update_interval": self.progress_update_interval,
            "error_callback_url": self.error_callback_url,
            "completion_callback_url": self.completion_callback_url,
        }


__all__ = [
    "BatchQueueConfig",
    "FileDiscoveryConfig",
    "FolderWatcherConfig",
]
