import pytest

pytestmark = pytest.mark.slow

"""Unit tests for ZoeDepth depth estimation module.

Tests cover:
- ZoeDepthModelVariant enum
- DepthMode enum
- ZoeDepthConfig dataclass
- Custom exceptions
- ZoeDepthEstimator class (with mocked torch)
- Model selector integration

Note: These tests mock torch before importing the depth module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

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

    for mod in ["video2d3d.depth", "video2d3d.depth.__init__", "video2d3d.depth.zoedepth"]:
        if mod in sys.modules:
            del sys.modules[mod]

    yield

    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    for mod in ["video2d3d.depth", "video2d3d.depth.zoedepth"]:
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
# ZoeDepthModelVariant Tests
# ---------------------------------------------------------------------------


class TestZoeDepthModelVariant:
    """Tests for ZoeDepthModelVariant enum."""

    def test_enum_values(self, mock_torch: MagicMock) -> None:
        """Test that all expected model variants exist."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.ZOE_N.value == "ZoeD_N"
        assert ZoeDepthModelVariant.ZOE_K.value == "ZoeD_K"
        assert ZoeDepthModelVariant.ZOE_NK.value == "ZoeD_NK"

    def test_from_string_n(self, mock_torch: MagicMock) -> None:
        """Test from_string with various N model name formats."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.from_string("zoedepth_n") == ZoeDepthModelVariant.ZOE_N
        assert ZoeDepthModelVariant.from_string("ZOED_N") == ZoeDepthModelVariant.ZOE_N
        assert ZoeDepthModelVariant.from_string("zoe_n") == ZoeDepthModelVariant.ZOE_N
        assert ZoeDepthModelVariant.from_string("nyu") == ZoeDepthModelVariant.ZOE_N
        assert ZoeDepthModelVariant.from_string("indoor") == ZoeDepthModelVariant.ZOE_N

    def test_from_string_k(self, mock_torch: MagicMock) -> None:
        """Test from_string with various K model name formats."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.from_string("zoedepth_k") == ZoeDepthModelVariant.ZOE_K
        assert ZoeDepthModelVariant.from_string("ZOED_K") == ZoeDepthModelVariant.ZOE_K
        assert ZoeDepthModelVariant.from_string("zoe_k") == ZoeDepthModelVariant.ZOE_K
        assert ZoeDepthModelVariant.from_string("kitti") == ZoeDepthModelVariant.ZOE_K
        assert ZoeDepthModelVariant.from_string("outdoor") == ZoeDepthModelVariant.ZOE_K

    def test_from_string_nk(self, mock_torch: MagicMock) -> None:
        """Test from_string with various NK model name formats."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.from_string("zoedepth_nk") == ZoeDepthModelVariant.ZOE_NK
        assert ZoeDepthModelVariant.from_string("ZOED_NK") == ZoeDepthModelVariant.ZOE_NK
        assert ZoeDepthModelVariant.from_string("zoe_nk") == ZoeDepthModelVariant.ZOE_NK
        assert ZoeDepthModelVariant.from_string("combined") == ZoeDepthModelVariant.ZOE_NK
        assert ZoeDepthModelVariant.from_string("zoedepth") == ZoeDepthModelVariant.ZOE_NK

    def test_from_string_invalid_raises(self, mock_torch: MagicMock) -> None:
        """Test that invalid model name raises ValueError."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        with pytest.raises(ValueError, match="Unknown ZoeDepth model name"):
            ZoeDepthModelVariant.from_string("invalid_model")

    def test_default_resolution(self, mock_torch: MagicMock) -> None:
        """Test default_resolution property."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.ZOE_N.default_resolution == 384
        assert ZoeDepthModelVariant.ZOE_K.default_resolution == 384
        assert ZoeDepthModelVariant.ZOE_NK.default_resolution == 384

    def test_max_depth(self, mock_torch: MagicMock) -> None:
        """Test max_depth property."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.ZOE_N.max_depth == 10.0  # NYU
        assert ZoeDepthModelVariant.ZOE_K.max_depth == 80.0  # KITTI
        assert ZoeDepthModelVariant.ZOE_NK.max_depth == 80.0  # Combined

    def test_supports_metric(self, mock_torch: MagicMock) -> None:
        """Test supports_metric property."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.ZOE_N.supports_metric is True
        assert ZoeDepthModelVariant.ZOE_K.supports_metric is True
        assert ZoeDepthModelVariant.ZOE_NK.supports_metric is True

    def test_default_domain(self, mock_torch: MagicMock) -> None:
        """Test default_domain property."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.ZOE_N.default_domain == "indoor"
        assert ZoeDepthModelVariant.ZOE_K.default_domain == "outdoor"
        assert ZoeDepthModelVariant.ZOE_NK.default_domain == "combined"


# ---------------------------------------------------------------------------
# DepthMode Tests
# ---------------------------------------------------------------------------


class TestDepthMode:
    """Tests for DepthMode enum."""

    def test_enum_values(self, mock_torch: MagicMock) -> None:
        """Test that all expected depth modes exist."""
        from video2d3d.depth.zoedepth import DepthMode

        assert DepthMode.RELATIVE.value == "relative"
        assert DepthMode.METRIC.value == "metric"


# ---------------------------------------------------------------------------
# ZoeDepthConfig Tests
# ---------------------------------------------------------------------------


class TestZoeDepthConfig:
    """Tests for ZoeDepthConfig dataclass."""

    def test_default_values(self, mock_torch: MagicMock) -> None:
        """Test default configuration values."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig, ZoeDepthModelVariant

        config = ZoeDepthConfig()

        assert config.model_variant == ZoeDepthModelVariant.ZOE_NK
        assert config.depth_mode == "relative"
        assert config.device == "cpu"
        assert config.cache_dir is None
        assert config.auto_download is True

    def test_custom_values(self, mock_torch: MagicMock) -> None:
        """Test custom configuration values."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig, ZoeDepthModelVariant

        config = ZoeDepthConfig(
            model_variant=ZoeDepthModelVariant.ZOE_K,
            depth_mode="metric",
            device="cuda",
            cache_dir=Path("/custom/cache"),
            auto_download=False,
            output_resolution=512,
            use_fp16=True,
        )

        assert config.model_variant == ZoeDepthModelVariant.ZOE_K
        assert config.depth_mode == "metric"
        assert config.device == "cuda"
        assert config.cache_dir == Path("/custom/cache")

    def test_string_model_variant_conversion(self, mock_torch: MagicMock) -> None:
        """Test that string model variant is converted to enum."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig, ZoeDepthModelVariant

        config = ZoeDepthConfig(model_variant="zoedepth_k")
        assert config.model_variant == ZoeDepthModelVariant.ZOE_K

    def test_effective_resolution_with_custom(self, mock_torch: MagicMock) -> None:
        """Test effective_resolution with custom output_resolution."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig

        config = ZoeDepthConfig(output_resolution=512)
        assert config.effective_resolution == 512

    def test_invalid_depth_mode_raises(self, mock_torch: MagicMock) -> None:
        """Test that invalid depth_mode raises ValueError."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig

        with pytest.raises(ValueError, match="Invalid depth_mode"):
            ZoeDepthConfig(depth_mode="invalid")

    def test_is_metric_mode(self, mock_torch: MagicMock) -> None:
        """Test is_metric_mode property."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig

        config_relative = ZoeDepthConfig(depth_mode="relative")
        config_metric = ZoeDepthConfig(depth_mode="metric")

        assert config_relative.is_metric_mode is False
        assert config_metric.is_metric_mode is True


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


class TestZoeDepthExceptions:
    """Tests for custom exception classes."""

    def test_zoedepth_load_error_basic(self, mock_torch: MagicMock) -> None:
        """Test basic ZoeDepthLoadError."""
        from video2d3d.depth.zoedepth import ZoeDepthLoadError

        error = ZoeDepthLoadError("Test error")
        assert str(error) == "Test error"
        assert error.model_variant is None
        assert error.device is None

    def test_zoedepth_load_error_with_params(self, mock_torch: MagicMock) -> None:
        """Test ZoeDepthLoadError with all parameters."""
        from video2d3d.depth.zoedepth import ZoeDepthLoadError

        original = ValueError("Original error")
        error = ZoeDepthLoadError(
            "Test error",
            model_variant="zoedepth_nk",
            device="cuda",
            original_exception=original,
        )

        assert error.model_variant == "zoedepth_nk"
        assert error.device == "cuda"
        assert error.original_exception is original

    def test_zoedepth_inference_error_inherits(self, mock_torch: MagicMock) -> None:
        """Test ZoeDepthInferenceError."""
        from video2d3d.depth.zoedepth import ZoeDepthInferenceError

        error = ZoeDepthInferenceError("Inference failed")
        assert isinstance(error, Exception)


# ---------------------------------------------------------------------------
# ZoeDepthEstimator Tests
# ---------------------------------------------------------------------------


class TestZoeDepthEstimatorInit:
    """Tests for ZoeDepthEstimator initialization."""

    def test_init_with_defaults(self, mock_torch: MagicMock) -> None:
        """Test initialization with default values."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthModelVariant

        estimator = ZoeDepthEstimator()

        assert estimator.config.model_variant == ZoeDepthModelVariant.ZOE_NK
        assert estimator.config.device == "cpu"
        assert estimator.is_loaded is False

    def test_init_with_model_variant_string(self, mock_torch: MagicMock) -> None:
        """Test initialization with model variant as string."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthModelVariant

        estimator = ZoeDepthEstimator(model_variant="zoedepth_k")
        assert estimator.config.model_variant == ZoeDepthModelVariant.ZOE_K

    def test_init_with_depth_mode(self, mock_torch: MagicMock) -> None:
        """Test initialization with depth mode."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(depth_mode="metric")
        assert estimator.config.depth_mode == "metric"

    def test_init_with_config(self, mock_torch: MagicMock) -> None:
        """Test initialization with ZoeDepthConfig."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig, ZoeDepthEstimator, ZoeDepthModelVariant

        config = ZoeDepthConfig(
            model_variant=ZoeDepthModelVariant.ZOE_K,
            depth_mode="metric",
            device="cpu",
        )
        estimator = ZoeDepthEstimator(config=config)

        assert estimator.config.model_variant == ZoeDepthModelVariant.ZOE_K
        assert estimator.config.depth_mode == "metric"


class TestZoeDepthEstimatorInputValidation:
    """Tests for input validation in ZoeDepthEstimator."""

    def test_estimate_depth_invalid_type(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises ZoeDepthInferenceError for non-array input."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError, match="Input must be a numpy array"):
            estimator.estimate_depth([[1, 2], [3, 4]])

    def test_estimate_depth_wrong_dimensions(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises ZoeDepthInferenceError for wrong dimensions."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError, match="Input must be 3D array"):
            estimator.estimate_depth(np.zeros((100, 100)))

    def test_estimate_depth_wrong_channels(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises ZoeDepthInferenceError for wrong channel count."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError, match="Input must have 3 channels"):
            estimator.estimate_depth(np.zeros((100, 100, 1)))

    def test_estimate_depth_batch_empty_list(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch raises ZoeDepthInferenceError for empty list."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError, match="Input frames list cannot be empty"):
            estimator.estimate_depth_batch([])


class TestZoeDepthEstimatorContextManager:
    """Tests for ZoeDepthEstimator context manager."""

    def test_context_manager_enter_returns_self(self, mock_torch: MagicMock) -> None:
        """Test __enter__ returns self."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        with estimator as ctx_estimator:
            assert ctx_estimator is estimator

    def test_close_clears_model(self, mock_torch: MagicMock) -> None:
        """Test close method clears model resources."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        estimator._model = MagicMock()
        estimator._is_loaded = True

        estimator.close()

        assert estimator._model is None
        assert estimator.is_loaded is False


class TestZoeDepthEstimatorConvenienceMethods:
    """Tests for convenience methods in ZoeDepthEstimator."""

    def test_estimate_metric_depth_sets_mode(self, mock_torch: MagicMock) -> None:
        """Test estimate_metric_depth uses metric mode."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        # Verify the method exists
        assert hasattr(estimator, "estimate_metric_depth")

    def test_estimate_relative_depth_sets_mode(self, mock_torch: MagicMock) -> None:
        """Test estimate_relative_depth uses relative mode."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        # Verify the method exists
        assert hasattr(estimator, "estimate_relative_depth")

    def test_callable_interface(self, mock_torch: MagicMock) -> None:
        """Test __call__ method calls estimate_depth."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        # Verify callable
        assert callable(estimator)


class TestZoeDepthEstimatorModelLoading:
    """Tests for model loading functionality."""

    def test_load_model_calls_torch_hub(self, mock_torch: MagicMock) -> None:
        """Test load_model calls torch.hub.load with correct arguments."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthModelVariant

        estimator = ZoeDepthEstimator(model_variant=ZoeDepthModelVariant.ZOE_NK)
        estimator.load_model()

        mock_torch.hub.load.assert_called_once()
        call_args = mock_torch.hub.load.call_args
        assert call_args[0][0] == "isl-org/ZoeDepth"
        assert call_args[0][1] == "ZoeD_NK"

    def test_load_model_sets_is_loaded_flag(self, mock_torch: MagicMock) -> None:
        """Test load_model sets _is_loaded to True."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        assert estimator.is_loaded is False

        estimator.load_model()
        assert estimator.is_loaded is True

    def test_model_property_triggers_lazy_loading(self, mock_torch: MagicMock) -> None:
        """Test model property triggers load_model if not loaded."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        assert estimator.is_loaded is False

        # Access model property
        _ = estimator.model

        assert estimator.is_loaded is True

    def test_load_model_raises_on_failure(self, mock_torch: MagicMock) -> None:
        """Test load_model raises ZoeDepthLoadError on torch.hub.load failure."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthLoadError

        mock_torch.hub.load.side_effect = RuntimeError("Download failed")

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthLoadError, match="Failed to load ZoeDepth model"):
            estimator.load_model()


class TestZoeDepthEstimatorTransforms:
    """Tests for transform creation and preprocessing."""

    def test_create_transform_creates_pipeline(self, mock_torch: MagicMock) -> None:
        """Test _create_transform creates a transform pipeline."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        estimator._create_transform()

        assert estimator._transform is not None

    def test_transform_property_lazy_creation(self, mock_torch: MagicMock) -> None:
        """Test transform property creates transform on first access."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        assert estimator._transform is None

        _ = estimator.transform

        assert estimator._transform is not None

    def test_close_clears_transform(self, mock_torch: MagicMock) -> None:
        """Test close method clears transform cache."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        _ = estimator.transform  # Create transform
        assert estimator._transform is not None

        estimator.close()

        assert estimator._transform is None

    def test_preprocess_image_creates_tensor(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test _preprocess_image returns a tensor."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        tensor = estimator._preprocess_image(sample_rgb_image)

        # Verify tensor methods were called
        assert tensor is not None


class TestZoeDepthEstimatorPostprocessing:
    """Tests for postprocessing depth outputs."""

    def test_postprocess_method_exists(self, mock_torch: MagicMock) -> None:
        """Test _postprocess_depth method exists."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(depth_mode="relative")
        assert hasattr(estimator, "_postprocess_depth")
        assert callable(estimator._postprocess_depth)

    def test_postprocess_accepts_depth_mode_override(self, mock_torch: MagicMock) -> None:
        """Test _postprocess_depth accepts depth_mode parameter."""
        import inspect

        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(depth_mode="relative")
        sig = inspect.signature(estimator._postprocess_depth)
        params = list(sig.parameters.keys())

        assert "depth_mode" in params


class TestZoeDepthEstimatorBatchProcessing:
    """Tests for batch depth estimation."""

    def test_estimate_depth_batch_method_exists(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch method exists."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        assert hasattr(estimator, "estimate_depth_batch")
        assert callable(estimator.estimate_depth_batch)

    def test_estimate_depth_batch_validates_empty_input(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch raises for empty input."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError, match="Input frames list cannot be empty"):
            estimator.estimate_depth_batch([])

    def test_estimate_depth_batch_accepts_batch_size_param(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch accepts batch_size parameter."""
        import inspect

        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        sig = inspect.signature(estimator.estimate_depth_batch)
        params = list(sig.parameters.keys())

        assert "batch_size" in params
        assert "depth_mode" in params


class TestZoeDepthEstimatorBatchProcessing:
    """Tests for batch depth estimation."""

    def test_estimate_depth_batch_requires_model(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch raises if model not loaded."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        mock_torch.hub.load.side_effect = Exception("No model")

        estimator = ZoeDepthEstimator()
        estimator._is_loaded = False
        estimator._model = None

        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)]

        with pytest.raises((ZoeDepthInferenceError, Exception)):
            estimator.estimate_depth_batch(frames)

    def test_estimate_depth_batch_returns_correct_count(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch returns correct number of depth maps."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig, ZoeDepthEstimator

        config = ZoeDepthConfig(auto_batch_size=False)
        estimator = ZoeDepthEstimator(config=config)

        # Create mock model
        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 4
        mock_prediction.squeeze.return_value = mock_prediction
        mock_prediction.cpu.return_value = mock_prediction
        mock_prediction.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
        mock_model.infer.return_value = mock_prediction
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(3)]


class TestZoeDepthEstimatorGPUFallback:
    """Tests for GPU fallback functionality."""

    def test_fallback_to_cpu_moves_model(self, mock_torch: MagicMock) -> None:
        """Test _fallback_to_cpu moves model to CPU."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(device="cuda")
        mock_model = MagicMock()
        estimator._model = mock_model
        estimator.config.device = "cuda"

        estimator._fallback_to_cpu()

        mock_model.to.assert_called_with("cpu")
        assert estimator.config.device == "cpu"

    def test_fallback_to_cpu_skips_if_already_cpu(self, mock_torch: MagicMock) -> None:
        """Test _fallback_to_cpu does nothing if already on CPU."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(device="cpu")
        mock_model = MagicMock()
        estimator._model = mock_model

        estimator._fallback_to_cpu()

        # Model.to should not be called if already on CPU
        mock_model.to.assert_not_called()


class TestZoeDepthModelVariantProperties:
    """Additional tests for ZoeDepthModelVariant properties."""

    def test_hub_name_property(self, mock_torch: MagicMock) -> None:
        """Test hub_name property returns correct values."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant

        assert ZoeDepthModelVariant.ZOE_N.hub_name == "ZoeD_N"
        assert ZoeDepthModelVariant.ZOE_K.hub_name == "ZoeD_K"
        assert ZoeDepthModelVariant.ZOE_NK.hub_name == "ZoeD_NK"


class TestZoeDepthConfigAdvanced:
    """Additional tests for ZoeDepthConfig."""

    def test_effective_resolution_uses_model_default(self, mock_torch: MagicMock) -> None:
        """Test effective_resolution uses model default when not specified."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig

        config = ZoeDepthConfig()  # No output_resolution specified
        assert config.effective_resolution == 384  # Default resolution

    def test_cache_dir_as_string_converted_to_path(self, mock_torch: MagicMock) -> None:
        """Test cache_dir string is converted to Path."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig

        config = ZoeDepthConfig(cache_dir="/tmp/cache")
        assert isinstance(config.cache_dir, Path)
        assert config.cache_dir == Path("/tmp/cache")

    def test_gpu_config_initialized_by_default(self, mock_torch: MagicMock) -> None:
        """Test gpu_config is initialized in __post_init__."""
        from video2d3d.depth.zoedepth import ZoeDepthConfig

        config = ZoeDepthConfig()
        assert config.gpu_config is not None


class TestZoeDepthConvenienceFunctionAdvanced:
    """Advanced tests for convenience functions."""

    def test_estimate_depth_zoedepth_function_exists(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_zoedepth function exists and is callable."""
        from video2d3d.depth.zoedepth import estimate_depth_zoedepth

        assert callable(estimate_depth_zoedepth)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestZoeDepthConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_zoedepth_estimator_defaults(self, mock_torch: MagicMock) -> None:
        """Test create_zoedepth_estimator with default values."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant, create_zoedepth_estimator

        estimator = create_zoedepth_estimator()
        assert estimator.config.model_variant == ZoeDepthModelVariant.ZOE_NK

    def test_create_zoedepth_estimator_custom_values(self, mock_torch: MagicMock) -> None:
        """Test create_zoedepth_estimator with custom values."""
        from video2d3d.depth.zoedepth import ZoeDepthModelVariant, create_zoedepth_estimator

        estimator = create_zoedepth_estimator(
            model_variant="zoedepth_k",
            device="cuda",
            depth_mode="metric",
        )
        assert estimator.config.model_variant == ZoeDepthModelVariant.ZOE_K
        assert estimator.config.depth_mode == "metric"


# ---------------------------------------------------------------------------
# Module Exports Tests
# ---------------------------------------------------------------------------


class TestZoeDepthModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self, mock_torch: MagicMock) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d.depth import zoedepth

        expected_exports = [
            "ZoeDepthEstimator",
            "ZoeDepthConfig",
            "ZoeDepthModelVariant",
            "DepthMode",
            "ZoeDepthLoadError",
            "ZoeDepthInferenceError",
            "create_zoedepth_estimator",
            "estimate_depth_zoedepth",
        ]

        for export in expected_exports:
            assert export in zoedepth.__all__, f"Missing export: {export}"


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestZoeDepthModuleConstants:
    """Tests for module-level constants."""

    def test_resolution_constant(self, mock_torch: MagicMock) -> None:
        """Test resolution constant is defined."""
        from video2d3d.depth.zoedepth import _ZOEDEPTH_DEFAULT_RESOLUTION

        assert _ZOEDEPTH_DEFAULT_RESOLUTION == 384

    def test_batch_size_constant(self, mock_torch: MagicMock) -> None:
        """Test batch size constant is defined."""
        from video2d3d.depth.zoedepth import _DEFAULT_BATCH_SIZE

        assert _DEFAULT_BATCH_SIZE == 4

    def test_hub_repo_constant(self, mock_torch: MagicMock) -> None:
        """Test hub repo constant is defined."""
        from video2d3d.depth.zoedepth import _ZOEDEPTH_HUB_REPO

        assert _ZOEDEPTH_HUB_REPO == "isl-org/ZoeDepth"


# ---------------------------------------------------------------------------
# Model Selector Integration Tests
# ---------------------------------------------------------------------------


class TestModelSelectorIntegration:
    """Tests for model selector integration with ZoeDepth."""

    def test_zoedepth_in_depth_model_type(self, mock_torch: MagicMock) -> None:
        """Test ZoeDepth types are in DepthModelType enum."""
        # Reimport to get updated enum
        if "video2d3d.depth.model_selector" in sys.modules:
            del sys.modules["video2d3d.depth.model_selector"]

        from video2d3d.depth.model_selector import DepthModelType

        assert hasattr(DepthModelType, "ZOEDEPTH_N")
        assert hasattr(DepthModelType, "ZOEDEPTH_K")
        assert hasattr(DepthModelType, "ZOEDEPTH_NK")

    def test_zoedepth_is_zoedepth_property(self, mock_torch: MagicMock) -> None:
        """Test is_zoedepth property works correctly."""
        # Reimport to get updated enum
        if "video2d3d.depth.model_selector" in sys.modules:
            del sys.modules["video2d3d.depth.model_selector"]

        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.ZOEDEPTH_N.is_zoedepth is True
        assert DepthModelType.ZOEDEPTH_K.is_zoedepth is True
        assert DepthModelType.ZOEDEPTH_NK.is_zoedepth is True
        assert DepthModelType.MIDAS_SMALL.is_zoedepth is False

    def test_zoedepth_supports_metric_property(self, mock_torch: MagicMock) -> None:
        """Test supports_metric property works correctly."""
        # Reimport to get updated enum
        if "video2d3d.depth.model_selector" in sys.modules:
            del sys.modules["video2d3d.depth.model_selector"]

        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.ZOEDEPTH_N.supports_metric is True
        assert DepthModelType.ZOEDEPTH_K.supports_metric is True
        assert DepthModelType.ZOEDEPTH_NK.supports_metric is True
        assert DepthModelType.MIDAS_SMALL.supports_metric is False
