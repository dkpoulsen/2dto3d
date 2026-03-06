#!/usr/bin/env python
"""Verification script for the depth-segmentation feature.

This script verifies that the semantic segmentation module is correctly
integrated and functional for improving depth estimation.
"""

from __future__ import annotations

import sys
import numpy as np


def verify_config_classes() -> bool:
    """Verify configuration classes can be instantiated."""
    print("Testing configuration classes...")

    # Test SAMConfig
    from video2d3d.segmentation import SAMConfig, SAMModelType

    config = SAMConfig()
    assert config.model_type == SAMModelType.VIT_B, "Default model type should be VIT_B"

    config_custom = SAMConfig(model_type="vit_h")
    assert config_custom.model_type == SAMModelType.VIT_H, "Custom model type should be VIT_H"

    print("  ✓ SAMConfig works correctly")

    # Test SegmentationProcessorConfig
    from video2d3d.segmentation.processor import SegmentationProcessorConfig

    proc_config = SegmentationProcessorConfig()
    assert proc_config.min_mask_area == 100, "Default min_mask_area should be 100"

    print("  ✓ SegmentationProcessorConfig works correctly")

    # Test IntegrationConfig
    from video2d3d.segmentation.integrator import IntegrationConfig

    int_config = IntegrationConfig()
    assert int_config.smoothing_strength == 0.5, "Default smoothing_strength should be 0.5"

    print("  ✓ IntegrationConfig works correctly")

    return True


def verify_segmenter_initialization() -> bool:
    """Verify SemanticSegmenter can be initialized."""
    print("\nTesting SemanticSegmenter initialization...")

    from video2d3d.segmentation import SemanticSegmenter, SAMModelType

    segmenter = SemanticSegmenter(device="cpu")
    assert segmenter.config is not None, "Config should be set"
    assert segmenter.config.device == "cpu", "Device should be CPU"
    assert not segmenter.is_loaded, "Model should not be loaded initially"

    print("  ✓ SemanticSegmenter initializes correctly")

    # Test with custom config
    config = SAMConfig(model_type=SAMModelType.VIT_L, device="cpu")
    segmenter2 = SemanticSegmenter(config=config)
    assert segmenter2.config.model_type == SAMModelType.VIT_L

    print("  ✓ SemanticSegmenter accepts custom config")

    return True


def verify_processor_functionality() -> bool:
    """Verify SegmentationProcessor functionality."""
    print("\nTesting SegmentationProcessor...")

    from video2d3d.segmentation.processor import SegmentationProcessor

    processor = SegmentationProcessor()
    assert processor.config is not None

    # Create sample masks
    masks = []
    for i in range(3):
        mask = np.zeros((100, 100), dtype=bool)
        y, x = np.ogrid[:100, :100]
        center_y, center_x = 30 + i * 20, 50
        radius = 15
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

    # Test processing
    processed = processor.process(masks, (100, 100))
    assert isinstance(processed, list), "Process should return a list"

    print("  ✓ SegmentationProcessor processes masks correctly")

    # Test boundary extraction
    boundaries = processor.extract_boundaries(masks, (100, 100))
    assert boundaries.shape == (100, 100), "Boundaries should match image shape"
    assert boundaries.dtype == bool, "Boundaries should be boolean"

    print("  ✓ Boundary extraction works correctly")

    return True


def verify_integrator_functionality() -> bool:
    """Verify DepthSegmentationIntegrator functionality."""
    print("\nTesting DepthSegmentationIntegrator...")

    from video2d3d.segmentation.integrator import DepthSegmentationIntegrator

    integrator = DepthSegmentationIntegrator()
    assert integrator.config is not None

    # Create sample depth map
    depth_map = np.random.rand(100, 100).astype(np.float32)

    # Create sample masks
    masks = []
    for i in range(2):
        mask = np.zeros((100, 100), dtype=bool)
        y, x = np.ogrid[:100, :100]
        center_y, center_x = 30 + i * 40, 50
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

    # Test boundary weight computation
    weights = integrator.compute_boundary_weights(masks, (100, 100))
    assert weights.shape == (100, 100), "Weights should match image shape"
    assert np.all(weights >= 1.0), "All weights should be >= 1"

    print("  ✓ Boundary weight computation works correctly")

    # Test depth refinement
    refined = integrator.refine(depth_map, masks)
    assert refined.shape == depth_map.shape, "Refined depth should match input shape"
    assert np.all(refined >= 0) and np.all(refined <= 1), "Refined depth should be in [0, 1]"

    print("  ✓ Depth refinement works correctly")

    # Test 3D object separation
    separated = integrator.separate_objects_3d(depth_map, masks)
    assert separated.shape == depth_map.shape, "Separated depth should match input shape"

    print("  ✓ 3D object separation works correctly")

    return True


def verify_convenience_functions() -> bool:
    """Verify convenience functions work correctly."""
    print("\nTesting convenience functions...")

    from video2d3d.segmentation import create_segmenter
    from video2d3d.segmentation.processor import create_segmentation_processor
    from video2d3d.segmentation.integrator import create_integrator

    # Test create_segmenter
    segmenter = create_segmenter(model_type="vit_b", device="cpu")
    assert segmenter is not None

    print("  ✓ create_segmenter works correctly")

    # Test create_segmentation_processor
    processor = create_segmentation_processor(min_mask_area=50)
    assert processor.config.min_mask_area == 50

    print("  ✓ create_segmentation_processor works correctly")

    # Test create_integrator
    integrator = create_integrator(smoothing_strength=0.7)
    assert integrator.config.smoothing_strength == 0.7

    print("  ✓ create_integrator works correctly")

    return True


def main() -> int:
    """Run all verification tests."""
    print("=" * 60)
    print("Depth-Segmentation Feature Verification")
    print("=" * 60)

    tests = [
        ("Configuration Classes", verify_config_classes),
        ("SemanticSegmenter Initialization", verify_segmenter_initialization),
        ("SegmentationProcessor Functionality", verify_processor_functionality),
        ("DepthSegmentationIntegrator Functionality", verify_integrator_functionality),
        ("Convenience Functions", verify_convenience_functions),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name} FAILED with exception: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
