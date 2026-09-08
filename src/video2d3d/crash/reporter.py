"""Main crash reporter module with exception hooks and signal handlers.

This module provides the core crash reporting functionality:
- CrashReporter: Main class for crash detection and reporting
- Exception hooks for uncaught exceptions
- Signal handlers for graceful shutdown
- Crash report storage and retrieval
- Integration with FastAPI lifecycle

Example usage:
    ```python
    from video2d3d.crash import init_crash_reporting, CrashReporterConfig

    # Quick setup with defaults
    reporter = init_crash_reporting()

    # Or with custom configuration
    config = CrashReporterConfig(
        crash_dir=Path("./crashes"),
        capture_system_state=True,
        max_log_excerpts=50,
    )
    reporter = init_crash_reporting(config)
    ```
"""

from __future__ import annotations

import contextlib
import os
import signal
import sys
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from video2d3d.crash.models import (
    CrashReport,
    CrashReportList,
    CrashReportSummary,
    CrashSeverity,
    CrashType,
)
from video2d3d.crash.state_capture import capture_system_state, set_app_start_time
from video2d3d.utils.logger import get_logger

if TYPE_CHECKING:

    from video2d3d.batch import BatchVideoQueue

# Signal name mapping
SIGNAL_NAMES: dict[int, str] = {
    getattr(signal, name): name
    for name in dir(signal)
    if name.startswith("SIG") and not name.startswith("SIG_")
}

# Global crash reporter instance
_crash_reporter: CrashReporter | None = None


@dataclass
class CrashReporterConfig:
    """Configuration for the crash reporter.

    Attributes:
        crash_dir: Directory to store crash reports.
        app_name: Application name for crash reports.
        app_version: Application version string.
        capture_system_state: Whether to capture system state at crash.
        max_log_excerpts: Maximum number of log lines to capture.
        max_crash_files: Maximum number of crash files to retain.
        signals_to_handle: Set of signals to catch for crash reporting.
        enabled: Whether crash reporting is enabled.
        callback: Optional callback called after crash report is generated.
    """

    crash_dir: Path = field(default_factory=lambda: Path("./crashes"))
    app_name: str = "video2d3d"
    app_version: str = ""
    capture_system_state: bool = True
    max_log_excerpts: int = 50
    max_crash_files: int = 100
    signals_to_handle: set[int] = field(
        default_factory=lambda: {
            signal.SIGTERM,
            signal.SIGINT,
            signal.SIGSEGV,
            signal.SIGABRT,
            signal.SIGFPE,
            signal.SIGBUS,
        }
    )
    enabled: bool = True
    callback: Callable[[CrashReport], None] | None = None

    def __post_init__(self):
        # Ensure crash_dir is a Path
        if isinstance(self.crash_dir, str):
            self.crash_dir = Path(self.crash_dir)


class CrashReporter:
    """Main crash detection and reporting class.

    This class handles:
    - Installing exception hooks for uncaught exceptions
    - Installing signal handlers for graceful shutdown
    - Generating and storing crash reports
    - Capturing system state at crash time
    - Providing access to crash history

    Thread Safety:
        This class uses locks to protect shared state and is safe for
        concurrent access.
    """

    def __init__(
        self,
        config: CrashReporterConfig | None = None,
        *,
        queue: BatchVideoQueue | None = None,
        app_config: dict[str, Any] | None = None,
    ):
        """Initialize the crash reporter.

        Args:
            config: Crash reporter configuration.
            queue: Batch video queue for capturing job state.
            app_config: Application configuration for state capture.
        """
        self.config = config or CrashReporterConfig()
        self.queue = queue
        self.app_config = app_config
        self._logger = get_logger("crash.reporter")
        self._lock = threading.RLock()
        self._original_excepthook: Callable | None = None
        self._original_signal_handlers: dict[int, Any] = {}
        self._handlers_installed = False
        self._crash_count = 0

        # Ensure crash directory exists
        if self.config.enabled:
            self.config.crash_dir.mkdir(parents=True, exist_ok=True)

    def install_handlers(self) -> None:
        """Install exception hooks and signal handlers.

        This method should be called once at application startup.
        It will replace the sys.excepthook and install signal handlers.
        """
        if not self.config.enabled:
            self._logger.info("Crash reporting is disabled")
            return

        with self._lock:
            if self._handlers_installed:
                self._logger.warning("Crash handlers already installed")
                return

            # Install exception hook
            self._original_excepthook = sys.excepthook
            sys.excepthook = self._excepthook

            # Install signal handlers
            self._install_signal_handlers()

            self._handlers_installed = True
            self._logger.info(
                f"Crash handlers installed. Reports will be saved to {self.config.crash_dir}"
            )

    def uninstall_handlers(self) -> None:
        """Uninstall exception hooks and signal handlers.

        Restores original handlers.
        """
        with self._lock:
            if not self._handlers_installed:
                return

            # Restore exception hook
            if self._original_excepthook is not None:
                sys.excepthook = self._original_excepthook
                self._original_excepthook = None

            # Restore signal handlers
            for sig, handler in self._original_signal_handlers.items():
                with contextlib.suppress(ValueError, OSError):
                    signal.signal(sig, handler)
            self._original_signal_handlers.clear()

            self._handlers_installed = False
            self._logger.info("Crash handlers uninstalled")

    def _install_signal_handlers(self) -> None:
        """Install signal handlers for crash detection."""
        for sig in self.config.signals_to_handle:
            try:
                self._original_signal_handlers[sig] = signal.signal(sig, self._signal_handler)
                self._logger.debug(f"Installed handler for {SIGNAL_NAMES.get(sig, sig)}")
            except (ValueError, OSError) as e:
                # Signal not supported on this platform
                self._logger.debug(
                    f"Could not install handler for {SIGNAL_NAMES.get(sig, sig)}: {e}"
                )

    def _excepthook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: Any | None,
    ) -> None:
        """Custom exception hook for uncaught exceptions.

        Args:
            exc_type: Exception type.
            exc_value: Exception instance.
            exc_tb: Exception traceback.
        """
        try:
            # Generate crash report
            report = self.create_crash_report(
                crash_type=CrashType.UNCAUGHT_EXCEPTION,
                exception=(exc_type, exc_value, exc_tb),
                severity=self._determine_severity(exc_value),
            )

            # Save report
            filepath = self.save_report(report)
            self._logger.error(f"Uncaught exception! Crash report saved to: {filepath}")

            # Call callback if set
            if self.config.callback:
                try:
                    self.config.callback(report)
                except Exception as e:
                    self._logger.error(f"Crash callback failed: {e}")

        except Exception as e:
            # Don't crash the crash handler
            self._logger.error(f"Error in crash handler: {e}")

        finally:
            # Call original exception hook
            if self._original_excepthook is not None:
                self._original_excepthook(exc_type, exc_value, exc_tb)
            else:
                # Default behavior: print traceback and exit
                traceback.print_exception(exc_type, exc_value, exc_tb)

    def _signal_handler(self, signum: int, frame: Any | None) -> None:
        """Signal handler for crash detection.

        Args:
            signum: Signal number.
            frame: Current stack frame.
        """
        signal_name = SIGNAL_NAMES.get(signum, f"SIGNAL_{signum}")

        try:
            # Determine severity based on signal
            severity = CrashSeverity.HIGH
            if signum in (signal.SIGTERM, signal.SIGINT):
                severity = CrashSeverity.LOW

            # Generate crash report
            report = self.create_crash_report(
                crash_type=CrashType.SIGNAL_RECEIVED,
                signal_number=signum,
                signal_name=signal_name,
                severity=severity,
                context={"signal_frame": self._format_frame(frame) if frame else None},
            )

            # Save report
            filepath = self.save_report(report)
            self._logger.warning(f"Received {signal_name}. Crash report saved to: {filepath}")

            # Call callback if set
            if self.config.callback:
                try:
                    self.config.callback(report)
                except Exception as e:
                    self._logger.error(f"Crash callback failed: {e}")

        except Exception as e:
            self._logger.error(f"Error in signal handler: {e}")

        finally:
            # Call original handler or default behavior
            original = self._original_signal_handlers.get(signum)
            if original is not None and callable(original):
                original(signum, frame)
            elif signum in (signal.SIGTERM, signal.SIGINT):
                # Graceful termination signals
                sys.exit(128 + signum)
            else:
                # Fatal signals - re-raise to get core dump
                signal.signal(signum, signal.SIG_DFL)
                os.kill(os.getpid(), signum)

    def _format_frame(self, frame: Any) -> str:
        """Format a stack frame for reporting.

        Args:
            frame: Stack frame object.

        Returns:
            Formatted frame string.
        """
        try:
            return "".join(traceback.format_stack(frame))
        except Exception:
            return "<frame unavailable>"

    def _determine_severity(self, exception: BaseException) -> CrashSeverity:
        """Determine crash severity from exception type.

        Args:
            exception: The exception that occurred.

        Returns:
            Appropriate severity level.
        """
        # Check for specific error types
        error_str = str(exception).lower()

        # Out of memory errors
        if "out of memory" in error_str or "oom" in error_str:
            return CrashSeverity.CRITICAL

        # GPU errors
        if "cuda" in error_str or "gpu" in error_str:
            return CrashSeverity.HIGH

        # Timeout errors
        if isinstance(exception, TimeoutError) or "timeout" in error_str:
            return CrashSeverity.MEDIUM

        # Connection errors
        if isinstance(exception, (ConnectionError, OSError)):
            return CrashSeverity.MEDIUM

        # Keyboard interrupt is intentional
        if isinstance(exception, KeyboardInterrupt):
            return CrashSeverity.LOW

        # Default
        return CrashSeverity.HIGH

    def create_crash_report(
        self,
        crash_type: CrashType,
        *,
        exception: tuple | None = None,
        signal_number: int | None = None,
        signal_name: str | None = None,
        severity: CrashSeverity = CrashSeverity.HIGH,
        context: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        user_message: str | None = None,
    ) -> CrashReport:
        """Create a crash report.

        Args:
            crash_type: Type of crash.
            exception: Exception tuple (type, value, traceback).
            signal_number: Signal number for signal-based crashes.
            signal_name: Signal name for signal-based crashes.
            severity: Crash severity level.
            context: Additional context dictionary.
            tags: List of tags for categorization.
            user_message: Optional user-provided message.

        Returns:
            Generated CrashReport.
        """
        report = CrashReport(
            crash_type=crash_type,
            severity=severity,
            tags=tags or [],
            user_message=user_message,
            context=context or {},
        )

        # Extract exception info
        if exception is not None:
            exc_type, exc_value, exc_tb = exception
            report.exception_type = exc_type.__name__ if exc_type else ""
            report.exception_message = str(exc_value) if exc_value else ""
            report.exception_module = exc_type.__module__ if exc_type else ""
            if exc_tb is not None:
                report.exception_traceback = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_tb)
                )

        # Signal info
        report.signal_number = signal_number
        report.signal_name = signal_name

        # Capture system state
        if self.config.capture_system_state:
            try:
                report.system_state = capture_system_state(
                    queue=self.queue,
                    app_version=self.config.app_version,
                    app_config=self.app_config,
                )
            except Exception as e:
                self._logger.error(f"Failed to capture system state: {e}")

        # Capture log excerpts (if log buffer is available)
        report.log_excerpts = self._get_log_excerpts()

        return report

    def _get_log_excerpts(self) -> list[str]:
        """Get recent log entries for crash context.

        Returns:
            List of recent log lines.
        """
        # This is a placeholder - actual implementation would need
        # integration with the logging system to capture recent logs
        return []

    def save_report(self, report: CrashReport) -> Path:
        """Save a crash report to disk.

        Args:
            report: The crash report to save.

        Returns:
            Path to the saved report file.
        """
        with self._lock:
            filepath = report.save(self.config.crash_dir)
            self._crash_count += 1

            # Clean up old crash files if needed
            self._cleanup_old_reports()

            return filepath

    def _cleanup_old_reports(self) -> None:
        """Remove old crash reports if count exceeds maximum."""
        try:
            crash_files = sorted(
                self.config.crash_dir.glob("crash_*.json"),
                key=lambda p: p.stat().st_mtime,
            )

            while len(crash_files) > self.config.max_crash_files:
                old_file = crash_files.pop(0)
                old_file.unlink()
                self._logger.debug(f"Removed old crash report: {old_file}")

        except Exception as e:
            self._logger.error(f"Error cleaning up crash reports: {e}")

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        severity: CrashSeverity | None = None,
    ) -> CrashReportList:
        """List crash reports.

        Args:
            page: Page number (1-indexed).
            page_size: Number of reports per page.
            severity: Optional severity filter.

        Returns:
            CrashReportList with summaries.
        """
        reports: list[CrashReportSummary] = []

        try:
            crash_files = sorted(
                self.config.crash_dir.glob("crash_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            for filepath in crash_files:
                try:
                    report = CrashReport.load(filepath)
                    summary = report.get_summary()

                    # Apply severity filter
                    if severity is not None and summary.severity != severity:
                        continue

                    reports.append(summary)
                except Exception as e:
                    self._logger.warning(f"Failed to load crash report {filepath}: {e}")

        except Exception as e:
            self._logger.error(f"Error listing crash reports: {e}")

        # Paginate
        total_count = len(reports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_reports = reports[start_idx:end_idx]

        return CrashReportList(
            reports=paged_reports,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    def get_report(self, report_id: str) -> CrashReport | None:
        """Get a specific crash report by ID.

        Args:
            report_id: The report ID to find.

        Returns:
            CrashReport if found, None otherwise.
        """
        try:
            # Search for report by ID prefix
            for filepath in self.config.crash_dir.glob(f"crash_*_{report_id[:8]}.json"):
                try:
                    report = CrashReport.load(filepath)
                    if report.report_id == report_id:
                        return report
                except Exception as e:
                    self._logger.warning(f"Failed to load crash report {filepath}: {e}")

        except Exception as e:
            self._logger.error(f"Error getting crash report {report_id}: {e}")

        return None

    def delete_report(self, report_id: str) -> bool:
        """Delete a crash report.

        Args:
            report_id: The report ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        try:
            for filepath in self.config.crash_dir.glob(f"crash_*_{report_id[:8]}.json"):
                try:
                    report = CrashReport.load(filepath)
                    if report.report_id == report_id:
                        filepath.unlink()
                        self._logger.info(f"Deleted crash report: {report_id}")
                        return True
                except Exception:
                    pass

        except Exception as e:
            self._logger.error(f"Error deleting crash report {report_id}: {e}")

        return False

    def clear_reports(self) -> int:
        """Delete all crash reports.

        Returns:
            Number of reports deleted.
        """
        count = 0
        try:
            for filepath in self.config.crash_dir.glob("crash_*.json"):
                try:
                    filepath.unlink()
                    count += 1
                except Exception:
                    pass
            self._logger.info(f"Cleared {count} crash reports")
        except Exception as e:
            self._logger.error(f"Error clearing crash reports: {e}")

        return count

    def report_manual(
        self,
        message: str,
        *,
        exception: Exception | None = None,
        context: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        severity: CrashSeverity = CrashSeverity.MEDIUM,
    ) -> CrashReport:
        """Manually create a crash report.

        Args:
            message: Description of the issue.
            exception: Optional exception to include.
            context: Additional context.
            tags: Tags for categorization.
            severity: Severity level.

        Returns:
            Generated CrashReport.
        """
        exc_tuple = None
        if exception is not None:
            exc_tuple = (type(exception), exception, exception.__traceback__)

        report = self.create_crash_report(
            crash_type=CrashType.MANUAL_REPORT,
            exception=exc_tuple,
            severity=severity,
            context=context,
            tags=tags or ["manual"],
            user_message=message,
        )

        filepath = self.save_report(report)
        self._logger.info(f"Manual crash report saved to: {filepath}")

        # Call callback if set
        if self.config.callback:
            try:
                self.config.callback(report)
            except Exception as e:
                self._logger.error(f"Crash callback failed: {e}")

        return report

    def set_queue(self, queue: BatchVideoQueue | None) -> None:
        """Set the batch queue for job state capture.

        Args:
            queue: The batch video queue instance.
        """
        with self._lock:
            self.queue = queue


def init_crash_reporting(
    config: CrashReporterConfig | None = None,
    *,
    queue: BatchVideoQueue | None = None,
    app_config: dict[str, Any] | None = None,
    app_version: str = "",
    app_start_time: float | None = None,
) -> CrashReporter:
    """Initialize global crash reporting.

    This is the recommended way to set up crash reporting.
    It creates a global CrashReporter instance and installs handlers.

    Args:
        config: Optional crash reporter configuration.
        queue: Optional batch video queue for job state capture.
        app_config: Optional application configuration.
        app_version: Application version string.
        app_start_time: Application start time for uptime calculation.

    Returns:
        The global CrashReporter instance.
    """
    global _crash_reporter

    if config is None:
        config = CrashReporterConfig(app_version=app_version)
    elif app_version:
        config.app_version = app_version

    # Set app start time for uptime calculation
    if app_start_time is not None:
        set_app_start_time(app_start_time)

    _crash_reporter = CrashReporter(config, queue=queue, app_config=app_config)
    _crash_reporter.install_handlers()

    return _crash_reporter


def get_crash_reporter() -> CrashReporter | None:
    """Get the global crash reporter instance.

    Returns:
        The global CrashReporter or None if not initialized.
    """
    return _crash_reporter


def set_crash_reporter_queue(queue: BatchVideoQueue | None) -> None:
    """Set the batch queue for the global crash reporter.

    This allows the crash reporter to capture active job information
    when generating crash reports.

    Args:
        queue: The batch video queue instance.
    """
    global _crash_reporter

    if _crash_reporter is not None:
        _crash_reporter.set_queue(queue)


def shutdown_crash_reporting() -> None:
    """Shutdown global crash reporting.

    Uninstalls exception hooks and signal handlers and clears the global
    CrashReporter instance. Safe to call even if crash reporting was
    never initialized.
    """
    global _crash_reporter

    if _crash_reporter is not None:
        _crash_reporter.uninstall_handlers()
        _crash_reporter = None


__all__ = [
    "CrashReporter",
    "CrashReporterConfig",
    "init_crash_reporting",
    "get_crash_reporter",
    "set_crash_reporter_queue",
    "shutdown_crash_reporting",
]
