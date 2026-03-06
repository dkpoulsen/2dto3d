I'll implement the memory monitoring feature. Let me start by exploring the codebase in parallel to understand the existing structure.

🔧 Tool: glob
Input: {
  "pattern": "**/*.dart"
}

🔧 Tool: glob
Input: {
  "pattern": "**/pubspec.yaml"
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find project structure and tech stack",
  "prompt": "[CONTEXT]: I'm implementing a memory monitoring feature and need to understand the overall project structure and technology stack.\n[GOAL]: Identify the project type (Flutter/Web/Node), main entry points, and where system utilities are typically placed.\n[DOWNSTREAM]: This will determine where to add the memory monitoring module and what APIs to use.\n[REQUEST]: Find: package.json/pubspec.yaml, main entry files (main.dart, index.ts), existing service/utility directories. Return project type, main directories structure, and technology stack."
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find existing monitoring/logging patterns",
  "prompt": "[CONTEXT]: I need to implement memory monitoring that fits existing patterns.\n[GOAL]: Find any existing monitoring, logging, or system utilities to match the coding style.\n[DOWNSTREAM]: Will structure the memory monitor to follow existing patterns.\n[REQUEST]: Search for: logger, monitor, service classes, singleton patterns, stream/broadcast patterns. Return file paths and code patterns found."
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find state management patterns",
  "prompt": "[CONTEXT]: Memory monitoring will need to broadcast warnings and updates.\n[GOAL]: Find how the app handles state updates and notifications.\n[DOWNSTREAM]: Will use the same pattern for memory warning broadcasts.\n[REQUEST]: Find: Provider, Bloc, Riverpod, or other state management patterns. Look for change notifier, stream controllers, or state classes. Return the state management approach used."
}

🔧 Tool: bash
Input: {
  "command": "ls -la",
  "description": "List project root directory"
}

🔧 Tool: bash
Input: {
  "command": "find . -maxdepth 3 -type f \\( -name \"*.ts\" -o -name \"*.tsx\" -o -name \"*.js\" -o -name \"*.jsx\" -o -name \"*.py\" -o -name \"package.json\" -o -name \"*.yaml\" -o -name \"*.yml\" \\) 2>/dev/null | head -50",
  "description": "Find project files"
}
Python project for video 2D to 3D conversion. Let me explore the source structure in parallel:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml"
}

🔧 Tool: bash
Input: {
  "command": "find ./src -type f -name \"*.py\" | head -40",
  "description": "List all Python source files"
}
Let me check the existing utility patterns and collect explore agent results:

🔧 Tool: background_output
Input: {
  "task_id": "bg_e91f3ae8"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_5b37b573"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_90c6e40a"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/logger.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/gpu.py"
}
Now I understand the codebase structure. This is a Python video processing app with:
- **Logging**: Loguru-based with context binding
- **GPU utilities**: Already has memory management with `psutil` and `torch`
- **Patterns**: Dataclasses, Enums, thread-safe operations

Let me create a detailed todo list and implement the memory monitoring feature:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create memory_monitor.py with MemoryMonitor class",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add MemoryInfo dataclass for memory statistics",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add MemoryWarningLevel enum for warning thresholds",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement real-time memory tracking with psutil",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add automatic garbage collection when thresholds exceeded",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add callback system for memory warnings",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add context manager for memory monitoring",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Export memory monitor from utils/__init__.py",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Write unit tests for memory monitor",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Verify with Playwright test",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create memory_monitor.py with MemoryMonitor class",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Add MemoryInfo dataclass for memory statistics",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add MemoryWarningLevel enum for warning thresholds",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Implement real-time memory tracking with psutil",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add automatic garbage collection when thresholds exceeded",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add callback system for memory warnings",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add context manager for memory monitoring",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Export memory monitor from utils/__init__.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Write unit tests for memory monitor",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Verify with Playwright test",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/memory_monitor.py",
  "content": "\"\"\"Real-time memory monitoring with automatic garbage collection and warnings.\n\nThis module provides comprehensive memory monitoring capabilities including:\n- Real-time system memory tracking via psutil\n- Automatic garbage collection when approaching memory limits\n- Configurable warning thresholds with callback support\n- Context manager for scoped memory monitoring\n- Thread-safe singleton pattern for global monitoring\n\"\"\"\n\nfrom __future__ import annotations\n\nimport gc\nimport threading\nimport time\nfrom contextlib import contextmanager\nfrom dataclasses import dataclass, field\nfrom enum import Enum, auto\nfrom typing import TYPE_CHECKING, Any, Callable, Optional\n\nimport psutil\n\nfrom video2d3d.utils.logger import get_logger, log_exception\n\nif TYPE_CHECKING:\n    from loguru import Logger\n    from collections.abc import Generator\n\n# Type alias for memory warning callbacks\nMemoryWarningCallback = Callable[[\"MemoryInfo\", \"MemoryWarningLevel\"], None]\n\n\n# ---------------------------------------------------------------------------\n# Constants\n# ---------------------------------------------------------------------------\n\n# Memory conversion constants\nBYTES_PER_MB: int = 1024 * 1024\nBYTES_PER_GB: int = 1024 * 1024 * 1024\n\n# Default warning thresholds (as fractions of total memory)\nDEFAULT_WARNING_THRESHOLD: float = 0.75  # 75% - Warning\nDEFAULT_CRITICAL_THRESHOLD: float = 0.85  # 85% - Critical\nDEFAULT_EMERGENCY_THRESHOLD: float = 0.95  # 95% - Emergency\n\n# Default monitoring interval in seconds\nDEFAULT_MONITOR_INTERVAL: float = 1.0\n\n# Default GC thresholds (as fractions of total memory)\nDEFAULT_GC_WARNING_THRESHOLD: float = 0.80  # Trigger GC at 80%\nDEFAULT_GC_CRITICAL_THRESHOLD: float = 0.90  # Force GC at 90%\n\n\nclass MemoryWarningLevel(Enum):\n    \"\"\"Memory warning severity levels.\"\"\"\n\n    NORMAL = auto()  # Memory usage is normal\n    WARNING = auto()  # Approaching memory limit\n    CRITICAL = auto()  # Near memory limit - GC recommended\n    EMERGENCY = auto()  # At memory limit - immediate action required\n\n\n@dataclass\nclass MemoryInfo:\n    \"\"\"Current memory statistics.\n\n    Attributes:\n        total_mb: Total system memory in MB.\n        available_mb: Available memory in MB.\n        used_mb: Used memory in MB.\n        percent: Memory usage percentage (0-100).\n        process_mb: Current process memory in MB.\n        process_percent: Process memory as percentage of total.\n        warning_level: Current warning level.\n        timestamp: Unix timestamp of measurement.\n    \"\"\"\n\n    total_mb: float\n    available_mb: float\n    used_mb: float\n    percent: float\n    process_mb: float\n    process_percent: float\n    warning_level: MemoryWarningLevel\n    timestamp: float = field(default_factory=time.time)\n\n    @property\n    def is_warning(self) -> bool:\n        \"\"\"Check if memory usage is at warning level or above.\"\"\"\n        return self.warning_level != MemoryWarningLevel.NORMAL\n\n    @property\n    def is_critical(self) -> bool:\n        \"\"\"Check if memory usage is at critical level or above.\"\"\"\n        return self.warning_level in (\n            MemoryWarningLevel.CRITICAL,\n            MemoryWarningLevel.EMERGENCY,\n        )\n\n    @property\n    def is_emergency(self) -> bool:\n        \"\"\"Check if memory usage is at emergency level.\"\"\"\n        return self.warning_level == MemoryWarningLevel.EMERGENCY\n\n\n@dataclass\nclass MemoryMonitorConfig:\n    \"\"\"Configuration for memory monitoring.\n\n    Attributes:\n        warning_threshold: Fraction of total memory for warning (0.0-1.0).\n        critical_threshold: Fraction of total memory for critical (0.0-1.0).\n        emergency_threshold: Fraction of total memory for emergency (0.0-1.0).\n        gc_warning_threshold: Fraction to trigger GC at warning level.\n        gc_critical_threshold: Fraction to force GC at critical level.\n        auto_gc_enabled: Whether to automatically run GC when thresholds exceeded.\n        monitor_interval: Seconds between memory checks when monitoring.\n        enable_callbacks: Whether to invoke warning callbacks.\n    \"\"\"\n\n    warning_threshold: float = DEFAULT_WARNING_THRESHOLD\n    critical_threshold: float = DEFAULT_CRITICAL_THRESHOLD\n    emergency_threshold: float = DEFAULT_EMERGENCY_THRESHOLD\n    gc_warning_threshold: float = DEFAULT_GC_WARNING_THRESHOLD\n    gc_critical_threshold: float = DEFAULT_GC_CRITICAL_THRESHOLD\n    auto_gc_enabled: bool = True\n    monitor_interval: float = DEFAULT_MONITOR_INTERVAL\n    enable_callbacks: bool = True\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate configuration values.\"\"\"\n        if not 0 < self.warning_threshold <= 1.0:\n            raise ValueError(\n                f\"warning_threshold must be between 0 and 1, got {self.warning_threshold}\"\n            )\n        if not 0 < self.critical_threshold <= 1.0:\n            raise ValueError(\n                f\"critical_threshold must be between 0 and 1, got {self.critical_threshold}\"\n            )\n        if not 0 < self.emergency_threshold <= 1.0:\n            raise ValueError(\n                f\"emergency_threshold must be between 0 and 1, got {self.emergency_threshold}\"\n            )\n        if not self.warning_threshold < self.critical_threshold < self.emergency_threshold:\n            raise ValueError(\n                \"Thresholds must be ordered: warning < critical < emergency\"\n            )\n        if self.monitor_interval <= 0:\n            raise ValueError(\n                f\"monitor_interval must be positive, got {self.monitor_interval}\"\n            )\n\n\nclass MemoryMonitor:\n    \"\"\"Real-time memory monitor with automatic garbage collection and warnings.\n\n    This class provides:\n    - Real-time memory tracking for system and process\n    - Configurable warning thresholds\n    - Automatic garbage collection when approaching limits\n    - Callback system for memory warning notifications\n    - Thread-safe singleton pattern\n\n    Example:\n        # Basic usage\n        monitor = MemoryMonitor()\n        info = monitor.get_memory_info()\n        print(f\"Memory usage: {info.percent:.1f}%\")\n\n        # With callbacks\n        def on_warning(info: MemoryInfo, level: MemoryWarningLevel):\n            print(f\"Memory warning: {level.name} at {info.percent:.1f}%\")\n\n        monitor.add_callback(on_warning)\n        monitor.start_monitoring()\n\n        # Context manager\n        with memory_monitor_context():\n            # Code that uses memory\n            pass\n    \"\"\"\n\n    _instance: Optional[\"MemoryMonitor\"] = None\n    _lock: threading.Lock = threading.Lock()\n\n    def __new__(cls, config: Optional[MemoryMonitorConfig] = None) -> \"MemoryMonitor\":\n        \"\"\"Create or return the singleton instance.\"\"\"\n        with cls._lock:\n            if cls._instance is None:\n                cls._instance = super().__new__(cls)\n                cls._instance._initialized = False\n            return cls._instance\n\n    def __init__(self, config: Optional[MemoryMonitorConfig] = None) -> None:\n        \"\"\"Initialize the memory monitor.\n\n        Args:\n            config: Configuration for monitoring thresholds and behavior.\n        \"\"\"\n        # Skip initialization if already done (singleton pattern)\n        if self._initialized:\n            if config is not None:\n                self._config = config\n            return\n\n        self._config = config or MemoryMonitorConfig()\n        self._callbacks: list[MemoryWarningCallback] = []\n        self._callback_lock = threading.Lock()\n        self._monitoring = False\n        self._monitor_thread: Optional[threading.Thread] = None\n        self._stop_event = threading.Event()\n        self._last_info: Optional[MemoryInfo] = None\n        self._last_gc_time: float = 0.0\n        self._gc_cooldown: float = 5.0  # Minimum seconds between GC runs\n        self._initialized = True\n        self._logger = self._get_memory_logger()\n\n    @staticmethod\n    def _get_memory_logger() -> \"Logger\":\n        \"\"\"Get the memory module logger (lazy initialization).\"\"\"\n        return get_logger(\"memory_monitor\")\n\n    @property\n    def config(self) -> MemoryMonitorConfig:\n        \"\"\"Get the current configuration.\"\"\"\n        return self._config\n\n    @config.setter\n    def config(self, value: MemoryMonitorConfig) -> None:\n        \"\"\"Set the configuration.\"\"\"\n        self._config = value\n\n    @property\n    def is_monitoring(self) -> bool:\n        \"\"\"Check if continuous monitoring is active.\"\"\"\n        return self._monitoring\n\n    @property\n    def last_info(self) -> Optional[MemoryInfo]:\n        \"\"\"Get the last memory info snapshot.\"\"\"\n        return self._last_info\n\n    def get_memory_info(self) -> MemoryInfo:\n        \"\"\"Get current memory statistics.\n\n        Returns:\n            MemoryInfo with current memory statistics.\n        \"\"\"\n        # System memory\n        mem = psutil.virtual_memory()\n        total_mb = mem.total / BYTES_PER_MB\n        available_mb = mem.available / BYTES_PER_MB\n        used_mb = mem.used / BYTES_PER_MB\n        percent = mem.percent\n\n        # Process memory\n        process = psutil.Process()\n        process_info = process.memory_info()\n        process_mb = process_info.rss / BYTES_PER_MB\n        process_percent = (process_mb / total_mb) * 100\n\n        # Determine warning level\n        usage_fraction = used_mb / total_mb\n        warning_level = self._determine_warning_level(usage_fraction)\n\n        info = MemoryInfo(\n            total_mb=total_mb,\n            available_mb=available_mb,\n            used_mb=used_mb,\n            percent=percent,\n            process_mb=process_mb,\n            process_percent=process_percent,\n            warning_level=warning_level,\n        )\n\n        self._last_info = info\n        return info\n\n    def _determine_warning_level(self, usage_fraction: float) -> MemoryWarningLevel:\n        \"\"\"Determine warning level based on memory usage fraction.\n\n        Args:\n            usage_fraction: Memory usage as fraction of total (0.0-1.0).\n\n        Returns:\n            Appropriate MemoryWarningLevel.\n        \"\"\"\n        if usage_fraction >= self._config.emergency_threshold:\n            return MemoryWarningLevel.EMERGENCY\n        if usage_fraction >= self._config.critical_threshold:\n            return MemoryWarningLevel.CRITICAL\n        if usage_fraction >= self._config.warning_threshold:\n            return MemoryWarningLevel.WARNING\n        return MemoryWarningLevel.NORMAL\n\n    def add_callback(self, callback: MemoryWarningCallback) -> None:\n        \"\"\"Add a callback for memory warnings.\n\n        Callbacks are invoked when warning level changes to WARNING or above.\n\n        Args:\n            callback: Function taking MemoryInfo and MemoryWarningLevel.\n        \"\"\"\n        with self._callback_lock:\n            if callback not in self._callbacks:\n                self._callbacks.append(callback)\n\n    def remove_callback(self, callback: MemoryWarningCallback) -> bool:\n        \"\"\"Remove a previously registered callback.\n\n        Args:\n            callback: The callback to remove.\n\n        Returns:\n            True if callback was removed, False if not found.\n        \"\"\"\n        with self._callback_lock:\n            try:\n                self._callbacks.remove(callback)\n                return True\n            except ValueError:\n                return False\n\n    def clear_callbacks(self) -> None:\n        \"\"\"Remove all registered callbacks.\"\"\"\n        with self._callback_lock:\n            self._callbacks.clear()\n\n    def _invoke_callbacks(self, info: MemoryInfo) -> None:\n        \"\"\"Invoke all registered callbacks with current memory info.\n\n        Args:\n            info: Current memory information.\n        \"\"\"\n        if not self._config.enable_callbacks:\n            return\n\n        if not info.is_warning:\n            return\n\n        with self._callback_lock:\n            callbacks = self._callbacks.copy()\n\n        for callback in callbacks:\n            try:\n                callback(info, info.warning_level)\n            except Exception as e:\n                log_exception(\n                    \"Error in memory warning callback\",\n                    exception=e,\n                    callback=callback.__name__,\n                )\n\n    def run_garbage_collection(self, force: bool = False) -> int:\n        \"\"\"Run garbage collection to free memory.\n\n        Args:\n            force: If True, run full collection regardless of cooldown.\n\n        Returns:\n            Number of objects collected.\n        \"\"\"\n        current_time = time.time()\n\n        # Check cooldown unless forced\n        if not force and (current_time - self._last_gc_time) < self._gc_cooldown:\n            self._logger.debug(\"GC skipped due to cooldown\")\n            return 0\n\n        self._logger.info(\"Running garbage collection\")\n\n        # Run garbage collection\n        collected = gc.collect()\n\n        # Also clear GPU memory if available\n        try:\n            from video2d3d.utils.gpu import clear_gpu_memory\n\n            clear_gpu_memory()\n        except ImportError:\n            pass\n\n        self._last_gc_time = current_time\n\n        if collected > 0:\n            self._logger.info(f\"Garbage collection freed {collected} objects\")\n\n        return collected\n\n    def check_and_collect(self, info: Optional[MemoryInfo] = None) -> bool:\n        \"\"\"Check memory and run GC if thresholds exceeded.\n\n        Args:\n            info: Memory info to check. If None, gets current info.\n\n        Returns:\n            True if GC was run, False otherwise.\n        \"\"\"\n        if info is None:\n            info = self.get_memory_info()\n\n        usage_fraction = info.used_mb / info.total_mb\n\n        # Force GC at critical threshold\n        if usage_fraction >= self._config.gc_critical_threshold:\n            self._logger.warning(\n                f\"Memory at critical level ({usage_fraction:.1%}), forcing GC\"\n            )\n            self.run_garbage_collection(force=True)\n            return True\n\n        # Normal GC at warning threshold\n        if (\n            self._config.auto_gc_enabled\n            and usage_fraction >= self._config.gc_warning_threshold\n        ):\n            self._logger.warning(\n                f\"Memory at warning level ({usage_fraction:.1%}), running GC\"\n            )\n            self.run_garbage_collection()\n            return True\n\n        return False\n\n    def _monitoring_loop(self) -> None:\n        \"\"\"Main monitoring loop running in background thread.\"\"\"\n        self._logger.info(\"Memory monitoring started\")\n\n        while not self._stop_event.is_set():\n            try:\n                info = self.get_memory_info()\n\n                # Check for warnings and invoke callbacks\n                if info.is_warning:\n                    self._invoke_callbacks(info)\n                    self.check_and_collect(info)\n\n                # Log periodic status at debug level\n                self._logger.debug(\n                    f\"Memory: {info.percent:.1f}% used \"\n                    f\"({info.used_mb:.0f}MB / {info.total_mb:.0f}MB), \"\n                    f\"process: {info.process_mb:.0f}MB\"\n                )\n\n            except Exception as e:\n                log_exception(\"Error in monitoring loop\", exception=e)\n\n            # Wait for next interval or stop signal\n            self._stop_event.wait(self._config.monitor_interval)\n\n        self._logger.info(\"Memory monitoring stopped\")\n\n    def start_monitoring(self) -> None:\n        \"\"\"Start continuous memory monitoring in a background thread.\"\"\"\n        if self._monitoring:\n            self._logger.warning(\"Monitoring already active\")\n            return\n\n        self._stop_event.clear()\n        self._monitoring = True\n        self._monitor_thread = threading.Thread(\n            target=self._monitoring_loop,\n            name=\"MemoryMonitor\",\n            daemon=True,\n        )\n        self._monitor_thread.start()\n\n    def stop_monitoring(self) -> None:\n        \"\"\"Stop continuous memory monitoring.\"\"\"\n        if not self._monitoring:\n            return\n\n        self._stop_event.set()\n        self._monitoring = False\n\n        if self._monitor_thread is not None:\n            self._monitor_thread.join(timeout=5.0)\n            self._monitor_thread = None\n\n    @classmethod\n    def reset_instance(cls) -> None:\n        \"\"\"Reset the singleton instance (mainly for testing).\"\"\"\n        with cls._lock:\n            if cls._instance is not None:\n                cls._instance.stop_monitoring()\n                cls._instance = None\n\n\n@contextmanager\ndef memory_monitor_context(\n    config: Optional[MemoryMonitorConfig] = None,\n    callback: Optional[MemoryWarningCallback] = None,\n) -> Generator[MemoryMonitor, None, None]:\n    \"\"\"Context manager for scoped memory monitoring.\n\n    Args:\n        config: Optional configuration for the monitor.\n        callback: Optional callback for memory warnings.\n\n    Yields:\n        MemoryMonitor instance.\n\n    Example:\n        with memory_monitor_context() as monitor:\n            # Code that uses memory\n            process_data()\n            # Check memory at any point\n            info = monitor.get_memory_info()\n    \"\"\"\n    monitor = MemoryMonitor(config)\n\n    if callback is not None:\n        monitor.add_callback(callback)\n\n    try:\n        yield monitor\n    finally:\n        # Report final memory status\n        info = monitor.get_memory_info()\n        if info.is_warning:\n            monitor._logger.warning(\n                f\"Context exiting with elevated memory: {info.percent:.1f}%\"\n            )\n\n\ndef get_memory_monitor(config: Optional[MemoryMonitorConfig] = None) -> MemoryMonitor:\n    \"\"\"Get the singleton MemoryMonitor instance.\n\n    Args:\n        config: Optional configuration to apply.\n\n    Returns:\n        MemoryMonitor singleton instance.\n    \"\"\"\n    return MemoryMonitor(config)\n\n\ndef get_current_memory_info() -> MemoryInfo:\n    \"\"\"Get current memory information without continuous monitoring.\n\n    Returns:\n        MemoryInfo snapshot of current memory state.\n    \"\"\"\n    monitor = MemoryMonitor()\n    return monitor.get_memory_info()\n\n\ndef format_memory_size(size_mb: float) -> str:\n    \"\"\"Format memory size in human-readable format.\n\n    Args:\n        size_mb: Size in megabytes.\n\n    Returns:\n        Formatted string (e.g., \"1.5 GB\", \"512 MB\").\n    \"\"\"\n    if size_mb >= 1024:\n        return f\"{size_mb / 1024:.1f} GB\"\n    return f\"{size_mb:.0f} MB\"\n\n\n# Module-level exports\n__all__ = [\n    # Enums\n    \"MemoryWarningLevel\",\n    # Dataclasses\n    \"MemoryInfo\",\n    \"MemoryMonitorConfig\",\n    # Classes\n    \"MemoryMonitor\",\n    # Functions\n    \"get_memory_monitor\",\n    \"get_current_memory_info\",\n    \"format_memory_size\",\n    # Context managers\n    \"memory_monitor_context\",\n    # Type aliases\n    \"MemoryWarningCallback\",\n    # Constants\n    \"BYTES_PER_MB\",\n    \"BYTES_PER_GB\",\n    \"DEFAULT_WARNING_THRESHOLD\",\n    \"DEFAULT_CRITICAL_THRESHOLD\",\n    \"DEFAULT_EMERGENCY_THRESHOLD\",\n    \"DEFAULT_MONITOR_INTERVAL\",\n    \"DEFAULT_GC_WARNING_THRESHOLD\",\n    \"DEFAULT_GC_CRITICAL_THRESHOLD\",\n]\n"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create memory_monitor.py with MemoryMonitor class",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add MemoryInfo dataclass for memory statistics",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add MemoryWarningLevel enum for warning thresholds",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement real-time memory tracking with psutil",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add automatic garbage collection when thresholds exceeded",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add callback system for memory warnings",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add context manager for memory monitoring",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Export memory monitor from utils/__init__.py",
      "priority": "medium",
      "status": "in_progress"
    },
    {
      "content": "Write unit tests for memory monitor",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Verify with Playwright test",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/__init__.py",
  "edits": [
    {
      "op": "append",
      "pos": "85#BQ|",
      "lines": "from video2d3d.utils.memory_monitor import (\n    # Classes and Enums\n    MemoryMonitor,\n    MemoryInfo,\n    MemoryMonitorConfig,\n    MemoryWarningLevel,\n    # Type Aliases\n    MemoryWarningCallback,\n    # Functions\n    get_memory_monitor,\n    get_current_memory_info,\n    format_memory_size,\n    # Context Managers\n    memory_monitor_context,\n    # Constants\n    BYTES_PER_MB,\n    BYTES_PER_GB,\n    DEFAULT_WARNING_THRESHOLD,\n    DEFAULT_CRITICAL_THRESHOLD,\n    DEFAULT_EMERGENCY_THRESHOLD,\n    DEFAULT_MONITOR_INTERVAL,\n    DEFAULT_GC_WARNING_THRESHOLD,\n    DEFAULT_GC_CRITICAL_THRESHOLD,\n)"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/__init__.py"
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "lines": "    # Error Detection Constants\n    \"OOM_ERROR_SUBSTRINGS\",\n    \"CUDA_ERROR_SUBSTRINGS\",\n    \"TIMEOUT_ERROR_SUBSTRINGS\",\n    # Memory Monitor\n    \"MemoryMonitor\",\n    \"MemoryInfo\",\n    \"MemoryMonitorConfig\",\n    \"MemoryWarningLevel\",\n    \"MemoryWarningCallback\",\n    \"get_memory_monitor\",\n    \"get_current_memory_info\",\n    \"format_memory_size\",\n    \"memory_monitor_context\",\n    \"BYTES_PER_MB\",\n    \"BYTES_PER_GB\",\n    \"DEFAULT_WARNING_THRESHOLD\",\n    \"DEFAULT_CRITICAL_THRESHOLD\",\n    \"DEFAULT_EMERGENCY_THRESHOLD\",\n    \"DEFAULT_MONITOR_INTERVAL\",\n    \"DEFAULT_GC_WARNING_THRESHOLD\",\n    \"DEFAULT_GC_CRITICAL_THRESHOLD\",\n]",
      "end": "187#XM|]",
      "op": "replace",
      "pos": "183#PN|"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/__init__.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create memory_monitor.py with MemoryMonitor class",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add MemoryInfo dataclass for memory statistics",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add MemoryWarningLevel enum for warning thresholds",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement real-time memory tracking with psutil",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add automatic garbage collection when thresholds exceeded",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add callback system for memory warnings",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add context manager for memory monitoring",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Export memory monitor from utils/__init__.py",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Write unit tests for memory monitor",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Verify with Playwright test",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_gpu.py"
}
Now I'll create comprehensive unit tests for the memory monitor:

🔧 Tool: write
Input: {
  "content": "\"\"\"Unit tests for memory monitoring utilities.\n\nTests cover:\n- Memory info retrieval\n- Warning level detection\n- Callback system\n- Garbage collection\n- Context manager\n- Singleton pattern\n\"\"\"\n\nfrom __future__ import annotations\n\nimport gc\nimport sys\nimport time\nfrom typing import TYPE_CHECKING\nfrom unittest.mock import MagicMock, patch\n\nimport pytest\n\nif TYPE_CHECKING:\n    from collections.abc import Generator\n\n\n@pytest.fixture(autouse=True)\ndef reset_memory_monitor_singleton() -> Generator[None, None, None]:\n    \"\"\"Reset MemoryMonitor singleton before and after each test.\"\"\"\n    # Reset before test\n    if \"video2d3d.utils.memory_monitor\" in sys.modules:\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        MemoryMonitor.reset_instance()\n        del sys.modules[\"video2d3d.utils.memory_monitor\"]\n\n    yield\n\n    # Reset after test\n    if \"video2d3d.utils.memory_monitor\" in sys.modules:\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        MemoryMonitor.reset_instance()\n        del sys.modules[\"video2d3d.utils.memory_monitor\"]\n\n\n@pytest.fixture\ndef mock_psutil() -> Generator[MagicMock, None, None]:\n    \"\"\"Mock psutil for controlled testing.\"\"\"\n    with patch(\"video2d3d.utils.memory_monitor.psutil\") as mock:\n        # Mock virtual_memory\n        mock_mem = MagicMock()\n        mock_mem.total = 16 * 1024**3  # 16 GB\n        mock_mem.available = 4 * 1024**3  # 4 GB available (75% used)\n        mock_mem.used = 12 * 1024**3  # 12 GB used\n        mock_mem.percent = 75.0\n        mock.virtual_memory.return_value = mock_mem\n\n        # Mock Process\n        mock_process = MagicMock()\n        mock_process_info = MagicMock()\n        mock_process_info.rss = 1 * 1024**3  # 1 GB\n        mock_process.memory_info.return_value = mock_process_info\n        mock.Process.return_value = mock_process\n\n        yield mock\n\n\n@pytest.fixture\ndef mock_logger() -> Generator[MagicMock, None, None]:\n    \"\"\"Mock logger module.\"\"\"\n    with patch(\"video2d3d.utils.memory_monitor.get_logger\") as mock_get_logger:\n        mock_log = MagicMock()\n        mock_get_logger.return_value = mock_log\n        yield mock_log\n\n\nclass TestMemoryWarningLevel:\n    \"\"\"Tests for MemoryWarningLevel enum.\"\"\"\n\n    def test_warning_levels_exist(self) -> None:\n        \"\"\"Test all warning levels are defined.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryWarningLevel\n\n        assert hasattr(MemoryWarningLevel, \"NORMAL\")\n        assert hasattr(MemoryWarningLevel, \"WARNING\")\n        assert hasattr(MemoryWarningLevel, \"CRITICAL\")\n        assert hasattr(MemoryWarningLevel, \"EMERGENCY\")\n\n    def test_warning_levels_unique(self) -> None:\n        \"\"\"Test warning levels have unique values.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryWarningLevel\n\n        levels = [level.value for level in MemoryWarningLevel]\n        assert len(levels) == len(set(levels))\n\n\nclass TestMemoryInfo:\n    \"\"\"Tests for MemoryInfo dataclass.\"\"\"\n\n    def test_memory_info_creation(self) -> None:\n        \"\"\"Test creating MemoryInfo with all fields.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel\n\n        info = MemoryInfo(\n            total_mb=16384.0,\n            available_mb=4096.0,\n            used_mb=12288.0,\n            percent=75.0,\n            process_mb=1024.0,\n            process_percent=6.25,\n            warning_level=MemoryWarningLevel.WARNING,\n        )\n\n        assert info.total_mb == 16384.0\n        assert info.available_mb == 4096.0\n        assert info.used_mb == 12288.0\n        assert info.percent == 75.0\n        assert info.process_mb == 1024.0\n        assert info.process_percent == 6.25\n        assert info.warning_level == MemoryWarningLevel.WARNING\n\n    def test_is_warning_true(self) -> None:\n        \"\"\"Test is_warning property returns True for warning level.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel\n\n        for level in [\n            MemoryWarningLevel.WARNING,\n            MemoryWarningLevel.CRITICAL,\n            MemoryWarningLevel.EMERGENCY,\n        ]:\n            info = MemoryInfo(\n                total_mb=16384.0,\n                available_mb=4096.0,\n                used_mb=12288.0,\n                percent=75.0,\n                process_mb=1024.0,\n                process_percent=6.25,\n                warning_level=level,\n            )\n            assert info.is_warning is True\n\n    def test_is_warning_false(self) -> None:\n        \"\"\"Test is_warning property returns False for normal level.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel\n\n        info = MemoryInfo(\n            total_mb=16384.0,\n            available_mb=4096.0,\n            used_mb=12288.0,\n            percent=75.0,\n            process_mb=1024.0,\n            process_percent=6.25,\n            warning_level=MemoryWarningLevel.NORMAL,\n        )\n        assert info.is_warning is False\n\n    def test_is_critical_true(self) -> None:\n        \"\"\"Test is_critical property returns True for critical and emergency.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel\n\n        for level in [MemoryWarningLevel.CRITICAL, MemoryWarningLevel.EMERGENCY]:\n            info = MemoryInfo(\n                total_mb=16384.0,\n                available_mb=4096.0,\n                used_mb=12288.0,\n                percent=75.0,\n                process_mb=1024.0,\n                process_percent=6.25,\n                warning_level=level,\n            )\n            assert info.is_critical is True\n\n    def test_is_critical_false(self) -> None:\n        \"\"\"Test is_critical property returns False for normal and warning.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel\n\n        for level in [MemoryWarningLevel.NORMAL, MemoryWarningLevel.WARNING]:\n            info = MemoryInfo(\n                total_mb=16384.0,\n                available_mb=4096.0,\n                used_mb=12288.0,\n                percent=75.0,\n                process_mb=1024.0,\n                process_percent=6.25,\n                warning_level=level,\n            )\n            assert info.is_critical is False\n\n    def test_is_emergency(self) -> None:\n        \"\"\"Test is_emergency property.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryInfo, MemoryWarningLevel\n\n        info_emergency = MemoryInfo(\n            total_mb=16384.0,\n            available_mb=4096.0,\n            used_mb=12288.0,\n            percent=95.0,\n            process_mb=1024.0,\n            process_percent=6.25,\n            warning_level=MemoryWarningLevel.EMERGENCY,\n        )\n        assert info_emergency.is_emergency is True\n\n        info_normal = MemoryInfo(\n            total_mb=16384.0,\n            available_mb=4096.0,\n            used_mb=12288.0,\n            percent=75.0,\n            process_mb=1024.0,\n            process_percent=6.25,\n            warning_level=MemoryWarningLevel.NORMAL,\n        )\n        assert info_normal.is_emergency is False\n\n\nclass TestMemoryMonitorConfig:\n    \"\"\"Tests for MemoryMonitorConfig dataclass.\"\"\"\n\n    def test_default_config(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitorConfig\n\n        config = MemoryMonitorConfig()\n\n        assert config.warning_threshold == 0.75\n        assert config.critical_threshold == 0.85\n        assert config.emergency_threshold == 0.95\n        assert config.auto_gc_enabled is True\n        assert config.monitor_interval == 1.0\n        assert config.enable_callbacks is True\n\n    def test_custom_config(self) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitorConfig\n\n        config = MemoryMonitorConfig(\n            warning_threshold=0.6,\n            critical_threshold=0.8,\n            emergency_threshold=0.9,\n            auto_gc_enabled=False,\n            monitor_interval=0.5,\n        )\n\n        assert config.warning_threshold == 0.6\n        assert config.critical_threshold == 0.8\n        assert config.emergency_threshold == 0.9\n        assert config.auto_gc_enabled is False\n        assert config.monitor_interval == 0.5\n\n    def test_invalid_warning_threshold(self) -> None:\n        \"\"\"Test invalid warning threshold raises error.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitorConfig\n\n        with pytest.raises(ValueError, match=\"warning_threshold must be between 0 and 1\"):\n            MemoryMonitorConfig(warning_threshold=1.5)\n\n        with pytest.raises(ValueError, match=\"warning_threshold must be between 0 and 1\"):\n            MemoryMonitorConfig(warning_threshold=0)\n\n    def test_invalid_threshold_order(self) -> None:\n        \"\"\"Test invalid threshold order raises error.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitorConfig\n\n        with pytest.raises(ValueError, match=\"Thresholds must be ordered\"):\n            MemoryMonitorConfig(\n                warning_threshold=0.9,\n                critical_threshold=0.8,\n                emergency_threshold=0.95,\n            )\n\n    def test_invalid_monitor_interval(self) -> None:\n        \"\"\"Test invalid monitor interval raises error.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitorConfig\n\n        with pytest.raises(ValueError, match=\"monitor_interval must be positive\"):\n            MemoryMonitorConfig(monitor_interval=0)\n\n        with pytest.raises(ValueError, match=\"monitor_interval must be positive\"):\n            MemoryMonitorConfig(monitor_interval=-1)\n\n\nclass TestMemoryMonitor:\n    \"\"\"Tests for MemoryMonitor class.\"\"\"\n\n    def test_singleton_pattern(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that MemoryMonitor is a singleton.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor1 = MemoryMonitor()\n        monitor2 = MemoryMonitor()\n\n        assert monitor1 is monitor2\n\n    def test_get_memory_info(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test getting memory info.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        info = monitor.get_memory_info()\n\n        assert info.total_mb > 0\n        assert info.used_mb > 0\n        assert 0 <= info.percent <= 100\n        assert info.process_mb > 0\n\n    def test_warning_level_determination(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test warning level is correctly determined.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            MemoryMonitorConfig,\n            MemoryWarningLevel,\n        )\n\n        # Test normal level (50% used)\n        config = MemoryMonitorConfig(\n            warning_threshold=0.75,\n            critical_threshold=0.85,\n            emergency_threshold=0.95,\n        )\n        monitor = MemoryMonitor(config)\n\n        # Mock 50% memory usage\n        mock_mem = MagicMock()\n        mock_mem.total = 16 * 1024**3\n        mock_mem.available = 8 * 1024**3\n        mock_mem.used = 8 * 1024**3\n        mock_mem.percent = 50.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n\n        info = monitor.get_memory_info()\n        assert info.warning_level == MemoryWarningLevel.NORMAL\n\n        # Test warning level (80% used)\n        mock_mem.available = 3.2 * 1024**3\n        mock_mem.used = 12.8 * 1024**3\n        mock_mem.percent = 80.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n\n        info = monitor.get_memory_info()\n        assert info.warning_level == MemoryWarningLevel.WARNING\n\n    def test_add_callback(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test adding callbacks.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        callback = MagicMock()\n\n        monitor.add_callback(callback)\n\n        assert callback in monitor._callbacks\n\n    def test_remove_callback(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test removing callbacks.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        callback = MagicMock()\n\n        monitor.add_callback(callback)\n        result = monitor.remove_callback(callback)\n\n        assert result is True\n        assert callback not in monitor._callbacks\n\n    def test_remove_nonexistent_callback(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test removing a callback that doesn't exist.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        callback = MagicMock()\n\n        result = monitor.remove_callback(callback)\n\n        assert result is False\n\n    def test_clear_callbacks(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test clearing all callbacks.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        monitor.add_callback(MagicMock())\n        monitor.add_callback(MagicMock())\n\n        monitor.clear_callbacks()\n\n        assert len(monitor._callbacks) == 0\n\n    def test_run_garbage_collection(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test running garbage collection.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        monitor._last_gc_time = 0  # Reset cooldown\n\n        with patch(\"video2d3d.utils.memory_monitor.gc\") as mock_gc:\n            mock_gc.collect.return_value = 10\n            collected = monitor.run_garbage_collection()\n\n            mock_gc.collect.assert_called_once()\n            assert collected == 10\n\n    def test_run_garbage_collection_cooldown(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test GC cooldown prevents repeated runs.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        monitor._last_gc_time = time.time()  # Just ran\n\n        with patch(\"video2d3d.utils.memory_monitor.gc\") as mock_gc:\n            collected = monitor.run_garbage_collection()\n\n            mock_gc.collect.assert_not_called()\n            assert collected == 0\n\n    def test_run_garbage_collection_forced(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test forced GC ignores cooldown.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n        monitor._last_gc_time = time.time()  # Just ran\n\n        with patch(\"video2d3d.utils.memory_monitor.gc\") as mock_gc:\n            mock_gc.collect.return_value = 5\n            collected = monitor.run_garbage_collection(force=True)\n\n            mock_gc.collect.assert_called_once()\n            assert collected == 5\n\n    def test_start_stop_monitoring(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test starting and stopping monitoring.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            MemoryMonitorConfig,\n        )\n\n        config = MemoryMonitorConfig(monitor_interval=0.1)\n        monitor = MemoryMonitor(config)\n\n        assert monitor.is_monitoring is False\n\n        monitor.start_monitoring()\n        assert monitor.is_monitoring is True\n\n        time.sleep(0.3)  # Let it run a few cycles\n\n        monitor.stop_monitoring()\n        assert monitor.is_monitoring is False\n\n    def test_callback_invoked_on_warning(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callback is invoked when memory warning occurs.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            MemoryMonitorConfig,\n        )\n\n        # Set up high memory usage\n        mock_mem = MagicMock()\n        mock_mem.total = 16 * 1024**3\n        mock_mem.available = 2.4 * 1024**3  # 85% used\n        mock_mem.used = 13.6 * 1024**3\n        mock_mem.percent = 85.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n\n        config = MemoryMonitorConfig(\n            warning_threshold=0.75,\n            monitor_interval=0.1,\n        )\n        monitor = MemoryMonitor(config)\n\n        callback = MagicMock()\n        monitor.add_callback(callback)\n\n        monitor.start_monitoring()\n        time.sleep(0.3)\n        monitor.stop_monitoring()\n\n        # Callback should have been called\n        assert callback.called\n\n    def test_config_setter(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test config can be updated.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            MemoryMonitorConfig,\n        )\n\n        monitor = MemoryMonitor()\n        new_config = MemoryMonitorConfig(warning_threshold=0.5)\n        monitor.config = new_config\n\n        assert monitor.config.warning_threshold == 0.5\n\n    def test_last_info_property(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test last_info property returns last snapshot.\"\"\"\n        from video2d3d.utils.memory_monitor import MemoryMonitor\n\n        monitor = MemoryMonitor()\n\n        info1 = monitor.get_memory_info()\n        assert monitor.last_info is info1\n\n\nclass TestContextManager:\n    \"\"\"Tests for memory_monitor_context context manager.\"\"\"\n\n    def test_context_manager_basic(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test basic context manager usage.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            memory_monitor_context,\n        )\n\n        with memory_monitor_context() as monitor:\n            assert isinstance(monitor, MemoryMonitor)\n            info = monitor.get_memory_info()\n            assert info is not None\n\n    def test_context_manager_with_callback(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test context manager with callback.\"\"\"\n        from video2d3d.utils.memory_monitor import memory_monitor_context\n\n        callback = MagicMock()\n\n        # Set up high memory usage\n        mock_mem = MagicMock()\n        mock_mem.total = 16 * 1024**3\n        mock_mem.available = 1.6 * 1024**3  # 90% used\n        mock_mem.used = 14.4 * 1024**3\n        mock_mem.percent = 90.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n\n        with memory_monitor_context(callback=callback) as monitor:\n            info = monitor.get_memory_info()\n            # Access to trigger warning checks\n            _ = info.is_warning\n\n\nclass TestHelperFunctions:\n    \"\"\"Tests for module helper functions.\"\"\"\n\n    def test_get_memory_monitor(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test get_memory_monitor returns singleton.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            get_memory_monitor,\n        )\n\n        monitor1 = get_memory_monitor()\n        monitor2 = get_memory_monitor()\n\n        assert monitor1 is monitor2\n        assert isinstance(monitor1, MemoryMonitor)\n\n    def test_get_current_memory_info(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test get_current_memory_info returns info.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryInfo,\n            get_current_memory_info,\n        )\n\n        info = get_current_memory_info()\n\n        assert isinstance(info, MemoryInfo)\n        assert info.total_mb > 0\n\n    def test_format_memory_size_mb(self) -> None:\n        \"\"\"Test formatting memory size in MB.\"\"\"\n        from video2d3d.utils.memory_monitor import format_memory_size\n\n        assert format_memory_size(512) == \"512 MB\"\n        assert format_memory_size(100.5) == \"100 MB\"\n\n    def test_format_memory_size_gb(self) -> None:\n        \"\"\"Test formatting memory size in GB.\"\"\"\n        from video2d3d.utils.memory_monitor import format_memory_size\n\n        assert format_memory_size(1024) == \"1.0 GB\"\n        assert format_memory_size(2048) == \"2.0 GB\"\n        assert format_memory_size(1536) == \"1.5 GB\"\n\n\nclass TestConstants:\n    \"\"\"Tests for module constants.\"\"\"\n\n    def test_constants_defined(self) -> None:\n        \"\"\"Test that module constants are properly defined.\"\"\"\n        from video2d3d.utils import memory_monitor\n\n        assert hasattr(memory_monitor, \"BYTES_PER_MB\")\n        assert memory_monitor.BYTES_PER_MB == 1024 * 1024\n\n        assert hasattr(memory_monitor, \"BYTES_PER_GB\")\n        assert memory_monitor.BYTES_PER_GB == 1024 * 1024 * 1024\n\n        assert hasattr(memory_monitor, \"DEFAULT_WARNING_THRESHOLD\")\n        assert memory_monitor.DEFAULT_WARNING_THRESHOLD == 0.75\n\n        assert hasattr(memory_monitor, \"DEFAULT_CRITICAL_THRESHOLD\")\n        assert memory_monitor.DEFAULT_CRITICAL_THRESHOLD == 0.85\n\n        assert hasattr(memory_monitor, \"DEFAULT_EMERGENCY_THRESHOLD\")\n        assert memory_monitor.DEFAULT_EMERGENCY_THRESHOLD == 0.95\n\n\nclass TestModuleExports:\n    \"\"\"Tests for module exports.\"\"\"\n\n    def test_all_exports_defined(self) -> None:\n        \"\"\"Test __all__ contains expected exports.\"\"\"\n        from video2d3d.utils import memory_monitor\n\n        expected_exports = [\n            \"MemoryWarningLevel\",\n            \"MemoryInfo\",\n            \"MemoryMonitorConfig\",\n            \"MemoryMonitor\",\n            \"get_memory_monitor\",\n            \"get_current_memory_info\",\n            \"format_memory_size\",\n            \"memory_monitor_context\",\n            \"MemoryWarningCallback\",\n        ]\n\n        for export in expected_exports:\n            assert export in memory_monitor.__all__, f\"Missing export: {export}\"\n\n\nclass TestIntegration:\n    \"\"\"Integration tests for memory monitoring.\"\"\"\n\n    def test_full_monitoring_cycle(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test complete monitoring cycle with callbacks.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            MemoryMonitorConfig,\n            MemoryWarningLevel,\n        )\n\n        config = MemoryMonitorConfig(\n            warning_threshold=0.7,\n            critical_threshold=0.8,\n            emergency_threshold=0.9,\n            monitor_interval=0.05,\n        )\n\n        monitor = MemoryMonitor(config)\n        warnings_received: list[MemoryWarningLevel] = []\n\n        def on_warning(info, level):\n            warnings_received.append(level)\n\n        monitor.add_callback(on_warning)\n\n        # Simulate memory pressure\n        mock_mem = MagicMock()\n        mock_mem.total = 16 * 1024**3\n\n        # Start at normal\n        mock_mem.available = 8 * 1024**3\n        mock_mem.used = 8 * 1024**3\n        mock_mem.percent = 50.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n\n        monitor.start_monitoring()\n        time.sleep(0.1)\n\n        # Increase to warning\n        mock_mem.available = 3.2 * 1024**3\n        mock_mem.used = 12.8 * 1024**3\n        mock_mem.percent = 80.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n        time.sleep(0.15)\n\n        monitor.stop_monitoring()\n\n        # Should have received at least one warning\n        assert len(warnings_received) > 0\n        assert MemoryWarningLevel.WARNING in warnings_received\n\n    def test_check_and_collect_triggers_gc(\n        self, mock_psutil: MagicMock, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test check_and_collect triggers GC at threshold.\"\"\"\n        from video2d3d.utils.memory_monitor import (\n            MemoryMonitor,\n            MemoryMonitorConfig,\n        )\n\n        config = MemoryMonitorConfig(\n            gc_warning_threshold=0.7,\n            auto_gc_enabled=True,\n        )\n\n        monitor = MemoryMonitor(config)\n\n        # Mock high memory usage\n        mock_mem = MagicMock()\n        mock_mem.total = 16 * 1024**3\n        mock_mem.available = 3.2 * 1024**3  # 80% used\n        mock_mem.used = 12.8 * 1024**3\n        mock_mem.percent = 80.0\n        mock_psutil.virtual_memory.return_value = mock_mem\n\n        with patch.object(monitor, \"run_garbage_collection\") as mock_gc:\n            mock_gc.return_value = 5\n            info = monitor.get_memory_info()\n            result = monitor.check_and_collect(info)\n\n            assert result is True\n            mock_gc.assert_called_once()\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_memory_monitor.py"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_memory_monitor.py -v --tb=short 2>&1 | head -100",
  "description": "Run memory monitor unit tests"
}


---

## Follow-up Session

I'll review the memory monitoring code I created and make improvements. Let me first check the test results and then perform a thorough code review.

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/memory_monitor.py"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_memory_monitor.py -v --tb=short 2>&1 | tail -80",
  "description": "Run memory monitor tests to see results"
}


---

## Follow-up Session

I'll complete the commit phase for the memory monitoring feature. Let me first review all changes and then commit them.

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff --stat",
  "description": "Show diff statistics"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log --oneline -5",
  "description": "Check recent commit messages"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status",
  "description": "Check git status for changes"
}
I see there are many changes from different features. Let me focus on staging only the memory monitoring related files:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff --cached --stat",
  "description": "Show staged changes statistics"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git add src/video2d3d/utils/memory_monitor.py src/video2d3d/utils/__init__.py tests/unit/test_memory_monitor.py",
  "description": "Stage memory monitoring files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status",
  "description": "Check staging status"
}
Files are staged. Now I'll execute the git commit with conventional commit format:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git commit -m \"$(cat <<'EOF'\nfeat(utils): add real-time memory monitoring with auto GC\n\nAdd comprehensive memory monitoring capabilities:\n- MemoryMonitor singleton with thread-safe operations\n- Real-time tracking via psutil for system/process memory\n- Configurable warning thresholds (warning/critical/emergency)\n- Automatic garbage collection when approaching limits\n- Callback system for memory warning notifications\n- Context manager for scoped memory monitoring\n- MemoryInfo dataclass with usage statistics\n- MemoryWarningLevel enum for severity classification\n- Unit tests with mocked psutil for deterministic testing\nEOF\n)\"",
  "description": "Commit memory monitoring feature"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create memory_monitor.py with MemoryMonitor class",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add MemoryInfo dataclass for memory statistics",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add MemoryWarningLevel enum for warning thresholds",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement real-time memory tracking with psutil",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add automatic garbage collection when thresholds exceeded",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add callback system for memory warnings",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add context manager for memory monitoring",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Export memory monitor from utils/__init__.py",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Write unit tests for memory monitor",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Verify with Playwright test",
      "priority": "high",
      "status": "completed"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log -1 --stat",
  "description": "Verify commit details"
}
<summary>
## Summary: Memory Usage Monitor

### Changes Implemented
- Created `MemoryMonitor` singleton class with thread-safe operations
- Added `MemoryInfo` dataclass for memory statistics (total, used, available, process memory, warning level)
- Added `MemoryWarningLevel` enum (NORMAL, WARNING, CRITICAL, EMERGENCY)
- Implemented real-time memory tracking via psutil
- Added automatic garbage collection when approaching memory limits
- Added configurable warning thresholds (default: 75%/85%/95%)
- Added callback system for memory warning notifications
- Added context manager `memory_monitor_context()` for scoped monitoring
- Integrated with existing GPU memory clearing utility
- Exported all components from `utils/__init__.py`
- Comprehensive unit tests with mocked psutil

### Files Modified
- `src/video2d3d/utils/memory_monitor.py` (new - 575 lines)
- `src/video2d3d/utils/__init__.py` (modified - added exports)
- `tests/unit/test_memory_monitor.py` (new - 723 lines)

### Verification Status
- Unit tests created with comprehensive coverage (mocked psutil for deterministic testing)
- Tests cover: MemoryInfo, MemoryWarningLevel, MemoryMonitorConfig, MemoryMonitor singleton, callbacks, GC, context manager
- Playwright verification not applicable - this is a Python backend module, not a web UI

### Commit Details
- **Commit Hash**: `18ccbc7cdb46f5c8918497d18859aca4e28fc39d`
- **Commit Message**:
  ```
  feat(utils): add real-time memory monitoring with auto GC
  
  Add comprehensive memory monitoring capabilities:
  - MemoryMonitor singleton with thread-safe operations
  - Real-time tracking via psutil for system/process memory
  - Configurable warning thresholds (warning/critical/emergency)
  - Automatic garbage collection when approaching limits
  - Callback system for memory warning notifications
  - Context manager for scoped memory monitoring
  - MemoryInfo dataclass with usage statistics
  - MemoryWarningLevel enum for severity classification
  - Unit tests with mocked psutil for deterministic testing
  ```
- **Files Changed**: 3 files, 1340 insertions(+)

### Notes for Developer
- Memory monitor uses singleton pattern - access via `get_memory_monitor()` or `MemoryMonitor()`
- Default thresholds: Warning (75%), Critical (85%), Emergency (95%)
- GC triggers at 80% (warning) and 90% (critical) by default
- All thresholds are configurable via `MemoryMonitorConfig`
- Callbacks receive `(MemoryInfo, MemoryWarningLevel)` when warnings occur
</summary>

---

## Follow-up Session

I'll review the existing test coverage for the memory monitoring feature and ensure comprehensive testing.

## Phase 1: Review Phase

Let me first examine what was implemented and what needs testing:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/memory_monitor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_memory_monitor.py"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_memory_monitor.py -v --tb=short 2>&1",
  "description": "Run memory monitor tests to check status"
}
