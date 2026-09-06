"""Unit tests for optical flow engine module.

Tests cover:
- OpticalFlowConfig dataclass
- OpticalFlowModelType enum
- OpticalFlowEngine initialization
- Input validation
- Error handling

Note: Tests for actual flow computation are marked as integration tests
and require OpenCV/cv2 to be installed.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a sample RGB frame for testing."""
    np.random.seed(42)
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_pair() -> tuple[np.ndarray, np.ndarray]:
    """Create a pair of frames for optical flow testing."""
    np.random.seed(42)
    frame1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frame2 = np.roll(frame1, 5, axis=1)
    return frame1, frame2


@pytest.fixture
def frame_sequence() -> list[np.ndarray]:
    """Create a sequence of frames for batch testing."""
    np.random.seed(42)
    base = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frames = []
    for i in range(5):
        frame = base.copy()
        shift = i * 2
        frame[:, shift:, :] = frame[:, :-shift, :] if shift > 0 else frame[:, :, :]
        frames.append(frame)
    return frames


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger module."""
    with patch("video2d3d.opticalflow.engine.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


@pytest.fixture
def mock_gpu_utils() -> Generator[dict, None, None]:
    """Mock GPU utilities for CPU-only testing."""
    with patch("video2d3d.opticalflow.engine.select_device") as mock_select:
        mock_selection = MagicMock()
        mock_selection.device = "cpu"
        mock_select.return_value = mock_selection
        with patch("video2d3d.opticalflow.engine.GPUConfig") as mock_config:
            mock_config.return_value = MagicMock()
            yield {"select_device": mock_select, "GPUConfig": mock_config}


@pytest.fixture
def mock_cv2_calc_optical_flow() -> Generator[MagicMock, None, None]:
    """Mock cv2.calcOpticalFlowFarneback for testing."""
    with patch("cv2.calcOpticalFlowFarneback") as mock_calc:
        # Return a dummy flow field
        mock_calc.return_value = np.zeros((100, 100, 2), dtype=np.float32)
        yield mock_calc


# ---------------------------------------------------------------------------
# OpticalFlowModelType Tests
# ---------------------------------------------------------------------------


class TestOpticalFlowModelType:
    """Tests for OpticalFlowModelType enum."""

    def test_from_string_raft_large(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test parsing raft_large model type."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        model = OpticalFlowModelType.from_string("raft_large")
        assert model == OpticalFlowModelType.RAFT_LARGE

    def test_from_string_raft_small(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test parsing raft_small model type."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        model = OpticalFlowModelType.from_string("raft_small")
        assert model == OpticalFlowModelType.RAFT_SMALL

    def test_from_string_farneback(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test parsing farneback model type."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        model = OpticalFlowModelType.from_string("farneback")
        assert model == OpticalFlowModelType.FARNEBACK

    def test_from_string_case_insensitive(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test case-insensitive parsing."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        assert OpticalFlowModelType.from_string("RAFT_LARGE") == OpticalFlowModelType.RAFT_LARGE
        assert OpticalFlowModelType.from_string("Raft_Small") == OpticalFlowModelType.RAFT_SMALL
        assert OpticalFlowModelType.from_string("FARNEBACK") == OpticalFlowModelType.FARNEBACK

    def test_from_string_invalid_raises(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test that invalid model name raises ValueError."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        with pytest.raises(ValueError, match="Unknown model name"):
            OpticalFlowModelType.from_string("invalid_model")

    def test_is_raft_property(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test is_raft property."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        assert OpticalFlowModelType.RAFT_LARGE.is_raft is True
        assert OpticalFlowModelType.RAFT_SMALL.is_raft is True
        assert OpticalFlowModelType.RAFT_Sintel.is_raft is True
        assert OpticalFlowModelType.FARNEBACK.is_raft is False
        assert OpticalFlowModelType.PWC_NET.is_raft is False

    def test_is_pwc_property(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test is_pwc property."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        assert OpticalFlowModelType.PWC_NET.is_pwc is True
        assert OpticalFlowModelType.RAFT_LARGE.is_pwc is False
        assert OpticalFlowModelType.FARNEBACK.is_pwc is False

    def test_is_deep_learning_property(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test is_deep_learning property."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        assert OpticalFlowModelType.RAFT_LARGE.is_deep_learning is True
        assert OpticalFlowModelType.RAFT_SMALL.is_deep_learning is True
        assert OpticalFlowModelType.PWC_NET.is_deep_learning is True
        assert OpticalFlowModelType.FARNEBACK.is_deep_learning is False

    def test_default_resolution_property(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test default_resolution property."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        assert OpticalFlowModelType.RAFT_LARGE.default_resolution == 384
        assert OpticalFlowModelType.RAFT_SMALL.default_resolution == 384
        assert OpticalFlowModelType.PWC_NET.default_resolution == 384
        assert OpticalFlowModelType.FARNEBACK.default_resolution == 0


# ---------------------------------------------------------------------------
# OpticalFlowConfig Tests
# ---------------------------------------------------------------------------


class TestOpticalFlowConfig:
    """Tests for OpticalFlowConfig dataclass."""

    def test_default_values(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test default configuration values."""
        from video2d3d.opticalflow.engine import (
            _DEFAULT_FARNEBACK_ITERATIONS,
            _DEFAULT_FARNEBACK_LEVELS,
            _DEFAULT_FARNEBACK_PYR_SCALE,
            _DEFAULT_FARNEBACK_WINDOW,
            OpticalFlowConfig,
            OpticalFlowModelType,
        )

        config = OpticalFlowConfig()

        assert config.model_type == OpticalFlowModelType.RAFT_SMALL
        assert config.device == "cpu"  # Mocked to return CPU
        assert config.auto_download is True
        assert config.use_fp16 is False
        assert config.farneback_pyr_scale == _DEFAULT_FARNEBACK_PYR_SCALE
        assert config.farneback_levels == _DEFAULT_FARNEBACK_LEVELS
        assert config.farneback_window == _DEFAULT_FARNEBACK_WINDOW
        assert config.farneback_iterations == _DEFAULT_FARNEBACK_ITERATIONS

    def test_custom_values(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test custom configuration values."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowModelType

        config = OpticalFlowConfig(
            model_type="farneback",
            farneback_levels=5,
            farneback_window=21,
        )

        assert config.model_type == OpticalFlowModelType.FARNEBACK
        assert config.farneback_levels == 5
        assert config.farneback_window == 21

    def test_string_model_type_conversion(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that string model types are converted to enum."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowModelType

        config = OpticalFlowConfig(model_type="farneback")
        assert config.model_type == OpticalFlowModelType.FARNEBACK

    def test_invalid_farneback_pyr_scale_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that invalid farneback_pyr_scale raises ValueError."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        with pytest.raises(ValueError, match="farneback_pyr_scale"):
            OpticalFlowConfig(farneback_pyr_scale=0)

        with pytest.raises(ValueError, match="farneback_pyr_scale"):
            OpticalFlowConfig(farneback_pyr_scale=1.5)

    def test_invalid_farneback_levels_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that invalid farneback_levels raises ValueError."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        with pytest.raises(ValueError, match="farneback_levels"):
            OpticalFlowConfig(farneback_levels=0)

    def test_invalid_farneback_window_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that invalid farneback_window raises ValueError."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        with pytest.raises(ValueError, match="farneback_window"):
            OpticalFlowConfig(farneback_window=0)

    def test_invalid_farneback_iterations_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that invalid farneback_iterations raises ValueError."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        with pytest.raises(ValueError, match="farneback_iterations"):
            OpticalFlowConfig(farneback_iterations=0)

    def test_effective_resolution(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test effective_resolution property."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="raft_large")
        assert config.effective_resolution == 384

        config_custom = OpticalFlowConfig(model_type="raft_large", input_resolution=512)
        assert config_custom.effective_resolution == 512


# ---------------------------------------------------------------------------
# OpticalFlowEngine Initialization Tests
# ---------------------------------------------------------------------------


class TestOpticalFlowEngineInit:
    """Tests for OpticalFlowEngine initialization."""

    def test_init_with_defaults(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test initialization with default values."""
        from video2d3d.opticalflow.engine import OpticalFlowEngine, OpticalFlowModelType

        engine = OpticalFlowEngine()

        assert engine.config.model_type == OpticalFlowModelType.RAFT_SMALL
        assert engine.is_loaded is False

    def test_init_with_config(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test initialization with OpticalFlowConfig."""
        from video2d3d.opticalflow.engine import (
            OpticalFlowConfig,
            OpticalFlowEngine,
            OpticalFlowModelType,
        )

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        assert engine.config.model_type == OpticalFlowModelType.FARNEBACK

    def test_init_with_kwargs(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test initialization with keyword arguments."""
        from video2d3d.opticalflow.engine import OpticalFlowEngine, OpticalFlowModelType

        engine = OpticalFlowEngine(model_type="farneback")

        assert engine.config.model_type == OpticalFlowModelType.FARNEBACK


# ---------------------------------------------------------------------------
# Farneback Optical Flow Tests
# ---------------------------------------------------------------------------


class TestFarnebackOpticalFlow:
    """Tests for Farneback optical flow."""

    def test_compute_flow_farneback(
        self,
        sample_frame_pair: tuple[np.ndarray, np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test Farneback flow computation."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        # Check output shape and type
        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32

    def test_compute_flow_identical_frames(
        self,
        sample_frame: np.ndarray,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test flow computation with identical frames."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        flow = engine.compute_flow(sample_frame, sample_frame)

        assert flow.shape == (sample_frame.shape[0], sample_frame.shape[1], 2)
        assert flow.dtype == np.float32


# ---------------------------------------------------------------------------
# Input Validation Tests
# ---------------------------------------------------------------------------


class TestInputValidation:
    """Tests for input validation."""

    def test_non_array_input_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that non-array input raises InferenceError."""
        from video2d3d.opticalflow.engine import (
            InferenceError,
            OpticalFlowConfig,
            OpticalFlowEngine,
        )

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        with pytest.raises(InferenceError, match="must be numpy arrays"):
            engine.compute_flow("not an array", np.zeros((10, 10, 3)))  # type: ignore

    def test_wrong_ndim_input_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that wrong ndim input raises InferenceError."""
        from video2d3d.opticalflow.engine import (
            InferenceError,
            OpticalFlowConfig,
            OpticalFlowEngine,
        )

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        with pytest.raises(InferenceError, match="must be 3D arrays"):
            engine.compute_flow(np.zeros((10, 10)), np.zeros((10, 10, 3)))

    def test_mismatched_shapes_raises(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that mismatched shapes raise InferenceError."""
        from video2d3d.opticalflow.engine import (
            InferenceError,
            OpticalFlowConfig,
            OpticalFlowEngine,
        )

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        with pytest.raises(InferenceError, match="must have the same shape"):
            engine.compute_flow(np.zeros((10, 10, 3)), np.zeros((20, 20, 3)))


# ---------------------------------------------------------------------------
# Batch Processing Tests
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    """Tests for batch processing."""

    def test_process_batch_basic(
        self,
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test basic batch processing."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frames1 = frame_sequence[:-1]
        frames2 = frame_sequence[1:]

        flows = engine.compute_flow_batch(frames1, frames2)

        assert len(flows) == len(frames1)
        for flow in flows:
            assert isinstance(flow, np.ndarray)
            assert flow.shape == (frames1[0].shape[0], frames1[0].shape[1], 2)

    def test_process_batch_length_mismatch(
        self,
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that mismatched lengths raise ValueError."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frames1 = frame_sequence[:3]
        frames2 = frame_sequence[:2]  # Wrong count

        with pytest.raises(ValueError, match="must have the same length"):
            engine.compute_flow_batch(frames1, frames2)

    def test_process_batch_empty_list(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that empty list returns empty list."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        flows = engine.compute_flow_batch([], [])

        assert flows == []


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling."""

    def test_optical_flow_error_attrs(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test OpticalFlowError attributes."""
        from video2d3d.opticalflow.engine import OpticalFlowError

        original = ValueError("Original error")
        error = OpticalFlowError(
            "Test error",
            model_type="raft_large",
            device="cuda",
            original_exception=original,
        )

        assert str(error) == "Test error"
        assert error.model_type == "raft_large"
        assert error.device == "cuda"
        assert error.original_exception is original

    def test_model_load_error_is_optical_flow_error(
        self, mock_cv2_calc_optical_flow: MagicMock
    ) -> None:
        """Test ModelLoadError is subclass of OpticalFlowError."""
        from video2d3d.opticalflow.engine import ModelLoadError, OpticalFlowError

        error = ModelLoadError("Load failed")
        assert isinstance(error, OpticalFlowError)

    def test_inference_error_is_optical_flow_error(
        self, mock_cv2_calc_optical_flow: MagicMock
    ) -> None:
        """Test InferenceError is subclass of OpticalFlowError."""
        from video2d3d.opticalflow.engine import InferenceError, OpticalFlowError

        error = InferenceError("Inference failed")
        assert isinstance(error, OpticalFlowError)


# ---------------------------------------------------------------------------
# Callable Interface Tests
# ---------------------------------------------------------------------------


class TestCallableInterface:
    """Tests for callable interface."""

    def test_callable_delegates_to_compute_flow(
        self,
        sample_frame_pair: tuple[np.ndarray, np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that __call__ delegates to compute_flow."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        result1 = engine.compute_flow(frame1, frame2)
        result2 = engine(frame1, frame2)

        np.testing.assert_array_equal(result1, result2)


# ---------------------------------------------------------------------------
# Context Manager Tests
# ---------------------------------------------------------------------------


class TestContextManager:
    """Tests for context manager interface."""

    def test_context_manager_enters_and_exits(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test context manager entry and exit."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")

        with OpticalFlowEngine(config=config) as engine:
            assert engine is not None

        # After context exit, model should be cleaned up
        assert engine._model is None
        assert engine.is_loaded is False


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_opticalflow_engine(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test create_opticalflow_engine function."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType, create_opticalflow_engine

        engine = create_opticalflow_engine(model_type="farneback")

        assert engine.config.model_type == OpticalFlowModelType.FARNEBACK

    def test_compute_optical_flow(
        self,
        sample_frame_pair: tuple[np.ndarray, np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test compute_optical_flow convenience function."""
        from video2d3d.opticalflow.engine import compute_optical_flow

        frame1, frame2 = sample_frame_pair
        flow = compute_optical_flow(frame1, frame2, model_type="farneback")

        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Tests for module constants."""

    def test_default_constants_exist(self, mock_cv2_calc_optical_flow: MagicMock) -> None:
        """Test that default constants are defined."""
        from video2d3d.opticalflow.engine import (
            _DEFAULT_FARNEBACK_ITERATIONS,
            _DEFAULT_FARNEBACK_LEVELS,
            _DEFAULT_FARNEBACK_PYR_SCALE,
            _DEFAULT_FARNEBACK_WINDOW,
            _DEFAULT_PWC_RESOLUTION,
            _DEFAULT_RAFT_RESOLUTION,
        )

        assert _DEFAULT_RAFT_RESOLUTION > 0
        assert _DEFAULT_PWC_RESOLUTION > 0
        assert 0 < _DEFAULT_FARNEBACK_PYR_SCALE < 1
        assert _DEFAULT_FARNEBACK_LEVELS >= 1
        assert _DEFAULT_FARNEBACK_WINDOW >= 1
        assert _DEFAULT_FARNEBACK_ITERATIONS >= 1


# ---------------------------------------------------------------------------
# Visualization Tests
# ---------------------------------------------------------------------------


class TestFlowVisualization:
    """Tests for flow visualization."""

    def test_visualize_flow_basic(
        self,
        sample_frame_pair: tuple[np.ndarray, np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test basic flow visualization."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        # Mock cv2 functions for visualization
        with patch("cv2.cartToPolar") as mock_polar:
            mock_polar.return_value = (
                np.zeros((100, 100), dtype=np.float32),
                np.zeros((100, 100), dtype=np.float32),
            )
            with patch("cv2.cvtColor") as mock_cvt:
                mock_cvt.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

                vis = engine.visualize_flow(flow)

                assert vis.shape == (frame1.shape[0], frame1.shape[1], 3)


# ---------------------------------------------------------------------------
# Additional Edge Cases and Missing Coverage Tests
# ---------------------------------------------------------------------------


class TestAdditionalEdgeCases:
    """Additional tests for edge cases and missing coverage."""

    def test_model_type_aliases(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test model type parsing with various aliases."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        # Test various aliases
        assert OpticalFlowModelType.from_string("raft") == OpticalFlowModelType.RAFT_LARGE
        assert OpticalFlowModelType.from_string("RAFT") == OpticalFlowModelType.RAFT_LARGE
        assert OpticalFlowModelType.from_string("pwc") == OpticalFlowModelType.PWC_NET
        assert OpticalFlowModelType.from_string("PWC") == OpticalFlowModelType.PWC_NET
        assert OpticalFlowModelType.from_string("opencv") == OpticalFlowModelType.FARNEBACK
        assert OpticalFlowModelType.from_string("sintel") == OpticalFlowModelType.RAFT_Sintel
        assert OpticalFlowModelType.from_string("kitti") == OpticalFlowModelType.RAFT_Kitti

    def test_model_type_with_hyphens_and_spaces(
        self,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test model type parsing handles hyphens and spaces."""
        from video2d3d.opticalflow.engine import OpticalFlowModelType

        assert OpticalFlowModelType.from_string("raft-large") == OpticalFlowModelType.RAFT_LARGE
        assert OpticalFlowModelType.from_string("raft small") == OpticalFlowModelType.RAFT_SMALL
        assert OpticalFlowModelType.from_string("pwc net") == OpticalFlowModelType.PWC_NET

    def test_config_cache_dir_path_normalization(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that cache_dir is normalized to Path."""
        from pathlib import Path

        from video2d3d.opticalflow.engine import OpticalFlowConfig

        # String path should be converted to Path
        config = OpticalFlowConfig(model_type="farneback", cache_dir="/tmp/cache")
        assert isinstance(config.cache_dir, Path)
        assert config.cache_dir == Path("/tmp/cache")

    def test_config_repr_method(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test OpticalFlowConfig __repr__ method."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="farneback")
        repr_str = repr(config)

        assert "OpticalFlowConfig" in repr_str
        assert "farneback" in repr_str
        assert "device" in repr_str

    def test_engine_repr_method(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test OpticalFlowEngine __repr__ method."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)
        repr_str = repr(engine)

        assert "OpticalFlowEngine" in repr_str
        assert "farneback" in repr_str
        assert "is_loaded" in repr_str

    def test_engine_close_method(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test explicit close() method call."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Engine should have no model loaded for Farneback
        assert engine._model is None

        # Close should not raise even with no model
        engine.close()

        assert engine._model is None
        assert not engine.is_loaded

    def test_model_property_lazy_loading(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that model property returns None for Farneback (no DL model)."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        # For Farneback, model property should return None
        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Farneback doesn't have a deep learning model, so model should return None
        model = engine.model
        assert model is None
        # is_loaded should be False until load_model is explicitly called for Farneback
        assert not engine.is_loaded

    def test_load_model_farneback(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test load_model for Farneback sets is_loaded to True."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)
        assert not engine.is_loaded

        # Calling load_model for Farneback sets is_loaded=True
        engine.load_model()
        assert engine.is_loaded

    def test_visualize_flow_non_array_input(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test visualize_flow raises error for non-array input."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        with pytest.raises(ValueError, match="flow must be a numpy array"):
            engine.visualize_flow("not an array")  # type: ignore

    def test_visualize_flow_wrong_ndim(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test visualize_flow raises error for wrong ndim."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # 2D array instead of 3D
        invalid_flow = np.zeros((100, 100), dtype=np.float32)

        with pytest.raises(ValueError, match="flow must have shape"):
            engine.visualize_flow(invalid_flow)

    def test_visualize_flow_wrong_channels(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test visualize_flow raises error for wrong channel count."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # 3 channels instead of 2
        invalid_flow = np.zeros((100, 100, 3), dtype=np.float32)

        with pytest.raises(ValueError, match="flow must have shape"):
            engine.visualize_flow(invalid_flow)

    def test_visualize_flow_frame_size_mismatch(
        self,
        sample_frame_pair: tuple[np.ndarray, np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test visualize_flow raises error when frame size doesn't match."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        # Wrong size frame
        wrong_frame = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="doesn't match flow shape"):
            engine.visualize_flow(flow, wrong_frame)

    def test_batch_with_custom_batch_size(
        self,
        frame_sequence: list[np.ndarray],
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test batch processing with custom batch size."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frames1 = frame_sequence[:-1]
        frames2 = frame_sequence[1:]

        # Process with batch_size=2
        flows = engine.compute_flow_batch(frames1, frames2, batch_size=2)

        assert len(flows) == len(frames1)
        for flow in flows:
            assert flow.shape == (frames1[0].shape[0], frames1[0].shape[1], 2)

    def test_config_with_fp16(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test config with FP16 enabled."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="farneback", use_fp16=True)

        assert config.use_fp16 is True

    def test_config_with_auto_download(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test config with auto_download disabled."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="farneback", auto_download=False)

        assert config.auto_download is False

    def test_config_with_input_resolution(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test config with custom input resolution."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="raft_large", input_resolution=512)

        assert config.input_resolution == 512
        assert config.effective_resolution == 512

    def test_farneback_default_resolution(
        self,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test that Farneback has 0 default resolution (native)."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="farneback")

        assert config.model_type.default_resolution == 0
        assert config.effective_resolution == 0

    def test_large_frame_processing(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test processing of larger frames."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Create larger frames
        np.random.seed(42)
        frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        frame2 = np.roll(frame1, 10, axis=1)

        # Mock should be updated to return correct shape
        with patch("cv2.calcOpticalFlowFarneback") as mock_calc:
            mock_calc.return_value = np.zeros((480, 640, 2), dtype=np.float32)
            flow = engine.compute_flow(frame1, frame2)

            assert flow.shape == (480, 640, 2)


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_pixel_flow(
        self,
        mock_logger: MagicMock,
        mock_gpu_utils: dict,
        mock_cv2_calc_optical_flow: MagicMock,
    ) -> None:
        """Test flow with minimal frame size."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Create small frames
        tiny_frame1 = np.array([[[128, 128, 128]]], dtype=np.uint8)
        tiny_frame2 = np.array([[[130, 130, 130]]], dtype=np.uint8)

        # Mock the flow computation to return the right shape
        with patch("cv2.calcOpticalFlowFarneback") as mock_calc:
            mock_calc.return_value = np.zeros((1, 1, 2), dtype=np.float32)
            flow = engine.compute_flow(tiny_frame1, tiny_frame2)

            assert flow.shape == (1, 1, 2)


# Mark as slow test
import pytest

pytestmark = pytest.mark.slow
