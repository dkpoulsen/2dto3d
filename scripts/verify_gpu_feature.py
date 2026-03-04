#!/usr/bin/env python
"""Verification script for GPU acceleration feature.

This script tests the GPU acceleration implementation to ensure:
1. GPU device detection works correctly
2. Automatic fallback to CPU when GPU unavailable
3. Memory management functions work
4. Batch size computation is functional
5. DepthEstimator integration works
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_gpu_module_imports() -> bool:
    """Test that the GPU module can be imported."""
    print("Testing GPU module imports...")
    try:
        from video2d3d.utils.gpu import (
            GPUConfig,
            GPUInfo,
            DeviceSelection,
            DeviceType,
            GPUError,
            OutOfMemoryError,
            is_cuda_available,
            is_mps_available,
            get_device_count,
            select_device,
            clear_gpu_memory,
            compute_optimal_batch_size,
            setup_device,
        )

        print("  ✓ All GPU module imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_device_detection() -> bool:
    """Test device detection functions."""
    print("Testing device detection...")
    try:
        from video2d3d.utils.gpu import (
            is_cuda_available,
            is_mps_available,
            get_device_count,
        )

        # These should work without errors
        cuda = is_cuda_available()
        mps = is_mps_available()
        count = get_device_count()

        print(f"  CUDA available: {cuda}")
        print(f"  MPS available: {mps}")
        print(f"  Device count: {count}")
        print("  ✓ Device detection working")
        return True
    except Exception as e:
        print(f"  ✗ Device detection failed: {e}")
        return False


def test_device_selection() -> bool:
    """Test device selection logic."""
    print("Testing device selection...")
    try:
        from video2d3d.utils.gpu import GPUConfig, select_device, DeviceType

        # Test CPU selection
        config = GPUConfig(device="cpu")
        selection = select_device(config)
        assert selection.device == "cpu", f"Expected 'cpu', got '{selection.device}'"
        assert selection.device_type == DeviceType.CPU
        print("  ✓ CPU selection works")

        # Test auto selection with fallback
        config = GPUConfig(device="auto", fallback_to_cpu=True)
        selection = select_device(config)
        print(f"  Auto selection chose: {selection.device} ({selection.device_name})")
        print("  ✓ Auto selection with fallback works")

        # Test disabled GPU
        config = GPUConfig(enabled=False)
        selection = select_device(config)
        assert selection.device == "cpu"
        print("  ✓ Disabled GPU falls back to CPU")

        return True
    except AssertionError as e:
        print(f"  ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Device selection failed: {e}")
        return False


def test_memory_functions() -> bool:
    """Test memory management functions."""
    print("Testing memory functions...")
    try:
        from video2d3d.utils.gpu import (
            estimate_memory_requirement,
            get_memory_usage,
            clear_gpu_memory,
        )

        # Test memory estimation
        mem_mb = estimate_memory_requirement(
            batch_size=4,
            image_height=384,
            image_width=384,
            channels=3,
        )
        assert mem_mb > 0, "Memory estimate should be positive"
        print(f"  Memory estimate for batch_size=4, 384x384: {mem_mb:.2f} MB")

        # Test get_memory_usage (should return zeros on CPU)
        used, free, total = get_memory_usage("cpu")
        print(f"  Memory usage (CPU): used={used:.0f}, free={free:.0f}, total={total:.0f}")

        # Test clear_gpu_memory (should not crash)
        clear_gpu_memory()
        print("  ✓ Memory functions working")

        return True
    except AssertionError as e:
        print(f"  ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Memory functions failed: {e}")
        return False


def test_batch_size_computation() -> bool:
    """Test optimal batch size computation."""
    print("Testing batch size computation...")
    try:
        from video2d3d.utils.gpu import GPUConfig, compute_optimal_batch_size

        # Test with auto disabled
        config = GPUConfig(batch_size_auto=False)
        batch_size = compute_optimal_batch_size(config, 384, 384)
        assert batch_size == 4, f"Expected 4, got {batch_size}"
        print(f"  Batch size (auto disabled): {batch_size}")

        # Test with auto enabled (will use min on CPU)
        config = GPUConfig(batch_size_auto=True, min_batch_size=1, max_batch_size=32)
        batch_size = compute_optimal_batch_size(config, 384, 384)
        assert batch_size >= config.min_batch_size
        assert batch_size <= config.max_batch_size
        print(f"  Batch size (auto enabled): {batch_size}")

        print("  ✓ Batch size computation working")
        return True
    except AssertionError as e:
        print(f"  ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Batch size computation failed: {e}")
        return False


def test_depth_estimator_integration() -> bool:
    """Test DepthEstimator integration with GPU utilities."""
    print("Testing DepthEstimator integration...")
    try:
        from video2d3d.depth import DepthEstimator, MiDaSConfig

        # Test default configuration
        config = MiDaSConfig()
        print(f"  Default device: {config.device}")
        print(f"  Auto batch size: {config.auto_batch_size}")
        print(f"  Fallback to CPU: {config.fallback_to_cpu}")

        # Test initialization
        estimator = DepthEstimator()
        print(f"  Estimator device: {estimator.config.device}")

        # Verify GPU config is set
        assert estimator.config.gpu_config is not None
        print("  ✓ GPU config integrated into MiDaSConfig")

        print("  ✓ DepthEstimator integration working")
        return True
    except AssertionError as e:
        print(f"  ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ DepthEstimator integration failed: {e}")
        return False


def test_exceptions() -> bool:
    """Test custom exceptions."""
    print("Testing custom exceptions...")
    try:
        from video2d3d.utils.gpu import GPUError, OutOfMemoryError

        # Test GPUError
        error = GPUError("Test error", device="cuda:0")
        assert str(error) == "Test error"
        assert error.device == "cuda:0"
        print("  ✓ GPUError works")

        # Test OutOfMemoryError
        oom_error = OutOfMemoryError("OOM", device="cuda:0")
        assert isinstance(oom_error, GPUError)
        print("  ✓ OutOfMemoryError inherits from GPUError")

        return True
    except AssertionError as e:
        print(f"  ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Exception tests failed: {e}")
        return False


def test_config_integration() -> bool:
    """Test ProcessingConfig integration."""
    print("Testing ProcessingConfig integration...")
    try:
        from video2d3d.utils.config import ProcessingConfig

        config = ProcessingConfig()

        # Check new GPU fields
        assert hasattr(config, "auto_batch_size")
        assert hasattr(config, "memory_fraction")
        assert hasattr(config, "fallback_to_cpu")
        assert hasattr(config, "pinned_memory")

        print(f"  Auto batch size: {config.auto_batch_size}")
        print(f"  Memory fraction: {config.memory_fraction}")
        print(f"  Fallback to CPU: {config.fallback_to_cpu}")
        print(f"  Pinned memory: {config.pinned_memory}")

        print("  ✓ ProcessingConfig integration working")
        return True
    except AssertionError as e:
        print(f"  ✗ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ ProcessingConfig integration failed: {e}")
        return False


def main() -> int:
    """Run all verification tests."""
    print("=" * 60)
    print("GPU Acceleration Feature Verification")
    print("=" * 60)
    print()

    tests = [
        ("GPU Module Imports", test_gpu_module_imports),
        ("Device Detection", test_device_detection),
        ("Device Selection", test_device_selection),
        ("Memory Functions", test_memory_functions),
        ("Batch Size Computation", test_batch_size_computation),
        ("DepthEstimator Integration", test_depth_estimator_integration),
        ("Custom Exceptions", test_exceptions),
        ("ProcessingConfig Integration", test_config_integration),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n[{name}]")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
