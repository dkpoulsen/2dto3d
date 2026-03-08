"""VR-compatible output generation module.

This module provides functionality for generating VR-compatible video formats
including side-by-side 360° equirectangular projection and stereo VR video
for Oculus, Vive, and other VR headsets.

Supported formats:
- EQUIRECTANGULAR_SBS: Side-by-side 360° equirectangular (most common for VR)
- EQUIRECTANGULAR_TB: Top-bottom 360° equirectangular (over-under)
- VR180_SBS: VR180 side-by-side format (180° field of view)
- STEREO_VR: Standard stereo VR with configurable interpupillary distance

VR video requires:
- Equirectangular projection for 360° content
- Proper stereo separation for depth perception
- Specific resolutions (typically 3840x1080 for 4K VR, 4096x2048 for 4K+)
- Metadata for VR players to recognize the format

References:
- https://developers.google.com/vr/concepts/vrvideo
- https://ffmpeg.org/ffmpeg-filters.html#v360
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Final

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.logger import get_logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Standard VR resolutions (width per eye for SBS format)
VR_RESOLUTION_4K: Final[int] = 3840  # 4K VR SBS width (1920 per eye)
VR_RESOLUTION_4K_PLUS: Final[int] = 4096  # 4K+ VR SBS width
VR_RESOLUTION_8K: Final[int] = 7680  # 8K VR SBS width (3840 per eye)

# Standard VR heights
VR_HEIGHT_2K: Final[int] = 1080  # 2K height
VR_HEIGHT_4K: Final[int] = 2160  # 4K height (for full-frame equirectangular)
VR_HEIGHT_8K: Final[int] = 4320  # 8K height

# Default interpupillary distance in meters (average adult IPD)
DEFAULT_IPD: Final[float] = 0.063  # 63mm

# Default field of view for VR180
DEFAULT_VR180_FOV: Final[float] = 180.0

# Minimum image dimension
MIN_VR_DIMENSION: Final[int] = 256


def _get_vr_logger() -> Logger:
    """Get the VR module logger (lazy initialization)."""
    return get_logger("stereo.vr")


class VRProjectionType(Enum):
    """Available projection types for VR content."""

    EQUIRECTANGULAR = "equirectangular"  # Full 360° equirectangular projection
    VR180 = "vr180"  # 180° field of view (half equirectangular)
    PERSPECTIVE = "perspective"  # Standard perspective (non-360 stereo)


class VROutputFormat(Enum):
    """Available VR output formats."""

    EQUIRECTANGULAR_SBS = "equirectangular_sbs"  # Side-by-side 360° equirectangular
    EQUIRECTANGULAR_TB = "equirectangular_tb"  # Top-bottom 360° equirectangular
    VR180_SBS = "vr180_sbs"  # VR180 side-by-side
    STEREO_VR = "stereo_vr"  # Standard stereo VR (configurable)


class VREyeOrder(Enum):
    """Eye ordering for VR output."""

    LEFT_RIGHT = "left_right"  # Left eye first (most common)
    RIGHT_LEFT = "right_left"  # Right eye first (cross-eye)


@dataclass
class VRMetadata:
    """Metadata for VR video files.

    This metadata should be embedded in the video file for VR players
    to properly recognize and display the content.

    Attributes:
        projection: Projection type (equirectangular, vr180, etc.)
        stereo_mode: Stereo layout (left-right, top-bottom)
        fov_horizontal: Horizontal field of view in degrees
        fov_vertical: Vertical field of view in degrees
        ipd: Interpupillary distance in meters
        source_type: Original content type
    """

    projection: str = "equirectangular"
    stereo_mode: str = "left-right"
    fov_horizontal: float = 360.0
    fov_vertical: float = 180.0
    ipd: float = DEFAULT_IPD
    source_type: str = "monoscopic_to_stereoscopic"

    def to_ffmpeg_metadata(self) -> dict[str, str]:
        """Convert to FFmpeg metadata format.

        Returns:
            Dictionary of metadata key-value pairs for FFmpeg.
        """
        return {
            "spherical": "1",
            "stitched": "1",
            "projection": self.projection,
            "stereo_mode": self.stereo_mode,
            "fov_horizontal": str(self.fov_horizontal),
            "fov_vertical": str(self.fov_vertical),
        }

    def to_spatial_media_metadata(self) -> dict[str, str]:
        """Convert to Google Spatial Media metadata format.

        Returns:
            Dictionary for spatial media injection.
        """
        return {
            "Spherical": "true",
            "Stitched": "true",
            "StereoMode": self.stereo_mode,
            "ProjectionType": (
                "equirectangular"
                if self.projection == "equirectangular"
                else "half-equirectangular"
            ),
            "SourceCount": "1",
            "InitialViewHeadingDegrees": "0",
            "InitialViewPitchDegrees": "0",
            "InitialViewRollDegrees": "0",
            "FieldOfViewHorizontal": str(self.fov_horizontal),
            "FieldOfViewVertical": str(self.fov_vertical),
        }


@dataclass
class VREncoderConfig:
    """Configuration for VR encoding.

    Attributes:
        output_format: VR output format type.
        projection: Projection type for the content.
        target_width: Target output width (total for SBS, per eye for full-frame).
        target_height: Target output height.
        ipd: Interpupillary distance in meters (affects stereo separation).
        swap_eyes: Swap left and right eye positions.
        half_width: Use half-width mode (each eye at half resolution).
        embed_metadata: Embed VR metadata in output.
        vr_quality: Quality preset (affects interpolation).
    """

    output_format: VROutputFormat = VROutputFormat.EQUIRECTANGULAR_SBS
    projection: VRProjectionType = VRProjectionType.EQUIRECTANGULAR
    target_width: int = VR_RESOLUTION_4K
    target_height: int = VR_HEIGHT_2K
    ipd: float = DEFAULT_IPD
    swap_eyes: bool = False
    half_width: bool = True
    embed_metadata: bool = True
    vr_quality: str = "high"  # "fast", "balanced", "high"

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.target_width < MIN_VR_DIMENSION:
            raise ValueError(
                f"target_width must be at least {MIN_VR_DIMENSION}, got {self.target_width}"
            )
        if self.target_height < MIN_VR_DIMENSION:
            raise ValueError(
                f"target_height must be at least {MIN_VR_DIMENSION}, got {self.target_height}"
            )
        if self.ipd <= 0:
            raise ValueError(f"ipd must be positive, got {self.ipd}")

        valid_qualities = ["fast", "balanced", "high"]
        if self.vr_quality not in valid_qualities:
            raise ValueError(f"vr_quality must be one of {valid_qualities}, got {self.vr_quality}")


class VREncoderError(Exception):
    """Exception raised for VR encoding errors."""

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


class VREncoder:
    """Encode stereoscopic content for VR playback.

    This class transforms standard stereo pairs into VR-compatible formats
    including equirectangular projection for 360° content and various
    VR headset-optimized layouts.

    The encoder supports:
    - **Projection types**: Full equirectangular (360°), VR180 (180°)
    - **Output layouts**: Side-by-side, top-bottom
    - **Resolution scaling**: Automatic or manual target resolution
    - **Metadata embedding**: VR player compatibility metadata

    Example usage:
        ```python
        # Basic VR encoding (equirectangular SBS)
        encoder = VREncoder()
        vr_frame = encoder.encode(left_view, right_view)

        # With configuration
        config = VREncoderConfig(
            output_format=VROutputFormat.EQUIRECTANGULAR_SBS,
            target_width=4096,
            target_height=2048,
        )
        encoder = VREncoder(config=config)
        vr_frame = encoder.encode(left_view, right_view)

        # Get VR metadata for file embedding
        metadata = encoder.get_metadata()

        # VR180 format
        config = VREncoderConfig(
            output_format=VROutputFormat.VR180_SBS,
            projection=VRProjectionType.VR180,
        )
        encoder = VREncoder(config=config)
        vr180_frame = encoder.encode(left_view, right_view)
        ```
    """

    def __init__(
        self,
        config: VREncoderConfig | None = None,
        *,
        output_format: VROutputFormat = VROutputFormat.EQUIRECTANGULAR_SBS,
        target_width: int = VR_RESOLUTION_4K,
        target_height: int = VR_HEIGHT_2K,
        swap_eyes: bool = False,
        half_width: bool = True,
    ) -> None:
        """Initialize the VR encoder.

        Args:
            config: VREncoderConfig object. If provided, other args are ignored.
            output_format: VR output format type.
            target_width: Target output width in pixels.
            target_height: Target output height in pixels.
            swap_eyes: Swap left and right eye positions.
            half_width: Use half-width mode for each eye.
        """
        if config is not None:
            self.config = config
        else:
            self.config = VREncoderConfig(
                output_format=output_format,
                target_width=target_width,
                target_height=target_height,
                swap_eyes=swap_eyes,
                half_width=half_width,
            )

        self._logger = _get_vr_logger()
        self._logger.debug(
            f"VREncoder initialized: format={self.config.output_format.value}, "
            f"resolution={self.config.target_width}x{self.config.target_height}"
        )

        # Determine interpolation method based on quality setting
        self._interpolation = self._get_interpolation_method()

    def _get_interpolation_method(self) -> int:
        """Get OpenCV interpolation method based on quality setting.

        Returns:
            OpenCV interpolation constant.
        """
        quality_map = {
            "fast": cv2.INTER_NEAREST,
            "balanced": cv2.INTER_LINEAR,
            "high": cv2.INTER_LANCZOS4,
        }
        return quality_map.get(self.config.vr_quality, cv2.INTER_LINEAR)

    def encode(
        self,
        left: np.ndarray,
        right: np.ndarray,
        output_format: VROutputFormat | None = None,
    ) -> np.ndarray:
        """Encode stereo pair into VR-compatible format.

        Args:
            left: Left eye view as numpy array (H, W) or (H, W, C).
            right: Right eye view as numpy array (H, W) or (H, W, C).
            output_format: Override output format. If None, uses config default.

        Returns:
            VR-encoded frame as numpy array.

        Raises:
            VREncoderError: If encoding fails.
        """
        format_to_use = output_format or self.config.output_format

        self._logger.debug(f"Encoding VR frame: format={format_to_use.value}")

        try:
            # Validate inputs
            if left.shape != right.shape:
                raise VREncoderError(
                    f"Left and right views must have the same shape. "
                    f"Left: {left.shape}, Right: {right.shape}"
                )

            # Scale frames to target resolution
            left_scaled = self._scale_frame(left)
            right_scaled = self._scale_frame(right)

            # Swap eyes if configured
            if self.config.swap_eyes:
                left_scaled, right_scaled = right_scaled, left_scaled

            # Encode based on output format
            if format_to_use in (VROutputFormat.EQUIRECTANGULAR_SBS, VROutputFormat.STEREO_VR):
                result = self._encode_side_by_side(left_scaled, right_scaled)
            elif format_to_use == VROutputFormat.EQUIRECTANGULAR_TB:
                result = self._encode_top_bottom(left_scaled, right_scaled)
            elif format_to_use == VROutputFormat.VR180_SBS:
                result = self._encode_vr180(left_scaled, right_scaled)
            else:
                raise VREncoderError(f"Unsupported output format: {format_to_use}")

            return result

        except VREncoderError:
            raise
        except Exception as e:
            self._logger.error(f"VR encoding failed: {e}")
            raise VREncoderError(
                f"VR encoding failed: {e}",
                operation="encode",
                original_exception=e,
            ) from e

    def _scale_frame(self, frame: np.ndarray) -> np.ndarray:
        """Scale frame to target resolution.

        Args:
            frame: Input frame to scale.

        Returns:
            Scaled frame at target resolution.
        """
        h, w = frame.shape[:2]

        # Calculate target dimensions for this eye
        if self.config.half_width:
            # Half-width mode: each eye is half the total width
            target_w = self.config.target_width // 2
        else:
            # Full-width mode: each eye at full width
            target_w = self.config.target_width

        target_h = self.config.target_height

        # Skip if already at target resolution
        if h == target_h and w == target_w:
            return frame

        return cv2.resize(frame, (target_w, target_h), interpolation=self._interpolation)

    def _encode_side_by_side(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode as side-by-side VR format.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Side-by-side VR frame.
        """
        return np.concatenate([left, right], axis=1)

    def _encode_top_bottom(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode as top-bottom VR format.

        Args:
            left: Left eye view (top).
            right: Right eye view (bottom).

        Returns:
            Top-bottom VR frame.
        """
        return np.concatenate([left, right], axis=0)

    def _encode_vr180(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode as VR180 format (180° field of view).

        VR180 uses half equirectangular projection, showing 180°
        horizontal field of view instead of full 360°.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            VR180 side-by-side frame.
        """
        # VR180 is essentially side-by-side with half the horizontal coverage
        # The input frames should already be in equirectangular format
        # We just combine them in SBS layout
        return self._encode_side_by_side(left, right)

    def get_metadata(self) -> VRMetadata:
        """Get VR metadata for the current configuration.

        Returns:
            VRMetadata instance configured for this encoder.
        """
        # Determine FOV based on projection type
        if self.config.projection == VRProjectionType.EQUIRECTANGULAR:
            fov_h = 360.0
            fov_v = 180.0
            projection = "equirectangular"
        elif self.config.projection == VRProjectionType.VR180:
            fov_h = 180.0
            fov_v = 180.0
            projection = "half-equirectangular"
        else:
            fov_h = 360.0
            fov_v = 180.0
            projection = "equirectangular"

        # Determine stereo mode
        if self.config.output_format in (
            VROutputFormat.EQUIRECTANGULAR_SBS,
            VROutputFormat.VR180_SBS,
            VROutputFormat.STEREO_VR,
        ):
            stereo_mode = "left-right" if not self.config.swap_eyes else "right-left"
        else:
            stereo_mode = "top-bottom" if not self.config.swap_eyes else "bottom-top"

        return VRMetadata(
            projection=projection,
            stereo_mode=stereo_mode,
            fov_horizontal=fov_h,
            fov_vertical=fov_v,
            ipd=self.config.ipd,
        )

    def get_output_dimensions(self) -> tuple[int, int]:
        """Get the output frame dimensions.

        Returns:
            Tuple of (width, height) for the output frame.
        """
        if self.config.half_width:
            # Half-width mode: output width = target_width (each eye is half)
            return (self.config.target_width, self.config.target_height)
        else:
            # Full-width mode: output width = 2 * target_width
            return (self.config.target_width * 2, self.config.target_height)

    def encode_equirectangular_sbs(
        self,
        left: np.ndarray,
        right: np.ndarray,
    ) -> np.ndarray:
        """Encode as side-by-side 360° equirectangular format.

        This is the most common format for VR video players.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Equirectangular SBS VR frame.
        """
        return self.encode(left, right, output_format=VROutputFormat.EQUIRECTANGULAR_SBS)

    def encode_equirectangular_tb(
        self,
        left: np.ndarray,
        right: np.ndarray,
    ) -> np.ndarray:
        """Encode as top-bottom 360° equirectangular format.

        Args:
            left: Left eye view (top).
            right: Right eye view (bottom).

        Returns:
            Equirectangular top-bottom VR frame.
        """
        return self.encode(left, right, output_format=VROutputFormat.EQUIRECTANGULAR_TB)

    def encode_vr180(
        self,
        left: np.ndarray,
        right: np.ndarray,
    ) -> np.ndarray:
        """Encode as VR180 side-by-side format.

        VR180 shows 180° horizontal field of view, which is
        more manageable for content creation.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            VR180 SBS frame.
        """
        return self.encode(left, right, output_format=VROutputFormat.VR180_SBS)


class VRStereoGenerator:
    """Generate VR stereo content from 2D images with depth maps.

    This class combines depth-based stereo generation with VR output
    formatting to create VR-ready stereoscopic content.

    Example usage:
        ```python
        from video2d3d.stereo import DIBREngine

        # Generate VR stereo content
        vr_gen = VRStereoGenerator()
        left, right = vr_gen.generate_stereo(frame, depth_map)
        vr_frame = vr_gen.encode_for_vr(left, right)
        ```
    """

    def __init__(
        self,
        vr_config: VREncoderConfig | None = None,
        baseline: float = 0.05,
        convergence: float = 0.5,
    ) -> None:
        """Initialize the VR stereo generator.

        Args:
            vr_config: Configuration for VR encoding.
            baseline: Stereo baseline (eye separation).
            convergence: Convergence distance (0-1).
        """
        self.vr_config = vr_config or VREncoderConfig()
        self.baseline = baseline
        self.convergence = convergence
        self._encoder = VREncoder(config=self.vr_config)
        self._logger = _get_vr_logger()

        # Import DIBR engine lazily to avoid circular imports
        from video2d3d.stereo.dibr import DIBREngine

        self._dibr = DIBREngine(baseline=baseline, convergence=convergence)

    def generate_stereo(
        self,
        frame: np.ndarray,
        depth_map: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate left and right eye views using DIBR.

        Args:
            frame: Input 2D frame.
            depth_map: Corresponding depth map.

        Returns:
            Tuple of (left_view, right_view).
        """
        return self._dibr.render(frame, depth_map)

    def encode_for_vr(
        self,
        left: np.ndarray,
        right: np.ndarray,
    ) -> np.ndarray:
        """Encode stereo views for VR playback.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            VR-encoded frame.
        """
        return self._encoder.encode(left, right)

    def process_to_vr(
        self,
        frame: np.ndarray,
        depth_map: np.ndarray,
    ) -> np.ndarray:
        """Process 2D frame with depth map directly to VR format.

        This combines stereo generation and VR encoding in one step.

        Args:
            frame: Input 2D frame.
            depth_map: Corresponding depth map.

        Returns:
            VR-encoded stereoscopic frame.
        """
        left, right = self.generate_stereo(frame, depth_map)
        return self.encode_for_vr(left, right)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_vr_encoder(
    output_format: VROutputFormat = VROutputFormat.EQUIRECTANGULAR_SBS,
    target_width: int = VR_RESOLUTION_4K,
    target_height: int = VR_HEIGHT_2K,
    swap_eyes: bool = False,
    half_width: bool = True,
    ipd: float = DEFAULT_IPD,
) -> VREncoder:
    """Create a VR encoder with the specified configuration.

    Args:
        output_format: VR output format type.
        target_width: Target output width in pixels.
        target_height: Target output height in pixels.
        swap_eyes: Swap left and right eye positions.
        half_width: Use half-width mode for each eye.
        ipd: Interpupillary distance in meters.

    Returns:
        Configured VREncoder instance.
    """
    config = VREncoderConfig(
        output_format=output_format,
        target_width=target_width,
        target_height=target_height,
        swap_eyes=swap_eyes,
        half_width=half_width,
        ipd=ipd,
    )
    return VREncoder(config=config)


def encode_vr_sbs(
    left: np.ndarray,
    right: np.ndarray,
    target_width: int = VR_RESOLUTION_4K,
    target_height: int = VR_HEIGHT_2K,
    swap_eyes: bool = False,
    half_width: bool = True,
) -> np.ndarray:
    """Encode stereo pair as VR side-by-side equirectangular (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        target_width: Target output width in pixels.
        target_height: Target output height in pixels.
        swap_eyes: Swap left and right eye positions.
        half_width: Use half-width mode for each eye.

    Returns:
        VR-encoded side-by-side frame.
    """
    encoder = create_vr_encoder(
        output_format=VROutputFormat.EQUIRECTANGULAR_SBS,
        target_width=target_width,
        target_height=target_height,
        swap_eyes=swap_eyes,
        half_width=half_width,
    )
    return encoder.encode(left, right)


def encode_vr_top_bottom(
    left: np.ndarray,
    right: np.ndarray,
    target_width: int = VR_RESOLUTION_4K,
    target_height: int = VR_HEIGHT_2K,
    swap_eyes: bool = False,
    half_width: bool = True,
) -> np.ndarray:
    """Encode stereo pair as VR top-bottom equirectangular (convenience function).

    Args:
        left: Left eye view (top).
        right: Right eye view (bottom).
        target_width: Target output width in pixels.
        target_height: Target output height in pixels.
        swap_eyes: Swap left and right eye positions.
        half_width: Use half-width mode for each eye.

    Returns:
        VR-encoded top-bottom frame.
    """
    encoder = create_vr_encoder(
        output_format=VROutputFormat.EQUIRECTANGULAR_TB,
        target_width=target_width,
        target_height=target_height,
        swap_eyes=swap_eyes,
        half_width=half_width,
    )
    return encoder.encode(left, right)


def encode_vr180(
    left: np.ndarray,
    right: np.ndarray,
    target_width: int = VR_RESOLUTION_4K,
    target_height: int = VR_HEIGHT_2K,
    swap_eyes: bool = False,
    half_width: bool = True,
) -> np.ndarray:
    """Encode stereo pair as VR180 format (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        target_width: Target output width in pixels.
        target_height: Target output height in pixels.
        swap_eyes: Swap left and right eye positions.
        half_width: Use half-width mode for each eye.

    Returns:
        VR180-encoded frame.
    """
    encoder = create_vr_encoder(
        output_format=VROutputFormat.VR180_SBS,
        target_width=target_width,
        target_height=target_height,
        swap_eyes=swap_eyes,
        half_width=half_width,
    )
    return encoder.encode(left, right)


def get_vr_metadata_for_format(
    output_format: VROutputFormat,
    projection: VRProjectionType = VRProjectionType.EQUIRECTANGULAR,
    ipd: float = DEFAULT_IPD,
) -> VRMetadata:
    """Get VR metadata for a specific output format.

    Args:
        output_format: VR output format type.
        projection: Projection type for the content.
        ipd: Interpupillary distance in meters.

    Returns:
        VRMetadata configured for the specified format.
    """
    config = VREncoderConfig(
        output_format=output_format,
        projection=projection,
        ipd=ipd,
    )
    encoder = VREncoder(config=config)
    return encoder.get_metadata()


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "VREncoder",
    "VREncoderConfig",
    "VREncoderError",
    "VRMetadata",
    "VRStereoGenerator",
    # Enums
    "VROutputFormat",
    "VRProjectionType",
    "VREyeOrder",
    # Functions
    "create_vr_encoder",
    "encode_vr_sbs",
    "encode_vr_top_bottom",
    "encode_vr180",
    "get_vr_metadata_for_format",
    # Constants
    "VR_RESOLUTION_4K",
    "VR_RESOLUTION_4K_PLUS",
    "VR_RESOLUTION_8K",
    "VR_HEIGHT_2K",
    "VR_HEIGHT_4K",
    "VR_HEIGHT_8K",
    "DEFAULT_IPD",
    "DEFAULT_VR180_FOV",
    "MIN_VR_DIMENSION",
    # Logger
    "_get_vr_logger",
]
