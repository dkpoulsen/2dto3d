"""Unit tests for GPU acceleration utilities.

Tests cover:
- Device detection and selection
- GPU info retrieval
- Memory management
- Batch size computation
- Transfer utilities
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def mock_torch_modules() -> Generator[None, None, None]:
    """Mock torch modules before any imports (autouse fixture)."""
    # Store original modules
    original_modules = {}
    modules_to_mock = [
        "torch",
        "torch.nn",
        "torch.nn.functional",
        "torchvision",
        "torchvision.transforms",
    ]

    for mod in modules_to_mock:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]

    # Create mock modules
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.cuda.device_count.return_value = 0
    mock_torch.cuda.get_device_properties = MagicMock()
    mock_torch.cuda.mem_get_info = MagicMock(return_value=(4 * 1024**3, 8 * 1024**3))
    mock_torch.cuda.set_device = MagicMock()
    mock_torch.cuda.empty_cache = MagicMock()
    mock_torch.cuda.synchronize = MagicMock()
    mock_torch.cuda.set_per_process_memory_fraction = MagicMock()
    mock_torch.backends.cudnn.benchmark = False
    mock_torch.backends.cudnn.deterministic = False
    mock_torch.Tensor = MagicMock
    mock_torch.float32 = "float32"
    mock_torch.float16 = "float16"

    # Mock tensor operations
    mock_tensor = MagicMock()
    mock_tensor.dim.return_value = 3
    mock_tensor.unsqueeze.return_value = mock_tensor
    mock_tensor.to.return_value = mock_tensor
    mock_tensor.squeeze.return_value = mock_tensor
    mock_tensor.cpu.return_value = mock_tensor
    mock_tensor.half.return_value = mock_tensor
    mock_tensor.is_pinned.return_value = False
    mock_tensor.pin_memory.return_value = mock_tensor
    mock_tensor.device = MagicMock(type="cpu")
    mock_tensor.detach.return_value = mock_tensor
    mock_tensor.numpy.return_value = np.zeros((100, 100), dtype=np.float32)
    mock_torch.from_numpy = MagicMock(return_value=mock_tensor)
    mock_torch.empty = MagicMock(return_value=mock_tensor)

    # Mock cat for batch operations
    mock_torch.cat = MagicMock(return_value=mock_tensor)

    # Mock MPS backend
    mock_mps = MagicMock()
    mock_mps.is_available.return_value = False
    mock_mps.is_built.return_value = False
    mock_torch.backends.mps = mock_mps

    # Set mock modules
    sys.modules["torch"] = mock_torch
    sys.modules["torch.nn"] = MagicMock()
    sys.modules["torch.nn.functional"] = MagicMock()
    sys.modules["torchvision"] = MagicMock()
    sys.modules["torchvision.transforms"] = MagicMock()

    # Mock loguru
    sys.modules["loguru"] = MagicMock()

    # Mock video2d3d.utils.logger only (don't mock the whole utils package)
    mock_logger_module = MagicMock()
    mock_logger_module.get_logger = MagicMock(return_value=MagicMock())
    mock_logger_module.log_exception = MagicMock()
    
    # Store original modules
    if "video2d3d.utils.logger" in sys.modules:
        original_modules["video2d3d.utils.logger"] = sys.modules["video2d3d.utils.logger"]
    sys.modules["video2d3d.utils.logger"] = mock_logger_module

    # Clear any cached imports of the gpu module
    if "video2d3d.utils.gpu" in sys.modules:
        del sys.modules["video2d3d.utils.gpu"]

    yield

    # Restore original modules
    for mod in modules_to_mock:
        if mod in original_modules:
            sys.modules[mod] = original_modules[mod]
        elif mod in sys.modules:
            del sys.modules[mod]

    # Clear gpu module cache
    if "video2d3d.utils.gpu" in sys.modules:
        del sys.modules["video2d3d.utils.gpu"]


@pytest.fixture
def mock_torch() -> MagicMock:
    """Get the mocked torch module."""
    return sys.modules["torch"]


class TestDeviceDetection:
    """Tests for device detection functions."""

    def test_is_cuda_available_no_cuda(self, mock_torch: MagicMock) -> None:
        """Test CUDA availability check when CUDA is not available."""
        from video2d3d.utils.gpu import is_cuda_available

        mock_torch.cuda.is_available.return_value = False
        assert is_cuda_available() is False

    def test_is_cuda_available_with_cuda(self, mock_torch: MagicMock) -> None:
        """Test CUDA availability check when CUDA is available."""
        from video2d3d.utils.gpu import is_cuda_available

        mock_torch.cuda.is_available.return_value = True
        assert is_cuda_available() is True

    def test_is_mps_available_no_mps(self, mock_torch: MagicMock) -> None:
        """Test MPS availability check when MPS is not available."""
        from video2d3d.utils.gpu import is_mps_available

        mock_torch.backends.mps.is_available.return_value = False
        assert is_mps_available() is False

    def test_get_device_count_no_cuda(self, mock_torch: MagicMock) -> None:
        """Test device count when CUDA is not available."""
        from video2d3d.utils.gpu import get_device_count

        mock_torch.cuda.is_available.return_value = False
        assert get_device_count() == 0

    def test_get_device_count_with_cuda(self, mock_torch: MagicMock) -> None:
        """Test device count when CUDA is available."""
        from video2d3d.utils.gpu import get_device_count

        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2
        assert get_device_count() == 2


class TestDeviceSelection:
    """Tests for device selection functions."""

    def test_select_device_cpu_explicit(self, mock_torch: MagicMock) -> None:
        """Test selecting CPU explicitly."""
        from video2d3d.utils.gpu import GPUConfig, select_device

        config = GPUConfig(device="cpu")
        selection = select_device(config)

        assert selection.device == "cpu"
        assert selection.device_type.value == "cpu"
        assert "CPU explicitly requested" in selection.reason

    def test_select_device_auto_fallback_to_cpu(self, mock_torch: MagicMock) -> None:
        """Test auto selection falls back to CPU when no GPU available."""
        from video2d3d.utils.gpu import GPUConfig, select_device

        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.device_count.return_value = 0
        mock_torch.backends.mps.is_available.return_value = False

        config = GPUConfig(device="auto")
        selection = select_device(config)

        assert selection.device == "cpu"
        assert selection.fallback_used is True

    def test_select_device_disabled(self, mock_torch: MagicMock) -> None:
        """Test device selection when GPU is disabled."""
        from video2d3d.utils.gpu import GPUConfig, select_device

        config = GPUConfig(enabled=False)
        selection = select_device(config)

        assert selection.device == "cpu"
        assert "GPU disabled in configuration" in selection.reason


class TestGPUConfig:
    """Tests for GPUConfig dataclass."""

    def test_default_config(self, mock_torch: MagicMock) -> None:
        """Test default GPU configuration values."""
        from video2d3d.utils.gpu import GPUConfig

        config = GPUConfig()

        assert config.enabled is True
        assert config.device == "auto"
        assert config.device_id == -1
        assert config.memory_fraction == 0.8
        assert config.fallback_to_cpu is True
        assert config.batch_size_auto is True
        assert config.min_batch_size == 1
        assert config.max_batch_size == 32

    def test_custom_config(self, mock_torch: MagicMock) -> None:
        """Test custom GPU configuration values."""
        from video2d3d.utils.gpu import GPUConfig

        config = GPUConfig(
            enabled=True,
            device="cuda",
            device_id=0,
            memory_fraction=0.5,
            fallback_to_cpu=False,
        )

        assert config.device == "cuda"
        assert config.device_id == 0
        assert config.memory_fraction == 0.5
        assert config.fallback_to_cpu is False


class TestMemoryFunctions:
    """Tests for memory-related functions."""

    def test_estimate_memory_requirement(self, mock_torch: MagicMock) -> None:
        """Test memory estimation for batches."""
        from video2d3d.utils.gpu import estimate_memory_requirement

        # Test with typical values
        mem_mb = estimate_memory_requirement(
            batch_size=4,
            image_height=384,
            image_width=384,
            channels=3,
            dtype_bytes=4,
        )

        # Should be positive and reasonable
        assert mem_mb > 0
        # Rough check: 4 * 3 * 384 * 384 * 4 bytes * 2.5 overhead ≈ 17.6 MB
        assert 10 < mem_mb < 50

    def test_estimate_memory_requirement_fp16(self, mock_torch: MagicMock) -> None:
        """Test memory estimation with FP16 uses less memory."""
        from video2d3d.utils.gpu import estimate_memory_requirement

        mem_fp32 = estimate_memory_requirement(
            batch_size=4, image_height=384, image_width=384, dtype_bytes=4
        )
        mem_fp16 = estimate_memory_requirement(
            batch_size=4, image_height=384, image_width=384, dtype_bytes=2
        )

        assert mem_fp16 < mem_fp32

    def test_get_memory_usage_no_cuda(self, mock_torch: MagicMock) -> None:
        """Test memory usage when CUDA is not available."""
        from video2d3d.utils.gpu import get_memory_usage

        mock_torch.cuda.is_available.return_value = False
        used, free, total = get_memory_usage("cuda:0")

        assert used == 0.0
        assert free == 0.0
        assert total == 0.0


class TestBatchSizeComputation:
    """Tests for optimal batch size computation."""

    def test_compute_optimal_batch_size_no_cuda(self, mock_torch: MagicMock) -> None:
        """Test batch size computation when CUDA is not available."""
        from video2d3d.utils.gpu import GPUConfig, compute_optimal_batch_size

        mock_torch.cuda.is_available.return_value = False

        config = GPUConfig(batch_size_auto=True)
        batch_size = compute_optimal_batch_size(config, 384, 384)

        assert batch_size == config.min_batch_size

    def test_compute_optimal_batch_size_disabled(self, mock_torch: MagicMock) -> None:
        """Test batch size computation when auto-adjust is disabled."""
        from video2d3d.utils.gpu import GPUConfig, compute_optimal_batch_size

        config = GPUConfig(batch_size_auto=False)
        batch_size = compute_optimal_batch_size(config, 384, 384)

        # Should return default of 4 when auto is disabled
        assert batch_size == 4


class TestExceptions:
    """Tests for custom exceptions."""

    def test_gpu_error_basic(self, mock_torch: MagicMock) -> None:
        """Test basic GPUError."""
        from video2d3d.utils.gpu import GPUError

        error = GPUError("Test error")
        assert str(error) == "Test error"
        assert error.device is None
        assert error.original_exception is None

    def test_gpu_error_with_params(self, mock_torch: MagicMock) -> None:
        """Test GPUError with all parameters."""
        from video2d3d.utils.gpu import GPUError

        original = ValueError("Original error")
        error = GPUError(
            "Test error",
            device="cuda:0",
            original_exception=original,
        )

        assert error.device == "cuda:0"
        assert error.original_exception is original

    def test_out_of_memory_error_inherits(self, mock_torch: MagicMock) -> None:
        """Test OutOfMemoryError inherits from GPUError."""
        from video2d3d.utils.gpu import GPUError, OutOfMemoryError

        error = OutOfMemoryError("OOM error")
        assert isinstance(error, GPUError)


class TestTransferFunctions:
    """Tests for tensor transfer functions."""

    def test_transfer_to_cpu(self, mock_torch: MagicMock) -> None:
        """Test transferring tensor to CPU."""
        from video2d3d.utils.gpu import transfer_to_cpu

        mock_tensor = MagicMock()
        mock_tensor.device.type = "cuda"
        mock_tensor.detach.return_value.cpu.return_value.numpy.return_value = np.zeros((10, 10))

        result = transfer_to_cpu(mock_tensor, async_transfer=True)

        assert isinstance(result, np.ndarray)


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self, mock_torch: MagicMock) -> None:
        """Test __all__ contains expected exports."""
        from video2d3d.utils import gpu

        expected_exports = [
            "GPUConfig",
            "GPUInfo",
            "DeviceSelection",
            "DeviceType",
            "GPUError",
            "OutOfMemoryError",
            "is_cuda_available",
            "is_mps_available",
            "get_device_count",
            "select_device",
            "clear_gpu_memory",
            "compute_optimal_batch_size",
            "setup_device",
        ]

        for export in expected_exports:
            assert export in gpu.__all__, f"Missing export: {export}"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_parse_device_id_with_colon(self, mock_torch: MagicMock) -> None:
        """Test parsing device ID from device string with colon."""
        from video2d3d.utils.gpu import _parse_device_id

        assert _parse_device_id("cuda:0") == 0
        assert _parse_device_id("cuda:1") == 1
        assert _parse_device_id("cuda:5") == 5

    def test_parse_device_id_without_colon(self, mock_torch: MagicMock) -> None:
        """Test parsing device ID from device string without colon."""
        from video2d3d.utils.gpu import _parse_device_id

        assert _parse_device_id("cuda") == 0
        assert _parse_device_id("cpu") == 0
        assert _parse_device_id("mps") == 0

    def test_parse_device_id_invalid(self, mock_torch: MagicMock) -> None:
        """Test parsing device ID from invalid device string."""
        from video2d3d.utils.gpu import _parse_device_id

        assert _parse_device_id("cuda:invalid") == 0
        assert _parse_device_id("cuda:") == 0

    def test_create_cpu_selection(self, mock_torch: MagicMock) -> None:
        """Test creating CPU device selection."""
        from video2d3d.utils.gpu import _create_cpu_selection, DeviceType

        selection = _create_cpu_selection("Test reason")

        assert selection.device == "cpu"
        assert selection.device_type == DeviceType.CPU
        assert selection.device_name == "CPU"
        assert selection.fallback_used is False
        assert "Test reason" in selection.reason

    def test_create_cpu_selection_with_fallback(self, mock_torch: MagicMock) -> None:
        """Test creating CPU device selection with fallback flag."""
        from video2d3d.utils.gpu import _create_cpu_selection, DeviceType

        selection = _create_cpu_selection("Test reason", fallback_used=True)

        assert selection.fallback_used is True


class TestSetupDevice:
    """Tests for setup_device function."""

    def test_setup_device_default(self, mock_torch: MagicMock) -> None:
        """Test device setup with default config."""
        from video2d3d.utils.gpu import setup_device, DeviceType

        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False

        selection = setup_device()

        assert selection.device == "cpu"
        assert selection.fallback_used is True

    def test_setup_device_with_override(self, mock_torch: MagicMock) -> None:
        """Test device setup with device override."""
        from video2d3d.utils.gpu import setup_device

        selection = setup_device(device_override="cpu")

        assert selection.device == "cpu"
        assert "CPU explicitly requested" in selection.reason


class TestConstants:
    """Tests for module constants."""

    def test_constants_defined(self, mock_torch: MagicMock) -> None:
        """Test that module constants are properly defined."""
        from video2d3d.utils import gpu

        assert hasattr(gpu, "BYTES_PER_MB")
        assert gpu.BYTES_PER_MB == 1024 * 1024

        assert hasattr(gpu, "DEFAULT_MEMORY_FRACTION")
        assert gpu.DEFAULT_MEMORY_FRACTION == 0.8

        assert hasattr(gpu, "MEMORY_SAFETY_MARGIN")
        assert gpu.MEMORY_SAFETY_MARGIN == 0.9

        assert hasattr(gpu, "DEFAULT_MIN_BATCH_SIZE")
        assert gpu.DEFAULT_MIN_BATCH_SIZE == 1

        assert hasattr(gpu, "DEFAULT_MAX_BATCH_SIZE")
        assert gpu.DEFAULT_MAX_BATCH_SIZE == 32
