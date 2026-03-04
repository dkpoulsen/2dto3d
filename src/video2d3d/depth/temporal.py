"""Temporal consistency for depth maps across video frames.

This module provides temporal smoothing and consistency algorithms to reduce
flickering and maintain smooth depth transitions in video sequences:

- Exponential Moving Average (EMA) filtering
- Optical flow-guided temporal propagation
- Sliding window temporal filtering
- Motion-compensated depth warping

The temporal smoother maintains state across frames and can be used in both
online (streaming) and batch processing modes.

Example usage:
    ```python
    from video2d3d.depth.temporal import TemporalSmoother, TemporalSmoothingConfig

    # Basic usage with EMA filtering
    config = TemporalSmoothingConfig(
        method="ema",
        smoothing_factor=0.5,
    )
    smoother = TemporalSmoother(config=config)

    # Process frames sequentially
    for frame in video_frames:
        depth_map = depth_estimator.estimate_depth(frame)
        smoothed_depth = smoother.smooth(depth_map, frame)

    # Reset for new video sequence
    smoother.reset()

    # With optical flow for motion compensation
    config = TemporalSmoothingConfig(
        method="optical_flow",
        smoothing_factor=0.7,
        flow_threshold=4.0,
    )
    smoother = TemporalSmoother(config=config)
    ```
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.logger import get_logger, log_exception, log_performance


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default values matching config/default.yaml
_DEFAULT_SMOOTHING_FACTOR: float = 0.5
_DEFAULT_FLOW_THRESHOLD: float = 4.0
_DEFAULT_WINDOW_SIZE: int = 5
_DEFAULT_PYRAMID_SCALE: float = 0.5
_DEFAULT_PYRAMID_LEVELS: int = 3
_DEFAULT_WINDOW_SIZE_FLOW: int = 15
_DEFAULT_ITERATIONS: int = 3
_DEFAULT_POLY_N: int = 5
_DEFAULT_POLY_SIGMA: float = 1.2
_DEFAULT_OCCLUSION_THRESHOLD: float = 0.1

class TemporalSmoothingMethod(Enum):
    """Available temporal smoothing methods."""

    EMA = "ema"  # Exponential Moving Average
    OPTICAL_FLOW = "optical_flow"  # Motion-compensated using optical flow
    SLIDING_WINDOW = "sliding_window"  # Sliding window average
    NONE = "none"  # No temporal smoothing


class TemporalSmoothingError(Exception):
    """Exception raised for temporal smoothing errors."""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            operation: Operation that caused the error.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.operation = operation
        self.original_exception = original_exception


def _get_temporal_logger() -> "Logger":
    """Get the temporal smoothing logger (lazy initialization)."""
    return get_logger("depth.temporal")


@dataclass
class TemporalSmoothingConfig:
    """Configuration for temporal smoothing.

    Attributes:
        method: Temporal smoothing method to use.
        smoothing_factor: Weight for current frame (0-1). Higher = less smoothing.
            For EMA: alpha in (1-alpha)*prev + alpha*current
            For optical_flow: blend factor for combining warped and current depth
        flow_threshold: Maximum optical flow magnitude for validity (pixels).
            Higher values allow more motion but may introduce artifacts.
        window_size: Number of frames for sliding window averaging.
        pyramid_scale: Image scale for optical flow pyramid (< 1).
        pyramid_levels: Number of pyramid levels for optical flow.
        flow_window_size: Window size for optical flow calculation.
        flow_iterations: Number of iterations for optical flow.
        flow_poly_n: Size of pixel neighborhood for optical flow poly expansion.
        flow_poly_sigma: Standard deviation for optical flow poly expansion.
        enable_occlusion_handling: Handle occluded regions in flow-based warping.
        occlusion_threshold: Threshold for depth discontinuity in occlusion detection.
    """
    method: str = "ema"
    smoothing_factor: float = _DEFAULT_SMOOTHING_FACTOR
    flow_threshold: float = _DEFAULT_FLOW_THRESHOLD
    window_size: int = _DEFAULT_WINDOW_SIZE
    pyramid_scale: float = _DEFAULT_PYRAMID_SCALE
    pyramid_levels: int = _DEFAULT_PYRAMID_LEVELS
    flow_window_size: int = _DEFAULT_WINDOW_SIZE_FLOW
    flow_iterations: int = _DEFAULT_ITERATIONS
    flow_poly_n: int = _DEFAULT_POLY_N
    flow_poly_sigma: float = _DEFAULT_POLY_SIGMA
    enable_occlusion_handling: bool = True
    occlusion_threshold: float = _DEFAULT_OCCLUSION_THRESHOLD

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Validate method
        valid_methods = [m.value for m in TemporalSmoothingMethod]
        if self.method.lower() not in valid_methods:
            raise ValueError(
                f"Invalid smoothing method '{self.method}'. Valid options: {valid_methods}"
            )
        self.method = self.method.lower()

        # Validate smoothing factor
        if not 0.0 <= self.smoothing_factor <= 1.0:
            raise ValueError(f"smoothing_factor must be in [0, 1], got {self.smoothing_factor}")

        # Validate window size
        if self.window_size < 1:
            raise ValueError(f"window_size must be >= 1, got {self.window_size}")

        # Validate flow parameters
        if self.flow_threshold <= 0:
            raise ValueError(f"flow_threshold must be > 0, got {self.flow_threshold}")

        if not 0 < self.pyramid_scale < 1:
            raise ValueError(f"pyramid_scale must be in (0, 1), got {self.pyramid_scale}")


@dataclass
class TemporalState:
    """State maintained across frames for temporal smoothing.

    Attributes:
        previous_depth: Previous frame's depth map.
        previous_frame: Previous RGB frame (for optical flow).
        depth_history: History of depth maps for sliding window.
        frame_count: Number of frames processed.
    """

    previous_depth: Optional[np.ndarray] = None
    previous_frame: Optional[np.ndarray] = None
    depth_history: deque = field(default_factory=lambda: deque(maxlen=5))
    frame_count: int = 0


class TemporalSmoother:
    """Temporal smoother for depth maps across video frames.

    This class provides temporal consistency for depth maps using various
    methods including exponential moving average, optical flow-guided warping,
    and sliding window averaging.

    The smoother maintains state across frames and supports both online
    (streaming) and batch processing modes.

    Example usage:
        ```python
        # Basic EMA smoothing
        config = TemporalSmoothingConfig(method="ema", smoothing_factor=0.5)
        smoother = TemporalSmoother(config=config)

        for frame in video_frames:
            depth = estimator.estimate_depth(frame)
            smoothed = smoother.smooth(depth, frame)
            process_output(smoothed)

        # With optical flow
        config = TemporalSmoothingConfig(method="optical_flow", smoothing_factor=0.7)
        smoother = TemporalSmoother(config=config)

        for frame in video_frames:
            depth = estimator.estimate_depth(frame)
            smoothed = smoother.smooth(depth, frame)
            process_output(smoothed)
        ```

    Attributes:
        config: TemporalSmoothingConfig object.
        state: Current temporal state.
    """

    def __init__(
        self,
        config: Optional[TemporalSmoothingConfig] = None,
        *,
        method: str = "ema",
        smoothing_factor: float = _DEFAULT_SMOOTHING_FACTOR,
    ) -> None:
        """Initialize the temporal smoother.

        Args:
            config: TemporalSmoothingConfig object. If provided, other args ignored.
            method: Smoothing method ('ema', 'optical_flow', 'sliding_window', 'none').
            smoothing_factor: Weight for current frame (0-1).
        """
        if config is not None:
            self.config = config
        else:
            self.config = TemporalSmoothingConfig(
                method=method,
                smoothing_factor=smoothing_factor,
            )

        self.state = TemporalState(depth_history=deque(maxlen=self.config.window_size))
        self._logger = _get_temporal_logger()
        self._logger.debug(
            f"TemporalSmoother initialized: method={self.config.method}, "
            f"smoothing_factor={self.config.smoothing_factor}"
        )

    def reset(self) -> None:
        """Reset the temporal state for a new video sequence."""
        self.state = TemporalState(depth_history=deque(maxlen=self.config.window_size))
        self._logger.debug("Temporal state reset")

    def smooth(
        self,
        depth_map: np.ndarray,
        frame: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Apply temporal smoothing to a depth map.

        Args:
            depth_map: Input depth map as float32 array (H, W) with values in [0, 1].
            frame: Optional RGB frame for optical flow calculation.
                   Required if method is 'optical_flow'.

        Returns:
            Temporally smoothed depth map.

        Raises:
            TemporalSmoothingError: If smoothing fails.
        """
        start_time = time.time()

        # Handle 'none' method
        if self.config.method == TemporalSmoothingMethod.NONE.value:
            self.state.frame_count += 1
            return depth_map.copy()

        # Handle first frame
        if self.state.previous_depth is None:
            self._initialize_state(depth_map, frame)
            return depth_map.copy()

        try:
            # Apply smoothing based on method
            if self.config.method == TemporalSmoothingMethod.EMA.value:
                result = self._smooth_ema(depth_map)
            elif self.config.method == TemporalSmoothingMethod.OPTICAL_FLOW.value:
                result = self._smooth_optical_flow(depth_map, frame)
            elif self.config.method == TemporalSmoothingMethod.SLIDING_WINDOW.value:
                result = self._smooth_sliding_window(depth_map)
            else:
                result = depth_map.copy()

            # Update state
            self.state.previous_depth = result.copy()
            if frame is not None:
                self.state.previous_frame = frame.copy()
            self.state.frame_count += 1

            # Clamp output to [0, 1] range to prevent drift
            result = np.clip(result, 0.0, 1.0).astype(np.float32)

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "temporal_smoothing",
                elapsed_ms,
                method=self.config.method,
                frame_count=self.state.frame_count,
            )

            return result

        except TemporalSmoothingError:
            raise
        except Exception as e:
            log_exception("Temporal smoothing failed", exception=e)
            raise TemporalSmoothingError(
                f"Temporal smoothing failed: {e}",
                operation="smooth",
                original_exception=e,
            ) from e

    def _initialize_state(
        self,
        depth_map: np.ndarray,
        frame: Optional[np.ndarray],
    ) -> None:
        """Initialize temporal state with the first frame."""
        self.state.previous_depth = depth_map.copy()
        self.state.previous_frame = frame.copy() if frame is not None else None
        self.state.depth_history.append(depth_map.copy())
        self.state.frame_count = 1
        self._logger.debug("Temporal state initialized with first frame")

    def _smooth_ema(self, depth_map: np.ndarray) -> np.ndarray:
        """Apply exponential moving average temporal smoothing.

        The formula is: smoothed = alpha * current + (1 - alpha) * previous
        where alpha is the smoothing_factor.

        Args:
            depth_map: Current frame's depth map.

        Returns:
            EMA-smoothed depth map.
        """
        if self.state.previous_depth is None:
            return depth_map.copy()

        alpha = self.config.smoothing_factor
        smoothed = alpha * depth_map + (1 - alpha) * self.state.previous_depth

        return smoothed.astype(np.float32)

    def _smooth_optical_flow(
        self,
        depth_map: np.ndarray,
        frame: Optional[np.ndarray],
    ) -> np.ndarray:
        """Apply optical flow-guided temporal smoothing.

        This method uses optical flow to warp the previous depth map to align
        with the current frame, then blends it with the current depth map.

        Args:
            depth_map: Current frame's depth map.
            frame: Current RGB frame (required for optical flow).

        Returns:
            Motion-compensated smoothed depth map.

        Raises:
            TemporalSmoothingError: If frame is not provided.
        """
        if frame is None:
            raise TemporalSmoothingError(
                "Frame is required for optical flow smoothing",
                operation="optical_flow",
            )

        if self.state.previous_frame is None or self.state.previous_depth is None:
            return depth_map.copy()

        try:
            # Compute optical flow
            flow = self._compute_optical_flow(frame)

            if flow is None:
                # Fall back to EMA if flow computation fails
                self._logger.warning("Optical flow computation failed, falling back to EMA")
                return self._smooth_ema(depth_map)

            # Warp previous depth map using the flow
            warped_depth = self._warp_depth_with_flow(self.state.previous_depth, flow)

            # Compute flow magnitude for validity mask
            flow_magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
            valid_mask = flow_magnitude < self.config.flow_threshold

            # Blend warped and current depth
            alpha = self.config.smoothing_factor
            smoothed = np.where(
                valid_mask[..., np.newaxis] if valid_mask.ndim == 3 else valid_mask,
                alpha * depth_map + (1 - alpha) * warped_depth,
                depth_map,
            )

            # Handle occlusions if enabled
            if self.config.enable_occlusion_handling:
                smoothed = self._handle_occlusions(
                    smoothed, depth_map, warped_depth, flow_magnitude
                )

            return smoothed.astype(np.float32)

        except Exception as e:
            log_exception("Optical flow smoothing failed", exception=e)
            # Fall back to EMA on error
            self._logger.warning(f"Optical flow smoothing failed, falling back to EMA: {e}")
            return self._smooth_ema(depth_map)

    def _compute_optical_flow(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Compute dense optical flow between previous and current frame.

        Uses Farneback's algorithm for dense optical flow estimation.

        Args:
            frame: Current RGB frame.

        Returns:
            Optical flow as (H, W, 2) array, or None if computation fails.
        """
        if self.state.previous_frame is None:
            return None

        try:
            # Convert frames to grayscale
            prev_gray = cv2.cvtColor(self.state.previous_frame, cv2.COLOR_RGB2GRAY)
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

            # Compute optical flow using Farneback's algorithm
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray,
                curr_gray,
                None,
                pyr_scale=self.config.pyramid_scale,
                levels=self.config.pyramid_levels,
                winsize=self.config.flow_window_size,
                iterations=self.config.flow_iterations,
                poly_n=self.config.flow_poly_n,
                poly_sigma=self.config.flow_poly_sigma,
                flags=0,
            )

            return flow

        except Exception as e:
            log_exception("Optical flow computation failed", exception=e)
            return None

    def _warp_depth_with_flow(
        self,
        depth_map: np.ndarray,
        flow: np.ndarray,
    ) -> np.ndarray:
        """Warp a depth map using optical flow.

        Args:
            depth_map: Depth map to warp.
            flow: Optical flow field (H, W, 2).

        Returns:
            Warped depth map.
        """
        h, w = depth_map.shape

        # Create coordinate grid
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)

        # Add flow to coordinates
        new_x = x + flow[..., 0]
        new_y = y + flow[..., 1]

        # Remap the depth map
        warped = cv2.remap(
            depth_map.astype(np.float32),
            new_x,
            new_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return warped

    def _handle_occlusions(
        self,
        smoothed: np.ndarray,
        current_depth: np.ndarray,
        warped_depth: np.ndarray,
        flow_magnitude: np.ndarray,
    ) -> np.ndarray:
        """Handle occluded regions in the smoothed depth map.

        Occlusions occur when regions are visible in one frame but not another.
        This method detects and handles such regions.

        Args:
            smoothed: Currently smoothed depth map.
            current_depth: Current frame's raw depth map.
            warped_depth: Warped previous depth map.
            flow_magnitude: Magnitude of optical flow.

        Returns:
            Depth map with occlusions handled.
        """
        # Detect potential occlusions based on depth discontinuities
        depth_diff = np.abs(current_depth - warped_depth)

        # High flow magnitude + high depth difference = likely occlusion
        potential_occlusion = (flow_magnitude > self.config.flow_threshold * 0.5) & (
            depth_diff > self.config.occlusion_threshold
        )

        # In occluded regions, prefer current depth
        result = np.where(
            potential_occlusion[..., np.newaxis]
            if potential_occlusion.ndim == 3
            else potential_occlusion,
            current_depth,
            smoothed,
        )

        return result

    def _smooth_sliding_window(self, depth_map: np.ndarray) -> np.ndarray:
        """Apply sliding window temporal averaging.

        Averages depth maps over a sliding window of recent frames.

        Args:
            depth_map: Current frame's depth map.

        Returns:
            Averaged depth map.
        """
        # Add current depth to history
        self.state.depth_history.append(depth_map.copy())

        # Compute average over window
        if len(self.state.depth_history) == 0:
            return depth_map.copy()

        # Weight recent frames more heavily using exponential weights
        weights = np.exp(np.linspace(-1, 0, len(self.state.depth_history)))
        weights = weights / weights.sum()

        # Compute weighted average
        smoothed = np.zeros_like(depth_map)
        for i, hist_depth in enumerate(self.state.depth_history):
            smoothed += weights[i] * hist_depth

        return smoothed.astype(np.float32)

    def process_batch(
        self,
        depth_maps: list[np.ndarray],
        frames: Optional[list[np.ndarray]] = None,
    ) -> list[np.ndarray]:
        """Process a batch of depth maps with temporal smoothing.

        This is a convenience method for batch processing that maintains
        temporal state across all frames in the batch.

        Args:
            depth_maps: List of depth maps to smooth.
            frames: Optional list of RGB frames (required for optical flow).
        Returns:
            List of temporally smoothed depth maps.
        
        Raises:
            ValueError: If depth_maps and frames have different lengths.
        """
        # Input validation
        if frames is not None and len(frames) != len(depth_maps):
            raise ValueError(
                f"Length mismatch: depth_maps has {len(depth_maps)} items, "
                f"but frames has {len(frames)} items"
            )

        if not depth_maps:
            return []

        results = []

        # Reset state for new batch
        self.reset()

        for i, depth_map in enumerate(depth_maps):
            frame = frames[i] if frames is not None else None
            smoothed = self.smooth(depth_map, frame)
            results.append(smoothed)

        return results

    def __call__(
        self,
        depth_map: np.ndarray,
        frame: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Apply temporal smoothing (callable interface).

        Args:
            depth_map: Input depth map.
            frame: Optional RGB frame for optical flow.

        Returns:
            Smoothed depth map.
        """
        return self.smooth(depth_map, frame)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_temporal_smoother(
    method: str = "ema",
    smoothing_factor: float = _DEFAULT_SMOOTHING_FACTOR,
    **kwargs: Union[str, float, int, bool],
) -> TemporalSmoother:
    """Create a temporal smoother with the specified configuration.

    Args:
        method: Smoothing method ('ema', 'optical_flow', 'sliding_window', 'none').
        smoothing_factor: Weight for current frame (0-1).
        **kwargs: Additional TemporalSmoothingConfig field values.

    Returns:
        Configured TemporalSmoother instance.
    """
    config = TemporalSmoothingConfig(
        method=method,
        smoothing_factor=smoothing_factor,
        **kwargs,  # type: ignore[arg-type]
    )
    return TemporalSmoother(config=config)


def smooth_depth_temporal(
    depth_maps: list[np.ndarray],
    frames: Optional[list[np.ndarray]] = None,
    method: str = "ema",
    smoothing_factor: float = _DEFAULT_SMOOTHING_FACTOR,
) -> list[np.ndarray]:
    """Apply temporal smoothing to a sequence of depth maps.

    This is a convenience function for batch processing.

    Args:
        depth_maps: List of depth maps to smooth.
        frames: Optional list of RGB frames (for optical flow).
        method: Smoothing method.
        smoothing_factor: Weight for current frame.

    Returns:
        List of smoothed depth maps.
    """
    smoother = create_temporal_smoother(
        method=method,
        smoothing_factor=smoothing_factor,
    )
    return smoother.process_batch(depth_maps, frames)


# Module-level exports
__all__ = [
    # Classes
    "TemporalSmoother",
    "TemporalSmoothingConfig",
    "TemporalState",
    "TemporalSmoothingError",
    # Enums
    "TemporalSmoothingMethod",
    # Functions
    "create_temporal_smoother",
    "smooth_depth_temporal",
    # Constants
    "_DEFAULT_SMOOTHING_FACTOR",
    "_DEFAULT_FLOW_THRESHOLD",
    "_DEFAULT_WINDOW_SIZE",
]
