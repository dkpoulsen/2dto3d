"""System state capture utilities for crash reporting.

This module provides functions to capture various aspects of system state:
- GPU information (memory, utilization, temperature)
- System memory information
- Process information (CPU, memory, file descriptors)
- Active job information from the batch queue
"""

from __future__ import annotations

import contextlib
import os
import platform
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import psutil

from video2d3d.crash.models import ActiveJobInfo, GPUInfo, MemoryInfo, ProcessInfo, SystemState

if TYPE_CHECKING:
    from video2d3d.batch import BatchVideoQueue

# Application start time for uptime calculation
_app_start_time: float = time.time()


def get_gpu_info() -> GPUInfo:
    """Capture current GPU state.

    Returns:
        GPUInfo with current GPU state.
    """
    gpu_info = GPUInfo(available=False)

    try:
        import torch

        if torch.cuda.is_available():
            gpu_info.available = True
            gpu_info.device_count = torch.cuda.device_count()

            # Get primary device info
            if gpu_info.device_count > 0:
                device = torch.cuda.current_device()
                props = torch.cuda.get_device_properties(device)
                gpu_info.device_name = props.name
                gpu_info.compute_capability = f"{props.major}.{props.minor}"
                gpu_info.memory_total_mb = props.total_memory / (1024 * 1024)

                # Memory usage
                memory_allocated = torch.cuda.memory_allocated(device)
                memory_reserved = torch.cuda.memory_reserved(device)
                gpu_info.memory_used_mb = memory_allocated / (1024 * 1024)
                gpu_info.memory_free_mb = gpu_info.memory_total_mb - memory_reserved / (1024 * 1024)

                if gpu_info.memory_total_mb > 0:
                    gpu_info.memory_utilization_percent = (
                        gpu_info.memory_used_mb / gpu_info.memory_total_mb * 100
                    )

    except ImportError:
        pass
    except Exception:
        # Don't fail crash reporting if GPU info capture fails
        pass

    return gpu_info


def get_memory_info() -> MemoryInfo:
    """Capture current system memory state.

    Returns:
        MemoryInfo with current memory state.
    """
    memory_info = MemoryInfo()

    try:
        import psutil

        mem = psutil.virtual_memory()
        memory_info.total_mb = mem.total / (1024 * 1024)
        memory_info.available_mb = mem.available / (1024 * 1024)
        memory_info.used_mb = mem.used / (1024 * 1024)
        memory_info.utilization_percent = mem.percent

        # Swap
        swap = psutil.swap_memory()
        memory_info.swap_total_mb = swap.total / (1024 * 1024)
        memory_info.swap_used_mb = swap.used / (1024 * 1024)
        if swap.total > 0:
            memory_info.swap_utilization_percent = (swap.used / swap.total) * 100

    except Exception:
        # Fallback to /proc/meminfo on Linux (also covers psutil failures)
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip().split()[0]
                            meminfo[key] = int(value) * 1024  # Convert from KB to bytes

                    memory_info.total_mb = meminfo.get("MemTotal", 0) / (1024 * 1024)
                    memory_info.available_mb = meminfo.get("MemAvailable", 0) / (1024 * 1024)
                    memory_info.used_mb = memory_info.total_mb - memory_info.available_mb
                    if memory_info.total_mb > 0:
                        memory_info.utilization_percent = (
                            memory_info.used_mb / memory_info.total_mb * 100
                        )

                    memory_info.swap_total_mb = meminfo.get("SwapTotal", 0) / (1024 * 1024)
                    memory_info.swap_used_mb = memory_info.swap_total_mb - meminfo.get(
                        "SwapFree", 0
                    ) / (1024 * 1024)
        except Exception:
            pass

    return memory_info


def get_process_info() -> ProcessInfo:
    """Capture current process state.

    Returns:
        ProcessInfo with current process state.
    """
    process_info = ProcessInfo()

    try:
        import psutil

        process = psutil.Process(os.getpid())
        process_info.pid = process.pid
        process_info.parent_pid = process.ppid()
        process_info.command_line = " ".join(process.cmdline())
        process_info.working_directory = process.cwd()

        with process.oneshot():
            # CPU and memory
            process_info.cpu_percent = process.cpu_percent(interval=None)  # Non-blocking
            mem_info = process.memory_info()
            process_info.memory_rss_mb = mem_info.rss / (1024 * 1024)
            process_info.memory_vms_mb = mem_info.vms / (1024 * 1024)

            # Threads and file descriptors
            process_info.num_threads = process.num_threads()
            with contextlib.suppress(AttributeError, psutil.AccessDenied):
                process_info.num_file_descriptors = process.num_fds()

            # Uptime
            create_time = process.create_time()
            process_info.uptime_seconds = time.time() - create_time

    except Exception:
        # Fallback for basic info (import failure, access denied, etc.)
        process_info.pid = os.getpid()
        process_info.uptime_seconds = time.time() - _app_start_time
        process_info.working_directory = os.getcwd()

    return process_info


def get_active_jobs(queue: BatchVideoQueue | None) -> list[ActiveJobInfo]:
    """Get information about active jobs in the queue.

    Args:
        queue: The batch video queue instance.

    Returns:
        List of ActiveJobInfo for active jobs.
    """
    jobs: list[ActiveJobInfo] = []

    if queue is None:
        return jobs

    try:
        # Get all jobs from queue
        all_jobs = queue.list_jobs()

        for job in all_jobs:
            # Only include active jobs (pending, running, retrying)
            if job.status in ("pending", "queued", "running", "preparing", "retrying"):
                job_info = ActiveJobInfo(
                    job_id=job.job_id,
                    status=job.status,
                    input_file=str(job.input_path) if job.input_path else None,
                    output_file=str(job.output_path) if job.output_path else None,
                    progress_percent=getattr(job, "progress", 0.0) or 0.0,
                    current_stage=getattr(job, "current_stage", None),
                    started_at=(job.started_at.isoformat() if job.started_at else None),
                    frames_processed=getattr(job, "frames_processed", 0) or 0,
                    total_frames=getattr(job, "total_frames", 0) or 0,
                    error_message=getattr(job, "error_message", None),
                )
                jobs.append(job_info)

    except Exception:
        # Don't fail crash reporting if job capture fails
        pass

    return jobs


def get_queue_stats(queue: BatchVideoQueue | None) -> dict[str, Any]:
    """Get queue statistics.

    Args:
        queue: The batch video queue instance.

    Returns:
        Dictionary of queue statistics.
    """
    if queue is None:
        return {}

    try:
        stats = queue.get_stats()
        return stats.to_dict() if hasattr(stats, "to_dict") else {}
    except Exception:
        return {}


def capture_system_state(
    queue: BatchVideoQueue | None = None,
    app_version: str = "",
    app_config: dict[str, Any] | None = None,
    app_start_time: float | None = None,
) -> SystemState:
    """Capture complete system state for crash reporting.

    Args:
        queue: Optional batch video queue for job information.
        app_version: Application version string.
        app_config: Application configuration dictionary.
        app_start_time: Application start time for uptime calculation.

    Returns:
        SystemState with all captured information.
    """
    global _app_start_time
    if app_start_time is not None:
        _app_start_time = app_start_time

    # Capture all state components
    gpu_info = get_gpu_info()
    memory_info = get_memory_info()
    process_info = get_process_info()
    active_jobs = get_active_jobs(queue)
    queue_stats = get_queue_stats(queue)

    # Build system state
    system_state = SystemState(
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=time.time() - _app_start_time,
        # Platform
        platform_system=platform.system(),
        platform_node=platform.node(),
        platform_release=platform.release(),
        platform_version=platform.version(),
        platform_machine=platform.machine(),
        platform_python_version=platform.python_version(),
        # Hardware
        gpu=gpu_info,
        memory=memory_info,
        process=process_info,
        # Application
        active_jobs=active_jobs,
        queue_stats=queue_stats,
        app_version=app_version,
        app_config=app_config or {},
    )

    return system_state


def set_app_start_time(start_time: float) -> None:
    """Set the application start time for uptime calculation.

    Args:
        start_time: Unix timestamp of application start.
    """
    global _app_start_time
    _app_start_time = start_time
