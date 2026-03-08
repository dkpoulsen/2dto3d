"""Unit tests for the video upscaler processor module."""

from __future__ import annotations

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video2d3d.upscaling.config import ModelType, UpscalerConfig
from video2d3d.upscaling.processor import (
    VideoUpscaleStats,
    VideoUpscaler,
    upscale_frames,
    upscale_video,
)


class TestVideoUpscaleStats:
    """Tests for VideoUpscaleStats dataclass."""

    def test_default_stats(self):
        """Test default stats values."""
        stats = VideoUpscaleStats()

        assert stats.frames_processed == 0
        assert stats.total_frames == 0
        assert stats.total_time_ms == 0.0
        assert stats.average_time_ms == 0.0
        assert stats.original_resolution == (0, 0)
        assert stats.output_resolution == (0, 0)
        assert stats.total_tiles == 0
        assert stats.memory_peak_mb == 0.0

    def test_stats_to_dict(self):
        """Test stats serialization to dictionary."""
        stats = VideoUpscaleStats(
            frames_processed=100,
            total_frames=100,
            total_time_ms=5000.0,
            average_time_ms=50.0,
            original_resolution=(480, 640),
            output_resolution=(1920, 2560),
            total_tiles=400,
            memory_peak_mb=2048.0,
        )

        d = stats.to_dict()

        assert d["frames_processed"] == 100
        assert d["total_frames"] == 100
        assert d["total_time_ms"] == 5000.0
        assert d["average_time_ms"] == 50.0
        assert d["original_resolution"] == (480, 640)
        assert d["output_resolution"] == (1920, 2560)
        assert d["total_tiles"] == 400
        assert d["memory_peak_mb"] == 2048.0

    def test_stats_with_calculated_average(self):
        """Test stats with calculated average time."""
        stats = VideoUpscaleStats(
            frames_processed=50,
            total_time_ms=2500.0,
        )

        # Average should be calculated manually
        expected_avg = 2500.0 / 50
        assert stats.average_time_ms == 0.0  # Not auto-calculated
        # Manual verification
        assert expected_avg == 50.0


class TestVideoUpscaler:
    """Tests for the VideoUpscaler class."""

    def test_video_upscaler_initialization(self):
        """Test VideoUpscaler initializes correctly."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        assert upscaler.config == config
        assert upscaler._use_dummy is True
        assert upscaler._is_initialized is False

    def test_video_upscaler_initialize(self):
        """Test VideoUpscaler initialize method."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        upscaler.initialize()

        assert upscaler._is_initialized is True
        assert upscaler._upscaler is not None

    def test_video_upscaler_double_initialize(self):
        """Test that double initialization doesn't reload model."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        upscaler.initialize()

        first_upscaler = upscaler._upscaler
        upscaler.initialize()  # Second call

        assert upscaler._upscaler is first_upscaler

    def test_video_upscaler_scale_property(self):
        """Test VideoUpscaler scale property."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X2PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        assert upscaler.scale == 2

    def test_video_upscaler_is_initialized_property(self):
        """Test VideoUpscaler is_initialized property."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        assert upscaler.is_initialized is False

        upscaler.initialize()
        assert upscaler.is_initialized is True

    def test_upscale_frame(self):
        """Test upscaling a single frame."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        frame = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        upscaled = upscaler.upscale_frame(frame)

        assert upscaled.shape == (256, 256, 3)

    def test_upscale_frame_auto_initialize(self):
        """Test that upscale_frame auto-initializes."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        assert upscaler._is_initialized is False

        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        upscaler.upscale_frame(frame)

        assert upscaler._is_initialized is True

    def test_upscale_frames(self):
        """Test upscaling multiple frames."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        frames = [np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8) for _ in range(5)]

        upscaled = upscaler.upscale_frames(frames)

        assert len(upscaled) == 5
        for frame in upscaled:
            assert frame.shape == (128, 128, 3)

    def test_upscale_frames_with_progress(self):
        """Test upscaling frames with progress callback."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        frames = [np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8) for _ in range(3)]

        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        upscaler.upscale_frames(frames, progress_callback=progress_callback)

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    def test_upscale_frame_generator(self):
        """Test upscaling frames from a generator."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        def frame_generator() -> Generator[tuple[int, np.ndarray], None, None]:
            for i in range(3):
                yield i, np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)

        results = list(upscaler.upscale_frame_generator(frame_generator(), total_frames=3))

        assert len(results) == 3
        for frame_number, upscaled_frame, result in results:
            assert isinstance(frame_number, int)
            assert upscaled_frame.shape == (128, 128, 3)
            assert result.success is True

    def test_upscale_frame_generator_with_progress(self):
        """Test generator upscaling with progress callback."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        def frame_generator() -> Generator[tuple[int, np.ndarray], None, None]:
            for i in range(3):
                yield i, np.zeros((16, 16, 3), dtype=np.uint8)

        progress_calls = []

        def progress_callback(frame_number, completed, total):
            progress_calls.append((frame_number, completed, total))

        list(
            upscaler.upscale_frame_generator(
                frame_generator(),
                progress_callback=progress_callback,
                total_frames=3,
            )
        )

        assert len(progress_calls) == 3

    def test_upscale_frame_generator_empty(self):
        """Test generator with no frames."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        def empty_generator() -> Generator[tuple[int, np.ndarray], None, None]:
            return
            yield  # Never reached

        results = list(upscaler.upscale_frame_generator(empty_generator()))

        assert len(results) == 0

    def test_video_upscaler_cleanup(self):
        """Test VideoUpscaler cleanup method."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        upscaler.initialize()

        assert upscaler._upscaler is not None

        upscaler.cleanup()

        assert upscaler._upscaler is None
        assert upscaler._is_initialized is False

    def test_video_upscaler_context_manager(self):
        """Test VideoUpscaler as context manager."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with VideoUpscaler(config, use_dummy=True) as upscaler:
            assert upscaler.is_initialized is True

            frame = np.zeros((32, 32, 3), dtype=np.uint8)
            upscaled = upscaler.upscale_frame(frame)

            assert upscaled.shape == (128, 128, 3)

        # After context exit, should be cleaned up
        assert upscaler._is_initialized is False


class TestUpscaleFramesFunction:
    """Tests for the upscale_frames convenience function."""

    def test_upscale_frames_default_config(self):
        """Test upscale_frames with default config."""
        frames = [np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8) for _ in range(3)]

        # Patch VideoUpscaler to use dummy
        with patch("video2d3d.upscaling.processor.VideoUpscaler") as MockUpscaler:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.upscale_frames.return_value = [
                np.zeros((128, 128, 3), dtype=np.uint8) for _ in range(3)
            ]
            MockUpscaler.return_value = mock_instance

            result = upscale_frames(frames, use_dummy=True)

        assert len(result) == 3

    def test_upscale_frames_custom_config(self):
        """Test upscale_frames with custom config."""
        config = UpscalerConfig(
            model_type=ModelType.REAL_ESRGAN_X2PLUS,
            use_gpu=False,
        )
        frames = [np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8) for _ in range(2)]

        with patch("video2d3d.upscaling.processor.VideoUpscaler") as MockUpscaler:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.upscale_frames.return_value = [
                np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(2)
            ]
            MockUpscaler.return_value = mock_instance

            result = upscale_frames(frames, config=config)

            MockUpscaler.assert_called_once_with(config)


class TestUpscaleVideoFunction:
    """Tests for the upscale_video convenience function."""

    def test_upscale_video_default_config(self, tmp_path):
        """Test upscale_video with default config."""
        input_path = tmp_path / "input.mp4"
        output_path = tmp_path / "output.mp4"

        # Create dummy input file
        input_path.touch()

        with patch("video2d3d.upscaling.processor.VideoUpscaler") as MockUpscaler:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.upscale_video.return_value = VideoUpscaleStats(
                frames_processed=100,
                total_frames=100,
            )
            MockUpscaler.return_value = mock_instance

            stats = upscale_video(input_path, output_path)

        assert stats.frames_processed == 100

    def test_upscale_video_custom_config(self, tmp_path):
        """Test upscale_video with custom config."""
        input_path = tmp_path / "input.mp4"
        output_path = tmp_path / "output.mp4"
        input_path.touch()

        config = UpscalerConfig(
            model_type=ModelType.REAL_ESRGAN_X2PLUS,
            tile_size=256,
        )

        with patch("video2d3d.upscaling.processor.VideoUpscaler") as MockUpscaler:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.upscale_video.return_value = VideoUpscaleStats()
            MockUpscaler.return_value = mock_instance

            upscale_video(input_path, output_path, config=config)

            MockUpscaler.assert_called_once_with(config)

    def test_upscale_video_with_progress(self, tmp_path):
        """Test upscale_video with progress callback."""
        input_path = tmp_path / "input.mp4"
        output_path = tmp_path / "output.mp4"
        input_path.touch()

        progress_calls = []

        def progress_callback(stage, current, total):
            progress_calls.append((stage, current, total))

        with patch("video2d3d.upscaling.processor.VideoUpscaler") as MockUpscaler:
            mock_instance = MagicMock()
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.upscale_video.return_value = VideoUpscaleStats()
            MockUpscaler.return_value = mock_instance

            upscale_video(input_path, output_path, progress_callback=progress_callback)

            # Verify the upscaler's upscale_video was called
            mock_instance.upscale_video.assert_called_once()


class TestVideoUpscalerErrorHandling:
    """Tests for error handling in VideoUpscaler."""

    def test_upscale_frame_not_initialized_error(self):
        """Test error when upscaler not properly initialized."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        # Don't initialize
        upscaler._upscaler = None
        upscaler._is_initialized = True  # Force initialized without upscaler

        frame = np.zeros((32, 32, 3), dtype=np.uint8)

        with pytest.raises(RuntimeError, match="Upscaler not initialized"):
            upscaler.upscale_frame(frame)

    def test_upscale_frames_not_initialized_error(self):
        """Test error when upscaler not properly initialized for batch."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        upscaler._upscaler = None
        upscaler._is_initialized = True

        frames = [np.zeros((32, 32, 3), dtype=np.uint8)]

        with pytest.raises(RuntimeError, match="Upscaler not initialized"):
            upscaler.upscale_frames(frames)

    def test_upscale_generator_not_initialized_error(self):
        """Test error when upscaler not properly initialized for generator."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        upscaler._upscaler = None
        upscaler._is_initialized = True

        def gen():
            yield 0, np.zeros((32, 32, 3), dtype=np.uint8)

        with pytest.raises(RuntimeError, match="Upscaler not initialized"):
            list(upscaler.upscale_frame_generator(gen()))


class TestVideoUpscalerMemoryManagement:
    """Tests for memory management in VideoUpscaler."""

    def test_periodic_gc_during_batch(self):
        """Test that periodic garbage collection is triggered."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        # Create enough frames to trigger GC (100+ frames)
        frames = [np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8) for _ in range(105)]

        with patch("video2d3d.upscaling.processor.gc.collect") as mock_gc:
            upscaler.upscale_frames(frames)

            # GC should be called once for 105 frames (at frame 100)
            mock_gc.assert_called_once()

    def test_periodic_gc_during_generator(self):
        """Test that periodic garbage collection is triggered during generator processing."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)

        def frame_generator():
            for i in range(105):
                yield i, np.zeros((16, 16, 3), dtype=np.uint8)

        with patch("video2d3d.upscaling.processor.gc.collect") as mock_gc:
            list(upscaler.upscale_frame_generator(frame_generator()))

            # GC should be called once for 105 frames
            mock_gc.assert_called_once()

    def test_cleanup_calls_gc(self):
        """Test that cleanup triggers garbage collection."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = VideoUpscaler(config, use_dummy=True)
        upscaler.initialize()

        with patch("video2d3d.upscaling.processor.gc.collect") as mock_gc:
            upscaler.cleanup()

            mock_gc.assert_called_once()
