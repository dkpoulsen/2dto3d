"""Utility functions and helpers."""

from video2d3d.utils.config import (
    Config,
    get_config,
    get_config_path,
    get_environment,
    load_config,
    reload_config,
)
from video2d3d.utils.logger import (
    LogLevel,
    configure_logging,
    get_logger,
    log_context,
    log_exception,
    log_performance,
    log_video_processing,
    log_model_inference,
    log_memory_usage,
    set_log_level,
    is_logging_configured,
)
from video2d3d.utils.gpu import (
    # Classes
    GPUConfig,
    GPUInfo,
    DeviceSelection,
    DeviceType,
    # Exceptions
    GPUError,
    OutOfMemoryError,
    # Functions
    is_torch_available,
    is_cuda_available,
    is_mps_available,
    get_device_count,
    get_gpu_info,
    get_all_gpu_info,
    select_best_gpu,
    select_device,
    clear_gpu_memory,
    get_memory_usage,
    estimate_memory_requirement,
    compute_optimal_batch_size,
    create_pinned_tensor,
    transfer_to_gpu,
    transfer_to_cpu,
    with_oom_retry,
    configure_cudnn,
    setup_device,
)
from video2d3d.utils.error_recovery import (
    # Configuration
    ErrorRecoveryConfig,
    RecoveryStats,
    RecoveryStrategy,
    BackoffStrategy,
    # Exceptions
    RecoveryError,
    MaxRetriesExceededError,
    AllModelsFailedError,
    FrameRecoveryFailedError,
    # Classes
    FrameRecoveryManager,
    ModelFallbackChain,
    RecoveryContext,
    # Decorators
    recovery_with_fallback,
    create_recovery_decorator,
    # Functions
    create_recovery_config_from_dict,
    # Constants
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_MAX_RETRY_DELAY_SECONDS,
    DEFAULT_MODEL_FALLBACK_CHAIN,
    DEFAULT_CPU_FALLBACK_ENABLED,
    DEFAULT_SKIP_ON_MAX_RETRIES,
    # Error Detection Constants
    OOM_ERROR_SUBSTRINGS,
    CUDA_ERROR_SUBSTRINGS,
    TIMEOUT_ERROR_SUBSTRINGS,
)

__all__ = [
    # Config
    "Config",
    "get_config",
    "get_config_path",
    "get_environment",
    "load_config",
    "reload_config",
    # Logging
    "LogLevel",
    "configure_logging",
    "get_logger",
    "log_context",
    "log_exception",
    "log_performance",
    "log_video_processing",
    "log_model_inference",
    "log_memory_usage",
    "set_log_level",
    "is_logging_configured",
    # GPU
    "GPUConfig",
    "GPUInfo",
    "DeviceSelection",
    "DeviceType",
    "GPUError",
    "OutOfMemoryError",
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
    # Error Recovery - Configuration
    "ErrorRecoveryConfig",
    "RecoveryStats",
    "RecoveryStrategy",
    "BackoffStrategy",
    # Error Recovery - Exceptions
    "RecoveryError",
    "MaxRetriesExceededError",
    "AllModelsFailedError",
    "FrameRecoveryFailedError",
    # Error Recovery - Classes
    "FrameRecoveryManager",
    "ModelFallbackChain",
    "RecoveryContext",
    # Error Recovery - Decorators
    "recovery_with_fallback",
    "create_recovery_decorator",
    # Error Recovery - Functions
    "create_recovery_config_from_dict",
    # Error Recovery - Constants
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY_SECONDS",
    "DEFAULT_BACKOFF_FACTOR",
    "DEFAULT_MAX_RETRY_DELAY_SECONDS",
    "DEFAULT_MODEL_FALLBACK_CHAIN",
    "DEFAULT_CPU_FALLBACK_ENABLED",
    "DEFAULT_SKIP_ON_MAX_RETRIES",
    # Error Detection Constants
    "OOM_ERROR_SUBSTRINGS",
    "CUDA_ERROR_SUBSTRINGS",
    "TIMEOUT_ERROR_SUBSTRINGS",
]
