"""Stereoscopic video generation.

This module provides functionality for generating stereoscopic 3D video
from 2D video and depth maps. Supports multiple output formats including
side-by-side, anaglyph, interlaced, and VR formats.

The module uses Depth-Image-Based Rendering (DIBR) to generate left and
right eye views by shifting pixels horizontally based on depth values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Tuple

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.stereo.dibr import (
    DIBRConfig,
    DIBREngine,
    DIBRError,
    HoleFillingMethod,
    DepthInterpretation,
    create_dibr_engine,
    render_stereo_pair,
)
from video2d3d.stereo.anaglyph import (
    AnaglyphEncoder,
    AnaglyphType,
    encode_anaglyph,
)
from video2d3d.stereo.side_by_side import (
    SideBySideEncoder,
    SideBySideLayout,
    encode_side_by_side,
)
from video2d3d.stereo.checkerboard import (
    CheckerboardEncoder,
    CheckerboardPattern,
    encode_checkerboard,
)

from video2d3d.utils.logger import (
    get_logger,
    log_exception,
    log_video_processing,
)


def _get_stereo_logger() -> "Logger":
    """Get the stereo module logger (lazy initialization)."""
    return get_logger("stereo")


StereoFormat = Literal["side_by_side", "anaglyph", "interlaced", "vr", "checkerboard"]


class StereoGenerator:
    """Generate stereoscopic 3D video from 2D video and depth maps.

    This class uses DIBR (Depth-Image-Based Rendering) to generate left
    and right eye views from a 2D image and its corresponding depth map.

    The stereo effect is controlled by:
    - baseline: Eye separation distance (higher = stronger 3D effect)
    - convergence: Depth at which objects appear at screen level
    - focal_length: Virtual camera focal length

    Example usage:
        ```python
        # Basic usage
        generator = StereoGenerator()
        left, right = generator.generate_stereo_pair(frame, depth_map)

        # With custom parameters
        generator = StereoGenerator(
            baseline=0.08,
            convergence=0.4,
            hole_filling="inpaint"
        )
        left, right = generator.generate_stereo_pair(frame, depth_map)

        # Configure DIBR engine directly
        config = DIBRConfig(baseline=0.1, convergence=0.3)
        generator = StereoGenerator(dibr_config=config)
        ```
    """

    def __init__(
        self,
        format: StereoFormat = "side_by_side",
        baseline: float = 0.05,
        convergence: float = 0.5,
        focal_length: float = 1.0,
        hole_filling: str = "nearest",
        dibr_config: Optional[DIBRConfig] = None,
    ) -> None:
        """Initialize the stereo generator.

        Args:
            format: Output 3D format.
            baseline: Stereo baseline (eye separation). Higher values
                create stronger 3D effect but may cause eye strain.
            convergence: Convergence distance (normalized 0-1). Objects
                at this depth appear at screen level.
            focal_length: Virtual camera focal length.
            hole_filling: Method to fill disocclusion holes.
                Options: 'none', 'nearest', 'linear', 'inpaint'.
            dibr_config: DIBRConfig object. If provided, other DIBR
                parameters are ignored.
        """
        self.format = format
        self.baseline = baseline
        self.convergence = convergence
        self.focal_length = focal_length

        # Initialize DIBR engine
        if dibr_config is not None:
            self._dibr_config = dibr_config
        else:
            self._dibr_config = DIBRConfig(
                baseline=baseline,
                focal_length=focal_length,
                convergence=convergence,
                hole_filling=hole_filling,
            )

        self._dibr_engine = DIBREngine(config=self._dibr_config)

        _get_stereo_logger().info(
            f"StereoGenerator initialized: format={format}, baseline={baseline}, "
            f"convergence={convergence}, hole_filling={hole_filling}"
        )

    def generate_stereo_pair(
        self,
        frame: np.ndarray,
        depth_map: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate left and right eye views from a frame and depth map.

        This method uses DIBR to shift pixels horizontally based on depth
        values, creating stereoscopic 3D views.

        Args:
            frame: Input 2D frame as numpy array (H, W) or (H, W, C).
                Expected dtype: uint8 for images, float32 for normalized.
            depth_map: Corresponding depth map as numpy array (H, W).
                Values should be normalized to [0, 1] range.
                By default (inverse interpretation): 0 = close, 1 = far.

        Returns:
            Tuple of (left_eye, right_eye) views as numpy arrays.

        Raises:
            DIBRError: If stereo pair generation fails.
            ValueError: If input dimensions don't match.
        """
        logger = _get_stereo_logger()
        logger.debug(f"Generating stereo pair for {self.format} format")

        try:
            # Use DIBR engine to generate stereo pair
            left_view, right_view = self._dibr_engine.render(frame, depth_map)

            logger.debug(
                f"Stereo pair generated: left shape={left_view.shape}, "
                f"right shape={right_view.shape}"
            )

            return left_view, right_view

        except DIBRError:
            raise
        except Exception as e:
            log_exception(
                "Stereo pair generation failed",
                exception=e,
                format=self.format,
            )
            raise DIBRError(
                f"Stereo pair generation failed: {e}",
                operation="generate_stereo_pair",
                original_exception=e,
            ) from e

    def process_video(
        self,
        frames: list,
        depth_maps: list,
        output_path: str,
        total_frames: int = 0,
    ) -> None:
        """Process video frames to generate stereoscopic output.

        Args:
            frames: List of input frames.
            depth_maps: List of corresponding depth maps.
            output_path: Path to save the output video.
            total_frames: Total number of frames (for progress logging).
        """
        logger = _get_stereo_logger()
        logger.info(f"Processing {len(frames)} frames for stereo output: {output_path}")

        if total_frames == 0:
            total_frames = len(frames)

        try:
            for i, (frame, depth) in enumerate(zip(frames, depth_maps)):
                # Generate stereo pair
                left, right = self.generate_stereo_pair(frame, depth)

                # Log progress periodically
                if (i + 1) % 10 == 0 or i == 0:
                    log_video_processing(
                        input_file="video_frames",
                        output_file=output_path,
                        frames_processed=i + 1,
                        total_frames=total_frames,
                        format=self.format,
                    )

            # TODO: Implement video writing
            logger.warning("Video processing not yet implemented")

        except Exception as e:
            log_exception(
                "Stereo video processing failed",
                exception=e,
                output_path=output_path,
            )
            raise

    def set_format(self, format: StereoFormat) -> None:
        """Change the output format.

        Args:
            format: New output format.
        """
        _get_stereo_logger().info(f"Changing stereo format: {self.format} -> {format}")
        self.format = format

    def set_baseline(self, baseline: float) -> None:
        """Update the baseline (eye separation).

        Args:
            baseline: New baseline value.
        """
        logger = _get_stereo_logger()
        logger.info(f"Updating baseline: {self.baseline} -> {baseline}")
        self.baseline = baseline
        self._dibr_config.baseline = baseline
        self._dibr_engine = DIBREngine(config=self._dibr_config)

    def set_convergence(self, convergence: float) -> None:
        """Update the convergence distance.

        Args:
            convergence: New convergence value (0-1).
        """
        logger = _get_stereo_logger()
        logger.info(f"Updating convergence: {self.convergence} -> {convergence}")
        self.convergence = convergence
        self._dibr_config.convergence = convergence
        self._dibr_engine = DIBREngine(config=self._dibr_config)

    def compute_disparity(
        self,
        depth_map: np.ndarray,
        image_width: int,
    ) -> np.ndarray:
        """Compute disparity map from depth values.

        This is a convenience method that delegates to the DIBR engine.

        Args:
            depth_map: Normalized depth map with values in [0, 1].
            image_width: Width of the target image in pixels.

        Returns:
            Disparity map with same shape as depth_map.
        """
        return self._dibr_engine.compute_disparity(depth_map, image_width)


class AnaglyphGenerator(StereoGenerator):
    """Generate anaglyph 3D video with support for multiple anaglyph types.

    This generator creates anaglyph 3D images that can be viewed with
    various types of colored 3D glasses:
    - Red-Cyan (most common, standard 3D glasses)
    - Magenta-Green (Trioscopic, better color reproduction)
    - Amber-Blue (ColorCode3D, excellent color preservation)

    Multiple encoding methods are available for red-cyan:
    - dubois: High-quality, minimal ghosting (recommended)
    - color: Simple channel mixing
    - gray: Grayscale, pure depth
    - half_color: Compromise between color and ghosting

    Example usage:
        ```python
        # Basic usage (default: red-cyan dubois)
        generator = AnaglyphGenerator()
        left, right = generator.generate_stereo_pair(frame, depth_map)
        anaglyph = generator.combine_to_anaglyph(left, right)

        # Specify anaglyph type
        generator = AnaglyphGenerator(anaglyph_type="magenta_green")
        anaglyph = generator.combine_to_anaglyph(left, right)

        # Use AnaglyphType enum
        generator = AnaglyphGenerator(anaglyph_type=AnaglyphType.AMBER_BLUE)
        anaglyph = generator.combine_to_anaglyph(left, right)
        ```
    """

    # Mapping from string names to AnaglyphType enum values
    _ANAGLYPH_TYPE_MAP = {
        # Red-Cyan variants
        "dubois": AnaglyphType.RED_CYAN_DUBOIS,
        "red_cyan_dubois": AnaglyphType.RED_CYAN_DUBOIS,
        "color": AnaglyphType.RED_CYAN_COLOR,
        "red_cyan_color": AnaglyphType.RED_CYAN_COLOR,
        "gray": AnaglyphType.RED_CYAN_GRAY,
        "red_cyan_gray": AnaglyphType.RED_CYAN_GRAY,
        "half_color": AnaglyphType.RED_CYAN_HALF_COLOR,
        "red_cyan_half_color": AnaglyphType.RED_CYAN_HALF_COLOR,
        # Magenta-Green
        "magenta_green": AnaglyphType.MAGENTA_GREEN,
        "trioscopic": AnaglyphType.MAGENTA_GREEN,
        # Amber-Blue
        "amber_blue": AnaglyphType.AMBER_BLUE,
        "colorcode": AnaglyphType.AMBER_BLUE,
        "colorcode3d": AnaglyphType.AMBER_BLUE,
    }

    def __init__(
        self,
        anaglyph_type: str | AnaglyphType = "dubois",
        baseline: float = 0.05,
        convergence: float = 0.5,
    ) -> None:
        """Initialize anaglyph generator.

        Args:
            anaglyph_type: Anaglyph encoding type. Can be a string or AnaglyphType enum.
                String options:
                - 'dubois' or 'red_cyan_dubois': Red-cyan Dubois (recommended)
                - 'color' or 'red_cyan_color': Simple red-cyan
                - 'gray' or 'red_cyan_gray': Grayscale red-cyan
                - 'half_color' or 'red_cyan_half_color': Half-color red-cyan
                - 'magenta_green' or 'trioscopic': Magenta-green (Trioscopic)
                - 'amber_blue' or 'colorcode3d': Amber-blue (ColorCode3D)
            baseline: Stereo baseline (eye separation).
            convergence: Convergence distance (0-1).
        """
        super().__init__(
            format="anaglyph",
            baseline=baseline,
            convergence=convergence,
        )
        # Convert string to AnaglyphType if needed
        if isinstance(anaglyph_type, str):
            anaglyph_type = self._parse_anaglyph_type(anaglyph_type)
        self.anaglyph_type = anaglyph_type
        self._encoder = AnaglyphEncoder(default_type=anaglyph_type)
        _get_stereo_logger().debug(f"AnaglyphGenerator initialized: type={anaglyph_type}")

    def _parse_anaglyph_type(self, type_str: str) -> AnaglyphType:
        """Parse string to AnaglyphType enum.

        Args:
            type_str: String representation of anaglyph type.

        Returns:
            Corresponding AnaglyphType enum value.

        Raises:
            ValueError: If string is not a valid anaglyph type.
        """
        type_lower = type_str.lower().strip()
        if type_lower not in self._ANAGLYPH_TYPE_MAP:
            valid_options = list(self._ANAGLYPH_TYPE_MAP.keys())
            raise ValueError(
                f"Invalid anaglyph type '{type_str}'. Valid options: {valid_options}"
            )
        return self._ANAGLYPH_TYPE_MAP[type_lower]

    def combine_to_anaglyph(
        self,
        left: np.ndarray,
        right: np.ndarray,
        method: Optional[str | AnaglyphType] = None,
    ) -> np.ndarray:
        """Combine left and right views into an anaglyph 3D image.

        Args:
            left: Left eye view.
            right: Right eye view.
            method: Anaglyph encoding method. If None, uses instance default.
                Can be a string name or AnaglyphType enum.

        Returns:
            Anaglyph 3D image as uint8 numpy array.
        """
        if method is None:
            anaglyph_type = self.anaglyph_type
        elif isinstance(method, str):
            anaglyph_type = self._parse_anaglyph_type(method)
        else:
            anaglyph_type = method

        return self._encoder.encode(left, right, anaglyph_type)

    def set_anaglyph_type(self, anaglyph_type: str | AnaglyphType) -> None:
        """Change the anaglyph encoding type.

        Args:
            anaglyph_type: New anaglyph type (string or AnaglyphType enum).
        """
        if isinstance(anaglyph_type, str):
            anaglyph_type = self._parse_anaglyph_type(anaglyph_type)
        _get_stereo_logger().info(f"Changing anaglyph type: {self.anaglyph_type} -> {anaglyph_type}")
        self.anaglyph_type = anaglyph_type
        self._encoder.default_type = anaglyph_type

    # Convenience methods for specific anaglyph types

    def encode_red_cyan_dubois(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using Dubois red-cyan method (high quality, minimal ghosting)."""
        return self._encoder.encode_red_cyan_dubois(left, right)

    def encode_red_cyan_color(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using simple color red-cyan method."""
        return self._encoder.encode_red_cyan_color(left, right)

    def encode_red_cyan_gray(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using grayscale red-cyan method."""
        return self._encoder.encode_red_cyan_gray(left, right)

    def encode_red_cyan_half_color(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using half-color red-cyan method."""
        return self._encoder.encode_red_cyan_half_color(left, right)

    def encode_magenta_green(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using magenta-green (Trioscopic) method."""
        return self._encoder.encode_magenta_green(left, right)

    def encode_amber_blue(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using amber-blue (ColorCode3D) method."""
        return self._encoder.encode_amber_blue(left, right)

class SideBySideGenerator(StereoGenerator):
    """Generate side-by-side 3D video.

    This generator creates side-by-side 3D images where left and right
    views are placed horizontally or vertically adjacent.

    Example usage:
        ```python
        generator = SideBySideGenerator(layout="horizontal")
        left, right = generator.generate_stereo_pair(frame, depth_map)
        sbs = generator.combine_to_side_by_side(left, right)
        ```
    """

    def __init__(
        self,
        layout: str = "horizontal",
        swap_eyes: bool = False,
        half_width: bool = False,
        baseline: float = 0.05,
        convergence: float = 0.5,
    ) -> None:
        """Initialize side-by-side generator.

        Args:
            layout: Layout direction ('horizontal' or 'vertical').
            swap_eyes: Swap left and right eye positions.
            half_width: Render each eye at half width.
            baseline: Stereo baseline (eye separation).
            convergence: Convergence distance (0-1).
        """
        super().__init__(
            format="side_by_side",
            baseline=baseline,
            convergence=convergence,
        )
        self.layout = layout
        self.swap_eyes = swap_eyes
        self.half_width = half_width
        _get_stereo_logger().debug(
            f"SideBySideGenerator initialized: layout={layout}, "
            f"swap_eyes={swap_eyes}, half_width={half_width}"
        )

    def combine_to_side_by_side(
        self,
        left: np.ndarray,
        right: np.ndarray,
    ) -> np.ndarray:
        """Combine left and right views into a side-by-side image.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Side-by-side 3D image.
        """
        # Handle half-width mode
        if self.half_width:
            h, w = left.shape[:2]
            new_w = w // 2
            left = cv2.resize(left, (new_w, h), interpolation=cv2.INTER_LINEAR)
            right = cv2.resize(right, (new_w, h), interpolation=cv2.INTER_LINEAR)

        # Swap eyes if requested
        if self.swap_eyes:
            left, right = right, left

        if self.layout == "horizontal":
            return np.concatenate([left, right], axis=1)
        else:  # vertical
            return np.concatenate([left, right], axis=0)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Main classes
    "StereoGenerator",
    "AnaglyphGenerator",
    "SideBySideGenerator",
    # Anaglyph classes
    "AnaglyphEncoder",
    "AnaglyphType",
    # Side-by-side classes
    "SideBySideEncoder",
    "SideBySideLayout",
    # Checkerboard classes
    "CheckerboardEncoder",
    "CheckerboardPattern",
    # DIBR classes (re-exported for convenience)
    "DIBREngine",
    "DIBRConfig",
    "DIBRError",
    "HoleFillingMethod",
    "DepthInterpretation",
    # Functions
    "create_dibr_engine",
    "render_stereo_pair",
    "encode_anaglyph",
    "encode_side_by_side",
    "encode_checkerboard",
    "create_checkerboard_encoder",
    # Logger
    "_get_stereo_logger",
]
