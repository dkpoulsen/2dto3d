"""Real-time memory monitoring with automatic garbage collection and warnings.

This module provides comprehensive memory monitoring capabilities including:
- Real-time system memory tracking via psutil
- Automatic garbage collection when approaching memory limits
- Configurable warning thresholds with callback support
- Context manager for scoped memory monitoring
- Thread-safe singleton pattern for global monitoring
"""

from __future__ import annotations

import gc
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable, Optional

import psutil

from video2d3d.utils.logger import get_logger, log_exception

if TYPE_CHECKING:
    from collections.abc import Generator

    from loguru import Logger

# Type alias for memory warning callbacks
MemoryWarningCallback = Callable[["MemoryInfo", "MemoryWarningLevel"], None]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Memory conversion constants
BYTES_PER_MB: int = 1024 * 1024
BYTES_PER_GB: int = 1024 * 1024 * 1024

# Default warning thresholds (as fractions of total memory)
DEFAULT_WARNING_THRESHOLD: float = 0.75  # 75% - Warning
DEFAULT_CRITICAL_THRESHOLD: float = 0.85  # 85% - Critical
DEFAULT_EMERGENCY_THRESHOLD: float = 0.95  # 95% - Emergency

# Default monitoring interval in seconds
DEFAULT_MONITOR_INTERVAL: float = 1.0

# Default GC thresholds (as fractions of total memory)
DEFAULT_GC_WARNING_THRESHOLD: float = 0.80  # Trigger GC at 80%
DEFAULT_GC_CRITICAL_THRESHOLD: float = 0.90  # Force GC at 90%


class MemoryWarningLevel(Enum):
    """Memory warning severity levels."""

    NORMAL = auto()  # Memory usage is normal
    WARNING = auto()  # Approaching memory limit
    CRITICAL = auto()  # Near memory limit - GC recommended
    EMERGENCY = auto()  # At memory limit - immediate action required


@dataclass
class MemoryInfo:
    """Current memory statistics.

    Attributes:
        total_mb: Total system memory in MB.
        available_mb: Available memory in MB.
        used_mb: Used memory in MB.
        percent: Memory usage percentage (0-100).
        process_mb: Current process memory in MB.
        process_percent: Process memory as percentage of total.
        warning_level: Current warning level.
        timestamp: Unix timestamp of measurement.
    """

    total_mb: float
    available_mb: float
    used_mb: float
    percent: float
    process_mb: float
    process_percent: float
    warning_level: MemoryWarningLevel
    timestamp: float = field(default_factory=time.time)

    @property
    def is_warning(self) -> bool:
        """Check if memory usage is at warning level or above."""
        return self.warning_level != MemoryWarningLevel.NORMAL

    @property
    def is_critical(self) -> bool:
        """Check if memory usage is at critical level or above."""
        return self.warning_level in (
            MemoryWarningLevel.CRITICAL,
            MemoryWarningLevel.EMERGENCY,
        )

    @property
    def is_emergency(self) -> bool:
        """Check if memory usage is at emergency level."""
        return self.warning_level == MemoryWarningLevel.EMERGENCY


@dataclass
class MemoryMonitorConfig:
    """Configuration for memory monitoring.

    Attributes:
        warning_threshold: Fraction of total memory for warning (0.0-1.0).
        critical_threshold: Fraction of total memory for critical (0.0-1.0).
        emergency_threshold: Fraction of total memory for emergency (0.0-1.0).
        gc_warning_threshold: Fraction to trigger GC at warning level.
        gc_critical_threshold: Fraction to force GC at critical level.
        auto_gc_enabled: Whether to automatically run GC when thresholds exceeded.
        monitor_interval: Seconds between memory checks when monitoring.
        enable_callbacks: Whether to invoke warning callbacks.
    """

    warning_threshold: float = DEFAULT_WARNING_THRESHOLD
    critical_threshold: float = DEFAULT_CRITICAL_THRESHOLD
    emergency_threshold: float = DEFAULT_EMERGENCY_THRESHOLD
    gc_warning_threshold: float = DEFAULT_GC_WARNING_THRESHOLD
    gc_critical_threshold: float = DEFAULT_GC_CRITICAL_THRESHOLD
    auto_gc_enabled: bool = True
    monitor_interval: float = DEFAULT_MONITOR_INTERVAL
    enable_callbacks: bool = True

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0 < self.warning_threshold <= 1.0:
            raise ValueError(
                f"warning_threshold must be between 0 and 1, got {self.warning_threshold}"
            )
        if not 0 < self.critical_threshold <= 1.0:
            raise ValueError(
                f"critical_threshold must be between 0 and 1, got {self.critical_threshold}"
            )
        if not 0 < self.emergency_threshold <= 1.0:
            raise ValueError(
                f"emergency_threshold must be between 0 and 1, got {self.emergency_threshold}"
            )
        if not self.warning_threshold < self.critical_threshold < self.emergency_threshold:
            raise ValueError("Thresholds must be ordered: warning < critical < emergency")
        if self.monitor_interval <= 0:
            raise ValueError(f"monitor_interval must be positive, got {self.monitor_interval}")


class MemoryMonitor:
    """Real-time memory monitor with automatic garbage collection and warnings.

    This class provides:
    - Real-time memory tracking for system and process
    - Configurable warning thresholds
    - Automatic garbage collection when approaching limits
    - Callback system for memory warning notifications
    - Thread-safe singleton pattern

    Example:
        # Basic usage
        monitor = MemoryMonitor()
        info = monitor.get_memory_info()
        print(f"Memory usage: {info.percent:.1f}%")

        # With callbacks
        def on_warning(info: MemoryInfo, level: MemoryWarningLevel):
            print(f"Memory warning: {level.name} at {info.percent:.1f}%")

        monitor.add_callback(on_warning)
        monitor.start_monitoring()

        # Context manager
        with memory_monitor_context():
            # Code that uses memory
            pass
    """

    _instance: Optional[MemoryMonitor] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, config: Optional[MemoryMonitorConfig] = None) -> MemoryMonitor:
        """Create or return the singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[MemoryMonitorConfig] = None) -> None:
        """Initialize the memory monitor.

        Args:
            config: Configuration for monitoring thresholds and behavior.
        """
        # Skip initialization if already done (singleton pattern)
        if self._initialized:
            if config is not None:
                self._config = config
            return

        self._config = config or MemoryMonitorConfig()
        self._callbacks: list[MemoryWarningCallback] = []
        self._callback_lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_info: Optional[MemoryInfo] = None
        self._last_gc_time: float = 0.0
        self._gc_cooldown: float = 5.0  # Minimum seconds between GC runs
        self._initialized = True
        self._logger = self._get_memory_logger()

    @staticmethod
    def _get_memory_logger() -> Logger:
        """Get the memory module logger (lazy initialization)."""
        return get_logger("memory_monitor")

    @property
    def config(self) -> MemoryMonitorConfig:
        """Get the current configuration."""
        return self._config

    @config.setter
    def config(self, value: MemoryMonitorConfig) -> None:
        """Set the configuration."""
        self._config = value

    @property
    def is_monitoring(self) -> bool:
        """Check if continuous monitoring is active."""
        return self._monitoring

    @property
    def last_info(self) -> Optional[MemoryInfo]:
        """Get the last memory info snapshot."""
        return self._last_info

    def get_memory_info(self) -> MemoryInfo:
        """Get current memory statistics.

        Returns:
            MemoryInfo with current memory statistics.
        """
        # System memory
        mem = psutil.virtual_memory()
        total_mb = mem.total / BYTES_PER_MB
        available_mb = mem.available / BYTES_PER_MB
        used_mb = mem.used / BYTES_PER_MB
        percent = mem.percent

        # Process memory
        process = psutil.Process()
        process_info = process.memory_info()
        process_mb = process_info.rss / BYTES_PER_MB
        process_percent = (process_mb / total_mb) * 100

        # Determine warning level
        usage_fraction = used_mb / total_mb
        warning_level = self._determine_warning_level(usage_fraction)

        info = MemoryInfo(
            total_mb=total_mb,
            available_mb=available_mb,
            used_mb=used_mb,
            percent=percent,
            process_mb=process_mb,
            process_percent=process_percent,
            warning_level=warning_level,
        )

        self._last_info = info
        return info

    def _determine_warning_level(self, usage_fraction: float) -> MemoryWarningLevel:
        """Determine warning level based on memory usage fraction.

        Args:
            usage_fraction: Memory usage as fraction of total (0.0-1.0).

        Returns:
            Appropriate MemoryWarningLevel.
        """
        if usage_fraction >= self._config.emergency_threshold:
            return MemoryWarningLevel.EMERGENCY
        if usage_fraction >= self._config.critical_threshold:
            return MemoryWarningLevel.CRITICAL
        if usage_fraction >= self._config.warning_threshold:
            return MemoryWarningLevel.WARNING
        return MemoryWarningLevel.NORMAL

    def add_callback(self, callback: MemoryWarningCallback) -> None:
        """Add a callback for memory warnings.

        Callbacks are invoked when warning level changes to WARNING or above.

        Args:
            callback: Function taking MemoryInfo and MemoryWarningLevel.
        """
        with self._callback_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: MemoryWarningCallback) -> bool:
        """Remove a previously registered callback.

        Args:
            callback: The callback to remove.

        Returns:
            True if callback was removed, False if not found.
        """
        with self._callback_lock:
            try:
                self._callbacks.remove(callback)
                return True
            except ValueError:
                return False

    def clear_callbacks(self) -> None:
        """Remove all registered callbacks."""
        with self._callback_lock:
            self._callbacks.clear()

    def _invoke_callbacks(self, info: MemoryInfo) -> None:
        """Invoke all registered callbacks with current memory info.

        Args:
            info: Current memory information.
        """
        if not self._config.enable_callbacks:
            return

        if not info.is_warning:
            return

        with self._callback_lock:
            callbacks = self._callbacks.copy()

        for callback in callbacks:
            try:
                callback(info, info.warning_level)
            except Exception as e:
                log_exception(
                    "Error in memory warning callback",
                    exception=e,
                    callback=callback.__name__,
                )

    def run_garbage_collection(self, force: bool = False) -> int:
        """Run garbage collection to free memory.

        Args:
            force: If True, run full collection regardless of cooldown.

        Returns:
            Number of objects collected.
        """
        current_time = time.time()

        # Check cooldown unless forced
        if not force and (current_time - self._last_gc_time) < self._gc_cooldown:
            self._logger.debug("GC skipped due to cooldown")
            return 0

        self._logger.info("Running garbage collection")

        # Run garbage collection
        collected = gc.collect()

        # Also clear GPU memory if available
        try:
            from video2d3d.utils.gpu import clear_gpu_memory

            clear_gpu_memory()
        except ImportError:
            pass

        self._last_gc_time = current_time

        if collected > 0:
            self._logger.info(f"Garbage collection freed {collected} objects")

        return collected

    def check_and_collect(self, info: Optional[MemoryInfo] = None) -> bool:
        """Check memory and run GC if thresholds exceeded.

        Args:
            info: Memory info to check. If None, gets current info.

        Returns:
            True if GC was run, False otherwise.
        """
        if info is None:
            info = self.get_memory_info()

        usage_fraction = info.used_mb / info.total_mb

        # Force GC at critical threshold
        if usage_fraction >= self._config.gc_critical_threshold:
            self._logger.warning(f"Memory at critical level ({usage_fraction:.1%}), forcing GC")
            self.run_garbage_collection(force=True)
            return True

        # Normal GC at warning threshold
        if self._config.auto_gc_enabled and usage_fraction >= self._config.gc_warning_threshold:
            self._logger.warning(f"Memory at warning level ({usage_fraction:.1%}), running GC")
            self.run_garbage_collection()
            return True

        return False

    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        self._logger.info("Memory monitoring started")

        while not self._stop_event.is_set():
            try:
                info = self.get_memory_info()

                # Check for warnings and invoke callbacks
                if info.is_warning:
                    self._invoke_callbacks(info)
                    self.check_and_collect(info)

                # Log periodic status at debug level
                self._logger.debug(
                    f"Memory: {info.percent:.1f}% used "
                    f"({info.used_mb:.0f}MB / {info.total_mb:.0f}MB), "
                    f"process: {info.process_mb:.0f}MB"
                )

            except Exception as e:
                log_exception("Error in monitoring loop", exception=e)

            # Wait for next interval or stop signal
            self._stop_event.wait(self._config.monitor_interval)

        self._logger.info("Memory monitoring stopped")

    def start_monitoring(self) -> None:
        """Start continuous memory monitoring in a background thread."""
        if self._monitoring:
            self._logger.warning("Monitoring already active")
            return

        self._stop_event.clear()
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MemoryMonitor",
            daemon=True,
        )
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop continuous memory monitoring."""
        if not self._monitoring:
            return

        self._stop_event.set()
        self._monitoring = False

        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (mainly for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.stop_monitoring()
                cls._instance = None


@contextmanager
def memory_monitor_context(
    config: Optional[MemoryMonitorConfig] = None,
    callback: Optional[MemoryWarningCallback] = None,
) -> Generator[MemoryMonitor, None, None]:
    """Context manager for scoped memory monitoring.

    Args:
        config: Optional configuration for the monitor.
        callback: Optional callback for memory warnings.

    Yields:
        MemoryMonitor instance.

    Example:
        with memory_monitor_context() as monitor:
            # Code that uses memory
            process_data()
            # Check memory at any point
            info = monitor.get_memory_info()
    """
    monitor = MemoryMonitor(config)

    if callback is not None:
        monitor.add_callback(callback)

    try:
        yield monitor
    finally:
        # Report final memory status
        info = monitor.get_memory_info()
        if info.is_warning:
            monitor._logger.warning(f"Context exiting with elevated memory: {info.percent:.1f}%")


def get_memory_monitor(config: Optional[MemoryMonitorConfig] = None) -> MemoryMonitor:
    """Get the singleton MemoryMonitor instance.

    Args:
        config: Optional configuration to apply.

    Returns:
        MemoryMonitor singleton instance.
    """
    return MemoryMonitor(config)


def get_current_memory_info() -> MemoryInfo:
    """Get current memory information without continuous monitoring.

    Returns:
        MemoryInfo snapshot of current memory state.
    """
    monitor = MemoryMonitor()
    return monitor.get_memory_info()


def format_memory_size(size_mb: float) -> str:
    """Format memory size in human-readable format.

    Args:
        size_mb: Size in megabytes.

    Returns:
        Formatted string (e.g., "1.5 GB", "512 MB").
    """
    if size_mb >= 1024:
        return f"{size_mb / 1024:.1f} GB"
    return f"{size_mb:.0f} MB"


# Module-level exports
__all__ = [
    # Enums
    "MemoryWarningLevel",
    # Dataclasses
    "MemoryInfo",
    "MemoryMonitorConfig",
    # Classes
    "MemoryMonitor",
    # Functions
    "get_memory_monitor",
    "get_current_memory_info",
    "format_memory_size",
    # Context managers
    "memory_monitor_context",
    # Type aliases
    "MemoryWarningCallback",
    # Constants
    "BYTES_PER_MB",
    "BYTES_PER_GB",
    "DEFAULT_WARNING_THRESHOLD",
    "DEFAULT_CRITICAL_THRESHOLD",
    "DEFAULT_EMERGENCY_THRESHOLD",
    "DEFAULT_MONITOR_INTERVAL",
    "DEFAULT_GC_WARNING_THRESHOLD",
    "DEFAULT_GC_CRITICAL_THRESHOLD",
]
