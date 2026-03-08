"""Live preview window for video processing quality assessment.

This module provides optional real-time preview functionality using OpenCV,
displaying the original frame, depth map, and stereoscopic result side-by-side
during processing for quality assessment.
"""

from __future__ import annotations

import contextlib
import threading
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from video2d3d.utils.logger import get_logger, log_exception

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Lazy import for cv2 to avoid import errors in headless environments
cv2 = None


def _ensure_cv2() -> None:
    """Ensure OpenCV is available, raise error if not."""
    global cv2
    if cv2 is None:
        try:
            import cv2 as _cv2

            cv2 = _cv2
        except ImportError as e:
            raise PreviewWindowError(
                "OpenCV is required for preview functionality. "
                "Install it with: pip install opencv-python"
            ) from e


class PreviewLayout(Enum):
    """Layout options for the preview window."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    GRID = "grid"


class PreviewWindowError(Exception):
    """Exception raised for preview window errors."""

    pass


@dataclass
class PreviewConfig:
    """Configuration for the preview window.

    Attributes:
        enabled: Whether preview is enabled.
        window_name: Name of the preview window.
        layout: Layout of the preview panels.
        scale: Scale factor for the preview (0.0-1.0, where 1.0 is original size).
        show_fps: Whether to display FPS counter.
        show_frame_info: Whether to display frame number and processing info.
        auto_resize: Whether to automatically resize window to fit screen.
        max_width: Maximum width of the preview window.
        max_height: Maximum height of the preview window.
        update_interval_ms: Minimum interval between frame updates in milliseconds.
    """

    enabled: bool = False
    window_name: str = "2Dto3D Preview"
    layout: PreviewLayout = PreviewLayout.HORIZONTAL
    scale: float = 0.5
    show_fps: bool = True
    show_frame_info: bool = True
    auto_resize: bool = True
    max_width: int = 1920
    max_height: int = 1080
    update_interval_ms: int = 33  # ~30 FPS max update rate


class PreviewWindow:
    """Live preview window for video processing quality assessment.

    Displays original frame, depth map, and stereoscopic result side-by-side
    during processing for quality assessment.

    Thread-safe implementation that can be updated from processing threads.

    Example:
        >>> config = PreviewConfig(enabled=True)
        >>> preview = PreviewWindow(config)
        >>> preview.show(original_frame, depth_map, stereo_result)
        >>> # During processing loop
        >>> preview.update(original, depth, stereo, frame_number=42)
        >>> # When done
        >>> preview.close()
    """

    # Constants for panel labels and colors
    PANEL_LABELS = ("Original", "Depth Map", "3D Result")
    LABEL_FONT = None  # Will use cv2.FONT_HERSHEY_SIMPLEX
    LABEL_FONT_SCALE = 0.6
    LABEL_COLOR = (255, 255, 255)
    LABEL_BG_COLOR = (0, 0, 0)
    LABEL_THICKNESS = 2

    def __init__(self, config: PreviewConfig | None = None) -> None:
        """Initialize the preview window.

        Args:
            config: Configuration for the preview window. Uses defaults if None.
        """
        self._config = config or PreviewConfig()
        self._logger = get_logger("preview_window")

        # State
        self._is_created = False
        self._is_closed = False
        self._lock = threading.Lock()
        self._last_update_time: float = 0.0

        # FPS calculation
        self._frame_times: list[float] = []
        self._fps: float = 0.0
        self._frame_count: int = 0

        # Panel dimensions (calculated on first frame)
        self._panel_height: int = 0
        self._panel_width: int = 0

        if self._config.enabled:
            self._logger.info("Preview window configured (will be created on first show)")

    @property
    def is_enabled(self) -> bool:
        """Check if preview is enabled."""
        return self._config.enabled

    @property
    def is_created(self) -> bool:
        """Check if the window has been created."""
        return self._is_created and not self._is_closed

    def _ensure_window_created(self) -> None:
        """Create the window if it doesn't exist."""
        if self._is_created or self._is_closed:
            return

        _ensure_cv2()

        try:
            cv2.namedWindow(self._config.window_name, cv2.WINDOW_NORMAL)
            self._is_created = True
            self._logger.debug(f"Created preview window: {self._config.window_name}")
        except Exception as e:
            log_exception("Failed to create preview window", exception=e)
            raise PreviewWindowError(f"Failed to create preview window: {e}") from e

    def _resize_if_needed(self, combined_frame: NDArray) -> NDArray:
        """Resize the combined frame if it exceeds maximum dimensions.

        Args:
            combined_frame: The combined preview frame.

        Returns:
            Resized frame if needed, otherwise original.
        """
        if not self._config.auto_resize:
            return combined_frame

        height, width = combined_frame.shape[:2]
        max_w, max_h = self._config.max_width, self._config.max_height

        if width > max_w or height > max_h:
            scale = min(max_w / width, max_h / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(combined_frame, (new_width, new_height))

        return combined_frame

    def _apply_scale(self, frame: NDArray) -> NDArray:
        """Apply scale factor to a frame.

        Args:
            frame: Input frame.

        Returns:
            Scaled frame.
        """
        if self._config.scale >= 1.0:
            return frame

        height, width = frame.shape[:2]
        new_width = int(width * self._config.scale)
        new_height = int(height * self._config.scale)
        return cv2.resize(frame, (new_width, new_height))

    def _add_label(self, frame: NDArray, label: str) -> NDArray:
        """Add a label to the top of a frame.

        Args:
            frame: Input frame.
            label: Label text.

        Returns:
            Frame with label added.
        """
        if not self._config.show_frame_info:
            return frame

        # Create label bar at top
        label_height = 30
        label_bar = np.zeros((label_height, frame.shape[1], 3), dtype=np.uint8)

        # Add label text
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(label, font, self.LABEL_FONT_SCALE, self.LABEL_THICKNESS)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = (label_height + text_size[1]) // 2

        cv2.putText(
            label_bar,
            label,
            (text_x, text_y),
            font,
            self.LABEL_FONT_SCALE,
            self.LABEL_COLOR,
            self.LABEL_THICKNESS,
        )

        # Combine label bar with frame
        return np.vstack([label_bar, frame])

    def _calculate_fps(self) -> float:
        """Calculate FPS from recent frame times.

        Returns:
            Current FPS estimate.
        """
        import time

        current_time = time.time()

        # Add current frame time
        self._frame_times.append(current_time)

        # Keep only last 30 frame times
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)

        # Calculate FPS if we have enough data
        if len(self._frame_times) >= 2:
            elapsed = self._frame_times[-1] - self._frame_times[0]
            if elapsed > 0:
                self._fps = (len(self._frame_times) - 1) / elapsed

        return self._fps

    def _should_update(self) -> bool:
        """Check if enough time has passed since last update.

        Returns:
            True if update should proceed.
        """
        import time

        current_time = time.time()
        elapsed_ms = (current_time - self._last_update_time) * 1000

        if elapsed_ms < self._config.update_interval_ms:
            return False

        self._last_update_time = current_time
        return True

    def _normalize_depth_map(self, depth_map: NDArray) -> NDArray:
        """Normalize depth map for display.

        Args:
            depth_map: Raw depth map (single channel).

        Returns:
            Normalized depth map as 8-bit BGR image.
        """
        # Handle different depth map formats
        if depth_map.dtype != np.uint8:
            # Normalize to 0-255 range
            depth_min = depth_map.min()
            depth_max = depth_map.max()
            if depth_max > depth_min:
                depth_normalized = ((depth_map - depth_min) / (depth_max - depth_min) * 255).astype(
                    np.uint8
                )
            else:
                depth_normalized = np.zeros_like(depth_map, dtype=np.uint8)
        else:
            depth_normalized = depth_map

        # Apply colormap for better visualization
        return cv2.applyColorMap(depth_normalized, cv2.COLORMAP_MAGMA)

    def _ensure_bgr(self, frame: NDArray) -> NDArray:
        """Ensure frame is in BGR format.

        Args:
            frame: Input frame (can be grayscale or BGR).

        Returns:
            Frame in BGR format.
        """
        if len(frame.shape) == 2:
            # Grayscale - convert to BGR
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            # RGBA - convert to BGR
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

    def _ensure_same_height(self, frames: list[NDArray]) -> list[NDArray]:
        """Resize frames to have the same height.

        Args:
            frames: List of frames with potentially different heights.

        Returns:
            List of frames with the same height.
        """
        if not frames:
            return frames

        # Find target height (use the first frame's height)
        target_height = frames[0].shape[0]

        resized = []
        for frame in frames:
            if frame.shape[0] != target_height:
                # Calculate new width maintaining aspect ratio
                ratio = target_height / frame.shape[0]
                new_width = int(frame.shape[1] * ratio)
                resized.append(cv2.resize(frame, (new_width, target_height)))
            else:
                resized.append(frame)

        return resized

    def combine_frames(
        self,
        original: NDArray,
        depth_map: NDArray,
        stereo_result: NDArray,
    ) -> NDArray:
        """Combine original, depth, and stereo frames into a single preview.

        Args:
            original: Original input frame.
            depth_map: Estimated depth map.
            stereo_result: Generated stereoscopic result.

        Returns:
            Combined preview frame.
        """
        # Ensure all frames are BGR
        original_bgr = self._ensure_bgr(original)
        depth_bgr = (
            self._normalize_depth_map(depth_map)
            if len(depth_map.shape) == 2
            else self._ensure_bgr(depth_map)
        )
        stereo_bgr = self._ensure_bgr(stereo_result)

        # Apply scale
        if self._config.scale < 1.0:
            original_bgr = self._apply_scale(original_bgr)
            depth_bgr = self._apply_scale(depth_bgr)
            stereo_bgr = self._apply_scale(stereo_bgr)

        # Ensure same height
        frames = self._ensure_same_height([original_bgr, depth_bgr, stereo_bgr])
        original_bgr, depth_bgr, stereo_bgr = frames

        # Add labels
        if self._config.show_frame_info:
            original_bgr = self._add_label(original_bgr, "Original")
            depth_bgr = self._add_label(depth_bgr, "Depth Map")
            stereo_bgr = self._add_label(
                stereo_result if stereo_result.shape == stereo_bgr.shape else stereo_bgr,
                "3D Result",
            )
            stereo_bgr = self._add_label(stereo_bgr, "3D Result")

        # Combine based on layout
        if self._config.layout == PreviewLayout.HORIZONTAL:
            combined = np.hstack([original_bgr, depth_bgr, stereo_bgr])
        elif self._config.layout == PreviewLayout.VERTICAL:
            combined = np.vstack([original_bgr, depth_bgr, stereo_bgr])
        else:  # GRID
            # 2x2 grid (first row: original + depth, second row: stereo + empty)
            top_row = np.hstack([original_bgr, depth_bgr])
            # Create empty panel for grid
            empty_panel = np.zeros_like(stereo_bgr)
            bottom_row = np.hstack([stereo_bgr, empty_panel])
            combined = np.vstack([top_row, bottom_row])

        return combined

    def update(
        self,
        original: NDArray,
        depth_map: NDArray,
        stereo_result: NDArray,
        frame_number: int = 0,
    ) -> bool:
        """Update the preview window with new frames.

        This method is thread-safe and can be called from processing threads.

        Args:
            original: Original input frame.
            depth_map: Estimated depth map.
            stereo_result: Generated stereoscopic result.
            frame_number: Current frame number for display.

        Returns:
            True if window is still open, False if closed by user.
        """
        if not self._config.enabled:
            return True

        with self._lock:
            # Check if we should update (rate limiting)
            if not self._should_update():
                return self.is_created

            try:
                # Ensure window exists
                self._ensure_window_created()

                if self._is_closed:
                    return False

                # Combine frames
                combined = self.combine_frames(original, depth_map, stereo_result)

                # Resize if needed
                combined = self._resize_if_needed(combined)

                # Calculate FPS
                fps = self._calculate_fps()
                self._frame_count += 1

                # Add info overlay
                if self._config.show_fps or self._config.show_frame_info:
                    info_parts = []
                    if self._config.show_fps:
                        info_parts.append(f"FPS: {fps:.1f}")
                    if self._config.show_frame_info:
                        info_parts.append(f"Frame: {frame_number}")

                    info_text = " | ".join(info_parts)
                    cv2.putText(
                        combined,
                        info_text,
                        (10, combined.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )

                # Show the frame
                cv2.imshow(self._config.window_name, combined)

                # Process events (non-blocking)
                key = cv2.pollKey()
                if key == 27 or key == ord("q"):  # ESC or Q to close
                    self.close()
                    return False

                return True

            except Exception as e:
                log_exception("Error updating preview window", exception=e)
                return self.is_created

    def show(
        self,
        original: NDArray,
        depth_map: NDArray,
        stereo_result: NDArray,
        wait: bool = True,
        wait_time_ms: int = 0,
    ) -> int:
        """Display a single frame preview (blocking or with wait).

        This is useful for displaying a preview without a processing loop.

        Args:
            original: Original input frame.
            depth_map: Estimated depth map.
            stereo_result: Generated stereoscopic result.
            wait: Whether to wait for a key press.
            wait_time_ms: Time to wait in milliseconds (0 = indefinite).

        Returns:
            Key code pressed, or -1 if no key was pressed.
        """
        if not self._config.enabled:
            return -1

        with self._lock:
            try:
                self._ensure_window_created()

                # Combine frames
                combined = self.combine_frames(original, depth_map, stereo_result)

                # Resize if needed
                combined = self._resize_if_needed(combined)

                # Show the frame
                cv2.imshow(self._config.window_name, combined)

                if wait:
                    return cv2.waitKey(wait_time_ms)
                else:
                    return cv2.pollKey()

            except Exception as e:
                log_exception("Error showing preview", exception=e)
                return -1

    def close(self) -> None:
        """Close the preview window and release resources."""
        if self._is_closed:
            return

        with self._lock:
            self._is_closed = True

            if self._is_created:
                try:
                    cv2.destroyWindow(self._config.window_name)
                    self._logger.debug(f"Closed preview window: {self._config.window_name}")
                except Exception as e:
                    log_exception("Error closing preview window", exception=e)

            self._is_created = False

    def __enter__(self) -> PreviewWindow:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures window is closed."""
        self.close()

    def __del__(self) -> None:
        """Destructor - ensures window is closed."""
        with contextlib.suppress(Exception):
            self.close()


def create_preview_window(config: PreviewConfig | None = None) -> PreviewWindow:
    """Factory function to create a preview window.

    Args:
        config: Configuration for the preview window. Uses defaults if None.

    Returns:
        Configured PreviewWindow instance.
    """
    return PreviewWindow(config)
