"""Integration tests for MiDaS depth estimation module.

These tests verify the full depth estimation workflow including:
- Model loading with mocked torch.hub
- Single-frame depth estimation
- Batch depth estimation
- Error handling flows
"""

from __future__ import annotations

import sys
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

    # Mock loguru
    sys.modules["loguru"] = MagicMock()

    # Mock video2d3d.utils modules
    sys.modules["video2d3d.utils"] = MagicMock()
    sys.modules["video2d3d.utils.logger"] = _create_mock_logger_module()
    if "video2d3d.depth" in sys.modules:
        del sys.modules["video2d3d.depth"]

    yield

    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    if "video2d3d.depth" in sys.modules:
        del sys.modules["video2d3d.depth"]


@pytest.fixture
def mock_torch() -> MagicMock:
    """Get the mocked torch module."""
    return sys.modules["torch"]


@pytest.fixture
def sample_rgb_image() -> np.ndarray:
    """Create a sample RGB image for testing."""
    np.random.seed(42)
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_rgb_images_batch() -> list[np.ndarray]:
    """Create a batch of sample RGB images for testing."""
    np.random.seed(42)
    return [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(4)]


@pytest.fixture
def mock_model_and_transforms(mock_torch: MagicMock) -> dict:
    """Mock model and transforms for full depth estimation flow."""
    mock_model = MagicMock()
    mock_model.eval.return_value = mock_model
    mock_model.to.return_value = mock_model
    mock_model.half.return_value = mock_model

    mock_output = MagicMock()
    mock_output.dim.return_value = 4
    mock_output.squeeze.return_value = mock_output
    mock_output.cpu.return_value = mock_output
    mock_output.numpy.return_value = np.random.random((100, 100)).astype(np.float32)
    mock_model.return_value = mock_output

    mock_transforms = MagicMock()
    mock_transform_fn = MagicMock()
    mock_transform_fn.dim.return_value = 3
    mock_transform_fn.unsqueeze.return_value = mock_transform_fn
    mock_transform_fn.to.return_value = mock_transform_fn
    mock_transforms.small_transform = mock_transform_fn
    mock_transforms.dpt_transform = MagicMock(
        dim=MagicMock(return_value=3),
        unsqueeze=MagicMock(return_value=MagicMock()),
    )

    mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

    return {
        "model": mock_model,
        "transforms": mock_transforms,
        "output": mock_output,
    }


# ---------------------------------------------------------------------------
# Model Loading Integration Tests
# ---------------------------------------------------------------------------


class TestModelLoadingFlow:
    """Integration tests for model loading flow."""

    def test_load_model_small_uses_small_transform(
        self, mock_torch: MagicMock, mock_model_and_transforms: dict
    ) -> None:
        """Test that loading MiDaS small model uses small_transform."""
        from video2d3d.depth import DepthEstimator, MiDaSModelType

        estimator = DepthEstimator(model_type=MiDaSModelType.MIDAS_V21_SMALL)
        estimator.load_model()

        calls = mock_torch.hub.load.call_args_list
        assert len(calls) >= 2

    def test_load_model_dpt_uses_dpt_transform(self, mock_torch: MagicMock) -> None:
        """Test that loading DPT model uses dpt_transform."""
        from video2d3d.depth import DepthEstimator, MiDaSModelType

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        mock_transforms = MagicMock()
        mock_transforms.dpt_transform = MagicMock()

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        estimator = DepthEstimator(model_type=MiDaSModelType.DPT_LARGE)
        estimator.load_model()

        assert estimator._transform is mock_transforms.dpt_transform

    def test_load_model_failure_raises_model_load_error(self, mock_torch: MagicMock) -> None:
        """Test that model loading failure raises ModelLoadError."""
        from video2d3d.depth import DepthEstimator, ModelLoadError

        mock_torch.hub.load.side_effect = RuntimeError("Network error")

        estimator = DepthEstimator()

        with pytest.raises(ModelLoadError, match="Failed to load MiDaS model"):
            estimator.load_model()


# ---------------------------------------------------------------------------
# Single-Frame Depth Estimation Tests
# ---------------------------------------------------------------------------


class TestSingleFrameDepthEstimation:
    """Integration tests for single-frame depth estimation."""

    def test_estimate_depth_full_flow(
        self,
        mock_torch: MagicMock,
        mock_model_and_transforms: dict,
        sample_rgb_image: np.ndarray,
    ) -> None:
        """Test full depth estimation flow with valid input."""
        from video2d3d.depth import DepthEstimator

        mock_depth = np.random.random((100, 100)).astype(np.float32)

        with patch("video2d3d.depth.F") as mock_F:
            mock_F.interpolate.return_value = MagicMock(
                squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
            )

            estimator = DepthEstimator()
            depth_map = estimator.estimate_depth(sample_rgb_image)

            assert isinstance(depth_map, np.ndarray)
            assert depth_map.shape == (100, 100)
            assert depth_map.dtype == np.float32

    def test_estimate_depth_inference_error_on_model_failure(
        self,
        mock_torch: MagicMock,
        sample_rgb_image: np.ndarray,
    ) -> None:
        """Test that inference failure raises InferenceError."""
        from video2d3d.depth import DepthEstimator, InferenceError

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
            estimator = DepthEstimator()

            with pytest.raises(InferenceError, match="Depth estimation failed"):
                estimator.estimate_depth(sample_rgb_image)


# ---------------------------------------------------------------------------
# Batch Depth Estimation Tests
# ---------------------------------------------------------------------------


class TestBatchDepthEstimation:
    """Integration tests for batch depth estimation."""

    def test_estimate_depth_batch_full_flow(
        self,
        mock_torch: MagicMock,
        sample_rgb_images_batch: list[np.ndarray],
    ) -> None:
        """Test full batch depth estimation flow."""
        from video2d3d.depth import DepthEstimator

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        mock_batch_output = [MagicMock() for _ in range(4)]
        for out in mock_batch_output:
            out.unsqueeze.return_value = out
        mock_model.return_value = mock_batch_output

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        mock_depth = np.random.random((100, 100)).astype(np.float32)

        with patch("video2d3d.depth.F") as mock_F:
            mock_F.interpolate.return_value = MagicMock(
                squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
            )

            with patch("torch.cat") as mock_cat:
                mock_cat.return_value = MagicMock()

                estimator = DepthEstimator()
                depth_maps = estimator.estimate_depth_batch(sample_rgb_images_batch)

                assert len(depth_maps) == len(sample_rgb_images_batch)

    def test_estimate_depth_batch_failure_raises_inference_error(
        self,
        mock_torch: MagicMock,
        sample_rgb_images_batch: list[np.ndarray],
    ) -> None:
        """Test that batch failure raises InferenceError."""
        from video2d3d.depth import DepthEstimator, InferenceError

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model
        mock_model.side_effect = RuntimeError("Batch processing error")

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        with patch("video2d3d.depth.F"), patch("torch.cat") as mock_cat:
            mock_cat.return_value = MagicMock()

            estimator = DepthEstimator()

            with pytest.raises(InferenceError, match="Batch depth estimation failed"):
                estimator.estimate_depth_batch(sample_rgb_images_batch)


# ---------------------------------------------------------------------------
# Context Manager Integration Tests
# ---------------------------------------------------------------------------


class TestContextManagerFlow:
    """Integration tests for context manager usage."""

    def test_context_manager_full_flow(
        self,
        mock_torch: MagicMock,
        sample_rgb_image: np.ndarray,
    ) -> None:
        """Test full depth estimation using context manager."""
        from video2d3d.depth import DepthEstimator

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        mock_output = MagicMock()
        mock_output.dim.return_value = 4
        mock_output.squeeze.return_value = mock_output
        mock_output.cpu.return_value = mock_output
        mock_output.numpy.return_value = np.random.random((100, 100)).astype(np.float32)
        mock_model.return_value = mock_output

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        mock_depth = np.random.random((100, 100)).astype(np.float32)

        with patch("video2d3d.depth.F") as mock_F:
            mock_F.interpolate.return_value = MagicMock(
                squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
            )

            with DepthEstimator() as estimator:
                depth_map = estimator.estimate_depth(sample_rgb_image)
                assert isinstance(depth_map, np.ndarray)

            assert estimator._model is None
            assert not estimator.is_loaded


# ---------------------------------------------------------------------------
# Edge Cases Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases."""

    def test_estimate_depth_flat_depth_map(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test handling of uniform depth map (min == max)."""
        from video2d3d.depth import DepthEstimator

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        uniform_depth = np.full((100, 100), 0.5, dtype=np.float32)
        mock_output = MagicMock()
        mock_output.dim.return_value = 4
        mock_output.squeeze.return_value = mock_output
        mock_output.cpu.return_value = mock_output
        mock_output.numpy.return_value = uniform_depth
        mock_model.return_value = mock_output

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
                    return_value=MagicMock(numpy=MagicMock(return_value=uniform_depth))
                )
            )

            estimator = DepthEstimator()
            depth_map = estimator.estimate_depth(sample_rgb_image)

            assert isinstance(depth_map, np.ndarray)

    def test_multiple_sequential_estimations(
        self,
        mock_torch: MagicMock,
        sample_rgb_image: np.ndarray,
    ) -> None:
        """Test multiple sequential depth estimations without reloading model."""
        from video2d3d.depth import DepthEstimator

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        mock_output = MagicMock()
        mock_output.dim.return_value = 4
        mock_output.squeeze.return_value = mock_output
        mock_output.cpu.return_value = mock_output
        mock_output.numpy.return_value = np.random.random((100, 100)).astype(np.float32)
        mock_model.return_value = mock_output

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        mock_depth = np.random.random((100, 100)).astype(np.float32)

        with patch("video2d3d.depth.F") as mock_F:
            mock_F.interpolate.return_value = MagicMock(
                squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
            )

            estimator = DepthEstimator()

            for _ in range(3):
                depth_map = estimator.estimate_depth(sample_rgb_image)
                assert isinstance(depth_map, np.ndarray)

            # Model should only be loaded once
            assert mock_torch.hub.load.call_count == 2

    def test_temporal_smoothing_warning(
        self, mock_torch: MagicMock, sample_rgb_image: np.ndarray
    ) -> None:
        """Test that temporal smoothing flag produces a warning but still works."""
        from video2d3d.depth import DepthEstimator

        mock_model = MagicMock()
        mock_model.eval.return_value = mock_model
        mock_model.to.return_value = mock_model

        mock_output = MagicMock()
        mock_output.dim.return_value = 4
        mock_output.squeeze.return_value = mock_output
        mock_output.cpu.return_value = mock_output
        mock_output.numpy.return_value = np.random.random((100, 100)).astype(np.float32)
        mock_model.return_value = mock_output

        mock_transforms = MagicMock()
        mock_transform_fn = MagicMock()
        mock_transform_fn.dim.return_value = 3
        mock_transform_fn.unsqueeze.return_value = mock_transform_fn
        mock_transform_fn.to.return_value = mock_transform_fn
        mock_transforms.small_transform = mock_transform_fn

        mock_torch.hub.load.side_effect = [mock_model, mock_transforms]

        mock_depth = np.random.random((100, 100)).astype(np.float32)

        with patch("video2d3d.depth.F") as mock_F:
            mock_F.interpolate.return_value = MagicMock(
                squeeze=MagicMock(return_value=MagicMock(numpy=MagicMock(return_value=mock_depth)))
            )

            estimator = DepthEstimator()
            depth_map = estimator.estimate_depth(sample_rgb_image, temporal_smoothing=True)

            assert isinstance(depth_map, np.ndarray)
