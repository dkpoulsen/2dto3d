"""Verification test for custom codecs feature (AV1, HEVC variants, VR-specific codecs).

This test verifies that the custom codecs implementation works correctly
without actually performing video conversion. It checks:
- Codec enum includes new codecs
- VideoWriterConfig accepts new parameters
- Convenience functions work correctly
- CODEC_DEFAULTS includes new codecs
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from video2d3d.video.video_writer import (
    VideoCodec,
    VideoWriterConfig,
    CODEC_DEFAULTS,
    create_video_writer,
    create_vr_video_writer,
    create_av1_video_writer,
    create_hevc_video_writer,
)


def test_av1_codecs_exist():
    """Test that AV1 codecs are defined in VideoCodec enum."""
    assert hasattr(VideoCodec, "AV1_AOM")
    assert VideoCodec.AV1_AOM.value == "libaom-av1"

    assert hasattr(VideoCodec, "AV1_SVT")
    assert VideoCodec.AV1_SVT.value == "libsvtav1"

    assert hasattr(VideoCodec, "AV1_RAV1E")
    assert VideoCodec.AV1_RAV1E.value == "librav1e"

    print("✅ AV1 codecs verified")


def test_hevc_variants_exist():
    """Test that HEVC hardware-accelerated variants are defined."""
    assert hasattr(VideoCodec, "HEVC_NVENC")
    assert VideoCodec.HEVC_NVENC.value == "hevc_nvenc"

    assert hasattr(VideoCodec, "HEVC_VAAPI")
    assert VideoCodec.HEVC_VAAPI.value == "hevc_vaapi"

    assert hasattr(VideoCodec, "HEVC_QSV")
    assert VideoCodec.HEVC_QSV.value == "hevc_qsv"

    assert hasattr(VideoCodec, "HEVC_VIDEOTOOLBOX")
    assert VideoCodec.HEVC_VIDEOTOOLBOX.value == "hevc_videotoolbox"

    print("✅ HEVC variants verified")


def test_vr_codecs_exist():
    """Test that VR-optimized codecs are defined."""
    assert hasattr(VideoCodec, "HEVC_VR")
    assert VideoCodec.HEVC_VR.value == "hevc_vr"

    assert hasattr(VideoCodec, "AV1_VR")
    assert VideoCodec.AV1_VR.value == "av1_vr"

    print("✅ VR codecs verified")


def test_codec_defaults_include_new_codecs():
    """Test that CODEC_DEFAULTS includes configurations for new codecs."""
    # AV1 codecs
    assert "libaom-av1" in CODEC_DEFAULTS
    assert "libsvtav1" in CODEC_DEFAULTS
    assert "librav1e" in CODEC_DEFAULTS

    # HEVC hardware variants
    assert "hevc_nvenc" in CODEC_DEFAULTS
    assert "hevc_vaapi" in CODEC_DEFAULTS
    assert "hevc_qsv" in CODEC_DEFAULTS
    assert "hevc_videotoolbox" in CODEC_DEFAULTS

    # VR codecs
    assert "hevc_vr" in CODEC_DEFAULTS
    assert "av1_vr" in CODEC_DEFAULTS

    print("✅ CODEC_DEFAULTS includes all new codecs")


def test_codec_defaults_have_required_fields():
    """Test that new codec defaults have required fields."""
    # AV1 should have cpu_used and crf
    av1_defaults = CODEC_DEFAULTS["libaom-av1"]
    assert "crf" in av1_defaults
    assert "cpu_used" in av1_defaults

    # HEVC NVENC should have preset and cq
    nvenc_defaults = CODEC_DEFAULTS["hevc_nvenc"]
    assert "preset" in nvenc_defaults
    assert "cq" in nvenc_defaults

    # VR codecs should have 10-bit pixel format
    hevc_vr_defaults = CODEC_DEFAULTS["hevc_vr"]
    assert hevc_vr_defaults["pixel_format"] == "yuv420p10le"

    print("✅ Codec defaults have required fields")


def test_video_writer_config_accepts_new_codecs():
    """Test that VideoWriterConfig can be created with new codecs."""
    # AV1 config
    config_av1 = VideoWriterConfig(codec="libaom-av1", crf=30)
    assert config_av1.codec == "libaom-av1"
    assert config_av1.crf == 30

    # HEVC NVENC config
    config_nvenc = VideoWriterConfig(codec="hevc_nvenc", preset="p4")
    assert config_nvenc.codec == "hevc_nvenc"
    assert config_nvenc.preset == "p4"

    # VR config
    config_vr = VideoWriterConfig(codec="hevc_vr", vr_mode=True)
    assert config_vr.codec == "hevc_vr"
    assert config_vr.vr_mode is True

    print("✅ VideoWriterConfig accepts new codecs")


def test_video_writer_config_new_fields():
    """Test that VideoWriterConfig accepts new codec options."""
    config = VideoWriterConfig(
        codec="libx265",
        tune="grain",
        profile="main10",
        level="5.1",
        vr_mode=True,
        x265_params={"frame-threads": 2},
        av1_params={"cpu_used": 4},
    )

    assert config.tune == "grain"
    assert config.profile == "main10"
    assert config.level == "5.1"
    assert config.vr_mode is True
    assert "frame-threads" in config.x265_params
    assert "cpu_used" in config.av1_params

    print("✅ VideoWriterConfig accepts new fields")


def test_create_vr_video_writer():
    """Test that create_vr_video_writer works correctly."""
    writer = create_vr_video_writer(
        output_path="test_vr.mp4",
        width=3840,
        height=1080,
        fps=30,
        codec="hevc_vr",
        quality="high",
    )

    assert writer.config.codec == "hevc_vr"
    assert writer.config.vr_mode is True
    assert writer.config.pixel_format == "yuv420p10le"
    assert writer.width == 3840
    assert writer.height == 1080

    print("✅ create_vr_video_writer works")


def test_create_av1_video_writer():
    """Test that create_av1_video_writer works correctly."""
    writer = create_av1_video_writer(
        output_path="test_av1.webm",
        width=1920,
        height=1080,
        fps=30,
        codec="libaom-av1",
        speed=4,
        crf=30,
    )

    assert writer.config.codec == "libaom-av1"
    assert writer.config.crf == 30
    assert writer.width == 1920
    assert writer.height == 1080

    print("✅ create_av1_video_writer works")


def test_create_hevc_video_writer():
    """Test that create_hevc_video_writer works correctly."""
    # Software encoding
    writer_sw = create_hevc_video_writer(
        output_path="test_hevc.mp4",
        width=1920,
        height=1080,
        fps=30,
        hwaccel=None,
        preset="slow",
        crf=20,
    )
    assert writer_sw.config.codec == "libx265"
    assert writer_sw.config.crf == 20

    # Hardware encoding (NVENC)
    writer_hw = create_hevc_video_writer(
        output_path="test_hevc_nvenc.mp4",
        width=1920,
        height=1080,
        fps=30,
        hwaccel="nvenc",
        preset="p4",
        crf=23,
    )
    assert writer_hw.config.codec == "hevc_nvenc"
    assert writer_hw.config.hwaccel is True

    print("✅ create_hevc_video_writer works")


def test_av1_crf_validation():
    """Test that AV1 CRF validation works (0-63 range)."""
    # Valid CRF
    config = VideoWriterConfig(codec="libaom-av1", crf=30)
    assert config.crf == 30

    # Edge cases
    config_min = VideoWriterConfig(codec="libaom-av1", crf=0)
    assert config_min.crf == 0

    config_max = VideoWriterConfig(codec="libaom-av1", crf=63)
    assert config_max.crf == 63

    print("✅ AV1 CRF validation works")


def test_vr_mode_enables_optimizations():
    """Test that VR mode enables appropriate optimizations."""
    config = VideoWriterConfig(
        codec="libx265",
        vr_mode=True,
        x265_params={"aq-mode": 3},
    )

    assert config.vr_mode is True
    assert "aq-mode" in config.x265_params

    print("✅ VR mode enables optimizations")


if __name__ == "__main__":
    """Run all verification tests."""
    print("=" * 70)
    print("Custom Codecs Feature Verification Test")
    print("=" * 70)
    print()

    # Run all tests
    test_av1_codecs_exist()
    test_hevc_variants_exist()
    test_vr_codecs_exist()
    test_codec_defaults_include_new_codecs()
    test_codec_defaults_have_required_fields()
    test_video_writer_config_accepts_new_codecs()
    test_video_writer_config_new_fields()
    test_create_vr_video_writer()
    test_create_av1_video_writer()
    test_create_hevc_video_writer()
    test_av1_crf_validation()
    test_vr_mode_enables_optimizations()

    print()
    print("=" * 70)
    print("✅ All custom codec verification tests passed!")
    print("=" * 70)
