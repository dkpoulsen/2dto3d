"""Unit tests for Interlaced 3D encoding module.

Tests cover:
- InterlacedPattern enum
- InterlacedEncoder class
- All interlaced encoding methods (row, column, swap eyes)
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
from video2d3d.stereo.interlaced import (
    InterlacedEncoder,
    InterlacedPattern,
    create_interlaced_encoder,
    encode_interlaced,
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
    with patch("video2d3d.stereo.interlaced.get_logger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# ---------------------------------------------------------------------------
# InterlacedPattern Tests
# ---------------------------------------------------------------------------


class TestInterlacedPattern:
    """Tests for InterlacedPattern enum."""

    def test_all_patterns_exist(self) -> None:
        """Test that all expected pattern types exist."""
        assert hasattr(InterlacedPattern, "ROW_INTERLEAVED")
        assert hasattr(InterlacedPattern, "COLUMN_INTERLEAVED")

    def test_pattern_values(self) -> None:
        """Test pattern string values."""
        assert InterlacedPattern.ROW_INTERLEAVED.value == "row_interleaved"
        assert InterlacedPattern.COLUMN_INTERLEAVED.value == "column_interleaved"


# ---------------------------------------------------------------------------
# InterlacedEncoder Tests
# ---------------------------------------------------------------------------


class TestInterlacedEncoder:
    """Tests for InterlacedEncoder class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default encoder initialization."""
        encoder = InterlacedEncoder()

        assert encoder.pattern == InterlacedPattern.ROW_INTERLEAVED
        assert encoder.swap_eyes is False

    def test_initialization_custom_pattern(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom pattern."""
        encoder = InterlacedEncoder(pattern=InterlacedPattern.COLUMN_INTERLEAVED)

        assert encoder.pattern == InterlacedPattern.COLUMN_INTERLEAVED

    def test_initialization_swap_eyes(self, mock_logger: MagicMock) -> None:
        """Test initialization with swap eyes."""
        encoder = InterlacedEncoder(swap_eyes=True)

        assert encoder.swap_eyes is True

    def test_encode_row_interleaved(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test row-interleaved pattern encoding."""
        encoder = InterlacedEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Output should have same dimensions as input
        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8

    def test_encode_column_interleaved(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test column-interleaved pattern encoding."""
        encoder = InterlacedEncoder(pattern=InterlacedPattern.COLUMN_INTERLEAVED)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        assert result.shape == sample_image.shape
        assert result.dtype == np.uint8

    def test_encode_swap_eyes(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that swap_eyes correctly swaps left and right eye assignments."""
        encoder = InterlacedEncoder()
        # Create distinct left and right views
        left = np.zeros((10, 10, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((10, 10, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result_normal = encoder.encode(left, right)
        result_swapped = encoder.encode(left, right, swap_eyes=True)

        # At row 0 (even) - normal uses left eye, swapped uses right
        # Normal: should be red, Swapped: should be blue
        assert result_normal[0, 0, 0] == 255  # Red channel (left)
        assert result_normal[0, 0, 2] == 0  # Blue channel

        assert result_swapped[0, 0, 0] == 0  # Red channel
        assert result_swapped[0, 0, 2] == 255  # Blue channel (right, swapped)

    def test_encode_override_pattern(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test overriding pattern in encode call."""
        encoder = InterlacedEncoder(pattern=InterlacedPattern.ROW_INTERLEAVED)
        left = sample_image.copy()
        right = sample_image.copy()

        # Override to column-interleaved
        result = encoder.encode(left, right, pattern=InterlacedPattern.COLUMN_INTERLEAVED)

        assert result.shape == sample_image.shape

    def test_encode_grayscale_input(
        self,
        mock_logger: MagicMock,
        sample_grayscale_image: np.ndarray,
    ) -> None:
        """Test encoding with grayscale input images."""
        encoder = InterlacedEncoder()
        left = sample_grayscale_image.copy()
        right = sample_grayscale_image.copy()

        result = encoder.encode(left, right)

        # Output should maintain grayscale (2D)
        assert result.shape == sample_grayscale_image.shape

    def test_encode_float_input(
        self,
        mock_logger: MagicMock,
        sample_float_image: np.ndarray,
    ) -> None:
        """Test encoding with float input images."""
        encoder = InterlacedEncoder()
        left = sample_float_image.copy()
        right = sample_float_image.copy()

        result = encoder.encode(left, right)

        assert result.shape == sample_float_image.shape
        # Float input should preserve dtype
        assert result.dtype == np.float32

    def test_encode_dimension_mismatch_raises_error(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that mismatched dimensions raise ValueError."""
        encoder = InterlacedEncoder()
        left = sample_image.copy()
        wrong_right = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="must have the same shape"):
            encoder.encode(left, wrong_right)

    def test_encode_row_interleaved_method(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_row_interleaved convenience method."""
        encoder = InterlacedEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_row_interleaved(left, right)

        assert result.shape == sample_image.shape

    def test_encode_column_interleaved_method(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_column_interleaved convenience method."""
        encoder = InterlacedEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_column_interleaved(left, right)

        assert result.shape == sample_image.shape

    def test_encode_with_swap_method(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_with_swap convenience method."""
        encoder = InterlacedEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_with_swap(left, right)

        assert result.shape == sample_image.shape


# ---------------------------------------------------------------------------
# Interlaced Pattern Logic Tests
# ---------------------------------------------------------------------------


class TestInterlacedPatternLogic:
    """Tests for the interlaced pattern pixel assignment logic."""

    def test_row_interleaved_pixel_assignment(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that row-interleaved pattern assigns pixels correctly."""
        encoder = InterlacedEncoder(pattern=InterlacedPattern.ROW_INTERLEAVED)
        # Create small test images with distinct values
        left = np.zeros((4, 4), dtype=np.uint8)
        left[:, :] = 100  # All pixels = 100
        right = np.zeros((4, 4), dtype=np.uint8)
        right[:, :] = 200  # All pixels = 200

        result = encoder.encode(left, right)

        # Check pattern: even rows = left (100), odd rows = right (200)
        assert result[0, 0] == 100  # Row 0 (even) -> left
        assert result[0, 1] == 100  # Row 0 (even) -> left
        assert result[1, 0] == 200  # Row 1 (odd) -> right
        assert result[1, 1] == 200  # Row 1 (odd) -> right
        assert result[2, 0] == 100  # Row 2 (even) -> left
        assert result[3, 0] == 200  # Row 3 (odd) -> right

    def test_column_interleaved_pixel_assignment(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that column-interleaved pattern assigns pixels correctly."""
        encoder = InterlacedEncoder(pattern=InterlacedPattern.COLUMN_INTERLEAVED)
        left = np.zeros((4, 4), dtype=np.uint8)
        left[:, :] = 100
        right = np.zeros((4, 4), dtype=np.uint8)
        right[:, :] = 200

        result = encoder.encode(left, right)

        # Check pattern: even columns = left (100), odd columns = right (200)
        assert result[0, 0] == 100  # Column 0 (even) -> left
        assert result[0, 1] == 200  # Column 1 (odd) -> right
        assert result[1, 0] == 100  # Column 0 (even) -> left
        assert result[1, 1] == 200  # Column 1 (odd) -> right
        assert result[0, 2] == 100  # Column 2 (even) -> left
        assert result[0, 3] == 200  # Column 3 (odd) -> right

    def test_swap_eyes_flips_pattern(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that swap_eyes flips the eye assignment."""
        encoder = InterlacedEncoder()
        left = np.zeros((4, 4), dtype=np.uint8)
        left[:, :] = 100
        right = np.zeros((4, 4), dtype=np.uint8)
        right[:, :] = 200

        result_normal = encoder.encode(left, right, swap_eyes=False)
        result_swapped = encoder.encode(left, right, swap_eyes=True)

        # Swapped should be inverse of normal for row-interleaved
        assert result_normal[0, 0] == 100
        assert result_swapped[0, 0] == 200
        assert result_normal[1, 0] == 200
        assert result_swapped[1, 0] == 100

    def test_half_rows_from_each_eye(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that exactly half the rows come from each eye in row-interleaved mode."""
        encoder = InterlacedEncoder()
        left = np.zeros((10, 10), dtype=np.uint8)
        left[:, :] = 100
        right = np.zeros((10, 10), dtype=np.uint8)
        right[:, :] = 200

        result = encoder.encode(left, right)

        # Count pixels from each eye
        left_pixels = np.sum(result == 100)
        right_pixels = np.sum(result == 200)

        # Should be exactly half each (50 each for 10x10)
        assert left_pixels == 50
        assert right_pixels == 50


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_interlaced_encoder(self, mock_logger: MagicMock) -> None:
        """Test create_interlaced_encoder function."""
        encoder = create_interlaced_encoder(
            pattern=InterlacedPattern.COLUMN_INTERLEAVED,
            swap_eyes=True,
        )

        assert encoder.pattern == InterlacedPattern.COLUMN_INTERLEAVED
        assert encoder.swap_eyes is True

    def test_encode_interlaced(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_interlaced convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_interlaced(left, right)

        assert result.shape == sample_image.shape

    def test_encode_interlaced_with_options(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_interlaced with all options."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_interlaced(
            left,
            right,
            pattern=InterlacedPattern.COLUMN_INTERLEAVED,
            swap_eyes=True,
        )

        assert result.shape == sample_image.shape


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
        encoder = InterlacedEncoder()
        left = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (10, 10, 3)

    def test_identical_views(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test with identical left and right views."""
        encoder = InterlacedEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Should still produce valid output identical to input
        assert result.shape == sample_image.shape
        assert np.array_equal(result, sample_image)

    def test_extreme_color_values(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with extreme color values (all 0 or all 255)."""
        encoder = InterlacedEncoder()
        left_black = np.zeros((50, 50, 3), dtype=np.uint8)
        right_white = np.full((50, 50, 3), 255, dtype=np.uint8)

        result = encoder.encode(left_black, right_white)

        assert result.shape == (50, 50, 3)
        # Half should be black, half white
        assert np.sum(np.all(result == 0, axis=2)) == 1250  # Half pixels
        assert np.sum(np.all(result == 255, axis=2)) == 1250  # Half pixels

    def test_image_too_small_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-height image raises ValueError."""
        encoder = InterlacedEncoder()
        left = np.zeros((0, 10, 3), dtype=np.uint8)
        right = np.zeros((0, 10, 3), dtype=np.uint8)
        with pytest.raises(ValueError, match="dimensions must be at least"):
            encoder.encode(left, right)

    def test_odd_dimensions(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with odd dimensions (should work fine)."""
        encoder = InterlacedEncoder()
        left = np.random.randint(0, 255, (99, 99, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (99, 99, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (99, 99, 3)

    def test_left_right_content_preserved(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that left and right content is preserved at correct positions."""
        encoder = InterlacedEncoder()
        left = np.zeros((4, 4, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((4, 4, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # At even rows, red channel should be set (from left)
        assert result[0, 0, 0] == 255  # Red at row 0
        assert result[0, 0, 2] == 0  # No blue

        # At odd rows, blue channel should be set (from right)
        assert result[1, 0, 0] == 0  # No red
        assert result[1, 0, 2] == 255  # Blue at row 1

    def test_image_zero_width_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-width image raises ValueError."""
        encoder = InterlacedEncoder()
        left = np.zeros((10, 0, 3), dtype=np.uint8)
        right = np.zeros((10, 0, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="dimensions must be at least"):
            encoder.encode(left, right)

    def test_repr_method(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test __repr__ method returns correct string representation."""
        encoder = InterlacedEncoder()
        repr_str = repr(encoder)

        assert "InterlacedEncoder" in repr_str
        assert "row_interleaved" in repr_str
        assert "swap_eyes=False" in repr_str

    def test_repr_method_with_options(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test __repr__ method with custom options."""
        encoder = InterlacedEncoder(
            pattern=InterlacedPattern.COLUMN_INTERLEAVED,
            swap_eyes=True,
        )
        repr_str = repr(encoder)

        assert "InterlacedEncoder" in repr_str
        assert "column_interleaved" in repr_str
        assert "swap_eyes=True" in repr_str


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests with stereo module."""

    def test_import_from_stereo_module(self) -> None:
        """Test that encoder can be imported from stereo module."""
        from video2d3d.stereo import (
            InterlacedEncoder,
            InterlacedPattern,
            encode_interlaced,
        )

        assert InterlacedEncoder is not None
        assert InterlacedPattern is not None
        assert encode_interlaced is not None

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

        encoder = InterlacedEncoder()
        result = encoder.encode(left, right)

        assert result.shape == (100, 100, 3)
        # Left and right should NOT be identical due to shift
        assert not np.array_equal(result, left)
        assert not np.array_equal(result, right)


class TestAdditionalEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_rgba_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with RGBA input (4 channels)."""
        encoder = InterlacedEncoder()
        # Create RGBA images (with alpha channel)
        left = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 4), dtype=np.uint8)

        result = encoder.encode(left, right)

        # RGBA input should produce RGBA output
        assert result.shape == (50, 50, 4)
        assert result.dtype == np.uint8

    def test_single_channel_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with single-channel (H, W, 1) input."""
        encoder = InterlacedEncoder()
        left = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (50, 50, 1)
        assert result.dtype == np.uint8

    def test_large_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with large image."""
        encoder = InterlacedEncoder()
        # 4K resolution
        left = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (2160, 3840, 3)

    def test_constants_exported(self) -> None:
        """Test that constants are properly exported."""
        from video2d3d.stereo.interlaced import MIN_IMAGE_DIMENSION

        assert MIN_IMAGE_DIMENSION == 1

    def test_different_dtypes_preserved(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that different dtypes are preserved in output."""
        encoder = InterlacedEncoder()

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

    def test_pattern_and_swap_combined(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test combining column-interleaved pattern with eye swap."""
        encoder = InterlacedEncoder()
        left = np.zeros((4, 4), dtype=np.uint8)
        left[:, :] = 100
        right = np.zeros((4, 4), dtype=np.uint8)
        right[:, :] = 200

        # Row-interleaved with no swap
        result_row = encoder.encode(left, right)
        # Column-interleaved with swap should be different
        result_col_swap = encoder.encode(
            left, right, pattern=InterlacedPattern.COLUMN_INTERLEAVED, swap_eyes=True
        )

        # These should NOT be equal (different pattern)
        assert not np.array_equal(result_row, result_col_swap)

    def test_column_interleaved_half_columns(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that column-interleaved has half columns from each eye."""
        encoder = InterlacedEncoder(pattern=InterlacedPattern.COLUMN_INTERLEAVED)
        left = np.zeros((10, 10), dtype=np.uint8)
        left[:, :] = 100
        right = np.zeros((10, 10), dtype=np.uint8)
        right[:, :] = 200

        result = encoder.encode(left, right)

        # Count pixels from each eye
        left_pixels = np.sum(result == 100)
        right_pixels = np.sum(result == 200)

        # Should be exactly half each (50 each for 10x10)
        assert left_pixels == 50
        assert right_pixels == 50
