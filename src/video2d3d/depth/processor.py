"""Depth map post-processing and refinement module.

This module provides depth map post-processing functionality including:
- Normalization (min-max, percentile, histogram equalization)
- Edge-aware filtering (bilateral filter, guided filter)
- Hole-filling (inpainting, nearest neighbor)
- Color mapping for visualization

The processor is designed to work with depth maps produced by DepthEstimator
and can be configured via the depth_processing section in the config.
"""

from __future__ import annotations

import time
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
_DEFAULT_SMOOTHING_RADIUS: int = 3
_DEFAULT_BILATERAL_SIGMA_COLOR: float = 0.1
_DEFAULT_BILATERAL_SIGMA_SPACE: int = 5
_DEFAULT_SHARPENING_AMOUNT: float = 0.5
_DEFAULT_PERCENTILE_LOW: float = 2.0
_DEFAULT_PERCENTILE_HIGH: float = 98.0
_DEFAULT_GUIDED_FILTER_RADIUS: int = 8
_DEFAULT_GUIDED_FILTER_EPS: float = 0.01

class NormalizationMethod(Enum):
    """Available depth normalization methods."""

    MIN_MAX = "min_max"
    PERCENTILE = "percentile"
    HISTOGRAM_EQUALIZATION = "histogram_equalization"


class HoleFillingMethod(Enum):
    """Available hole-filling methods."""

    INPAINT = "inpaint"
    NEAREST = "nearest"
    LINEAR = "linear"

class ColorMapType(Enum):
    """Available color map types for visualization."""

    TURBO = cv2.COLORMAP_TURBO
    PLASMA = cv2.COLORMAP_PLASMA
    VIRIDIS = cv2.COLORMAP_VIRIDIS
    MAGMA = cv2.COLORMAP_MAGMA
    JET = cv2.COLORMAP_JET
    INFERNO = cv2.COLORMAP_INFERNO
    GRAY = None  # Grayscale output


class EdgeAwareFilterType(Enum):
    """Available edge-aware filter types."""

    BILATERAL = "bilateral"
    GUIDED = "guided"
    NONE = "none"

@dataclass
class DepthProcessorConfig:
    """Configuration for depth map post-processing.

    Attributes:
        edge_aware_smoothing: Enable edge-aware smoothing.
        smoothing_radius: Radius for smoothing operations.
        bilateral_filter: Enable bilateral filtering.
        bilateral_sigma_color: Sigma for color space in bilateral filter.
        bilateral_sigma_space: Sigma for coordinate space in bilateral filter.
        guided_filter: Enable guided filtering.
        guided_filter_radius: Radius for guided filter window.
        guided_filter_eps: Regularization parameter for guided filter.
        edge_filter_type: Type of edge-aware filter to use ('bilateral', 'guided', 'none').
        hole_filling: Enable hole-filling for occlusions.
        hole_filling_method: Method to use for hole-filling.
        sharpening: Enable depth map sharpening.
        sharpening_amount: Amount of sharpening to apply (0.0 to 1.0).
        normalization_method: Method for depth normalization.
        percentile_low: Lower percentile for percentile normalization.
        percentile_high: Upper percentile for percentile normalization.
        colormap: Color map type for visualization.
    """

    edge_aware_smoothing: bool = True
    smoothing_radius: int = _DEFAULT_SMOOTHING_RADIUS
    bilateral_filter: bool = True
    bilateral_sigma_color: float = _DEFAULT_BILATERAL_SIGMA_COLOR
    bilateral_sigma_space: int = _DEFAULT_BILATERAL_SIGMA_SPACE
    guided_filter: bool = False
    guided_filter_radius: int = _DEFAULT_GUIDED_FILTER_RADIUS
    guided_filter_eps: float = _DEFAULT_GUIDED_FILTER_EPS
    edge_filter_type: str = "bilateral"
    hole_filling: bool = True
    hole_filling_method: str = "inpaint"
    sharpening: bool = False
    sharpening_amount: float = _DEFAULT_SHARPENING_AMOUNT
    normalization_method: str = "min_max"
    percentile_low: float = _DEFAULT_PERCENTILE_LOW
    percentile_high: float = _DEFAULT_PERCENTILE_HIGH
    colormap: str = "turbo"
    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Validate normalization method
        valid_methods = [m.value for m in NormalizationMethod]
        if self.normalization_method not in valid_methods:
            raise ValueError(
                f"Invalid normalization method '{self.normalization_method}'. "
                f"Valid options: {valid_methods}"
            )

        # Validate hole filling method
        valid_fill_methods = [m.value for m in HoleFillingMethod]
        if self.hole_filling_method not in valid_fill_methods:
            raise ValueError(
                f"Invalid hole filling method '{self.hole_filling_method}'. "
                f"Valid options: {valid_fill_methods}"
            )

        # Validate colormap
        valid_colormaps = [m.name.lower() for m in ColorMapType]
        if self.colormap.lower() not in valid_colormaps:
            raise ValueError(
                f"Invalid colormap '{self.colormap}'. Valid options: {valid_colormaps}"
            )

        # Validate ranges
        if not 0.0 <= self.sharpening_amount <= 1.0:
            raise ValueError(f"sharpening_amount must be in [0, 1], got {self.sharpening_amount}")

        if not 0.0 <= self.percentile_low < self.percentile_high <= 100.0:
            raise ValueError(
                f"percentile_low ({self.percentile_low}) must be less than "
                f"percentile_high ({self.percentile_high}), both in [0, 100]"
            )

        if self.smoothing_radius < 1:
            raise ValueError(f"smoothing_radius must be >= 1, got {self.smoothing_radius}")

        # Validate guided filter parameters
        if self.guided_filter_radius < 1:
            raise ValueError(
                f"guided_filter_radius must be >= 1, got {self.guided_filter_radius}"
            )

        if self.guided_filter_eps <= 0:
            raise ValueError(
                f"guided_filter_eps must be > 0, got {self.guided_filter_eps}"
            )

        # Validate edge filter type
        valid_filter_types = [f.value for f in EdgeAwareFilterType]
        if self.edge_filter_type not in valid_filter_types:
            raise ValueError(
                f"Invalid edge_filter_type '{self.edge_filter_type}'. "
                f"Valid options: {valid_filter_types}"
            )

        # Warn about potential config inconsistencies
        if self.edge_filter_type == EdgeAwareFilterType.GUIDED.value and not self.guided_filter:
            # Auto-enable guided_filter if edge_filter_type is guided
            object.__setattr__(self, 'guided_filter', True)
        elif self.edge_filter_type == EdgeAwareFilterType.BILATERAL.value and not self.bilateral_filter:
            # Auto-enable bilateral_filter if edge_filter_type is bilateral
            object.__setattr__(self, 'bilateral_filter', True)


class DepthProcessingError(Exception):
    """Exception raised for depth processing errors."""

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


def _get_processor_logger() -> "Logger":
    """Get the depth processor logger (lazy initialization)."""
    return get_logger("depth.processor")


class DepthMapProcessor:
    """Post-process depth maps for improved quality and visualization.

    This class provides a pipeline of depth map post-processing operations
    that can be selectively enabled via configuration.

    Example usage:
        ```python
        # Basic usage
        processor = DepthMapProcessor()
        processed = processor.process(depth_map)

        # With configuration
        config = DepthProcessorConfig(
            bilateral_filter=True,
            hole_filling=True,
            colormap="plasma"
        )
        processor = DepthMapProcessor(config=config)
        processed = processor.process(depth_map)

        # Individual operations
        normalized = processor.normalize(depth_map, method="percentile")
        filtered = processor.apply_bilateral_filter(normalized)
        colored = processor.apply_colormap(filtered)
        ```

    Attributes:
        config: DepthProcessorConfig object.
    """

    def __init__(
        self,
        config: Optional[DepthProcessorConfig] = None,
        *,
        edge_aware_smoothing: bool = True,
        bilateral_filter: bool = True,
        hole_filling: bool = True,
        colormap: str = "turbo",
    ) -> None:
        """Initialize the depth map processor.

        Args:
            config: DepthProcessorConfig object. If provided, other args ignored.
            edge_aware_smoothing: Enable edge-aware smoothing.
            bilateral_filter: Enable bilateral filtering.
            hole_filling: Enable hole-filling.
            colormap: Default color map for visualization.
        """
        if config is not None:
            self.config = config
        else:
            self.config = DepthProcessorConfig(
                edge_aware_smoothing=edge_aware_smoothing,
                bilateral_filter=bilateral_filter,
                hole_filling=hole_filling,
                colormap=colormap,
            )

        self._logger = _get_processor_logger()
        self._logger.debug(
            f"DepthMapProcessor initialized: smoothing={self.config.edge_aware_smoothing}, "
            f"bilateral={self.config.bilateral_filter}, hole_fill={self.config.hole_filling}"
        )

    def normalize(
        self,
        depth_map: np.ndarray,
        method: Optional[str] = None,
    ) -> np.ndarray:
        """Normalize depth map to [0, 1] range.

        Args:
            depth_map: Input depth map as float32 array.
            method: Normalization method. If None, uses config setting.
                   Options: 'min_max', 'percentile', 'histogram_equalization'

        Returns:
            Normalized depth map with values in [0, 1].

        Raises:
            DepthProcessingError: If normalization fails.
        """
        norm_method = method or self.config.normalization_method

        try:
            if norm_method == NormalizationMethod.MIN_MAX.value:
                return self._normalize_min_max(depth_map)
            elif norm_method == NormalizationMethod.PERCENTILE.value:
                return self._normalize_percentile(depth_map)
            elif norm_method == NormalizationMethod.HISTOGRAM_EQUALIZATION.value:
                return self._normalize_histogram(depth_map)
            else:
                raise DepthProcessingError(
                    f"Unknown normalization method: {norm_method}",
                    operation="normalize",
                )
        except DepthProcessingError:
            raise
        except Exception as e:
            log_exception("Normalization failed", exception=e, method=norm_method)
            raise DepthProcessingError(
                f"Normalization failed: {e}",
                operation="normalize",
                original_exception=e,
            ) from e

    def _normalize_min_max(self, depth_map: np.ndarray) -> np.ndarray:
        """Normalize using min-max scaling."""
        depth_min = depth_map.min()
        depth_max = depth_map.max()

        if depth_max - depth_min < 1e-8:
            # Constant depth, return zeros
            return np.zeros_like(depth_map, dtype=np.float32)

        normalized = (depth_map - depth_min) / (depth_max - depth_min)
        return normalized.astype(np.float32)

    def _normalize_percentile(self, depth_map: np.ndarray) -> np.ndarray:
        """Normalize using percentile clipping."""
        low = np.percentile(depth_map, self.config.percentile_low)
        high = np.percentile(depth_map, self.config.percentile_high)

        if high - low < 1e-8:
            return np.zeros_like(depth_map, dtype=np.float32)

        # Clip to percentile range
        clipped = np.clip(depth_map, low, high)
        normalized = (clipped - low) / (high - low)
        return normalized.astype(np.float32)

    def _normalize_histogram(self, depth_map: np.ndarray) -> np.ndarray:
        """Normalize using histogram equalization."""
        # Convert to 8-bit for histogram equalization
        depth_8bit = (depth_map * 255).astype(np.uint8)

        # Apply histogram equalization
        equalized = cv2.equalizeHist(depth_8bit)

        # Convert back to float
        return equalized.astype(np.float32) / 255.0

    def apply_bilateral_filter(
        self,
        depth_map: np.ndarray,
        sigma_color: Optional[float] = None,
        sigma_space: Optional[int] = None,
    ) -> np.ndarray:
        """Apply edge-preserving bilateral filter to depth map.

        This filter smooths the depth map while preserving edges,
        which is important for maintaining depth discontinuities.

        Args:
            depth_map: Input depth map (values in [0, 1]).
            sigma_color: Filter sigma in color space. If None, uses config.
            sigma_space: Filter sigma in coordinate space. If None, uses config.

        Returns:
            Filtered depth map.

        Raises:
            DepthProcessingError: If filtering fails.
        """
        sigma_c = sigma_color if sigma_color is not None else self.config.bilateral_sigma_color
        sigma_s = sigma_space if sigma_space is not None else self.config.bilateral_sigma_space

        try:
            # Convert to 8-bit for bilateral filter
            depth_8bit = (depth_map * 255).astype(np.uint8)

            # Apply bilateral filter
            # d=-1 means diameter is computed from sigma_space
            filtered = cv2.bilateralFilter(
                depth_8bit,
                d=-1,
                sigmaColor=sigma_c * 255,  # Scale to 8-bit range
                sigmaSpace=sigma_s,
            )

            # Convert back to float
            return filtered.astype(np.float32) / 255.0

        except Exception as e:
            log_exception("Bilateral filter failed", exception=e)
            raise DepthProcessingError(
                f"Bilateral filter failed: {e}",
                operation="bilateral_filter",
                original_exception=e,
            ) from e

    def apply_guided_filter(
        self,
        depth_map: np.ndarray,
        guidance: Optional[np.ndarray] = None,
        radius: Optional[int] = None,
        eps: Optional[float] = None,
    ) -> np.ndarray:
        """Apply edge-preserving guided filter to depth map.

        The guided filter uses a guidance image to preserve edges while
        smoothing. It performs better than bilateral filter for edge preservation
        and is computationally more efficient.

        Based on: He et al., "Guided Image Filtering", PAMI 2010.

        Args:
            depth_map: Input depth map (values in [0, 1]).
            guidance: Optional guidance image. If None, uses depth_map as guidance.
            radius: Radius of the local window. If None, uses config.
            eps: Regularization parameter. If None, uses config.
                 Larger values = more smoothing, smaller = edge preservation.

        Returns:
            Filtered depth map.

        Raises:
            DepthProcessingError: If filtering fails.
        """
        r = radius if radius is not None else self.config.guided_filter_radius
        epsilon = eps if eps is not None else self.config.guided_filter_eps

        # Validate image size vs filter radius
        min_dimension = min(depth_map.shape[0], depth_map.shape[1])
        if min_dimension <= 2 * r:
            # Image too small for the requested radius, adjust it
            r = max(1, (min_dimension - 1) // 2)
            self._logger.debug(
                f"Adjusted guided filter radius from {radius} to {r} for image size {depth_map.shape}"
            )

        # Use depth map as guidance if not provided
        if guidance is None:
            I = depth_map.astype(np.float64)
        else:
            I = guidance.astype(np.float64)

        p = depth_map.astype(np.float64)

        try:
            self._logger.debug(f"Applying guided filter: radius={r}, eps={epsilon}")
            # Compute box filter (mean) using integral images
            # This is a fast implementation using cv2.boxFilter
            mean_I = cv2.boxFilter(I, -1, (2 * r + 1, 2 * r + 1), normalize=True)
            mean_p = cv2.boxFilter(p, -1, (2 * r + 1, 2 * r + 1), normalize=True)

            # Compute correlation
            mean_Ip = cv2.boxFilter(I * p, -1, (2 * r + 1, 2 * r + 1), normalize=True)

            # Compute covariance and variance
            cov_Ip = mean_Ip - mean_I * mean_p
            mean_II = cv2.boxFilter(I * I, -1, (2 * r + 1, 2 * r + 1), normalize=True)
            var_I = mean_II - mean_I * mean_I

            # Compute linear coefficients a and b
            a = cov_Ip / (var_I + epsilon)
            b = mean_p - a * mean_I

            # Compute mean of a and b
            mean_a = cv2.boxFilter(a, -1, (2 * r + 1, 2 * r + 1), normalize=True)
            mean_b = cv2.boxFilter(b, -1, (2 * r + 1, 2 * r + 1), normalize=True)

            # Compute output
            q = mean_a * I + mean_b

            # Clip to valid range and convert back to float32
            result = np.clip(q, 0.0, 1.0).astype(np.float32)
            return result

        except Exception as e:
            log_exception("Guided filter failed", exception=e)
            raise DepthProcessingError(
                f"Guided filter failed: {e}",
                operation="guided_filter",
                original_exception=e,
            ) from e


    def fill_holes(
        self,
        depth_map: np.ndarray,
        method: Optional[str] = None,
    ) -> np.ndarray:
        """Fill holes (invalid/zero regions) in the depth map.

        Args:
            depth_map: Input depth map (values in [0, 1]).
            method: Hole-filling method. If None, uses config setting.
                   Options: 'inpaint', 'nearest', 'linear'

        Returns:
            Depth map with holes filled.

        Raises:
            DepthProcessingError: If hole filling fails.
        """
        fill_method = method or self.config.hole_filling_method

        try:
            if fill_method == HoleFillingMethod.INPAINT.value:
                return self._fill_holes_inpaint(depth_map)
            elif fill_method == HoleFillingMethod.NEAREST.value:
                return self._fill_holes_nearest(depth_map)
            elif fill_method == HoleFillingMethod.LINEAR.value:
                return self._fill_holes_linear(depth_map)
            else:
                raise DepthProcessingError(
                    f"Unknown hole filling method: {fill_method}",
                    operation="fill_holes",
                )
        except DepthProcessingError:
            raise
        except Exception as e:
            log_exception("Hole filling failed", exception=e, method=fill_method)
            raise DepthProcessingError(
                f"Hole filling failed: {e}",
                operation="fill_holes",
                original_exception=e,
            ) from e

    def _fill_holes_inpaint(self, depth_map: np.ndarray) -> np.ndarray:
        """Fill holes using inpainting (Navier-Stokes based)."""
        # Detect holes (very small values or NaN)
        mask = (depth_map < 1e-6) | np.isnan(depth_map)
        mask_uint8 = mask.astype(np.uint8) * 255

        if not mask.any():
            return depth_map

        # Convert to 8-bit
        depth_8bit = (np.nan_to_num(depth_map) * 255).astype(np.uint8)

        # Apply inpainting (Navier-Stokes method)
        filled = cv2.inpaint(depth_8bit, mask_uint8, inpaintRadius=3, flags=cv2.INPAINT_NS)

        return filled.astype(np.float32) / 255.0

    def _fill_holes_nearest(self, depth_map: np.ndarray) -> np.ndarray:
        """Fill holes using nearest-neighbor interpolation."""
        result = depth_map.copy()

        # Create mask of invalid pixels
        mask = (result < 1e-6) | np.isnan(result)

        if not mask.any():
            return result

        # Replace NaNs with 0 for distance calculation
        result = np.nan_to_num(result)

        # Use distance transform to find nearest valid value
        valid_mask = (~mask).astype(np.uint8)

        # Get indices of nearest valid pixels
        dist, labels = cv2.distanceTransformWithLabels(
            valid_mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE
        )

        # Create output by indexing into original
        # First, get coordinates of all valid pixels
        valid_coords = np.where(~mask)
        if len(valid_coords[0]) == 0:
            return result

        # Map label indices to valid pixel coordinates
        # The labels start from 0, and 0 is background
        # We need to create an index mapping
        result = result.astype(np.float32)

        # Simple approach: dilate valid regions
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(result, kernel, iterations=10)

        # Only use dilated values where original was invalid
        result[mask] = dilated[mask]

        return result.astype(np.float32)

    def _fill_holes_linear(self, depth_map: np.ndarray) -> np.ndarray:
        """Fill holes using linear interpolation."""
        result = depth_map.copy()

        # Create mask of invalid pixels
        mask = (result < 1e-6) | np.isnan(result)

        if not mask.any():
            return result

        # Replace NaNs with 0
        result = np.nan_to_num(result)

        # Use morphological closing to fill small holes
        kernel_size = self.config.smoothing_radius * 2 + 1
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        # Convert to 8-bit
        depth_8bit = (result * 255).astype(np.uint8)

        # Apply morphological closing
        closed = cv2.morphologyEx(depth_8bit, cv2.MORPH_CLOSE, kernel)

        # Only use closed values where original was invalid
        result_8bit = depth_8bit.copy()
        result_8bit[mask] = closed[mask]

        return result_8bit.astype(np.float32) / 255.0

    def sharpen(
        self,
        depth_map: np.ndarray,
        amount: Optional[float] = None,
    ) -> np.ndarray:
        """Apply unsharp mask sharpening to the depth map.

        Args:
            depth_map: Input depth map (values in [0, 1]).
            amount: Sharpening amount (0.0 to 1.0). If None, uses config.

        Returns:
            Sharpened depth map.

        Raises:
            DepthProcessingError: If sharpening fails.
        """
        sharp_amount = amount if amount is not None else self.config.sharpening_amount

        try:
            # Convert to 8-bit
            depth_8bit = (depth_map * 255).astype(np.uint8)

            # Gaussian blur for unsharp mask
            blurred = cv2.GaussianBlur(depth_8bit, (0, 0), sigmaX=3)

            # Unsharp mask: sharpened = original + amount * (original - blurred)
            # Using addWeighted: result = original*(1+amount) - blurred*amount
            alpha = 1.0 + sharp_amount
            beta = -sharp_amount

            sharpened = cv2.addWeighted(depth_8bit, alpha, blurred, -beta, 0)

            # Clip to valid range
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

            return sharpened.astype(np.float32) / 255.0

        except Exception as e:
            log_exception("Sharpening failed", exception=e)
            raise DepthProcessingError(
                f"Sharpening failed: {e}",
                operation="sharpen",
                original_exception=e,
            ) from e

    def apply_colormap(
        self,
        depth_map: np.ndarray,
        colormap: Optional[str] = None,
    ) -> np.ndarray:
        """Apply color mapping to depth map for visualization.

        Args:
            depth_map: Input depth map (values in [0, 1]).
            colormap: Color map name. If None, uses config setting.
                     Options: 'turbo', 'plasma', 'viridis', 'magma',
                             'jet', 'inferno', 'gray'

        Returns:
            Color-mapped depth map as RGB image (H, W, 3) uint8.

        Raises:
            DepthProcessingError: If color mapping fails.
        """
        colormap_name = (colormap or self.config.colormap).upper()

        try:
            # Normalize to [0, 1] if needed
            if depth_map.max() > 1.0 or depth_map.min() < 0.0:
                depth_map = self._normalize_min_max(depth_map)

            # Convert to 8-bit
            depth_8bit = (depth_map * 255).astype(np.uint8)

            # Get colormap enum value
            if colormap_name == "GRAY":
                # Grayscale output
                return cv2.cvtColor(depth_8bit, cv2.COLOR_GRAY2RGB)

            try:
                colormap_enum = ColorMapType[colormap_name]
            except KeyError:
                valid_names = [m.name for m in ColorMapType]
                raise DepthProcessingError(
                    f"Unknown colormap '{colormap_name}'. Valid options: {valid_names}",
                    operation="apply_colormap",
                )

            # Apply colormap
            colored = cv2.applyColorMap(depth_8bit, colormap_enum.value)

            # Convert BGR to RGB
            return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)

        except DepthProcessingError:
            raise
        except Exception as e:
            log_exception("Color mapping failed", exception=e, colormap=colormap_name)
            raise DepthProcessingError(
                f"Color mapping failed: {e}",
                operation="apply_colormap",
                original_exception=e,
            ) from e

    def process(
        self,
        depth_map: np.ndarray,
        apply_colormap: bool = False,
    ) -> np.ndarray:
        """Process depth map through the full pipeline.

        The pipeline applies operations in the following order:
        1. Normalization
        2. Hole filling (if enabled)
        3. Edge-aware filtering (bilateral or guided, based on edge_filter_type)
        4. Sharpening (if enabled)
        5. Colormap (if requested)

        Args:
            depth_map: Input depth map as float32 array.
            apply_colormap: Whether to apply color mapping for visualization.

        Returns:
            Processed depth map (or colored depth map if apply_colormap=True).

        Raises:
            DepthProcessingError: If processing fails.
        """
        start_time = time.time()
        result = depth_map.astype(np.float32)

        try:
            # Step 1: Normalize
            result = self.normalize(result)

            # Step 2: Fill holes
            if self.config.hole_filling:
                result = self.fill_holes(result)

            # Step 3: Apply edge-aware smoothing
            if self.config.edge_filter_type == EdgeAwareFilterType.BILATERAL.value:
                if self.config.bilateral_filter:
                    self._logger.debug("Applying bilateral filter for edge-aware smoothing")
                    result = self.apply_bilateral_filter(result)
            elif self.config.edge_filter_type == EdgeAwareFilterType.GUIDED.value:
                if self.config.guided_filter:
                    self._logger.debug("Applying guided filter for edge-aware smoothing")
                    result = self.apply_guided_filter(result)
                result = self.sharpen(result)

            # Step 5: Apply colormap for visualization
            if apply_colormap:
                result = self.apply_colormap(result)

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "depth_processing",
                elapsed_ms,
                operations={
                    "normalization": self.config.normalization_method,
                    "hole_filling": self.config.hole_filling,
                    "edge_filter_type": self.config.edge_filter_type,
                    "bilateral_filter": self.config.bilateral_filter,
                    "guided_filter": self.config.guided_filter,
                    "sharpening": self.config.sharpening,
                    "colormap": apply_colormap,
                },
            )

            return result

        except DepthProcessingError:
            raise
        except Exception as e:
            log_exception("Depth processing pipeline failed", exception=e)
            raise DepthProcessingError(
                f"Processing pipeline failed: {e}",
                operation="process",
                original_exception=e,
            ) from e

    def __call__(
        self,
        depth_map: np.ndarray,
        apply_colormap: bool = False,
    ) -> np.ndarray:
        """Process depth map (callable interface).

        Args:
            depth_map: Input depth map.
            apply_colormap: Whether to apply color mapping.

        Returns:
            Processed depth map.
        """
        return self.process(depth_map, apply_colormap=apply_colormap)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_processor(
    bilateral_filter: bool = True,
    hole_filling: bool = True,
    colormap: str = "turbo",
    **kwargs: Union[bool, int, float, str],
) -> DepthMapProcessor:
    """Create a depth map processor with the specified configuration.

    Args:
        bilateral_filter: Enable bilateral filtering.
        guided_filter: Enable guided filtering.
        hole_filling: Enable hole-filling.
        colormap: Default color map for visualization.
        edge_filter_type: Type of edge-aware filter ('bilateral', 'guided', 'none').
        **kwargs: Additional DepthProcessorConfig field values.

    Returns:
        Configured DepthMapProcessor instance.
    """
    config = DepthProcessorConfig(
        bilateral_filter=bilateral_filter,
        guided_filter=kwargs.pop("guided_filter", False),
        edge_filter_type=kwargs.pop("edge_filter_type", "bilateral"),
        hole_filling=hole_filling,
        colormap=colormap,
        **kwargs,  # type: ignore[arg-type]
    )
    return DepthMapProcessor(config=config)


def process_depth_map(
    depth_map: np.ndarray,
    *,
    normalize: bool = True,
    fill_holes: bool = True,
    bilateral_filter: bool = True,
    guided_filter: bool = False,
    colormap: Optional[str] = None,
) -> np.ndarray:
    """Process a depth map with default settings (convenience function).

    Args:
        depth_map: Input depth map.
        normalize: Apply normalization.
        fill_holes: Fill holes in the depth map.
        bilateral_filter: Apply bilateral filtering.
        guided_filter: Apply guided filtering (takes precedence if both enabled).
        colormap: If provided, apply this colormap and return RGB image.

    Returns:
        Processed depth map.
    """
    edge_filter_type = "guided" if guided_filter else ("bilateral" if bilateral_filter else "none")
    config = DepthProcessorConfig(
        edge_aware_smoothing=False,
        bilateral_filter=bilateral_filter,
        guided_filter=guided_filter,
        edge_filter_type=edge_filter_type,
        hole_filling=fill_holes,
        normalization_method="min_max" if normalize else "min_max",
    )

    processor = DepthMapProcessor(config=config)
    return processor.process(depth_map, apply_colormap=colormap is not None)

__all__ = [
    # Classes
    "DepthMapProcessor",
    "DepthProcessorConfig",
    "DepthProcessingError",
    # Enums
    "NormalizationMethod",
    "HoleFillingMethod",
    "ColorMapType",
    "EdgeAwareFilterType",
    # Functions
    "create_processor",
    "process_depth_map",
    # Constants
    "_DEFAULT_SMOOTHING_RADIUS",
    "_DEFAULT_BILATERAL_SIGMA_COLOR",
    "_DEFAULT_BILATERAL_SIGMA_SPACE",
    "_DEFAULT_SHARPENING_AMOUNT",
    "_DEFAULT_GUIDED_FILTER_RADIUS",
    "_DEFAULT_GUIDED_FILTER_EPS",
]
