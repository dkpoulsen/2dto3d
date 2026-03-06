"""Unit tests for crash report data models.

Tests cover:
- CrashReport model creation and serialization
- CrashType and CrashSeverity enums
- SystemState model with GPU, memory, process info
- ActiveJobInfo model
- Crash report file save/load operations
- CrashReportSummary and CrashReportList
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from video2d3d.crash.models import (
    ActiveJobInfo,
    CrashReport,
    CrashReportList,
    CrashReportSummary,
    CrashSeverity,
    CrashType,
    GPUInfo,
    MemoryInfo,
    ProcessInfo,
    SystemState,
    _sanitize_filename,
)


class TestCrashTypeEnum:
    """Tests for CrashType enum."""

    def test_crash_type_values(self) -> None:
        """Test CrashType enum values."""
        assert CrashType.UNCAUGHT_EXCEPTION.value == "uncaught_exception"
        assert CrashType.SIGNAL_RECEIVED.value == "signal_received"
        assert CrashType.MANUAL_REPORT.value == "manual_report"
        assert CrashType.OOM_ERROR.value == "oom_error"
        assert CrashType.GPU_ERROR.value == "gpu_error"
        assert CrashType.TIMEOUT_ERROR.value == "timeout_error"
        assert CrashType.PROCESSING_ERROR.value == "processing_error"

    def test_crash_type_from_string(self) -> None:
        """Test CrashType can be created from string."""
        assert CrashType("uncaught_exception") == CrashType.UNCAUGHT_EXCEPTION
        assert CrashType("signal_received") == CrashType.SIGNAL_RECEIVED

    def test_crash_type_invalid_value(self) -> None:
        """Test CrashType rejects invalid values."""
        with pytest.raises(ValueError):
            CrashType("invalid_type")


class TestCrashSeverityEnum:
    """Tests for CrashSeverity enum."""

    def test_severity_values(self) -> None:
        """Test CrashSeverity enum values."""
        assert CrashSeverity.LOW.value == "low"
        assert CrashSeverity.MEDIUM.value == "medium"
        assert CrashSeverity.HIGH.value == "high"
        assert CrashSeverity.CRITICAL.value == "critical"

    def test_severity_order(self) -> None:
        """Test severity levels are ordered correctly."""
        assert CrashSeverity.LOW.value < CrashSeverity.MEDIUM.value
        assert CrashSeverity.MEDIUM.value < CrashSeverity.HIGH.value
        assert CrashSeverity.HIGH.value < CrashSeverity.CRITICAL.value


class TestActiveJobInfo:
    """Tests for ActiveJobInfo model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        job = ActiveJobInfo(job_id="job-123", status="running")
        assert job.job_id == "job-123"
        assert job.status == "running"
        assert job.input_file is None
        assert job.output_file is None
        assert job.progress_percent == 0.0
        assert job.current_stage is None
        assert job.started_at is None
        assert job.frames_processed == 0
        assert job.total_frames == 0
        assert job.error_message is None
        assert job.metadata == {}

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        job = ActiveJobInfo(
            job_id="job-456",
            status="failed",
            input_file="/input/video.mp4",
            output_file="/output/video_3d.mp4",
            progress_percent=75.5,
            current_stage="depth_estimation",
            started_at="2024-01-15T10:30:00Z",
            frames_processed=750,
            total_frames=1000,
            error_message="CUDA out of memory",
            metadata={"retry_count": 2},
        )
        assert job.job_id == "job-456"
        assert job.status == "failed"
        assert job.input_file == "/input/video.mp4"
        assert job.progress_percent == 75.5
        assert job.frames_processed == 750
        assert job.metadata == {"retry_count": 2}

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        job = ActiveJobInfo(
            job_id="job-789",
            status="completed",
            frames_processed=100,
        )
        data = job.to_dict()
        assert data["job_id"] == "job-789"
        assert data["status"] == "completed"
        assert data["frames_processed"] == 100

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        data = {
            "job_id": "job-abc",
            "status": "pending",
            "progress_percent": 0.0,
            "frames_processed": 0,
            "total_frames": 0,
        }
        job = ActiveJobInfo.from_dict(data)
        assert job.job_id == "job-abc"
        assert job.status == "pending"


class TestGPUInfo:
    """Tests for GPUInfo model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        gpu = GPUInfo()
        assert gpu.available is False
        assert gpu.device_name is None
        assert gpu.device_count == 0
        assert gpu.memory_used_mb == 0.0
        assert gpu.memory_free_mb == 0.0
        assert gpu.memory_total_mb == 0.0

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        gpu = GPUInfo(
            available=True,
            device_name="NVIDIA RTX 3080",
            device_count=1,
            memory_used_mb=8192.0,
            memory_total_mb=10240.0,
            memory_utilization_percent=80.0,
            compute_capability="8.6",
            temperature_celsius=75.0,
        )
        assert gpu.available is True
        assert gpu.device_name == "NVIDIA RTX 3080"
        assert gpu.memory_used_mb == 8192.0
        assert gpu.compute_capability == "8.6"

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        gpu = GPUInfo(available=True, device_name="Test GPU")
        data = gpu.to_dict()
        assert data["available"] is True
        assert data["device_name"] == "Test GPU"


class TestMemoryInfo:
    """Tests for MemoryInfo model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        mem = MemoryInfo()
        assert mem.total_mb == 0.0
        assert mem.available_mb == 0.0
        assert mem.used_mb == 0.0
        assert mem.utilization_percent == 0.0

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        mem = MemoryInfo(
            total_mb=32768.0,
            available_mb=8192.0,
            used_mb=24576.0,
            utilization_percent=75.0,
            swap_total_mb=8192.0,
            swap_used_mb=1024.0,
        )
        assert mem.total_mb == 32768.0
        assert mem.utilization_percent == 75.0

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        mem = MemoryInfo(total_mb=16384.0)
        data = mem.to_dict()
        assert data["total_mb"] == 16384.0


class TestProcessInfo:
    """Tests for ProcessInfo model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        proc = ProcessInfo()
        assert proc.pid == 0
        assert proc.parent_pid is None
        assert proc.command_line == ""
        assert proc.cpu_percent == 0.0
        assert proc.memory_rss_mb == 0.0
        assert proc.num_threads == 1

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        proc = ProcessInfo(
            pid=12345,
            parent_pid=1000,
            command_line="python -m video2d3d serve",
            working_directory="/app",
            cpu_percent=45.5,
            memory_rss_mb=2048.0,
            memory_vms_mb=4096.0,
            num_threads=8,
            uptime_seconds=3600.0,
        )
        assert proc.pid == 12345
        assert proc.cpu_percent == 45.5
        assert proc.num_threads == 8

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        proc = ProcessInfo(pid=999, cpu_percent=25.0)
        data = proc.to_dict()
        assert data["pid"] == 999
        assert data["cpu_percent"] == 25.0


class TestSystemState:
    """Tests for SystemState model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        state = SystemState()
        assert state.timestamp == ""
        assert state.uptime_seconds == 0.0
        assert state.platform_system == ""
        assert state.gpu is not None
        assert state.memory is not None
        assert state.process is not None
        assert state.active_jobs == []
        assert state.queue_stats == {}
        assert state.app_version == ""

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        state = SystemState(
            timestamp="2024-01-15T10:30:00Z",
            uptime_seconds=3600.0,
            platform_system="Linux",
            platform_python_version="3.10.0",
            gpu=GPUInfo(available=True, device_name="RTX 3080"),
            memory=MemoryInfo(total_mb=32768.0),
            process=ProcessInfo(pid=12345),
            active_jobs=[
                ActiveJobInfo(job_id="job-1", status="running"),
            ],
            queue_stats={"pending": 5, "running": 2},
            app_version="0.1.0",
        )
        assert state.timestamp == "2024-01-15T10:30:00Z"
        assert state.uptime_seconds == 3600.0
        assert state.platform_system == "Linux"
        assert state.gpu.available is True
        assert state.memory.total_mb == 32768.0
        assert len(state.active_jobs) == 1
        assert state.queue_stats["pending"] == 5

    def test_to_dict(self) -> None:
        """Test to_dict serialization with nested objects."""
        state = SystemState(
            timestamp="2024-01-15T10:30:00Z",
            platform_system="Linux",
            gpu=GPUInfo(available=True),
            active_jobs=[ActiveJobInfo(job_id="job-1", status="pending")],
        )
        data = state.to_dict()
        assert data["timestamp"] == "2024-01-15T10:30:00Z"
        assert data["platform_system"] == "Linux"
        assert data["gpu"]["available"] is True
        assert len(data["active_jobs"]) == 1

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        data = {
            "timestamp": "2024-01-15T10:30:00Z",
            "uptime_seconds": 1800.0,
            "platform_system": "Windows",
            "platform_python_version": "3.11.0",
            "gpu": {"available": True, "device_name": "RTX 4090"},
            "memory": {"total_mb": 65536.0},
            "process": {"pid": 9999, "cpu_percent": 50.0},
            "active_jobs": [{"job_id": "job-abc", "status": "running", "progress_percent": 50.0}],
            "queue_stats": {"total": 10},
            "app_version": "1.0.0",
        }
        state = SystemState.from_dict(data)
        assert state.timestamp == "2024-01-15T10:30:00Z"
        assert state.uptime_seconds == 1800.0
        assert state.platform_system == "Windows"
        assert state.gpu.available is True
        assert state.gpu.device_name == "RTX 4090"
        assert state.memory.total_mb == 65536.0
        assert state.process.pid == 9999
        assert len(state.active_jobs) == 1
        assert state.active_jobs[0].job_id == "job-abc"


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_colons(self) -> None:
        """Test colons are replaced."""
        result = _sanitize_filename("2024-01-15T10:30:00")
        assert ":" not in result
        assert "_" in result

    def test_sanitize_dots(self) -> None:
        """Test dots are handled correctly."""
        result = _sanitize_filename("file.123.json")
        # Dots should be preserved in extensions
        assert "file" in result
        assert "json" in result

    def test_sanitize_special_chars(self) -> None:
        """Test special characters are replaced."""
        result = _sanitize_filename("test+value@host")
        assert "+" not in result
        assert "@" not in result

    def test_sanitize_preserves_alphanumeric(self) -> None:
        """Test alphanumeric and common safe chars preserved."""
        result = _sanitize_filename("safe-name_123")
        assert result == "safe-name_123"

    def test_sanitize_iso_timestamp(self) -> None:
        """Test ISO timestamp sanitization."""
        result = _sanitize_filename("2024-01-15T10:30:00.123456Z")
        assert ":" not in result
        assert "+" not in result


class TestCrashReport:
    """Tests for CrashReport model."""

    def test_default_values(self) -> None:
        """Test default values and auto-generation."""
        report = CrashReport()
        assert report.report_id != ""  # Auto-generated UUID
        assert report.created_at != ""  # Auto-generated timestamp
        assert report.crash_type == CrashType.UNCAUGHT_EXCEPTION
        assert report.severity == CrashSeverity.HIGH
        assert report.exception_type == ""
        assert report.exception_message == ""
        assert report.context == {}
        assert report.tags == []
        assert report.recovered is False

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        report = CrashReport(
            report_id="custom-report-id",
            created_at="2024-01-15T10:30:00Z",
            crash_type=CrashType.GPU_ERROR,
            severity=CrashSeverity.CRITICAL,
            exception_type="RuntimeError",
            exception_message="CUDA out of memory",
            exception_traceback="Traceback...",
            exception_module="torch",
            signal_number=11,
            signal_name="SIGSEGV",
            context={"gpu_memory": "10GB"},
            tags=["gpu", "oom"],
            user_message="Application crashed during processing",
            log_excerpts=["Line 1", "Line 2"],
            recovered=True,
            recovery_action="Restarted process",
        )
        assert report.report_id == "custom-report-id"
        assert report.crash_type == CrashType.GPU_ERROR
        assert report.severity == CrashSeverity.CRITICAL
        assert report.exception_type == "RuntimeError"
        assert report.signal_name == "SIGSEGV"
        assert report.recovered is True

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        report = CrashReport(
            report_id="test-id",
            crash_type=CrashType.MANUAL_REPORT,
            severity=CrashSeverity.MEDIUM,
            exception_message="Test error",
        )
        data = report.to_dict()
        assert data["report_id"] == "test-id"
        assert data["crash_type"] == "manual_report"
        assert data["severity"] == "medium"

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        report = CrashReport(
            report_id="json-test",
            exception_type="ValueError",
        )
        json_str = report.to_json()
        data = json.loads(json_str)
        assert data["report_id"] == "json-test"
        assert data["exception_type"] == "ValueError"

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        data = {
            "report_id": "loaded-report",
            "created_at": "2024-01-15T10:30:00Z",
            "crash_type": "signal_received",
            "severity": "high",
            "exception_type": "KeyboardInterrupt",
            "exception_message": "User cancelled",
            "exception_traceback": "",
            "exception_module": "builtins",
            "signal_number": 2,
            "signal_name": "SIGINT",
            "context": {"user_initiated": True},
            "tags": ["user"],
            "user_message": None,
            "system_state": None,
            "log_excerpts": [],
            "recovered": False,
            "recovery_action": None,
        }
        report = CrashReport.from_dict(data)
        assert report.report_id == "loaded-report"
        assert report.crash_type == CrashType.SIGNAL_RECEIVED
        assert report.signal_name == "SIGINT"

    def test_from_json(self) -> None:
        """Test from_json deserialization."""
        json_str = json.dumps(
            {
                "report_id": "json-loaded",
                "created_at": "2024-01-15T10:30:00Z",
                "crash_type": "uncaught_exception",
                "severity": "low",
                "exception_type": "",
                "exception_message": "",
                "exception_traceback": "",
                "exception_module": "",
                "context": {},
                "tags": [],
                "log_excerpts": [],
                "recovered": False,
            }
        )
        report = CrashReport.from_json(json_str)
        assert report.report_id == "json-loaded"

    def test_save_and_load(self) -> None:
        """Test save and load operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crash_dir = Path(tmpdir)
            report = CrashReport(
                crash_type=CrashType.PROCESSING_ERROR,
                exception_type="ProcessingError",
                exception_message="Frame extraction failed",
            )

            # Save
            filepath = report.save(crash_dir)
            assert filepath.exists()
            assert filepath.suffix == ".json"

            # Load
            loaded = CrashReport.load(filepath)
            assert loaded.report_id == report.report_id
            assert loaded.crash_type == CrashType.PROCESSING_ERROR
            assert loaded.exception_type == "ProcessingError"

    def test_save_creates_directory(self) -> None:
        """Test save creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crash_dir = Path(tmpdir) / "nested" / "crashes"
            report = CrashReport(report_id="dir-test")

            filepath = report.save(crash_dir)
            assert crash_dir.exists()
            assert filepath.exists()

    def test_get_summary(self) -> None:
        """Test get_summary creates correct summary."""
        report = CrashReport(
            report_id="summary-test",
            created_at="2024-01-15T10:30:00Z",
            crash_type=CrashType.UNCAUGHT_EXCEPTION,
            severity=CrashSeverity.HIGH,
            exception_type="ValueError",
            exception_message="This is a very long error message that should be truncated in the summary to prevent issues",
            recovered=True,
        )
        summary = report.get_summary()

        assert isinstance(summary, CrashReportSummary)
        assert summary.report_id == "summary-test"
        assert summary.created_at == "2024-01-15T10:30:00Z"
        assert summary.crash_type == CrashType.UNCAUGHT_EXCEPTION
        assert summary.severity == CrashSeverity.HIGH
        assert summary.exception_type == "ValueError"
        assert len(summary.exception_message) <= 200
        assert summary.recovered is True

    def test_with_system_state(self) -> None:
        """Test report with system state."""
        state = SystemState(
            timestamp="2024-01-15T10:30:00Z",
            platform_system="Linux",
            gpu=GPUInfo(available=True, device_name="RTX 3080"),
        )
        report = CrashReport(
            report_id="state-test",
            system_state=state,
        )

        assert report.system_state is not None
        assert report.system_state.platform_system == "Linux"
        assert report.system_state.gpu.device_name == "RTX 3080"

    def test_serialization_with_system_state(self) -> None:
        """Test serialization round-trip with system state."""
        state = SystemState(
            timestamp="2024-01-15T10:30:00Z",
            gpu=GPUInfo(available=True),
            memory=MemoryInfo(total_mb=16384.0),
            active_jobs=[ActiveJobInfo(job_id="job-1", status="running")],
        )
        report = CrashReport(
            report_id="serialize-test",
            system_state=state,
        )

        # Round-trip through JSON
        json_str = report.to_json()
        loaded = CrashReport.from_json(json_str)

        assert loaded.system_state is not None
        assert loaded.system_state.memory.total_mb == 16384.0
        assert len(loaded.system_state.active_jobs) == 1


class TestCrashReportSummary:
    """Tests for CrashReportSummary model."""

    def test_default_values(self) -> None:
        """Test required fields must be provided."""
        # Should fail without required fields
        with pytest.raises(TypeError):
            CrashReportSummary()

    def test_required_fields(self) -> None:
        """Test required fields are set."""
        summary = CrashReportSummary(
            report_id="summary-id",
            created_at="2024-01-15T10:30:00Z",
            crash_type=CrashType.UNCAUGHT_EXCEPTION,
            severity=CrashSeverity.HIGH,
            exception_type="RuntimeError",
            exception_message="Test error",
        )
        assert summary.report_id == "summary-id"
        assert summary.recovered is False  # Default

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        summary = CrashReportSummary(
            report_id="dict-test",
            created_at="2024-01-15T10:30:00Z",
            crash_type=CrashType.MANUAL_REPORT,
            severity=CrashSeverity.MEDIUM,
            exception_type="TestError",
            exception_message="Message",
            recovered=True,
        )
        data = summary.to_dict()
        assert data["report_id"] == "dict-test"
        assert data["crash_type"] == "manual_report"
        assert data["recovered"] is True


class TestCrashReportList:
    """Tests for CrashReportList model."""

    def test_default_values(self) -> None:
        """Test required fields must be provided."""
        with pytest.raises(TypeError):
            CrashReportList()

    def test_with_empty_list(self) -> None:
        """Test with empty list."""
        report_list = CrashReportList(reports=[], total_count=0)
        assert report_list.reports == []
        assert report_list.total_count == 0
        assert report_list.page == 1
        assert report_list.page_size == 20

    def test_with_reports(self) -> None:
        """Test with reports."""
        summary1 = CrashReportSummary(
            report_id="report-1",
            created_at="2024-01-15T10:30:00Z",
            crash_type=CrashType.UNCAUGHT_EXCEPTION,
            severity=CrashSeverity.HIGH,
            exception_type="Error1",
            exception_message="Message 1",
        )
        summary2 = CrashReportSummary(
            report_id="report-2",
            created_at="2024-01-15T11:00:00Z",
            crash_type=CrashType.SIGNAL_RECEIVED,
            severity=CrashSeverity.LOW,
            exception_type="",
            exception_message="",
        )
        report_list = CrashReportList(
            reports=[summary1, summary2],
            total_count=2,
            page=1,
            page_size=10,
        )
        assert len(report_list.reports) == 2
        assert report_list.total_count == 2
        assert report_list.page_size == 10

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        summary = CrashReportSummary(
            report_id="list-test",
            created_at="2024-01-15T10:30:00Z",
            crash_type=CrashType.MANUAL_REPORT,
            severity=CrashSeverity.MEDIUM,
            exception_type="Test",
            exception_message="Test",
        )
        report_list = CrashReportList(
            reports=[summary],
            total_count=1,
            page=1,
            page_size=20,
        )
        data = report_list.to_dict()
        assert data["total_count"] == 1
        assert len(data["reports"]) == 1
        assert data["page"] == 1


class TestModelEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_exception_message(self) -> None:
        """Test empty exception message is handled."""
        report = CrashReport(exception_message="")
        assert report.exception_message == ""

    def test_very_long_exception_message(self) -> None:
        """Test very long exception message is stored."""
        long_message = "x" * 10000
        report = CrashReport(exception_message=long_message)
        assert report.exception_message == long_message

    def test_unicode_in_exception_message(self) -> None:
        """Test unicode characters in exception message."""
        report = CrashReport(exception_message="Error: 文件不存在 🚨")
        assert "文件" in report.exception_message
        assert "🚨" in report.exception_message

    def test_multiline_traceback(self) -> None:
        """Test multiline traceback is preserved."""
        traceback_text = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    raise ValueError("test error")
ValueError: test error"""
        report = CrashReport(exception_traceback=traceback_text)
        assert "Traceback" in report.exception_traceback
        assert "ValueError" in report.exception_traceback

    def test_complex_context(self) -> None:
        """Test complex nested context."""
        context = {
            "nested": {"deep": {"value": 123}},
            "list": [1, 2, 3],
            "mixed": [{"a": 1}, {"b": 2}],
        }
        report = CrashReport(context=context)
        assert report.context["nested"]["deep"]["value"] == 123
        assert len(report.context["list"]) == 3
