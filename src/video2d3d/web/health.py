"""Health monitoring utilities for comprehensive system status checks.

This module provides functions for collecting system health metrics including:
- GPU status (availability, memory, utilization)
- System memory usage
- Queue health and statistics
- Overall health determination
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from video2d3d.utils.gpu import get_all_gpu_info, get_device_count, is_cuda_available
from video2d3d.utils.logger import get_logger
from video2d3d.web.schemas import (
    ComprehensiveHealthResponse,
    GPUStatusResponse,
    HealthStatus,
    QueueHealthResponse,
    SystemMemoryResponse,
)

if TYPE_CHECKING:
    from video2d3d.batch import BatchVideoQueue

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore[assignment]

logger = get_logger("web.health")

# Memory thresholds for health status
MEMORY_WARNING_THRESHOLD = 85.0  # Percent
MEMORY_CRITICAL_THRESHOLD = 95.0  # Percent

# GPU memory thresholds
GPU_MEMORY_WARNING_THRESHOLD = 90.0  # Percent
GPU_MEMORY_CRITICAL_THRESHOLD = 98.0  # Percent

# Conversion constant
BYTES_TO_MB = 1024 * 1024


def get_system_memory() -> SystemMemoryResponse:
    """Get current system memory usage.

    Returns:
        SystemMemoryResponse with memory statistics.
    """
    if psutil is None:
        logger.debug("psutil not available, returning default memory stats")
        return SystemMemoryResponse(
            total_mb=0.0,
            available_mb=0.0,
            used_mb=0.0,
            utilization_percent=0.0,
        )
    try:
        memory = psutil.virtual_memory()
        total_mb = memory.total / BYTES_TO_MB
        available_mb = memory.available / BYTES_TO_MB
        used_mb = memory.used / BYTES_TO_MB
        utilization = memory.percent
        return SystemMemoryResponse(
            total_mb=round(total_mb, 2),
            available_mb=round(available_mb, 2),
            used_mb=round(used_mb, 2),
            utilization_percent=round(utilization, 2),
        )
    except Exception as e:
        logger.warning(f"Failed to get system memory: {e}")
        return SystemMemoryResponse(
            total_mb=0.0,
            available_mb=0.0,
            used_mb=0.0,
            utilization_percent=0.0,
        )


def get_gpu_status() -> GPUStatusResponse:
    """Get current GPU status and memory usage.

    Returns:
        GPUStatusResponse with GPU statistics.
    """
    try:
        if not is_cuda_available():
            return GPUStatusResponse(
                available=False,
                device_count=0,
            )

        device_count = get_device_count()
        if device_count == 0:
            return GPUStatusResponse(
                available=False,
                device_count=0,
            )

        # Get info for the first GPU (primary)
        gpu_infos = get_all_gpu_info()
        if not gpu_infos:
            return GPUStatusResponse(
                available=True,
                device_count=device_count,
            )

        primary_gpu = gpu_infos[0]

        return GPUStatusResponse(
            available=True,
            device_name=primary_gpu.name,
            device_count=device_count,
            memory_used_mb=round(primary_gpu.used_memory_mb, 2),
            memory_free_mb=round(primary_gpu.free_memory_mb, 2),
            memory_total_mb=round(primary_gpu.total_memory_mb, 2),
            memory_utilization_percent=round(primary_gpu.memory_utilization, 2),
            compute_capability=f"{primary_gpu.compute_capability[0]}.{primary_gpu.compute_capability[1]}",
        )

    except Exception as e:
        logger.warning(f"Failed to get GPU status: {e}")
        return GPUStatusResponse(
            available=False,
            device_count=0,
        )


def get_queue_health(queue: BatchVideoQueue | None) -> QueueHealthResponse:
    """Get queue health and statistics.

    Args:
        queue: The batch video queue instance.

    Returns:
        QueueHealthResponse with queue statistics.
    """
    if queue is None:
        return QueueHealthResponse(
            running=False,
            paused=False,
        )

    try:
        stats = queue.get_stats()
        queue_depth = stats.pending_jobs + stats.running_jobs

        return QueueHealthResponse(
            running=queue.is_running,
            paused=queue.is_paused,
            total_jobs=stats.total_jobs,
            pending_jobs=stats.pending_jobs,
            running_jobs=stats.running_jobs,
            completed_jobs=stats.completed_jobs,
            failed_jobs=stats.failed_jobs,
            queue_depth=queue_depth,
            success_rate_percent=round(stats.success_rate, 2),
        )

    except Exception as e:
        logger.warning(f"Failed to get queue health: {e}")
        return QueueHealthResponse(
            running=False,
            paused=False,
        )


def determine_health_status(
    gpu_status: GPUStatusResponse,
    memory_status: SystemMemoryResponse,
    queue_status: QueueHealthResponse,
) -> tuple[HealthStatus, dict[str, bool]]:
    """Determine overall health status based on component status.

    Args:
        gpu_status: GPU status information.
        memory_status: System memory status.
        queue_status: Queue health status.

    Returns:
        Tuple of (overall health status, individual check results).
    """
    checks: dict[str, bool] = {}

    # Check queue health
    queue_healthy = queue_status.running
    checks["queue"] = queue_healthy

    # Check memory health (if psutil is available)
    memory_healthy = True
    if memory_status.total_mb > 0:
        memory_healthy = memory_status.utilization_percent < MEMORY_CRITICAL_THRESHOLD
        checks["memory"] = memory_healthy
    else:
        checks["memory"] = True  # Unknown, assume OK

    # Check GPU health (if available)
    gpu_healthy = True
    if gpu_status.available:
        gpu_healthy = gpu_status.memory_utilization_percent < GPU_MEMORY_CRITICAL_THRESHOLD
        checks["gpu"] = gpu_healthy
    else:
        checks["gpu"] = True  # GPU not required, consider OK

    # Determine overall status
    all_healthy = all(checks.values())

    if all_healthy:
        # Check for degraded states
        degraded = False

        if (
            memory_status.total_mb > 0
            and memory_status.utilization_percent >= MEMORY_WARNING_THRESHOLD
        ):
            degraded = True

        if (
            gpu_status.available
            and gpu_status.memory_utilization_percent >= GPU_MEMORY_WARNING_THRESHOLD
        ):
            degraded = True

        if degraded:
            return HealthStatus.DEGRADED, checks

        return HealthStatus.HEALTHY, checks

    return HealthStatus.UNHEALTHY, checks


def get_comprehensive_health(
    queue: BatchVideoQueue | None,
    version: str,
    uptime_seconds: float,
) -> ComprehensiveHealthResponse:
    """Get comprehensive health status of the system.

    This is the main entry point for collecting all health metrics.

    Args:
        queue: The batch video queue instance.
        version: Application version string.
        uptime_seconds: Application uptime in seconds.

    Returns:
        ComprehensiveHealthResponse with all health metrics.
    """
    gpu_status = get_gpu_status()
    memory_status = get_system_memory()
    queue_status = get_queue_health(queue)

    overall_status, checks = determine_health_status(
        gpu_status=gpu_status,
        memory_status=memory_status,
        queue_status=queue_status,
    )

    return ComprehensiveHealthResponse(
        status=overall_status,
        version=version,
        uptime_seconds=uptime_seconds,
        timestamp=datetime.utcnow(),
        gpu=gpu_status,
        memory=memory_status,
        queue=queue_status,
        checks=checks,
    )


__all__ = [
    "get_system_memory",
    "get_gpu_status",
    "get_queue_health",
    "determine_health_status",
    "get_comprehensive_health",
    "MEMORY_WARNING_THRESHOLD",
    "MEMORY_CRITICAL_THRESHOLD",
    "GPU_MEMORY_WARNING_THRESHOLD",
    "GPU_MEMORY_CRITICAL_THRESHOLD",
    "BYTES_TO_MB",
]
