"""Integration tests for frame extraction system.

These tests verify frame extraction with actual video processing.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import cv2
import numpy as np
import pytest

from video2d3d.video import (
    FrameBuffer,
    FrameExtractor,
    FrameExtractorConfig,
    SamplingStrategy,
    extract_frame_at,
    extract_frames,
)


def create_test_video(
    output_path: Path,
    width: int = 640,
    height: int = 480,
    fps: float = 30.0,
    frame_count: int = 60,
) -> None:
    """Create a simple test video with colored frames.

    Args:
        output_path: Path to save the video.
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frames per second.
        frame_count: Number of frames to generate.
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    for i in range(frame_count):
        # Create a frame with a gradient based on frame number
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Fill with a color that changes with frame number
        r = int((i * 4) % 256)
        g = int((i * 2) % 256)
        b = int((i * 3) % 256)
        frame[:, :] = (b, g, r)  # BGR for OpenCV

        out.write(frame)

    out.release()


@pytest.fixture
def sample_video(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a sample video file for testing."""
    video_path = tmp_path / "test_video.mp4"
    create_test_video(video_path, width=320, height=240, fps=30.0, frame_count=60)
    yield video_path


@pytest.fixture
def large_video(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a larger video for memory tests."""
    video_path = tmp_path / "large_video.mp4"
    create_test_video(video_path, width=640, height=480, fps=30.0, frame_count=300)
    yield video_path


class TestFrameExtractorIntegration:
    """Integration tests for FrameExtractor with real video files."""

    def test_extract_all_frames_real_video(self, sample_video: Path) -> None:
        """Test extracting all frames from a real video."""
        extractor = FrameExtractor(sample_video, validate_video=False)

        frames = list(extractor.extract_frames())
        assert len(frames) == 60

        # Verify frame shapes
        for frame_num, frame in frames:
            assert frame.shape == (240, 320, 3), f"Frame {frame_num} has wrong shape"

    def test_extract_with_interval_real_video(self, sample_video: Path) -> None:
        """Test extracting frames with interval from a real video."""
        extractor = FrameExtractor(
            sample_video,
            sampling_interval=10,
            validate_video=False,
        )

        frames = list(extractor)
        assert len(frames) == 6  # Frames 0, 10, 20, 30, 40, 50

    def test_extract_single_frame_real_video(self, sample_video: Path) -> None:
        """Test extracting a single frame from a real video."""
        frame = extract_frame_at(sample_video, 30)
        assert frame.shape == (240, 320, 3)

    def test_extract_convenience_function(self, sample_video: Path) -> None:
        """Test extract_frames convenience function."""
        frames = list(extract_frames(sample_video, sampling_interval=15))
        assert len(frames) == 4  # Frames 0, 15, 30, 45

    def test_uniform_sampling_real_video(self, sample_video: Path) -> None:
        """Test uniform sampling on a real video."""
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.UNIFORM,
            target_frame_count=10,
        )
        extractor = FrameExtractor(sample_video, config=config, validate_video=False)

        frames = list(extractor)
        assert len(frames) == 10

    def test_keyframe_sampling_real_video(self, sample_video: Path) -> None:
        """Test keyframe sampling on a real video."""
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.KEYFRAME,
        )
        extractor = FrameExtractor(sample_video, config=config, validate_video=False)

        indices = extractor.get_sample_indices()
        # Should use GOP size of 30
        assert len(indices) == 2  # 60 frames / 30 = 2

    def test_frame_preprocessing_resize_real_video(self, sample_video: Path) -> None:
        """Test frame resizing during extraction."""
        extractor = FrameExtractor(
            sample_video,
            resize_width=160,
            resize_height=120,
            validate_video=False,
        )

        frame = extractor.get_frame(0)
        assert frame.shape == (120, 160, 3)

    def test_frame_preprocessing_normalize_real_video(self, sample_video: Path) -> None:
        """Test frame normalization during extraction."""
        config = FrameExtractorConfig(normalize=True)
        extractor = FrameExtractor(sample_video, config=config, validate_video=False)

        frame = extractor.get_frame(0)
        assert frame.dtype == np.float32
        assert frame.max() <= 1.0
        assert frame.min() >= 0.0

    def test_buffer_caching_real_video(self, sample_video: Path) -> None:
        """Test that buffer caching works with real video."""
        extractor = FrameExtractor(sample_video, validate_video=False)

        # Extract same frame twice
        frame1 = extractor.get_frame(10)
        frame2 = extractor.get_frame(10)

        # Should be identical
        np.testing.assert_array_equal(frame1, frame2)

        # Buffer should contain the frame
        stats = extractor.get_buffer_stats()
        assert stats["size"] >= 1

    def test_context_manager_real_video(self, sample_video: Path) -> None:
        """Test context manager with real video."""
        with FrameExtractor(sample_video, validate_video=False) as extractor:
            frame = extractor.get_frame(0)
            assert frame is not None

        # After context exit, buffer should be cleared
        # (can't easily test this without accessing private members)

    def test_extract_range_real_video(self, sample_video: Path) -> None:
        """Test extracting a range of frames from a real video."""
        extractor = FrameExtractor(sample_video, validate_video=False)

        frames = extractor.extract_range(10, 20)
        assert len(frames) == 10

    def test_video_metadata_real_video(self, sample_video: Path) -> None:
        """Test that metadata is correctly extracted from a real video."""
        extractor = FrameExtractor(sample_video, validate_video=False)

        metadata = extractor.metadata
        assert metadata.width == 320
        assert metadata.height == 240
        assert metadata.fps == 30.0
        assert metadata.frame_count == 60

    def test_large_video_memory_efficiency(self, large_video: Path) -> None:
        """Test that large video can be processed without memory issues."""
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.INTERVAL,
            sampling_interval=30,
            buffer_size=5,
            max_memory_mb=50.0,  # Small memory limit
        )

        extractor = FrameExtractor(large_video, config=config, validate_video=False)

        # Process all frames using generator (memory efficient)
        frame_count = 0
        for _frame_num, frame in extractor:
            frame_count += 1
            assert frame is not None

        assert frame_count == 10  # 300 frames / 30 interval

    def test_frame_content_consistency(self, sample_video: Path) -> None:
        """Test that frame content is consistent across multiple extractions."""
        extractor = FrameExtractor(sample_video, validate_video=False)

        # Extract frame 20 three times
        frame1 = extractor.get_frame(20)
        frame2 = extractor.get_frame(20)
        extractor.clear_buffer()  # Clear buffer
        frame3 = extractor.get_frame(20)

        # All should be identical
        np.testing.assert_array_equal(frame1, frame2)
        np.testing.assert_array_equal(frame1, frame3)


class TestFrameBufferIntegration:
    """Integration tests for FrameBuffer with real frames."""

    def test_buffer_with_real_frames(self, sample_video: Path) -> None:
        """Test buffer with real video frames."""
        buffer = FrameBuffer(max_size=10, max_memory_mb=100.0)

        # Extract some frames and add to buffer
        extractor = FrameExtractor(sample_video, validate_video=False)

        for i in range(5):
            frame = extractor.get_frame(i)
            buffer.put(i, frame)

        assert buffer.size == 5

        # Retrieve frames from buffer
        for i in range(5):
            cached = buffer.get(i)
            assert cached is not None
            np.testing.assert_array_equal(cached, extractor.get_frame(i))

    def test_buffer_eviction_with_real_frames(self, sample_video: Path) -> None:
        """Test buffer eviction with real frames."""
        buffer = FrameBuffer(max_size=3, max_memory_mb=100.0)

        extractor = FrameExtractor(sample_video, validate_video=False)

        # Add more frames than buffer can hold
        for i in range(5):
            frame = extractor.get_frame(i)
            buffer.put(i, frame)

        # Only last 3 frames should remain
        assert buffer.size == 3
        assert not buffer.contains(0)
        assert not buffer.contains(1)
        assert buffer.contains(2)
        assert buffer.contains(3)
        assert buffer.contains(4)


class TestEndToEndScenarios:
    """End-to-end test scenarios for frame extraction."""

    def test_complete_extraction_workflow(self, sample_video: Path) -> None:
        """Test a complete frame extraction workflow."""
        # 1. Create configuration
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.UNIFORM,
            target_frame_count=20,
            convert_to_rgb=True,
        )

        # 2. Initialize extractor
        with FrameExtractor(sample_video, config=config, validate_video=False) as extractor:
            # 3. Verify metadata
            assert extractor.metadata.frame_count == 60

            # 4. Extract frames
            frames = []
            for frame_num, frame in extractor:
                frames.append((frame_num, frame))

            # 5. Verify results
            assert len(frames) == 20

            # 6. Check buffer stats
            stats = extractor.get_buffer_stats()
            assert stats["size"] <= config.buffer_size

    def test_video_thumbnail_extraction(self, sample_video: Path) -> None:
        """Test extracting thumbnails from a video (common use case)."""
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.UNIFORM,
            target_frame_count=5,
            resize_width=160,
            resize_height=120,
        )

        with FrameExtractor(sample_video, config=config, validate_video=False) as extractor:
            thumbnails = [frame for _, frame in extractor]

            assert len(thumbnails) == 5
            for thumb in thumbnails:
                assert thumb.shape == (120, 160, 3)

    def test_video_analysis_workflow(self, sample_video: Path) -> None:
        """Test a video analysis workflow (common use case)."""
        # Extract keyframes for analysis
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.KEYFRAME,
            convert_to_rgb=True,
            normalize=True,
        )

        with FrameExtractor(sample_video, config=config, validate_video=False) as extractor:
            keyframes = []
            for frame_num, frame in extractor:
                # Simulate some analysis
                mean_color = frame.mean(axis=(0, 1))
                keyframes.append(
                    {
                        "frame_num": frame_num,
                        "mean_color": mean_color,
                    }
                )

            assert len(keyframes) >= 1
            for kf in keyframes:
                assert "frame_num" in kf
                assert "mean_color" in kf
                assert len(kf["mean_color"]) == 3
