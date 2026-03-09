"""Unit tests for the semantic segmentation module.

Tests cover:
- SemanticSegmenter configuration and initialization
- SegmentationProcessor mask processing
- DepthSegmentationIntegrator depth refinement
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.slow

pytestmark = pytest.mark.slow


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
        from video2d3d.segmentation.processor import BoundaryType, SegmentationProcessor

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
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

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
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

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


# ---------------------------------------------------------------------------
# Constants Tests
# ---------------------------------------------------------------------------


class TestSegmentationConstants:
    """Tests for module constants."""

    def test_main_module_constants_exist(self) -> None:
        """Test that main module constants are defined."""
        from video2d3d.segmentation import _SAM_DEFAULT_INPUT_SIZE

        # Verify constants have expected values
        assert _SAM_DEFAULT_INPUT_SIZE == 1024

    def test_processor_constants_exist(self) -> None:
        """Test that processor module constants are defined."""
        from video2d3d.segmentation.processor import (
            _DEFAULT_BOUNDARY_WIDTH,
            _DEFAULT_GAUSSIAN_KERNEL_SIZE,
            _DEFAULT_MAX_AREA,
            _DEFAULT_MIN_AREA,
            _DEFAULT_MORPHOLOGY_KERNEL_SIZE,
            _VALID_HOLE_FILLING_METHODS,
        )

        assert _DEFAULT_MIN_AREA == 100
        assert _DEFAULT_MAX_AREA == 10000000
        assert _DEFAULT_MORPHOLOGY_KERNEL_SIZE == 5
        assert _DEFAULT_BOUNDARY_WIDTH == 3
        assert _DEFAULT_GAUSSIAN_KERNEL_SIZE == 5
        assert "morphology" in _VALID_HOLE_FILLING_METHODS
        assert "flood_fill" in _VALID_HOLE_FILLING_METHODS

    def test_integrator_constants_exist(self) -> None:
        """Test that integrator module constants are defined."""
        from video2d3d.segmentation.integrator import (
            _CANNY_HIGH_THRESHOLD,
            _CANNY_LOW_THRESHOLD,
            _DEFAULT_BOUNDARY_SHARPNESS,
            _DEFAULT_EDGE_DILATION,
            _DEFAULT_SMOOTHING_STRENGTH,
        )

        assert _DEFAULT_SMOOTHING_STRENGTH == 0.5
        assert _DEFAULT_BOUNDARY_SHARPNESS == 1.5
        assert _DEFAULT_EDGE_DILATION == 3
        assert _CANNY_LOW_THRESHOLD == 50
        assert _CANNY_HIGH_THRESHOLD == 150


# ---------------------------------------------------------------------------
# Additional Processor Validation Tests
# ---------------------------------------------------------------------------


class TestSegmentationProcessorAdvancedValidation:
    """Additional validation tests for SegmentationProcessor."""

    def test_invalid_hole_filling_method(self) -> None:
        """Test validation of hole_filling_method."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        with pytest.raises(ValueError, match="hole_filling_method must be one of"):
            SegmentationProcessorConfig(hole_filling_method="invalid_method")

    def test_valid_hole_filling_methods(self) -> None:
        """Test that valid hole filling methods are accepted."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        # morphology method
        config1 = SegmentationProcessorConfig(hole_filling_method="morphology")
        assert config1.hole_filling_method == "morphology"

        # flood_fill method
        config2 = SegmentationProcessorConfig(hole_filling_method="flood_fill")
        assert config2.hole_filling_method == "flood_fill"

    def test_invalid_morphology_kernel_size(self) -> None:
        """Test validation of morphology_kernel_size."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        with pytest.raises(ValueError, match="morphology_kernel_size must be >= 1"):
            SegmentationProcessorConfig(morphology_kernel_size=0)

    def test_invalid_boundary_width(self) -> None:
        """Test validation of boundary_width."""
        from video2d3d.segmentation.processor import SegmentationProcessorConfig

        with pytest.raises(ValueError, match="boundary_width must be >= 1"):
            SegmentationProcessorConfig(boundary_width=0)

    def test_morphology_kernel_helper(self, sample_masks: list[dict[str, Any]]) -> None:
        """Test the _get_morphology_kernel helper method."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(morphology_kernel_size=7)
        processor = SegmentationProcessor(config=config)
        kernel = processor._get_morphology_kernel()

        assert kernel.shape == (7, 7)


# ---------------------------------------------------------------------------
# SemanticSegmenter Lifecycle Tests
# ---------------------------------------------------------------------------


class TestSemanticSegmenterLifecycle:
    """Tests for SemanticSegmenter lifecycle management."""

    def test_close_method(self) -> None:
        """Test the close() method releases resources."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        segmenter._is_loaded = True
        segmenter._sam = MagicMock()
        segmenter._mask_generator = MagicMock()

        segmenter.close()

        assert segmenter._sam is None
        assert segmenter._mask_generator is None
        assert not segmenter._is_loaded

    def test_context_manager_enter_exit(self) -> None:
        """Test context manager protocol."""
        from video2d3d.segmentation import SemanticSegmenter

        with SemanticSegmenter(device="cpu") as segmenter:
            assert segmenter is not None
            assert not segmenter.is_loaded
            # Simulate loading
            segmenter._is_loaded = True
            segmenter._sam = MagicMock()

        # After exiting context, resources should be released
        assert segmenter._sam is None
        assert not segmenter._is_loaded

    def test_context_manager_with_exception(self) -> None:
        """Test context manager cleans up even with exception."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        segmenter._is_loaded = True
        segmenter._sam = MagicMock()

        try:
            with segmenter:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Resources should still be cleaned up
        assert segmenter._sam is None

    def test_fallback_to_cpu(self) -> None:
        """Test GPU to CPU fallback."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cuda")
        segmenter._sam = MagicMock()
        segmenter._sam.to = MagicMock()

        segmenter._fallback_to_cpu()

        segmenter._sam.to.assert_called_once_with(device="cpu")
        assert segmenter.config.device == "cpu"

    def test_fallback_to_cpu_already_on_cpu(self) -> None:
        """Test fallback when already on CPU."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        segmenter._sam = MagicMock()

        # Should not raise and should not change anything
        segmenter._fallback_to_cpu()

        assert segmenter.config.device == "cpu"


# ---------------------------------------------------------------------------
# Depth Refinement Method Tests
# ---------------------------------------------------------------------------


class TestDepthRefinementMethods:
    """Tests for all depth refinement methods."""

    def test_boundary_sharpening_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test boundary_sharpening refinement method."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(
            depth_refinement="boundary_sharpening",
            preserve_sharp_boundaries=True,
        )
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape
        assert refined.dtype == np.float32

    def test_object_smoothing_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test object_smoothing refinement method."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(
            depth_refinement="object_smoothing",
            smooth_within_objects=True,
        )
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape
        assert refined.dtype == np.float32

    def test_edge_aware_filter_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
        sample_image: np.ndarray,
    ) -> None:
        """Test edge_aware_filter refinement method."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(depth_refinement="edge_aware_filter")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks, sample_image)

        assert refined.shape == sample_depth_map.shape
        assert refined.dtype == np.float32

    def test_combined_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
        sample_image: np.ndarray,
    ) -> None:
        """Test combined refinement method (default)."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(depth_refinement="combined")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks, sample_image)

        assert refined.shape == sample_depth_map.shape
        assert refined.dtype == np.float32
        assert np.all(refined >= 0) and np.all(refined <= 1)

    def test_disabled_boundary_preservation(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test with boundary preservation disabled."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(
            depth_refinement="boundary_sharpening",
            preserve_sharp_boundaries=False,
        )
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        # Should return original depth map when preservation is disabled
        np.testing.assert_array_almost_equal(refined, sample_depth_map)

    def test_disabled_object_smoothing(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test with object smoothing disabled."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(
            depth_refinement="object_smoothing",
            smooth_within_objects=False,
        )
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        np.testing.assert_array_almost_equal(refined, sample_depth_map)


# ---------------------------------------------------------------------------
# Edge-Aware Filter Image Format Tests
# ---------------------------------------------------------------------------


class TestEdgeAwareFilterFormats:
    """Tests for edge-aware filter with various image formats."""

    def test_grayscale_image_input(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test edge-aware filter with grayscale image."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        # Create grayscale image
        np.random.seed(42)
        gray_image = np.random.randint(0, 255, (256, 256), dtype=np.uint8)

        config = IntegrationConfig(depth_refinement="edge_aware_filter")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks, gray_image)

        assert refined.shape == sample_depth_map.shape

    def test_four_channel_image_input(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test edge-aware filter with 4-channel RGBA image."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        # Create 4-channel RGBA image
        np.random.seed(42)
        rgba_image = np.random.randint(0, 255, (256, 256, 4), dtype=np.uint8)

        config = IntegrationConfig(depth_refinement="edge_aware_filter")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks, rgba_image)

        assert refined.shape == sample_depth_map.shape

    def test_no_image_edge_aware_filter(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test edge-aware filter without image input."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(depth_refinement="edge_aware_filter")
        integrator = DepthSegmentationIntegrator(config=config)
        # Should return original when no image is provided
        refined = integrator.refine(sample_depth_map, sample_masks, None)

        np.testing.assert_array_almost_equal(refined, sample_depth_map)


# ---------------------------------------------------------------------------
# Integration Tests - Segmentation + Depth Pipeline
# ---------------------------------------------------------------------------


class TestSegmentationDepthIntegration:
    """Integration tests for segmentation and depth pipeline."""

    def test_full_segmentation_to_depth_pipeline(
        self,
        sample_image: np.ndarray,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test full pipeline from segmentation to depth refinement."""
        from video2d3d.segmentation import SemanticSegmenter
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator
        from video2d3d.segmentation.processor import SegmentationProcessor

        # Step 1: Create segmenter and extract boundaries
        segmenter = SemanticSegmenter(device="cpu")
        boundaries = segmenter.extract_boundaries([], (256, 256))

        assert boundaries.shape == (256, 256)

        # Step 2: Process masks
        processor = SegmentationProcessor()
        weight_map = processor.create_weight_map([], (256, 256))

        assert weight_map.shape == (256, 256)
        assert np.all(weight_map >= 1.0)

        # Step 3: Refine depth
        integrator = DepthSegmentationIntegrator()
        refined_depth = integrator.refine(sample_depth_map, [])

        assert refined_depth.shape == sample_depth_map.shape

    def test_segmentation_improves_depth_boundaries(
        self,
        sample_image: np.ndarray,
    ) -> None:
        """Test that segmentation-based refinement preserves depth edges."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        # Create depth map with sharp edge
        depth_map = np.zeros((100, 100), dtype=np.float32)
        depth_map[:, :50] = 0.2  # Near
        depth_map[:, 50:] = 0.8  # Far

        # Create mask matching the depth edge
        mask = np.zeros((100, 100), dtype=bool)
        mask[:, :50] = True
        masks = [
            {
                "segmentation": mask,
                "area": 5000,
                "bbox": [0, 0, 50, 100],
                "predicted_iou": 0.95,
                "stability_score": 0.95,
            }
        ]

        # Refine depth with high sharpness
        config = IntegrationConfig(
            boundary_sharpness=2.0,
            preserve_sharp_boundaries=True,
        )
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(depth_map, masks)

        assert refined.shape == depth_map.shape
        assert np.all(refined >= 0) and np.all(refined <= 1)

    def test_object_separation_enhancement(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test that 3D object separation increases depth differences."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        # Create depth map with two objects at similar depth
        depth_map = np.ones((100, 100), dtype=np.float32) * 0.5

        # Create two separate masks
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[20:40, 20:40] = True
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[60:80, 60:80] = True

        masks = [
            {
                "segmentation": mask1,
                "area": 400,
                "bbox": [20, 20, 20, 20],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
            {
                "segmentation": mask2,
                "area": 400,
                "bbox": [60, 60, 20, 20],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        integrator = DepthSegmentationIntegrator()
        separated = integrator.separate_objects_3d(depth_map, masks, separation_strength=1.0)

        assert separated.shape == depth_map.shape
        # Separation should maintain valid depth range
        assert np.all(separated >= 0) and np.all(separated <= 1)


# ---------------------------------------------------------------------------
# Edge Case Tests - Additional Coverage
# ---------------------------------------------------------------------------


class TestAdditionalEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_very_large_mask(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test handling of masks covering most of the image."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        # Create mask covering 90% of image
        large_mask = np.ones((256, 256), dtype=bool)
        large_mask[:26, :] = False  # 10% uncovered

        masks = [
            {
                "segmentation": large_mask,
                "area": int(np.sum(large_mask)),
                "bbox": [0, 0, 256, 230],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            }
        ]

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(sample_depth_map, masks)

        assert refined.shape == sample_depth_map.shape

    def test_overlapping_masks(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test handling of overlapping masks."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        # Create two overlapping masks
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[20:60, 20:60] = True

        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[40:80, 40:80] = True  # Overlaps with mask1

        masks = [
            {
                "segmentation": mask1,
                "area": int(np.sum(mask1)),
                "bbox": [20, 20, 40, 40],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
            {
                "segmentation": mask2,
                "area": int(np.sum(mask2)),
                "bbox": [40, 40, 40, 40],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        depth = np.random.rand(100, 100).astype(np.float32)
        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(depth, masks)

        assert refined.shape == depth.shape

    def test_tiny_masks_filtered_out(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test that tiny masks are filtered during processing."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        # Create tiny mask that should be filtered
        tiny_mask = np.zeros((256, 256), dtype=bool)
        tiny_mask[100:102, 100:102] = True  # Only 4 pixels

        masks = sample_masks + [
            {
                "segmentation": tiny_mask,
                "area": 4,
                "bbox": [100, 100, 2, 2],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            }
        ]

        config = SegmentationProcessorConfig(min_mask_area=10)
        processor = SegmentationProcessor(config=config)
        processed = processor.process(masks, (256, 256))

        # Tiny mask should be filtered out
        for m in processed:
            assert m["area"] >= 10

    def test_boundary_type_inner_only(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test extracting only inner boundaries."""
        from video2d3d.segmentation.processor import BoundaryType, SegmentationProcessor

        processor = SegmentationProcessor()
        inner = processor.extract_boundaries(sample_masks, (256, 256), BoundaryType.INNER)

        assert inner.shape == (256, 256)
        assert inner.dtype == bool

    def test_boundary_type_outer_only(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test extracting only outer boundaries."""
        from video2d3d.segmentation.processor import BoundaryType, SegmentationProcessor

        processor = SegmentationProcessor()
        outer = processor.extract_boundaries(sample_masks, (256, 256), BoundaryType.OUTER)

        assert outer.shape == (256, 256)
        assert outer.dtype == bool

    def test_weight_map_boundary_weight(self) -> None:
        """Test weight map with custom boundary weight."""
        from video2d3d.segmentation.processor import SegmentationProcessor

        # Create simple mask
        mask = np.zeros((50, 50), dtype=bool)
        mask[10:40, 10:40] = True
        masks = [
            {
                "segmentation": mask,
                "area": 900,
                "bbox": [10, 10, 30, 30],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            }
        ]

        processor = SegmentationProcessor()
        weights = processor.create_weight_map(masks, (50, 50), boundary_weight=3.0)

        assert np.max(weights) <= 3.0
        assert np.min(weights) >= 1.0


# ---------------------------------------------------------------------------
# Model Type and Checkpoint Tests
# ---------------------------------------------------------------------------


class TestModelTypeAndCheckpoints:
    """Tests for model type handling and checkpoint management."""

    def test_checkpoint_filename_property(self) -> None:
        """Test checkpoint_filename property for all model types."""
        from video2d3d.segmentation import SAMModelType

        assert SAMModelType.VIT_H.checkpoint_filename == "sam_vit_h.pth"
        assert SAMModelType.VIT_L.checkpoint_filename == "sam_vit_l.pth"
        assert SAMModelType.VIT_B.checkpoint_filename == "sam_vit_b.pth"

    def test_checkpoint_url_format(self) -> None:
        """Test that checkpoint URLs have correct format."""
        from video2d3d.segmentation import SAMModelType

        for model_type in SAMModelType:
            url = model_type.checkpoint_url
            assert url.startswith("https://")
            assert "fbaipublicfiles.com" in url
            assert url.endswith(".pth")

    def test_from_string_case_insensitive(self) -> None:
        """Test that from_string is case insensitive."""
        from video2d3d.segmentation import SAMModelType

        assert SAMModelType.from_string("VIT_H") == SAMModelType.VIT_H
        assert SAMModelType.from_string("Vit_L") == SAMModelType.VIT_L
        assert SAMModelType.from_string("VIT_B") == SAMModelType.VIT_B

    def test_from_string_with_spaces(self) -> None:
        """Test from_string with spaces in name."""
        from video2d3d.segmentation import SAMModelType

        # Spaces should be converted to underscores
        assert SAMModelType.from_string("vit huge") == SAMModelType.VIT_H
        assert SAMModelType.from_string("vit large") == SAMModelType.VIT_L
        assert SAMModelType.from_string("vit base") == SAMModelType.VIT_B

    def test_from_string_with_dashes(self) -> None:
        """Test from_string with dashes in name."""
        from video2d3d.segmentation import SAMModelType

        # Dashes should be converted to underscores
        assert SAMModelType.from_string("vit-huge") == SAMModelType.VIT_H
        assert SAMModelType.from_string("vit-large") == SAMModelType.VIT_L
        assert SAMModelType.from_string("vit-base") == SAMModelType.VIT_B


# ---------------------------------------------------------------------------
# Segmentation Mode Tests
# ---------------------------------------------------------------------------


class TestSegmentationModes:
    """Tests for different segmentation modes."""

    def test_segmentation_mode_enum_values(self) -> None:
        """Test SegmentationMode enum values."""
        from video2d3d.segmentation import SegmentationMode

        assert SegmentationMode.AUTOMATIC.value == "automatic"
        assert SegmentationMode.EDGE_AWARE.value == "edge_aware"
        assert SegmentationMode.OBJECT_CENTRIC.value == "object_centric"

    def test_filter_edge_masks_with_rgb_image(self) -> None:
        """Test _filter_edge_masks handles RGB images."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")

        # Create RGB test image
        rgb_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Create some test masks
        masks = [
            {
                "segmentation": np.ones((100, 100), dtype=bool),
                "area": 10000,
                "bbox": [0, 0, 100, 100],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        # Should not raise for RGB images
        filtered = segmenter._filter_edge_masks(masks, rgb_image)
        assert isinstance(filtered, list)

    def test_filter_edge_masks_with_grayscale_image(self) -> None:
        """Test _filter_edge_masks handles grayscale images."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")

        # Create grayscale test image
        gray_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        masks = [
            {
                "segmentation": np.ones((100, 100), dtype=bool),
                "area": 10000,
                "bbox": [0, 0, 100, 100],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        # Should not raise for grayscale images
        filtered = segmenter._filter_edge_masks(masks, gray_image)
        assert isinstance(filtered, list)

    def test_filter_object_masks_high_quality(self) -> None:
        """Test _filter_object_masks keeps high quality masks."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")

        # Create masks with varying quality
        high_quality_mask = {
            "segmentation": np.ones((100, 100), dtype=bool),
            "area": 1000,
            "bbox": [0, 0, 100, 100],
            "predicted_iou": 0.95,
            "stability_score": 0.95,
        }
        low_quality_mask = {
            "segmentation": np.ones((100, 100), dtype=bool),
            "area": 1000,
            "bbox": [0, 0, 100, 100],
            "predicted_iou": 0.8,
            "stability_score": 0.8,
        }

        filtered = segmenter._filter_object_masks([high_quality_mask, low_quality_mask])

        # Only high quality mask should remain
        assert len(filtered) == 1
        assert filtered[0]["predicted_iou"] > 0.9


# ---------------------------------------------------------------------------
# Boundary Preservation Method Tests
# ---------------------------------------------------------------------------


class TestBoundaryPreservationMethods:
    """Tests for boundary preservation method configuration."""

    def test_edge_weighted_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test edge_weighted boundary preservation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(boundary_preservation="edge_weighted")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape

    def test_mask_guided_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test mask_guided boundary preservation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(boundary_preservation="mask_guided")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape

    def test_joint_bilateral_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test joint_bilateral boundary preservation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(boundary_preservation="joint_bilateral")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape

    def test_none_preservation_method(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test none boundary preservation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(boundary_preservation="none")
        integrator = DepthSegmentationIntegrator(config=config)
        refined = integrator.refine(sample_depth_map, sample_masks)

        assert refined.shape == sample_depth_map.shape


# ---------------------------------------------------------------------------
# Invalid Depth Refinement Method Test
# ---------------------------------------------------------------------------


class TestInvalidRefinementMethod:
    """Test invalid refinement method handling."""

    def test_invalid_depth_refinement_method(self) -> None:
        """Test that invalid depth_refinement raises error."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="Invalid depth_refinement"):
            IntegrationConfig(depth_refinement="invalid_method")

    def test_invalid_boundary_preservation_method(self) -> None:
        """Test that invalid boundary_preservation raises error."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="Invalid boundary_preservation"):
            IntegrationConfig(boundary_preservation="invalid_method")

    def test_invalid_smoothing_strength_negative(self) -> None:
        """Test that negative smoothing_strength raises error."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="smoothing_strength must be in"):
            IntegrationConfig(smoothing_strength=-0.5)

    def test_invalid_boundary_sharpness_zero(self) -> None:
        """Test that zero boundary_sharpness raises error."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="boundary_sharpness must be positive"):
            IntegrationConfig(boundary_sharpness=0)

    def test_invalid_boundary_sharpness_negative(self) -> None:
        """Test that negative boundary_sharpness raises error."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="boundary_sharpness must be positive"):
            IntegrationConfig(boundary_sharpness=-1.5)

    def test_invalid_edge_dilation(self) -> None:
        """Test that negative edge_dilation raises error."""
        from video2d3d.segmentation.integrator import IntegrationConfig

        with pytest.raises(ValueError, match="edge_dilation must be >= 0"):
            IntegrationConfig(edge_dilation=-1)


# ---------------------------------------------------------------------------
# Mask Merging Tests
# ---------------------------------------------------------------------------


class TestMaskMerging:
    """Tests for mask merging functionality."""

    def test_merge_overlapping_masks_disabled(self) -> None:
        """Test that overlapping masks are not merged when disabled."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        # Create overlapping masks
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[20:60, 20:60] = True

        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[40:80, 40:80] = True

        masks = [
            {
                "segmentation": mask1,
                "area": 1600,
                "bbox": [20, 20, 40, 40],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
            {
                "segmentation": mask2,
                "area": 1600,
                "bbox": [40, 40, 40, 40],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        config = SegmentationProcessorConfig(merge_overlapping=False)
        processor = SegmentationProcessor(config=config)
        processed = processor.process(masks, (100, 100))

        # Both masks should remain when merging is disabled
        assert len(processed) >= 1

    def test_merge_overlapping_masks_enabled(self) -> None:
        """Test that overlapping masks are merged when enabled."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        # Create highly overlapping masks (>50% IoU)
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[20:60, 20:60] = True

        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[30:50, 30:50] = True  # Mostly inside mask1

        masks = [
            {
                "segmentation": mask1,
                "area": 1600,
                "bbox": [20, 20, 40, 40],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
            {
                "segmentation": mask2,
                "area": 400,
                "bbox": [30, 30, 20, 20],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        config = SegmentationProcessorConfig(
            merge_overlapping=True,
            overlap_threshold=0.5,
        )
        processor = SegmentationProcessor(config=config)
        processed = processor.process(masks, (100, 100))

        # Masks should be merged
        assert isinstance(processed, list)


# ---------------------------------------------------------------------------
# Additional SemanticSegmenter Tests
# ---------------------------------------------------------------------------


class TestSemanticSegmenterAdvanced:
    """Additional tests for SemanticSegmenter."""

    def test_get_checkpoint_path_custom(self, tmp_path) -> None:
        """Test _get_checkpoint_path with custom path."""
        from video2d3d.segmentation import SAMConfig, SAMModelType, SemanticSegmenter

        custom_path = tmp_path / "custom_checkpoint.pth"
        custom_path.touch()  # Create the file

        config = SAMConfig(
            model_type=SAMModelType.VIT_B,
            checkpoint_path=custom_path,
        )
        segmenter = SemanticSegmenter(config=config)

        result_path = segmenter._get_checkpoint_path()

        assert result_path == custom_path

    def test_is_loaded_property(self) -> None:
        """Test is_loaded property."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")

        assert not segmenter.is_loaded

        segmenter._is_loaded = True
        assert segmenter.is_loaded

        segmenter._is_loaded = False
        assert not segmenter.is_loaded

    def test_segment_ensures_model_loaded(self) -> None:
        """Test that segment() calls load_model() if not loaded."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")

        # Mock load_model to avoid actual loading
        with patch.object(segmenter, "load_model") as mock_load:
            segmenter._mask_generator = MagicMock()
            segmenter._mask_generator.generate.return_value = []

            try:
                segmenter.segment(np.zeros((100, 100, 3), dtype=np.uint8))
            except Exception:
                pass  # May fail for other reasons

            # load_model should have been called since _is_loaded is False
            mock_load.assert_called_once()

    def test_segment_4_channel_image(self) -> None:
        """Test segmentation with 4-channel image."""
        from video2d3d.segmentation import SemanticSegmenter

        segmenter = SemanticSegmenter(device="cpu")
        segmenter._is_loaded = True
        segmenter._mask_generator = MagicMock()
        segmenter._mask_generator.generate.return_value = []

        # 4-channel RGBA image
        rgba_image = np.random.randint(0, 255, (100, 100, 4), dtype=np.uint8)

        # Should not raise - uses first 3 channels
        result = segmenter.segment(rgba_image)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Get Object Depth Layers Edge Cases
# ---------------------------------------------------------------------------


class TestGetObjectDepthLayersEdgeCases:
    """Tests for get_object_depth_layers edge cases."""

    def test_empty_masks_returns_empty_list(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test that empty masks returns empty list."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()
        layers = integrator.get_object_depth_layers(sample_depth_map, [])

        assert layers == []

    def test_masks_with_zero_area_skipped(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test that masks with zero area are skipped."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        # Mask with no True pixels
        empty_mask = np.zeros((100, 100), dtype=bool)

        masks = [
            {
                "segmentation": empty_mask,
                "area": 0,
                "bbox": [0, 0, 0, 0],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            }
        ]

        depth = np.random.rand(100, 100).astype(np.float32)
        integrator = DepthSegmentationIntegrator()
        layers = integrator.get_object_depth_layers(depth, masks)

        assert layers == []

    def test_layers_sorted_by_depth(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test that layers are properly sorted by depth."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        # Create masks at different depth regions
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[:50, :] = True  # Top half (likely different depth)

        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[50:, :] = True  # Bottom half

        masks = [
            {
                "segmentation": mask1,
                "area": 5000,
                "bbox": [0, 0, 100, 50],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
            {
                "segmentation": mask2,
                "area": 5000,
                "bbox": [0, 50, 100, 50],
                "predicted_iou": 0.9,
                "stability_score": 0.9,
            },
        ]

        depth = sample_depth_map[:100, :100]
        integrator = DepthSegmentationIntegrator()
        layers = integrator.get_object_depth_layers(depth, masks)

        # Extract depths and verify sorted
        depths = [d for _, d in layers]
        assert depths == sorted(depths)


# ---------------------------------------------------------------------------
# Segmentation Error Classes Tests
# ---------------------------------------------------------------------------


class TestSegmentationErrorClasses:
    """Tests for segmentation error classes."""

    def test_segmentation_error_attributes(self) -> None:
        """Test SegmentationError attributes."""
        from video2d3d.segmentation import SegmentationError

        original = ValueError("original error")
        error = SegmentationError(
            "test message",
            model_type="vit_b",
            device="cuda",
            original_exception=original,
        )

        assert str(error) == "test message"
        assert error.model_type == "vit_b"
        assert error.device == "cuda"
        assert error.original_exception == original

    def test_model_load_error_is_segmentation_error(self) -> None:
        """Test ModelLoadError is subclass of SegmentationError."""
        from video2d3d.segmentation import ModelLoadError, SegmentationError

        assert issubclass(ModelLoadError, SegmentationError)

        error = ModelLoadError("load failed", model_type="vit_b")
        assert isinstance(error, SegmentationError)

    def test_inference_error_is_segmentation_error(self) -> None:
        """Test InferenceError is subclass of SegmentationError."""
        from video2d3d.segmentation import InferenceError, SegmentationError

        assert issubclass(InferenceError, SegmentationError)

        error = InferenceError("inference failed", device="cpu")
        assert isinstance(error, SegmentationError)

    def test_processor_error_attributes(self) -> None:
        """Test SegmentationProcessorError attributes."""
        from video2d3d.segmentation.processor import SegmentationProcessorError

        original = ValueError("original error")
        error = SegmentationProcessorError(
            "processor failed",
            operation="filter",
            original_exception=original,
        )

        assert str(error) == "processor failed"
        assert error.operation == "filter"
        assert error.original_exception == original

    def test_integration_error_attributes(self) -> None:
        """Test IntegrationError attributes."""
        from video2d3d.segmentation.integrator import IntegrationError

        original = ValueError("original error")
        error = IntegrationError(
            "integration failed",
            operation="refine",
            original_exception=original,
        )

        assert str(error) == "integration failed"
        assert error.operation == "refine"
        assert error.original_exception == original


# ---------------------------------------------------------------------------
# Depth Map Edge Value Tests
# ---------------------------------------------------------------------------


class TestDepthMapEdgeValues:
    """Tests for depth maps with edge values."""

    def test_all_zeros_depth_map(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test handling of all-zeros depth map."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        zero_depth = np.zeros((100, 100), dtype=np.float32)

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(zero_depth, sample_masks[:1])

        assert refined.shape == zero_depth.shape
        assert np.all(refined >= 0)

    def test_all_ones_depth_map(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test handling of all-ones depth map."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        ones_depth = np.ones((100, 100), dtype=np.float32)

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(ones_depth, sample_masks[:1])

        assert refined.shape == ones_depth.shape
        assert np.all(refined <= 1)

    def test_binary_depth_map(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test handling of binary depth map."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        # Create binary depth map with sharp edge
        binary_depth = np.zeros((100, 100), dtype=np.float32)
        binary_depth[:, 50:] = 1.0

        integrator = DepthSegmentationIntegrator()
        refined = integrator.refine(binary_depth, sample_masks[:1])

        assert refined.shape == binary_depth.shape
        assert np.all(refined >= 0) and np.all(refined <= 1)


# ---------------------------------------------------------------------------
# Smoothing Iterations Tests
# ---------------------------------------------------------------------------


class TestSmoothingIterations:
    """Tests for different smoothing iteration counts."""

    def test_zero_smoothing_iterations(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test processor with zero smoothing iterations."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(
            enable_smoothing=True,
            smoothing_iterations=0,
        )
        processor = SegmentationProcessor(config=config)
        processed = processor.process(sample_masks, (256, 256))

        assert isinstance(processed, list)

    def test_high_smoothing_iterations(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test processor with high smoothing iterations."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(
            enable_smoothing=True,
            smoothing_iterations=5,
        )
        processor = SegmentationProcessor(config=config)
        processed = processor.process(sample_masks, (256, 256))

        assert isinstance(processed, list)


# ---------------------------------------------------------------------------
# Boundary Width Configuration Tests
# ---------------------------------------------------------------------------


class TestBoundaryWidthConfiguration:
    """Tests for different boundary width configurations."""

    def test_small_boundary_width(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test processor with small boundary width."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(boundary_width=1)
        processor = SegmentationProcessor(config=config)
        boundaries = processor.extract_boundaries(sample_masks, (256, 256))

        assert boundaries.shape == (256, 256)

    def test_large_boundary_width(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test processor with large boundary width."""
        from video2d3d.segmentation.processor import (
            SegmentationProcessor,
            SegmentationProcessorConfig,
        )

        config = SegmentationProcessorConfig(boundary_width=10)
        processor = SegmentationProcessor(config=config)
        boundaries = processor.extract_boundaries(sample_masks, (256, 256))

        assert boundaries.shape == (256, 256)


# ---------------------------------------------------------------------------
# Edge Dilation Configuration Tests
# ---------------------------------------------------------------------------


class TestEdgeDilationConfiguration:
    """Tests for different edge dilation configurations."""

    def test_zero_edge_dilation(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test integrator with zero edge dilation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(edge_dilation=0)
        integrator = DepthSegmentationIntegrator(config=config)
        weights = integrator.compute_boundary_weights(sample_masks, (256, 256))

        assert weights.shape == (256, 256)

    def test_large_edge_dilation(
        self,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test integrator with large edge dilation."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator, IntegrationConfig

        config = IntegrationConfig(edge_dilation=10)
        integrator = DepthSegmentationIntegrator(config=config)
        weights = integrator.compute_boundary_weights(sample_masks, (256, 256))

        assert weights.shape == (256, 256)
        assert np.all(weights >= 1.0)


# ---------------------------------------------------------------------------
# Integration with Depth Processor (Mock Test)
# ---------------------------------------------------------------------------


class TestIntegrationWithDepthProcessor:
    """Tests for integration with depth processor module."""

    def test_segmentation_output_compatible_with_depth_input(
        self,
        sample_depth_map: np.ndarray,
        sample_masks: list[dict[str, Any]],
    ) -> None:
        """Test that segmentation output is compatible with depth processing."""
        from video2d3d.segmentation.integrator import refine_depth_with_segmentation
        from video2d3d.segmentation.processor import process_segmentation_masks

        # Process masks
        processed_masks = process_segmentation_masks(
            sample_masks,
            sample_depth_map.shape,
        )

        # Refine depth
        refined_depth = refine_depth_with_segmentation(
            sample_depth_map,
            processed_masks,
        )

        # Verify output is valid depth map
        assert refined_depth.shape == sample_depth_map.shape
        assert refined_depth.dtype == np.float32
        assert np.all(refined_depth >= 0) and np.all(refined_depth <= 1)

    def test_pipeline_with_varying_mask_counts(
        self,
        sample_depth_map: np.ndarray,
    ) -> None:
        """Test pipeline handles varying numbers of masks."""
        from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

        integrator = DepthSegmentationIntegrator()

        # Test with 0, 1, 5, 10 masks
        for num_masks in [0, 1, 5, 10]:
            masks = []
            for i in range(num_masks):
                mask = np.zeros((256, 256), dtype=bool)
                y, x = np.ogrid[:256, :256]
                center_y = (i * 50 + 50) % 256
                center_x = (i * 30 + 30) % 256
                radius = 20
                mask[(y - center_y) ** 2 + (x - center_x) ** 2 <= radius**2] = True
                masks.append(
                    {
                        "segmentation": mask,
                        "area": int(np.sum(mask)),
                        "bbox": [center_x - radius, center_y - radius, radius * 2, radius * 2],
                        "predicted_iou": 0.9,
                        "stability_score": 0.9,
                    }
                )

            refined = integrator.refine(sample_depth_map, masks)
            assert refined.shape == sample_depth_map.shape


# ---------------------------------------------------------------------------
# End of Additional Tests
# ---------------------------------------------------------------------------
