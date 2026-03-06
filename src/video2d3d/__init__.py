"""
2Dto3D Video Converter

A Python application that leverages machine learning models to convert 2D videos
into 3D videos using depth estimation and stereoscopic video generation.

Modules:
    - depth: Depth estimation (MiDaS, DPT, AdaBins)
    - opticalflow: Optical flow calculation (RAFT, PWC-Net)
    - segmentation: Instance segmentation (SAM)
    - stereo: Stereoscopic video generation
"""

from video2d3d._version import __version__, __author__

# Expose submodules for convenience
from video2d3d import depth
from video2d3d import opticalflow

__all__ = ["__version__", "__author__", "depth", "opticalflow"]
