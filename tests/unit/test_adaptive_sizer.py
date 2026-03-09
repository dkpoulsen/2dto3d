import pytest

pytestmark = pytest.mark.slow

"""Unit tests for adaptive batch sizing.

Tests cover:
- AdaptiveBatchConfig validation
- AdaptiveBatchSizer functionality
- Batch size adjustment logic
- Callback system
- Thread safety
- Context manager
"""

from __future__ import annotations

import sys
import threading
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def mock_dependencies() -> Generator[None, None, None]:
    """Mock dependencies for adaptive sizer tests."""
    # Store original modules
    original_modules = {}
    modules_to_mock = [
        "torch",
        "loguru",
    ]

    for mod in modules_to_mock:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]

    # Create mock torch
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.cuda.device_count.return_value = 0
    mock_torch.cuda.get_device_properties = MagicMock()
    mock_torch.cuda.mem_get_info = MagicMock(return_value=(4 * 1024**3, 8 * 1024**3))
    mock_torch.cuda.set_device = MagicMock()

    sys.modules["torch"] = mock_torch

    # Mock loguru
    sys.modules["loguru"] = MagicMock()

    # Mock video2d3d.utils.logger
    mock_logger_module = MagicMock()
    mock_logger_module.get_logger = MagicMock(return_value=MagicMock())
    mock_logger_module.log_exception = MagicMock()

    if "video2d3d.utils.logger" in sys.modules:
        original_modules["video2d3d.utils.logger"] = sys.modules["video2d3d.utils.logger"]
    sys.modules["video2d3d.utils.logger"] = mock_logger_module

    # Clear any cached imports
    for mod in [
        "video2d3d.utils.gpu",
        "video2d3d.utils.memory_monitor",
        "video2d3d.batch.adaptive_sizer",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]

    yield

    original_modules

    # Restore original modules
    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    # Clear cached imports
    for mod in [
        "video2d3d.utils.gpu",
        "video2d3d.utils.memory_monitor",
        "video2d3d.batch.adaptive_sizer",
    ]:
        if mod in sys.modules:
            del sys.modules[mod]


@pytest.fixture
def mock_memory_monitor() -> Generator[MagicMock, None, None]:
    """Mock memory monitor for controlled testing."""
    with patch("video2d3d.utils.memory_monitor.get_current_memory_info") as mock:
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        info = MemoryInfo(
            total_mb=16384.0,
            available_mb=8192.0,
            used_mb=8192.0,
            percent=50.0,
            process_mb=1024.0,
            process_percent=6.25,
            warning_level=MemoryWarningLevel.NORMAL,
        )
        mock.return_value = info
        yield mock


@pytest.fixture
def mock_gpu_utils() -> Generator[dict[str, MagicMock], None, None]:
    """Mock GPU utilities."""
    with (
        patch("video2d3d.utils.gpu.is_cuda_available") as mock_cuda_avail,
        patch("video2d3d.utils.gpu.get_gpu_info") as mock_get_gpu,
        patch("video2d3d.utils.gpu.get_memory_usage") as mock_mem_usage,
    ):
        mock_cuda_avail.return_value = False
        mock_get_gpu.return_value = None
        mock_mem_usage.return_value = (4000.0, 4000.0, 8000.0)

        yield {
            "is_cuda_available": mock_cuda_avail,
            "get_gpu_info": mock_get_gpu,
            "get_memory_usage": mock_mem_usage,
        }


class TestAdjustmentReason:
    """Tests for AdjustmentReason enum."""

    def test_reasons_exist(self) -> None:
        """Test all adjustment reasons are defined."""
        from video2d3d.batch.adaptive_sizer import AdjustmentReason

        assert hasattr(AdjustmentReason, "MEMORY_PRESSURE")
        assert hasattr(AdjustmentReason, "MEMORY_AVAILABLE")
        assert hasattr(AdjustmentReason, "GPU_UNDERUTILIZED")
        assert hasattr(AdjustmentReason, "GPU_OVERLOADED")
        assert hasattr(AdjustmentReason, "OOM_RECOVERY")
        assert hasattr(AdjustmentReason, "MANUAL")
        assert hasattr(AdjustmentReason, "INITIALIZATION")

    def test_reasons_unique(self) -> None:
        """Test adjustment reasons have unique values."""
        from video2d3d.batch.adaptive_sizer import AdjustmentReason

        values = [reason.value for reason in AdjustmentReason]
        assert len(values) == len(set(values))


class TestAdaptiveBatchConfig:
    """Tests for AdaptiveBatchConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        config = AdaptiveBatchConfig()

        assert config.enabled is True
        assert config.initial_batch_size == 4
        assert config.min_batch_size == 1
        assert config.max_batch_size == 64
        assert config.memory_high_threshold == 0.80
        assert config.memory_low_threshold == 0.50
        assert config.gpu_util_low_threshold == 0.60
        assert config.gpu_util_high_threshold == 0.95
        assert config.scale_up_factor == 1.5
        assert config.scale_down_factor == 0.5

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        config = AdaptiveBatchConfig(
            enabled=False,
            initial_batch_size=8,
            min_batch_size=2,
            max_batch_size=32,
            memory_high_threshold=0.85,
            memory_low_threshold=0.40,
        )

        assert config.enabled is False
        assert config.initial_batch_size == 8
        assert config.min_batch_size == 2
        assert config.max_batch_size == 32
        assert config.memory_high_threshold == 0.85
        assert config.memory_low_threshold == 0.40

    def test_invalid_min_batch_size(self) -> None:
        """Test invalid min_batch_size raises error."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        with pytest.raises(ValueError, match="min_batch_size must be >= 1"):
            AdaptiveBatchConfig(min_batch_size=0)

    def test_invalid_max_batch_size(self) -> None:
        """Test max_batch_size < min_batch_size raises error."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        with pytest.raises(ValueError, match="max_batch_size .* must be >= min_batch_size"):
            AdaptiveBatchConfig(min_batch_size=10, max_batch_size=5)

    def test_invalid_memory_thresholds(self) -> None:
        """Test invalid memory threshold order raises error."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        with pytest.raises(ValueError, match="Thresholds must satisfy"):
            AdaptiveBatchConfig(
                memory_low_threshold=0.8,
                memory_high_threshold=0.5,
            )

    def test_invalid_gpu_thresholds(self) -> None:
        """Test invalid GPU threshold order raises error."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        with pytest.raises(ValueError, match="GPU thresholds must satisfy"):
            AdaptiveBatchConfig(
                gpu_util_low_threshold=0.9,
                gpu_util_high_threshold=0.7,
            )

    def test_invalid_scale_up_factor(self) -> None:
        """Test invalid scale_up_factor raises error."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        with pytest.raises(ValueError, match="scale_up_factor must be > 1.0"):
            AdaptiveBatchConfig(scale_up_factor=1.0)

        with pytest.raises(ValueError, match="scale_up_factor must be > 1.0"):
            AdaptiveBatchConfig(scale_up_factor=0.5)

    def test_invalid_scale_down_factor(self) -> None:
        """Test invalid scale_down_factor raises error."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        with pytest.raises(ValueError, match="scale_down_factor must be between 0 and 1"):
            AdaptiveBatchConfig(scale_down_factor=0)

        with pytest.raises(ValueError, match="scale_down_factor must be between 0 and 1"):
            AdaptiveBatchConfig(scale_down_factor=1.5)

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        config = AdaptiveBatchConfig(initial_batch_size=8, min_batch_size=2)
        data = config.to_dict()

        assert data["initial_batch_size"] == 8
        assert data["min_batch_size"] == 2
        assert data["enabled"] is True

    def test_from_dict(self) -> None:
        """Test from_dict deserialization."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig

        data = {
            "enabled": False,
            "initial_batch_size": 16,
            "min_batch_size": 4,
            "max_batch_size": 128,
        }
        config = AdaptiveBatchConfig.from_dict(data)

        assert config.enabled is False
        assert config.initial_batch_size == 16
        assert config.min_batch_size == 4
        assert config.max_batch_size == 128


class TestBatchSizeHistory:
    """Tests for BatchSizeHistory dataclass."""

    def test_add_sample(self) -> None:
        """Test adding samples to history."""
        from video2d3d.batch.adaptive_sizer import BatchSizeHistory

        history = BatchSizeHistory()
        history.add_sample(batch_size=4, memory_usage=0.5, gpu_util=0.6)

        assert len(history.batch_sizes) == 1
        assert history.batch_sizes[0] == 4
        assert history.memory_usages[0] == 0.5
        assert history.gpu_utils[0] == 0.6

    def test_max_history_limit(self) -> None:
        """Test history is trimmed to max_history."""
        from video2d3d.batch.adaptive_sizer import BatchSizeHistory

        history = BatchSizeHistory(max_history=5)

        for i in range(10):
            history.add_sample(batch_size=i, memory_usage=0.5, gpu_util=0.5)

        assert len(history.batch_sizes) == 5
        assert history.batch_sizes == [5, 6, 7, 8, 9]

    def test_get_recent_average_empty(self) -> None:
        """Test get_recent_average with empty history."""
        from video2d3d.batch.adaptive_sizer import BatchSizeHistory

        history = BatchSizeHistory()
        avg_batch, avg_mem, avg_gpu = history.get_recent_average()

        assert avg_batch == 0.0
        assert avg_mem == 0.0
        assert avg_gpu == 0.0

    def test_get_recent_average(self) -> None:
        """Test get_recent_average calculation."""
        from video2d3d.batch.adaptive_sizer import BatchSizeHistory

        history = BatchSizeHistory()
        for i in range(5):
            history.add_sample(batch_size=i + 1, memory_usage=0.5 * (i + 1), gpu_util=0.3)

        avg_batch, avg_mem, avg_gpu = history.get_recent_average(window=3)

        assert avg_batch == 4.0  # (3 + 4 + 5) / 3
        assert avg_mem == 2.0  # (1.5 + 2.0 + 2.5) / 3
        assert avg_gpu == 0.3


class TestAdaptiveBatchSizer:
    """Tests for AdaptiveBatchSizer class."""

    def test_initialization_default(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test initialization with default config."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()

        assert sizer.current_batch_size == 4
        assert sizer.is_monitoring is False

    def test_initialization_custom(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test initialization with custom config."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(initial_batch_size=8, min_batch_size=2, max_batch_size=32)
        sizer = AdaptiveBatchSizer(config)

        assert sizer.current_batch_size == 8
        assert sizer.config.min_batch_size == 2
        assert sizer.config.max_batch_size == 32

    def test_get_batch_size(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test get_batch_size returns current batch size."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        assert sizer.get_batch_size() == 4

    def test_set_batch_size_manual(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test manually setting batch size."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer, AdjustmentReason

        sizer = AdaptiveBatchSizer()
        new_size = sizer.set_batch_size(16, AdjustmentReason.MANUAL)

        assert new_size == 16
        assert sizer.current_batch_size == 16

    def test_set_batch_size_clamped(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test batch size is clamped to min/max bounds."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(min_batch_size=2, max_batch_size=16)
        sizer = AdaptiveBatchSizer(config)

        # Test below min
        sizer.set_batch_size(1, AdjustmentReason.MANUAL)
        assert sizer.current_batch_size == 2

        # Test above max
        sizer.set_batch_size(32, AdjustmentReason.MANUAL)
        assert sizer.current_batch_size == 16

    def test_add_callback(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test adding callbacks."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        callback = MagicMock()

        sizer.add_callback(callback)
        assert callback in sizer._callbacks

    def test_remove_callback(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test removing callbacks."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        callback = MagicMock()

        sizer.add_callback(callback)
        result = sizer.remove_callback(callback)

        assert result is True
        assert callback not in sizer._callbacks

    def test_remove_nonexistent_callback(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test removing a callback that doesn't exist."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        callback = MagicMock()

        result = sizer.remove_callback(callback)
        assert result is False

    def test_clear_callbacks(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test clearing all callbacks."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        sizer.add_callback(MagicMock())
        sizer.add_callback(MagicMock())

        sizer.clear_callbacks()
        assert len(sizer._callbacks) == 0

    # MS|    def test_callback_invoked_on_change(
    # MR|        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    # BJ|    ) -> None:
    # PH|        """Test callback is invoked when batch size changes."""
    # ZM|        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer, AdjustmentReason
    # HP|
    # YJ|        sizer = AdaptiveBatchSizer()
    # NP|        callback = MagicMock()
    # NZ|        sizer.add_callback(callback)
    # SZ|
    # KW|        sizer.set_batch_size(8, AdjustmentReason.MANUAL)
    # PM|
    # SW|        callback.assert_called_once()
    # MB|        args = callback.call_args[0]
    # QQ|        # Callback signature is (old_size, new_size, reason)
    # MR|        assert args[0] == 4  # old size
    # VV|        assert args[1] == 8  # new size
    # YR|        assert args[2] == AdjustmentReason.MANUAL
    # JX|
    def test_handle_oom_error(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test OOM error handling reduces batch size."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(initial_batch_size=8)
        sizer = AdaptiveBatchSizer(config)

        new_size = sizer.handle_oom_error()

        assert new_size == 4  # Halved from 8
        assert sizer.current_batch_size == 4

    def test_handle_oom_error_at_min(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test OOM error at minimum batch size stays at minimum."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(initial_batch_size=1, min_batch_size=1)
        sizer = AdaptiveBatchSizer(config)

        new_size = sizer.handle_oom_error()

        assert new_size == 1

    def test_disabled_no_adjustment(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test disabled config doesn't adjust batch size."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(enabled=False, initial_batch_size=4)
        sizer = AdaptiveBatchSizer(config)

        # Even with high memory pressure, should not adjust
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

        assert result == 4  # Should not change

    def test_config_setter_updates_bounds(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test config setter clamps current batch size to new bounds."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        sizer._current_batch_size = 32

        # Update config with lower max
        new_config = AdaptiveBatchConfig(max_batch_size=16)
        sizer.config = new_config

        assert sizer.current_batch_size == 16  # Clamped to new max


class TestBatchSizeScaling:
    """Tests for batch size scaling logic."""

    def test_scale_down_on_memory_pressure(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test batch size scales down under memory pressure."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(
            initial_batch_size=10,
            memory_high_threshold=0.80,
            scale_down_factor=0.5,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0  # Clear cooldown

        callback = MagicMock()
        sizer.add_callback(callback)

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

            sizer.adjust_batch_size()

        # Should have scaled down
        assert sizer.current_batch_size < 10
        callback.assert_called()
        assert callback.call_args[0][2] == AdjustmentReason.MEMORY_PRESSURE

    def test_no_negative_batch_size_on_scale_down(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test batch size never goes below min_batch_size even with extreme scale down."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(
            initial_batch_size=1,  # Start at minimum
            min_batch_size=1,
            memory_high_threshold=0.80,
            scale_down_factor=0.5,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0  # Clear cooldown

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

            sizer.adjust_batch_size()

        # Should stay at minimum, never go below
        assert sizer.current_batch_size >= config.min_batch_size

    def test_scale_up_on_memory_available(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test batch size scales up when memory is available."""
        from video2d3d.batch.adaptive_sizer import (
            AdaptiveBatchConfig,
            AdaptiveBatchSizer,
            AdjustmentReason,
        )

        config = AdaptiveBatchConfig(
            initial_batch_size=4,
            memory_low_threshold=0.50,
            scale_up_factor=1.5,
        )
        sizer = AdaptiveBatchSizer(config)
        sizer._last_adjustment_time = 0  # Clear cooldown

        callback = MagicMock()
        sizer.add_callback(callback)

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
            mock_state.return_value = (low_memory_info, None, 0.0)

            sizer.adjust_batch_size()

        # Should have scaled up
        assert sizer.current_batch_size > 4
        callback.assert_called()
        assert callback.call_args[0][2] == AdjustmentReason.MEMORY_AVAILABLE


class TestMonitoring:
    """Tests for automatic monitoring functionality."""

    def test_start_stop_monitoring(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test starting and stopping monitoring."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(adjustment_interval=0.1)
        sizer = AdaptiveBatchSizer(config)

        assert sizer.is_monitoring is False

        sizer.start_monitoring()
        assert sizer.is_monitoring is True

        time.sleep(0.3)  # Let it run a bit

        sizer.stop_monitoring()
        assert sizer.is_monitoring is False

    def test_double_start_warning(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test starting monitoring twice logs warning."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()

        sizer.start_monitoring()
        assert sizer.is_monitoring is True

        # Second start should not create new thread
        sizer.start_monitoring()
        assert sizer.is_monitoring is True

        sizer.stop_monitoring()

    def test_disabled_does_not_start(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test disabled config does not start monitoring."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchConfig, AdaptiveBatchSizer

        config = AdaptiveBatchConfig(enabled=False)
        sizer = AdaptiveBatchSizer(config)

        sizer.start_monitoring()
        assert sizer.is_monitoring is False


class TestContextManager:
    """Tests for adaptive_batch_sizer_context context manager."""

    def test_context_manager_basic(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test basic context manager usage."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer, adaptive_batch_sizer_context

        with adaptive_batch_sizer_context() as sizer:
            assert isinstance(sizer, AdaptiveBatchSizer)
            assert sizer.current_batch_size > 0

    def test_context_manager_with_callback(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test context manager with callback."""
        from video2d3d.batch.adaptive_sizer import adaptive_batch_sizer_context

        callback = MagicMock()

        with adaptive_batch_sizer_context(callback=callback) as sizer:
            assert callback in sizer._callbacks

    def test_context_manager_stops_monitoring(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test context manager stops monitoring on exit."""
        from video2d3d.batch.adaptive_sizer import adaptive_batch_sizer_context

        with adaptive_batch_sizer_context() as sizer:
            sizer.start_monitoring()
            assert sizer.is_monitoring is True

        # After exit, monitoring should be stopped
        assert sizer.is_monitoring is False


class TestFactoryFunction:
    """Tests for create_adaptive_sizer factory function."""

    def test_factory_default(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test factory with default parameters."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer, create_adaptive_sizer

        sizer = create_adaptive_sizer()

        assert isinstance(sizer, AdaptiveBatchSizer)
        assert sizer.current_batch_size == 4

    def test_factory_custom(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test factory with custom parameters."""
        from video2d3d.batch.adaptive_sizer import create_adaptive_sizer

        sizer = create_adaptive_sizer(
            initial_batch_size=16,
            min_batch_size=4,
            max_batch_size=64,
        )

        assert sizer.current_batch_size == 16
        assert sizer.config.min_batch_size == 4
        assert sizer.config.max_batch_size == 64


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d.batch import adaptive_sizer

        expected_exports = [
            "AdjustmentReason",
            "AdaptiveBatchConfig",
            "BatchSizeHistory",
            "AdaptiveBatchSizer",
            "create_adaptive_sizer",
            "adaptive_batch_sizer_context",
            "BatchSizeCallback",
            "DEFAULT_MEMORY_HIGH_THRESHOLD",
            "DEFAULT_MEMORY_LOW_THRESHOLD",
            "DEFAULT_INITIAL_BATCH_SIZE",
            "DEFAULT_MIN_BATCH_SIZE",
            "DEFAULT_MAX_BATCH_SIZE",
        ]

        for export in expected_exports:
            assert export in adaptive_sizer.__all__, f"Missing export: {export}"


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_batch_size_access(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test concurrent access to batch size is thread-safe."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer, AdjustmentReason

        sizer = AdaptiveBatchSizer()
        errors: list[Exception] = []

        def reader():
            for _ in range(100):
                try:
                    _ = sizer.current_batch_size
                    _ = sizer.get_batch_size()
                except Exception as e:
                    errors.append(e)

        def writer():
            for i in range(100):
                try:
                    sizer.set_batch_size((i % 10) + 1, AdjustmentReason.MANUAL)
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        threads += [threading.Thread(target=writer) for _ in range(2)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_callback_modification(
        self, mock_memory_monitor: MagicMock, mock_gpu_utils: dict[str, MagicMock]
    ) -> None:
        """Test concurrent callback add/remove is thread-safe."""
        from video2d3d.batch.adaptive_sizer import AdaptiveBatchSizer

        sizer = AdaptiveBatchSizer()
        errors: list[Exception] = []

        def adder():
            for _ in range(50):
                try:
                    sizer.add_callback(MagicMock())
                except Exception as e:
                    errors.append(e)

        def remover():
            for _ in range(50):
                try:
                    sizer.remove_callback(MagicMock())
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=adder) for _ in range(3)]
        threads += [threading.Thread(target=remover) for _ in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# Mark as slow test
import pytest
pytestmark = pytest.mark.slow
