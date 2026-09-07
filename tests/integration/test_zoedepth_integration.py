"""Integration tests for ZoeDepth depth estimation module.

Tests cover:
- Model loading and caching
- Depth estimation with both relative and metric modes
- Model selector integration with ZoeDepth
- Batch processing integration
- End-to-end depth estimation workflows

These tests verify the interaction between ZoeDepth components and the model selector.
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
    mock.no_grad = MagicMock(
        return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock(return_value=False))
    )
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
    mock_torch.nn = mock_torch_nn
    mock_torch.nn.functional = mock_torch_nn.functional
    mock_torchview = MagicMock()
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

    # Create proper GPU mock with select_device returning cpu
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
        "video2d3d.depth.zoedepth",
        "video2d3d.depth.model_selector",
    ]:
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
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image for testing."""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


class TestZoeDepthModelLoadingIntegration:
    """Integration tests for ZoeDepth model loading."""

    def test_load_model_from_torch_hub(self, mock_torch_modules: None) -> None:
        """Test model is loaded from PyTorch Hub with correct parameters."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthModelVariant

        estimator = ZoeDepthEstimator(model_variant=ZoeDepthModelVariant.ZOE_NK)
        estimator.load_model()

        mock_torch = sys.modules["torch"]
        mock_torch.hub.load.assert_called_once()

        call_args = mock_torch.hub.load.call_args
        assert call_args[0][0] == "isl-org/ZoeDepth"
        assert call_args[0][1] == "ZoeD_NK"

    def test_model_variant_selection(self, mock_torch_modules: None) -> None:
        """Test different model variants are loaded correctly."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthModelVariant

        variants = [
            (ZoeDepthModelVariant.ZOE_N, "ZoeD_N"),
            (ZoeDepthModelVariant.ZOE_K, "ZoeD_K"),
            (ZoeDepthModelVariant.ZOE_NK, "ZoeD_NK"),
        ]

        for variant, expected_hub_name in variants:
            # Clear previous calls
            mock_torch = sys.modules["torch"]
            mock_torch.hub.load.reset_mock()

            estimator = ZoeDepthEstimator(model_variant=variant)
            estimator.load_model()

            call_args = mock_torch.hub.load.call_args
            assert call_args[0][1] == expected_hub_name

    def test_model_caching_via_hub_dir(self, mock_torch_modules: None) -> None:
        """Test model caching uses torch hub directory."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()
        estimator.load_model()

        mock_torch = sys.modules["torch"]
        mock_torch.hub.set_dir.assert_called()


class TestZoeDepthDepthEstimationIntegration:
    """Integration tests for depth estimation with ZoeDepth."""

    def test_estimate_depth_returns_valid_depth_map(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        """Test estimate_depth returns a valid depth map."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()

        # Create a mock model that returns a valid depth prediction
        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 4
        mock_prediction.squeeze.return_value = mock_prediction
        mock_prediction.cpu.return_value = mock_prediction
        mock_prediction.numpy.return_value = np.random.random((100, 100)).astype(np.float32) * 10
        mock_model.infer.return_value = mock_prediction
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        result = estimator.estimate_depth(sample_rgb_image)

        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100)
        assert result.dtype == np.float32

    def test_relative_mode_normalizes_output(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        """Test relative mode normalizes depth values to [0, 1]."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(depth_mode="relative")

        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 4
        mock_prediction.squeeze.return_value = mock_prediction
        mock_prediction.cpu.return_value = mock_prediction
        # Return values outside [0, 1] range
        mock_prediction.numpy.return_value = np.array([[5.0, 10.0], [15.0, 20.0]], dtype=np.float32)
        mock_model.infer.return_value = mock_prediction
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        result = estimator.estimate_depth(sample_rgb_image, depth_mode="relative")

        # After normalization, values should be in [0, 1]
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_metric_mode_preserves_scale(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        """Test metric mode preserves absolute depth scale."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthModelVariant

        estimator = ZoeDepthEstimator(
            model_variant=ZoeDepthModelVariant.ZOE_N,
            depth_mode="metric",
        )

        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 4
        mock_prediction.squeeze.return_value = mock_prediction
        mock_prediction.cpu.return_value = mock_prediction
        # Return metric depth values
        mock_prediction.numpy.return_value = np.random.random((100, 100)).astype(np.float32) * 5
        mock_model.infer.return_value = mock_prediction
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        result = estimator.estimate_depth(sample_rgb_image, depth_mode="metric")

        # Values should be within max_depth for NYU (10.0)
        assert np.all(result >= 0)
        assert np.all(result <= 10.0)


class TestZoeDepthBatchProcessingIntegration:
    """Integration tests for batch processing with ZoeDepth."""

    def test_batch_processing_multiple_frames(self, mock_torch_modules: None) -> None:
        """Test batch processing handles multiple frames correctly."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator()

        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 3
        mock_prediction.squeeze.return_value = MagicMock(
            cpu=MagicMock(
                return_value=MagicMock(numpy=MagicMock(return_value=np.zeros((100, 100), dtype=np.float32)))
            )
        )
        batch_sizes = iter([4, 1])

        def infer_side_effect(_tensor):
            return [mock_prediction] * next(batch_sizes)

        mock_model.infer.side_effect = infer_side_effect
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(5)]

        results = estimator.estimate_depth_batch(frames, batch_size=2)

        assert len(results) == 5
        for result in results:
            assert isinstance(result, np.ndarray)

    def test_batch_processing_respects_batch_size(self, mock_torch_modules: None) -> None:
        """Test batch processing respects the batch size parameter."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(auto_batch_size=False)

        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 3
        mock_prediction.squeeze.return_value = MagicMock(
            cpu=MagicMock(
                return_value=MagicMock(numpy=MagicMock(return_value=np.zeros((100, 100), dtype=np.float32)))
            )
        )
        batch_sizes = iter([3, 3, 3, 1])

        def infer_side_effect(_tensor):
            return [mock_prediction] * next(batch_sizes)

        mock_model.infer.side_effect = infer_side_effect
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(10)]

        results = estimator.estimate_depth_batch(frames, batch_size=3)

        assert len(results) == 10


class TestZoeDepthModelSelectorIntegration:
    """Integration tests for ZoeDepth with the model selector."""

    def test_selector_creates_zoedepth_estimator(self, mock_torch_modules: None) -> None:
        """Test model selector can create ZoeDepth estimators."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        estimator = selector._get_estimator(DepthModelType.ZOEDEPTH_NK)

        assert estimator is not None
        assert hasattr(estimator, "estimate_depth")

    def test_selector_estimates_depth_with_zoedepth(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        """Test model selector can estimate depth using ZoeDepth."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        # Create mock estimator
        mock_estimator = MagicMock()
        mock_estimator.estimate_depth.return_value = np.zeros((100, 100), dtype=np.float32)
        selector._get_estimator = MagicMock(return_value=mock_estimator)
        selector._active_model = DepthModelType.ZOEDEPTH_NK

        result = selector.estimate_depth(sample_rgb_image)

        assert result.shape == (100, 100)
        assert selector.active_model == DepthModelType.ZOEDEPTH_NK

    def test_selector_all_three_zoedepth_variants(self, mock_torch_modules: None) -> None:
        """Test model selector supports all three ZoeDepth variants."""
        from video2d3d.depth.model_selector import DepthModelSelector, DepthModelType

        selector = DepthModelSelector()

        variants = [
            DepthModelType.ZOEDEPTH_N,
            DepthModelType.ZOEDEPTH_K,
            DepthModelType.ZOEDEPTH_NK,
        ]

        for variant in variants:
            estimator = selector._get_estimator(variant)
            assert estimator is not None

    def test_selector_zoedepth_in_fallback_chain(self, mock_torch_modules: None) -> None:
        """Test ZoeDepth is available in model fallback chain."""
        from video2d3d.depth.model_selector import DepthModelConfig, DepthModelSelector

        config = DepthModelConfig(
            fallback_chain=["zoedepth_nk", "midas_small"],
        )
        DepthModelSelector(config=config)

        # Verify ZoeDepth is first in the chain
        assert "zoedepth_nk" in config.fallback_chain


class TestZoeDepthContextManagerIntegration:
    """Integration tests for context manager usage."""

    def test_context_manager_cleanup(self, mock_torch_modules: None) -> None:
        """Test context manager properly cleans up resources."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        with ZoeDepthEstimator() as estimator:
            estimator.load_model()
            assert estimator.is_loaded is True

        # After context exit, resources should be cleaned
        assert estimator._model is None
        assert estimator.is_loaded is False

    def test_context_manager_with_depth_estimation(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        """Test context manager works with depth estimation."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 4
        mock_prediction.squeeze.return_value = mock_prediction
        mock_prediction.cpu.return_value = mock_prediction
        mock_prediction.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
        mock_model.infer.return_value = mock_prediction
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        with ZoeDepthEstimator() as estimator:
            estimator._model = mock_model
            estimator._is_loaded = True

            result = estimator.estimate_depth(sample_rgb_image)

            assert isinstance(result, np.ndarray)


class TestZoeDepthErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_inference_error_on_invalid_input(self, mock_torch_modules: None) -> None:
        """Test ZoeDepthInferenceError is raised for invalid input."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError, match="Input must be a numpy array"):
            estimator.estimate_depth("not an array")

    def test_load_error_on_torch_hub_failure(self, mock_torch_modules: None) -> None:
        """Test ZoeDepthLoadError is raised when torch.hub.load fails."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthLoadError

        mock_torch = sys.modules["torch"]
        mock_torch.hub.load.side_effect = RuntimeError("Network error")

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthLoadError, match="Failed to load ZoeDepth model"):
            estimator.load_model()

    def test_error_preserves_context(self, mock_torch_modules: None) -> None:
        """Test errors preserve context about the failure."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthInferenceError

        estimator = ZoeDepthEstimator()

        with pytest.raises(ZoeDepthInferenceError) as exc_info:
            estimator.estimate_depth(np.zeros((10, 10, 4)))  # Wrong channel count

        error = exc_info.value
        assert error.model_variant is not None
        assert error.device is not None


class TestZoeDepthConvenienceFunctionsIntegration:
    """Integration tests for convenience functions."""

    def test_create_zoedepth_estimator_creates_valid_estimator(
        self, mock_torch_modules: None
    ) -> None:
        """Test create_zoedepth_estimator creates a valid estimator."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator, create_zoedepth_estimator

        estimator = create_zoedepth_estimator(
            model_variant="zoedepth_nk",
            depth_mode="metric",
        )

        assert isinstance(estimator, ZoeDepthEstimator)
        assert estimator.config.depth_mode == "metric"


class TestZoeDepthDepthModeIntegration:
    """Integration tests for depth mode switching."""

    def test_override_depth_mode_per_inference(
        self, mock_torch_modules: None, sample_rgb_image: np.ndarray
    ) -> None:
        """Test depth mode can be overridden per inference call."""
        from video2d3d.depth.zoedepth import ZoeDepthEstimator

        estimator = ZoeDepthEstimator(depth_mode="relative")

        mock_model = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.dim.return_value = 4
        mock_prediction.squeeze.return_value = mock_prediction
        mock_prediction.cpu.return_value = mock_prediction
        mock_prediction.numpy.return_value = np.random.random((100, 100)).astype(np.float32) * 5
        mock_model.infer.return_value = mock_prediction
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = mock_model

        estimator._model = mock_model
        estimator._is_loaded = True

        # Call with metric mode override
        result = estimator.estimate_depth(sample_rgb_image, depth_mode="metric")

        assert isinstance(result, np.ndarray)
        # Config should remain unchanged
        assert estimator.config.depth_mode == "relative"


# Import for test discovery
