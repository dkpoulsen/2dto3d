"""Adaptive batch sizing that automatically adjusts based on available memory and GPU utilization.

This module provides intelligent batch sizing that dynamically adjusts to optimize
throughput while preventing out-of-memory errors.

Key features:
- Memory-aware batch sizing (both RAM and GPU VRAM)
- GPU utilization monitoring for optimal throughput
- Configurable thresholds and scaling factors
- Callbacks for batch size changes
- Thread-safe implementation
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from collections.abc import Generator


# BQ|from video2d3d.utils.gpu import (
# QJ|    GPUConfig,
# ZN|    GPUInfo,
# RS|    compute_optimal_batch_size,
# ZH|    get_gpu_info,
# PJ|    get_memory_usage,
# RK|    is_cuda_available,
# RK|)
from video2d3d.utils.logger import get_logger, log_exception
from video2d3d.utils.memory_monitor import MemoryInfo, get_current_memory_info

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default thresholds
DEFAULT_MEMORY_HIGH_THRESHOLD: float = 0.80  # Scale down above 80% memory usage
DEFAULT_MEMORY_LOW_THRESHOLD: float = 0.50  # Scale up below 50% memory usage
DEFAULT_GPU_UTIL_LOW_THRESHOLD: float = 0.60  # Scale up if GPU util < 60%
DEFAULT_GPU_UTIL_HIGH_THRESHOLD: float = 0.95  # Scale down if GPU util > 95%

# Default scaling factors
DEFAULT_SCALE_UP_FACTOR: float = 1.5
DEFAULT_SCALE_DOWN_FACTOR: float = 0.5
DEFAULT_MIN_SCALE_STEP: int = 1

# Default timing
DEFAULT_ADJUSTMENT_INTERVAL: float = 2.0  # Seconds between adjustments
DEFAULT_COOLDOWN_PERIOD: float = 5.0  # Seconds to wait after adjustment
DEFAULT_STABILITY_WINDOW: int = 3  # Number of samples for stability check

# Default batch sizes
DEFAULT_INITIAL_BATCH_SIZE: int = 4
DEFAULT_MIN_BATCH_SIZE: int = 1
DEFAULT_MAX_BATCH_SIZE: int = 64


class AdjustmentReason(Enum):
    """Reasons for batch size adjustment."""

    MEMORY_PRESSURE = auto()  # High memory usage
    MEMORY_AVAILABLE = auto()  # Low memory usage, can scale up
    GPU_UNDERUTILIZED = auto()  # GPU not fully utilized
    GPU_OVERLOADED = auto()  # GPU overloaded
    OOM_RECOVERY = auto()  # Recovering from OOM
    MANUAL = auto()  # Manual adjustment
    INITIALIZATION = auto()  # Initial setup


@dataclass
class AdaptiveBatchConfig:
    """Configuration for adaptive batch sizing.

    Attributes:
        enabled: Whether adaptive batch sizing is enabled.
        initial_batch_size: Starting batch size.
        min_batch_size: Minimum allowed batch size.
        max_batch_size: Maximum allowed batch size.
        memory_high_threshold: Scale down if memory usage exceeds this (0.0-1.0).
        memory_low_threshold: Scale up if memory usage below this (0.0-1.0).
        gpu_util_low_threshold: Scale up if GPU utilization below this (0.0-1.0).
        gpu_util_high_threshold: Scale down if GPU utilization above this (0.0-1.0).
        scale_up_factor: Multiply batch size by this when scaling up.
        scale_down_factor: Multiply batch size by this when scaling down.
        min_scale_step: Minimum change in batch size.
        adjustment_interval: Seconds between adjustment checks.
        cooldown_period: Seconds to wait after an adjustment.
        stability_window: Number of samples to confirm stability.
        gpu_config: GPU configuration for memory calculations.
        image_height: Default image height for memory estimation.
        image_width: Default image width for memory estimation.
    """

    enabled: bool = True
    initial_batch_size: int = DEFAULT_INITIAL_BATCH_SIZE
    min_batch_size: int = DEFAULT_MIN_BATCH_SIZE
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE
    memory_high_threshold: float = DEFAULT_MEMORY_HIGH_THRESHOLD
    memory_low_threshold: float = DEFAULT_MEMORY_LOW_THRESHOLD
    gpu_util_low_threshold: float = DEFAULT_GPU_UTIL_LOW_THRESHOLD
    gpu_util_high_threshold: float = DEFAULT_GPU_UTIL_HIGH_THRESHOLD
    scale_up_factor: float = DEFAULT_SCALE_UP_FACTOR
    scale_down_factor: float = DEFAULT_SCALE_DOWN_FACTOR
    min_scale_step: int = DEFAULT_MIN_SCALE_STEP
    adjustment_interval: float = DEFAULT_ADJUSTMENT_INTERVAL
    cooldown_period: float = DEFAULT_COOLDOWN_PERIOD
    stability_window: int = DEFAULT_STABILITY_WINDOW
    gpu_config: GPUConfig | None = None
    image_height: int = 384
    image_width: int = 384

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.min_batch_size < 1:
            raise ValueError(f"min_batch_size must be >= 1, got {self.min_batch_size}")
        if self.max_batch_size < self.min_batch_size:
            raise ValueError(
                f"max_batch_size ({self.max_batch_size}) must be >= "
                f"min_batch_size ({self.min_batch_size})"
            )
        if not 0 < self.memory_low_threshold < self.memory_high_threshold < 1:
            raise ValueError(
                "Thresholds must satisfy: 0 < memory_low_threshold < "
                f"memory_high_threshold < 1, got {self.memory_low_threshold} < "
                f"{self.memory_high_threshold}"
            )
        if not 0 < self.gpu_util_low_threshold < self.gpu_util_high_threshold <= 1:
            raise ValueError(
                "GPU thresholds must satisfy: 0 < gpu_util_low_threshold < "
                f"gpu_util_high_threshold <= 1, got {self.gpu_util_low_threshold} < "
                f"{self.gpu_util_high_threshold}"
            )
        if self.scale_up_factor <= 1.0:
            raise ValueError(f"scale_up_factor must be > 1.0, got {self.scale_up_factor}")
        if not 0 < self.scale_down_factor < 1:
            raise ValueError(
                f"scale_down_factor must be between 0 and 1, got {self.scale_down_factor}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "initial_batch_size": self.initial_batch_size,
            "min_batch_size": self.min_batch_size,
            "max_batch_size": self.max_batch_size,
            "memory_high_threshold": self.memory_high_threshold,
            "memory_low_threshold": self.memory_low_threshold,
            "gpu_util_low_threshold": self.gpu_util_low_threshold,
            "gpu_util_high_threshold": self.gpu_util_high_threshold,
            "scale_up_factor": self.scale_up_factor,
            "scale_down_factor": self.scale_down_factor,
            "min_scale_step": self.min_scale_step,
            "adjustment_interval": self.adjustment_interval,
            "cooldown_period": self.cooldown_period,
            "stability_window": self.stability_window,
            "image_height": self.image_height,
            "image_width": self.image_width,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdaptiveBatchConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            initial_batch_size=data.get("initial_batch_size", DEFAULT_INITIAL_BATCH_SIZE),
            min_batch_size=data.get("min_batch_size", DEFAULT_MIN_BATCH_SIZE),
            max_batch_size=data.get("max_batch_size", DEFAULT_MAX_BATCH_SIZE),
            memory_high_threshold=data.get("memory_high_threshold", DEFAULT_MEMORY_HIGH_THRESHOLD),
            memory_low_threshold=data.get("memory_low_threshold", DEFAULT_MEMORY_LOW_THRESHOLD),
            gpu_util_low_threshold=data.get(
                "gpu_util_low_threshold", DEFAULT_GPU_UTIL_LOW_THRESHOLD
            ),
            gpu_util_high_threshold=data.get(
                "gpu_util_high_threshold", DEFAULT_GPU_UTIL_HIGH_THRESHOLD
            ),
            scale_up_factor=data.get("scale_up_factor", DEFAULT_SCALE_UP_FACTOR),
            scale_down_factor=data.get("scale_down_factor", DEFAULT_SCALE_DOWN_FACTOR),
            min_scale_step=data.get("min_scale_step", DEFAULT_MIN_SCALE_STEP),
            adjustment_interval=data.get("adjustment_interval", DEFAULT_ADJUSTMENT_INTERVAL),
            cooldown_period=data.get("cooldown_period", DEFAULT_COOLDOWN_PERIOD),
            stability_window=data.get("stability_window", DEFAULT_STABILITY_WINDOW),
            image_height=data.get("image_height", 384),
            image_width=data.get("image_width", 384),
        )


@dataclass
class BatchSizeHistory:
    """History of batch size adjustments for analysis."""

    batch_sizes: list[int] = field(default_factory=list)
    memory_usages: list[float] = field(default_factory=list)
    gpu_utils: list[float] = field(default_factory=list)
    timestamps: list[float] = field(default_factory=list)
    max_history: int = 100

    def add_sample(
        self,
        batch_size: int,
        memory_usage: float,
        gpu_util: float,
    ) -> None:
        """Add a sample to history."""
        self.batch_sizes.append(batch_size)
        self.memory_usages.append(memory_usage)
        self.gpu_utils.append(gpu_util)
        self.timestamps.append(time.time())

        # Trim to max history
        if len(self.batch_sizes) > self.max_history:
            self.batch_sizes = self.batch_sizes[-self.max_history :]
            self.memory_usages = self.memory_usages[-self.max_history :]
            self.gpu_utils = self.gpu_utils[-self.max_history :]
            self.timestamps = self.timestamps[-self.max_history :]

    def get_recent_average(self, window: int = 5) -> tuple[float, float, float]:
        """Get recent averages for batch size, memory, and GPU util."""
        if not self.batch_sizes:
            return (0.0, 0.0, 0.0)

        window = min(window, len(self.batch_sizes))
        avg_batch = sum(self.batch_sizes[-window:]) / window
        avg_mem = sum(self.memory_usages[-window:]) / window
        avg_gpu = sum(self.gpu_utils[-window:]) / window

        return (avg_batch, avg_mem, avg_gpu)


# Type alias for batch size change callbacks
BatchSizeCallback = Callable[[int, int, AdjustmentReason], None]  # old_size, new_size, reason


class AdaptiveBatchSizer:
    """Dynamically adjusts batch size based on system resources.

    This class monitors memory (RAM and GPU VRAM) and GPU utilization
    to automatically adjust batch size for optimal throughput while
    preventing out-of-memory errors.

    Example:
        config = AdaptiveBatchConfig(
            initial_batch_size=4,
            min_batch_size=1,
            max_batch_size=32,
        )
        sizer = AdaptiveBatchSizer(config)

        # Get current batch size
        batch_size = sizer.get_batch_size()

        # Start automatic monitoring
        sizer.start_monitoring()

        # Register callback for changes
        sizer.add_callback(on_batch_size_changed)

        # Stop monitoring
        sizer.stop_monitoring()
    """

    def __init__(
        self,
        config: AdaptiveBatchConfig | None = None,
        initial_batch_size: int | None = None,
    ) -> None:
        """Initialize the adaptive batch sizer.

        Args:
            config: Configuration for adaptive sizing.
            initial_batch_size: Override initial batch size (deprecated, use config).
        """
        self._config = config or AdaptiveBatchConfig()

        # Handle deprecated initial_batch_size parameter
        if initial_batch_size is not None:
            self._current_batch_size = initial_batch_size
        else:
            self._current_batch_size = self._config.initial_batch_size

        self._logger = get_logger("adaptive_batch_sizer")
        self._lock = threading.RLock()

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Cooldown tracking
        self._last_adjustment_time: float = 0.0
        self._last_adjustment_reason: AdjustmentReason | None = None

        # Callbacks
        self._callbacks: list[BatchSizeCallback] = []
        self._callback_lock = threading.Lock()

        # History tracking
        self._history = BatchSizeHistory()

        # Stability tracking
        self._stability_samples: list[tuple[float, float]] = []  # (memory, gpu_util)

    @property
    def config(self) -> AdaptiveBatchConfig:
        """Get current configuration."""
        return self._config

    @config.setter
    def config(self, value: AdaptiveBatchConfig) -> None:
        """Set configuration."""
        with self._lock:
            self._config = value
            # Ensure current batch size is within new bounds
            self._current_batch_size = max(
                self._config.min_batch_size,
                min(self._config.max_batch_size, self._current_batch_size),
            )

    @property
    def current_batch_size(self) -> int:
        """Get current batch size."""
        with self._lock:
            return self._current_batch_size

    @property
    def is_monitoring(self) -> bool:
        """Check if automatic monitoring is active."""
        return self._monitoring

    @property
    def history(self) -> BatchSizeHistory:
        """Get batch size history."""
        return self._history

    def get_batch_size(self) -> int:
        """Get current batch size (alias for current_batch_size property)."""
        return self.current_batch_size

    def set_batch_size(
        self,
        new_size: int,
        reason: AdjustmentReason = AdjustmentReason.MANUAL,
    ) -> int:
        """Manually set batch size.

        Args:
            new_size: Desired batch size.
            reason: Reason for adjustment.

        Returns:
            Actual batch size set (clamped to min/max).
        """
        with self._lock:
            old_size = self._current_batch_size

            # Clamp to bounds
            new_size = max(self._config.min_batch_size, min(self._config.max_batch_size, new_size))

            if new_size != old_size:
                self._current_batch_size = new_size
                self._last_adjustment_time = time.time()
                self._last_adjustment_reason = reason

                self._logger.info(
                    f"Batch size adjusted: {old_size} -> {new_size} (reason: {reason.name})"
                )

                # Invoke callbacks
                self._invoke_callbacks(old_size, new_size, reason)

            return self._current_batch_size

    def _invoke_callbacks(
        self,
        old_size: int,
        new_size: int,
        reason: AdjustmentReason,
    ) -> None:
        """Invoke all registered callbacks."""
        with self._callback_lock:
            callbacks = self._callbacks.copy()

        for callback in callbacks:
            try:
                callback(old_size, new_size, reason)
            except Exception as e:
                log_exception(
                    "Error in batch size callback",
                    exception=e,
                    callback=callback.__name__,
                )

    def add_callback(self, callback: BatchSizeCallback) -> None:
        """Add a callback for batch size changes.

        Args:
            callback: Function called when batch size changes.
        """
        with self._callback_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: BatchSizeCallback) -> bool:
        """Remove a callback.

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
        """Remove all callbacks."""
        with self._callback_lock:
            self._callbacks.clear()

    def _get_system_state(self) -> tuple[MemoryInfo, GPUInfo | None, float]:
        """Get current system state.

        Returns:
            Tuple of (memory_info, gpu_info, gpu_utilization).
        """
        # Get memory info
        memory_info = get_current_memory_info()

        # Get GPU info
        gpu_info: GPUInfo | None = None
        gpu_util = 0.0

        if is_cuda_available():
            try:
                gpu_info = get_gpu_info(0)
                if gpu_info:
                    gpu_util = gpu_info.memory_utilization / 100.0
            except Exception as e:
                self._logger.debug(f"Could not get GPU info: {e}")

        return (memory_info, gpu_info, gpu_util)

    def _calculate_optimal_batch_size(
        self,
        memory_info: MemoryInfo,
        gpu_info: GPUInfo | None,
        gpu_util: float,
    ) -> tuple[int, AdjustmentReason | None]:
        """Calculate optimal batch size based on system state.

        Args:
            memory_info: Current memory state.
            gpu_info: Current GPU state (if available).
            gpu_util: Current GPU utilization (0.0-1.0).

        Returns:
            Tuple of (optimal_batch_size, adjustment_reason).
        """
        current_size = self._current_batch_size
        config = self._config

        # Calculate memory usage fraction
        memory_usage = (
            memory_info.used_mb / memory_info.total_mb if memory_info.total_mb > 0 else 0.0
        )

        # Add to stability samples
        self._stability_samples.append((memory_usage, gpu_util))
        if len(self._stability_samples) > config.stability_window:
            self._stability_samples = self._stability_samples[-config.stability_window :]

        # Record in history
        self._history.add_sample(current_size, memory_usage, gpu_util)

        # Determine adjustment based on system state
        new_size = current_size
        reason: AdjustmentReason | None = None

        # High memory pressure - scale down aggressively
        if memory_usage >= config.memory_high_threshold:
            new_size = max(
                config.min_batch_size,
                int(current_size * config.scale_down_factor),
            )
            # Ensure at least one step reduction, but never below min_batch_size
            if current_size > config.min_batch_size:
                new_size = min(new_size, current_size - config.min_scale_step)
                new_size = max(config.min_batch_size, new_size)
            reason = AdjustmentReason.MEMORY_PRESSURE

        # Low memory usage and low GPU util - scale up
        elif (
            memory_usage <= config.memory_low_threshold and gpu_util < config.gpu_util_low_threshold
        ):
            new_size = min(
                config.max_batch_size,
                int(current_size * config.scale_up_factor),
            )
            # Ensure at least one step increase
            new_size = max(new_size, current_size + config.min_scale_step)
            reason = AdjustmentReason.MEMORY_AVAILABLE

        # Low memory usage alone - try scaling up
        elif memory_usage <= config.memory_low_threshold:
            new_size = min(
                config.max_batch_size,
                int(current_size * config.scale_up_factor),
            )
            new_size = max(new_size, current_size + config.min_scale_step)
            reason = AdjustmentReason.MEMORY_AVAILABLE

        # GPU overloaded - scale down slightly
        elif gpu_util >= config.gpu_util_high_threshold:
            # More conservative scale down for GPU overload
            new_size = max(
                config.min_batch_size,
                current_size - config.min_scale_step,
            )
            reason = AdjustmentReason.GPU_OVERLOADED

        # GPU underutilized but memory moderate - try small scale up
        elif (
            gpu_util < config.gpu_util_low_threshold
            and memory_usage < config.memory_high_threshold * 0.9
        ):
            new_size = min(
                config.max_batch_size,
                current_size + config.min_scale_step,
            )
            reason = AdjustmentReason.GPU_UNDERUTILIZED

        # Clamp to bounds
        new_size = max(config.min_batch_size, min(config.max_batch_size, new_size))

        return (new_size, reason if new_size != current_size else None)

    def _is_in_cooldown(self) -> bool:
        """Check if we're in cooldown period after last adjustment."""
        if self._last_adjustment_time == 0:
            return False

        elapsed = time.time() - self._last_adjustment_time
        return elapsed < self._config.cooldown_period

    def _is_stable(self) -> bool:
        """Check if system state is stable (consistent readings)."""
        if len(self._stability_samples) < self._config.stability_window:
            return False

        samples = self._stability_samples[-self._config.stability_window :]

        # Check if memory and GPU util are relatively stable
        mem_values = [s[0] for s in samples]
        gpu_values = [s[1] for s in samples]

        # Stability threshold (coefficient of variation < 10%)
        if mem_values:
            mem_mean = sum(mem_values) / len(mem_values)
            if mem_mean > 0:
                mem_var = sum((m - mem_mean) ** 2 for m in mem_values) / len(mem_values)
                mem_cv = (mem_var**0.5) / mem_mean
                if mem_cv > 0.1:
                    return False

        if gpu_values:
            gpu_mean = sum(gpu_values) / len(gpu_values)
            if gpu_mean > 0:
                gpu_var = sum((g - gpu_mean) ** 2 for g in gpu_values) / len(gpu_values)
                gpu_cv = (gpu_var**0.5) / gpu_mean
                if gpu_cv > 0.15:
                    return False

        return True

    def adjust_batch_size(self) -> int:
        """Perform a single batch size adjustment based on current state.

        Returns:
            Current batch size after potential adjustment.
        """
        if not self._config.enabled:
            return self._current_batch_size

        with self._lock:
            # Check cooldown
            if self._is_in_cooldown():
                return self._current_batch_size

            # Get current system state
            memory_info, gpu_info, gpu_util = self._get_system_state()

            # Calculate optimal batch size
            new_size, reason = self._calculate_optimal_batch_size(memory_info, gpu_info, gpu_util)

            # Apply adjustment if needed
            if reason is not None and new_size != self._current_batch_size:
                self.set_batch_size(new_size, reason)

            return self._current_batch_size

    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        self._logger.info("Adaptive batch sizing monitoring started")

        while not self._stop_event.is_set():
            try:
                self.adjust_batch_size()

                # Log current state periodically
                mem_info, gpu_info, gpu_util = self._get_system_state()
                self._logger.debug(
                    f"Batch size: {self._current_batch_size}, "
                    f"Memory: {mem_info.percent:.1f}%, "
                    f"GPU util: {gpu_util * 100:.1f}%"
                )

            except Exception as e:
                log_exception("Error in adaptive batch sizing loop", exception=e)

            # Wait for next interval or stop signal
            self._stop_event.wait(self._config.adjustment_interval)

        self._logger.info("Adaptive batch sizing monitoring stopped")

    def start_monitoring(self) -> None:
        """Start automatic batch size monitoring."""
        if self._monitoring:
            self._logger.warning("Monitoring already active")
            return

        if not self._config.enabled:
            self._logger.info("Adaptive batch sizing is disabled")
            return

        self._stop_event.clear()
        self._monitoring = True

        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="AdaptiveBatchSizer",
            daemon=True,
        )
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop automatic batch size monitoring."""
        if not self._monitoring:
            return

        self._stop_event.set()
        self._monitoring = False

        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

    def handle_oom_error(self) -> int:
        """Handle an out-of-memory error by reducing batch size.

        Call this when an OOM error occurs during processing.

        Returns:
            New batch size after reduction.
        """
        with self._lock:
            old_size = self._current_batch_size

            # Reduce by half, minimum 1
            new_size = max(self._config.min_batch_size, old_size // 2)

            if new_size != old_size:
                self._current_batch_size = new_size
                self._last_adjustment_time = time.time()
                self._last_adjustment_reason = AdjustmentReason.OOM_RECOVERY

                self._logger.warning(f"OOM recovery: batch size reduced {old_size} -> {new_size}")

                self._invoke_callbacks(old_size, new_size, AdjustmentReason.OOM_RECOVERY)

            return self._current_batch_size

    def get_recommended_batch_size(
        self,
        image_height: int | None = None,
        image_width: int | None = None,
    ) -> int:
        """Get recommended batch size based on current system state.

        This is a one-shot recommendation without modifying internal state.

        Args:
            image_height: Image height for memory calculation.
            image_width: Image width for memory calculation.

        Returns:
            Recommended batch size.
        """
        memory_info, gpu_info, gpu_util = self._get_system_state()

        # Use provided dimensions or config defaults

        # Start with current batch size
        recommended = self._current_batch_size

        # Calculate memory usage fraction
        memory_usage = (
            memory_info.used_mb / memory_info.total_mb if memory_info.total_mb > 0 else 0.0
        )

        # Adjust based on memory
        if memory_usage >= self._config.memory_high_threshold:
            recommended = max(
                self._config.min_batch_size,
                int(recommended * self._config.scale_down_factor),
            )
        elif memory_usage <= self._config.memory_low_threshold:
            recommended = min(
                self._config.max_batch_size,
                int(recommended * self._config.scale_up_factor),
            )

        # Adjust based on GPU utilization
        if gpu_util >= self._config.gpu_util_high_threshold:
            recommended = max(self._config.min_batch_size, recommended - 1)
        elif gpu_util < self._config.gpu_util_low_threshold:
            recommended = min(self._config.max_batch_size, recommended + 1)

        # KN|        # If we have GPU info, use GPU memory-based calculation as a ceiling
        # MT|        if gpu_info and self._config.gpu_config:
        # HJ|            gpu_recommended = compute_optimal_batch_size(
        # PQ|                self._config.gpu_config,
        # SW|                height,
        # QZ|                width,
        # NV|            )
        # WB|            recommended = min(recommended, gpu_recommended)
        # RN|

        # Clamp to bounds
        recommended = max(
            self._config.min_batch_size, min(self._config.max_batch_size, recommended)
        )

        return recommended


@contextmanager
def adaptive_batch_sizer_context(
    config: AdaptiveBatchConfig | None = None,
    callback: BatchSizeCallback | None = None,
) -> Generator[AdaptiveBatchSizer, None, None]:
    """Context manager for adaptive batch sizing.

    Args:
        config: Configuration for the sizer.
        callback: Optional callback for batch size changes.

    Yields:
        AdaptiveBatchSizer instance.

    Example:
        with adaptive_batch_sizer_context() as sizer:
            batch_size = sizer.get_batch_size()
            process_batch(data, batch_size)
    """
    sizer = AdaptiveBatchSizer(config)

    if callback is not None:
        sizer.add_callback(callback)

    try:
        yield sizer
    finally:
        sizer.stop_monitoring()


def create_adaptive_sizer(
    initial_batch_size: int = DEFAULT_INITIAL_BATCH_SIZE,
    min_batch_size: int = DEFAULT_MIN_BATCH_SIZE,
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
    **kwargs: Any,
) -> AdaptiveBatchSizer:
    """Factory function to create an AdaptiveBatchSizer with common settings.

    Args:
        initial_batch_size: Starting batch size.
        min_batch_size: Minimum batch size.
        max_batch_size: Maximum batch size.
        **kwargs: Additional configuration options.

    Returns:
        Configured AdaptiveBatchSizer instance.
    """
    config = AdaptiveBatchConfig(
        initial_batch_size=initial_batch_size,
        min_batch_size=min_batch_size,
        max_batch_size=max_batch_size,
        **kwargs,
    )
    return AdaptiveBatchSizer(config)


# Module-level exports
__all__ = [
    # Enums
    "AdjustmentReason",
    # Dataclasses
    "AdaptiveBatchConfig",
    "BatchSizeHistory",
    # Classes
    "AdaptiveBatchSizer",
    # Functions
    "create_adaptive_sizer",
    # Context managers
    "adaptive_batch_sizer_context",
    # Type aliases
    "BatchSizeCallback",
    # Constants
    "DEFAULT_MEMORY_HIGH_THRESHOLD",
    "DEFAULT_MEMORY_LOW_THRESHOLD",
    "DEFAULT_GPU_UTIL_LOW_THRESHOLD",
    "DEFAULT_GPU_UTIL_HIGH_THRESHOLD",
    "DEFAULT_SCALE_UP_FACTOR",
    "DEFAULT_SCALE_DOWN_FACTOR",
    "DEFAULT_MIN_SCALE_STEP",
    "DEFAULT_ADJUSTMENT_INTERVAL",
    "DEFAULT_COOLDOWN_PERIOD",
    "DEFAULT_STABILITY_WINDOW",
    "DEFAULT_INITIAL_BATCH_SIZE",
    "DEFAULT_MIN_BATCH_SIZE",
    "DEFAULT_MAX_BATCH_SIZE",
]
