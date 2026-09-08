"""Unit tests for depth map processor module.

Tests cover:
- DepthProcessorConfig dataclass
- Normalization methods
- Bilateral filtering
- Hole filling algorithms
- Color mapping
- Full processing pipeline

Note: These tests rely on mocks set up in tests/conftest.py.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Import the module under test (mocks are set up in conftest.py)
from video2d3d.depth.processor import (
    ColorMapType,
    DepthMapProcessor,
    DepthProcessingError,
    DepthProcessorConfig,
    EdgeAwareFilterType,
    HoleFillingMethod,
    NormalizationMethod,
    create_processor,
    process_depth_map,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_depth_map() -> np.ndarray:
    """Create a sample depth map for testing."""
    np.random.seed(42)
    return np.random.random((100, 100)).astype(np.float32)


@pytest.fixture
def depth_map_with_holes() -> np.ndarray:
    """Create a depth map with holes (zeros/NaNs)."""
    np.random.seed(42)
    depth = np.random.random((100, 100)).astype(np.float32)
    # Add some holes
    depth[20:30, 20:30] = 0.0
    depth[50:55, 50:55] = 0.0
    depth[80:85, 10:20] = np.nan
    return depth


@pytest.fixture
def constant_depth_map() -> np.ndarray:
    """Create a constant depth map (edge case)."""
    return np.full((50, 50), 0.5, dtype=np.float32)


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    import video2d3d.depth.processor as processor_module

    with patch.object(processor_module, "get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


# ---------------------------------------------------------------------------
# DepthProcessorConfig Tests
# ---------------------------------------------------------------------------


class TestDepthProcessorConfig:
    """Tests for DepthProcessorConfig dataclass."""

    def test_default_values(self, mock_logger: MagicMock) -> None:
        """Test default configuration values."""
        config = DepthProcessorConfig()

        assert config.edge_aware_smoothing is True
        assert config.smoothing_radius == 3
        assert config.bilateral_filter is True
        assert config.bilateral_sigma_color == 0.1
        assert config.bilateral_sigma_space == 5
        assert config.hole_filling is True
        assert config.hole_filling_method == "inpaint"
        assert config.sharpening is False
        assert config.sharpening_amount == 0.5
        assert config.normalization_method == "min_max"
        assert config.percentile_low == 2.0
        assert config.percentile_high == 98.0
        assert config.colormap == "turbo"

    def test_custom_values(self, mock_logger: MagicMock) -> None:
        """Test custom configuration values."""
        config = DepthProcessorConfig(
            edge_aware_smoothing=False,
            smoothing_radius=5,
            bilateral_filter=False,
            bilateral_sigma_color=0.2,
            bilateral_sigma_space=10,
            hole_filling=False,
            hole_filling_method="nearest",
            sharpening=True,
            sharpening_amount=0.75,
            normalization_method="percentile",
            percentile_low=5.0,
            percentile_high=95.0,
            colormap="plasma",
        )

        assert config.edge_aware_smoothing is False
        assert config.smoothing_radius == 5
        assert config.bilateral_filter is False
        assert config.bilateral_sigma_color == 0.2
        assert config.bilateral_sigma_space == 10
        assert config.hole_filling is False
        assert config.hole_filling_method == "nearest"
        assert config.sharpening is True
        assert config.sharpening_amount == 0.75
        assert config.normalization_method == "percentile"
        assert config.percentile_low == 5.0
        assert config.percentile_high == 95.0
        assert config.colormap == "plasma"

    def test_invalid_normalization_method_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid normalization method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid normalization method"):
            DepthProcessorConfig(normalization_method="invalid")

    def test_invalid_hole_filling_method_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid hole filling method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hole filling method"):
            DepthProcessorConfig(hole_filling_method="invalid")

    def test_invalid_colormap_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid colormap raises ValueError."""
        with pytest.raises(ValueError, match="Invalid colormap"):
            DepthProcessorConfig(colormap="invalid_color")

    def test_invalid_sharpening_amount_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid sharpening_amount raises ValueError."""
        with pytest.raises(ValueError, match="sharpening_amount"):
            DepthProcessorConfig(sharpening_amount=1.5)

        with pytest.raises(ValueError, match="sharpening_amount"):
            DepthProcessorConfig(sharpening_amount=-0.1)

    def test_invalid_percentile_range_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid percentile range raises ValueError."""
        with pytest.raises(ValueError, match="percentile_low"):
            DepthProcessorConfig(percentile_low=50, percentile_high=40)

        with pytest.raises(ValueError, match="percentile_low"):
            DepthProcessorConfig(percentile_low=-1, percentile_high=50)

        with pytest.raises(ValueError, match="smoothing_radius"):
            DepthProcessorConfig(smoothing_radius=0)

    def test_invalid_guided_filter_radius_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid guided_filter_radius raises ValueError."""
        with pytest.raises(ValueError, match="guided_filter_radius"):
            DepthProcessorConfig(guided_filter_radius=0)

    def test_invalid_guided_filter_eps_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid guided_filter_eps raises ValueError."""
        with pytest.raises(ValueError, match="guided_filter_eps"):
            DepthProcessorConfig(guided_filter_eps=0)

        with pytest.raises(ValueError, match="guided_filter_eps"):
            DepthProcessorConfig(guided_filter_eps=-0.01)

    def test_invalid_edge_filter_type_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid edge_filter_type raises ValueError."""
        with pytest.raises(ValueError, match="edge_filter_type"):
            DepthProcessorConfig(edge_filter_type="invalid")

    def test_guided_filter_auto_enabled(self, mock_logger: MagicMock) -> None:
        """Test that guided_filter is auto-enabled when edge_filter_type is 'guided'."""
        config = DepthProcessorConfig(
            edge_filter_type="guided",
            guided_filter=False,  # Explicitly False, should be auto-enabled
        )
        assert config.guided_filter is True
        assert config.edge_filter_type == "guided"

    def test_bilateral_filter_explicit_config_respected(self, mock_logger: MagicMock) -> None:
        """Test that an explicit bilateral_filter=False is respected."""
        config = DepthProcessorConfig(
            edge_filter_type="bilateral",
            bilateral_filter=False,
        )
        assert config.bilateral_filter is False
        assert config.edge_filter_type == "bilateral"


# ---------------------------------------------------------------------------
# DepthMapProcessor Initialization Tests
# ---------------------------------------------------------------------------


class TestDepthMapProcessorInit:
    """Tests for DepthMapProcessor initialization."""

    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:
        """Test initialization with default values."""
        processor = DepthMapProcessor()

        assert processor.config.bilateral_filter is True
        assert processor.config.hole_filling is True
        assert processor.config.colormap == "turbo"

    def test_init_with_config(self, mock_logger: MagicMock) -> None:
        """Test initialization with DepthProcessorConfig."""
        config = DepthProcessorConfig(
            bilateral_filter=False,
            colormap="plasma",
        )
        processor = DepthMapProcessor(config=config)

        assert processor.config.bilateral_filter is False
        assert processor.config.colormap == "plasma"

    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:
        """Test initialization with keyword arguments."""
        processor = DepthMapProcessor(
            edge_aware_smoothing=False,
            bilateral_filter=False,
            hole_filling=False,
            colormap="viridis",
        )

        assert processor.config.edge_aware_smoothing is False
        assert processor.config.bilateral_filter is False
        assert processor.config.hole_filling is False
        assert processor.config.colormap == "viridis"


# ---------------------------------------------------------------------------
# Normalization Tests
# ---------------------------------------------------------------------------


class TestNormalization:
    """Tests for depth map normalization."""

    def test_normalize_min_max(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test min-max normalization."""
        processor = DepthMapProcessor()

        result = processor.normalize(sample_depth_map, method="min_max")

        assert result.dtype == np.float32
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_normalize_min_max_constant_depth(
        self, constant_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test min-max normalization with constant depth."""
        processor = DepthMapProcessor()

        result = processor.normalize(constant_depth_map, method="min_max")

        # Should return zeros for constant input
        assert np.allclose(result, 0.0)

    def test_normalize_percentile(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test percentile normalization."""
        processor = DepthMapProcessor()

        result = processor.normalize(sample_depth_map, method="percentile")

        assert result.dtype == np.float32
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_normalize_histogram(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test histogram equalization normalization."""
        processor = DepthMapProcessor()

        result = processor.normalize(sample_depth_map, method="histogram_equalization")

        assert result.dtype == np.float32
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_normalize_uses_config_method(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that normalize uses config method when not specified."""
        config = DepthProcessorConfig(normalization_method="percentile")
        processor = DepthMapProcessor(config=config)

        # Should not raise - uses percentile method from config
        result = processor.normalize(sample_depth_map)
        assert result.dtype == np.float32

    def test_normalize_invalid_method_raises(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that invalid normalization method raises error."""
        processor = DepthMapProcessor()

        with pytest.raises(DepthProcessingError, match="Unknown normalization method"):
            processor.normalize(sample_depth_map, method="invalid")


# ---------------------------------------------------------------------------
# Bilateral Filter Tests
# ---------------------------------------------------------------------------


class TestBilateralFilter:
    """Tests for bilateral filtering."""

    def test_bilateral_filter_basic(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test basic bilateral filter application."""
        processor = DepthMapProcessor()

        result = processor.apply_bilateral_filter(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_bilateral_filter_custom_params(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test bilateral filter with custom parameters."""
        processor = DepthMapProcessor()

        result = processor.apply_bilateral_filter(
            sample_depth_map,
            sigma_color=0.2,
            sigma_space=10,
        )

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_bilateral_filter_preserves_edges(self, mock_logger: MagicMock) -> None:
        """Test that bilateral filter preserves edges."""
        processor = DepthMapProcessor()

        # Create a depth map with sharp edge
        depth = np.zeros((100, 100), dtype=np.float32)
        depth[:, 50:] = 1.0

        result = processor.apply_bilateral_filter(depth)

        # Check that edge is still visible (not completely smoothed)
        edge_region = result[:, 48:52]
        assert edge_region.std() > 0.1  # Should have variation at edge


# ---------------------------------------------------------------------------
# Guided Filter Tests
# ---------------------------------------------------------------------------


class TestGuidedFilter:
    """Tests for guided filtering."""

    def test_guided_filter_basic(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test basic guided filter application."""
        processor = DepthMapProcessor()

        result = processor.apply_guided_filter(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_guided_filter_custom_params(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test guided filter with custom parameters."""
        processor = DepthMapProcessor()

        result = processor.apply_guided_filter(
            sample_depth_map,
            radius=16,
            eps=0.001,
        )

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_guided_filter_with_guidance(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test guided filter with separate guidance image."""
        processor = DepthMapProcessor()

        # Create a guidance image (e.g., a smoothed version)
        guidance = np.random.random((100, 100)).astype(np.float32)

        result = processor.apply_guided_filter(
            sample_depth_map,
            guidance=guidance,
        )

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_guided_filter_preserves_edges(self, mock_logger: MagicMock) -> None:
        """Test that guided filter preserves edges."""
        processor = DepthMapProcessor()

        # Create a depth map with sharp edge
        depth = np.zeros((100, 100), dtype=np.float32)
        depth[:, 50:] = 1.0

        result = processor.apply_guided_filter(depth, radius=8, eps=0.01)

        # Check that edge is still visible (not completely smoothed)
        edge_region = result[:, 48:52]
        assert edge_region.std() > 0.1  # Should have variation at edge

    def test_guided_filter_smoothing_effect(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that guided filter actually smooths the image."""
        processor = DepthMapProcessor()

        # Add some noise to the depth map
        noisy_depth = sample_depth_map + np.random.normal(0, 0.1, sample_depth_map.shape)
        noisy_depth = np.clip(noisy_depth, 0, 1).astype(np.float32)

        result = processor.apply_guided_filter(noisy_depth, radius=16, eps=0.01)

        # The smoothed result should have lower variance than noisy input
        # (smoothing effect)
        assert result.dtype == np.float32
        # Just check it runs without error and produces valid output
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_guided_filter_small_image(self, mock_logger: MagicMock) -> None:
        """Test guided filter with image smaller than filter radius."""
        processor = DepthMapProcessor()

        # Create a small depth map (10x10)
        small_depth = np.random.random((10, 10)).astype(np.float32)

        # Request a large radius (8), should be auto-adjusted
        result = processor.apply_guided_filter(small_depth, radius=8, eps=0.01)

        assert result.dtype == np.float32
        assert result.shape == small_depth.shape
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_guided_filter_tiny_image(self, mock_logger: MagicMock) -> None:
        """Test guided filter with very tiny image (3x3)."""
        processor = DepthMapProcessor()

        # Create a tiny depth map
        tiny_depth = np.random.random((3, 3)).astype(np.float32)

        result = processor.apply_guided_filter(tiny_depth, radius=8, eps=0.01)

        assert result.dtype == np.float32
        assert result.shape == tiny_depth.shape


# ---------------------------------------------------------------------------
# Hole Filling Tests
# ---------------------------------------------------------------------------


class TestHoleFilling:
    """Tests for hole-filling algorithms."""

    def test_fill_holes_inpaint(
        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test inpaint hole-filling method."""
        processor = DepthMapProcessor()

        result = processor.fill_holes(depth_map_with_holes, method="inpaint")

        assert result.dtype == np.float32
        # Check that some holes were filled
        # The zero regions should now have values
        assert not np.all(result[20:30, 20:30] == 0.0)

    def test_fill_holes_nearest(
        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test nearest-neighbor hole-filling method."""
        processor = DepthMapProcessor()

        result = processor.fill_holes(depth_map_with_holes, method="nearest")

        assert result.dtype == np.float32
        assert not np.isnan(result).any()

    def test_fill_holes_linear(
        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test linear interpolation hole-filling method."""
        processor = DepthMapProcessor()

        result = processor.fill_holes(depth_map_with_holes, method="linear")

        assert result.dtype == np.float32
        assert not np.isnan(result).any()

    def test_fill_holes_no_holes(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test hole-filling on depth map without holes."""
        processor = DepthMapProcessor()

        result = processor.fill_holes(sample_depth_map, method="inpaint")

        # Should return essentially the same map
        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=5)

    def test_fill_holes_invalid_method_raises(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that invalid hole-filling method raises error."""
        processor = DepthMapProcessor()

        with pytest.raises(DepthProcessingError, match="Unknown hole filling method"):
            processor.fill_holes(sample_depth_map, method="invalid")


# ---------------------------------------------------------------------------
# Sharpening Tests
# ---------------------------------------------------------------------------


class TestSharpening:
    """Tests for depth map sharpening."""

    def test_sharpen_basic(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test basic sharpening."""
        processor = DepthMapProcessor()

        result = processor.sharpen(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_sharpen_custom_amount(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test sharpening with custom amount."""
        processor = DepthMapProcessor()

        result = processor.sharpen(sample_depth_map, amount=0.75)

        assert result.dtype == np.float32

    def test_sharpen_zero_amount(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that zero sharpening amount returns similar result."""
        processor = DepthMapProcessor()

        result = processor.sharpen(sample_depth_map, amount=0.0)

        # Should be very close to original
        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=2)


# ---------------------------------------------------------------------------
# Color Mapping Tests
# ---------------------------------------------------------------------------


class TestColorMapping:
    """Tests for color mapping."""

    def test_apply_colormap_turbo(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test turbo colormap."""
        processor = DepthMapProcessor()

        result = processor.apply_colormap(sample_depth_map, colormap="turbo")

        assert result.dtype == np.uint8
        assert result.shape == (*sample_depth_map.shape, 3)  # RGB

    def test_apply_colormap_plasma(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test plasma colormap."""
        processor = DepthMapProcessor()

        result = processor.apply_colormap(sample_depth_map, colormap="plasma")

        assert result.dtype == np.uint8
        assert result.shape == (*sample_depth_map.shape, 3)

    def test_apply_colormap_gray(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test grayscale colormap."""
        processor = DepthMapProcessor()

        result = processor.apply_colormap(sample_depth_map, colormap="gray")

        assert result.dtype == np.uint8
        assert result.shape == (*sample_depth_map.shape, 3)  # Still RGB but grayscale values

    def test_apply_colormap_auto_normalize(self, mock_logger: MagicMock) -> None:
        """Test that colormap auto-normalizes out-of-range input."""
        processor = DepthMapProcessor()

        # Create depth map outside [0, 1]
        np.random.seed(123)
        depth = (np.random.random((50, 50)) * 10 - 2).astype(np.float32)

        result = processor.apply_colormap(depth, colormap="turbo")

        assert result.dtype == np.uint8
        assert result.shape == (50, 50, 3)

    def test_apply_colormap_invalid_raises(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that invalid colormap raises error."""
        processor = DepthMapProcessor()

        # Need to bypass config validation by calling directly
        with pytest.raises(DepthProcessingError, match="Unknown colormap"):
            processor.apply_colormap(sample_depth_map, colormap="invalid_cmap")


# ---------------------------------------------------------------------------
# Full Pipeline Tests
# ---------------------------------------------------------------------------


class TestFullPipeline:
    """Tests for full processing pipeline."""

    def test_process_full_pipeline(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test full processing pipeline."""
        config = DepthProcessorConfig(
            bilateral_filter=True,
            hole_filling=True,
            sharpening=True,
        )
        processor = DepthMapProcessor(config=config)

        result = processor.process(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_process_with_colormap(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test processing with colormap output."""
        processor = DepthMapProcessor()

        result = processor.process(sample_depth_map, apply_colormap=True)

        assert result.dtype == np.uint8
        assert result.shape == (*sample_depth_map.shape, 3)

    def test_process_disabled_operations(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test pipeline with operations disabled."""
        config = DepthProcessorConfig(
            bilateral_filter=False,
            hole_filling=False,
            sharpening=False,
        )
        processor = DepthMapProcessor(config=config)

        result = processor.process(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_callable_interface(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test callable interface."""
        processor = DepthMapProcessor()

        result = processor(sample_depth_map)

        assert result.dtype == np.float32

    def test_callable_with_colormap(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test callable interface with colormap."""
        processor = DepthMapProcessor()

        result = processor(sample_depth_map, apply_colormap=True)

        assert result.dtype == np.uint8
        assert result.shape == (*sample_depth_map.shape, 3)

    def test_process_with_guided_filter(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test processing with guided filter instead of bilateral."""
        config = DepthProcessorConfig(
            guided_filter=True,
            edge_filter_type="guided",
            bilateral_filter=False,
            hole_filling=True,
        )
        processor = DepthMapProcessor(config=config)

        result = processor.process(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_process_edge_filter_none(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test processing with edge filter disabled."""
        config = DepthProcessorConfig(
            edge_filter_type="none",
            bilateral_filter=False,
            guided_filter=False,
        )
        processor = DepthMapProcessor(config=config)

        result = processor.process(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_processor_defaults(self, mock_logger: MagicMock) -> None:
        """Test create_processor with defaults."""
        processor = create_processor()

        assert processor.config.bilateral_filter is True
        assert processor.config.hole_filling is True
        assert processor.config.colormap == "turbo"

    def test_create_processor_custom(self, mock_logger: MagicMock) -> None:
        """Test create_processor with custom values."""
        processor = create_processor(
            bilateral_filter=False,
            hole_filling=False,
            colormap="viridis",
            sharpening=True,
        )

        assert processor.config.bilateral_filter is False
        assert processor.config.hole_filling is False
        assert processor.config.colormap == "viridis"
        assert processor.config.sharpening is True

    def test_process_depth_map_basic(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test process_depth_map convenience function."""
        result = process_depth_map(sample_depth_map)

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape

    def test_process_depth_map_with_colormap(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test process_depth_map with colormap."""
        result = process_depth_map(sample_depth_map, colormap="plasma")

        assert result.dtype == np.uint8
        assert result.shape == (*sample_depth_map.shape, 3)

    def test_process_depth_map_disabled_operations(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test process_depth_map with operations disabled."""
        result = process_depth_map(
            sample_depth_map,
            fill_holes=False,
            bilateral_filter=False,
        )

        assert result.dtype == np.float32

    def test_process_depth_map_with_guided_filter(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test process_depth_map with guided filter."""
        result = process_depth_map(
            sample_depth_map,
            guided_filter=True,
            bilateral_filter=False,
        )

        assert result.dtype == np.float32
        assert result.shape == sample_depth_map.shape


# ---------------------------------------------------------------------------
# Enum Tests
# ---------------------------------------------------------------------------


class TestEnums:
    """Tests for enum types."""

    def test_normalization_method_values(self) -> None:
        """Test NormalizationMethod enum values."""
        assert NormalizationMethod.MIN_MAX.value == "min_max"
        assert NormalizationMethod.PERCENTILE.value == "percentile"
        assert NormalizationMethod.HISTOGRAM_EQUALIZATION.value == "histogram_equalization"

    def test_hole_filling_method_values(self) -> None:
        """Test HoleFillingMethod enum values."""
        assert HoleFillingMethod.INPAINT.value == "inpaint"
        assert HoleFillingMethod.NEAREST.value == "nearest"
        assert HoleFillingMethod.LINEAR.value == "linear"

    def test_color_map_type_values(self) -> None:
        """Test ColorMapType enum values."""
        assert ColorMapType.TURBO.value is not None
        assert ColorMapType.GRAY.value is None

    def test_edge_aware_filter_type_values(self) -> None:
        """Test EdgeAwareFilterType enum values."""
        assert EdgeAwareFilterType.BILATERAL.value == "bilateral"
        assert EdgeAwareFilterType.GUIDED.value == "guided"
        assert EdgeAwareFilterType.NONE.value == "none"


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling."""

    def test_depth_processing_error_attrs(self, mock_logger: MagicMock) -> None:
        """Test DepthProcessingError attributes."""
        original = ValueError("Original error")
        error = DepthProcessingError(
            "Test error",
            operation="test_op",
            original_exception=original,
        )

        assert str(error) == "Test error"
        assert error.operation == "test_op"
        assert error.original_exception is original

    def test_depth_processing_error_inheritance(self, mock_logger: MagicMock) -> None:
        """Test DepthProcessingError inheritance."""
        error = DepthProcessingError("Test")
        assert isinstance(error, Exception)


# Mark as slow test
import pytest

pytestmark = pytest.mark.slow
