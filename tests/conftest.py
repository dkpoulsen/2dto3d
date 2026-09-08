"""Conftest for pytest fixtures.

This module sets up mocks for external dependencies before tests are collected.
"""

import sys
from unittest.mock import MagicMock

import numpy as np


def _create_mock_torch() -> MagicMock:
    """Create a mock torch module."""
    mock = MagicMock()
    mock.cuda.is_available.return_value = False
    mock.hub.get_dir.return_value = "/tmp/torch_hub"
    mock.hub.set_dir = MagicMock()
    return mock


def _create_mock_cv2() -> MagicMock:
    """Create a mock cv2 module."""
    mock = MagicMock()
    mock.COLORMAP_TURBO = 1
    mock.COLORMAP_PLASMA = 2
    mock.COLORMAP_VIRIDIS = 3
    mock.COLORMAP_MAGMA = 4
    mock.COLORMAP_JET = 5
    mock.COLORMAP_INFERNO = 6
    mock.INPAINT_NS = 1
    mock.INPAINT_TELEA = 2
    mock.DIST_L2 = 2
    mock.DIST_MASK_PRECISE = 0
    mock.MORPH_CLOSE = 3
    mock.COLOR_GRAY2RGB = 8
    mock.COLOR_BGR2RGB = 4

    # Mock bilateralFilter to return input
    def mock_bilateral_filter(img, d, sigmaColor, sigmaSpace):
        return img

    mock.bilateralFilter = mock_bilateral_filter

    # Mock equalizeHist to return input converted
    def mock_equalize_hist(img):
        return img

    mock.equalizeHist = mock_equalize_hist

    # Mock inpaint to return input
    def mock_inpaint(img, mask, inpaintRadius, flags):
        return img

    mock.inpaint = mock_inpaint

    # Mock distanceTransformWithLabels
    def mock_distance_transform_with_labels(mask, distType, maskSize):
        dist = np.zeros_like(mask, dtype=np.float32)
        labels = np.zeros_like(mask, dtype=np.int32)
        return dist, labels

    mock.distanceTransformWithLabels = mock_distance_transform_with_labels

    # Mock dilate
    def mock_dilate(img, kernel, iterations=1):
        return img

    mock.dilate = mock_dilate

    # Mock morphologyEx
    def mock_morphology_ex(img, op, kernel):
        return img

    mock.morphologyEx = mock_morphology_ex

    # Mock GaussianBlur
    def mock_gaussian_blur(img, ksize, sigmaX):
        return img

    mock.GaussianBlur = mock_gaussian_blur

    # Mock addWeighted
    def mock_add_weighted(img1, alpha, img2, beta, gamma):
        return img1

    mock.addWeighted = mock_add_weighted

    # Mock applyColorMap
    def mock_apply_colormap(img, colormap):
        h, w = img.shape[:2]
        return np.zeros((h, w, 3), dtype=np.uint8)

    mock.applyColorMap = mock_apply_colormap

    # Mock cvtColor
    def mock_cvt_color(img, code):
        if len(img.shape) == 2:
            h, w = img.shape
            return np.stack([img, img, img], axis=-1)
        return img

    mock.cvtColor = mock_cvt_color

    # Mock remap for DIBR warping
    def mock_remap(img, map1, map2, interpolation, borderMode=0, borderValue=0):
        # Return a copy of the input image with same shape and dtype
        return img.copy()

    mock.remap = mock_remap
    mock.BORDER_CONSTANT = 0
    mock.INTER_LINEAR = 1

    # Mock resize for side-by-side generator
    # Use simple slicing for nearest-neighbor-like resize (preserves content)
    def mock_resize(img, dsize, interpolation=1):
        target_h, target_w = dsize[1], dsize[0]
        src_h, src_w = img.shape[:2]

        # Calculate scale factors
        scale_y = src_h / target_h
        scale_x = src_w / target_w

        # Simple nearest-neighbor interpolation
        y_indices = (np.arange(target_h) * scale_y).astype(int)
        x_indices = (np.arange(target_w) * scale_x).astype(int)

        # Clip to valid range
        y_indices = np.clip(y_indices, 0, src_h - 1)
        x_indices = np.clip(x_indices, 0, src_w - 1)

        if len(img.shape) == 3:
            result = img[y_indices][:, x_indices]
            return result
        return img[np.ix_(y_indices, x_indices)]

    mock.resize = mock_resize
    mock.INTER_AREA = 3
    return mock


def _create_mock_loguru() -> MagicMock:
    """Create a mock loguru module."""
    mock_logger_instance = MagicMock()
    mock_logger_instance.debug = MagicMock()
    mock_logger_instance.info = MagicMock()
    mock_logger_instance.warning = MagicMock()
    mock_logger_instance.error = MagicMock()
    mock_logger_instance.exception = MagicMock()
    mock_logger_instance.bind = MagicMock(return_value=mock_logger_instance)
    mock_logger_instance.remove = MagicMock()
    mock_logger_instance.add = MagicMock()
    mock_logger_instance.level = MagicMock(return_value=MagicMock(no=40))

    mock_loguru = MagicMock()
    mock_loguru.logger = mock_logger_instance
    return mock_loguru


# Set up mocks before any test module is imported.
# Only fall back to mocks when the real package is unavailable; CI installs
# the real dependencies, and tests that exercise real image/video paths
# (Canny, Hough, GaussianBlur, ...) fail against unconditional mocks.
try:
    import torch  # noqa: F401
except ImportError:
    sys.modules["torch"] = _create_mock_torch()
    sys.modules["torch.nn"] = MagicMock()
    sys.modules["torch.nn.functional"] = MagicMock()
    sys.modules["torchvision"] = MagicMock()
    sys.modules["torchvision.transforms"] = MagicMock()

try:
    import cv2  # noqa: F401
except ImportError:
    sys.modules["cv2"] = _create_mock_cv2()

try:
    import loguru  # noqa: F401
except ImportError:
    sys.modules["loguru"] = _create_mock_loguru()

try:
    import scipy  # noqa: F401
except ImportError:
    mock_scipy = MagicMock()
    mock_scipy.ndimage = MagicMock()
    mock_scipy.ndimage.laplace = MagicMock(return_value=np.zeros((10, 10)))
    mock_scipy.ndimage.zoom = MagicMock(return_value=np.zeros((10, 10)))
    mock_scipy.interpolate = MagicMock()
    mock_scipy.interpolate.CubicSpline = MagicMock
    mock_scipy.interpolate.interp1d = MagicMock
    mock_scipy.signal = MagicMock()
    sys.modules["scipy"] = mock_scipy
    sys.modules["scipy.ndimage"] = mock_scipy.ndimage
    sys.modules["scipy.interpolate"] = mock_scipy.interpolate
    sys.modules["scipy.signal"] = mock_scipy.signal
