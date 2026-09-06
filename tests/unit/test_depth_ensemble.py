"""Unit tests for ensemble depth prediction feature.

Tests cover:
- EnsembleMethod enum
- WeightStrategy enum
- EnsembleConfig dataclass
- EnsembleError exception
- EnsemblePredictor class
- Combination methods
- Convenience functions

Note: These tests mock torch before importing the depth module.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

if TYPE_CHECKING:
    pass


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
    mock.ones = MagicMock(return_value=mock_tensor)

    # Add nn module
    mock.nn = MagicMock()
    mock.nn.Module = MagicMock

    # Add functional
    mock.functional = MagicMock()
    mock.functional.interpolate = MagicMock(return_value=mock_tensor)
    mock.F = mock.functional

    return mock


def _create_mock_torchvision() -> MagicMock:
    """Create a mock torchvision module."""
    mock = MagicMock()
    mock.transforms = MagicMock()
    mock.transforms.Compose = MagicMock
    mock.transforms.ToPILImage = MagicMock
    mock.transforms.Resize = MagicMock
    mock.transforms.ToTensor = MagicMock
    mock.transforms.Normalize = MagicMock
    return mock


def _create_mock_scipy() -> MagicMock:
    """Create a mock scipy module."""
    mock = MagicMock()

    # Mock ndimage
    mock.ndimage = MagicMock()
    mock.ndimage.laplace = MagicMock(return_value=np.zeros((10, 10)))
    mock.ndimage.zoom = MagicMock(return_value=np.zeros((10, 10)))

    # Mock interpolate
    mock.interpolate = MagicMock()
    mock.interpolate.CubicSpline = MagicMock
    mock.interpolate.interp1d = MagicMock

    # Mock signal
    mock.signal = MagicMock()

    return mock


# Mock torch, torchvision, and scipy before importing the module
_original_modules = {
    mod: sys.modules[mod]
    for mod in [
        "torch",
        "torch.nn",
        "torch.nn.functional",
        "torchvision",
        "torchvision.transforms",
        "scipy",
        "scipy.ndimage",
        "scipy.interpolate",
        "scipy.signal",
    ]
    if mod in sys.modules
}
sys.modules["torch"] = _create_mock_torch()
sys.modules["torch.nn"] = sys.modules["torch"].nn
sys.modules["torch.nn.functional"] = sys.modules["torch"].functional
sys.modules["torchvision"] = _create_mock_torchvision()
sys.modules["torchvision.transforms"] = sys.modules["torchvision"].transforms
_scipy_mock = _create_mock_scipy()
sys.modules["scipy"] = _scipy_mock
sys.modules["scipy.ndimage"] = _scipy_mock.ndimage
sys.modules["scipy.interpolate"] = _scipy_mock.interpolate
sys.modules["scipy.signal"] = _scipy_mock.signal
# Now import the module under test
from video2d3d.depth.ensemble import (
    _DEFAULT_WEIGHTS,
    EnsembleConfig,
    EnsembleError,
    EnsembleMethod,
    EnsemblePredictor,
    WeightStrategy,
    _normalize_weights_list,
    create_ensemble_predictor,
    estimate_depth_ensemble,
)

# Restore the real modules so other test files in this worker are unaffected
for _mod, _val in _original_modules.items():
    sys.modules[_mod] = _val
for _mod in [
    "torch",
    "torch.nn",
    "torch.nn.functional",
    "torchvision",
    "torchvision.transforms",
    "scipy",
    "scipy.ndimage",
    "scipy.interpolate",
    "scipy.signal",
]:
    if _mod in sys.modules and _mod not in _original_modules:
        del sys.modules[_mod]
import scipy  # noqa: F401 - ensure real scipy importable after restore


class TestEnsembleMethod:
    """Tests for EnsembleMethod enum."""

    def test_values(self):
        assert EnsembleMethod.WEIGHTED_AVERAGE.value == "weighted_average"
        assert EnsembleMethod.AVERAGE.value == "average"
        assert EnsembleMethod.MEDIAN.value == "median"
        assert EnsembleMethod.MAX.value == "max"
        assert EnsembleMethod.MIN.value == "min"
        assert EnsembleMethod.VOTING.value == "voting"


class TestWeightStrategy:
    """Tests for WeightStrategy enum."""

    def test_values(self):
        assert WeightStrategy.UNIFORM.value == "uniform"
        assert WeightStrategy.PREDEFINED.value == "predefined"
        assert WeightStrategy.PERFORMANCE.value == "performance"
        assert WeightStrategy.UNCERTAINTY.value == "uncertainty"


class TestEnsembleConfig:
    """Tests for EnsembleConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = EnsembleConfig()

        assert config.method == EnsembleMethod.WEIGHTED_AVERAGE
        assert config.auto_weight is True
        assert config.weight_strategy == WeightStrategy.PREDEFINED
        assert config.normalize_weights is True
        assert config.fallback_on_error is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            method=EnsembleMethod.MEDIAN,
            weights=[0.6, 0.4],
            normalize_weights=False,
            fallback_on_error=False,
        )

        assert config.models == ["model_a", "model_b"]
        assert config.method == EnsembleMethod.MEDIAN
        assert config.weights == [0.6, 0.4]
        assert config.normalize_weights is False
        assert config.fallback_on_error is False

    def test_invalid_config_empty_models(self):
        """Test invalid configuration with empty models."""
        with pytest.raises(ValueError):
            EnsembleConfig(models=[])

    def test_invalid_config_wrong_weights_count(self):
        """Test invalid configuration with wrong weights count."""
        with pytest.raises(ValueError):
            EnsembleConfig(
                models=["model_a"],
                weights=[0.5, 0.5],
            )

    def test_invalid_config_negative_weights(self):
        """Test invalid configuration with negative weights."""
        with pytest.raises(ValueError):
            EnsembleConfig(
                models=["model_a"],
                weights=[-0.1],
            )

    def test_weight_normalization(self):
        """Test weight normalization."""
        config = EnsembleConfig(
            models=["model_a", "model_b", "model_c"],
            weights=[1.0, 2.0, 7.0],
        )

        # Check that weights are normalized
        assert abs(config.weights[0] - 0.1) < 0.01
        assert abs(config.weights[1] - 0.2) < 0.01
        assert abs(config.weights[2] - 0.7) < 0.01

    def test_min_agreement_capping(self):
        """Test min_agreement is capped at number of models."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            min_agreement=3,
        )
        assert config.min_agreement == 2


class TestNormalizeWeightsList:
    """Tests for _normalize_weights_list helper function."""

    def test_normalize_weights_basic(self):
        """Test basic weight normalization."""
        weights = [1.0, 2.0, 7.0]
        result = _normalize_weights_list(weights)

        assert abs(result[0] - 0.1) < 0.01
        assert abs(result[1] - 0.2) < 0.01
        assert abs(result[2] - 0.7) < 0.01
        assert abs(sum(result) - 1.0) < 0.01

    def test_normalize_weights_already_normalized(self):
        """Test weights that already sum to 1."""
        weights = [0.25, 0.25, 0.5]
        result = _normalize_weights_list(weights)

        assert result[0] == 0.25
        assert result[1] == 0.25
        assert result[2] == 0.5

    def test_normalize_weights_zero_sum(self):
        """Test that zero sum raises ValueError."""
        with pytest.raises(ValueError):
            _normalize_weights_list([0.0, 0.0, 0.0])

    def test_normalize_weights_negative_sum(self):
        """Test that negative sum raises ValueError."""
        with pytest.raises(ValueError):
            _normalize_weights_list([-1.0, -1.0, -1.0])


class TestCombinationMethods:
    """Tests for combination methods."""

    def test_combine_weighted_average(self):
        """Test weighted average combination."""
        config = EnsembleConfig(models=["a", "b"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [0.3, 0.7]
        predictor._logger = MagicMock()

        pred_a = np.ones((10, 10), dtype=np.float32) * 0.3
        pred_b = np.ones((10, 10), dtype=np.float32) * 0.7

        result = predictor._combine_weighted_average([pred_a, pred_b], [0.3, 0.7])

        # Expected: 0.3 * 0.3 + 0.7 * 0.7 = 0.58
        expected = 0.3 * 0.3 + 0.7 * 0.7
        assert np.allclose(result, np.ones((10, 10)) * expected)

    def test_combine_average(self):
        """Test simple average combination."""
        config = EnsembleConfig(models=["a", "b"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [0.5, 0.5]
        predictor._logger = MagicMock()

        pred_a = np.ones((10, 10), dtype=np.float32) * 0.2
        pred_b = np.ones((10, 10), dtype=np.float32) * 0.8

        result = predictor._combine_average([pred_a, pred_b])

        expected = (0.2 + 0.8) / 2
        assert np.allclose(result, np.ones((10, 10)) * expected)

    def test_combine_median(self):
        """Test median combination."""
        config = EnsembleConfig(models=["a", "b", "c"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [1 / 3, 1 / 3, 1 / 3]
        predictor._logger = MagicMock()

        pred_a = np.ones((10, 10), dtype=np.float32) * 0.1
        pred_b = np.ones((10, 10), dtype=np.float32) * 0.5
        pred_c = np.ones((10, 10), dtype=np.float32) * 0.9

        result = predictor._combine_median([pred_a, pred_b, pred_c])

        # Median of [0.1, 0.5, 0.9] is 0.5
        assert np.allclose(result, np.ones((10, 10)) * 0.5)

    def test_combine_max(self):
        """Test max combination."""
        config = EnsembleConfig(models=["a", "b"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [0.5, 0.5]
        predictor._logger = MagicMock()

        pred_a = np.ones((10, 10), dtype=np.float32) * 0.3
        pred_b = np.ones((10, 10), dtype=np.float32) * 0.7

        result = predictor._combine_max([pred_a, pred_b])

        assert np.allclose(result, np.ones((10, 10)) * 0.7)

    def test_combine_min(self):
        """Test min combination."""
        config = EnsembleConfig(models=["a", "b"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [0.5, 0.5]
        predictor._logger = MagicMock()

        pred_a = np.ones((10, 10), dtype=np.float32) * 0.3
        pred_b = np.ones((10, 10), dtype=np.float32) * 0.7

        result = predictor._combine_min([pred_a, pred_b])

        assert np.allclose(result, np.ones((10, 10)) * 0.3)


class TestReprMethod:
    """Tests for __repr__ method."""

    def test_repr_basic(self):
        """Test __repr__ returns correct string."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            method=EnsembleMethod.WEIGHTED_AVERAGE,
            device="cpu",
        )
        predictor = EnsemblePredictor(config=config)

        result = repr(predictor)

        assert "EnsemblePredictor" in result
        assert "model_a" in result
        assert "model_b" in result
        assert "weighted_average" in result
        assert "cpu" in result


class TestInputValidation:
    """Tests for input validation."""

    def test_invalid_input_type(self):
        """Test invalid input type."""
        config = EnsembleConfig(models=["model_a"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [1.0]
        predictor._logger = MagicMock()

        with pytest.raises(EnsembleError):
            predictor.estimate_depth("not an array")

    def test_wrong_dimensions(self):
        """Test wrong dimensions (2D instead of 3D)."""
        config = EnsembleConfig(models=["model_a"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [1.0]
        predictor._logger = MagicMock()

        with pytest.raises(EnsembleError):
            predictor.estimate_depth(np.zeros((100, 100)))

    def test_wrong_channels(self):
        """Test wrong number of channels."""
        config = EnsembleConfig(models=["model_a"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [1.0]
        predictor._logger = MagicMock()

        with pytest.raises(EnsembleError):
            predictor.estimate_depth(np.zeros((100, 100, 4)))


class TestModelWeights:
    """Tests for model weight management."""

    def test_get_model_weights(self):
        """Test getting model weights."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            weights=[0.4, 0.6],
        )
        predictor = EnsemblePredictor(config=config)

        weights = predictor.get_model_weights()
        assert isinstance(weights, dict)
        assert "model_a" in weights
        assert "model_b" in weights

    def test_set_model_weights(self):
        """Test setting model weights."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            weights=[0.5, 0.5],
        )
        predictor = EnsemblePredictor(config=config)

        predictor.set_model_weights({"model_a": 0.8, "model_b": 0.2})

        weights = predictor.get_model_weights()
        assert weights["model_a"] == 0.8
        assert weights["model_b"] == 0.2

    def test_set_model_weights_negative_raises(self):
        """Test that setting negative weights raises ValueError."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            weights=[0.5, 0.5],
        )
        predictor = EnsemblePredictor(config=config)

        with pytest.raises(ValueError, match="must be non-negative"):
            predictor.set_model_weights({"model_a": -0.5, "model_b": 0.5})


class TestPerformanceTracking:
    """Tests for performance tracking."""

    def test_update_performance(self):
        """Test performance tracking for adaptive weights."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            weight_strategy=WeightStrategy.PERFORMANCE,
            device="cpu",
        )

        predictor = EnsemblePredictor(config=config)

        # Update performance
        predictor.update_performance("model_a", 0.8)
        predictor.update_performance("model_b", 0.6)

        # Check history
        assert predictor._performance_history["model_a"] == [0.8]
        assert predictor._performance_history["model_b"] == [0.6]

    def test_update_performance_invalid_model_raises(self):
        """Test that updating performance for unknown model raises ValueError."""
        config = EnsembleConfig(
            models=["model_a", "model_b"],
            weight_strategy=WeightStrategy.PERFORMANCE,
            device="cpu",
        )

        predictor = EnsemblePredictor(config=config)

        with pytest.raises(ValueError, match="not in ensemble"):
            predictor.update_performance("unknown_model", 0.8)


class TestEnsembleError:
    """Tests for EnsembleError exception."""

    def test_error_creation(self):
        """Test creating EnsembleError."""
        error = EnsembleError(
            "Test error",
            failed_models=["model_a"],
            successful_models=["model_b"],
        )

        assert str(error) == "Test error"
        assert error.failed_models == ["model_a"]
        assert error.successful_models == ["model_b"]

    def test_error_str_with_failed_models(self):
        """Test EnsembleError __str__ includes failed models."""
        error = EnsembleError(
            "Test error",
            failed_models=["model_a", "model_b"],
        )

        result = str(error)
        assert "Test error" in result
        assert "failed" in result.lower()


class TestAutoWeights:
    """Tests for automatic weight computation."""

    def test_uniform_weights(self):
        """Test uniform weight strategy."""
        config = EnsembleConfig(
            models=["model_a", "model_b", "model_c"],
            weight_strategy=WeightStrategy.UNIFORM,
            device="cpu",
        )
        predictor = EnsemblePredictor(config=config)

        weights = predictor._compute_auto_weights()

        assert len(weights) == 3
        assert abs(sum(weights) - 1.0) < 0.01
        assert abs(weights[0] - weights[1]) < 0.01

    def test_predefined_weights(self):
        """Test predefined weight strategy."""
        config = EnsembleConfig(
            models=["midas_small", "adabins_nyu"],
            weight_strategy=WeightStrategy.PREDEFINED,
            device="cpu",
        )
        predictor = EnsemblePredictor(config=config)

        weights = predictor._compute_auto_weights()

        assert len(weights) == 2
        assert abs(sum(weights) - 1.0) < 0.01


class TestCallableInterface:
    """Tests for callable interface."""

    def test_callable(self):
        """Test __call__ method."""
        config = EnsembleConfig(models=["model_a"], device="cpu")
        predictor = EnsemblePredictor.__new__(EnsemblePredictor)
        predictor._estimators = {}
        predictor._weights = [1.0]
        predictor._logger = MagicMock()

        call_count = [0]

        def mock_estimate(frame):
            call_count[0] += 1
            return np.zeros((100, 100), dtype=np.float32)

        predictor.estimate_depth = mock_estimate

        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = predictor(frame)

        assert isinstance(result, np.ndarray)
        assert call_count[0] == 1


class TestContextManager:
    """Tests for context manager."""

    def test_context_manager(self):
        """Test __enter__ and __exit__ methods."""
        config = EnsembleConfig(models=["model_a"], device="cpu")
        predictor = EnsemblePredictor(config=config)

        close_called = [False]

        def mock_close():
            close_called[0] = True

        predictor.close = mock_close

        with predictor as p:
            assert p is predictor

        assert close_called[0]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_ensemble_predictor_exists(self):
        """Test create_ensemble_predictor function exists."""

        assert callable(create_ensemble_predictor)

    def test_estimate_depth_ensemble_exists(self):
        """Test estimate_depth_ensemble function exists."""

        assert callable(estimate_depth_ensemble)


class TestNormalizeWeightsMethod:
    """Tests for _normalize_weights method."""

    def test_normalize_weights_basic(self):
        """Test _normalize_weights method."""
        config = EnsembleConfig(models=["a", "b"], device="cpu")
        predictor = EnsemblePredictor(config=config)

        result = predictor._normalize_weights([1.0, 3.0])

        assert abs(result[0] - 0.25) < 0.01
        assert abs(result[1] - 0.75) < 0.01

    def test_normalize_weights_zero_sum_returns_uniform(self):
        """Test _normalize_weights returns uniform when sum is zero."""
        config = EnsembleConfig(models=["a", "b"], device="cpu")
        predictor = EnsemblePredictor(config=config)

        result = predictor._normalize_weights([0.0, 0.0])

        assert result[0] == 0.5
        assert result[1] == 0.5


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_predefined_weights(self):
        """Test _get_predefined_weights method."""
        config = EnsembleConfig(
            models=["midas_small", "adabins_nyu"],
            device="cpu",
        )
        predictor = EnsemblePredictor(config=config)

        result = predictor._get_predefined_weights()

        assert len(result) == 2
        assert result[0] == _DEFAULT_WEIGHTS["midas_small"]
        assert result[1] == _DEFAULT_WEIGHTS["adabins_nyu"]

    def test_get_predefined_weights_unknown_model(self):
        """Test _get_predefined_weights with unknown model uses default."""
        config = EnsembleConfig(models=["unknown_model"], device="cpu")
        predictor = EnsemblePredictor(config=config)

        result = predictor._get_predefined_weights()

        # Should use default weight
        assert len(result) == 1
        assert result[0] > 0

    def test_get_performance_weights_no_history(self):
        """Test _get_performance_weights with no history."""
        config = EnsembleConfig(models=["model_a"], device="cpu")
        predictor = EnsemblePredictor(config=config)

        result = predictor._get_performance_weights()

        assert len(result) == 1
        assert result[0] > 0

    def test_get_performance_weights_with_history(self):
        """Test _get_performance_weights with history."""
        config = EnsembleConfig(
            models=["model_a"],
            device="cpu",
        )
        predictor = EnsemblePredictor(config=config)
        predictor._performance_history["model_a"] = [0.5, 0.7, 0.9]

        result = predictor._get_performance_weights()

        assert len(result) == 1
        # Should use average of history
        expected = sum([0.5, 0.7, 0.9]) / 3
        assert abs(result[0] - expected) < 0.01
