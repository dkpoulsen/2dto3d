"""Optical flow calculation module.

This module provides optical flow estimation using deep learning models
(RAFT, PWC-Net) for accurate motion estimation in video processing pipelines.

Available models:
- RAFT (Recurrent All-Pairs Field Transforms) - High accuracy
- PWC-Net (Pyramid, Warping, and Cost volume) - Fast inference
- Farneback (OpenCV) - CPU fallback

Example usage:
    ```python
    from video2d3d.opticalflow import OpticalFlowEngine, OpticalFlowConfig

    # Basic usage with Farneback (no GPU required)
    config = OpticalFlowConfig(model_type="farneback")
    engine = OpticalFlowEngine(config=config)
    flow = engine.compute_flow(frame1, frame2)

    # With GPU acceleration using RAFT
    config = OpticalFlowConfig(model_type="raft_small", device="cuda")
    engine = OpticalFlowEngine(config=config)
    flow = engine.compute_flow(frame1, frame2)

    # Batch processing
    flows = engine.compute_flow_batch(frames[:-1], frames[1:])

    # Visualize flow
    flow_vis = engine.visualize_flow(flow, frame1)
    ```
"""

from video2d3d.opticalflow.engine import (
    # Classes
    OpticalFlowEngine,
    OpticalFlowConfig,
    OpticalFlowModelType,
    # Exceptions
    OpticalFlowError,
    ModelLoadError,
    InferenceError,
    # Functions
    create_opticalflow_engine,
    compute_optical_flow,
    # Constants
    _DEFAULT_RAFT_RESOLUTION,
    _DEFAULT_PWC_RESOLUTION,
    _DEFAULT_FARNEBACK_PYR_SCALE,
    _DEFAULT_FARNEBACK_LEVELS,
    _DEFAULT_FARNEBACK_WINDOW,
    _DEFAULT_FARNEBACK_ITERATIONS,
)


__all__ = [
    # Classes
    "OpticalFlowEngine",
    "OpticalFlowConfig",
    "OpticalFlowModelType",
    # Exceptions
    "OpticalFlowError",
    "ModelLoadError",
    "InferenceError",
    # Functions
    "create_opticalflow_engine",
    "compute_optical_flow",
    # Constants
    "_DEFAULT_RAFT_RESOLUTION",
    "_DEFAULT_PWC_RESOLUTION",
    "_DEFAULT_FARNEBACK_PYR_SCALE",
    "_DEFAULT_FARNEBACK_LEVELS",
    "_DEFAULT_FARNEBACK_WINDOW",
    "_DEFAULT_FARNEBACK_ITERATIONS",
]
