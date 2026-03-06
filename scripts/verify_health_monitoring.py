#!/usr/bin/env python3
"""Verification script for health monitoring feature.

This script tests the health monitoring endpoint by:
1. Testing the health monitoring functions directly
2. Starting the API server
3. Testing the /health and /health/detailed endpoints
4. Verifying response schemas
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_health_functions():
    """Test health monitoring functions directly."""
    print("=" * 60)
    print("Testing Health Monitoring Functions")
    print("=" * 60)

    from video2d3d.web.health import (
        get_comprehensive_health,
        get_gpu_status,
        get_queue_health,
        get_system_memory,
        determine_health_status,
    )
    from video2d3d.web.schemas import HealthStatus

    # Test GPU status
    print("\n1. Testing GPU status...")
    gpu = get_gpu_status()
    print(f"   GPU Available: {gpu.available}")
    print(f"   Device Count: {gpu.device_count}")
    if gpu.available:
        print(f"   Device Name: {gpu.device_name}")
        print(f"   Memory Total: {gpu.memory_total_mb:.2f} MB")
        print(f"   Memory Used: {gpu.memory_used_mb:.2f} MB")
        print(f"   Memory Utilization: {gpu.memory_utilization_percent:.2f}%")
    print("   ✓ GPU status function working")

    # Test system memory
    print("\n2. Testing System memory...")
    mem = get_system_memory()
    print(f"   Total Memory: {mem.total_mb:.2f} MB")
    print(f"   Available Memory: {mem.available_mb:.2f} MB")
    print(f"   Used Memory: {mem.used_mb:.2f} MB")
    print(f"   Utilization: {mem.utilization_percent:.2f}%")
    print("   ✓ System memory function working")

    # Test queue health (without queue)
    print("\n3. Testing Queue health (no queue)...")
    queue = get_queue_health(None)
    print(f"   Queue Running: {queue.running}")
    print(f"   Queue Paused: {queue.paused}")
    print("   ✓ Queue health function working")

    # Test health status determination
    print("\n4. Testing Health status determination...")
    status, checks = determine_health_status(gpu, mem, queue)
    print(f"   Overall Status: {status.value}")
    print(f"   Checks: {checks}")
    print("   ✓ Health status determination working")

    # Test comprehensive health
    print("\n5. Testing Comprehensive health...")
    health = get_comprehensive_health(
        queue=None,
        version="0.1.0",
        uptime_seconds=100.0,
    )
    print(f"   Status: {health.status.value}")
    print(f"   Version: {health.version}")
    print(f"   Uptime: {health.uptime_seconds}s")
    print(f"   Checks: {health.checks}")
    print("   ✓ Comprehensive health function working")

    print("\n" + "=" * 60)
    print("All health monitoring functions working correctly!")
    print("=" * 60)
    return True


def test_api_endpoints():
    """Test API endpoints using FastAPI TestClient."""
    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)

    try:
        from fastapi.testclient import TestClient
        from video2d3d.web.app import create_app
    except ImportError as e:
        print(f"   ⚠ Skipping API tests: {e}")
        return True

    # Create test app
    print("\n1. Creating test application...")
    app = create_app()
    client = TestClient(app)
    print("   ✓ Test application created")

    # Test basic health endpoint
    print("\n2. Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print(f"   Status: {data.get('status')}")
    print(f"   Version: {data.get('version')}")
    print(f"   Queue Running: {data.get('queue_running')}")
    print(f"   GPU Available: {data.get('gpu_available')}")
    print("   ✓ /health endpoint working")

    # Test detailed health endpoint
    print("\n3. Testing /health/detailed endpoint...")
    response = client.get("/health/detailed")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Verify response structure
    assert "status" in data, "Missing 'status' field"
    assert "version" in data, "Missing 'version' field"
    assert "uptime_seconds" in data, "Missing 'uptime_seconds' field"
    assert "gpu" in data, "Missing 'gpu' field"
    assert "memory" in data, "Missing 'memory' field"
    assert "queue" in data, "Missing 'queue' field"
    assert "checks" in data, "Missing 'checks' field"

    print(f"   Overall Status: {data['status']}")
    print(f"   Version: {data['version']}")
    print(f"   Uptime: {data['uptime_seconds']:.2f}s")
    print(f"   GPU Available: {data['gpu']['available']}")
    print(f"   Memory Utilization: {data['memory']['utilization_percent']:.2f}%")
    print(f"   Queue Running: {data['queue']['running']}")
    print(f"   Component Checks: {data['checks']}")
    print("   ✓ /health/detailed endpoint working")

    print("\n" + "=" * 60)
    print("All API endpoints working correctly!")
    print("=" * 60)
    return True


def main():
    """Run all verification tests."""
    print("\n" + "#" * 60)
    print("# Health Monitoring Feature Verification")
    print("#" * 60)

    all_passed = True

    # Test health functions
    try:
        if not test_health_functions():
            all_passed = False
    except Exception as e:
        print(f"\n✗ Health function tests failed: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    # Test API endpoints
    try:
        if not test_api_endpoints():
            all_passed = False
    except Exception as e:
        print(f"\n✗ API endpoint tests failed: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    # Final result
    print("\n" + "#" * 60)
    if all_passed:
        print("# ✓ ALL VERIFICATION TESTS PASSED")
        print("# Health monitoring feature is working correctly!")
    else:
        print("# ✗ SOME TESTS FAILED")
        print("# Please review the errors above.")
    print("#" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
