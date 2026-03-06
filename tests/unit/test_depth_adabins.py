"""Unit tests for AdaBins (AdaDepth) depth estimation module.

Tests cover:
- AdaBinsModelType enum
- AdaBinsConfig dataclass
- Custom exceptions
- AdaBinsEstimator class (with mocked torch)
- Model selector integration

Note: These tests mock torch before importing the depth module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


def _create_mock_torch() -> MagicMock:
    """Create a mock torch module."""
    mock = MagicMock()
    mock.cuda.is_available.return_value = False
    mock.hub.get_dir.return_value = "/tmp/torch_hub"
    mock.hub.set_dir = MagicMock()
    mock.hub.load = MagicMock()
    mock.no_grad = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    mock.backends.cudnn.benchmark = False
    mock.Tensor = MagicMock

    mock_tensor = MagicMock()
    mock_tensor.dim.return_value = 3
    mock_tensor.unsqueeze.return_value = mock_tensor
    mock_tensor.squeeze.return_value = mock_tensor
    mock_tensor.to.return_value = mock_tensor
    mock_tensor.cpu.return_value = mock_tensor
    mock_tensor.half.return_value = mock_tensor
    mock_tensor.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
    mock.from_numpy = MagicMock(return_value=mock_tensor)
    mock.cat = MagicMock(return_value=mock_tensor)
    mock.zeros = MagicMock(return_value=mock_tensor)

    return mock


def _create_mock_torch_nn_functional() -> MagicMock:
    """Create a mock torch.nn.functional module."""
    mock = MagicMock()
    mock_depth = np.random.random((100, 100)).astype(np.float32)
    mock.interpolate = MagicMock(
        return_value=MagicMock(
            squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
        )
    )
    return mock


def _create_mock_logger() -> MagicMock:
    """Create a mock loguru logger."""
    mock_logger = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.critical = MagicMock()
    return mock_logger


def _create_mock_logger_module() -> MagicMock:
    """Create a mock video2d3d.utils.logger module."""
    mock_module = MagicMock()
    mock_module.get_logger = MagicMock(return_value=_create_mock_logger())
    mock_module.log_exception = MagicMock()
    mock_module.log_model_inference = MagicMock()
    return mock_module


@pytest.fixture(autouse=True)
def mock_torch_modules() -> Generator[None, None, None]:
    """Mock torch modules before any imports (autouse fixture)."""
    original_modules = {}
    modules_to_mock = [
        "torch",
        "torch.nn",
        "torch.nn.functional",
        "torchvision",
        "torchvision.transforms",
        "huggingface_hub",
    ]

    for mod in modules_to_mock:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]

    mock_torch = _create_mock_torch()
    mock_torch_nn = MagicMock()
    mock_torch_nn.functional = _create_mock_torch_nn_functional()
    mock_torchvision = MagicMock()
    mock_torchvision.transforms = MagicMock()

    sys.modules["torch"] = mock_torch
    sys.modules["torch.nn"] = mock_torch_nn
    sys.modules["torch.nn.functional"] = mock_torch_nn.functional
    sys.modules["torchvision"] = mock_torchvision
    sys.modules["torchvision.transforms"] = mock_torchvision.transforms
    sys.modules["huggingface_hub"] = MagicMock()

    sys.modules["loguru"] = MagicMock()
    sys.modules["video2d3d.utils"] = MagicMock()
    sys.modules["video2d3d.utils.logger"] = _create_mock_logger_module()
    
    # Create proper GPU mock with select_device returning cpu
    mock_gpu = MagicMock()
    mock_gpu.GPUConfig = MagicMock
    mock_selection = MagicMock()
    mock_selection.device = "cpu"
    mock_gpu.select_device = MagicMock(return_value=mock_selection)
    mock_gpu.clear_gpu_memory = MagicMock()
    mock_gpu.compute_optimal_batch_size = MagicMock(return_value=4)
    sys.modules["video2d3d.utils.gpu"] = mock_gpu

    for mod in ["video2d3d.depth", "video2d3d.depth.__init__", "video2d3d.depth.adadepth"]:
        if mod in sys.modules:
            del sys.modules[mod]

    yield

    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    for mod in ["video2d3d.depth", "video2d3d.depth.adadepth"]:
        if mod in sys.modules:
            del sys.modules[mod]


@pytest.fixture
def mock_torch() -> MagicMock:
    """Get the mocked torch module."""
    return sys.modules["torch"]


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image for testing."""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# AdaBinsModelType Tests
# ---------------------------------------------------------------------------


class TestAdaBinsModelType:
    """Tests for AdaBinsModelType enum."""

    def test_enum_values(self, mock_torch: MagicMock) -> None:
        """Test that all expected model types exist."""
        from video2d3d.depth.adadepth import AdaBinsModelType

        assert AdaBinsModelType.ADADEPTH_NYU.value == "adadepth_nyu"
        assert AdaBinsModelType.ADADEPTH_KITTI.value == "adadepth_kitti"

    def test_from_string_nyu(self, mock_torch: MagicMock) -> None:
        """Test from_string with various NYU model name formats."""
        from video2d3d.depth.adadepth import AdaBinsModelType

        assert AdaBinsModelType.from_string("adadepth_nyu") == AdaBinsModelType.ADADEPTH_NYU
        assert AdaBinsModelType.from_string("ADABINS_NYU") == AdaBinsModelType.ADADEPTH_NYU
        assert AdaBinsModelType.from_string("nyu") == AdaBinsModelType.ADADEPTH_NYU

    def test_from_string_kitti(self, mock_torch: MagicMock) -> None:
        """Test from_string with various KITTI model name formats."""
        from video2d3d.depth.adadepth import AdaBinsModelType

        assert AdaBinsModelType.from_string("adadepth_kitti") == AdaBinsModelType.ADADEPTH_KITTI
        assert AdaBinsModelType.from_string("ADABINS_KITTI") == AdaBinsModelType.ADADEPTH_KITTI
        assert AdaBinsModelType.from_string("kitti") == AdaBinsModelType.ADADEPTH_KITTI

    def test_from_string_invalid_raises(self, mock_torch: MagicMock) -> None:
        """Test that invalid model name raises ValueError."""
        from video2d3d.depth.adadepth import AdaBinsModelType

        with pytest.raises(ValueError, match="Unknown AdaBins model name"):
            AdaBinsModelType.from_string("invalid_model")

    def test_default_resolution(self, mock_torch: MagicMock) -> None:
        """Test default_resolution property."""
        from video2d3d.depth.adadepth import AdaBinsModelType

        assert AdaBinsModelType.ADADEPTH_NYU.default_resolution == 384
        assert AdaBinsModelType.ADADEPTH_KITTI.default_resolution == 384

    def test_max_depth(self, mock_torch: MagicMock) -> None:
        """Test max_depth property."""
        from video2d3d.depth.adadepth import AdaBinsModelType

        assert AdaBinsModelType.ADADEPTH_NYU.max_depth == 10.0
        assert AdaBinsModelType.ADADEPTH_KITTI.max_depth == 80.0


# ---------------------------------------------------------------------------
# AdaBinsConfig Tests
# ---------------------------------------------------------------------------


class TestAdaBinsConfig:
    """Tests for AdaBinsConfig dataclass."""

    def test_default_values(self, mock_torch: MagicMock) -> None:
        """Test default configuration values."""
        from video2d3d.depth.adadepth import AdaBinsConfig, AdaBinsModelType

        config = AdaBinsConfig()

        assert config.model_type == AdaBinsModelType.ADADEPTH_NYU
        assert config.device == "cpu"
        assert config.cache_dir is None
        assert config.auto_download is True

    def test_custom_values(self, mock_torch: MagicMock) -> None:
        """Test custom configuration values."""
        from video2d3d.depth.adadepth import AdaBinsConfig, AdaBinsModelType

        config = AdaBinsConfig(
            model_type=AdaBinsModelType.ADADEPTH_KITTI,
            device="cuda",
            cache_dir=Path("/custom/cache"),
            auto_download=False,
            output_resolution=512,
            use_fp16=True,
        )

        assert config.model_type == AdaBinsModelType.ADADEPTH_KITTI
        assert config.device == "cuda"
        assert config.cache_dir == Path("/custom/cache")

    def test_string_model_type_conversion(self, mock_torch: MagicMock) -> None:
        """Test that string model type is converted to enum."""
        from video2d3d.depth.adadepth import AdaBinsConfig, AdaBinsModelType

        config = AdaBinsConfig(model_type="adabins_kitti")
        assert config.model_type == AdaBinsModelType.ADADEPTH_KITTI

    def test_effective_resolution_with_custom(self, mock_torch: MagicMock) -> None:
        """Test effective_resolution with custom output_resolution."""
        from video2d3d.depth.adadepth import AdaBinsConfig

        config = AdaBinsConfig(output_resolution=512)
        assert config.effective_resolution == 512


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


class TestAdaBinsExceptions:
    """Tests for custom exception classes."""

    def test_adabins_load_error_basic(self, mock_torch: MagicMock) -> None:
        """Test basic AdaBinsLoadError."""
        from video2d3d.depth.adadepth import AdaBinsLoadError

        error = AdaBinsLoadError("Test error")
        assert str(error) == "Test error"
        assert error.model_type is None
        assert error.device is None

    def test_adabins_load_error_with_params(self, mock_torch: MagicMock) -> None:
        """Test AdaBinsLoadError with all parameters."""
        from video2d3d.depth.adadepth import AdaBinsLoadError

        original = ValueError("Original error")
        error = AdaBinsLoadError(
            "Test error",
            model_type="adabins_nyu",
            device="cuda",
            original_exception=original,
        )

        assert error.model_type == "adabins_nyu"
        assert error.device == "cuda"
        assert error.original_exception is original

    def test_adabins_inference_error_inherits(self, mock_torch: MagicMock) -> None:
        """Test AdaBinsInferenceError."""
        from video2d3d.depth.adadepth import AdaBinsInferenceError

        error = AdaBinsInferenceError("Inference failed")
        assert isinstance(error, Exception)


# ---------------------------------------------------------------------------
# AdaBinsEstimator Tests
# ---------------------------------------------------------------------------


class TestAdaBinsEstimatorInit:
    """Tests for AdaBinsEstimator initialization."""

    def test_init_with_defaults(self, mock_torch: MagicMock) -> None:
        """Test initialization with default values."""
        from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsModelType

        estimator = AdaBinsEstimator()

        assert estimator.config.model_type == AdaBinsModelType.ADADEPTH_NYU
        assert estimator.config.device == "cpu"
        assert estimator.is_loaded is False

    def test_init_with_model_type_string(self, mock_torch: MagicMock) -> None:
        """Test initialization with model type as string."""
        from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsModelType

        estimator = AdaBinsEstimator(model_type="adabins_kitti")
        assert estimator.config.model_type == AdaBinsModelType.ADADEPTH_KITTI

    def test_init_with_config(self, mock_torch: MagicMock) -> None:
        """Test initialization with AdaBinsConfig."""
        from video2d3d.depth.adadepth import (
            AdaBinsEstimator,
            AdaBinsConfig,
            AdaBinsModelType,
        )

        config = AdaBinsConfig(model_type=AdaBinsModelType.ADADEPTH_KITTI, device="cpu")
        estimator = AdaBinsEstimator(config=config)

        assert estimator.config.model_type == AdaBinsModelType.ADADEPTH_KITTI


class TestAdaBinsEstimatorInputValidation:
    """Tests for input validation in AdaBinsEstimator."""

    def test_estimate_depth_invalid_type(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises AdaBinsInferenceError for non-array input."""
        from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsInferenceError

        estimator = AdaBinsEstimator()

        with pytest.raises(AdaBinsInferenceError, match="Input must be a numpy array"):
            estimator.estimate_depth([[1, 2], [3, 4]])

    def test_estimate_depth_wrong_dimensions(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises AdaBinsInferenceError for wrong dimensions."""
        from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsInferenceError

        estimator = AdaBinsEstimator()

        with pytest.raises(AdaBinsInferenceError, match="Input must be 3D array"):
            estimator.estimate_depth(np.zeros((100, 100)))

    def test_estimate_depth_wrong_channels(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises AdaBinsInferenceError for wrong channel count."""
        from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsInferenceError

        estimator = AdaBinsEstimator()

        with pytest.raises(AdaBinsInferenceError, match="Input must have 3 channels"):
            estimator.estimate_depth(np.zeros((100, 100, 1)))

    def test_estimate_depth_batch_empty_list(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch raises AdaBinsInferenceError for empty list."""
        from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsInferenceError

        estimator = AdaBinsEstimator()

        with pytest.raises(AdaBinsInferenceError, match="Input frames list cannot be empty"):
            estimator.estimate_depth_batch([])


class TestAdaBinsEstimatorContextManager:
    """Tests for AdaBinsEstimator context manager."""

    def test_context_manager_enter_returns_self(self, mock_torch: MagicMock) -> None:
        """Test __enter__ returns self."""
        from video2d3d.depth.adadepth import AdaBinsEstimator

        estimator = AdaBinsEstimator()
        with estimator as ctx_estimator:
            assert ctx_estimator is estimator

    def test_close_clears_model(self, mock_torch: MagicMock) -> None:
        """Test close method clears model resources."""
        from video2d3d.depth.adadepth import AdaBinsEstimator

        estimator = AdaBinsEstimator()
        estimator._model = MagicMock()
        estimator._is_loaded = True

        estimator.close()

        assert estimator._model is None
        assert estimator.is_loaded is False


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestAdaBinsConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_adabins_estimator_defaults(self, mock_torch: MagicMock) -> None:
        """Test create_adabins_estimator with default values."""
        from video2d3d.depth.adadepth import (
            create_adabins_estimator,
            AdaBinsModelType,
        )

        estimator = create_adabins_estimator()
        assert estimator.config.model_type == AdaBinsModelType.ADADEPTH_NYU

    def test_create_adabins_estimator_custom_values(self, mock_torch: MagicMock) -> None:
        """Test create_adabins_estimator with custom values."""
        from video2d3d.depth.adadepth import (
            create_adabins_estimator,
            AdaBinsModelType,
        )

        estimator = create_adabins_estimator(model_type="adabins_kitti", device="cuda")
        assert estimator.config.model_type == AdaBinsModelType.ADADEPTH_KITTI


# ---------------------------------------------------------------------------
# Module Exports Tests
# ---------------------------------------------------------------------------


class TestAdaBinsModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self, mock_torch: MagicMock) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d.depth import adadepth

        expected_exports = [
            "AdaBinsEstimator",
            "AdaBinsConfig",
            "AdaBinsModelType",
            "AdaBinsLoadError",
            "AdaBinsInferenceError",
            "create_adabins_estimator",
            "estimate_depth_adabins",
        ]

        for export in expected_exports:
            assert export in adadepth.__all__, f"Missing export: {export}"


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestAdaBinsModuleConstants:
    """Tests for module-level constants."""

    def test_resolution_constant(self, mock_torch: MagicMock) -> None:
        """Test resolution constant is defined."""
        from video2d3d.depth.adadepth import _ADABINS_DEFAULT_RESOLUTION

        assert _ADABINS_DEFAULT_RESOLUTION == 384

    def test_batch_size_constant(self, mock_torch: MagicMock) -> None:
        """Test batch size constant is defined."""
        from video2d3d.depth.adadepth import _DEFAULT_BATCH_SIZE

        assert _DEFAULT_BATCH_SIZE == 4
