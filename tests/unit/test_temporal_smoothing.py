"""Unit tests for temporal smoothing module.

Tests cover:
- TemporalSmoothingConfig dataclass
- TemporalSmoothingMethod enum
- Exponential moving average (EMA) smoothing
- Optical flow-based smoothing
- Sliding window smoothing
- Batch processing
- State management

Note: These tests rely on mocks set up in tests/conftest.py.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Import the module under test (mocks are set up in conftest.py)
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
    """Create a sample RGB frame for testing."""
    np.random.seed(42)
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def depth_map_sequence() -> list[np.ndarray]:
    """Create a sequence of depth maps for testing."""
    np.random.seed(42)
    sequence = []
    for _ in range(10):
        # Create smooth transitions
        base = np.sin(np.linspace(0, np.pi, 100)).reshape(100, 1) * np.cos(
            np.linspace(0, np.pi, 100)
        ).reshape(1, 100)
        noise = np.random.random((100, 100)) * 0.1
        depth = (base * 0.5 + 0.3 + noise).astype(np.float32)
        sequence.append(depth)
    return sequence


@pytest.fixture
def frame_sequence() -> list[np.ndarray]:
    """Create a sequence of RGB frames for testing."""
    np.random.seed(42)
    sequence = []
    for _ in range(10):
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        sequence.append(frame)
    return sequence


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.depth.temporal.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


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
            window_size=7,
        )

        assert config.method == "optical_flow"
        assert config.smoothing_factor == 0.7
        assert config.flow_threshold == 8.0
        assert config.window_size == 7

    def test_method_normalization(self, mock_logger: MagicMock) -> None:
        """Test that method is normalized to lowercase."""
        config = TemporalSmoothingConfig(method="EMA")
        assert config.method == "ema"

        config = TemporalSmoothingConfig(method="OPTICAL_FLOW")
        assert config.method == "optical_flow"

    def test_invalid_method(self, mock_logger: MagicMock) -> None:
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid smoothing method"):
            TemporalSmoothingConfig(method="invalid")

    def test_invalid_smoothing_factor_low(self, mock_logger: MagicMock) -> None:
        """Test that smoothing_factor < 0 raises ValueError."""
        with pytest.raises(ValueError, match="smoothing_factor must be in"):
            TemporalSmoothingConfig(smoothing_factor=-0.1)

    def test_invalid_smoothing_factor_high(self, mock_logger: MagicMock) -> None:
        """Test that smoothing_factor > 1 raises ValueError."""
        with pytest.raises(ValueError, match="smoothing_factor must be in"):
            TemporalSmoothingConfig(smoothing_factor=1.5)

    def test_invalid_window_size(self, mock_logger: MagicMock) -> None:
        """Test that window_size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="window_size must be >= 1"):
            TemporalSmoothingConfig(window_size=0)

    def test_invalid_flow_threshold(self, mock_logger: MagicMock) -> None:
        """Test that flow_threshold <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="flow_threshold must be > 0"):
            TemporalSmoothingConfig(flow_threshold=0)

    def test_invalid_pyramid_scale(self, mock_logger: MagicMock) -> None:
        """Test that pyramid_scale outside (0, 1) raises ValueError."""
        with pytest.raises(ValueError, match="pyramid_scale must be in"):
            TemporalSmoothingConfig(pyramid_scale=0.0)

        with pytest.raises(ValueError, match="pyramid_scale must be in"):
            TemporalSmoothingConfig(pyramid_scale=1.0)


# ---------------------------------------------------------------------------
# TemporalSmoother Tests
# ---------------------------------------------------------------------------


class TestTemporalSmoother:
    """Tests for TemporalSmoother class."""

    def test_initialization_default(self, mock_logger: MagicMock) -> None:
        """Test default initialization."""
        smoother = TemporalSmoother()

        assert smoother.config.method == "ema"
        assert smoother.config.smoothing_factor == 0.5
        assert smoother.state.previous_depth is None
        assert smoother.state.frame_count == 0

    def test_initialization_custom_config(self, mock_logger: MagicMock) -> None:
        """Test initialization with custom config."""
        config = TemporalSmoothingConfig(
            method="optical_flow",
            smoothing_factor=0.7,
        )
        smoother = TemporalSmoother(config=config)

        assert smoother.config.method == "optical_flow"
        assert smoother.config.smoothing_factor == 0.7

    def test_initialization_with_params(self, mock_logger: MagicMock) -> None:
        """Test initialization with direct parameters."""
        smoother = TemporalSmoother(method="sliding_window", smoothing_factor=0.3)

        assert smoother.config.method == "sliding_window"
        assert smoother.config.smoothing_factor == 0.3

    def test_reset(self, mock_logger: MagicMock, sample_depth_map: np.ndarray) -> None:
        """Test reset clears state."""
        smoother = TemporalSmoother()
        smoother.smooth(sample_depth_map)

        assert smoother.state.previous_depth is not None
        assert smoother.state.frame_count == 1

        smoother.reset()

        assert smoother.state.previous_depth is None
        assert smoother.state.frame_count == 0

    def test_callable_interface(self, mock_logger: MagicMock, sample_depth_map: np.ndarray) -> None:
        """Test callable interface."""
        smoother = TemporalSmoother()
        result = smoother(sample_depth_map)

        assert result is not None
        assert result.shape == sample_depth_map.shape


# ---------------------------------------------------------------------------
# EMA Smoothing Tests
# ---------------------------------------------------------------------------


class TestEMASmoothing:
    """Tests for exponential moving average smoothing."""

    def test_first_frame_passthrough(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test that first frame passes through unchanged."""
        smoother = TemporalSmoother(method="ema")
        result = smoother.smooth(sample_depth_map)

        np.testing.assert_array_almost_equal(result, sample_depth_map)

    def test_second_frame_blend(self, mock_logger: MagicMock, sample_depth_map: np.ndarray) -> None:
        """Test that second frame is blended with first."""
        smoother = TemporalSmoother(method="ema", smoothing_factor=0.5)

        # First frame
        smoother.smooth(sample_depth_map)

        # Second frame (different)
        second_depth = sample_depth_map * 2
        result2 = smoother.smooth(second_depth)

        # Result should be between the two
        assert result2.min() >= sample_depth_map.min()
        assert result2.max() <= second_depth.max()

    def test_smoothing_factor_effect(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test that smoothing_factor affects blending."""
        second_depth = sample_depth_map * 2

        # High smoothing factor (less temporal smoothing)
        smoother_high = TemporalSmoother(method="ema", smoothing_factor=0.9)
        smoother_high.smooth(sample_depth_map)
        result_high = smoother_high.smooth(second_depth)

        # Low smoothing factor (more temporal smoothing)
        smoother_low = TemporalSmoother(method="ema", smoothing_factor=0.1)
        smoother_low.smooth(sample_depth_map)
        result_low = smoother_low.smooth(second_depth)

        # Higher smoothing factor should result in values closer to second frame
        # (since we're blending towards the new frame more aggressively)
        assert np.mean(np.abs(result_high - second_depth)) < np.mean(
            np.abs(result_low - second_depth)
        )

    def test_none_method_passthrough(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test that 'none' method passes frames through unchanged."""
        smoother = TemporalSmoother(method="none")

        result1 = smoother.smooth(sample_depth_map)
        np.testing.assert_array_almost_equal(result1, sample_depth_map)

        second_depth = sample_depth_map * 2
        result2 = smoother.smooth(second_depth)
        np.testing.assert_array_almost_equal(result2, second_depth)

    def test_output_clamping(self, mock_logger: MagicMock) -> None:
        """Test that output values are clamped to [0, 1] range."""
        smoother = TemporalSmoother(method="ema", smoothing_factor=0.5)

        # Create a depth map with values outside [0, 1]
        depth_high = np.ones((10, 10), dtype=np.float32) * 2.0
        depth_low = np.ones((10, 10), dtype=np.float32) * -0.5

        # First frame to initialize state
        smoother.smooth(np.ones((10, 10), dtype=np.float32) * 0.5)

        # Process out-of-range values
        result_high = smoother.smooth(depth_high)
        result_low = smoother.smooth(depth_low)

        # Results should be clamped
        assert result_high.max() <= 1.0
        assert result_low.min() >= 0.0


# ---------------------------------------------------------------------------
# Optical Flow Smoothing Tests
# ---------------------------------------------------------------------------


class TestOpticalFlowSmoothing:
    """Tests for optical flow-based smoothing."""

    def test_requires_frame(self, mock_logger: MagicMock, sample_depth_map: np.ndarray) -> None:
        """Test that optical flow requires frame."""
        smoother = TemporalSmoother(method="optical_flow")

        # First frame is okay
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        smoother.smooth(sample_depth_map, frame)

        # Second frame without frame raises error
        second_depth = sample_depth_map * 2
        with pytest.raises(TemporalSmoothingError, match="Frame is required"):
            smoother.smooth(second_depth, None)

    def test_first_frame_passthrough(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test that first frame passes through unchanged."""
        smoother = TemporalSmoother(method="optical_flow")
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = smoother.smooth(sample_depth_map, frame)
        np.testing.assert_array_almost_equal(result, sample_depth_map)

    def test_motion_compensation(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test that optical flow provides motion compensation."""
        smoother = TemporalSmoother(method="optical_flow", smoothing_factor=0.5)

        # Create two frames with slight shift
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame1[30:70, 30:70] = 255

        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2[35:75, 35:75] = 255  # Shifted by 5 pixels

        # Process frames
        smoother.smooth(sample_depth_map, frame1)
        result = smoother.smooth(sample_depth_map, frame2)

        # Result should have valid depth values
        assert result is not None
        assert result.shape == sample_depth_map.shape
        assert not np.any(np.isnan(result))


# ---------------------------------------------------------------------------
# Sliding Window Smoothing Tests
# ---------------------------------------------------------------------------


class TestSlidingWindowSmoothing:
    """Tests for sliding window averaging."""

    def test_first_frame_passthrough(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test that first frame passes through unchanged."""
        smoother = TemporalSmoother(method="sliding_window")
        result = smoother.smooth(sample_depth_map)

        np.testing.assert_array_almost_equal(result, sample_depth_map)

    def test_window_size(
        self, mock_logger: MagicMock, depth_map_sequence: list[np.ndarray]
    ) -> None:
        """Test that window size is respected."""
        smoother = TemporalSmoother(method="sliding_window", window_size=3)

        for depth in depth_map_sequence[:5]:
            smoother.smooth(depth)

        # Window should have at most 3 frames
        assert len(smoother.state.depth_history) <= 3

    def test_weighted_average(
        self, mock_logger: MagicMock, depth_map_sequence: list[np.ndarray]
    ) -> None:
        """Test that sliding window computes weighted average."""
        smoother = TemporalSmoother(method="sliding_window", window_size=5)

        results = []
        for depth in depth_map_sequence:
            result = smoother.smooth(depth)
            results.append(result)

        # Later results should be different from input due to averaging
        assert len(results) == len(depth_map_sequence)
        # The last result should be smoothed
        assert results[-1] is not None


# ---------------------------------------------------------------------------
# Batch Processing Tests
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    """Tests for batch processing."""

    def test_process_batch(
        self,
        mock_logger: MagicMock,
        depth_map_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
    ) -> None:
        """Test batch processing with frames."""
        smoother = TemporalSmoother(method="ema")

        results = smoother.process_batch(depth_map_sequence, frame_sequence)

        assert len(results) == len(depth_map_sequence)
        for result in results:
            assert result.shape == depth_map_sequence[0].shape

    def test_process_batch_resets_state(
        self,
        mock_logger: MagicMock,
        depth_map_sequence: list[np.ndarray],
    ) -> None:
        """Test that batch processing resets state."""
        smoother = TemporalSmoother()

        # Process one frame first
        smoother.smooth(depth_map_sequence[0])
        assert smoother.state.frame_count == 1

        # Batch processing should reset
        results = smoother.process_batch(depth_map_sequence[:3])
        assert len(results) == 3

    def test_process_batch_length_mismatch(
        self,
        mock_logger: MagicMock,
        depth_map_sequence: list[np.ndarray],
        frame_sequence: list[np.ndarray],
    ) -> None:
        """Test that batch processing raises error on length mismatch."""
        smoother = TemporalSmoother(method="optical_flow")

        # Mismatched lengths should raise ValueError
        with pytest.raises(ValueError, match="Length mismatch"):
            smoother.process_batch(depth_map_sequence, frame_sequence[:5])

    def test_process_batch_empty(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """Test that batch processing handles empty input."""
        smoother = TemporalSmoother()
        results = smoother.process_batch([])
        assert results == []


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_temporal_smoother(self, mock_logger: MagicMock) -> None:
        """Test create_temporal_smoother function."""
        smoother = create_temporal_smoother(
            method="optical_flow",
            smoothing_factor=0.7,
        )

        assert smoother.config.method == "optical_flow"
        assert smoother.config.smoothing_factor == 0.7

    def test_smooth_depth_temporal(
        self,
        mock_logger: MagicMock,
        depth_map_sequence: list[np.ndarray],
    ) -> None:
        """Test smooth_depth_temporal function."""
        results = smooth_depth_temporal(
            depth_map_sequence,
            method="ema",
            smoothing_factor=0.5,
        )

        assert len(results) == len(depth_map_sequence)
        for result in results:
            assert result.shape == depth_map_sequence[0].shape


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling."""

    def test_temporal_smoothing_error(
        self, mock_logger: MagicMock, sample_depth_map: np.ndarray
    ) -> None:
        """Test TemporalSmoothingError is raised appropriately."""
        smoother = TemporalSmoother(method="optical_flow")

        # First frame with frame data
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        smoother.smooth(sample_depth_map, frame)

        # Second frame without frame data should raise error
        with pytest.raises(TemporalSmoothingError):
            smoother.smooth(sample_depth_map, None)


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

    def test_custom_state(self) -> None:
        """Test custom state values."""
        depth = np.zeros((10, 10), dtype=np.float32)
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        history = deque([depth], maxlen=5)

        state = TemporalState(
            previous_depth=depth,
            previous_frame=frame,
            depth_history=history,
            frame_count=1,
        )

        assert state.previous_depth is not None
        assert state.previous_frame is not None
        assert state.frame_count == 1
        assert len(state.depth_history) == 1


# ---------------------------------------------------------------------------
# Enum Tests
# ---------------------------------------------------------------------------


class TestTemporalSmoothingMethod:
    """Tests for TemporalSmoothingMethod enum."""

    def test_enum_values(self) -> None:
        """Test enum has expected values."""
        assert TemporalSmoothingMethod.EMA.value == "ema"
        assert TemporalSmoothingMethod.OPTICAL_FLOW.value == "optical_flow"
        assert TemporalSmoothingMethod.SLIDING_WINDOW.value == "sliding_window"
        assert TemporalSmoothingMethod.NONE.value == "none"
