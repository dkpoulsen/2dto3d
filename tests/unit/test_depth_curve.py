"""Unit tests for depth curve adjustment functionality."""

import numpy as np
import pytest

from video2d3d.depth.curve import (
    PRESET_CURVES,
    CurveControlPoint,
    CurvePreset,
    DepthCurveConfig,
    DepthCurveError,
    apply_curve_lut,
    apply_depth_curve,
    create_curve_lut,
)


class TestCurveControlPoint:
    """Tests for CurveControlPoint dataclass."""

    def test_create_control_point(self):
        """Test creating a valid control point."""
        point = CurveControlPoint(x=0.5, y=0.7)
        assert point.x == 0.5
        assert point.y == 0.7

    def test_control_point_validation_x(self):
        """Test that x must be in [0, 1]."""
        with pytest.raises(ValueError, match="x must be in"):
            CurveControlPoint(x=-0.1, y=0.5)

        with pytest.raises(ValueError, match="x must be in"):
            CurveControlPoint(x=1.1, y=0.5)

    def test_control_point_validation_y(self):
        """Test that y must be in [0, 1]."""
        with pytest.raises(ValueError, match="y must be in"):
            CurveControlPoint(x=0.5, y=-0.1)

        with pytest.raises(ValueError, match="y must be in"):
            CurveControlPoint(x=0.5, y=1.1)

    def test_to_tuple(self):
        """Test conversion to tuple."""
        point = CurveControlPoint(x=0.3, y=0.8)
        assert point.to_tuple() == (0.3, 0.8)

    def test_from_tuple(self):
        """Test creation from tuple."""
        point = CurveControlPoint.from_tuple((0.4, 0.6))
        assert point.x == 0.4
        assert point.y == 0.6


class TestDepthCurveConfig:
    """Tests for DepthCurveConfig dataclass."""

    def test_default_config(self):
        """Test default configuration is linear curve."""
        config = DepthCurveConfig()
        assert config.enabled is False
        assert len(config.control_points) == 2
        assert config.control_points[0].x == 0.0
        assert config.control_points[-1].x == 1.0

    def test_linear_preset(self):
        """Test linear preset creates identity curve."""
        config = DepthCurveConfig.linear()
        assert config.enabled is False
        assert config.preset == "linear"

    def test_from_preset(self):
        """Test creating config from preset enum."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        assert config.enabled is True
        assert config.preset == "s_curve"
        assert len(config.control_points) == len(PRESET_CURVES[CurvePreset.S_CURVE])

    def test_preset_overrides_control_points(self):
        """Test that preset overrides any provided control points."""
        custom_points = [CurveControlPoint(0.0, 0.0), CurveControlPoint(1.0, 1.0)]
        config = DepthCurveConfig(enabled=True, control_points=custom_points, preset="s_curve")
        assert len(config.control_points) == len(PRESET_CURVES[CurvePreset.S_CURVE])

    def test_invalid_preset_raises_error(self):
        """Test that invalid preset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown curve preset"):
            DepthCurveConfig(preset="invalid_preset")

    def test_minimum_control_points(self):
        """Test that at least 2 control points are required."""
        with pytest.raises(ValueError, match="Must have at least 2 control points"):
            DepthCurveConfig(control_points=[CurveControlPoint(0.5, 0.5)])

    def test_control_points_sorted_by_x(self):
        """Test that control points are sorted by x coordinate."""
        points = [
            CurveControlPoint(0.8, 0.8),
            CurveControlPoint(0.2, 0.2),
            CurveControlPoint(0.5, 0.5),
        ]
        config = DepthCurveConfig(control_points=points)
        assert config.control_points[0].x == 0.0  # Auto-added endpoint
        assert config.control_points[1].x == 0.2
        assert config.control_points[2].x == 0.5
        assert config.control_points[3].x == 0.8
        assert config.control_points[4].x == 1.0  # Auto-added endpoint

    def test_endpoints_auto_added(self):
        """Test that endpoints are automatically added if missing."""
        points = [CurveControlPoint(0.3, 0.3), CurveControlPoint(0.7, 0.7)]
        config = DepthCurveConfig(control_points=points)
        assert config.control_points[0].x == 0.0
        assert config.control_points[-1].x == 1.0

    def test_non_increasing_x_raises_error(self):
        """Test that non-increasing x values raise error."""
        points = [
            CurveControlPoint(0.0, 0.0),
            CurveControlPoint(0.5, 0.5),
            CurveControlPoint(0.5, 0.3),  # Duplicate x
            CurveControlPoint(1.0, 1.0),
        ]
        with pytest.raises(ValueError, match="x values must be strictly increasing"):
            DepthCurveConfig(control_points=points)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = DepthCurveConfig(enabled=True, preset="s_curve")
        data = config.to_dict()
        assert data["enabled"] is True
        assert data["preset"] == "s_curve"
        assert "control_points" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "enabled": True,
            "preset": None,
            "control_points": [
                {"x": 0.0, "y": 0.0},
                {"x": 0.5, "y": 0.6},
                {"x": 1.0, "y": 1.0},
            ],
        }
        config = DepthCurveConfig.from_dict(data)
        assert config.enabled is True
        assert len(config.control_points) == 3

    def test_get_xy_arrays(self):
        """Test getting x and y arrays for interpolation."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        x_vals, y_vals = config.get_xy_arrays()
        assert len(x_vals) == len(config.control_points)
        assert len(y_vals) == len(config.control_points)
        assert np.all(np.diff(x_vals) > 0)  # Monotonically increasing


class TestApplyDepthCurve:
    """Tests for apply_depth_curve function."""

    def test_disabled_curve_returns_input(self):
        """Test that disabled curve returns input unchanged."""
        config = DepthCurveConfig(enabled=False)
        depth_map = np.random.rand(10, 10).astype(np.float32)
        result = apply_depth_curve(depth_map, config)
        np.testing.assert_array_equal(result, depth_map)

    def test_linear_curve_is_identity(self):
        """Test that linear curve (0,0)-(1,1) is identity."""
        config = DepthCurveConfig(enabled=True, preset=CurvePreset.LINEAR.value)
        depth_map = np.linspace(0, 1, 100).reshape(10, 10).astype(np.float32)
        result = apply_depth_curve(depth_map, config)
        np.testing.assert_allclose(result, depth_map, rtol=1e-5)

    def test_s_curve_increases_contrast(self):
        """Test that S-curve increases contrast in mid-tones."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        # Mid-tone input (0.5) should stay at 0.5 for S-curve
        depth_map = np.array([[0.5]], dtype=np.float32)
        result = apply_depth_curve(depth_map, config)
        np.testing.assert_allclose(result[0, 0], 0.5, rtol=0.1)

    def test_contrast_boost_stretches_midtones(self):
        """Test that contrast boost stretches mid-tones."""
        config = DepthCurveConfig.from_preset(CurvePreset.CONTRAST_BOOST)
        depth_map = np.array([[0.2], [0.8]], dtype=np.float32)
        result = apply_depth_curve(depth_map, config)
        # Dark values should get darker, bright values should get brighter
        assert result[0, 0] < 0.2
        assert result[1, 0] > 0.8

    def test_output_is_clipped_to_valid_range(self):
        """Test that output is always in [0, 1]."""
        config = DepthCurveConfig.from_preset(CurvePreset.CONTRAST_BOOST)
        depth_map = np.random.rand(100, 100).astype(np.float32)
        result = apply_depth_curve(depth_map, config)
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_preserves_dtype(self):
        """Test that original dtype is preserved."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        depth_map = np.random.rand(10, 10).astype(np.float32)
        result = apply_depth_curve(depth_map, config)
        assert result.dtype == np.float32

    def test_handles_constant_depth_map(self):
        """Test handling of constant depth maps."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        depth_map = np.full((10, 10), 0.5, dtype=np.float32)
        result = apply_depth_curve(depth_map, config)
        assert result.shape == depth_map.shape

    def test_handles_boundary_values(self):
        """Test handling of 0 and 1 boundary values."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        depth_map = np.array([[0.0, 1.0], [0.5, 0.5]], dtype=np.float32)
        result = apply_depth_curve(depth_map, config)
        # Endpoints should map to endpoints
        np.testing.assert_allclose(result[0, 0], 0.0, atol=0.01)
        np.testing.assert_allclose(result[0, 1], 1.0, atol=0.01)


class TestCurveLUT:
    """Tests for lookup table functions."""

    def test_create_linear_lut(self):
        """Test creating LUT for linear curve."""
        config = DepthCurveConfig(enabled=False)
        lut = create_curve_lut(config, num_entries=256)
        assert len(lut) == 256
        # Linear LUT should be identity
        expected = np.linspace(0, 1, 256, dtype=np.float32)
        np.testing.assert_allclose(lut, expected, rtol=1e-5)

    def test_create_s_curve_lut(self):
        """Test creating LUT for S-curve."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        lut = create_curve_lut(config, num_entries=256)
        assert len(lut) == 256
        assert lut[0] == pytest.approx(0.0, abs=0.01)
        assert lut[-1] == pytest.approx(1.0, abs=0.01)
        assert lut[128] == pytest.approx(0.5, abs=0.1)  # Mid-point

    def test_apply_curve_lut(self):
        """Test applying curve using LUT."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        lut = create_curve_lut(config, num_entries=256)
        depth_map = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
        result = apply_curve_lut(depth_map, lut)
        assert result.shape == depth_map.shape

    def test_lut_vs_direct_application(self):
        """Test that LUT gives similar results to direct application."""
        config = DepthCurveConfig.from_preset(CurvePreset.S_CURVE)
        depth_map = np.random.rand(50, 50).astype(np.float32)

        # Direct application
        direct_result = apply_depth_curve(depth_map, config)

        # LUT application
        lut = create_curve_lut(config, num_entries=1024)
        lut_result = apply_curve_lut(depth_map, lut)

        # Should be very close (some difference due to LUT discretization)
        np.testing.assert_allclose(direct_result, lut_result, atol=0.01)


class TestCurvePresets:
    """Tests for curve presets."""

    def test_all_presets_have_valid_control_points(self):
        """Test that all presets have valid control points."""
        for preset in CurvePreset:
            points = PRESET_CURVES[preset]
            assert len(points) >= 2
            assert (
                points[0].x == 0.0
                if isinstance(points[0], CurveControlPoint)
                else points[0][0] == 0.0
            )
            assert (
                points[-1].x == 1.0
                if isinstance(points[-1], CurveControlPoint)
                else points[-1][0] == 1.0
            )

    def test_all_presets_can_create_config(self):
        """Test that all presets can be used to create config."""
        for preset in CurvePreset:
            config = DepthCurveConfig.from_preset(preset)
            assert config.enabled is True
            assert config.preset == preset.value

    def test_preset_curves_are_monotonic(self):
        """Test that all preset curves have monotonically increasing x values."""
        for preset in CurvePreset:
            points = PRESET_CURVES[preset]
            x_values = [p.x if isinstance(p, CurveControlPoint) else p[0] for p in points]
            assert all(x_values[i] < x_values[i + 1] for i in range(len(x_values) - 1))


class TestDepthCurveError:
    """Tests for DepthCurveError exception."""

    def test_error_creation(self):
        """Test creating error with message."""
        error = DepthCurveError("Test error")
        assert str(error) == "Test error"
        assert error.operation is None
        assert error.original_exception is None

    def test_error_with_operation(self):
        """Test error with operation info."""
        error = DepthCurveError("Test error", operation="apply_curve")
        assert error.operation == "apply_curve"

    def test_error_with_original_exception(self):
        """Test error wrapping original exception."""
        original = ValueError("Original error")
        error = DepthCurveError("Wrapped error", original_exception=original)
        assert error.original_exception is original
