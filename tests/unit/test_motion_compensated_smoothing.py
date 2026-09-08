"""Unit tests for motion-compensated temporal smoothing module.

Tests cover:
- MotionCompensatedConfig dataclass
- MotionCompensatedSmoother class
- Forward-backward flow consistency
- Edge-preserving temporal blending
- Motion-based depth consistency refinement
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
    MotionCompensatedConfig,
    MotionCompensatedSmoother,
    TemporalSmoothingError,
    create_motion_compensated_smoother,
    smooth_depth_motion_compensated,
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
    # Add slight variations with motion
    frames = []
    for i in range(5):
        frame = base.copy()
        # Shift some pixels to simulate motion
        shift = i * 2
        frame[:, shift:, :] = frame[:, :-shift, :] if shift > 0 else frame[:, :, :]
        frames.append(frame)
    return frames


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    import video2d3d.depth.temporal as temporal_module

    with patch.object(temporal_module, "get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


# ---------------------------------------------------------------------------
# MotionCompensatedConfig Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedConfig:
    """Tests for MotionCompensatedConfig dataclass."""

    def test_default_values(self, mock_logger: MagicMock) -> None:
        """Test default configuration values."""
        config = MotionCompensatedConfig()

        assert config.smoothing_factor == 0.5
        assert config.flow_threshold == 8.0
        assert config.consistency_threshold == 1.0
        assert config.edge_preservation_factor == 0.7
        assert config.motion_history_length == 5
        assert config.depth_consistency_weight == 0.3
        assert config.multi_scale_flow is True
        assert config.pyramid_scale == 0.5
        assert config.pyramid_levels == 3
        assert config.flow_window_size == 21
        assert config.flow_iterations == 5
        assert config.enable_forward_backward_check is True
        assert config.enable_edge_preservation is True
        assert config.enable_motion_segmentation is True

    def test_custom_values(self, mock_logger: MagicMock) -> None:
        """Test custom configuration values."""
        config = MotionCompensatedConfig(
            smoothing_factor=0.7,
            flow_threshold=10.0,
            consistency_threshold=2.0,
            edge_preservation_factor=0.8,
            motion_history_length=10,
            depth_consistency_weight=0.4,
        )

        assert config.smoothing_factor == 0.7
        assert config.flow_threshold == 10.0
        assert config.consistency_threshold == 2.0
        assert config.edge_preservation_factor == 0.8
        assert config.motion_history_length == 10
        assert config.depth_consistency_weight == 0.4

    def test_invalid_smoothing_factor_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid smoothing_factor raises ValueError."""
        with pytest.raises(ValueError, match="smoothing_factor"):
            MotionCompensatedConfig(smoothing_factor=1.5)

        with pytest.raises(ValueError, match="smoothing_factor"):
            MotionCompensatedConfig(smoothing_factor=-0.1)

    def test_invalid_flow_threshold_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid flow_threshold raises ValueError."""
        with pytest.raises(ValueError, match="flow_threshold"):
            MotionCompensatedConfig(flow_threshold=0)

        with pytest.raises(ValueError, match="flow_threshold"):
            MotionCompensatedConfig(flow_threshold=-1.0)

    def test_invalid_consistency_threshold_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid consistency_threshold raises ValueError."""
        with pytest.raises(ValueError, match="consistency_threshold"):
            MotionCompensatedConfig(consistency_threshold=-1.0)

    def test_invalid_edge_preservation_factor_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid edge_preservation_factor raises ValueError."""
        with pytest.raises(ValueError, match="edge_preservation_factor"):
            MotionCompensatedConfig(edge_preservation_factor=1.5)

        with pytest.raises(ValueError, match="edge_preservation_factor"):
            MotionCompensatedConfig(edge_preservation_factor=-0.1)

    def test_invalid_motion_history_length_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid motion_history_length raises ValueError."""
        with pytest.raises(ValueError, match="motion_history_length"):
            MotionCompensatedConfig(motion_history_length=0)

    def test_invalid_depth_consistency_weight_raises(self, mock_logger: MagicMock) -> None:
        """Test that invalid depth_consistency_weight raises ValueError."""
        with pytest.raises(ValueError, match="depth_consistency_weight"):
            MotionCompensatedConfig(depth_consistency_weight=1.5)

        with pytest.raises(ValueError, match="depth_consistency_weight"):
            MotionCompensatedConfig(depth_consistency_weight=-0.1)


# ---------------------------------------------------------------------------
# MotionCompensatedSmoother Initialization Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedSmootherInit:
    """Tests for MotionCompensatedSmoother initialization."""

    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:
        """Test initialization with default values."""
        smoother = MotionCompensatedSmoother()

        assert smoother.config.smoothing_factor == 0.5
        assert smoother.state.frame_count == 0

    def test_init_with_config(self, mock_logger: MagicMock) -> None:
        """Test initialization with MotionCompensatedConfig."""
        config = MotionCompensatedConfig(
            smoothing_factor=0.7,
            enable_forward_backward_check=True,
        )
        smoother = MotionCompensatedSmoother(config=config)

        assert smoother.config.smoothing_factor == 0.7
        assert smoother.config.enable_forward_backward_check is True

    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:
        """Test initialization with keyword arguments."""
        smoother = MotionCompensatedSmoother(smoothing_factor=0.6)

        assert smoother.config.smoothing_factor == 0.6


# ---------------------------------------------------------------------------
# Motion-Compensated Smoothing Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedSmoothing:
    """Tests for motion-compensated smoothing."""

    def test_first_frame(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test smoothing on first frame returns input."""
        smoother = MotionCompensatedSmoother()

        result = smoother.smooth(sample_depth_map, sample_frame)

        np.testing.assert_array_almost_equal(result, sample_depth_map)
        assert smoother.state.frame_count == 1

    def test_second_frame(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test smoothing on second frame produces valid output."""
        config = MotionCompensatedConfig(smoothing_factor=0.5)
        smoother = MotionCompensatedSmoother(config=config)

        # First frame
        smoother.smooth(sample_depth_map, sample_frame)

        # Second frame with different values
        second_frame = np.roll(sample_frame, 5, axis=1)
        second_depth = sample_depth_map + 0.1
        result = smoother.smooth(second_depth, second_frame)

        # Result should be valid depth map
        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32
        assert result.min() >= 0.0
        assert result.max() <= 1.0
        assert smoother.state.frame_count == 2

    def test_with_frame_sequence(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test smoothing with a sequence of frames."""
        smoother = MotionCompensatedSmoother()

        results = []
        for depth, frame in zip(depth_sequence, frame_sequence):
            result = smoother.smooth(depth, frame)
            results.append(result)
            assert result.shape == depth.shape
            assert result.dtype == np.float32
            assert result.min() >= 0.0
            assert result.max() <= 1.0

        assert len(results) == len(depth_sequence)

    def test_with_forward_backward_check_disabled(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test smoothing with forward-backward check disabled."""
        config = MotionCompensatedConfig(
            enable_forward_backward_check=False,
        )
        smoother = MotionCompensatedSmoother(config=config)

        # First frame
        smoother.smooth(sample_depth_map, sample_frame)

        # Second frame
        second_frame = np.roll(sample_frame, 5, axis=1)
        second_depth = sample_depth_map + 0.1
        result = smoother.smooth(second_depth, second_frame)

        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32

    def test_with_edge_preservation_disabled(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test smoothing with edge preservation disabled."""
        config = MotionCompensatedConfig(
            enable_edge_preservation=False,
        )
        smoother = MotionCompensatedSmoother(config=config)

        # First frame
        smoother.smooth(sample_depth_map, sample_frame)

        # Second frame
        second_frame = np.roll(sample_frame, 5, axis=1)
        second_depth = sample_depth_map + 0.1
        result = smoother.smooth(second_depth, second_frame)

        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32

    def test_with_motion_segmentation_disabled(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test smoothing with motion segmentation disabled."""
        config = MotionCompensatedConfig(
            enable_motion_segmentation=False,
        )
        smoother = MotionCompensatedSmoother(config=config)

        # First frame
        smoother.smooth(sample_depth_map, sample_frame)

        # Second frame
        second_frame = np.roll(sample_frame, 5, axis=1)
        second_depth = sample_depth_map + 0.1
        result = smoother.smooth(second_depth, second_frame)

        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32

    def test_resets_state(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that reset clears temporal state."""
        smoother = MotionCompensatedSmoother()

        # Process some frames
        smoother.smooth(sample_depth_map, sample_frame)
        smoother.smooth(sample_depth_map + 0.1, np.roll(sample_frame, 5, axis=1))
        assert smoother.state.frame_count == 2

        # Reset
        smoother.reset()
        assert smoother.state.frame_count == 0
        assert smoother.state.previous_depth is None


# ---------------------------------------------------------------------------
# Batch Processing Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedBatchProcessing:
    """Tests for batch processing."""

    def test_process_batch_basic(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test basic batch processing."""
        smoother = MotionCompensatedSmoother()

        results = smoother.process_batch(depth_sequence, frame_sequence)

        assert len(results) == len(depth_sequence)
        for result in results:
            assert isinstance(result, np.ndarray)
            assert result.shape == depth_sequence[0].shape
            assert result.dtype == np.float32

    def test_process_batch_length_mismatch(
        self, depth_sequence: list[np.ndarray], mock_logger: MagicMock
    ) -> None:
        """Test that mismatched lengths raise ValueError."""
        smoother = MotionCompensatedSmoother()
        wrong_frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(3)]  # Wrong count

        with pytest.raises(ValueError, match="Length mismatch"):
            smoother.process_batch(depth_sequence, frames=wrong_frames)

    def test_process_batch_empty_list(self, mock_logger: MagicMock) -> None:
        """Test that empty list returns empty list."""
        smoother = MotionCompensatedSmoother()

        results = smoother.process_batch([], [])

        assert results == []

    def test_process_batch_resets_state(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test that batch processing resets state."""
        smoother = MotionCompensatedSmoother()

        # Process first batch
        smoother.process_batch(depth_sequence[:3], frame_sequence[:3])

        # Process second batch - should reset
        smoother.process_batch(depth_sequence[3:], frame_sequence[3:])

        # Frame count should reflect new batch, not cumulative
        assert smoother.state.frame_count == len(depth_sequence) - 3


# ---------------------------------------------------------------------------
# Callable Interface Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedCallableInterface:
    """Tests for callable interface."""

    def test_callable_delegates_to_smooth(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test that __call__ delegates to smooth."""
        smoother = MotionCompensatedSmoother()

        result1 = smoother.smooth(sample_depth_map, sample_frame)
        smoother.reset()
        result2 = smoother(sample_depth_map, sample_frame)

        np.testing.assert_array_almost_equal(result1, result2)


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedErrorHandling:
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

    def test_output_clamped_to_valid_range(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test that output is clamped to [0, 1] range."""
        smoother = MotionCompensatedSmoother()

        for depth, frame in zip(depth_sequence, frame_sequence):
            result = smoother.smooth(depth, frame)
            assert result.min() >= 0.0
            assert result.max() <= 1.0


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_motion_compensated_smoother_defaults(self, mock_logger: MagicMock) -> None:
        """Test create_motion_compensated_smoother with defaults."""
        smoother = create_motion_compensated_smoother()

        assert smoother.config.smoothing_factor == 0.5

    def test_create_motion_compensated_smoother_custom(self, mock_logger: MagicMock) -> None:
        """Test create_motion_compensated_smoother with custom values."""
        smoother = create_motion_compensated_smoother(
            smoothing_factor=0.7,
        )

        assert smoother.config.smoothing_factor == 0.7

    def test_smooth_depth_motion_compensated(
        self,
        depth_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
    ) -> None:
        """Test smooth_depth_motion_compensated convenience function."""
        results = smooth_depth_motion_compensated(depth_sequence, frame_sequence)

        assert len(results) == len(depth_sequence)
        for result in results:
            assert isinstance(result, np.ndarray)


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestMotionCompensatedEdgeCases:
    """Tests for edge cases."""

    def test_constant_depth_map(self, sample_frame: np.ndarray, mock_logger: MagicMock) -> None:
        """Test smoothing with constant depth map."""
        smoother = MotionCompensatedSmoother()
        constant_depth = np.full((50, 50), 0.5, dtype=np.float32)

        frame1 = sample_frame[:50, :50, :]
        frame2 = np.roll(frame1, 5, axis=1)

        result1 = smoother.smooth(constant_depth, frame1)
        smoother.smooth(constant_depth, frame2)

        np.testing.assert_array_almost_equal(result1, constant_depth)

    def test_single_pixel_depth(self, mock_logger: MagicMock) -> None:
        """Test smoothing with minimal depth map size."""
        smoother = MotionCompensatedSmoother()
        tiny_depth = np.array([[0.5]], dtype=np.float32)
        tiny_frame = np.array([[[128, 128, 128]]], dtype=np.uint8)

        result = smoother.smooth(tiny_depth, tiny_frame)

        assert result.shape == (1, 1)
        np.testing.assert_array_almost_equal(result, tiny_depth)

    def test_large_smoothing_factor(
        self, sample_depth_map: np.ndarray, sample_frame: np.ndarray, mock_logger: MagicMock
    ) -> None:
        """Test with smoothing factor of 1.0."""
        config = MotionCompensatedConfig(smoothing_factor=1.0)
        smoother = MotionCompensatedSmoother(config=config)

        smoother.smooth(sample_depth_map, sample_frame)
        second_frame = np.roll(sample_frame, 5, axis=1)
        second_depth = sample_depth_map + 0.2
        result = smoother.smooth(second_depth, second_frame)

        # Result should be closer to second frame with high factor
        assert result.shape == sample_depth_map.shape

    def test_small_depth_map_with_motion(self, mock_logger: MagicMock) -> None:
        """Test with small depth map and significant motion."""
        smoother = MotionCompensatedSmoother()

        # Create small frames with visible motion
        depth1 = np.random.random((32, 32)).astype(np.float32)
        frame1 = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)

        # Shifted frame for motion
        depth2 = np.roll(depth1, 5, axis=1)
        frame2 = np.roll(frame1, 5, axis=1)

        result1 = smoother.smooth(depth1, frame1)
        result2 = smoother.smooth(depth2, frame2)

        assert result1.shape == depth1.shape
        assert result2.shape == depth2.shape
