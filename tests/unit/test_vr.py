"""Unit tests for VR output generation module.

Tests cover:
- VROutputFormat and VRProjectionType enums
- VREncoder and VREncoderConfig classes
- VRMetadata class
- VRStereoGenerator class
- All VR encoding methods (SBS, top-bottom, VR180)
- Input validation and error handling
- Convenience functions

Note: These tests rely on mocks set up in tests/conftest.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Import the module under test
from video2d3d.stereo.vr import (
    DEFAULT_IPD,
    VR_HEIGHT_2K,
    VR_HEIGHT_4K,
    VR_RESOLUTION_4K,
    VR_RESOLUTION_4K_PLUS,
    VR_RESOLUTION_8K,
    VREncoder,
    VREncoderConfig,
    VREncoderError,
    VREyeOrder,
    VRMetadata,
    VROutputFormat,
    VRProjectionType,
    VRStereoGenerator,
    create_vr_encoder,
    encode_vr180,
    encode_vr_sbs,
    encode_vr_top_bottom,
    get_vr_metadata_for_format,
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
    """Create a sample depth map for testing."""
    np.random.seed(42)
    return np.random.random((100, 100)).astype(np.float32)


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.stereo.vr.get_logger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


# ---------------------------------------------------------------------------
# Enum Tests
# ---------------------------------------------------------------------------


class TestVREnums:
    """Tests for VR enums."""

    def test_output_format_values(self) -> None:
        """Test VROutputFormat enum values."""
        assert VROutputFormat.EQUIRECTANGULAR_SBS.value == "equirectangular_sbs"
        assert VROutputFormat.EQUIRECTANGULAR_TB.value == "equirectangular_tb"
        assert VROutputFormat.VR180_SBS.value == "vr180_sbs"
        assert VROutputFormat.STEREO_VR.value == "stereo_vr"

    def test_projection_type_values(self) -> None:
        """Test VRProjectionType enum values."""
        assert VRProjectionType.EQUIRECTANGULAR.value == "equirectangular"
        assert VRProjectionType.VR180.value == "vr180"
        assert VRProjectionType.PERSPECTIVE.value == "perspective"

    def test_eye_order_values(self) -> None:
        """Test VREyeOrder enum values."""
        assert VREyeOrder.LEFT_RIGHT.value == "left_right"
        assert VREyeOrder.RIGHT_LEFT.value == "right_left"


# ---------------------------------------------------------------------------
# VRMetadata Tests
# ---------------------------------------------------------------------------


class TestVRMetadata:
    """Tests for VRMetadata class."""

    def test_default_metadata(self) -> None:
        """Test default metadata values."""
        metadata = VRMetadata()

        assert metadata.projection == "equirectangular"
        assert metadata.stereo_mode == "left-right"
        assert metadata.fov_horizontal == 360.0
        assert metadata.fov_vertical == 180.0
        assert metadata.ipd == DEFAULT_IPD
        assert metadata.source_type == "monoscopic_to_stereoscopic"

    def test_custom_metadata(self) -> None:
        """Test custom metadata values."""
        metadata = VRMetadata(
            projection="half-equirectangular",
            stereo_mode="top-bottom",
            fov_horizontal=180.0,
            fov_vertical=180.0,
            ipd=0.065,
        )

        assert metadata.projection == "half-equirectangular"
        assert metadata.stereo_mode == "top-bottom"
        assert metadata.fov_horizontal == 180.0
        assert metadata.fov_vertical == 180.0
        assert metadata.ipd == 0.065

    def test_to_ffmpeg_metadata(self) -> None:
        """Test conversion to FFmpeg metadata format."""
        metadata = VRMetadata()
        ffmpeg_meta = metadata.to_ffmpeg_metadata()

        assert "spherical" in ffmpeg_meta
        assert ffmpeg_meta["spherical"] == "1"
        assert "projection" in ffmpeg_meta
        assert "stereo_mode" in ffmpeg_meta

    def test_to_spatial_media_metadata(self) -> None:
        """Test conversion to Google Spatial Media format."""
        metadata = VRMetadata()
        spatial_meta = metadata.to_spatial_media_metadata()

        assert "Spherical" in spatial_meta
        assert spatial_meta["Spherical"] == "true"
        assert "StereoMode" in spatial_meta
        assert "ProjectionType" in spatial_meta


# ---------------------------------------------------------------------------
# VREncoderConfig Tests
# ---------------------------------------------------------------------------


class TestVREncoderConfig:
    """Tests for VREncoderConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = VREncoderConfig()

        assert config.output_format == VROutputFormat.EQUIRECTANGULAR_SBS
        assert config.projection == VRProjectionType.EQUIRECTANGULAR
        assert config.target_width == VR_RESOLUTION_4K
        assert config.target_height == VR_HEIGHT_2K
        assert config.ipd == DEFAULT_IPD
        assert config.swap_eyes is False
        assert config.half_width is True
        assert config.embed_metadata is True
        assert config.vr_quality == "high"

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = VREncoderConfig(
            output_format=VROutputFormat.VR180_SBS,
            projection=VRProjectionType.VR180,
            target_width=VR_RESOLUTION_8K,
            target_height=VR_HEIGHT_4K,
            swap_eyes=True,
            half_width=False,
            vr_quality="fast",
        )

        assert config.output_format == VROutputFormat.VR180_SBS
        assert config.projection == VRProjectionType.VR180
        assert config.target_width == VR_RESOLUTION_8K
        assert config.target_height == VR_HEIGHT_4K
        assert config.swap_eyes is True
        assert config.half_width is False
        assert config.vr_quality == "fast"

    def test_invalid_width_raises_error(self) -> None:
        """Test that invalid width raises ValueError."""
        with pytest.raises(ValueError, match="target_width"):
            VREncoderConfig(target_width=100)

    def test_invalid_height_raises_error(self) -> None:
        """Test that invalid height raises ValueError."""
        with pytest.raises(ValueError, match="target_height"):
            VREncoderConfig(target_height=100)

    def test_invalid_ipd_raises_error(self) -> None:
        """Test that invalid IPD raises ValueError."""
        with pytest.raises(ValueError, match="ipd"):
            VREncoderConfig(ipd=0)

    def test_invalid_quality_raises_error(self) -> None:
        """Test that invalid quality raises ValueError."""
        with pytest.raises(ValueError, match="vr_quality"):
            VREncoderConfig(vr_quality="invalid")


# ---------------------------------------------------------------------------
# VREncoder Tests
# ---------------------------------------------------------------------------


class TestVREncoder:
    """Tests for VREncoder class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default encoder initialization."""
        encoder = VREncoder()

        assert encoder.config.output_format == VROutputFormat.EQUIRECTANGULAR_SBS
        assert encoder.config.half_width is True

    def test_initialization_custom(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom config."""
        config = VREncoderConfig(
            output_format=VROutputFormat.EQUIRECTANGULAR_TB,
            swap_eyes=True,
        )
        encoder = VREncoder(config=config)

        assert encoder.config.output_format == VROutputFormat.EQUIRECTANGULAR_TB
        assert encoder.config.swap_eyes is True

    def test_encode_sbs(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encoding in side-by-side format."""
        encoder = VREncoder(
            output_format=VROutputFormat.EQUIRECTANGULAR_SBS,
            target_width=200,
            target_height=100,
            half_width=True,
        )
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Half-width mode: output should be 200 wide (100 per eye)
        assert result.shape == (100, 200, 3)
        assert result.dtype == np.uint8

    def test_encode_top_bottom(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encoding in top-bottom format."""
        encoder = VREncoder(
            output_format=VROutputFormat.EQUIRECTANGULAR_TB,
            target_width=100,
            target_height=200,
            half_width=True,
        )
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Top-bottom: height should be 2 * target_height
        assert result.shape == (200, 100, 3)
        assert result.dtype == np.uint8

    def test_encode_vr180(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encoding in VR180 format."""
        encoder = VREncoder(
            output_format=VROutputFormat.VR180_SBS,
            target_width=200,
            target_height=100,
            half_width=True,
        )
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        assert result.shape == (100, 200, 3)
        assert result.dtype == np.uint8

    def test_encode_swap_eyes(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that swap_eyes correctly swaps left and right views."""
        encoder = VREncoder(
            target_width=200,
            target_height=100,
            swap_eyes=True,
            half_width=True,
        )
        # Create distinct left and right views
        left = np.zeros((100, 100, 3), dtype=np.uint8)
        left[:, :, 0] = 255  # Red
        right = np.zeros((100, 100, 3), dtype=np.uint8)
        right[:, :, 2] = 255  # Blue

        result = encoder.encode(left, right)

        # With swap_eyes=True, right (blue) should be on left side
        assert result[50, 25, 2] == 255  # Blue channel in left half
        # Left (red) should be on right side
        assert result[50, 150, 0] == 255  # Red channel in right half

    def test_encode_dimension_mismatch_raises_error(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test that mismatched dimensions raise VREncoderError."""
        encoder = VREncoder()
        left = sample_image.copy()
        wrong_right = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(VREncoderError, match="same shape"):
            encoder.encode(left, wrong_right)

    def test_get_metadata(self, mock_logger: MagicMock) -> None:
        """Test get_metadata returns correct VRMetadata."""
        encoder = VREncoder()
        metadata = encoder.get_metadata()

        assert isinstance(metadata, VRMetadata)
        assert metadata.projection == "equirectangular"
        assert metadata.stereo_mode == "left-right"

    def test_get_output_dimensions(self, mock_logger: MagicMock) -> None:
        """Test get_output_dimensions returns correct dimensions."""
        encoder = VREncoder(
            target_width=3840,
            target_height=1080,
            half_width=True,
        )
        width, height = encoder.get_output_dimensions()

        assert width == 3840  # Total width in half-width mode
        assert height == 1080

    def test_full_width_mode(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test full-width mode (each eye at full resolution)."""
        encoder = VREncoder(
            target_width=100,
            target_height=100,
            half_width=False,
        )
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Full-width mode: output should be 2 * target_width
        assert result.shape == (100, 200, 3)

    def test_encode_equirectangular_sbs_method(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_equirectangular_sbs convenience method."""
        encoder = VREncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_equirectangular_sbs(left, right)

        assert result is not None

    def test_encode_equirectangular_tb_method(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_equirectangular_tb convenience method."""
        encoder = VREncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_equirectangular_tb(left, right)

        assert result is not None

    def test_encode_vr180_method(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_vr180 convenience method."""
        encoder = VREncoder()
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode_vr180(left, right)

        assert result is not None


# ---------------------------------------------------------------------------
# VRStereoGenerator Tests
# ---------------------------------------------------------------------------


class TestVRStereoGenerator:
    """Tests for VRStereoGenerator class."""

    def test_initialization(self, mock_logger: MagicMock) -> None:
        """Test VRStereoGenerator initialization."""
        generator = VRStereoGenerator()

        assert generator.vr_config is not None
        assert generator.baseline == 0.05
        assert generator.convergence == 0.5

    def test_generate_stereo(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test generate_stereo produces left and right views."""
        generator = VRStereoGenerator()

        left, right = generator.generate_stereo(sample_image, sample_depth_map)

        assert left.shape == sample_image.shape
        assert right.shape == sample_image.shape

    def test_encode_for_vr(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_for_vr produces VR output."""
        generator = VRStereoGenerator()
        left = sample_image.copy()
        right = sample_image.copy()

        result = generator.encode_for_vr(left, right)

        assert result is not None

    def test_process_to_vr(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test process_to_vr combines stereo generation and VR encoding."""
        generator = VRStereoGenerator()

        result = generator.process_to_vr(sample_image, sample_depth_map)

        assert result is not None


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_vr_encoder(self, mock_logger: MagicMock) -> None:
        """Test create_vr_encoder function."""
        encoder = create_vr_encoder(
            output_format=VROutputFormat.EQUIRECTANGULAR_TB,
            target_width=4096,
            target_height=2048,
            swap_eyes=True,
            half_width=False,
        )

        assert encoder.config.output_format == VROutputFormat.EQUIRECTANGULAR_TB
        assert encoder.config.target_width == 4096
        assert encoder.config.target_height == 2048
        assert encoder.config.swap_eyes is True
        assert encoder.config.half_width is False

    def test_encode_vr_sbs(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_vr_sbs convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_vr_sbs(left, right)

        assert result is not None

    def test_encode_vr_top_bottom(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_vr_top_bottom convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_vr_top_bottom(left, right)

        assert result is not None

    def test_encode_vr180(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test encode_vr180 convenience function."""
        left = sample_image.copy()
        right = sample_image.copy()

        result = encode_vr180(left, right)

        assert result is not None

    def test_get_vr_metadata_for_format(self) -> None:
        """Test get_vr_metadata_for_format function."""
        metadata = get_vr_metadata_for_format(
            VROutputFormat.VR180_SBS,
            projection=VRProjectionType.VR180,
        )

        assert isinstance(metadata, VRMetadata)
        assert metadata.projection == "half-equirectangular"
        assert metadata.fov_horizontal == 180.0


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Tests for module constants."""

    def test_resolution_constants(self) -> None:
        """Test that resolution constants have expected values."""
        assert VR_RESOLUTION_4K == 3840
        assert VR_RESOLUTION_4K_PLUS == 4096
        assert VR_RESOLUTION_8K == 7680
        assert VR_HEIGHT_2K == 1080
        assert VR_HEIGHT_4K == 2160

    def test_ipd_constant(self) -> None:
        """Test that default IPD is set correctly."""
        assert DEFAULT_IPD == 0.063  # 63mm


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and special inputs."""

    def test_grayscale_input(
        self,
        mock_logger: MagicMock,
        sample_grayscale_image: np.ndarray,
    ) -> None:
        """Test encoding with grayscale input images."""
        encoder = VREncoder(
            target_width=200,
            target_height=100,
            half_width=True,
        )
        left = sample_grayscale_image.copy()
        right = sample_grayscale_image.copy()

        result = encoder.encode(left, right)

        # Output should maintain grayscale (2D)
        assert result.shape == (100, 200)

    def test_large_image(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with large image (4K)."""
        encoder = VREncoder(
            target_width=3840,
            target_height=1080,
            half_width=True,
        )
        # Create 2K input images
        left = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        right = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        result = encoder.encode(left, right)

        assert result.shape == (1080, 3840, 3)

    def test_identical_views(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
    ) -> None:
        """Test with identical left and right views."""
        encoder = VREncoder(
            target_width=200,
            target_height=100,
            half_width=True,
        )
        left = sample_image.copy()
        right = sample_image.copy()

        result = encoder.encode(left, right)

        # Should still produce valid output
        assert result.shape == (100, 200, 3)

    def test_extreme_color_values(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test with extreme color values (all 0 or all 255)."""
        encoder = VREncoder(
            target_width=200,
            target_height=100,
            half_width=True,
        )
        left_black = np.zeros((100, 100, 3), dtype=np.uint8)
        right_white = np.full((100, 100, 3), 255, dtype=np.uint8)

        result = encoder.encode(left_black, right_white)

        assert result.shape == (100, 200, 3)

    def test_float_input(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test encoding with float input images."""
        encoder = VREncoder(
            target_width=200,
            target_height=100,
            half_width=True,
        )
        left = np.random.random((100, 100, 3)).astype(np.float32)
        right = np.random.random((100, 100, 3)).astype(np.float32)

        result = encoder.encode(left, right)

        assert result.shape == (100, 200, 3)
        # Float input should preserve dtype
        assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests with stereo module."""

    def test_import_from_stereo_module(self) -> None:
        """Test that VR encoder can be imported from stereo module."""
        from video2d3d.stereo import (
            VREncoder,
            VROutputFormat,
            encode_vr_sbs,
        )

        assert VREncoder is not None
        assert VROutputFormat is not None
        assert encode_vr_sbs is not None

    def test_vr_encoder_with_dibr(
        self,
        mock_logger: MagicMock,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test VR encoder with views from DIBR engine."""
        # Generate stereo views using DIBR
        from video2d3d.stereo.dibr import DIBREngine

        dibr = DIBREngine()
        left, right = dibr.render(sample_image, sample_depth_map)

        # Encode for VR
        encoder = VREncoder(
            target_width=200,
            target_height=100,
            half_width=True,
        )
        result = encoder.encode(left, right)

        assert result.shape == (100, 200, 3)
