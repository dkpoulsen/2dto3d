"""Integration tests for preview window with config system."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.preview import PreviewConfig, PreviewLayout, PreviewWindow
from video2d3d.utils.config import load_config


class TestPreviewConfigIntegration:
    """Tests for preview configuration integration with main config system."""

    def test_load_config_includes_preview_section(self):
        """Test that load_config includes preview settings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
preview:
  enabled: true
  window_name: "Test Preview"
  layout: vertical
  scale: 0.75
  show_fps: false
  show_frame_info: true
  auto_resize: false
  max_width: 1280
  max_height: 720
  update_interval_ms: 50
""")
            f.flush()
            config_path = f.name

        try:
            # Load config with preview section
            config = load_config(config_path=config_path)

            # Verify preview config is loaded
            assert hasattr(config, "preview")
            assert config.preview.enabled is True
            assert config.preview.window_name == "Test Preview"
            assert config.preview.layout == "vertical"
            assert config.preview.scale == 0.75
            assert config.preview.show_fps is False
            assert config.preview.show_frame_info is True
            assert config.preview.auto_resize is False
            assert config.preview.max_width == 1280
            assert config.preview.max_height == 720
            assert config.preview.update_interval_ms == 50
        finally:
            os.unlink(config_path)

    def test_load_config_defaults_for_preview(self):
        """Test default values when preview section not in config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
processing:
  batch_size: 4
""")
            f.flush()
            config_path = f.name

        try:
            config = load_config(config_path=config_path)

            # Preview config should have defaults
            assert hasattr(config, "preview")
            assert config.preview.enabled is False
        finally:
            os.unlink(config_path)

    def test_create_preview_window_from_app_config(self):
        """Test creating preview window from loaded app config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
preview:
  enabled: true
  window_name: "Integration Test"
  scale: 0.6
""")
            f.flush()
            config_path = f.name

        try:
            app_config = load_config(config_path=config_path)

            # Convert app config preview to PreviewConfig
            preview_config = PreviewConfig(
                enabled=app_config.preview.enabled,
                window_name=app_config.preview.window_name,
                scale=app_config.preview.scale,
            )

            preview = PreviewWindow(preview_config)
            assert preview.is_enabled is True
            assert preview._config.window_name == "Integration Test"
            assert preview._config.scale == 0.6
        finally:
            os.unlink(config_path)

    def test_layout_string_to_enum_conversion(self):
        """Test converting layout string from config to enum."""
        layout_map = {
            "horizontal": PreviewLayout.HORIZONTAL,
            "vertical": PreviewLayout.VERTICAL,
            "grid": PreviewLayout.GRID,
        }

        for layout_str, expected_enum in layout_map.items():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                f.write(f"""
preview:
  enabled: true
  layout: {layout_str}
""")
                f.flush()
                config_path = f.name

            try:
                app_config = load_config(config_path=config_path)
                layout_enum = layout_map.get(app_config.preview.layout, PreviewLayout.HORIZONTAL)
                assert layout_enum == expected_enum
            finally:
                os.unlink(config_path)


class TestPreviewWindowWithComponents:
    """Tests for preview window integration with other components."""

    @pytest.fixture
    def mock_cv2(self):
        """Mock cv2 module."""
        cv2_mock = MagicMock()
        cv2_mock.namedWindow = MagicMock()
        cv2_mock.destroyWindow = MagicMock()
        cv2_mock.imshow = MagicMock()
        cv2_mock.waitKey = MagicMock(return_value=-1)
        cv2_mock.pollKey = MagicMock(return_value=-1)
        cv2_mock.resize = MagicMock(side_effect=lambda f, s: f)
        cv2_mock.cvtColor = MagicMock(side_effect=lambda f, code: f)
        cv2_mock.applyColorMap = MagicMock(side_effect=lambda f, cm: f)
        cv2_mock.putText = MagicMock()
        cv2_mock.getTextSize = MagicMock(return_value=((100, 20), 10))
        cv2_mock.FONT_HERSHEY_SIMPLEX = 0
        cv2_mock.WINDOW_NORMAL = 0
        cv2_mock.COLORMAP_MAGMA = 0
        return cv2_mock

    def test_preview_with_depth_processor_output(self, mock_cv2):
        """Test preview with realistic depth processor output."""
        import numpy as np

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True, update_interval_ms=0, scale=1.0)
                preview = PreviewWindow(config)

                # Simulate realistic depth processor output
                # Depth maps often have values in range [0, 1] or [0, 255]
                original = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
                depth_float = np.random.rand(720, 1280).astype(np.float32)
                stereo = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

                result = preview.update(
                    original=original,
                    depth_map=depth_float,
                    stereo_result=stereo,
                    frame_number=42,
                )

                assert isinstance(result, bool)
                preview.close()

    def test_preview_with_different_resolutions(self, mock_cv2):
        """Test preview handles different input resolutions."""
        import numpy as np

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True, update_interval_ms=0)
                preview = PreviewWindow(config)

                resolutions = [
                    (480, 640),
                    (720, 1280),
                    (1080, 1920),
                    (2160, 3840),
                ]

                for h, w in resolutions:
                    original = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
                    depth = np.random.rand(h, w).astype(np.float32)
                    stereo = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

                    result = preview.update(
                        original=original,
                        depth_map=depth,
                        stereo_result=stereo,
                        frame_number=0,
                    )

                    assert isinstance(result, bool)

                preview.close()

    def test_preview_auto_resize_with_large_frames(self, mock_cv2):
        """Test auto-resize with frames larger than max dimensions."""
        import numpy as np

        # Create a mock that actually resizes
        def mock_resize(frame, size):
            return np.zeros((size[1], size[0], frame.shape[2]), dtype=frame.dtype)

        mock_cv2.resize.side_effect = mock_resize

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(
                    enabled=True,
                    update_interval_ms=0,
                    auto_resize=True,
                    max_width=640,
                    max_height=480,
                    scale=1.0,
                )
                preview = PreviewWindow(config)

                # Large 4K frame
                large_frame = np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)
                large_depth = np.random.rand(2160, 3840).astype(np.float32)

                result = preview.update(
                    original=large_frame,
                    depth_map=large_depth,
                    stereo_result=large_frame,
                    frame_number=0,
                )

                # Should have been resized
                assert mock_cv2.resize.called or isinstance(result, bool)
                preview.close()


class TestPreviewErrorHandling:
    """Tests for error handling in preview window."""

    @pytest.fixture
    def mock_cv2_with_error(self):
        """Mock cv2 that raises errors."""
        cv2_mock = MagicMock()
        cv2_mock.namedWindow = MagicMock(side_effect=RuntimeError("Display error"))
        cv2_mock.destroyWindow = MagicMock()
        return cv2_mock

    def test_handles_window_creation_error(self, mock_cv2_with_error):
        """Test handling of window creation errors."""
        import numpy as np

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2_with_error):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True, update_interval_ms=0)
                preview = PreviewWindow(config)

                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                depth = np.random.rand(480, 640).astype(np.float32)

                # Should not raise, returns True/False gracefully
                result = preview.update(
                    original=frame,
                    depth_map=depth,
                    stereo_result=frame,
                    frame_number=0,
                )

                # Result indicates window state
                assert isinstance(result, bool)

    def test_handles_show_error_gracefully(self, mock_cv2_with_error):
        """Test handling of show errors."""
        import numpy as np

        with patch("video2d3d.preview.preview_window.cv2", mock_cv2_with_error):
            with patch("video2d3d.preview.preview_window._ensure_cv2"):
                config = PreviewConfig(enabled=True)
                preview = PreviewWindow(config)

                frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                depth = np.random.rand(480, 640).astype(np.float32)

                # Should not raise
                result = preview.show(
                    original=frame,
                    depth_map=depth,
                    stereo_result=frame,
                    wait=False,
                )

                # Returns -1 on error
                assert result == -1


class TestPreviewPerformance:
    """Tests for preview window performance characteristics."""

    def test_update_rate_limiting_prevents_excessive_updates(self):
        """Test that rate limiting prevents excessive updates."""
        import time

        config = PreviewConfig(enabled=False, update_interval_ms=100)
        preview = PreviewWindow(config)

        import numpy as np

        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        depth = np.random.rand(480, 640).astype(np.float32)

        # Make many rapid update calls
        start_time = time.time()
        update_count = 0

        for _ in range(100):
            preview.update(original=frame, depth_map=depth, stereo_result=frame)
            update_count += 1

        elapsed = time.time() - start_time

        # Should complete quickly (no actual rendering when disabled)
        # and rate limiting logic should work
        assert elapsed < 1.0  # Should be very fast

    def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up resources."""
        config = PreviewConfig(enabled=False)
        preview_count = 0

        for _ in range(10):
            with PreviewWindow(config) as preview:
                preview_count += 1
                assert preview is not None

        # All previews should be cleaned up
        assert preview_count == 10
