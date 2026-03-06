"""Unit tests for memory monitoring utilities.

Tests cover:
- Memory info retrieval
- Warning level detection
- Callback system
- Garbage collection
- Context manager
- Singleton pattern
"""

from __future__ import annotations

import gc
import sys
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def reset_memory_monitor_singleton() -> Generator[None, None, None]:
    """Reset MemoryMonitor singleton before and after each test."""
    # Reset before test
    if "video2d3d.utils.memory_monitor" in sys.modules:
        from video2d3d.utils.memory_monitor import MemoryMonitor

        MemoryMonitor.reset_instance()
        del sys.modules["video2d3d.utils.memory_monitor"]

    yield

    # Reset after test
    if "video2d3d.utils.memory_monitor" in sys.modules:
        from video2d3d.utils.memory_monitor import MemoryMonitor

        MemoryMonitor.reset_instance()
        del sys.modules["video2d3d.utils.memory_monitor"]


@pytest.fixture
def mock_psutil() -> Generator[MagicMock, None, None]:
    """Mock psutil for controlled testing."""
    with patch("video2d3d.utils.memory_monitor.psutil") as mock:
        # Mock virtual_memory
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3  # 16 GB
        mock_mem.available = 4 * 1024**3  # 4 GB available (75% used)
        mock_mem.used = 12 * 1024**3  # 12 GB used
        mock_mem.percent = 75.0
        mock.virtual_memory.return_value = mock_mem

        # Mock Process
        mock_process = MagicMock()
        mock_process_info = MagicMock()
        mock_process_info.rss = 1 * 1024**3  # 1 GB
        mock_process.memory_info.return_value = mock_process_info
        mock.Process.return_value = mock_process

        yield mock


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock logger module."""
    with patch("video2d3d.utils.memory_monitor.get_logger") as mock_get_logger:
        mock_log = MagicMock()
        mock_get_logger.return_value = mock_log
        yield mock_log


class TestMemoryWarningLevel:
    """Tests for MemoryWarningLevel enum."""

    def test_warning_levels_exist(self) -> None:
        """Test all warning levels are defined."""
        from video2d3d.utils.memory_monitor import MemoryWarningLevel

        assert hasattr(MemoryWarningLevel, "NORMAL")
        assert hasattr(MemoryWarningLevel, "WARNING")
        assert hasattr(MemoryWarningLevel, "CRITICAL")
        assert hasattr(MemoryWarningLevel, "EMERGENCY")

    def test_warning_levels_unique(self) -> None:
        """Test warning levels have unique values."""
        from video2d3d.utils.memory_monitor import MemoryWarningLevel

        levels = [level.value for level in MemoryWarningLevel]
        assert len(levels) == len(set(levels))


class TestMemoryInfo:
    """Tests for MemoryInfo dataclass."""

    def test_memory_info_creation(self) -> None:
        """Test creating MemoryInfo with all fields."""
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        info = MemoryInfo(
            total_mb=16384.0,
            available_mb=4096.0,
            used_mb=12288.0,
            percent=75.0,
            process_mb=1024.0,
            process_percent=6.25,
            warning_level=MemoryWarningLevel.WARNING,
        )

        assert info.total_mb == 16384.0
        assert info.available_mb == 4096.0
        assert info.used_mb == 12288.0
        assert info.percent == 75.0
        assert info.process_mb == 1024.0
        assert info.process_percent == 6.25
        assert info.warning_level == MemoryWarningLevel.WARNING

    def test_is_warning_true(self) -> None:
        """Test is_warning property returns True for warning level."""
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        for level in [
            MemoryWarningLevel.WARNING,
            MemoryWarningLevel.CRITICAL,
            MemoryWarningLevel.EMERGENCY,
        ]:
            info = MemoryInfo(
                total_mb=16384.0,
                available_mb=4096.0,
                used_mb=12288.0,
                percent=75.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=level,
            )
            assert info.is_warning is True

    def test_is_warning_false(self) -> None:
        """Test is_warning property returns False for normal level."""
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        info = MemoryInfo(
            total_mb=16384.0,
            available_mb=4096.0,
            used_mb=12288.0,
            percent=75.0,
            process_mb=1024.0,
            process_percent=6.25,
            warning_level=MemoryWarningLevel.NORMAL,
        )
        assert info.is_warning is False

    def test_is_critical_true(self) -> None:
        """Test is_critical property returns True for critical and emergency."""
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        for level in [MemoryWarningLevel.CRITICAL, MemoryWarningLevel.EMERGENCY]:
            info = MemoryInfo(
                total_mb=16384.0,
                available_mb=4096.0,
                used_mb=12288.0,
                percent=75.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=level,
            )
            assert info.is_critical is True

    def test_is_critical_false(self) -> None:
        """Test is_critical property returns False for normal and warning."""
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        for level in [MemoryWarningLevel.NORMAL, MemoryWarningLevel.WARNING]:
            info = MemoryInfo(
                total_mb=16384.0,
                available_mb=4096.0,
                used_mb=12288.0,
                percent=75.0,
                process_mb=1024.0,
                process_percent=6.25,
                warning_level=level,
            )
            assert info.is_critical is False

    def test_is_emergency(self) -> None:
        """Test is_emergency property."""
        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel

        info_emergency = MemoryInfo(
            total_mb=16384.0,
            available_mb=4096.0,
            used_mb=12288.0,
            percent=95.0,
            process_mb=1024.0,
            process_percent=6.25,
            warning_level=MemoryWarningLevel.EMERGENCY,
        )
        assert info_emergency.is_emergency is True

        info_normal = MemoryInfo(
            total_mb=16384.0,
            available_mb=4096.0,
            used_mb=12288.0,
            percent=75.0,
            process_mb=1024.0,
            process_percent=6.25,
            warning_level=MemoryWarningLevel.NORMAL,
        )
        assert info_normal.is_emergency is False


class TestMemoryMonitorConfig:
    """Tests for MemoryMonitorConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        from video2d3d.utils.memory_monitor import MemoryMonitorConfig

        config = MemoryMonitorConfig()

        assert config.warning_threshold == 0.75
        assert config.critical_threshold == 0.85
        assert config.emergency_threshold == 0.95
        assert config.auto_gc_enabled is True
        assert config.monitor_interval == 1.0
        assert config.enable_callbacks is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        from video2d3d.utils.memory_monitor import MemoryMonitorConfig

        config = MemoryMonitorConfig(
            warning_threshold=0.6,
            critical_threshold=0.8,
            emergency_threshold=0.9,
            auto_gc_enabled=False,
            monitor_interval=0.5,
        )

        assert config.warning_threshold == 0.6
        assert config.critical_threshold == 0.8
        assert config.emergency_threshold == 0.9
        assert config.auto_gc_enabled is False
        assert config.monitor_interval == 0.5

    def test_invalid_warning_threshold(self) -> None:
        """Test invalid warning threshold raises error."""
        from video2d3d.utils.memory_monitor import MemoryMonitorConfig

        with pytest.raises(ValueError, match="warning_threshold must be between 0 and 1"):
            MemoryMonitorConfig(warning_threshold=1.5)

        with pytest.raises(ValueError, match="warning_threshold must be between 0 and 1"):
            MemoryMonitorConfig(warning_threshold=0)

    def test_invalid_threshold_order(self) -> None:
        """Test invalid threshold order raises error."""
        from video2d3d.utils.memory_monitor import MemoryMonitorConfig

        with pytest.raises(ValueError, match="Thresholds must be ordered"):
            MemoryMonitorConfig(
                warning_threshold=0.9,
                critical_threshold=0.8,
                emergency_threshold=0.95,
            )

    def test_invalid_monitor_interval(self) -> None:
        """Test invalid monitor interval raises error."""
        from video2d3d.utils.memory_monitor import MemoryMonitorConfig

        with pytest.raises(ValueError, match="monitor_interval must be positive"):
            MemoryMonitorConfig(monitor_interval=0)

        with pytest.raises(ValueError, match="monitor_interval must be positive"):
            MemoryMonitorConfig(monitor_interval=-1)


class TestMemoryMonitor:
    """Tests for MemoryMonitor class."""

    def test_singleton_pattern(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test that MemoryMonitor is a singleton."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor1 = MemoryMonitor()
        monitor2 = MemoryMonitor()

        assert monitor1 is monitor2

    def test_get_memory_info(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test getting memory info."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        info = monitor.get_memory_info()

        assert info.total_mb > 0
        assert info.used_mb > 0
        assert 0 <= info.percent <= 100
        assert info.process_mb > 0

    def test_warning_level_determination(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test warning level is correctly determined."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            MemoryMonitorConfig,
            MemoryWarningLevel,
        )

        # Test normal level (50% used)
        config = MemoryMonitorConfig(
            warning_threshold=0.75,
            critical_threshold=0.85,
            emergency_threshold=0.95,
        )
        monitor = MemoryMonitor(config)

        # Mock 50% memory usage
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3
        mock_mem.available = 8 * 1024**3
        mock_mem.used = 8 * 1024**3
        mock_mem.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_mem

        info = monitor.get_memory_info()
        assert info.warning_level == MemoryWarningLevel.NORMAL

        # Test warning level (80% used)
        mock_mem.available = 3.2 * 1024**3
        mock_mem.used = 12.8 * 1024**3
        mock_mem.percent = 80.0
        mock_psutil.virtual_memory.return_value = mock_mem

        info = monitor.get_memory_info()
        assert info.warning_level == MemoryWarningLevel.WARNING

    def test_add_callback(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test adding callbacks."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        callback = MagicMock()

        monitor.add_callback(callback)

        assert callback in monitor._callbacks

    def test_remove_callback(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test removing callbacks."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        callback = MagicMock()

        monitor.add_callback(callback)
        result = monitor.remove_callback(callback)

        assert result is True
        assert callback not in monitor._callbacks

    def test_remove_nonexistent_callback(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test removing a callback that doesn't exist."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        callback = MagicMock()

        result = monitor.remove_callback(callback)

        assert result is False

    def test_clear_callbacks(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test clearing all callbacks."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        monitor.add_callback(MagicMock())
        monitor.add_callback(MagicMock())

        monitor.clear_callbacks()

        assert len(monitor._callbacks) == 0

    def test_run_garbage_collection(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test running garbage collection."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        monitor._last_gc_time = 0  # Reset cooldown

        with patch("video2d3d.utils.memory_monitor.gc") as mock_gc:
            mock_gc.collect.return_value = 10
            collected = monitor.run_garbage_collection()

            mock_gc.collect.assert_called_once()
            assert collected == 10

    def test_run_garbage_collection_cooldown(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test GC cooldown prevents repeated runs."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        monitor._last_gc_time = time.time()  # Just ran

        with patch("video2d3d.utils.memory_monitor.gc") as mock_gc:
            collected = monitor.run_garbage_collection()

            mock_gc.collect.assert_not_called()
            assert collected == 0

    def test_run_garbage_collection_forced(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test forced GC ignores cooldown."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()
        monitor._last_gc_time = time.time()  # Just ran

        with patch("video2d3d.utils.memory_monitor.gc") as mock_gc:
            mock_gc.collect.return_value = 5
            collected = monitor.run_garbage_collection(force=True)

            mock_gc.collect.assert_called_once()
            assert collected == 5

    def test_start_stop_monitoring(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test starting and stopping monitoring."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            MemoryMonitorConfig,
        )

        config = MemoryMonitorConfig(monitor_interval=0.1)
        monitor = MemoryMonitor(config)

        assert monitor.is_monitoring is False

        monitor.start_monitoring()
        assert monitor.is_monitoring is True

        time.sleep(0.3)  # Let it run a few cycles

        monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    def test_callback_invoked_on_warning(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test callback is invoked when memory warning occurs."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            MemoryMonitorConfig,
        )

        # Set up high memory usage
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3
        mock_mem.available = 2.4 * 1024**3  # 85% used
        mock_mem.used = 13.6 * 1024**3
        mock_mem.percent = 85.0
        mock_psutil.virtual_memory.return_value = mock_mem

        config = MemoryMonitorConfig(
            warning_threshold=0.75,
            monitor_interval=0.1,
        )
        monitor = MemoryMonitor(config)

        callback = MagicMock()
        monitor.add_callback(callback)

        monitor.start_monitoring()
        time.sleep(0.3)
        monitor.stop_monitoring()

        # Callback should have been called
        assert callback.called

    def test_config_setter(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test config can be updated."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            MemoryMonitorConfig,
        )

        monitor = MemoryMonitor()
        new_config = MemoryMonitorConfig(warning_threshold=0.5)
        monitor.config = new_config

        assert monitor.config.warning_threshold == 0.5

    def test_last_info_property(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test last_info property returns last snapshot."""
        from video2d3d.utils.memory_monitor import MemoryMonitor

        monitor = MemoryMonitor()

        info1 = monitor.get_memory_info()
        assert monitor.last_info is info1


class TestContextManager:
    """Tests for memory_monitor_context context manager."""

    def test_context_manager_basic(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test basic context manager usage."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            memory_monitor_context,
        )

        with memory_monitor_context() as monitor:
            assert isinstance(monitor, MemoryMonitor)
            info = monitor.get_memory_info()
            assert info is not None

    def test_context_manager_with_callback(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test context manager with callback."""
        from video2d3d.utils.memory_monitor import memory_monitor_context

        callback = MagicMock()

        # Set up high memory usage
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3
        mock_mem.available = 1.6 * 1024**3  # 90% used
        mock_mem.used = 14.4 * 1024**3
        mock_mem.percent = 90.0
        mock_psutil.virtual_memory.return_value = mock_mem

        with memory_monitor_context(callback=callback) as monitor:
            info = monitor.get_memory_info()
            # Access to trigger warning checks
            _ = info.is_warning


class TestHelperFunctions:
    """Tests for module helper functions."""

    def test_get_memory_monitor(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test get_memory_monitor returns singleton."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            get_memory_monitor,
        )

        monitor1 = get_memory_monitor()
        monitor2 = get_memory_monitor()

        assert monitor1 is monitor2
        assert isinstance(monitor1, MemoryMonitor)

    def test_get_current_memory_info(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test get_current_memory_info returns info."""
        from video2d3d.utils.memory_monitor import (
            MemoryInfo,
            get_current_memory_info,
        )

        info = get_current_memory_info()

        assert isinstance(info, MemoryInfo)
        assert info.total_mb > 0

    def test_format_memory_size_mb(self) -> None:
        """Test formatting memory size in MB."""
        from video2d3d.utils.memory_monitor import format_memory_size

        assert format_memory_size(512) == "512 MB"
        assert format_memory_size(100.5) == "100 MB"

    def test_format_memory_size_gb(self) -> None:
        """Test formatting memory size in GB."""
        from video2d3d.utils.memory_monitor import format_memory_size

        assert format_memory_size(1024) == "1.0 GB"
        assert format_memory_size(2048) == "2.0 GB"
        assert format_memory_size(1536) == "1.5 GB"


class TestConstants:
    """Tests for module constants."""

    def test_constants_defined(self) -> None:
        """Test that module constants are properly defined."""
        from video2d3d.utils import memory_monitor

        assert hasattr(memory_monitor, "BYTES_PER_MB")
        assert memory_monitor.BYTES_PER_MB == 1024 * 1024

        assert hasattr(memory_monitor, "BYTES_PER_GB")
        assert memory_monitor.BYTES_PER_GB == 1024 * 1024 * 1024

        assert hasattr(memory_monitor, "DEFAULT_WARNING_THRESHOLD")
        assert memory_monitor.DEFAULT_WARNING_THRESHOLD == 0.75

        assert hasattr(memory_monitor, "DEFAULT_CRITICAL_THRESHOLD")
        assert memory_monitor.DEFAULT_CRITICAL_THRESHOLD == 0.85

        assert hasattr(memory_monitor, "DEFAULT_EMERGENCY_THRESHOLD")
        assert memory_monitor.DEFAULT_EMERGENCY_THRESHOLD == 0.95


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d.utils import memory_monitor

        expected_exports = [
            "MemoryWarningLevel",
            "MemoryInfo",
            "MemoryMonitorConfig",
            "MemoryMonitor",
            "get_memory_monitor",
            "get_current_memory_info",
            "format_memory_size",
            "memory_monitor_context",
            "MemoryWarningCallback",
        ]

        for export in expected_exports:
            assert export in memory_monitor.__all__, f"Missing export: {export}"


class TestIntegration:
    """Integration tests for memory monitoring."""

    def test_full_monitoring_cycle(self, mock_psutil: MagicMock, mock_logger: MagicMock) -> None:
        """Test complete monitoring cycle with callbacks."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            MemoryMonitorConfig,
            MemoryWarningLevel,
        )

        config = MemoryMonitorConfig(
            warning_threshold=0.7,
            critical_threshold=0.8,
            emergency_threshold=0.9,
            monitor_interval=0.05,
        )

        monitor = MemoryMonitor(config)
        warnings_received: list[MemoryWarningLevel] = []

        def on_warning(info, level):
            warnings_received.append(level)

        monitor.add_callback(on_warning)

        # Simulate memory pressure
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3

        # Start at normal
        mock_mem.available = 8 * 1024**3
        mock_mem.used = 8 * 1024**3
        mock_mem.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_mem

        monitor.start_monitoring()
        time.sleep(0.1)

        # Increase to warning
        mock_mem.available = 3.2 * 1024**3
        mock_mem.used = 12.8 * 1024**3
        mock_mem.percent = 80.0
        mock_psutil.virtual_memory.return_value = mock_mem
        time.sleep(0.15)

        monitor.stop_monitoring()

        # Should have received at least one warning
        assert len(warnings_received) > 0
        assert MemoryWarningLevel.WARNING in warnings_received

    def test_check_and_collect_triggers_gc(
        self, mock_psutil: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Test check_and_collect triggers GC at threshold."""
        from video2d3d.utils.memory_monitor import (
            MemoryMonitor,
            MemoryMonitorConfig,
        )

        config = MemoryMonitorConfig(
            gc_warning_threshold=0.7,
            auto_gc_enabled=True,
        )

        monitor = MemoryMonitor(config)

        # Mock high memory usage
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3
        mock_mem.available = 3.2 * 1024**3  # 80% used
        mock_mem.used = 12.8 * 1024**3
        mock_mem.percent = 80.0
        mock_psutil.virtual_memory.return_value = mock_mem

        with patch.object(monitor, "run_garbage_collection") as mock_gc:
            mock_gc.return_value = 5
            info = monitor.get_memory_info()
            result = monitor.check_and_collect(info)

            assert result is True
            mock_gc.assert_called_once()
