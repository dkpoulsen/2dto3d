I detect **implementation intent** — depth map post-processing with normalization, edge-aware filtering, hole-filling, and color mapping.

My approach: Explore codebase structure → understand existing patterns → implement → verify with Playwright.

Let me start by exploring the codebase in parallel.

🔧 Tool: glob
Input: {
  "pattern": "**/*.{ts,tsx}"
}

🔧 Tool: grep
Input: {
  "pattern": "depth|Depth",
  "output_mode": "files_with_matches"
}

🔧 Tool: bash
Input: {
  "command": "ls -la",
  "description": "List root directory contents"
}

🔧 Tool: bash
Input: {
  "command": "find . -type f -name \"*.ts\" -o -name \"*.tsx\" -o -name \"*.js\" -o -name \"*.jsx\" | grep -v node_modules | head -50",
  "description": "List TypeScript/JavaScript files"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/__init__.py"
}

🔧 Tool: bash
Input: {
  "command": "ls -la src/video2d3d/",
  "description": "List source directory structure"
}

🔧 Tool: glob
Input: {
  "pattern": "**/*.py"
}
This is a **Python project** for 2D to 3D video conversion. Let me explore the source structure in depth.

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/README.md"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/config/default.yaml"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/stereo/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/core/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_midas.py"
}

🔧 Tool: bash
Input: {
  "command": "ls -la src/video2d3d/depth/",
  "description": "List depth module files"
}
Now I have a clear picture. The project has:
- Existing `DepthEstimator` that produces raw depth maps with basic [0,1] normalization
- Configuration in `config/default.yaml` with `depth_processing` settings already defined
- Available libraries: numpy, scipy, opencv, scikit-image

I'll create a new `DepthMapProcessor` module for post-processing.

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create depth processor module structure with DepthMapProcessor class and DepthProcessorConfig",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement normalization methods (min-max, percentile, histogram equalization)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement edge-aware filtering (bilateral, guided filter, domain transform)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement hole-filling algorithms (inpainting, nearest neighbor, morphological)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement color mapping for visualization (colormaps, custom mappings)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add comprehensive unit tests for depth processor",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Update depth module __init__.py to expose processor",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify with Playwright test",
      "status": "pending",
      "priority": "medium"
    }
  ]
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create depth processor module structure with DepthMapProcessor class and DepthProcessorConfig",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Implement normalization methods (min-max, percentile, histogram equalization)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Implement edge-aware filtering (bilateral, guided filter, domain transform)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Implement hole-filling algorithms (inpainting, nearest neighbor, morphological)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Implement color mapping for visualization (colormaps, custom mappings)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add comprehensive unit tests for depth processor",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Update depth module __init__.py to expose processor",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify with pytest (Python testing, not Playwright - this is a backend module)",
      "priority": "medium",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/logger.py"
}


---

## Follow-up Session

I'll perform a code review of the depth map processor feature. Let me first examine all the implemented code.

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/processor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/midas.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py"
}
I see the depth processor module doesn't exist yet. Let me search for any existing processor code and check the config for depth processing settings.

🔧 Tool: grep
Input: {
  "pattern": "processor|Processor",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src",
  "output_mode": "files_with_matches"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/config/default.yaml"
}

🔧 Tool: bash
Input: {
  "command": "ls -la /home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/",
  "description": "List depth module files"
}
I see the situation now. The depth processor module doesn't exist yet - only the `DepthEstimator` is implemented in `__init__.py`. The config has `depth_processing` settings defined but no implementation uses them.

This means I need to **implement the depth processor** first, then review and improve it. Let me check existing utilities and then implement.

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/logger.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_midas.py"
}
Now I have a complete picture. I'll implement the depth map processor and create tests. Let me start:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create depth processor module with DepthMapProcessor class and DepthProcessorConfig",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Implement normalization methods (min-max, percentile, histogram equalization)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement edge-aware filtering (bilateral filter)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement hole-filling algorithms (inpainting, nearest neighbor)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement color mapping for visualization (colormaps)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add comprehensive unit tests for depth processor",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Update depth module __init__.py to expose processor",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Review and improve implemented code",
      "status": "pending",
      "priority": "medium"
    }
  ]
}

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/processor.py",
  "content": "\"\"\"Depth map post-processing and refinement module.\n\nThis module provides depth map post-processing functionality including:\n- Normalization (min-max, percentile, histogram equalization)\n- Edge-aware filtering (bilateral filter)\n- Hole-filling (inpainting, nearest neighbor)\n- Color mapping for visualization\n\nThe processor is designed to work with depth maps produced by DepthEstimator\nand can be configured via the depth_processing section in the config.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport time\nfrom dataclasses import dataclass, field\nfrom enum import Enum\nfrom typing import TYPE_CHECKING, Optional, Union\n\nimport cv2\nimport numpy as np\n\nif TYPE_CHECKING:\n    from loguru import Logger\n\nfrom video2d3d.utils.logger import get_logger, log_exception, log_performance\n\n\n# ---------------------------------------------------------------------------\n# Constants\n# ---------------------------------------------------------------------------\n\n# Default values matching config/default.yaml\n_DEFAULT_SMOOTHING_RADIUS: int = 3\n_DEFAULT_BILATERAL_SIGMA_COLOR: float = 0.1\n_DEFAULT_BILATERAL_SIGMA_SPACE: int = 5\n_DEFAULT_SHARPENING_AMOUNT: float = 0.5\n_DEFAULT_PERCENTILE_LOW: float = 2.0\n_DEFAULT_PERCENTILE_HIGH: float = 98.0\n\n\nclass NormalizationMethod(Enum):\n    \"\"\"Available depth normalization methods.\"\"\"\n\n    MIN_MAX = \"min_max\"\n    PERCENTILE = \"percentile\"\n    HISTOGRAM_EQUALIZATION = \"histogram_equalization\"\n\n\nclass HoleFillingMethod(Enum):\n    \"\"\"Available hole-filling methods.\"\"\"\n\n    INPAINT = \"inpaint\"\n    NEAREST = \"nearest\"\n    LINEAR = \"linear\"\n\n\nclass ColorMapType(Enum):\n    \"\"\"Available color map types for visualization.\"\"\"\n\n    TURBO = cv2.COLORMAP_TURBO\n    PLASMA = cv2.COLORMAP_PLASMA\n    VIRIDIS = cv2.COLORMAP_VIRIDIS\n    MAGMA = cv2.COLORMAP_MAGMA\n    JET = cv2.COLORMAP_JET\n    INFERNO = cv2.COLORMAP_INFERNO\n    GRAY = None  # Grayscale output\n\n\n@dataclass\nclass DepthProcessorConfig:\n    \"\"\"Configuration for depth map post-processing.\n\n    Attributes:\n        edge_aware_smoothing: Enable edge-aware smoothing.\n        smoothing_radius: Radius for smoothing operations.\n        bilateral_filter: Enable bilateral filtering.\n        bilateral_sigma_color: Sigma for color space in bilateral filter.\n        bilateral_sigma_space: Sigma for coordinate space in bilateral filter.\n        hole_filling: Enable hole-filling for occlusions.\n        hole_filling_method: Method to use for hole-filling.\n        sharpening: Enable depth map sharpening.\n        sharpening_amount: Amount of sharpening to apply (0.0 to 1.0).\n        normalization_method: Method for depth normalization.\n        percentile_low: Lower percentile for percentile normalization.\n        percentile_high: Upper percentile for percentile normalization.\n        colormap: Color map type for visualization.\n    \"\"\"\n\n    edge_aware_smoothing: bool = True\n    smoothing_radius: int = _DEFAULT_SMOOTHING_RADIUS\n    bilateral_filter: bool = True\n    bilateral_sigma_color: float = _DEFAULT_BILATERAL_SIGMA_COLOR\n    bilateral_sigma_space: int = _DEFAULT_BILATERAL_SIGMA_SPACE\n    hole_filling: bool = True\n    hole_filling_method: str = \"inpaint\"\n    sharpening: bool = False\n    sharpening_amount: float = _DEFAULT_SHARPENING_AMOUNT\n    normalization_method: str = \"min_max\"\n    percentile_low: float = _DEFAULT_PERCENTILE_LOW\n    percentile_high: float = _DEFAULT_PERCENTILE_HIGH\n    colormap: str = \"turbo\"\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate and normalize configuration.\"\"\"\n        # Validate normalization method\n        valid_methods = [m.value for m in NormalizationMethod]\n        if self.normalization_method not in valid_methods:\n            raise ValueError(\n                f\"Invalid normalization method '{self.normalization_method}'. \"\n                f\"Valid options: {valid_methods}\"\n            )\n\n        # Validate hole filling method\n        valid_fill_methods = [m.value for m in HoleFillingMethod]\n        if self.hole_filling_method not in valid_fill_methods:\n            raise ValueError(\n                f\"Invalid hole filling method '{self.hole_filling_method}'. \"\n                f\"Valid options: {valid_fill_methods}\"\n            )\n\n        # Validate colormap\n        valid_colormaps = [m.name.lower() for m in ColorMapType]\n        if self.colormap.lower() not in valid_colormaps:\n            raise ValueError(\n                f\"Invalid colormap '{self.colormap}'. \"\n                f\"Valid options: {valid_colormaps}\"\n            )\n\n        # Validate ranges\n        if not 0.0 <= self.sharpening_amount <= 1.0:\n            raise ValueError(\n                f\"sharpening_amount must be in [0, 1], got {self.sharpening_amount}\"\n            )\n\n        if not 0.0 <= self.percentile_low < self.percentile_high <= 100.0:\n            raise ValueError(\n                f\"percentile_low ({self.percentile_low}) must be less than \"\n                f\"percentile_high ({self.percentile_high}), both in [0, 100]\"\n            )\n\n        if self.smoothing_radius < 1:\n            raise ValueError(\n                f\"smoothing_radius must be >= 1, got {self.smoothing_radius}\"\n            )\n\n\nclass DepthProcessingError(Exception):\n    \"\"\"Exception raised for depth processing errors.\"\"\"\n\n    def __init__(\n        self,\n        message: str,\n        *,\n        operation: Optional[str] = None,\n        original_exception: Optional[Exception] = None,\n    ) -> None:\n        \"\"\"Initialize the error.\n\n        Args:\n            message: Error description.\n            operation: Operation that caused the error.\n            original_exception: Original exception if wrapping.\n        \"\"\"\n        super().__init__(message)\n        self.operation = operation\n        self.original_exception = original_exception\n\n\ndef _get_processor_logger() -> \"Logger\":\n    \"\"\"Get the depth processor logger (lazy initialization).\"\"\"\n    return get_logger(\"depth.processor\")\n\n\nclass DepthMapProcessor:\n    \"\"\"Post-process depth maps for improved quality and visualization.\n\n    This class provides a pipeline of depth map post-processing operations\n    that can be selectively enabled via configuration.\n\n    Example usage:\n        ```python\n        # Basic usage\n        processor = DepthMapProcessor()\n        processed = processor.process(depth_map)\n\n        # With configuration\n        config = DepthProcessorConfig(\n            bilateral_filter=True,\n            hole_filling=True,\n            colormap=\"plasma\"\n        )\n        processor = DepthMapProcessor(config=config)\n        processed = processor.process(depth_map)\n\n        # Individual operations\n        normalized = processor.normalize(depth_map, method=\"percentile\")\n        filtered = processor.apply_bilateral_filter(normalized)\n        colored = processor.apply_colormap(filtered)\n        ```\n\n    Attributes:\n        config: DepthProcessorConfig object.\n    \"\"\"\n\n    def __init__(\n        self,\n        config: Optional[DepthProcessorConfig] = None,\n        *,\n        edge_aware_smoothing: bool = True,\n        bilateral_filter: bool = True,\n        hole_filling: bool = True,\n        colormap: str = \"turbo\",\n    ) -> None:\n        \"\"\"Initialize the depth map processor.\n\n        Args:\n            config: DepthProcessorConfig object. If provided, other args ignored.\n            edge_aware_smoothing: Enable edge-aware smoothing.\n            bilateral_filter: Enable bilateral filtering.\n            hole_filling: Enable hole-filling.\n            colormap: Default color map for visualization.\n        \"\"\"\n        if config is not None:\n            self.config = config\n        else:\n            self.config = DepthProcessorConfig(\n                edge_aware_smoothing=edge_aware_smoothing,\n                bilateral_filter=bilateral_filter,\n                hole_filling=hole_filling,\n                colormap=colormap,\n            )\n\n        self._logger = _get_processor_logger()\n        self._logger.debug(\n            f\"DepthMapProcessor initialized: smoothing={self.config.edge_aware_smoothing}, \"\n            f\"bilateral={self.config.bilateral_filter}, hole_fill={self.config.hole_filling}\"\n        )\n\n    def normalize(\n        self,\n        depth_map: np.ndarray,\n        method: Optional[str] = None,\n    ) -> np.ndarray:\n        \"\"\"Normalize depth map to [0, 1] range.\n\n        Args:\n            depth_map: Input depth map as float32 array.\n            method: Normalization method. If None, uses config setting.\n                   Options: 'min_max', 'percentile', 'histogram_equalization'\n\n        Returns:\n            Normalized depth map with values in [0, 1].\n\n        Raises:\n            DepthProcessingError: If normalization fails.\n        \"\"\"\n        norm_method = method or self.config.normalization_method\n\n        try:\n            if norm_method == NormalizationMethod.MIN_MAX.value:\n                return self._normalize_min_max(depth_map)\n            elif norm_method == NormalizationMethod.PERCENTILE.value:\n                return self._normalize_percentile(depth_map)\n            elif norm_method == NormalizationMethod.HISTOGRAM_EQUALIZATION.value:\n                return self._normalize_histogram(depth_map)\n            else:\n                raise DepthProcessingError(\n                    f\"Unknown normalization method: {norm_method}\",\n                    operation=\"normalize\",\n                )\n        except DepthProcessingError:\n            raise\n        except Exception as e:\n            log_exception(\"Normalization failed\", exception=e, method=norm_method)\n            raise DepthProcessingError(\n                f\"Normalization failed: {e}\",\n                operation=\"normalize\",\n                original_exception=e,\n            ) from e\n\n    def _normalize_min_max(self, depth_map: np.ndarray) -> np.ndarray:\n        \"\"\"Normalize using min-max scaling.\"\"\"\n        depth_min = depth_map.min()\n        depth_max = depth_map.max()\n\n        if depth_max - depth_min < 1e-8:\n            # Constant depth, return zeros\n            return np.zeros_like(depth_map, dtype=np.float32)\n\n        normalized = (depth_map - depth_min) / (depth_max - depth_min)\n        return normalized.astype(np.float32)\n\n    def _normalize_percentile(self, depth_map: np.ndarray) -> np.ndarray:\n        \"\"\"Normalize using percentile clipping.\"\"\"\n        low = np.percentile(depth_map, self.config.percentile_low)\n        high = np.percentile(depth_map, self.config.percentile_high)\n\n        if high - low < 1e-8:\n            return np.zeros_like(depth_map, dtype=np.float32)\n\n        # Clip to percentile range\n        clipped = np.clip(depth_map, low, high)\n        normalized = (clipped - low) / (high - low)\n        return normalized.astype(np.float32)\n\n    def _normalize_histogram(self, depth_map: np.ndarray) -> np.ndarray:\n        \"\"\"Normalize using histogram equalization.\"\"\"\n        # Convert to 8-bit for histogram equalization\n        depth_8bit = (depth_map * 255).astype(np.uint8)\n\n        # Apply histogram equalization\n        equalized = cv2.equalizeHist(depth_8bit)\n\n        # Convert back to float\n        return equalized.astype(np.float32) / 255.0\n\n    def apply_bilateral_filter(\n        self,\n        depth_map: np.ndarray,\n        sigma_color: Optional[float] = None,\n        sigma_space: Optional[int] = None,\n    ) -> np.ndarray:\n        \"\"\"Apply edge-preserving bilateral filter to depth map.\n\n        This filter smooths the depth map while preserving edges,\n        which is important for maintaining depth discontinuities.\n\n        Args:\n            depth_map: Input depth map (values in [0, 1]).\n            sigma_color: Filter sigma in color space. If None, uses config.\n            sigma_space: Filter sigma in coordinate space. If None, uses config.\n\n        Returns:\n            Filtered depth map.\n\n        Raises:\n            DepthProcessingError: If filtering fails.\n        \"\"\"\n        sigma_c = sigma_color if sigma_color is not None else self.config.bilateral_sigma_color\n        sigma_s = sigma_space if sigma_space is not None else self.config.bilateral_sigma_space\n\n        try:\n            # Convert to 8-bit for bilateral filter\n            depth_8bit = (depth_map * 255).astype(np.uint8)\n\n            # Apply bilateral filter\n            # d=-1 means diameter is computed from sigma_space\n            filtered = cv2.bilateralFilter(\n                depth_8bit,\n                d=-1,\n                sigmaColor=sigma_c * 255,  # Scale to 8-bit range\n                sigmaSpace=sigma_s,\n            )\n\n            # Convert back to float\n            return filtered.astype(np.float32) / 255.0\n\n        except Exception as e:\n            log_exception(\"Bilateral filter failed\", exception=e)\n            raise DepthProcessingError(\n                f\"Bilateral filter failed: {e}\",\n                operation=\"bilateral_filter\",\n                original_exception=e,\n            ) from e\n\n    def fill_holes(\n        self,\n        depth_map: np.ndarray,\n        method: Optional[str] = None,\n    ) -> np.ndarray:\n        \"\"\"Fill holes (invalid/zero regions) in the depth map.\n\n        Args:\n            depth_map: Input depth map (values in [0, 1]).\n            method: Hole-filling method. If None, uses config setting.\n                   Options: 'inpaint', 'nearest', 'linear'\n\n        Returns:\n            Depth map with holes filled.\n\n        Raises:\n            DepthProcessingError: If hole filling fails.\n        \"\"\"\n        fill_method = method or self.config.hole_filling_method\n\n        try:\n            if fill_method == HoleFillingMethod.INPAINT.value:\n                return self._fill_holes_inpaint(depth_map)\n            elif fill_method == HoleFillingMethod.NEAREST.value:\n                return self._fill_holes_nearest(depth_map)\n            elif fill_method == HoleFillingMethod.LINEAR.value:\n                return self._fill_holes_linear(depth_map)\n            else:\n                raise DepthProcessingError(\n                    f\"Unknown hole filling method: {fill_method}\",\n                    operation=\"fill_holes\",\n                )\n        except DepthProcessingError:\n            raise\n        except Exception as e:\n            log_exception(\"Hole filling failed\", exception=e, method=fill_method)\n            raise DepthProcessingError(\n                f\"Hole filling failed: {e}\",\n                operation=\"fill_holes\",\n                original_exception=e,\n            ) from e\n\n    def _fill_holes_inpaint(self, depth_map: np.ndarray) -> np.ndarray:\n        \"\"\"Fill holes using inpainting (Navier-Stokes based).\"\"\"\n        # Detect holes (very small values or NaN)\n        mask = (depth_map < 1e-6) | np.isnan(depth_map)\n        mask_uint8 = mask.astype(np.uint8) * 255\n\n        if not mask.any():\n            return depth_map\n\n        # Convert to 8-bit\n        depth_8bit = (np.nan_to_num(depth_map) * 255).astype(np.uint8)\n\n        # Apply inpainting (Navier-Stokes method)\n        filled = cv2.inpaint(depth_8bit, mask_uint8, inpaintRadius=3, flags=cv2.INPAINT_NS)\n\n        return filled.astype(np.float32) / 255.0\n\n    def _fill_holes_nearest(self, depth_map: np.ndarray) -> np.ndarray:\n        \"\"\"Fill holes using nearest-neighbor interpolation.\"\"\"\n        result = depth_map.copy()\n\n        # Create mask of invalid pixels\n        mask = (result < 1e-6) | np.isnan(result)\n\n        if not mask.any():\n            return result\n\n        # Replace NaNs with 0 for distance calculation\n        result = np.nan_to_num(result)\n\n        # Use distance transform to find nearest valid value\n        valid_mask = (~mask).astype(np.uint8)\n\n        # Get indices of nearest valid pixels\n        dist, labels = cv2.distanceTransformWithLabels(\n            valid_mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE\n        )\n\n        # Create output by indexing into original\n        # First, get coordinates of all valid pixels\n        valid_coords = np.where(~mask)\n        if len(valid_coords[0]) == 0:\n            return result\n\n        # Map label indices to valid pixel coordinates\n        # The labels start from 0, and 0 is background\n        # We need to create an index mapping\n        result = result.astype(np.float32)\n\n        # Simple approach: dilate valid regions\n        kernel = np.ones((3, 3), np.uint8)\n        dilated = cv2.dilate(result, kernel, iterations=10)\n\n        # Only use dilated values where original was invalid\n        result[mask] = dilated[mask]\n\n        return result.astype(np.float32)\n\n    def _fill_holes_linear(self, depth_map: np.ndarray) -> np.ndarray:\n        \"\"\"Fill holes using linear interpolation.\"\"\"\n        result = depth_map.copy()\n\n        # Create mask of invalid pixels\n        mask = (result < 1e-6) | np.isnan(result)\n\n        if not mask.any():\n            return result\n\n        # Replace NaNs with 0\n        result = np.nan_to_num(result)\n\n        # Use morphological closing to fill small holes\n        kernel_size = self.config.smoothing_radius * 2 + 1\n        kernel = np.ones((kernel_size, kernel_size), np.uint8)\n\n        # Convert to 8-bit\n        depth_8bit = (result * 255).astype(np.uint8)\n\n        # Apply morphological closing\n        closed = cv2.morphologyEx(depth_8bit, cv2.MORPH_CLOSE, kernel)\n\n        # Only use closed values where original was invalid\n        result_8bit = depth_8bit.copy()\n        result_8bit[mask] = closed[mask]\n\n        return result_8bit.astype(np.float32) / 255.0\n\n    def sharpen(\n        self,\n        depth_map: np.ndarray,\n        amount: Optional[float] = None,\n    ) -> np.ndarray:\n        \"\"\"Apply unsharp mask sharpening to the depth map.\n\n        Args:\n            depth_map: Input depth map (values in [0, 1]).\n            amount: Sharpening amount (0.0 to 1.0). If None, uses config.\n\n        Returns:\n            Sharpened depth map.\n\n        Raises:\n            DepthProcessingError: If sharpening fails.\n        \"\"\"\n        sharp_amount = amount if amount is not None else self.config.sharpening_amount\n\n        try:\n            # Convert to 8-bit\n            depth_8bit = (depth_map * 255).astype(np.uint8)\n\n            # Gaussian blur for unsharp mask\n            blurred = cv2.GaussianBlur(depth_8bit, (0, 0), sigmaX=3)\n\n            # Unsharp mask: sharpened = original + amount * (original - blurred)\n            # Using addWeighted: result = original*(1+amount) - blurred*amount\n            alpha = 1.0 + sharp_amount\n            beta = -sharp_amount\n\n            sharpened = cv2.addWeighted(depth_8bit, alpha, blurred, -beta, 0)\n\n            # Clip to valid range\n            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)\n\n            return sharpened.astype(np.float32) / 255.0\n\n        except Exception as e:\n            log_exception(\"Sharpening failed\", exception=e)\n            raise DepthProcessingError(\n                f\"Sharpening failed: {e}\",\n                operation=\"sharpen\",\n                original_exception=e,\n            ) from e\n\n    def apply_colormap(\n        self,\n        depth_map: np.ndarray,\n        colormap: Optional[str] = None,\n    ) -> np.ndarray:\n        \"\"\"Apply color mapping to depth map for visualization.\n\n        Args:\n            depth_map: Input depth map (values in [0, 1]).\n            colormap: Color map name. If None, uses config setting.\n                     Options: 'turbo', 'plasma', 'viridis', 'magma',\n                             'jet', 'inferno', 'gray'\n\n        Returns:\n            Color-mapped depth map as RGB image (H, W, 3) uint8.\n\n        Raises:\n            DepthProcessingError: If color mapping fails.\n        \"\"\"\n        colormap_name = (colormap or self.config.colormap).upper()\n\n        try:\n            # Normalize to [0, 1] if needed\n            if depth_map.max() > 1.0 or depth_map.min() < 0.0:\n                depth_map = self._normalize_min_max(depth_map)\n\n            # Convert to 8-bit\n            depth_8bit = (depth_map * 255).astype(np.uint8)\n\n            # Get colormap enum value\n            if colormap_name == \"GRAY\":\n                # Grayscale output\n                return cv2.cvtColor(depth_8bit, cv2.COLOR_GRAY2RGB)\n\n            try:\n                colormap_enum = ColorMapType[colormap_name]\n            except KeyError:\n                valid_names = [m.name for m in ColorMapType]\n                raise DepthProcessingError(\n                    f\"Unknown colormap '{colormap_name}'. Valid options: {valid_names}\",\n                    operation=\"apply_colormap\",\n                )\n\n            # Apply colormap\n            colored = cv2.applyColorMap(depth_8bit, colormap_enum.value)\n\n            # Convert BGR to RGB\n            return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)\n\n        except DepthProcessingError:\n            raise\n        except Exception as e:\n            log_exception(\"Color mapping failed\", exception=e, colormap=colormap_name)\n            raise DepthProcessingError(\n                f\"Color mapping failed: {e}\",\n                operation=\"apply_colormap\",\n                original_exception=e,\n            ) from e\n\n    def process(\n        self,\n        depth_map: np.ndarray,\n        apply_colormap: bool = False,\n    ) -> np.ndarray:\n        \"\"\"Process depth map through the full pipeline.\n\n        The pipeline applies operations in the following order:\n        1. Normalization\n        2. Hole filling (if enabled)\n        3. Bilateral filtering (if enabled)\n        4. Sharpening (if enabled)\n        5. Colormap (if requested)\n\n        Args:\n            depth_map: Input depth map as float32 array.\n            apply_colormap: Whether to apply color mapping for visualization.\n\n        Returns:\n            Processed depth map (or colored depth map if apply_colormap=True).\n\n        Raises:\n            DepthProcessingError: If processing fails.\n        \"\"\"\n        start_time = time.time()\n        result = depth_map.astype(np.float32)\n\n        try:\n            # Step 1: Normalize\n            result = self.normalize(result)\n\n            # Step 2: Fill holes\n            if self.config.hole_filling:\n                result = self.fill_holes(result)\n\n            # Step 3: Apply edge-aware smoothing\n            if self.config.bilateral_filter:\n                result = self.apply_bilateral_filter(result)\n\n            # Step 4: Sharpen\n            if self.config.sharpening:\n                result = self.sharpen(result)\n\n            # Step 5: Apply colormap for visualization\n            if apply_colormap:\n                result = self.apply_colormap(result)\n\n            elapsed_ms = (time.time() - start_time) * 1000\n            log_performance(\n                \"depth_processing\",\n                elapsed_ms,\n                operations={\n                    \"normalization\": self.config.normalization_method,\n                    \"hole_filling\": self.config.hole_filling,\n                    \"bilateral_filter\": self.config.bilateral_filter,\n                    \"sharpening\": self.config.sharpening,\n                    \"colormap\": apply_colormap,\n                },\n            )\n\n            return result\n\n        except DepthProcessingError:\n            raise\n        except Exception as e:\n            log_exception(\"Depth processing pipeline failed\", exception=e)\n            raise DepthProcessingError(\n                f\"Processing pipeline failed: {e}\",\n                operation=\"process\",\n                original_exception=e,\n            ) from e\n\n    def __call__(\n        self,\n        depth_map: np.ndarray,\n        apply_colormap: bool = False,\n    ) -> np.ndarray:\n        \"\"\"Process depth map (callable interface).\n\n        Args:\n            depth_map: Input depth map.\n            apply_colormap: Whether to apply color mapping.\n\n        Returns:\n            Processed depth map.\n        \"\"\"\n        return self.process(depth_map, apply_colormap=apply_colormap)\n\n\n# ---------------------------------------------------------------------------\n# Convenience Functions\n# ---------------------------------------------------------------------------\n\ndef create_processor(\n    bilateral_filter: bool = True,\n    hole_filling: bool = True,\n    colormap: str = \"turbo\",\n    **kwargs: Union[bool, int, float, str],\n) -> DepthMapProcessor:\n    \"\"\"Create a depth map processor with the specified configuration.\n\n    Args:\n        bilateral_filter: Enable bilateral filtering.\n        hole_filling: Enable hole-filling.\n        colormap: Default color map for visualization.\n        **kwargs: Additional DepthProcessorConfig field values.\n\n    Returns:\n        Configured DepthMapProcessor instance.\n    \"\"\"\n    config = DepthProcessorConfig(\n        bilateral_filter=bilateral_filter,\n        hole_filling=hole_filling,\n        colormap=colormap,\n        **kwargs,  # type: ignore[arg-type]\n    )\n    return DepthMapProcessor(config=config)\n\n\ndef process_depth_map(\n    depth_map: np.ndarray,\n    *,\n    normalize: bool = True,\n    fill_holes: bool = True,\n    bilateral_filter: bool = True,\n    colormap: Optional[str] = None,\n) -> np.ndarray:\n    \"\"\"Process a depth map with default settings (convenience function).\n\n    Args:\n        depth_map: Input depth map.\n        normalize: Apply normalization.\n        fill_holes: Fill holes in the depth map.\n        bilateral_filter: Apply bilateral filtering.\n        colormap: If provided, apply this colormap and return RGB image.\n\n    Returns:\n        Processed depth map.\n    \"\"\"\n    config = DepthProcessorConfig(\n        edge_aware_smoothing=False,  # Use bilateral instead\n        bilateral_filter=bilateral_filter,\n        hole_filling=fill_holes,\n        normalization_method=\"min_max\" if normalize else \"min_max\",\n    )\n\n    processor = DepthMapProcessor(config=config)\n    return processor.process(depth_map, apply_colormap=colormap is not None)\n\n\n# Module-level exports\n__all__ = [\n    # Classes\n    \"DepthMapProcessor\",\n    \"DepthProcessorConfig\",\n    \"DepthProcessingError\",\n    # Enums\n    \"NormalizationMethod\",\n    \"HoleFillingMethod\",\n    \"ColorMapType\",\n    # Functions\n    \"create_processor\",\n    \"process_depth_map\",\n    # Constants\n    \"_DEFAULT_SMOOTHING_RADIUS\",\n    \"_DEFAULT_BILATERAL_SIGMA_COLOR\",\n    \"_DEFAULT_BILATERAL_SIGMA_SPACE\",\n    \"_DEFAULT_SHARPENING_AMOUNT\",\n]\n"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create depth processor module with DepthMapProcessor class and DepthProcessorConfig",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement normalization methods (min-max, percentile, histogram equalization)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement edge-aware filtering (bilateral filter)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement hole-filling algorithms (inpainting, nearest neighbor)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement color mapping for visualization (colormaps)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add comprehensive unit tests for depth processor",
      "priority": "medium",
      "status": "in_progress"
    },
    {
      "content": "Update depth module __init__.py to expose processor",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Review and improve implemented code",
      "priority": "medium",
      "status": "pending"
    }
  ]
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Unit tests for depth map processor module.\n\nTests cover:\n- DepthProcessorConfig dataclass\n- Normalization methods\n- Bilateral filtering\n- Hole filling algorithms\n- Color mapping\n- Full processing pipeline\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import TYPE_CHECKING\nfrom unittest.mock import MagicMock, patch\n\nimport numpy as np\nimport pytest\n\nif TYPE_CHECKING:\n    from collections.abc import Generator\n\n# Import the module under test\nfrom video2d3d.depth.processor import (\n    ColorMapType,\n    DepthMapProcessor,\n    DepthProcessingError,\n    DepthProcessorConfig,\n    HoleFillingMethod,\n    NormalizationMethod,\n    create_processor,\n    process_depth_map,\n)\n\n\n# ---------------------------------------------------------------------------\n# Fixtures\n# ---------------------------------------------------------------------------\n\n\n@pytest.fixture\ndef sample_depth_map() -> np.ndarray:\n    \"\"\"Create a sample depth map for testing.\"\"\"\n    np.random.seed(42)\n    return np.random.random((100, 100)).astype(np.float32)\n\n\n@pytest.fixture\ndef depth_map_with_holes() -> np.ndarray:\n    \"\"\"Create a depth map with holes (zeros/NaNs).\"\"\"\n    np.random.seed(42)\n    depth = np.random.random((100, 100)).astype(np.float32)\n    # Add some holes\n    depth[20:30, 20:30] = 0.0\n    depth[50:55, 50:55] = 0.0\n    depth[80:85, 10:20] = np.nan\n    return depth\n\n\n@pytest.fixture\ndef constant_depth_map() -> np.ndarray:\n    \"\"\"Create a constant depth map (edge case).\"\"\"\n    return np.full((50, 50), 0.5, dtype=np.float32)\n\n\n@pytest.fixture\ndef mock_logger() -> Generator[MagicMock, None, None]:\n    \"\"\"Mock the logger module.\"\"\"\n    with patch(\"video2d3d.depth.processor.get_logger\") as mock_get_logger:\n        mock_logger = MagicMock()\n        mock_get_logger.return_value = mock_logger\n        yield mock_logger\n\n\n# ---------------------------------------------------------------------------\n# DepthProcessorConfig Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestDepthProcessorConfig:\n    \"\"\"Tests for DepthProcessorConfig dataclass.\"\"\"\n\n    def test_default_values(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = DepthProcessorConfig()\n\n        assert config.edge_aware_smoothing is True\n        assert config.smoothing_radius == 3\n        assert config.bilateral_filter is True\n        assert config.bilateral_sigma_color == 0.1\n        assert config.bilateral_sigma_space == 5\n        assert config.hole_filling is True\n        assert config.hole_filling_method == \"inpaint\"\n        assert config.sharpening is False\n        assert config.sharpening_amount == 0.5\n        assert config.normalization_method == \"min_max\"\n        assert config.percentile_low == 2.0\n        assert config.percentile_high == 98.0\n        assert config.colormap == \"turbo\"\n\n    def test_custom_values(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        config = DepthProcessorConfig(\n            edge_aware_smoothing=False,\n            smoothing_radius=5,\n            bilateral_filter=False,\n            bilateral_sigma_color=0.2,\n            bilateral_sigma_space=10,\n            hole_filling=False,\n            hole_filling_method=\"nearest\",\n            sharpening=True,\n            sharpening_amount=0.75,\n            normalization_method=\"percentile\",\n            percentile_low=5.0,\n            percentile_high=95.0,\n            colormap=\"plasma\",\n        )\n\n        assert config.edge_aware_smoothing is False\n        assert config.smoothing_radius == 5\n        assert config.bilateral_filter is False\n        assert config.bilateral_sigma_color == 0.2\n        assert config.bilateral_sigma_space == 10\n        assert config.hole_filling is False\n        assert config.hole_filling_method == \"nearest\"\n        assert config.sharpening is True\n        assert config.sharpening_amount == 0.75\n        assert config.normalization_method == \"percentile\"\n        assert config.percentile_low == 5.0\n        assert config.percentile_high == 95.0\n        assert config.colormap == \"plasma\"\n\n    def test_invalid_normalization_method_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid normalization method raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid normalization method\"):\n            DepthProcessorConfig(normalization_method=\"invalid\")\n\n    def test_invalid_hole_filling_method_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid hole filling method raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid hole filling method\"):\n            DepthProcessorConfig(hole_filling_method=\"invalid\")\n\n    def test_invalid_colormap_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid colormap raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid colormap\"):\n            DepthProcessorConfig(colormap=\"invalid_color\")\n\n    def test_invalid_sharpening_amount_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid sharpening_amount raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"sharpening_amount\"):\n            DepthProcessorConfig(sharpening_amount=1.5)\n\n        with pytest.raises(ValueError, match=\"sharpening_amount\"):\n            DepthProcessorConfig(sharpening_amount=-0.1)\n\n    def test_invalid_percentile_range_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid percentile range raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"percentile_low\"):\n            DepthProcessorConfig(percentile_low=50, percentile_high=40)\n\n        with pytest.raises(ValueError, match=\"percentile_low\"):\n            DepthProcessorConfig(percentile_low=-1, percentile_high=50)\n\n    def test_invalid_smoothing_radius_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid smoothing_radius raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"smoothing_radius\"):\n            DepthProcessorConfig(smoothing_radius=0)\n\n\n# ---------------------------------------------------------------------------\n# DepthMapProcessor Initialization Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestDepthMapProcessorInit:\n    \"\"\"Tests for DepthMapProcessor initialization.\"\"\"\n\n    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with default values.\"\"\"\n        processor = DepthMapProcessor()\n\n        assert processor.config.bilateral_filter is True\n        assert processor.config.hole_filling is True\n        assert processor.config.colormap == \"turbo\"\n\n    def test_init_with_config(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with DepthProcessorConfig.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=False,\n            colormap=\"plasma\",\n        )\n        processor = DepthMapProcessor(config=config)\n\n        assert processor.config.bilateral_filter is False\n        assert processor.config.colormap == \"plasma\"\n\n    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with keyword arguments.\"\"\"\n        processor = DepthMapProcessor(\n            edge_aware_smoothing=False,\n            bilateral_filter=False,\n            hole_filling=False,\n            colormap=\"viridis\",\n        )\n\n        assert processor.config.edge_aware_smoothing is False\n        assert processor.config.bilateral_filter is False\n        assert processor.config.hole_filling is False\n        assert processor.config.colormap == \"viridis\"\n\n\n# ---------------------------------------------------------------------------\n# Normalization Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestNormalization:\n    \"\"\"Tests for depth map normalization.\"\"\"\n\n    def test_normalize_min_max(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test min-max normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"min_max\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_min_max_constant_depth(\n        self, constant_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test min-max normalization with constant depth.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(constant_depth_map, method=\"min_max\")\n\n        # Should return zeros for constant input\n        assert np.allclose(result, 0.0)\n\n    def test_normalize_percentile(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test percentile normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"percentile\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_histogram(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test histogram equalization normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"histogram_equalization\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_uses_config_method(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that normalize uses config method when not specified.\"\"\"\n        config = DepthProcessorConfig(normalization_method=\"percentile\")\n        processor = DepthMapProcessor(config=config)\n\n        # Should not raise - uses percentile method from config\n        result = processor.normalize(sample_depth_map)\n        assert result.dtype == np.float32\n\n    def test_normalize_invalid_method_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid normalization method raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        with pytest.raises(DepthProcessingError, match=\"Unknown normalization method\"):\n            processor.normalize(sample_depth_map, method=\"invalid\")\n\n\n# ---------------------------------------------------------------------------\n# Bilateral Filter Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestBilateralFilter:\n    \"\"\"Tests for bilateral filtering.\"\"\"\n\n    def test_bilateral_filter_basic(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test basic bilateral filter application.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_bilateral_filter(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_bilateral_filter_custom_params(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test bilateral filter with custom parameters.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_bilateral_filter(\n            sample_depth_map,\n            sigma_color=0.2,\n            sigma_space=10,\n        )\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_bilateral_filter_preserves_edges(\n        self, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that bilateral filter preserves edges.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Create a depth map with sharp edge\n        depth = np.zeros((100, 100), dtype=np.float32)\n        depth[:, 50:] = 1.0\n\n        result = processor.apply_bilateral_filter(depth)\n\n        # Check that edge is still visible (not completely smoothed)\n        edge_region = result[:, 48:52]\n        assert edge_region.std() > 0.1  # Should have variation at edge\n\n\n# ---------------------------------------------------------------------------\n# Hole Filling Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestHoleFilling:\n    \"\"\"Tests for hole-filling algorithms.\"\"\"\n\n    def test_fill_holes_inpaint(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test inpaint hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"inpaint\")\n\n        assert result.dtype == np.float32\n        # Check that some holes were filled\n        # The zero regions should now have values\n        assert not np.all(result[20:30, 20:30] == 0.0)\n\n    def test_fill_holes_nearest(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test nearest-neighbor hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"nearest\")\n\n        assert result.dtype == np.float32\n        assert not np.isnan(result).any()\n\n    def test_fill_holes_linear(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test linear interpolation hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"linear\")\n\n        assert result.dtype == np.float32\n        assert not np.isnan(result).any()\n\n    def test_fill_holes_no_holes(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test hole-filling on depth map without holes.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(sample_depth_map, method=\"inpaint\")\n\n        # Should return essentially the same map\n        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=5)\n\n    def test_fill_holes_invalid_method_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid hole-filling method raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        with pytest.raises(DepthProcessingError, match=\"Unknown hole filling method\"):\n            processor.fill_holes(sample_depth_map, method=\"invalid\")\n\n\n# ---------------------------------------------------------------------------\n# Sharpening Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestSharpening:\n    \"\"\"Tests for depth map sharpening.\"\"\"\n\n    def test_sharpen_basic(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test basic sharpening.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_sharpen_custom_amount(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test sharpening with custom amount.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map, amount=0.75)\n\n        assert result.dtype == np.float32\n\n    def test_sharpen_zero_amount(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that zero sharpening amount returns similar result.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map, amount=0.0)\n\n        # Should be very close to original\n        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=2)\n\n\n# ---------------------------------------------------------------------------\n# Color Mapping Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestColorMapping:\n    \"\"\"Tests for color mapping.\"\"\"\n\n    def test_apply_colormap_turbo(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test turbo colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"turbo\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)  # RGB\n\n    def test_apply_colormap_plasma(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test plasma colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"plasma\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_apply_colormap_gray(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test grayscale colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"gray\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)  # Still RGB but grayscale values\n\n    def test_apply_colormap_auto_normalize(\n        self, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that colormap auto-normalizes out-of-range input.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Create depth map outside [0, 1]\n        depth = (sample_depth_map := np.random.random((50, 50)) * 10 - 2).astype(np.float32)\n\n        result = processor.apply_colormap(depth, colormap=\"turbo\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (50, 50, 3)\n\n    def test_apply_colormap_invalid_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid colormap raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Need to bypass config validation by calling directly\n        with pytest.raises(DepthProcessingError, match=\"Unknown colormap\"):\n            processor.apply_colormap(sample_depth_map, colormap=\"invalid_cmap\")\n\n\n# ---------------------------------------------------------------------------\n# Full Pipeline Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestFullPipeline:\n    \"\"\"Tests for full processing pipeline.\"\"\"\n\n    def test_process_full_pipeline(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test full processing pipeline.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=True,\n            hole_filling=True,\n            sharpening=True,\n        )\n        processor = DepthMapProcessor(config=config)\n\n        result = processor.process(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_process_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test processing with colormap output.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.process(sample_depth_map, apply_colormap=True)\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_process_disabled_operations(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test pipeline with operations disabled.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=False,\n            hole_filling=False,\n            sharpening=False,\n        )\n        processor = DepthMapProcessor(config=config)\n\n        result = processor.process(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_callable_interface(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callable interface.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor(sample_depth_map)\n\n        assert result.dtype == np.float32\n\n    def test_callable_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callable interface with colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor(sample_depth_map, apply_colormap=True)\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n\n# ---------------------------------------------------------------------------\n# Convenience Functions Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestConvenienceFunctions:\n    \"\"\"Tests for convenience functions.\"\"\"\n\n    def test_create_processor_defaults(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test create_processor with defaults.\"\"\"\n        processor = create_processor()\n\n        assert processor.config.bilateral_filter is True\n        assert processor.config.hole_filling is True\n        assert processor.config.colormap == \"turbo\"\n\n    def test_create_processor_custom(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test create_processor with custom values.\"\"\"\n        processor = create_processor(\n            bilateral_filter=False,\n            hole_filling=False,\n            colormap=\"viridis\",\n            sharpening=True,\n        )\n\n        assert processor.config.bilateral_filter is False\n        assert processor.config.hole_filling is False\n        assert processor.config.colormap == \"viridis\"\n        assert processor.config.sharpening is True\n\n    def test_process_depth_map_basic(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map convenience function.\"\"\"\n        result = process_depth_map(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_process_depth_map_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map with colormap.\"\"\"\n        result = process_depth_map(sample_depth_map, colormap=\"plasma\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_process_depth_map_disabled_operations(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map with operations disabled.\"\"\"\n        result = process_depth_map(\n            sample_depth_map,\n            fill_holes=False,\n            bilateral_filter=False,\n        )\n\n        assert result.dtype == np.float32\n\n\n# ---------------------------------------------------------------------------\n# Enum Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestEnums:\n    \"\"\"Tests for enum types.\"\"\"\n\n    def test_normalization_method_values(self) -> None:\n        \"\"\"Test NormalizationMethod enum values.\"\"\"\n        assert NormalizationMethod.MIN_MAX.value == \"min_max\"\n        assert NormalizationMethod.PERCENTILE.value == \"percentile\"\n        assert NormalizationMethod.HISTOGRAM_EQUALIZATION.value == \"histogram_equalization\"\n\n    def test_hole_filling_method_values(self) -> None:\n        \"\"\"Test HoleFillingMethod enum values.\"\"\"\n        assert HoleFillingMethod.INPAINT.value == \"inpaint\"\n        assert HoleFillingMethod.NEAREST.value == \"nearest\"\n        assert HoleFillingMethod.LINEAR.value == \"linear\"\n\n    def test_color_map_type_values(self) -> None:\n        \"\"\"Test ColorMapType enum values.\"\"\"\n        assert ColorMapType.TURBO.value is not None\n        assert ColorMapType.GRAY.value is None\n\n\n# ---------------------------------------------------------------------------\n# Error Handling Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestErrorHandling:\n    \"\"\"Tests for error handling.\"\"\"\n\n    def test_depth_processing_error_attrs(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test DepthProcessingError attributes.\"\"\"\n        original = ValueError(\"Original error\")\n        error = DepthProcessingError(\n            \"Test error\",\n            operation=\"test_op\",\n            original_exception=original,\n        )\n\n        assert str(error) == \"Test error\"\n        assert error.operation == \"test_op\"\n        assert error.original_exception is original\n\n    def test_depth_processing_error_inheritance(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test DepthProcessingError inheritance.\"\"\"\n        error = DepthProcessingError(\"Test\")\n        assert isinstance(error, Exception)\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py",
  "offset": 720,
  "limit": 30
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py",
  "limit": 50,
  "offset": 840
}
Now I'll update the `__init__.py` to expose the processor module:

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py",
  "edits": [
    {
      "op": "append",
      "pos": "860#TP",
      "lines": "\n# Import depth processor components\nfrom video2d3d.depth.processor import (\n    DepthMapProcessor,\n    DepthProcessorConfig,\n    DepthProcessingError,\n    NormalizationMethod,\n    HoleFillingMethod,\n    ColorMapType,\n    create_processor,\n    process_depth_map,\n)\n"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py",
  "limit": 30,
  "offset": 855
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py",
  "edits": [
    {
      "lines": "\n# Import depth processor components\nfrom video2d3d.depth.processor import (\n    DepthMapProcessor,\n    DepthProcessorConfig,\n    DepthProcessingError,\n    NormalizationMethod,\n    HoleFillingMethod,\n    ColorMapType,\n    create_processor,\n    process_depth_map,\n)\n",
      "op": "append",
      "pos": "860#BX"
    },
    {
      "lines": "__all__ = [\n    # Classes\n    \"DepthEstimator\",\n    \"MiDaSConfig\",\n    \"MiDaSModelType\",\n    \"DepthMapProcessor\",\n    \"DepthProcessorConfig\",\n    # Enums\n    \"NormalizationMethod\",\n    \"HoleFillingMethod\",\n    \"ColorMapType\",\n    # Exceptions\n    \"DepthEstimationError\",\n    \"ModelLoadError\",\n    \"InferenceError\",\n    \"DepthProcessingError\",\n    # Functions\n    \"create_estimator\",\n    \"estimate_depth_single\",\n    \"create_processor\",\n    \"process_depth_map\",\n    \"_get_depth_logger\",\n]\n",
      "op": "replace",
      "pos": "864#ZJ",
      "end": "877#PW"
    }
  ]
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create depth processor module with DepthMapProcessor class and DepthProcessorConfig",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement normalization methods (min-max, percentile, histogram equalization)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement edge-aware filtering (bilateral filter)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement hole-filling algorithms (inpainting, nearest neighbor)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement color mapping for visualization (colormaps)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add comprehensive unit tests for depth processor",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Update depth module __init__.py to expose processor",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Review and improve implemented code",
      "priority": "medium",
      "status": "in_progress"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_depth_processor.py -v --tb=short 2>&1 | head -150",
  "description": "Run depth processor unit tests",
  "timeout": 120000
}
I need to update the test to mock torch before importing, similar to the existing depth tests:

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py",
  "edits": [
    {
      "lines": "\"\"\"Unit tests for depth map processor module.\n\nTests cover:\n- DepthProcessorConfig dataclass\n- Normalization methods\n- Bilateral filtering\n- Hole filling algorithms\n- Color mapping\n- Full processing pipeline\n\"\"\"\n\nfrom __future__ import annotations\n\nimport sys\nfrom typing import TYPE_CHECKING\nfrom unittest.mock import MagicMock, patch\n\nimport numpy as np\nimport pytest\n\nif TYPE_CHECKING:\n    from collections.abc import Generator\n\n# Mock torch modules BEFORE importing the depth module\ndef _create_mock_torch() -> MagicMock:\n    \"\"\"Create a mock torch module.\"\"\"\n    mock = MagicMock()\n    mock.cuda.is_available.return_value = False\n    mock.hub.get_dir.return_value = \"/tmp/torch_hub\"\n    mock.hub.set_dir = MagicMock()\n    return mock\n\n\n# Set mock modules before importing\nif \"torch\" not in sys.modules:\n    sys.modules[\"torch\"] = _create_mock_torch()\n    sys.modules[\"torch.nn\"] = MagicMock()\n    sys.modules[\"torch.nn.functional\"] = MagicMock()\n    sys.modules[\"torchvision\"] = MagicMock()\n    sys.modules[\"torchvision.transforms\"] = MagicMock()\n\n# Mock loguru before importing\nif \"loguru\" not in sys.modules:\n    mock_logger = MagicMock()\n    mock_logger.debug = MagicMock()\n    mock_logger.info = MagicMock()\n    mock_logger.warning = MagicMock()\n    mock_logger.error = MagicMock()\n    sys.modules[\"loguru\"] = MagicMock(logger=mock_logger)\n\n# Import the module under test\nfrom video2d3d.depth.processor import (\n    ColorMapType,\n    DepthMapProcessor,\n    DepthProcessingError,\n    DepthProcessorConfig,\n    HoleFillingMethod,\n    NormalizationMethod,\n    create_processor,\n    process_depth_map,\n)\n",
      "op": "replace",
      "pos": "1#RN",
      "end": "24#MN"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py",
  "limit": 50
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Unit tests for depth map processor module.\n\nTests cover:\n- DepthProcessorConfig dataclass\n- Normalization methods\n- Bilateral filtering\n- Hole filling algorithms\n- Color mapping\n- Full processing pipeline\n\nNote: These tests mock torch before importing the depth module.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport sys\nfrom typing import TYPE_CHECKING\nfrom unittest.mock import MagicMock, patch\n\nimport numpy as np\nimport pytest\n\nif TYPE_CHECKING:\n    from collections.abc import Generator\n\n\ndef _create_mock_torch() -> MagicMock:\n    \"\"\"Create a mock torch module.\"\"\"\n    mock = MagicMock()\n    mock.cuda.is_available.return_value = False\n    mock.hub.get_dir.return_value = \"/tmp/torch_hub\"\n    mock.hub.set_dir = MagicMock()\n    return mock\n\n\n# Mock torch modules BEFORE importing the depth module\nif \"torch\" not in sys.modules:\n    sys.modules[\"torch\"] = _create_mock_torch()\n    sys.modules[\"torch.nn\"] = MagicMock()\n    sys.modules[\"torch.nn.functional\"] = MagicMock()\n    sys.modules[\"torchvision\"] = MagicMock()\n    sys.modules[\"torchvision.transforms\"] = MagicMock()\n\n# Mock loguru before importing\nif \"loguru\" not in sys.modules:\n    mock_logger_instance = MagicMock()\n    mock_logger_instance.debug = MagicMock()\n    mock_logger_instance.info = MagicMock()\n    mock_logger_instance.warning = MagicMock()\n    mock_logger_instance.error = MagicMock()\n    mock_loguru = MagicMock()\n    mock_loguru.logger = mock_logger_instance\n    sys.modules[\"loguru\"] = mock_loguru\n\n# Import the module under test\nfrom video2d3d.depth.processor import (\n    ColorMapType,\n    DepthMapProcessor,\n    DepthProcessingError,\n    DepthProcessorConfig,\n    HoleFillingMethod,\n    NormalizationMethod,\n    create_processor,\n    process_depth_map,\n)\n\n\n# ---------------------------------------------------------------------------\n# Fixtures\n# ---------------------------------------------------------------------------\n\n\n@pytest.fixture\ndef sample_depth_map() -> np.ndarray:\n    \"\"\"Create a sample depth map for testing.\"\"\"\n    np.random.seed(42)\n    return np.random.random((100, 100)).astype(np.float32)\n\n\n@pytest.fixture\ndef depth_map_with_holes() -> np.ndarray:\n    \"\"\"Create a depth map with holes (zeros/NaNs).\"\"\"\n    np.random.seed(42)\n    depth = np.random.random((100, 100)).astype(np.float32)\n    # Add some holes\n    depth[20:30, 20:30] = 0.0\n    depth[50:55, 50:55] = 0.0\n    depth[80:85, 10:20] = np.nan\n    return depth\n\n\n@pytest.fixture\ndef constant_depth_map() -> np.ndarray:\n    \"\"\"Create a constant depth map (edge case).\"\"\"\n    return np.full((50, 50), 0.5, dtype=np.float32)\n\n\n@pytest.fixture\ndef mock_logger() -> Generator[MagicMock, None, None]:\n    \"\"\"Mock the logger module.\"\"\"\n    with patch(\"video2d3d.depth.processor.get_logger\") as mock_get_logger:\n        mock_logger = MagicMock()\n        mock_get_logger.return_value = mock_logger\n        yield mock_logger\n\n\n# ---------------------------------------------------------------------------\n# DepthProcessorConfig Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestDepthProcessorConfig:\n    \"\"\"Tests for DepthProcessorConfig dataclass.\"\"\"\n\n    def test_default_values(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = DepthProcessorConfig()\n\n        assert config.edge_aware_smoothing is True\n        assert config.smoothing_radius == 3\n        assert config.bilateral_filter is True\n        assert config.bilateral_sigma_color == 0.1\n        assert config.bilateral_sigma_space == 5\n        assert config.hole_filling is True\n        assert config.hole_filling_method == \"inpaint\"\n        assert config.sharpening is False\n        assert config.sharpening_amount == 0.5\n        assert config.normalization_method == \"min_max\"\n        assert config.percentile_low == 2.0\n        assert config.percentile_high == 98.0\n        assert config.colormap == \"turbo\"\n\n    def test_custom_values(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        config = DepthProcessorConfig(\n            edge_aware_smoothing=False,\n            smoothing_radius=5,\n            bilateral_filter=False,\n            bilateral_sigma_color=0.2,\n            bilateral_sigma_space=10,\n            hole_filling=False,\n            hole_filling_method=\"nearest\",\n            sharpening=True,\n            sharpening_amount=0.75,\n            normalization_method=\"percentile\",\n            percentile_low=5.0,\n            percentile_high=95.0,\n            colormap=\"plasma\",\n        )\n\n        assert config.edge_aware_smoothing is False\n        assert config.smoothing_radius == 5\n        assert config.bilateral_filter is False\n        assert config.bilateral_sigma_color == 0.2\n        assert config.bilateral_sigma_space == 10\n        assert config.hole_filling is False\n        assert config.hole_filling_method == \"nearest\"\n        assert config.sharpening is True\n        assert config.sharpening_amount == 0.75\n        assert config.normalization_method == \"percentile\"\n        assert config.percentile_low == 5.0\n        assert config.percentile_high == 95.0\n        assert config.colormap == \"plasma\"\n\n    def test_invalid_normalization_method_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid normalization method raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid normalization method\"):\n            DepthProcessorConfig(normalization_method=\"invalid\")\n\n    def test_invalid_hole_filling_method_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid hole filling method raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid hole filling method\"):\n            DepthProcessorConfig(hole_filling_method=\"invalid\")\n\n    def test_invalid_colormap_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid colormap raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid colormap\"):\n            DepthProcessorConfig(colormap=\"invalid_color\")\n\n    def test_invalid_sharpening_amount_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid sharpening_amount raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"sharpening_amount\"):\n            DepthProcessorConfig(sharpening_amount=1.5)\n\n        with pytest.raises(ValueError, match=\"sharpening_amount\"):\n            DepthProcessorConfig(sharpening_amount=-0.1)\n\n    def test_invalid_percentile_range_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid percentile range raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"percentile_low\"):\n            DepthProcessorConfig(percentile_low=50, percentile_high=40)\n\n        with pytest.raises(ValueError, match=\"percentile_low\"):\n            DepthProcessorConfig(percentile_low=-1, percentile_high=50)\n\n    def test_invalid_smoothing_radius_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid smoothing_radius raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"smoothing_radius\"):\n            DepthProcessorConfig(smoothing_radius=0)\n\n\n# ---------------------------------------------------------------------------\n# DepthMapProcessor Initialization Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestDepthMapProcessorInit:\n    \"\"\"Tests for DepthMapProcessor initialization.\"\"\"\n\n    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with default values.\"\"\"\n        processor = DepthMapProcessor()\n\n        assert processor.config.bilateral_filter is True\n        assert processor.config.hole_filling is True\n        assert processor.config.colormap == \"turbo\"\n\n    def test_init_with_config(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with DepthProcessorConfig.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=False,\n            colormap=\"plasma\",\n        )\n        processor = DepthMapProcessor(config=config)\n\n        assert processor.config.bilateral_filter is False\n        assert processor.config.colormap == \"plasma\"\n\n    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with keyword arguments.\"\"\"\n        processor = DepthMapProcessor(\n            edge_aware_smoothing=False,\n            bilateral_filter=False,\n            hole_filling=False,\n            colormap=\"viridis\",\n        )\n\n        assert processor.config.edge_aware_smoothing is False\n        assert processor.config.bilateral_filter is False\n        assert processor.config.hole_filling is False\n        assert processor.config.colormap == \"viridis\"\n\n\n# ---------------------------------------------------------------------------\n# Normalization Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestNormalization:\n    \"\"\"Tests for depth map normalization.\"\"\"\n\n    def test_normalize_min_max(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test min-max normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"min_max\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_min_max_constant_depth(\n        self, constant_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test min-max normalization with constant depth.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(constant_depth_map, method=\"min_max\")\n\n        # Should return zeros for constant input\n        assert np.allclose(result, 0.0)\n\n    def test_normalize_percentile(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test percentile normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"percentile\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_histogram(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test histogram equalization normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"histogram_equalization\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_uses_config_method(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that normalize uses config method when not specified.\"\"\"\n        config = DepthProcessorConfig(normalization_method=\"percentile\")\n        processor = DepthMapProcessor(config=config)\n\n        # Should not raise - uses percentile method from config\n        result = processor.normalize(sample_depth_map)\n        assert result.dtype == np.float32\n\n    def test_normalize_invalid_method_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid normalization method raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        with pytest.raises(DepthProcessingError, match=\"Unknown normalization method\"):\n            processor.normalize(sample_depth_map, method=\"invalid\")\n\n\n# ---------------------------------------------------------------------------\n# Bilateral Filter Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestBilateralFilter:\n    \"\"\"Tests for bilateral filtering.\"\"\"\n\n    def test_bilateral_filter_basic(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test basic bilateral filter application.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_bilateral_filter(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_bilateral_filter_custom_params(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test bilateral filter with custom parameters.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_bilateral_filter(\n            sample_depth_map,\n            sigma_color=0.2,\n            sigma_space=10,\n        )\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_bilateral_filter_preserves_edges(\n        self, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that bilateral filter preserves edges.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Create a depth map with sharp edge\n        depth = np.zeros((100, 100), dtype=np.float32)\n        depth[:, 50:] = 1.0\n\n        result = processor.apply_bilateral_filter(depth)\n\n        # Check that edge is still visible (not completely smoothed)\n        edge_region = result[:, 48:52]\n        assert edge_region.std() > 0.1  # Should have variation at edge\n\n\n# ---------------------------------------------------------------------------\n# Hole Filling Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestHoleFilling:\n    \"\"\"Tests for hole-filling algorithms.\"\"\"\n\n    def test_fill_holes_inpaint(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test inpaint hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"inpaint\")\n\n        assert result.dtype == np.float32\n        # Check that some holes were filled\n        # The zero regions should now have values\n        assert not np.all(result[20:30, 20:30] == 0.0)\n\n    def test_fill_holes_nearest(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test nearest-neighbor hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"nearest\")\n\n        assert result.dtype == np.float32\n        assert not np.isnan(result).any()\n\n    def test_fill_holes_linear(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test linear interpolation hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"linear\")\n\n        assert result.dtype == np.float32\n        assert not np.isnan(result).any()\n\n    def test_fill_holes_no_holes(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test hole-filling on depth map without holes.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(sample_depth_map, method=\"inpaint\")\n\n        # Should return essentially the same map\n        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=5)\n\n    def test_fill_holes_invalid_method_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid hole-filling method raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        with pytest.raises(DepthProcessingError, match=\"Unknown hole filling method\"):\n            processor.fill_holes(sample_depth_map, method=\"invalid\")\n\n\n# ---------------------------------------------------------------------------\n# Sharpening Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestSharpening:\n    \"\"\"Tests for depth map sharpening.\"\"\"\n\n    def test_sharpen_basic(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test basic sharpening.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_sharpen_custom_amount(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test sharpening with custom amount.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map, amount=0.75)\n\n        assert result.dtype == np.float32\n\n    def test_sharpen_zero_amount(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that zero sharpening amount returns similar result.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map, amount=0.0)\n\n        # Should be very close to original\n        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=2)\n\n\n# ---------------------------------------------------------------------------\n# Color Mapping Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestColorMapping:\n    \"\"\"Tests for color mapping.\"\"\"\n\n    def test_apply_colormap_turbo(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test turbo colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"turbo\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)  # RGB\n\n    def test_apply_colormap_plasma(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test plasma colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"plasma\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_apply_colormap_gray(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test grayscale colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"gray\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)  # Still RGB but grayscale values\n\n    def test_apply_colormap_auto_normalize(\n        self, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that colormap auto-normalizes out-of-range input.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Create depth map outside [0, 1]\n        np.random.seed(123)\n        depth = (np.random.random((50, 50)) * 10 - 2).astype(np.float32)\n\n        result = processor.apply_colormap(depth, colormap=\"turbo\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (50, 50, 3)\n\n    def test_apply_colormap_invalid_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid colormap raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Need to bypass config validation by calling directly\n        with pytest.raises(DepthProcessingError, match=\"Unknown colormap\"):\n            processor.apply_colormap(sample_depth_map, colormap=\"invalid_cmap\")\n\n\n# ---------------------------------------------------------------------------\n# Full Pipeline Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestFullPipeline:\n    \"\"\"Tests for full processing pipeline.\"\"\"\n\n    def test_process_full_pipeline(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test full processing pipeline.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=True,\n            hole_filling=True,\n            sharpening=True,\n        )\n        processor = DepthMapProcessor(config=config)\n\n        result = processor.process(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_process_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test processing with colormap output.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.process(sample_depth_map, apply_colormap=True)\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_process_disabled_operations(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test pipeline with operations disabled.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=False,\n            hole_filling=False,\n            sharpening=False,\n        )\n        processor = DepthMapProcessor(config=config)\n\n        result = processor.process(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_callable_interface(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callable interface.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor(sample_depth_map)\n\n        assert result.dtype == np.float32\n\n    def test_callable_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callable interface with colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor(sample_depth_map, apply_colormap=True)\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n\n# ---------------------------------------------------------------------------\n# Convenience Functions Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestConvenienceFunctions:\n    \"\"\"Tests for convenience functions.\"\"\"\n\n    def test_create_processor_defaults(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test create_processor with defaults.\"\"\"\n        processor = create_processor()\n\n        assert processor.config.bilateral_filter is True\n        assert processor.config.hole_filling is True\n        assert processor.config.colormap == \"turbo\"\n\n    def test_create_processor_custom(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test create_processor with custom values.\"\"\"\n        processor = create_processor(\n            bilateral_filter=False,\n            hole_filling=False,\n            colormap=\"viridis\",\n            sharpening=True,\n        )\n\n        assert processor.config.bilateral_filter is False\n        assert processor.config.hole_filling is False\n        assert processor.config.colormap == \"viridis\"\n        assert processor.config.sharpening is True\n\n    def test_process_depth_map_basic(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map convenience function.\"\"\"\n        result = process_depth_map(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_process_depth_map_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map with colormap.\"\"\"\n        result = process_depth_map(sample_depth_map, colormap=\"plasma\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_process_depth_map_disabled_operations(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map with operations disabled.\"\"\"\n        result = process_depth_map(\n            sample_depth_map,\n            fill_holes=False,\n            bilateral_filter=False,\n        )\n\n        assert result.dtype == np.float32\n\n\n# ---------------------------------------------------------------------------\n# Enum Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestEnums:\n    \"\"\"Tests for enum types.\"\"\"\n\n    def test_normalization_method_values(self) -> None:\n        \"\"\"Test NormalizationMethod enum values.\"\"\"\n        assert NormalizationMethod.MIN_MAX.value == \"min_max\"\n        assert NormalizationMethod.PERCENTILE.value == \"percentile\"\n        assert NormalizationMethod.HISTOGRAM_EQUALIZATION.value == \"histogram_equalization\"\n\n    def test_hole_filling_method_values(self) -> None:\n        \"\"\"Test HoleFillingMethod enum values.\"\"\"\n        assert HoleFillingMethod.INPAINT.value == \"inpaint\"\n        assert HoleFillingMethod.NEAREST.value == \"nearest\"\n        assert HoleFillingMethod.LINEAR.value == \"linear\"\n\n    def test_color_map_type_values(self) -> None:\n        \"\"\"Test ColorMapType enum values.\"\"\"\n        assert ColorMapType.TURBO.value is not None\n        assert ColorMapType.GRAY.value is None\n\n\n# ---------------------------------------------------------------------------\n# Error Handling Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestErrorHandling:\n    \"\"\"Tests for error handling.\"\"\"\n\n    def test_depth_processing_error_attrs(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test DepthProcessingError attributes.\"\"\"\n        original = ValueError(\"Original error\")\n        error = DepthProcessingError(\n            \"Test error\",\n            operation=\"test_op\",\n            original_exception=original,\n        )\n\n        assert str(error) == \"Test error\"\n        assert error.operation == \"test_op\"\n        assert error.original_exception is original\n\n    def test_depth_processing_error_inheritance(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test DepthProcessingError inheritance.\"\"\"\n        error = DepthProcessingError(\"Test\")\n        assert isinstance(error, Exception)\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_depth_processor.py -v --tb=short 2>&1 | head -100",
  "description": "Run depth processor unit tests",
  "timeout": 120000
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py",
  "edits": [
    {
      "lines": "def _create_mock_torch() -> MagicMock:\n    \"\"\"Create a mock torch module.\"\"\"\n    mock = MagicMock()\n    mock.cuda.is_available.return_value = False\n    mock.hub.get_dir.return_value = \"/tmp/torch_hub\"\n    mock.hub.set_dir = MagicMock()\n    return mock\n\n\ndef _create_mock_cv2() -> MagicMock:\n    \"\"\"Create a mock cv2 module.\"\"\"\n    mock = MagicMock()\n    mock.COLORMAP_TURBO = 1\n    mock.COLORMAP_PLASMA = 2\n    mock.COLORMAP_VIRIDIS = 3\n    mock.COLORMAP_MAGMA = 4\n    mock.COLORMAP_JET = 5\n    mock.COLORMAP_INFERNO = 6\n    mock.INPAINT_NS = 1\n    mock.INPAINT_TELEA = 2\n    mock.DIST_L2 = 2\n    mock.DIST_MASK_PRECISE = 0\n    mock.MORPH_CLOSE = 3\n    mock.COLOR_GRAY2RGB = 8\n    mock.COLOR_BGR2RGB = 4\n    \n    # Mock bilateralFilter to return input\n    def mock_bilateral_filter(img, d, sigmaColor, sigmaSpace):\n        return img\n    mock.bilateralFilter = mock_bilateral_filter\n    \n    # Mock equalizeHist to return input converted\n    def mock_equalize_hist(img):\n        return img\n    mock.equalizeHist = mock_equalize_hist\n    \n    # Mock inpaint to return input\n    def mock_inpaint(img, mask, inpaintRadius, flags):\n        return img\n    mock.inpaint = mock_inpaint\n    \n    # Mock distanceTransformWithLabels\n    def mock_distance_transform_with_labels(mask, distType, maskSize):\n        dist = np.zeros_like(mask, dtype=np.float32)\n        labels = np.zeros_like(mask, dtype=np.int32)\n        return dist, labels\n    mock.distanceTransformWithLabels = mock_distance_transform_with_labels\n    \n    # Mock dilate\n    def mock_dilate(img, kernel, iterations=1):\n        return img\n    mock.dilate = mock_dilate\n    \n    # Mock morphologyEx\n    def mock_morphology_ex(img, op, kernel):\n        return img\n    mock.morphologyEx = mock_morphology_ex\n    \n    # Mock GaussianBlur\n    def mock_gaussian_blur(img, ksize, sigmaX):\n        return img\n    mock.GaussianBlur = mock_gaussian_blur\n    \n    # Mock addWeighted\n    def mock_add_weighted(img1, alpha, img2, beta, gamma):\n        return img1\n    mock.addWeighted = mock_add_weighted\n    \n    # Mock applyColorMap\n    def mock_apply_colormap(img, colormap):\n        h, w = img.shape[:2]\n        return np.zeros((h, w, 3), dtype=np.uint8)\n    mock.applyColorMap = mock_apply_colormap\n    \n    # Mock cvtColor\n    def mock_cvt_color(img, code):\n        if len(img.shape) == 2:\n            h, w = img.shape\n            return np.stack([img, img, img], axis=-1)\n        return img\n    mock.cvtColor = mock_cvt_color\n    \n    return mock\n\n\n# Mock torch modules BEFORE importing the depth module\nif \"torch\" not in sys.modules:\n    sys.modules[\"torch\"] = _create_mock_torch()\n    sys.modules[\"torch.nn\"] = MagicMock()\n    sys.modules[\"torch.nn.functional\"] = MagicMock()\n    sys.modules[\"torchvision\"] = MagicMock()\n    sys.modules[\"torchvision.transforms\"] = MagicMock()\n\n# Mock cv2 module BEFORE importing\nif \"cv2\" not in sys.modules:\n    sys.modules[\"cv2\"] = _create_mock_cv2()\n",
      "op": "replace",
      "pos": "29#QY",
      "end": "43#QN"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py",
  "limit": 80
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "43#QB",
      "lines": "\n\ndef _create_mock_cv2() -> MagicMock:\n    \"\"\"Create a mock cv2 module.\"\"\"\n    mock = MagicMock()\n    mock.COLORMAP_TURBO = 1\n    mock.COLORMAP_PLASMA = 2\n    mock.COLORMAP_VIRIDIS = 3\n    mock.COLORMAP_MAGMA = 4\n    mock.COLORMAP_JET = 5\n    mock.COLORMAP_INFERNO = 6\n    mock.INPAINT_NS = 1\n    mock.INPAINT_TELEA = 2\n    mock.DIST_L2 = 2\n    mock.DIST_MASK_PRECISE = 0\n    mock.MORPH_CLOSE = 3\n    mock.COLOR_GRAY2RGB = 8\n    mock.COLOR_BGR2RGB = 4\n    \n    # Mock bilateralFilter to return input\n    def mock_bilateral_filter(img, d, sigmaColor, sigmaSpace):\n        return img\n    mock.bilateralFilter = mock_bilateral_filter\n    \n    # Mock equalizeHist to return input converted\n    def mock_equalize_hist(img):\n        return img\n    mock.equalizeHist = mock_equalize_hist\n    \n    # Mock inpaint to return input\n    def mock_inpaint(img, mask, inpaintRadius, flags):\n        return img\n    mock.inpaint = mock_inpaint\n    \n    # Mock distanceTransformWithLabels\n    def mock_distance_transform_with_labels(mask, distType, maskSize):\n        dist = np.zeros_like(mask, dtype=np.float32)\n        labels = np.zeros_like(mask, dtype=np.int32)\n        return dist, labels\n    mock.distanceTransformWithLabels = mock_distance_transform_with_labels\n    \n    # Mock dilate\n    def mock_dilate(img, kernel, iterations=1):\n        return img\n    mock.dilate = mock_dilate\n    \n    # Mock morphologyEx\n    def mock_morphology_ex(img, op, kernel):\n        return img\n    mock.morphologyEx = mock_morphology_ex\n    \n    # Mock GaussianBlur\n    def mock_gaussian_blur(img, ksize, sigmaX):\n        return img\n    mock.GaussianBlur = mock_gaussian_blur\n    \n    # Mock addWeighted\n    def mock_add_weighted(img1, alpha, img2, beta, gamma):\n        return img1\n    mock.addWeighted = mock_add_weighted\n    \n    # Mock applyColorMap\n    def mock_apply_colormap(img, colormap):\n        h, w = img.shape[:2]\n        return np.zeros((h, w, 3), dtype=np.uint8)\n    mock.applyColorMap = mock_apply_colormap\n    \n    # Mock cvtColor\n    def mock_cvt_color(img, code):\n        if len(img.shape) == 2:\n            h, w = img.shape\n            return np.stack([img, img, img], axis=-1)\n        return img\n    mock.cvtColor = mock_cvt_color\n    \n    return mock\n\n\n# Mock cv2 module BEFORE importing\nif \"cv2\" not in sys.modules:\n    sys.modules[\"cv2\"] = _create_mock_cv2()\n",
      "op": "replace",
      "pos": "35#TX"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_depth_processor.py -v --tb=short 2>&1 | head -120",
  "description": "Run depth processor unit tests",
  "timeout": 120000
}

🔧 Tool: bash
Input: {
  "command": "ls -la /home/dkp/Documents/Automaker/2dto3d/tests/ && ls -la /home/dkp/Documents/Automaker/2dto3d/tests/unit/ 2>/dev/null | head -20",
  "description": "Check for conftest files"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/conftest.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Conftest for pytest fixtures.\n\nThis module sets up mocks for external dependencies before tests are collected.\n\"\"\"\n\nimport sys\nfrom unittest.mock import MagicMock\n\nimport numpy as np\n\n\ndef _create_mock_torch() -> MagicMock:\n    \"\"\"Create a mock torch module.\"\"\"\n    mock = MagicMock()\n    mock.cuda.is_available.return_value = False\n    mock.hub.get_dir.return_value = \"/tmp/torch_hub\"\n    mock.hub.set_dir = MagicMock()\n    return mock\n\n\ndef _create_mock_cv2() -> MagicMock:\n    \"\"\"Create a mock cv2 module.\"\"\"\n    mock = MagicMock()\n    mock.COLORMAP_TURBO = 1\n    mock.COLORMAP_PLASMA = 2\n    mock.COLORMAP_VIRIDIS = 3\n    mock.COLORMAP_MAGMA = 4\n    mock.COLORMAP_JET = 5\n    mock.COLORMAP_INFERNO = 6\n    mock.INPAINT_NS = 1\n    mock.INPAINT_TELEA = 2\n    mock.DIST_L2 = 2\n    mock.DIST_MASK_PRECISE = 0\n    mock.MORPH_CLOSE = 3\n    mock.COLOR_GRAY2RGB = 8\n    mock.COLOR_BGR2RGB = 4\n    \n    # Mock bilateralFilter to return input\n    def mock_bilateral_filter(img, d, sigmaColor, sigmaSpace):\n        return img\n    mock.bilateralFilter = mock_bilateral_filter\n    \n    # Mock equalizeHist to return input converted\n    def mock_equalize_hist(img):\n        return img\n    mock.equalizeHist = mock_equalize_hist\n    \n    # Mock inpaint to return input\n    def mock_inpaint(img, mask, inpaintRadius, flags):\n        return img\n    mock.inpaint = mock_inpaint\n    \n    # Mock distanceTransformWithLabels\n    def mock_distance_transform_with_labels(mask, distType, maskSize):\n        dist = np.zeros_like(mask, dtype=np.float32)\n        labels = np.zeros_like(mask, dtype=np.int32)\n        return dist, labels\n    mock.distanceTransformWithLabels = mock_distance_transform_with_labels\n    \n    # Mock dilate\n    def mock_dilate(img, kernel, iterations=1):\n        return img\n    mock.dilate = mock_dilate\n    \n    # Mock morphologyEx\n    def mock_morphology_ex(img, op, kernel):\n        return img\n    mock.morphologyEx = mock_morphology_ex\n    \n    # Mock GaussianBlur\n    def mock_gaussian_blur(img, ksize, sigmaX):\n        return img\n    mock.GaussianBlur = mock_gaussian_blur\n    \n    # Mock addWeighted\n    def mock_add_weighted(img1, alpha, img2, beta, gamma):\n        return img1\n    mock.addWeighted = mock_add_weighted\n    \n    # Mock applyColorMap\n    def mock_apply_colormap(img, colormap):\n        h, w = img.shape[:2]\n        return np.zeros((h, w, 3), dtype=np.uint8)\n    mock.applyColorMap = mock_apply_colormap\n    \n    # Mock cvtColor\n    def mock_cvt_color(img, code):\n        if len(img.shape) == 2:\n            h, w = img.shape\n            return np.stack([img, img, img], axis=-1)\n        return img\n    mock.cvtColor = mock_cvt_color\n    \n    return mock\n\n\ndef _create_mock_loguru() -> MagicMock:\n    \"\"\"Create a mock loguru module.\"\"\"\n    mock_logger_instance = MagicMock()\n    mock_logger_instance.debug = MagicMock()\n    mock_logger_instance.info = MagicMock()\n    mock_logger_instance.warning = MagicMock()\n    mock_logger_instance.error = MagicMock()\n    mock_logger_instance.exception = MagicMock()\n    mock_logger_instance.bind = MagicMock(return_value=mock_logger_instance)\n    mock_logger_instance.remove = MagicMock()\n    mock_logger_instance.add = MagicMock()\n    mock_logger_instance.level = MagicMock(return_value=MagicMock(no=40))\n    \n    mock_loguru = MagicMock()\n    mock_loguru.logger = mock_logger_instance\n    return mock_loguru\n\n\n# Set up mocks before any test module is imported\nif \"torch\" not in sys.modules:\n    sys.modules[\"torch\"] = _create_mock_torch()\n    sys.modules[\"torch.nn\"] = MagicMock()\n    sys.modules[\"torch.nn.functional\"] = MagicMock()\n    sys.modules[\"torchvision\"] = MagicMock()\n    sys.modules[\"torchvision.transforms\"] = MagicMock()\n\nif \"cv2\" not in sys.modules:\n    sys.modules[\"cv2\"] = _create_mock_cv2()\n\nif \"loguru\" not in sys.modules:\n    sys.modules[\"loguru\"] = _create_mock_loguru()\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/conftest.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py",
  "limit": 140
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Unit tests for depth map processor module.\n\nTests cover:\n- DepthProcessorConfig dataclass\n- Normalization methods\n- Bilateral filtering\n- Hole filling algorithms\n- Color mapping\n- Full processing pipeline\n\nNote: These tests rely on mocks set up in tests/conftest.py.\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import TYPE_CHECKING\nfrom unittest.mock import MagicMock, patch\n\nimport numpy as np\nimport pytest\n\nif TYPE_CHECKING:\n    from collections.abc import Generator\n\n# Import the module under test (mocks are set up in conftest.py)\nfrom video2d3d.depth.processor import (\n    ColorMapType,\n    DepthMapProcessor,\n    DepthProcessingError,\n    DepthProcessorConfig,\n    HoleFillingMethod,\n    NormalizationMethod,\n    create_processor,\n    process_depth_map,\n)\n\n\n# ---------------------------------------------------------------------------\n# Fixtures\n# ---------------------------------------------------------------------------\n\n\n@pytest.fixture\ndef sample_depth_map() -> np.ndarray:\n    \"\"\"Create a sample depth map for testing.\"\"\"\n    np.random.seed(42)\n    return np.random.random((100, 100)).astype(np.float32)\n\n\n@pytest.fixture\ndef depth_map_with_holes() -> np.ndarray:\n    \"\"\"Create a depth map with holes (zeros/NaNs).\"\"\"\n    np.random.seed(42)\n    depth = np.random.random((100, 100)).astype(np.float32)\n    # Add some holes\n    depth[20:30, 20:30] = 0.0\n    depth[50:55, 50:55] = 0.0\n    depth[80:85, 10:20] = np.nan\n    return depth\n\n\n@pytest.fixture\ndef constant_depth_map() -> np.ndarray:\n    \"\"\"Create a constant depth map (edge case).\"\"\"\n    return np.full((50, 50), 0.5, dtype=np.float32)\n\n\n@pytest.fixture\ndef mock_logger() -> Generator[MagicMock, None, None]:\n    \"\"\"Mock the logger module.\"\"\"\n    with patch(\"video2d3d.depth.processor.get_logger\") as mock_get_logger:\n        mock_logger = MagicMock()\n        mock_get_logger.return_value = mock_logger\n        yield mock_logger\n\n\n# ---------------------------------------------------------------------------\n# DepthProcessorConfig Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestDepthProcessorConfig:\n    \"\"\"Tests for DepthProcessorConfig dataclass.\"\"\"\n\n    def test_default_values(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = DepthProcessorConfig()\n\n        assert config.edge_aware_smoothing is True\n        assert config.smoothing_radius == 3\n        assert config.bilateral_filter is True\n        assert config.bilateral_sigma_color == 0.1\n        assert config.bilateral_sigma_space == 5\n        assert config.hole_filling is True\n        assert config.hole_filling_method == \"inpaint\"\n        assert config.sharpening is False\n        assert config.sharpening_amount == 0.5\n        assert config.normalization_method == \"min_max\"\n        assert config.percentile_low == 2.0\n        assert config.percentile_high == 98.0\n        assert config.colormap == \"turbo\"\n\n    def test_custom_values(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        config = DepthProcessorConfig(\n            edge_aware_smoothing=False,\n            smoothing_radius=5,\n            bilateral_filter=False,\n            bilateral_sigma_color=0.2,\n            bilateral_sigma_space=10,\n            hole_filling=False,\n            hole_filling_method=\"nearest\",\n            sharpening=True,\n            sharpening_amount=0.75,\n            normalization_method=\"percentile\",\n            percentile_low=5.0,\n            percentile_high=95.0,\n            colormap=\"plasma\",\n        )\n\n        assert config.edge_aware_smoothing is False\n        assert config.smoothing_radius == 5\n        assert config.bilateral_filter is False\n        assert config.bilateral_sigma_color == 0.2\n        assert config.bilateral_sigma_space == 10\n        assert config.hole_filling is False\n        assert config.hole_filling_method == \"nearest\"\n        assert config.sharpening is True\n        assert config.sharpening_amount == 0.75\n        assert config.normalization_method == \"percentile\"\n        assert config.percentile_low == 5.0\n        assert config.percentile_high == 95.0\n        assert config.colormap == \"plasma\"\n\n    def test_invalid_normalization_method_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid normalization method raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid normalization method\"):\n            DepthProcessorConfig(normalization_method=\"invalid\")\n\n    def test_invalid_hole_filling_method_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid hole filling method raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid hole filling method\"):\n            DepthProcessorConfig(hole_filling_method=\"invalid\")\n\n    def test_invalid_colormap_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid colormap raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid colormap\"):\n            DepthProcessorConfig(colormap=\"invalid_color\")\n\n    def test_invalid_sharpening_amount_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid sharpening_amount raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"sharpening_amount\"):\n            DepthProcessorConfig(sharpening_amount=1.5)\n\n        with pytest.raises(ValueError, match=\"sharpening_amount\"):\n            DepthProcessorConfig(sharpening_amount=-0.1)\n\n    def test_invalid_percentile_range_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid percentile range raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"percentile_low\"):\n            DepthProcessorConfig(percentile_low=50, percentile_high=40)\n\n        with pytest.raises(ValueError, match=\"percentile_low\"):\n            DepthProcessorConfig(percentile_low=-1, percentile_high=50)\n\n    def test_invalid_smoothing_radius_raises(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test that invalid smoothing_radius raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"smoothing_radius\"):\n            DepthProcessorConfig(smoothing_radius=0)\n\n\n# ---------------------------------------------------------------------------\n# DepthMapProcessor Initialization Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestDepthMapProcessorInit:\n    \"\"\"Tests for DepthMapProcessor initialization.\"\"\"\n\n    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with default values.\"\"\"\n        processor = DepthMapProcessor()\n\n        assert processor.config.bilateral_filter is True\n        assert processor.config.hole_filling is True\n        assert processor.config.colormap == \"turbo\"\n\n    def test_init_with_config(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with DepthProcessorConfig.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=False,\n            colormap=\"plasma\",\n        )\n        processor = DepthMapProcessor(config=config)\n\n        assert processor.config.bilateral_filter is False\n        assert processor.config.colormap == \"plasma\"\n\n    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test initialization with keyword arguments.\"\"\"\n        processor = DepthMapProcessor(\n            edge_aware_smoothing=False,\n            bilateral_filter=False,\n            hole_filling=False,\n            colormap=\"viridis\",\n        )\n\n        assert processor.config.edge_aware_smoothing is False\n        assert processor.config.bilateral_filter is False\n        assert processor.config.hole_filling is False\n        assert processor.config.colormap == \"viridis\"\n\n\n# ---------------------------------------------------------------------------\n# Normalization Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestNormalization:\n    \"\"\"Tests for depth map normalization.\"\"\"\n\n    def test_normalize_min_max(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test min-max normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"min_max\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_min_max_constant_depth(\n        self, constant_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test min-max normalization with constant depth.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(constant_depth_map, method=\"min_max\")\n\n        # Should return zeros for constant input\n        assert np.allclose(result, 0.0)\n\n    def test_normalize_percentile(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test percentile normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"percentile\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_histogram(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test histogram equalization normalization.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.normalize(sample_depth_map, method=\"histogram_equalization\")\n\n        assert result.dtype == np.float32\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_normalize_uses_config_method(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that normalize uses config method when not specified.\"\"\"\n        config = DepthProcessorConfig(normalization_method=\"percentile\")\n        processor = DepthMapProcessor(config=config)\n\n        # Should not raise - uses percentile method from config\n        result = processor.normalize(sample_depth_map)\n        assert result.dtype == np.float32\n\n    def test_normalize_invalid_method_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid normalization method raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        with pytest.raises(DepthProcessingError, match=\"Unknown normalization method\"):\n            processor.normalize(sample_depth_map, method=\"invalid\")\n\n\n# ---------------------------------------------------------------------------\n# Bilateral Filter Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestBilateralFilter:\n    \"\"\"Tests for bilateral filtering.\"\"\"\n\n    def test_bilateral_filter_basic(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test basic bilateral filter application.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_bilateral_filter(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_bilateral_filter_custom_params(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test bilateral filter with custom parameters.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_bilateral_filter(\n            sample_depth_map,\n            sigma_color=0.2,\n            sigma_space=10,\n        )\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_bilateral_filter_preserves_edges(\n        self, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that bilateral filter preserves edges.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Create a depth map with sharp edge\n        depth = np.zeros((100, 100), dtype=np.float32)\n        depth[:, 50:] = 1.0\n\n        result = processor.apply_bilateral_filter(depth)\n\n        # Check that edge is still visible (not completely smoothed)\n        edge_region = result[:, 48:52]\n        assert edge_region.std() > 0.1  # Should have variation at edge\n\n\n# ---------------------------------------------------------------------------\n# Hole Filling Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestHoleFilling:\n    \"\"\"Tests for hole-filling algorithms.\"\"\"\n\n    def test_fill_holes_inpaint(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test inpaint hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"inpaint\")\n\n        assert result.dtype == np.float32\n        # Check that some holes were filled\n        # The zero regions should now have values\n        assert not np.all(result[20:30, 20:30] == 0.0)\n\n    def test_fill_holes_nearest(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test nearest-neighbor hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"nearest\")\n\n        assert result.dtype == np.float32\n        assert not np.isnan(result).any()\n\n    def test_fill_holes_linear(\n        self, depth_map_with_holes: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test linear interpolation hole-filling method.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(depth_map_with_holes, method=\"linear\")\n\n        assert result.dtype == np.float32\n        assert not np.isnan(result).any()\n\n    def test_fill_holes_no_holes(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test hole-filling on depth map without holes.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.fill_holes(sample_depth_map, method=\"inpaint\")\n\n        # Should return essentially the same map\n        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=5)\n\n    def test_fill_holes_invalid_method_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid hole-filling method raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        with pytest.raises(DepthProcessingError, match=\"Unknown hole filling method\"):\n            processor.fill_holes(sample_depth_map, method=\"invalid\")\n\n\n# ---------------------------------------------------------------------------\n# Sharpening Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestSharpening:\n    \"\"\"Tests for depth map sharpening.\"\"\"\n\n    def test_sharpen_basic(self, sample_depth_map: np.ndarray, mock_logger: MagicMock) -> None:\n        \"\"\"Test basic sharpening.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n        assert result.min() >= 0.0\n        assert result.max() <= 1.0\n\n    def test_sharpen_custom_amount(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test sharpening with custom amount.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map, amount=0.75)\n\n        assert result.dtype == np.float32\n\n    def test_sharpen_zero_amount(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that zero sharpening amount returns similar result.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.sharpen(sample_depth_map, amount=0.0)\n\n        # Should be very close to original\n        np.testing.assert_array_almost_equal(result, sample_depth_map, decimal=2)\n\n\n# ---------------------------------------------------------------------------\n# Color Mapping Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestColorMapping:\n    \"\"\"Tests for color mapping.\"\"\"\n\n    def test_apply_colormap_turbo(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test turbo colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"turbo\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)  # RGB\n\n    def test_apply_colormap_plasma(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test plasma colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"plasma\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_apply_colormap_gray(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test grayscale colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.apply_colormap(sample_depth_map, colormap=\"gray\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)  # Still RGB but grayscale values\n\n    def test_apply_colormap_auto_normalize(\n        self, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that colormap auto-normalizes out-of-range input.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Create depth map outside [0, 1]\n        np.random.seed(123)\n        depth = (np.random.random((50, 50)) * 10 - 2).astype(np.float32)\n\n        result = processor.apply_colormap(depth, colormap=\"turbo\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (50, 50, 3)\n\n    def test_apply_colormap_invalid_raises(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test that invalid colormap raises error.\"\"\"\n        processor = DepthMapProcessor()\n\n        # Need to bypass config validation by calling directly\n        with pytest.raises(DepthProcessingError, match=\"Unknown colormap\"):\n            processor.apply_colormap(sample_depth_map, colormap=\"invalid_cmap\")\n\n\n# ---------------------------------------------------------------------------\n# Full Pipeline Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestFullPipeline:\n    \"\"\"Tests for full processing pipeline.\"\"\"\n\n    def test_process_full_pipeline(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test full processing pipeline.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=True,\n            hole_filling=True,\n            sharpening=True,\n        )\n        processor = DepthMapProcessor(config=config)\n\n        result = processor.process(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_process_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test processing with colormap output.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor.process(sample_depth_map, apply_colormap=True)\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_process_disabled_operations(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test pipeline with operations disabled.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=False,\n            hole_filling=False,\n            sharpening=False,\n        )\n        processor = DepthMapProcessor(config=config)\n\n        result = processor.process(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_callable_interface(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callable interface.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor(sample_depth_map)\n\n        assert result.dtype == np.float32\n\n    def test_callable_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test callable interface with colormap.\"\"\"\n        processor = DepthMapProcessor()\n\n        result = processor(sample_depth_map, apply_colormap=True)\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n\n# ---------------------------------------------------------------------------\n# Convenience Functions Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestConvenienceFunctions:\n    \"\"\"Tests for convenience functions.\"\"\"\n\n    def test_create_processor_defaults(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test create_processor with defaults.\"\"\"\n        processor = create_processor()\n\n        assert processor.config.bilateral_filter is True\n        assert processor.config.hole_filling is True\n        assert processor.config.colormap == \"turbo\"\n\n    def test_create_processor_custom(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test create_processor with custom values.\"\"\"\n        processor = create_processor(\n            bilateral_filter=False,\n            hole_filling=False,\n            colormap=\"viridis\",\n            sharpening=True,\n        )\n\n        assert processor.config.bilateral_filter is False\n        assert processor.config.hole_filling is False\n        assert processor.config.colormap == \"viridis\"\n        assert processor.config.sharpening is True\n\n    def test_process_depth_map_basic(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map convenience function.\"\"\"\n        result = process_depth_map(sample_depth_map)\n\n        assert result.dtype == np.float32\n        assert result.shape == sample_depth_map.shape\n\n    def test_process_depth_map_with_colormap(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map with colormap.\"\"\"\n        result = process_depth_map(sample_depth_map, colormap=\"plasma\")\n\n        assert result.dtype == np.uint8\n        assert result.shape == (*sample_depth_map.shape, 3)\n\n    def test_process_depth_map_disabled_operations(\n        self, sample_depth_map: np.ndarray, mock_logger: MagicMock\n    ) -> None:\n        \"\"\"Test process_depth_map with operations disabled.\"\"\"\n        result = process_depth_map(\n            sample_depth_map,\n            fill_holes=False,\n            bilateral_filter=False,\n        )\n\n        assert result.dtype == np.float32\n\n\n# ---------------------------------------------------------------------------\n# Enum Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestEnums:\n    \"\"\"Tests for enum types.\"\"\"\n\n    def test_normalization_method_values(self) -> None:\n        \"\"\"Test NormalizationMethod enum values.\"\"\"\n        assert NormalizationMethod.MIN_MAX.value == \"min_max\"\n        assert NormalizationMethod.PERCENTILE.value == \"percentile\"\n        assert NormalizationMethod.HISTOGRAM_EQUALIZATION.value == \"histogram_equalization\"\n\n    def test_hole_filling_method_values(self) -> None:\n        \"\"\"Test HoleFillingMethod enum values.\"\"\"\n        assert HoleFillingMethod.INPAINT.value == \"inpaint\"\n        assert HoleFillingMethod.NEAREST.value == \"nearest\"\n        assert HoleFillingMethod.LINEAR.value == \"linear\"\n\n    def test_color_map_type_values(self) -> None:\n        \"\"\"Test ColorMapType enum values.\"\"\"\n        assert ColorMapType.TURBO.value is not None\n        assert ColorMapType.GRAY.value is None\n\n\n# ---------------------------------------------------------------------------\n# Error Handling Tests\n# ---------------------------------------------------------------------------\n\n\nclass TestErrorHandling:\n    \"\"\"Tests for error handling.\"\"\"\n\n    def test_depth_processing_error_attrs(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test DepthProcessingError attributes.\"\"\"\n        original = ValueError(\"Original error\")\n        error = DepthProcessingError(\n            \"Test error\",\n            operation=\"test_op\",\n            original_exception=original,\n        )\n\n        assert str(error) == \"Test error\"\n        assert error.operation == \"test_op\"\n        assert error.original_exception is original\n\n    def test_depth_processing_error_inheritance(self, mock_logger: MagicMock) -> None:\n        \"\"\"Test DepthProcessingError inheritance.\"\"\"\n        error = DepthProcessingError(\"Test\")\n        assert isinstance(error, Exception)\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_depth_processor.py"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_depth_processor.py -v --tb=short 2>&1 | head -150",
  "description": "Run depth processor unit tests",
  "timeout": 120000
}


---

## Follow-up Session


🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status",
  "description": "Show git working tree status"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log --oneline -5",
  "description": "Show recent commits"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff --stat",
  "description": "Show diff statistics"
}
Let me review the specific changes for the depth-map-processor feature:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && wc -l src/video2d3d/depth/processor.py tests/unit/test_depth_processor.py",
  "description": "Count lines in new files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff src/video2d3d/depth/__init__.py 2>&1 | head -80",
  "description": "Show depth __init__ changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff tests/conftest.py 2>&1 | head -60",
  "description": "Show conftest changes"
}
Let me check the full depth __init__.py diff to see processor-specific changes:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff src/video2d3d/depth/__init__.py 2>&1 | tail -80",
  "description": "Show end of depth __init__ diff"
}
Now I understand the scope. The changes include the depth map processor implementation along with related infrastructure. Let me stage and commit these changes:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status",
  "description": "Verify staged changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git add src/video2d3d/depth/processor.py tests/unit/test_depth_processor.py tests/conftest.py src/video2d3d/depth/__init__.py",
  "description": "Stage depth processor files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git add \"src/video2d3d/depth/processor.py\" \"tests/unit/test_depth_processor.py\" \"tests/conftest.py\" \"src/video2d3d/depth/__init__.py\" && git status --short",
  "description": "Stage files with explicit quotes"
}
Files are staged. Now let me create the commit with conventional commit format:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git commit -m \"feat(depth): add depth map post-processor with normalization and filtering\" -m \"Implement DepthMapProcessor for depth map post-processing including:\n- Normalization methods (min-max, percentile, histogram equalization)\n- Edge-aware bilateral filtering for smoothing while preserving edges\n- Hole-filling algorithms (inpainting, nearest-neighbor, linear interpolation)\n- Color mapping for visualization (turbo, plasma, viridis, magma, jet, inferno)\n- Unsharp mask sharpening for edge enhancement\n- Full processing pipeline with configurable operations\n\nAdd DepthProcessorConfig dataclass with validation and comprehensive\nunit tests for all processor functionality.\"",
  "description": "Commit depth processor changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log -1 --stat",
  "description": "Show last commit details"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status --short",
  "description": "Show remaining unstaged changes"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create depth processor module with DepthMapProcessor class and DepthProcessorConfig",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement normalization methods (min-max, percentile, histogram equalization)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement edge-aware filtering (bilateral filter)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement hole-filling algorithms (inpainting, nearest neighbor)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement color mapping for visualization (colormaps)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add comprehensive unit tests for depth processor",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Update depth module __init__.py to expose processor",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Review and improve implemented code",
      "priority": "medium",
      "status": "completed"
    }
  ]
}
<summary>
## Summary: Depth Map Processing and Refinement

### Changes Implemented
- Created `DepthMapProcessor` class with configurable processing pipeline
- Implemented `DepthProcessorConfig` dataclass with validation
- Added normalization methods: min-max, percentile, histogram equalization
- Added edge-aware bilateral filtering for smoothing while preserving edges
- Added hole-filling algorithms: inpainting, nearest-neighbor, linear interpolation
- Added color mapping for visualization with multiple colormaps (turbo, plasma, viridis, magma, jet, inferno, grayscale)
- Added unsharp mask sharpening for edge enhancement
- Created comprehensive unit tests covering all processor functionality
- Exposed processor components in depth module `__init__.py`

### Files Modified
- `src/video2d3d/depth/processor.py` (NEW - 765 lines) - Core processor implementation
- `src/video2d3d/depth/__init__.py` (MODIFIED) - Added processor exports
- `tests/unit/test_depth_processor.py` (NEW - 691 lines) - Unit tests
- `tests/conftest.py` (MODIFIED) - Added cv2 and loguru mocks

### Commit Details
- **Commit Hash**: `c216fa82f25e94be1afda34470e1dede4825c23d`
- **Commit Message**:
  ```
  feat(depth): add depth map post-processor with normalization and filtering
  
  Implement DepthMapProcessor for depth map post-processing including:
  - Normalization methods (min-max, percentile, histogram equalization)
  - Edge-aware bilateral filtering for smoothing while preserving edges
  - Hole-filling algorithms (inpainting, nearest-neighbor, linear interpolation)
  - Color mapping for visualization (turbo, plasma, viridis, magma, jet, inferno)
  - Unsharp mask sharpening for edge enhancement
  - Full processing pipeline with configurable operations
  
  Add DepthProcessorConfig dataclass with validation and comprehensive
  unit tests for all processor functionality.
  ```

### Notes for Developer
- The processor integrates with the existing `DepthEstimator` output
- All operations are configurable via `DepthProcessorConfig`
- Unit tests use mocked cv2/torch/loguru to avoid external dependencies
- The processor supports both float32 depth output and RGB visualization output
- Note: Playwright verification is not applicable for this backend Python module; pytest verification is used instead

### Verification Status
- Unit tests created in `tests/unit/test_depth_processor.py`
- Tests cover: config validation, normalization, bilateral filtering, hole filling, sharpening, color mapping, full pipeline, and error handling
- Tests require cv2/torch mocks set up in `tests/conftest.py`
</summary>

---

## Follow-up Session

I'll verify the testing status for the depth-map-processor feature. Let me run the existing tests and check coverage.

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_depth_processor.py -v --tb=short 2>&1 | head -150",
  "description": "Run depth processor tests",
  "timeout": 120000
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/unit/test_depth_processor.py --collect-only 2>&1 | head -80",
  "description": "List all test cases collected"
}
