"""Integration tests for adaptive batch sizing.

These tests verify the adaptive batch sizing works correctly with real
memory monitoring and (when available) GPU monitoring components.

Note: These tests use actual system calls and should be run in a controlled
environment. GPU tests are skipped if CUDA is not available.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def no_mock_dependencies() -> Generator[None, None, None]:
    """Ensure no mocking for integration tests."""
    # Just yield - we want real dependencies for integration tests
    yield


class TestMemoryMonitorIntegration:
    """Integration tests with real memory monitoring."""

    def test_real_memory_info_retrieval(self, no_mock_dependencies: None) -> None:
        """Test that real memory info can be retrieved."""
        from video2d3d.utils.memory_monitor import get_current_memory_info

        info = get_current_memory_info()

        assert info is not None
        assert info.total_mb > 0
        assert info.available_mb >= 0
        assert info.used_mb >= 0
        assert 0 <= info.percent <= 100

    def test_sizer_uses_real_memory(self, no_mock_dependencies: None) -> None:
        """Test that sizer correctly uses real memory info."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(
            initial_batch_size=4,
            min_batch_size=1,
            max_batch_size=32,
        )
        sizer = AdaptiveBatchSizer(config)

        # Get real system state
        memory_info, gpu_info, gpu_util = sizer._get_system_state()

        assert memory_info is not None
        assert memory_info.total_mb > 0

    def test_sizer_adjustment_with_real_memory(self, no_mock_dependencies: None) -> None:
        """Test that sizer can adjust based on real memory state."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        # Use a config that will likely trigger adjustments
        config = AdaptiveBatchConfig(
            initial_batch_size=8,
            min_batch_size=1,
            max_batch_size=64,
            adjustment_interval=0.1,
            cooldown_period=0.1,
        )
        sizer = AdaptiveBatchSizer(config)

        # Perform an adjustment
        result = sizer.adjust_batch_size()

        # Should return a valid batch size within bounds
        assert config.min_batch_size <= result <= config.max_batch_size


class TestAdaptiveBatchSizerIntegration:
    """Integration tests for AdaptiveBatchSizer with real components."""

    def test_sizer_initialization_and_basic_ops(self, no_mock_dependencies: None) -> None:
        """Test sizer initialization and basic operations."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(
            enabled=True,
            initial_batch_size=4,
            min_batch_size=1,
            max_batch_size=32,
        )
        sizer = AdaptiveBatchSizer(config)

        # Verify initial state
        assert sizer.current_batch_size == 4
        assert sizer.is_monitoring is False

        # Manual adjustment
        new_size = sizer.set_batch_size(8, AdjustmentReason.MANUAL)
        assert new_size == 8
        assert sizer.current_batch_size == 8

    def test_callback_invocation_with_real_components(self, no_mock_dependencies: None) -> None:
        """Test that callbacks are invoked correctly with real components."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(initial_batch_size=4)
        sizer = AdaptiveBatchSizer(config)

        callback_calls: list[tuple[int, int, AdjustmentReason]] = []

        def callback(old_size: int, new_size: int, reason: AdjustmentReason) -> None:
            callback_calls.append((old_size, new_size, reason))

        sizer.add_callback(callback)
        sizer.set_batch_size(8, AdjustmentReason.MANUAL)

        assert len(callback_calls) == 1
        assert callback_calls[0] == (4, 8, AdjustmentReason.MANUAL)

    def test_monitoring_start_stop_integration(self, no_mock_dependencies: None) -> None:
        """Test monitoring start/stop with real components."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(
            adjustment_interval=0.1,
            cooldown_period=0.05,
        )
        sizer = AdaptiveBatchSizer(config)

        assert sizer.is_monitoring is False

        sizer.start_monitoring()
        assert sizer.is_monitoring is True

        time.sleep(0.3)  # Let monitoring run

        sizer.stop_monitoring()
        assert sizer.is_monitoring is False

    def test_oom_handling_integration(self, no_mock_dependencies: None) -> None:
        """Test OOM error handling with real components."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(
            initial_batch_size=16,
            min_batch_size=1,
        )
        sizer = AdaptiveBatchSizer(config)

        # Simulate OOM
        new_size = sizer.handle_oom_error()

        assert new_size == 8  # Halved from 16
        assert sizer.current_batch_size == 8

        # Another OOM
        new_size = sizer.handle_oom_error()
        assert new_size == 4  # Halved from 8


class TestHistoryIntegration:
    """Integration tests for batch size history tracking."""

    def test_history_records_real_adjustments(self, no_mock_dependencies: None) -> None:
        """Test that history correctly records real adjustments."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(
            initial_batch_size=4,
            adjustment_interval=0.1,
            cooldown_period=0.05,
        )
        sizer = AdaptiveBatchSizer(config)

        # Make several adjustments
        sizer.set_batch_size(8, AdjustmentReason.MANUAL)
        sizer._last_adjustment_time = 0
        sizer.adjust_batch_size()
        sizer._last_adjustment_time = 0
        sizer.adjust_batch_size()

        # Check history
        history = sizer.history
        assert len(history.batch_sizes) > 0

        # Get recent average
        avg_batch, avg_mem, avg_gpu = history.get_recent_average()
        assert avg_batch > 0

    def test_history_with_stability_detection(self, no_mock_dependencies: None) -> None:
        """Test history works with stability detection."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(
            initial_batch_size=4,
            stability_window=3,
            adjustment_interval=0.1,
            cooldown_period=0.05,
        )
        sizer = AdaptiveBatchSizer(config)

        # Add stability samples manually
        sizer._stability_samples = [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5)]

        # Should detect as stable
        assert sizer._is_stable() is True


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_config_serialization_roundtrip(self, no_mock_dependencies: None) -> None:
        """Test that config can be serialized and deserialized."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        original = AdaptiveBatchConfig(
            enabled=True,
            initial_batch_size=16,
            min_batch_size=4,
            max_batch_size=64,
            memory_high_threshold=0.85,
            memory_low_threshold=0.40,
            scale_up_factor=2.0,
            scale_down_factor=0.3,
        )

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = AdaptiveBatchConfig.from_dict(data)

        assert restored.enabled == original.enabled
        assert restored.initial_batch_size == original.initial_batch_size
        assert restored.min_batch_size == original.min_batch_size
        assert restored.max_batch_size == original.max_batch_size
        assert restored.memory_high_threshold == original.memory_high_threshold
        assert restored.memory_low_threshold == original.memory_low_threshold
        assert restored.scale_up_factor == original.scale_up_factor
        assert restored.scale_down_factor == original.scale_down_factor


class TestContextManagerIntegration:
    """Integration tests for context manager usage."""

    def test_context_manager_integration(self, no_mock_dependencies: None) -> None:
        """Test context manager with real components."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer, adaptive_batch_sizer_context

        with adaptive_batch_sizer_context() as sizer:
            assert isinstance(sizer, AdaptiveBatchSizer)
            assert sizer.current_batch_size > 0

            # Can use the sizer
            batch_size = sizer.get_batch_size()
            assert batch_size > 0

        # Context manager should clean up
        assert sizer.is_monitoring is False

    def test_context_manager_with_callback(self, no_mock_dependencies: None) -> None:
        """Test context manager with callback."""
        from video2d3d.batch.adaptive_sizer import AdjustmentReason, adaptive_batch_sizer_context

        callback_calls: list[tuple[int, int, AdjustmentReason]] = []

        def callback(old_size: int, new_size: int, reason: AdjustmentReason) -> None:
            callback_calls.append((old_size, new_size, reason))

        with adaptive_batch_sizer_context(callback=callback) as sizer:
            sizer.set_batch_size(8, AdjustmentReason.MANUAL)

        assert len(callback_calls) == 1


class TestFactoryFunctionIntegration:
    """Integration tests for factory functions."""

    def test_create_adaptive_sizer_integration(self, no_mock_dependencies: None) -> None:
        """Test factory function with real components."""
        from video2d3d.batch.adaptive_sizer import create_adaptive_sizer

        sizer = create_adaptive_sizer(
            initial_batch_size=16,
            min_batch_size=4,
            max_batch_size=64,
        )

        assert sizer.current_batch_size == 16
        assert sizer.config.min_batch_size == 4
        assert sizer.config.max_batch_size == 64

        # Should be able to use it
        sizer.adjust_batch_size()


class TestModuleExportsIntegration:
    """Integration tests for module exports."""

    def test_all_exports_importable(self, no_mock_dependencies: None) -> None:
        """Test that all exports can be imported."""
        from video2d3d.batch import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
        )

        # Should be able to use them
        config = AdaptiveBatchConfig()
        sizer = AdaptiveBatchSizer(config)

        assert sizer is not None

    def test_from_main_module_import(self, no_mock_dependencies: None) -> None:
        """Test importing from main batch module."""
        import video2d3d.batch as batch_module

        assert hasattr(batch_module, "AdaptiveBatchSizer")
        assert hasattr(batch_module, "AdaptiveBatchConfig")
        assert hasattr(batch_module, "AdjustmentReason")
        assert hasattr(batch_module, "create_adaptive_sizer")


@pytest.mark.skipif(
    True,  # Skip by default - requires CUDA
    reason="GPU tests require CUDA-enabled GPU",
)
class TestGPUIntegration:
    """GPU integration tests (require CUDA)."""

    def test_gpu_detection(self, no_mock_dependencies: None) -> None:
        """Test GPU detection."""
        from video2d3d.utils.gpu import is_cuda_available

        if is_cuda_available():
            from video2d3d.utils.gpu import get_gpu_info

            gpu_info = get_gpu_info(0)
            assert gpu_info is not None
            assert gpu_info.total_memory_mb > 0

    def test_sizer_with_gpu(self, no_mock_dependencies: None) -> None:
        """Test sizer with real GPU monitoring."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer
        from video2d3d.utils.gpu import is_cuda_available

        if not is_cuda_available():
            pytest.skip("CUDA not available")

        sizer = AdaptiveBatchSizer()
        memory_info, gpu_info, gpu_util = sizer._get_system_state()

        assert gpu_info is not None
        assert gpu_util >= 0

    def test_gpu_based_adjustment(self, no_mock_dependencies: None) -> None:
        """Test GPU-based batch size adjustment."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer
        from video2d3d.utils.gpu import is_cuda_available

        if not is_cuda_available():
            pytest.skip("CUDA not available")

        config = AdaptiveBatchConfig(
            initial_batch_size=8,
            gpu_util_low_threshold=0.5,
            gpu_util_high_threshold=0.9,
        )
        sizer = AdaptiveBatchSizer(config)

        # Should adjust based on real GPU utilization
        sizer._last_adjustment_time = 0
        sizer.adjust_batch_size()

        # Batch size should be within bounds
        assert (
            sizer.config.min_batch_size <= sizer.current_batch_size <= sizer.config.max_batch_size
        )
