"""Unit tests for Top-Bottom 3D encoding module.

Tests cover:
- TopBottomLayout enum
- TopBottomEncoder class
- All top-bottom encoding methods (standard, swapped, half-width, full-width)
- Input validation and error handling

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
from video2d3d.stereo.top_bottom import (
    TopBottomEncoder,
    TopBottomLayout,
    create_top_bottom_encoder,
    encode_top_bottom,
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
def sample_float_image() -> np.ndarray:
    """Create a sample float image for testing."""
    np.random.seed(42)
    return np.random.random((100, 100, 3)).astype(np.float32)


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.stereo.top_bottom.get_logger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# ---------------------------------------------------------------------------
# TopBottomLayout Tests
# ---------------------------------------------------------------------------


class TestTopBottomLayout:
    """Tests for TopBottomLayout enum."""

    def test_all_layouts_exist(self) -> None:
        """Test that all expected layout types exist."""
        assert hasattr(TopBottomLayout, "STANDARD")
        assert hasattr(TopBottomLayout, "SWAPPED")

    def test_layout_values(self) -> None:
        """Test layout string values."""
        assert TopBottomLayout.STANDARD.value == "standard"
        assert TopBottomLayout.SWAPPED.value == "swapped"


# ---------------------------------------------------------------------------
# TopBottomEncoder Tests
# ---------------------------------------------------------------------------


class TestTopBottomEncoder:
    """Tests for TopBottomEncoder class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default encoder initialization."""
        encoder = TopBottomEncoder()

        assert encoder.layout == TopBottomLayout.STANDARD
        assert encoder.half_width is False

    def test_initialization_custom_layout(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom layout."""
        encoder = TopBottomEncoder(layout=TopBottomLayout.SWAPPED)

        assert encoder.layout == TopBottomLayout.SWAPPED

    def test_repr(self, mock_logger: MagicMock) -> None:
        """Test __repr__ method returns correct string."""
        # Default encoder
        encoder = TopBottomEncoder()
        assert repr(encoder) == "TopBottomEncoder(layout=standard, half_width=False)"

        # Custom encoder
        encoder_custom = TopBottomEncoder(layout=TopBottomLayout.SWAPPED, half_width=True)
        assert repr(encoder_custom) == "TopBottomEncoder(layout=swapped, half_width=True)"

    def test_encode_standard_full_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test standard layout with full width."""
        encoder = TopBottomEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Full width top-bottom: output height = 2 * input height
        assert result.shape == (200, 100, 3)
        assert result.dtype == np.uint8

    def test_encode_standard_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test standard layout with half width."""
        encoder = TopBottomEncoder(half_width=True)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Half width top-bottom: output width = input width / 2, height = 2 * input height
        assert result.shape == (200, 50, 3)
        assert result.dtype == np.uint8

    def test_encode_swapped_full_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test swapped layout with full width."""
        encoder = TopBottomEncoder(layout=TopBottomLayout.SWAPPED)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Full width swapped: output height = 2 * input height
        assert result.shape == (200, 100, 3)
        assert result.dtype == np.uint8

    def test_encode_swapped_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test swapped layout with half width."""
        encoder = TopBottomEncoder(layout=TopBottomLayout.SWAPPED, half_width=True)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Half width swapped: output height = 2 * input height, width = input width / 2
        assert result.shape == (200, 50, 3)
        assert result.dtype == np.uint8

    def test_encode_standard_layout_places_left_on_top(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that standard layout places left view on top."""
        encoder = TopBottomEncoder()
        # Create distinct left and right views
        left = np.zeros((100, 100, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((100, 100, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # Top half should be red (left view) - rows 0-99
        assert result[50, 50, 0] == 255  # Red channel in top half
        assert result[50, 50, 2] == 0  # No blue in top half
        # Bottom half should be blue (right view) - rows 100-199
        assert result[150, 50, 0] == 0  # No red in bottom half
        assert result[150, 50, 2] == 255  # Blue channel in bottom half

    def test_encode_swapped_layout_places_right_on_top(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that swapped layout places right view on top."""
        encoder = TopBottomEncoder(layout=TopBottomLayout.SWAPPED)
        # Create distinct left and right views
        left = np.zeros((100, 100, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((100, 100, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # Top half should be blue (right view) - rows 0-99
        assert result[50, 50, 0] == 0  # No red in top half
        assert result[50, 50, 2] == 255  # Blue channel in top half
        # Bottom half should be red (left view) - rows 100-199
        assert result[150, 50, 0] == 255  # Red channel in bottom half
        assert result[150, 50, 2] == 0  # No blue in bottom half

    def test_encode_override_layout(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test overriding layout in encode call."""
        encoder = TopBottomEncoder(layout=TopBottomLayout.STANDARD)
        left = sample_image.copy()
        right = sample_image.copy()

        # Override to swapped
        result = encoder.encode(left, right, layout=TopBottomLayout.SWAPPED)

        assert result.shape == (200, 100, 3)

    def test_encode_override_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test overriding half_width in encode call."""
        encoder = TopBottomEncoder(half_width=False)
        left = sample_image.copy()
        right = sample_image.copy()

        # Override to half width
        result = encoder.encode(left, right, half_width=True)

        assert result.shape == (200, 50, 3)

    def test_encode_grayscale_input(
        self,
        mock_logger: MagicMock,
        sample_grayscale_image: np.ndarray,
    ) -> None:
        """Test encoding with grayscale input images."""
        encoder = TopBottomEncoder()
        left = sample_grayscale_image.copy()
        right = sample_grayscale_image.copy()

        result = encoder.encode(left, right)

        # Output should maintain grayscale (2D)
        assert result.shape == (200, 100)

    def test_encode_float_input(
        self,
        mock_logger: MagicMock,
        sample_float_image: np.ndarray,
    ) -> None:
        """Test encoding with float input images."""
        encoder = TopBottomEncoder()
        left = sample_float_image.copy()
        right = sample_float_image.copy()

        result = encoder.encode(left, right)

        assert result.shape == (200, 100, 3)
        # Float input should preserve dtype
        assert result.dtype == np.float32

    def test_encode_dimension_mismatch_raises_error(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that mismatched dimensions raise ValueError."""
        encoder = TopBottomEncoder()
        left = sample_image.copy()
        wrong_right = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="must have the same shape"):
            encoder.encode(left, wrong_right)

    def test_encode_standard(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_standard convenience method."""
        encoder = TopBottomEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_standard(left, right)

        assert result.shape == (200, 100, 3)

    def test_encode_swapped(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_swapped convenience method."""
        encoder = TopBottomEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_swapped(left, right)

        assert result.shape == (200, 100, 3)

    def test_encode_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_half_width convenience method."""
        encoder = TopBottomEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_half_width(left, right)

        assert result.shape == (200, 50, 3)

    def test_encode_full_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_full_width convenience method."""
        encoder = TopBottomEncoder(half_width=True)  # Default is half-width
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_full_width(left, right)

        assert result.shape == (200, 100, 3)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_top_bottom_encoder(self, mock_logger: MagicMock) -> None:
        """Test create_top_bottom_encoder function."""
        encoder = create_top_bottom_encoder(
            layout=TopBottomLayout.SWAPPED,
            half_width=True,
        )

        assert encoder.layout == TopBottomLayout.SWAPPED
        assert encoder.half_width is True

    def test_encode_top_bottom(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_top_bottom convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_top_bottom(left, right)

        assert result.shape == (200, 100, 3)

    def test_encode_top_bottom_with_options(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_top_bottom with all options."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_top_bottom(
            left,
            right,
            layout=TopBottomLayout.SWAPPED,
            half_width=True,
        )

        assert result.shape == (200, 50, 3)


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and special inputs."""

    def test_very_small_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with very small image."""
        encoder = TopBottomEncoder()
        left = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (20, 10, 3)

    def test_identical_views(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test with identical left and right views."""
        encoder = TopBottomEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Should still produce valid output
        assert result.shape == (200, 100, 3)
        # Top and bottom halves should be identical
        assert np.array_equal(result[:100], result[100:])

    def test_extreme_color_values(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with extreme color values (all 0 or all 255)."""
        encoder = TopBottomEncoder()
        left_black = np.zeros((50, 50, 3), dtype=np.uint8)
        right_white = np.full((50, 50, 3), 255, dtype=np.uint8)

        result = encoder.encode(left_black, right_white)

        assert result.shape == (100, 50, 3)
        # Top half should be black
        assert np.all(result[:50] == 0)
        # Bottom half should be white
        assert np.all(result[50:] == 255)

    def test_image_too_small_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-dimension image raises ValueError."""
        encoder = TopBottomEncoder()
        left = np.zeros((0, 10, 3), dtype=np.uint8)
        right = np.zeros((0, 10, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="dimensions must be at least"):
            encoder.encode(left, right)

    def test_odd_width_half_width(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test half-width encoding with odd width (should handle gracefully)."""
        encoder = TopBottomEncoder(half_width=True)
        left = np.random.randint(0, 255, (100, 101, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (100, 101, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        # 101 // 2 = 50, so output width should be 50
        assert result.shape == (200, 50, 3)

    def test_top_bottom_content_preserved(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that top and bottom content is preserved in output."""
        encoder = TopBottomEncoder()
        left = np.zeros((50, 50, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((50, 50, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # Check top half is red - rows 0-49
        assert result[25, 25, 0] == 255  # Red channel
        assert result[25, 25, 2] == 0  # Blue channel
        # Check bottom half is blue - rows 50-99
        assert result[75, 25, 0] == 0  # Red channel
        assert result[75, 25, 2] == 255  # Blue channel

    def test_none_input_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that None inputs raise ValueError."""
        encoder = TopBottomEncoder()
        valid_image = np.zeros((50, 50, 3), dtype=np.uint8)

        # Test None left
        with pytest.raises(ValueError, match="cannot be None"):
            encoder.encode(None, valid_image)  # type: ignore

        # Test None right
        with pytest.raises(ValueError, match="cannot be None"):
            encoder.encode(valid_image, None)  # type: ignore

        # Test both None
        with pytest.raises(ValueError, match="cannot be None"):
            encoder.encode(None, None)  # type: ignore

    def test_zero_width_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-width image raises ValueError."""
        encoder = TopBottomEncoder()
        left = np.zeros((10, 0, 3), dtype=np.uint8)
        right = np.zeros((10, 0, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="dimensions must be at least"):
            encoder.encode(left, right)


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests with stereo module."""

    def test_import_from_stereo_module(self) -> None:
        """Test that encoder can be imported from stereo module."""
        from video2d3d.stereo import (
            TopBottomEncoder,
            TopBottomLayout,
            create_top_bottom_encoder,
            encode_top_bottom,
        )

        assert TopBottomEncoder is not None
        assert TopBottomLayout is not None
        assert encode_top_bottom is not None
        assert create_top_bottom_encoder is not None

    def test_encoder_with_dibr_generated_views(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoder with views that would come from DIBR engine."""
        # Simulate DIBR output (slightly different left/right views)
        np.random.seed(42)
        base = (np.random.random((100, 100, 3)) * 255).astype(np.uint8)
        left = base.copy()
        right = np.roll(base, 5, axis=1)  # Simulated disparity shift

        encoder = TopBottomEncoder()
        result = encoder.encode(left, right)

        assert result.shape == (200, 100, 3)
        # Top and bottom should NOT be identical due to shift
        assert not np.array_equal(result[:100], result[100:])


class TestAdditionalEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_rgba_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with RGBA input (4 channels)."""
        encoder = TopBottomEncoder()
        # Create RGBA images (with alpha channel)
        left = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)

        result = encoder.encode(left, right)

        # RGBA input should produce RGBA output
        assert result.shape == (100, 50, 4)
        assert result.dtype == np.uint8

    def test_single_channel_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with single-channel (H, W, 1) input."""
        encoder = TopBottomEncoder()
        left = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (100, 50, 1)
        assert result.dtype == np.uint8

    def test_float_input_outside_range(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with float input outside [0, 1] range."""
        encoder = TopBottomEncoder()
        # Float images with values outside [0, 1] - cv2 handles this
        left = np.random.uniform(-0.5, 1.5, (50, 50, 3)).astype(np.float32)
        right = np.random.uniform(-0.5, 1.5, (50, 50, 3)).astype(np.float32)

        # Should work but cv2 will clip values during resize
        result = encoder.encode(left, right)

        assert result.shape == (100, 50, 3)
        assert result.dtype == np.float32

    def test_large_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with large image."""
        encoder = TopBottomEncoder()
        # 4K resolution
        left = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (4320, 3840, 3)

    def test_large_image_half_width(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with large image in half-width mode."""
        encoder = TopBottomEncoder(half_width=True)
        # 4K resolution
        left = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (4320, 1920, 3)

    def test_constants_exported(self) -> None:
        """Test that constants are properly exported."""
        from video2d3d.stereo.top_bottom import (
            LUMINANCE_B,
            LUMINANCE_G,
            LUMINANCE_R,
            MIN_IMAGE_DIMENSION,
        )

        assert MIN_IMAGE_DIMENSION == 1
        assert LUMINANCE_R == 0.299
        assert LUMINANCE_G == 0.587
        assert LUMINANCE_B == 0.114

    def test_different_dtypes_preserved(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that different dtypes are preserved in output."""
        encoder = TopBottomEncoder()

        # Test uint16
        left = np.random.randint(0, 65535, (50, 50, 3), dtype=np.uint16)
        right = np.random.randint(0, 65535, (50, 50, 3), dtype=np.uint16)
        result = encoder.encode(left, right)
        assert result.dtype == np.uint16

        # Test float64
        left = np.random.random((50, 50, 3)).astype(np.float64)
        right = np.random.random((50, 50, 3)).astype(np.float64)
        result = encoder.encode(left, right)
        assert result.dtype == np.float64

    def test_interpolation_quality_half_width(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that INTER_AREA provides good quality for downscaling."""
        encoder = TopBottomEncoder(half_width=True)
        # Create image with solid blocks
        left = np.zeros((100, 100, 3), dtype=np.uint8)
        left[:, :50, :] = 255  # Left half white
        right = np.zeros((100, 100, 3), dtype=np.uint8)
        right[:, :50, :] = 128  # Left half gray

        result = encoder.encode(left, right)

        # With half_width=True:
        # Each image is scaled from 100x100 to 100x50
        # Then they are concatenated vertically: 200x50
        assert result.shape == (200, 50, 3)
        # Top half (left view): cols 0-24 white, cols 25-49 black
        assert result[50, 10, 0] > 200  # Should be close to 255 (white)
        assert result[50, 40, 0] < 50  # Should be close to 0 (black)
        # Bottom half (right view): cols 0-24 gray, cols 25-49 black
        assert 100 < result[150, 10, 0] < 150  # Should be close to 128 (gray)
        assert result[150, 40, 0] < 50  # Should be close to 0 (black)
