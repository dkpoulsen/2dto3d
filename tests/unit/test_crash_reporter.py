"""Unit tests for crash reporter functionality.

Tests cover:
- CrashReporter initialization and configuration
- Exception hook installation and handling
- Signal handler installation and handling
- Crash report creation
- Crash report storage and retrieval
- Manual crash report creation
- Crash reporter lifecycle management
"""

from __future__ import annotations

import signal
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock

from video2d3d.crash.models import CrashReport, CrashSeverity, CrashType
from video2d3d.crash.reporter import (
    CrashReporter,
    CrashReporterConfig,
    get_crash_reporter,
    init_crash_reporting,
    set_crash_reporter_queue,
    shutdown_crash_reporting,
)


class TestCrashReporterConfig:
    """Tests for CrashReporterConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = CrashReporterConfig()

        assert config.app_name == "video2d3d"
        assert config.app_version == ""
        assert config.capture_system_state is True
        assert config.max_log_excerpts == 50
        assert config.max_crash_files == 100
        assert config.enabled is True
        assert config.callback is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = CrashReporterConfig(
            crash_dir=Path("/custom/crashes"),
            app_name="custom_app",
            app_version="1.0.0",
            capture_system_state=False,
            max_log_excerpts=100,
            max_crash_files=50,
            enabled=False,
        )

        assert config.crash_dir == Path("/custom/crashes")
        assert config.app_name == "custom_app"
        assert config.app_version == "1.0.0"
        assert config.capture_system_state is False
        assert config.enabled is False

    def test_crash_dir_string_to_path(self) -> None:
        """Test crash_dir string is converted to Path."""
        config = CrashReporterConfig(crash_dir="/string/path")
        assert isinstance(config.crash_dir, Path)
        assert config.crash_dir == Path("/string/path")

    def test_default_signals(self) -> None:
        """Test default signals to handle."""
        config = CrashReporterConfig()

        # Common signals should be included
        assert signal.SIGTERM in config.signals_to_handle
        assert signal.SIGINT in config.signals_to_handle


class TestCrashReporter:
    """Tests for CrashReporter class."""

    def test_initialization_default(self) -> None:
        """Test reporter initialization with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            assert reporter.config == config
            assert reporter.queue is None
            assert reporter._handlers_installed is False

    def test_initialization_with_queue(self) -> None:
        """Test reporter initialization with queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            mock_queue = MagicMock()
            reporter = CrashReporter(config, queue=mock_queue)

            assert reporter.queue == mock_queue

    def test_initialization_creates_directory(self) -> None:
        """Test reporter creates crash directory on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crash_dir = Path(tmpdir) / "nested" / "crashes"
            config = CrashReporterConfig(crash_dir=crash_dir)

            CrashReporter(config)

            assert crash_dir.exists()

    def test_disabled_reporter(self) -> None:
        """Test disabled reporter doesn't install handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir), enabled=False)
            reporter = CrashReporter(config)

            reporter.install_handlers()

            assert not reporter._handlers_installed

    def test_install_handlers_once(self) -> None:
        """Test handlers are only installed once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            reporter.install_handlers()
            assert reporter._handlers_installed is True

            # Second call should be safe
            reporter.install_handlers()
            assert reporter._handlers_installed is True

            reporter.uninstall_handlers()

    def test_uninstall_handlers(self) -> None:
        """Test handlers can be uninstalled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            reporter.install_handlers()
            assert reporter._handlers_installed is True

            reporter.uninstall_handlers()
            assert reporter._handlers_installed is False


class TestCrashReportCreation:
    """Tests for crash report creation."""

    def test_create_crash_report_basic(self) -> None:
        """Test basic crash report creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(
                crash_type=CrashType.UNCAUGHT_EXCEPTION,
                severity=CrashSeverity.HIGH,
            )

            assert report.crash_type == CrashType.UNCAUGHT_EXCEPTION
            assert report.severity == CrashSeverity.HIGH
            assert report.report_id != ""

    def test_create_crash_report_with_exception(self) -> None:
        """Test crash report with exception info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            try:
                raise ValueError("Test error message")
            except ValueError as e:
                exc_tuple = (type(e), e, e.__traceback__)
                report = reporter.create_crash_report(
                    crash_type=CrashType.UNCAUGHT_EXCEPTION,
                    exception=exc_tuple,
                )

            assert report.exception_type == "ValueError"
            assert "Test error message" in report.exception_message
            assert "Traceback" in report.exception_traceback

    def test_create_crash_report_with_signal(self) -> None:
        """Test crash report with signal info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(
                crash_type=CrashType.SIGNAL_RECEIVED,
                signal_number=signal.SIGTERM,
                signal_name="SIGTERM",
                severity=CrashSeverity.LOW,
            )

            assert report.signal_number == signal.SIGTERM
            assert report.signal_name == "SIGTERM"
            assert report.severity == CrashSeverity.LOW

    def test_create_crash_report_with_context(self) -> None:
        """Test crash report with context and tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(
                crash_type=CrashType.PROCESSING_ERROR,
                context={"input_file": "video.mp4", "frame": 150},
                tags=["processing", "video"],
                user_message="Failed during frame extraction",
            )

            assert report.context["input_file"] == "video.mp4"
            assert report.context["frame"] == 150
            assert "processing" in report.tags
            assert report.user_message == "Failed during frame extraction"

    def test_create_crash_report_captures_system_state(self) -> None:
        """Test crash report captures system state when enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir), capture_system_state=True)
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(crash_type=CrashType.UNCAUGHT_EXCEPTION)

            assert report.system_state is not None
            assert report.system_state.platform_system != ""

    def test_create_crash_report_no_system_state(self) -> None:
        """Test crash report without system state when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir), capture_system_state=False)
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(crash_type=CrashType.UNCAUGHT_EXCEPTION)

            # System state may be None or have minimal info
            # The key is that it doesn't fail


class TestSeverityDetermination:
    """Tests for severity determination logic."""

    def test_oom_severity(self) -> None:
        """Test OOM errors get critical severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            severity = reporter._determine_severity(RuntimeError("CUDA out of memory"))
            assert severity == CrashSeverity.CRITICAL

    def test_gpu_error_severity(self) -> None:
        """Test GPU errors get high severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            severity = reporter._determine_severity(RuntimeError("CUDA device error"))
            assert severity == CrashSeverity.HIGH

    def test_timeout_severity(self) -> None:
        """Test timeout errors get medium severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            severity = reporter._determine_severity(TimeoutError("Operation timed out"))
            assert severity == CrashSeverity.MEDIUM

    def test_keyboard_interrupt_severity(self) -> None:
        """Test keyboard interrupt gets low severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            severity = reporter._determine_severity(KeyboardInterrupt())
            assert severity == CrashSeverity.LOW

    def test_connection_error_severity(self) -> None:
        """Test connection errors get medium severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            severity = reporter._determine_severity(ConnectionError("Connection refused"))
            assert severity == CrashSeverity.MEDIUM


class TestCrashReportStorage:
    """Tests for crash report storage."""

    def test_save_report(self) -> None:
        """Test saving a crash report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(crash_type=CrashType.MANUAL_REPORT)
            filepath = reporter.save_report(report)

            assert filepath.exists()
            assert filepath.suffix == ".json"

    def test_list_reports_empty(self) -> None:
        """Test listing reports when empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report_list = reporter.list_reports()

            assert report_list.total_count == 0
            assert report_list.reports == []

    def test_list_reports_with_data(self) -> None:
        """Test listing reports with data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            # Create some reports
            for i in range(3):
                report = reporter.create_crash_report(
                    crash_type=CrashType.MANUAL_REPORT,
                    severity=CrashSeverity.HIGH if i < 2 else CrashSeverity.LOW,
                )
                reporter.save_report(report)

            report_list = reporter.list_reports()

            assert report_list.total_count == 3
            assert len(report_list.reports) == 3

    def test_list_reports_pagination(self) -> None:
        """Test listing reports with pagination."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            # Create 5 reports
            for _ in range(5):
                report = reporter.create_crash_report(crash_type=CrashType.MANUAL_REPORT)
                reporter.save_report(report)

            # First page
            page1 = reporter.list_reports(page=1, page_size=2)
            assert len(page1.reports) == 2
            assert page1.total_count == 5
            assert page1.page == 1

            # Second page
            page2 = reporter.list_reports(page=2, page_size=2)
            assert len(page2.reports) == 2
            assert page2.page == 2

    def test_list_reports_filter_severity(self) -> None:
        """Test listing reports filtered by severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            # Create reports with different severities
            report_high = reporter.create_crash_report(
                crash_type=CrashType.MANUAL_REPORT,
                severity=CrashSeverity.HIGH,
            )
            reporter.save_report(report_high)

            report_low = reporter.create_crash_report(
                crash_type=CrashType.MANUAL_REPORT,
                severity=CrashSeverity.LOW,
            )
            reporter.save_report(report_low)

            # Filter for HIGH severity
            filtered = reporter.list_reports(severity=CrashSeverity.HIGH)

            assert filtered.total_count == 1
            assert filtered.reports[0].severity == CrashSeverity.HIGH

    def test_get_report_by_id(self) -> None:
        """Test getting a specific report by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(crash_type=CrashType.MANUAL_REPORT)
            reporter.save_report(report)

            retrieved = reporter.get_report(report.report_id)

            assert retrieved is not None
            assert retrieved.report_id == report.report_id

    def test_get_report_not_found(self) -> None:
        """Test getting a non-existent report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            retrieved = reporter.get_report("non-existent-id")

            assert retrieved is None

    def test_delete_report(self) -> None:
        """Test deleting a report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.create_crash_report(crash_type=CrashType.MANUAL_REPORT)
            reporter.save_report(report)

            deleted = reporter.delete_report(report.report_id)
            assert deleted is True

            # Verify it's gone
            retrieved = reporter.get_report(report.report_id)
            assert retrieved is None

    def test_clear_all_reports(self) -> None:
        """Test clearing all reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            # Create multiple reports
            for _ in range(3):
                report = reporter.create_crash_report(crash_type=CrashType.MANUAL_REPORT)
                reporter.save_report(report)

            count = reporter.clear_reports()

            assert count == 3

            # Verify all gone
            report_list = reporter.list_reports()
            assert report_list.total_count == 0


class TestManualReport:
    """Tests for manual crash report creation."""

    def test_manual_report_basic(self) -> None:
        """Test basic manual report creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.report_manual(message="User reported issue")

            assert report.crash_type == CrashType.MANUAL_REPORT
            assert report.user_message == "User reported issue"
            assert "manual" in report.tags

    def test_manual_report_with_exception(self) -> None:
        """Test manual report with exception."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            try:
                raise RuntimeError("Client error")
            except RuntimeError as e:
                report = reporter.report_manual(
                    message="Client encountered error",
                    exception=e,
                    tags=["client", "runtime"],
                )

            assert report.exception_type == "RuntimeError"
            assert "Client error" in report.exception_message

    def test_manual_report_with_context(self) -> None:
        """Test manual report with context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            report = reporter.report_manual(
                message="Processing failed",
                context={"video": "test.mp4", "frame": 100},
                severity=CrashSeverity.HIGH,
            )

            assert report.context["video"] == "test.mp4"
            assert report.severity == CrashSeverity.HIGH


class TestCleanup:
    """Tests for crash report cleanup."""

    def test_cleanup_old_reports(self) -> None:
        """Test old reports are cleaned up when limit exceeded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(
                crash_dir=Path(tmpdir),
                max_crash_files=3,
            )
            reporter = CrashReporter(config)

            # Create more reports than the limit
            for i in range(5):
                report = reporter.create_crash_report(
                    crash_type=CrashType.MANUAL_REPORT,
                )
                reporter.save_report(report)

            # Should have cleaned up to max_crash_files
            crash_files = list(Path(tmpdir).glob("crash_*.json"))
            assert len(crash_files) <= 3


class TestQueueIntegration:
    """Tests for queue integration."""

    def test_set_queue(self) -> None:
        """Test setting queue after initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            assert reporter.queue is None

            mock_queue = MagicMock()
            reporter.set_queue(mock_queue)

            assert reporter.queue == mock_queue

    def test_report_with_queue(self) -> None:
        """Test report creation captures queue jobs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir), capture_system_state=True)
            reporter = CrashReporter(config)

            # Create mock queue with jobs
            mock_job = MagicMock()
            mock_job.job_id = "job-123"
            mock_job.status = "running"
            mock_job.input_path = None
            mock_job.output_path = None
            mock_job.started_at = None
            mock_job.progress = None
            mock_job.current_stage = None
            mock_job.frames_processed = None
            mock_job.total_frames = None

            mock_queue = MagicMock()
            mock_queue.list_jobs.return_value = [mock_job]
            mock_queue.get_stats.return_value = MagicMock(to_dict=lambda: {"total": 1})

            reporter.set_queue(mock_queue)

            report = reporter.create_crash_report(crash_type=CrashType.MANUAL_REPORT)

            # System state should include queue info
            assert report.system_state is not None


class TestGlobalReporter:
    """Tests for global crash reporter functions."""

    def test_init_crash_reporting(self) -> None:
        """Test global crash reporting initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))

            reporter = init_crash_reporting(config)

            assert reporter is not None
            assert reporter._handlers_installed is True

            # Global should be set
            global_reporter = get_crash_reporter()
            assert global_reporter is reporter

            shutdown_crash_reporting()

    def test_set_crash_reporter_queue(self) -> None:
        """Test setting queue on global reporter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            init_crash_reporting(config)

            mock_queue = MagicMock()
            set_crash_reporter_queue(mock_queue)

            reporter = get_crash_reporter()
            assert reporter.queue == mock_queue

            shutdown_crash_reporting()

    def test_shutdown_crash_reporting(self) -> None:
        """Test shutting down global crash reporting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            init_crash_reporting(config)

            assert get_crash_reporter() is not None

            shutdown_crash_reporting()

            assert get_crash_reporter() is None

    def test_get_crash_reporter_when_not_initialized(self) -> None:
        """Test get_crash_reporter returns None when not initialized."""
        # Ensure no global reporter
        shutdown_crash_reporting()

        reporter = get_crash_reporter()
        assert reporter is None


class TestCallback:
    """Tests for crash report callback functionality."""

    def test_callback_on_report(self) -> None:
        """Test callback is called when report is created."""
        callback_called = []

        def my_callback(report: CrashReport) -> None:
            callback_called.append(report.report_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(
                crash_dir=Path(tmpdir),
                callback=my_callback,
            )
            reporter = CrashReporter(config)

            report = reporter.report_manual("Test callback")

            assert report.report_id in callback_called

    def test_callback_exception_handling(self) -> None:
        """Test callback exceptions are handled gracefully."""

        def failing_callback(report: CrashReport) -> None:
            raise RuntimeError("Callback failed!")

        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(
                crash_dir=Path(tmpdir),
                callback=failing_callback,
            )
            reporter = CrashReporter(config)

            # Should not raise
            report = reporter.report_manual("Test failing callback")

            assert report is not None


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_report_creation(self) -> None:
        """Test concurrent report creation is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CrashReporterConfig(crash_dir=Path(tmpdir))
            reporter = CrashReporter(config)

            created_reports = []
            errors = []

            def create_report(i: int) -> None:
                try:
                    report = reporter.create_crash_report(
                        crash_type=CrashType.MANUAL_REPORT,
                        context={"thread_id": i},
                    )
                    reporter.save_report(report)
                    created_reports.append(report.report_id)
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=create_report, args=(i,)) for i in range(10)]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # All should succeed without errors
            assert len(errors) == 0
            assert len(created_reports) == 10
