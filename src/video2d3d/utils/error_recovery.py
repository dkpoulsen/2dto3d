"""Error recovery mechanisms for automatic retry and fallback handling.

This module provides robust error recovery capabilities including:
- Automatic retry with configurable backoff strategies
- Model fallback chains for alternative model switching
- Frame-level recovery tracking
- Configurable recovery strategies

Example usage:
    ```python
    from video2d3d.utils.error_recovery import (
        ErrorRecoveryConfig,
        FrameRecoveryManager,
        ModelFallbackChain,
        recovery_with_fallback,
    )

    # Configure recovery
    config = ErrorRecoveryConfig(
        max_retries=3,
        retry_backoff_factor=2.0,
        model_fallback_chain=["midas_small", "dpt_hybrid"],
    )

    # Use with depth estimation
    recovery_manager = FrameRecoveryManager(config)
    result = recovery_manager.process_with_recovery(
        frame,
        process_fn=depth_estimator.estimate_depth
    )
    ```
"""

from __future__ import annotations

import functools
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Generic, List, Optional, TypeVar

import numpy as np

from video2d3d.utils.logger import get_logger

if TYPE_CHECKING:
    from loguru import Logger


# ---------------------------------------------------------------------------
# Type Variables
# ---------------------------------------------------------------------------

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
FrameT = np.ndarray


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_DELAY_SECONDS: float = 0.1
DEFAULT_BACKOFF_FACTOR: float = 2.0
DEFAULT_MAX_RETRY_DELAY_SECONDS: float = 30.0
DEFAULT_MODEL_FALLBACK_CHAIN: List[str] = ["midas_small"]
DEFAULT_CPU_FALLBACK_ENABLED: bool = True
DEFAULT_SKIP_ON_MAX_RETRIES: bool = False  # If True, skip frame after max retries

# Exception type detection constants (avoid magic strings)
OOM_ERROR_SUBSTRINGS: tuple[str, ...] = ("out of memory", "cuda out of memory", "oom")
CUDA_ERROR_SUBSTRINGS: tuple[str, ...] = ("cuda", "gpu", "cuda error")
TIMEOUT_ERROR_SUBSTRINGS: tuple[str, ...] = ("timeout", "timed out")


def _fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number iteratively.

    Args:
        n: The index in the Fibonacci sequence (0-indexed).

    Returns:
        The nth Fibonacci number.

    Note:
        Uses iterative approach to avoid recursion overhead.
        Sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21...
    """
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 1, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RecoveryStrategy(Enum):
    """Available recovery strategies for failed operations."""

    RETRY = "retry"  # Retry with same parameters
    BACKOFF = "backoff"  # Retry with exponential backoff
    FALLBACK_MODEL = "fallback_model"  # Switch to alternative model
    FALLBACK_CPU = "fallback_cpu"  # Fall back to CPU processing
    SKIP = "skip"  # Skip the failed item
    RAISE = "raise"  # Raise the exception (no recovery)


class BackoffStrategy(Enum):
    """Available backoff strategies for retry delays."""

    FIXED = "fixed"  # Fixed delay between retries
    LINEAR = "linear"  # Linearly increasing delay
    EXPONENTIAL = "exponential"  # Exponentially increasing delay
    FIBONACCI = "fibonacci"  # Fibonacci-based delay


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RecoveryError(Exception):
    """Base exception for recovery-related errors."""

    def __init__(
        self,
        message: str,
        *,
        attempts: int = 0,
        original_exception: Optional[Exception] = None,
        recovery_strategy: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.original_exception = original_exception
        self.recovery_strategy = recovery_strategy


class MaxRetriesExceededError(RecoveryError):
    """Raised when maximum retry attempts are exceeded."""

    pass


class AllModelsFailedError(RecoveryError):
    """Raised when all models in the fallback chain have failed."""

    def __init__(
        self,
        message: str,
        *,
        failed_models: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.failed_models = failed_models or []


class FrameRecoveryFailedError(RecoveryError):
    """Raised when frame recovery fails after all strategies are exhausted."""

    def __init__(
        self,
        message: str,
        *,
        frame_index: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.frame_index = frame_index


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class ErrorRecoveryConfig:
    """Configuration for error recovery mechanisms.

    Attributes:
        max_retries: Maximum number of retry attempts per operation.
        retry_delay_seconds: Initial delay between retries in seconds.
        backoff_factor: Multiplier for exponential backoff.
        max_retry_delay_seconds: Maximum delay between retries.
        backoff_strategy: Strategy for calculating retry delays.
        model_fallback_chain: Ordered list of models to try if primary fails.
        enable_cpu_fallback: Whether to fall back to CPU on GPU errors.
        skip_on_max_retries: Skip failed frames instead of raising.
        track_failures: Whether to track failed frames for later retry.
        retry_on_exceptions: Exception types that should trigger retry.
        fatal_exceptions: Exception types that should not be retried.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    max_retry_delay_seconds: float = DEFAULT_MAX_RETRY_DELAY_SECONDS
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    model_fallback_chain: List[str] = field(
        default_factory=lambda: list(DEFAULT_MODEL_FALLBACK_CHAIN)
    )
    enable_cpu_fallback: bool = DEFAULT_CPU_FALLBACK_ENABLED
    skip_on_max_retries: bool = DEFAULT_SKIP_ON_MAX_RETRIES
    track_failures: bool = True
    retry_on_exceptions: Optional[List[type[Exception]]] = None
    fatal_exceptions: Optional[List[type[Exception]]] = None

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")

        if self.retry_delay_seconds < 0:
            raise ValueError(f"retry_delay_seconds must be >= 0, got {self.retry_delay_seconds}")

        if self.backoff_factor < 1.0:
            raise ValueError(f"backoff_factor must be >= 1.0, got {self.backoff_factor}")

        if not self.model_fallback_chain:
            raise ValueError("model_fallback_chain cannot be empty")

    def get_delay_for_attempt(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: The attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        if self.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.retry_delay_seconds

        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.retry_delay_seconds * (attempt + 1)

        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.retry_delay_seconds * (self.backoff_factor**attempt)

        elif self.backoff_strategy == BackoffStrategy.FIBONACCI:
            # Fibonacci sequence starting from 1, 1, 2, 3, 5...
            # Use iterative calculation to avoid list building overhead
            fib_n = _fibonacci(attempt + 1)
            delay = self.retry_delay_seconds * fib_n

        else:
            delay = self.retry_delay_seconds

        return min(delay, self.max_retry_delay_seconds)

    def should_retry_exception(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception that occurred.

        Returns:
            True if the exception should be retried.
        """
        # Check if it's a fatal exception (never retry)
        if self.fatal_exceptions:
            for fatal_type in self.fatal_exceptions:
                if isinstance(exception, fatal_type):
                    return False

        # If specific retry exceptions are defined, check them
        if self.retry_on_exceptions:
            for retry_type in self.retry_on_exceptions:
                if isinstance(exception, retry_type):
                    return True
            return False

        # Default: retry on common transient errors
        # RuntimeError (often OOM), OSError, ConnectionError, etc.
        transient_types = (
            RuntimeError,
            OSError,
            ConnectionError,
            TimeoutError,
        )
        return isinstance(exception, transient_types)


@dataclass
class RecoveryStats:
    """Statistics for recovery operations.

    Attributes:
        total_attempts: Total number of processing attempts.
        successful_recoveries: Number of successful recoveries after retry.
        permanent_failures: Number of failures that couldn't be recovered.
        model_switches: Number of times model was switched.
        cpu_fallbacks: Number of times CPU fallback was used.
        skipped_frames: Number of frames that were skipped.
        total_retry_time_seconds: Total time spent in retries.
    """

    total_attempts: int = 0
    successful_recoveries: int = 0
    permanent_failures: int = 0
    model_switches: int = 0
    cpu_fallbacks: int = 0
    skipped_frames: int = 0
    total_retry_time_seconds: float = 0.0

    @property
    def recovery_rate(self) -> float:
        """Calculate the recovery success rate."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_recoveries / self.total_attempts) * 100

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging."""
        return (
            f"RecoveryStats(attempts={self.total_attempts}, "
            f"recoveries={self.successful_recoveries}, "
            f"failures={self.permanent_failures}, "
            f"rate={self.recovery_rate:.1f}%)"
        )

    def summary(self) -> str:
        """Return a human-readable summary of recovery statistics."""
        return (
            f"Recovery Statistics:\n"
            f"  Total attempts: {self.total_attempts}\n"
            f"  Successful recoveries: {self.successful_recoveries}\n"
            f"  Permanent failures: {self.permanent_failures}\n"
            f"  Recovery rate: {self.recovery_rate:.1f}%\n"
            f"  Model switches: {self.model_switches}\n"
            f"  CPU fallbacks: {self.cpu_fallbacks}\n"
            f"  Skipped frames: {self.skipped_frames}\n"
            f"  Total retry time: {self.total_retry_time_seconds:.2f}s"
        )


# ---------------------------------------------------------------------------
# Frame Recovery Manager
# ---------------------------------------------------------------------------


class FrameRecoveryManager(Generic[InputT, OutputT]):
    """Manages frame-level error recovery with retry and fallback support.

    This class provides comprehensive error recovery for frame processing
    operations, including automatic retries with backoff, model fallback,
    and CPU fallback strategies.

    Example usage:
        ```python
        config = ErrorRecoveryConfig(max_retries=3)
        manager = FrameRecoveryManager(config)

        # Process with recovery
        result = manager.process_with_recovery(
            frame,
            process_fn=depth_estimator.estimate_depth
        )
        ```

    Thread Safety:
        This class uses locks to protect shared state and is safe for use
        across multiple threads processing frames concurrently.
    """

    def __init__(
        self,
        config: Optional[ErrorRecoveryConfig] = None,
        *,
        on_recovery: Optional[Callable[[int, Exception, RecoveryStrategy], None]] = None,
        on_failure: Optional[Callable[[int, Exception], None]] = None,
    ) -> None:
        """Initialize the frame recovery manager.

        Args:
            config: Recovery configuration. If None, uses defaults.
            on_recovery: Callback called when recovery succeeds.
            on_failure: Callback called when recovery fails permanently.
        """
        self.config = config or ErrorRecoveryConfig()
        self.on_recovery = on_recovery
        self.on_failure = on_failure
        self._logger = _get_recovery_logger()
        self._stats = RecoveryStats()
        self._failed_frames: dict[int, tuple[InputT, Exception]] = {}
        # Thread safety locks
        self._stats_lock = threading.Lock()
        self._failed_frames_lock = threading.Lock()

    @property
    def stats(self) -> RecoveryStats:
        """Get recovery statistics (thread-safe copy)."""
        with self._stats_lock:
            # Return a copy to prevent external modification
            return RecoveryStats(
                total_attempts=self._stats.total_attempts,
                successful_recoveries=self._stats.successful_recoveries,
                permanent_failures=self._stats.permanent_failures,
                model_switches=self._stats.model_switches,
                cpu_fallbacks=self._stats.cpu_fallbacks,
                skipped_frames=self._stats.skipped_frames,
                total_retry_time_seconds=self._stats.total_retry_time_seconds,
            )

    def get_failed_frames(self) -> dict[int, tuple[InputT, Exception]]:
        """Get dictionary of failed frames and their exceptions (thread-safe copy)."""
        with self._failed_frames_lock:
            return self._failed_frames.copy()

    def clear_failed_frames(self) -> None:
        """Clear the failed frames tracking (thread-safe)."""
        with self._failed_frames_lock:
            self._failed_frames.clear()

    def process_with_recovery(
        self,
        item: InputT,
        process_fn: Callable[[InputT], OutputT],
        *,
        item_index: Optional[int] = None,
    ) -> OutputT:
        """Process an item with automatic error recovery.

        Args:
            item: The item to process.
            process_fn: The processing function to apply.
            item_index: Optional index for tracking (e.g., frame number).

        Returns:
            The processed output.

        Raises:
            FrameRecoveryFailedError: If all recovery attempts fail.
        """
        last_exception: Optional[Exception] = None
        start_time = time.time()

        for attempt in range(self.config.max_retries + 1):
            with self._stats_lock:
                self._stats.total_attempts += 1

            try:
                result = process_fn(item)

                # Track successful recovery if this wasn't the first attempt
                if attempt > 0:
                    with self._stats_lock:
                        self._stats.successful_recoveries += 1
                    self._logger.info(
                        f"Recovery succeeded on attempt {attempt + 1} for item {item_index}"
                    )
                    if self.on_recovery and last_exception:
                        self.on_recovery(
                            item_index or -1,
                            last_exception,
                            RecoveryStrategy.BACKOFF,
                        )

                return result

            except Exception as e:
                last_exception = e
                self._logger.warning(
                    f"Processing failed for item {item_index}, "
                    f"attempt {attempt + 1}/{self.config.max_retries + 1}: {e}"
                )

                # Check if we should retry this exception
                if not self.config.should_retry_exception(e):
                    self._logger.error(
                        f"Non-retryable exception for item {item_index}: {type(e).__name__}"
                    )
                    break

                # If we have more retries, wait and try again
                if attempt < self.config.max_retries:
                    delay = self.config.get_delay_for_attempt(attempt)
                    with self._stats_lock:
                        self._stats.total_retry_time_seconds += delay
                    self._logger.debug(f"Waiting {delay:.3f}s before retry")
                    time.sleep(delay)

        # All retries exhausted
        with self._stats_lock:
            self._stats.permanent_failures += 1

        # Track failed frame if enabled
        if self.config.track_failures and item_index is not None:
            with self._failed_frames_lock:
                self._failed_frames[item_index] = (item, last_exception)  # type: ignore

        # Call failure callback
        if self.on_failure and last_exception:
            self.on_failure(item_index or -1, last_exception)

        # Skip or raise based on configuration
        if self.config.skip_on_max_retries:
            with self._stats_lock:
                self._stats.skipped_frames += 1
            self._logger.warning(f"Skipping item {item_index} after max retries")
            raise FrameRecoveryFailedError(
                f"Skipped item {item_index} after {self.config.max_retries + 1} attempts",
                frame_index=item_index,
                attempts=self.config.max_retries + 1,
                original_exception=last_exception,
            )

        raise MaxRetriesExceededError(
            f"Max retries exceeded for item {item_index}",
            attempts=self.config.max_retries + 1,
            original_exception=last_exception,
        )

    def process_batch_with_recovery(
        self,
        items: List[InputT],
        process_fn: Callable[[InputT], OutputT],
    ) -> tuple[List[Optional[OutputT]], List[tuple[int, Exception]]]:
        """Process a batch of items with recovery.

        Args:
            items: List of items to process.
            process_fn: Processing function to apply to each item.

        Returns:
            Tuple of (outputs list, errors list with indices).
        """
        outputs: List[Optional[OutputT]] = [None] * len(items)
        errors: List[tuple[int, Exception]] = []

        for idx, item in enumerate(items):
            try:
                outputs[idx] = self.process_with_recovery(item, process_fn, item_index=idx)
            except (MaxRetriesExceededError, FrameRecoveryFailedError) as e:
                errors.append((idx, e.original_exception or e))
                if self.config.skip_on_max_retries:
                    outputs[idx] = None  # type: ignore
                else:
                    raise

        return outputs, errors

    def reset_stats(self) -> None:
        """Reset recovery statistics (thread-safe)."""
        with self._stats_lock:
            self._stats = RecoveryStats()


# ---------------------------------------------------------------------------
# Model Fallback Chain
# ---------------------------------------------------------------------------


class ModelFallbackChain:
    """Manages fallback between multiple depth estimation models.

    This class handles model switching when the primary model fails,
    trying alternative models in sequence until one succeeds or all fail.

    Example usage:
        ```python
        fallback_chain = ModelFallbackChain(
            models=["midas_small", "dpt_hybrid", "dpt_large"]
        )

        # Create estimators for each model
        fallback_chain.initialize_estimators(
            estimator_factory=lambda model_type: DepthEstimator(model_type=model_type)
        )

        # Process with fallback
        depth_map = fallback_chain.estimate_with_fallback(frame)
        ```

    Thread Safety:
        This class uses reentrant locks to protect model switching state
        and is safe for concurrent access from multiple threads.
    """

    def __init__(
        self,
        models: Optional[List[str]] = None,
        *,
        retry_with_same_model: int = 1,
        switch_on_oom: bool = True,
        switch_on_timeout: bool = True,
        enable_cpu_fallback: bool = True,
        cpu_fallback_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        """Initialize the model fallback chain.

        Args:
            models: Ordered list of model names to try. First is primary.
            retry_with_same_model: Retry attempts before switching models.
            switch_on_oom: Switch models on out-of-memory errors.
            switch_on_timeout: Switch models on timeout errors.
            enable_cpu_fallback: Fall back to CPU if all GPU models fail.
            cpu_fallback_factory: Factory function for creating CPU estimators.
        """
        self.models = models or list(DEFAULT_MODEL_FALLBACK_CHAIN)
        self.retry_with_same_model = retry_with_same_model
        self.switch_on_oom = switch_on_oom
        self.switch_on_timeout = switch_on_timeout
        self.enable_cpu_fallback = enable_cpu_fallback
        self.cpu_fallback_factory = cpu_fallback_factory
        self._logger = _get_recovery_logger()
        self._estimators: dict[str, Any] = {}
        self._cpu_estimators: dict[str, Any] = {}
        self._current_model_idx = 0
        self._failed_models: set[str] = set()
        self._using_cpu_fallback = False
        # Thread safety lock (reentrant for nested calls)
        self._model_lock = threading.RLock()

        if not self.models:
            raise ValueError("Model fallback chain cannot be empty")

    @property
    def current_model(self) -> str:
        """Get the current model name."""
        with self._model_lock:
            return self.models[self._current_model_idx]

    @property
    def available_models(self) -> List[str]:
        """Get list of models that haven't failed."""
        with self._model_lock:
            return [m for m in self.models if m not in self._failed_models]

    def initialize_estimators(
        self,
        estimator_factory: Callable[[str], Any],
        cpu_estimator_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        """Initialize estimators for all models in the chain.

        Args:
            estimator_factory: Function that creates an estimator for a model type.
            cpu_estimator_factory: Optional factory for CPU estimators. If not
                provided and enable_cpu_fallback is True, will attempt to use
                the same factory with device='cpu'.

        Raises:
            ValueError: If all models fail to initialize.
        """
        with self._model_lock:
            for model in self.models:
                try:
                    self._estimators[model] = estimator_factory(model)
                    self._logger.debug(f"Initialized estimator for model: {model}")
                except Exception as e:
                    self._logger.warning(f"Failed to initialize estimator for {model}: {e}")
                    self._failed_models.add(model)

            # Store CPU factory for later use
            if cpu_estimator_factory:
                self.cpu_fallback_factory = cpu_estimator_factory

            # Validate we have at least one working model
            if len(self._failed_models) >= len(self.models):
                raise ValueError(
                    f"Failed to initialize all models in fallback chain: {self.models}"
                )

    def get_estimator(self, model_name: Optional[str] = None) -> Any:
        """Get an estimator by model name.

        Args:
            model_name: Model name, or None for current model.

        Returns:
            The estimator instance.

        Raises:
            ValueError: If no estimator is available for the model.
        """
        with self._model_lock:
            if self._using_cpu_fallback:
                model = model_name or self.current_model
                if model in self._cpu_estimators:
                    return self._cpu_estimators[model]
                # Create CPU estimator on demand if factory available
                if self.cpu_fallback_factory:
                    self._cpu_estimators[model] = self.cpu_fallback_factory(model)
                    return self._cpu_estimators[model]

            model = model_name or self.current_model
            if model not in self._estimators:
                raise ValueError(f"No estimator available for model: {model}")
            return self._estimators[model]

    def switch_to_next_model(self) -> str:
        """Switch to the next available model in the chain.

        Returns:
            The new current model name.

        Raises:
            AllModelsFailedError: If all models have failed.
        """
        with self._model_lock:
            # Mark current model as failed
            self._failed_models.add(self.current_model)

            # Find next available model
            for idx in range(len(self.models)):
                next_idx = (self._current_model_idx + idx + 1) % len(self.models)
                model = self.models[next_idx]
                if model not in self._failed_models:
                    self._current_model_idx = next_idx
                    self._logger.info(f"Switched to fallback model: {model}")
                    return model

            # All GPU models failed, try CPU fallback
            if self.enable_cpu_fallback and not self._using_cpu_fallback:
                self._using_cpu_fallback = True
                self._logger.warning("All GPU models failed, switching to CPU fallback")
                return self.current_model

            raise AllModelsFailedError(
                "All models in fallback chain have failed",
                failed_models=list(self._failed_models),
            )

    def _is_oom_error(self, exception: Exception) -> bool:
        """Check if exception indicates out-of-memory error.

        Uses predefined substrings for reliable detection across platforms.

        Args:
            exception: The exception to check.

        Returns:
            True if this is an OOM error.
        """
        error_str = str(exception).lower()
        return any(sub in error_str for sub in OOM_ERROR_SUBSTRINGS)

    def _is_cuda_error(self, exception: Exception) -> bool:
        """Check if exception indicates CUDA/GPU error.

        Uses predefined substrings for reliable detection across platforms.

        Args:
            exception: The exception to check.

        Returns:
            True if this is a CUDA error.
        """
        error_str = str(exception).lower()
        return any(sub in error_str for sub in CUDA_ERROR_SUBSTRINGS)

    def _is_timeout_error(self, exception: Exception) -> bool:
        """Check if exception indicates timeout error.

        Checks both exception type and error message.

        Args:
            exception: The exception to check.

        Returns:
            True if this is a timeout error.
        """
        if isinstance(exception, TimeoutError):
            return True
        error_str = str(exception).lower()
        return any(sub in error_str for sub in TIMEOUT_ERROR_SUBSTRINGS)

    def should_switch_model(self, exception: Exception) -> bool:
        """Determine if we should switch models based on the exception.

        Args:
            exception: The exception that occurred.

        Returns:
            True if we should switch to a different model.
        """
        if self.switch_on_oom and self._is_oom_error(exception):
            return True

        if self.switch_on_timeout and self._is_timeout_error(exception):
            return True

        # CUDA errors often indicate model-specific or GPU issues
        if self._is_cuda_error(exception):
            return True

        return False

    def estimate_with_fallback(
        self,
        frame: FrameT,
        **kwargs: Any,
    ) -> np.ndarray:
        """Estimate depth with automatic model fallback.

        Args:
            frame: Input frame for depth estimation.
            **kwargs: Additional arguments passed to estimate_depth.

        Returns:
            Depth map as numpy array.

        Raises:
            AllModelsFailedError: If all models fail (including CPU fallback).
        """
        last_exception: Optional[Exception] = None

        with self._model_lock:
            tried_models: set[str] = set()
            available = list(self.available_models)  # Snapshot under lock

            while len(tried_models) < len(available) or (
                self._using_cpu_fallback and self.enable_cpu_fallback
            ):
                current = self.current_model

                if current in tried_models and not self._using_cpu_fallback:
                    # Already tried this model, switch
                    try:
                        self.switch_to_next_model()
                        continue
                    except AllModelsFailedError:
                        break

                tried_models.add(current)

                try:
                    estimator = self.get_estimator()

                    # Try with retries on the same model
                    for retry in range(self.retry_with_same_model + 1):
                        try:
                            return estimator.estimate_depth(frame, **kwargs)
                        except Exception as e:
                            last_exception = e
                            if retry < self.retry_with_same_model:
                                self._logger.debug(f"Retry {retry + 1} for model {current}")
                                continue

                            # Check if we should switch models
                            if self.should_switch_model(e):
                                self._logger.warning(
                                    f"Model {current} failed with switch-worthy error: {e}"
                                )
                                break
                            else:
                                # Non-switch-worthy error, but model failed
                                raise

                except Exception as e:
                    last_exception = e
                    self._logger.warning(f"Model {current} failed: {e}")

                    # Try to switch to next model
                    try:
                        self.switch_to_next_model()
                    except AllModelsFailedError:
                        break

        raise AllModelsFailedError(
            "All depth estimation models failed",
            failed_models=list(tried_models),
            original_exception=last_exception,
        )

    def reset(self) -> None:
        """Reset the fallback chain state (thread-safe)."""
        with self._model_lock:
            self._current_model_idx = 0
            self._failed_models.clear()
            self._using_cpu_fallback = False
            self._cpu_estimators.clear()
            self._logger.debug("Model fallback chain reset")


# ---------------------------------------------------------------------------
# Decorators and Utilities
# ---------------------------------------------------------------------------


def recovery_with_fallback(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    fallback_value: Optional[OutputT] = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[[InputT], OutputT]], Callable[[InputT], OutputT]]:
    """Decorator that adds retry and fallback behavior to a function.

    Args:
        max_retries: Maximum number of retry attempts.
        backoff_factor: Multiplier for exponential backoff.
        fallback_value: Value to return if all retries fail (None raises).
        exceptions: Exception types to catch and retry.

    Returns:
        Decorated function with recovery behavior.

    Example:
        ```python
        @recovery_with_fallback(max_retries=3, fallback_value=None)
        def process_frame(frame):
            return depth_estimator.estimate_depth(frame)
        ```
    """

    def decorator(func: Callable[[InputT], OutputT]) -> Callable[[InputT], OutputT]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> OutputT:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = DEFAULT_RETRY_DELAY_SECONDS * (backoff_factor**attempt)
                        time.sleep(delay)

            if fallback_value is not None:
                return fallback_value

            raise MaxRetriesExceededError(
                f"Function {func.__name__} failed after {max_retries + 1} attempts",
                attempts=max_retries + 1,
                original_exception=last_exception,
            )

        return wrapper

    return decorator


def create_recovery_decorator(
    config: ErrorRecoveryConfig,
) -> Callable[[Callable[[InputT], OutputT]], Callable[[InputT], OutputT]]:
    """Create a recovery decorator from a configuration.

    Args:
        config: Error recovery configuration.

    Returns:
        A decorator function that applies recovery behavior.

    Example:
        ```python
        config = ErrorRecoveryConfig(max_retries=5, backoff_factor=1.5)
        recovery_decorator = create_recovery_decorator(config)

        @recovery_decorator
        def process_frame(frame):
            return depth_estimator.estimate_depth(frame)
        ```
    """

    def decorator(func: Callable[[InputT], OutputT]) -> Callable[[InputT], OutputT]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> OutputT:
            manager = FrameRecoveryManager(config)

            # Create a process function that properly forwards all arguments
            # This avoids the issue of passing the wrong item to recovery
            def process_fn(_: Any) -> OutputT:
                return func(*args, **kwargs)

            # Use first argument as the recovery item (convention)
            item = args[0] if args else None
            return manager.process_with_recovery(
                item,
                process_fn,
            )

        return wrapper

    return decorator


class RecoveryContext:
    """Context manager for temporary recovery configuration.

    Example:
        ```python
        with RecoveryContext(max_retries=5) as ctx:
            result = ctx.process(frame, depth_estimator.estimate_depth)
        ```
    """

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        **kwargs: Any,
    ) -> None:
        """Initialize recovery context.

        Args:
            max_retries: Maximum retry attempts.
            backoff_factor: Backoff multiplier.
            **kwargs: Additional ErrorRecoveryConfig arguments.
        """
        self.config = ErrorRecoveryConfig(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            **kwargs,
        )
        self._manager = FrameRecoveryManager(self.config)

    def process(
        self,
        item: InputT,
        process_fn: Callable[[InputT], OutputT],
        item_index: Optional[int] = None,
    ) -> OutputT:
        """Process an item with recovery."""
        return self._manager.process_with_recovery(item, process_fn, item_index=item_index)

    @property
    def stats(self) -> RecoveryStats:
        """Get recovery statistics."""
        return self._manager.stats

    def __enter__(self) -> RecoveryContext:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> bool:
        """Exit the recovery context.

        Args:
            exc_type: The exception type if an exception was raised.
            exc_val: The exception instance if an exception was raised.
            exc_tb: The traceback if an exception was raised.

        Returns:
            False to propagate any exception that occurred.
        """
        # Log any exception that occurred within the context
        if exc_type is not None and exc_val is not None:
            logger = _get_recovery_logger()
            logger.error(f"Exception in RecoveryContext: {exc_type.__name__}: {exc_val}")
        return False  # Do not suppress exceptions


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _get_recovery_logger() -> Logger:
    """Get the recovery module logger."""
    return get_logger("error_recovery")


def create_recovery_config_from_dict(config_dict: dict[str, Any]) -> ErrorRecoveryConfig:
    """Create ErrorRecoveryConfig from a dictionary.

    Args:
        config_dict: Dictionary with configuration values.

    Returns:
        ErrorRecoveryConfig instance.
    """
    backoff_str = config_dict.get("backoff_strategy", "exponential")
    try:
        backoff_strategy = BackoffStrategy(backoff_str.lower())
    except ValueError:
        backoff_strategy = BackoffStrategy.EXPONENTIAL

    return ErrorRecoveryConfig(
        max_retries=config_dict.get("max_retries", DEFAULT_MAX_RETRIES),
        retry_delay_seconds=config_dict.get("retry_delay_seconds", DEFAULT_RETRY_DELAY_SECONDS),
        backoff_factor=config_dict.get("backoff_factor", DEFAULT_BACKOFF_FACTOR),
        max_retry_delay_seconds=config_dict.get(
            "max_retry_delay_seconds", DEFAULT_MAX_RETRY_DELAY_SECONDS
        ),
        backoff_strategy=backoff_strategy,
        model_fallback_chain=config_dict.get(
            "model_fallback_chain", list(DEFAULT_MODEL_FALLBACK_CHAIN)
        ),
        enable_cpu_fallback=config_dict.get("enable_cpu_fallback", DEFAULT_CPU_FALLBACK_ENABLED),
        skip_on_max_retries=config_dict.get("skip_on_max_retries", DEFAULT_SKIP_ON_MAX_RETRIES),
        track_failures=config_dict.get("track_failures", True),
    )


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Configuration
    "ErrorRecoveryConfig",
    "RecoveryStats",
    "RecoveryStrategy",
    "BackoffStrategy",
    # Exceptions
    "RecoveryError",
    "MaxRetriesExceededError",
    "AllModelsFailedError",
    "FrameRecoveryFailedError",
    # Classes
    "FrameRecoveryManager",
    "ModelFallbackChain",
    "RecoveryContext",
    # Decorators
    "recovery_with_fallback",
    "create_recovery_decorator",
    # Functions
    "create_recovery_config_from_dict",
    # Constants
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
