"""Crash detection and reporting system for debugging failures.

This module provides comprehensive crash detection, reporting, and diagnostics:
- Automatic capture of uncaught exceptions
- Signal handlers for graceful shutdown
- System state capture (GPU, memory, active jobs)
- Structured crash report storage
- API endpoints for crash report retrieval

Example usage:
    ```python
    from video2d3d.crash import CrashReporter, init_crash_reporting

    # Initialize crash reporting
    reporter = init_crash_reporting()

    # Or manually configure
    reporter = CrashReporter(
        app_name="video2d3d",
        crash_dir=Path("./crashes"),
        capture_system_state=True,
    )
    reporter.install_handlers()
    ```
"""

from video2d3d.crash.models import (
    ActiveJobInfo,
    CrashReport,
    CrashReportSummary,
    CrashSeverity,
    CrashType,
    SystemState,
)
from video2d3d.crash.reporter import (
    CrashReporter,
    CrashReporterConfig,
    get_crash_reporter,
    init_crash_reporting,
    set_crash_reporter_queue,
    shutdown_crash_reporting,
)
from video2d3d.crash.state_capture import (
    capture_system_state,
    get_gpu_info,
    get_memory_info,
    get_process_info,
)

__all__ = [
    # Models
    "CrashReport",
    "CrashReportSummary",
    "CrashSeverity",
    "CrashType",
    "SystemState",
    "ActiveJobInfo",
    # Reporter
    "CrashReporter",
    "CrashReporterConfig",
    "get_crash_reporter",
    "set_crash_reporter_queue",
    "shutdown_crash_reporting",
]
