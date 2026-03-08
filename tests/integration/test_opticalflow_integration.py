"""Integration tests for optical flow engine module.

These tests use real OpenCV operations and require:
- opencv-python-headless or opencv-python installed
- No mocking of cv2 functions

Run with: pytest tests/integration/test_opticalflow_integration.py -v
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    pass

# Check if OpenCV is available
pytest.importorskip("cv2")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a sample RGB frame for testing."""
    np.random.seed(42)
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_pair() -> tuple[np.ndarray, np.ndarray]:
    """Create a pair of frames with known motion for optical flow testing."""
    np.random.seed(42)
    frame1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    # Add horizontal shift to simulate motion
    frame2 = np.roll(frame1, 5, axis=1)
    return frame1, frame2


@pytest.fixture
def frame_sequence() -> list[np.ndarray]:
    """Create a sequence of frames for batch testing."""
    np.random.seed(42)
    base = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    frames = []
    for i in range(5):
        frame = base.copy()
        shift = i * 2
        if shift > 0:
            frame[:, shift:, :] = frame[:, :-shift, :]
        frames.append(frame)
    return frames


@pytest.fixture
def motion_frames() -> tuple[np.ndarray, np.ndarray]:
    """Create frames with simple translational motion for testing flow accuracy."""
    # Create a frame with a distinctive pattern
    frame1 = np.zeros((120, 160, 3), dtype=np.uint8)
    frame1[30:90, 40:120] = 255  # White rectangle
    frame1[50:70, 60:100] = 0  # Black center

    # Create second frame with the rectangle shifted
    frame2 = np.zeros((120, 160, 3), dtype=np.uint8)
    frame2[30:90, 45:125] = 255  # Shifted 5 pixels right
    frame2[50:70, 65:105] = 0

    return frame1, frame2


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestFarnebackOpticalFlowIntegration:
    """Integration tests for Farneback optical flow using real OpenCV."""

    def test_compute_flow_farneback_basic(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test basic Farneback flow computation with real OpenCV."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        # Check output shape and type
        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32

        # Check that flow values are finite
        assert np.all(np.isfinite(flow))

    def test_compute_flow_farneback_identical_frames(self, sample_frame: np.ndarray) -> None:
        """Test that identical frames produce near-zero flow."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        flow = engine.compute_flow(sample_frame, sample_frame)

        # Flow should be near zero for identical frames
        mean_flow = np.mean(np.abs(flow))
        assert mean_flow < 0.5, f"Mean flow magnitude should be < 0.5, got {mean_flow}"

    def test_compute_flow_farneback_motion_frames(
        self, motion_frames: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test Farneback flow detects known translational motion."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = motion_frames
        flow = engine.compute_flow(frame1, frame2)

        # Check output
        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32

        # In the moving region, horizontal flow should be positive (moving right)
        # The white rectangle moved 5 pixels right
        moving_region = frame1[30:90, 40:120]
        flow_in_region = flow[30:90, 40:120, 0]  # Horizontal flow

        # Mean horizontal flow in the moving region should be positive
        mean_horizontal_flow = np.mean(flow_in_region[moving_region[:, :, 0] > 0])
        # Allow some tolerance since Farneback is not exact
        assert (
            mean_horizontal_flow > 0
        ), f"Expected positive horizontal flow, got {mean_horizontal_flow}"

    def test_compute_flow_farneback_custom_params(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test Farneback with custom parameters."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(
            model_type="farneback",
            farneback_levels=5,
            farneback_window=21,
            farneback_iterations=5,
        )
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32

    def test_compute_flow_farneback_different_sizes(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test Farneback with different input sizes."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Test with various sizes
        sizes = [(50, 50), (100, 150), (240, 320), (480, 640)]

        for h, w in sizes:
            np.random.seed(42)
            frame1 = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
            frame2 = np.roll(frame1, 3, axis=1)

            flow = engine.compute_flow(frame1, frame2)

            assert flow.shape == (h, w, 2), f"Failed for size {(h, w)}"
            assert flow.dtype == np.float32


class TestBatchProcessingIntegration:
    """Integration tests for batch processing."""

    def test_batch_processing_farneback(self, frame_sequence: list[np.ndarray]) -> None:
        """Test batch processing with Farneback."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frames1 = frame_sequence[:-1]
        frames2 = frame_sequence[1:]

        flows = engine.compute_flow_batch(frames1, frames2)

        assert len(flows) == len(frames1)
        for i, flow in enumerate(flows):
            assert isinstance(flow, np.ndarray)
            assert flow.shape == (frames1[0].shape[0], frames1[0].shape[1], 2)
            assert flow.dtype == np.float32
            assert np.all(np.isfinite(flow)), f"Flow {i} contains non-finite values"

    def test_batch_processing_consistency(self, frame_sequence: list[np.ndarray]) -> None:
        """Test that batch processing produces same results as individual calls."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frames1 = frame_sequence[:-1]
        frames2 = frame_sequence[1:]

        # Process in batch
        batch_flows = engine.compute_flow_batch(frames1, frames2)

        # Process individually
        individual_flows = []
        for f1, f2 in zip(frames1, frames2):
            flow = engine.compute_flow(f1, f2)
            individual_flows.append(flow)

        # Compare results
        for i, (batch_flow, indiv_flow) in enumerate(zip(batch_flows, individual_flows)):
            np.testing.assert_array_almost_equal(
                batch_flow,
                indiv_flow,
                decimal=5,
                err_msg=f"Flow {i} differs between batch and individual processing",
            )


class TestFlowVisualizationIntegration:
    """Integration tests for flow visualization."""

    def test_visualize_flow_basic(self, sample_frame_pair: tuple[np.ndarray, np.ndarray]) -> None:
        """Test basic flow visualization with real OpenCV."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)
        vis = engine.visualize_flow(flow)

        assert vis.shape == (frame1.shape[0], frame1.shape[1], 3)
        assert vis.dtype == np.uint8

    def test_visualize_flow_with_overlay(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test flow visualization with frame overlay."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)
        vis = engine.visualize_flow(flow, frame1)

        assert vis.shape == (frame1.shape[0], frame1.shape[1], 3)
        assert vis.dtype == np.uint8

    def test_visualize_flow_zero_flow(self, sample_frame: np.ndarray) -> None:
        """Test visualization of zero flow (no motion)."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        flow = engine.compute_flow(sample_frame, sample_frame)
        vis = engine.visualize_flow(flow)

        assert vis.shape == (sample_frame.shape[0], sample_frame.shape[1], 3)
        # With zero flow, the visualization should be mostly uniform
        # (hue would be undefined for zero magnitude)


class TestConvenienceFunctionsIntegration:
    """Integration tests for convenience functions."""

    def test_compute_optical_flow_function(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test the compute_optical_flow convenience function."""
        from video2d3d.opticalflow.engine import compute_optical_flow

        frame1, frame2 = sample_frame_pair
        flow = compute_optical_flow(frame1, frame2, model_type="farneback")

        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32
        assert np.all(np.isfinite(flow))

    def test_create_opticalflow_engine_function(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test the create_opticalflow_engine convenience function."""
        from video2d3d.opticalflow.engine import create_opticalflow_engine

        engine = create_opticalflow_engine(model_type="farneback")

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)


class TestContextManagerIntegration:
    """Integration tests for context manager."""

    def test_context_manager_cleanup(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that context manager properly cleans up resources."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")

        with OpticalFlowEngine(config=config) as engine:
            frame1, frame2 = sample_frame_pair
            flow = engine.compute_flow(frame1, frame2)
            assert flow.shape == (100, 100, 2)

        # After context, resources should be cleaned up
        assert engine._model is None
        assert not engine.is_loaded


class TestCallableInterfaceIntegration:
    """Integration tests for callable interface."""

    def test_callable_interface(self, sample_frame_pair: tuple[np.ndarray, np.ndarray]) -> None:
        """Test that engine can be called as a function."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine(frame1, frame2)

        assert flow.shape == (frame1.shape[0], frame1.shape[1], 2)
        assert flow.dtype == np.float32


class TestInputValidationIntegration:
    """Integration tests for input validation."""

    def test_visualize_flow_validation_invalid_shape(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test visualize_flow raises error for invalid flow shape."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        # Invalid flow shape (3 channels instead of 2)
        invalid_flow = np.zeros((100, 100, 3), dtype=np.float32)

        with pytest.raises(ValueError, match="flow must have shape"):
            engine.visualize_flow(invalid_flow)

    def test_visualize_flow_validation_frame_mismatch(
        self, sample_frame_pair: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test visualize_flow raises error when frame size doesn't match flow."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)

        frame1, frame2 = sample_frame_pair
        flow = engine.compute_flow(frame1, frame2)

        # Wrong size frame
        wrong_frame = np.zeros((50, 50, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="doesn't match flow shape"):
            engine.visualize_flow(flow, wrong_frame)


class TestModuleImportsIntegration:
    """Integration tests for module imports."""

    def test_module_level_imports(self) -> None:
        """Test that all expected exports are available from the module."""
        from video2d3d.opticalflow import (
            InferenceError,
            ModelLoadError,
            OpticalFlowConfig,
            OpticalFlowEngine,
            OpticalFlowError,
            OpticalFlowModelType,
            compute_optical_flow,
            create_opticalflow_engine,
        )

        assert OpticalFlowEngine is not None
        assert OpticalFlowConfig is not None
        assert OpticalFlowModelType is not None
        assert OpticalFlowError is not None
        assert ModelLoadError is not None
        assert InferenceError is not None
        assert create_opticalflow_engine is not None
        assert compute_optical_flow is not None

    def test_engine_module_imports(self) -> None:
        """Test imports from engine submodule."""
        from video2d3d.opticalflow.engine import (
            _DEFAULT_FARNEBACK_PYR_SCALE,
            _DEFAULT_PWC_RESOLUTION,
            _DEFAULT_RAFT_RESOLUTION,
        )

        assert _DEFAULT_RAFT_RESOLUTION == 384
        assert _DEFAULT_PWC_RESOLUTION == 384
        assert _DEFAULT_FARNEBACK_PYR_SCALE == 0.5


class TestReprMethodsIntegration:
    """Integration tests for __repr__ methods."""

    def test_config_repr(self) -> None:
        """Test OpticalFlowConfig __repr__ method."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig

        config = OpticalFlowConfig(model_type="farneback")
        repr_str = repr(config)

        assert "OpticalFlowConfig" in repr_str
        assert "farneback" in repr_str
        assert "device" in repr_str

    def test_engine_repr(self) -> None:
        """Test OpticalFlowEngine __repr__ method."""
        from video2d3d.opticalflow.engine import OpticalFlowConfig, OpticalFlowEngine

        config = OpticalFlowConfig(model_type="farneback")
        engine = OpticalFlowEngine(config=config)
        repr_str = repr(engine)

        assert "OpticalFlowEngine" in repr_str
        assert "farneback" in repr_str
        assert "is_loaded" in repr_str
