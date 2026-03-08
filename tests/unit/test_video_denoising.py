"""Unit tests for video denoising module.

Tests cover:
- Configuration classes
- Exception handling
- FastDVDNet denoiser
- BasicVSR++ denoiser
- VideoDenoiserSelector
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from video2d3d.denoising import (
    BasicVSRPlusPlusConfig,
    DenoiserModelType,
    FastDVDNetConfig,
    InferenceError,
    ModelLoadError,
    VideoDenoiserConfig,
    VideoDenoiserSelector,
    VideoDenoisingError,
    create_video_denoiser,
    denoise_frames_auto,
)
from video2d3d.denoising.basicvsr_plusplus import BasicVSRPlusPlusModel
from video2d3d.denoising.fastdvdnet import FastDVDNetModel


class TestDenoiserModelType:
    """Tests for DenoiserModelType enum."""

    def test_from_string_valid_names(self) -> None:
        """Test conversion from string to enum for valid names."""
        assert DenoiserModelType.from_string("fastdvdnet") == DenoiserModelType.FASTDVDNET
        assert DenoiserModelType.from_string("FastDVDNet") == DenoiserModelType.FASTDVDNET
        assert DenoiserModelType.from_string("FASTDVDNET") == DenoiserModelType.FASTDVDNET
        assert DenoiserModelType.from_string("fast-dvdnet") == DenoiserModelType.FASTDVDNET
        assert (
            DenoiserModelType.from_string("basicvsr_plusplus")
            == DenoiserModelType.BASICVSR_PLUSPLUS
        )
        assert DenoiserModelType.from_string("basicvsr++") == DenoiserModelType.BASICVSR_PLUSPLUS
        assert DenoiserModelType.from_string("none") == DenoiserModelType.NONE

    def test_from_string_invalid_name(self) -> None:
        """Test that invalid model names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown denoising model"):
            DenoiserModelType.from_string("invalid_model")

    def test_is_enabled(self) -> None:
        """Test is_enabled property."""
        assert DenoiserModelType.FASTDVDNET.is_enabled is True
        assert DenoiserModelType.NONE.is_enabled is False

    def test_requires_temporal_context(self) -> None:
        """Test requires_temporal_context property."""
        assert DenoiserModelType.FASTDVDNET.requires_temporal_context is True
        assert DenoiserModelType.BASICVSR_PLUSPLUS.requires_temporal_context is True
        assert DenoiserModelType.NONE.requires_temporal_context is False


class TestFastDVDNetConfig:
    """Tests for FastDVDNetConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = FastDVDNetConfig()
        assert config.num_input_frames == 5
        assert config.noise_level == 30.0
        assert config.noise_level_mode == "blind"
        assert config.auto_download is True
        assert config.pretrained_model is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = FastDVDNetConfig(
            num_input_frames=7,
            noise_level=50.0,
            noise_level_mode="fixed",
        )
        assert config.num_input_frames == 7
        assert config.noise_level == 50.0
        assert config.noise_level_mode == "fixed"

    def test_invalid_num_frames(self) -> None:
        """Test that invalid num_input_frames raises ValueError."""
        with pytest.raises(ValueError, match="num_input_frames must be >= 1"):
            FastDVDNetConfig(num_input_frames=0)

    def test_invalid_noise_level(self) -> None:
        """Test that invalid noise_level raises ValueError."""
        with pytest.raises(ValueError, match="noise_level must be positive"):
            FastDVDNetConfig(noise_level=0)

    def test_invalid_noise_level_mode(self) -> None:
        """Test that invalid noise_level_mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid noise_level_mode"):
            FastDVDNetConfig(noise_level_mode="invalid")

    def test_path_conversion(self) -> None:
        """Test that pretrained_model string is converted to Path."""
        config = FastDVDNetConfig(pretrained_model="/path/to/model.pt")
        assert isinstance(config.pretrained_model, Path)


class TestBasicVSRPlusPlusConfig:
    """Tests for BasicVSRPlusPlusConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BasicVSRPlusPlusConfig()
        assert config.num_input_frames == 15
        assert config.scale == 1
        assert config.auto_download is True
        assert config.use_spynet is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BasicVSRPlusPlusConfig(
            num_input_frames=30,
            scale=4,
            use_spynet=False,
        )
        assert config.num_input_frames == 30
        assert config.scale == 4
        assert config.use_spynet is False

    def test_invalid_num_frames(self) -> None:
        """Test that invalid num_input_frames raises ValueError."""
        with pytest.raises(ValueError, match="num_input_frames must be >= 1"):
            BasicVSRPlusPlusConfig(num_input_frames=0)

    def test_invalid_scale(self) -> None:
        """Test that invalid scale raises ValueError."""
        with pytest.raises(ValueError, match="scale must be >= 1"):
            BasicVSRPlusPlusConfig(scale=0)


class TestVideoDenoiserConfig:
    """Tests for VideoDenoiserConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = VideoDenoiserConfig()
        assert config.enabled is False
        assert config.model_type == DenoiserModelType.FASTDVDNET
        assert config.enable_fallback is True
        assert config.batch_size == 4

    def test_from_string_model_type(self) -> None:
        """Test that model_type string is converted to enum."""
        config = VideoDenoiserConfig(model_type="basicvsr_plusplus")
        assert config.model_type == DenoiserModelType.BASICVSR_PLUSPLUS

    def test_effective_model_when_disabled(self) -> None:
        """Test that effective_model returns NONE when disabled."""
        config = VideoDenoiserConfig(enabled=False, model_type=DenoiserModelType.FASTDVDNET)
        assert config.effective_model == DenoiserModelType.NONE

    def test_effective_model_when_enabled(self) -> None:
        """Test that effective_model returns configured model when enabled."""
        config = VideoDenoiserConfig(enabled=True, model_type=DenoiserModelType.FASTDVDNET)
        assert config.effective_model == DenoiserModelType.FASTDVDNET

    def test_invalid_output_dtype(self) -> None:
        """Test that invalid output_dtype raises ValueError."""
        with pytest.raises(ValueError, match="Invalid output_dtype"):
            VideoDenoiserConfig(output_dtype="invalid")


class TestFastDVDNetModel:
    """Tests for FastDVDNetModel neural network."""

    def test_model_creation(self) -> None:
        """Test model can be created."""
        model = FastDVDNetModel(num_input_frames=5)
        assert model.num_input_frames == 5
        assert model.num_features == 64

    def test_forward_pass_shape(self) -> None:
        """Test forward pass output shape."""
        import torch

        model = FastDVDNetModel(num_input_frames=5)
        model.eval()

        # Input: (B, T*C, H, W) where T=5, C=3
        x = torch.randn(1, 5 * 3, 64, 64)
        with torch.no_grad():
            output = model(x)

        # Output: (B, 3, H, W)
        assert output.shape == (1, 3, 64, 64)


class TestBasicVSRPlusPlusModel:
    """Tests for BasicVSRPlusPlusModel neural network."""

    def test_model_creation(self) -> None:
        """Test model can be created."""
        model = BasicVSRPlusPlusModel(num_feat=64, num_block=7)
        assert model.num_feat == 64

    def test_forward_pass_shape(self) -> None:
        """Test forward pass output shape."""
        import torch

        model = BasicVSRPlusPlusModel(num_feat=32, num_block=3)
        model.eval()

        # Input: (B, T, C, H, W)
        x = torch.randn(1, 3, 3, 32, 32)
        with torch.no_grad():
            output = model(x)

        # Output: (B, T, C, H, W)
        assert output.shape == (1, 3, 3, 32, 32)


class TestVideoDenoiserSelector:
    """Tests for VideoDenoiserSelector."""

    @pytest.fixture
    def sample_frames(self) -> list[np.ndarray]:
        """Create sample test frames."""
        np.random.seed(42)
        return [(np.random.rand(64, 64, 3) * 255).astype(np.uint8) for _ in range(10)]

    def test_selector_creation_default(self) -> None:
        """Test selector creation with defaults."""
        selector = VideoDenoiserSelector()
        assert selector.config is not None
        assert selector.is_enabled is False  # Disabled by default

    def test_selector_creation_with_config(self) -> None:
        """Test selector creation with custom config."""
        config = VideoDenoiserConfig(
            enabled=True,
            model_type=DenoiserModelType.FASTDVDNET,
        )
        selector = VideoDenoiserSelector(config=config)
        assert selector.is_enabled is True

    def test_denoise_frames_disabled(self, sample_frames: list[np.ndarray]) -> None:
        """Test that disabled denoiser returns frames unchanged."""
        config = VideoDenoiserConfig(enabled=False)
        selector = VideoDenoiserSelector(config=config)

        result = selector.denoise_frames(sample_frames)
        assert len(result) == len(sample_frames)
        # Frames should be unchanged
        for _i, (original, denoised) in enumerate(zip(sample_frames, result)):
            np.testing.assert_array_equal(original, denoised)

    def test_denoise_frames_empty_input(self) -> None:
        """Test that empty input returns empty output."""
        selector = VideoDenoiserSelector()
        result = selector.denoise_frames([])
        assert result == []

    def test_context_manager(self) -> None:
        """Test context manager usage."""
        config = VideoDenoiserConfig(enabled=False)
        with VideoDenoiserSelector(config=config) as selector:
            assert selector is not None

    def test_switch_model(self) -> None:
        """Test model switching."""
        selector = VideoDenoiserSelector()
        success = selector.switch_model(DenoiserModelType.FASTDVDNET)
        assert success is True


class TestExceptions:
    """Tests for exception classes."""

    def test_video_denoising_error(self) -> None:
        """Test VideoDenoisingError creation."""
        error = VideoDenoisingError(
            "Test error",
            model_name="test_model",
            device="cuda",
        )
        assert str(error) == "Test error"
        assert error.model_name == "test_model"
        assert error.device == "cuda"

    def test_model_load_error(self) -> None:
        """Test ModelLoadError creation."""
        original = ValueError("Original error")
        error = ModelLoadError(
            "Failed to load",
            model_name="test",
            original_exception=original,
        )
        assert error.original_exception == original

    def test_inference_error(self) -> None:
        """Test InferenceError creation."""
        error = InferenceError(
            "Inference failed",
            model_name="test",
            device="cpu",
        )
        assert "Inference failed" in str(error)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_video_denoiser(self) -> None:
        """Test create_video_denoiser function."""
        denoiser = create_video_denoiser(
            model_type="fastdvdnet",
            enabled=False,
        )
        assert isinstance(denoiser, VideoDenoiserSelector)
        assert denoiser.config.enabled is False

    def test_denoise_frames_auto(self) -> None:
        """Test denoise_frames_auto function."""
        np.random.seed(42)
        frames = [(np.random.rand(32, 32, 3) * 255).astype(np.uint8) for _ in range(5)]
        result = denoise_frames_auto(frames, model_type="none")
        assert len(result) == len(frames)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
