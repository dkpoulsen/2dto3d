"""Unit tests for frame extraction system."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from video2d3d.video import (
    FrameBuffer,
    FrameBufferError,
    FrameExtractionError,
    FrameExtractor,
    FrameExtractorConfig,
    FrameInfo,
    InvalidSamplingStrategyError,
    MemoryLimitExceededError,
    SamplingStrategy,
    VideoFileNotFoundError,
    extract_frame_at,
    extract_frames,
)


# Fixtures
@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Create a sample video file path."""
    return tmp_path / "sample.mp4"


@pytest.fixture
def frame_extractor_config() -> FrameExtractorConfig:
    """Create a sample frame extractor configuration."""
    return FrameExtractorConfig(
        sampling_strategy=SamplingStrategy.ALL,
        sampling_interval=1,
        buffer_size=10,
        max_memory_mb=100.0,
        convert_to_rgb=True,
        normalize=False,
    )


@pytest.fixture
def mock_video_capture() -> Generator[MagicMock, None, None]:
    """Mock OpenCV VideoCapture for testing."""
    with patch("cv2.VideoCapture") as mock_cap_class:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 100,
        }.get(prop, 0)

        # Create a sample frame
        sample_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, sample_frame)
        mock_cap_class.return_value = mock_cap
        yield mock_cap


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a sample frame for testing."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


# Tests for SamplingStrategy enum
class TestSamplingStrategy:
    """Tests for SamplingStrategy enum."""

    def test_sampling_strategy_values(self) -> None:
        """Test that all expected strategies are defined."""
        assert SamplingStrategy.ALL.value == "all"
        assert SamplingStrategy.INTERVAL.value == "interval"
        assert SamplingStrategy.UNIFORM.value == "uniform"
        assert SamplingStrategy.KEYFRAME.value == "keyframe"
        assert SamplingStrategy.CUSTOM.value == "custom"


# Tests for FrameExtractorConfig
class TestFrameExtractorConfig:
    """Tests for FrameExtractorConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = FrameExtractorConfig()
        assert config.sampling_strategy == SamplingStrategy.ALL
        assert config.sampling_interval == 1
        assert config.target_frame_count is None
        assert config.buffer_size == 100
        assert config.max_memory_mb == 1024.0
        assert config.convert_to_rgb is True
        assert config.normalize is False

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.INTERVAL,
            sampling_interval=10,
            buffer_size=50,
            max_memory_mb=512.0,
            resize_width=320,
            resize_height=240,
            convert_to_rgb=False,
            normalize=True,
        )
        assert config.sampling_strategy == SamplingStrategy.INTERVAL
        assert config.sampling_interval == 10
        assert config.buffer_size == 50
        assert config.max_memory_mb == 512.0
        assert config.resize_width == 320
        assert config.resize_height == 240
        assert config.convert_to_rgb is False
        assert config.normalize is True

    def test_invalid_sampling_interval(self) -> None:
        """Test that invalid sampling_interval raises ValueError."""
        with pytest.raises(ValueError, match="sampling_interval"):
            FrameExtractorConfig(sampling_interval=0)
        with pytest.raises(ValueError, match="sampling_interval"):
            FrameExtractorConfig(sampling_interval=-1)

    def test_invalid_target_frame_count(self) -> None:
        """Test that invalid target_frame_count raises ValueError."""
        with pytest.raises(ValueError, match="target_frame_count"):
            FrameExtractorConfig(target_frame_count=0)
        with pytest.raises(ValueError, match="target_frame_count"):
            FrameExtractorConfig(target_frame_count=-1)

    def test_invalid_buffer_size(self) -> None:
        """Test that invalid buffer_size raises ValueError."""
        with pytest.raises(ValueError, match="buffer_size"):
            FrameExtractorConfig(buffer_size=0)
        with pytest.raises(ValueError, match="buffer_size"):
            FrameExtractorConfig(buffer_size=-1)

    def test_invalid_max_memory_mb(self) -> None:
        """Test that invalid max_memory_mb raises ValueError."""
        with pytest.raises(ValueError, match="max_memory_mb"):
            FrameExtractorConfig(max_memory_mb=0)
        with pytest.raises(ValueError, match="max_memory_mb"):
            FrameExtractorConfig(max_memory_mb=-1)


# Tests for FrameInfo
class TestFrameInfo:
    """Tests for FrameInfo dataclass."""

    def test_frame_info_creation(self) -> None:
        """Test creating FrameInfo instance."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        info = FrameInfo(
            frame_number=10,
            timestamp=0.33,
            frame=frame,
            is_keyframe=True,
        )
        assert info.frame_number == 10
        assert info.timestamp == 0.33
        assert info.is_keyframe is True
        assert info.is_loaded is True

    def test_frame_info_not_loaded(self) -> None:
        """Test FrameInfo without frame data."""
        info = FrameInfo(frame_number=5, timestamp=0.16)
        assert info.frame is None
        assert info.is_loaded is False


# Tests for FrameBuffer
class TestFrameBuffer:
    """Tests for FrameBuffer class."""

    def test_buffer_creation(self) -> None:
        """Test creating FrameBuffer instance."""
        buffer = FrameBuffer(max_size=10, max_memory_mb=100.0)
        assert buffer.max_size == 10
        assert buffer.max_memory_mb == 100.0
        assert buffer.size == 0

    def test_buffer_put_and_get(self, sample_frame: np.ndarray) -> None:
        """Test adding and retrieving frames from buffer."""
        buffer = FrameBuffer(max_size=10, max_memory_mb=100.0)

        buffer.put(0, sample_frame)
        assert buffer.size == 1
        assert buffer.contains(0)

        retrieved = buffer.get(0)
        assert retrieved is not None
        np.testing.assert_array_equal(retrieved, sample_frame)

    def test_buffer_eviction(self, sample_frame: np.ndarray) -> None:
        """Test that buffer evicts oldest frames when full."""
        buffer = FrameBuffer(max_size=3, max_memory_mb=100.0)

        for i in range(5):
            buffer.put(i, sample_frame.copy())

        # First two frames should be evicted
        assert buffer.size == 3
        assert not buffer.contains(0)
        assert not buffer.contains(1)
        assert buffer.contains(2)
        assert buffer.contains(3)
        assert buffer.contains(4)

    def test_buffer_clear(self, sample_frame: np.ndarray) -> None:
        """Test clearing the buffer."""
        buffer = FrameBuffer(max_size=10, max_memory_mb=100.0)

        for i in range(5):
            buffer.put(i, sample_frame.copy())

        assert buffer.size == 5
        buffer.clear()
        assert buffer.size == 0

    def test_buffer_memory_limit(self, sample_frame: np.ndarray) -> None:
        """Test buffer respects memory limit."""
        # Create a very small memory limit
        buffer = FrameBuffer(max_size=100, max_memory_mb=0.001)

        # Should raise error for large frame
        large_frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
        with pytest.raises(FrameBufferError):
            buffer.put(0, large_frame)

    def test_buffer_stats(self, sample_frame: np.ndarray) -> None:
        """Test buffer statistics."""
        buffer = FrameBuffer(max_size=10, max_memory_mb=100.0)

        for i in range(3):
            buffer.put(i, sample_frame.copy())

        stats = buffer.get_stats()
        assert stats["size"] == 3
        assert stats["max_size"] == 10
        assert stats["memory_mb"] > 0
        assert stats["utilization"] == 0.3


# Tests for FrameExtractor
class TestFrameExtractor:
    """Tests for FrameExtractor class."""

    def test_extractor_missing_file(self) -> None:
        """Test that missing file raises error."""
        with pytest.raises(VideoFileNotFoundError):
            FrameExtractor("/nonexistent/video.mp4")

    def test_extractor_with_config(
        self,
        sample_video_path: Path,
        frame_extractor_config: FrameExtractorConfig,
        mock_video_capture: MagicMock,
    ) -> None:
        """Test creating extractor with configuration."""
        sample_video_path.touch()

        with patch.object(FrameExtractor, "_validate_video"):  # Skip validation for test
            extractor = FrameExtractor(
                sample_video_path,
                config=frame_extractor_config,
                validate_video=False,
            )
            assert extractor.config == frame_extractor_config

    def test_extractor_with_params(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test creating extractor with individual parameters."""
        sample_video_path.touch()

        extractor = FrameExtractor(
            sample_video_path,
            sampling_interval=5,
            resize_width=320,
            resize_height=240,
            validate_video=False,
        )

        assert extractor.config.sampling_interval == 5
        assert extractor.config.resize_width == 320
        assert extractor.config.resize_height == 240

    def test_extract_single_frame(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extracting a single frame."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        frame = extractor.get_frame(0)

        assert frame is not None
        assert isinstance(frame, np.ndarray)

    def test_extract_frame_out_of_range(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extracting frame with invalid index."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)

        with pytest.raises(FrameExtractionError):
            extractor.get_frame(1000)  # Beyond video length

    def test_extract_frames_generator(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extracting frames as generator."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        frames = list(extractor.extract_frames(end_frame=5))

        assert len(frames) == 5
        for i, (frame_num, frame) in enumerate(frames):
            assert frame_num == i
            assert isinstance(frame, np.ndarray)

    def test_sampling_interval(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test frame extraction with sampling interval."""
        sample_video_path.touch()

        extractor = FrameExtractor(
            sample_video_path,
            sampling_interval=10,
            validate_video=False,
        )

        indices = extractor.get_sample_indices()
        assert indices[0] == 0
        assert indices[1] == 10
        assert indices[2] == 20

    def test_sampling_uniform(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test uniform frame sampling."""
        sample_video_path.touch()

        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.UNIFORM,
            target_frame_count=10,
        )

        extractor = FrameExtractor(
            sample_video_path,
            config=config,
            validate_video=False,
        )

        indices = extractor.get_sample_indices()
        assert len(indices) == 10

    def test_sampling_keyframe(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test keyframe sampling strategy."""
        sample_video_path.touch()

        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.KEYFRAME,
        )

        extractor = FrameExtractor(
            sample_video_path,
            config=config,
            validate_video=False,
        )

        indices = extractor.get_sample_indices()
        # Keyframe uses DEFAULT_ESTIMATED_GOP_SIZE (30) as interval
        assert len(indices) == 4  # 100 frames / 30 = ~3.33, so 4 indices (0, 30, 60, 90)
        assert indices[0] == 0
        assert indices[1] == 30
        assert indices[2] == 60
        assert indices[3] == 90

    def test_negative_frame_index(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test that negative frame index raises error."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)

        with pytest.raises(FrameExtractionError, match="out of range"):
            extractor.get_frame(-1)

    def test_negative_frame_info(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test that negative frame index in get_frame_info raises error."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)

        with pytest.raises(FrameExtractionError, match="out of range"):
            extractor.get_frame_info(-1)

    def test_len(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test __len__ returns correct frame count."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        assert len(extractor) == 100  # Total frames from mock

    def test_iterator(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test iterator protocol."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        count = 0
        for _ in extractor:
            count += 1
            if count >= 5:
                break

        assert count == 5

    def test_context_manager(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test context manager protocol."""
        sample_video_path.touch()

        with FrameExtractor(sample_video_path, validate_video=False) as extractor:
            frame = extractor.get_frame(0)
            assert frame is not None

    def test_get_frame_info(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test getting frame info without loading frame."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        info = extractor.get_frame_info(10)

        assert info.frame_number == 10
        assert info.timestamp == pytest.approx(10 / 30.0, rel=0.01)

    def test_seek_and_tell(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test seek and tell methods."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        extractor.seek(50)
        assert extractor.tell() == 50

    def test_clear_buffer(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test clearing buffer."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        extractor.get_frame(0)  # Load a frame to buffer

        extractor.clear_buffer()
        stats = extractor.get_buffer_stats()
        assert stats["size"] == 0

    def test_memory_limit_exceeded(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test memory limit exceeded error."""
        sample_video_path.touch()

        config = FrameExtractorConfig(
            max_memory_mb=0.001,  # Very small limit
        )

        extractor = FrameExtractor(
            sample_video_path,
            config=config,
            validate_video=False,
        )

        with pytest.raises(MemoryLimitExceededError):
            extractor.extract_all()

    def test_extract_range(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test extracting a range of frames."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        frames = extractor.extract_range(0, 5)

        assert len(frames) == 5
        assert all(isinstance(f, np.ndarray) for f in frames)


# Tests for FrameExtractionError
class TestFrameExtractionError:
    """Tests for FrameExtractionError exception."""

    def test_error_basic(self) -> None:
        """Test basic FrameExtractionError."""
        error = FrameExtractionError(
            file_path=Path("/test/video.mp4"),
        )
        assert "Failed to extract frame" in str(error)

    def test_error_with_frame_number(self) -> None:
        """Test error with frame number."""
        error = FrameExtractionError(
            file_path=Path("/test/video.mp4"),
            frame_number=42,
        )
        assert "42" in str(error)

    def test_error_with_reason(self) -> None:
        """Test error with reason."""
        error = FrameExtractionError(
            file_path=Path("/test/video.mp4"),
            frame_number=42,
            reason="Corrupted data",
        )
        assert "Corrupted data" in str(error)


# Tests for MemoryLimitExceededError
class TestMemoryLimitExceededError:
    """Tests for MemoryLimitExceededError exception."""

    def test_memory_error(self) -> None:
        """Test MemoryLimitExceededError."""
        error = MemoryLimitExceededError(
            file_path=Path("/test/video.mp4"),
            required_mb=500.0,
            available_mb=256.0,
        )
        assert "500" in str(error)
        assert "256" in str(error)
        assert error.required_mb == 500.0
        assert error.available_mb == 256.0


# Tests for InvalidSamplingStrategyError
class TestInvalidSamplingStrategyError:
    """Tests for InvalidSamplingStrategyError exception."""

    def test_invalid_strategy(self) -> None:
        """Test InvalidSamplingStrategyError."""
        error = InvalidSamplingStrategyError(
            strategy="invalid",
            valid_strategies=["all", "interval", "uniform"],
        )
        assert "invalid" in str(error)
        assert "all" in str(error)
        assert error.strategy == "invalid"


# Tests for convenience functions
class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_extract_frames_function(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extract_frames convenience function."""
        sample_video_path.touch()

        frames = list(extract_frames(sample_video_path, sampling_interval=10, end_frame=30))
        assert len(frames) == 3  # Frames 0, 10, 20

    def test_extract_frame_at_function(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extract_frame_at convenience function."""
        sample_video_path.touch()

        frame = extract_frame_at(sample_video_path, 5)
        assert isinstance(frame, np.ndarray)


# Tests for edge cases
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_frame_preprocessing_resize(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test frame preprocessing with resize."""
        sample_video_path.touch()

        extractor = FrameExtractor(
            sample_video_path,
            resize_width=160,
            resize_height=120,
            validate_video=False,
        )
        frame = extractor.get_frame(0)

        # Frame should be resized
        assert frame.shape[0] == 120
        assert frame.shape[1] == 160

    def test_empty_frame_indices(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extraction with empty frame indices."""
        sample_video_path.touch()

        # Very large interval results in few frames
        extractor = FrameExtractor(
            sample_video_path,
            sampling_interval=1000,
            validate_video=False,
        )

        indices = extractor.get_sample_indices()
        assert len(indices) == 1  # Only frame 0

    def test_frame_preprocessing_normalize(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test frame preprocessing with normalization."""
        sample_video_path.touch()

        config = FrameExtractorConfig(normalize=True)
        extractor = FrameExtractor(
            sample_video_path,
            config=config,
            validate_video=False,
        )
        frame = extractor.get_frame(0)

        # Frame should be normalized to float32 in [0, 1]
        assert frame.dtype == np.float32
        assert frame.max() <= 1.0
        assert frame.min() >= 0.0

    def test_frame_preprocessing_no_rgb_conversion(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test frame preprocessing without RGB conversion."""
        sample_video_path.touch()

        config = FrameExtractorConfig(convert_to_rgb=False)
        extractor = FrameExtractor(
            sample_video_path,
            config=config,
            validate_video=False,
        )

        # Just verify it doesn't crash - the color space is still 3 channels
        frame = extractor.get_frame(0)
        assert frame is not None
        assert len(frame.shape) == 3

    def test_generator_with_start_frame(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extract_frames generator with start_frame > 0."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        frames = list(extractor.extract_frames(start_frame=50, end_frame=55))

        assert len(frames) == 5
        # First frame should be 50
        assert frames[0][0] == 50

    def test_seek_invalid_frame(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test seek with frame not in sample indices."""
        sample_video_path.touch()

        extractor = FrameExtractor(
            sample_video_path,
            sampling_interval=10,
            validate_video=False,
        )

        # Frame 5 is not in sample indices (0, 10, 20, ...)
        with pytest.raises(FrameExtractionError, match="not in sample indices"):
            extractor.seek(5)

    def test_close_method(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test close method releases resources."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        extractor.get_frame(0)  # Load a frame

        extractor.close()

        # Buffer should be cleared
        stats = extractor.get_buffer_stats()
        assert stats["size"] == 0

    def test_buffer_memory_usage_property(self, sample_frame: np.ndarray) -> None:
        """Test buffer memory_usage_mb property."""
        buffer = FrameBuffer(max_size=10, max_memory_mb=100.0)

        buffer.put(0, sample_frame)
        assert buffer.memory_usage_mb > 0

    def test_buffer_cache_hit(self, sample_video_path: Path, mock_video_capture: MagicMock) -> None:
        """Test buffer returns cached frame on second request."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)

        # First call reads from video
        frame1 = extractor.get_frame(0)

        # Second call should come from buffer
        frame2 = extractor.get_frame(0)

        np.testing.assert_array_equal(frame1, frame2)


class TestProgressCallback:
    """Tests for progress callback in frame extraction."""

    def test_extract_frames_with_callback(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extract_frames calls progress callback."""
        sample_video_path.touch()

        progress_calls = []

        def callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        list(extractor.extract_frames(end_frame=5, progress_callback=callback))

        assert len(progress_calls) == 5
        assert progress_calls[-1] == (5, 5)

    def test_extract_frames_callback_values(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test progress callback receives correct values."""
        sample_video_path.touch()

        progress_calls = []

        def callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        list(extractor.extract_frames(start_frame=10, end_frame=15, progress_callback=callback))

        assert progress_calls[0] == (1, 5)
        assert progress_calls[-1] == (5, 5)

    def test_extract_frames_without_callback(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test extract_frames works without callback."""
        sample_video_path.touch()

        extractor = FrameExtractor(sample_video_path, validate_video=False)
        frames = list(extractor.extract_frames(end_frame=5))

        assert len(frames) == 5

    def test_callback_with_interval_sampling(
        self, sample_video_path: Path, mock_video_capture: MagicMock
    ) -> None:
        """Test callback with interval sampling."""
        sample_video_path.touch()

        progress_calls = []

        def callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        extractor = FrameExtractor(
            sample_video_path,
            sampling_interval=20,
            validate_video=False,
        )
        list(extractor.extract_frames(end_frame=60, progress_callback=callback))

        assert len(progress_calls) == 3  # Frames 0, 20, 40


# Mark as slow test
import pytest

pytestmark = pytest.mark.slow
