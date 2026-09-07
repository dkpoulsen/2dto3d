"""Base classes and interfaces for AI-based video upscaling.

This module provides the abstract base class for upscalers and common
data structures used across the upscaling module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np


@dataclass
class UpscaleResult:
    """Result of an upscaling operation.

    Attributes:
        image: The upscaled image as numpy array.
        original_size: Original image size (height, width).
        output_size: Output image size (height, width).
        scale: Scale factor used.
        processing_time_ms: Processing time in milliseconds.
        tiles_processed: Number of tiles processed (for tiled upscaling).
        model_name: Name of the model used.
        success: Whether the operation was successful.
        error_message: Error message if unsuccessful.
    """

    image: np.ndarray | None = None
    original_size: tuple[int, int] = (0, 0)
    output_size: tuple[int, int] = (0, 0)
    scale: int = 1
    processing_time_ms: float = 0.0
    tiles_processed: int = 1
    model_name: str = ""
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "original_size": self.original_size,
            "output_size": self.output_size,
            "scale": self.scale,
            "processing_time_ms": self.processing_time_ms,
            "tiles_processed": self.tiles_processed,
            "model_name": self.model_name,
            "success": self.success,
            "error_message": self.error_message,
        }


class BaseUpscaler(ABC):
    """Abstract base class for AI-based image upscalers.

    This class defines the interface that all upscaler implementations
    must follow. Implementations can use different backends (ONNX, PyTorch,
    TensorRT, etc.) but must provide the same interface.

    Example:
        ```python
        class MyUpscaler(BaseUpscaler):
            def __init__(self, config):
                super().__init__(config)
                # Initialize model

            def _load_model(self):
                # Load model from file
                pass

            def _upscale_image(self, image):
                # Run inference
                return upscaled_image
        ```
    """

    def __init__(self, config: UpscalerConfig) -> None:
        """Initialize the upscaler.

        Args:
            config: Configuration for the upscaler.
        """
        from video2d3d.utils.logger import get_logger

        self.config = config
        self._logger = get_logger("upscaler")
        self._model = None
        self._is_loaded = False
        self._model_info = config.model_info

        # Initialize model (a load failure defers the error to upscale())
        try:
            self._load_model()
        except ModelLoadError:
            self._is_loaded = False

    @abstractmethod
    def _load_model(self) -> None:
        """Load the upscaling model.

        This method must be implemented by subclasses to load
        the model from disk and prepare it for inference.
        """
        pass

    @abstractmethod
    def _upscale_image(self, image: np.ndarray) -> np.ndarray:
        """Upscale a single image.

        This method must be implemented by subclasses to perform
        the actual upscaling inference.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            Upscaled image as numpy array.
        """
        pass

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded and ready."""
        return self._is_loaded

    @property
    def model_name(self) -> str:
        """Get the name of the loaded model."""
        return self._model_info.get("name", "Unknown")

    @property
    def scale(self) -> int:
        """Get the scale factor of the model."""
        return self.config.effective_scale

    def upscale(
        self,
        image: np.ndarray,
        return_info: bool = False,
    ) -> np.ndarray | tuple[np.ndarray, UpscaleResult]:
        """Upscale an image.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.
            return_info: If True, return tuple of (image, result_info).

        Returns:
            Upscaled image, or tuple of (image, result_info) if return_info=True.

        Raises:
            RuntimeError: If model is not loaded.
            ValueError: If image format is invalid.
        """
        import time

        if not self._is_loaded:
            raise RuntimeError("Model is not loaded. Call _load_model() first.")

        # Validate input
        if image is None or image.size == 0:
            raise ValueError("Input image is empty")

        if image.ndim not in (2, 3):
            raise ValueError(f"Expected 2D or 3D array, got shape {image.shape}")

        # Convert grayscale to RGB if needed
        if image.ndim == 2:
            image = np.stack([image] * 3, axis=-1)

        # Ensure contiguous array
        if not image.flags["C_CONTIGUOUS"]:
            image = np.ascontiguousarray(image)

        start_time = time.perf_counter()
        original_size = (image.shape[0], image.shape[1])

        try:
            # Process image (with or without tiling)
            if self.config.tile_size > 0:
                result_image = self._upscale_with_tiling(image)
            else:
                result_image = self._upscale_image(image)

            processing_time = (time.perf_counter() - start_time) * 1000
            output_size = (result_image.shape[0], result_image.shape[1])

            result = UpscaleResult(
                image=result_image,
                original_size=original_size,
                output_size=output_size,
                scale=self.scale,
                processing_time_ms=processing_time,
                model_name=self.model_name,
                success=True,
            )

        except Exception as e:
            processing_time = (time.perf_counter() - start_time) * 1000
            self._logger.error(f"Upscaling failed: {e}")

            result = UpscaleResult(
                original_size=original_size,
                scale=self.scale,
                processing_time_ms=processing_time,
                model_name=self.model_name,
                success=False,
                error_message=str(e),
            )
            # Return original image on failure
            result_image = image

        if return_info:
            return result_image, result
        return result_image

    def _upscale_with_tiling(self, image: np.ndarray) -> np.ndarray:
        """Upscale an image using tile-based processing.

        This method splits the image into tiles, processes each tile,
        and stitches them back together. This is useful for large images
        that don't fit in GPU memory.

        Args:
            image: Input image as numpy array.

        Returns:
            Upscaled image as numpy array.
        """
        h, w = image.shape[:2]
        tile_size = self.config.tile_size
        tile_pad = self.config.tile_pad
        scale = self.scale

        # Calculate output dimensions
        out_h = h * scale
        out_w = w * scale
        channels = image.shape[2] if image.ndim == 3 else 1

        # Initialize output array
        output = np.zeros(
            (out_h, out_w, channels) if channels > 1 else (out_h, out_w), dtype=image.dtype
        )

        # Calculate number of tiles
        tiles_h = (h + tile_size - 1) // tile_size
        tiles_w = (w + tile_size - 1) // tile_size

        self._logger.debug(f"Processing {tiles_h}x{tiles_w} tiles for {h}x{w} image")

        for i in range(tiles_h):
            for j in range(tiles_w):
                # Calculate tile boundaries
                top = i * tile_size
                left = j * tile_size
                bottom = min(top + tile_size, h)
                right = min(left + tile_size, w)

                # Add padding
                top_pad = max(0, tile_pad) if top > 0 else 0
                left_pad = max(0, tile_pad) if left > 0 else 0
                bottom_pad = min(tile_pad, h - bottom) if bottom < h else 0
                right_pad = min(tile_pad, w - right) if right < w else 0

                # Extract tile with padding
                tile_top = max(0, top - top_pad)
                tile_left = max(0, left - left_pad)
                tile_bottom = min(h, bottom + bottom_pad)
                tile_right = min(w, right + right_pad)

                tile = image[tile_top:tile_bottom, tile_left:tile_right]

                # Upscale tile
                upscaled_tile = self._upscale_image(tile)

                # Calculate output boundaries (valid region within upscaled tile)
                out_top = (top - tile_top) * scale
                out_left = (left - tile_left) * scale
                out_bottom = (bottom - tile_top) * scale
                out_right = (right - tile_left) * scale

                # Calculate destination in output
                dst_top = top * scale
                dst_left = left * scale
                dst_bottom = bottom * scale
                dst_right = right * scale

                # Extract valid region from upscaled tile
                src_tile = upscaled_tile[out_top:out_bottom, out_left:out_right]

                # Place in output with blending for overlapping regions
                self._blend_tile(output, src_tile, dst_top, dst_left, dst_bottom, dst_right)

        return output

    def _blend_tile(
        self,
        output: np.ndarray,
        tile: np.ndarray,
        top: int,
        left: int,
        bottom: int,
        right: int,
    ) -> None:
        """Blend a tile into the output array.

        Uses simple averaging for overlapping regions.

        Args:
            output: Output array to blend into.
            tile: Tile to blend.
            top, left, bottom, right: Destination coordinates.
        """
        tile_h, tile_w = tile.shape[:2]
        out_h, out_w = output.shape[:2]

        # Ensure we don't go out of bounds
        if top >= out_h or left >= out_w:
            return

        # Adjust coordinates if needed
        actual_bottom = min(bottom, out_h)
        actual_right = min(right, out_w)
        actual_tile_h = actual_bottom - top
        actual_tile_w = actual_right - left

        if actual_tile_h <= 0 or actual_tile_w <= 0:
            return

        # Get the region to update
        tile_region = tile[:actual_tile_h, :actual_tile_w]
        output_region = output[top:actual_bottom, left:actual_right]

        # Simple blending (could be improved with feathering)
        # For first tile, just copy
        if np.all(output_region == 0):
            output[top:actual_bottom, left:actual_right] = tile_region
        else:
            # Average with existing content
            output[top:actual_bottom, left:actual_right] = (output_region + tile_region) / 2

    def upscale_batch(
        self,
        images: list[np.ndarray],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[UpscaleResult]:
        """Upscale multiple images.

        Args:
            images: List of input images.
            progress_callback: Optional callback(completed, total) for progress.

        Returns:
            List of UpscaleResult objects.
        """
        results = []
        total = len(images)

        for i, image in enumerate(images):
            _, result = self.upscale(image, return_info=True)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.model_name}, scale={self.scale})"


class UpscalerError(Exception):
    """Base exception for upscaler errors."""

    pass


class ModelNotFoundError(UpscalerError):
    """Raised when the model file cannot be found."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        super().__init__(f"Model file not found: {model_path}")


class ModelLoadError(UpscalerError):
    """Raised when the model fails to load."""

    def __init__(self, model_path: Path, reason: str = "") -> None:
        self.model_path = model_path
        self.reason = reason
        message = f"Failed to load model: {model_path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class InferenceError(UpscalerError):
    """Raised when inference fails."""

    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        message = "Inference failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


__all__ = [
    "UpscaleResult",
    "BaseUpscaler",
    "UpscalerError",
    "ModelNotFoundError",
    "ModelLoadError",
    "InferenceError",
]
