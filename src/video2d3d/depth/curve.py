"""Depth curve adjustment module for non-linear depth mapping.

This module provides functionality for applying non-linear curve adjustments
to depth maps, allowing users to customize the 3D effect strength for artistic
control. Similar to curves adjustments in photo editing software (like Photoshop),
this enables fine-tuned control over how depth values are mapped.

Key features:
- Cubic spline interpolation for smooth curves
- Control points with x,y coordinates in normalized [0,1] range
- Preset curves for common use cases (linear, s-curve, contrast boost)
- Validation for monotonicity and proper control point ordering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from scipy.interpolate import CubicSpline


class CurvePreset(str, Enum):
    """Built-in curve presets for common adjustments."""

    LINEAR = "linear"  # No adjustment (identity)
    S_CURVE = "s_curve"  # S-curve for enhanced depth contrast
    CONTRAST_BOOST = "contrast_boost"  # High contrast for dramatic 3D
    SOFT_CURVE = "soft_curve"  # Gentle curve for subtle 3D
    INVERSE_S = "inverse_s"  # Inverse S-curve for reduced contrast
    SHADOW_LIFT = "shadow_lift"  # Lift darker regions
    HIGHLIGHT_COMPRESS = "highlight_compress"  # Compress bright regions


# Default control points for each preset
PRESET_CURVES: dict[CurvePreset, list[tuple[float, float]]] = {
    CurvePreset.LINEAR: [(0.0, 0.0), (1.0, 1.0)],
    CurvePreset.S_CURVE: [(0.0, 0.0), (0.25, 0.15), (0.5, 0.5), (0.75, 0.85), (1.0, 1.0)],
    CurvePreset.CONTRAST_BOOST: [(0.0, 0.0), (0.2, 0.05), (0.5, 0.5), (0.8, 0.95), (1.0, 1.0)],
    CurvePreset.SOFT_CURVE: [(0.0, 0.0), (0.3, 0.25), (0.7, 0.75), (1.0, 1.0)],
    CurvePreset.INVERSE_S: [(0.0, 0.0), (0.25, 0.35), (0.5, 0.5), (0.75, 0.65), (1.0, 1.0)],
    CurvePreset.SHADOW_LIFT: [(0.0, 0.15), (0.25, 0.3), (0.5, 0.55), (0.75, 0.8), (1.0, 1.0)],
    CurvePreset.HIGHLIGHT_COMPRESS: [(0.0, 0.0), (0.25, 0.2), (0.5, 0.5), (0.75, 0.75), (1.0, 0.9)],
}


@dataclass
class CurveControlPoint:
    """A single control point on the depth curve.

    Attributes:
        x: Input depth value (normalized 0-1).
        y: Output depth value (normalized 0-1).
    """

    x: float
    y: float

    def __post_init__(self) -> None:
        """Validate control point values."""
        if not 0.0 <= self.x <= 1.0:
            raise ValueError(f"x must be in [0, 1], got {self.x}")
        if not 0.0 <= self.y <= 1.0:
            raise ValueError(f"y must be in [0, 1], got {self.y}")

    def to_tuple(self) -> tuple[float, float]:
        """Convert to tuple format."""
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, t: tuple[float, float]) -> CurveControlPoint:
        """Create from tuple format."""
        return cls(x=t[0], y=t[1])


@dataclass
class DepthCurveConfig:
    """Configuration for depth curve adjustment.

    The curve maps input depth values (x-axis) to output depth values (y-axis).
    Control points define the shape of the curve, and cubic spline interpolation
    creates a smooth transition between points.

    Attributes:
        enabled: Whether curve adjustment is enabled.
        control_points: List of control points defining the curve shape.
            Must include endpoints (0,0) and (1,1) for proper mapping.
        preset: Optional preset name to use instead of custom points.
            If provided, control_points are ignored.
    """

    enabled: bool = False
    control_points: list[CurveControlPoint] = field(
        default_factory=lambda: [
            CurveControlPoint(0.0, 0.0),
            CurveControlPoint(1.0, 1.0),
        ]
    )
    preset: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # If preset is specified, use preset control points
        if self.preset is not None:
            try:
                preset_enum = CurvePreset(self.preset)
                preset_points = PRESET_CURVES[preset_enum]
                self.control_points = [CurveControlPoint(x, y) for x, y in preset_points]
            except ValueError:
                valid_presets = [p.value for p in CurvePreset]
                raise ValueError(
                    f"Unknown curve preset '{self.preset}'. Valid options: {valid_presets}"
                )

        # Validate control points
        if len(self.control_points) < 2:
            raise ValueError(f"Must have at least 2 control points, got {len(self.control_points)}")

        # Sort points by x coordinate, then ensure strictly increasing
        self.control_points = sorted(self.control_points, key=lambda p: p.x)
        xs = [p.x for p in self.control_points]
        if any(b <= a for a, b in zip(xs, xs[1:])):
            raise ValueError("x values must be strictly increasing")

        # Ensure endpoints exist
        first_point = self.control_points[0]
        last_point = self.control_points[-1]

        if abs(first_point.x) > 1e-6:
            self.control_points.insert(0, CurveControlPoint(0.0, first_point.y))
        if abs(last_point.x - 1.0) > 1e-6:
            self.control_points.append(CurveControlPoint(1.0, last_point.y))

        # Validate monotonicity of x coordinates
        for i in range(1, len(self.control_points)):
            if self.control_points[i].x <= self.control_points[i - 1].x:
                raise ValueError(
                    f"Control point x values must be strictly increasing. "
                    f"Point {i}: x={self.control_points[i].x}, "
                    f"Point {i - 1}: x={self.control_points[i - 1].x}"
                )

    def get_xy_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        """Get x and y values as numpy arrays for interpolation.

        Returns:
            Tuple of (x_array, y_array) sorted by x.
        """
        x_vals = np.array([p.x for p in self.control_points])
        y_vals = np.array([p.y for p in self.control_points])
        return x_vals, y_vals

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "control_points": [{"x": p.x, "y": p.y} for p in self.control_points],
            "preset": self.preset,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DepthCurveConfig:
        """Create from dictionary."""
        control_points_data = data.get("control_points", [])
        control_points = [
            CurveControlPoint(x=p.get("x", 0.0), y=p.get("y", 0.0)) for p in control_points_data
        ]

        return cls(
            enabled=data.get("enabled", False),
            control_points=control_points if control_points else None,
            preset=data.get("preset"),
        )

    @classmethod
    def linear(cls) -> DepthCurveConfig:
        """Create a linear (no adjustment) curve config."""
        return cls(enabled=False, preset=CurvePreset.LINEAR.value)

    @classmethod
    def from_preset(cls, preset: CurvePreset) -> DepthCurveConfig:
        """Create a curve config from a preset."""
        return cls(enabled=True, preset=preset.value)


class DepthCurveError(Exception):
    """Exception raised for depth curve processing errors."""

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        original_exception: Exception | None = None,
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


def apply_depth_curve(
    depth_map: np.ndarray,
    config: DepthCurveConfig,
) -> np.ndarray:
    """Apply curve adjustment to a depth map.

    Uses cubic spline interpolation to map input depth values to output
    depth values based on the control points in the configuration.

    Args:
        depth_map: Input depth map with values in [0, 1].
        config: Curve configuration specifying control points.

    Returns:
        Curve-adjusted depth map with values in [0, 1].

    Raises:
        DepthCurveError: If curve application fails.
    """
    if not config.enabled:
        return depth_map

    try:
        # Get control point arrays
        x_vals, y_vals = config.get_xy_arrays()

        depth_clipped = np.clip(depth_map, 0.0, 1.0)

        # Two control points with equal slope is a straight line - use linear
        # interpolation (a clamped cubic spline would bend the identity curve)
        if len(x_vals) == 2:
            result = np.interp(depth_clipped, x_vals, y_vals)
            return result.astype(depth_map.dtype, copy=False)

        # Create cubic spline interpolator
        # Use 'clamped' boundary conditions (first derivative = slope at endpoints)
        spline = CubicSpline(x_vals, y_vals, bc_type="clamped")

        # Apply spline interpolation
        result = spline(depth_clipped)

        # Clip result to valid range (spline can overshoot slightly)
        result = np.clip(result, 0.0, 1.0)

        # Preserve original dtype
        return result.astype(depth_map.dtype)

    except Exception as e:
        raise DepthCurveError(
            f"Failed to apply depth curve: {e}",
            operation="apply_depth_curve",
            original_exception=e,
        ) from e


def create_curve_lut(
    config: DepthCurveConfig,
    num_entries: int = 256,
) -> np.ndarray:
    """Create a lookup table for fast curve application.

    This is useful for real-time preview or repeated application
    of the same curve to many depth maps.

    Args:
        config: Curve configuration.
        num_entries: Number of LUT entries (higher = more precision).

    Returns:
        1D numpy array mapping input indices to output values.
    """
    if not config.enabled:
        # Return identity LUT
        return np.linspace(0.0, 1.0, num_entries, dtype=np.float32)

    # Get control point arrays
    x_vals, y_vals = config.get_xy_arrays()

    # Create spline
    spline = CubicSpline(x_vals, y_vals, bc_type="clamped")

    # Generate LUT
    input_vals = np.linspace(0.0, 1.0, num_entries)
    output_vals = spline(input_vals)

    # Clip to valid range
    output_vals = np.clip(output_vals, 0.0, 1.0)

    return output_vals.astype(np.float32)


def apply_curve_lut(
    depth_map: np.ndarray,
    lut: np.ndarray,
) -> np.ndarray:
    """Apply curve using a pre-computed lookup table.

    This is faster than apply_depth_curve for repeated applications.

    Args:
        depth_map: Input depth map with values in [0, 1].
        lut: Pre-computed lookup table from create_curve_lut().

    Returns:
        Curve-adjusted depth map.
    """
    num_entries = len(lut)

    # Scale depth values to LUT indices
    indices = (depth_map * (num_entries - 1)).astype(np.int32)

    # Clip indices to valid range
    indices = np.clip(indices, 0, num_entries - 1)

    # Apply LUT
    return lut[indices].astype(depth_map.dtype)


__all__ = [
    # Classes
    "DepthCurveConfig",
    "CurveControlPoint",
    "DepthCurveError",
    # Enums
    "CurvePreset",
    # Functions
    "apply_depth_curve",
    "create_curve_lut",
    "apply_curve_lut",
    # Constants
    "PRESET_CURVES",
]
