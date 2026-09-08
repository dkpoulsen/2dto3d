"""Unit tests for MiDaS depth estimation module.

Tests cover:
- MiDaSModelType enum
- MiDaSConfig dataclass
- Custom exceptions
- DepthEstimator class (with mocked torch)
- Convenience functions

Note: These tests mock torch before importing the depth module.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

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
    mock.no_grad = MagicMock(
        return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock(return_value=False))
    )
    mock.backends.cudnn.benchmark = False
    mock.Tensor = MagicMock

    # Mock tensor operations
    mock_tensor = MagicMock()
    mock_tensor.dim.return_value = 3
    mock_tensor.unsqueeze.return_value = mock_tensor
    mock_tensor.to.return_value = mock_tensor
    mock_tensor.squeeze.return_value = mock_tensor
    mock_tensor.cpu.return_value = mock_tensor
    mock_tensor.half.return_value = mock_tensor
    mock_tensor.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
    mock.from_numpy = MagicMock(return_value=mock_tensor)

    # Mock cat for batch operations
    mock.cat = MagicMock(return_value=mock_tensor)

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
    # Store original modules
    original_modules = {}
    modules_to_mock = [
        "torch",
        "torch.nn",
        "torch.nn.functional",
        "torchvision",
        "torchvision.transforms",
        "loguru",
        "video2d3d.utils",
        "video2d3d.utils.logger",
        "video2d3d.utils.gpu",
    ]

    for mod in modules_to_mock:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]

    # Create mock modules
    mock_torch = _create_mock_torch()
    mock_torch_nn = MagicMock()
    mock_torch_nn.functional = _create_mock_torch_nn_functional()
    mock_torchvision = MagicMock()
    mock_torchvision.transforms = MagicMock()

    # Set mock modules
    sys.modules["torch"] = mock_torch
    sys.modules["torch.nn"] = mock_torch_nn
    sys.modules["torch.nn.functional"] = mock_torch_nn.functional
    sys.modules["torchvision"] = mock_torchvision
    sys.modules["torchvision.transforms"] = mock_torchvision.transforms

    # Mock loguru
    sys.modules["loguru"] = MagicMock()

    # Mock video2d3d.utils modules (package-like so submodule imports work)
    mock_utils = MagicMock()
    mock_utils.__path__ = []
    mock_gpu = MagicMock()
    mock_gpu.GPUConfig = MagicMock
    mock_gpu.select_device = MagicMock(return_value=MagicMock(device="cpu"))
    mock_gpu.clear_gpu_memory = MagicMock()
    mock_gpu.compute_optimal_batch_size = MagicMock(return_value=4)
    mock_gpu.get_memory_usage = MagicMock(return_value={})
    mock_gpu.setup_device = MagicMock(return_value=MagicMock(device="cpu"))
    mock_gpu.with_oom_retry = MagicMock()
    mock_gpu.GPUError = Exception
    mock_gpu.OutOfMemoryError = Exception
    sys.modules["video2d3d.utils"] = mock_utils
    sys.modules["video2d3d.utils.gpu"] = mock_gpu
    sys.modules["video2d3d.utils.logger"] = _create_mock_logger_module()
    # Clear any cached imports of the depth module
    for mod_name in [m for m in sys.modules if m == "video2d3d.depth" or m.startswith("video2d3d.depth.")]:
        del sys.modules[mod_name]

    yield

    # Restore original modules
    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    # Clear depth module cache (including submodules) so later imports start fresh
    for mod_name in [m for m in sys.modules if m == "video2d3d.depth" or m.startswith("video2d3d.depth.")]:
        del sys.modules[mod_name]


@pytest.fixture
def mock_torch() -> MagicMock:
    """Get the mocked torch module."""
    return sys.modules["torch"]


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image for testing."""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# MiDaSModelType Tests
# ---------------------------------------------------------------------------


class TestMiDaSModelType:
    """Tests for MiDaSModelType enum."""

    def test_enum_values(self, mock_torch: MagicMock) -> None:
        """Test that all expected model types exist."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.MIDAS_V21_SMALL.value == "MiDaS_small"
        assert MiDaSModelType.MIDAS_V21.value == "MiDaS"
        assert MiDaSModelType.DPT_LARGE.value == "DPT_Large"
        assert MiDaSModelType.DPT_HYBRID.value == "DPT_Hybrid"

    def test_from_string_midas_small(self, mock_torch: MagicMock) -> None:
        """Test from_string with various MiDaS small name formats."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.from_string("midas_small") == MiDaSModelType.MIDAS_V21_SMALL
        assert MiDaSModelType.from_string("MIDAS_SMALL") == MiDaSModelType.MIDAS_V21_SMALL
        assert MiDaSModelType.from_string("midas-small") == MiDaSModelType.MIDAS_V21_SMALL
        assert MiDaSModelType.from_string("midas small") == MiDaSModelType.MIDAS_V21_SMALL

    def test_from_string_dpt_large(self, mock_torch: MagicMock) -> None:
        """Test from_string with various DPT Large name formats."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.from_string("dpt_large") == MiDaSModelType.DPT_LARGE
        assert MiDaSModelType.from_string("DPT_Large") == MiDaSModelType.DPT_LARGE
        assert MiDaSModelType.from_string("dpt-large") == MiDaSModelType.DPT_LARGE

    def test_from_string_dpt_hybrid(self, mock_torch: MagicMock) -> None:
        """Test from_string with various DPT Hybrid name formats."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.from_string("dpt_hybrid") == MiDaSModelType.DPT_HYBRID
        assert MiDaSModelType.from_string("DPT_Hybrid") == MiDaSModelType.DPT_HYBRID

    def test_from_string_invalid_raises(self, mock_torch: MagicMock) -> None:
        """Test that invalid model name raises ValueError."""
        from video2d3d.depth import MiDaSModelType

        with pytest.raises(ValueError, match="Unknown model name"):
            MiDaSModelType.from_string("invalid_model")

    def test_hub_name_property(self, mock_torch: MagicMock) -> None:
        """Test hub_name property returns correct value."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.MIDAS_V21_SMALL.hub_name == "MiDaS_small"
        assert MiDaSModelType.DPT_LARGE.hub_name == "DPT_Large"

    def test_default_resolution_midas(self, mock_torch: MagicMock) -> None:
        """Test default_resolution for MiDaS models."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.MIDAS_V21_SMALL.default_resolution == 256
        assert MiDaSModelType.MIDAS_V21.default_resolution == 256

    def test_default_resolution_dpt(self, mock_torch: MagicMock) -> None:
        """Test default_resolution for DPT models."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.DPT_LARGE.default_resolution == 384
        assert MiDaSModelType.DPT_HYBRID.default_resolution == 384

    def test_is_dpt_property(self, mock_torch: MagicMock) -> None:
        """Test is_dpt property returns correct boolean."""
        from video2d3d.depth import MiDaSModelType

        assert MiDaSModelType.MIDAS_V21_SMALL.is_dpt is False
        assert MiDaSModelType.MIDAS_V21.is_dpt is False
        assert MiDaSModelType.DPT_LARGE.is_dpt is True
        assert MiDaSModelType.DPT_HYBRID.is_dpt is True


# ---------------------------------------------------------------------------
# MiDaSConfig Tests
# ---------------------------------------------------------------------------


class TestMiDaSConfig:
    """Tests for MiDaSConfig dataclass."""

    def test_default_values(self, mock_torch: MagicMock) -> None:
        """Test default configuration values."""
        from video2d3d.depth import MiDaSConfig, MiDaSModelType

        config = MiDaSConfig()

        assert config.model_type == MiDaSModelType.MIDAS_V21_SMALL
        assert config.device == "cpu"
        assert config.cache_dir is None
        assert config.auto_download is True

    def test_custom_values(self, mock_torch: MagicMock) -> None:
        """Test custom configuration values."""
        from video2d3d.depth import MiDaSConfig, MiDaSModelType

        config = MiDaSConfig(
            model_type=MiDaSModelType.DPT_LARGE,
            device="cuda",
            cache_dir=Path("/custom/cache"),
            auto_download=False,
            output_resolution=512,
            use_fp16=True,
        )

        assert config.model_type == MiDaSModelType.DPT_LARGE
        assert config.device == "cuda"
        assert config.cache_dir == Path("/custom/cache")

    def test_string_model_type_conversion(self, mock_torch: MagicMock) -> None:
        """Test that string model type is converted to enum."""
        from video2d3d.depth import MiDaSConfig, MiDaSModelType

        config = MiDaSConfig(model_type="dpt_large")  # type: ignore[arg-type]
        assert config.model_type == MiDaSModelType.DPT_LARGE

    def test_effective_resolution_with_custom(self, mock_torch: MagicMock) -> None:
        """Test effective_resolution with custom output_resolution."""
        from video2d3d.depth import MiDaSConfig

        config = MiDaSConfig(output_resolution=512)
        assert config.effective_resolution == 512


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


class TestDepthEstimationExceptions:
    """Tests for custom exception classes."""

    def test_depth_estimation_error_basic(self, mock_torch: MagicMock) -> None:
        """Test basic DepthEstimationError."""
        from video2d3d.depth import DepthEstimationError

        error = DepthEstimationError("Test error")
        assert str(error) == "Test error"
        assert error.model_type is None
        assert error.device is None

    def test_depth_estimation_error_with_params(self, mock_torch: MagicMock) -> None:
        """Test DepthEstimationError with all parameters."""
        from video2d3d.depth import DepthEstimationError

        original = ValueError("Original error")
        error = DepthEstimationError(
            "Test error",
            model_type="midas_small",
            device="cuda",
            original_exception=original,
        )

        assert error.model_type == "midas_small"
        assert error.device == "cuda"
        assert error.original_exception is original

    def test_model_load_error_inherits(self, mock_torch: MagicMock) -> None:
        """Test ModelLoadError inherits from DepthEstimationError."""
        from video2d3d.depth import DepthEstimationError, ModelLoadError

        error = ModelLoadError("Load failed")
        assert isinstance(error, DepthEstimationError)

    def test_inference_error_inherits(self, mock_torch: MagicMock) -> None:
        """Test InferenceError inherits from DepthEstimationError."""
        from video2d3d.depth import DepthEstimationError, InferenceError

        error = InferenceError("Inference failed")
        assert isinstance(error, DepthEstimationError)


# ---------------------------------------------------------------------------
# DepthEstimator Tests
# ---------------------------------------------------------------------------


class TestDepthEstimatorInit:
    """Tests for DepthEstimator initialization."""

    def test_init_with_defaults(self, mock_torch: MagicMock) -> None:
        """Test initialization with default values."""
        from video2d3d.depth import DepthEstimator, MiDaSModelType

        estimator = DepthEstimator()

        assert estimator.config.model_type == MiDaSModelType.MIDAS_V21_SMALL
        assert estimator.config.device == "cpu"
        assert estimator.is_loaded is False

    def test_init_with_model_type_string(self, mock_torch: MagicMock) -> None:
        """Test initialization with model type as string."""
        from video2d3d.depth import DepthEstimator, MiDaSModelType

        estimator = DepthEstimator(model_type="dpt_large")
        assert estimator.config.model_type == MiDaSModelType.DPT_LARGE

    def test_init_with_config(self, mock_torch: MagicMock) -> None:
        """Test initialization with MiDaSConfig."""
        from video2d3d.depth import DepthEstimator, MiDaSConfig, MiDaSModelType

        config = MiDaSConfig(model_type=MiDaSModelType.DPT_LARGE, device="cpu")
        estimator = DepthEstimator(config=config)

        assert estimator.config.model_type == MiDaSModelType.DPT_LARGE


class TestDepthEstimatorInputValidation:
    """Tests for input validation in DepthEstimator."""

    def test_estimate_depth_invalid_type(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises InferenceError for non-array input."""
        from video2d3d.depth import DepthEstimator, InferenceError

        estimator = DepthEstimator()

        with pytest.raises(InferenceError, match="Input must be a numpy array"):
            estimator.estimate_depth([[1, 2], [3, 4]])  # type: ignore[arg-type]

    def test_estimate_depth_wrong_dimensions(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises InferenceError for wrong dimensions."""
        from video2d3d.depth import DepthEstimator, InferenceError

        estimator = DepthEstimator()

        with pytest.raises(InferenceError, match="Input must be 3D array"):
            estimator.estimate_depth(np.zeros((100, 100)))

    def test_estimate_depth_wrong_channels(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth raises InferenceError for wrong channel count."""
        from video2d3d.depth import DepthEstimator, InferenceError

        estimator = DepthEstimator()

        with pytest.raises(InferenceError, match="Input must have 3 channels"):
            estimator.estimate_depth(np.zeros((100, 100, 1)))

    def test_estimate_depth_batch_empty_list(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch raises InferenceError for empty list."""
        from video2d3d.depth import DepthEstimator, InferenceError

        estimator = DepthEstimator()

        with pytest.raises(InferenceError, match="Input frames list cannot be empty"):
            estimator.estimate_depth_batch([])


class TestDepthEstimatorContextManager:
    """Tests for DepthEstimator context manager."""

    def test_context_manager_enter_returns_self(self, mock_torch: MagicMock) -> None:
        """Test __enter__ returns self."""
        from video2d3d.depth import DepthEstimator

        estimator = DepthEstimator()
        with estimator as ctx_estimator:
            assert ctx_estimator is estimator

    def test_close_clears_model(self, mock_torch: MagicMock) -> None:
        """Test close method clears model resources."""
        from video2d3d.depth import DepthEstimator

        estimator = DepthEstimator()
        estimator._model = MagicMock()  # type: ignore[assignment]
        estimator._is_loaded = True

        estimator.close()

        assert estimator._model is None
        assert estimator.is_loaded is False


class TestDepthEstimatorCallable:
    """Tests for DepthEstimator callable interface."""

    def test_callable_calls_estimate_depth(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test __call__ delegates to estimate_depth."""
        from video2d3d.depth import DepthEstimator

        estimator = DepthEstimator()
        estimator.estimate_depth = MagicMock(return_value=np.zeros((100, 100)))  # type: ignore[method-assign]

        estimator(sample_rgb_image)
        estimator.estimate_depth.assert_called_once_with(sample_rgb_image)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_estimator_defaults(self, mock_torch: MagicMock) -> None:
        """Test create_estimator with default values."""
        from video2d3d.depth import MiDaSModelType, create_estimator

        estimator = create_estimator()
        assert estimator.config.model_type == MiDaSModelType.MIDAS_V21_SMALL

    def test_create_estimator_custom_values(self, mock_torch: MagicMock) -> None:
        """Test create_estimator with custom values."""
        from video2d3d.depth import MiDaSModelType, create_estimator

        estimator = create_estimator(model_type="dpt_large", device="cuda")
        assert estimator.config.model_type == MiDaSModelType.DPT_LARGE


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_resolution_constants(self, mock_torch: MagicMock) -> None:
        """Test resolution constants are defined."""
        from video2d3d.depth import _DPT_DEFAULT_RESOLUTION, _MIDAS_DEFAULT_RESOLUTION

        assert _MIDAS_DEFAULT_RESOLUTION == 256
        assert _DPT_DEFAULT_RESOLUTION == 384

    def test_batch_size_constant(self, mock_torch: MagicMock) -> None:
        """Test batch size constant is defined."""
        from video2d3d.depth import _DEFAULT_BATCH_SIZE

        assert _DEFAULT_BATCH_SIZE == 4


# ---------------------------------------------------------------------------
# Module Exports Tests
# ---------------------------------------------------------------------------


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self, mock_torch: MagicMock) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d import depth

        expected_exports = [
            "DepthEstimator",
            "MiDaSConfig",
            "MiDaSModelType",
            "DepthEstimationError",
            "ModelLoadError",
            "InferenceError",
            "create_estimator",
            "estimate_depth_single",
        ]

        for export in expected_exports:
            assert export in depth.__all__, f"Missing export: {export}"


# ---------------------------------------------------------------------------
# Model Caching Tests
# ---------------------------------------------------------------------------


class TestModelCaching:
    """Tests for model caching behavior."""

    def test_torch_hub_directory_set(self, mock_torch: MagicMock) -> None:
        """Test that torch hub directory is configured."""
        from pathlib import Path

        from video2d3d.depth import DepthEstimator

        custom_cache = Path("/tmp/test_cache")
        config = type(
            "Config",
            (),
            {
                "model_type": type("MT", (), {"value": "MiDaS_small", "hub_name": "MiDaS_small"})(),
                "device": "cpu",
                "cache_dir": custom_cache,
                "auto_download": True,
                "optimize": False,
                "use_fp16": False,
            },
        )()

        estimator = DepthEstimator.__new__(DepthEstimator)
        estimator.config = config
        estimator._model = None
        estimator._transform = None
        estimator._is_loaded = False
        estimator._temporal_smoother = None
        estimator._temporal_config = None

        estimator._get_torch_hub_dir()

        mock_torch.hub.set_dir.assert_called()

    def test_cache_dir_from_config(self, mock_torch: MagicMock) -> None:
        """Test that cache directory is used from config."""
        from pathlib import Path

        from video2d3d.depth import DepthEstimator, MiDaSConfig

        custom_cache = Path("/tmp/test_cache")
        config = MiDaSConfig(cache_dir=custom_cache)
        estimator = DepthEstimator(config=config)

        # Verify config has the cache_dir
        assert estimator.config.cache_dir == custom_cache

    def test_default_cache_dir(self, mock_torch: MagicMock) -> None:
        """Test that default cache dir uses torch.hub.get_dir()."""
        from video2d3d.depth import DepthEstimator

        mock_torch.hub.get_dir.return_value = "/default/torch/hub"

        estimator = DepthEstimator()
        hub_dir = estimator._get_torch_hub_dir()

        # Should use the default torch hub directory
        assert str(hub_dir) == "/default/torch/hub"

    def test_auto_download_flag_passed_to_torch_hub(self, mock_torch: MagicMock) -> None:
        """Test that auto_download flag is passed correctly."""
        from video2d3d.depth import DepthEstimator, MiDaSConfig

        # Test with auto_download=True (default)
        config = MiDaSConfig(auto_download=True)
        estimator = DepthEstimator(config=config)
        estimator.load_model()

        # Verify torch.hub.load was called
        assert mock_torch.hub.load.call_count >= 1

    def test_model_load_only_once(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that model is only loaded once during multiple inferences."""
        from video2d3d.depth import DepthEstimator

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model
        mock_output = MagicMock()
        mock_output.dim.return_value = 4
        mock_output.squeeze.return_value = mock_output
        mock_output.cpu.return_value = mock_output
        mock_output.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
        mock_model.return_value = mock_output

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms, mock_transforms]

        estimator = DepthEstimator()

        # Multiple calls to property should not reload model
        _ = estimator.model
        _ = estimator.model
        _ = estimator.model

        # Model load should only be called twice (model + transforms)
        assert mock_torch.hub.load.call_count <= 3


# ---------------------------------------------------------------------------
# GPU Fallback Tests
# ---------------------------------------------------------------------------


class TestGPUFallback:
    """Tests for GPU fallback behavior."""

    def test_fallback_to_cpu_on_oom(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that GPU OOM triggers CPU fallback."""
        from video2d3d.depth import DepthEstimator, MiDaSConfig

        config = MiDaSConfig(device="cuda", fallback_to_cpu=True)
        estimator = DepthEstimator(config=config)

        # Set up model that raises OOM on first call
        call_count = [0]

        def mock_inference(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("CUDA out of memory")
            mock_output = MagicMock()
            mock_output.dim.return_value = 4
            mock_output.squeeze.return_value = mock_output
            mock_output.cpu.return_value = mock_output
            mock_output.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
            return mock_output

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model
        mock_model.side_effect = mock_inference

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        with patch("video2d3d.depth.F") as mock_F:
            mock_F.interpolate.return_value = MagicMock(
                squeeze=MagicMock(
                    return_value=MagicMock(
                        numpy=MagicMock(return_value=np.zeros((100, 100), dtype=np.float32))
                    )
                )
            )
            result = estimator.estimate_depth(sample_rgb_image)

            # Should have fallen back to CPU
            assert estimator.config.device == "cpu"
            assert isinstance(result, np.ndarray)

    def test_no_fallback_when_disabled(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that OOM raises error when fallback is disabled."""
        from video2d3d.depth import DepthEstimator, InferenceError, MiDaSConfig

        config = MiDaSConfig(device="cuda", fallback_to_cpu=False)
        estimator = DepthEstimator(config=config)

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model
        mock_model.side_effect = RuntimeError("CUDA out of memory")

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        with patch("video2d3d.depth.F"):
            with pytest.raises(InferenceError, match="Depth estimation failed"):
                estimator.estimate_depth(sample_rgb_image)


# Mark as slow test
import pytest

pytestmark = pytest.mark.slow
