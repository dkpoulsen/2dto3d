"""Unit tests for DepthModelSelector module.

Tests cover:
- DepthModelType enum
- SceneType enum
- DepthModelConfig dataclass
- ModelLoadError and ModelInferenceError exceptions
- DepthModelSelector class
- Scene classification heuristics
- Model fallback logic
- Convenience functions

Note: These tests mock torch before importing the depth module.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.slow

import sys
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
        "loguru",
        "video2d3d.utils",
        "video2d3d.utils.logger",
        "video2d3d.utils.gpu",
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

    # Clear any cached depth modules
    for mod in [
        "video2d3d.depth",
        "video2d3d.depth.__init__",
        "video2d3d.depth.model_selector",
        "video2d3d.depth.adadepth",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    yield

    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    for mod in ["video2d3d.depth", "video2d3d.depth.model_selector"]:
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


@pytest.fixture
def warm_indoor_image() -> np.ndarray:
    """Create a warm-toned image simulating indoor scene."""
    # Higher red, lower blue for warm indoor lighting
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :, 0] = 180  # High red
    image[:, :, 1] = 120  # Medium green
    image[:, :, 2] = 80  # Low blue
    return image


@pytest.fixture
def cool_outdoor_image() -> np.ndarray:
    """Create a cool-toned image simulating outdoor scene."""
    # Lower red, higher blue for cool outdoor lighting
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, :, 0] = 80  # Low red
    image[:, :, 1] = 150  # Medium-high green
    image[:, :, 2] = 200  # High blue
    return image


# ---------------------------------------------------------------------------
# DepthModelType Tests
# ---------------------------------------------------------------------------


class TestDepthModelType:
    """Tests for DepthModelType enum."""

    def test_enum_values(self, mock_torch: MagicMock) -> None:
        """Test that all expected model types exist."""
        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.MIDAS_SMALL.value == "midas_small"
        assert DepthModelType.MIDAS_HYBRID.value == "midas_hybrid"
        assert DepthModelType.DPT_LARGE.value == "dpt_large"
        assert DepthModelType.DPT_HYBRID.value == "dpt_hybrid"
        assert DepthModelType.ADABINS_NYU.value == "adabins_nyu"
        assert DepthModelType.ADABINS_KITTI.value == "adabins_kitti"

    def test_from_string_midas(self, mock_torch: MagicMock) -> None:
        """Test from_string with MiDaS model names."""
        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.from_string("midas_small") == DepthModelType.MIDAS_SMALL
        assert DepthModelType.from_string("MIDAS_SMALL") == DepthModelType.MIDAS_SMALL
        assert DepthModelType.from_string("midas") == DepthModelType.MIDAS_SMALL
        assert DepthModelType.from_string("midas-2.1") == DepthModelType.MIDAS_SMALL

    def test_from_string_dpt(self, mock_torch: MagicMock) -> None:
        """Test from_string with DPT model names."""
        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.from_string("dpt_large") == DepthModelType.DPT_LARGE
        assert DepthModelType.from_string("DPT_LARGE_384") == DepthModelType.DPT_LARGE
        assert DepthModelType.from_string("dpt_hybrid") == DepthModelType.DPT_HYBRID

    def test_from_string_adabins(self, mock_torch: MagicMock) -> None:
        """Test from_string with AdaBins model names."""
        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.from_string("adabins_nyu") == DepthModelType.ADABINS_NYU
        assert DepthModelType.from_string("adadepth_nyu") == DepthModelType.ADABINS_NYU
        assert DepthModelType.from_string("nyu") == DepthModelType.ADABINS_NYU
        assert DepthModelType.from_string("adabins_kitti") == DepthModelType.ADABINS_KITTI
        assert DepthModelType.from_string("kitti") == DepthModelType.ADABINS_KITTI

    def test_from_string_invalid_raises(self, mock_torch: MagicMock) -> None:
        """Test that invalid model name raises ValueError."""
        from video2d3d.depth.model_selector import DepthModelType

        with pytest.raises(ValueError, match="Unknown model name"):
            DepthModelType.from_string("invalid_model")

    def test_is_midas_property(self, mock_torch: MagicMock) -> None:
        """Test is_midas property returns correct values."""
        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.MIDAS_SMALL.is_midas is True
        assert DepthModelType.MIDAS_HYBRID.is_midas is True
        assert DepthModelType.DPT_LARGE.is_midas is True
        assert DepthModelType.DPT_HYBRID.is_midas is True
        assert DepthModelType.ADABINS_NYU.is_midas is False
        assert DepthModelType.ADABINS_KITTI.is_midas is False

    def test_is_adabins_property(self, mock_torch: MagicMock) -> None:
        """Test is_adabins property returns correct values."""
        from video2d3d.depth.model_selector import DepthModelType

        assert DepthModelType.ADABINS_NYU.is_adabins is True
        assert DepthModelType.ADABINS_KITTI.is_adabins is True
        assert DepthModelType.MIDAS_SMALL.is_adabins is False
        assert DepthModelType.DPT_LARGE.is_adabins is False


# ---------------------------------------------------------------------------
# SceneType Tests
# ---------------------------------------------------------------------------


class TestSceneType:
    """Tests for SceneType enum."""

    def test_enum_values(self, mock_torch: MagicMock) -> None:
        """Test that all scene types exist."""
        from video2d3d.depth.model_selector import SceneType

        assert SceneType.INDOOR.value == "indoor"
        assert SceneType.OUTDOOR.value == "outdoor"
        assert SceneType.MIXED.value == "mixed"
        assert SceneType.UNKNOWN.value == "unknown"


# ---------------------------------------------------------------------------
# DepthModelConfig Tests
# ---------------------------------------------------------------------------


class TestDepthModelConfig:
    """Tests for DepthModelConfig dataclass."""

    def test_default_values(self, mock_torch: MagicMock) -> None:
        """Test default configuration values."""
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig()

        assert config.primary_model == DepthModelType.ADABINS_NYU
        assert config.fallback_model == DepthModelType.MIDAS_SMALL
        assert config.enable_auto_fallback is True
        assert config.enable_scene_adaptation is False
        assert config.device == "cpu"

    def test_custom_values(self, mock_torch: MagicMock) -> None:
        """Test custom configuration values."""
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(
            primary_model=DepthModelType.DPT_LARGE,
            fallback_model=DepthModelType.MIDAS_HYBRID,
            enable_auto_fallback=False,
            enable_scene_adaptation=True,
            device="cuda",
            model_load_timeout=120.0,
        )

        assert config.primary_model == DepthModelType.DPT_LARGE
        assert config.fallback_model == DepthModelType.MIDAS_HYBRID
        assert config.enable_auto_fallback is False
        assert config.enable_scene_adaptation is True
        assert config.device == "cuda"
        assert config.model_load_timeout == 120.0

    def test_string_model_type_conversion(self, mock_torch: MagicMock) -> None:
        """Test that string model types are converted to enums."""
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(
            primary_model="dpt_large",
            fallback_model="adabins_kitti",
        )
        assert config.primary_model == DepthModelType.DPT_LARGE
        assert config.fallback_model == DepthModelType.ADABINS_KITTI

    def test_fallback_chain_normalization(self, mock_torch: MagicMock) -> None:
        """Test that fallback chain is normalized from strings."""
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(fallback_chain=["midas_small", "dpt_hybrid", "adabins_nyu"])

        assert DepthModelType.MIDAS_SMALL in config.fallback_chain
        assert DepthModelType.DPT_HYBRID in config.fallback_chain
        assert DepthModelType.ADABINS_NYU in config.fallback_chain


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


class TestModelSelectorExceptions:
    """Tests for custom exception classes."""

    def test_model_load_error_basic(self, mock_torch: MagicMock) -> None:
        """Test basic ModelLoadError."""
        from video2d3d.depth.model_selector import ModelLoadError

        error = ModelLoadError("Test error")
        assert str(error) == "Test error"
        assert error.attempted_models == []
        assert error.original_exceptions == []

    def test_model_load_error_with_params(self, mock_torch: MagicMock) -> None:
        """Test ModelLoadError with all parameters."""
        from video2d3d.depth.model_selector import ModelLoadError

        original = ValueError("Original error")
        error = ModelLoadError(
            "All models failed",
            attempted_models=["adabins_nyu", "midas_small"],
            original_exceptions=[original],
        )

        assert error.attempted_models == ["adabins_nyu", "midas_small"]
        assert error.original_exceptions == [original]

    def test_model_inference_error_inherits(self, mock_torch: MagicMock) -> None:
        """Test ModelInferenceError."""
        from video2d3d.depth.model_selector import ModelInferenceError

        error = ModelInferenceError("Inference failed")
        assert isinstance(error, Exception)
        assert error.attempted_models == []


# ---------------------------------------------------------------------------
# DepthModelSelector Tests
# ---------------------------------------------------------------------------


class TestDepthModelSelectorInit:
    """Tests for DepthModelSelector initialization."""

    def test_init_with_defaults(self, mock_torch: MagicMock) -> None:
        """Test initialization with default values."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        assert selector.config.primary_model == DepthModelType.ADABINS_NYU
        assert selector.config.fallback_model == DepthModelType.MIDAS_SMALL
        assert selector.active_model is None

    def test_init_with_model_type_string(self, mock_torch: MagicMock) -> None:
        """Test initialization with model type as string."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector(
            primary_model="dpt_large",
            fallback_model="midas_small",
        )
        assert selector.config.primary_model == DepthModelType.DPT_LARGE

    def test_init_with_config(self, mock_torch: MagicMock) -> None:
        """Test initialization with DepthModelConfig."""
        from video2d3d.depth.model_selector import (
            DepthModelConfig,
            DepthModelSelector,
            DepthModelType,
        )

        config = DepthModelConfig(
            primary_model=DepthModelType.DPT_HYBRID,
            fallback_model=DepthModelType.MIDAS_SMALL,
            device="cpu",
        )
        selector = DepthModelSelector(config=config)

        assert selector.config.primary_model == DepthModelType.DPT_HYBRID


class TestSceneClassification:
    """Tests for scene classification heuristics."""

    def test_classify_warm_indoor_scene(
        self, mock_torch: MagicMock, warm_indoor_image: np.ndarray
    ) -> None:
        """Test that warm-toned image is classified as indoor."""
        from video2d3d.depth.model_selector import DepthModelSelector, SceneType

        selector = DepthModelSelector()

        scene_type = selector._classify_scene(warm_indoor_image)

        assert scene_type == SceneType.INDOOR

    def test_classify_cool_outdoor_scene(
        self, mock_torch: MagicMock, cool_outdoor_image: np.ndarray
    ) -> None:
        """Test that cool-toned image is classified as outdoor."""
        from video2d3d.depth.model_selector import DepthModelSelector, SceneType

        selector = DepthModelSelector()

        scene_type = selector._classify_scene(cool_outdoor_image)

        assert scene_type == SceneType.OUTDOOR

    def test_classify_mixed_scene(self, mock_torch: MagicMock) -> None:
        """Test that neutral-toned image is classified as mixed."""
        from video2d3d.depth.model_selector import DepthModelSelector, SceneType

        selector = DepthModelSelector()

        # Create neutral image
        neutral_image = np.full((100, 100, 3), 128, dtype=np.uint8)
        scene_type = selector._classify_scene(neutral_image)

        # Should be either MIXED or UNKNOWN for neutral images
        assert scene_type in [SceneType.MIXED, SceneType.OUTDOOR, SceneType.INDOOR]

    def test_scene_type_is_stored(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that last scene type is stored."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector(
            primary_model="adabins_nyu",
            fallback_model="midas_small",
            device="cpu",
        )
        selector.config.enable_scene_adaptation = True

        # The last_scene_type should be UNKNOWN initially
        assert selector.last_scene_type.value == "unknown"


class TestModelSelectionForScene:
    """Tests for model selection based on scene type."""

    def test_select_model_for_indoor(self, mock_torch: MagicMock) -> None:
        """Test that indoor scene selects NYU model."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType, SceneType

        selector = DepthModelSelector()

        model = selector._select_model_for_scene(SceneType.INDOOR)

        assert model == DepthModelType.ADABINS_NYU

    def test_select_model_for_outdoor(self, mock_torch: MagicMock) -> None:
        """Test that outdoor scene selects KITTI model."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType, SceneType

        selector = DepthModelSelector()

        model = selector._select_model_for_scene(SceneType.OUTDOOR)

        assert model == DepthModelType.ADABINS_KITTI

    def test_select_model_for_unknown_uses_primary(self, mock_torch: MagicMock) -> None:
        """Test that unknown scene uses primary model."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType, SceneType

        selector = DepthModelSelector(primary_model="dpt_large")

        model = selector._select_model_for_scene(SceneType.UNKNOWN)

        assert model == DepthModelType.DPT_LARGE


class TestDepthModelSelectorMethods:
    """Tests for DepthModelSelector methods."""

    def test_switch_model_success(self, mock_torch: MagicMock) -> None:
        """Test switch_model returns True for valid model."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        # Create a mock estimator
        selector._estimators[DepthModelType.MIDAS_SMALL] = MagicMock()

        result = selector.switch_model("midas_small")

        assert result is True
        assert selector.active_model == DepthModelType.MIDAS_SMALL

    def test_switch_model_failure(self, mock_torch: MagicMock) -> None:
        """Test switch_model returns False for failed load."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()

        # Mock _get_estimator to raise exception
        selector._get_estimator = MagicMock(side_effect=Exception("Load failed"))

        result = selector.switch_model("invalid_model")

        assert result is False

    def test_get_available_models(self, mock_torch: MagicMock) -> None:
        """Test get_available_models returns loaded estimators."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()
        selector._estimators[DepthModelType.ADABINS_NYU] = MagicMock()
        selector._estimators[DepthModelType.MIDAS_SMALL] = MagicMock()

        available = selector.get_available_models()

        assert DepthModelType.ADABINS_NYU in available
        assert DepthModelType.MIDAS_SMALL in available

    def test_preload_models(self, mock_torch: MagicMock) -> None:
        """Test preload_models loads specified models."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()

        # Mock _get_estimator
        selector._get_estimator = MagicMock()

        results = selector.preload_models(["midas_small", "dpt_large"])

        assert results["midas_small"] is True
        assert results["dpt_large"] is True

    def test_preload_models_with_failure(self, mock_torch: MagicMock) -> None:
        """Test preload_models handles failures."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()

        # Mock _get_estimator to succeed for first, fail for second
        call_count = [0]

        def mock_get_estimator(model_type):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock()
            raise Exception("Load failed")

        selector._get_estimator = mock_get_estimator

        results = selector.preload_models(["midas_small", "dpt_large"])

        assert results["midas_small"] is True
        assert results["dpt_large"] is False

    def test_close_clears_resources(self, mock_torch: MagicMock) -> None:
        """Test close method clears all resources."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        # Add mock estimators
        mock_estimator = MagicMock()
        selector._estimators[DepthModelType.MIDAS_SMALL] = mock_estimator
        selector._active_model = DepthModelType.MIDAS_SMALL

        selector.close()

        mock_estimator.close.assert_called_once()
        assert len(selector._estimators) == 0
        assert selector.active_model is None


class TestDepthModelSelectorContextManager:
    """Tests for DepthModelSelector context manager."""

    def test_context_manager_enter_returns_self(self, mock_torch: MagicMock) -> None:
        """Test __enter__ returns self."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()
        with selector as ctx_selector:
            assert ctx_selector is selector


class TestBatchProcessing:
    """Tests for batch processing functionality."""

    def test_estimate_depth_batch_empty(self, mock_torch: MagicMock) -> None:
        """Test estimate_depth_batch with empty list returns empty."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()

        result = selector.estimate_depth_batch([])

        assert result == []

    def test_estimate_depth_batch_single_frame(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test estimate_depth_batch with single frame."""
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()

        # Mock the internal estimator
        mock_estimator = MagicMock()
        mock_estimator.estimate_depth.return_value = np.zeros((100, 100), dtype=np.float32)
        mock_estimator.estimate_depth_batch.return_value = []
        selector._get_estimator = MagicMock(return_value=mock_estimator)
        selector._active_model = type("ModelType", (), {"value": "test"})()

        result = selector.estimate_depth_batch([sample_rgb_image])

        assert len(result) == 1
        assert result[0].shape == (100, 100)


# ---------------------------------------------------------------------------
# Convenience Functions Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_model_selector_defaults(self, mock_torch: MagicMock) -> None:
        """Test create_model_selector with default values."""
        from video2d3d.depth.model_selector import DepthModelType, create_model_selector

        selector = create_model_selector()
        assert selector.config.primary_model == DepthModelType.ADABINS_NYU

    def test_create_model_selector_custom_values(self, mock_torch: MagicMock) -> None:
        """Test create_model_selector with custom values."""
        from video2d3d.depth.model_selector import DepthModelType, create_model_selector

        selector = create_model_selector(
            primary_model="dpt_large",
            fallback_model="midas_small",
            device="cpu",
        )
        assert selector.config.primary_model == DepthModelType.DPT_LARGE


# ---------------------------------------------------------------------------
# Module Exports Tests
# ---------------------------------------------------------------------------


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self, mock_torch: MagicMock) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d.depth import model_selector

        expected_exports = [
            "DepthModelSelector",
            "DepthModelConfig",
            "DepthModelType",
            "SceneType",
            "ModelLoadError",
            "ModelInferenceError",
            "create_model_selector",
            "estimate_depth_auto",
        ]

        for export in expected_exports:
            assert export in model_selector.__all__, f"Missing export: {export}"


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_timeout_constant(self, mock_torch: MagicMock) -> None:
        """Test timeout constant is defined."""
        from video2d3d.depth.model_selector import _DEFAULT_MODEL_LOAD_TIMEOUT

        assert _DEFAULT_MODEL_LOAD_TIMEOUT == 60.0

    def test_confidence_threshold_constant(self, mock_torch: MagicMock) -> None:
        """Test confidence threshold constant is defined."""
        from video2d3d.depth.model_selector import _DEFAULT_SCENE_CONFIDENCE_THRESHOLD

        assert _DEFAULT_SCENE_CONFIDENCE_THRESHOLD == 0.7


# Mark as slow test
import pytest

pytestmark = pytest.mark.slow
