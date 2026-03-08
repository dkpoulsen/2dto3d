
🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && source .venv/bin/activate && python -c \"from video2d3d.denoising import VideoDenoiserSelector, DenoiserModelType, VideoDenoiserConfig; print('Import successful')\"",
  "description": "Test denoising module import"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && source .venv/bin/activate && python -c \"from video2d3d.utils.config import VideoDenoisingConfig; print('Config import successful')\"",
  "description": "Test config import"
}


---

## Follow-up Session

I'll perform a thorough code review of the Video Denoising feature and then update the code based on my findings. Let me start by exploring the implementation.

🔧 Tool: glob
Input: {
  "pattern": "**/*denois*.py"
}

🔧 Tool: glob
Input: {
  "pattern": "**/video2d3d/**/*.py"
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find denoising module files",
  "prompt": "I'm reviewing the Video Denoising feature implementation. Find all files related to denoising - including the main denoising module, config files, and any related utilities. I need to understand the complete implementation structure. Return file paths and brief descriptions of each file's purpose."
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find existing codebase patterns",
  "prompt": "I need to understand the existing codebase patterns for reviewing the denoising feature. Find:\n1. How other modules are structured (e.g., depth estimation, video processing)\n2. Configuration patterns used across the codebase\n3. Logging and error handling patterns\n4. Any base classes or utilities used by other modules\n\nFocus on src/video2d3d/ directory. Return file paths and pattern descriptions."
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/__init__.py"
}
Let me read all the denoising module files:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/base.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/exceptions.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/selector.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py"
}
Let me also look at existing codebase patterns for comparison:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/upscaling/config.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/gpu.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/logger.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/upscaling/base.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}
Now let me create a todo list and start the code review and update process:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Improve exception handling consistency",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify all changes work correctly",
      "status": "pending",
      "priority": "high"
    }
  ]
}
Based on my code review, I've identified several issues that need to be fixed. Let me address them:

## Phase 1: Review Findings

**Issues Found:**

1. **Type Hint Issue (config.py)**: `progress_callback: callable | None` uses `callable` (built-in) instead of `Callable` (typing)
2. **Exception Missing Attributes (exceptions.py)**: `InferenceError` is missing `attempted_models` and `original_exceptions` attributes that are used in selector.py
3. **Magic Numbers**: `255.0` for normalization is hardcoded in multiple places
4. **Inconsistent Exception Raising**: selector.py passes unsupported arguments to InferenceError

Let me fix these issues:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Improve exception handling consistency",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify all changes work correctly",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py",
  "edits": [
    {
      "op": "replace",
      "pos": "7#ZQ|",
      "end": "12#TX|",
      "lines": "from __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom enum import Enum\nfrom pathlib import Path\nfrom typing import TYPE_CHECKING, Callable\n\nif TYPE_CHECKING:\n    pass\n\nimport numpy as np\n\nfrom video2d3d.utils.gpu import GPUConfig, select_device"
    },
    {
      "op": "replace",
      "pos": "257#SJ|",
      "end": "259#RK|",
      "lines": "    buffer_size: int = 30\n    overlap: int = 2\n    progress_callback: Callable[[int, int], None] | None = None\n    enable_profiling: bool = False"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py",
  "edits": [
    {
      "end": "13#MY|",
      "lines": "from __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom enum import Enum\nfrom pathlib import Path\nfrom typing import TYPE_CHECKING, Callable\n\nif TYPE_CHECKING:\n    pass\n\nfrom video2d3d.utils.gpu import GPUConfig, select_device",
      "op": "replace",
      "pos": "7#ZQ|"
    },
    {
      "end": "259#RK|",
      "lines": "    buffer_size: int = 30\n    overlap: int = 2\n    progress_callback: Callable[[int, int], None] | None = None\n    enable_profiling: bool = False",
      "op": "replace",
      "pos": "256#QK|"
    }
  ]
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Improve exception handling consistency",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify all changes work correctly",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/exceptions.py"
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "44#PB|",
      "lines": "class InferenceError(VideoDenoisingError):\n    \"\"\"Exception raised when denoising inference fails.\n\n    Attributes:\n        attempted_models: List of model names that were attempted before failure.\n        original_exceptions: List of original exceptions from each attempt.\n    \"\"\"\n\n    def __init__(\n        self,\n        message: str,\n        *,\n        attempted_models: list[str] | None = None,\n        original_exceptions: list[Exception] | None = None,\n        **kwargs,\n    ) -> None:\n        \"\"\"Initialize the inference error.\n\n        Args:\n            message: Error description.\n            attempted_models: List of model names that were attempted.\n            original_exceptions: List of exceptions from each attempt.\n            **kwargs: Additional arguments passed to parent.\n        \"\"\"\n        super().__init__(message, **kwargs)\n        self.attempted_models = attempted_models or []\n        self.original_exceptions = original_exceptions or []",
      "op": "replace",
      "pos": "40#ZR|"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/exceptions.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "priority": "medium",
      "status": "in_progress"
    },
    {
      "content": "Improve exception handling consistency",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify all changes work correctly",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py"
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "23#NV|",
      "lines": "# Default configuration values\n_DEFAULT_NUM_INPUT_FRAMES: int = 5  # Number of frames for temporal denoising\n_DEFAULT_NOISE_LEVEL: float = 30.0  # Default noise level (sigma)\n_DEFAULT_BATCH_SIZE: int = 4\n\n# Pixel value normalization constant for uint8 to float conversion\n_UINT8_MAX_VALUE: float = 255.0",
      "op": "replace",
      "pos": "19#VK|"
    },
    {
      "end": "286#XM|",
      "lines": "__all__ = [\n    # Enums\n    \"DenoiserModelType\",\n    \"NoiseLevelMode\",\n    # Config classes\n    \"FastDVDNetConfig\",\n    \"BasicVSRPlusPlusConfig\",\n    \"VideoDenoiserConfig\",\n    \"VideoDenoisingPipelineConfig\",\n    # Constants\n    \"_DEFAULT_NUM_INPUT_FRAMES\",\n    \"_DEFAULT_NOISE_LEVEL\",\n    \"_DEFAULT_BATCH_SIZE\",\n    \"_UINT8_MAX_VALUE\",\n]",
      "op": "replace",
      "pos": "273#ZJ|"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py"
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "29#PR|",
      "lines": "from .base import VideoDenoiserBase\nfrom .config import _UINT8_MAX_VALUE, FastDVDNetConfig\nfrom .exceptions import InferenceError, ModelLoadError, PretrainedModelError",
      "op": "replace",
      "pos": "27#TS|"
    },
    {
      "end": "277#HQ|",
      "lines": "            tensor = torch.from_numpy(frame.astype(np.float32) / _UINT8_MAX_VALUE)\n            # Change from (H, W, C) to (C, H, W)\n            tensor = tensor.permute(2, 0, 1)\n            frame_tensors.append(tensor)",
      "op": "replace",
      "pos": "273#TJ|"
    },
    {
      "end": "305#NN|",
      "lines": "        frame = tensor.clamp(0, 1).numpy()\n        frame = (frame * _UINT8_MAX_VALUE).astype(np.uint8)\n\n        return frame",
      "op": "replace",
      "pos": "303#RP|"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py",
  "limit": 35
}

🔧 Tool: grep
Input: {
  "pattern": "log_exception",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/logger.py",
  "output_mode": "content"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py",
  "offset": 265,
  "limit": 50
}

🔧 Tool: grep
Input: {
  "output_mode": "content",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py",
  "pattern": "_postprocess"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py",
  "limit": 50
}

🔧 Tool: grep
Input: {
  "output_mode": "content",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py",
  "pattern": "255",
  "head_limit": 10
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py",
  "limit": 100,
  "offset": 430
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "30#PR|",
      "lines": "from .base import VideoDenoiserBase\nfrom .config import _UINT8_MAX_VALUE, BasicVSRPlusPlusConfig\nfrom .exceptions import InferenceError, ModelLoadError, PretrainedModelError",
      "op": "replace",
      "pos": "28#TS|"
    },
    {
      "end": "446#HQ|",
      "lines": "            tensor = torch.from_numpy(frame.astype(np.float32) / _UINT8_MAX_VALUE)\n            # (H, W, C) -> (C, H, W)\n            tensor = tensor.permute(2, 0, 1)\n            frame_tensors.append(tensor)",
      "op": "replace",
      "pos": "442#WS|"
    },
    {
      "end": "474#XV|",
      "lines": "            frame = frame.clamp(0, 1).numpy()\n            frame = (frame * _UINT8_MAX_VALUE).astype(np.uint8)\n            frames.append(frame)\n\n        return frames",
      "op": "replace",
      "pos": "471#MP|"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Improve exception handling consistency",
      "priority": "medium",
      "status": "in_progress"
    },
    {
      "content": "Verify all changes work correctly",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/__init__.py"
}

🔧 Tool: grep
Input: {
  "output_mode": "content",
  "path": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/selector.py",
  "pattern": "^def "
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "54#KT|",
      "lines": "from video2d3d.denoising.config import (\n    _DEFAULT_BATCH_SIZE,\n    _DEFAULT_NOISE_LEVEL,\n    _DEFAULT_NUM_INPUT_FRAMES,\n    _UINT8_MAX_VALUE,\n    BasicVSRPlusPlusConfig,\n    DenoiserModelType,\n    FastDVDNetConfig,\n    NoiseLevelMode,\n    VideoDenoiserConfig,\n    VideoDenoisingPipelineConfig,\n)",
      "op": "replace",
      "pos": "44#VM|"
    },
    {
      "end": "114#SR|",
      "lines": "    # Constants\n    \"_DEFAULT_NUM_INPUT_FRAMES\",\n    \"_DEFAULT_NOISE_LEVEL\",\n    \"_DEFAULT_BATCH_SIZE\",\n    \"_UINT8_MAX_VALUE\",\n]",
      "op": "replace",
      "pos": "110#HW|"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/fastdvdnet.py",
  "limit": 35
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/basicvsr_plusplus.py",
  "limit": 35
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Improve exception handling consistency",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Verify all changes work correctly",
      "priority": "high",
      "status": "in_progress"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && source .venv/bin/activate && python -c \"from video2d3d.denoising import VideoDenoiserSelector, DenoiserModelType, VideoDenoiserConfig, _UINT8_MAX_VALUE; print(f'Import successful. _UINT8_MAX_VALUE = {_UINT8_MAX_VALUE}')\"",
  "description": "Test denoising module import"
}


---

## Follow-up Session


🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git log -3 --oneline",
  "description": "Show recent commit history"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git status",
  "description": "Check git status for changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git diff --stat",
  "description": "Show diff statistics"
}
Let me look at the specific changes made to the denoising module:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git diff src/video2d3d/denoising/",
  "description": "Show diff for denoising module"
}
Now I'll stage the denoising module changes and create the commit:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git add src/video2d3d/denoising/",
  "description": "Stage denoising module changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git commit -m \"refactor(denoising): improve code quality and type safety\" -m \"- Fix type hint: use Callable from typing instead of builtin callable\n- Add InferenceError attributes for attempted_models and original_exceptions\n- Extract magic number 255.0 to _UINT8_MAX_VALUE constant\n- Add missing imports for type hints in config.py\"",
  "description": "Commit denoising code review fixes"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review code quality issues in denoising module",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix type hint issues (callable vs Callable)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Fix InferenceError missing attributes",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Add normalization constant for magic numbers",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Improve exception handling consistency",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Verify all changes work correctly",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Commit denoising module changes",
      "priority": "high",
      "status": "completed"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git log -1 --format=full",
  "description": "Verify commit details"
}
<summary>
## Summary: Video Denoiser Code Review and Quality Improvements

### Changes Implemented
- **Type Hint Fix**: Changed `progress_callback: callable | None` to `progress_callback: Callable[[int, int], None] | None` using proper `Callable` from `typing` module
- **InferenceError Enhancement**: Added `attempted_models` and `original_exceptions` attributes to `InferenceError` class for better error tracking during fallback model selection
- **Magic Number Elimination**: Extracted hardcoded `255.0` to `_UINT8_MAX_VALUE` constant for pixel value normalization
- **Import Organization**: Added proper imports for type hints in config.py

### Files Modified
- `src/video2d3d/denoising/__init__.py` - Export `_UINT8_MAX_VALUE` constant
- `src/video2d3d/denoising/config.py` - Added `Callable` import, defined `_UINT8_MAX_VALUE` constant, fixed type hint
- `src/video2d3d/denoising/exceptions.py` - Enhanced `InferenceError` with tracking attributes
- `src/video2d3d/denoising/fastdvdnet.py` - Use `_UINT8_MAX_VALUE` instead of magic number
- `src/video2d3d/denoising/basicvsr_plusplus.py` - Use `_UINT8_MAX_VALUE` instead of magic number

### Notes for Developer
- The `InferenceError` now supports tracking which models were attempted and what exceptions occurred, useful for debugging fallback scenarios
- The normalization constant `_UINT8_MAX_VALUE` is now exported from the denoising module's public API

### Verification Status
- Import verification passed: `from video2d3d.denoising import VideoDenoiserSelector, DenoiserModelType, VideoDenoiserConfig, _UINT8_MAX_VALUE` works correctly

### Commit Details
- **Commit Hash**: `d5b28a0f7c38ba41d9a113e1b4432af6a24dc8d2`
- **Commit Message**:
  ```
  refactor(denoising): improve code quality and type safety
  
  - Fix type hint: use Callable from typing instead of builtin callable
  - Add InferenceError attributes for attempted_models and original_exceptions
  - Extract magic number 255.0 to _UINT8_MAX_VALUE constant
  - Add missing imports for type hints in config.py
  ```
- **Files Committed**: 5 files changed, 40 insertions(+), 11 deletions(-)
</summary>

---

## Follow-up Session

I'll complete the Testing step for the Video Denoiser feature. Let me first review what needs testing and then write comprehensive tests.

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py"
}

🔧 Tool: glob
Input: {
  "pattern": "tests/**/*.py"
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find existing test patterns",
  "prompt": "I need to write tests for the Video Denoising module. Find:\n1. Existing test files in the tests/ directory to understand the testing patterns used\n2. How tests are structured (fixtures, mocking, assertions)\n3. Any test utilities or base classes used\n4. How external dependencies like PyTorch are mocked in tests\n\nReturn file paths and example patterns I should follow."
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "run_in_background": true,
  "load_skills": [],
  "description": "Find denoising module test file",
  "prompt": "Find the existing test file for video denoising if it exists. Look for tests/unit/test_video_denoising.py or similar files. I need to see what tests already exist and what coverage gaps there are. Return the full content of any existing test files."
}
Let me read the denoising module files to understand what needs to be tested, and check the background agents' output:

🔧 Tool: background_output
Input: {
  "task_id": "bg_0f5c8147"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/exceptions.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/selector.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/conftest.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review existing test coverage and identify gaps",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Write tests for NoiseLevelMode enum",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for VideoDenoisingPipelineConfig",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for FrameBufferError exception",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for InferenceError with attempted_models/original_exceptions",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for selector fallback behavior",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for _UINT8_MAX_VALUE constant",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Write tests for preload_models functionality",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Run tests and verify coverage",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_2923b67d"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/denoising/config.py"
}
Now I have a clear picture. Let me update the test file to add missing test coverage:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review existing test coverage and identify gaps",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Write tests for NoiseLevelMode enum",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Write tests for VideoDenoisingPipelineConfig",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for FrameBufferError exception",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for InferenceError with attempted_models/original_exceptions",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for selector fallback behavior",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write tests for _UINT8_MAX_VALUE constant",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Write tests for preload_models functionality",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Run tests and verify coverage",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py"
}
Now let me add comprehensive test coverage by editing the test file:

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py",
  "edits": [
    {
      "end": "32#JQ|",
      "lines": "from video2d3d.denoising import (\n    _UINT8_MAX_VALUE,\n    BasicVSRPlusPlusConfig,\n    BasicVSRPlusPlusDenoiser,\n    DenoiserModelType,\n    FastDVDNetConfig,\n    FastDVDNetDenoiser,\n    FrameBufferError,\n    InferenceError,\n    ModelLoadError,\n    NoiseLevelMode,\n    PretrainedModelError,\n    UnsupportedModelError,\n    VideoDenoiserConfig,\n    VideoDenoiserSelector,\n    VideoDenoisingError,\n    VideoDenoisingPipelineConfig,\n    create_video_denoiser,\n    denoise_frames_auto,\n)",
      "op": "replace",
      "pos": "18#VR|"
    },
    {
      "end": "34#SX|",
      "lines": "from video2d3d.denoising.basicvsr_plusplus import BasicVSRPlusPlusModel\nfrom video2d3d.denoising.fastdvdnet import FastDVDNetModel\n\n\nclass TestNoiseLevelMode:\n    \"\"\"Tests for NoiseLevelMode enum.\"\"\"\n\n    def test_mode_values(self) -> None:\n        \"\"\"Test NoiseLevelMode enum values.\"\"\"\n        assert NoiseLevelMode.FIXED.value == \"fixed\"\n        assert NoiseLevelMode.ESTIMATED.value == \"estimated\"\n        assert NoiseLevelMode.BLIND.value == \"blind\"\n\n    def test_mode_count(self) -> None:\n        \"\"\"Test that all expected modes exist.\"\"\"\n        modes = list(NoiseLevelMode)\n        assert len(modes) == 3\n",
      "op": "replace",
      "pos": "30#XW|"
    },
    {
      "end": "108#BM|",
      "lines": "    def test_path_conversion(self) -> None:\n        \"\"\"Test that pretrained_model string is converted to Path.\"\"\"\n        config = FastDVDNetConfig(pretrained_model=\"/path/to/model.pt\")\n        assert isinstance(config.pretrained_model, Path)\n\n    def test_even_num_frames_warning(self) -> None:\n        \"\"\"Test that even num_input_frames triggers a warning.\"\"\"\n        import warnings\n\n        with warnings.catch_warnings(record=True) as w:\n            warnings.simplefilter(\"always\")\n            FastDVDNetConfig(num_input_frames=4)\n            assert len(w) == 1\n            assert \"should be odd\" in str(w[0].message)\n",
      "op": "replace",
      "pos": "105#VT|"
    },
    {
      "end": "143#RS|",
      "lines": "    def test_invalid_scale(self) -> None:\n        \"\"\"Test that invalid scale raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"scale must be >= 1\"):\n            BasicVSRPlusPlusConfig(scale=0)\n\n    def test_path_conversion(self) -> None:\n        \"\"\"Test that pretrained_model string is converted to Path.\"\"\"\n        config = BasicVSRPlusPlusConfig(pretrained_model=\"/path/to/model.pt\")\n        assert isinstance(config.pretrained_model, Path)\n",
      "op": "replace",
      "pos": "138#JY|"
    },
    {
      "end": "175#BN|",
      "lines": "    def test_invalid_output_dtype(self) -> None:\n        \"\"\"Test that invalid output_dtype raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid output_dtype\"):\n            VideoDenoiserConfig(output_dtype=\"invalid\")\n\n    def test_valid_output_dtypes(self) -> None:\n        \"\"\"Test that valid output_dtypes are accepted.\"\"\"\n        for dtype in [\"float32\", \"float64\", \"uint8\", \"uint16\"]:\n            config = VideoDenoiserConfig(output_dtype=dtype)\n            assert config.output_dtype == dtype\n\n    def test_cache_dir_path_conversion(self) -> None:\n        \"\"\"Test that cache_dir string is converted to Path.\"\"\"\n        config = VideoDenoiserConfig(cache_dir=\"/path/to/cache\")\n        assert isinstance(config.cache_dir, Path)\n\n    def test_fallback_chain_from_strings(self) -> None:\n        \"\"\"Test that fallback_chain strings are converted to enums.\"\"\"\n        config = VideoDenoiserConfig(fallback_chain=[\"fastdvdnet\", \"basicvsr_plusplus\"])\n        assert config.fallback_chain[0] == DenoiserModelType.FASTDVDNET\n        assert config.fallback_chain[1] == DenoiserModelType.BASICVSR_PLUSPLUS\n\n\nclass TestVideoDenoisingPipelineConfig:\n    \"\"\"Tests for VideoDenoisingPipelineConfig.\"\"\"\n\n    def test_default_values(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = VideoDenoisingPipelineConfig()\n        assert config.buffer_size == 30\n        assert config.overlap == 2\n        assert config.progress_callback is None\n        assert config.enable_profiling is False\n\n    def test_custom_values(self) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        callback = lambda current, total: None\n        config = VideoDenoisingPipelineConfig(\n            buffer_size=60,\n            overlap=5,\n            progress_callback=callback,\n            enable_profiling=True,\n        )\n        assert config.buffer_size == 60\n        assert config.overlap == 5\n        assert config.progress_callback is callback\n        assert config.enable_profiling is True\n\n    def test_invalid_buffer_size(self) -> None:\n        \"\"\"Test that invalid buffer_size raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"buffer_size must be >= 1\"):\n            VideoDenoisingPipelineConfig(buffer_size=0)\n\n    def test_invalid_overlap(self) -> None:\n        \"\"\"Test that negative overlap raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"overlap must be >= 0\"):\n            VideoDenoisingPipelineConfig(overlap=-1)\n\n\nclass TestConstants:\n    \"\"\"Tests for module constants.\"\"\"\n\n    def test_uint8_max_value(self) -> None:\n        \"\"\"Test _UINT8_MAX_VALUE constant.\"\"\"\n        assert _UINT8_MAX_VALUE == 255.0\n        assert isinstance(_UINT8_MAX_VALUE, float)\n",
      "op": "replace",
      "pos": "170#WS|"
    },
    {
      "end": "280#NB|",
      "lines": "    def test_switch_model(self) -> None:\n        \"\"\"Test model switching.\"\"\"\n        selector = VideoDenoiserSelector()\n        success = selector.switch_model(DenoiserModelType.FASTDVDNET)\n        assert success is True\n\n    def test_switch_model_from_string(self) -> None:\n        \"\"\"Test model switching using string.\"\"\"\n        selector = VideoDenoiserSelector()\n        success = selector.switch_model(\"fastdvdnet\")\n        assert success is True\n\n    def test_get_available_models_initially_empty(self) -> None:\n        \"\"\"Test that available models is initially empty.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.get_available_models() == []\n\n    def test_close_releases_resources(self) -> None:\n        \"\"\"Test that close() releases resources.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n        selector.close()\n        assert selector.get_available_models() == []\n\n    def test_denoise_frame_single(self) -> None:\n        \"\"\"Test denoising a single frame.\"\"\"\n        np.random.seed(42)\n        frame = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frame(frame)\n        assert result.shape == frame.shape\n\n    def test_denoise_frame_with_context(self) -> None:\n        \"\"\"Test denoising a single frame with temporal context.\"\"\"\n        np.random.seed(42)\n        frames = [(np.random.rand(64, 64, 3) * 255).astype(np.uint8) for _ in range(5)]\n        center_frame = frames[2]\n        context_frames = frames\n\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frame(center_frame, context_frames=context_frames)\n        assert result.shape == center_frame.shape\n\n    def test_active_model_property(self) -> None:\n        \"\"\"Test active_model property.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.active_model is None\n\n    def test_preload_models_success(self) -> None:\n        \"\"\"Test preload_models returns results.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n        # Preload models with fallback enabled but not actually loading\n        results = selector.preload_models([DenoiserModelType.NONE])\n        # NONE is skipped, so empty results\n        assert results == {}\n",
      "op": "replace",
      "pos": "272#SR|"
    },
    {
      "end": "315#RN|",
      "lines": "    def test_inference_error(self) -> None:\n        \"\"\"Test InferenceError creation.\"\"\"\n        error = InferenceError(\n            \"Inference failed\",\n            model_name=\"test\",\n            device=\"cpu\",\n        )\n        assert \"Inference failed\" in str(error)\n\n    def test_inference_error_with_attempted_models(self) -> None:\n        \"\"\"Test InferenceError with attempted_models attribute.\"\"\"\n        error = InferenceError(\n            \"All models failed\",\n            attempted_models=[\"fastdvdnet\", \"basicvsr_plusplus\"],\n        )\n        assert error.attempted_models == [\"fastdvdnet\", \"basicvsr_plusplus\"]\n        assert error.original_exceptions == []\n\n    def test_inference_error_with_original_exceptions(self) -> None:\n        \"\"\"Test InferenceError with original_exceptions attribute.\"\"\"\n        exc1 = ValueError(\"Error 1\")\n        exc2 = RuntimeError(\"Error 2\")\n        error = InferenceError(\n            \"All models failed\",\n            attempted_models=[\"fastdvdnet\"],\n            original_exceptions=[exc1, exc2],\n        )\n        assert error.attempted_models == [\"fastdvdnet\"]\n        assert error.original_exceptions == [exc1, exc2]\n\n    def test_frame_buffer_error(self) -> None:\n        \"\"\"Test FrameBufferError creation with attributes.\"\"\"\n        error = FrameBufferError(\n            \"Buffer underflow\",\n            buffer_size=5,\n            required_frames=10,\n        )\n        assert \"Buffer underflow\" in str(error)\n        assert error.buffer_size == 5\n        assert error.required_frames == 10\n\n    def test_frame_buffer_error_defaults(self) -> None:\n        \"\"\"Test FrameBufferError with default attributes.\"\"\"\n        error = FrameBufferError(\"Buffer error\")\n        assert error.buffer_size is None\n        assert error.required_frames is None\n\n    def test_unsupported_model_error(self) -> None:\n        \"\"\"Test UnsupportedModelError creation.\"\"\"\n        error = UnsupportedModelError(\n            \"Model not supported\",\n            model_name=\"unknown_model\",\n        )\n        assert \"Model not supported\" in str(error)\n        assert error.model_name == \"unknown_model\"\n\n    def test_pretrained_model_error(self) -> None:\n        \"\"\"Test PretrainedModelError creation.\"\"\"\n        error = PretrainedModelError(\n            \"Failed to download\",\n            model_name=\"fastdvdnet\",\n        )\n        assert \"Failed to download\" in str(error)\n        assert error.model_name == \"fastdvdnet\"\n",
      "op": "replace",
      "pos": "303#TM|"
    },
    {
      "end": "335#TT|",
      "lines": "    def test_denoise_frames_auto(self) -> None:\n        \"\"\"Test denoise_frames_auto function.\"\"\"\n        np.random.seed(42)\n        frames = [(np.random.rand(32, 32, 3) * 255).astype(np.uint8) for _ in range(5)]\n        result = denoise_frames_auto(frames, model_type=\"none\")\n        assert len(result) == len(frames)\n\n    def test_create_video_denoiser_with_device(self) -> None:\n        \"\"\"Test create_video_denoiser with device parameter.\"\"\"\n        denoiser = create_video_denoiser(\n            model_type=\"fastdvdnet\",\n            enabled=False,\n            device=\"cpu\",\n        )\n        assert isinstance(denoiser, VideoDenoiserSelector)\n        assert denoiser.config.device == \"cpu\"\n\n\nclass TestDenoiserModelTypeExtended:\n    \"\"\"Extended tests for DenoiserModelType enum.\"\"\"\n\n    def test_from_string_aliases(self) -> None:\n        \"\"\"Test conversion from various aliases.\"\"\"\n        # FastDVDNet aliases\n        assert DenoiserModelType.from_string(\"fast_dvdnet\") == DenoiserModelType.FASTDVDNET\n        assert DenoiserModelType.from_string(\"fast-dvdnet\") == DenoiserModelType.FASTDVDNET\n\n        # BasicVSR++ aliases\n        assert DenoiserModelType.from_string(\"basicvsr++\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert DenoiserModelType.from_string(\"basicvsr_pp\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert (\n            DenoiserModelType.from_string(\"basicvsrplusplus\")\n            == DenoiserModelType.BASICVSR_PLUSPLUS\n        )\n\n        # NONE aliases\n        assert DenoiserModelType.from_string(\"disabled\") == DenoiserModelType.NONE\n        assert DenoiserModelType.from_string(\"off\") == DenoiserModelType.NONE\n\n    def test_basicvsr_model_type(self) -> None:\n        \"\"\"Test BASICVSR model type.\"\"\"\n        assert DenoiserModelType.BASICVSR.value == \"basicvsr\"\n        assert DenoiserModelType.from_string(\"basicvsr\") == DenoiserModelType.BASICVSR\n        assert DenoiserModelType.BASICVSR.is_enabled is True\n        assert DenoiserModelType.BASICVSR.requires_temporal_context is True\n",
      "op": "replace",
      "pos": "325#KM|"
    }
  ]
}
Let me re-read the test file and make the edits with the correct line references:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py",
  "edits": [
    {
      "end": "32#JQ|",
      "lines": "from video2d3d.denoising import (\n    _UINT8_MAX_VALUE,\n    BasicVSRPlusPlusConfig,\n    BasicVSRPlusPlusDenoiser,\n    DenoiserModelType,\n    FastDVDNetConfig,\n    FastDVDNetDenoiser,\n    FrameBufferError,\n    InferenceError,\n    ModelLoadError,\n    NoiseLevelMode,\n    PretrainedModelError,\n    UnsupportedModelError,\n    VideoDenoiserConfig,\n    VideoDenoiserSelector,\n    VideoDenoisingError,\n    VideoDenoisingPipelineConfig,\n    create_video_denoiser,\n    denoise_frames_auto,\n)",
      "op": "replace",
      "pos": "18#VR|"
    },
    {
      "end": "34#SX|",
      "lines": "from video2d3d.denoising.basicvsr_plusplus import BasicVSRPlusPlusModel\nfrom video2d3d.denoising.fastdvdnet import FastDVDNetModel\n\n\nclass TestNoiseLevelMode:\n    \"\"\"Tests for NoiseLevelMode enum.\"\"\"\n\n    def test_mode_values(self) -> None:\n        \"\"\"Test NoiseLevelMode enum values.\"\"\"\n        assert NoiseLevelMode.FIXED.value == \"fixed\"\n        assert NoiseLevelMode.ESTIMATED.value == \"estimated\"\n        assert NoiseLevelMode.BLIND.value == \"blind\"\n\n    def test_mode_count(self) -> None:\n        \"\"\"Test that all expected modes exist.\"\"\"\n        modes = list(NoiseLevelMode)\n        assert len(modes) == 3\n",
      "op": "replace",
      "pos": "30#XW|"
    },
    {
      "end": "109#BP|",
      "lines": "    def test_path_conversion(self) -> None:\n        \"\"\"Test that pretrained_model string is converted to Path.\"\"\"\n        config = FastDVDNetConfig(pretrained_model=\"/path/to/model.pt\")\n        assert isinstance(config.pretrained_model, Path)\n\n    def test_even_num_frames_warning(self) -> None:\n        \"\"\"Test that even num_input_frames triggers a warning.\"\"\"\n        import warnings\n\n        with warnings.catch_warnings(record=True) as w:\n            warnings.simplefilter(\"always\")\n            FastDVDNetConfig(num_input_frames=4)\n            assert len(w) == 1\n            assert \"should be odd\" in str(w[0].message)\n",
      "op": "replace",
      "pos": "105#VT|"
    },
    {
      "end": "142#HQ|",
      "lines": "    def test_invalid_scale(self) -> None:\n        \"\"\"Test that invalid scale raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"scale must be >= 1\"):\n            BasicVSRPlusPlusConfig(scale=0)\n\n    def test_path_conversion(self) -> None:\n        \"\"\"Test that pretrained_model string is converted to Path.\"\"\"\n        config = BasicVSRPlusPlusConfig(pretrained_model=\"/path/to/model.pt\")\n        assert isinstance(config.pretrained_model, Path)\n",
      "op": "replace",
      "pos": "138#JY|"
    },
    {
      "end": "175#BN|",
      "lines": "    def test_invalid_output_dtype(self) -> None:\n        \"\"\"Test that invalid output_dtype raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid output_dtype\"):\n            VideoDenoiserConfig(output_dtype=\"invalid\")\n\n    def test_valid_output_dtypes(self) -> None:\n        \"\"\"Test that valid output_dtypes are accepted.\"\"\"\n        for dtype in [\"float32\", \"float64\", \"uint8\", \"uint16\"]:\n            config = VideoDenoiserConfig(output_dtype=dtype)\n            assert config.output_dtype == dtype\n\n    def test_cache_dir_path_conversion(self) -> None:\n        \"\"\"Test that cache_dir string is converted to Path.\"\"\"\n        config = VideoDenoiserConfig(cache_dir=\"/path/to/cache\")\n        assert isinstance(config.cache_dir, Path)\n\n    def test_fallback_chain_from_strings(self) -> None:\n        \"\"\"Test that fallback_chain strings are converted to enums.\"\"\"\n        config = VideoDenoiserConfig(fallback_chain=[\"fastdvdnet\", \"basicvsr_plusplus\"])\n        assert config.fallback_chain[0] == DenoiserModelType.FASTDVDNET\n        assert config.fallback_chain[1] == DenoiserModelType.BASICVSR_PLUSPLUS\n\n\nclass TestVideoDenoisingPipelineConfig:\n    \"\"\"Tests for VideoDenoisingPipelineConfig.\"\"\"\n\n    def test_default_values(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = VideoDenoisingPipelineConfig()\n        assert config.buffer_size == 30\n        assert config.overlap == 2\n        assert config.progress_callback is None\n        assert config.enable_profiling is False\n\n    def test_custom_values(self) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n\n        def callback(current: int, total: int) -> None:\n            pass\n\n        config = VideoDenoisingPipelineConfig(\n            buffer_size=60,\n            overlap=5,\n            progress_callback=callback,\n            enable_profiling=True,\n        )\n        assert config.buffer_size == 60\n        assert config.overlap == 5\n        assert config.progress_callback is callback\n        assert config.enable_profiling is True\n\n    def test_invalid_buffer_size(self) -> None:\n        \"\"\"Test that invalid buffer_size raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"buffer_size must be >= 1\"):\n            VideoDenoisingPipelineConfig(buffer_size=0)\n\n    def test_invalid_overlap(self) -> None:\n        \"\"\"Test that negative overlap raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"overlap must be >= 0\"):\n            VideoDenoisingPipelineConfig(overlap=-1)\n\n\nclass TestConstants:\n    \"\"\"Tests for module constants.\"\"\"\n\n    def test_uint8_max_value(self) -> None:\n        \"\"\"Test _UINT8_MAX_VALUE constant.\"\"\"\n        assert _UINT8_MAX_VALUE == 255.0\n        assert isinstance(_UINT8_MAX_VALUE, float)\n",
      "op": "replace",
      "pos": "170#WS|"
    },
    {
      "end": "278#NB|",
      "lines": "    def test_switch_model(self) -> None:\n        \"\"\"Test model switching.\"\"\"\n        selector = VideoDenoiserSelector()\n        success = selector.switch_model(DenoiserModelType.FASTDVDNET)\n        assert success is True\n\n    def test_switch_model_from_string(self) -> None:\n        \"\"\"Test model switching using string.\"\"\"\n        selector = VideoDenoiserSelector()\n        success = selector.switch_model(\"fastdvdnet\")\n        assert success is True\n\n    def test_get_available_models_initially_empty(self) -> None:\n        \"\"\"Test that available models is initially empty.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.get_available_models() == []\n\n    def test_close_releases_resources(self) -> None:\n        \"\"\"Test that close() releases resources.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n        selector.close()\n        assert selector.get_available_models() == []\n\n    def test_denoise_frame_single(self) -> None:\n        \"\"\"Test denoising a single frame.\"\"\"\n        np.random.seed(42)\n        frame = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frame(frame)\n        assert result.shape == frame.shape\n\n    def test_denoise_frame_with_context(self) -> None:\n        \"\"\"Test denoising a single frame with temporal context.\"\"\"\n        np.random.seed(42)\n        frames = [(np.random.rand(64, 64, 3) * 255).astype(np.uint8) for _ in range(5)]\n        center_frame = frames[2]\n        context_frames = frames\n\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frame(center_frame, context_frames=context_frames)\n        assert result.shape == center_frame.shape\n\n    def test_active_model_property(self) -> None:\n        \"\"\"Test active_model property.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.active_model is None\n\n    def test_preload_models_none_skipped(self) -> None:\n        \"\"\"Test preload_models skips NONE model type.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n        results = selector.preload_models([DenoiserModelType.NONE])\n        # NONE is skipped, so empty results\n        assert results == {}\n",
      "op": "replace",
      "pos": "272#SR|"
    },
    {
      "end": "311#RN|",
      "lines": "    def test_inference_error(self) -> None:\n        \"\"\"Test InferenceError creation.\"\"\"\n        error = InferenceError(\n            \"Inference failed\",\n            model_name=\"test\",\n            device=\"cpu\",\n        )\n        assert \"Inference failed\" in str(error)\n\n    def test_inference_error_with_attempted_models(self) -> None:\n        \"\"\"Test InferenceError with attempted_models attribute.\"\"\"\n        error = InferenceError(\n            \"All models failed\",\n            attempted_models=[\"fastdvdnet\", \"basicvsr_plusplus\"],\n        )\n        assert error.attempted_models == [\"fastdvdnet\", \"basicvsr_plusplus\"]\n        assert error.original_exceptions == []\n\n    def test_inference_error_with_original_exceptions(self) -> None:\n        \"\"\"Test InferenceError with original_exceptions attribute.\"\"\"\n        exc1 = ValueError(\"Error 1\")\n        exc2 = RuntimeError(\"Error 2\")\n        error = InferenceError(\n            \"All models failed\",\n            attempted_models=[\"fastdvdnet\"],\n            original_exceptions=[exc1, exc2],\n        )\n        assert error.attempted_models == [\"fastdvdnet\"]\n        assert error.original_exceptions == [exc1, exc2]\n\n    def test_frame_buffer_error(self) -> None:\n        \"\"\"Test FrameBufferError creation with attributes.\"\"\"\n        error = FrameBufferError(\n            \"Buffer underflow\",\n            buffer_size=5,\n            required_frames=10,\n        )\n        assert \"Buffer underflow\" in str(error)\n        assert error.buffer_size == 5\n        assert error.required_frames == 10\n\n    def test_frame_buffer_error_defaults(self) -> None:\n        \"\"\"Test FrameBufferError with default attributes.\"\"\"\n        error = FrameBufferError(\"Buffer error\")\n        assert error.buffer_size is None\n        assert error.required_frames is None\n\n    def test_unsupported_model_error(self) -> None:\n        \"\"\"Test UnsupportedModelError creation.\"\"\"\n        error = UnsupportedModelError(\n            \"Model not supported\",\n            model_name=\"unknown_model\",\n        )\n        assert \"Model not supported\" in str(error)\n        assert error.model_name == \"unknown_model\"\n\n    def test_pretrained_model_error(self) -> None:\n        \"\"\"Test PretrainedModelError creation.\"\"\"\n        error = PretrainedModelError(\n            \"Failed to download\",\n            model_name=\"fastdvdnet\",\n        )\n        assert \"Failed to download\" in str(error)\n        assert error.model_name == \"fastdvdnet\"\n",
      "op": "replace",
      "pos": "303#TM|"
    },
    {
      "end": "331#TT|",
      "lines": "    def test_denoise_frames_auto(self) -> None:\n        \"\"\"Test denoise_frames_auto function.\"\"\"\n        np.random.seed(42)\n        frames = [(np.random.rand(32, 32, 3) * 255).astype(np.uint8) for _ in range(5)]\n        result = denoise_frames_auto(frames, model_type=\"none\")\n        assert len(result) == len(frames)\n\n    def test_create_video_denoiser_with_device(self) -> None:\n        \"\"\"Test create_video_denoiser with device parameter.\"\"\"\n        denoiser = create_video_denoiser(\n            model_type=\"fastdvdnet\",\n            enabled=False,\n            device=\"cpu\",\n        )\n        assert isinstance(denoiser, VideoDenoiserSelector)\n        assert denoiser.config.device == \"cpu\"\n\n\nclass TestDenoiserModelTypeExtended:\n    \"\"\"Extended tests for DenoiserModelType enum.\"\"\"\n\n    def test_from_string_aliases(self) -> None:\n        \"\"\"Test conversion from various aliases.\"\"\"\n        # FastDVDNet aliases\n        assert DenoiserModelType.from_string(\"fast_dvdnet\") == DenoiserModelType.FASTDVDNET\n        assert DenoiserModelType.from_string(\"fast-dvdnet\") == DenoiserModelType.FASTDVDNET\n\n        # BasicVSR++ aliases\n        assert DenoiserModelType.from_string(\"basicvsr++\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert DenoiserModelType.from_string(\"basicvsr_pp\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert (\n            DenoiserModelType.from_string(\"basicvsrplusplus\")\n            == DenoiserModelType.BASICVSR_PLUSPLUS\n        )\n\n        # NONE aliases\n        assert DenoiserModelType.from_string(\"disabled\") == DenoiserModelType.NONE\n        assert DenoiserModelType.from_string(\"off\") == DenoiserModelType.NONE\n\n    def test_basicvsr_model_type(self) -> None:\n        \"\"\"Test BASICVSR model type.\"\"\"\n        assert DenoiserModelType.BASICVSR.value == \"basicvsr\"\n        assert DenoiserModelType.from_string(\"basicvsr\") == DenoiserModelType.BASICVSR\n        assert DenoiserModelType.BASICVSR.is_enabled is True\n        assert DenoiserModelType.BASICVSR.requires_temporal_context is True\n",
      "op": "replace",
      "pos": "325#KM|"
    }
  ]
}
Let me rewrite the test file completely to add all the missing tests:

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_video_denoising.py",
  "content": "\"\"\"Unit tests for video denoising module.\n\nTests cover:\n- Configuration classes\n- Exception handling\n- FastDVDNet denoiser\n- BasicVSR++ denoiser\n- VideoDenoiserSelector\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom pathlib import Path\n\nimport numpy as np\nimport pytest\n\nfrom video2d3d.denoising import (\n    _UINT8_MAX_VALUE,\n    BasicVSRPlusPlusConfig,\n    DenoiserModelType,\n    FastDVDNetConfig,\n    FrameBufferError,\n    InferenceError,\n    ModelLoadError,\n    NoiseLevelMode,\n    PretrainedModelError,\n    UnsupportedModelError,\n    VideoDenoiserConfig,\n    VideoDenoiserSelector,\n    VideoDenoisingError,\n    VideoDenoisingPipelineConfig,\n    create_video_denoiser,\n    denoise_frames_auto,\n)\nfrom video2d3d.denoising.basicvsr_plusplus import BasicVSRPlusPlusModel\nfrom video2d3d.denoising.fastdvdnet import FastDVDNetModel\n\n\nclass TestNoiseLevelMode:\n    \"\"\"Tests for NoiseLevelMode enum.\"\"\"\n\n    def test_mode_values(self) -> None:\n        \"\"\"Test NoiseLevelMode enum values.\"\"\"\n        assert NoiseLevelMode.FIXED.value == \"fixed\"\n        assert NoiseLevelMode.ESTIMATED.value == \"estimated\"\n        assert NoiseLevelMode.BLIND.value == \"blind\"\n\n    def test_mode_count(self) -> None:\n        \"\"\"Test that all expected modes exist.\"\"\"\n        modes = list(NoiseLevelMode)\n        assert len(modes) == 3\n\n\nclass TestDenoiserModelType:\n    \"\"\"Tests for DenoiserModelType enum.\"\"\"\n\n    def test_from_string_valid_names(self) -> None:\n        \"\"\"Test conversion from string to enum for valid names.\"\"\"\n        assert DenoiserModelType.from_string(\"fastdvdnet\") == DenoiserModelType.FASTDVDNET\n        assert DenoiserModelType.from_string(\"FastDVDNet\") == DenoiserModelType.FASTDVDNET\n        assert DenoiserModelType.from_string(\"FASTDVDNET\") == DenoiserModelType.FASTDVDNET\n        assert DenoiserModelType.from_string(\"fast-dvdnet\") == DenoiserModelType.FASTDVDNET\n        assert (\n            DenoiserModelType.from_string(\"basicvsr_plusplus\")\n            == DenoiserModelType.BASICVSR_PLUSPLUS\n        )\n        assert DenoiserModelType.from_string(\"basicvsr++\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert DenoiserModelType.from_string(\"none\") == DenoiserModelType.NONE\n\n    def test_from_string_invalid_name(self) -> None:\n        \"\"\"Test that invalid model names raise ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Unknown denoising model\"):\n            DenoiserModelType.from_string(\"invalid_model\")\n\n    def test_is_enabled(self) -> None:\n        \"\"\"Test is_enabled property.\"\"\"\n        assert DenoiserModelType.FASTDVDNET.is_enabled is True\n        assert DenoiserModelType.NONE.is_enabled is False\n\n    def test_requires_temporal_context(self) -> None:\n        \"\"\"Test requires_temporal_context property.\"\"\"\n        assert DenoiserModelType.FASTDVDNET.requires_temporal_context is True\n        assert DenoiserModelType.BASICVSR_PLUSPLUS.requires_temporal_context is True\n        assert DenoiserModelType.NONE.requires_temporal_context is False\n\n    def test_from_string_aliases(self) -> None:\n        \"\"\"Test conversion from various aliases.\"\"\"\n        # FastDVDNet aliases\n        assert DenoiserModelType.from_string(\"fast_dvdnet\") == DenoiserModelType.FASTDVDNET\n        assert DenoiserModelType.from_string(\"fast-dvdnet\") == DenoiserModelType.FASTDVDNET\n\n        # BasicVSR++ aliases\n        assert DenoiserModelType.from_string(\"basicvsr++\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert DenoiserModelType.from_string(\"basicvsr_pp\") == DenoiserModelType.BASICVSR_PLUSPLUS\n        assert (\n            DenoiserModelType.from_string(\"basicvsrplusplus\")\n            == DenoiserModelType.BASICVSR_PLUSPLUS\n        )\n\n        # NONE aliases\n        assert DenoiserModelType.from_string(\"disabled\") == DenoiserModelType.NONE\n        assert DenoiserModelType.from_string(\"off\") == DenoiserModelType.NONE\n\n    def test_basicvsr_model_type(self) -> None:\n        \"\"\"Test BASICVSR model type.\"\"\"\n        assert DenoiserModelType.BASICVSR.value == \"basicvsr\"\n        assert DenoiserModelType.from_string(\"basicvsr\") == DenoiserModelType.BASICVSR\n        assert DenoiserModelType.BASICVSR.is_enabled is True\n        assert DenoiserModelType.BASICVSR.requires_temporal_context is True\n\n\nclass TestFastDVDNetConfig:\n    \"\"\"Tests for FastDVDNetConfig.\"\"\"\n\n    def test_default_values(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = FastDVDNetConfig()\n        assert config.num_input_frames == 5\n        assert config.noise_level == 30.0\n        assert config.noise_level_mode == \"blind\"\n        assert config.auto_download is True\n        assert config.pretrained_model is None\n\n    def test_custom_values(self) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        config = FastDVDNetConfig(\n            num_input_frames=7,\n            noise_level=50.0,\n            noise_level_mode=\"fixed\",\n        )\n        assert config.num_input_frames == 7\n        assert config.noise_level == 50.0\n        assert config.noise_level_mode == \"fixed\"\n\n    def test_invalid_num_frames(self) -> None:\n        \"\"\"Test that invalid num_input_frames raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"num_input_frames must be >= 1\"):\n            FastDVDNetConfig(num_input_frames=0)\n\n    def test_invalid_noise_level(self) -> None:\n        \"\"\"Test that invalid noise_level raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"noise_level must be positive\"):\n            FastDVDNetConfig(noise_level=0)\n\n    def test_invalid_noise_level_mode(self) -> None:\n        \"\"\"Test that invalid noise_level_mode raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid noise_level_mode\"):\n            FastDVDNetConfig(noise_level_mode=\"invalid\")\n\n    def test_path_conversion(self) -> None:\n        \"\"\"Test that pretrained_model string is converted to Path.\"\"\"\n        config = FastDVDNetConfig(pretrained_model=\"/path/to/model.pt\")\n        assert isinstance(config.pretrained_model, Path)\n\n    def test_even_num_frames_warning(self) -> None:\n        \"\"\"Test that even num_input_frames triggers a warning.\"\"\"\n        import warnings\n\n        with warnings.catch_warnings(record=True) as w:\n            warnings.simplefilter(\"always\")\n            FastDVDNetConfig(num_input_frames=4)\n            assert len(w) == 1\n            assert \"should be odd\" in str(w[0].message)\n\n\nclass TestBasicVSRPlusPlusConfig:\n    \"\"\"Tests for BasicVSRPlusPlusConfig.\"\"\"\n\n    def test_default_values(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = BasicVSRPlusPlusConfig()\n        assert config.num_input_frames == 15\n        assert config.scale == 1\n        assert config.auto_download is True\n        assert config.use_spynet is True\n\n    def test_custom_values(self) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n        config = BasicVSRPlusPlusConfig(\n            num_input_frames=30,\n            scale=4,\n            use_spynet=False,\n        )\n        assert config.num_input_frames == 30\n        assert config.scale == 4\n        assert config.use_spynet is False\n\n    def test_invalid_num_frames(self) -> None:\n        \"\"\"Test that invalid num_input_frames raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"num_input_frames must be >= 1\"):\n            BasicVSRPlusPlusConfig(num_input_frames=0)\n\n    def test_invalid_scale(self) -> None:\n        \"\"\"Test that invalid scale raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"scale must be >= 1\"):\n            BasicVSRPlusPlusConfig(scale=0)\n\n    def test_path_conversion(self) -> None:\n        \"\"\"Test that pretrained_model string is converted to Path.\"\"\"\n        config = BasicVSRPlusPlusConfig(pretrained_model=\"/path/to/model.pt\")\n        assert isinstance(config.pretrained_model, Path)\n\n\nclass TestVideoDenoiserConfig:\n    \"\"\"Tests for VideoDenoiserConfig.\"\"\"\n\n    def test_default_values(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = VideoDenoiserConfig()\n        assert config.enabled is False\n        assert config.model_type == DenoiserModelType.FASTDVDNET\n        assert config.enable_fallback is True\n        assert config.batch_size == 4\n\n    def test_from_string_model_type(self) -> None:\n        \"\"\"Test that model_type string is converted to enum.\"\"\"\n        config = VideoDenoiserConfig(model_type=\"basicvsr_plusplus\")\n        assert config.model_type == DenoiserModelType.BASICVSR_PLUSPLUS\n\n    def test_effective_model_when_disabled(self) -> None:\n        \"\"\"Test that effective_model returns NONE when disabled.\"\"\"\n        config = VideoDenoiserConfig(enabled=False, model_type=DenoiserModelType.FASTDVDNET)\n        assert config.effective_model == DenoiserModelType.NONE\n\n    def test_effective_model_when_enabled(self) -> None:\n        \"\"\"Test that effective_model returns configured model when enabled.\"\"\"\n        config = VideoDenoiserConfig(enabled=True, model_type=DenoiserModelType.FASTDVDNET)\n        assert config.effective_model == DenoiserModelType.FASTDVDNET\n\n    def test_invalid_output_dtype(self) -> None:\n        \"\"\"Test that invalid output_dtype raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"Invalid output_dtype\"):\n            VideoDenoiserConfig(output_dtype=\"invalid\")\n\n    def test_valid_output_dtypes(self) -> None:\n        \"\"\"Test that valid output_dtypes are accepted.\"\"\"\n        for dtype in [\"float32\", \"float64\", \"uint8\", \"uint16\"]:\n            config = VideoDenoiserConfig(output_dtype=dtype)\n            assert config.output_dtype == dtype\n\n    def test_cache_dir_path_conversion(self) -> None:\n        \"\"\"Test that cache_dir string is converted to Path.\"\"\"\n        config = VideoDenoiserConfig(cache_dir=\"/path/to/cache\")\n        assert isinstance(config.cache_dir, Path)\n\n    def test_fallback_chain_from_strings(self) -> None:\n        \"\"\"Test that fallback_chain strings are converted to enums.\"\"\"\n        config = VideoDenoiserConfig(fallback_chain=[\"fastdvdnet\", \"basicvsr_plusplus\"])\n        assert config.fallback_chain[0] == DenoiserModelType.FASTDVDNET\n        assert config.fallback_chain[1] == DenoiserModelType.BASICVSR_PLUSPLUS\n\n\nclass TestVideoDenoisingPipelineConfig:\n    \"\"\"Tests for VideoDenoisingPipelineConfig.\"\"\"\n\n    def test_default_values(self) -> None:\n        \"\"\"Test default configuration values.\"\"\"\n        config = VideoDenoisingPipelineConfig()\n        assert config.buffer_size == 30\n        assert config.overlap == 2\n        assert config.progress_callback is None\n        assert config.enable_profiling is False\n\n    def test_custom_values(self) -> None:\n        \"\"\"Test custom configuration values.\"\"\"\n\n        def callback(current: int, total: int) -> None:\n            pass\n\n        config = VideoDenoisingPipelineConfig(\n            buffer_size=60,\n            overlap=5,\n            progress_callback=callback,\n            enable_profiling=True,\n        )\n        assert config.buffer_size == 60\n        assert config.overlap == 5\n        assert config.progress_callback is callback\n        assert config.enable_profiling is True\n\n    def test_invalid_buffer_size(self) -> None:\n        \"\"\"Test that invalid buffer_size raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"buffer_size must be >= 1\"):\n            VideoDenoisingPipelineConfig(buffer_size=0)\n\n    def test_invalid_overlap(self) -> None:\n        \"\"\"Test that negative overlap raises ValueError.\"\"\"\n        with pytest.raises(ValueError, match=\"overlap must be >= 0\"):\n            VideoDenoisingPipelineConfig(overlap=-1)\n\n\nclass TestConstants:\n    \"\"\"Tests for module constants.\"\"\"\n\n    def test_uint8_max_value(self) -> None:\n        \"\"\"Test _UINT8_MAX_VALUE constant.\"\"\"\n        assert _UINT8_MAX_VALUE == 255.0\n        assert isinstance(_UINT8_MAX_VALUE, float)\n\n\nclass TestFastDVDNetModel:\n    \"\"\"Tests for FastDVDNetModel neural network.\"\"\"\n\n    def test_model_creation(self) -> None:\n        \"\"\"Test model can be created.\"\"\"\n        model = FastDVDNetModel(num_input_frames=5)\n        assert model.num_input_frames == 5\n        assert model.num_features == 64\n\n    def test_forward_pass_shape(self) -> None:\n        \"\"\"Test forward pass output shape.\"\"\"\n        import torch\n\n        model = FastDVDNetModel(num_input_frames=5)\n        model.eval()\n\n        # Input: (B, T*C, H, W) where T=5, C=3\n        x = torch.randn(1, 5 * 3, 64, 64)\n        with torch.no_grad():\n            output = model(x)\n\n        # Output: (B, 3, H, W)\n        assert output.shape == (1, 3, 64, 64)\n\n\nclass TestBasicVSRPlusPlusModel:\n    \"\"\"Tests for BasicVSRPlusPlusModel neural network.\"\"\"\n\n    def test_model_creation(self) -> None:\n        \"\"\"Test model can be created.\"\"\"\n        model = BasicVSRPlusPlusModel(num_feat=64, num_block=7)\n        assert model.num_feat == 64\n\n    def test_forward_pass_shape(self) -> None:\n        \"\"\"Test forward pass output shape.\"\"\"\n        import torch\n\n        model = BasicVSRPlusPlusModel(num_feat=32, num_block=3)\n        model.eval()\n\n        # Input: (B, T, C, H, W)\n        x = torch.randn(1, 3, 3, 32, 32)\n        with torch.no_grad():\n            output = model(x)\n\n        # Output: (B, T, C, H, W)\n        assert output.shape == (1, 3, 3, 32, 32)\n\n\nclass TestVideoDenoiserSelector:\n    \"\"\"Tests for VideoDenoiserSelector.\"\"\"\n\n    @pytest.fixture\n    def sample_frames(self) -> list[np.ndarray]:\n        \"\"\"Create sample test frames.\"\"\"\n        np.random.seed(42)\n        return [(np.random.rand(64, 64, 3) * 255).astype(np.uint8) for _ in range(10)]\n\n    def test_selector_creation_default(self) -> None:\n        \"\"\"Test selector creation with defaults.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.config is not None\n        assert selector.is_enabled is False  # Disabled by default\n\n    def test_selector_creation_with_config(self) -> None:\n        \"\"\"Test selector creation with custom config.\"\"\"\n        config = VideoDenoiserConfig(\n            enabled=True,\n            model_type=DenoiserModelType.FASTDVDNET,\n        )\n        selector = VideoDenoiserSelector(config=config)\n        assert selector.is_enabled is True\n\n    def test_denoise_frames_disabled(self, sample_frames: list[np.ndarray]) -> None:\n        \"\"\"Test that disabled denoiser returns frames unchanged.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frames(sample_frames)\n        assert len(result) == len(sample_frames)\n        # Frames should be unchanged\n        for _i, (original, denoised) in enumerate(zip(sample_frames, result)):\n            np.testing.assert_array_equal(original, denoised)\n\n    def test_denoise_frames_empty_input(self) -> None:\n        \"\"\"Test that empty input returns empty output.\"\"\"\n        selector = VideoDenoiserSelector()\n        result = selector.denoise_frames([])\n        assert result == []\n\n    def test_context_manager(self) -> None:\n        \"\"\"Test context manager usage.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        with VideoDenoiserSelector(config=config) as selector:\n            assert selector is not None\n\n    def test_switch_model(self) -> None:\n        \"\"\"Test model switching.\"\"\"\n        selector = VideoDenoiserSelector()\n        success = selector.switch_model(DenoiserModelType.FASTDVDNET)\n        assert success is True\n\n    def test_switch_model_from_string(self) -> None:\n        \"\"\"Test model switching using string.\"\"\"\n        selector = VideoDenoiserSelector()\n        success = selector.switch_model(\"fastdvdnet\")\n        assert success is True\n\n    def test_get_available_models_initially_empty(self) -> None:\n        \"\"\"Test that available models is initially empty.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.get_available_models() == []\n\n    def test_close_releases_resources(self) -> None:\n        \"\"\"Test that close() releases resources.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n        selector.close()\n        assert selector.get_available_models() == []\n\n    def test_denoise_frame_single(self) -> None:\n        \"\"\"Test denoising a single frame.\"\"\"\n        np.random.seed(42)\n        frame = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frame(frame)\n        assert result.shape == frame.shape\n\n    def test_denoise_frame_with_context(self) -> None:\n        \"\"\"Test denoising a single frame with temporal context.\"\"\"\n        np.random.seed(42)\n        frames = [(np.random.rand(64, 64, 3) * 255).astype(np.uint8) for _ in range(5)]\n        center_frame = frames[2]\n        context_frames = frames\n\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n\n        result = selector.denoise_frame(center_frame, context_frames=context_frames)\n        assert result.shape == center_frame.shape\n\n    def test_active_model_property(self) -> None:\n        \"\"\"Test active_model property.\"\"\"\n        selector = VideoDenoiserSelector()\n        assert selector.active_model is None\n\n    def test_preload_models_none_skipped(self) -> None:\n        \"\"\"Test preload_models skips NONE model type.\"\"\"\n        config = VideoDenoiserConfig(enabled=False)\n        selector = VideoDenoiserSelector(config=config)\n        results = selector.preload_models([DenoiserModelType.NONE])\n        # NONE is skipped, so empty results\n        assert results == {}\n\n\nclass TestExceptions:\n    \"\"\"Tests for exception classes.\"\"\"\n\n    def test_video_denoising_error(self) -> None:\n        \"\"\"Test VideoDenoisingError creation.\"\"\"\n        error = VideoDenoisingError(\n            \"Test error\",\n            model_name=\"test_model\",\n            device=\"cuda\",\n        )\n        assert str(error) == \"Test error\"\n        assert error.model_name == \"test_model\"\n        assert error.device == \"cuda\"\n\n    def test_model_load_error(self) -> None:\n        \"\"\"Test ModelLoadError creation.\"\"\"\n        original = ValueError(\"Original error\")\n        error = ModelLoadError(\n            \"Failed to load\",\n            model_name=\"test\",\n            original_exception=original,\n        )\n        assert error.original_exception == original\n\n    def test_inference_error(self) -> None:\n        \"\"\"Test InferenceError creation.\"\"\"\n        error = InferenceError(\n            \"Inference failed\",\n            model_name=\"test\",\n            device=\"cpu\",\n        )\n        assert \"Inference failed\" in str(error)\n\n    def test_inference_error_with_attempted_models(self) -> None:\n        \"\"\"Test InferenceError with attempted_models attribute.\"\"\"\n        error = InferenceError(\n            \"All models failed\",\n            attempted_models=[\"fastdvdnet\", \"basicvsr_plusplus\"],\n        )\n        assert error.attempted_models == [\"fastdvdnet\", \"basicvsr_plusplus\"]\n        assert error.original_exceptions == []\n\n    def test_inference_error_with_original_exceptions(self) -> None:\n        \"\"\"Test InferenceError with original_exceptions attribute.\"\"\"\n        exc1 = ValueError(\"Error 1\")\n        exc2 = RuntimeError(\"Error 2\")\n        error = InferenceError(\n            \"All models failed\",\n            attempted_models=[\"fastdvdnet\"],\n            original_exceptions=[exc1, exc2],\n        )\n        assert error.attempted_models == [\"fastdvdnet\"]\n        assert error.original_exceptions == [exc1, exc2]\n\n    def test_frame_buffer_error(self) -> None:\n        \"\"\"Test FrameBufferError creation with attributes.\"\"\"\n        error = FrameBufferError(\n            \"Buffer underflow\",\n            buffer_size=5,\n            required_frames=10,\n        )\n        assert \"Buffer underflow\" in str(error)\n        assert error.buffer_size == 5\n        assert error.required_frames == 10\n\n    def test_frame_buffer_error_defaults(self) -> None:\n        \"\"\"Test FrameBufferError with default attributes.\"\"\"\n        error = FrameBufferError(\"Buffer error\")\n        assert error.buffer_size is None\n        assert error.required_frames is None\n\n    def test_unsupported_model_error(self) -> None:\n        \"\"\"Test UnsupportedModelError creation.\"\"\"\n        error = UnsupportedModelError(\n            \"Model not supported\",\n            model_name=\"unknown_model\",\n        )\n        assert \"Model not supported\" in str(error)\n        assert error.model_name == \"unknown_model\"\n\n    def test_pretrained_model_error(self) -> None:\n        \"\"\"Test PretrainedModelError creation.\"\"\"\n        error = PretrainedModelError(\n            \"Failed to download\",\n            model_name=\"fastdvdnet\",\n        )\n        assert \"Failed to download\" in str(error)\n        assert error.model_name == \"fastdvdnet\"\n\n\nclass TestConvenienceFunctions:\n    \"\"\"Tests for convenience functions.\"\"\"\n\n    def test_create_video_denoiser(self) -> None:\n        \"\"\"Test create_video_denoiser function.\"\"\"\n        denoiser = create_video_denoiser(\n            model_type=\"fastdvdnet\",\n            enabled=False,\n        )\n        assert isinstance(denoiser, VideoDenoiserSelector)\n        assert denoiser.config.enabled is False\n\n    def test_denoise_frames_auto(self) -> None:\n        \"\"\"Test denoise_frames_auto function.\"\"\"\n        np.random.seed(42)\n        frames = [(np.random.rand(32, 32, 3) * 255).astype(np.uint8) for _ in range(5)]\n        result = denoise_frames_auto(frames, model_type=\"none\")\n        assert len(result) == len(frames)\n\n    def test_create_video_denoiser_with_device(self) -> None:\n        \"\"\"Test create_video_denoiser with device parameter.\"\"\"\n        denoiser = create_video_denoiser(\n            model_type=\"fastdvdnet\",\n            enabled=False,\n            device=\"cpu\",\n        )\n        assert isinstance(denoiser, VideoDenoiserSelector)\n        assert denoiser.config.device == \"cpu\"\n\n\nif __name__ == \"__main__\":\n    pytest.main([__file__, \"-v\"])\n"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review existing test coverage and identify gaps",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write tests for NoiseLevelMode enum",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write tests for VideoDenoisingPipelineConfig",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write tests for FrameBufferError exception",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write tests for InferenceError with attempted_models/original_exceptions",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write tests for selector fallback behavior",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write tests for _UINT8_MAX_VALUE constant",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Write tests for preload_models functionality",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Run tests and verify coverage",
      "priority": "high",
      "status": "in_progress"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && source .venv/bin/activate && python -m pytest tests/unit/test_video_denoising.py -v --tb=short 2>&1 | head -120",
  "description": "Run video denoising tests",
  "timeout": 120000
}
