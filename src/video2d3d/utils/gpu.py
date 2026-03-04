"""GPU acceleration utilities for CUDA device detection, memory management, and optimization.

This module provides comprehensive GPU support including:
- Automatic device detection with multi-GPU support
- Graceful CPU fallback when GPU is unavailable
- Memory management for GPU batches with OOM handling
- Optimized tensor operations with pinned memory and async transfers
"""

from __future__ import annotations

import gc
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore[misc,assignment]

from video2d3d.utils.logger import get_logger, log_exception

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Memory conversion constants
BYTES_PER_MB: int = 1024 * 1024

# GPU memory management constants
# DEFAULT_MEMORY_FRACTION: Maximum fraction of total GPU memory to allocate for the process
DEFAULT_MEMORY_FRACTION: float = 0.8
# MEMORY_SAFETY_MARGIN: Factor applied to free_memory in GPUInfo.available_memory_mb
# (e.g., 0.9 means only 90% of reported free memory is considered available)
MEMORY_SAFETY_MARGIN: float = 0.9
# DEFAULT_SAFETY_MARGIN: Factor applied in compute_optimal_batch_size for batch memory calculation
# (e.g., 0.8 means use 80% of available memory for batch sizing)
DEFAULT_SAFETY_MARGIN: float = 0.8

# Default batch size settings
DEFAULT_MIN_BATCH_SIZE: int = 1
DEFAULT_MAX_BATCH_SIZE: int = 32
DEFAULT_BATCH_SIZE_WHEN_DISABLED: int = 4

# Model overhead multiplier (parameters + activations + gradients)
DEFAULT_MODEL_OVERHEAD: float = 2.5

# Type variable for generic return types
T = TypeVar("T")


class DeviceType(Enum):
    """Available computation device types."""

    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon GPU
    AUTO = "auto"


@dataclass
class GPUInfo:
    """Information about a GPU device.

    Attributes:
        device_id: CUDA device index.
        name: GPU device name.
        total_memory_mb: Total GPU memory in megabytes.
        free_memory_mb: Free GPU memory in megabytes.
        used_memory_mb: Used GPU memory in megabytes.
        compute_capability: CUDA compute capability tuple (major, minor).
        multi_processor_count: Number of streaming multiprocessors.
    """

    device_id: int
    name: str
    total_memory_mb: float
    free_memory_mb: float
    used_memory_mb: float
    compute_capability: tuple[int, int]
    multi_processor_count: int

    @property
    def memory_utilization(self) -> float:
        """Get GPU memory utilization as a percentage (0-100)."""
        if self.total_memory_mb > 0:
            return (self.used_memory_mb / self.total_memory_mb) * 100
        return 0.0

    @property
    def available_memory_mb(self) -> float:
        return self.free_memory_mb * MEMORY_SAFETY_MARGIN


@dataclass
class GPUConfig:
    """Configuration for GPU acceleration.

    Attributes:
        enabled: Whether GPU acceleration is enabled.
        device: Device type (auto, cuda, cpu, mps).
        device_id: Specific GPU device ID (-1 for auto-select best).
        memory_fraction: Maximum fraction of GPU memory to use.
        fallback_to_cpu: Whether to fall back to CPU on GPU errors.
        enable_memory_growth: Dynamically allocate memory as needed.
        pinned_memory: Use pinned memory for faster CPU-GPU transfers.
        async_transfer: Enable asynchronous data transfers.
        batch_size_auto: Automatically adjust batch size based on memory.
        min_batch_size: Minimum batch size when auto-adjusting.
        max_batch_size: Maximum batch size when auto-adjusting.
        memory_monitor_interval: Seconds between memory checks.
        oom_retry_enabled: Retry with smaller batch on OOM errors.
        fp16_enabled: Use half-precision (FP16) for faster inference.
        cudnn_benchmark: Enable cuDNN benchmark mode for optimal kernels.
    """

    enabled: bool = True
    device: str = "auto"
    device_id: int = -1
    memory_fraction: float = DEFAULT_MEMORY_FRACTION
    fallback_to_cpu: bool = True
    enable_memory_growth: bool = True
    pinned_memory: bool = True
    async_transfer: bool = True
    batch_size_auto: bool = True
    min_batch_size: int = DEFAULT_MIN_BATCH_SIZE
    max_batch_size: int = DEFAULT_MAX_BATCH_SIZE
    memory_monitor_interval: float = 0.5
    oom_retry_enabled: bool = True
    fp16_enabled: bool = False
    cudnn_benchmark: bool = True


@dataclass
class DeviceSelection:
    """Result of device selection process.

    Attributes:
        device: Selected PyTorch device string.
        device_type: Device type enum value.
        device_name: Human-readable device name.
        gpu_info: GPU info if a GPU was selected.
        fallback_used: Whether CPU fallback was used.
        reason: Reason for device selection.
    """

    device: str
    device_type: DeviceType
    device_name: str
    gpu_info: Optional[GPUInfo] = None
    fallback_used: bool = False
    reason: str = ""


class GPUError(Exception):
    """Exception raised for GPU-related errors."""

    def __init__(
        self,
        message: str,
        *,
        device: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ) -> None:
        """Initialize GPU error.

        Args:
            message: Error description.
            device: Device that caused the error.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.device = device
        self.original_exception = original_exception


class OutOfMemoryError(GPUError):
    """Exception raised when GPU runs out of memory."""

    pass


def _get_gpu_logger() -> "Logger":
    """Get the GPU module logger (lazy initialization)."""
    return get_logger("gpu")


def _parse_device_id(device: str) -> int:
    """Parse device ID from device string.
    
    Args:
        device: Device string like 'cuda:0', 'cuda', or 'cpu'.
        
    Returns:
        Device ID integer, or 0 if not specified.
        
    Examples:
        >>> _parse_device_id("cuda:0")
        0
        >>> _parse_device_id("cuda:2")
        2
        >>> _parse_device_id("cuda")
        0
    """
    if ":" in device:
        try:
            return int(device.split(":")[1])
        except (IndexError, ValueError):
            return 0
    return 0


def _create_cpu_selection(
    reason: str,
    fallback_used: bool = False,
) -> DeviceSelection:
    """Create a DeviceSelection for CPU.
    
    Args:
        reason: Reason for CPU selection.
        fallback_used: Whether this is a fallback from GPU.
        
    Returns:
        DeviceSelection configured for CPU.
    """
    return DeviceSelection(
        device="cpu",
        device_type=DeviceType.CPU,
        device_name="CPU",
        fallback_used=fallback_used,
        reason=reason,
    )


def is_torch_available() -> bool:
    """Check if PyTorch is available."""
    return TORCH_AVAILABLE


def is_cuda_available() -> bool:
    """Check if CUDA is available."""
    if not TORCH_AVAILABLE:
        return False
    return torch is not None and torch.cuda.is_available()  # type: ignore[no-any-return]


def is_mps_available() -> bool:
    """Check if MPS (Apple Silicon) is available."""
    if not TORCH_AVAILABLE:
        return False
    if torch is None:
        return False
    return (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()  # type: ignore[no-any-return]
        and torch.backends.mps.is_built()  # type: ignore[no-any-return]
    )


def get_device_count() -> int:
    """Get the number of available CUDA devices."""
    if not is_cuda_available():
        return 0
    return torch.cuda.device_count()  # type: ignore[no-any-return]


def get_gpu_info(device_id: int = 0) -> Optional[GPUInfo]:
    """Get detailed information about a specific GPU device.

    Args:
        device_id: CUDA device index.

    Returns:
        GPUInfo object if the device exists, None otherwise.
    """
    logger = _get_gpu_logger()

    if not is_cuda_available():
        return None

    try:
        if device_id < 0 or device_id >= get_device_count():
            logger.warning(f"Invalid device_id: {device_id}")
            return None

        # Get device properties
        props = torch.cuda.get_device_properties(device_id)  # type: ignore[misc]

        # Get memory info
        torch.cuda.set_device(device_id)  # type: ignore[misc]
        free, total = torch.cuda.mem_get_info(device_id)  # type: ignore[misc]

        return GPUInfo(
            device_id=device_id,
            name=props.name,  # type: ignore[misc]
            total_memory_mb=total / BYTES_PER_MB,
            free_memory_mb=free / BYTES_PER_MB,
            used_memory_mb=(total - free) / BYTES_PER_MB,
            compute_capability=(props.major, props.minor),  # type: ignore[misc]
            multi_processor_count=props.multi_processor_count,  # type: ignore[misc]
        )

    except Exception as e:
        log_exception("Failed to get GPU info", exception=e, device_id=device_id)
        return None


def get_all_gpu_info() -> list[GPUInfo]:
    """Get information about all available GPU devices.

    Returns:
        List of GPUInfo objects for all available GPUs.
    """
    devices: list[GPUInfo] = []
    for i in range(get_device_count()):
        info = get_gpu_info(i)
        if info is not None:
            devices.append(info)
    return devices


def select_best_gpu(
    min_memory_mb: Optional[float] = None,
    prefer_memory: bool = True,
) -> Optional[int]:
    """Select the best available GPU device.

    Args:
        min_memory_mb: Minimum required GPU memory in MB.
        prefer_memory: If True, prefer GPU with most free memory;
                      otherwise prefer GPU with highest compute capability.

    Returns:
        Device ID of the best GPU, or None if no suitable GPU found.
    """
    logger = _get_gpu_logger()

    devices = get_all_gpu_info()
    if not devices:
        logger.debug("No GPU devices available")
        return None

    # Filter by minimum memory requirement
    if min_memory_mb is not None:
        devices = [d for d in devices if d.free_memory_mb >= min_memory_mb]
        if not devices:
            logger.warning(f"No GPU with minimum {min_memory_mb}MB free memory available")
            return None

    if prefer_memory:
        # Sort by free memory (descending)
        devices.sort(key=lambda d: d.free_memory_mb, reverse=True)
    else:
        # Sort by compute capability then multiprocessor count
        devices.sort(
            key=lambda d: (d.compute_capability, d.multi_processor_count),
            reverse=True,
        )

    best = devices[0]
    logger.info(
        f"Selected GPU {best.device_id}: {best.name} "
        f"({best.free_memory_mb:.0f}MB free / {best.total_memory_mb:.0f}MB total)"
    )
    return best.device_id


def select_device(config: Optional[GPUConfig] = None) -> DeviceSelection:
    """Select the best computation device based on configuration and availability.

    Args:
        config: GPU configuration. Uses defaults if None.

    Returns:
        DeviceSelection with the selected device information.
    """
    logger = _get_gpu_logger()
    config = config or GPUConfig()

    # If explicitly disabled, use CPU
    if not config.enabled:
        return _create_cpu_selection("GPU disabled in configuration")

    # Handle explicit device selection
    device_str = config.device.lower()

    if device_str == "cpu":
        return _create_cpu_selection("CPU explicitly requested")

    if device_str == "mps":
        if is_mps_available():
            return DeviceSelection(
                device="mps",
                device_type=DeviceType.MPS,
                device_name="Apple Silicon GPU",
                reason="MPS (Apple Silicon) explicitly requested and available",
            )
        if config.fallback_to_cpu:
            logger.warning("MPS requested but not available, falling back to CPU")
            return _create_cpu_selection(
                "MPS requested but unavailable, CPU fallback enabled",
                fallback_used=True,
            )
        raise GPUError("MPS requested but not available and fallback disabled")

    # Handle CUDA/AUTO selection
    if device_str in ("cuda", "auto", "gpu"):
        if is_cuda_available():
            # Select specific device or best available
            if config.device_id >= 0:
                gpu_info = get_gpu_info(config.device_id)
                if gpu_info is None:
                    if config.fallback_to_cpu:
                        logger.warning(
                            f"CUDA device {config.device_id} not available, falling back to CPU"
                        )
                        return _create_cpu_selection(
                            f"CUDA device {config.device_id} unavailable, CPU fallback enabled",
                            fallback_used=True,
                        )
                    raise GPUError(f"CUDA device {config.device_id} not available")

                return DeviceSelection(
                    device=f"cuda:{config.device_id}",
                    device_type=DeviceType.CUDA,
                    device_name=gpu_info.name,
                    gpu_info=gpu_info,
                    reason=f"CUDA device {config.device_id} explicitly requested",
                )

            # Auto-select best GPU
            best_id = select_best_gpu()
            if best_id is not None:
                gpu_info = get_gpu_info(best_id)
                return DeviceSelection(
                    device=f"cuda:{best_id}",
                    device_type=DeviceType.CUDA,
                    device_name=gpu_info.name if gpu_info else f"CUDA:{best_id}",
                    gpu_info=gpu_info,
                    reason="Best available GPU auto-selected",
                )

        # Try MPS as fallback for auto mode
        if device_str == "auto" and is_mps_available():
            return DeviceSelection(
                device="mps",
                device_type=DeviceType.MPS,
                device_name="Apple Silicon GPU",
                reason="MPS available as fallback (auto mode)",
            )

        # Fall back to CPU
        if config.fallback_to_cpu:
            logger.warning(f"No GPU available for '{device_str}' mode, falling back to CPU")
            return _create_cpu_selection(
                f"No GPU available for '{device_str}' mode, CPU fallback enabled",
                fallback_used=True,
            )

        raise GPUError(f"No GPU available for '{device_str}' mode and fallback disabled")

    # Unknown device type
    if config.fallback_to_cpu:
        logger.warning(f"Unknown device '{device_str}', falling back to CPU")
        return _create_cpu_selection(
            f"Unknown device '{device_str}', CPU fallback enabled",
            fallback_used=True,
        )

    raise GPUError(f"Unknown device type: {device_str}")


def clear_gpu_memory(device: Optional[str] = None) -> None:
    """Clear GPU memory cache.

    Args:
        device: Device to clear. If None, clears all GPU memory.
    """
    logger = _get_gpu_logger()

    if not is_cuda_available():
        return

    try:
        # Run garbage collection
        gc.collect()

        # Clear PyTorch cache
        if device is not None and device.startswith("cuda"):
            device_id = _parse_device_id(device)
            torch.cuda.set_device(device_id)  # type: ignore[misc]

        torch.cuda.empty_cache()  # type: ignore[misc]
        torch.cuda.synchronize()  # type: ignore[misc]

        logger.debug("GPU memory cache cleared")

    except Exception as e:
        log_exception("Failed to clear GPU memory", exception=e)


def get_memory_usage(device: str = "cuda:0") -> tuple[float, float, float]:
    """Get current GPU memory usage.

    Args:
        device: Device to query.

    Returns:
        Tuple of (used_mb, free_mb, total_mb).
    """
    if not is_cuda_available():
        return (0.0, 0.0, 0.0)

    try:
        device_id = _parse_device_id(device)
        torch.cuda.set_device(device_id)  # type: ignore[misc]
        free, total = torch.cuda.mem_get_info()  # type: ignore[misc]
        used = total - free

        return (
            used / BYTES_PER_MB,
            free / BYTES_PER_MB,
            total / BYTES_PER_MB,
        )
    except Exception as e:
        # Log the exception but don't propagate - this is often called for monitoring
        logger = _get_gpu_logger()
        logger.debug(f"Could not get memory usage for device {device}: {e}")
        return (0.0, 0.0, 0.0)


def estimate_memory_requirement(
    batch_size: int,
    image_height: int,
    image_width: int,
    channels: int = 3,
    dtype_bytes: int = 4,  # float32
    model_overhead: float = DEFAULT_MODEL_OVERHEAD,
) -> float:
    """Estimate GPU memory requirement for a batch.

    Args:
        batch_size: Number of images in the batch. Must be positive.
        image_height: Height of images in pixels. Must be positive.
        image_width: Width of images in pixels. Must be positive.
        channels: Number of channels (default 3 for RGB). Must be positive.
        dtype_bytes: Bytes per element (4 for float32, 2 for float16). Must be positive.
        model_overhead: Multiplier for model overhead (parameters + activations + gradients). Must be positive.

    Returns:
        Estimated memory requirement in megabytes.

    Raises:
        ValueError: If any parameter is not positive.
    """
    # Validate inputs
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if image_height <= 0:
        raise ValueError(f"image_height must be positive, got {image_height}")
    if image_width <= 0:
        raise ValueError(f"image_width must be positive, got {image_width}")
    if channels <= 0:
        raise ValueError(f"channels must be positive, got {channels}")
    if dtype_bytes <= 0:
        raise ValueError(f"dtype_bytes must be positive, got {dtype_bytes}")
    if model_overhead <= 0:
        raise ValueError(f"model_overhead must be positive, got {model_overhead}")

    # Calculate tensor size
    elements = batch_size * channels * image_height * image_width
    tensor_bytes = elements * dtype_bytes

    # Add model overhead
    total_bytes = tensor_bytes * model_overhead

    return total_bytes / BYTES_PER_MB


def compute_optimal_batch_size(
    config: GPUConfig,
    image_height: int,
    image_width: int,
    channels: int = 3,
    use_fp16: bool = False,
    safety_margin: float = DEFAULT_SAFETY_MARGIN,
) -> int:
    """Compute the optimal batch size based on available GPU memory.

    Args:
        config: GPU configuration.
        image_height: Height of images in pixels. Must be positive.
        image_width: Width of images in pixels. Must be positive.
        channels: Number of channels. Must be positive.
        use_fp16: Whether FP16 is being used.
        safety_margin: Fraction of available memory to use. Must be between 0 and 1.

    Returns:
        Optimal batch size within configured limits.
    """
    # Validate inputs
    if image_height <= 0:
        raise ValueError(f"image_height must be positive, got {image_height}")
    if image_width <= 0:
        raise ValueError(f"image_width must be positive, got {image_width}")
    if channels <= 0:
        raise ValueError(f"channels must be positive, got {channels}")
    if not 0 < safety_margin <= 1:
        raise ValueError(f"safety_margin must be between 0 and 1, got {safety_margin}")

    logger = _get_gpu_logger()

    if not config.batch_size_auto:
        return max(config.min_batch_size, min(config.max_batch_size, DEFAULT_BATCH_SIZE_WHEN_DISABLED))

    if not is_cuda_available():
        return config.min_batch_size

    try:
        # Get available memory
        used_mb, free_mb, total_mb = get_memory_usage()
        available_mb = total_mb * config.memory_fraction * safety_margin - used_mb
        available_mb = max(available_mb, 0)

        # Memory per element
        dtype_bytes = 2 if use_fp16 else 4

        # Binary search for optimal batch size
        low, high = config.min_batch_size, config.max_batch_size
        optimal = config.min_batch_size

        while low <= high:
            mid = (low + high) // 2
            required_mb = estimate_memory_requirement(
                mid, image_height, image_width, channels, dtype_bytes
            )

            if required_mb <= available_mb:
                optimal = mid
                low = mid + 1
            else:
                high = mid - 1

        logger.debug(
            f"Computed optimal batch size: {optimal} "
            f"(available: {available_mb:.0f}MB, "
            f"required: {estimate_memory_requirement(optimal, image_height, image_width, channels, dtype_bytes):.0f}MB)"
        )

        return max(config.min_batch_size, min(optimal, config.max_batch_size))

    except Exception as e:
        log_exception("Failed to compute optimal batch size", exception=e)
        return config.min_batch_size


def create_pinned_tensor(
    shape: tuple[int, ...],
    dtype: Optional["torch.dtype"] = None,
) -> Optional["torch.Tensor"]:

    """Create a pinned memory tensor for faster CPU-GPU transfers.

    Args:
        shape: Shape of the tensor.
        dtype: Data type of the tensor.

    Returns:
        Pinned tensor if CUDA is available, regular tensor otherwise.
    """
    if not is_cuda_available():
        return None

    if dtype is None:
        dtype = torch.float32

    tensor = torch.empty(shape, dtype=dtype)
    tensor = tensor.pin_memory()
    return tensor


def transfer_to_gpu(
    data: np.ndarray,
    device: str,
    pinned: bool = True,
    async_transfer: bool = True,
    fp16: bool = False,
) -> "torch.Tensor":
    """Transfer numpy array to GPU with optimizations.

    Args:
        data: Numpy array to transfer.
        device: Target device.
        pinned: Use pinned memory for faster transfer.
        async_transfer: Use asynchronous transfer.
        fp16: Convert to half precision.

    Returns:
        Tensor on the target device.
    """
    if not TORCH_AVAILABLE or torch is None:
        raise GPUError("PyTorch not available")

    # Convert to tensor
    tensor = torch.from_numpy(data)

    # Convert dtype if needed
    if fp16:
        tensor = tensor.half()

    # Use pinned memory for faster transfer
    if pinned and device.startswith("cuda") and not tensor.is_pinned():
        tensor = tensor.pin_memory()

    # Transfer to device
    non_blocking = async_transfer and device.startswith("cuda")
    tensor = tensor.to(device, non_blocking=non_blocking)

    return tensor


def transfer_to_cpu(
    tensor: "torch.Tensor",
    async_transfer: bool = True,
) -> np.ndarray:
    """Transfer tensor from GPU to CPU with optimizations.

    Args:
        tensor: Tensor to transfer.
        async_transfer: Use asynchronous transfer.

    Returns:
        Numpy array on CPU.
    """
    non_blocking = async_transfer and tensor.device.type == "cuda"
    return tensor.detach().cpu().numpy(non_blocking=non_blocking)  # type: ignore[no-any-return]


def with_oom_retry(
    func: Callable[..., T],
    config: GPUConfig,
    initial_batch_size: int,
    *args: Any,
    **kwargs: Any,
) -> tuple[T, int]:
    """Execute a function with OOM retry logic.

    If the function fails with OOM, it will be retried with progressively
    smaller batch sizes until it succeeds or minimum batch size is reached.

    Args:
        func: Function to execute.
        config: GPU configuration.
        initial_batch_size: Starting batch size.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        Tuple of (function result, final batch size used).

    Raises:
        OutOfMemoryError: If all retry attempts fail.
    """
    logger = _get_gpu_logger()

    batch_size = initial_batch_size

    while batch_size >= config.min_batch_size:
        try:
            result = func(*args, **kwargs)
            return result, batch_size

        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str or "oom" in error_str:
                logger.warning(
                    f"GPU out of memory with batch_size={batch_size}, "
                    f"retrying with {batch_size // 2}"
                )

                # Clear memory and retry
                clear_gpu_memory()

                batch_size = batch_size // 2
                if batch_size < config.min_batch_size:
                    break
            else:
                raise  # Re-raise non-OOM RuntimeErrors
            continue  # Retry with smaller batch size
    raise OutOfMemoryError(
        f"Failed to execute even with minimum batch_size={config.min_batch_size}",
        device=None,
    )


def configure_cudnn(device: str, benchmark: bool = True, deterministic: bool = False) -> None:
    """Configure cuDNN settings for optimal performance.

    Args:
        device: Target device.
        benchmark: Enable cuDNN benchmark for optimal kernel selection.
        deterministic: Use deterministic algorithms (slower but reproducible).
    """
    if not is_cuda_available() or not device.startswith("cuda"):
        return

    if benchmark and not deterministic:
        torch.backends.cudnn.benchmark = True  # type: ignore[misc]
        torch.backends.cudnn.deterministic = False  # type: ignore[misc]
    elif deterministic:
        torch.backends.cudnn.benchmark = False  # type: ignore[misc]
        torch.backends.cudnn.deterministic = True  # type: ignore[misc]


def setup_device(
    config: Optional[GPUConfig] = None,
    device_override: Optional[str] = None,
) -> DeviceSelection:
    """Set up and configure the computation device.

    This is the main entry point for device initialization, combining
    device selection with configuration and optimization setup.

    Args:
        config: GPU configuration. Uses defaults if None.
        device_override: Override device string (e.g., from CLI).

    Returns:
        DeviceSelection with the configured device.
    """
    logger = _get_gpu_logger()
    config = config or GPUConfig()

    # Apply device override
    if device_override is not None:
        config.device = device_override

    # Select device
    selection = select_device(config)

    logger.info(
        f"Device setup complete: {selection.device_name} ({selection.device}) - {selection.reason}"
    )

    # Configure cuDNN for CUDA
    if selection.device_type == DeviceType.CUDA:
        configure_cudnn(
            selection.device,
            benchmark=config.cudnn_benchmark,
        )

        # Set memory fraction
        if config.memory_fraction < 1.0:
            device_id = int(selection.device.split(":")[1]) if ":" in selection.device else 0
            torch.cuda.set_per_process_memory_fraction(  # type: ignore[misc]
                config.memory_fraction, device=device_id
            )

    return selection


# Module-level exports
__all__ = [
    # Enums
    "DeviceType",
    # Dataclasses
    "GPUInfo",
    "GPUConfig",
    "DeviceSelection",
    # Exceptions
    "GPUError",
    "OutOfMemoryError",
    # Utility functions
    "is_torch_available",
    "is_cuda_available",
    "is_mps_available",
    "get_device_count",
    "get_gpu_info",
    "get_all_gpu_info",
    "select_best_gpu",
    "select_device",
    "clear_gpu_memory",
    "get_memory_usage",
    "estimate_memory_requirement",
    "compute_optimal_batch_size",
    "create_pinned_tensor",
    "transfer_to_gpu",
    "transfer_to_cpu",
    "with_oom_retry",
    "configure_cudnn",
    "setup_device",
]
