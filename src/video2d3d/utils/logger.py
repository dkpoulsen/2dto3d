"""Structured logging system with multiple log levels, file rotation, and error tracking.

This module provides a centralized logging system built on loguru that supports:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File rotation with configurable size and retention
- Console output with colorization
- Detailed error tracking with exception context
- Structured JSON logging for production
- Context-aware logging with extra fields
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from loguru import Logger

from loguru import logger

from video2d3d.utils.config import LoggingConfig, get_config

# Remove default handler
logger.remove()

# Global flag to track if logging has been configured (thread-safe)
_logging_configured: bool = False
_logging_lock = threading.Lock()


class LogLevel:
    """Log level constants matching standard logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def get_log_format(
    include_json: bool = False,
    colorize: bool = True,
) -> str:
    """Get the log format string based on configuration.

    Args:
        include_json: If True, return JSON format for structured logging.
        colorize: If True, include color tags in the format.

    Returns:
        Format string for loguru.
    """
    if include_json:
        # Structured JSON format for production
        return (
            '{{"timestamp": "{time:YYYY-MM-DDTHH:mm:ss.SSSZ}", '
            '"level": "{level}", '
            '"logger": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}", '
            '"extra": {extra}}}'
        )

    # Human-readable format with optional colors
    base_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    if not colorize:
        # Remove color tags
        base_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )

    return base_format


def configure_logging(
    config: Optional[LoggingConfig] = None,
    *,
    log_level: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    rotation: Optional[str] = None,
    retention: Optional[str] = None,
    colorize: Optional[bool] = None,
    console_output: bool = True,
    json_format: bool = False,
) -> None:
    """Configure the logging system with the given settings.

    This function should be called once at application startup. Subsequent
    calls will reset the logging configuration.

    Args:
        config: LoggingConfig object. If None, loads from global config.
        log_level: Override log level from config.
        log_file: Override log file path from config.
        rotation: Override rotation setting from config.
        retention: Override retention setting from config.
        colorize: Override colorize setting from config.
        console_output: Whether to output to console. Default True.
        json_format: Use JSON structured logging format. Default False.
    """
    global _logging_configured

    # Load config if not provided
    if config is None:
        try:
            app_config = get_config()
            config = app_config.logging
        except Exception:
            # Fallback to defaults
            config = LoggingConfig()

    # Apply overrides
    level = log_level or config.level
    file_path = Path(log_file) if log_file else Path(config.file)
    rot = rotation or config.rotation
    ret = retention or config.retention
    color = colorize if colorize is not None else config.colorize

    # Reset logging configuration
    logger.remove()
    _logging_configured = False

    # Create log directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Console handler
    if console_output:
        console_format = get_log_format(include_json=json_format, colorize=color)
        logger.add(
            sys.stderr,
            format=console_format,
            level=level,
            colorize=color,
            backtrace=True,
            diagnose=True,
        )

    # File handler with rotation
    file_format = get_log_format(include_json=json_format, colorize=False)
    logger.add(
        str(file_path),
        format=file_format,
        level=level,
        rotation=rot,
        retention=ret,
        compression="gz",
        backtrace=True,
        diagnose=True,
    )

    # Add error-specific file handler for error tracking
    error_log_path = file_path.parent / f"{file_path.stem}_errors{file_path.suffix}"
    logger.add(
        str(error_log_path),
        format=file_format,
        level="ERROR",
        rotation=rot,
        retention=ret,
        compression="gz",
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["level"].no >= logger.level("ERROR").no,
    )

    with _logging_lock:
        _logging_configured = True
    logger.debug(f"Logging configured: level={level}, file={file_path}")


def get_logger(name: Optional[str] = None) -> Logger:
    """Get a logger instance with optional name binding.

    Args:
        name: Logger name. If provided, binds it to the logger context.

    Returns:
        Logger instance with optional name binding.
    """
    with _logging_lock:
        if not _logging_configured:
            configure_logging()

    if name:
        return logger.bind(name=name)
    return logger


def log_context(**kwargs: Any) -> Logger:
    """Create a logging context with extra fields.

    All logged messages within this context will include the extra fields.

    Args:
        **kwargs: Key-value pairs to add to the logging context.

    Returns:
        Logger with context binding.

    Example:
        log = log_context(user_id="123", session="abc")
        log.info("Processing request")  # Will include user_id and session
    """
    with _logging_lock:
        if not _logging_configured:
            configure_logging()

    return logger.bind(**kwargs)


def log_exception(
    message: str,
    exception: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
    """Log an exception with detailed context.

    Args:
        message: Error message.
        exception: Exception instance. If None, uses current exception context.
        **kwargs: Additional context to log.
    """
    if not _logging_configured:
        configure_logging()

    context_logger = logger.bind(**kwargs) if kwargs else logger

    if exception is not None:
        # Log the provided exception with full traceback
        context_logger.opt(exception=True).error(
            f"{message}: {type(exception).__name__}: {exception}"
        )
    else:
        # Use the current exception context (must be called from within except block)
        context_logger.exception(message)


def log_performance(
    operation: str,
    duration_ms: float,
    **metrics: Any,
) -> None:
    """Log performance metrics for an operation.

    Args:
        operation: Name of the operation.
        duration_ms: Duration in milliseconds.
        **metrics: Additional performance metrics.
    """
    if not _logging_configured:
        configure_logging()

    logger.bind(
        operation=operation,
        duration_ms=duration_ms,
        **metrics,
    ).info(f"Performance: {operation} completed in {duration_ms:.2f}ms")


def log_video_processing(
    input_file: str,
    output_file: str,
    frames_processed: int,
    total_frames: int,
    **kwargs: Any,
) -> None:
    """Log video processing progress.

    Args:
        input_file: Input video file path.
        output_file: Output video file path.
        frames_processed: Number of frames processed.
        total_frames: Total number of frames.
        **kwargs: Additional context.
    """
    if not _logging_configured:
        configure_logging()

    progress = (frames_processed / total_frames * 100) if total_frames > 0 else 0
    logger.bind(
        input_file=input_file,
        output_file=output_file,
        frames_processed=frames_processed,
        total_frames=total_frames,
        progress_percent=f"{progress:.1f}%",
        **kwargs,
    ).info(f"Processing: {frames_processed}/{total_frames} frames ({progress:.1f}%)")


def log_model_inference(
    model_name: str,
    batch_size: int,
    inference_time_ms: float,
    **kwargs: Any,
) -> None:
    """Log model inference metrics.

    Args:
        model_name: Name of the model.
        batch_size: Batch size used for inference.
        inference_time_ms: Inference time in milliseconds.
        **kwargs: Additional metrics.
    """
    if not _logging_configured:
        configure_logging()

    logger.bind(
        model_name=model_name,
        batch_size=batch_size,
        inference_time_ms=inference_time_ms,
        **kwargs,
    ).debug(
        f"Model inference: {model_name} processed {batch_size} items in {inference_time_ms:.2f}ms"
    )


def log_memory_usage(
    operation: str,
    memory_mb: float,
    peak_memory_mb: Optional[float] = None,
    **kwargs: Any,
) -> None:
    """Log memory usage for an operation.

    Args:
        operation: Name of the operation.
        memory_mb: Current memory usage in MB.
        peak_memory_mb: Peak memory usage in MB.
        **kwargs: Additional metrics.
    """
    if not _logging_configured:
        configure_logging()

    context = {"operation": operation, "memory_mb": memory_mb, **kwargs}
    if peak_memory_mb is not None:
        context["peak_memory_mb"] = peak_memory_mb

    logger.bind(**context).debug(f"Memory: {operation} using {memory_mb:.1f}MB")


def set_log_level(level: str) -> None:
    """Dynamically change the log level.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    if not _logging_configured:
        configure_logging()

    # Reconfigure with new level
    config = get_config().logging
    configure_logging(config, log_level=level)
    logger.info(f"Log level changed to {level}")


def is_logging_configured() -> bool:
    """Check if logging has been configured.

    Returns:
        True if logging has been configured, False otherwise.
    """
    return _logging_configured


# Convenience exports
__all__ = [
    "LogLevel",
    "configure_logging",
    "get_logger",
    "get_log_format",
    "log_context",
    "log_exception",
    "log_performance",
    "log_video_processing",
    "log_model_inference",
    "log_memory_usage",
    "set_log_level",
    "is_logging_configured",
    "logger",
]
