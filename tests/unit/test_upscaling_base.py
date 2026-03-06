"""Unit tests for the upscaler base classes."""

from __future__ import annotations

import pytest
import numpy as np

from video2d3d.upscaling.base import (
    BaseUpscaler,
    UpscaleResult,
    UpscalerError,
    ModelNotFoundError,
    ModelLoadError,
    InferenceError,
)
from video2d3d.upscaling.config import UpscalerConfig, ModelType


class TestUpscaleResult:
    """Tests for UpscaleResult dataclass."""

    def test_default_result(self):
        """Test default UpscaleResult values."""
        result = UpscaleResult()
        assert result.image is None
        assert result.original_size == (0, 0)
        assert result.output_size == (0, 0)
        assert result.scale == 1
        assert result.processing_time_ms == 0.0
        assert result.tiles_processed == 1
        assert result.model_name == ""
        assert result.success is True
        assert result.error_message is None

    def test_result_to_dict(self):
        """Test UpscaleResult serialization."""
        result = UpscaleResult(
            image=np.zeros((100, 100, 3), dtype=np.uint8),
            original_size=(50, 50),
            output_size=(200, 200),
            scale=4,
            processing_time_ms=150.5,
            tiles_processed=4,
            model_name="Real-ESRGAN x4plus",
            success=True,
        )
        d = result.to_dict()

        assert d["original_size"] == (50, 50)
        assert d["output_size"] == (200, 200)
        assert d["scale"] == 4
        assert d["processing_time_ms"] == 150.5
        assert d["tiles_processed"] == 4
        assert d["model_name"] == "Real-ESRGAN x4plus"
        assert d["success"] is True
        assert "image" not in d  # Image is not included in dict

    def test_failed_result(self):
        """Test failed UpscaleResult."""
        result = UpscaleResult(
            success=False,
            error_message="Out of memory",
        )
        assert result.success is False
        assert result.error_message == "Out of memory"


class TestUpscalerExceptions:
    """Tests for upscaler exception classes."""

    def test_upscaler_error(self):
        """Test base UpscalerError."""
        error = UpscalerError("Test error")
        assert str(error) == "Test error"

    def test_model_not_found_error(self, tmp_path):
        """Test ModelNotFoundError."""
        path = tmp_path / "model.onnx"
        error = ModelNotFoundError(path)
        assert "Model file not found" in str(error)
        assert str(path) in str(error)
        assert error.model_path == path

    def test_model_load_error(self, tmp_path):
        """Test ModelLoadError."""
        path = tmp_path / "model.onnx"
        error = ModelLoadError(path, "Invalid ONNX format")
        assert "Failed to load model" in str(error)
        assert "Invalid ONNX format" in str(error)
        assert error.model_path == path
        assert error.reason == "Invalid ONNX format"

    def test_inference_error(self):
        """Test InferenceError."""
        error = InferenceError("Shape mismatch")
        assert "Inference failed" in str(error)
        assert "Shape mismatch" in str(error)
        assert error.reason == "Shape mismatch"


class DummyUpscaler(BaseUpscaler):
    """Dummy upscaler for testing without model files."""

    def __init__(self, config: UpscalerConfig, fail_load: bool = False, fail_upscale: bool = False):
        self._fail_load = fail_load
        self._fail_upscale = fail_upscale
        super().__init__(config)

    def _load_model(self):
        if self._fail_load:
            raise ModelLoadError(self.config.get_model_file_path(), "Test failure")
        self._is_loaded = True

    def _upscale_image(self, image: np.ndarray) -> np.ndarray:
        if self._fail_upscale:
            raise InferenceError("Test inference failure")

        # Simple bilinear upsampling for testing
        import cv2

        h, w = image.shape[:2]
        new_h = h * self.scale
        new_w = w * self.scale
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)


class TestBaseUpscaler:
    """Tests for BaseUpscaler abstract class."""

    def test_upscaler_initialization(self):
        """Test upscaler initialization."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        assert upscaler.is_loaded is True
        assert upscaler.scale == 4
        assert "Real-ESRGAN" in upscaler.model_name

    def test_upscaler_upscale_simple(self):
        """Test simple image upscaling."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        # Create test image
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        assert upscaled.shape == (256, 256, 3)  # 4x scale
        assert upscaled.dtype == np.uint8

    def test_upscaler_upscale_with_info(self):
        """Test upscaling with result info."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        upscaled, result = upscaler.upscale(image, return_info=True)

        assert result.success is True
        assert result.original_size == (64, 64)
        assert result.output_size == (256, 256)
        assert result.scale == 4
        assert result.processing_time_ms > 0

    def test_upscaler_grayscale_input(self):
        """Test upscaling grayscale image (converted to RGB)."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        # Grayscale image
        image = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        # Should be converted to RGB
        assert upscaled.shape == (256, 256, 3)

    def test_upscaler_with_tiling(self):
        """Test upscaling with tile-based processing."""
        config = UpscalerConfig(
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            tile_size=32,  # Small tiles for testing
            tile_pad=8,
        )
        upscaler = DummyUpscaler(config)

        # Larger image to trigger tiling
        image = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        assert upscaled.shape == (512, 512, 3)

    def test_upscaler_batch_processing(self):
        """Test batch upscaling."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        images = [np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8) for _ in range(5)]

        results = upscaler.upscale_batch(images)

        assert len(results) == 5
        for result in results:
            assert result.success is True
            assert result.output_size == (128, 128)

    def test_upscaler_batch_with_progress(self):
        """Test batch upscaling with progress callback."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        images = [np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8) for _ in range(3)]

        progress_calls = []

        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        upscaler.upscale_batch(images, progress_callback=progress_callback)

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    def test_upscaler_model_not_loaded(self):
        """Test upscaling fails when model not loaded."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config, fail_load=True)

        image = np.zeros((64, 64, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError, match="Model is not loaded"):
            upscaler.upscale(image)

    def test_upscaler_invalid_input(self):
        """Test upscaler handles invalid input."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        # Empty image
        with pytest.raises(ValueError, match="empty"):
            upscaler.upscale(np.array([]))

        # Wrong dimensions
        with pytest.raises(ValueError, match="Expected 2D or 3D"):
            upscaler.upscale(np.zeros((10, 10, 10, 3)))

    def test_upscaler_inference_failure(self):
        """Test handling of inference failures."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config, fail_upscale=True)

        image = np.zeros((64, 64, 3), dtype=np.uint8)
        _, result = upscaler.upscale(image, return_info=True)

        assert result.success is False
        assert "inference failure" in result.error_message

    def test_upscaler_repr(self):
        """Test string representation."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)
        upscaler = DummyUpscaler(config)

        repr_str = repr(upscaler)
        assert "DummyUpscaler" in repr_str
        assert "scale=4" in repr_str
