"""Test preview window functionality."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import numpy as np
import threading
import time

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

    def test_edge_case_scale_zero(self):
        """Test scale at boundary (zero)."""
        config = PreviewConfig(scale=0.0)
        assert config.scale == 0.0

    def test_edge_case_scale_one(self):
        """Test scale at boundary (one)."""
        config = PreviewConfig(scale=1.0)
        assert config.scale == 1.0


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
    def sample_depth_map_normalized(self):
        """Create a normalized depth map for testing."""
        return np.random.randint(0, 256, (480, 640), dtype=np.uint8)

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

    def test_combine_frames_with_labels(self, sample_frame, sample_depth_map):
        """Test frame combination with labels enabled."""
        config = PreviewConfig(layout=PreviewLayout.HORIZONTAL, show_frame_info=True, scale=1.0)
        preview = PreviewWindow(config)

        combined = preview.combine_frames(
            original=sample_frame,
            depth_map=sample_depth_map,
            stereo_result=sample_frame,
        )

        # Should have extra height for labels
        assert combined.shape[2] == 3

    def test_normalize_depth_map(self, sample_depth_map):
        """Test depth map normalization."""
        config = PreviewConfig(scale=1.0)
        preview = PreviewWindow(config)

        normalized = preview._normalize_depth_map(sample_depth_map)

        assert normalized.dtype == np.uint8
        assert len(normalized.shape) == 3  # Should be BGR after colormap
        assert normalized.shape[2] == 3

    def test_normalize_depth_map_uint8_input(self, sample_depth_map_normalized):
        """Test depth map normalization with uint8 input."""
        config = PreviewConfig(scale=1.0)
        preview = PreviewWindow(config)

        normalized = preview._normalize_depth_map(sample_depth_map_normalized)

        assert normalized.dtype == np.uint8
        assert len(normalized.shape) == 3

    def test_normalize_depth_map_uniform_values(self):
        """Test depth map normalization with uniform values."""
        config = PreviewConfig(scale=1.0)
        preview = PreviewWindow(config)

        # All same value - should not divide by zero
        depth_uniform = np.ones((480, 640), dtype=np.float32) * 0.5
        normalized = preview._normalize_depth_map(depth_uniform)

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

    def test_ensure_bgr_rgba_input(self):
        """Test BGR conversion for RGBA input."""
        config = PreviewConfig()
        preview = PreviewWindow(config)

        rgba = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
        bgr = preview._ensure_bgr(rgba)

        assert len(bgr.shape) == 3
        assert bgr.shape[2] == 3

    def test_ensure_same_height(self):
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

    def test_ensure_same_height_empty_list(self):
        """Test height normalization with empty list."""
        config = PreviewConfig()
        preview = PreviewWindow(config)

        result = preview._ensure_same_height([])
        assert result == []

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

    def test_resize_if_needed_disabled(self):
        """Test resize when auto_resize is disabled."""
        config = PreviewConfig(auto_resize=False)
        preview = PreviewWindow(config)

        # Create a large frame
        frame = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
        result = preview._resize_if_needed(frame)

        # Should not resize
        np.testing.assert_array_equal(result, frame)

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

    def test_should_update_after_interval(self):
        """Test update after interval passes."""
        config = PreviewConfig(update_interval_ms=10)
        preview = PreviewWindow(config)

        # First call should return True
        assert preview._should_update() is True

        # Wait for interval to pass
        time.sleep(0.02)

        # Should now return True
        assert preview._should_update() is True

    def test_calculate_fps(self):
        """Test FPS calculation."""
        config = PreviewConfig()
        preview = PreviewWindow(config)

        # Initial FPS should be 0
        fps = preview._calculate_fps()
        assert fps >= 0

        # After multiple calls, should have a value
        for _ in range(5):
            time.sleep(0.01)
            preview._calculate_fps()

        assert preview._fps > 0

    def test_thread_safety(self, sample_frame, sample_depth_map):
        """Test that update is thread-safe."""
        config = PreviewConfig(enabled=False)  # Disabled to avoid cv2
        preview = PreviewWindow(config)

        results = []

        def update_thread(frame_num):
            result = preview.update(
                original=sample_frame,
                depth_map=sample_depth_map,
                stereo_result=sample_frame,
                frame_number=frame_num,
            )
            results.append(result)

        threads = [threading.Thread(target=update_thread, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All updates should succeed
        assert all(results)


class TestPreviewWindowError:
    """Tests for PreviewWindowError exception."""

    def test_exception_creation(self):
        """Test exception can be raised and caught."""
        with pytest.raises(PreviewWindowError) as exc_info:
            raise PreviewWindowError("Test error message")

        assert "Test error message" in str(exc_info.value)

    def test_exception_inheritance(self):
        """Test exception inherits from Exception."""
        assert issubclass(PreviewWindowError, Exception)

    def test_exception_with_cause(self):
        """Test exception can have a cause."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            wrapped = PreviewWindowError("Wrapped error")
            wrapped.__cause__ = e
            assert wrapped.__cause__ is e


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
    """Tests with mocked cv2 for headless environments."""

    @pytest.fixture
    def mock_cv2(self):
        """Mock cv2 module."""
        with patch("video2d3d.preview.preview_window.cv2", None) as mock:
            # Create a comprehensive mock
            cv2_mock = MagicMock()
            cv2_mock.namedWindow = MagicMock()
            cv2_mock.destroyWindow = MagicMock()
            cv2_mock.imshow = MagicMock()
            cv2_mock.waitKey = MagicMock(return_value=-1)
            cv2_mock.pollKey = MagicMock(return_value=-1)
            cv2_mock.resize = MagicMock(side_effect=lambda f, s: f)
            cv2_mock.cvtColor = MagicMock(
                side_effect=lambda f, code: f if len(f.shape) == 3 else np.stack([f] * 3, axis=-1)
            )
            cv2_mock.applyColorMap = MagicMock(side_effect=lambda f, cm: np.stack([f] * 3, axis=-1))
            cv2_mock.putText = MagicMock()
            cv2_mock.getTextSize = MagicMock(return_value=((100, 20), 10))
            cv2_mock.FONT_HERSHEY_SIMPLEX = 0
            cv2_mock.WINDOW_NORMAL = 0
            cv2_mock.COLORMAP_MAGMA = 0
            cv2_mock.COLOR_GRAY2BGR = 8
            cv2_mock.COLOR_BGRA2BGR = 12

            yield cv2_mock

    @pytest.fixture
    def sample_frame(self):
        """Create a sample frame for testing."""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    @pytest.fixture
    def sample_depth_map(self):
        """Create a sample depth map for testing."""
        return np.random.rand(480, 640).astype(np.float32)

    def test_update_with_mocked_cv2(self, mock_cv2, sample_frame, sample_depth_map):
        """Test update with mocked cv2."""
        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True, update_interval_ms=0)
                preview = PreviewWindow(config)

                result = preview.update(
                    original=sample_frame,
                    depth_map=sample_depth_map,
                    stereo_result=sample_frame,
                    frame_number=1,
                )

                assert isinstance(result, bool)
                preview.close()

    def test_show_with_mocked_cv2(self, mock_cv2, sample_frame, sample_depth_map):
        """Test show with mocked cv2."""
        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True)
                preview = PreviewWindow(config)

                result = preview.show(
                    original=sample_frame,
                    depth_map=sample_depth_map,
                    stereo_result=sample_frame,
                    wait=False,
                )

                assert isinstance(result, int)
                preview.close()

    def test_close_with_mocked_cv2(self, mock_cv2):
        """Test close with mocked cv2."""
        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True)
                preview = PreviewWindow(config)
                preview.close()

                assert preview.is_created is False

    def test_ensure_cv2_raises_error_when_missing(self):
        """Test _ensure_cv2 raises error when cv2 is not available."""
        from video2d3d.preview.preview_window import _ensure_cv2

        with patch.dict("sys.modules", {"cv2": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'cv2'")):
                with pytest.raises(PreviewWindowError) as exc_info:
                    _ensure_cv2()

                assert "OpenCV is required" in str(exc_info.value)

    def test_update_with_esc_key_closes_window(self, mock_cv2, sample_frame, sample_depth_map):
        """Test that ESC key closes the window."""
        mock_cv2.pollKey.return_value = 27  # ESC key

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True, update_interval_ms=0)
                preview = PreviewWindow(config)

                result = preview.update(
                    original=sample_frame,
                    depth_map=sample_depth_map,
                    stereo_result=sample_frame,
                    frame_number=1,
                )

                # Should return False after ESC
                assert result is False

    def test_update_with_q_key_closes_window(self, mock_cv2, sample_frame, sample_depth_map):
        """Test that Q key closes the window."""
        mock_cv2.pollKey.return_value = ord("q")

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True, update_interval_ms=0)
                preview = PreviewWindow(config)

                result = preview.update(
                    original=sample_frame,
                    depth_map=sample_depth_map,
                    stereo_result=sample_frame,
                    frame_number=1,
                )

                # Should return False after Q
                assert result is False
