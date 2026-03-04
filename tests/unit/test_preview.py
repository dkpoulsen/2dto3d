"""Test preview window functionality."""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from video2d3d.preview import (
    PreviewConfig,
    PreviewWindow,
    PreviewWindowError,
    PreviewLayout,
    create_preview_window,
)


class TestPreviewConfig:
    """Tests for PreviewConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PreviewConfig()
        assert config.enabled is False
        assert config.window_name == "2Dto3D Preview"
        assert config.layout == PreviewLayout.HORIZONTAL
        assert config.scale == 0.5
        assert config.show_fps is True
        assert config.show_frame_info is True
        assert config.auto_resize is True
        assert config.max_width == 1920
        assert config.max_height == 1080
        assert config.update_interval_ms == 33

    def test_custom_values(self):
        """Test custom configuration values."""
        config = PreviewConfig(
            enabled=True,
            window_name="Custom Preview",
            layout=PreviewLayout.VERTICAL,
            scale=0.75,
            show_fps=False,
        )
        assert config.enabled is True
        assert config.window_name == "Custom Preview"
        assert config.layout == PreviewLayout.VERTICAL
        assert config.scale == 0.75
        assert config.show_fps is False

    def test_layout_enum_values(self):
        """Test PreviewLayout enum values."""
        assert PreviewLayout.HORIZONTAL.value == "horizontal"
        assert PreviewLayout.VERTICAL.value == "vertical"
        assert PreviewLayout.GRID.value == "grid"


class TestPreviewWindow:
    """Tests for PreviewWindow class."""

    @pytest.fixture
    def sample_frame(self):
        """Create a sample frame for testing."""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    @pytest.fixture
    def sample_depth_map(self):
        """Create a sample depth map for testing."""
        return np.random.rand(480, 640).astype(np.float32)

    @pytest.fixture
    def disabled_config(self):
        """Create a config with preview disabled."""
        return PreviewConfig(enabled=False)

    @pytest.fixture
    def enabled_config(self):
        """Create a config with preview enabled."""
        return PreviewConfig(enabled=True)

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        preview = PreviewWindow()
        assert preview.is_enabled is False
        assert preview.is_created is False

    def test_init_with_custom_config(self, enabled_config):
        """Test initialization with custom config."""
        preview = PreviewWindow(enabled_config)
        assert preview.is_enabled is True
        assert preview.is_created is False  # Not created until first show

    def test_update_does_nothing_when_disabled(
        self, disabled_config, sample_frame, sample_depth_map
    ):
        """Test that update does nothing when preview is disabled."""
        preview = PreviewWindow(disabled_config)
        result = preview.update(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
        )
        assert result is True  # Returns True even when disabled
        assert preview.is_created is False

    def test_show_does_nothing_when_disabled(self, disabled_config, sample_frame, sample_depth_map):
        """Test that show does nothing when preview is disabled."""
        preview = PreviewWindow(disabled_config)
        result = preview.show(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
        )
        assert result == -1  # Returns -1 when disabled

    def test_context_manager(self, enabled_config):
        """Test context manager usage."""
        with PreviewWindow(enabled_config) as preview:
            assert preview.is_enabled is True

        # After context exit, window should be closed
        assert preview.is_created is False

    def test_close_is_idempotent(self, enabled_config):
        """Test that close can be called multiple times safely."""
        preview = PreviewWindow(enabled_config)
        preview.close()
        preview.close()  # Should not raise

    def test_combine_frames_horizontal(self, sample_frame, sample_depth_map):
        """Test horizontal frame combination."""
        config = PreviewConfig(layout=PreviewLayout.HORIZONTAL, show_frame_info=False, scale=1.0)
        preview = PreviewWindow(config)

        combined = preview.combine_frames(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
        )

        # Combined width should be approximately 3x original (3 panels side by side)
        assert combined.shape[0] == sample_frame.shape[0]  # Same height
        assert combined.shape[2] == 3  # BGR channels

    def test_combine_frames_vertical(self, sample_frame, sample_depth_map):
        """Test vertical frame combination."""
        config = PreviewConfig(layout=PreviewLayout.VERTICAL, show_frame_info=False, scale=1.0)
        preview = PreviewWindow(config)

        combined = preview.combine_frames(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
        )

        # Combined height should be approximately 3x original (3 panels stacked)
        assert combined.shape[1] == sample_frame.shape[1]  # Same width
        assert combined.shape[2] == 3  # BGR channels

    def test_combine_frames_grid(self, sample_frame, sample_depth_map):
        """Test grid frame combination."""
        config = PreviewConfig(layout=PreviewLayout.GRID, show_frame_info=False, scale=1.0)
        preview = PreviewWindow(config)

        combined = preview.combine_frames(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
        )

        assert combined.shape[2] == 3  # BGR channels

    def test_normalize_depth_map(self, sample_depth_map):
        """Test depth map normalization."""
        config = PreviewConfig(scale=1.0)
        preview = PreviewWindow(config)

        normalized = preview._normalize_depth_map(sample_depth_map)

        assert normalized.dtype == np.uint8
        assert len(normalized.shape) == 3  # Should be BGR after colormap
        assert normalized.shape[2] == 3

    def test_normalize_depth_map_uint8_input(self):
        """Test depth map normalization with uint8 input."""
        config = PreviewConfig(scale=1.0)
        preview = PreviewWindow(config)

        depth_uint8 = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        normalized = preview._normalize_depth_map(depth_uint8)

        assert normalized.dtype == np.uint8
        assert len(normalized.shape) == 3

    def test_ensure_bgr_grayscale_input(self):
        """Test BGR conversion for grayscale input."""
        config = PreviewConfig()
        preview = PreviewWindow(config)

        grayscale = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
        bgr = preview._ensure_bgr(grayscale)

        assert len(bgr.shape) == 3
        assert bgr.shape[2] == 3

    def test_ensure_bgr_bgr_input(self, sample_frame):
        """Test BGR conversion for BGR input (no change)."""
        config = PreviewConfig()
        preview = PreviewWindow(config)

        bgr = preview._ensure_bgr(sample_frame)

        assert bgr.shape == sample_frame.shape
        np.testing.assert_array_equal(bgr, sample_frame)

    def test_ensure_same_height(self, sample_frame):
        """Test frame height normalization."""
        config = PreviewConfig()
        preview = PreviewWindow(config)

        # Create frames with different heights
        frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        frame2 = np.random.randint(0, 255, (360, 480, 3), dtype=np.uint8)
        frame3 = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)

        normalized = preview._ensure_same_height([frame1, frame2, frame3])

        # All frames should have the same height as the first
        assert all(f.shape[0] == 480 for f in normalized)

    def test_resize_if_needed_no_resize(self):
        """Test resize when frame is within limits."""
        config = PreviewConfig(auto_resize=True, max_width=1920, max_height=1080)
        preview = PreviewWindow(config)

        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = preview._resize_if_needed(frame)

        np.testing.assert_array_equal(result, frame)

    def test_resize_if_needed_with_resize(self):
        """Test resize when frame exceeds limits."""
        config = PreviewConfig(auto_resize=True, max_width=320, max_height=240)
        preview = PreviewWindow(config)

        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = preview._resize_if_needed(frame)

        # Should be resized to fit within limits
        assert result.shape[1] <= 320
        assert result.shape[0] <= 240

    def test_apply_scale(self, sample_frame):
        """Test scale application."""
        config = PreviewConfig(scale=0.5)
        preview = PreviewWindow(config)

        scaled = preview._apply_scale(sample_frame)

        assert scaled.shape[0] == sample_frame.shape[0] // 2
        assert scaled.shape[1] == sample_frame.shape[1] // 2

    def test_apply_scale_no_scale(self, sample_frame):
        """Test scale application with scale=1.0 (no change)."""
        config = PreviewConfig(scale=1.0)
        preview = PreviewWindow(config)

        scaled = preview._apply_scale(sample_frame)

        np.testing.assert_array_equal(scaled, sample_frame)

    def test_add_label(self, sample_frame):
        """Test label addition to frame."""
        config = PreviewConfig(show_frame_info=True)
        preview = PreviewWindow(config)

        labeled = preview._add_label(sample_frame, "Test Label")

        # Should have extra height for the label bar
        assert labeled.shape[0] > sample_frame.shape[0]
        assert labeled.shape[1] == sample_frame.shape[1]

    def test_add_label_disabled(self, sample_frame):
        """Test label addition when disabled."""
        config = PreviewConfig(show_frame_info=False)
        preview = PreviewWindow(config)

        labeled = preview._add_label(sample_frame, "Test Label")

        # Should return original frame unchanged
        np.testing.assert_array_equal(labeled, sample_frame)

    def test_should_update_rate_limiting(self):
        """Test update rate limiting."""
        config = PreviewConfig(update_interval_ms=100)
        preview = PreviewWindow(config)

        # First call should return True
        assert preview._should_update() is True

        # Immediate second call should return False (rate limited)
        assert preview._should_update() is False


class TestPreviewWindowError:
    """Tests for PreviewWindowError exception."""

    def test_exception_creation(self):
        """Test exception can be raised and caught."""
        with pytest.raises(PreviewWindowError) as exc_info:
            raise PreviewWindowError("Test error message")

        assert "Test error message" in str(exc_info.value)


class TestCreatePreviewWindow:
    """Tests for factory function."""

    def test_create_with_default_config(self):
        """Test creating preview window with default config."""
        preview = create_preview_window()
        assert isinstance(preview, PreviewWindow)
        assert preview.is_enabled is False

    def test_create_with_custom_config(self):
        """Test creating preview window with custom config."""
        config = PreviewConfig(enabled=True, window_name="Test")
        preview = create_preview_window(config)
        assert preview.is_enabled is True


class TestPreviewWindowWithMockedCV2:
    """Tests that require cv2 to be available."""

    def test_update_with_enabled_preview(self, sample_frame, sample_depth_map):
        """Test update with preview enabled."""
        import cv2

        config = PreviewConfig(enabled=True, update_interval_ms=0)
        preview = PreviewWindow(config)

        result = preview.update(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
            frame_number=1,
        )

        # Should return True if window is created
        assert result is True

        preview.close()

    def test_show_with_enabled_preview(self, sample_frame, sample_depth_map):
        """Test show with preview enabled."""
        import cv2

        config = PreviewConfig(enabled=True)
        preview = PreviewWindow(config)

        # show with wait=False should be non-blocking
        result = preview.show(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
            wait=False,
        )

        # Result can be -1 if no key was pressed (expected in mock/test environment)
        assert isinstance(result, int)

        preview.close()
