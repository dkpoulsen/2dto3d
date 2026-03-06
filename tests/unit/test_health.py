"""Unit tests for health monitoring module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.web.health import (
    GPU_MEMORY_CRITICAL_THRESHOLD,
    GPU_MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD,
    MEMORY_WARNING_THRESHOLD,
    determine_health_status,
    get_comprehensive_health,
    get_gpu_status,
    get_queue_health,
    get_system_memory,
)
from video2d3d.web.schemas import (
    GPUStatusResponse,
    HealthStatus,
    QueueHealthResponse,
    SystemMemoryResponse,
)


class TestGetSystemMemory:
    """Tests for get_system_memory function."""

    def test_get_system_memory_with_psutil(self) -> None:
        """Test system memory retrieval with psutil available."""
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16 GB
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_memory.used = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_memory.percent = 50.0

        with patch("video2d3d.web.health.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = mock_memory
            result = get_system_memory()

            assert isinstance(result, SystemMemoryResponse)
            assert result.total_mb > 0
            assert result.utilization_percent == 50.0

    def test_get_system_memory_without_psutil(self) -> None:
        """Test system memory retrieval when psutil is not available."""
        with patch("video2d3d.web.health.psutil", side_effect=ImportError):
            result = get_system_memory()

            assert isinstance(result, SystemMemoryResponse)
            assert result.total_mb == 0.0
            assert result.utilization_percent == 0.0


class TestGetGPUStatus:
    """Tests for get_gpu_status function."""

    def test_get_gpu_status_no_cuda(self) -> None:
        """Test GPU status when CUDA is not available."""
        with patch("video2d3d.web.health.is_cuda_available", return_value=False):
            result = get_gpu_status()

            assert isinstance(result, GPUStatusResponse)
            assert result.available is False
            assert result.device_count == 0

    def test_get_gpu_status_with_cuda(self) -> None:
        """Test GPU status with CUDA available."""
        mock_gpu_info = MagicMock()
        mock_gpu_info.name = "NVIDIA RTX 3090"
        mock_gpu_info.used_memory_mb = 5000.0
        mock_gpu_info.free_memory_mb = 19000.0
        mock_gpu_info.total_memory_mb = 24000.0
        mock_gpu_info.memory_utilization = 20.83
        mock_gpu_info.compute_capability = (8, 6)

        with (
            patch("video2d3d.web.health.is_cuda_available", return_value=True),
            patch("video2d3d.web.health.get_device_count", return_value=1),
            patch("video2d3d.web.health.get_all_gpu_info", return_value=[mock_gpu_info]),
        ):
            result = get_gpu_status()

            assert isinstance(result, GPUStatusResponse)
            assert result.available is True
            assert result.device_count == 1
            assert result.device_name == "NVIDIA RTX 3090"
            assert result.compute_capability == "8.6"

    def test_get_gpu_status_cuda_no_devices(self) -> None:
        """Test GPU status when CUDA available but no devices."""
        with (
            patch("video2d3d.web.health.is_cuda_available", return_value=True),
            patch("video2d3d.web.health.get_device_count", return_value=0),
        ):
            result = get_gpu_status()

            assert isinstance(result, GPUStatusResponse)
            assert result.available is False
            assert result.device_count == 0

    def test_get_gpu_status_cuda_empty_info_list(self) -> None:
        """Test GPU status when CUDA available but info list is empty."""
        with (
            patch("video2d3d.web.health.is_cuda_available", return_value=True),
            patch("video2d3d.web.health.get_device_count", return_value=1),
            patch("video2d3d.web.health.get_all_gpu_info", return_value=[]),
        ):
            result = get_gpu_status()

            assert isinstance(result, GPUStatusResponse)
            assert result.available is True
            assert result.device_count == 1
            assert result.device_name is None  # No device info available

    def test_get_gpu_status_exception_handling(self) -> None:
        """Test GPU status handles exceptions gracefully."""
        with patch(
            "video2d3d.web.health.is_cuda_available",
            side_effect=RuntimeError("CUDA error"),
        ):
            result = get_gpu_status()

            assert isinstance(result, GPUStatusResponse)
            assert result.device_count == 0


class TestGetQueueHealth:
    """Tests for get_queue_health function."""

    def test_get_queue_health_no_queue(self) -> None:
        """Test queue health when queue is None."""
        result = get_queue_health(None)

        assert isinstance(result, QueueHealthResponse)
        assert result.running is False
        assert result.paused is False
    def test_get_queue_health_running(self) -> None:
        """Test queue health when queue is running."""
        mock_queue = MagicMock()
        mock_queue.is_running = True
        mock_queue.is_paused = False
        mock_stats = MagicMock()
        mock_stats.total_jobs = 10
        mock_stats.pending_jobs = 3
        mock_stats.running_jobs = 2
        mock_stats.completed_jobs = 4
        mock_stats.failed_jobs = 1
        mock_stats.success_rate = 80.0
        mock_queue.get_stats.return_value = mock_stats

        result = get_queue_health(mock_queue)

        assert isinstance(result, QueueHealthResponse)
        assert result.running is True
        assert result.paused is False
        assert result.total_jobs == 10
        assert result.pending_jobs == 3
        assert result.running_jobs == 2
        assert result.completed_jobs == 4
        assert result.failed_jobs == 1
        assert result.queue_depth == 5  # pending + running
        assert result.success_rate_percent == 80.0


class TestDetermineHealthStatus:
    """Tests for determine_health_status function."""

    def test_healthy_status(self) -> None:
        """Test healthy status when all components are healthy."""
        gpu_status = GPUStatusResponse(
            available=True,
            memory_utilization_percent=50.0,
        )
        memory_status = SystemMemoryResponse(
            total_mb=16000.0,
            available_mb=8000.0,
            used_mb=8000.0,
            utilization_percent=50.0,
        )
        queue_status = QueueHealthResponse(running=True)

        status, checks = determine_health_status(gpu_status, memory_status, queue_status)

        assert status == HealthStatus.HEALTHY
        assert all(checks.values()) is True

    def test_degraded_status_high_memory(self) -> None:
        """Test degraded status when memory utilization is high."""
        gpu_status = GPUStatusResponse(available=False)
        memory_status = SystemMemoryResponse(
            total_mb=16000.0,
            available_mb=2000.0,
            used_mb=14000.0,
            utilization_percent=90.0,  # Above warning threshold
        )
        queue_status = QueueHealthResponse(running=True)

        status, checks = determine_health_status(gpu_status, memory_status, queue_status)

        assert status == HealthStatus.DEGRADED
        assert checks["memory"] is True  # Still OK, just degraded

    def test_unhealthy_status_queue_down(self) -> None:
        """Test unhealthy status when queue is not running."""
        gpu_status = GPUStatusResponse(available=False)
        memory_status = SystemMemoryResponse(
            total_mb=16000.0,
            available_mb=8000.0,
            used_mb=8000.0,
            utilization_percent=50.0,
        )
        queue_status = QueueHealthResponse(running=False)

        status, checks = determine_health_status(gpu_status, memory_status, queue_status)

        assert status == HealthStatus.UNHEALTHY
        assert checks["queue"] is False

    def test_unhealthy_status_critical_memory(self) -> None:
        """Test unhealthy status when memory is critically high."""
        gpu_status = GPUStatusResponse(available=False)
        memory_status = SystemMemoryResponse(
            total_mb=16000.0,
            available_mb=500.0,
            used_mb=15500.0,
            utilization_percent=97.0,  # Above critical threshold
        )
        queue_status = QueueHealthResponse(running=True)

        status, checks = determine_health_status(gpu_status, memory_status, queue_status)

        assert status == HealthStatus.UNHEALTHY
        assert checks["memory"] is False

    def test_unhealthy_status_critical_gpu_memory(self) -> None:
        """Test unhealthy status when GPU memory is critically high."""
        gpu_status = GPUStatusResponse(
            available=True,
            memory_utilization_percent=99.0,  # Above critical threshold
        )
        memory_status = SystemMemoryResponse(
            total_mb=16000.0,
            available_mb=8000.0,
            used_mb=8000.0,
            utilization_percent=50.0,
        )
        queue_status = QueueHealthResponse(running=True)

        status, checks = determine_health_status(gpu_status, memory_status, queue_status)

        assert status == HealthStatus.UNHEALTHY
        assert checks["gpu"] is False

    def test_degraded_status_gpu_memory_warning(self) -> None:
        """Test degraded status when GPU memory is at warning level."""
        gpu_status = GPUStatusResponse(
            available=True,
            memory_utilization_percent=92.0,  # Above warning, below critical
        )
        memory_status = SystemMemoryResponse(
            total_mb=16000.0,
            available_mb=8000.0,
            used_mb=8000.0,
            utilization_percent=50.0,
        )
        queue_status = QueueHealthResponse(running=True)

        status, checks = determine_health_status(gpu_status, memory_status, queue_status)

        assert status == HealthStatus.DEGRADED
        assert checks["gpu"] is True  # Still OK, just degraded


class TestGetComprehensiveHealth:
    """Tests for get_comprehensive_health function."""

    def test_comprehensive_health_structure(self) -> None:
        """Test that comprehensive health returns correct structure."""
        mock_queue = MagicMock()
        mock_queue.is_running = True
        mock_queue.is_paused = False
        mock_stats = MagicMock()
        mock_stats.total_jobs = 5
        mock_stats.pending_jobs = 2
        mock_stats.running_jobs = 1
        mock_stats.completed_jobs = 2
        mock_stats.failed_jobs = 0
        mock_stats.success_rate = 100.0
        mock_queue.get_stats.return_value = mock_stats

        with patch("video2d3d.web.health.is_cuda_available", return_value=False):
            result = get_comprehensive_health(
                queue=mock_queue,
                version="0.1.0",
                uptime_seconds=3600.0,
            )

        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert result.version == "0.1.0"
        assert result.uptime_seconds == 3600.0
        assert isinstance(result.timestamp, datetime)
        assert isinstance(result.gpu, GPUStatusResponse)
        assert isinstance(result.memory, SystemMemoryResponse)
        assert isinstance(result.queue, QueueHealthResponse)
        assert isinstance(result.checks, dict)

    def test_comprehensive_health_no_queue(self) -> None:
        """Test comprehensive health when queue is None."""
        with patch("video2d3d.web.health.is_cuda_available", return_value=False):
            result = get_comprehensive_health(
                queue=None,
                version="0.1.0",
                uptime_seconds=100.0,
            )

        assert result.queue.running is False
        assert result.status == HealthStatus.UNHEALTHY  # Queue not running
        assert result.checks["queue"] is False
