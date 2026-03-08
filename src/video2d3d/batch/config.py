"""Configuration for batch video processing queue.

This module provides configuration classes for the batch queue system:
- BatchQueueConfig: Main configuration for the queue
- FileDiscoveryConfig: Configuration for file discovery patterns
- FolderWatcherConfig: Configuration for folder monitoring
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from video2d3d.batch.models import JobPriority
from video2d3d.checkpoint.models import CheckpointConfig


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

    def to_dict(self) -> dict[str, Any]:
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileDiscoveryConfig:
        """Create from dictionary."""
        return cls(
            patterns=data.get("patterns", ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm"]),
            exclude_patterns=data.get("exclude_patterns", []),
            recursive=data.get("recursive", True),
            case_sensitive=data.get("case_sensitive", False),
            max_depth=data.get("max_depth", 10),
            follow_symlinks=data.get("follow_symlinks", False),
            min_file_size_mb=data.get("min_file_size_mb", 0.0),
            max_file_size_mb=data.get("max_file_size_mb", 0.0),
        )


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

    def to_dict(self) -> dict[str, Any]:
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FolderWatcherConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            watch_paths=[Path(p) for p in data.get("watch_paths", [])],
            poll_interval_seconds=data.get("poll_interval_seconds", 2.0),
            use_inotify=data.get("use_inotify", True),
            stable_time_seconds=data.get("stable_time_seconds", 5.0),
            process_existing=data.get("process_existing", True),
            recursive=data.get("recursive", True),
        )


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
        checkpoint: Checkpoint configuration for frame-level resume.
    """

    max_concurrent_jobs: int = 1
    default_priority: JobPriority = JobPriority.NORMAL
    auto_start: bool = True
    retry_failed: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 5.0
    job_timeout_seconds: float = 3600.0  # 1 hour
    output_directory: Path | None = None
    output_naming_pattern: str = "{name}_3d{ext}"
    preserve_directory_structure: bool = False
    skip_existing: bool = True
    save_state: bool = True
    state_file: Path | None = None
    state_save_interval: float = 30.0
    file_discovery: FileDiscoveryConfig = field(default_factory=FileDiscoveryConfig)
    folder_watcher: FolderWatcherConfig = field(default_factory=FolderWatcherConfig)
    progress_update_interval: float = 1.0
    error_callback_url: str | None = None
    completion_callback_url: str | None = None
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)

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
                "Consider using a lower value to avoid resource issues.",
                stacklevel=2,
            )

    def get_output_path(self, input_path: Path, base_output_dir: Path | None = None) -> Path:
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

    def to_dict(self) -> dict[str, Any]:
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
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchQueueConfig:
        """Create from dictionary."""
        return cls(
            max_concurrent_jobs=data.get("max_concurrent_jobs", 1),
            default_priority=JobPriority(data.get("default_priority", JobPriority.NORMAL.value)),
            auto_start=data.get("auto_start", True),
            retry_failed=data.get("retry_failed", True),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 5.0),
            job_timeout_seconds=data.get("job_timeout_seconds", 3600.0),
            output_directory=(
                Path(data["output_directory"]) if data.get("output_directory") else None
            ),
            output_naming_pattern=data.get("output_naming_pattern", "{name}_3d{ext}"),
            preserve_directory_structure=data.get("preserve_directory_structure", False),
            skip_existing=data.get("skip_existing", True),
            save_state=data.get("save_state", True),
            state_file=Path(data["state_file"]) if data.get("state_file") else None,
            state_save_interval=data.get("state_save_interval", 30.0),
            file_discovery=FileDiscoveryConfig.from_dict(data.get("file_discovery", {})),
            folder_watcher=FolderWatcherConfig.from_dict(data.get("folder_watcher", {})),
            progress_update_interval=data.get("progress_update_interval", 1.0),
            error_callback_url=data.get("error_callback_url"),
            completion_callback_url=data.get("completion_callback_url"),
            checkpoint=(
                CheckpointConfig.from_dict(data["checkpoint"])
                if data.get("checkpoint")
                else CheckpointConfig()
            ),
        )


__all__ = [
    "BatchQueueConfig",
    "FileDiscoveryConfig",
    "FolderWatcherConfig",
    "CheckpointConfig",
]
