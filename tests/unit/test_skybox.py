"""Unit tests for skybox module.

Tests cover:
- Configuration validation
- Sky detection algorithms
- Depth processing
- Integration functions
"""

from __future__ import annotations

import pytest
import numpy as np

from video2d3d.skybox.config import (
    SkyDetectionMethod,
    SkyDepthMode,
    SkyboxConfig,
    ColorDetectionConfig,
    PositionDetectionConfig,
    EdgeDetectionConfig,
    SkyDepthConfig,
)
from video2d3d.skybox.detector import (
    SkyDetector,
    SkyDetectionResult,
    SkyDetectionError,
    create_sky_detector,
    detect_sky,
)
from video2d3d.skybox.processor import (
    SkyProcessor,
    SkyProcessingError,
    integrate_sky_depth,
    create_sky_depth_mask,
    blend_depth_at_boundary,
    create_sky_processor,
    process_sky_depth,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def blue_sky_image():
    """Create a synthetic image with blue sky at top."""
    h, w = 240, 320
    image = np.zeros((h, w, 3), dtype=np.uint8)

    # Top half: blue sky (RGB values for blue)
    image[: h // 2, :, 0] = 135  # R
    image[: h // 2, :, 1] = 206  # G
    image[: h // 2, :, 2] = 235  # B

    # Bottom half: green grass
    image[h // 2 :, :, 0] = 34  # R
    image[h // 2 :, :, 1] = 139  # G
    image[h // 2 :, :, 2] = 34  # B

    return image


@pytest.fixture
def gradient_sky_image():
    """Create an image with vertical gradient sky."""
    h, w = 240, 320
    image = np.zeros((h, w, 3), dtype=np.uint8)

    # Create gradient from dark blue to light blue
    for y in range(h // 2):
        intensity = int(135 + (y / (h // 2)) * 50)
        image[y, :, 0] = intensity
        image[y, :, 1] = intensity + 40
        image[y, :, 2] = intensity + 70

    # Bottom half: darker (ground)
    image[h // 2 :, :, :] = [50, 80, 50]

    return image


@pytest.fixture
def no_sky_image():
    """Create an image without sky (indoor scene)."""
    h, w = 240, 320
    image = np.zeros((h, w, 3), dtype=np.uint8)

    # Fill with indoor colors (walls, furniture)
    image[:, :, 0] = 100
    image[:, :, 1] = 80
    image[:, :, 2] = 60

    return image


@pytest.fixture
def sample_depth_map():
    """Create a sample depth map."""
    h, w = 240, 320
    depth = np.random.rand(h, w).astype(np.float32)
    # Make sky region have varying depth (simulating artifacts)
    depth[: h // 2, :] = np.random.rand(h // 2, w).astype(np.float32) * 0.5
    return depth


# ---------------------------------------------------------------------------
# Configuration Tests
# ---------------------------------------------------------------------------


class TestSkyboxConfig:
    """Tests for SkyboxConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SkyboxConfig()

        assert config.enabled is True
        assert config.detection_method == "combined"
        assert config.min_confidence == 0.3
        assert config.temporal_consistency is True
        assert config.smoothing_frames == 5

        # Sub-configs should be initialized
        assert config.color_config is not None
        assert config.position_config is not None
        assert config.edge_config is not None
        assert config.depth_config is not None

    def test_invalid_detection_method(self):
        """Test that invalid detection method raises error."""
        with pytest.raises(ValueError, match="Invalid detection_method"):
            SkyboxConfig(detection_method="invalid")

    def test_invalid_min_confidence(self):
        """Test that invalid min_confidence raises error."""
        with pytest.raises(ValueError, match="min_confidence"):
            SkyboxConfig(min_confidence=1.5)

        with pytest.raises(ValueError, match="min_confidence"):
            SkyboxConfig(min_confidence=-0.1)

    def test_custom_sub_configs(self):
        """Test providing custom sub-configurations."""
        color_config = ColorDetectionConfig(hue_min=180, hue_max=270)
        config = SkyboxConfig(color_config=color_config)

        assert config.color_config.hue_min == 180
        assert config.color_config.hue_max == 270

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "enabled": False,
            "detection_method": "color",
            "min_confidence": 0.5,
        }
        config = SkyboxConfig.from_dict(config_dict)

        assert config.enabled is False
        assert config.detection_method == "color"
        assert config.min_confidence == 0.5


class TestColorDetectionConfig:
    """Tests for ColorDetectionConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ColorDetectionConfig()

        assert 0 <= config.hue_min <= 360
        assert 0 <= config.hue_max <= 360
        assert 0 <= config.saturation_max <= 1
        assert 0 <= config.value_min <= 1

    def test_invalid_hue(self):
        """Test that invalid hue values raise error."""
        with pytest.raises(ValueError, match="hue_min"):
            ColorDetectionConfig(hue_min=400)

        with pytest.raises(ValueError, match="hue_max"):
            ColorDetectionConfig(hue_max=-10)

    def test_invalid_saturation(self):
        """Test that invalid saturation raises error."""
        with pytest.raises(ValueError, match="saturation_max"):
            ColorDetectionConfig(saturation_max=1.5)


class TestPositionDetectionConfig:
    """Tests for PositionDetectionConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PositionDetectionConfig()

        assert 0 <= config.sky_region_ratio <= 1
        assert 0 <= config.min_sky_coverage <= 1
        assert 0 <= config.max_sky_coverage <= 1

    def test_invalid_coverage_range(self):
        """Test that min > max coverage raises error."""
        with pytest.raises(ValueError, match="cannot exceed"):
            PositionDetectionConfig(min_sky_coverage=0.6, max_sky_coverage=0.4)


class TestSkyDepthConfig:
    """Tests for SkyDepthConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SkyDepthConfig()

        assert config.depth_mode == "maximum"
        assert 0 <= config.sky_depth_value <= 1
        assert config.boundary_blend_pixels >= 0

    def test_invalid_depth_mode(self):
        """Test that invalid depth mode raises error."""
        with pytest.raises(ValueError, match="Invalid depth_mode"):
            SkyDepthConfig(depth_mode="invalid")

    def test_invalid_depth_value(self):
        """Test that invalid depth value raises error."""
        with pytest.raises(ValueError, match="sky_depth_value"):
            SkyDepthConfig(sky_depth_value=1.5)


# ---------------------------------------------------------------------------
# Detector Tests
# ---------------------------------------------------------------------------


class TestSkyDetector:
    """Tests for SkyDetector class."""

    def test_detect_blue_sky(self, blue_sky_image):
        """Test detection of blue sky."""
        detector = SkyDetector()
        result = detector.detect(blue_sky_image)

        assert isinstance(result, SkyDetectionResult)
        assert result.sky_mask.shape == blue_sky_image.shape[:2]
        assert result.confidence > 0
        assert result.sky_coverage > 0

    def test_detect_gradient_sky(self, gradient_sky_image):
        """Test detection of gradient sky."""
        detector = SkyDetector()
        result = detector.detect(gradient_sky_image)

        assert isinstance(result, SkyDetectionResult)
        assert result.sky_mask.shape == gradient_sky_image.shape[:2]

    def test_detect_no_sky(self, no_sky_image):
        """Test detection in image without sky."""
        detector = SkyDetector()
        result = detector.detect(no_sky_image)

        assert isinstance(result, SkyDetectionResult)
        # Should have low confidence or low coverage
        assert result.confidence < 0.7 or result.sky_coverage < 0.3

    def test_invalid_input_type(self):
        """Test that invalid input type raises error."""
        detector = SkyDetector()

        with pytest.raises(SkyDetectionError, match="must be numpy array"):
            detector.detect([[1, 2], [3, 4]])  # type: ignore

    def test_invalid_input_dimensions(self):
        """Test that wrong dimensions raise error."""
        detector = SkyDetector()

        with pytest.raises(SkyDetectionError, match="must be 3D"):
            detector.detect(np.zeros((100, 100)))

    def test_color_detection_method(self, blue_sky_image):
        """Test color-only detection method."""
        config = SkyboxConfig(detection_method="color")
        detector = SkyDetector(config=config)
        result = detector.detect(blue_sky_image)

        assert "color_total_confidence" in result.method_results

    def test_position_detection_method(self, blue_sky_image):
        """Test position-only detection method."""
        config = SkyboxConfig(detection_method="position")
        detector = SkyDetector(config=config)
        result = detector.detect(blue_sky_image)

        assert "position_coverage" in result.method_results

    def test_edge_detection_method(self, blue_sky_image):
        """Test edge-only detection method."""
        config = SkyboxConfig(detection_method="edge")
        detector = SkyDetector(config=config)
        result = detector.detect(blue_sky_image)

        assert "edge_total_edges" in result.method_results

    def test_combined_detection_method(self, blue_sky_image):
        """Test combined detection method."""
        config = SkyboxConfig(detection_method="combined")
        detector = SkyDetector(config=config)
        result = detector.detect(blue_sky_image)

        # Should have results from all methods
        assert "color_total_confidence" in result.method_results
        assert "position_coverage" in result.method_results
        assert "edge_total_edges" in result.method_results

    def test_temporal_consistency(self, blue_sky_image):
        """Test temporal smoothing across frames."""
        config = SkyboxConfig(temporal_consistency=True, smoothing_frames=3)
        detector = SkyDetector(config=config)

        # Process same image multiple times
        result1 = detector.detect(blue_sky_image)
        result2 = detector.detect(blue_sky_image)
        result3 = detector.detect(blue_sky_image)

        # Results should be similar (temporal smoothing)
        assert np.allclose(result3.sky_mask, result2.sky_mask, atol=0.1)

    def test_reset_temporal_state(self, blue_sky_image):
        """Test resetting temporal state."""
        config = SkyboxConfig(temporal_consistency=True)
        detector = SkyDetector(config=config)

        detector.detect(blue_sky_image)
        detector.reset_temporal_state()

        # Should have no previous mask
        assert detector._previous_mask is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_sky_detector(self):
        """Test create_sky_detector function."""
        detector = create_sky_detector(detection_method="color")

        assert isinstance(detector, SkyDetector)
        assert detector.config.detection_method == "color"

    def test_detect_sky(self, blue_sky_image):
        """Test detect_sky convenience function."""
        result = detect_sky(blue_sky_image, method="combined")

        assert isinstance(result, SkyDetectionResult)


# ---------------------------------------------------------------------------
# Processor Tests
# ---------------------------------------------------------------------------


class TestSkyProcessor:
    """Tests for SkyProcessor class."""

    def test_process_depth_map(self, blue_sky_image, sample_depth_map):
        """Test processing depth map with sky detection."""
        detector = SkyDetector()
        sky_result = detector.detect(blue_sky_image)

        processor = SkyProcessor()
        adjusted = processor.process(sample_depth_map, sky_result)

        assert adjusted.shape == sample_depth_map.shape
        assert adjusted.dtype == np.float32
        # Sky region should have high depth values
        if sky_result.confidence > 0.3:
            sky_depth = adjusted[sky_result.sky_mask].mean()
            assert sky_depth > 0.5

    def test_process_with_low_confidence(self, no_sky_image, sample_depth_map):
        """Test processing when sky detection has low confidence."""
        detector = SkyDetector()
        sky_result = detector.detect(no_sky_image)

        processor = SkyProcessor()
        adjusted = processor.process(sample_depth_map, sky_result)

        # Should return original when confidence is low
        if sky_result.confidence < 0.3:
            np.testing.assert_array_almost_equal(adjusted, sample_depth_map, decimal=5)

    def test_invalid_depth_map_type(self, blue_sky_image):
        """Test that invalid depth map type raises error."""
        detector = SkyDetector()
        sky_result = detector.detect(blue_sky_image)

        processor = SkyProcessor()

        with pytest.raises(SkyProcessingError, match="must be numpy array"):
            processor.process([[1, 2], [3, 4]], sky_result)  # type: ignore

    def test_invalid_depth_map_dimensions(self, blue_sky_image):
        """Test that wrong dimensions raise error."""
        detector = SkyDetector()
        sky_result = detector.detect(blue_sky_image)

        processor = SkyProcessor()

        with pytest.raises(SkyProcessingError, match="must be 2D"):
            processor.process(np.zeros((100, 100, 3)), sky_result)

    def test_gradient_depth_mode(self, blue_sky_image, sample_depth_map):
        """Test gradient depth mode."""
        config = SkyboxConfig(depth_config=SkyDepthConfig(depth_mode="gradient"))
        detector = SkyDetector(config=config)
        sky_result = detector.detect(blue_sky_image)

        processor = SkyProcessor(config=config)
        adjusted = processor.process(sample_depth_map, sky_result)

        assert adjusted.shape == sample_depth_map.shape

    def test_boundary_blending(self, blue_sky_image, sample_depth_map):
        """Test boundary blending."""
        config = SkyboxConfig(depth_config=SkyDepthConfig(boundary_blend_pixels=20))
        detector = SkyDetector(config=config)
        sky_result = detector.detect(blue_sky_image)

        processor = SkyProcessor(config=config)
        adjusted = processor.process(sample_depth_map, sky_result)

        # Should have smooth transitions
        assert adjusted.shape == sample_depth_map.shape


class TestProcessorConvenienceFunctions:
    """Tests for processor convenience functions."""

    def test_integrate_sky_depth(self, blue_sky_image, sample_depth_map):
        """Test integrate_sky_depth function."""
        adjusted, result = integrate_sky_depth(sample_depth_map, blue_sky_image)

        assert adjusted.shape == sample_depth_map.shape
        assert isinstance(result, SkyDetectionResult)

    def test_create_sky_depth_mask(self):
        """Test create_sky_depth_mask function."""
        h, w = 100, 100
        sky_mask = np.zeros((h, w), dtype=bool)
        sky_mask[: h // 2, :] = True

        depth_mask = create_sky_depth_mask(
            sky_mask, horizon_y=h // 2, max_depth=1.0, gradient_strength=0.3
        )

        assert depth_mask.shape == (h, w)
        assert depth_mask.dtype == np.float32

    def test_blend_depth_at_boundary(self, sample_depth_map):
        """Test blend_depth_at_boundary function."""
        h, w = sample_depth_map.shape
        sky_mask = np.zeros((h, w), dtype=bool)
        sky_mask[: h // 2, :] = True

        result = blend_depth_at_boundary(sample_depth_map, sky_mask, sky_depth=1.0, blend_pixels=10)

        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32

    def test_create_sky_processor(self):
        """Test create_sky_processor function."""
        processor = create_sky_processor(detection_method="color")

        assert isinstance(processor, SkyProcessor)
        assert processor.config.detection_method == "color"

    def test_process_sky_depth(self, blue_sky_image, sample_depth_map):
        """Test process_sky_depth function."""
        result = process_sky_depth(blue_sky_image, sample_depth_map)

        assert result.shape == sample_depth_map.shape
        assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests for the complete skybox pipeline."""

    def test_full_pipeline(self, blue_sky_image, sample_depth_map):
        """Test the complete detection and processing pipeline."""
        # Detect sky
        detector = SkyDetector()
        sky_result = detector.detect(blue_sky_image)

        # Process depth
        processor = SkyProcessor()
        adjusted_depth = processor.process(sample_depth_map, sky_result)

        # Verify results
        assert adjusted_depth.shape == sample_depth_map.shape
        assert np.all(adjusted_depth >= 0)
        assert np.all(adjusted_depth <= 1)

    def test_pipeline_with_custom_config(self, blue_sky_image, sample_depth_map):
        """Test pipeline with custom configuration."""
        config = SkyboxConfig(
            detection_method="combined",
            min_confidence=0.2,
            depth_config=SkyDepthConfig(depth_mode="gradient", gradient_strength=0.3),
        )

        detector = SkyDetector(config=config)
        sky_result = detector.detect(blue_sky_image)

        processor = SkyProcessor(config=config)
        adjusted_depth = processor.process(sample_depth_map, sky_result)

        assert adjusted_depth.shape == sample_depth_map.shape

    def test_edge_cases(self):
        """Test edge cases."""
        # Very small image
        small_image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        small_depth = np.random.rand(10, 10).astype(np.float32)

        detector = SkyDetector()
        result = detector.detect(small_image)

        processor = SkyProcessor()
        adjusted = processor.process(small_depth, result)

        assert adjusted.shape == (10, 10)

    def test_different_image_sizes(self):
        """Test with different image sizes."""
        sizes = [(120, 160), (240, 320), (480, 640)]

        for h, w in sizes:
            image = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            depth = np.random.rand(h, w).astype(np.float32)

            adjusted, _ = integrate_sky_depth(depth, image)

            assert adjusted.shape == (h, w)


# ---------------------------------------------------------------------------
# Run Tests
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
