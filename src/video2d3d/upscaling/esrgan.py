"""Real-ESRGAN upscaler implementation using ONNX Runtime.

This module provides an implementation of the BaseUpscaler interface
using Real-ESRGAN models with ONNX Runtime for inference.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from video2d3d.upscaling.base import (
    BaseUpscaler,
    InferenceError,
    ModelLoadError,
    ModelNotFoundError,
)
from video2d3d.upscaling.config import UpscalerConfig
from video2d3d.utils.logger import get_logger


class RealESRGANUpscaler(BaseUpscaler):
    """Real-ESRGAN upscaler using ONNX Runtime.

    This class implements the BaseUpscaler interface using Real-ESRGAN
    models converted to ONNX format. It supports GPU and CPU inference
    with optional half-precision for faster processing.

    Example:
        ```python
        config = UpscalerConfig(
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=True,
            tile_size=512,
        )
        upscaler = RealESRGANUpscaler(config)
        upscaled = upscaler.upscale(image)
        ```
    """

    def __init__(self, config: UpscalerConfig) -> None:
        """Initialize the Real-ESRGAN upscaler.

        Args:
            config: Configuration for the upscaler.
        """
        self._logger = get_logger("realesrgan_upscaler")
        self._session = None
        self._providers = []
        super().__init__(config)

    def _load_model(self) -> None:
        """Load the ONNX model.

        Attempts to use GPU if available and configured, falls back to CPU.
        """
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError(
                "onnxruntime is required for Real-ESRGAN upscaling. "
                "Install it with: pip install onnxruntime-gpu (for GPU) "
                "or pip install onnxruntime (for CPU)"
            )

        model_path = self.config.get_model_file_path()

        # Check if model exists
        if not model_path.exists():
            # Try to download or provide helpful message
            self._logger.warning(f"Model file not found: {model_path}")
            self._logger.info(
                f"Please download the model from: {self._model_info.get('url', 'N/A')}"
            )
            raise ModelNotFoundError(model_path)

        # Configure providers based on settings
        self._providers = self._get_providers(ort)

        # Create inference session
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        # Set intra-op parallelism
        session_options.intra_op_num_threads = 4

        try:
            self._session = ort.InferenceSession(
                str(model_path),
                sess_options=session_options,
                providers=self._providers,
            )

            # Verify the session is using the expected provider
            actual_providers = self._session.get_providers()
            self._logger.info(f"ONNX Runtime session created with providers: {actual_providers}")

            # Check if we got GPU provider
            if self.config.use_gpu:
                gpu_provider = self._get_gpu_provider_name(ort)
                if gpu_provider and gpu_provider not in actual_providers:
                    self._logger.warning(
                        f"GPU provider {gpu_provider} not available, using {actual_providers[0]}"
                    )

            self._is_loaded = True

        except Exception as e:
            self._logger.error(f"Failed to load model: {e}")
            raise ModelLoadError(model_path, str(e)) from e

    def _get_providers(self, ort: Any) -> list:
        """Get the list of execution providers.

        Args:
            ort: The onnxruntime module.

        Returns:
            List of provider names in priority order.
        """
        available_providers = ort.get_available_providers()
        self._logger.debug(f"Available providers: {available_providers}")

        if self.config.use_gpu:
            # Try GPU providers in order of preference
            gpu_providers = [
                "CUDAExecutionProvider",
                "ROCMExecutionProvider",
                "TensorrtExecutionProvider",
            ]

            for provider in gpu_providers:
                if provider in available_providers:
                    return [provider, "CPUExecutionProvider"]

        # Fallback to CPU
        return ["CPUExecutionProvider"]

    def _get_gpu_provider_name(self, ort: Any) -> Optional[str]:
        """Get the name of the GPU provider being used.

        Args:
            ort: The onnxruntime module.

        Returns:
            GPU provider name or None.
        """
        if self.config.use_gpu:
            gpu_providers = [
                "CUDAExecutionProvider",
                "ROCMExecutionProvider",
                "TensorrtExecutionProvider",
            ]
            available = ort.get_available_providers()
            for provider in gpu_providers:
                if provider in available:
                    return provider
        return None

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for inference.

        Converts image to the format expected by the model:
        - Convert to float32
        - Normalize to [0, 1]
        - Convert HWC to NCHW format

        Args:
            image: Input image (H, W, C) in uint8.

        Returns:
            Preprocessed image (1, C, H, W) in float32.
        """
        # Ensure correct dtype
        if image.dtype != np.uint8:
            if image.dtype == np.float32 or image.dtype == np.float64:
                # Already normalized, denormalize first
                if image.max() <= 1.0:
                    image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)

        # Convert to float32 and normalize
        img = image.astype(np.float32) / 255.0

        # Convert HWC to CHW
        if img.ndim == 2:
            # Grayscale
            img = np.expand_dims(img, axis=0)
        else:
            img = np.transpose(img, (2, 0, 1))

        # Add batch dimension
        img = np.expand_dims(img, axis=0)

        return img

    def _postprocess_image(self, output: np.ndarray) -> np.ndarray:
        """Postprocess model output.

        Converts output back to image format:
        - Remove batch dimension
        - Convert NCHW to HWC
        - Clip and convert to uint8

        Args:
            output: Model output (1, C, H, W) in float32.

        Returns:
            Output image (H, W, C) in uint8.
        """
        # Remove batch dimension
        img = output.squeeze(0)

        # Convert CHW to HWC
        if img.ndim == 3:
            img = np.transpose(img, (1, 2, 0))

        # Clip values
        img = np.clip(img, 0, 1)

        # Convert to uint8
        img = (img * 255).astype(np.uint8)

        return img

    def _upscale_image(self, image: np.ndarray) -> np.ndarray:
        """Upscale a single image using the Real-ESRGAN model.

        Args:
            image: Input image (H, W, C) in uint8 RGB format.

        Returns:
            Upscaled image (H*scale, W*scale, C) in uint8 RGB format.

        Raises:
            InferenceError: If inference fails.
        """
        if self._session is None:
            raise InferenceError("Model session not initialized")

        try:
            # Get input name
            input_name = self._session.get_inputs()[0].name

            # Preprocess
            input_tensor = self._preprocess_image(image)

            # Run inference
            start_time = time.perf_counter()

            outputs = self._session.run(None, {input_name: input_tensor})

            inference_time = time.perf_counter() - start_time
            self._logger.debug(f"Inference time: {inference_time * 1000:.2f}ms")

            # Postprocess
            output_image = self._postprocess_image(outputs[0])

            return output_image

        except Exception as e:
            self._logger.error(f"Inference failed: {e}")
            raise InferenceError(str(e)) from e

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information.
        """
        info = {
            "name": self.model_name,
            "scale": self.scale,
            "is_loaded": self._is_loaded,
            "providers": self._providers,
        }

        if self._session is not None:
            # Get input/output shapes
            inputs = self._session.get_inputs()
            outputs = self._session.get_outputs()

            info["inputs"] = [{"name": i.name, "shape": i.shape} for i in inputs]
            info["outputs"] = [{"name": o.name, "shape": o.shape} for o in outputs]

        return info

    def cleanup(self) -> None:
        """Release model resources."""
        if self._session is not None:
            del self._session
            self._session = None
            self._is_loaded = False
            self._logger.info("Model resources released")

    def __del__(self) -> None:
        """Cleanup on destruction."""
        self.cleanup()


class DummyUpscaler(BaseUpscaler):
    """Dummy upscaler for testing without model files.

    This upscaler simply resizes the image using interpolation,
    useful for testing the pipeline without downloading models.
    """

    def __init__(self, config: UpscalerConfig) -> None:
        """Initialize the dummy upscaler.

        Args:
            config: Configuration for the upscaler.
        """
        self._logger = get_logger("dummy_upscaler")
        # Skip parent __init__ to avoid model loading
        self.config = config
        self._model = None
        self._is_loaded = True
        self._model_info = config.model_info

    def _load_model(self) -> None:
        """No model loading needed for dummy upscaler."""
        self._is_loaded = True

    def _upscale_image(self, image: np.ndarray) -> np.ndarray:
        """Upscale using simple interpolation.

        Args:
            image: Input image.

        Returns:
            Resized image.
        """
        import cv2

        h, w = image.shape[:2]
        new_h = h * self.scale
        new_w = w * self.scale

        # Use Lanczos interpolation for best quality
        upscaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        self._logger.debug(f"Dummy upscale: {h}x{w} -> {new_h}x{new_w}")

        return upscaled


def create_upscaler(config: UpscalerConfig, use_dummy: bool = False) -> BaseUpscaler:
    """Factory function to create an upscaler.

    Args:
        config: Configuration for the upscaler.
        use_dummy: If True, create a dummy upscaler for testing.

    Returns:
        Upscaler instance.
    """
    if use_dummy:
        return DummyUpscaler(config)
    return RealESRGANUpscaler(config)
