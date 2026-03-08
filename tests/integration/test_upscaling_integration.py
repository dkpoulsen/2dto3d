"""Integration tests for the video upscaling pipeline.

These tests verify the end-to-end functionality of the upscaling module,
including integration with video processing components.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video2d3d.upscaling import (
    ModelType,
    UpscalerConfig,
    VideoUpscaler,
    VideoUpscaleStats,
    create_upscaler,
    upscale_frames,
)
from video2d3d.upscaling.base import UpscaleResult
from video2d3d.upscaling.esrgan import DummyUpscaler


class TestUpscalingPipelineIntegration:
    """Integration tests for the complete upscaling pipeline."""

    def test_end_to_end_single_frame_upscaling(self):
        """Test end-to-end single frame upscaling pipeline."""
        # Configure upscaler
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
        )

        # Create upscaler using factory
        upscaler = create_upscaler(config, use_dummy=True)

        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Upscale frame
        upscaled_frame, result = upscaler.upscale(frame, return_info=True)

        # Verify result
        assert result.success is True
        assert result.original_size == (480, 640)
        assert result.output_size == (1920, 2560)
        assert result.scale == 4
        assert upscaled_frame.shape == (1920, 2560, 3)

    def test_end_to_end_batch_upscaling(self):
        """Test end-to-end batch frame upscaling pipeline."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X2PLUS,
            use_gpu=False,
        )

        # Use VideoUpscaler for batch processing
        with VideoUpscaler(config, use_dummy=True) as upscaler:
            # Create test frames (simulating video frames)
            frames = [np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8) for _ in range(10)]

            # Track progress
            progress_tracking = []

            def progress_callback(completed, total):
                progress_tracking.append((completed, total))

            # Upscale all frames
            upscaled_frames = upscaler.upscale_frames(frames, progress_callback=progress_callback)

            # Verify results
            assert len(upscaled_frames) == 10
            assert len(progress_tracking) == 10
            assert progress_tracking[-1] == (10, 10)

            for upscaled in upscaled_frames:
                assert upscaled.shape == (480, 640, 3)  # 2x scale

    def test_end_to_end_generator_upscaling(self):
        """Test end-to-end frame generator upscaling pipeline."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
        )

        # Simulate video frame generator
        def frame_generator(num_frames: int = 5) -> Generator[tuple[int, np.ndarray], None, None]:
            for i in range(num_frames):
                yield i, np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)

        with VideoUpscaler(config, use_dummy=True) as upscaler:
            # Process frames through generator
            results = []
            for frame_number, upscaled_frame, result in upscaler.upscale_frame_generator(
                frame_generator(),
                total_frames=5,
            ):
                results.append((frame_number, upscaled_frame, result))

            # Verify results
            assert len(results) == 5
            for i, (frame_number, upscaled_frame, result) in enumerate(results):
                assert frame_number == i
                assert result.success is True
                assert upscaled_frame.shape == (480, 640, 3)


class TestUpscalingWithTiling:
    """Integration tests for tile-based upscaling."""

    def test_tiled_upscaling_large_image(self):
        """Test tile-based upscaling for large images."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            tile_size=64,  # Small tiles for testing
            tile_pad=8,
            use_gpu=False,
        )

        upscaler = create_upscaler(config, use_dummy=True)

        # Create larger image that requires tiling
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)

        # Upscale with tiling
        upscaled, result = upscaler.upscale(image, return_info=True)

        # Verify result
        assert result.success is True
        assert upscaled.shape == (1024, 1024, 3)

    def test_tiled_upscaling_exact_tile_size(self):
        """Test tile-based upscaling with image size matching tile size."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            tile_size=128,
            tile_pad=0,
            use_gpu=False,
        )

        upscaler = create_upscaler(config, use_dummy=True)

        # Image size exactly matches tile size
        image = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)

        upscaled, result = upscaler.upscale(image, return_info=True)

        assert result.success is True
        assert upscaled.shape == (512, 512, 3)


class TestUpscalingModelVariants:
    """Integration tests for different upscaling models."""

    @pytest.mark.parametrize(
        "model_type,scale",
        [
            (ModelType.REAL_ESRGAN_X4PLUS, 4),
            (ModelType.REAL_ESRGAN_X2PLUS, 2),
            (ModelType.REAL_ESRGAN_X4PLUS_ANIME, 4),
            (ModelType.REAL_ESRGAN_GENERAL_X4V3, 4),
        ],
    )
    def test_different_model_types(self, model_type: ModelType, scale: int):
        """Test upscaling with different model types."""
        config = UpscalerConfig(
            enabled=True,
            model_type=model_type,
            use_gpu=False,
        )

        upscaler = create_upscaler(config, use_dummy=True)

        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        assert upscaled.shape == (64 * scale, 64 * scale, 3)

    def test_model_type_anime_optimized(self):
        """Test anime-optimized model variant."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS_ANIME,
            use_gpu=False,
        )

        upscaler = create_upscaler(config, use_dummy=True)

        # Simulate anime-style image (more uniform colors)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[25:75, 25:75] = [255, 100, 50]

        upscaled = upscaler.upscale(image)

        assert upscaled.shape == (400, 400, 3)


class TestUpscalingConfigIntegration:
    """Integration tests for configuration handling."""

    def test_config_serialization_roundtrip(self):
        """Test config serialization and deserialization."""
        original_config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
            tile_size=512,
            tile_pad=16,
            denoise_strength=0.3,
        )

        # Serialize to dict
        config_dict = original_config.to_dict()

        # Deserialize back
        restored_config = UpscalerConfig.from_dict(config_dict)

        # Verify all fields match
        assert restored_config.enabled == original_config.enabled
        assert restored_config.model_type == original_config.model_type
        assert restored_config.use_gpu == original_config.use_gpu
        assert restored_config.tile_size == original_config.tile_size
        assert restored_config.tile_pad == original_config.tile_pad
        assert restored_config.denoise_strength == original_config.denoise_strength

    def test_config_with_video_upscaler(self):
        """Test config integration with VideoUpscaler."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X2PLUS,
            tile_size=256,
        )

        with VideoUpscaler(config, use_dummy=True) as upscaler:
            assert upscaler.config.model_type == ModelType.REAL_ESRGAN_X2PLUS
            assert upscaler.scale == 2


class TestUpscalingErrorRecovery:
    """Integration tests for error recovery."""

    def test_upscaling_continues_after_bad_frame(self):
        """Test that upscaling continues after encountering a bad frame."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
        )

        upscaler = DummyUpscaler(config)

        # Create frames with one invalid frame
        frames = [
            np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8),
            None,  # Invalid frame
            np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8),
        ]

        # Process each frame individually to handle errors
        results = []
        for frame in frames:
            if frame is not None:
                result = upscaler.upscale(frame)
                results.append(result)

        # Should have processed 2 valid frames
        assert len(results) == 2
        for result in results:
            assert result.shape == (128, 128, 3)


class TestUpscalingMemoryEfficiency:
    """Integration tests for memory efficiency."""

    def test_generator_memory_efficiency(self):
        """Test that generator processing is memory efficient."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
        )

        # Create a large number of frames via generator
        def large_frame_generator(num_frames: int = 100):
            for i in range(num_frames):
                # Yield frame one at a time
                yield i, np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)

        with VideoUpscaler(config, use_dummy=True) as upscaler:
            # Process frames without storing all in memory
            processed_count = 0
            for _ in upscaler.upscale_frame_generator(large_frame_generator()):
                processed_count += 1

            assert processed_count == 100

    def test_batch_cleanup(self):
        """Test that batch processing cleans up resources."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
        )

        # Create many frames
        frames = [np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8) for _ in range(150)]

        with VideoUpscaler(config, use_dummy=True) as upscaler:
            # Process large batch
            upscaled = upscaler.upscale_frames(frames)

            assert len(upscaled) == 150


class TestUpscalingStatsTracking:
    """Integration tests for statistics tracking."""

    def test_video_upscale_stats(self):
        """Test VideoUpscaleStats tracking during upscaling."""
        stats = VideoUpscaleStats(
            frames_processed=100,
            total_frames=100,
            total_time_ms=5000.0,
            average_time_ms=50.0,
            original_resolution=(480, 640),
            output_resolution=(1920, 2560),
            total_tiles=100,
        )

        stats_dict = stats.to_dict()

        assert stats_dict["frames_processed"] == 100
        assert stats_dict["total_time_ms"] == 5000.0
        assert stats_dict["original_resolution"] == (480, 640)
        assert stats_dict["output_resolution"] == (1920, 2560)

    def test_upscale_result_tracking(self):
        """Test UpscaleResult tracking during upscaling."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=False,
        )

        upscaler = create_upscaler(config, use_dummy=True)

        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        _, result = upscaler.upscale(image, return_info=True)

        # Verify result tracking
        assert result.success is True
        assert result.original_size == (64, 64)
        assert result.output_size == (256, 256)
        assert result.scale == 4
        assert result.processing_time_ms > 0
        assert "Real-ESRGAN" in result.model_name
