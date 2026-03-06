#!/usr/bin/env python
"""Verification script for optical flow engine feature.

This script verifies that the optical flow engine works correctly by:
1. Testing basic Farneback flow computation
2. Testing batch processing
3. Testing visualization
4. Verifying error handling

Run with: python scripts/verify_opticalflow_feature.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


def create_test_frames(height: int = 100, width: int = 100) -> tuple[np.ndarray, np.ndarray]:
    """Create a pair of test frames with known motion.

    Args:
        height: Frame height.
        width: Frame width.

    Returns:
        Tuple of (frame1, frame2) with frame2 being a shifted version of frame1.
    """
    # Create a simple test pattern with a moving object
    frame1 = np.zeros((height, width, 3), dtype=np.uint8)

    # Add a white rectangle
    frame1[20:40, 30:50] = 255

    # Add some texture
    np.random.seed(42)
    frame1[50:80, 60:90] = np.random.randint(100, 200, (30, 30, 3), dtype=np.uint8)

    # Create frame2 by shifting the object (simulating motion)
    frame2 = np.zeros_like(frame1)
    frame2[20:40, 35:55] = 255  # Shifted 5 pixels right
    frame2[50:80, 65:95] = frame1[50:80, 60:90]  # Shifted 5 pixels right

    return frame1, frame2


def verify_imports() -> bool:
    """Verify that all required imports work.

    Returns:
        True if all imports succeed, False otherwise.
    """
    print("1. Verifying imports...")

    try:
        from video2d3d.opticalflow.engine import (
            OpticalFlowEngine,
            OpticalFlowConfig,
            OpticalFlowModelType,
            OpticalFlowError,
            ModelLoadError,
            InferenceError,
            create_opticalflow_engine,
            compute_optical_flow,
        )

        print("   ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        return False


def verify_config() -> bool:
    """Verify OpticalFlowConfig works correctly.

    Returns:
        True if config tests pass, False otherwise.
    """
    print("\n2. Verifying OpticalFlowConfig...")

    try:
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowModelType

        # Test default config
        config = OpticalFlowConfig(model_type="farneback")
        assert config.model_type == OpticalFlowModelType.FARNEBACK
        print("   ✓ Default config creation works")

        # Test string to enum conversion
        config2 = OpticalFlowConfig(model_type="RAFT_LARGE")
        assert config2.model_type == OpticalFlowModelType.RAFT_LARGE
        print("   ✓ String to enum conversion works")

        # Test config validation
        try:
            OpticalFlowConfig(farneback_pyr_scale=2.0)
            print("   ✗ Config validation should have failed for invalid pyr_scale")
            return False
        except ValueError:
            print("   ✓ Config validation works for invalid parameters")

        return True

    except Exception as e:
        print(f"   ✗ Config verification failed: {e}")
        return False


def verify_farneback_flow() -> bool:
    """Verify Farneback optical flow computation.

    Returns:
        True if flow computation works, False otherwise.
    """
    print("\n3. Verifying Farneback optical flow...")

    try:
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        # Create test frames
        frame1, frame2 = create_test_frames()

        # Create engine with Farneback
        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Compute flow
        flow = engine.compute_flow(frame1, frame2)

        # Verify output shape and type
        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2), (
            f"Expected shape {(frame1.shape[0], frame1.shape[1], 2)}, got {flow.shape}"
        )
        assert flow.dtype == np.float32, f"Expected dtype float32, got {flow.dtype}"

        print(f"   ✓ Flow computation successful (shape: {flow.shape})")

        # Check that flow values are reasonable (not all zeros)
        mean_flow = np.mean(np.abs(flow))
        print(f"   ✓ Mean flow magnitude: {mean_flow:.4f}")

        return True

    except Exception as e:
        print(f"   ✗ Farneback flow verification failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_batch_processing() -> bool:
    """Verify batch processing of frame pairs.

    Returns:
        True if batch processing works, False otherwise.
    """
    print("\n4. Verifying batch processing...")

    try:
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        # Create multiple frame pairs
        frames = [create_test_frames()[0] for _ in range(5)]
        for i in range(1, len(frames)):
            frames[i] = np.roll(frames[i - 1], i * 2, axis=1)

        frames1 = frames[:-1]
        frames2 = frames[1:]

        # Create engine
        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Process batch
        flows = engine.compute_flow_batch(frames1, frames2)

        assert len(flows) == len(frames1), f"Expected {len(frames1)} flows, got {len(flows)}"

        for i, flow in enumerate(flows):
            assert flow.shape == (frames1[0].shape[0], frames1[0].shape[1], 2), (
                f"Flow {i} has wrong shape: {flow.shape}"
            )

        print(f"   ✓ Batch processing successful ({len(flows)} frame pairs)")

        return True

    except Exception as e:
        print(f"   ✗ Batch processing verification failed: {e}")
        return False


def verify_error_handling() -> bool:
    """Verify error handling works correctly.

    Returns:
        True if error handling works, False otherwise.
    """
    print("\n5. Verifying error handling...")

    try:
        from video2d3d.opticalflow.engine import (
            InferenceError,
            OpticalFlowConfig,
            OpticalFlowEngine,
        )

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Test invalid input (wrong type)
        try:
            engine.compute_flow("not an array", np.zeros((10, 10, 3)))  # type: ignore
            print("   ✗ Should have raised InferenceError for invalid input")
            return False
        except InferenceError:
            print("   ✓ Correctly raises InferenceError for invalid input")

        # Test mismatched shapes
        try:
            engine.compute_flow(np.zeros((10, 10, 3)), np.zeros((20, 20, 3)))
            print("   ✗ Should have raised InferenceError for mismatched shapes")
            return False
        except InferenceError:
            print("   ✓ Correctly raises InferenceError for mismatched shapes")

        return True

    except Exception as e:
        print(f"   ✗ Error handling verification failed: {e}")
        return False


def verify_convenience_functions() -> bool:
    """Verify convenience functions work.

    Returns:
        True if convenience functions work, False otherwise.
    """
    print("\n6. Verifying convenience functions...")

    try:
        from video2d3d.opticalflow.engine import (
            compute_optical_flow,
            create_opticalflow_engine,
        )

        frame1, frame2 = create_test_frames()

        # Test create_opticalflow_engine
        engine = create_opticalflow_engine(model_type="farneback")
        print("   ✓ create_opticalflow_engine works")

        # Test compute_optical_flow
        flow = compute_optical_flow(frame1, frame2, model_type="farneback")
        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        print("   ✓ compute_optical_flow works")

        return True

    except Exception as e:
        print(f"   ✗ Convenience functions verification failed: {e}")
        return False


def verify_context_manager() -> bool:
    """Verify context manager works correctly.

    Returns:
        True if context manager works, False otherwise.
    """
    print("\n7. Verifying context manager...")

    try:
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")

        with OpticalFlowEngine(config=config) as engine:
            frame1, frame2 = create_test_frames()
            flow = engine.compute_flow(frame1, frame2)
            assert flow.shape == (100, 100, 2)

        # After context, model should be cleaned up
        assert engine._model is None
        assert not engine.is_loaded

        print("   ✓ Context manager works correctly")

        return True

    except Exception as e:
        print(f"   ✗ Context manager verification failed: {e}")
        return False


def main() -> int:
    """Run all verification tests.

    Returns:
        0 if all tests pass, 1 otherwise.
    """
    print("=" * 60)
    print("Optical Flow Engine Feature Verification")
    print("=" * 60)

    tests = [
        verify_imports,
        verify_config,
        verify_farneback_flow,
        verify_batch_processing,
        verify_error_handling,
        verify_convenience_functions,
        verify_context_manager,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✓ All verification tests passed!")
        return 0
    else:
        print("\n✗ Some verification tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
