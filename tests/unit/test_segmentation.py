"""Unit tests for the semantic segmentation module.

Tests cover:
- SemanticSegmenter configuration and initialization
- SegmentationProcessor mask processing
- DepthSegmentationIntegrator depth refinement
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_image() -> np.ndarray:
    """Create a sample test image."""
    np.random.seed(42)
    return np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)


@pytest.fixture
def sample_depth_map() -> np.ndarray:
    """Create a sample depth map."""
    np.random.seed(42)
    return np.random.rand(256, 256).astype(np.float32)


@pytest.fixture
def sample_masks() -> list[dict[str, Any]]:
    """Create sample segmentation masks."""
    np.random.seed(42)
    masks = []
    for i in range(3):
        mask = np.zeros((256, 256), dtype=bool)
        # Create random object region
        y, x = np.ogrid[:256, :256]
        center_y, center_x = 64 + i * 64, 128
        radius = 30 + i * 10
        mask[(y - center_y) ** 2 + (x - center_x) ** 2 <= radius**2] = True
        masks.append(
            {
                "segmentation": mask,
                "area": int(np.sum(mask)),
                "bbox": [center_x - radius, center_y - radius, radius * 2, radius * 2],
                "predicted_iou": 0.9 + np.random.rand() * 0.1,
                "stability_score": 0.85 + np.random.rand() * 0.15,
            }
        )
    return masks


# ---------------------------------------------------------------------------
# SAMConfig Tests
# ---------------------------------------------------------------------------


class TestSAMConfig:
    """Tests for SAMConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        from video2d3d.segmentation import SAMConfig, SAMModelType

        config = SAMConfig()

        assert config.model_type == SAMModelType.VIT_B
        assert config.device == "auto"
        assert config.checkpoint_path is None
        assert config.auto_download is True
        assert config.input_size == 1024
        assert config.use_fp16 is False

    def test_config_from_string(self) -> None:
        """Test configuration with string model type."""
        from video2d3d.segmentation import SAMConfig, SAMModelType

        config = SAMConfig(model_type="vit_h")

        assert config.model_type == SAMModelType.VIT_H

    def test_invalid_model_type(self) -> None:
        """Test that invalid model type raises error."""
        from video2d3d.segmentation import SAMConfig

        with pytest.raises(ValueError, match="Unknown SAM model name"):
            SAMConfig(model_type="invalid_model")


# ---------------------------------------------------------------------------
# SAMModelType Tests
# ---------------------------------------------------------------------------


class TestSAMModelType:
    """Tests for SAMModelType enum."""

    def test_from_string_vit_h(self) -> None:
        """Test parsing vit_h model type."""
        from video2d3d.segmentation import SAMModelType

        assert SAMModelType.from_string("vit_h") == SAMModelType.VIT_H
        assert SAMModelType.from_string("VIT_H") == SAMModelType.VIT_H
        assert SAMModelType.from_string("sam_vit_h") == SAMModelType.VIT_H

    def test_from_string_vit_l(self) -> None:
        """Test parsing vit_l model type."""
        from video2d3d.segmentation import SAMModelType

        assert SAMModelType.from_string("vit_l") == SAMModelType.VIT_L

    def test_from_string_vit_b(self) -> None:
        """Test parsing vit_b model type."""
        from video2d3d.segmentation import SAMModelType

        assert SAMModelType.from_string("vit_b") == SAMModelType.VIT_B
        assert SAMModelType.from_string("vit_base") == SAMModelType.VIT_B

    def test_checkpoint_url(self) -> None:
        """Test checkpoint URL property."""
        from video2d3d.segmentation import SAMModelType

        url = SAMModelType.VIT_B.checkpoint_url
        assert "sam_vit_b" in url
        assert url.endswith(".pth")


# ---------------------------------------------------------------------------
# SemanticSegmenter Tests
# ---------------------------------------------------------------------------


class TestSemanticSegmenter:
    """Tests for SemanticSegmenter class."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter()

        assert segmenter.config is not None
        assert not segmenter.is_loaded

    def test_initialization_with_config(self) -> None:
        """Test initialization with custom config."""
        from video2d3d.segmentation import SAMConfig, SAMModelType, SemanticSegmenter

        config = SAMConfig(model_type=SAMModelType.VIT_L, device="cpu")
        segmenter = SemanticSegmenter(config=config)

        assert segmenter.config.model_type == SAMModelType.VIT_L
        assert segmenter.config.device == "cpu"

    def test_initialization_with_string_model(self) -> None:
        """Test initialization with string model type."""
        from video2d3d.segmentation import SAMModelType, SemanticSegmenter

        segmenter = SemanticSegmenter(model_type="vit_h")

        assert segmenter.config.model_type == SAMModelType.VIT_H

    def test_segment_invalid_input_type(self) -> None:
        """Test that invalid input type raises error."""
        from video2d3d.segmentation import InferenceError, SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        segmenter._is_loaded = True
        segmenter._mask_generator = MagicMock()

        with pytest.raises(InferenceError, match="must be a numpy array"):
            segmenter.segment([[1, 2], [3, 4]])  # type: ignore

    def test_segment_invalid_dimensions(self) -> None:
        """Test that invalid dimensions raise error."""
        from video2d3d.segmentation import InferenceError, SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        segmenter._is_loaded = True
        segmenter._mask_generator = MagicMock()

        # 2D array instead of 3D
        with pytest.raises(InferenceError, match="must be 3D"):
            segmenter.segment(np.zeros((256, 256)))

    def test_extract_boundaries(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test boundary extraction from masks."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        boundaries = segmenter.extract_boundaries(sample_masks, (256, 256))

        assert boundaries.shape == (256, 256)
        assert boundaries.dtype == bool
        # Should have some boundary pixels
        assert np.sum(boundaries) > 0

    def test_create_combined_mask(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test combined mask creation."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        combined = segmenter.create_combined_mask(sample_masks, (256, 256))

        assert combined.shape == (256, 256)
        assert combined.dtype == np.int32
        # Should have multiple objects
        assert len(np.unique(combined)) > 1


# ---------------------------------------------------------------------------
# SegmentationProcessor Tests
# ---------------------------------------------------------------------------


class TestSegmentationProcessorConfig:
    """Tests for SegmentationProcessorConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        config = SegmentationProcessorConfig()

        assert config.min_mask_area == 100
        assert config.max_mask_area == 10000000
        assert config.enable_hole_filling is True
        assert config.enable_morphology is True

    def test_invalid_min_area(self) -> None:
        """Test validation of min_mask_area."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        with pytest.raises(ValueError, match="min_mask_area must be >= 0"):
            SegmentationProcessorConfig(min_mask_area=-1)

    def test_invalid_max_area(self) -> None:
        """Test validation of max_mask_area."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        with pytest.raises(ValueError, match="max_mask_area.*must be > min_mask_area"):
            SegmentationProcessorConfig(min_mask_area=100, max_mask_area=50)

    def test_invalid_overlap_threshold(self) -> None:
        """Test validation of overlap_threshold."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        with pytest.raises(ValueError, match="overlap_threshold must be in"):
            SegmentationProcessorConfig(overlap_threshold=1.5)


class TestSegmentationProcessor:
    """Tests for SegmentationProcessor class."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        from video2d3d.segmentation.processor import SegmentationProcessor

        processor = SegmentationProcessor()

        assert processor.config is not None

    def test_initialization_with_config(self) -> None:
        """Test initialization with config."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(min_mask_area=50)
        processor = SegmentationProcessor(config=config)

        assert processor.config.min_mask_area == 50

    def test_filter_by_area(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test filtering masks by area."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(
            min_mask_area=500,
            max_mask_area=5000,
        )
        processor = SegmentationProcessor(config=config)

        filtered = processor._filter_by_area(sample_masks)

        for mask in filtered:
            assert 500 <= mask["area"] <= 5000

    def test_fill_holes(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test hole filling in masks."""
        from video2d3d.segmentation.processor import SegmentationProcessor

        processor = SegmentationProcessor()

        # Add a mask with a hole
        mask_with_hole = sample_masks[0].copy()
        mask_with_hole["segmentation"] = mask_with_hole["segmentation"].copy()
        mask_with_hole["segmentation"][100:120, 100:120] = False

        filled = processor._fill_holes(mask_with_hole)

        assert "segmentation" in filled
        assert filled["segmentation"].dtype == bool

    def test_process_pipeline(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test full processing pipeline."""
        from video2d3d.segmentation.processor import SegmentationProcessor

        processor = SegmentationProcessor()
        processed = processor.process(sample_masks, (256, 256))

        assert isinstance(processed, list)
        # At least some masks should pass filtering

    def test_extract_boundaries(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test boundary extraction."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            BoundaryType,
        )

        processor = SegmentationProcessor()

        # Test different boundary types
        for boundary_type in [BoundaryType.INNER, BoundaryType.OUTER, BoundaryType.BOTH]:
            boundaries = processor.extract_boundaries(sample_masks, (256, 256), boundary_type)
            assert boundaries.shape == (256, 256)
            assert boundaries.dtype == bool

    def test_create_weight_map(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test weight map creation."""
        from video2d3d.segmentation.processor import SegmentationProcessor

        processor = SegmentationProcessor()
        weights = processor.create_weight_map(sample_masks, (256, 256))

        assert weights.shape == (256, 256)
        assert weights.dtype == np.float32
        assert np.all(weights >= 1.0)  # All weights should be >= 1


# ---------------------------------------------------------------------------
# DepthSegmentationIntegrator Tests
# ---------------------------------------------------------------------------


class TestIntegrationConfig:
    """Tests for IntegrationConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        config = IntegrationConfig()

        assert config.boundary_preservation == "edge_weighted"
        assert config.depth_refinement == "combined"
        assert config.smoothing_strength == 0.5
        assert config.boundary_sharpness == 1.5

    def test_invalid_smoothing_strength(self) -> None:
        """Test validation of smoothing_strength."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="smoothing_strength must be in"):
            IntegrationConfig(smoothing_strength=1.5)

    def test_invalid_boundary_preservation(self) -> None:
        """Test validation of boundary_preservation method."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="Invalid boundary_preservation"):
            IntegrationConfig(boundary_preservation="invalid")


class TestDepthSegmentationIntegrator:
    """Tests for DepthSegmentationIntegrator class."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()

        assert integrator.config is not None

    def test_initialization_with_config(self) -> None:
        """Test initialization with config."""
        from video2d3d.segmentation.integrator import (
            DepthSegmentationIntegrator,
            IntegrationConfig,
        )

        config = IntegrationConfig(smoothing_strength=0.8)
        integrator = DepthSegmentationIntegrator(config=config)

        assert integrator.config.smoothing_strength == 0.8

    def test_compute_boundary_weights(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test boundary weight computation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        weights = integrator.compute_boundary_weights(sample_masks, (256, 256))

        assert weights.shape == (256, 256)
        assert weights.dtype == np.float32
        assert np.all(weights >= 1.0)

    def test_refine_depth(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test depth refinement."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape
        assert refined.dtype == np.float32
        assert np.all(refined >= 0) and np.all(refined <= 1)

    def test_refine_depth_with_image(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
        sample_image: np.ndarray,
    ) -> None:
        """Test depth refinement with image for edge detection."""
        from video2d3d.segmentation.integrator import (
            DepthSegmentationIntegrator,
            IntegrationConfig,
        )

        config = IntegrationConfig(depth_refinement="edge_aware_filter")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks, sample_image)

        assert refined.shape == sample_depth_map.shape

    def test_separate_objects_3d(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test 3D object separation enhancement."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        separated = integrator.separate_objects_3d(sample_depth_map, sample_masks)

        assert separated.shape == sample_depth_map.shape
        assert separated.dtype == np.float32
        assert np.all(separated >= 0) and np.all(separated <= 1)

    def test_get_object_depth_layers(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test getting depth layers for objects."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        layers = integrator.get_object_depth_layers(sample_depth_map, sample_masks)

        assert len(layers) == len(sample_masks)
        # Should be sorted by depth
        depths = [depth for _, depth in layers]
        assert depths == sorted(depths)


# ---------------------------------------------------------------------------
# Convenience Function Tests
# ---------------------------------------------------------------------------


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_segmenter(self) -> None:
        """Test create_segmenter function."""
        from video2d3d.segmentation import SAMModelType, create_segmenter

        segmenter = create_segmenter(model_type="vit_b", device="cpu")

        assert segmenter.config.model_type == SAMModelType.VIT_B

    def test_create_segmentation_processor(self) -> None:
        """Test create_segmentation_processor function."""
        from video2d3d.segmentation.processor import create_segmentation_processor

        processor = create_segmentation_processor(min_mask_area=50)

        assert processor.config.min_mask_area == 50

    def test_create_integrator(self) -> None:
        """Test create_integrator function."""
        from video2d3d.segmentation.integrator import create_integrator

        integrator = create_integrator(smoothing_strength=0.7)

        assert integrator.config.smoothing_strength == 0.7

    def test_process_segmentation_masks(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test process_segmentation_masks function."""
        from video2d3d.segmentation.processor import process_segmentation_masks

        processed = process_segmentation_masks(
            sample_masks,
            (256, 256),
        )

        assert isinstance(processed, list)

    def test_refine_depth_with_segmentation(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test refine_depth_with_segmentation function."""
        from video2d3d.segmentation.integrator import refine_depth_with_segmentation

        refined = refine_depth_with_segmentation(
            sample_depth_map,
            sample_masks,
            smoothing=0.5,
            sharpen=1.5,
        )

        assert refined.shape == sample_depth_map.shape


# ---------------------------------------------------------------------------
# Edge Cases and Error Handling
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_masks_list(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test handling of empty masks list."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(sample_depth_map, [])

        assert refined.shape == sample_depth_map.shape

    def test_single_mask(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test handling of single mask."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(sample_depth_map, [sample_masks[0]])

        assert refined.shape == sample_depth_map.shape

    def test_empty_processor_result(self) -> None:
        """Test processor with empty input."""
        from video2d3d.segmentation.processor import SegmentationProcessor

        processor = SegmentationProcessor()
        result = processor.process([], (256, 256))

        assert result == []

    def test_constant_depth_map(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test with constant depth map."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        constant_depth = np.ones((256, 256), dtype=np.float32) * 0.5

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(constant_depth, sample_masks)

        # Should still return valid depth map
        assert refined.shape == constant_depth.shape
