"""Unit tests for the upscaler configuration module."""

from __future__ import annotations

import pytest
from pathlib import Path

from video2d3d.upscaling.config import (
    ModelType,
    UpscalerConfig,
    get_model_info,
    get_model_scale,
    list_available_models,
    get_default_model_path,
)


class TestModelType:
    """Tests for ModelType enum."""

    def test_model_type_values(self):
        """Test that all expected model types exist."""
        assert ModelType.ESRGAN.value == "esrgan"
        assert ModelType.REAL_ESRGAN_X4PLUS.value == "realesrgan-x4plus"
        assert ModelType.REAL_ESRGAN_X4PLUS_ANIME.value == "realesrgan-x4plus-anime"
        assert ModelType.REAL_ESRGAN_X2PLUS.value == "realesrgan-x2plus"
        assert ModelType.REAL_ESRGAN_GENERAL_X4V3.value == "realesrgan-general-x4v3"

    def test_model_type_from_string(self):
        """Test creating ModelType from string."""
        model = ModelType("realesrgan-x4plus")
        assert model == ModelType.REAL_ESRGAN_X4PLUS

    def test_model_type_invalid_string(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            ModelType("invalid-model")


class TestGetModelInfo:
    """Tests for get_model_info function."""

    def test_get_model_info_valid(self):
        """Test getting info for valid model."""
        info = get_model_info(ModelType.REAL_ESRGAN_X4PLUS)
        assert info["name"] == "Real-ESRGAN x4plus"
        assert info["scale"] == 4
        assert "description" in info
        assert "onnx_file" in info

    def test_get_model_info_from_string(self):
        """Test getting info using string model type."""
        info = get_model_info("realesrgan-x4plus-anime")
        assert info["name"] == "Real-ESRGAN x4plus Anime"
        assert info["scale"] == 4

    def test_get_model_info_invalid(self):
        """Test that invalid model raises ValueError."""
        with pytest.raises(ValueError):
            get_model_info("nonexistent-model")

    def test_model_info_has_required_fields(self):
        """Test that all models have required info fields."""
        required_fields = [
            "name",
            "scale",
            "description",
            "onnx_file",
            "input_channels",
            "output_channels",
        ]

        for model_type in ModelType:
            info = get_model_info(model_type)
            for field in required_fields:
                assert field in info, f"Missing field {field} for {model_type}"


class TestGetModelScale:
    """Tests for get_model_scale function."""

    def test_get_scale_x4plus(self):
        """Test getting scale for 4x model."""
        assert get_model_scale(ModelType.REAL_ESRGAN_X4PLUS) == 4

    def test_get_scale_x2plus(self):
        """Test getting scale for 2x model."""
        assert get_model_scale(ModelType.REAL_ESRGAN_X2PLUS) == 2

    def test_get_scale_from_string(self):
        """Test getting scale using string model type."""
        assert get_model_scale("realesrgan-general-x4v3") == 4


class TestListAvailableModels:
    """Tests for list_available_models function."""

    def test_list_models(self):
        """Test that list returns all model types."""
        models = list_available_models()
        assert isinstance(models, list)
        assert len(models) == len(ModelType)
        assert "realesrgan-x4plus" in models
        assert "realesrgan-x2plus" in models


class TestGetDefaultModelPath:
    """Tests for get_default_model_path function."""

    def test_default_path(self, monkeypatch):
        """Test default path is returned when no env var set."""
        monkeypatch.delenv("VIDEO2D3D_MODELS_PATH", raising=False)
        path = get_default_model_path()
        assert isinstance(path, Path)
        assert "models" in str(path)
        assert "upscaling" in str(path)

    def test_custom_path_from_env(self, monkeypatch, tmp_path):
        """Test custom path from environment variable."""
        custom_path = str(tmp_path / "custom_models")
        monkeypatch.setenv("VIDEO2D3D_MODELS_PATH", custom_path)
        path = get_default_model_path()
        assert str(path) == custom_path


class TestUpscalerConfig:
    """Tests for UpscalerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = UpscalerConfig()
        assert config.enabled is False
        assert config.model_type == ModelType.REAL_ESRGAN_X4PLUS
        assert config.scale == 4
        assert config.use_gpu is True
        assert config.tile_size == 0
        assert config.tile_pad == 16
        assert config.half_precision is True
        assert config.denoise_strength == 0.5

    def test_config_with_model_type_string(self):
        """Test config accepts string model type."""
        config = UpscalerConfig(model_type="realesrgan-x2plus")
        assert config.model_type == ModelType.REAL_ESRGAN_X2PLUS
        assert config.scale == 2

    def test_config_custom_scale(self):
        """Test custom scale overrides model default."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS, scale=2)
        assert config.scale == 2

    def test_config_invalid_scale(self):
        """Test that invalid scale raises ValueError."""
        with pytest.raises(ValueError):
            UpscalerConfig(scale=3)

    def test_config_invalid_denoise_strength(self):
        """Test that invalid denoise strength raises ValueError."""
        with pytest.raises(ValueError):
            UpscalerConfig(denoise_strength=1.5)

        with pytest.raises(ValueError):
            UpscalerConfig(denoise_strength=-0.1)

    def test_config_invalid_tile_size(self):
        """Test that invalid tile size raises ValueError."""
        with pytest.raises(ValueError):
            UpscalerConfig(tile_size=-1)

        with pytest.raises(ValueError):
            UpscalerConfig(tile_size=32)  # Less than 64

    def test_config_to_dict(self):
        """Test config serialization to dict."""
        config = UpscalerConfig(
            enabled=True,
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            scale=4,
            use_gpu=False,
        )
        d = config.to_dict()

        assert d["enabled"] is True
        assert d["model_type"] == "realesrgan-x4plus"
        assert d["scale"] == 4
        assert d["use_gpu"] is False

    def test_config_from_dict(self):
        """Test config deserialization from dict."""
        d = {
            "enabled": True,
            "model_type": "realesrgan-x2plus",
            "scale": 2,
            "use_gpu": True,
            "tile_size": 512,
        }
        config = UpscalerConfig.from_dict(d)

        assert config.enabled is True
        assert config.model_type == ModelType.REAL_ESRGAN_X2PLUS
        assert config.scale == 2
        assert config.tile_size == 512

    def test_config_model_info_property(self):
        """Test model_info property returns correct info."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X4PLUS_ANIME)
        info = config.model_info

        assert info["name"] == "Real-ESRGAN x4plus Anime"
        assert info["scale"] == 4

    def test_config_effective_scale(self):
        """Test effective_scale property."""
        config = UpscalerConfig(model_type=ModelType.REAL_ESRGAN_X2PLUS)
        assert config.effective_scale == 2

        config_with_custom = UpscalerConfig(
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            scale=2,
        )
        assert config_with_custom.effective_scale == 2

    def test_config_model_path(self):
        """Test get_model_file_path returns correct path."""
        config = UpscalerConfig()
        path = config.get_model_file_path()

        assert isinstance(path, Path)
        assert path.name == "realesrgan-x4plus.onnx"

    def test_config_custom_model_path(self, tmp_path):
        """Test custom model path."""
        custom_path = tmp_path / "custom_model.onnx"
        config = UpscalerConfig(model_path=custom_path)

        assert config.get_model_file_path() == custom_path
