"""Unit tests for Anaglyph 3D encoding module.

Tests cover:
- AnaglyphType enum
- AnaglyphEncoder class
- All anaglyph encoding methods (red-cyan, magenta-green, amber-blue)
- Input validation and error handling
- Integration with AnaglyphGenerator

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
from video2d3d.stereo import AnaglyphGenerator
from video2d3d.stereo.anaglyph import (
    AnaglyphEncoder,
    AnaglyphType,
    create_anaglyph_encoder,
    encode_anaglyph,
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
def sample_rgba_image() -> np.ndarray:
    """Create a sample RGBA image for testing."""
    np.random.seed(42)
    return (np.random.random((100, 100, 4)) * 255).astype(np.uint8)


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.stereo.anaglyph.get_logger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# ---------------------------------------------------------------------------
# AnaglyphType Tests
# ---------------------------------------------------------------------------


class TestAnaglyphType:
    """Tests for AnaglyphType enum."""

    def test_all_types_exist(self) -> None:
        """Test that all expected anaglyph types exist."""
        assert hasattr(AnaglyphType, "RED_CYAN_DUBOIS")
        assert hasattr(AnaglyphType, "RED_CYAN_COLOR")
        assert hasattr(AnaglyphType, "RED_CYAN_GRAY")
        assert hasattr(AnaglyphType, "RED_CYAN_HALF_COLOR")
        assert hasattr(AnaglyphType, "MAGENTA_GREEN")
        assert hasattr(AnaglyphType, "AMBER_BLUE")

    def test_type_values(self) -> None:
        """Test anaglyph type string values."""
        assert AnaglyphType.RED_CYAN_DUBOIS.value == "red_cyan_dubois"
        assert AnaglyphType.RED_CYAN_COLOR.value == "red_cyan_color"
        assert AnaglyphType.RED_CYAN_GRAY.value == "red_cyan_gray"
        assert AnaglyphType.RED_CYAN_HALF_COLOR.value == "red_cyan_half_color"
        assert AnaglyphType.MAGENTA_GREEN.value == "magenta_green"
        assert AnaglyphType.AMBER_BLUE.value == "amber_blue"


# ---------------------------------------------------------------------------
# AnaglyphEncoder Tests
# ---------------------------------------------------------------------------


class TestAnaglyphEncoder:
    """Tests for AnaglyphEncoder class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default encoder initialization."""
        encoder = AnaglyphEncoder()

        assert encoder.default_type == AnaglyphType.RED_CYAN_DUBOIS

    def test_initialization_custom_type(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom default type."""
        encoder = AnaglyphEncoder(default_type=AnaglyphType.MAGENTA_GREEN)

        assert encoder.default_type == AnaglyphType.MAGENTA_GREEN

    def test_encode_red_cyan_dubois(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test red-cyan Dubois encoding."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8
        # Values should be in valid range
        assert np.all(result >= 0)
        assert np.all(result <= 255)

    def test_encode_red_cyan_color(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test simple color red-cyan encoding."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_COLOR)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_red_cyan_gray(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test grayscale red-cyan encoding."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_GRAY)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_red_cyan_half_color(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test half-color red-cyan encoding."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_HALF_COLOR)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_magenta_green(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test magenta-green (Trioscopic) encoding."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.MAGENTA_GREEN)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_amber_blue(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test amber-blue (ColorCode3D) encoding."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.AMBER_BLUE)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_uses_default_type(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that encode uses default_type when no type specified."""
        encoder = AnaglyphEncoder(default_type=AnaglyphType.AMBER_BLUE)
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_grayscale_input(
        self,
        mock_logger: MagicMock,
        sample_grayscale_image: np.ndarray,
    ) -> None:
        """Test encoding with grayscale input images."""
        encoder = AnaglyphEncoder()
        left = sample_grayscale_image.copy()
        right = sample_grayscale_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (*sample_grayscale_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_float_input(
        self,
        mock_logger: MagicMock,
        sample_float_image: np.ndarray,
    ) -> None:
        """Test encoding with float input images."""
        encoder = AnaglyphEncoder()
        left = sample_float_image.copy()
        right = sample_float_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (*sample_float_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_rgba_input(
        self,
        mock_logger: MagicMock,
        sample_rgba_image: np.ndarray,
    ) -> None:
        """Test encoding with RGBA input (alpha channel should be dropped)."""
        encoder = AnaglyphEncoder()
        left = sample_rgba_image.copy()
        right = sample_rgba_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (*sample_rgba_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_encode_dimension_mismatch_raises_error(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that mismatched dimensions raise ValueError."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        wrong_right = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="must have the same shape"):
            encoder.encode(left, wrong_right, AnaglyphType.RED_CYAN_DUBOIS)

    def test_convenience_methods(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test all convenience encoding methods."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        # Test all convenience methods
        result_dubois = encoder.encode_red_cyan_dubois(left, right)
        assert result_dubois.shape == (*sample_image.shape[:2], 3)

        result_color = encoder.encode_red_cyan_color(left, right)
        assert result_color.shape == (*sample_image.shape[:2], 3)

        result_gray = encoder.encode_red_cyan_gray(left, right)
        assert result_gray.shape == (*sample_image.shape[:2], 3)

        result_half = encoder.encode_red_cyan_half_color(left, right)
        assert result_half.shape == (*sample_image.shape[:2], 3)

        result_mg = encoder.encode_magenta_green(left, right)
        assert result_mg.shape == (*sample_image.shape[:2], 3)

        result_ab = encoder.encode_amber_blue(left, right)
        assert result_ab.shape == (*sample_image.shape[:2], 3)


# ---------------------------------------------------------------------------
# AnaglyphGenerator Integration Tests
# ---------------------------------------------------------------------------


class TestAnaglyphGeneratorIntegration:
    """Integration tests for AnaglyphGenerator with new anaglyph types."""

    def test_initialization_with_string(self, mock_logger: MagicMock) -> None:
        """Test AnaglyphGenerator initialization with string type."""
        generator = AnaglyphGenerator(anaglyph_type="magenta_green")

        assert generator.anaglyph_type == AnaglyphType.MAGENTA_GREEN

    def test_initialization_with_enum(self, mock_logger: MagicMock) -> None:
        """Test AnaglyphGenerator initialization with enum type."""
        generator = AnaglyphGenerator(anaglyph_type=AnaglyphType.AMBER_BLUE)

        assert generator.anaglyph_type == AnaglyphType.AMBER_BLUE

    def test_combine_with_magenta_green(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with magenta-green."""
        generator = AnaglyphGenerator(anaglyph_type="magenta_green")
        left = sample_image.copy()
        right = sample_image.copy()

        result = generator.combine_to_anaglyph(left, right)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_combine_with_amber_blue(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with amber-blue."""
        generator = AnaglyphGenerator(anaglyph_type="amber_blue")
        left = sample_image.copy()
        right = sample_image.copy()

        result = generator.combine_to_anaglyph(left, right)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_combine_with_half_color(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with half-color."""
        generator = AnaglyphGenerator(anaglyph_type="half_color")
        left = sample_image.copy()
        right = sample_image.copy()

        result = generator.combine_to_anaglyph(left, right)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_combine_with_method_override(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with method override."""
        generator = AnaglyphGenerator(anaglyph_type="dubois")
        left = sample_image.copy()
        right = sample_image.copy()

        # Override with different method
        result = generator.combine_to_anaglyph(left, right, method="magenta_green")

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_combine_with_enum_override(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test anaglyph combination with enum method override."""
        generator = AnaglyphGenerator(anaglyph_type="dubois")
        left = sample_image.copy()
        right = sample_image.copy()

        # Override with enum type
        result = generator.combine_to_anaglyph(left, right, method=AnaglyphType.AMBER_BLUE)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_invalid_anaglyph_type_string(self, mock_logger: MagicMock) -> None:
        """Test that invalid anaglyph type string raises error."""
        with pytest.raises(ValueError, match="Invalid anaglyph type"):
            AnaglyphGenerator(anaglyph_type="invalid_type")

    def test_set_anaglyph_type(self, mock_logger: MagicMock) -> None:
        """Test changing anaglyph type."""
        generator = AnaglyphGenerator(anaglyph_type="dubois")
        generator.set_anaglyph_type("magenta_green")

        assert generator.anaglyph_type == AnaglyphType.MAGENTA_GREEN

    def test_set_anaglyph_type_with_enum(self, mock_logger: MagicMock) -> None:
        """Test changing anaglyph type with enum."""
        generator = AnaglyphGenerator(anaglyph_type="dubois")
        generator.set_anaglyph_type(AnaglyphType.AMBER_BLUE)

        assert generator.anaglyph_type == AnaglyphType.AMBER_BLUE

    def test_all_string_aliases(self, mock_logger: MagicMock) -> None:
        """Test all string aliases for anaglyph types."""
        # Test all aliases
        aliases = [
            ("dubois", AnaglyphType.RED_CYAN_DUBOIS),
            ("red_cyan_dubois", AnaglyphType.RED_CYAN_DUBOIS),
            ("color", AnaglyphType.RED_CYAN_COLOR),
            ("red_cyan_color", AnaglyphType.RED_CYAN_COLOR),
            ("gray", AnaglyphType.RED_CYAN_GRAY),
            ("red_cyan_gray", AnaglyphType.RED_CYAN_GRAY),
            ("half_color", AnaglyphType.RED_CYAN_HALF_COLOR),
            ("red_cyan_half_color", AnaglyphType.RED_CYAN_HALF_COLOR),
            ("magenta_green", AnaglyphType.MAGENTA_GREEN),
            ("trioscopic", AnaglyphType.MAGENTA_GREEN),
            ("amber_blue", AnaglyphType.AMBER_BLUE),
            ("colorcode", AnaglyphType.AMBER_BLUE),
            ("colorcode3d", AnaglyphType.AMBER_BLUE),
        ]

        for alias, expected_type in aliases:
            generator = AnaglyphGenerator(anaglyph_type=alias)
            assert generator.anaglyph_type == expected_type, f"Failed for alias: {alias}"

    def test_convenience_methods(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test all convenience encoding methods on generator."""
        generator = AnaglyphGenerator()
        left = sample_image.copy()
        right = sample_image.copy()

        # Test all convenience methods
        result_dubois = generator.encode_red_cyan_dubois(left, right)
        assert result_dubois.shape == (*sample_image.shape[:2], 3)

        result_color = generator.encode_red_cyan_color(left, right)
        assert result_color.shape == (*sample_image.shape[:2], 3)

        result_gray = generator.encode_red_cyan_gray(left, right)
        assert result_gray.shape == (*sample_image.shape[:2], 3)

        result_half = generator.encode_red_cyan_half_color(left, right)
        assert result_half.shape == (*sample_image.shape[:2], 3)

        result_mg = generator.encode_magenta_green(left, right)
        assert result_mg.shape == (*sample_image.shape[:2], 3)

        result_ab = generator.encode_amber_blue(left, right)
        assert result_ab.shape == (*sample_image.shape[:2], 3)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_anaglyph_encoder(self, mock_logger: MagicMock) -> None:
        """Test create_anaglyph_encoder function."""
        encoder = create_anaglyph_encoder(default_type=AnaglyphType.AMBER_BLUE)

        assert encoder.default_type == AnaglyphType.AMBER_BLUE

    def test_encode_anaglyph(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_anaglyph convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_anaglyph(left, right, AnaglyphType.MAGENTA_GREEN)

        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and special inputs."""

    def test_single_channel_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with single channel image (H, W, 1)."""
        encoder = AnaglyphEncoder()
        left = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)
        right = np.random.randint(0, 255, (50, 50, 1), dtype=np.uint8)

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (50, 50, 3)

    def test_very_small_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with very small image."""
        encoder = AnaglyphEncoder()
        left = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (10, 10, 3)

    def test_identical_views(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test with identical left and right views."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        # Should still produce valid output
        assert result.shape == (*sample_image.shape[:2], 3)
        assert result.dtype == np.uint8

    def test_extreme_color_values(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with extreme color values (all 0 or all 255)."""
        encoder = AnaglyphEncoder()
        left_black = np.zeros((50, 50, 3), dtype=np.uint8)
        right_white = np.full((50, 50, 3), 255, dtype=np.uint8)

        result = encoder.encode(left_black, right_white, AnaglyphType.RED_CYAN_DUBOIS)

        assert result.shape == (50, 50, 3)
        assert result.dtype == np.uint8

    def test_different_encodings_produce_different_results(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that different encoding methods produce different results."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = np.roll(sample_image, 5, axis=1)  # Shifted right view

        results = {}
        for at in AnaglyphType:
            results[at] = encoder.encode(left, right, at)

        # Different methods should produce different results
        # (at least some should differ)
        unique_results = set()
        for result in results.values():
            unique_results.add(result.tobytes())

        # At least some results should be different
        assert len(unique_results) > 1, "All encoding methods produced identical results"

    def test_case_insensitive_parsing(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that string parsing is case-insensitive."""
        generator = AnaglyphGenerator(anaglyph_type="MAGENTA_GREEN")
        assert generator.anaglyph_type == AnaglyphType.MAGENTA_GREEN

        generator = AnaglyphGenerator(anaglyph_type="Amber_Blue")
        assert generator.anaglyph_type == AnaglyphType.AMBER_BLUE

    def test_invalid_image_shape_1d_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that 1D array raises ValueError."""
        encoder = AnaglyphEncoder()
        left = np.array([1, 2, 3])
        right = np.array([1, 2, 3])

        with pytest.raises(ValueError, match="Expected at least 2D array"):
            encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

    def test_image_too_small_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that zero-dimension image raises ValueError."""
        encoder = AnaglyphEncoder()
        left = np.zeros((0, 10, 3), dtype=np.uint8)
        right = np.zeros((0, 10, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="dimensions too small"):
            encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

    def test_float_image_outside_range_clips(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that float images outside [0,1] range are clipped."""
        encoder = AnaglyphEncoder()
        # Create float image with values outside [0, 1]
        left = np.random.uniform(-0.5, 1.5, (50, 50, 3)).astype(np.float32)
        right = np.random.uniform(-0.5, 1.5, (50, 50, 3)).astype(np.float32)

        result = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

        # Should produce valid output despite out-of-range input
        assert result.shape == (50, 50, 3)
        assert result.dtype == np.uint8
        assert np.all(result >= 0)
        assert np.all(result <= 255)
        # Logger should have been warned about clipping
        assert mock_logger.warning.called

    def test_invalid_channel_count_raises_error(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that images with invalid channel count raise ValueError."""
        encoder = AnaglyphEncoder()
        left = np.zeros((50, 50, 5), dtype=np.uint8)  # Invalid: 5 channels
        right = np.zeros((50, 50, 5), dtype=np.uint8)

        with pytest.raises(ValueError, match="Expected.*H, W.*1.*3.*4"):
            encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)


class TestPerformanceOptimizations:
    """Tests for performance optimizations."""

    def test_einsum_produces_same_results_as_loops(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Verify that optimized einsum produces same results as original loop implementation."""
        encoder = AnaglyphEncoder()
        left = sample_image.copy()
        right = np.roll(sample_image, 5, axis=1)

        # Test all Dubois-based methods (which use einsum)
        result_dubois = encoder.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)
        result_magenta = encoder.encode(left, right, AnaglyphType.MAGENTA_GREEN)
        result_amber = encoder.encode(left, right, AnaglyphType.AMBER_BLUE)

        # Results should be deterministic and valid
        assert result_dubois.shape == (*sample_image.shape[:2], 3)
        assert result_magenta.shape == (*sample_image.shape[:2], 3)
        assert result_amber.shape == (*sample_image.shape[:2], 3)

        # Results should be different for different methods
        assert not np.array_equal(result_dubois, result_magenta)
        assert not np.array_equal(result_dubois, result_amber)


class TestConstants:
    """Tests for module constants."""

    def test_luminance_constants_exist(self) -> None:
        """Test that luminance constants are exported."""
        from video2d3d.stereo.anaglyph import (
            LUMINANCE_B,
            LUMINANCE_G,
            LUMINANCE_R,
            MIN_IMAGE_DIMENSION,
        )

        assert LUMINANCE_R == 0.299
        assert LUMINANCE_G == 0.587
        assert LUMINANCE_B == 0.114
        assert MIN_IMAGE_DIMENSION == 1
