"""Unit tests for temporal depth smoothing module.

Tests cover:
- TemporalSmoothingMethod enum
- TemporalSmoothingConfig dataclass
- TemporalSmoother class
- EMA smoothing
- Optical flow smoothing
- Sliding window smoothing
- Batch processing
- Error handling
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.depth.temporal import (
    TemporalSmoother,
    TemporalSmoothingConfig,
    TemporalSmoothingError,
    TemporalSmoothingMethod,
    TemporalState,
    create_temporal_smoother,
    smooth_depth_temporal,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_depth_map() -> np.ndarray:
    """Create a sample depth map for testing."""
    np.random.seed(42)
    return np.random.random((100, 100)).astype(np.float32)


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a sample RGB frame for optical flow testing."""
    np.random.seed(42)
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def depth_sequence() -> list[np.ndarray]:
    """Create a sequence of depth maps for temporal testing."""
    np.random.seed(42)
    base = np.random.random((100, 100)).astype(np.float32)
    # Add slight variations to simulate video
    return [
        np.clip(base + np.random.normal(0, 0.05, (100, 100)).astype(np.float32), 0, 1)
        for _ in range(5)
    ]


@pytest.fixture
def frame_sequence() -> list[np.ndarray]:
    """Create a sequence of frames for optical flow testing."""
    np.random.seed(42)
    base = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    # Add slight variations
    frames = []
    for i in range(5):
        frame = base.copy()
        # Shift some pixels to simulate motion
        frame[:, 10:, :] = frame[:, :-10, :]
        frames.append(frame)
    return frames


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.depth.temporal.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


# ---------------------------------------------------------------------------
# TemporalSmoothingMethod Enum Tests
# ---------------------------------------------------------------------------


class TestTemporalSmoothingMethod:
    """Tests for TemporalSmoothingMethod enum."""

    def test_enum_values(self) -> None:
        """Test that all expected smoothing methods exist."""
        assert TemporalSmoothingMethod.EMA.value == "ema"
        assert TemporalSmoothingMethod.OPTICAL_FLOW.value == "optical_flow"
        assert TemporalSmoothingMethod.SLIDING_WINDOW.value == "sliding_window"
        assert TemporalSmoothingMethod.NONE.value == "none"

    def test_all_methods_have_values(self) -> None:
        """Test that all enum values are strings."""
        for method in TemporalSmoothingMethod:
            assert isinstance(method.value, str)


# ---------------------------------------------------------------------------
# TemporalSmoothingConfig Tests
# ---------------------------------------------------------------------------


class TestTemporalSmoothingConfig:
    """Tests for TemporalSmoothingConfig dataclass."""

    def test_default_values(self, mock_logger: MagicMock) -> None:
        """Test default configuration values."""
        config = TemporalSmoothingConfig()

        assert config.method == "ema"
        assert config.smoothing_factor == 0.5
        assert config.flow_threshold == 4.0
        assert config.window_size == 5
        assert config.pyramid_scale == 0.5
        assert config.pyramid_levels == 3
        assert config.flow_window_size == 15
        assert config.flow_iterations == 3
        assert config.flow_poly_n == 5
        assert config.flow_poly_sigma == 1.2
        assert config.enable_occlusion_handling is True
        assert config.occlusion_threshold == 0.1

    def test_custom_values(self, mock_logger: MagicMock) -> None:
        """Test custom configuration values."""
        config = TemporalSmoothingConfig(
            method="optical_flow",
            smoothing_factor=0.7,
            flow_threshold=8.0,
            window_size=10,
        )

        assert config.method == "optical_flow"
        assert config.smoothing_factor == 0.7
        assert config.flow_threshold == 8.0
        assert config.window_size == 10

    def test_method_normalization(self, mock_logger: MagicMock) -> None:
        """Test that method is normalized to lowercase."""
        config = TemporalSmoothingConfig(method="EMA")
        assert config.method == "ema"

    def test_invalid_method_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid smoothing method"):
            TemporalSmoothingConfig(method="invalid")

    def test_invalid_smoothing_factor_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid smoothing_factor raises ValueError."""
        with pytest.raises(ValueError, match="smoothing_factor"):
            TemporalSmoothingConfig(smoothing_factor=1.5)

        with pytest.raises(ValueError, match="smoothing_factor"):
            TemporalSmoothingConfig(smoothing_factor=-0.1)

    def test_invalid_window_size_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid window_size raises ValueError."""
        with pytest.raises(ValueError, match="window_size"):
            TemporalSmoothingConfig(window_size=0)

    def test_invalid_flow_threshold_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid flow_threshold raises ValueError."""
        with pytest.raises(ValueError, match="flow_threshold"):
            TemporalSmoothingConfig(flow_threshold=0)

        with pytest.raises(ValueError, match="flow_threshold"):
            TemporalSmoothingConfig(flow_threshold=-1.0)

    def test_invalid_pyramid_scale_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid pyramid_scale raises ValueError."""
        with pytest.raises(ValueError, match="pyramid_scale"):
            TemporalSmoothingConfig(pyramid_scale=1.0)

        with pytest.raises(ValueError, match="pyramid_scale"):
            TemporalSmoothingConfig(pyramid_scale=0.0)


# ---------------------------------------------------------------------------
# TemporalState Tests
# ---------------------------------------------------------------------------


class TestTemporalState:
    """Tests for TemporalState dataclass."""

    def test_default_state(self) -> None:
        """Test default state values."""
        state = TemporalState()

        assert state.previous_depth is None
        assert state.previous_frame is None
        assert state.frame_count == 0
        assert len(state.depth_history) == 0


# ---------------------------------------------------------------------------
# TemporalSmoother Initialization Tests
# ---------------------------------------------------------------------------


class TestTemporalSmootherInit:
    """Tests for TemporalSmoother initialization."""

    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:
        """Test initialization with default values."""
        smoother = TemporalSmoother()

        assert smoother.config.method == "ema"
        assert smoother.config.smoothing_factor == 0.5
        assert smoother.state.frame_count == 0

    def test_init_with_config(self, mock_logger: MagicMock) -> None:
        """Test initialization with TemporalSmoothingConfig."""
        config = TemporalSmoothingConfig(
            method="optical_flow",
            smoothing_factor=0.7,
        )
        smoother = TemporalSmoother(config=config)

        assert smoother.config.method == "optical_flow"
        assert smoother.config.smoothing_factor == 0.7

    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:
        """Test initialization with keyword arguments."""
        smoother = TemporalSmoother(method="sliding_window", smoothing_factor=0.6)

        assert smoother.config.method == "sliding_window"
        assert smoother.config.smoothing_factor == 0.6


# ---------------------------------------------------------------------------
# EMA Smoothing Tests
# ---------------------------------------------------------------------------


class TestEMASmoothing:
    """Tests for EMA temporal smoothing."""

    def test_ema_first_frame(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test EMA smoothing on first frame returns input."""
        smoother = TemporalSmoother(method="ema")

        result = smoother.smooth(sample_depth_map)

        np.testing.assert_array_almost_equal(result, sample_depth_map)
        assert smoother.state.frame_count == 1

    def test_ema_second_frame(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test EMA smoothing blends previous and current frames."""
        config = TemporalSmoothingConfig(smoothing_factor=0.5)
        smoother = TemporalSmoother(config=config)

        # First frame
        smoother.smooth(sample_depth_map)

        # Second frame with different values
        second_depth = sample_depth_map + 0.1
        result = smoother.smooth(second_depth)

        # Result should be between first and second frame
        assert not np.allclose(result, sample_depth_map)
        assert not np.allclose(result, second_depth)
        assert smoother.state.frame_count == 2

    def test_ema_high_smoothing_factor(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test EMA with high smoothing factor (more weight to current)."""
        config = TemporalSmoothingConfig(smoothing_factor=0.9)
        smoother = TemporalSmoother(config=config)

        smoother.smooth(sample_depth_map)
        second_depth = sample_depth_map + 0.2
        result = smoother.smooth(second_depth)

        # Should be closer to second frame with high factor
        diff_from_second = np.abs(result - second_depth).mean()
        diff_from_first = np.abs(result - sample_depth_map).mean()
        assert diff_from_second < diff_from_first

    def test_ema_low_smoothing_factor(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test EMA with low smoothing factor (more weight to previous)."""
        config = TemporalSmoothingConfig(smoothing_factor=0.1)
        smoother = TemporalSmoother(config=config)

        smoother.smooth(sample_depth_map)
        second_depth = sample_depth_map + 0.2
        result = smoother.smooth(second_depth)

        # Should be closer to first frame with low factor
        diff_from_first = np.abs(result - sample_depth_map).mean()
        diff_from_second = np.abs(result - second_depth).mean()
        assert diff_from_first < diff_from_second

    def test_ema_resets_state(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test that reset clears temporal state."""
        smoother = TemporalSmoother(method="ema")

        # Process some frames
        smoother.smooth(sample_depth_map)
        smoother.smooth(sample_depth_map + 0.1)
        assert smoother.state.frame_count == 2

        # Reset
        smoother.reset()
        assert smoother.state.frame_count == 0
        assert smoother.state.previous_depth is None


# ---------------------------------------------------------------------------
# None Method Tests
# ---------------------------------------------------------------------------


class TestNoneMethod:
    """Tests for 'none' smoothing method (passthrough)."""

    def test_none_returns_input(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:
        """Test that 'none' method returns input unchanged."""
        smoother = TemporalSmoother(method="none")

        result = smoother.smooth(sample_depth_map)

        np.testing.assert_array_equal(result, sample_depth_map)

    def test_none_increments_frame_count(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that 'none' method still increments frame count."""
        smoother = TemporalSmoother(method="none")

        smoother.smooth(sample_depth_map)
        smoother.smooth(sample_depth_map)

        assert smoother.state.frame_count == 2


# ---------------------------------------------------------------------------
# Optical Flow Smoothing Tests
# ---------------------------------------------------------------------------


class TestOpticalFlowSmoothing:
    """Tests for optical flow temporal smoothing."""

    def test_optical_flow_first_frame(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test optical flow smoothing on first frame."""
        smoother = TemporalSmoother(method="optical_flow")

        result = smoother.smooth(sample_depth_map, frame=sample_frame)

        np.testing.assert_array_almost_equal(result, sample_depth_map)
        assert smoother.state.frame_count == 1

    def test_optical_flow_requires_frame(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that optical flow raises error without frame."""
        smoother = TemporalSmoother(method="optical_flow")

        # Process first frame (OK)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        smoother.smooth(sample_depth_map, frame=frame)

        # Second frame without providing frame should raise error
        with pytest.raises(TemporalSmoothingError, match="Frame is required"):
            smoother.smooth(sample_depth_map, frame=None)

    def test_optical_flow_with_frames(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test optical flow with a sequence of frames."""
        smoother = TemporalSmoother(method="optical_flow")

        results = []
        for depth, frame in zip(depth_sequence, frame_sequence):
            result = smoother.smooth(depth, frame=frame)
            results.append(result)
            assert result.shape == depth.shape
            assert result.dtype == np.float32
            assert result.min() >= 0.0
            assert result.max() <= 1.0

        assert len(results) == len(depth_sequence)

    def test_optical_flow_occlusion_handling(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test optical flow with occlusion handling enabled."""
        config = TemporalSmoothingConfig(
            method="optical_flow",
            enable_occlusion_handling=True,
        )
        smoother = TemporalSmoother(config=config)

        # First frame
        smoother.smooth(sample_depth_map, frame=sample_frame)

        # Second frame
        second_frame = np.roll(sample_frame, 5, axis=1)
        second_depth = sample_depth_map + 0.1
        result = smoother.smooth(second_depth, frame=second_frame)

        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# Sliding Window Smoothing Tests
# ---------------------------------------------------------------------------


class TestSlidingWindowSmoothing:
    """Tests for sliding window temporal smoothing."""

    def test_sliding_window_first_frame(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test sliding window on first frame."""
        smoother = TemporalSmoother(method="sliding_window")

        result = smoother.smooth(sample_depth_map)

        np.testing.assert_array_almost_equal(result, sample_depth_map)
        assert len(smoother.state.depth_history) == 1

    def test_sliding_window_averaging(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test that sliding window averages multiple frames."""
        config = TemporalSmoothingConfig(
            method="sliding_window",
            window_size=5,
        )
        smoother = TemporalSmoother(config=config)

        results = []
        for depth in depth_sequence:
            result = smoother.smooth(depth)
            results.append(result)

        # After processing all frames, should have full window
        assert len(smoother.state.depth_history) == len(depth_sequence)

    def test_sliding_window_respects_window_size(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test that sliding window respects window size."""
        config = TemporalSmoothingConfig(
            method="sliding_window",
            window_size=3,
        )
        smoother = TemporalSmoother(config=config)

        # Process more frames than window size
        extended_sequence = depth_sequence * 2  # 10 frames
        for depth in extended_sequence:
            smoother.smooth(depth)

        # History should not exceed window size
        assert len(smoother.state.depth_history) <= 3


# ---------------------------------------------------------------------------
# Batch Processing Tests
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    """Tests for batch processing."""

    def test_process_batch_basic(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test basic batch processing."""
        smoother = TemporalSmoother(method="ema")

        results = smoother.process_batch(depth_sequence)

        assert len(results) == len(depth_sequence)
        for result in results:
            assert isinstance(result, np.ndarray)
            assert result.shape == depth_sequence[0].shape
            assert result.dtype == np.float32

    def test_process_batch_with_frames(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test batch processing with frames for optical flow."""
        smoother = TemporalSmoother(method="optical_flow")

        results = smoother.process_batch(depth_sequence, frames=frame_sequence)

        assert len(results) == len(depth_sequence)

    def test_process_batch_length_mismatch(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test that mismatched lengths raise ValueError."""
        smoother = TemporalSmoother(method="optical_flow")
        wrong_frames = frame_sequence = [
            np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(3)
        ]  # Wrong count

        with pytest.raises(ValueError, match="Length mismatch"):
            smoother.process_batch(depth_sequence, frames=wrong_frames)

    def test_process_batch_empty_list(self, mock_logger: MagicMock) -> None:
        """Test that empty list returns empty list."""
        smoother = TemporalSmoother(method="ema")

        results = smoother.process_batch([])

        assert results == []

    def test_process_batch_resets_state(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test that batch processing resets state."""
        smoother = TemporalSmoother(method="ema")

        # Process first batch
        smoother.process_batch(depth_sequence[:3])
        first_count = smoother.state.frame_count

        # Process second batch - should reset
        smoother.process_batch(depth_sequence[3:])

        # Frame count should reflect new batch, not cumulative
        assert smoother.state.frame_count == len(depth_sequence) - 3


# ---------------------------------------------------------------------------
# Callable Interface Tests
# ---------------------------------------------------------------------------


class TestCallableInterface:
    """Tests for callable interface."""

    def test_callable_delegates_to_smooth(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that __call__ delegates to smooth."""
        smoother = TemporalSmoother(method="ema")

        result1 = smoother.smooth(sample_depth_map)
        smoother.reset()
        result2 = smoother(sample_depth_map)

        np.testing.assert_array_almost_equal(result1, result2)


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling."""

    def test_temporal_smoothing_error_attrs(self) -> None:
        """Test TemporalSmoothingError attributes."""
        original = ValueError("Original error")
        error = TemporalSmoothingError(
            "Test error",
            operation="test_op",
            original_exception=original,
        )

        assert str(error) == "Test error"
        assert error.operation == "test_op"
        assert error.original_exception is original

    def test_temporal_smoothing_error_inheritance(self) -> None:
        """Test TemporalSmoothingError inheritance."""
        error = TemporalSmoothingError("Test")
        assert isinstance(error, Exception)

    def test_output_clamped_to_valid_range(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test that output is clamped to [0, 1] range."""
        smoother = TemporalSmoother(method="ema")

        for depth in depth_sequence:
            result = smoother.smooth(depth)
            assert result.min() >= 0.0
            assert result.max() <= 1.0


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_temporal_smoother_defaults(self, mock_logger: MagicMock) -> None:
        """Test create_temporal_smoother with defaults."""
        smoother = create_temporal_smoother()

        assert smoother.config.method == "ema"
        assert smoother.config.smoothing_factor == 0.5

    def test_create_temporal_smoother_custom(self, mock_logger: MagicMock) -> None:
        """Test create_temporal_smoother with custom values."""
        smoother = create_temporal_smoother(
            method="optical_flow",
            smoothing_factor=0.7,
        )

        assert smoother.config.method == "optical_flow"
        assert smoother.config.smoothing_factor == 0.7

    def test_smooth_depth_temporal(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test smooth_depth_temporal convenience function."""
        results = smooth_depth_temporal(depth_sequence, method="ema")

        assert len(results) == len(depth_sequence)
        for result in results:
            assert isinstance(result, np.ndarray)

    def test_smooth_depth_temporal_with_frames(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test smooth_depth_temporal with frames."""
        results = smooth_depth_temporal(
            depth_sequence,
            frames=frame_sequence,
            method="optical_flow",
        )

        assert len(results) == len(depth_sequence)


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases."""

    def test_constant_depth_map(self, mock_logger: MagicMock) -> None:
        """Test smoothing with constant depth map."""
        smoother = TemporalSmoother(method="ema")
        constant_depth = np.full((50, 50), 0.5, dtype=np.float32)

        result1 = smoother.smooth(constant_depth)
        result2 = smoother.smooth(constant_depth)

        np.testing.assert_array_almost_equal(result1, constant_depth)
        np.testing.assert_array_almost_equal(result2, constant_depth)

    def test_single_pixel_depth(self, mock_logger: MagicMock) -> None:
        """Test smoothing with minimal depth map size."""
        smoother = TemporalSmoother(method="ema")
        tiny_depth = np.array([[0.5]], dtype=np.float32)

        result = smoother.smooth(tiny_depth)

        assert result.shape == (1, 1)
        np.testing.assert_array_almost_equal(result, tiny_depth)

    def test_large_smoothing_factor(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test with smoothing factor of 1.0."""
        config = TemporalSmoothingConfig(smoothing_factor=1.0)
        smoother = TemporalSmoother(config=config)

        smoother.smooth(sample_depth_map)
        second_depth = sample_depth_map + 0.2
        result = smoother.smooth(second_depth)

        # With factor 1.0, should be exactly second frame
        np.testing.assert_array_almost_equal(result, second_depth)

    def test_zero_smoothing_factor(
        self, sample_depth_map: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test with smoothing factor of 0.0."""
        config = TemporalSmoothingConfig(smoothing_factor=0.0)
        smoother = TemporalSmoother(config=config)

        smoother.smooth(sample_depth_map)
        second_depth = sample_depth_map + 0.2
        result = smoother.smooth(second_depth)

        # With factor 0.0, should be exactly first frame
        np.testing.assert_array_almost_equal(result, sample_depth_map)
