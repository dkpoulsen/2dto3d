"""Folder monitoring for automatic batch job creation.

Uses watchdog library for efficient file system monitoring.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from video2d3d.batch.config import FolderWatcherConfig
from video2d3d.utils.logger import get_logger

if TYPE_CHECKING:
    from video2d3d.batch.file_discovery import FileDiscovery

try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
    from watchdog.observers.api import BaseObserver

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    BaseObserver = None

    class FileSystemEvent:
        pass

    class FileSystemEventHandler:
        pass


class StableFileTracker:
    """Track files to ensure they're stable (not being written) before processing."""

    def __init__(self, stable_time_seconds: float = 5.0) -> None:
        self.stable_time_seconds = stable_time_seconds
        self._file_times: dict[Path, float] = {}
        self._file_sizes: dict[Path, int] = {}
        self._lock = threading.Lock()

    def record_file_event(self, file_path: Path, size: int | None = None) -> bool:
        """Record a file event and check if file is stable.

        Returns:
            True if file is now stable, False if still being written.
        """
        with self._lock:
            now = time.time()
            current_size = size or self._get_file_size(file_path)

            if current_size is None:
                return False

            previous_size = self._file_sizes.get(file_path)
            previous_time = self._file_times.get(file_path)

            self._file_times[file_path] = now
            self._file_sizes[file_path] = current_size

            if previous_size is None or previous_time is None:
                return False

            if current_size != previous_size:
                return False

            elapsed = now - previous_time
            return elapsed >= self.stable_time_seconds

    def is_file_stable(self, file_path: Path) -> bool:
        """Check if a file is stable."""
        with self._lock:
            previous_time = self._file_times.get(file_path)
            if previous_time is None:
                return False

            elapsed = time.time() - previous_time
            return elapsed >= self.stable_time_seconds

    def mark_processed(self, file_path: Path) -> None:
        """Remove file from tracking after it's been processed."""
        with self._lock:
            self._file_times.pop(file_path, None)
            self._file_sizes.pop(file_path, None)

    def _get_file_size(self, file_path: Path) -> int | None:
        """Get file size safely."""
        try:
            return file_path.stat().st_size
        except OSError:
            return None

    def cleanup_old_entries(self, max_age_seconds: float = 3600.0) -> None:
        """Remove old entries that haven't been updated."""
        with self._lock:
            now = time.time()
            to_remove = [path for path, t in self._file_times.items() if now - t > max_age_seconds]
            for path in to_remove:
                self._file_times.pop(path, None)
                self._file_sizes.pop(path, None)


class FolderWatcherEventHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Event handler for file system events."""

    def __init__(
        self,
        callback: Callable[[Path], None],
        config: FolderWatcherConfig,
        file_discovery: FileDiscovery | None = None,
    ) -> None:
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.callback = callback
        self.config = config
        self.file_discovery = file_discovery
        self._logger = get_logger("folder_watcher")
        self._stable_tracker = StableFileTracker(config.stable_time_seconds)
        self._pending_files: dict[Path, float] = {}
        self._lock = threading.Lock()
        self._check_thread: threading.Thread | None = None
        self._running = False
        self._processed_files: set[Path] = set()

    def start(self) -> None:
        """Start the background checker thread."""
        self._running = True
        self._check_thread = threading.Thread(target=self._check_stable_files, daemon=True)
        self._check_thread.start()

    def stop(self) -> None:
        """Stop the background checker thread."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=2.0)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        self._handle_file_event(file_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        self._handle_file_event(file_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move event."""
        if event.is_directory:
            return

        file_path = Path(event.dest_path)
        self._handle_file_event(file_path)

    def _handle_file_event(self, file_path: Path) -> None:
        """Handle a file event."""
        if not self._should_process(file_path):
            return

        if file_path in self._processed_files:
            return

        with self._lock:
            self._pending_files[file_path] = time.time()

    def _should_process(self, file_path: Path) -> bool:
        """Check if file should be processed."""
        if not file_path.is_file():
            return False

        if self.file_discovery:
            try:
                config = self.file_discovery.config
                from video2d3d.batch.file_discovery import FileDiscovery

                discovery = FileDiscovery(config)
                if not any(
                    discovery._matches_patterns(file_path, config.patterns, config.exclude_patterns)
                ):
                    return False
            except Exception:
                pass

        return True

    def _check_stable_files(self) -> None:
        """Background thread to check for stable files."""
        while self._running:
            try:
                self._process_stable_files()
                self._stable_tracker.cleanup_old_entries()
            except Exception as e:
                self._logger.error(f"Error checking stable files: {e}")

            time.sleep(0.5)

    def _process_stable_files(self) -> None:
        """Process files that are now stable."""
        with self._lock:
            pending = list(self._pending_files.items())

        now = time.time()
        for file_path, event_time in pending:
            if now - event_time < self.config.stable_time_seconds:
                continue

            if file_path in self._processed_files:
                with self._lock:
                    self._pending_files.pop(file_path, None)
                continue

            try:
                if self._stable_tracker.record_file_event(file_path):
                    self._processed_files.add(file_path)
                    with self._lock:
                        self._pending_files.pop(file_path, None)
                    self._logger.info(f"File stable, processing: {file_path}")
                    self.callback(file_path)
            except Exception as e:
                self._logger.error(f"Error processing file {file_path}: {e}")


class FolderWatcher:
    """Watch folders for new video files and trigger processing."""

    def __init__(
        self,
        config: FolderWatcherConfig,
        callback: Callable[[Path], None],
        file_discovery: FileDiscovery | None = None,
    ) -> None:
        self.config = config
        self.callback = callback
        self.file_discovery = file_discovery
        self._logger = get_logger("folder_watcher")
        self._observer: BaseObserver | None = None
        self._event_handlers: list[FolderWatcherEventHandler] = []
        self._running = False
        self._poll_thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running

    def start(self) -> None:
        """Start watching configured folders."""
        if self._running:
            return

        if not self.config.watch_paths:
            self._logger.warning("No watch paths configured")
            return

        if WATCHDOG_AVAILABLE and self.config.use_inotify:
            self._start_watchdog()
        else:
            self._start_polling()

        self._running = True
        self._logger.info(f"Folder watcher started, watching {len(self.config.watch_paths)} paths")

    def _start_watchdog(self) -> None:
        """Start watchdog-based monitoring."""
        if Observer is None:
            self._logger.warning("Watchdog not available, falling back to polling")
            self._start_polling()
            return

        self._observer = Observer()

        for watch_path in self.config.watch_paths:
            if not watch_path.exists():
                self._logger.warning(f"Watch path does not exist: {watch_path}")
                continue

            handler = FolderWatcherEventHandler(
                callback=self.callback,
                config=self.config,
                file_discovery=self.file_discovery,
            )
            handler.start()
            self._event_handlers.append(handler)

            self._observer.schedule(
                handler,
                str(watch_path),
                recursive=self.config.recursive,
            )
            self._logger.info(f"Watching: {watch_path}")

        if self._observer:
            self._observer.start()

            if self.config.process_existing:
                self._process_existing_files()

    def _start_polling(self) -> None:
        """Start polling-based monitoring."""
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        if self.config.process_existing:
            self._process_existing_files()

    def _poll_loop(self) -> None:
        """Polling loop for file checking."""
        seen_files: set[Path] = set()

        while self._running:
            try:
                current_files = self._scan_files()
                new_files = current_files - seen_files

                for file_path in new_files:
                    try:
                        self.callback(file_path)
                    except Exception as e:
                        self._logger.error(f"Error processing {file_path}: {e}")

                seen_files = current_files

            except Exception as e:
                self._logger.error(f"Error in polling loop: {e}")

            time.sleep(self.config.poll_interval_seconds)

    def _scan_files(self) -> set[Path]:
        """Scan watched directories for files."""
        files: set[Path] = set()

        if not self.file_discovery:
            return files

        for watch_path in self.config.watch_paths:
            if not watch_path.exists():
                continue

            try:
                for file_path in self.file_discovery.discover(watch_path):
                    files.add(file_path)
            except Exception as e:
                self._logger.error(f"Error scanning {watch_path}: {e}")

        return files

    def _process_existing_files(self) -> None:
        """Process files that already exist when watcher starts."""
        if not self.file_discovery:
            return

        self._logger.info("Processing existing files in watch directories")

        for watch_path in self.config.watch_paths:
            if not watch_path.exists():
                continue

            try:
                for file_path in self.file_discovery.discover(watch_path):
                    try:
                        self.callback(file_path)
                    except Exception as e:
                        self._logger.error(f"Error processing existing file {file_path}: {e}")
            except Exception as e:
                self._logger.error(f"Error scanning {watch_path}: {e}")

    def stop(self) -> None:
        """Stop watching folders."""
        self._running = False

        for handler in self._event_handlers:
            handler.stop()

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

        if self._poll_thread:
            self._poll_thread.join(timeout=5.0)
            self._poll_thread = None

        self._event_handlers.clear()
        self._logger.info("Folder watcher stopped")

    def add_watch_path(self, path: Path) -> None:
        """Add a path to watch."""
        if path not in self.config.watch_paths:
            self.config.watch_paths.append(path)

            if self._running and self._observer:
                handler = FolderWatcherEventHandler(
                    callback=self.callback,
                    config=self.config,
                    file_discovery=self.file_discovery,
                )
                handler.start()
                self._event_handlers.append(handler)

                self._observer.schedule(
                    handler,
                    str(path),
                    recursive=self.config.recursive,
                )

    def __enter__(self) -> FolderWatcher:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit."""
        self.stop()


__all__ = [
    "FolderWatcher",
    "FolderWatcherEventHandler",
    "StableFileTracker",
    "WATCHDOG_AVAILABLE",
]
