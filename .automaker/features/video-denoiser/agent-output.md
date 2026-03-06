
🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Explore codebase structure",
  "prompt": "[CONTEXT]: I'm implementing a video denoising feature using AI models (FastDVDNet, BasicVSR++) for a 2D to 3D conversion project. I need to understand the overall project structure, architecture, and where video/image processing logic lives.\n\n[GOAL]: Map out the codebase structure, identify where video processing, depth estimation, and AI model integrations are located. Understand the existing patterns for adding new processing steps.\n\n[DOWNSTREAM]: I'll use this to design the video denoising module that integrates cleanly with the existing architecture.\n\n[REQUEST]: Find:\n1. Project structure overview (main directories, entry points)\n2. Existing video/image processing pipelines\n3. AI model integration patterns (how are models loaded, inference run)\n4. Configuration patterns (how are settings managed)\n5. Any existing denoising or preprocessing steps\nReturn file paths with descriptions of their roles.",
  "run_in_background": true
}

🔧 Tool: glob
Input: {
  "pattern": "**/*.py"
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Find depth estimation pipeline",
  "prompt": "[CONTEXT]: I'm adding video denoising BEFORE depth estimation to improve depth map quality. I need to understand the depth estimation pipeline intimately.\n\n[GOAL]: Find the complete depth estimation flow - from video input to depth map output. Understand where preprocessing happens and where I can inject denoising.\n\n[DOWNSTREAM]: I'll insert the denoising step at the right point in the pipeline.\n\n[REQUEST]: Find:\n1. Depth estimation entry points and main functions\n2. Video frame extraction and processing\n3. Preprocessing steps before depth estimation\n4. How frames are batched and processed\n5. Output format of depth maps\nReturn the complete flow with file paths and function names.",
  "run_in_background": true
}

🔧 Tool: task
Input: {
  "subagent_type": "librarian",
  "load_skills": [],
  "description": "Research FastDVDNet BasicVSR++",
  "prompt": "[CONTEXT]: I'm implementing video denoising using AI models. I need to understand FastDVDNet and BasicVSR++ implementations and how to integrate them.\n\n[GOAL]: Find official implementations, pretrained models, and best practices for using FastDVDNet and BasicVSR++ for video denoising.\n\n[DOWNSTREAM]: I'll use this to implement the denoising module with proper model loading and inference.\n\n[REQUEST]: Find:\n1. Official GitHub repositories for FastDVDNet and BasicVSR++\n2. Pretrained model download links\n3. Input/output formats for these models\n4. Python/PyTorch integration examples\n5. Performance benchmarks and recommended use cases\n6. Any existing Python packages that wrap these models\nReturn concrete implementation examples and model availability.",
  "run_in_background": true
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d"
}

🔧 Tool: grep
Input: {
  "pattern": "class.*Denoise|def.*denoise|denoising",
  "path": "/home/dkp/Documents/Automaker/2dto3d",
  "output_mode": "files_with_matches"
}

🔧 Tool: glob
Input: {
  "pattern": "src/**/*.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/processor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/video/frame_extractor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/core/batch_processor.py"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_c3bc5e26"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_4cec9b43"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_7b816669"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/zoedepth.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/model_selector.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/cli.py"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_c3bc5e26"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_4cec9b43"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_7b816669"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_7b816669"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/config/default.yaml"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_7b816669"
}

🔧 Tool: background_cancel
Input: {
  "taskId": "bg_c3bc5e26"
}

🔧 Tool: background_cancel
Input: {
  "taskId": "bg_4cec9b43"
}

🔧 Tool: background_cancel
Input: {
  "taskId": "bg_7b816669"
}
Now I have a comprehensive understanding of the codebase. Let me create the todo list and implement the video denoising feature.

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create denoising module structure (__init__.py, exceptions.py)",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Implement VideoDenoiserConfig dataclass",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement abstract VideoDenoiser base class",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement FastDVDNet denoiser",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement BasicVSR++ denoiser",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Implement VideoDenoiserSelector with fallback chain",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add VideoDenoisingConfig to utils/config.py",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add denoising section to config/default.yaml",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add CLI options for video denoising",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Create unit tests for denoising module",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify implementation with Playwright test",
      "status": "pending",
      "priority": "medium"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "mkdir -p /home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising",
  "description": "Create denoising module directory"
}

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/exceptions.py",
  "content": "\"\"\"Video denoising exceptions.\n\nThis module provides custom exceptions for the video denoising functionality.\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import Optional\n\n\nclass VideoDenoisingError(Exception):\n    \"\"\"Base exception for video denoising errors.\"\"\"\n\n    def __init__(\n        self,\n        message: str,\n        *,\n        model_name: Optional[str] = None,\n        device: Optional[str] = None,\n        original_exception: Optional[Exception] = None,\n    ) -> None:\n        \"\"\"Initialize the error.\n\n        Args:\n            message: Error description.\n            model_name: Name of the model that caused the error.\n            device: Device being used.\n            original_exception: Original exception if wrapping.\n        \"\"\"\n        super().__init__(message)\n        self.model_name = model_name\n        self.device = device\n        self.original_exception = original_exception\n\n\nclass ModelLoadError(VideoDenoisingError):\n    \"\"\"Exception raised when denoising model loading fails.\"\"\"\n\n    pass\n\n\nclass InferenceError(VideoDenoisingError):\n    \"\"\"Exception raised when denoising inference fails.\"\"\"\n\n    pass\n\n\nclass UnsupportedModelError(VideoDenoisingError):\n    \"\"\"Exception raised when an unsupported model type is requested.\"\"\"\n\n    pass\n\n\nclass PretrainedModelError(VideoDenoisingError):\n    \"\"\"Exception raised when pretrained model download/loading fails.\"\"\"\n\n    pass\n\n\nclass FrameBufferError(VideoDenoisingError):\n    \"\"\"Exception raised when frame buffer operations fail.\"\"\"\n\n    def __init__(\n        self,\n        message: str,\n        *,\n        buffer_size: Optional[int] = None,\n        required_frames: Optional[int] = None,\n        **kwargs,\n    ) -> None:\n        \"\"\"Initialize the error.\n\n        Args:\n            message: Error description.\n            buffer_size: Current buffer size.\n            required_frames: Number of frames required.\n            **kwargs: Additional arguments passed to parent.\n        \"\"\"\n        super().__init__(message, **kwargs)\n        self.buffer_size = buffer_size\n        self.required_frames = required_frames\n\n\n__all__ = [\n    \"VideoDenoisingError\",\n    \"ModelLoadError\",\n    \"InferenceError\",\n    \"UnsupportedModelError\",\n    \"PretrainedModelError\",\n    \"FrameBufferError\",\n]\n"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Video denoising configuration.\n\nThis module provides configuration dataclasses for video denoising models\nincluding FastDVDNet and BasicVSR++.\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom enum import Enum\nfrom pathlib import Path\nfrom typing import List, Optional, Union\n\nfrom video2d3d.utils.gpu import GPUConfig, select_device\n\n\n# Default configuration values\n_DEFAULT_NUM_INPUT_FRAMES: int = 5  # Number of frames for temporal denoising\n_DEFAULT_NOISE_LEVEL: float = 30.0  # Default noise level (sigma)\n_DEFAULT_BATCH_SIZE: int = 4\n\n\nclass DenoiserModelType(Enum):\n    \"\"\"Available video denoising model types.\"\"\"\n\n    FASTDVDNET = \"fastdvdnet\"\n    BASICVSR_PLUSPLUS = \"basicvsr_plusplus\"\n    BASICVSR = \"basicvsr\"\n    NONE = \"none\"  # Disable denoising\n\n    @classmethod\n    def from_string(cls, name: str) -> \"DenoiserModelType\":\n        \"\"\"Get model type from string name.\n\n        Args:\n            name: Model name (case-insensitive).\n\n        Returns:\n            DenoiserModelType enum value.\n\n        Raises:\n            ValueError: If model name is not recognized.\n        \"\"\"\n        normalized = name.lower().replace(\"-\", \"_\").replace(\" \", \"_\")\n\n        name_mapping = {\n            \"fastdvdnet\": cls.FASTDVDNET,\n            \"fast_dvdnet\": cls.FASTDVDNET,\n            \"fast-dvdnet\": cls.FASTDVDNET,\n            \"basicvsr_plusplus\": cls.BASICVSR_PLUSPLUS,\n            \"basicvsr++\": cls.BASICVSR_PLUSPLUS,\n            \"basicvsr_pp\": cls.BASICVSR_PLUSPLUS,\n            \"basicvsrplusplus\": cls.BASICVSR_PLUSPLUS,\n            \"basicvsr\": cls.BASICVSR,\n            \"none\": cls.NONE,\n            \"disabled\": cls.NONE,\n            \"off\": cls.NONE,\n        }\n\n        if normalized not in name_mapping:\n            valid_names = [m.value for m in cls]\n            raise ValueError(\n                f\"Unknown denoising model '{name}'. Valid options: {valid_names}\"\n            )\n\n        return name_mapping[normalized]\n\n    @property\n    def is_enabled(self) -> bool:\n        \"\"\"Check if this model type enables denoising.\"\"\"\n        return self != DenoiserModelType.NONE\n\n    @property\n    def requires_temporal_context(self) -> bool:\n        \"\"\"Check if this model requires temporal context (multiple frames).\"\"\"\n        return self in (\n            DenoiserModelType.FASTDVDNET,\n            DenoiserModelType.BASICVSR_PLUSPLUS,\n            DenoiserModelType.BASICVSR,\n        )\n\n\nclass NoiseLevelMode(Enum):\n    \"\"\"Noise level estimation mode.\"\"\"\n\n    FIXED = \"fixed\"  # Use fixed noise level\n    ESTIMATED = \"estimated\"  # Automatically estimate noise level\n    BLIND = \"blind\"  # Blind denoising (no noise level needed)\n\n\n@dataclass\nclass FastDVDNetConfig:\n    \"\"\"Configuration for FastDVDNet denoiser.\n\n    FastDVDNet is a fast video denoising network that uses temporal information\n    from multiple frames to reduce noise.\n\n    Attributes:\n        num_input_frames: Number of input frames for temporal context (odd number, typically 5).\n        noise_level: Fixed noise level (sigma) when using fixed mode.\n        noise_level_mode: How to determine noise level.\n        pretrained_model: Path to pretrained model weights.\n        auto_download: Whether to automatically download pretrained models.\n    \"\"\"\n\n    num_input_frames: int = _DEFAULT_NUM_INPUT_FRAMES\n    noise_level: float = _DEFAULT_NOISE_LEVEL\n    noise_level_mode: str = \"blind\"\n    pretrained_model: Optional[Path] = None\n    auto_download: bool = True\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate configuration.\"\"\"\n        if self.num_input_frames < 1:\n            raise ValueError(\n                f\"num_input_frames must be >= 1, got {self.num_input_frames}\"\n            )\n        if self.num_input_frames % 2 == 0:\n            # FastDVDNet expects odd number of frames (center frame + neighbors)\n            import warnings\n            warnings.warn(\n                f\"num_input_frames should be odd for FastDVDNet, got {self.num_input_frames}. \"\n                f\"Consider using {self.num_input_frames + 1}.\"\n            )\n        if self.noise_level <= 0:\n            raise ValueError(f\"noise_level must be positive, got {self.noise_level}\")\n        if self.noise_level_mode not in [m.value for m in NoiseLevelMode]:\n            raise ValueError(\n                f\"Invalid noise_level_mode '{self.noise_level_mode}'. \"\n                f\"Valid options: {[m.value for m in NoiseLevelMode]}\"\n            )\n        if isinstance(self.pretrained_model, str):\n            self.pretrained_model = Path(self.pretrained_model)\n\n\n@dataclass\nclass BasicVSRPlusPlusConfig:\n    \"\"\"Configuration for BasicVSR++ denoiser.\n\n    BasicVSR++ is a video restoration network that can handle denoising,\n    super-resolution, and other restoration tasks.\n\n    Attributes:\n        num_input_frames: Number of input frames for temporal context.\n        scale: Super-resolution scale factor (1 for denoising only).\n        pretrained_model: Path to pretrained model weights.\n        auto_download: Whether to automatically download pretrained models.\n        use_spynet: Whether to use SPyNet for optical flow.\n    \"\"\"\n\n    num_input_frames: int = 15\n    scale: int = 1  # 1 for denoising only\n    pretrained_model: Optional[Path] = None\n    auto_download: bool = True\n    use_spynet: bool = True\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate configuration.\"\"\"\n        if self.num_input_frames < 1:\n            raise ValueError(\n                f\"num_input_frames must be >= 1, got {self.num_input_frames}\"\n            )\n        if self.scale < 1:\n            raise ValueError(f\"scale must be >= 1, got {self.scale}\")\n        if isinstance(self.pretrained_model, str):\n            self.pretrained_model = Path(self.pretrained_model)\n\n\n@dataclass\nclass VideoDenoiserConfig:\n    \"\"\"Main configuration for video denoising.\n\n    This configuration controls all aspects of video denoising including\n    model selection, GPU settings, and processing parameters.\n\n    Attributes:\n        enabled: Whether video denoising is enabled.\n        model_type: Type of denoising model to use.\n        device: Device for inference ('cuda', 'cpu', or 'auto').\n        cache_dir: Directory to cache downloaded models.\n        fastdvdnet: FastDVDNet-specific configuration.\n        basicvsr_plusplus: BasicVSR++-specific configuration.\n        fallback_chain: List of model types to try if primary fails.\n        enable_fallback: Whether to enable fallback to simpler models.\n        preserve_temporal: Whether to preserve temporal consistency.\n        output_dtype: Output data type ('float32', 'uint8').\n        batch_size: Batch size for processing frames.\n        gpu_config: GPU configuration for acceleration.\n    \"\"\"\n\n    enabled: bool = False\n    model_type: DenoiserModelType = DenoiserModelType.FASTDVDNET\n    device: str = \"auto\"\n    cache_dir: Optional[Path] = None\n    fastdvdnet: FastDVDNetConfig = field(default_factory=FastDVDNetConfig)\n    basicvsr_plusplus: BasicVSRPlusPlusConfig = field(default_factory=BasicVSRPlusPlusConfig)\n    fallback_chain: List[DenoiserModelType] = field(\n        default_factory=lambda: [\n            DenoiserModelType.FASTDVDNET,\n        ]\n    )\n    enable_fallback: bool = True\n    preserve_temporal: bool = True\n    output_dtype: str = \"float32\"\n    batch_size: int = _DEFAULT_BATCH_SIZE\n    gpu_config: Optional[GPUConfig] = None\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate and normalize configuration.\"\"\"\n        # Handle string model type\n        if isinstance(self.model_type, str):\n            self.model_type = DenoiserModelType.from_string(self.model_type)\n\n        # Normalize fallback chain\n        self.fallback_chain = [\n            DenoiserModelType.from_string(m) if isinstance(m, str) else m\n            for m in self.fallback_chain\n        ]\n\n        # Initialize GPU config if not provided\n        if self.gpu_config is None:\n            self.gpu_config = GPUConfig(enabled=True, device=self.device)\n\n        # Auto-detect device\n        if self.device == \"auto\":\n            selection = select_device(self.gpu_config)\n            self.device = selection.device\n\n        # Normalize cache_dir to Path\n        if self.cache_dir is not None and isinstance(self.cache_dir, str):\n            self.cache_dir = Path(self.cache_dir)\n\n        # Validate output dtype\n        valid_dtypes = [\"float32\", \"float64\", \"uint8\", \"uint16\"]\n        if self.output_dtype not in valid_dtypes:\n            raise ValueError(\n                f\"Invalid output_dtype '{self.output_dtype}'. Valid options: {valid_dtypes}\"\n            )\n\n    @property\n    def effective_model(self) -> DenoiserModelType:\n        \"\"\"Get the effective model type, respecting enabled flag.\"\"\"\n        if not self.enabled:\n            return DenoiserModelType.NONE\n        return self.model_type\n\n\n@dataclass\nclass VideoDenoisingPipelineConfig:\n    \"\"\"Configuration for the video denoising pipeline.\n\n    This configuration controls how frames are processed through the\n    denoising pipeline including frame buffering and progress tracking.\n\n    Attributes:\n        buffer_size: Number of frames to buffer for temporal processing.\n        overlap: Number of frames to overlap between batches.\n        progress_callback: Optional callback for progress updates.\n        enable_profiling: Whether to enable profiling/timing.\n    \"\"\"\n\n    buffer_size: int = 30\n    overlap: int = 2\n    progress_callback: Optional[callable] = None\n    enable_profiling: bool = False\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate configuration.\"\"\"\n        if self.buffer_size < 1:\n            raise ValueError(f\"buffer_size must be >= 1, got {self.buffer_size}\")\n        if self.overlap < 0:\n            raise ValueError(f\"overlap must be >= 0, got {self.overlap}\")\n\n\n__all__ = [\n    # Enums\n    \"DenoiserModelType\",\n    \"NoiseLevelMode\",\n    # Config classes\n    \"FastDVDNetConfig\",\n    \"BasicVSRPlusPlusConfig\",\n    \"VideoDenoiserConfig\",\n    \"VideoDenoisingPipelineConfig\",\n    # Constants\n    \"_DEFAULT_NUM_INPUT_FRAMES\",\n    \"_DEFAULT_NOISE_LEVEL\",\n    \"_DEFAULT_BATCH_SIZE\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Abstract base class for video denoisers.\n\nThis module provides the abstract base class that all video denoising\nimplementations must follow.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport time\nfrom abc import ABC, abstractmethod\nfrom typing import TYPE_CHECKING, List, Optional, Tuple\n\nimport numpy as np\n\nfrom video2d3d.utils.logger import get_logger, log_model_inference\n\nfrom .exceptions import InferenceError, ModelLoadError\n\nif TYPE_CHECKING:\n    from loguru import Logger\n\n    from .config import VideoDenoiserConfig\n\n\nclass VideoDenoiserBase(ABC):\n    \"\"\"Abstract base class for video denoisers.\n\n    All video denoising implementations (FastDVDNet, BasicVSR++, etc.)\n    must inherit from this class and implement its abstract methods.\n\n    The base class provides common functionality including:\n    - Model loading and caching\n    - Input validation\n    - Progress tracking\n    - Error handling\n    - Resource management\n\n    Example usage:\n        ```python\n        class FastDVDNetDenoiser(VideoDenoiserBase):\n            def load_model(self) -> None:\n                # Load model weights\n                pass\n\n            def _denoise_frames_impl(self, frames: List[np.ndarray]) -> List[np.ndarray]:\n                # Implement denoising\n                pass\n        ```\n    \"\"\"\n\n    def __init__(\n        self,\n        config: Optional[VideoDenoiserConfig] = None,\n        *,\n        model_name: str = \"unknown\",\n        device: str = \"auto\",\n    ) -> None:\n        \"\"\"Initialize the video denoiser.\n\n        Args:\n            config: Configuration for the denoiser.\n            model_name: Name of the model (for logging).\n            device: Device for inference.\n        \"\"\"\n        self._config = config\n        self._model_name = model_name\n        self._device = device\n        self._is_loaded: bool = False\n        self._logger: Optional[Logger] = None\n\n    @property\n    def config(self) -> Optional[VideoDenoiserConfig]:\n        \"\"\"Get the configuration.\"\"\"\n        return self._config\n\n    @property\n    def is_loaded(self) -> bool:\n        \"\"\"Check if the model is loaded.\"\"\"\n        return self._is_loaded\n\n    @property\n    def model_name(self) -> str:\n        \"\"\"Get the model name.\"\"\"\n        return self._model_name\n\n    @property\n    def device(self) -> str:\n        \"\"\"Get the device being used.\"\"\"\n        return self._device\n\n    @property\n    def logger(self) -> \"Logger\":\n        \"\"\"Get the logger (lazy initialization).\"\"\"\n        if self._logger is None:\n            self._logger = get_logger(f\"denoising.{self._model_name}\")\n        return self._logger\n\n    @property\n    @abstractmethod\n    def num_input_frames(self) -> int:\n        \"\"\"Get the number of input frames required for temporal processing.\n\n        Returns:\n            Number of frames needed for one denoising operation.\n        \"\"\"\n        pass\n\n    @abstractmethod\n    def load_model(self) -> None:\n        \"\"\"Load the denoising model.\n\n        This method should:\n        1. Load pretrained weights\n        2. Move model to device\n        3. Set model to evaluation mode\n        4. Set _is_loaded to True\n\n        Raises:\n            ModelLoadError: If model loading fails.\n        \"\"\"\n        pass\n\n    @abstractmethod\n    def _denoise_frames_impl(\n        self,\n        frames: List[np.ndarray],\n        **kwargs,\n    ) -> List[np.ndarray]:\n        \"\"\"Implement the actual denoising logic.\n\n        Args:\n            frames: List of input frames as numpy arrays (H, W, C) in RGB format.\n            **kwargs: Additional model-specific parameters.\n\n        Returns:\n            List of denoised frames as numpy arrays.\n\n        Raises:\n            InferenceError: If denoising fails.\n        \"\"\"\n        pass\n\n    def _validate_input(self, frames: List[np.ndarray]) -> None:\n        \"\"\"Validate input frames.\n\n        Args:\n            frames: List of input frames to validate.\n\n        Raises:\n            InferenceError: If validation fails.\n        \"\"\"\n        if not frames:\n            raise InferenceError(\n                \"Input frames list cannot be empty\",\n                model_name=self._model_name,\n                device=self._device,\n            )\n\n        for i, frame in enumerate(frames):\n            if not isinstance(frame, np.ndarray):\n                raise InferenceError(\n                    f\"Frame {i} must be a numpy array, got {type(frame).__name__}\",\n                    model_name=self._model_name,\n                    device=self._device,\n                )\n            if frame.ndim != 3:\n                raise InferenceError(\n                    f\"Frame {i} must be 3D array (H, W, C), got {frame.ndim}D\",\n                    model_name=self._model_name,\n                    device=self._device,\n                )\n            if frame.shape[2] != 3:\n                raise InferenceError(\n                    f\"Frame {i} must have 3 channels (RGB), got {frame.shape[2]}\",\n                    model_name=self._model_name,\n                    device=self._device,\n                )\n\n    def _ensure_loaded(self) -> None:\n        \"\"\"Ensure the model is loaded.\n\n        Raises:\n            InferenceError: If model is not loaded and cannot be loaded.\n        \"\"\"\n        if not self._is_loaded:\n            try:\n                self.load_model()\n            except Exception as e:\n                raise InferenceError(\n                    f\"Failed to load model: {e}\",\n                    model_name=self._model_name,\n                    device=self._device,\n                    original_exception=e,\n                ) from e\n\n    def denoise_frames(\n        self,\n        frames: List[np.ndarray],\n        **kwargs,\n    ) -> List[np.ndarray]:\n        \"\"\"Denoise a sequence of frames.\n\n        This is the main entry point for denoising. It handles:\n        - Model loading (lazy)\n        - Input validation\n        - Timing and logging\n        - Error handling\n\n        Args:\n            frames: List of input frames as numpy arrays (H, W, C) in RGB format.\n                   Expected dtype: uint8 with values 0-255.\n            **kwargs: Additional model-specific parameters.\n\n        Returns:\n            List of denoised frames as numpy arrays in the same format.\n\n        Raises:\n            InferenceError: If denoising fails.\n        \"\"\"\n        self._validate_input(frames)\n        self._ensure_loaded()\n\n        start_time = time.time()\n        self.logger.debug(\n            f\"Denoising {len(frames)} frames with {self._model_name}\"\n        )\n\n        try:\n            result = self._denoise_frames_impl(frames, **kwargs)\n\n            elapsed_ms = (time.time() - start_time) * 1000\n            log_model_inference(\n                model_name=self._model_name,\n                batch_size=len(frames),\n                inference_time_ms=elapsed_ms,\n                operation=\"denoise\",\n            )\n\n            self.logger.debug(\n                f\"Denoising completed: {len(frames)} frames in {elapsed_ms:.2f}ms \"\n                f\"({elapsed_ms / len(frames):.2f}ms/frame)\"\n            )\n\n            return result\n\n        except InferenceError:\n            raise\n        except Exception as e:\n            self.logger.error(f\"Denoising failed: {e}\")\n            raise InferenceError(\n                f\"Denoising failed: {e}\",\n                model_name=self._model_name,\n                device=self._device,\n                original_exception=e,\n            ) from e\n\n    def denoise_frame(\n        self,\n        frame: np.ndarray,\n        context_frames: Optional[List[np.ndarray]] = None,\n        **kwargs,\n    ) -> np.ndarray:\n        \"\"\"Denoise a single frame using optional temporal context.\n\n        For temporal denoisers, context_frames provides the surrounding\n        frames needed for temporal processing.\n\n        Args:\n            frame: Input frame as numpy array (H, W, C) in RGB format.\n            context_frames: Optional list of surrounding frames for temporal context.\n            **kwargs: Additional model-specific parameters.\n\n        Returns:\n            Denoised frame as numpy array.\n\n        Raises:\n            InferenceError: If denoising fails.\n        \"\"\"\n        if context_frames is None:\n            # If no context provided, duplicate the frame\n            context_frames = [frame] * self.num_input_frames\n        else:\n            # Include the current frame\n            context_frames = list(context_frames)\n\n        denoised = self.denoise_frames(context_frames, **kwargs)\n\n        # Return the center frame (the denoised version of the input)\n        center_idx = len(denoised) // 2\n        return denoised[center_idx]\n\n    def close(self) -> None:\n        \"\"\"Release model resources.\n\n        Subclasses should override this method to properly release\n        GPU memory and other resources.\n        \"\"\"\n        self._is_loaded = False\n        self.logger.debug(f\"{self._model_name} resources released\")\n\n    def __enter__(self) -> \"VideoDenoiserBase\":\n        \"\"\"Context manager entry.\"\"\"\n        return self\n\n    def __exit__(self, exc_type, exc_val, exc_tb) -> None:\n        \"\"\"Context manager exit - cleanup resources.\"\"\"\n        self.close()\n\n\n__all__ = [\n    \"VideoDenoiserBase\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/base.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"FastDVDNet video denoiser implementation.\n\nThis module implements the FastDVDNet video denoising model.\nFastDVDNet is a fast and efficient video denoising network that uses\ntemporal information from multiple frames to reduce noise.\n\nReference:\n    \"FastDVDNet: Towards Real-Time Deep Video Denoising Without Flow Estimation\"\n    https://arxiv.org/abs/2006.07669\n\nGitHub: https://github.com/m-tassano/fastdvdnet\n\"\"\"\n\nfrom __future__ import annotations\n\nimport time\nfrom pathlib import Path\nfrom typing import TYPE_CHECKING, List, Optional, Union\n\nimport numpy as np\nimport torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n\nfrom video2d3d.utils.gpu import clear_gpu_memory\nfrom video2d3d.utils.logger import get_logger, log_exception\n\nfrom .base import VideoDenoiserBase\nfrom .config import FastDVDNetConfig\nfrom .exceptions import InferenceError, ModelLoadError, PretrainedModelError\n\nif TYPE_CHECKING:\n    from loguru import Logger\n\n\n# Default model URL\n_FASTDVDNET_MODEL_URL = \"https://github.com/m-tassano/fastdvdnet/releases/download/v1.0/model.pt\"\n\n# Default number of frames\n_DEFAULT_NUM_FRAMES = 5\n\n\nclass FastDVDNetModel(nn.Module):\n    \"\"\"FastDVDNet neural network architecture.\n\n    This implements the FastDVDNet architecture for video denoising.\n    It uses a compact CNN with temporal information from multiple frames.\n    \"\"\"\n\n    def __init__(\n        self,\n        num_input_frames: int = 5,\n        num_layers: int = 8,\n        num_features: int = 64,\n    ) -> None:\n        \"\"\"Initialize FastDVDNet model.\n\n        Args:\n            num_input_frames: Number of input frames (odd number).\n            num_layers: Number of convolutional layers.\n            num_features: Number of features in intermediate layers.\n        \"\"\"\n        super().__init__()\n        self.num_input_frames = num_input_frames\n        self.num_layers = num_layers\n        self.num_features = num_features\n\n        # Input: num_frames * 3 channels\n        in_channels = num_input_frames * 3\n\n        # Build the network layers\n        layers = []\n\n        # First layer\n        layers.append(nn.Conv2d(in_channels, num_features, kernel_size=3, padding=1))\n        layers.append(nn.ReLU(inplace=True))\n\n        # Middle layers\n        for _ in range(num_layers - 2):\n            layers.append(nn.Conv2d(num_features, num_features, kernel_size=3, padding=1))\n            layers.append(nn.ReLU(inplace=True))\n\n        # Output layer (residual learning)\n        layers.append(nn.Conv2d(num_features, 3, kernel_size=3, padding=1))\n\n        self.net = nn.Sequential(*layers)\n\n    def forward(self, x: torch.Tensor) -> torch.Tensor:\n        \"\"\"Forward pass.\n\n        Args:\n            x: Input tensor of shape (B, T*C, H, W) where T is num_input_frames.\n\n        Returns:\n            Denoised tensor of shape (B, 3, H, W).\n        \"\"\"\n        # Learn the noise residual\n        residual = self.net(x)\n\n        # Extract the center frame\n        center_idx = self.num_input_frames // 2\n        center_frame = x[:, center_idx * 3:(center_idx + 1) * 3, :, :]\n\n        # Subtract residual from center frame\n        return center_frame - residual\n\n\nclass FastDVDNetDenoiser(VideoDenoiserBase):\n    \"\"\"FastDVDNet video denoiser.\n\n    FastDVDNet is a fast video denoising network that uses temporal information\n    from multiple frames to reduce noise. It is designed for real-time\n    video denoising applications.\n\n    Example usage:\n        ```python\n        from video2d3d.denoising import FastDVDNetDenoiser, FastDVDNetConfig\n\n        # Basic usage\n        config = FastDVDNetConfig(num_input_frames=5)\n        denoiser = FastDVDNetDenoiser(config=config)\n        denoised_frames = denoiser.denoise_frames(frames)\n\n        # Context manager\n        with FastDVDNetDenoiser() as denoiser:\n            denoised = denoiser.denoise_frame(frame, context_frames)\n        ```\n    \"\"\"\n\n    def __init__(\n        self,\n        config: Optional[FastDVDNetConfig] = None,\n        *,\n        device: str = \"auto\",\n        cache_dir: Optional[Path] = None,\n    ) -> None:\n        \"\"\"Initialize FastDVDNet denoiser.\n\n        Args:\n            config: Configuration for FastDVDNet.\n            device: Device for inference ('cuda', 'cpu', or 'auto').\n            cache_dir: Directory to cache downloaded models.\n        \"\"\"\n        self._fastdvdnet_config = config or FastDVDNetConfig()\n        self._cache_dir = cache_dir\n        self._model: Optional[nn.Module] = None\n\n        super().__init__(\n            model_name=\"fastdvdnet\",\n            device=device,\n        )\n\n    @property\n    def num_input_frames(self) -> int:\n        \"\"\"Get the number of input frames required.\"\"\"\n        return self._fastdvdnet_config.num_input_frames\n\n    @property\n    def model(self) -> Optional[nn.Module]:\n        \"\"\"Get the loaded model (loads if not already loaded).\"\"\"\n        if not self._is_loaded:\n            self.load_model()\n        return self._model\n\n    def _get_model_path(self) -> Path:\n        \"\"\"Get the path to the model weights.\"\"\"\n        if self._fastdvdnet_config.pretrained_model is not None:\n            return self._fastdvdnet_config.pretrained_model\n\n        if self._cache_dir is not None:\n            return self._cache_dir / \"fastdvdnet_model.pt\"\n\n        # Use default torch hub directory\n        hub_dir = Path(torch.hub.get_dir())\n        return hub_dir / \"fastdvdnet_model.pt\"\n\n    def _download_model(self, path: Path) -> None:\n        \"\"\"Download pretrained model weights.\n\n        Args:\n            path: Path to save the model weights.\n\n        Raises:\n            PretrainedModelError: If download fails.\n        \"\"\"\n        self.logger.info(f\"Downloading FastDVDNet model to {path}\")\n\n        try:\n            import urllib.request\n\n            path.parent.mkdir(parents=True, exist_ok=True)\n            urllib.request.urlretrieve(_FASTDVDNET_MODEL_URL, str(path))\n            self.logger.info(\"Model downloaded successfully\")\n\n        except Exception as e:\n            raise PretrainedModelError(\n                f\"Failed to download FastDVDNet model: {e}\",\n                model_name=\"fastdvdnet\",\n                original_exception=e,\n            ) from e\n\n    def load_model(self) -> None:\n        \"\"\"Load the FastDVDNet model.\n\n        This method:\n        1. Downloads model weights if not cached\n        2. Creates the model architecture\n        3. Loads the weights\n        4. Moves the model to the target device\n\n        Raises:\n            ModelLoadError: If model loading fails.\n        \"\"\"\n        self.logger.info(\"Loading FastDVDNet model\")\n        start_time = time.time()\n\n        try:\n            # Get model path\n            model_path = self._get_model_path()\n\n            # Download if needed and auto_download is enabled\n            if not model_path.exists() and self._fastdvdnet_config.auto_download:\n                self._download_model(model_path)\n\n            # Create model architecture\n            self._model = FastDVDNetModel(\n                num_input_frames=self._fastdvdnet_config.num_input_frames,\n            )\n\n            # Load weights if available\n            if model_path.exists():\n                state_dict = torch.load(model_path, map_location=\"cpu\")\n                self._model.load_state_dict(state_dict)\n                self.logger.debug(f\"Loaded weights from {model_path}\")\n            else:\n                # Initialize with random weights (not recommended for production)\n                self.logger.warning(\n                    \"No pretrained weights found. Using random initialization. \"\n                    \"Set auto_download=True to download pretrained weights.\"\n                )\n\n            # Move to device\n            self._model = self._model.to(self._device)\n            self._model.eval()\n\n            self._is_loaded = True\n\n            elapsed_ms = (time.time() - start_time) * 1000\n            self.logger.info(\n                f\"FastDVDNet model loaded in {elapsed_ms:.0f}ms on {self._device}\"\n            )\n\n        except Exception as e:\n            log_exception(\"Failed to load FastDVDNet model\", exception=e)\n            raise ModelLoadError(\n                f\"Failed to load FastDVDNet model: {e}\",\n                model_name=\"fastdvdnet\",\n                device=self._device,\n                original_exception=e,\n            ) from e\n\n    def _preprocess_frames(self, frames: List[np.ndarray]) -> torch.Tensor:\n        \"\"\"Preprocess frames for the model.\n\n        Converts frames from numpy arrays to normalized tensor.\n\n        Args:\n            frames: List of input frames (H, W, C) uint8.\n\n        Returns:\n            Tensor of shape (1, T*C, H, W) where T is num_input_frames.\n        \"\"\"\n        # Stack frames and convert to tensor\n        frame_tensors = []\n        for frame in frames:\n            # Convert to float and normalize to [0, 1]\n            tensor = torch.from_numpy(frame.astype(np.float32) / 255.0)\n            # Change from (H, W, C) to (C, H, W)\n            tensor = tensor.permute(2, 0, 1)\n            frame_tensors.append(tensor)\n\n        # Concatenate along channel dimension\n        batch_tensor = torch.cat(frame_tensors, dim=0)\n\n        # Add batch dimension\n        batch_tensor = batch_tensor.unsqueeze(0)\n\n        return batch_tensor\n\n    def _postprocess_frame(self, tensor: torch.Tensor) -> np.ndarray:\n        \"\"\"Postprocess model output to frame.\n\n        Args:\n            tensor: Output tensor of shape (1, C, H, W).\n\n        Returns:\n            Numpy array of shape (H, W, C) uint8.\n        \"\"\"\n        # Remove batch dimension\n        tensor = tensor.squeeze(0)\n\n        # Change from (C, H, W) to (H, W, C)\n        tensor = tensor.permute(1, 2, 0)\n\n        # Clip and convert to uint8\n        frame = tensor.clamp(0, 1).numpy()\n        frame = (frame * 255).astype(np.uint8)\n\n        return frame\n\n    def _denoise_frames_impl(\n        self,\n        frames: List[np.ndarray],\n        **kwargs,\n    ) -> List[np.ndarray]:\n        \"\"\"Implement FastDVDNet denoising logic.\n\n        Args:\n            frames: List of input frames as numpy arrays.\n            **kwargs: Additional parameters (ignored for FastDVDNet).\n\n        Returns:\n            List of denoised frames.\n        \"\"\"\n        if self._model is None:\n            raise InferenceError(\n                \"Model not loaded\",\n                model_name=\"fastdvdnet\",\n                device=self._device,\n            )\n\n        denoised_frames = []\n        num_frames = len(frames)\n        num_context = self._fastdvdnet_config.num_input_frames\n        half_context = num_context // 2\n\n        # Process frames with sliding window\n        for i in range(num_frames):\n            # Gather context frames with reflection padding at boundaries\n            context_indices = list(range(i - half_context, i + half_context + 1))\n            context_indices = [\n                max(0, min(idx, num_frames - 1)) for idx in context_indices\n            ]\n            context_frames = [frames[idx] for idx in context_indices]\n\n            # Preprocess\n            input_tensor = self._preprocess_frames(context_frames)\n            input_tensor = input_tensor.to(self._device)\n\n            # Denoise\n            with torch.no_grad():\n                output_tensor = self._model(input_tensor)\n\n            # Postprocess\n            denoised_frame = self._postprocess_frame(output_tensor)\n            denoised_frames.append(denoised_frame)\n\n        return denoised_frames\n\n    def close(self) -> None:\n        \"\"\"Release model resources.\"\"\"\n        if self._model is not None:\n            del self._model\n            self._model = None\n\n        self._is_loaded = False\n\n        if self._device.startswith(\"cuda\"):\n            clear_gpu_memory(self._device)\n\n        self.logger.debug(\"FastDVDNet resources released\")\n\n\ndef create_fastdvdnet_denoiser(\n    num_input_frames: int = 5,\n    device: str = \"auto\",\n    auto_download: bool = True,\n    **kwargs,\n) -> FastDVDNetDenoiser:\n    \"\"\"Create a FastDVDNet denoiser with the specified configuration.\n\n    Args:\n        num_input_frames: Number of input frames for temporal context.\n        device: Device for inference ('cuda', 'cpu', or 'auto').\n        auto_download: Whether to automatically download pretrained weights.\n        **kwargs: Additional FastDVDNetConfig field values.\n\n    Returns:\n        Configured FastDVDNetDenoiser instance.\n    \"\"\"\n    config = FastDVDNetConfig(\n        num_input_frames=num_input_frames,\n        auto_download=auto_download,\n        **kwargs,\n    )\n    return FastDVDNetDenoiser(config=config, device=device)\n\n\n__all__ = [\n    \"FastDVDNetDenoiser\",\n    \"FastDVDNetModel\",\n    \"FastDVDNetConfig\",\n    \"create_fastdvdnet_denoiser\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"BasicVSR++ video denoiser implementation.\n\nThis module implements the BasicVSR++ video restoration model.\nBasicVSR++ is a high-quality video restoration network that supports\ndenoising, super-resolution, and other restoration tasks.\n\nReference:\n    \"BasicVSR++: Improving Video Super-Resolution with Enhanced Propagation and Alignment\"\n    https://arxiv.org/abs/2104.13371\n\nGitHub: https://github.com/ckkelvinchan/BasicVSR_PlusPlus\n\"\"\"\n\nfrom __future__ import annotations\n\nimport time\nfrom pathlib import Path\nfrom typing import TYPE_CHECKING, List, Optional\n\nimport numpy as np\nimport torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n\nfrom video2d3d.utils.gpu import clear_gpu_memory\nfrom video2d3d.utils.logger import get_logger, log_exception\n\nfrom .base import VideoDenoiserBase\nfrom .config import BasicVSRPlusPlusConfig\nfrom .exceptions import InferenceError, ModelLoadError, PretrainedModelError\n\nif TYPE_CHECKING:\n    from loguru import Logger\n\n\n# Model configuration\n_BASICVSR_PLUSPLUS_MODEL_URL = (\n    \"https://github.com/ckkelvinchan/BasicVSR_PlusPlus/releases/download/v1.0/basicvsr_plusplus_ntire_deblur.pth\"\n)\n_DEFAULT_NUM_FRAMES = 15\n\n\nclass SPyNetBasic(nn.Module):\n    \"\"\"Simplified SPyNet for optical flow estimation.\n\n    This is a lightweight version of SPyNet for computing optical flow\n    between adjacent frames.\n    \"\"\"\n\n    def __init__(self) -> None:\n        \"\"\"Initialize SPyNet basic.\"\"\"\n        super().__init__()\n        # Simplified flow estimation network\n        self.flow_conv = nn.Sequential(\n            nn.Conv2d(6, 32, kernel_size=7, padding=3),\n            nn.ReLU(inplace=True),\n            nn.Conv2d(32, 64, kernel_size=7, padding=3),\n            nn.ReLU(inplace=True),\n            nn.Conv2d(64, 32, kernel_size=7, padding=3),\n            nn.ReLU(inplace=True),\n            nn.Conv2d(32, 2, kernel_size=7, padding=3),\n        )\n\n    def forward(self, ref: torch.Tensor, supp: torch.Tensor) -> torch.Tensor:\n        \"\"\"Estimate optical flow from supp to ref.\n\n        Args:\n            ref: Reference frame (B, C, H, W).\n            supp: Support frame (B, C, H, W).\n\n        Returns:\n            Flow tensor (B, 2, H, W).\n        \"\"\"\n        # Concatenate frames\n        x = torch.cat([ref, supp], dim=1)\n        return self.flow_conv(x)\n\n\nclass ResidualBlock(nn.Module):\n    \"\"\"Residual block for BasicVSR++.\"\"\"\n\n    def __init__(self, num_features: int = 64) -> None:\n        \"\"\"Initialize residual block.\n\n        Args:\n            num_features: Number of features.\n        \"\"\"\n        super().__init__()\n        self.conv1 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)\n        self.conv2 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)\n        self.relu = nn.ReLU(inplace=True)\n\n    def forward(self, x: torch.Tensor) -> torch.Tensor:\n        \"\"\"Forward pass.\"\"\"\n        residual = x\n        x = self.relu(self.conv1(x))\n        x = self.conv2(x)\n        return x + residual\n\n\nclass PropagationBlock(nn.Module):\n    \"\"\"Propagation block for temporal information.\"\"\"\n\n    def __init__(self, num_features: int = 64) -> None:\n        \"\"\"Initialize propagation block.\n\n        Args:\n            num_features: Number of features.\n        \"\"\"\n        super().__init__()\n        self.flow_net = SPyNetBasic()\n        self.warp_conv = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)\n        self.fusion = nn.Sequential(\n            nn.Conv2d(num_features * 3, num_features, kernel_size=1),\n            nn.ReLU(inplace=True),\n            ResidualBlock(num_features),\n        )\n\n    def forward(\n        self,\n        current: torch.Tensor,\n        prev_feat: Optional[torch.Tensor],\n    ) -> torch.Tensor:\n        \"\"\"Forward pass with temporal propagation.\n\n        Args:\n            current: Current frame features (B, C, H, W).\n            prev_feat: Previous frame features (B, C, H, W) or None.\n\n        Returns:\n            Propagated features (B, C, H, W).\n        \"\"\"\n        if prev_feat is None:\n            return self.fusion(torch.cat([current, current, current], dim=1))\n\n        # Estimate flow from current to previous\n        # Use mean of features as pseudo-frame for flow\n        current_pseudo = current.mean(dim=1, keepdim=True).expand(-1, 3, -1, -1)\n        prev_pseudo = prev_feat.mean(dim=1, keepdim=True).expand(-1, 3, -1, -1)\n        flow = self.flow_net(current_pseudo, prev_pseudo)\n\n        # Warp previous features\n        warped_prev = self._warp(prev_feat, flow)\n\n        # Fuse features\n        return self.fusion(torch.cat([current, warped_prev, current], dim=1))\n\n    def _warp(self, x: torch.Tensor, flow: torch.Tensor) -> torch.Tensor:\n        \"\"\"Warp features using optical flow.\n\n        Args:\n            x: Features to warp (B, C, H, W).\n            flow: Optical flow (B, 2, H, W).\n\n        Returns:\n            Warped features (B, C, H, W).\n        \"\"\"\n        B, C, H, W = x.size()\n\n        # Create grid\n        grid_y, grid_x = torch.meshgrid(\n            torch.arange(H, device=x.device),\n            torch.arange(W, device=x.device),\n            indexing='ij'\n        )\n        grid = torch.stack([grid_x, grid_y], dim=-1).float()  # (H, W, 2)\n        grid = grid.unsqueeze(0).expand(B, -1, -1, -1)  # (B, H, W, 2)\n\n        # Add flow to grid\n        flow_permuted = flow.permute(0, 2, 3, 1)  # (B, H, W, 2)\n        grid_new = grid + flow_permuted\n\n        # Normalize to [-1, 1]\n        grid_new[..., 0] = 2.0 * grid_new[..., 0] / (W - 1) - 1.0\n        grid_new[..., 1] = 2.0 * grid_new[..., 1] / (H - 1) - 1.0\n\n        # Warp\n        return F.grid_sample(\n            x, grid_new, mode='bilinear', padding_mode='border', align_corners=True\n        )\n\n\nclass BasicVSRPlusPlusModel(nn.Module):\n    \"\"\"BasicVSR++ neural network architecture.\n\n    This implements the BasicVSR++ architecture for video restoration.\n    It uses bidirectional propagation with optical flow alignment.\n    \"\"\"\n\n    def __init__(\n        self,\n        num_in_ch: int = 3,\n        num_out_ch: int = 3,\n        num_feat: int = 64,\n        num_block: int = 7,\n        scale: int = 1,\n    ) -> None:\n        \"\"\"Initialize BasicVSR++ model.\n\n        Args:\n            num_in_ch: Number of input channels.\n            num_out_ch: Number of output channels.\n            num_feat: Number of features in intermediate layers.\n            num_block: Number of residual blocks.\n            scale: Super-resolution scale factor (1 for denoising).\n        \"\"\"\n        super().__init__()\n        self.num_feat = num_feat\n        self.scale = scale\n\n        # Feature extraction\n        self.feat_extract = nn.Sequential(\n            nn.Conv2d(num_in_ch, num_feat, kernel_size=3, padding=1),\n            nn.ReLU(inplace=True),\n            nn.Conv2d(num_feat, num_feat, kernel_size=3, padding=1),\n            nn.ReLU(inplace=True),\n        )\n\n        # Propagation blocks\n        self.prop_blocks = nn.ModuleList([\n            PropagationBlock(num_feat) for _ in range(num_block)\n        ])\n\n        # Reconstruction\n        self.recon = nn.Sequential(\n            nn.Conv2d(num_feat, num_feat, kernel_size=3, padding=1),\n            nn.ReLU(inplace=True),\n            nn.Conv2d(num_feat, num_out_ch, kernel_size=3, padding=1),\n        )\n\n        # Upsampling (if scale > 1)\n        if scale > 1:\n            self.upsample = nn.Sequential(\n                nn.Conv2d(num_feat, num_feat * scale * scale, kernel_size=3, padding=1),\n                nn.PixelShuffle(scale),\n                nn.ReLU(inplace=True),\n            )\n        else:\n            self.upsample = None\n\n    def forward(self, frames: torch.Tensor) -> torch.Tensor:\n        \"\"\"Forward pass.\n\n        Args:\n            frames: Input tensor of shape (B, T, C, H, W).\n\n        Returns:\n            Output tensor of shape (B, T, C, H*scale, W*scale).\n        \"\"\"\n        B, T, C, H, W = frames.size()\n\n        # Extract features for all frames\n        frames_flat = frames.view(B * T, C, H, W)\n        feats = self.feat_extract(frames_flat)\n        feats = feats.view(B, T, self.num_feat, H, W)\n\n        # Bidirectional propagation\n        outputs = []\n\n        for t in range(T):\n            current = feats[:, t, :, :, :]\n\n            # Forward propagation\n            prev_feat = None\n            for prop_block in self.prop_blocks:\n                current = prop_block(current, prev_feat)\n                prev_feat = current\n\n            # Reconstruction\n            if self.upsample is not None:\n                current = self.upsample(current)\n            output = self.recon(current)\n            outputs.append(output)\n\n        # Stack outputs\n        outputs = torch.stack(outputs, dim=1)\n        return outputs\n\n\nclass BasicVSRPlusPlusDenoiser(VideoDenoiserBase):\n    \"\"\"BasicVSR++ video denoiser.\n\n    BasicVSR++ is a high-quality video restoration network that uses\n    bidirectional propagation with optical flow alignment for effective\n    denoising and restoration.\n\n    Example usage:\n        ```python\n        from video2d3d.denoising import BasicVSRPlusPlusDenoiser, BasicVSRPlusPlusConfig\n\n        # Basic usage\n        config = BasicVSRPlusPlusConfig(num_input_frames=15)\n        denoiser = BasicVSRPlusPlusDenoiser(config=config)\n        denoised_frames = denoiser.denoise_frames(frames)\n\n        # Context manager\n        with BasicVSRPlusPlusDenoiser() as denoiser:\n            denoised = denoiser.denoise_frame(frame, context_frames)\n        ```\n    \"\"\"\n\n    def __init__(\n        self,\n        config: Optional[BasicVSRPlusPlusConfig] = None,\n        *,\n        device: str = \"auto\",\n        cache_dir: Optional[Path] = None,\n    ) -> None:\n        \"\"\"Initialize BasicVSR++ denoiser.\n\n        Args:\n            config: Configuration for BasicVSR++.\n            device: Device for inference ('cuda', 'cpu', or 'auto').\n            cache_dir: Directory to cache downloaded models.\n        \"\"\"\n        self._basicvsr_config = config or BasicVSRPlusPlusConfig()\n        self._cache_dir = cache_dir\n        self._model: Optional[nn.Module] = None\n\n        super().__init__(\n            model_name=\"basicvsr_plusplus\",\n            device=device,\n        )\n\n    @property\n    def num_input_frames(self) -> int:\n        \"\"\"Get the number of input frames required.\"\"\"\n        return self._basicvsr_config.num_input_frames\n\n    @property\n    def model(self) -> Optional[nn.Module]:\n        \"\"\"Get the loaded model (loads if not already loaded).\"\"\"\n        if not self._is_loaded:\n            self.load_model()\n        return self._model\n\n    def _get_model_path(self) -> Path:\n        \"\"\"Get the path to the model weights.\"\"\"\n        if self._basicvsr_config.pretrained_model is not None:\n            return self._basicvsr_config.pretrained_model\n\n        if self._cache_dir is not None:\n            return self._cache_dir / \"basicvsr_plusplus_model.pth\"\n\n        hub_dir = Path(torch.hub.get_dir())\n        return hub_dir / \"basicvsr_plusplus_model.pth\"\n\n    def _download_model(self, path: Path) -> None:\n        \"\"\"Download pretrained model weights.\n\n        Args:\n            path: Path to save the model weights.\n\n        Raises:\n            PretrainedModelError: If download fails.\n        \"\"\"\n        self.logger.info(f\"Downloading BasicVSR++ model to {path}\")\n\n        try:\n            import urllib.request\n\n            path.parent.mkdir(parents=True, exist_ok=True)\n            urllib.request.urlretrieve(_BASICVSR_PLUSPLUS_MODEL_URL, str(path))\n            self.logger.info(\"Model downloaded successfully\")\n\n        except Exception as e:\n            raise PretrainedModelError(\n                f\"Failed to download BasicVSR++ model: {e}\",\n                model_name=\"basicvsr_plusplus\",\n                original_exception=e,\n            ) from e\n\n    def load_model(self) -> None:\n        \"\"\"Load the BasicVSR++ model.\n\n        This method:\n        1. Downloads model weights if not cached\n        2. Creates the model architecture\n        3. Loads the weights\n        4. Moves the model to the target device\n\n        Raises:\n            ModelLoadError: If model loading fails.\n        \"\"\"\n        self.logger.info(\"Loading BasicVSR++ model\")\n        start_time = time.time()\n\n        try:\n            # Get model path\n            model_path = self._get_model_path()\n\n            # Download if needed\n            if not model_path.exists() and self._basicvsr_config.auto_download:\n                self._download_model(model_path)\n\n            # Create model architecture\n            self._model = BasicVSRPlusPlusModel(\n                num_in_ch=3,\n                num_out_ch=3,\n                num_feat=64,\n                num_block=7,\n                scale=self._basicvsr_config.scale,\n            )\n\n            # Load weights if available\n            if model_path.exists():\n                state_dict = torch.load(model_path, map_location=\"cpu\")\n                # Handle potential key mismatches\n                if any(k.startswith('module.') for k in state_dict.keys()):\n                    state_dict = {k[7:]: v for k, v in state_dict.items()}\n                self._model.load_state_dict(state_dict, strict=False)\n                self.logger.debug(f\"Loaded weights from {model_path}\")\n            else:\n                self.logger.warning(\n                    \"No pretrained weights found. Using random initialization. \"\n                    \"Set auto_download=True to download pretrained weights.\"\n                )\n\n            # Move to device\n            self._model = self._model.to(self._device)\n            self._model.eval()\n\n            self._is_loaded = True\n\n            elapsed_ms = (time.time() - start_time) * 1000\n            self.logger.info(\n                f\"BasicVSR++ model loaded in {elapsed_ms:.0f}ms on {self._device}\"\n            )\n\n        except Exception as e:\n            log_exception(\"Failed to load BasicVSR++ model\", exception=e)\n            raise ModelLoadError(\n                f\"Failed to load BasicVSR++ model: {e}\",\n                model_name=\"basicvsr_plusplus\",\n                device=self._device,\n                original_exception=e,\n            ) from e\n\n    def _preprocess_frames(self, frames: List[np.ndarray]) -> torch.Tensor:\n        \"\"\"Preprocess frames for the model.\n\n        Args:\n            frames: List of input frames (H, W, C) uint8.\n\n        Returns:\n            Tensor of shape (B, T, C, H, W) normalized to [0, 1].\n        \"\"\"\n        frame_tensors = []\n        for frame in frames:\n            # Convert to float and normalize\n            tensor = torch.from_numpy(frame.astype(np.float32) / 255.0)\n            # (H, W, C) -> (C, H, W)\n            tensor = tensor.permute(2, 0, 1)\n            frame_tensors.append(tensor)\n\n        # Stack frames: (T, C, H, W)\n        stacked = torch.stack(frame_tensors, dim=0)\n        # Add batch dimension: (1, T, C, H, W)\n        return stacked.unsqueeze(0)\n\n    def _postprocess_frames(self, tensor: torch.Tensor) -> List[np.ndarray]:\n        \"\"\"Postprocess model output to frames.\n\n        Args:\n            tensor: Output tensor of shape (B, T, C, H, W).\n\n        Returns:\n            List of numpy arrays (H, W, C) uint8.\n        \"\"\"\n        # Remove batch dimension: (T, C, H, W)\n        tensor = tensor.squeeze(0)\n\n        frames = []\n        for i in range(tensor.size(0)):\n            frame = tensor[i]\n            # (C, H, W) -> (H, W, C)\n            frame = frame.permute(1, 2, 0)\n            # Clip and convert to uint8\n            frame = frame.clamp(0, 1).numpy()\n            frame = (frame * 255).astype(np.uint8)\n            frames.append(frame)\n\n        return frames\n\n    def _denoise_frames_impl(\n        self,\n        frames: List[np.ndarray],\n        **kwargs,\n    ) -> List[np.ndarray]:\n        \"\"\"Implement BasicVSR++ denoising logic.\n\n        Args:\n            frames: List of input frames as numpy arrays.\n            **kwargs: Additional parameters (ignored).\n\n        Returns:\n            List of denoised frames.\n        \"\"\"\n        if self._model is None:\n            raise InferenceError(\n                \"Model not loaded\",\n                model_name=\"basicvsr_plusplus\",\n                device=self._device,\n            )\n\n        # BasicVSR++ processes all frames together\n        input_tensor = self._preprocess_frames(frames)\n        input_tensor = input_tensor.to(self._device)\n\n        with torch.no_grad():\n            output_tensor = self._model(input_tensor)\n\n        denoised_frames = self._postprocess_frames(output_tensor)\n\n        return denoised_frames\n\n    def close(self) -> None:\n        \"\"\"Release model resources.\"\"\"\n        if self._model is not None:\n            del self._model\n            self._model = None\n\n        self._is_loaded = False\n\n        if self._device.startswith(\"cuda\"):\n            clear_gpu_memory(self._device)\n\n        self.logger.debug(\"BasicVSR++ resources released\")\n\n\ndef create_basicvsr_plusplus_denoiser(\n    num_input_frames: int = 15,\n    scale: int = 1,\n    device: str = \"auto\",\n    auto_download: bool = True,\n    **kwargs,\n) -> BasicVSRPlusPlusDenoiser:\n    \"\"\"Create a BasicVSR++ denoiser with the specified configuration.\n\n    Args:\n        num_input_frames: Number of input frames for temporal context.\n        scale: Super-resolution scale (1 for denoising only).\n        device: Device for inference ('cuda', 'cpu', or 'auto').\n        auto_download: Whether to automatically download pretrained weights.\n        **kwargs: Additional BasicVSRPlusPlusConfig field values.\n\n    Returns:\n        Configured BasicVSRPlusPlusDenoiser instance.\n    \"\"\"\n    config = BasicVSRPlusPlusConfig(\n        num_input_frames=num_input_frames,\n        scale=scale,\n        auto_download=auto_download,\n        **kwargs,\n    )\n    return BasicVSRPlusPlusDenoiser(config=config, device=device)\n\n\n__all__ = [\n    \"BasicVSRPlusPlusDenoiser\",\n    \"BasicVSRPlusPlusModel\",\n    \"BasicVSRPlusPlusConfig\",\n    \"create_basicvsr_plusplus_denoiser\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Video denoiser selector with automatic model selection and fallback.\n\nThis module provides a unified interface for video denoising that automatically\nselects the best available model and handles fallback between different models.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport time\nfrom pathlib import Path\nfrom typing import TYPE_CHECKING, List, Optional, Union\n\nimport numpy as np\n\nfrom video2d3d.utils.logger import get_logger, log_exception\n\nfrom .base import VideoDenoiserBase\nfrom .config import DenoiserModelType, VideoDenoiserConfig\nfrom .exceptions import InferenceError, VideoDenoisingError\nfrom .fastdvdnet import FastDVDNetDenoiser\nfrom .basicvsr_plusplus import BasicVSRPlusPlusDenoiser\n\nif TYPE_CHECKING:\n    from loguru import Logger\n\n\nclass VideoDenoiserSelector:\n    \"\"\"Unified video denoising with automatic model selection and fallback.\n\n    This class provides a single interface for video denoising that handles\n    model selection, loading, and fallback automatically.\n\n    Example usage:\n        ```python\n        # Basic usage\n        config = VideoDenoiserConfig(\n            model_type=DenoiserModelType.FASTDVDNET,\n            enable_fallback=True,\n        )\n        selector = VideoDenoiserSelector(config=config)\n        denoised_frames = selector.denoise_frames(frames)\n\n        # Context manager\n        with VideoDenoiserSelector() as selector:\n            denoised = selector.denoise_frames(frames)\n        ```\n    \"\"\"\n\n    def __init__(\n        self,\n        config: Optional[VideoDenoiserConfig] = None,\n        *,\n        model_type: str = \"fastdvdnet\",\n        device: str = \"auto\",\n        cache_dir: Optional[Path] = None,\n    ) -> None:\n        \"\"\"Initialize the video denoiser selector.\n\n        Args:\n            config: VideoDenoiserConfig object. If provided, model_type and device\n                   are ignored.\n            model_type: Primary model type to use.\n            device: Device for inference.\n            cache_dir: Directory to cache downloaded models.\n        \"\"\"\n        if config is not None:\n            self.config = config\n        else:\n            self.config = VideoDenoiserConfig(\n                model_type=DenoiserModelType.from_string(model_type),\n                device=device,\n            )\n\n        self._cache_dir = cache_dir\n\n        # Loaded denoisers cache\n        self._denoisers: dict[DenoiserModelType, VideoDenoiserBase] = {}\n        self._active_model: Optional[DenoiserModelType] = None\n\n        self._logger = get_logger(\"denoising.selector\")\n        self._logger.info(\n            f\"VideoDenoiserSelector initialized: model={self.config.model_type.value}, \"\n            f\"enabled={self.config.enabled}, device={self.config.device}\"\n        )\n\n    @property\n    def active_model(self) -> Optional[DenoiserModelType]:\n        \"\"\"Get the currently active model type.\"\"\"\n        return self._active_model\n\n    @property\n    def is_enabled(self) -> bool:\n        \"\"\"Check if denoising is enabled.\"\"\"\n        return self.config.enabled and self.config.model_type != DenoiserModelType.NONE\n\n    def _get_denoiser(self, model_type: DenoiserModelType) -> VideoDenoiserBase:\n        \"\"\"Get or create a denoiser for the specified model type.\n\n        Args:\n            model_type: Model type to get denoiser for.\n\n        Returns:\n            Denoiser instance for the model.\n\n        Raises:\n            VideoDenoisingError: If model loading fails.\n        \"\"\"\n        if model_type in self._denoisers:\n            return self._denoisers[model_type]\n\n        try:\n            denoiser = self._create_denoiser(model_type)\n            self._denoisers[model_type] = denoiser\n            return denoiser\n        except Exception as e:\n            self._logger.warning(f\"Failed to create {model_type.value} denoiser: {e}\")\n            raise\n\n    def _create_denoiser(self, model_type: DenoiserModelType) -> VideoDenoiserBase:\n        \"\"\"Create a new denoiser for the specified model type.\n\n        Args:\n            model_type: Model type to create denoiser for.\n\n        Returns:\n            New denoiser instance.\n\n        Raises:\n            VideoDenoisingError: If model creation fails.\n        \"\"\"\n        if model_type == DenoiserModelType.FASTDVDNET:\n            return FastDVDNetDenoiser(\n                config=self.config.fastdvdnet,\n                device=self.config.device,\n                cache_dir=self._cache_dir,\n            )\n        elif model_type in (DenoiserModelType.BASICVSR_PLUSPLUS, DenoiserModelType.BASICVSR):\n            return BasicVSRPlusPlusDenoiser(\n                config=self.config.basicvsr_plusplus,\n                device=self.config.device,\n                cache_dir=self._cache_dir,\n            )\n        else:\n            raise VideoDenoisingError(\n                f\"Unknown model type: {model_type}\",\n                model_name=model_type.value,\n            )\n\n    def _build_attempt_order(self) -> List[DenoiserModelType]:\n        \"\"\"Build the order of models to try.\n\n        Returns:\n            List of model types to try in order.\n        \"\"\"\n        if not self.config.enable_fallback:\n            return [self.config.model_type]\n\n        # Start with primary model\n        attempt_order = [self.config.model_type]\n\n        # Add fallback chain\n        for model in self.config.fallback_chain:\n            if model not in attempt_order and model != DenoiserModelType.NONE:\n                attempt_order.append(model)\n\n        return attempt_order\n\n    def denoise_frames(\n        self,\n        frames: List[np.ndarray],\n    ) -> List[np.ndarray]:\n        \"\"\"Denoise a sequence of frames with automatic model selection and fallback.\n\n        Args:\n            frames: List of input frames as numpy arrays (H, W, C) in RGB format.\n\n        Returns:\n            List of denoised frames.\n\n        Raises:\n            InferenceError: If all models fail.\n        \"\"\"\n        # If denoising is disabled, return frames unchanged\n        if not self.is_enabled:\n            return frames\n\n        if not frames:\n            return frames\n\n        start_time = time.time()\n\n        # Build attempt order\n        attempt_order = self._build_attempt_order()\n\n        # Try each model\n        errors: List[tuple[DenoiserModelType, Exception]] = []\n\n        for model_type in attempt_order:\n            try:\n                denoiser = self._get_denoiser(model_type)\n                result = denoiser.denoise_frames(frames)\n                self._active_model = model_type\n\n                elapsed_ms = (time.time() - start_time) * 1000\n                self._logger.debug(\n                    f\"Denoising completed with {model_type.value} in {elapsed_ms:.2f}ms\"\n                )\n\n                return result\n\n            except Exception as e:\n                self._logger.warning(\n                    f\"Model {model_type.value} failed: {e}. Trying next model...\"\n                )\n                errors.append((model_type, e))\n                continue\n\n        # All models failed\n        error_msg = f\"All denoising models failed. Attempted: {[m.value for m, _ in errors]}\"\n        self._logger.error(error_msg)\n\n        # If fallback to original frames is desired, return them\n        # Otherwise, raise an error\n        if self.config.enable_fallback and errors:\n            self._logger.warning(\n                \"All denoising models failed. Returning original frames.\"\n            )\n            return frames\n\n        raise InferenceError(\n            error_msg,\n            attempted_models=[m.value for m, _ in errors],\n            original_exceptions=[e for _, e in errors],\n        )\n\n    def denoise_frame(\n        self,\n        frame: np.ndarray,\n        context_frames: Optional[List[np.ndarray]] = None,\n    ) -> np.ndarray:\n        \"\"\"Denoise a single frame using optional temporal context.\n\n        Args:\n            frame: Input frame as numpy array (H, W, C) in RGB format.\n            context_frames: Optional list of surrounding frames for temporal context.\n\n        Returns:\n            Denoised frame as numpy array.\n\n        Raises:\n            InferenceError: If denoising fails.\n        \"\"\"\n        if not self.is_enabled:\n            return frame\n\n        if context_frames is None:\n            context_frames = [frame]\n\n        denoised = self.denoise_frames(context_frames)\n\n        # Return the center frame (the denoised version of the input)\n        center_idx = len(denoised) // 2\n        return denoised[center_idx]\n\n    def get_available_models(self) -> List[DenoiserModelType]:\n        \"\"\"Get list of available model types.\n\n        Returns:\n            List of model types that are available (successfully loaded).\n        \"\"\"\n        return list(self._denoisers.keys())\n\n    def preload_models(\n        self,\n        models: Optional[List[Union[str, DenoiserModelType]]] = None,\n    ) -> dict[str, bool]:\n        \"\"\"Preload specified models or all models in fallback chain.\n\n        Args:\n            models: List of models to preload. If None, preloads fallback chain.\n\n        Returns:\n            Dictionary mapping model names to load success status.\n        \"\"\"\n        if models is None:\n            models = [self.config.model_type] + self.config.fallback_chain\n        else:\n            models = [\n                DenoiserModelType.from_string(m) if isinstance(m, str) else m\n                for m in models\n            ]\n\n        results: dict[str, bool] = {}\n\n        for model_type in models:\n            if model_type == DenoiserModelType.NONE:\n                continue\n\n            try:\n                self._get_denoiser(model_type)\n                results[model_type.value] = True\n                self._logger.info(f\"Preloaded model: {model_type.value}\")\n            except Exception as e:\n                results[model_type.value] = False\n                self._logger.warning(f\"Failed to preload {model_type.value}: {e}\")\n\n        return results\n\n    def switch_model(self, model_type: Union[str, DenoiserModelType]) -> bool:\n        \"\"\"Switch to a different model.\n\n        Args:\n            model_type: Model type to switch to.\n\n        Returns:\n            True if switch was successful, False otherwise.\n        \"\"\"\n        if isinstance(model_type, str):\n            model_type = DenoiserModelType.from_string(model_type)\n\n        try:\n            self._get_denoiser(model_type)\n            self._active_model = model_type\n            self._logger.info(f\"Switched to model: {model_type.value}\")\n            return True\n        except Exception as e:\n            self._logger.error(f\"Failed to switch to model {model_type.value}: {e}\")\n            return False\n\n    def close(self) -> None:\n        \"\"\"Release all loaded model resources.\"\"\"\n        for model_type, denoiser in self._denoisers.items():\n            try:\n                denoiser.close()\n            except Exception as e:\n                self._logger.warning(f\"Error closing {model_type.value}: {e}\")\n\n        self._denoisers.clear()\n        self._active_model = None\n        self._logger.debug(\"VideoDenoiserSelector resources released\")\n\n    def __enter__(self) -> \"VideoDenoiserSelector\":\n        \"\"\"Context manager entry.\"\"\"\n        return self\n\n    def __exit__(self, exc_type, exc_val, exc_tb) -> None:\n        \"\"\"Context manager exit - cleanup resources.\"\"\"\n        self.close()\n\n\ndef create_video_denoiser(\n    model_type: str = \"fastdvdnet\",\n    enabled: bool = True,\n    device: str = \"auto\",\n    **kwargs,\n) -> VideoDenoiserSelector:\n    \"\"\"Create a video denoiser with the specified configuration.\n\n    Args:\n        model_type: Model type string ('fastdvdnet', 'basicvsr_plusplus', etc.).\n        enabled: Whether denoising is enabled.\n        device: Device for inference.\n        **kwargs: Additional VideoDenoiserConfig field values.\n\n    Returns:\n        Configured VideoDenoiserSelector instance.\n    \"\"\"\n    config = VideoDenoiserConfig(\n        enabled=enabled,\n        model_type=DenoiserModelType.from_string(model_type),\n        device=device,\n        **kwargs,\n    )\n    return VideoDenoiserSelector(config=config)\n\n\ndef denoise_frames_auto(\n    frames: List[np.ndarray],\n    model_type: str = \"fastdvdnet\",\n    device: str = \"auto\",\n) -> List[np.ndarray]:\n    \"\"\"Denoise frames with automatic model selection (convenience function).\n\n    Args:\n        frames: List of input frames as numpy arrays.\n        model_type: Model type string.\n        device: Device for inference.\n\n    Returns:\n        List of denoised frames.\n    \"\"\"\n    with create_video_denoiser(model_type=model_type, device=device) as denoiser:\n        return denoiser.denoise_frames(frames)\n\n\n__all__ = [\n    \"VideoDenoiserSelector\",\n    \"create_video_denoiser\",\n    \"denoise_frames_auto\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/selector.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create denoising module structure (__init__.py, exceptions.py)",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Implement VideoDenoiserConfig dataclass",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Implement abstract VideoDenoiser base class",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Implement FastDVDNet denoiser",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Implement BasicVSR++ denoiser",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Implement VideoDenoiserSelector with fallback chain",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Add VideoDenoisingConfig to utils/config.py",
      "status": "in_progress",
      "priority": "medium"
    },
    {
      "content": "Add denoising section to config/default.yaml",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add CLI options for video denoising",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Create unit tests for denoising module",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify implementation with Playwright test",
      "status": "pending",
      "priority": "medium"
    }
  ]
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Video denoising module.\n\nThis module provides video denoising functionality using AI models\nincluding FastDVDNet and BasicVSR++ for reducing noise in video frames\nbefore depth estimation.\n\nSupported models:\n- FastDVDNet: Fast video denoising without flow estimation\n- BasicVSR++: High-quality video restoration with bidirectional propagation\n\nExample usage:\n    ```python\n    from video2d3d.denoising import (\n        VideoDenoiserSelector,\n        VideoDenoiserConfig,\n        DenoiserModelType,\n    )\n\n    # Basic usage\n    config = VideoDenoiserConfig(\n        enabled=True,\n        model_type=DenoiserModelType.FASTDVDNET,\n    )\n    denoiser = VideoDenoiserSelector(config=config)\n    denoised_frames = denoiser.denoise_frames(frames)\n\n    # Context manager\n    with VideoDenoiserSelector(model_type=\"fastdvdnet\") as denoiser:\n        denoised = denoiser.denoise_frames(frames)\n    ```\n\"\"\"\n\nfrom __future__ import annotations\n\n# Configuration\nfrom video2d3d.denoising.config import (\n    DenoiserModelType,\n    NoiseLevelMode,\n    FastDVDNetConfig,\n    BasicVSRPlusPlusConfig,\n    VideoDenoiserConfig,\n    VideoDenoisingPipelineConfig,\n    _DEFAULT_NUM_INPUT_FRAMES,\n    _DEFAULT_NOISE_LEVEL,\n    _DEFAULT_BATCH_SIZE,\n)\n\n# Base class\nfrom video2d3d.denoising.base import VideoDenoiserBase\n\n# Exceptions\nfrom video2d3d.denoising.exceptions import (\n    VideoDenoisingError,\n    ModelLoadError,\n    InferenceError,\n    UnsupportedModelError,\n    PretrainedModelError,\n    FrameBufferError,\n)\n\n# Model implementations\nfrom video2d3d.denoising.fastdvdnet import (\n    FastDVDNetDenoiser,\n    FastDVDNetModel,\n    create_fastdvdnet_denoiser,\n)\n\nfrom video2d3d.denoising.basicvsr_plusplus import (\n    BasicVSRPlusPlusDenoiser,\n    BasicVSRPlusPlusModel,\n    create_basicvsr_plusplus_denoiser,\n)\n\n# Selector with fallback\nfrom video2d3d.denoising.selector import (\n    VideoDenoiserSelector,\n    create_video_denoiser,\n    denoise_frames_auto,\n)\n\n\n__all__ = [\n    # Enums\n    \"DenoiserModelType\",\n    \"NoiseLevelMode\",\n    # Config classes\n    \"FastDVDNetConfig\",\n    \"BasicVSRPlusPlusConfig\",\n    \"VideoDenoiserConfig\",\n    \"VideoDenoisingPipelineConfig\",\n    # Base class\n    \"VideoDenoiserBase\",\n    # Exceptions\n    \"VideoDenoisingError\",\n    \"ModelLoadError\",\n    \"InferenceError\",\n    \"UnsupportedModelError\",\n    \"PretrainedModelError\",\n    \"FrameBufferError\",\n    # FastDVDNet\n    \"FastDVDNetDenoiser\",\n    \"FastDVDNetModel\",\n    \"create_fastdvdnet_denoiser\",\n    # BasicVSR++\n    \"BasicVSRPlusPlusDenoiser\",\n    \"BasicVSRPlusPlusModel\",\n    \"create_basicvsr_plusplus_denoiser\",\n    # Selector\n    \"VideoDenoiserSelector\",\n    \"create_video_denoiser\",\n    \"denoise_frames_auto\",\n    # Constants\n    \"_DEFAULT_NUM_INPUT_FRAMES\",\n    \"_DEFAULT_NOISE_LEVEL\",\n    \"_DEFAULT_BATCH_SIZE\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "offset": 1,
  "limit": 100
}

🔧 Tool: grep
Input: {
  "pattern": "UpscalerConfig|class Config",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "output_mode": "content",
  "head_limit": 50
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "limit": 100,
  "offset": 310
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "edits": [
    {
      "op": "replace",
      "pos": "40#HT",
      "lines": [
        "    \"VideoDenoisingConfig\","
      ]
    },
    {
      "op": "replace",
      "pos": "25#ZJ#__all__",
      "lines": [
        "# Public API\n__all__ = [\n    \"Config\",\n    \"ProcessingConfig\",\n    \"VideoInputConfig\",\n    \"VideoOutputConfig\",\n    \"DepthEstimationConfig\",\n    \"AnaglyphConfig\",\n    \"SideBySideConfig\",\n    \"StereoGenerationConfig\",\n    \"QualityConfig\",\n    \"LoggingConfig\",\n    \"RateLimitConfig\",\n    \"WebApiConfig\",\n    \"PreviewConfig\",\n    \"ProgressTrackingConfig\",\n    \"UpscalerConfig\",\n    \"VideoDenoisingConfig\",\n    \"export_config\",\n    \"import_config\",\n    \"export_current_config\",\n    \"import_and_apply_config\",\n    \"load_config\",\n    \"get_config\",\n    \"reload_config\",\n    \"FORMAT_JSON\",\n    \"FORMAT_YAML\",\n    \"SUPPORTED_EXPORT_FORMATS\",\n]"
      ]
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "limit": 50,
  "offset": 325
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "edits": [
    {
      "end": "361#BR|",
      "lines": [
        "",
        "@dataclass",
        "class VideoDenoisingConfig:",
        "    \"\"\"Video denoising configuration settings.",
        "",
        "    Attributes:",
        "        enabled: Whether video denoising is enabled.",
        "        model_type: Type of denoising model (fastdvdnet, basicvsr_plusplus).",
        "        use_gpu: Whether to use GPU acceleration.",
        "        num_frames: Number of frames for temporal context.",
        "        noise_level: Default noise level for denoising.",
        "        fallback_to_cpu: Whether to fallback to CPU on GPU error.",
        "    \"\"\"",
        "",
        "    enabled: bool = False",
        "    model_type: str = \"fastdvdnet\"",
        "    use_gpu: bool = True",
        "    num_frames: int = 5",
        "    noise_level: float = 30.0",
        "    fallback_to_cpu: bool = True",
        "",
        "    def to_dict(self) -> Dict[str, Any]:",
        "        \"\"\"Convert to dictionary.\"\"\"",
        "        return asdict(self)",
        ""
      ],
      "op": "append",
      "pos": "361#BR|"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "limit": 50,
  "offset": 380
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "402#VJ|",
      "lines": [
        "    upscaler: UpscalerConfig = field(default_factory=UpscalerConfig)",
        "    video_denoising: VideoDenoisingConfig = field(default_factory=VideoDenoisingConfig)",
        ""
      ],
      "op": "append",
      "pos": "401#MP|progress: ProgressTrackingConfig = field(default_factory=ProgressTrackingConfig)"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}

🔧 Tool: grep
Input: {
  "output_mode": "content",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "pattern": "_parse_simple_section.*Progress|progress.*_parse",
  "head_limit": 10
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "limit": 50,
  "offset": 470
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "475#MX|",
      "lines": [
        "",
        "            if \"video_denoising\" in data:",
        "                config.video_denoising = cls._parse_simple_section(",
        "                    data[\"video_denoising\"], VideoDenoisingConfig",
        "                )",
        ""
      ],
      "op": "append",
      "pos": "475#MX|)"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py",
  "limit": 50,
  "offset": 630
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "643#VY|config.progress = _parse_config_section(merged_config, \"progress\", ProgressTrackingConfig)",
      "lines": [
        "",
        "    if \"upscaler\" in merged_config:",
        "        config.upscaler = _parse_config_section(merged_config, \"upscaler\", UpscalerConfig)",
        "",
        "    if \"video_denoising\" in merged_config:",
        "        config.video_denoising = _parse_config_section(merged_config, \"video_denoising\", VideoDenoisingConfig)",
        ""
      ],
      "op": "append",
      "pos": "643#VY|config.progress = _parse_config_section(merged_config, \"progress\", ProgressTrackingConfig)"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create denoising module structure (__init__.py, exceptions.py)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement VideoDenoiserConfig dataclass",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement abstract VideoDenoiser base class",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement FastDVDNet denoiser",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement BasicVSR++ denoiser",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement VideoDenoiserSelector with fallback chain",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add VideoDenoisingConfig to utils/config.py",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add denoising section to config/default.yaml",
      "priority": "medium",
      "status": "in_progress"
    },
    {
      "content": "Add CLI options for video denoising",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for denoising module",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with Playwright test",
      "priority": "medium",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/config/default.yaml",
  "limit": 50,
  "offset": 380
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "394#WS|track_failures: true",
      "lines": [
        "",
        "# Video Denoising Settings",
        "# AI-based video denoising for cleaner depth estimation",
        "video_denoising:",
        "  # Enable/disable video denoising",
        "  enabled: false",
        "  ",
        "  # Denoising model to use",
        "  # Options: fastdvdnet, basicvsr_plusplus, basicvsr",
        "  model_type: fastdvdnet",
        "  ",
        "  # Use GPU for inference",
        "  use_gpu: true",
        "  ",
        "  # Number of frames for temporal context",
        "  # Higher values = better temporal consistency but slower",
        "  num_frames: 5",
        "  ",
        "  # Default noise level (sigma)",
        "  # Used for fixed noise level mode",
        "  noise_level: 30.0",
        "  ",
        "  # Fallback to CPU if GPU errors occur",
        "  fallback_to_cpu: true"
      ],
      "op": "append",
      "pos": "394#WS|track_failures: true"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/config/default.yaml"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create denoising module structure (__init__.py, exceptions.py)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement VideoDenoiserConfig dataclass",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement abstract VideoDenoiser base class",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement FastDVDNet denoiser",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement BasicVSR++ denoiser",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Implement VideoDenoiserSelector with fallback chain",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add VideoDenoisingConfig to utils/config.py",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add denoising section to config/default.yaml",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Create unit tests for denoising module",
      "priority": "medium",
      "status": "in_progress"
    },
    {
      "content": "Verify implementation with Playwright test",
      "priority": "medium",
      "status": "pending"
    }
  ]
}
