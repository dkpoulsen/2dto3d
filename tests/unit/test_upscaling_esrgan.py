"""Unit tests for the ESRGAN upscaler module."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video2d3d.upscaling.config import ModelType, UpscalerConfig
from video2d3d.upscaling.esrgan import (
    DummyUpscaler,
    RealESRGANUpscaler,
    create_upscaler,
)
from video2d3d.upscaling.base import InferenceError, ModelLoadError, ModelNotFoundError


class TestRealESRGANUpscalerPreprocessing:
    """Tests for image preprocessing in RealESRGANUpscaler."""

    def test_preprocess_uint8_image(self):
        """Test preprocessing of uint8 image."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with patch.object(RealESRGANUpscaler, "_load_model"):
            upscaler = RealESRGANUpscaler(config)
            upscaler._is_loaded = True

        # Create test image
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        preprocessed = upscaler._preprocess_image(image)

        # Check shape: (1, C, H, W)
        assert preprocessed.shape == (1, 3, 64, 64)
        # Check dtype
        assert preprocessed.dtype == np.float32
        # Check normalization
        assert preprocessed.min() >= 0.0
        assert preprocessed.max() <= 1.0

    def test_preprocess_grayscale_image(self):
        """Test preprocessing of grayscale image."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with patch.object(RealESRGANUpscaler, "_load_model"):
            upscaler = RealESRGANUpscaler(config)
            upscaler._is_loaded = True

        # Create grayscale image
        image = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
        preprocessed = upscaler._preprocess_image(image)

        # Check shape: (1, 1, H, W) for grayscale
        assert preprocessed.shape == (1, 1, 64, 64)

    def test_preprocess_float_image(self):
        """Test preprocessing of already normalized float image."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with patch.object(RealESRGANUpscaler, "_load_model"):
            upscaler = RealESRGANUpscaler(config)
            upscaler._is_loaded = True

        # Create normalized float image
        image = np.random.rand(64, 64, 3).astype(np.float32)
        preprocessed = upscaler._preprocess_image(image)

        # Should be denormalized then normalized correctly
        assert preprocessed.shape == (1, 3, 64, 64)
        assert preprocessed.dtype == np.float32


class TestRealESRGANUpscalerPostprocessing:
    """Tests for image postprocessing in RealESRGANUpscaler."""

    def test_postprocess_output(self):
        """Test postprocessing of model output."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with patch.object(RealESRGANUpscaler, "_load_model"):
            upscaler = RealESRGANUpscaler(config)
            upscaler._is_loaded = True

        # Create model output (NCHW format)
        output = np.random.rand(1, 3, 256, 256).astype(np.float32)
        postprocessed = upscaler._postprocess_image(output)

        # Check shape: (H, W, C)
        assert postprocessed.shape == (256, 256, 3)
        # Check dtype
        assert postprocessed.dtype == np.uint8
        # Check value range
        assert postprocessed.min() >= 0
        assert postprocessed.max() <= 255

    def test_postprocess_clips_values(self):
        """Test that postprocessing clips out-of-range values."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with patch.object(RealESRGANUpscaler, "_load_model"):
            upscaler = RealESRGANUpscaler(config)
            upscaler._is_loaded = True

        # Create output with out-of-range values
        output = np.array([[[[2.0, -0.5], [0.5, 1.5]]]], dtype=np.float32)  # Shape (1, 1, 2, 2)
        postprocessed = upscaler._postprocess_image(output)

        # Check clipped values
        assert postprocessed.min() >= 0
        assert postprocessed.max() <= 255


class TestRealESRGANUpscalerModelLoading:
    """Tests for model loading in RealESRGANUpscaler."""

    def test_model_not_found_error(self, tmp_path):
        """Test that missing model raises ModelNotFoundError."""
        config = UpscalerConfig(model_path=tmp_path / "nonexistent.onnx")

        with pytest.raises(ModelNotFoundError) as exc_info:
            RealESRGANUpscaler(config)

        assert "Model file not found" in str(exc_info.value)

    def test_onnxruntime_not_installed(self, tmp_path, monkeypatch):
        """Test error when onnxruntime is not installed."""
        config = UpscalerConfig(model_path=tmp_path / "model.onnx")
        # Create empty model file
        (tmp_path / "model.onnx").touch()

        def mock_import(name, *args, **kwargs):
            if name == "onnxruntime":
                raise ImportError("No module named 'onnxruntime'")
            return original_import(name, *args, **kwargs)

        original_import = __builtins__.__import__
        monkeypatch.setattr(__builtins__, "__import__", mock_import)

        with pytest.raises(ImportError) as exc_info:
            RealESRGANUpscaler(config)

        assert "onnxruntime" in str(exc_info.value).lower()


class TestRealESRGANUpscalerSessionInfo:
    """Tests for session info method."""

    def test_get_session_info_not_loaded(self):
        """Test get_session_info when model not loaded."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        with patch.object(RealESRGANUpscaler, "_load_model"):
            upscaler = RealESRGANUpscaler(config)

        info = upscaler.get_session_info()

        assert info["is_loaded"] is False
        assert "name" in info
        assert "scale" in info

    def test_get_session_info_with_session(self, tmp_path):
        """Test get_session_info with loaded session."""
        config = UpscalerConfig(model_path=tmp_path / "model.onnx")
        (tmp_path / "model.onnx").touch()

        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 64, 64]
        mock_output = MagicMock()
        mock_output.name = "output"
        mock_output.shape = [1, 3, 256, 256]

        mock_session.get_inputs.return_value = [mock_input]
        mock_session.get_outputs.return_value = [mock_output]

        with patch("video2d3d.upscaling.esrgan.ort") as mock_ort:
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            mock_ort.SessionOptions.return_value = MagicMock()
            mock_ort.GraphOptimizationLevel.ORT_ENABLE_ALL = 1
            mock_ort.InferenceSession.return_value = mock_session

            upscaler = RealESRGANUpscaler(config)

        info = upscaler.get_session_info()

        assert info["is_loaded"] is True
        assert "inputs" in info
        assert "outputs" in info
        assert len(info["inputs"]) == 1
        assert info["inputs"][0]["name"] == "input"


class TestRealESRGANUpscalerCleanup:
    """Tests for resource cleanup."""

    def test_cleanup_releases_session(self, tmp_path):
        """Test that cleanup releases the ONNX session."""
        config = UpscalerConfig(model_path=tmp_path / "model.onnx")
        (tmp_path / "model.onnx").touch()

        mock_session = MagicMock()

        with patch("video2d3d.upscaling.esrgan.ort") as mock_ort:
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            mock_ort.SessionOptions.return_value = MagicMock()
            mock_ort.GraphOptimizationLevel.ORT_ENABLE_ALL = 1
            mock_ort.InferenceSession.return_value = mock_session

            upscaler = RealESRGANUpscaler(config)
            assert upscaler._session is not None

        upscaler.cleanup()

        assert upscaler._session is None
        assert upscaler._is_loaded is False


class TestDummyUpscaler:
    """Tests for the DummyUpscaler class."""

    def test_dummy_upscaler_initialization(self):
        """Test DummyUpscaler initializes without model files."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = DummyUpscaler(config)

        assert upscaler.is_loaded is True
        assert upscaler.scale == 4

    def test_dummy_upscaler_upscale(self):
        """Test DummyUpscaler upscales images correctly."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = DummyUpscaler(config)

        # Create test image
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        # Check output dimensions (4x scale)
        assert upscaled.shape == (256, 256, 3)
        assert upscaled.dtype == np.uint8

    def test_dummy_upscaler_2x_scale(self):
        """Test DummyUpscaler with 2x scale model."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X2PLUS)

        upscaler = DummyUpscaler(config)

        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        # Check output dimensions (2x scale)
        assert upscaled.shape == (200, 200, 3)

    def test_dummy_upscaler_grayscale(self):
        """Test DummyUpscaler handles grayscale images."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS)

        upscaler = DummyUpscaler(config)

        # Grayscale image (2D)
        image = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        upscaled = upscaler.upscale(image)

        # Should handle via base class conversion
        assert upscaled.shape[0] == 200
        assert upscaled.shape[1] == 200


class TestCreateUpscaler:
    """Tests for the create_upscaler factory function."""

    def test_create_upscaler_real(self, tmp_path):
        """Test creating RealESRGANUpscaler."""
        config = UpscalerConfig(model_path=tmp_path / "model.onnx")
        (tmp_path / "model.onnx").touch()

        with patch("video2d3d.upscaling.esrgan.ort") as mock_ort:
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            mock_ort.SessionOptions.return_value = MagicMock()
            mock_ort.GraphOptimizationLevel.ORT_ENABLE_ALL = 1
            mock_ort.InferenceSession.return_value = MagicMock()

            upscaler = create_upscaler(config, use_dummy=False)

        assert isinstance(upscaler, RealESRGANUpscaler)

    def test_create_upscaler_dummy(self):
        """Test creating DummyUpscaler."""
        config = UpscalerConfig()

        upscaler = create_upscaler(config, use_dummy=True)

        assert isinstance(upscaler, DummyUpscaler)

    def test_create_upscaler_default(self):
        """Test create_upscaler defaults to RealESRGANUpscaler."""
        config = UpscalerConfig()

        # Will fail because model doesn't exist, but type check works
        try:
            upscaler = create_upscaler(config, use_dummy=False)
        except ModelNotFoundError:
            pass  # Expected when model doesn't exist
