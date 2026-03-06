#QZ|"""
#HX|2Dto3D Video Converter
#KM|
#PH|A Python application that leverages machine learning models to convert 2D videos
#SJ|into 3D videos using depth estimation and stereoscopic video generation.
#KM|
#NH|Modules:
#QX|    - depth: Depth estimation (MiDaS, DPT, AdaBins)
#ZS|    - opticalflow: Optical flow calculation (RAFT, PWC-Net)
#QM|    - segmentation: Instance segmentation (SAM)
#MT|    - stereo: Stereoscopic video generation
#XZ|"""
#BY|
#BW|from video2d3d._version import __version__, __author__
#VJ|
#HB|# Expose submodules for convenience
#ZK|from video2d3d import depth
#ZM|from video2d3d import opticalflow
#RW|
__all__ = ["__version__", "__author__", "depth", "opticalflow"]
