"""Ensemble depth estimation module.

This module provides ensemble prediction by combining outputs from multiple
depth models using weighted averaging, voting, or other aggregation methods
for improved accuracy and robustness.

Ensemble methods can improve depth estimation by:
- Reducing individual model biases
- Providing more robust predictions across different scene types
- Combining complementary strengths of different architectures

Example usage:
    ```python
    from video2d3d.depth.ensemble import EnsemblePredictor, EnsembleConfig

    # Basic usage with default models
    config = EnsembleConfig(
        models=["midas_small", "adabins_nyu"],
        method="weighted_average",
        weights=[0.4, 0.6],
    )
    predictor = EnsemblePredictor(config=config)
    depth_map = predictor.estimate_depth(image)

    # Auto-weighted ensemble
    config = EnsembleConfig(
        models=["zoedepth_nk", "adabins_nyu", "midas_small"],
        method="weighted_average",
        auto_weight=True,
    )
    predictor = EnsemblePredictor(config=config)
    depth_map = predictor.estimate_depth(image)

    # Context manager for automatic cleanup
    with EnsemblePredictor() as predictor:
        depth_map = predictor.estimate_depth(image)
    ```
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.gpu import GPUConfig, select_device
from video2d3d.utils.logger import get_logger, log_model_inference

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default weights for common model combinations
_DEFAULT_WEIGHTS: dict[str, float] = {
    "midas_small": 0.25,
    "midas_hybrid": 0.3,
    "dpt_large": 0.35,
    "dpt_hybrid": 0.35,
    "adabins_nyu": 0.4,
    "adabins_kitti": 0.4,
    "zoedepth_n": 0.45,
    "zoedepth_k": 0.45,
    "zoedepth_nk": 0.5,
}

# Default models for ensemble if none specified
_DEFAULT_ENSEMBLE_MODELS: list[str] = ["zoedepth_nk", "midas_small"]

# Confidence threshold for uncertainty estimation
_DEFAULT_CONFIDENCE_THRESHOLD: float = 0.1

# Default weight when model not in predefined weights
_DEFAULT_MODEL_WEIGHT: float = 0.3

# Epsilon for numerical stability in normalization
_NORMALIZATION_EPSILON: float = 1e-8

# Maximum number of performance scores to keep per model
_MAX_PERFORMANCE_HISTORY_SIZE: int = 100

# Number of recent performance scores to use for weight computation
_PERFORMANCE_WINDOW_SIZE: int = 10


class EnsembleMethod(Enum):
    """Available ensemble combination methods."""

    WEIGHTED_AVERAGE = "weighted_average"  # Weighted average of predictions
    AVERAGE = "average"  # Simple average (equal weights)
    MEDIAN = "median"  # Median of predictions (robust to outliers)
    MAX = "max"  # Maximum value across predictions
    MIN = "min"  # Minimum value across predictions
    VOTING = "voting"  # Soft voting based on confidence


class WeightStrategy(Enum):
    """Strategies for determining ensemble weights."""

    UNIFORM = "uniform"  # Equal weights for all models
    PREDEFINED = "predefined"  # Use predefined quality-based weights
    PERFORMANCE = "performance"  # Weights based on historical performance
    UNCERTAINTY = "uncertainty"  # Inverse uncertainty weighting


@dataclass
class EnsembleConfig:
    """Configuration for ensemble depth estimation.

    Attributes:
        models: List of model names to include in the ensemble.
                Can be model type strings or DepthModelType enums.
        method: Combination method for ensemble predictions.
        weights: Custom weights for each model (must match length of models).
                If None and method is weighted_average, uses auto_weight strategy.
        auto_weight: Automatically determine weights based on strategy.
        weight_strategy: Strategy for automatic weight determination.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        parallel_inference: Run model inference in parallel (experimental).
        normalize_weights: Normalize weights to sum to 1.0.
        min_agreement: Minimum number of models that must agree (for voting).
        confidence_threshold: Threshold for uncertainty-based filtering.
        gpu_config: GPU configuration for acceleration.
        fallback_on_error: Continue with remaining models if one fails.
    """

    models: list[str] = field(default_factory=lambda: _DEFAULT_ENSEMBLE_MODELS.copy())
    method: EnsembleMethod = EnsembleMethod.WEIGHTED_AVERAGE
    weights: list[float] | None = None
    auto_weight: bool = True
    weight_strategy: WeightStrategy = WeightStrategy.PREDEFINED
    device: str = "auto"
    parallel_inference: bool = False
    normalize_weights: bool = True
    min_agreement: int = 2
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD
    gpu_config: GPUConfig | None = None
    fallback_on_error: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Validate models list
        if not self.models:
            raise ValueError("At least one model must be specified for ensemble")

        # Handle string method
        if isinstance(self.method, str):
            self.method = EnsembleMethod(self.method.lower())

        # Handle string weight strategy
        if isinstance(self.weight_strategy, str):
            self.weight_strategy = WeightStrategy(self.weight_strategy.lower())

        # Validate and normalize weights
        if self.weights is not None:
            if len(self.weights) != len(self.models):
                raise ValueError(
                    f"Number of weights ({len(self.weights)}) must match "
                    f"number of models ({len(self.models)})"
                )
            if any(w < 0 for w in self.weights):
                raise ValueError("Weights must be non-negative")
            if self.normalize_weights:
                total = sum(self.weights)
                if total > 0:
                    self.weights = [w / total for w in self.weights]
                else:
                    raise ValueError("Sum of weights must be positive")

        # Initialize GPU config if not provided
        if self.gpu_config is None:
            self.gpu_config = GPUConfig(enabled=True, device=self.device)

        # Auto-detect device
        if self.device == "auto":
            selection = select_device(self.gpu_config)
            self.device = selection.device

        if self.min_agreement > len(self.models):
            self.min_agreement = len(self.models)


class EnsembleError(Exception):
    """Exception raised for ensemble prediction errors."""

    def __init__(
        self,
        message: str,
        *,
        failed_models: list[str] | None = None,
        successful_models: list[str] | None = None,
        original_exceptions: list[Exception] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            failed_models: List of models that failed.
            successful_models: List of models that succeeded.
            original_exceptions: Original exceptions from failed models.
        """
        super().__init__(message)
        self.failed_models = failed_models or []
        self.successful_models = successful_models or []
        self.original_exceptions = original_exceptions or []

    def __str__(self) -> str:
        """Return string representation including failure details."""
        base = super().__str__()
        if self.failed_models:
            return f"{base} (failed: {self.failed_models})"
        return base


def _normalize_weights_list(weights: list[float]) -> list[float]:
    """Normalize a list of weights to sum to 1.0.

    Args:
        weights: List of weights to normalize.

    Returns:
        Normalized weights that sum to 1.0.

    Raises:
        ValueError: If sum of weights is zero or negative.
    """
    total = sum(weights)
    if total <= 0:
        raise ValueError(f"Sum of weights must be positive, got {total}")
    return [w / total for w in weights]
    """Exception raised for ensemble prediction errors."""

    def __init__(
        self,
        message: str,
        *,
        failed_models: list[str] | None = None,
        successful_models: list[str] | None = None,
        original_exceptions: list[Exception] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            failed_models: List of models that failed.
            successful_models: List of models that succeeded.
            original_exceptions: Original exceptions from failed models.
        """
        super().__init__(message)
        self.failed_models = failed_models or []
        self.successful_models = successful_models or []
        self.original_exceptions = original_exceptions or []


def _get_ensemble_logger() -> Logger:
    """Get the ensemble module logger (lazy initialization)."""
    return get_logger("depth.ensemble")


class EnsemblePredictor:
    """Ensemble depth predictor combining multiple depth models.

    This class provides ensemble prediction by running multiple depth models
    and combining their outputs using configurable aggregation methods.

    Supported combination methods:
    - Weighted average: Weighted combination based on model quality/confidence
    - Simple average: Equal-weight combination
    - Median: Robust combination using median (outlier-resistant)
    - Max/Min: Extreme value combination
    - Voting: Soft voting based on prediction confidence

    Example usage:
        ```python
        # Basic usage
        predictor = EnsemblePredictor()
        depth_map = predictor.estimate_depth(image)

        # With configuration
        config = EnsembleConfig(
            models=["zoedepth_nk", "adabins_nyu", "midas_small"],
            method="weighted_average",
        )
        predictor = EnsemblePredictor(config=config)
        depth_map = predictor.estimate_depth(image)

        # Context manager
        with EnsemblePredictor() as predictor:
            depth_map = predictor.estimate_depth(image)
        ```

    Attributes:
        config: EnsembleConfig configuration.
        estimators: Dictionary of loaded model estimators.
        weights: Current weights for each model.
    """

    def __init__(
        self,
        config: EnsembleConfig | None = None,
        *,
        models: list[str] | None = None,
        method: str = "weighted_average",
        device: str = "auto",
    ) -> None:
        """Initialize the ensemble predictor.

        Args:
            config: EnsembleConfig object. If provided, other args are ignored.
            models: List of model names to include in ensemble.
            method: Combination method for ensemble predictions.
            device: Device for inference.
        """
        if config is not None:
            self.config = config
        else:
            self.config = EnsembleConfig(
                models=models or _DEFAULT_ENSEMBLE_MODELS.copy(),
                method=EnsembleMethod(method.lower()),
                device=device,
            )

        # Loaded estimators cache
        self._estimators: dict[str, Any] = {}

        # Compute weights
        self._weights: list[float] | None = None
        if self.config.weights is not None:
            self._weights = self.config.weights
        elif self.config.auto_weight:
            self._weights = self._compute_auto_weights()

        # Performance tracking for adaptive weighting
        self._performance_history: dict[str, list[float]] = {
            model: [] for model in self.config.models
        }

        self._logger = _get_ensemble_logger()
        self._logger.info(
            f"EnsemblePredictor initialized: models={self.config.models}, "
            f"method={self.config.method.value}, device={self.config.device}"
        )

    def __repr__(self) -> str:
        """Return string representation of the ensemble predictor."""
        return (
            f"EnsemblePredictor(models={self.config.models}, "
            f"method={self.config.method.value}, device={self.config.device})"
        )

    def _normalize_weights(self, weights: list[float]) -> list[float]:
        """Normalize weights to sum to 1.0.

        Args:
            weights: List of weights to normalize.

        Returns:
            Normalized weights that sum to 1.0.
        """
        total = sum(weights)
        if total > 0:
            return [w / total for w in weights]
        n = len(weights)
        return [1.0 / n] * n if n > 0 else []

    @property
    def weights(self) -> list[float]:
        """Get the current weights for each model."""
        if self._weights is None:
            # Default to uniform weights
            n = len(self.config.models)
            return [1.0 / n] * n
        return self._weights

    @property
    def loaded_models(self) -> list[str]:
        """Get list of successfully loaded models."""
        return list(self._estimators.keys())

    def _compute_auto_weights(self) -> list[float]:
        """Compute automatic weights based on strategy.

        Returns:
            List of weights corresponding to each model.
        """
        n = len(self.config.models)

        if self.config.weight_strategy == WeightStrategy.UNIFORM:
            return [1.0 / n] * n if n > 0 else []

        if self.config.weight_strategy == WeightStrategy.PREDEFINED:
            weights = self._get_predefined_weights()
            if self.config.normalize_weights:
                weights = self._normalize_weights(weights)
            return weights

        if self.config.weight_strategy == WeightStrategy.PERFORMANCE:
            weights = self._get_performance_weights()
            if self.config.normalize_weights:
                weights = self._normalize_weights(weights)
            return weights

        if self.config.weight_strategy == WeightStrategy.UNCERTAINTY:
            # Will be computed dynamically during inference
            # Return uniform as placeholder
            return [1.0 / n] * n if n > 0 else []

        # Fallback to uniform (should not reach here if all enum cases covered)
        return [1.0 / n] * n if n > 0 else []

    def _get_predefined_weights(self) -> list[float]:
        """Get predefined quality-based weights for models.

        Returns:
            List of weights corresponding to each model.
        """
        weights = []
        for model in self.config.models:
            normalized = model.lower().replace("-", "_")
            weight = _DEFAULT_WEIGHTS.get(normalized, _DEFAULT_MODEL_WEIGHT)
            weights.append(weight)
        return weights

    def _get_performance_weights(self) -> list[float]:
        """Get weights based on historical performance.

        Returns:
            List of weights corresponding to each model.
        """
        weights = []
        for model in self.config.models:
            history = self._performance_history.get(model, [])
            if history:
                # Use average of recent performance as weight
                recent = history[-_PERFORMANCE_WINDOW_SIZE:]
                weight = sum(recent) / len(recent)
            else:
                # Fall back to predefined weight
                normalized = model.lower().replace("-", "_")
                weight = _DEFAULT_WEIGHTS.get(normalized, _DEFAULT_MODEL_WEIGHT)
            weights.append(weight)
        return weights

    def _get_estimator(self, model_name: str) -> Any:
        """Get or create an estimator for the specified model.

        Args:
            model_name: Model name to get estimator for.

        Returns:
            Estimator instance for the model.

        Raises:
            ValueError: If model name is not recognized.
            Exception: If model loading fails.
        """
        if model_name in self._estimators:
            return self._estimators[model_name]

        # Import here to avoid circular imports
        from video2d3d.depth.model_selector import (
            DepthModelConfig,
            DepthModelSelector,
            DepthModelType,
        )

        try:
            # Use DepthModelSelector which handles all model types
            config = DepthModelConfig(
                primary_model=model_name,
                device=self.config.device,
            )
            selector = DepthModelSelector(config=config)
            # Force load by calling _get_estimator
            estimator = selector._get_estimator(DepthModelType.from_string(model_name))
            self._estimators[model_name] = estimator
            self._logger.info(f"Loaded model: {model_name}")
            return estimator

        except Exception as e:
            self._logger.warning(f"Failed to load model {model_name}: {e}")
            raise

    def preload_models(self) -> dict[str, bool]:
        """Preload all models in the ensemble.

        Returns:
            Dictionary mapping model names to load success status.
        """
        results: dict[str, bool] = {}

        for model_name in self.config.models:
            try:
                self._get_estimator(model_name)
                results[model_name] = True
                self._logger.info(f"Preloaded model: {model_name}")
            except Exception as e:
                results[model_name] = False
                self._logger.warning(f"Failed to preload {model_name}: {e}")

        return results

    def _estimate_single_model(
        self,
        frame: np.ndarray,
        model_name: str,
    ) -> np.ndarray:
        """Estimate depth using a single model.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
            model_name: Name of the model to use.

        Returns:
            Depth map as numpy array (H, W) with float32 values in [0, 1].

        Raises:
            Exception: If estimation fails.
        """
        estimator = self._get_estimator(model_name)
        return estimator.estimate_depth(frame)

    def _compute_uncertainty_weights(
        self,
        predictions: list[np.ndarray],
    ) -> list[float]:
        """Compute weights based on prediction uncertainty.

        Lower uncertainty (variance) -> higher weight.

        Args:
            predictions: List of depth map predictions.

        Returns:
            List of uncertainty-based weights.
        """
        # Lazy import to avoid dependency if not used
        try:
            from scipy import ndimage
        except ImportError as e:
            self._logger.warning(f"scipy not available, using uniform weights: {e}")
            return [1.0 / len(predictions)] * len(predictions)

        uncertainties = []
        for pred in predictions:
            # Compute local variance as uncertainty measure
            # Lower variance = more confident = higher weight
            # Use Laplacian variance as sharpness/confidence measure
            laplacian = ndimage.laplace(pred)
            uncertainty = 1.0 / (laplacian.var() + _NORMALIZATION_EPSILON)
            uncertainties.append(uncertainty)

        # Normalize: lower uncertainty -> higher weight
        return self._normalize_weights(uncertainties)

    def _compute_uncertainty_weights(
        self,
        predictions: list[np.ndarray],
    ) -> list[float]:
        """Compute weights based on prediction uncertainty.

        Lower uncertainty (variance) -> higher weight.

        Args:
            predictions: List of depth map predictions.

        Returns:
            List of uncertainty-based weights.
        """
        uncertainties = []
        for pred in predictions:
            # Compute local variance as uncertainty measure
            # Lower variance = more confident = higher weight
            from scipy import ndimage

            # Use Laplacian variance as sharpness/confidence measure
            laplacian = ndimage.laplace(pred)
            uncertainty = 1.0 / (laplacian.var() + 1e-8)
            uncertainties.append(uncertainty)

        # Invert: lower uncertainty -> higher weight
        total = sum(uncertainties)
        if total > 0:
            return [u / total for u in uncertainties]
        else:
            n = len(predictions)
            return [1.0 / n] * n

    def _combine_weighted_average(
        self,
        predictions: list[np.ndarray],
        weights: list[float],
    ) -> np.ndarray:
        """Combine predictions using weighted average.

        Args:
            predictions: List of depth map predictions.
            weights: Weights for each prediction.

        Returns:
            Combined depth map.
        """
        # Stack predictions
        stacked = np.stack(predictions, axis=0)

        # Compute weighted average
        weights_array = np.array(weights).reshape(-1, 1, 1)
        combined = np.sum(stacked * weights_array, axis=0)

        return combined.astype(np.float32)

    def _combine_average(self, predictions: list[np.ndarray]) -> np.ndarray:
        """Combine predictions using simple average.

        Args:
            predictions: List of depth map predictions.

        Returns:
            Combined depth map.
        """
        stacked = np.stack(predictions, axis=0)
        return np.mean(stacked, axis=0).astype(np.float32)

    def _combine_median(self, predictions: list[np.ndarray]) -> np.ndarray:
        """Combine predictions using median.

        Args:
            predictions: List of depth map predictions.

        Returns:
            Combined depth map.
        """
        stacked = np.stack(predictions, axis=0)
        return np.median(stacked, axis=0).astype(np.float32)

    def _combine_max(self, predictions: list[np.ndarray]) -> np.ndarray:
        """Combine predictions using maximum.

        Args:
            predictions: List of depth map predictions.

        Returns:
            Combined depth map.
        """
        stacked = np.stack(predictions, axis=0)
        return np.max(stacked, axis=0).astype(np.float32)

    def _combine_min(self, predictions: list[np.ndarray]) -> np.ndarray:
        """Combine predictions using minimum.

        Args:
            predictions: List of depth map predictions.

        Returns:
            Combined depth map.
        """
        stacked = np.stack(predictions, axis=0)
        return np.min(stacked, axis=0).astype(np.float32)

    def _combine_voting(
        self,
        predictions: list[np.ndarray],
        weights: list[float],
    ) -> np.ndarray:
        """Combine predictions using soft voting.

        Args:
            predictions: List of depth map predictions.
            weights: Weights for each prediction.

        Returns:
            Combined depth map.
        """
        # For depth, soft voting is essentially weighted average
        # with confidence-based weight adjustment
        return self._combine_weighted_average(predictions, weights)

    def _combine_predictions(
        self,
        predictions: list[np.ndarray],
        weights: list[float] | None = None,
    ) -> np.ndarray:
        """Combine predictions using the configured method.

        Args:
            predictions: List of depth map predictions.
            weights: Optional weights for weighted methods.

        Returns:
            Combined depth map.
        """
        if not predictions:
            raise EnsembleError("No predictions to combine")

        method = self.config.method

        if method == EnsembleMethod.WEIGHTED_AVERAGE:
            effective_weights = weights or self.weights
            if len(effective_weights) != len(predictions):
                # Adjust weights to match available predictions
                n = len(predictions)
                effective_weights = [1.0 / n] * n
            return self._combine_weighted_average(predictions, effective_weights)

        elif method == EnsembleMethod.AVERAGE:
            return self._combine_average(predictions)

        elif method == EnsembleMethod.MEDIAN:
            return self._combine_median(predictions)

        elif method == EnsembleMethod.MAX:
            return self._combine_max(predictions)

        elif method == EnsembleMethod.MIN:
            return self._combine_min(predictions)

        elif method == EnsembleMethod.VOTING:
            effective_weights = weights or self.weights
            if len(effective_weights) != len(predictions):
                n = len(predictions)
                effective_weights = [1.0 / n] * n
            return self._combine_voting(predictions, effective_weights)

        else:
            # Default to average
            return self._combine_average(predictions)

    def estimate_depth(
        self,
        frame: np.ndarray,
        return_uncertainty: bool = False,
    ) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
        """Estimate depth using the ensemble of models.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            return_uncertainty: If True, also return uncertainty map.

        Returns:
            Depth map as numpy array (H, W) with float32 values in [0, 1].
            If return_uncertainty is True, returns tuple of (depth_map, uncertainty_map).

        Raises:
            EnsembleError: If all models fail and fallback_on_error is False.
        """
        start_time = time.time()

        # Input validation
        if not isinstance(frame, np.ndarray):
            raise EnsembleError(f"Input must be a numpy array, got {type(frame).__name__}")
        if frame.ndim != 3:
            raise EnsembleError(f"Input must be 3D array (H, W, C), got {frame.ndim}D")
        if frame.shape[2] != 3:
            raise EnsembleError(f"Input must have 3 channels (RGB), got {frame.shape[2]}")

        self._logger.debug(f"Estimating depth with ensemble: shape={frame.shape}")

        # Collect predictions from all models
        predictions: list[np.ndarray] = []
        successful_models: list[str] = []
        failed_models: list[str] = []
        errors: list[Exception] = []

        for model_name in self.config.models:
            try:
                pred = self._estimate_single_model(frame, model_name)
                predictions.append(pred)
                successful_models.append(model_name)
                self._logger.debug(f"Model {model_name} prediction successful")
            except Exception as e:
                failed_models.append(model_name)
                errors.append(e)
                self._logger.warning(f"Model {model_name} failed: {e}")

                if not self.config.fallback_on_error:
                    raise EnsembleError(
                        f"Model {model_name} failed and fallback disabled",
                        failed_models=[model_name],
                        original_exceptions=[e],
                    ) from e

        # Check if we have enough predictions
        if len(predictions) < self.config.min_agreement:
            raise EnsembleError(
                f"Not enough successful models: {len(predictions)} < {self.config.min_agreement}",
                failed_models=failed_models,
                successful_models=successful_models,
                original_exceptions=errors,
            )

        # Compute weights for available predictions
        weights = self.weights[: len(predictions)]
        if self.config.weight_strategy == WeightStrategy.UNCERTAINTY:
            weights = self._compute_uncertainty_weights(predictions)

        # Normalize weights
        if self.config.normalize_weights and weights:
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]

        # Combine predictions
        combined = self._combine_predictions(predictions, weights)

        # Normalize to [0, 1]
        combined = self._normalize_depth_map(combined)

        elapsed_ms = (time.time() - start_time) * 1000
        self._logger.debug(
            f"Ensemble prediction completed in {elapsed_ms:.2f}ms with {len(predictions)} models"
        )

        log_model_inference(
            model_name="ensemble",
            batch_size=1,
            inference_time_ms=elapsed_ms,
            models_used=successful_models,
            method=self.config.method.value,
        )

        if return_uncertainty:
            uncertainty = self._compute_uncertainty_map(predictions, combined)
            return combined, uncertainty

        return combined.astype(np.float32)

    def _normalize_depth_map(self, depth_map: np.ndarray) -> np.ndarray:
        """Normalize depth map to [0, 1] range.

        Args:
            depth_map: Input depth map.

        Returns:
            Normalized depth map with values in [0, 1].
        """
        min_val = depth_map.min()
        max_val = depth_map.max()
        if max_val - min_val > _NORMALIZATION_EPSILON:
            return ((depth_map - min_val) / (max_val - min_val)).astype(np.float32)
        return np.zeros_like(depth_map)

    def _compute_uncertainty_map(
        self,
        predictions: list[np.ndarray],
        combined: np.ndarray,
    ) -> np.ndarray:
        """Compute uncertainty map from predictions.

        Args:
            predictions: List of depth predictions.
            combined: Combined depth map.

        Returns:
            Uncertainty map with values in [0, 1].
        """
        if len(predictions) > 1:
            stacked = np.stack(predictions, axis=0)
            uncertainty = np.std(stacked, axis=0).astype(np.float32)
            # Normalize uncertainty to [0, 1]
            u_max = uncertainty.max()
            if u_max > 0:
                uncertainty = uncertainty / u_max
            return uncertainty
        return np.zeros_like(combined)

    def estimate_depth_batch(
        self,
        frames: list[np.ndarray],
        batch_size: int = 4,
    ) -> list[np.ndarray]:
        """Estimate depth for a batch of frames using the ensemble.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
            batch_size: Batch size for processing (per model). Note: Currently
                        processes frames sequentially; batch_size reserved for
                        future parallel optimization.

        Returns:
            List of depth maps as numpy arrays (H, W) with float32 values in [0, 1].
        """
        if not frames:
            return []

        self._logger.info(
            f"Processing batch of {len(frames)} frames with ensemble " f"(batch_size={batch_size})"
        )

        # TODO: Implement parallel batch processing when models support it
        # For now, process each frame through the ensemble sequentially
        depth_maps: list[np.ndarray] = []
        for frame in frames:
            depth_map = self.estimate_depth(frame)
            depth_maps.append(depth_map)

        return depth_maps

    def get_model_weights(self) -> dict[str, float]:
        """Get the current weights for each model.

        Returns:
            Dictionary mapping model names to their weights.
        """
        return dict(zip(self.config.models, self.weights))

    def set_model_weights(self, weights: dict[str, float]) -> None:
        """Set custom weights for models.

        Args:
            weights: Dictionary mapping model names to weights.

        Raises:
            ValueError: If any weight is negative.
        """
        # Validate weights first
        for model_name, weight in weights.items():
            if weight < 0:
                raise ValueError(
                    f"Weight for model '{model_name}' must be non-negative, got {weight}"
                )

        new_weights = []
        for model in self.config.models:
            if model in weights:
                new_weights.append(weights[model])
            else:
                # Keep existing weight or use default
                idx = self.config.models.index(model)
                if self._weights and idx < len(self._weights):
                    new_weights.append(self._weights[idx])
                else:
                    new_weights.append(1.0 / len(self.config.models))

        if self.config.normalize_weights:
            new_weights = self._normalize_weights(new_weights)

        self._weights = new_weights

    def update_performance(self, model_name: str, score: float) -> None:
        """Update performance history for a model.

        Args:
            model_name: Name of the model.
            score: Performance score (higher is better).

        Raises:
            ValueError: If model_name is not in the ensemble.
        """
        if model_name not in self._performance_history:
            raise ValueError(
                f"Model '{model_name}' not in ensemble. "
                f"Available models: {list(self._performance_history.keys())}"
            )

        self._performance_history[model_name].append(score)
        # Keep only recent scores
        self._performance_history[model_name] = self._performance_history[model_name][
            -_MAX_PERFORMANCE_HISTORY_SIZE:
        ]

        # Recompute weights if using performance strategy
        if self.config.weight_strategy == WeightStrategy.PERFORMANCE:
            self._weights = self._compute_auto_weights()

    def get_uncertainty_map(
        self,
        predictions: list[np.ndarray] | None = None,
        frame: np.ndarray | None = None,
    ) -> np.ndarray:
        """Compute uncertainty map from predictions.

        Args:
            predictions: Optional list of predictions. If None, will run inference.
            frame: Required if predictions is None.

        Returns:
            Uncertainty map with values in [0, 1].

        Raises:
            ValueError: If neither predictions nor frame is provided.
        """
        if predictions is None:
            if frame is None:
                raise ValueError("Either predictions or frame must be provided")
            _, uncertainty = self.estimate_depth(frame, return_uncertainty=True)
            return uncertainty

        if len(predictions) < 2:
            return np.zeros_like(predictions[0]) if predictions else np.array([])

        stacked = np.stack(predictions, axis=0)
        uncertainty = np.std(stacked, axis=0).astype(np.float32)

        # Normalize to [0, 1]
        u_max = uncertainty.max()
        if u_max > 0:
            uncertainty = uncertainty / u_max

        return uncertainty

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        """Estimate depth from a single frame (callable interface)."""
        return self.estimate_depth(frame)

    def __enter__(self) -> EnsemblePredictor:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self) -> None:
        """Release all loaded model resources."""
        for model_name, estimator in self._estimators.items():
            try:
                if hasattr(estimator, "close"):
                    estimator.close()
            except Exception as e:
                self._logger.warning(f"Error closing {model_name}: {e}")

        self._estimators.clear()
        self._logger.debug("EnsemblePredictor resources released")


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_ensemble_predictor(
    models: list[str] | None = None,
    method: str = "weighted_average",
    weights: list[float] | None = None,
    device: str = "auto",
    **kwargs: Any,
) -> EnsemblePredictor:
    """Create an ensemble depth predictor with the specified configuration.

    Args:
        models: List of model names to include in ensemble.
        method: Combination method ('weighted_average', 'average', 'median', etc.).
        weights: Custom weights for each model.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        **kwargs: Additional EnsembleConfig field values.

    Returns:
        Configured EnsemblePredictor instance.
    """
    config = EnsembleConfig(
        models=models or _DEFAULT_ENSEMBLE_MODELS.copy(),
        method=EnsembleMethod(method.lower()),
        weights=weights,
        device=device,
        **kwargs,
    )
    return EnsemblePredictor(config=config)


def estimate_depth_ensemble(
    image: np.ndarray,
    models: list[str] | None = None,
    method: str = "weighted_average",
    weights: list[float] | None = None,
    device: str = "auto",
) -> np.ndarray:
    """Estimate depth using an ensemble of models (convenience function).

    Args:
        image: Input image as numpy array (H, W, C) in RGB format.
        models: List of model names to include in ensemble.
        method: Combination method ('weighted_average', 'average', 'median', etc.).
        weights: Custom weights for each model.
        device: Device for inference.

    Returns:
        Depth map as numpy array (H, W) with float32 values in [0, 1].
    """
    with create_ensemble_predictor(
        models=models,
        method=method,
        weights=weights,
        device=device,
    ) as predictor:
        return predictor.estimate_depth(image)


# Module-level exports
__all__ = [
    # Classes
    "EnsemblePredictor",
    "EnsembleConfig",
    # Enums
    "EnsembleMethod",
    "WeightStrategy",
    # Exceptions
    "EnsembleError",
    # Functions
    "create_ensemble_predictor",
    "estimate_depth_ensemble",
    # Constants
    "_DEFAULT_WEIGHTS",
    "_DEFAULT_ENSEMBLE_MODELS",
    "_DEFAULT_CONFIDENCE_THRESHOLD",
    # Helper functions
    "_normalize_weights_list",
]
