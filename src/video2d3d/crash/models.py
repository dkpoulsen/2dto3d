"""Data models for crash reports and system state.

This module defines the core data structures used for crash reporting:
- CrashReport: Full crash report with all captured data
- CrashReportSummary: Lightweight summary for listing
- SystemState: Captured system state at crash time
- ActiveJobInfo: Information about active processing jobs
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

# Sanitization pattern for filenames - keep only safe characters
SAFE_FILENAME_PATTERN = re.compile(r"[^\w\-.]")


def _sanitize_filename(text: str) -> str:
    """Sanitize text for use in a filename.

    Replaces any characters that are not word characters, hyphens, or dots with underscores.
    """
    return SAFE_FILENAME_PATTERN.sub("_", text)


class CrashType(str, Enum):
    """Types of crashes that can be detected."""

    UNCAUGHT_EXCEPTION = "uncaught_exception"
    SIGNAL_RECEIVED = "signal_received"
    MANUAL_REPORT = "manual_report"
    OOM_ERROR = "oom_error"
    GPU_ERROR = "gpu_error"
    TIMEOUT_ERROR = "timeout_error"
    PROCESSING_ERROR = "processing_error"


class CrashSeverity(str, Enum):
    """Severity levels for crash reports."""

    LOW = "low"  # Recoverable, minimal impact
    MEDIUM = "medium"  # Partial functionality lost
    HIGH = "high"  # Major functionality lost
    CRITICAL = "critical"  # Application terminated


@dataclass
class ActiveJobInfo:
    """Information about an active job at crash time."""

    job_id: str
    status: str
    input_file: str | None = None
    output_file: str | None = None
    progress_percent: float = 0.0
    current_stage: str | None = None
    started_at: str | None = None
    frames_processed: int = 0
    total_frames: int = 0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActiveJobInfo:
        return cls(**data)


@dataclass
class GPUInfo:
    """GPU state at crash time."""

    available: bool = False
    device_name: str | None = None
    device_count: int = 0
    memory_used_mb: float = 0.0
    memory_free_mb: float = 0.0
    memory_total_mb: float = 0.0
    memory_utilization_percent: float = 0.0
    compute_capability: str | None = None
    temperature_celsius: float | None = None
    power_usage_watts: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryInfo:
    """System memory state at crash time."""

    total_mb: float = 0.0
    available_mb: float = 0.0
    used_mb: float = 0.0
    utilization_percent: float = 0.0
    swap_total_mb: float = 0.0
    swap_used_mb: float = 0.0
    swap_utilization_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessInfo:
    """Process state at crash time."""

    pid: int = 0
    parent_pid: int | None = None
    command_line: str = ""
    working_directory: str = ""
    cpu_percent: float = 0.0
    memory_rss_mb: float = 0.0
    memory_vms_mb: float = 0.0
    num_threads: int = 1
    num_file_descriptors: int | None = None
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SystemState:
    """Complete system state captured at crash time."""

    # Timestamp
    timestamp: str = ""
    uptime_seconds: float = 0.0

    # Platform info
    platform_system: str = ""
    platform_node: str = ""
    platform_release: str = ""
    platform_version: str = ""
    platform_machine: str = ""
    platform_python_version: str = ""

    # Hardware state
    gpu: GPUInfo = field(default_factory=GPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    process: ProcessInfo = field(default_factory=ProcessInfo)

    # Application state
    active_jobs: list[ActiveJobInfo] = field(default_factory=list)
    queue_stats: dict[str, Any] = field(default_factory=dict)
    app_version: str = ""
    app_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime_seconds,
            "platform_system": self.platform_system,
            "platform_node": self.platform_node,
            "platform_release": self.platform_release,
            "platform_version": self.platform_version,
            "platform_machine": self.platform_machine,
            "platform_python_version": self.platform_python_version,
            "gpu": self.gpu.to_dict(),
            "memory": self.memory.to_dict(),
            "process": self.process.to_dict(),
            "active_jobs": [j.to_dict() for j in self.active_jobs],
            "queue_stats": self.queue_stats,
            "app_version": self.app_version,
            "app_config": self.app_config,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemState:
        gpu_data = data.get("gpu", {})
        memory_data = data.get("memory", {})
        process_data = data.get("process", {})
        jobs_data = data.get("active_jobs", [])

        return cls(
            timestamp=data.get("timestamp", ""),
            uptime_seconds=data.get("uptime_seconds", 0.0),
            platform_system=data.get("platform_system", ""),
            platform_node=data.get("platform_node", ""),
            platform_release=data.get("platform_release", ""),
            platform_version=data.get("platform_version", ""),
            platform_machine=data.get("platform_machine", ""),
            platform_python_version=data.get("platform_python_version", ""),
            gpu=GPUInfo(**gpu_data),
            memory=MemoryInfo(**memory_data),
            process=ProcessInfo(**process_data),
            active_jobs=[ActiveJobInfo.from_dict(j) for j in jobs_data],
            queue_stats=data.get("queue_stats", {}),
            app_version=data.get("app_version", ""),
            app_config=data.get("app_config", {}),
        )


@dataclass
class CrashReport:
    """Complete crash report with all captured data."""

    # Identification
    report_id: str = ""
    created_at: str = ""

    # Crash details
    crash_type: CrashType = CrashType.UNCAUGHT_EXCEPTION
    severity: CrashSeverity = CrashSeverity.HIGH

    # Exception info
    exception_type: str = ""
    exception_message: str = ""
    exception_traceback: str = ""
    exception_module: str = ""

    # Signal info (for signal-based crashes)
    signal_number: int | None = None
    signal_name: str | None = None

    # Context
    context: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    user_message: str | None = None

    # System state
    system_state: SystemState | None = None

    # Log excerpts (last N log lines before crash)
    log_excerpts: list[str] = field(default_factory=list)

    # Recovery info
    recovered: bool = False
    recovery_action: str | None = None

    def __post_init__(self):
        if not self.report_id:
            self.report_id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "crash_type": self.crash_type.value,
            "severity": self.severity.value,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "exception_traceback": self.exception_traceback,
            "exception_module": self.exception_module,
            "signal_number": self.signal_number,
            "signal_name": self.signal_name,
            "context": self.context,
            "tags": self.tags,
            "user_message": self.user_message,
            "system_state": self.system_state.to_dict() if self.system_state else None,
            "log_excerpts": self.log_excerpts,
            "recovered": self.recovered,
            "recovery_action": self.recovery_action,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CrashReport:
        system_state = None
        if data.get("system_state"):
            system_state = SystemState.from_dict(data["system_state"])

        return cls(
            report_id=data.get("report_id", ""),
            created_at=data.get("created_at", ""),
            crash_type=CrashType(data.get("crash_type", "uncaught_exception")),
            severity=CrashSeverity(data.get("severity", "high")),
            exception_type=data.get("exception_type", ""),
            exception_message=data.get("exception_message", ""),
            exception_traceback=data.get("exception_traceback", ""),
            exception_module=data.get("exception_module", ""),
            signal_number=data.get("signal_number"),
            signal_name=data.get("signal_name"),
            context=data.get("context", {}),
            tags=data.get("tags", []),
            user_message=data.get("user_message"),
            system_state=system_state,
            log_excerpts=data.get("log_excerpts", []),
            recovered=data.get("recovered", False),
            recovery_action=data.get("recovery_action"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> CrashReport:
        return cls.from_dict(json.loads(json_str))

    def save(self, crash_dir: Path) -> Path:
        """Save crash report to a file.

        Args:
            crash_dir: Directory to save crash reports.

        Returns:
            Path to the saved crash report file.
        """
        crash_dir.mkdir(parents=True, exist_ok=True)
        # Sanitize timestamp for safe filename (remove special chars like :, ., +, Z)
        safe_timestamp = _sanitize_filename(self.created_at)
        filename = f"crash_{safe_timestamp}_{self.report_id[:8]}.json"
        filepath = crash_dir / filename
        filepath.write_text(self.to_json())
        return filepath

    @classmethod
    def load(cls, filepath: Path) -> CrashReport:
        """Load crash report from a file.

        Args:
            filepath: Path to the crash report file.

        Returns:
            Loaded CrashReport instance.
        """
        return cls.from_json(filepath.read_text())

    def get_summary(self) -> CrashReportSummary:
        """Get a lightweight summary of this crash report."""
        return CrashReportSummary(
            report_id=self.report_id,
            created_at=self.created_at,
            crash_type=self.crash_type,
            severity=self.severity,
            exception_type=self.exception_type,
            exception_message=self.exception_message[:200] if self.exception_message else "",
            recovered=self.recovered,
        )


@dataclass
class CrashReportSummary:
    """Lightweight summary of a crash report for listing."""

    report_id: str
    created_at: str
    crash_type: CrashType
    severity: CrashSeverity
    exception_type: str
    exception_message: str
    recovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "crash_type": self.crash_type.value,
            "severity": self.severity.value,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "recovered": self.recovered,
        }


@dataclass
class CrashReportList:
    """List of crash report summaries with metadata."""

    reports: list[CrashReportSummary]
    total_count: int
    page: int = 1
    page_size: int = 20

    def to_dict(self) -> dict[str, Any]:
        return {
            "reports": [r.to_dict() for r in self.reports],
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
        }
