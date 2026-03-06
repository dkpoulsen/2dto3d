"""Additional unit tests for adaptive batch sizing - Part 2.

These tests cover areas not fully tested in the main test file:
- Cooldown period enforcement
- Stability detection
- Recommended batch size calculation
- GPU-based scaling
- Edge cases

These tests are written to match the actual implementation.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


# Re-use fixtures from the main test file
# These tests assume the mock_dependencies fixture is active


class TestCooldownPeriod:
    """Tests for cooldown period enforcement."""

    def test_is_in_cooldown_initially_false(self) -> None:
        """Test that cooldown is False initially."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        assert sizer._is_in_cooldown() is False

    def test_is_in_cooldown_after_adjustment(self) -> None:
        """Test that cooldown is True after adjustment."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(cooldown_period=5.0)
        sizer = AdaptiveBatchSizer(config)
        sizer.set_batch_size(8, AdjustmentReason.MANUAL)

        assert sizer._is_in_cooldown() is True

    def test_is_in_cooldown_expires(self) -> None:
        """Test that cooldown expires after cooldown_period."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(cooldown_period=0.01)  # 10ms cooldown
        sizer = AdaptiveBatchSizer(config)
        sizer.set_batch_size(8, AdjustmentReason.MANUAL)

        assert sizer._is_in_cooldown() is True

        time.sleep(0.05)  # Wait for cooldown to expire

        assert sizer._is_in_cooldown() is False

    def test_adjustment_skipped_during_cooldown(self) -> None:
        """Test that adjustment is skipped during cooldown."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(
            cooldown_period=5.0,
            initial_batch_size=4,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer.set_batch_size(8, AdjustmentReason.MANUAL)

        # Try to adjust during cooldown - should be skipped
        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            high_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=1000.0,
                used_mb=15384.0,
                percent=94.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.CRITICAL,
            )
            mock_state.return_value = (high_memory_info, None, 0.0)

            result = sizer.adjust_batch_size()

        # Should still be 8 (no adjustment due to cooldown)
        assert result == 8


class TestStabilityDetection:
    """Tests for system stability detection."""

    def test_is_stable_insufficient_samples(self) -> None:
        """Test that stability is False with insufficient samples."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()

        # No samples added yet
        assert sizer._is_stable() is False

        # Add one sample
        sizer._stability_samples.append((0.5, 0.5))
        assert sizer._is_stable() is False

    def test_is_stable_with_consistent_samples(self) -> None:
        """Test that stability is True with consistent samples."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(stability_window=3)
        sizer = AdaptiveBatchSizer(config)

        # Add consistent samples
        sizer._stability_samples = [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5)]

        assert sizer._is_stable() is True

    def test_is_stable_with_varying_samples(self) -> None:
        """Test that stability is False with varying samples."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(stability_window=3)
        sizer = AdaptiveBatchSizer(config)

        # Add highly varying samples
        sizer._stability_samples = [(0.1, 0.1), (0.9, 0.9), (0.1, 0.1)]

        assert sizer._is_stable() is False

    def test_is_stable_with_zero_mean(self) -> None:
        """Test stability with zero mean values (edge case)."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(stability_window=3)
        sizer = AdaptiveBatchSizer(config)

        # Add samples with zero mean
        sizer._stability_samples = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

        # Should be stable even with zero mean
        assert sizer._is_stable() is True


class TestRecommendedBatchSize:
    """Tests for get_recommended_batch_size method."""

    def test_recommended_batch_size_basic(self) -> None:
        """Test basic recommended batch size calculation."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()

        # get_recommended_batch_size uses internal _get_system_state
        recommended = sizer.get_recommended_batch_size(
            image_height=1080,
            image_width=1920,
        )

        assert recommended > 0
        assert recommended <= sizer.config.max_batch_size

    def test_recommended_batch_size_respects_max(self) -> None:
        """Test that recommended batch size respects max_batch_size."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(max_batch_size=8, initial_batch_size=8)
        sizer = AdaptiveBatchSizer(config)

        recommended = sizer.get_recommended_batch_size(
            image_height=1080,
            image_width=1920,
        )

        assert recommended <= 8

    def test_recommended_batch_size_respects_min(self) -> None:
        """Test that recommended batch size respects min_batch_size."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(min_batch_size=2)
        sizer = AdaptiveBatchSizer(config)

        recommended = sizer.get_recommended_batch_size(
            image_height=1080,
            image_width=1920,
        )

        assert recommended >= 2

    def test_recommended_batch_size_with_memory_pressure(self) -> None:
        """Test recommended batch size scales down under memory pressure."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(initial_batch_size=10)
        sizer = AdaptiveBatchSizer(config)

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            high_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=500.0,
                used_mb=15884.0,
                percent=97.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.CRITICAL,
            )
            mock_state.return_value = (high_memory_info, None, 0.5)

            recommended = sizer.get_recommended_batch_size()

        # Should scale down under memory pressure
        assert recommended < 10

    def test_recommended_batch_size_with_available_memory(self) -> None:
        """Test recommended batch size scales up with available memory."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(initial_batch_size=4)
        sizer = AdaptiveBatchSizer(config)

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            low_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=14000.0,
                used_mb=2384.0,
                percent=15.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.NORMAL,
            )
            mock_state.return_value = (low_memory_info, None, 0.3)

            recommended = sizer.get_recommended_batch_size()

        # Should scale up with available memory
        assert recommended > 4


class TestGPUScaling:
    """Tests for GPU-based batch scaling."""

    def test_scale_up_on_gpu_underutilized(self) -> None:
        """Test batch size scales up when GPU is underutilized."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )
        from video2d3d.utils.gpu import GPUInfo

        config = AdaptiveBatchConfig(
            initial_batch_size=4,
            gpu_util_low_threshold=0.60,
            scale_up_factor=1.5,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0  # Clear cooldown

        callback = MagicMock()
        sizer.add_callback(callback)

        # Mock GPU info with low utilization
        mock_gpu = MagicMock(spec=GPUInfo)
        mock_gpu.memory_utilization = 30.0  # 30% utilization

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            low_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=12000.0,
                used_mb=4384.0,
                percent=27.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.NORMAL,
            )
            mock_state.return_value = (low_memory_info, mock_gpu, 0.3)  # 30% GPU util

            sizer.adjust_batch_size()

        # Should have scaled up due to GPU underutilization
        assert sizer.current_batch_size > 4
        callback.assert_called()
        assert callback.call_args[0][2] == AdjustmentReason.GPU_UNDERUTILIZED

    def test_scale_down_on_gpu_overloaded(self) -> None:
        """Test batch size scales down when GPU is overloaded."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )
        from video2d3d.utils.gpu import GPUInfo

        config = AdaptiveBatchConfig(
            initial_batch_size=10,
            gpu_util_high_threshold=0.95,
            scale_down_factor=0.5,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0  # Clear cooldown

        callback = MagicMock()
        sizer.add_callback(callback)

        # Mock GPU info with high utilization
        mock_gpu = MagicMock(spec=GPUInfo)
        mock_gpu.memory_utilization = 98.0  # 98% utilization

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            normal_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=8192.0,
                used_mb=8192.0,
                percent=50.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.NORMAL,
            )
            mock_state.return_value = (normal_memory_info, mock_gpu, 0.98)  # 98% GPU util

            sizer.adjust_batch_size()

        # Should have scaled down due to GPU overload
        assert sizer.current_batch_size < 10
        callback.assert_called()
        assert callback.call_args[0][2] == AdjustmentReason.GPU_OVERLOADED


class TestHistoryTracking:
    """Additional tests for history tracking."""

    def test_history_tracks_all_adjustments(self) -> None:
        """Test that history tracks all adjustments."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(initial_batch_size=4)
        sizer = AdaptiveBatchSizer(config)

        # Make multiple adjustments
        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            normal_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=8192.0,
                used_mb=8192.0,
                percent=50.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.NORMAL,
            )
            mock_state.return_value = (normal_memory_info, None, 0.5)

            for _ in range(3):
                sizer.adjust_batch_size()
                sizer._last_adjustment_time = 0  # Clear cooldown for next adjustment

        # History should have tracked the adjustments
        assert len(sizer.history.batch_sizes) == 3

    def test_history_window_behavior(self) -> None:
        """Test that get_recent_average respects window parameter."""
        from video2d3d.batch.adaptive_sizer import BatchSizeHistory

        history = BatchSizeHistory()

        # Add 10 samples
        for i in range(10):
            history.add_sample(batch_size=i, memory_usage=0.5, gpu_util=0.5)

        # Get average with window of 3
        avg_batch, _, _ = history.get_recent_average(window=3)
        assert avg_batch == 8.0  # (7 + 8 + 9) / 3

        # Get average with window of 5
        avg_batch, _, _ = history.get_recent_average(window=5)
        assert avg_batch == 7.0  # (5 + 6 + 7 + 8 + 9) / 5


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_batch_size_at_max_no_scale_up(self) -> None:
        """Test that batch size doesn't exceed max even when resources available."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
        )

        config = AdaptiveBatchConfig(
            initial_batch_size=64,
            max_batch_size=64,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            low_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=14000.0,
                used_mb=2384.0,
                percent=15.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.NORMAL,
            )
            mock_state.return_value = (low_memory_info, None, 0.3)

            sizer.adjust_batch_size()

        # Should stay at max
        assert sizer.current_batch_size == 64

    def test_batch_size_at_min_no_scale_down(self) -> None:
        """Test that batch size doesn't go below min even under pressure."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
        )

        config = AdaptiveBatchConfig(
            initial_batch_size=1,
            min_batch_size=1,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            high_memory_info = MemoryInfo(
                total_mb=16384.0,
                available_mb=500.0,
                used_mb=15884.0,
                percent=97.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=MemoryWarningLevel.CRITICAL,
            )
            mock_state.return_value = (high_memory_info, None, 0.9)

            sizer.adjust_batch_size()

        # Should stay at minimum
        assert sizer.current_batch_size == 1

    def test_callback_exception_handling(self) -> None:
        """Test that callback exceptions don't crash the sizer."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        sizer = AdaptiveBatchSizer()

        # Add a callback that raises an exception
        def bad_callback(old: int, new: int, reason: object) -> None:
            raise RuntimeError("Callback failed")

        sizer.add_callback(bad_callback)

        # Should not raise - exception should be caught
        sizer.set_batch_size(8, AdjustmentReason.MANUAL)

        assert sizer.current_batch_size == 8

    def test_zero_memory_total_handling(self) -> None:
        """Test handling of zero total memory (edge case)."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        sizer._last_adjustment_time = 0

        with patch.object(sizer, "_get_system_state") as mock_state:
            from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

            # Edge case: zero total memory
            zero_memory_info = MemoryInfo(
                total_mb=0.0,
                available_mb=0.0,
                used_mb=0.0,
                percent=0.0,
                process_mb=0.0,
                process_percent=0.0,
                warning_level=MemoryWarningLevel.NORMAL,
            )
            mock_state.return_value = (zero_memory_info, None, 0.0)

            # Should not crash
            result = sizer.adjust_batch_size()

        assert result > 0  # Should still have a valid batch size
