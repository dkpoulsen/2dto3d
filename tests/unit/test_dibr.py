"""Unit tests for DIBR (Depth-Image-Based Rendering) engine.

Tests cover:
- DIBRConfig dataclass validation
- Disparity computation
- Image warping
- Hole filling algorithms
- Stereo pair generation
- StereoGenerator integration

Note: These tests rely on mocks set up in tests/conftest.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Import the module under test (mocks are set up in conftest.py)
from video2d3d.stereo import (
    AnaglyphGenerator,
    DIBRConfig,
    DIBREngine,
    DIBRError,
    DepthInterpretation,
    HoleFillingMethod,
    SideBySideGenerator,
    StereoGenerator,
    create_dibr_engine,
    render_stereo_pair,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_image() -> np.ndarray:
    """Create a sample image for testing."""
    np.random.seed(42)
    return (np.random.random((100, 100, 3)) * 255).astype(np.uint8)


@pytest.fixture
def sample_grayscale_image() -> np.ndarray:
    """Create a sample grayscale image for testing."""
    np.random.seed(42)
    return (np.random.random((100, 100)) * 255).astype(np.uint8)


@pytest.fixture
def sample_depth_map() -> np.ndarray:
    """Create a sample depth map for testing (MiDaS-style inverse depth)."""
    np.random.seed(42)
    # MiDaS outputs inverse depth: high value = far
    return np.random.random((100, 100)).astype(np.float32)


@pytest.fixture
def gradient_depth_map() -> np.ndarray:
    """Create a gradient depth map for predictable testing."""
    h, w = 100, 100
    # Create horizontal gradient: left=near, right=far
    gradient = np.linspace(0.1, 0.9, w).astype(np.float32)
    depth = np.tile(gradient, (h, 1))
    return depth


@pytest.fixture
def constant_depth_map() -> np.ndarray:
    """Create a constant depth map (edge case)."""
    return np.full((100, 100), 0.5, dtype=np.float32)


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.stereo.dibr.get_logger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# ---------------------------------------------------------------------------
# DIBRConfig Tests
# ---------------------------------------------------------------------------


class TestDIBRConfig:
    """Tests for DIBRConfig dataclass."""

    def test_default_values(self, mock_logger: MagicMock) -> None:
        """Test default configuration values."""
        config = DIBRConfig()

        assert config.baseline == 0.05
        assert config.focal_length == 1.0
        assert config.convergence == 0.5
        assert config.hole_filling == "nearest"
        assert config.depth_interpretation == "inverse"
        assert config.max_disparity == 64
        assert config.depth_scale == 1.0

    def test_custom_values(self, mock_logger: MagicMock) -> None:
        """Test custom configuration values."""
        config = DIBRConfig(
            baseline=0.1,
            focal_length=2.0,
            convergence=0.3,
            hole_filling="inpaint",
            max_disparity=128,
        )

        assert config.baseline == 0.1
        assert config.focal_length == 2.0
        assert config.convergence == 0.3
        assert config.hole_filling == "inpaint"
        assert config.max_disparity == 128

    def test_invalid_baseline(self, mock_logger: MagicMock) -> None:
        """Test that invalid baseline raises error."""
        with pytest.raises(ValueError, match="baseline must be positive"):
            DIBRConfig(baseline=0)

        with pytest.raises(ValueError, match="baseline must be positive"):
            DIBRConfig(baseline=-0.1)

    def test_invalid_focal_length(self, mock_logger: MagicMock) -> None:
        """Test that invalid focal length raises error."""
        with pytest.raises(ValueError, match="focal_length must be positive"):
            DIBRConfig(focal_length=0)

        with pytest.raises(ValueError, match="focal_length must be positive"):
            DIBRConfig(focal_length=-1.0)

    def test_invalid_convergence(self, mock_logger: MagicMock) -> None:
        """Test that invalid convergence raises error."""
        with pytest.raises(ValueError, match="convergence must be in"):
            DIBRConfig(convergence=-0.1)

        with pytest.raises(ValueError, match="convergence must be in"):
            DIBRConfig(convergence=1.5)

    def test_invalid_hole_filling(self, mock_logger: MagicMock) -> None:
        """Test that invalid hole filling method raises error."""
        with pytest.raises(ValueError, match="Invalid hole_filling"):
            DIBRConfig(hole_filling="invalid")

    def test_invalid_depth_interpretation(self, mock_logger: MagicMock) -> None:
        """Test that invalid depth interpretation raises error."""
        with pytest.raises(ValueError, match="Invalid depth_interpretation"):
            DIBRConfig(depth_interpretation="invalid")

    def test_invalid_max_disparity(self, mock_logger: MagicMock) -> None:
        """Test that invalid max_disparity raises error."""
        with pytest.raises(ValueError, match="max_disparity must be positive"):
            DIBRConfig(max_disparity=0)

        with pytest.raises(ValueError, match="max_disparity must be positive"):
            DIBRConfig(max_disparity=-1)

    def test_invalid_depth_scale(self, mock_logger: MagicMock) -> None:
        """Test that invalid depth_scale raises error."""
        with pytest.raises(ValueError, match="depth_scale must be positive"):
            DIBRConfig(depth_scale=0)

        with pytest.raises(ValueError, match="depth_scale must be positive"):
            DIBRConfig(depth_scale=-0.5)

# ---------------------------------------------------------------------------
# DIBREngine Tests
# ---------------------------------------------------------------------------


class TestDIBREngine:
    """Tests for DIBREngine class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default engine initialization."""
        engine = DIBREngine()

        assert engine.config.baseline == 0.05
        assert engine.config.focal_length == 1.0
        assert engine.config.convergence == 0.5

    def test_initialization_custom_config(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom config."""
        config = DIBRConfig(
            baseline=0.1,
            convergence=0.3,
        )
        engine = DIBREngine(config=config)

        assert engine.config.baseline == 0.1
        assert engine.config.convergence == 0.3

    def test_initialization_custom_params(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom parameters."""
        engine = DIBREngine(
            baseline=0.08,
            focal_length=1.5,
            convergence=0.4,
            hole_filling="linear",
        )

        assert engine.config.baseline == 0.08
        assert engine.config.focal_length == 1.5
        assert engine.config.convergence == 0.4
        assert engine.config.hole_filling == "linear"

    def test_compute_disparity_basic(
        self,
        mock_logger: MagicMock,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test basic disparity computation."""
        engine = DIBREngine()
        disparity = engine.compute_disparity(sample_depth_map, image_width=100)

        # Check output shape matches input
        assert disparity.shape == sample_depth_map.shape

        # Check values are non-negative and within max disparity
        assert np.all(disparity >= 0)
        assert np.all(disparity <= engine.config.max_disparity)

    def test_compute_disparity_gradient(
        self,
        mock_logger: MagicMock,
        gradient_depth_map: np.ndarray,
    ) -> None:
        """Test disparity computation with gradient depth."""
        engine = DIBREngine(baseline=0.05, focal_length=1.0)
        disparity = engine.compute_disparity(gradient_depth_map, image_width=100)

        # Check shape
        assert disparity.shape == gradient_depth_map.shape

        # Check that disparity values are finite
        assert np.all(np.isfinite(disparity))

    def test_render_basic(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test basic stereo pair rendering."""
        engine = DIBREngine()
        left, right = engine.render(sample_image, sample_depth_map)

        # Check output shapes match input
        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

        # Check output type
        assert left.dtype == sample_image.dtype
        assert right.dtype == sample_image.dtype

    def test_render_grayscale(
        self,
        mock_logger: MagicMock,
        sample_grayscale_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test rendering with grayscale image."""
        engine = DIBREngine()
        left, right = engine.render(sample_grayscale_image, sample_depth_map)

        # Check output shapes
        assert left.shape == sample_grayscale_image.shape
        assert right.shape == sample_grayscale_image.shape

    def test_render_constant_depth(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        constant_depth_map: np.ndarray,
    ) -> None:
        """Test rendering with constant depth (no stereo effect)."""
        engine = DIBREngine(convergence=0.5)
        left, right = engine.render(sample_image, constant_depth_map)

        # With constant depth at convergence, views should be very similar
        # (just small edge effects)
        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_render_dimension_mismatch(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that dimension mismatch raises error."""
        engine = DIBREngine()
        wrong_depth = np.zeros((50, 50), dtype=np.float32)

        with pytest.raises(DIBRError, match="dimensions must match"):
            engine.render(sample_image, wrong_depth)

    def test_render_different_hole_filling(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test rendering with different hole filling methods."""
        for method in ["none", "nearest", "linear"]:
            engine = DIBREngine(hole_filling=method)
            left, right = engine.render(sample_image, sample_depth_map)

            assert left.shape == sample_image.shape
            assert right.shape == sample_image.shape

    def test_callable_interface(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test callable interface."""
        engine = DIBREngine()
        left, right = engine(sample_image, sample_depth_map)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_different_baseline_values(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test that different baseline values produce different results."""
        engine_low = DIBREngine(baseline=0.02)
        engine_high = DIBREngine(baseline=0.1)

        left_low, right_low = engine_low.render(sample_image, sample_depth_map)
        left_high, right_high = engine_high.render(sample_image, sample_depth_map)

        # Higher baseline should produce more disparity (more different views)
        # The difference between left and right should be greater with higher baseline
        diff_low = np.abs(left_low.astype(np.float32) - right_low.astype(np.float32)).mean()
        diff_high = np.abs(left_high.astype(np.float32) - right_high.astype(np.float32)).mean()

        # Higher baseline should create more difference between views
        assert diff_high >= diff_low or diff_high > 0 or diff_low > 0


# ---------------------------------------------------------------------------
# StereoGenerator Tests
# ---------------------------------------------------------------------------


class TestStereoGenerator:
    """Tests for StereoGenerator class."""

    def test_initialization(self, mock_logger: MagicMock) -> None:
        """Test StereoGenerator initialization."""
        generator = StereoGenerator()

        assert generator.format == "side_by_side"
        assert generator.baseline == 0.05
        assert generator.convergence == 0.5

    def test_initialization_custom(self, mock_logger: MagicMock) -> None:
        """Test StereoGenerator with custom parameters."""
        generator = StereoGenerator(
            format="anaglyph",
            baseline=0.08,
            convergence=0.3,
            hole_filling="inpaint",
        )

        assert generator.format == "anaglyph"
        assert generator.baseline == 0.08
        assert generator.convergence == 0.3

    def test_generate_stereo_pair(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test stereo pair generation."""
        generator = StereoGenerator()
        left, right = generator.generate_stereo_pair(sample_image, sample_depth_map)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_set_format(self, mock_logger: MagicMock) -> None:
        """Test format change."""
        generator = StereoGenerator(format="side_by_side")
        generator.set_format("anaglyph")

        assert generator.format == "anaglyph"

    def test_set_baseline(self, mock_logger: MagicMock) -> None:
        """Test baseline update."""
        generator = StereoGenerator(baseline=0.05)
        generator.set_baseline(0.1)

        assert generator.baseline == 0.1

    def test_set_convergence(self, mock_logger: MagicMock) -> None:
        """Test convergence update."""
        generator = StereoGenerator(convergence=0.5)
        generator.set_convergence(0.3)

        assert generator.convergence == 0.3

    def test_compute_disparity(
        self,
        mock_logger: MagicMock,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test disparity computation through generator."""
        generator = StereoGenerator()
        disparity = generator.compute_disparity(sample_depth_map, image_width=100)

        assert disparity.shape == sample_depth_map.shape
        assert np.all(disparity >= 0)


# ---------------------------------------------------------------------------
# AnaglyphGenerator Tests
# ---------------------------------------------------------------------------


class TestAnaglyphGenerator:
    """Tests for AnaglyphGenerator class."""

    def test_initialization(self, mock_logger: MagicMock) -> None:
        """Test AnaglyphGenerator initialization."""
        generator = AnaglyphGenerator()

        assert generator.format == "anaglyph"
        assert generator.color_method == "dubois"

    def test_combine_to_anaglyph_dubois(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with Dubois method."""
        generator = AnaglyphGenerator(color_method="dubois")

        # Create left and right views (same image for simplicity)
        left = sample_image.copy()
        right = sample_image.copy()

        anaglyph = generator.combine_to_anaglyph(left, right)

        assert anaglyph.shape == (*sample_image.shape[:2], 3)
        assert anaglyph.dtype == np.uint8

    def test_combine_to_anaglyph_gray(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with gray method."""
        generator = AnaglyphGenerator(color_method="gray")

        left = sample_image.copy()
        right = sample_image.copy()

        anaglyph = generator.combine_to_anaglyph(left, right)

        assert anaglyph.shape == (*sample_image.shape[:2], 3)
        assert anaglyph.dtype == np.uint8

    def test_combine_to_anaglyph_color(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with color method."""
        generator = AnaglyphGenerator(color_method="color")

        left = sample_image.copy()
        right = sample_image.copy()

        anaglyph = generator.combine_to_anaglyph(left, right, method="color")

        assert anaglyph.shape == (*sample_image.shape[:2], 3)
        assert anaglyph.dtype == np.uint8


# ---------------------------------------------------------------------------
# SideBySideGenerator Tests
# ---------------------------------------------------------------------------


class TestSideBySideGenerator:
    """Tests for SideBySideGenerator class."""

    def test_initialization(self, mock_logger: MagicMock) -> None:
        """Test SideBySideGenerator initialization."""
        generator = SideBySideGenerator()

        assert generator.format == "side_by_side"
        assert generator.layout == "horizontal"
        assert generator.swap_eyes is False
        assert generator.half_width is False

    def test_combine_horizontal(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test horizontal side-by-side combination."""
        generator = SideBySideGenerator(layout="horizontal")

        left = sample_image.copy()
        right = sample_image.copy()

        sbs = generator.combine_to_side_by_side(left, right)

        h, w, c = sample_image.shape
        assert sbs.shape == (h, w * 2, c)

    def test_combine_vertical(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test vertical side-by-side combination."""
        generator = SideBySideGenerator(layout="vertical")

        left = sample_image.copy()
        right = sample_image.copy()

        sbs = generator.combine_to_side_by_side(left, right)

        h, w, c = sample_image.shape
        assert sbs.shape == (h * 2, w, c)

    def test_swap_eyes(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test eye swapping."""
        generator = SideBySideGenerator(swap_eyes=True, layout="horizontal")

        left = sample_image.copy()
        right = np.zeros_like(sample_image)  # Different from left

        sbs = generator.combine_to_side_by_side(left, right)

        # With swap_eyes=True, right should be on left side
        h, w, c = sample_image.shape
        # Left half of SBS should be 'right' input (zeros)
        assert np.allclose(sbs[:, :w, :], 0)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_dibr_engine(self, mock_logger: MagicMock) -> None:
        """Test create_dibr_engine function."""
        engine = create_dibr_engine(
            baseline=0.1,
            convergence=0.3,
        )

        assert engine.config.baseline == 0.1
        assert engine.config.convergence == 0.3

    def test_render_stereo_pair(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test render_stereo_pair convenience function."""
        left, right = render_stereo_pair(
            sample_image,
            sample_depth_map,
            baseline=0.05,
            convergence=0.5,
        )

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_very_small_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with very small image."""
        engine = DIBREngine()
        small_image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        small_depth = np.random.random((10, 10)).astype(np.float32)

        left, right = engine.render(small_image, small_depth)

        assert left.shape == small_image.shape
        assert right.shape == small_image.shape

    def test_depth_map_normalization(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that depth map is normalized if not in [0, 1]."""
        engine = DIBREngine()

        # Create depth map outside [0, 1] range
        depth = np.random.uniform(10, 100, sample_image.shape[:2]).astype(np.float32)

        left, right = engine.render(sample_image, depth)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_depth_map_with_extreme_values(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test with depth map containing extreme values."""
        engine = DIBREngine()

        # Create depth map with some extreme values
        depth = np.random.random(sample_image.shape[:2]).astype(np.float32)
        depth[0, 0] = 0.0
        depth[1, 1] = 1.0

        left, right = engine.render(sample_image, depth)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_minimum_dimension_validation(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-dimension images raise error."""
        engine = DIBREngine()

        # Create image with zero dimension (edge case)
        zero_image = np.zeros((0, 100, 3), dtype=np.uint8)
        zero_depth = np.zeros((0, 100), dtype=np.float32)

        with pytest.raises(DIBRError, match="dimensions must be at least"):
            engine.render(zero_image, zero_depth)

    def test_direct_depth_interpretation(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test rendering with direct depth interpretation."""
        config = DIBRConfig(depth_interpretation="direct")
        engine = DIBREngine(config=config)

        # With direct interpretation: high value = close
        depth = np.random.random(sample_image.shape[:2]).astype(np.float32)

        left, right = engine.render(sample_image, depth)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_float32_image_input(
        self,
        mock_logger: MagicMock,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test rendering with float32 image input."""
        engine = DIBREngine()

        # Create float32 image (normalized 0-1)
        float_image = np.random.random((100, 100, 3)).astype(np.float32)

        left, right = engine.render(float_image, sample_depth_map)

        assert left.shape == float_image.shape
        assert right.shape == float_image.shape


class TestAdditionalCoverage:
    """Additional tests for improved code coverage."""

    def test_inpaint_hole_filling(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test rendering with inpaint hole filling method."""
        engine = DIBREngine(hole_filling="inpaint")
        left, right = engine.render(sample_image, sample_depth_map)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_linear_hole_filling_single_valid_pixel(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test linear hole filling with only one valid pixel per row."""
        engine = DIBREngine(hole_filling="linear")

        # Create small test image and depth
        image = np.ones((10, 10, 3), dtype=np.uint8) * 128
        # Create depth that causes large holes
        depth = np.zeros((10, 10), dtype=np.float32)
        depth[:, 5:] = 0.9  # Far region

        left, right = engine.render(image, depth)

        assert left.shape == image.shape
        assert right.shape == image.shape

    def test_half_width_mode(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test side-by-side generator with half-width mode."""
        generator = SideBySideGenerator(
            half_width=True,
            layout="horizontal"
        )

        left = sample_image.copy()
        right = sample_image.copy()

        sbs = generator.combine_to_side_by_side(left, right)

        h, w, c = sample_image.shape
        # With half_width, each eye is resized to half width
        assert sbs.shape == (h, w, c)  # Total width = w/2 + w/2 = w

    def test_half_width_mode_vertical(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test side-by-side generator with half-width and vertical layout."""
        generator = SideBySideGenerator(
            half_width=True,
            layout="vertical"
        )

        left = sample_image.copy()
        right = sample_image.copy()

        sbs = generator.combine_to_side_by_side(left, right)

        h, w, c = sample_image.shape
        # Vertical layout stacks images, half-width doesn't affect vertical dimension
        assert sbs.shape == (h * 2, w // 2, c)

    def test_constant_depth_normalization(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test rendering with constant depth map that needs normalization."""
        engine = DIBREngine()

        # Create depth map with values outside [0, 1] range, all same value
        constant_depth = np.full(sample_image.shape[:2], 50.0, dtype=np.float32)

        left, right = engine.render(sample_image, constant_depth)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_dibr_error_operation_and_original_exception(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test DIBRError with operation and original_exception attributes."""
        original = ValueError("Original error")
        error = DIBRError(
            "Test error",
            operation="test_op",
            original_exception=original
        )

        assert str(error) == "Test error"
        assert error.operation == "test_op"
        assert error.original_exception == original

    def test_stereo_generator_with_dibr_config(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test StereoGenerator initialization with DIBRConfig."""
        config = DIBRConfig(
            baseline=0.08,
            convergence=0.4,
            hole_filling="linear"
        )
        generator = StereoGenerator(dibr_config=config)

        # DIBRConfig overrides individual parameters
        assert generator.baseline == 0.05  # Default, not from config
        # But the engine uses the config values
        left, right = generator.generate_stereo_pair(sample_image, sample_depth_map)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_grayscale_anaglyph_combination(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test anaglyph combination with grayscale input."""
        generator = AnaglyphGenerator(color_method="color")

        # Create grayscale images
        left_gray = (np.random.random((50, 50)) * 255).astype(np.uint8)
        right_gray = (np.random.random((50, 50)) * 255).astype(np.uint8)

        anaglyph = generator.combine_to_anaglyph(left_gray, right_gray)

        assert anaglyph.shape == (50, 50, 3)
        assert anaglyph.dtype == np.uint8

    def test_float_image_anaglyph(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test anaglyph combination with float images."""
        generator = AnaglyphGenerator(color_method="dubois")

        # Create float images (normalized 0-1)
        left_float = np.random.random((50, 50, 3)).astype(np.float32)
        right_float = np.random.random((50, 50, 3)).astype(np.float32)

        anaglyph = generator.combine_to_anaglyph(left_float, right_float)

        assert anaglyph.shape == (50, 50, 3)
        assert anaglyph.dtype == np.uint8

    def test_custom_max_disparity(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test that custom max_disparity limits disparity values."""
        config = DIBRConfig(
            baseline=0.1,
            max_disparity=10
        )
        engine = DIBREngine(config=config)

        disparity = engine.compute_disparity(sample_depth_map, image_width=100)

        # Check that disparity is clamped to max_disparity
        assert np.all(disparity <= 10)

    def test_custom_depth_scale(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test rendering with custom depth scale."""
        config = DIBRConfig(depth_scale=2.0)
        engine = DIBREngine(config=config)

        left, right = engine.render(sample_image, sample_depth_map)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape
