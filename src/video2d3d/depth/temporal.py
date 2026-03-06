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

# Motion-compensated smoothing constants
_MOTION_MASK_THRESHOLD_FACTOR: float = 0.1  # Factor for motion mask threshold
_CONSISTENCY_FACTOR: float = 0.5  # Weight for inconsistent regions
_BILATERAL_BLEND_WEIGHT: float = 0.7  # Weight for refined result in bilateral blend
_BILATERAL_D: int = 5  # Bilateral filter diameter
_BILATERAL_SIGMA_COLOR: float = 30.0  # Bilateral filter color sigma
_BILATERAL_SIGMA_SPACE: float = 30.0  # Bilateral filter space sigma

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
# ---------------------------------------------------------------------------
# Motion-Compensated Temporal Smoothing
# ---------------------------------------------------------------------------


@dataclass
class MotionCompensatedConfig:
    """Configuration for motion-compensated temporal smoothing.
    
    This configuration extends the basic temporal smoothing with advanced
    optical flow tracking capabilities for better handling of moving objects.
    
    Attributes:
        smoothing_factor: Weight for current frame (0-1). Higher = less smoothing.
        flow_threshold: Maximum optical flow magnitude for validity (pixels).
        consistency_threshold: Threshold for forward-backward flow consistency.
        edge_preservation_factor: Factor for edge-preserving blending (0-1).
        motion_history_length: Number of frames to track motion history.
        depth_consistency_weight: Weight for depth consistency refinement.
        multi_scale_flow: Enable multi-scale optical flow computation.
        pyramid_scale: Image scale for optical flow pyramid (< 1).
        pyramid_levels: Number of pyramid levels for optical flow.
        flow_window_size: Window size for optical flow calculation.
        flow_iterations: Number of iterations for optical flow.
        enable_forward_backward_check: Enable forward-backward consistency check.
        enable_edge_preservation: Enable edge-preserving temporal blending.
        enable_motion_segmentation: Enable motion-based object segmentation.
    """
    smoothing_factor: float = 0.5
    flow_threshold: float = 8.0
    consistency_threshold: float = 1.0
    edge_preservation_factor: float = 0.7
    motion_history_length: int = 5
    depth_consistency_weight: float = 0.3
    multi_scale_flow: bool = True
    pyramid_scale: float = 0.5
    pyramid_levels: int = 3
    flow_window_size: int = 21
    flow_iterations: int = 5
    enable_forward_backward_check: bool = True
    enable_edge_preservation: bool = True
    enable_motion_segmentation: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0.0 <= self.smoothing_factor <= 1.0:
            raise ValueError(
                f"smoothing_factor must be in [0, 1], got {self.smoothing_factor}"
            )
        if self.flow_threshold <= 0:
            raise ValueError(
                f"flow_threshold must be > 0, got {self.flow_threshold}"
            )
        if self.consistency_threshold < 0:
            raise ValueError(
                f"consistency_threshold must be >= 0, got {self.consistency_threshold}"
            )
        if not 0.0 <= self.edge_preservation_factor <= 1.0:
            raise ValueError(
                f"edge_preservation_factor must be in [0, 1], got {self.edge_preservation_factor}"
            )
        if self.motion_history_length < 1:
            raise ValueError(
                f"motion_history_length must be >= 1, got {self.motion_history_length}"
            )
        if not 0.0 <= self.depth_consistency_weight <= 1.0:
            raise ValueError(
                f"depth_consistency_weight must be in [0, 1], got {self.depth_consistency_weight}"
            )


class MotionCompensatedSmoother:
    """Motion-compensated temporal smoother for depth maps.
    
    This class provides advanced temporal smoothing that tracks moving objects
    using optical flow and maintains depth consistency across frame transitions.
    
    Key features:
    - Forward-backward optical flow consistency checking
    - Edge-preserving temporal blending
    - Motion-based depth consistency refinement
    - Multi-scale optical flow for robust tracking
    
    Example usage:
        ```python
        config = MotionCompensatedConfig(
            smoothing_factor=0.6,
            enable_forward_backward_check=True,
            enable_edge_preservation=True,
        )
        smoother = MotionCompensatedSmoother(config=config)
        
        for frame in video_frames:
            depth = estimator.estimate_depth(frame)
            smoothed = smoother.smooth(depth, frame)
            process_output(smoothed)
        
        # Reset for new video sequence
        smoother.reset()
        ```
    
    Attributes:
        config: MotionCompensatedConfig object.
        state: Current temporal state.
    """

    def __init__(
        self,
        config: Optional[MotionCompensatedConfig] = None,
        *,
        smoothing_factor: float = 0.5,
    ) -> None:
        """Initialize the motion-compensated smoother.
        
        Args:
            config: MotionCompensatedConfig object. If provided, other args ignored.
            smoothing_factor: Weight for current frame (0-1).
        """
        if config is not None:
            self.config = config
        else:
            self.config = MotionCompensatedConfig(
                smoothing_factor=smoothing_factor,
            )

        self.state = TemporalState(
            depth_history=deque(maxlen=self.config.motion_history_length)
        )
        self._motion_history: deque = deque(maxlen=self.config.motion_history_length)
        self._flow_history: deque = deque(maxlen=self.config.motion_history_length)
        self._logger = _get_temporal_logger()
        self._logger.debug(
            f"MotionCompensatedSmoother initialized: "
            f"smoothing_factor={self.config.smoothing_factor}, "
            f"forward_backward_check={self.config.enable_forward_backward_check}, "
        )

        # Warn about unused multi_scale_flow option
        if self.config.multi_scale_flow:
            self._logger.warning(
                "multi_scale_flow option is enabled but not currently implemented. "
                "This option is reserved for future enhancements."
            )

        # Warn about unimplemented features
        if self.config.multi_scale_flow:
            self._logger.warning(
                "multi_scale_flow is enabled but not yet implemented. "
                "Using single-scale optical flow."
            )

    def reset(self) -> None:
        """Reset the temporal state for a new video sequence."""
        self.state = TemporalState(
            depth_history=deque(maxlen=self.config.motion_history_length)
        )
        self._motion_history = deque(maxlen=self.config.motion_history_length)
        self._flow_history = deque(maxlen=self.config.motion_history_length)
        self._logger.debug("Motion-compensated smoother state reset")

    def smooth(
        self,
        depth_map: np.ndarray,
        frame: np.ndarray,
    ) -> np.ndarray:
        """Apply motion-compensated temporal smoothing to a depth map.
        
        Args:
            depth_map: Input depth map as float32 array (H, W) with values in [0, 1].
            frame: RGB frame for optical flow calculation.
        
        Returns:
            Motion-compensated temporally smoothed depth map.
        
        Raises:
            TemporalSmoothingError: If smoothing fails.
        """
        start_time = time.time()

        # Handle first frame
        if self.state.previous_depth is None:
            self._initialize_state(depth_map, frame)
            return depth_map.copy()

        try:
            # Compute optical flow with forward-backward consistency
            flow_forward, flow_backward, consistency_mask = (
                self._compute_consistent_optical_flow(frame)
            )

            # Initialize motion_mask to default (will be updated if flow succeeds)
            motion_mask = np.zeros_like(depth_map, dtype=bool)

            if flow_forward is None:
                # Fall back to simple blending if flow fails
                self._logger.warning("Optical flow computation failed, using simple blend")
                result = self._simple_blend(depth_map)
                self._logger.warning("Optical flow computation failed, using simple blend")
                result = self._simple_blend(depth_map)
            else:
                # Warp previous depth using forward flow
                warped_depth = self._warp_depth_with_flow(
                    self.state.previous_depth, flow_forward
                )

                # Compute motion mask based on flow magnitude
                flow_magnitude = np.sqrt(
                    flow_forward[..., 0] ** 2 + flow_forward[..., 1] ** 2
                )
                motion_mask = flow_magnitude > self.config.flow_threshold * _MOTION_MASK_THRESHOLD_FACTOR

                # Edge-preserving temporal blending
                if self.config.enable_edge_preservation:
                    result = self._edge_preserving_blend(
                        depth_map, warped_depth, flow_magnitude, consistency_mask
                    )
                else:
                    result = self._simple_blend_with_mask(
                        depth_map, warped_depth, consistency_mask
                    )

                # Apply motion-based depth consistency refinement
                if self.config.enable_motion_segmentation:
                    result = self._refine_depth_consistency(
                        result, depth_map, warped_depth, motion_mask, flow_magnitude
                    )

            # Update state
            self.state.previous_depth = result.copy()
            self.state.previous_frame = frame.copy()
            self.state.frame_count += 1
            self._motion_history.append(motion_mask)
            if flow_forward is not None:
                self._flow_history.append(flow_forward.copy())

            # Clamp output to [0, 1] range
            result = np.clip(result, 0.0, 1.0).astype(np.float32)

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "motion_compensated_smoothing",
                elapsed_ms,
                smoothing_factor=self.config.smoothing_factor,
                frame_count=self.state.frame_count,
            )

            return result

        except Exception as e:
            log_exception("Motion-compensated smoothing failed", exception=e)
            raise TemporalSmoothingError(
                f"Motion-compensated smoothing failed: {e}",
                operation="motion_compensated_smooth",
                original_exception=e,
            ) from e

    def _initialize_state(
        self,
        depth_map: np.ndarray,
        frame: np.ndarray,
    ) -> None:
        """Initialize temporal state with the first frame."""
        self.state.previous_depth = depth_map.copy()
        self.state.previous_frame = frame.copy()
        self.state.depth_history.append(depth_map.copy())
        self.state.frame_count = 1
        self._logger.debug("Motion-compensated smoother initialized with first frame")

    def _compute_consistent_optical_flow(
        self,
        frame: np.ndarray,
    ) -> tuple[Optional[np.ndarray], Optional[np.ndarray], np.ndarray]:
        """Compute optical flow with forward-backward consistency check.
        
        Computes flow in both directions and checks consistency to detect
        occlusions and unreliable flow regions.
        
        Args:
            frame: Current RGB frame.
        
        Returns:
            Tuple of (forward_flow, backward_flow, consistency_mask).
            Returns (None, None, empty_mask) if computation fails.
        """
        if self.state.previous_frame is None:
            return None, None, np.ones(frame.shape[:2], dtype=bool)

        try:
            # Convert frames to grayscale
            prev_gray = cv2.cvtColor(self.state.previous_frame, cv2.COLOR_RGB2GRAY)
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

            # Compute forward flow (prev -> curr)
            flow_forward = cv2.calcOpticalFlowFarneback(
                prev_gray,
                curr_gray,
                None,
                pyr_scale=self.config.pyramid_scale,
                levels=self.config.pyramid_levels,
                winsize=self.config.flow_window_size,
                iterations=self.config.flow_iterations,
                poly_n=5,
                poly_sigma=1.2,
                flags=0,
            )

            # Compute backward flow (curr -> prev) for consistency check
            if self.config.enable_forward_backward_check:
                flow_backward = cv2.calcOpticalFlowFarneback(
                    curr_gray,
                    prev_gray,
                    None,
                    pyr_scale=self.config.pyramid_scale,
                    levels=self.config.pyramid_levels,
                    winsize=self.config.flow_window_size,
                    iterations=self.config.flow_iterations,
                    poly_n=5,
                    poly_sigma=1.2,
                    flags=0,
                )

                # Check forward-backward consistency
                consistency_mask = self._compute_flow_consistency(
                    flow_forward, flow_backward
                )
            else:
                flow_backward = None
                consistency_mask = np.ones(frame.shape[:2], dtype=bool)

            return flow_forward, flow_backward, consistency_mask

        except Exception as e:
            log_exception("Optical flow computation failed", exception=e)
            return None, None, np.ones(frame.shape[:2], dtype=bool)

    def _compute_flow_consistency(
        self,
        flow_forward: np.ndarray,
        flow_backward: np.ndarray,
    ) -> np.ndarray:
        """Compute forward-backward flow consistency mask.
        
        Checks if warping the forward flow with the backward flow returns
        to approximately the same location, indicating reliable flow.
        
        Args:
            flow_forward: Forward optical flow (prev -> curr).
            flow_backward: Backward optical flow (curr -> prev).
        
        Returns:
            Boolean mask where True indicates consistent/reliable flow.
        """
        h, w = flow_forward.shape[:2]
        
        # Create coordinate grid
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        
        # Warp forward flow using backward flow
        warped_x = x + flow_backward[..., 0]
        warped_y = y + flow_backward[..., 1]
        
        # Sample forward flow at warped locations
        # (this simulates applying backward flow to the forward flow endpoints)
        warped_flow_x = cv2.remap(
            flow_forward[..., 0],
            warped_x,
            warped_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        warped_flow_y = cv2.remap(
            flow_forward[..., 1],
            warped_x,
            warped_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        
        # Compute inconsistency: forward flow + backward flow should be ~0
        inconsistency = np.sqrt(
            (warped_flow_x + flow_backward[..., 0]) ** 2 +
            (warped_flow_y + flow_backward[..., 1]) ** 2
        )
        
        # Mark as consistent where inconsistency is below threshold
        consistency_mask = inconsistency < self.config.consistency_threshold
        
        return consistency_mask

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

    def _edge_preserving_blend(
        self,
        current_depth: np.ndarray,
        warped_depth: np.ndarray,
        flow_magnitude: np.ndarray,
        consistency_mask: np.ndarray,
    ) -> np.ndarray:
        """Blend depth maps with edge preservation.
        
        Uses depth edges to guide the temporal blending, preserving
        depth discontinuities while smoothing uniform regions.
        
        Args:
            current_depth: Current frame's depth map.
            warped_depth: Warped previous depth map.
            flow_magnitude: Magnitude of optical flow.
            consistency_mask: Forward-backward consistency mask.
        
        Returns:
            Edge-preserving blended depth map.
        """
        # Compute depth edges using gradient
        grad_x = cv2.Sobel(current_depth, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(current_depth, cv2.CV_32F, 0, 1, ksize=3)
        edge_strength = np.sqrt(grad_x ** 2 + grad_y ** 2)
        
        # Normalize edge strength to [0, 1]
        if edge_strength.max() > 0:
            edge_strength = edge_strength / edge_strength.max()
        
        # Compute adaptive blending weight
        # More weight to current frame at edges and in inconsistent regions
        base_alpha = self.config.smoothing_factor
        edge_factor = edge_strength * self.config.edge_preservation_factor
        consistency_factor = (~consistency_mask).astype(np.float32) * _CONSISTENCY_FACTOR
        
        # Adaptive alpha: higher at edges and inconsistent regions
        adaptive_alpha = np.clip(
            base_alpha + edge_factor + consistency_factor,
            0.0,
            1.0
        )
        
        # Blend depth maps
        result = (
            adaptive_alpha * current_depth +
            (1 - adaptive_alpha) * warped_depth
        )
        
        return result.astype(np.float32)

    def _simple_blend(
        self,
        current_depth: np.ndarray,
    ) -> np.ndarray:
        """Simple temporal blend without optical flow.
        
        Args:
            current_depth: Current frame's depth map.
        
        Returns:
            Blended depth map.
        """
        if self.state.previous_depth is None:
            return current_depth.copy()
        
        alpha = self.config.smoothing_factor
        result = alpha * current_depth + (1 - alpha) * self.state.previous_depth
        return result.astype(np.float32)

    def _simple_blend_with_mask(
        self,
        current_depth: np.ndarray,
        warped_depth: np.ndarray,
        consistency_mask: np.ndarray,
    ) -> np.ndarray:
        """Blend depth maps with consistency mask.
        
        Args:
            current_depth: Current frame's depth map.
            warped_depth: Warped previous depth map.
            consistency_mask: Forward-backward consistency mask.
        
        Returns:
            Blended depth map.
        """
        alpha = self.config.smoothing_factor
        
        # In inconsistent regions, prefer current depth
        blended = alpha * current_depth + (1 - alpha) * warped_depth
        
        # Use current depth in inconsistent regions
        result = np.where(
            consistency_mask[..., np.newaxis]
            if consistency_mask.ndim == 3
            else consistency_mask,
            blended,
            current_depth,
        )
        
        return result.astype(np.float32)

    def _refine_depth_consistency(
        self,
        smoothed: np.ndarray,
        current_depth: np.ndarray,
        warped_depth: np.ndarray,
        motion_mask: np.ndarray,
        flow_magnitude: np.ndarray,
    ) -> np.ndarray:
        """Refine depth consistency for moving objects.
        
        Ensures depth values remain consistent for tracked objects across
        frames by analyzing motion patterns and depth continuity.
        
        Args:
            smoothed: Currently smoothed depth map.
            current_depth: Current frame's raw depth map.
            warped_depth: Warped previous depth map.
            motion_mask: Boolean mask of moving regions.
            flow_magnitude: Magnitude of optical flow.
        
        Returns:
            Refined depth map with improved motion consistency.
        """
        # Compute depth difference
        depth_diff = np.abs(current_depth - warped_depth)
        
        # Identify regions with both high motion and depth inconsistency
        motion_depth_conflict = motion_mask & (
            depth_diff > self.config.flow_threshold * _MOTION_MASK_THRESHOLD_FACTOR
        )
        
        # For regions with motion-depth conflict, use a weighted combination
        # that favors temporal consistency while preserving current depth structure
        consistency_weight = self.config.depth_consistency_weight
        
        # Create refined result
        refined = smoothed.copy()
        
        # In motion regions, blend more towards the current depth to avoid
        # ghosting artifacts while maintaining some temporal smoothness
        if motion_depth_conflict.any():
            # Use bilateral-like weighting based on depth similarity
            # This preserves depth edges within moving regions
            refined = np.where(
                motion_depth_conflict[..., np.newaxis]
                if motion_depth_conflict.ndim == 3
                else motion_depth_conflict,
                (1 - consistency_weight) * smoothed + consistency_weight * current_depth,
                refined,
            )
        
        # Apply light bilateral filtering to smooth while preserving edges
        refined_8bit = (refined * 255).astype(np.uint8)
        smoothed_bilateral = cv2.bilateralFilter(
            refined_8bit,
            d=_BILATERAL_D,
            sigmaColor=_BILATERAL_SIGMA_COLOR,
            sigmaSpace=_BILATERAL_SIGMA_SPACE,
        )

        # Blend bilateral filtered result
        result = (
            _BILATERAL_BLEND_WEIGHT * refined +
            (1 - _BILATERAL_BLEND_WEIGHT) * (smoothed_bilateral.astype(np.float32) / 255.0)
        )
        # Blend bilateral filtered result
        result = 0.7 * refined + 0.3 * (smoothed_bilateral.astype(np.float32) / 255.0)
        
        return result.astype(np.float32)

    def process_batch(
        self,
        depth_maps: list[np.ndarray],
        frames: list[np.ndarray],
    ) -> list[np.ndarray]:
        """Process a batch of depth maps with motion-compensated smoothing.
        
        Args:
            depth_maps: List of depth maps to smooth.
            frames: List of RGB frames (required for optical flow).
        
        Returns:
            List of motion-compensated smoothed depth maps.
        
        Raises:
            ValueError: If depth_maps and frames have different lengths.
        """
        if len(frames) != len(depth_maps):
            raise ValueError(
                f"Length mismatch: depth_maps has {len(depth_maps)} items, "
                f"but frames has {len(frames)} items"
            )

        if not depth_maps:
            return []

        results = []
        self.reset()

        for depth_map, frame in zip(depth_maps, frames):
            smoothed = self.smooth(depth_map, frame)
            results.append(smoothed)

        return results

    def __call__(
        self,
        depth_map: np.ndarray,
        frame: np.ndarray,
    ) -> np.ndarray:
        """Apply motion-compensated smoothing (callable interface).
        
        Args:
            depth_map: Input depth map.
            frame: RGB frame for optical flow.
        
        Returns:
            Smoothed depth map.
        """
        return self.smooth(depth_map, frame)


# ---------------------------------------------------------------------------
# Convenience Functions for Motion-Compensated Smoothing
# ---------------------------------------------------------------------------


def create_motion_compensated_smoother(
    smoothing_factor: float = 0.5,
    **kwargs: Union[str, float, int, bool],
) -> MotionCompensatedSmoother:
    """Create a motion-compensated smoother with the specified configuration.
    
    Args:
        smoothing_factor: Weight for current frame (0-1).
        **kwargs: Additional MotionCompensatedConfig field values.
    
    Returns:
        Configured MotionCompensatedSmoother instance.
    """
    config = MotionCompensatedConfig(
        smoothing_factor=smoothing_factor,
        **kwargs,  # type: ignore[arg-type]
    )
    return MotionCompensatedSmoother(config=config)


def smooth_depth_motion_compensated(
    depth_maps: list[np.ndarray],
    frames: list[np.ndarray],
    smoothing_factor: float = 0.5,
) -> list[np.ndarray]:
    """Apply motion-compensated smoothing to a sequence of depth maps.
    
    This is a convenience function for batch processing.
    
    Args:
        depth_maps: List of depth maps to smooth.
        frames: List of RGB frames (for optical flow).
        smoothing_factor: Weight for current frame.
    
    Returns:
        List of smoothed depth maps.
    """
    smoother = create_motion_compensated_smoother(
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
    # Motion-compensated classes
    "MotionCompensatedSmoother",
    "MotionCompensatedConfig",
    # Enums
    "TemporalSmoothingMethod",
    # Functions
    "create_temporal_smoother",
    "smooth_depth_temporal",
    "create_motion_compensated_smoother",
    "smooth_depth_motion_compensated",
    # Constants
    "_DEFAULT_SMOOTHING_FACTOR",
    "_DEFAULT_FLOW_THRESHOLD",
    "_DEFAULT_WINDOW_SIZE",
]
