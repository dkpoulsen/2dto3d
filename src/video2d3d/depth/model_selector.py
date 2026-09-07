"""Depth model selector for automatic model selection and fallback.

This module provides a unified interface for depth estimation that automatically
selects the best available model and handles fallback between different models
(AdaBins, MiDaS) based on performance, scene characteristics, and error conditions.

Example usage:
    ```python
    from video2d3d.depth.model_selector import DepthModelSelector, DepthModelConfig

    # Basic usage with automatic model selection
    config = DepthModelConfig(
        primary_model="adabins",
        fallback_model="midas_small",
        enable_auto_fallback=True,
    )
    selector = DepthModelSelector(config=config)
    depth_map = selector.estimate_depth(image)

    # Scene-adaptive selection
    config = DepthModelConfig(enable_scene_adaptation=True)
    selector = DepthModelSelector(config=config)
    depth_map = selector.estimate_depth(image)
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
from video2d3d.utils.logger import get_logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default timeout for model loading (seconds)
_DEFAULT_MODEL_LOAD_TIMEOUT: float = 60.0

# Confidence threshold for scene classification
_DEFAULT_SCENE_CONFIDENCE_THRESHOLD: float = 0.7


class DepthModelType(str, Enum):
    """Available depth estimation model types."""

    MIDAS_SMALL = "midas_small"
    MIDAS_HYBRID = "midas_hybrid"
    DPT_LARGE = "dpt_large"
    DPT_HYBRID = "dpt_hybrid"
    ADABINS_NYU = "adabins_nyu"
    ADABINS_KITTI = "adabins_kitti"
    ZOEDEPTH_N = "zoedepth_n"
    ZOEDEPTH_K = "zoedepth_k"
    ZOEDEPTH_NK = "zoedepth_nk"

    @classmethod
    def from_string(cls, name: str) -> DepthModelType:
        """Get model type from string name.

        Args:
            name: Model name (case-insensitive).

        Returns:
            DepthModelType enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        name_mapping = {
            "midas_small": cls.MIDAS_SMALL,
            "midas_small_2.1": cls.MIDAS_SMALL,
            "midas": cls.MIDAS_SMALL,
            "midas_2.1": cls.MIDAS_SMALL,
            "midas_hybrid": cls.MIDAS_HYBRID,
            "dpt_large": cls.DPT_LARGE,
            "dpt_large_384": cls.DPT_LARGE,
            "dpt_hybrid": cls.DPT_HYBRID,
            "dpt_hybrid_384": cls.DPT_HYBRID,
            "adabins_nyu": cls.ADABINS_NYU,
            "adadepth_nyu": cls.ADABINS_NYU,
            "nyu": cls.ADABINS_NYU,
            "adabins_kitti": cls.ADABINS_KITTI,
            "adadepth_kitti": cls.ADABINS_KITTI,
            "kitti": cls.ADABINS_KITTI,
            "zoedepth_n": cls.ZOEDEPTH_N,
            "zoed_n": cls.ZOEDEPTH_N,
            "zoe_n": cls.ZOEDEPTH_N,
            "zoedepth_k": cls.ZOEDEPTH_K,
            "zoed_k": cls.ZOEDEPTH_K,
            "zoe_k": cls.ZOEDEPTH_K,
            "zoedepth_nk": cls.ZOEDEPTH_NK,
            "zoed_nk": cls.ZOEDEPTH_NK,
            "zoe_nk": cls.ZOEDEPTH_NK,
            "zoedepth": cls.ZOEDEPTH_NK,
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown model name '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def is_midas(self) -> bool:
        """Check if this is a MiDaS/DPT model."""
        return self in (
            DepthModelType.MIDAS_SMALL,
            DepthModelType.MIDAS_HYBRID,
            DepthModelType.DPT_LARGE,
            DepthModelType.DPT_HYBRID,
        )

    @property
    def is_adabins(self) -> bool:
        """Check if this is an AdaBins model."""
        return self in (DepthModelType.ADABINS_NYU, DepthModelType.ADABINS_KITTI)

    @property
    def is_zoedepth(self) -> bool:
        """Check if this is a ZoeDepth model."""
        return self in (
            DepthModelType.ZOEDEPTH_N,
            DepthModelType.ZOEDEPTH_K,
            DepthModelType.ZOEDEPTH_NK,
        )

    @property
    def supports_metric(self) -> bool:
        """Check if this model supports metric depth estimation."""
        return self.is_zoedepth


class SceneType(Enum):
    """Scene classification types for adaptive model selection."""

    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class DepthModelConfig:
    """Configuration for depth model selection and fallback.

    Attributes:
        primary_model: Primary model to use for depth estimation.
        fallback_model: Fallback model if primary fails.
        enable_auto_fallback: Enable automatic fallback on errors.
        enable_scene_adaptation: Enable scene-adaptive model selection.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        model_load_timeout: Timeout for model loading in seconds.
        scene_confidence_threshold: Confidence threshold for scene classification.
        gpu_config: GPU configuration for acceleration.
    """

    primary_model: DepthModelType = DepthModelType.ADABINS_NYU
    fallback_model: DepthModelType = DepthModelType.MIDAS_SMALL
    enable_auto_fallback: bool = True
    enable_scene_adaptation: bool = False
    device: str = "auto"
    model_load_timeout: float = _DEFAULT_MODEL_LOAD_TIMEOUT
    scene_confidence_threshold: float = _DEFAULT_SCENE_CONFIDENCE_THRESHOLD
    gpu_config: GPUConfig | None = None

    # Fallback chain for model failures
    fallback_chain: list[DepthModelType] = field(
        default_factory=lambda: [
            DepthModelType.ADABINS_NYU,
            DepthModelType.MIDAS_SMALL,
            DepthModelType.DPT_HYBRID,
        ]
    )

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Handle string model types
        if isinstance(self.primary_model, str):
            self.primary_model = DepthModelType.from_string(self.primary_model)
        if isinstance(self.fallback_model, str):
            self.fallback_model = DepthModelType.from_string(self.fallback_model)

        # Normalize fallback chain
        self.fallback_chain = [
            DepthModelType.from_string(m) if isinstance(m, str) else m for m in self.fallback_chain
        ]

        # Initialize GPU config if not provided
        if self.gpu_config is None:
            self.gpu_config = GPUConfig(enabled=True, device=self.device)

        # Auto-detect device
        if self.device == "auto":
            selection = select_device(self.gpu_config)
            self.device = selection.device


class ModelLoadError(Exception):
    """Exception raised when all models fail to load."""

    def __init__(
        self,
        message: str,
        *,
        attempted_models: list[str] | None = None,
        original_exceptions: list[Exception] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            attempted_models: List of models that were attempted.
            original_exceptions: List of original exceptions.
        """
        super().__init__(message)
        self.attempted_models = attempted_models or []
        self.original_exceptions = original_exceptions or []


class ModelInferenceError(Exception):
    """Exception raised when inference fails on all models."""

    def __init__(
        self,
        message: str,
        *,
        attempted_models: list[str] | None = None,
        original_exceptions: list[Exception] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            attempted_models: List of models that were attempted.
            original_exceptions: List of original exceptions.
        """
        super().__init__(message)
        self.attempted_models = attempted_models or []
        self.original_exceptions = original_exceptions or []


def _get_selector_logger() -> Logger:
    """Get the model selector logger (lazy initialization)."""
    return get_logger("depth.model_selector")


class DepthModelSelector:
    """Unified depth estimation with automatic model selection and fallback.

    This class provides a single interface for depth estimation that handles
    model selection, loading, fallback, and scene adaptation automatically.

    Example usage:
        ```python
        # Basic usage
        selector = DepthModelSelector()
        depth_map = selector.estimate_depth(image)

        # With configuration
        config = DepthModelConfig(
            primary_model="adabins_nyu",
            fallback_model="midas_small",
            enable_auto_fallback=True,
        )
        selector = DepthModelSelector(config=config)
        depth_map = selector.estimate_depth(image)

        # Context manager
        with DepthModelSelector() as selector:
            depth_map = selector.estimate_depth(image)
        ```

    Attributes:
        config: DepthModelConfig configuration.
    """

    def __init__(
        self,
        config: DepthModelConfig | None = None,
        *,
        primary_model: str = "adabins_nyu",
        fallback_model: str = "midas_small",
        device: str = "auto",
    ) -> None:
        """Initialize the depth model selector.

        Args:
            config: DepthModelConfig object. If provided, other args are ignored.
            primary_model: Primary model type.
            fallback_model: Fallback model type.
            device: Device for inference.
        """
        if config is not None:
            self.config = config
        else:
            self.config = DepthModelConfig(
                primary_model=DepthModelType.from_string(primary_model),
                fallback_model=DepthModelType.from_string(fallback_model),
                device=device,
            )

        # Loaded estimators cache
        self._estimators: dict[DepthModelType, Any] = {}
        self._active_model: DepthModelType | None = None

        # Scene classifier state
        self._last_scene_type: SceneType = SceneType.UNKNOWN

        self._logger = _get_selector_logger()
        self._logger.info(
            f"DepthModelSelector initialized: primary={self.config.primary_model.value}, "
            f"fallback={self.config.fallback_model.value}"
        )

    @property
    def active_model(self) -> DepthModelType | None:
        """Get the currently active model type."""
        return self._active_model

    @property
    def last_scene_type(self) -> SceneType:
        """Get the last detected scene type."""
        return self._last_scene_type

    def _get_estimator(self, model_type: DepthModelType) -> Any:
        """Get or create an estimator for the specified model type.

        Args:
            model_type: Model type to get estimator for.

        Returns:
            Estimator instance for the model.

        Raises:
            ModelLoadError: If model loading fails.
        """
        if model_type in self._estimators:
            return self._estimators[model_type]

        try:
            estimator = self._create_estimator(model_type)
            self._estimators[model_type] = estimator
            return estimator
        except Exception as e:
            self._logger.warning(f"Failed to load model {model_type.value}: {e}")
            raise

    def _create_estimator(self, model_type: DepthModelType) -> Any:
        """Create a new estimator for the specified model type.

        Args:
            model_type: Model type to create estimator for.

        Returns:
            New estimator instance.
        """
        if model_type.is_midas:
            from video2d3d.depth import DepthEstimator, MiDaSConfig, MiDaSModelType

            # Map DepthModelType to MiDaSModelType
            midas_mapping = {
                DepthModelType.MIDAS_SMALL: MiDaSModelType.MIDAS_V21_SMALL,
                DepthModelType.MIDAS_HYBRID: MiDaSModelType.MIDAS_V21,
                DepthModelType.DPT_LARGE: MiDaSModelType.DPT_LARGE,
                DepthModelType.DPT_HYBRID: MiDaSModelType.DPT_HYBRID,
            }

            config = MiDaSConfig(
                model_type=midas_mapping.get(model_type, MiDaSModelType.MIDAS_V21_SMALL),
                device=self.config.device,
            )
            return DepthEstimator(config=config)

        elif model_type.is_adabins:
            from video2d3d.depth.adadepth import AdaBinsConfig, AdaBinsEstimator, AdaBinsModelType

            # Map DepthModelType to AdaBinsModelType
            adabins_mapping = {
                DepthModelType.ADABINS_NYU: AdaBinsModelType.ADADEPTH_NYU,
                DepthModelType.ADABINS_KITTI: AdaBinsModelType.ADADEPTH_KITTI,
            }

            config = AdaBinsConfig(
                model_type=adabins_mapping.get(model_type, AdaBinsModelType.ADADEPTH_NYU),
                device=self.config.device,
            )
            return AdaBinsEstimator(config=config)

        elif model_type.is_zoedepth:
            from video2d3d.depth.zoedepth import (
                ZoeDepthConfig,
                ZoeDepthEstimator,
                ZoeDepthModelVariant,
            )

            # Map DepthModelType to ZoeDepthModelVariant
            zoedepth_mapping = {
                DepthModelType.ZOEDEPTH_N: ZoeDepthModelVariant.ZOE_N,
                DepthModelType.ZOEDEPTH_K: ZoeDepthModelVariant.ZOE_K,
                DepthModelType.ZOEDEPTH_NK: ZoeDepthModelVariant.ZOE_NK,
            }

            config = ZoeDepthConfig(
                model_variant=zoedepth_mapping.get(model_type, ZoeDepthModelVariant.ZOE_NK),
                device=self.config.device,
            )
            return ZoeDepthEstimator(config=config)

        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def _classify_scene(self, image: np.ndarray) -> SceneType:
        """Classify the scene type for adaptive model selection.

        This is a simple heuristic-based classifier. For production use,
        consider using a trained classifier.

        Args:
            image: Input RGB image.

        Returns:
            Detected scene type.
        """
        # Simple heuristic: analyze color distribution
        # Indoor scenes tend to have warmer colors, outdoor cooler

        try:
            # Convert to float
            img_float = image.astype(np.float32) / 255.0

            # Calculate mean colors
            r_mean = np.mean(img_float[:, :, 0])
            g_mean = np.mean(img_float[:, :, 1])
            b_mean = np.mean(img_float[:, :, 2])

            # Calculate color temperature (simplified)
            # Higher R/B ratio suggests warmer (indoor) lighting
            warmth_ratio = r_mean / b_mean if b_mean > 0.01 else 1.0

            # Calculate brightness
            brightness = (r_mean + g_mean + b_mean) / 3.0

            # Simple classification
            if warmth_ratio > 1.3 and brightness < 0.5:
                return SceneType.INDOOR
            elif warmth_ratio < 0.9 or brightness > 0.6:
                return SceneType.OUTDOOR
            else:
                return SceneType.MIXED

        except Exception as e:
            self._logger.debug(f"Scene classification failed: {e}")
            return SceneType.UNKNOWN

    def _select_model_for_scene(self, scene_type: SceneType) -> DepthModelType:
        """Select the best model for a given scene type.

        Args:
            scene_type: Detected scene type.

        Returns:
            Best model type for the scene.
        """
        if scene_type == SceneType.INDOOR:
            # AdaBins NYU is trained on indoor scenes
            return DepthModelType.ADABINS_NYU
        elif scene_type == SceneType.OUTDOOR:
            # AdaBins KITTI is trained on outdoor (driving) scenes
            return DepthModelType.ADABINS_KITTI
        else:
            # Default to primary model
            return self.config.primary_model

    def estimate_depth(
        self,
        frame: np.ndarray,
        scene_type: SceneType | None = None,
    ) -> np.ndarray:
        """Estimate depth with automatic model selection and fallback.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
            scene_type: Optional scene type hint. If None and scene adaptation
                       is enabled, will attempt to classify automatically.

        Returns:
            Depth map as numpy array (H, W) with float32 values in [0, 1].

        Raises:
            ModelInferenceError: If all models fail.
        """
        start_time = time.time()

        # Honor explicitly-selected active model (e.g. set by the caller)
        if self._active_model is not None:
            estimator = self._get_estimator(self._active_model)
            depth_map = estimator.estimate_depth(frame)
            self._logger.debug(
                f"Depth estimation completed with {self._active_model.value} "
                f"in {(time.time() - start_time) * 1000:.2f}ms"
            )
            return depth_map

        # Determine scene type if needed
        if self.config.enable_scene_adaptation and scene_type is None:
            scene_type = self._classify_scene(frame)
            self._last_scene_type = scene_type
            self._logger.debug(f"Detected scene type: {scene_type.value}")

        # Select primary model
        if scene_type is not None and self.config.enable_scene_adaptation:
            primary_model = self._select_model_for_scene(scene_type)
        else:
            primary_model = self.config.primary_model

        # Build attempt order
        if self.config.enable_auto_fallback:
            # Use fallback chain, starting with primary
            attempt_order = [primary_model]
            for model in self.config.fallback_chain:
                if model not in attempt_order:
                    attempt_order.append(model)
            # Always add fallback model as last resort
            if self.config.fallback_model not in attempt_order:
                attempt_order.append(self.config.fallback_model)
        else:
            attempt_order = [primary_model]

        # Try each model
        errors: list[tuple[DepthModelType, Exception]] = []

        for model_type in attempt_order:
            try:
                estimator = self._get_estimator(model_type)
                depth_map = estimator.estimate_depth(frame)
                self._active_model = model_type

                elapsed_ms = (time.time() - start_time) * 1000
                self._logger.debug(
                    f"Depth estimation completed with {model_type.value} in {elapsed_ms:.2f}ms"
                )

                return depth_map

            except Exception as e:
                self._logger.warning(f"Model {model_type.value} failed: {e}. Trying next model...")
                errors.append((model_type, e))
                continue

        # All models failed
        error_msg = f"All depth models failed. Attempted: {[m.value for m, _ in errors]}"
        self._logger.error(error_msg)

        raise ModelInferenceError(
            error_msg,
            attempted_models=[m.value for m, _ in errors],
            original_exceptions=[e for _, e in errors],
        )

    def estimate_depth_batch(
        self,
        frames: list[np.ndarray],
        batch_size: int = 4,
    ) -> list[np.ndarray]:
        """Estimate depth for a batch of frames.

        Uses the same model for all frames to ensure consistency.

        Args:
            frames: List of input frames.
            batch_size: Batch size for processing.

        Returns:
            List of depth maps.
        """
        if not frames:
            return []

        # Use first frame to select model
        first_depth = self.estimate_depth(frames[0])

        if self._active_model is None:
            raise ModelInferenceError("No active model available")

        # Get the active estimator for batch processing
        try:
            estimator = self._get_estimator(self._active_model)
            remaining_depths = estimator.estimate_depth_batch(frames[1:], batch_size=batch_size)
            return [first_depth] + remaining_depths
        except Exception as e:
            # Fall back to sequential processing
            self._logger.warning(f"Batch processing failed, falling back to sequential: {e}")
            depths = [first_depth]
            for frame in frames[1:]:
                depths.append(self.estimate_depth(frame))
            return depths

    def switch_model(self, model_type: str | DepthModelType) -> bool:
        """Switch to a different model.

        Args:
            model_type: Model type to switch to.

        Returns:
            True if switch was successful, False otherwise.
        """
        if isinstance(model_type, str):
            model_type = DepthModelType.from_string(model_type)

        try:
            self._get_estimator(model_type)
            self._active_model = model_type
            self._logger.info(f"Switched to model: {model_type.value}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to switch to model {model_type.value}: {e}")
            return False

    def get_available_models(self) -> list[DepthModelType]:
        """Get list of available model types.

        Returns:
            List of model types that are available (successfully loaded).
        """
        return list(self._estimators.keys())

    def preload_models(self, models: list[str | DepthModelType] | None = None) -> dict[str, bool]:
        """Preload specified models or all models in fallback chain.

        Args:
            models: List of models to preload. If None, preloads fallback chain.

        Returns:
            Dictionary mapping model names to load success status.
        """
        if models is None:
            models = self.config.fallback_chain
        else:
            models = [DepthModelType.from_string(m) if isinstance(m, str) else m for m in models]

        results: dict[str, bool] = {}

        for model_type in models:
            try:
                self._get_estimator(model_type)
                results[model_type.value] = True
                self._logger.info(f"Preloaded model: {model_type.value}")
            except Exception as e:
                results[model_type.value] = False
                self._logger.warning(f"Failed to preload {model_type.value}: {e}")

        return results

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        """Estimate depth from a single frame (callable interface)."""
        return self.estimate_depth(frame)

    def __enter__(self) -> DepthModelSelector:
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
        for model_type, estimator in self._estimators.items():
            try:
                if hasattr(estimator, "close"):
                    estimator.close()
            except Exception as e:
                self._logger.warning(f"Error closing {model_type.value}: {e}")

        self._estimators.clear()
        self._active_model = None
        self._logger.debug("DepthModelSelector resources released")


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_model_selector(
    primary_model: str = "adabins_nyu",
    fallback_model: str = "midas_small",
    device: str = "auto",
    **kwargs: Any,
) -> DepthModelSelector:
    """Create a depth model selector with the specified configuration.

    Args:
        primary_model: Primary model type.
        fallback_model: Fallback model type.
        device: Device for inference.
        **kwargs: Additional DepthModelConfig field values.

    Returns:
        Configured DepthModelSelector instance.
    """
    config = DepthModelConfig(
        primary_model=DepthModelType.from_string(primary_model),
        fallback_model=DepthModelType.from_string(fallback_model),
        device=device,
        **kwargs,
    )
    return DepthModelSelector(config=config)


def estimate_depth_auto(
    image: np.ndarray,
    primary_model: str = "adabins_nyu",
    fallback_model: str = "midas_small",
    device: str = "auto",
) -> np.ndarray:
    """Estimate depth with automatic model selection (convenience function).

    Args:
        image: Input image as numpy array (H, W, C) in RGB format.
        primary_model: Primary model type.
        fallback_model: Fallback model type.
        device: Device for inference.

    Returns:
        Depth map as numpy array.
    """
    with create_model_selector(
        primary_model=primary_model,
        fallback_model=fallback_model,
        device=device,
    ) as selector:
        return selector.estimate_depth(image)


# Module-level exports
__all__ = [
    # Classes
    "DepthModelSelector",
    "DepthModelConfig",
    "DepthModelType",
    "SceneType",
    # Exceptions
    "ModelLoadError",
    "ModelInferenceError",
    # Functions
    "create_model_selector",
    "estimate_depth_auto",
    # Constants
    "_DEFAULT_MODEL_LOAD_TIMEOUT",
    "_DEFAULT_SCENE_CONFIDENCE_THRESHOLD",
]
