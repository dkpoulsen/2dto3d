"""Unit tests for crash system state capture.

Tests cover:
- GPU information capture
- System memory information capture
- Process information capture
- Active job information extraction
- Queue statistics extraction
- Full system state capture integration
"""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock, patch

from video2d3d.crash.models import GPUInfo, MemoryInfo, ProcessInfo, SystemState
from video2d3d.crash.state_capture import (
    capture_system_state,
    get_active_jobs,
    get_gpu_info,
    get_memory_info,
    get_process_info,
    get_queue_stats,
    set_app_start_time,
)


class TestGetGPUInfo:
    """Tests for GPU information capture."""

    def test_no_torch_available(self) -> None:
        """Test GPU info when torch is not available."""
        with patch.dict("sys.modules", {"torch": None}):
            gpu = get_gpu_info()
            assert gpu.available is False
            assert gpu.device_count == 0

    def test_torch_cuda_not_available(self) -> None:
        """Test GPU info when CUDA is not available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            gpu = get_gpu_info()
            assert gpu.available is False

    def test_cuda_available_single_gpu(self) -> None:
        """Test GPU info with single GPU available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.cuda.current_device.return_value = 0

        # Mock device properties
        mock_props = MagicMock()
        mock_props.name = "NVIDIA RTX 3080"
        mock_props.major = 8
        mock_props.minor = 6
        mock_props.total_memory = 10 * 1024 * 1024 * 1024  # 10GB
        mock_torch.cuda.get_device_properties.return_value = mock_props

        # Mock memory functions
        mock_torch.cuda.memory_allocated.return_value = 5 * 1024 * 1024 * 1024  # 5GB
        mock_torch.cuda.memory_reserved.return_value = 6 * 1024 * 1024 * 1024  # 6GB

        with patch.dict("sys.modules", {"torch": mock_torch}):
            gpu = get_gpu_info()

            assert gpu.available is True
            assert gpu.device_count == 1
            assert gpu.device_name == "NVIDIA RTX 3080"
            assert gpu.compute_capability == "8.6"
            assert gpu.memory_total_mb > 0
            assert gpu.memory_used_mb > 0

    def test_cuda_exception_handling(self) -> None:
        """Test GPU info handles exceptions gracefully."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.side_effect = RuntimeError("CUDA error")

        with patch.dict("sys.modules", {"torch": mock_torch}):
            # Should not raise, should return default
            gpu = get_gpu_info()
            assert isinstance(gpu, GPUInfo)

    def test_multiple_gpus(self) -> None:
        """Test GPU info with multiple GPUs."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2
        mock_torch.cuda.current_device.return_value = 0

        mock_props = MagicMock()
        mock_props.name = "NVIDIA RTX 3090"
        mock_props.major = 8
        mock_props.minor = 6
        mock_props.total_memory = 24 * 1024 * 1024 * 1024
        mock_torch.cuda.get_device_properties.return_value = mock_props

        with patch.dict("sys.modules", {"torch": mock_torch}):
            gpu = get_gpu_info()
            assert gpu.device_count == 2


class TestGetMemoryInfo:
    """Tests for system memory information capture."""

    def test_with_psutil(self) -> None:
        """Test memory info with psutil available."""
        mock_psutil = MagicMock()
        mock_mem = MagicMock()
        mock_mem.total = 32 * 1024 * 1024 * 1024  # 32GB
        mock_mem.available = 8 * 1024 * 1024 * 1024  # 8GB
        mock_mem.used = 24 * 1024 * 1024 * 1024  # 24GB
        mock_mem.percent = 75.0
        mock_psutil.virtual_memory.return_value = mock_mem

        mock_swap = MagicMock()
        mock_swap.total = 8 * 1024 * 1024 * 1024
        mock_swap.used = 2 * 1024 * 1024 * 1024
        mock_psutil.swap_memory.return_value = mock_swap

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            mem = get_memory_info()

            assert mem.total_mb > 0
            assert mem.available_mb > 0
            assert mem.used_mb > 0
            assert mem.utilization_percent == 75.0

    def test_without_psutil_linux(self) -> None:
        """Test memory info fallback without psutil on Linux."""
        with patch("video2d3d.crash.state_capture.psutil", None):
            with patch("platform.system", return_value="Linux"):
                with patch("builtins.open", create=True) as mock_open:
                    mock_file = MagicMock()
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=False)
                    mock_file.__iter__ = MagicMock(
                        return_value=iter(
                            [
                                "MemTotal:       32768 kB",
                                "MemFree:          1024 kB",
                                "MemAvailable:     8192 kB",
                                "SwapTotal:       8192 kB",
                                "SwapFree:        6144 kB",
                            ]
                        )
                    )
                    mock_open.return_value = mock_file

                    mem = get_memory_info()
                    # Should have read from /proc/meminfo
                    assert isinstance(mem, MemoryInfo)

    def test_exception_handling(self) -> None:
        """Test memory info handles exceptions gracefully."""
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.side_effect = RuntimeError("Access denied")

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            mem = get_memory_info()
            assert isinstance(mem, MemoryInfo)


class TestGetProcessInfo:
    """Tests for process information capture."""

    def test_with_psutil(self) -> None:
        """Test process info with psutil available."""
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.ppid.return_value = 1000
        mock_process.cmdline.return_value = ["python", "-m", "video2d3d", "serve"]
        mock_process.cwd.return_value = "/app"
        mock_process.cpu_percent.return_value = 45.5

        mock_mem_info = MagicMock()
        mock_mem_info.rss = 2 * 1024 * 1024 * 1024  # 2GB
        mock_mem_info.vms = 4 * 1024 * 1024 * 1024  # 4GB
        mock_process.memory_info.return_value = mock_mem_info

        mock_process.num_threads.return_value = 8
        mock_process.create_time.return_value = time.time() - 3600  # Started 1 hour ago

        mock_process.oneshot.return_value.__enter__ = MagicMock(return_value=None)
        mock_process.oneshot.return_value.__exit__ = MagicMock(return_value=None)

        mock_psutil.Process.return_value = mock_process

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            proc = get_process_info()

            assert proc.pid == 12345
            assert proc.parent_pid == 1000
            assert proc.cpu_percent == 45.5
            assert proc.num_threads == 8
            assert proc.uptime_seconds >= 3600

    def test_without_psutil(self) -> None:
        """Test process info fallback without psutil."""
        with patch("video2d3d.crash.state_capture.psutil", None):
            proc = get_process_info()

            assert proc.pid == os.getpid()
            assert proc.uptime_seconds >= 0

    def test_process_info_exception(self) -> None:
        """Test process info handles exceptions."""
        mock_psutil = MagicMock()
        mock_psutil.Process.side_effect = RuntimeError("Access denied")

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            proc = get_process_info()
            assert isinstance(proc, ProcessInfo)
            assert proc.pid == os.getpid()

    def test_num_fds_unavailable(self) -> None:
        """Test num_fds handling when not available."""
        mock_psutil = MagicMock()
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.cmdline.return_value = []
        mock_process.cwd.return_value = "/app"
        mock_process.cpu_percent.return_value = 0.0
        mock_process.memory_info.return_value = MagicMock(rss=0, vms=0)
        mock_process.num_threads.return_value = 1
        mock_process.create_time.return_value = time.time()
        mock_process.num_fds.side_effect = AttributeError("Not available")

        mock_process.oneshot.return_value.__enter__ = MagicMock(return_value=None)
        mock_process.oneshot.return_value.__exit__ = MagicMock(return_value=None)

        mock_psutil.Process.return_value = mock_process
        mock_psutil.AccessDenied = PermissionError

        with patch.dict("sys.modules", {"psutil": mock_psutil}):
            proc = get_process_info()
            assert proc.num_file_descriptors is None


class TestGetActiveJobs:
    """Tests for active job information extraction."""

    def test_no_queue(self) -> None:
        """Test active jobs when no queue is available."""
        jobs = get_active_jobs(None)
        assert jobs == []

    def test_empty_queue(self) -> None:
        """Test active jobs with empty queue."""
        mock_queue = MagicMock()
        mock_queue.list_jobs.return_value = []

        jobs = get_active_jobs(mock_queue)
        assert jobs == []

    def test_active_jobs_only(self) -> None:
        """Test only active jobs are included."""
        # Create mock jobs
        mock_job_running = MagicMock()
        mock_job_running.job_id = "job-running"
        mock_job_running.status = "running"
        mock_job_running.input_path = "/input/video.mp4"
        mock_job_running.output_path = "/output/video_3d.mp4"
        mock_job_running.started_at = MagicMock()
        mock_job_running.started_at.isoformat.return_value = "2024-01-15T10:30:00Z"
        mock_job_running.progress = 50.0
        mock_job_running.current_stage = "depth_estimation"
        mock_job_running.frames_processed = 500
        mock_job_running.total_frames = 1000

        mock_job_completed = MagicMock()
        mock_job_completed.job_id = "job-completed"
        mock_job_completed.status = "completed"

        mock_job_pending = MagicMock()
        mock_job_pending.job_id = "job-pending"
        mock_job_pending.status = "pending"
        mock_job_pending.input_path = None
        mock_job_pending.output_path = None
        mock_job_pending.started_at = None
        mock_job_pending.progress = None
        mock_job_pending.current_stage = None
        mock_job_pending.frames_processed = None
        mock_job_pending.total_frames = None

        mock_queue = MagicMock()
        mock_queue.list_jobs.return_value = [mock_job_running, mock_job_completed, mock_job_pending]

        jobs = get_active_jobs(mock_queue)

        # Only running and pending should be included
        assert len(jobs) == 2
        job_ids = [j.job_id for j in jobs]
        assert "job-running" in job_ids
        assert "job-pending" in job_ids
        assert "job-completed" not in job_ids

    def test_exception_handling(self) -> None:
        """Test active jobs handles exceptions."""
        mock_queue = MagicMock()
        mock_queue.list_jobs.side_effect = RuntimeError("Queue error")

        jobs = get_active_jobs(mock_queue)
        assert jobs == []


class TestGetQueueStats:
    """Tests for queue statistics extraction."""

    def test_no_queue(self) -> None:
        """Test queue stats when no queue is available."""
        stats = get_queue_stats(None)
        assert stats == {}

    def test_queue_with_stats(self) -> None:
        """Test queue stats extraction."""
        mock_stats = MagicMock()
        mock_stats.to_dict.return_value = {
            "total_jobs": 100,
            "pending_jobs": 10,
            "running_jobs": 5,
            "completed_jobs": 80,
            "failed_jobs": 5,
        }

        mock_queue = MagicMock()
        mock_queue.get_stats.return_value = mock_stats

        stats = get_queue_stats(mock_queue)

        assert stats["total_jobs"] == 100
        assert stats["pending_jobs"] == 10

    def test_queue_without_to_dict(self) -> None:
        """Test queue stats when stats object has no to_dict."""
        mock_stats = MagicMock(spec=[])  # No to_dict method
        mock_queue = MagicMock()
        mock_queue.get_stats.return_value = mock_stats

        stats = get_queue_stats(mock_queue)
        assert stats == {}

    def test_exception_handling(self) -> None:
        """Test queue stats handles exceptions."""
        mock_queue = MagicMock()
        mock_queue.get_stats.side_effect = RuntimeError("Stats error")

        stats = get_queue_stats(mock_queue)
        assert stats == {}


class TestCaptureSystemState:
    """Tests for full system state capture."""

    def test_basic_capture(self) -> None:
        """Test basic system state capture."""
        state = capture_system_state()

        assert isinstance(state, SystemState)
        assert state.timestamp != ""
        assert state.platform_system != ""
        assert state.platform_python_version != ""
        assert isinstance(state.gpu, GPUInfo)
        assert isinstance(state.memory, MemoryInfo)
        assert isinstance(state.process, ProcessInfo)

    def test_capture_with_queue(self) -> None:
        """Test system state capture with queue."""
        mock_queue = MagicMock()
        mock_queue.list_jobs.return_value = []
        mock_queue.get_stats.return_value = MagicMock(to_dict=lambda: {"total": 0})

        state = capture_system_state(queue=mock_queue)

        assert isinstance(state, SystemState)
        assert state.active_jobs == []
        assert state.queue_stats == {}

    def test_capture_with_app_info(self) -> None:
        """Test system state capture with application info."""
        state = capture_system_state(
            app_version="1.0.0",
            app_config={"debug": False, "max_workers": 4},
        )

        assert state.app_version == "1.0.0"
        assert state.app_config["debug"] is False
        assert state.app_config["max_workers"] == 4

    def test_uptime_calculation(self) -> None:
        """Test uptime is calculated correctly."""
        start_time = time.time() - 7200  # Started 2 hours ago

        state = capture_system_state(app_start_time=start_time)

        assert state.uptime_seconds >= 7200
        assert state.uptime_seconds < 7210  # Allow some tolerance

    def test_set_app_start_time(self) -> None:
        """Test set_app_start_time function."""
        new_start = 1000.0
        set_app_start_time(new_start)

        # Capture should use the new start time
        state = capture_system_state()
        assert state.uptime_seconds > 0

    def test_all_platform_info_captured(self) -> None:
        """Test all platform information is captured."""
        state = capture_system_state()

        assert state.platform_system != ""
        assert state.platform_node != ""
        assert state.platform_release != ""
        assert state.platform_machine != ""
        assert state.platform_python_version != ""


class TestIntegration:
    """Integration tests for state capture."""

    def test_full_capture_no_mocks(self) -> None:
        """Test full capture without mocks (where possible)."""
        state = capture_system_state(
            app_version="test-1.0.0",
            app_config={"test": True},
        )

        # Verify basic structure
        assert state.timestamp != ""
        assert state.uptime_seconds >= 0
        assert state.app_version == "test-1.0.0"

        # Verify process info
        assert state.process.pid == os.getpid()

        # Verify can be serialized
        data = state.to_dict()
        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "gpu" in data
        assert "memory" in data
        assert "process" in data

    def test_state_serialization_roundtrip(self) -> None:
        """Test state can be serialized and deserialized."""
        state = capture_system_state(
            app_version="1.0.0",
            app_config={"key": "value"},
        )

        # Serialize
        data = state.to_dict()

        # Deserialize
        loaded = SystemState.from_dict(data)

        assert loaded.timestamp == state.timestamp
        assert loaded.platform_system == state.platform_system
        assert loaded.app_version == "1.0.0"
        assert loaded.app_config["key"] == "value"
