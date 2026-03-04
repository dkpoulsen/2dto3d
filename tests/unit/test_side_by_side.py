"""Unit tests for Side-by-Side 3D encoding module.

Tests cover:
- SideBySideLayout enum
- SideBySideEncoder class
- All side-by-side encoding methods (horizontal, vertical, half-width, full-width)
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
from video2d3d.stereo.side_by_side import (
    SideBySideEncoder,
    SideBySideLayout,
    create_side_by_side_encoder,
    encode_side_by_side,
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
    with patch("video2d3d.stereo.side_by_side.get_logger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# ---------------------------------------------------------------------------
# SideBySideLayout Tests
# ---------------------------------------------------------------------------


class TestSideBySideLayout:
    """Tests for SideBySideLayout enum."""

    def test_all_layouts_exist(self) -> None:
        """Test that all expected layout types exist."""
        assert hasattr(SideBySideLayout, "HORIZONTAL")
        assert hasattr(SideBySideLayout, "VERTICAL")

    def test_layout_values(self) -> None:
        """Test layout string values."""
        assert SideBySideLayout.HORIZONTAL.value == "horizontal"
        assert SideBySideLayout.VERTICAL.value == "vertical"


# ---------------------------------------------------------------------------
# SideBySideEncoder Tests
# ---------------------------------------------------------------------------


class TestSideBySideEncoder:
    """Tests for SideBySideEncoder class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default encoder initialization."""
        encoder = SideBySideEncoder()

        assert encoder.layout == SideBySideLayout.HORIZONTAL
        assert encoder.half_width is False
        assert encoder.swap_eyes is False

    def test_initialization_custom_layout(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom layout."""
        encoder = SideBySideEncoder(layout=SideBySideLayout.VERTICAL)

        assert encoder.layout == SideBySideLayout.VERTICAL

    def test_initialization_half_width(self, mock_logger: MagicMock) -> None:
        """Test initialization with half-width mode."""
        encoder = SideBySideEncoder(half_width=True)

        assert encoder.half_width is True

    def test_initialization_swap_eyes(self, mock_logger: MagicMock) -> None:
        """Test initialization with swap eyes."""
        encoder = SideBySideEncoder(swap_eyes=True)

        assert encoder.swap_eyes is True

    def test_encode_horizontal_full_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test horizontal layout with full width."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Full width horizontal: output width = 2 * input width
        assert result.shape == (100, 200, 3)
        assert result.dtype == np.uint8

    def test_encode_horizontal_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test horizontal layout with half width."""
        encoder = SideBySideEncoder(half_width=True)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Half width horizontal: output width = input width
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_encode_vertical_full_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test vertical layout with full width."""
        encoder = SideBySideEncoder(layout=SideBySideLayout.VERTICAL)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Full width vertical: output height = 2 * input height
        assert result.shape == (200, 100, 3)
        assert result.dtype == np.uint8

    def test_encode_vertical_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test vertical layout with half width."""
        encoder = SideBySideEncoder(layout=SideBySideLayout.VERTICAL, half_width=True)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Half width vertical: output height = 2 * input height, width = input width / 2
        assert result.shape == (200, 50, 3)
        assert result.dtype == np.uint8

    def test_encode_swap_eyes(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that swap_eyes correctly swaps left and right views."""
        encoder = SideBySideEncoder(swap_eyes=True)
        # Create distinct left and right views
        left = np.zeros((100, 100, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((100, 100, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # With swap_eyes=True, right (blue) should be on left side
        # Left half should be blue (right view) - columns 0-99
        assert result[50, 25, 2] == 255  # Blue channel in left half
        # Right half should be red (left view) - columns 100-199
        assert result[50, 150, 0] == 255  # Red channel in right half

    def test_encode_override_layout(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test overriding layout in encode call."""
        encoder = SideBySideEncoder(layout=SideBySideLayout.HORIZONTAL)
        left = sample_image.copy()
        right = sample_image.copy()

        # Override to vertical
        result = encoder.encode(left, right, layout=SideBySideLayout.VERTICAL)

        assert result.shape == (200, 100, 3)

    def test_encode_override_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test overriding half_width in encode call."""
        encoder = SideBySideEncoder(half_width=False)
        left = sample_image.copy()
        right = sample_image.copy()

        # Override to half width
        result = encoder.encode(left, right, half_width=True)

        assert result.shape == (100, 100, 3)

    def test_encode_grayscale_input(
        self,
        mock_logger: MagicMock,
        sample_grayscale_image: np.ndarray,
    ) -> None:
        """Test encoding with grayscale input images."""
        encoder = SideBySideEncoder()
        left = sample_grayscale_image.copy()
        right = sample_grayscale_image.copy()

        result = encoder.encode(left, right)

        # Output should maintain grayscale (2D or 3D with same dimensions)
        assert result.shape == (100, 200)

    def test_encode_float_input(
        self,
        mock_logger: MagicMock,
        sample_float_image: np.ndarray,
    ) -> None:
        """Test encoding with float input images."""
        encoder = SideBySideEncoder()
        left = sample_float_image.copy()
        right = sample_float_image.copy()

        result = encoder.encode(left, right)

        assert result.shape == (100, 200, 3)
        # Float input should preserve dtype
        assert result.dtype == np.float32

    def test_encode_dimension_mismatch_raises_error(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that mismatched dimensions raise ValueError."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        wrong_right = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="must have the same shape"):
            encoder.encode(left, wrong_right)

    def test_encode_horizontal(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_horizontal convenience method."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_horizontal(left, right)

        assert result.shape == (100, 200, 3)

    def test_encode_vertical(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_vertical convenience method."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_vertical(left, right)

        assert result.shape == (200, 100, 3)

    def test_encode_half_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_half_width convenience method."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_half_width(left, right)

        assert result.shape == (100, 100, 3)

    def test_encode_full_width(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_full_width convenience method."""
        encoder = SideBySideEncoder(half_width=True)  # Default is half-width
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_full_width(left, right)

        assert result.shape == (100, 200, 3)

    def test_encode_cross_eye(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_cross_eye convenience method."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_cross_eye(left, right)

        assert result.shape == (100, 200, 3)

    def test_encode_parallel(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_parallel convenience method."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_parallel(left, right)

        assert result.shape == (100, 200, 3)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_side_by_side_encoder(self, mock_logger: MagicMock) -> None:
        """Test create_side_by_side_encoder function."""
        encoder = create_side_by_side_encoder(
            layout=SideBySideLayout.VERTICAL,
            half_width=True,
            swap_eyes=True,
        )

        assert encoder.layout == SideBySideLayout.VERTICAL
        assert encoder.half_width is True
        assert encoder.swap_eyes is True

    def test_encode_side_by_side(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_side_by_side convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_side_by_side(left, right)

        assert result.shape == (100, 200, 3)

    def test_encode_side_by_side_with_options(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_side_by_side with all options."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_side_by_side(
            left,
            right,
            layout=SideBySideLayout.VERTICAL,
            half_width=True,
            swap_eyes=False,
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
        encoder = SideBySideEncoder()
        left = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (10, 20, 3)

    def test_identical_views(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test with identical left and right views."""
        encoder = SideBySideEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Should still produce valid output
        assert result.shape == (100, 200, 3)
        # Left and right halves should be identical
        assert np.array_equal(result[:, :100], result[:, 100:])

    def test_extreme_color_values(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with extreme color values (all 0 or all 255)."""
        encoder = SideBySideEncoder()
        left_black = np.zeros((50, 50, 3), dtype=np.uint8)
        right_white = np.full((50, 50, 3), 255, dtype=np.uint8)

        result = encoder.encode(left_black, right_white)

        assert result.shape == (50, 100, 3)
        # Left half should be black
        assert np.all(result[:, :50] == 0)
        # Right half should be white
        assert np.all(result[:, 50:] == 255)

    def test_image_too_small_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-dimension image raises ValueError."""
        encoder = SideBySideEncoder()
        left = np.zeros((0, 10, 3), dtype=np.uint8)
        right = np.zeros((0, 10, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="dimensions must be at least"):
            encoder.encode(left, right)

    def test_odd_width_half_width(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test half-width encoding with odd width (should handle gracefully)."""
        encoder = SideBySideEncoder(half_width=True)
        left = np.random.randint(0, 255, (100, 101, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (100, 101, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        # 101 // 2 = 50, so output width should be 100
        assert result.shape == (100, 100, 3)

    def test_left_right_content_preserved(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that left and right content is preserved in output."""
        encoder = SideBySideEncoder()
        left = np.zeros((50, 50, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((50, 50, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # Check left half is red - columns 0-49
        assert result[25, 12, 0] == 255  # Red channel
        assert result[25, 12, 2] == 0  # Blue channel
        # Check right half is blue - columns 50-99
        assert result[25, 75, 0] == 0  # Red channel
        assert result[25, 75, 2] == 255  # Blue channel


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests with stereo module."""

    def test_import_from_stereo_module(self) -> None:
        """Test that encoder can be imported from stereo module."""
        from video2d3d.stereo import (
            SideBySideEncoder,
            SideBySideLayout,
            encode_side_by_side,
        )

        assert SideBySideEncoder is not None
        assert SideBySideLayout is not None
        assert encode_side_by_side is not None

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

        encoder = SideBySideEncoder()
        result = encoder.encode(left, right)

        assert result.shape == (100, 200, 3)
        # Left and right should NOT be identical due to shift
        assert not np.array_equal(result[:, :100], result[:, 100:])


class TestAdditionalEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_rgba_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with RGBA input (4 channels)."""
        encoder = SideBySideEncoder()
        # Create RGBA images (with alpha channel)
        left = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)

        result = encoder.encode(left, right)

        # RGBA input should produce RGBA output
        assert result.shape == (50, 100, 4)
        assert result.dtype == np.uint8

    def test_single_channel_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with single-channel (H, W, 1) input."""
        encoder = SideBySideEncoder()
        left = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (50, 100, 1)
        assert result.dtype == np.uint8

    def test_float_input_outside_range(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with float input outside [0, 1] range."""
        encoder = SideBySideEncoder()
        # Float images with values outside [0, 1] - cv2 handles this
        left = np.random.uniform(-0.5, 1.5, (50, 50, 3)).astype(np.float32)
        right = np.random.uniform(-0.5, 1.5, (50, 50, 3)).astype(np.float32)

        # Should work but cv2 will clip values during resize
        result = encoder.encode(left, right)

        assert result.shape == (50, 100, 3)
        assert result.dtype == np.float32

    def test_large_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with large image."""
        encoder = SideBySideEncoder()
        # 4K resolution
        left = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (2160, 7680, 3)

    def test_large_image_half_width(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with large image in half-width mode."""
        encoder = SideBySideEncoder(half_width=True)
        # 4K resolution
        left = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (2160, 3840, 3)

    def test_constants_exported(self) -> None:
        """Test that constants are properly exported."""
        from video2d3d.stereo.side_by_side import (
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
        encoder = SideBySideEncoder()

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
        encoder = SideBySideEncoder(half_width=True)
        # Create image with solid blocks (not thin lines which get averaged out)
        left = np.zeros((100, 100, 3), dtype=np.uint8)
        left[:, :50, :] = 255  # Left half white
        right = np.zeros((100, 100, 3), dtype=np.uint8)
        right[:, :50, :] = 128  # Left half gray

        result = encoder.encode(left, right)

        # With half_width=True:
        # 1. Each image is scaled from 100x100 to 100x50
        # 2. They are concatenated: left_scaled (50 wide) + right_scaled (50 wide) = 100 wide
        # Original left: cols 0-49 white, cols 50-99 black
        # Original right: cols 0-49 gray, cols 50-99 black
        # After scaling: each half maps to 25 output columns
        assert result.shape == (100, 100, 3)
        # Left scaled image: cols 0-24 white, cols 25-49 black
        assert result[50, 10, 0] > 200  # Should be close to 255 (white)
        assert result[50, 40, 0] < 50  # Should be close to 0 (black)
        # Right scaled image: cols 50-74 gray, cols 75-99 black
        assert 100 < result[50, 60, 0] < 150  # Should be close to 128 (gray)
        assert result[50, 90, 0] < 50  # Should be close to 0 (black)
