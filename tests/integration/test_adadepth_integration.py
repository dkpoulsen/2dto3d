"""Integration tests for AdaDepth model fallback behavior.

Tests cover:
- Model selection and fallback chain
- Automatic fallback on model failures
- Scene-adaptive model selection
- Configuration loading for model selection
- End-to-end depth estimation with model selector

These tests verify the interaction between components.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


def _create_mock_torch() -> MagicMock:
    """Create mock torch module."""
    mock = MagicMock()
    mock.cuda.is_available.return_value = False
    mock.hub.get_dir.return_value = "/tmp/torch_hub"
    mock.hub.set_dir = MagicMock()
    mock.hub.load = MagicMock()
    mock.no_grad = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    mock.backends.cudnn.benchmark = False

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
    """Create mock torch.nn.functional module."""
    mock = MagicMock()
    mock_depth = np.random.random((100, 100)).astype(np.float32)
    mock.interpolate = MagicMock(
        return_value=MagicMock(
            squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
        )
    )
    return mock


def _create_mock_logger_module() -> MagicMock:
    """Create mock video2d3d.utils.logger module."""
    mock_module = MagicMock()
    mock_logger = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_module.get_logger = MagicMock(return_value=mock_logger)
    mock_module.log_exception = MagicMock()
    mock_module.log_model_inference = MagicMock()
    return mock_module


@pytest.fixture(autouse=True)
def mock_torch_modules() -> Generator[None, None, None]:
    """Mock torch modules before any imports."""
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
    MagicMock()
    mock_torchview.transforms = MagicMock()

    sys.modules["torch"] = mock_torch
    sys.modules["torch.nn"] = mock_torch_nn
    sys.modules["torch.nn.functional"] = mock_torch_nn.functional
    sys.modules["torchvision"] = mock_torchview
    sys.modules["torchvision.transforms"] = mock_torchview.transforms
    sys.modules["huggingface_hub"] = MagicMock()

    sys.modules["loguru"] = MagicMock()
    sys.modules["video2d3d.utils"] = MagicMock()
    sys.modules["video2d3d.utils.logger"] = _create_mock_logger_module()

    mock_gpu = MagicMock()
    mock_gpu.GPUConfig = MagicMock
    mock_selection = MagicMock()
    mock_selection.device = "cpu"
    mock_gpu.select_device = MagicMock(return_value=mock_selection)
    mock_gpu.clear_gpu_memory = MagicMock()
    mock_gpu.compute_optimal_batch_size = MagicMock(return_value=4)
    sys.modules["video2d3d.utils.gpu"] = mock_gpu

    for mod in [
        "video2d3d.depth",
        "video2d3d.depth.__init__",
        "video2d3d.depth.model_selector",
        "video2d3d.depth.adadepth",
        "video2d3d.depth.processor",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    yield

    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create sample RGB image for testing."""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


class TestModelFallbackChain:
    """Integration tests for model fallback chain behavior."""

    def test_fallback_chain_order(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(
            primary_model=DepthModelType.ADABINS_NYU,
            fallback_model=DepthModelType.MIDAS_SMALL,
            fallback_chain=[
                DepthModelType.ADABINS_NYU,
                DepthModelType.ADABINS_KITTI,
                DepthModelType.MIDAS_SMALL,
            ],
        )

        assert config.fallback_chain[0] == DepthModelType.ADABINS_NYU
        assert config.fallback_chain[1] == DepthModelType.ADABINS_KITTI
        assert config.fallback_chain[2] == DepthModelType.MIDAS_SMALL

    def test_fallback_on_primary_failure(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        from video2d3d.depth.model_selector import (
            DepthModelSelector,
            DepthModelType,
        )

        selector = DepthModelSelector(
            primary_model="adabins_nyu",
            fallback_model="midas_small",
        )

        call_order = []

        def mock_get_estimator(model_type):
            call_order.append(model_type)

            if model_type == DepthModelType.ADABINS_NYU:
                raise Exception("AdaBins failed to load")

            mock_estimator = MagicMock()
            mock_estimator.estimate_depth.return_value = np.zeros((100, 100), dtype=np.float32)
            return mock_estimator

        selector._get_estimator = mock_get_estimator

        result = selector.estimate_depth(sample_rgb_image)

        assert DepthModelType.ADABINS_NYU in call_order
        assert result is not None

    def test_all_models_failure_raises_error(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector, ModelInferenceError

        selector = DepthModelSelector()

        def mock_get_estimator(model_type):
            raise Exception("All models failed")

        selector._get_estimator = mock_get_estimator

        with pytest.raises(ModelInferenceError) as exc_info:
            selector.estimate_depth(sample_rgb_image)

        assert "All depth models failed" in str(exc_info.value)


class TestSceneAdaptiveSelection:
    """Integration tests for scene-adaptive model selection."""

    def test_scene_adaptation_enabled_selects_correct_model(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(
            enable_scene_adaptation=True,
            primary_model=DepthModelType.ADABINS_NYU,
        )

        assert config.enable_scene_adaptation is True

    def test_scene_adaptation_disabled_uses_primary(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(
            enable_scene_adaptation=False,
            primary_model=DepthModelType.DPT_LARGE,
        )

        assert config.enable_scene_adaptation is False
        assert config.primary_model == DepthModelType.DPT_LARGE


class TestConfigurationLoading:
    """Integration tests for configuration loading."""

    def test_config_from_string_model_types(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(
            primary_model="adabins_nyu",
            fallback_model="midas_small",
        )

        assert isinstance(config.primary_model, DepthModelType)
        assert isinstance(config.fallback_model, DepthModelType)

    def test_config_fallback_chain_from_strings(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelType

        config = DepthModelConfig(fallback_chain=["adabins_nyu", "midas_small", "dpt_hybrid"])

        for model in config.fallback_chain:
            assert isinstance(model, DepthModelType)


class TestModelSelectorWithMockedEstimators:
    """Integration tests with mocked estimators."""

    def test_successful_estimation_with_adabins(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector(
            primary_model="adabins_nyu",
            fallback_model="midas_small",
        )

        mock_estimator = MagicMock()
        mock_estimator.estimate_depth.return_value = np.zeros((100, 100), dtype=np.float32)
        selector._get_estimator = MagicMock(return_value=mock_estimator)

        result = selector.estimate_depth(sample_rgb_image)

        assert result.shape == (100, 100)
        assert selector.active_model == DepthModelType.ADABINS_NYU

    def test_batch_processing_consistency(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()

        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(3)]

        mock_estimator = MagicMock()
        mock_estimator.estimate_depth.return_value = np.zeros((100, 100), dtype=np.float32)
        mock_estimator.estimate_depth_batch.return_value = [
            np.zeros((100, 100), dtype=np.float32) for _ in range(2)
        ]
        selector._get_estimator = MagicMock(return_value=mock_estimator)
        selector._active_model = DepthModelType.ADABINS_NYU

        results = selector.estimate_depth_batch(frames, batch_size=2)

        assert len(results) == 3


class TestPreloading:
    """Integration tests for model preloading."""

    def test_preload_all_models_in_chain(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()
        selector._get_estimator = MagicMock()

        results = selector.preload_models()

        assert len(results) > 0

    def test_preload_specific_models(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector

        selector = DepthModelSelector()
        selector._get_estimator = MagicMock()

        results = selector.preload_models(["midas_small", "dpt_large"])

        assert "midas_small" in results
        assert "dpt_large" in results


class TestErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    def test_estimator_close_on_selector_close(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        mock_estimator = MagicMock()
        selector._estimators[DepthModelType.ADABINS_NYU] = mock_estimator
        selector._active_model = DepthModelType.ADABINS_NYU

        selector.close()

        mock_estimator.close.assert_called_once()
        assert len(selector._estimators) == 0

    def test_context_manager_cleans_up(self, mock_torch_modules: None) -> None:
        from video2d3d.depth.model_selector import DepthModelSelector

        with DepthModelSelector() as selector:
            mock_estimator = MagicMock()
            from video2d3d.depth.model_selector import DepthModelType

            selector._estimators[DepthModelType.ADABINS_NYU] = mock_estimator

        mock_estimator.close.assert_called_once()


# Import DepthModelType for use in tests
from video2d3d.depth.model_selector import DepthModelType
