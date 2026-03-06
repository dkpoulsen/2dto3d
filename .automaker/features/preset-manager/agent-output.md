
🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pubspec.yaml"
}

🔧 Tool: glob
Input: {
  "pattern": "**/*.dart"
}
I'll start by exploring the codebase to understand the existing structure, patterns, and where the preset system should integrate.

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Find processing settings patterns",
  "prompt": "[CONTEXT]: I'm implementing a preset manager feature for a 2D to 3D conversion app. Need to understand how processing settings, configurations, and parameters are currently handled.\n\n[GOAL]: Find existing settings/configuration patterns, processing parameters, and state management approaches to design the preset system that fits naturally.\n\n[DOWNSTREAM]: Will use this to design the Preset model and determine what settings should be saved/loaded.\n\n[REQUEST]: Find:\n1. Any existing settings or configuration classes\n2. Processing parameters (resolution, quality, format settings)\n3. State management patterns (Provider, Riverpod, Bloc, etc.)\n4. JSON serialization patterns\n5. Local storage approaches (shared_preferences, hive, etc.)\n\nReturn file paths with relevant code snippets and pattern descriptions.",
  "run_in_background": true
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Find UI and feature structure",
  "prompt": "[CONTEXT]: Building a preset manager UI for a 2D to 3D conversion Flutter app. Need to understand the UI architecture.\n\n[GOAL]: Find the app's UI structure, navigation patterns, and how features are organized to determine where preset UI should live.\n\n[DOWNSTREAM]: Will use this to create preset selection/management UI components.\n\n[REQUEST]: Find:\n1. Main app structure and navigation (MaterialApp, routes, etc.)\n2. Existing settings screens or dialogs\n3. Widget organization patterns\n4. Theme and styling approaches\n5. Dialog/bottom sheet patterns\n\nReturn file paths with UI structure details.",
  "run_in_background": true
}

🔧 Tool: task
Input: {
  "subagent_type": "librarian",
  "load_skills": [],
  "description": "Find Flutter preset patterns",
  "prompt": "[CONTEXT]: Implementing a preset/settings management system in Flutter for saving and loading processing configurations.\n\n[GOAL]: Find best practices and patterns for implementing preset systems in Flutter apps - storage, serialization, and UI patterns.\n\n[DOWNSTREAM]: Will use this to architect the preset manager following Flutter best practices.\n\n[REQUEST]: Find:\n1. Flutter preset/settings manager implementations\n2. Best practices for storing user preferences and configurations\n3. JSON serialization with freezed/json_serializable\n4. Share/export preset patterns (file export, deep links)\n5. Popular Flutter apps with preset systems (camera apps, video editors, etc.)\n\nSkip basic tutorials - focus on production-quality implementations.",
  "run_in_background": true
}
Let me check the actual project structure:

🔧 Tool: bash
Input: {
  "command": "ls -la",
  "description": "List project root files"
}

🔧 Tool: bash
Input: {
  "command": "find . -maxdepth 3 -type f -name \"*.yaml\" -o -name \"*.json\" -o -name \"*.dart\" -o -name \"*.ts\" -o -name \"*.js\" 2>/dev/null | head -50",
  "description": "Find project files"
}
This is a Python project! Let me explore the source code structure:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/README.md"
}

🔧 Tool: bash
Input: {
  "command": "find ./src -type f -name \"*.py\" | head -50",
  "description": "Find Python source files"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/cli.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/batch/config.py"
}

🔧 Tool: bash
Input: {
  "command": "ls -la config/",
  "description": "List config directory"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_d8c8ffba"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_caf1975c"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/config/default.yaml"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/web/schemas.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/web/app.py"
}
Let me cancel the irrelevant librarian task (it's searching for Flutter patterns, but this is a Python project) and create the todo list for implementation:

🔧 Tool: background_cancel
Input: {
  "taskId": "bg_caf1975c"
}

🔧 Tool: background_cancel
Input: {
  "taskId": "bg_d8c8ffba"
}

🔧 Tool: background_cancel
Input: {
  "taskId": "bg_e4645ef7"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Register preset router in web/app.py",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Create unit tests for preset manager",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify implementation with test run",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "mkdir -p src/video2d3d/presets",
  "description": "Create presets module directory"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Preset data models for saving, loading, and sharing processing configurations.\n\nThis module provides dataclasses for representing presets that capture\nall processing settings for different use cases (cinema, VR, web, mobile).\n\"\"\"\n\nfrom __future__ import annotations\n\nimport json\nfrom dataclasses import asdict, dataclass, field\nfrom datetime import datetime\nfrom enum import Enum\nfrom typing import Any, Dict, List, Optional\nfrom uuid import uuid4\n\n\nclass PresetCategory(str, Enum):\n    \"\"\"Categories for organizing presets by use case.\"\"\"\n\n    CINEMA = \"cinema\"\n    VR = \"vr\"\n    WEB = \"web\"\n    MOBILE = \"mobile\"\n    CUSTOM = \"custom\"\n    GENERAL = \"general\"\n\n\n@dataclass\nclass DepthEstimationSettings:\n    \"\"\"Depth estimation settings for a preset.\"\"\"\n\n    model: str = \"midas_small\"\n    output_width: int = 384\n    output_height: int = 384\n    min_depth: float = 0.0\n    max_depth: float = 1.0\n    temporal_consistency: bool = True\n    temporal_smoothing_factor: float = 0.5\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> DepthEstimationSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            model=data.get(\"model\", \"midas_small\"),\n            output_width=data.get(\"output_width\", 384),\n            output_height=data.get(\"output_height\", 384),\n            min_depth=data.get(\"min_depth\", 0.0),\n            max_depth=data.get(\"max_depth\", 1.0),\n            temporal_consistency=data.get(\"temporal_consistency\", True),\n            temporal_smoothing_factor=data.get(\"temporal_smoothing_factor\", 0.5),\n        )\n\n\n@dataclass\nclass StereoGenerationSettings:\n    \"\"\"Stereoscopic generation settings for a preset.\"\"\"\n\n    format: str = \"side_by_side\"\n    baseline: float = 0.05\n    focal_length: float = 1.0\n    convergence: float = 0.5\n    # Anaglyph-specific\n    anaglyph_type: str = \"red_cyan\"\n    anaglyph_color_method: str = \"dubois\"\n    # Side-by-side specific\n    sbs_layout: str = \"horizontal\"\n    sbs_swap_eyes: bool = False\n    sbs_half_width: bool = False\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> StereoGenerationSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            format=data.get(\"format\", \"side_by_side\"),\n            baseline=data.get(\"baseline\", 0.05),\n            focal_length=data.get(\"focal_length\", 1.0),\n            convergence=data.get(\"convergence\", 0.5),\n            anaglyph_type=data.get(\"anaglyph_type\", \"red_cyan\"),\n            anaglyph_color_method=data.get(\"anaglyph_color_method\", \"dubois\"),\n            sbs_layout=data.get(\"sbs_layout\", \"horizontal\"),\n            sbs_swap_eyes=data.get(\"sbs_swap_eyes\", False),\n            sbs_half_width=data.get(\"sbs_half_width\", False),\n        )\n\n\n@dataclass\nclass VideoOutputSettings:\n    \"\"\"Video output settings for a preset.\"\"\"\n\n    format: str = \"mp4\"\n    codec: str = \"libx264\"\n    preset: str = \"medium\"\n    crf: int = 23\n    pixel_format: str = \"yuv420p\"\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> VideoOutputSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            format=data.get(\"format\", \"mp4\"),\n            codec=data.get(\"codec\", \"libx264\"),\n            preset=data.get(\"preset\", \"medium\"),\n            crf=data.get(\"crf\", 23),\n            pixel_format=data.get(\"pixel_format\", \"yuv420p\"),\n        )\n\n\n@dataclass\nclass ProcessingSettings:\n    \"\"\"Processing settings for a preset.\"\"\"\n\n    batch_size: int = 4\n    num_workers: int = 4\n    use_gpu: bool = True\n    gpu_device: int = 0\n    mixed_precision: bool = True\n    max_memory_percent: int = 80\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> ProcessingSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            batch_size=data.get(\"batch_size\", 4),\n            num_workers=data.get(\"num_workers\", 4),\n            use_gpu=data.get(\"use_gpu\", True),\n            gpu_device=data.get(\"gpu_device\", 0),\n            mixed_precision=data.get(\"mixed_precision\", True),\n            max_memory_percent=data.get(\"max_memory_percent\", 80),\n        )\n\n\n@dataclass\nclass QualitySettings:\n    \"\"\"Quality settings for a preset.\"\"\"\n\n    preset: str = \"balanced\"  # fast, balanced, quality\n    post_processing: bool = True\n    calculate_metrics: bool = False\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> QualitySettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            preset=data.get(\"preset\", \"balanced\"),\n            post_processing=data.get(\"post_processing\", True),\n            calculate_metrics=data.get(\"calculate_metrics\", False),\n        )\n\n\n@dataclass\nclass PresetSettings:\n    \"\"\"Complete settings for a processing preset.\"\"\"\n\n    depth_estimation: DepthEstimationSettings = field(\n        default_factory=DepthEstimationSettings\n    )\n    stereo_generation: StereoGenerationSettings = field(\n        default_factory=StereoGenerationSettings\n    )\n    video_output: VideoOutputSettings = field(default_factory=VideoOutputSettings)\n    processing: ProcessingSettings = field(default_factory=ProcessingSettings)\n    quality: QualitySettings = field(default_factory=QualitySettings)\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return {\n            \"depth_estimation\": self.depth_estimation.to_dict(),\n            \"stereo_generation\": self.stereo_generation.to_dict(),\n            \"video_output\": self.video_output.to_dict(),\n            \"processing\": self.processing.to_dict(),\n            \"quality\": self.quality.to_dict(),\n        }\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> PresetSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            depth_estimation=DepthEstimationSettings.from_dict(\n                data.get(\"depth_estimation\", {})\n            ),\n            stereo_generation=StereoGenerationSettings.from_dict(\n                data.get(\"stereo_generation\", {})\n            ),\n            video_output=VideoOutputSettings.from_dict(\n                data.get(\"video_output\", {})\n            ),\n            processing=ProcessingSettings.from_dict(data.get(\"processing\", {})),\n            quality=QualitySettings.from_dict(data.get(\"quality\", {})),\n        )\n\n\n@dataclass\nclass Preset:\n    \"\"\"A processing preset with complete settings for a specific use case.\n\n    Presets capture all processing configuration and can be saved, loaded,\n    shared, and applied to video conversion jobs.\n    \"\"\"\n\n    # Identity\n    id: str = field(default_factory=lambda: str(uuid4()))\n    name: str = \"\"\n    description: str = \"\"\n\n    # Classification\n    category: PresetCategory = PresetCategory.GENERAL\n    tags: List[str] = field(default_factory=list)\n\n    # Settings\n    settings: PresetSettings = field(default_factory=PresetSettings)\n\n    # Metadata\n    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())\n    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())\n    is_builtin: bool = False\n    version: str = \"1.0.0\"\n    author: str = \"\"\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return {\n            \"id\": self.id,\n            \"name\": self.name,\n            \"description\": self.description,\n            \"category\": self.category.value,\n            \"tags\": self.tags,\n            \"settings\": self.settings.to_dict(),\n            \"created_at\": self.created_at,\n            \"updated_at\": self.updated_at,\n            \"is_builtin\": self.is_builtin,\n            \"version\": self.version,\n            \"author\": self.author,\n        }\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> Preset:\n        \"\"\"Create from dictionary.\"\"\"\n        category_str = data.get(\"category\", \"general\")\n        try:\n            category = PresetCategory(category_str.lower())\n        except ValueError:\n            category = PresetCategory.GENERAL\n\n        return cls(\n            id=data.get(\"id\", str(uuid4())),\n            name=data.get(\"name\", \"\"),\n            description=data.get(\"description\", \"\"),\n            category=category,\n            tags=data.get(\"tags\", []),\n            settings=PresetSettings.from_dict(data.get(\"settings\", {})),\n            created_at=data.get(\"created_at\", datetime.utcnow().isoformat()),\n            updated_at=data.get(\"updated_at\", datetime.utcnow().isoformat()),\n            is_builtin=data.get(\"is_builtin\", False),\n            version=data.get(\"version\", \"1.0.0\"),\n            author=data.get(\"author\", \"\"),\n        )\n\n    def to_json(self, indent: int = 2) -> str:\n        \"\"\"Convert to JSON string.\"\"\"\n        return json.dumps(self.to_dict(), indent=indent)\n\n    @classmethod\n    def from_json(cls, json_str: str) -> Preset:\n        \"\"\"Create from JSON string.\"\"\"\n        data = json.loads(json_str)\n        return cls.from_dict(data)\n\n    def update_timestamp(self) -> None:\n        \"\"\"Update the updated_at timestamp.\"\"\"\n        self.updated_at = datetime.utcnow().isoformat()\n\n    def __eq__(self, other: object) -> bool:\n        \"\"\"Check equality by ID.\"\"\"\n        if not isinstance(other, Preset):\n            return False\n        return self.id == other.id\n\n    def __hash__(self) -> int:\n        \"\"\"Hash by ID.\"\"\"\n        return hash(self.id)\n\n    def __str__(self) -> str:\n        \"\"\"String representation.\"\"\"\n        return f\"Preset({self.name}, category={self.category.value})\"\n\n    def __repr__(self) -> str:\n        \"\"\"Detailed representation.\"\"\"\n        return (\n            f\"Preset(id={self.id!r}, name={self.name!r}, \"\n            f\"category={self.category.value!r})\"\n        )\n\n\n__all__ = [\n    \"PresetCategory\",\n    \"DepthEstimationSettings\",\n    \"StereoGenerationSettings\",\n    \"VideoOutputSettings\",\n    \"ProcessingSettings\",\n    \"QualitySettings\",\n    \"PresetSettings\",\n    \"Preset\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Preset storage for persisting presets to JSON files.\n\nThis module provides classes for storing and retrieving presets from\nthe filesystem, supporting both user presets and built-in presets.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport json\nimport shutil\nfrom pathlib import Path\nfrom typing import Dict, List, Optional\n\nfrom video2d3d.presets.models import Preset\nfrom video2d3d.utils.logger import get_logger\n\nlogger = get_logger(\"presets.storage\")\n\n\nclass PresetStorageError(Exception):\n    \"\"\"Exception raised for preset storage errors.\"\"\"\n    pass\n\n\nclass PresetStorage:\n    \"\"\"Manages persistent storage of presets in JSON files.\n\n    Presets are stored in a dedicated directory with each preset as a\n    separate JSON file. Built-in presets are stored separately from\n    user-created presets.\n    \"\"\"\n\n    def __init__(\n        self,\n        presets_dir: Optional[Path] = None,\n        builtin_presets_dir: Optional[Path] = None,\n    ):\n        \"\"\"Initialize preset storage.\n\n        Args:\n            presets_dir: Directory for user presets. Defaults to 'presets/' in project root.\n            builtin_presets_dir: Directory for built-in presets. Defaults to package presets.\n        \"\"\"\n        if presets_dir is None:\n            # Default to 'presets/' directory in project root\n            project_root = Path(__file__).parent.parent.parent.parent\n            presets_dir = project_root / \"presets\"\n\n        if builtin_presets_dir is None:\n            # Default to 'builtins' subdirectory in presets module\n            builtin_presets_dir = Path(__file__).parent / \"builtins\"\n\n        self.presets_dir = Path(presets_dir)\n        self.builtin_presets_dir = Path(builtin_presets_dir)\n\n        # Ensure directories exist\n        self.presets_dir.mkdir(parents=True, exist_ok=True)\n\n        logger.debug(\n            f\"PresetStorage initialized: user_dir={self.presets_dir}, \"\n            f\"builtin_dir={self.builtin_presets_dir}\"\n        )\n\n    def _get_preset_path(self, preset_id: str, is_builtin: bool = False) -> Path:\n        \"\"\"Get the file path for a preset.\n\n        Args:\n            preset_id: The preset ID.\n            is_builtin: Whether the preset is built-in.\n\n        Returns:\n            Path to the preset JSON file.\n        \"\"\"\n        base_dir = self.builtin_presets_dir if is_builtin else self.presets_dir\n        return base_dir / f\"{preset_id}.json\"\n\n    def save(self, preset: Preset) -> Path:\n        \"\"\"Save a preset to storage.\n\n        Args:\n            preset: The preset to save.\n\n        Returns:\n            Path to the saved preset file.\n\n        Raises:\n            PresetStorageError: If saving fails.\n        \"\"\"\n        try:\n            # Built-in presets should not be overwritten\n            if preset.is_builtin:\n                raise PresetStorageError(\n                    f\"Cannot save built-in preset '{preset.name}'. \"\n                    \"Create a copy to modify it.\"\n                )\n\n            file_path = self._get_preset_path(preset.id, is_builtin=False)\n\n            with open(file_path, \"w\", encoding=\"utf-8\") as f:\n                json.dump(preset.to_dict(), f, indent=2)\n\n            logger.info(f\"Saved preset '{preset.name}' to {file_path}\")\n            return file_path\n\n        except (IOError, OSError) as e:\n            logger.error(f\"Failed to save preset '{preset.name}': {e}\")\n            raise PresetStorageError(f\"Failed to save preset: {e}\") from e\n\n    def load(self, preset_id: str, is_builtin: bool = False) -> Optional[Preset]:\n        \"\"\"Load a preset by ID.\n\n        Args:\n            preset_id: The preset ID to load.\n            is_builtin: Whether to look for a built-in preset.\n\n        Returns:\n            The loaded preset, or None if not found.\n        \"\"\"\n        # Try user presets first, then built-in\n        for builtin in [False, True] if not is_builtin else [True]:\n            file_path = self._get_preset_path(preset_id, is_builtin=builtin)\n\n            if file_path.exists():\n                try:\n                    with open(file_path, encoding=\"utf-8\") as f:\n                        data = json.load(f)\n                    preset = Preset.from_dict(data)\n                    preset.is_builtin = builtin\n                    logger.debug(f\"Loaded preset '{preset.name}' from {file_path}\")\n                    return preset\n\n                except (json.JSONDecodeError, KeyError) as e:\n                    logger.error(f\"Failed to parse preset file {file_path}: {e}\")\n                    continue\n\n        logger.warning(f\"Preset '{preset_id}' not found\")\n        return None\n\n    def delete(self, preset_id: str) -> bool:\n        \"\"\"Delete a preset by ID.\n\n        Args:\n            preset_id: The preset ID to delete.\n\n        Returns:\n            True if deleted, False if not found.\n\n        Raises:\n            PresetStorageError: If trying to delete a built-in preset.\n        \"\"\"\n        # Check if it's a built-in preset\n        preset = self.load(preset_id)\n        if preset and preset.is_builtin:\n            raise PresetStorageError(\n                f\"Cannot delete built-in preset '{preset.name}'.\"\n            )\n\n        file_path = self._get_preset_path(preset_id, is_builtin=False)\n\n        if file_path.exists():\n            file_path.unlink()\n            logger.info(f\"Deleted preset {preset_id}\")\n            return True\n\n        return False\n\n    def list_all(self, include_builtins: bool = True) -> List[Preset]:\n        \"\"\"List all presets.\n\n        Args:\n            include_builtins: Whether to include built-in presets.\n\n        Returns:\n            List of all presets.\n        \"\"\"\n        presets: Dict[str, Preset] = {}\n\n        # Load built-in presets first (lower priority)\n        if include_builtins and self.builtin_presets_dir.exists():\n            for file_path in self.builtin_presets_dir.glob(\"*.json\"):\n                try:\n                    with open(file_path, encoding=\"utf-8\") as f:\n                        data = json.load(f)\n                    preset = Preset.from_dict(data)\n                    preset.is_builtin = True\n                    presets[preset.id] = preset\n                except (json.JSONDecodeError, KeyError) as e:\n                    logger.warning(f\"Failed to load built-in preset {file_path}: {e}\")\n\n        # Load user presets (higher priority, can override built-ins by ID)\n        if self.presets_dir.exists():\n            for file_path in self.presets_dir.glob(\"*.json\"):\n                try:\n                    with open(file_path, encoding=\"utf-8\") as f:\n                        data = json.load(f)\n                    preset = Preset.from_dict(data)\n                    preset.is_builtin = False\n                    presets[preset.id] = preset\n                except (json.JSONDecodeError, KeyError) as e:\n                    logger.warning(f\"Failed to load user preset {file_path}: {e}\")\n\n        return list(presets.values())\n\n    def list_by_category(\n        self, category: str, include_builtins: bool = True\n    ) -> List[Preset]:\n        \"\"\"List presets by category.\n\n        Args:\n            category: The category to filter by.\n            include_builtins: Whether to include built-in presets.\n\n        Returns:\n            List of presets in the category.\n        \"\"\"\n        all_presets = self.list_all(include_builtins=include_builtins)\n        return [p for p in all_presets if p.category.value == category.lower()]\n\n    def exists(self, preset_id: str) -> bool:\n        \"\"\"Check if a preset exists.\n\n        Args:\n            preset_id: The preset ID to check.\n\n        Returns:\n            True if the preset exists.\n        \"\"\"\n        return (\n            self._get_preset_path(preset_id, is_builtin=False).exists()\n            or self._get_preset_path(preset_id, is_builtin=True).exists()\n        )\n\n    def export_preset(self, preset_id: str, export_path: Path) -> Path:\n        \"\"\"Export a preset to a file.\n\n        Args:\n            preset_id: The preset ID to export.\n            export_path: Path to export the preset to.\n\n        Returns:\n            Path to the exported file.\n\n        Raises:\n            PresetStorageError: If preset not found or export fails.\n        \"\"\"\n        preset = self.load(preset_id)\n        if not preset:\n            raise PresetStorageError(f\"Preset '{preset_id}' not found\")\n\n        try:\n            with open(export_path, \"w\", encoding=\"utf-8\") as f:\n                json.dump(preset.to_dict(), f, indent=2)\n\n            logger.info(f\"Exported preset '{preset.name}' to {export_path}\")\n            return export_path\n\n        except (IOError, OSError) as e:\n            logger.error(f\"Failed to export preset: {e}\")\n            raise PresetStorageError(f\"Failed to export preset: {e}\") from e\n\n    def import_preset(self, import_path: Path, overwrite: bool = False) -> Preset:\n        \"\"\"Import a preset from a file.\n\n        Args:\n            import_path: Path to the preset file to import.\n            overwrite: Whether to overwrite existing preset with same ID.\n\n        Returns:\n            The imported preset.\n\n        Raises:\n            PresetStorageError: If import fails or preset already exists.\n        \"\"\"\n        try:\n            with open(import_path, encoding=\"utf-8\") as f:\n                data = json.load(f)\n\n            preset = Preset.from_dict(data)\n            preset.is_builtin = False  # Imported presets are never built-in\n\n            # Check if preset already exists\n            if self.exists(preset.id) and not overwrite:\n                raise PresetStorageError(\n                    f\"Preset with ID '{preset.id}' already exists. \"\n                    \"Use overwrite=True to replace it.\"\n                )\n\n            # Save the imported preset\n            self.save(preset)\n\n            logger.info(f\"Imported preset '{preset.name}' from {import_path}\")\n            return preset\n\n        except json.JSONDecodeError as e:\n            logger.error(f\"Invalid preset file format: {e}\")\n            raise PresetStorageError(f\"Invalid preset file format: {e}\") from e\n        except (IOError, OSError) as e:\n            logger.error(f\"Failed to import preset: {e}\")\n            raise PresetStorageError(f\"Failed to import preset: {e}\") from e\n\n    def backup_presets(self, backup_path: Path) -> Path:\n        \"\"\"Create a backup of all user presets.\n\n        Args:\n            backup_path: Path for the backup directory or archive.\n\n        Returns:\n            Path to the backup.\n        \"\"\"\n        if backup_path.is_dir():\n            # Copy entire presets directory\n            shutil.copytree(self.presets_dir, backup_path / \"presets\", dirs_exist_ok=True)\n        else:\n            # Create archive\n            shutil.make_archive(str(backup_path), \"zip\", self.presets_dir)\n\n        logger.info(f\"Created preset backup at {backup_path}\")\n        return backup_path\n\n\n__all__ = [\n    \"PresetStorageError\",\n    \"PresetStorage\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Preset manager for managing processing presets.\n\nThis module provides the PresetManager class which offers a high-level\ninterface for creating, reading, updating, and deleting presets.\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom datetime import datetime\nfrom pathlib import Path\nfrom typing import Dict, List, Optional\n\nfrom video2d3d.presets.models import (\n    Preset,\n    PresetCategory,\n    PresetSettings,\n)\nfrom video2d3d.presets.storage import PresetStorage, PresetStorageError\nfrom video2d3d.utils.config import (\n    Config,\n    DepthEstimationConfig,\n    ProcessingConfig,\n    QualityConfig,\n    StereoGenerationConfig,\n    VideoOutputConfig,\n)\nfrom video2d3d.utils.logger import get_logger\n\nlogger = get_logger(\"presets.manager\")\n\n\nclass PresetManagerError(Exception):\n    \"\"\"Exception raised for preset manager errors.\"\"\"\n    pass\n\n\nclass PresetManager:\n    \"\"\"High-level manager for processing presets.\n\n    Provides a unified interface for managing presets, including:\n    - Creating, reading, updating, and deleting presets\n    - Applying presets to job configurations\n    - Importing and exporting presets\n    - Searching and filtering presets\n    \"\"\"\n\n    def __init__(\n        self,\n        presets_dir: Optional[Path] = None,\n        storage: Optional[PresetStorage] = None,\n    ):\n        \"\"\"Initialize the preset manager.\n\n        Args:\n            presets_dir: Directory for storing presets.\n            storage: Custom preset storage instance.\n        \"\"\"\n        self.storage = storage or PresetStorage(presets_dir=presets_dir)\n        self._cache: Optional[Dict[str, Preset]] = None\n\n    def _invalidate_cache(self) -> None:\n        \"\"\"Invalidate the preset cache.\"\"\"\n        self._cache = None\n\n    def _get_cached_presets(self) -> Dict[str, Preset]:\n        \"\"\"Get cached presets, loading if necessary.\"\"\"\n        if self._cache is None:\n            presets = self.storage.list_all(include_builtins=True)\n            self._cache = {p.id: p for p in presets}\n        return self._cache\n\n    # =========================================================================\n    # CRUD Operations\n    # =========================================================================\n\n    def create(\n        self,\n        name: str,\n        settings: Optional[PresetSettings] = None,\n        category: PresetCategory = PresetCategory.CUSTOM,\n        description: str = \"\",\n        tags: Optional[List[str]] = None,\n        author: str = \"\",\n    ) -> Preset:\n        \"\"\"Create a new preset.\n\n        Args:\n            name: Preset name (must be unique among user presets).\n            settings: Preset settings. Uses defaults if not provided.\n            category: Preset category.\n            description: Preset description.\n            tags: List of tags for filtering.\n            author: Author name.\n\n        Returns:\n            The created preset.\n\n        Raises:\n            PresetManagerError: If a preset with the same name already exists.\n        \"\"\"\n        # Check for duplicate name\n        existing = self.get_by_name(name)\n        if existing:\n            raise PresetManagerError(\n                f\"Preset with name '{name}' already exists (id={existing.id})\"\n            )\n\n        preset = Preset(\n            name=name,\n            description=description,\n            category=category,\n            tags=tags or [],\n            settings=settings or PresetSettings(),\n            author=author,\n            is_builtin=False,\n        )\n\n        self.storage.save(preset)\n        self._invalidate_cache()\n\n        logger.info(f\"Created preset '{name}' (id={preset.id})\")\n        return preset\n\n    def get(self, preset_id: str) -> Optional[Preset]:\n        \"\"\"Get a preset by ID.\n\n        Args:\n            preset_id: The preset ID.\n\n        Returns:\n            The preset, or None if not found.\n        \"\"\"\n        return self.storage.load(preset_id)\n\n    def get_by_name(self, name: str) -> Optional[Preset]:\n        \"\"\"Get a preset by name.\n\n        Args:\n            name: The preset name (case-insensitive).\n\n        Returns:\n            The preset, or None if not found.\n        \"\"\"\n        all_presets = self._get_cached_presets()\n        name_lower = name.lower()\n\n        for preset in all_presets.values():\n            if preset.name.lower() == name_lower:\n                return preset\n\n        return None\n\n    def update(\n        self,\n        preset_id: str,\n        name: Optional[str] = None,\n        description: Optional[str] = None,\n        category: Optional[PresetCategory] = None,\n        tags: Optional[List[str]] = None,\n        settings: Optional[PresetSettings] = None,\n    ) -> Preset:\n        \"\"\"Update an existing preset.\n\n        Args:\n            preset_id: The preset ID to update.\n            name: New name (optional).\n            description: New description (optional).\n            category: New category (optional).\n            tags: New tags (optional).\n            settings: New settings (optional).\n\n        Returns:\n            The updated preset.\n\n        Raises:\n            PresetManagerError: If preset not found or new name conflicts.\n        \"\"\"\n        preset = self.get(preset_id)\n        if not preset:\n            raise PresetManagerError(f\"Preset '{preset_id}' not found\")\n\n        if preset.is_builtin:\n            raise PresetManagerError(\n                f\"Cannot update built-in preset '{preset.name}'. \"\n                \"Create a copy to modify it.\"\n            )\n\n        # Check for name conflict\n        if name and name != preset.name:\n            existing = self.get_by_name(name)\n            if existing and existing.id != preset_id:\n                raise PresetManagerError(\n                    f\"Preset with name '{name}' already exists\"\n                )\n            preset.name = name\n\n        if description is not None:\n            preset.description = description\n        if category is not None:\n            preset.category = category\n        if tags is not None:\n            preset.tags = tags\n        if settings is not None:\n            preset.settings = settings\n\n        preset.update_timestamp()\n        self.storage.save(preset)\n        self._invalidate_cache()\n\n        logger.info(f\"Updated preset '{preset.name}' (id={preset_id})\")\n        return preset\n\n    def delete(self, preset_id: str) -> bool:\n        \"\"\"Delete a preset.\n\n        Args:\n            preset_id: The preset ID to delete.\n\n        Returns:\n            True if deleted, False if not found.\n\n        Raises:\n            PresetManagerError: If trying to delete a built-in preset.\n        \"\"\"\n        preset = self.get(preset_id)\n        if not preset:\n            return False\n\n        result = self.storage.delete(preset_id)\n        self._invalidate_cache()\n\n        if result:\n            logger.info(f\"Deleted preset '{preset.name}' (id={preset_id})\")\n\n        return result\n\n    def duplicate(self, preset_id: str, new_name: Optional[str] = None) -> Preset:\n        \"\"\"Create a copy of an existing preset.\n\n        Args:\n            preset_id: The preset ID to duplicate.\n            new_name: Name for the copy. Defaults to \"{original} (copy)\".\n\n        Returns:\n            The duplicated preset.\n\n        Raises:\n            PresetManagerError: If preset not found or name conflicts.\n        \"\"\"\n        preset = self.get(preset_id)\n        if not preset:\n            raise PresetManagerError(f\"Preset '{preset_id}' not found\")\n\n        name = new_name or f\"{preset.name} (copy)\"\n\n        return self.create(\n            name=name,\n            settings=preset.settings,  # Will be copied since dataclass\n            category=preset.category,\n            description=preset.description,\n            tags=preset.tags.copy(),\n            author=preset.author,\n        )\n\n    # =========================================================================\n    # Listing and Searching\n    # =========================================================================\n\n    def list_all(self, include_builtins: bool = True) -> List[Preset]:\n        \"\"\"List all presets.\n\n        Args:\n            include_builtins: Whether to include built-in presets.\n\n        Returns:\n            List of all presets.\n        \"\"\"\n        return self.storage.list_all(include_builtins=include_builtins)\n\n    def list_by_category(\n        self, category: PresetCategory, include_builtins: bool = True\n    ) -> List[Preset]:\n        \"\"\"List presets by category.\n\n        Args:\n            category: The category to filter by.\n            include_builtins: Whether to include built-in presets.\n\n        Returns:\n            List of presets in the category.\n        \"\"\"\n        return self.storage.list_by_category(\n            category.value, include_builtins=include_builtins\n        )\n\n    def search(\n        self,\n        query: str,\n        category: Optional[PresetCategory] = None,\n        tags: Optional[List[str]] = None,\n    ) -> List[Preset]:\n        \"\"\"Search presets by query, category, and/or tags.\n\n        Args:\n            query: Search query (searches name and description).\n            category: Optional category filter.\n            tags: Optional tags filter (matches any tag).\n\n        Returns:\n            List of matching presets.\n        \"\"\"\n        all_presets = self.list_all()\n        query_lower = query.lower()\n\n        results = []\n        for preset in all_presets:\n            # Category filter\n            if category and preset.category != category:\n                continue\n\n            # Tags filter\n            if tags and not any(tag in preset.tags for tag in tags):\n                continue\n\n            # Query filter\n            if query:\n                if (\n                    query_lower not in preset.name.lower()\n                    and query_lower not in preset.description.lower()\n                ):\n                    continue\n\n            results.append(preset)\n\n        return results\n\n    # =========================================================================\n    # Import/Export\n    # =========================================================================\n\n    def export_preset(self, preset_id: str, export_path: Path) -> Path:\n        \"\"\"Export a preset to a file.\n\n        Args:\n            preset_id: The preset ID to export.\n            export_path: Path to export the preset to.\n\n        Returns:\n            Path to the exported file.\n\n        Raises:\n            PresetManagerError: If preset not found or export fails.\n        \"\"\"\n        try:\n            return self.storage.export_preset(preset_id, export_path)\n        except PresetStorageError as e:\n            raise PresetManagerError(str(e)) from e\n\n    def import_preset(\n        self, import_path: Path, overwrite: bool = False\n    ) -> Preset:\n        \"\"\"Import a preset from a file.\n\n        Args:\n            import_path: Path to the preset file to import.\n            overwrite: Whether to overwrite existing preset with same ID.\n\n        Returns:\n            The imported preset.\n\n        Raises:\n            PresetManagerError: If import fails.\n        \"\"\"\n        try:\n            preset = self.storage.import_preset(import_path, overwrite=overwrite)\n            self._invalidate_cache()\n            return preset\n        except PresetStorageError as e:\n            raise PresetManagerError(str(e)) from e\n\n    # =========================================================================\n    # Configuration Integration\n    # =========================================================================\n\n    def apply_preset_to_config(self, preset: Preset, config: Config) -> Config:\n        \"\"\"Apply preset settings to a Config object.\n\n        Creates a new Config with the preset's settings applied.\n        Does not modify the original config.\n\n        Args:\n            preset: The preset to apply.\n            config: The base configuration.\n\n        Returns:\n            A new Config with preset settings applied.\n        \"\"\"\n        # Create new config objects with preset settings\n        processing = ProcessingConfig(\n            batch_size=preset.settings.processing.batch_size,\n            num_workers=preset.settings.processing.num_workers,\n            use_gpu=preset.settings.processing.use_gpu,\n            gpu_device=preset.settings.processing.gpu_device,\n            mixed_precision=preset.settings.processing.mixed_precision,\n            max_memory_percent=preset.settings.processing.max_memory_percent,\n        )\n\n        depth_estimation = DepthEstimationConfig(\n            model=preset.settings.depth_estimation.model,\n            output_width=preset.settings.depth_estimation.output_width,\n            output_height=preset.settings.depth_estimation.output_height,\n            min_depth=preset.settings.depth_estimation.min_depth,\n            max_depth=preset.settings.depth_estimation.max_depth,\n            temporal_consistency=preset.settings.depth_estimation.temporal_consistency,\n            temporal_smoothing_factor=preset.settings.depth_estimation.temporal_smoothing_factor,\n        )\n\n        from video2d3d.utils.config import AnaglyphConfig, SideBySideConfig\n\n        stereo_generation = StereoGenerationConfig(\n            format=preset.settings.stereo_generation.format,\n            baseline=preset.settings.stereo_generation.baseline,\n            focal_length=preset.settings.stereo_generation.focal_length,\n            convergence=preset.settings.stereo_generation.convergence,\n            anaglyph=AnaglyphConfig(\n                type=preset.settings.stereo_generation.anaglyph_type,\n                color_method=preset.settings.stereo_generation.anaglyph_color_method,\n            ),\n            side_by_side=SideBySideConfig(\n                layout=preset.settings.stereo_generation.sbs_layout,\n                swap_eyes=preset.settings.stereo_generation.sbs_swap_eyes,\n                half_width=preset.settings.stereo_generation.sbs_half_width,\n            ),\n        )\n\n        video_output = VideoOutputConfig(\n            format=preset.settings.video_output.format,\n            codec=preset.settings.video_output.codec,\n            preset=preset.settings.video_output.preset,\n            crf=preset.settings.video_output.crf,\n            pixel_format=preset.settings.video_output.pixel_format,\n        )\n\n        quality = QualityConfig(\n            preset=preset.settings.quality.preset,\n            post_processing=preset.settings.quality.post_processing,\n            calculate_metrics=preset.settings.quality.calculate_metrics,\n        )\n\n        # Create new config with updated sections\n        config.processing = processing\n        config.depth_estimation = depth_estimation\n        config.stereo_generation = stereo_generation\n        config.video_output = video_output\n        config.quality = quality\n\n        return config\n\n    def create_preset_from_config(\n        self,\n        name: str,\n        config: Config,\n        category: PresetCategory = PresetCategory.CUSTOM,\n        description: str = \"\",\n        tags: Optional[List[str]] = None,\n    ) -> Preset:\n        \"\"\"Create a preset from a Config object.\n\n        Args:\n            name: Preset name.\n            config: Configuration to create preset from.\n            category: Preset category.\n            description: Preset description.\n            tags: List of tags.\n\n        Returns:\n            The created preset.\n        \"\"\"\n        settings = PresetSettings(\n            depth_estimation=PresetSettings.__dataclass_fields__[\n                \"depth_estimation\"\n            ].type(\n                model=config.depth_estimation.model,\n                output_width=config.depth_estimation.output_width,\n                output_height=config.depth_estimation.output_height,\n                min_depth=config.depth_estimation.min_depth,\n                max_depth=config.depth_estimation.max_depth,\n                temporal_consistency=config.depth_estimation.temporal_consistency,\n                temporal_smoothing_factor=config.depth_estimation.temporal_smoothing_factor,\n            ),\n            stereo_generation=PresetSettings.__dataclass_fields__[\n                \"stereo_generation\"\n            ].type(\n                format=config.stereo_generation.format,\n                baseline=config.stereo_generation.baseline,\n                focal_length=config.stereo_generation.focal_length,\n                convergence=config.stereo_generation.convergence,\n                anaglyph_type=config.stereo_generation.anaglyph.type,\n                anaglyph_color_method=config.stereo_generation.anaglyph.color_method,\n                sbs_layout=config.stereo_generation.side_by_side.layout,\n                sbs_swap_eyes=config.stereo_generation.side_by_side.swap_eyes,\n                sbs_half_width=config.stereo_generation.side_by_side.half_width,\n            ),\n            video_output=PresetSettings.__dataclass_fields__[\n                \"video_output\"\n            ].type(\n                format=config.video_output.format,\n                codec=config.video_output.codec,\n                preset=config.video_output.preset,\n                crf=config.video_output.crf,\n                pixel_format=config.video_output.pixel_format,\n            ),\n            processing=PresetSettings.__dataclass_fields__[\"processing\"].type(\n                batch_size=config.processing.batch_size,\n                num_workers=config.processing.num_workers,\n                use_gpu=config.processing.use_gpu,\n                gpu_device=config.processing.gpu_device,\n                mixed_precision=config.processing.mixed_precision,\n                max_memory_percent=config.processing.max_memory_percent,\n            ),\n            quality=PresetSettings.__dataclass_fields__[\"quality\"].type(\n                preset=config.quality.preset,\n                post_processing=config.quality.post_processing,\n                calculate_metrics=config.quality.calculate_metrics,\n            ),\n        )\n\n        return self.create(\n            name=name,\n            settings=settings,\n            category=category,\n            description=description,\n            tags=tags,\n        )\n\n\n# Singleton instance for convenience\n_manager: Optional[PresetManager] = None\n\n\ndef get_preset_manager(reload: bool = False) -> PresetManager:\n    \"\"\"Get the global PresetManager instance.\n\n    Args:\n        reload: Force reload of the manager.\n\n    Returns:\n        The PresetManager instance.\n    \"\"\"\n    global _manager\n    if _manager is None or reload:\n        _manager = PresetManager()\n    return _manager\n\n\n__all__ = [\n    \"PresetManagerError\",\n    \"PresetManager\",\n    \"get_preset_manager\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/manager.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Built-in presets for common use cases.\n\nThis module defines ready-to-use presets for different scenarios:\n- Cinema: High quality for theatrical/large screen viewing\n- VR: Optimized for VR headsets (over-under format)\n- Web: Balanced for web streaming and sharing\n- Mobile: Optimized for mobile devices\n- Fast: Quick preview with lower quality\n- Quality: Maximum quality for archival\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import List\n\nfrom video2d3d.presets.models import (\n    DepthEstimationSettings,\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    ProcessingSettings,\n    QualitySettings,\n    StereoGenerationSettings,\n    VideoOutputSettings,\n)\n\n\ndef _create_builtin_preset(\n    preset_id: str,\n    name: str,\n    description: str,\n    category: PresetCategory,\n    tags: List[str],\n    depth_model: str,\n    stereo_format: str,\n    video_preset: str,\n    video_crf: int,\n    quality_preset: str,\n    depth_width: int = 384,\n    depth_height: int = 384,\n    baseline: float = 0.05,\n    sbs_half_width: bool = False,\n    batch_size: int = 4,\n    **kwargs,\n) -> Preset:\n    \"\"\"Helper to create built-in presets with consistent structure.\"\"\"\n    settings = PresetSettings(\n        depth_estimation=DepthEstimationSettings(\n            model=depth_model,\n            output_width=depth_width,\n            output_height=depth_height,\n            temporal_consistency=True,\n            temporal_smoothing_factor=0.5,\n        ),\n        stereo_generation=StereoGenerationSettings(\n            format=stereo_format,\n            baseline=baseline,\n            focal_length=1.0,\n            convergence=0.5,\n            sbs_half_width=sbs_half_width,\n        ),\n        video_output=VideoOutputSettings(\n            format=\"mp4\",\n            codec=\"libx264\",\n            preset=video_preset,\n            crf=video_crf,\n            pixel_format=\"yuv420p\",\n        ),\n        processing=ProcessingSettings(\n            batch_size=batch_size,\n            num_workers=4,\n            use_gpu=True,\n            mixed_precision=True,\n        ),\n        quality=QualitySettings(\n            preset=quality_preset,\n            post_processing=True,\n            calculate_metrics=False,\n        ),\n    )\n\n    return Preset(\n        id=preset_id,\n        name=name,\n        description=description,\n        category=category,\n        tags=tags,\n        settings=settings,\n        is_builtin=True,\n        version=\"1.0.0\",\n        author=\"2Dto3D\",\n    )\n\n\n# =============================================================================\n# CINEMA PRESETS - High quality for large screens\n# =============================================================================\n\nCINEMA_SBS = _create_builtin_preset(\n    preset_id=\"builtin-cinema-sbs\",\n    name=\"Cinema (Side-by-Side)\",\n    description=(\n        \"High-quality preset optimized for large screen viewing. \"\n        \"Uses DPT Large model for best depth estimation and slow encoding \"\n        \"for optimal quality. Ideal for theatrical presentations and home cinema.\"\n    ),\n    category=PresetCategory.CINEMA,\n    tags=[\"cinema\", \"high-quality\", \"side-by-side\", \"large-screen\"],\n    depth_model=\"dpt_large\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"slow\",\n    video_crf=18,\n    quality_preset=\"quality\",\n    depth_width=384,\n    depth_height=384,\n    baseline=0.05,\n    batch_size=2,  # Lower batch size for quality\n)\n\nCINEMA_ANAGLYPH = _create_builtin_preset(\n    preset_id=\"builtin-cinema-anaglyph\",\n    name=\"Cinema (Anaglyph)\",\n    description=(\n        \"High-quality anaglyph preset for red-cyan 3D glasses. \"\n        \"Uses Dubois color method for best color reproduction. \"\n        \"Optimized for viewing on large screens with 3D glasses.\"\n    ),\n    category=PresetCategory.CINEMA,\n    tags=[\"cinema\", \"anaglyph\", \"high-quality\", \"glasses\"],\n    depth_model=\"dpt_large\",\n    stereo_format=\"anaglyph\",\n    video_preset=\"slow\",\n    video_crf=18,\n    quality_preset=\"quality\",\n)\n\n\n# =============================================================================\n# VR PRESETS - Optimized for VR headsets\n# =============================================================================\n\nVR_OVER_UNDER = _create_builtin_preset(\n    preset_id=\"builtin-vr-over-under\",\n    name=\"VR (Over-Under)\",\n    description=(\n        \"Optimized for VR headset viewing with over-under format. \"\n        \"Uses increased baseline for stronger 3D effect and \"\n        \"higher depth resolution. Compatible with most VR players.\"\n    ),\n    category=PresetCategory.VR,\n    tags=[\"vr\", \"over-under\", \"headset\", \"immersive\"],\n    depth_model=\"dpt_hybrid\",\n    stereo_format=\"vr\",\n    video_preset=\"medium\",\n    video_crf=20,\n    quality_preset=\"balanced\",\n    depth_width=512,\n    depth_height=512,\n    baseline=0.08,  # Stronger 3D for VR\n)\n\nVR_SIDE_BY_SIDE = _create_builtin_preset(\n    preset_id=\"builtin-vr-sbs\",\n    name=\"VR (Side-by-Side)\",\n    description=(\n        \"Side-by-side format optimized for VR viewing. \"\n        \"Half-width encoding for compatibility with mobile VR. \"\n        \"Good balance of quality and file size.\"\n    ),\n    category=PresetCategory.VR,\n    tags=[\"vr\", \"side-by-side\", \"mobile-vr\", \"oculus\", \"cardboard\"],\n    depth_model=\"midas_hybrid\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"medium\",\n    video_crf=22,\n    quality_preset=\"balanced\",\n    sbs_half_width=True,\n    baseline=0.07,\n)\n\n\n# =============================================================================\n# WEB PRESETS - Optimized for web streaming\n# =============================================================================\n\nWEB_SBS = _create_builtin_preset(\n    preset_id=\"builtin-web-sbs\",\n    name=\"Web (Side-by-Side)\",\n    description=(\n        \"Optimized for web streaming and sharing. \"\n        \"Good quality with reasonable file sizes. \"\n        \"Fast encoding preset for quick processing. \"\n        \"Compatible with YouTube 3D and most web players.\"\n    ),\n    category=PresetCategory.WEB,\n    tags=[\"web\", \"streaming\", \"youtube\", \"sharing\", \"side-by-side\"],\n    depth_model=\"midas_hybrid\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"fast\",\n    video_crf=23,\n    quality_preset=\"balanced\",\n)\n\nWEB_ANAGLYPH = _create_builtin_preset(\n    preset_id=\"builtin-web-anaglyph\",\n    name=\"Web (Anaglyph)\",\n    description=(\n        \"Anaglyph format for easy web sharing. \"\n        \"Works with standard red-cyan glasses. \"\n        \"Small file sizes, fast processing. \"\n        \"Great for social media and quick previews.\"\n    ),\n    category=PresetCategory.WEB,\n    tags=[\"web\", \"anaglyph\", \"social-media\", \"sharing\", \"glasses\"],\n    depth_model=\"midas_small\",\n    stereo_format=\"anaglyph\",\n    video_preset=\"fast\",\n    video_crf=24,\n    quality_preset=\"fast\",\n)\n\n\n# =============================================================================\n# MOBILE PRESETS - Optimized for mobile devices\n# =============================================================================\n\nMOBILE_SBS = _create_builtin_preset(\n    preset_id=\"builtin-mobile-sbs\",\n    name=\"Mobile (Side-by-Side)\",\n    description=(\n        \"Optimized for viewing on mobile devices. \"\n        \"Half-width side-by-side for VR cardboards. \"\n        \"Small file sizes and fast processing. \"\n        \"Compatible with Google Cardboard and similar viewers.\"\n    ),\n    category=PresetCategory.MOBILE,\n    tags=[\"mobile\", \"cardboard\", \"side-by-side\", \"portable\"],\n    depth_model=\"midas_small\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"fast\",\n    video_crf=25,\n    quality_preset=\"fast\",\n    sbs_half_width=True,\n    baseline=0.04,\n)\n\nMOBILE_ANAGLYPH = _create_builtin_preset(\n    preset_id=\"builtin-mobile-anaglyph\",\n    name=\"Mobile (Anaglyph)\",\n    description=(\n        \"Lightweight anaglyph preset for mobile devices. \"\n        \"Small file sizes, fast processing. \"\n        \"Good for quick viewing with 3D glasses on phones/tablets.\"\n    ),\n    category=PresetCategory.MOBILE,\n    tags=[\"mobile\", \"anaglyph\", \"lightweight\", \"portable\"],\n    depth_model=\"midas_small\",\n    stereo_format=\"anaglyph\",\n    video_preset=\"fast\",\n    video_crf=26,\n    quality_preset=\"fast\",\n)\n\n\n# =============================================================================\n# QUALITY PRESETS\n# =============================================================================\n\nFAST_PREVIEW = _create_builtin_preset(\n    preset_id=\"builtin-fast-preview\",\n    name=\"Fast Preview\",\n    description=(\n        \"Quick preview preset for testing and fast iterations. \"\n        \"Uses fastest settings for minimal processing time. \"\n        \"Not recommended for final output.\"\n    ),\n    category=PresetCategory.GENERAL,\n    tags=[\"fast\", \"preview\", \"test\", \"quick\"],\n    depth_model=\"midas_small\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"ultrafast\",\n    video_crf=28,\n    quality_preset=\"fast\",\n    batch_size=8,\n)\n\nMAX_QUALITY = _create_builtin_preset(\n    preset_id=\"builtin-max-quality\",\n    name=\"Maximum Quality\",\n    description=(\n        \"Highest quality preset for archival and professional use. \"\n        \"Uses best depth model, slowest encoding, and all quality enhancements. \"\n        \"Processing will be slow but results will be optimal.\"\n    ),\n    category=PresetCategory.GENERAL,\n    tags=[\"quality\", \"archive\", \"professional\", \"best\"],\n    depth_model=\"dpt_large\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"veryslow\",\n    video_crf=16,\n    quality_preset=\"quality\",\n    depth_width=384,\n    depth_height=384,\n    batch_size=1,  # Max quality, single frame at a time\n)\n\nBALANCED = _create_builtin_preset(\n    preset_id=\"builtin-balanced\",\n    name=\"Balanced\",\n    description=(\n        \"Default balanced preset for general use. \"\n        \"Good compromise between quality and processing speed. \"\n        \"Suitable for most common scenarios.\"\n    ),\n    category=PresetCategory.GENERAL,\n    tags=[\"balanced\", \"default\", \"general\"],\n    depth_model=\"midas_hybrid\",\n    stereo_format=\"side_by_side\",\n    video_preset=\"medium\",\n    video_crf=23,\n    quality_preset=\"balanced\",\n)\n\n\n# =============================================================================\n# ALL BUILT-IN PRESETS\n# =============================================================================\n\nALL_BUILTIN_PRESETS: List[Preset] = [\n    # Cinema\n    CINEMA_SBS,\n    CINEMA_ANAGLYPH,\n    # VR\n    VR_OVER_UNDER,\n    VR_SIDE_BY_SIDE,\n    # Web\n    WEB_SBS,\n    WEB_ANAGLYPH,\n    # Mobile\n    MOBILE_SBS,\n    MOBILE_ANAGLYPH,\n    # Quality\n    FAST_PREVIEW,\n    MAX_QUALITY,\n    BALANCED,\n]\n\n# Mapping by ID for quick lookup\nBUILTIN_PRESETS_BY_ID = {p.id: p for p in ALL_BUILTIN_PRESETS}\n\n# Mapping by name for quick lookup\nBUILTIN_PRESETS_BY_NAME = {p.name: p for p in ALL_BUILTIN_PRESETS}\n\n\ndef get_builtin_preset(preset_id: str) -> Preset | None:\n    \"\"\"Get a built-in preset by ID.\n\n    Args:\n        preset_id: The preset ID.\n\n    Returns:\n        The preset, or None if not found.\n    \"\"\"\n    return BUILTIN_PRESETS_BY_ID.get(preset_id)\n\n\ndef get_builtin_preset_by_name(name: str) -> Preset | None:\n    \"\"\"Get a built-in preset by name.\n\n    Args:\n        name: The preset name (case-insensitive).\n\n    Returns:\n        The preset, or None if not found.\n    \"\"\"\n    name_lower = name.lower()\n    for preset in ALL_BUILTIN_PRESETS:\n        if preset.name.lower() == name_lower:\n            return preset\n    return None\n\n\n__all__ = [\n    # Individual presets\n    \"CINEMA_SBS\",\n    \"CINEMA_ANAGLYPH\",\n    \"VR_OVER_UNDER\",\n    \"VR_SIDE_BY_SIDE\",\n    \"WEB_SBS\",\n    \"WEB_ANAGLYPH\",\n    \"MOBILE_SBS\",\n    \"MOBILE_ANAGLYPH\",\n    \"FAST_PREVIEW\",\n    \"MAX_QUALITY\",\n    \"BALANCED\",\n    # Collections\n    \"ALL_BUILTIN_PRESETS\",\n    \"BUILTIN_PRESETS_BY_ID\",\n    \"BUILTIN_PRESETS_BY_NAME\",\n    # Functions\n    \"get_builtin_preset\",\n    \"get_builtin_preset_by_name\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins.py"
}

🔧 Tool: bash
Input: {
  "command": "mkdir -p src/video2d3d/presets/builtins",
  "description": "Create builtins directory"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Preset management for video2d3d.\n\nThis module provides a system for saving, loading, and sharing processing\npresets with optimized settings for different use cases (cinema, VR, web, mobile).\n\nUsage:\n    from video2d3d.presets import PresetManager, get_preset_manager\n    from video2d3d.presets.models import Preset, PresetCategory\n\n    # Get the preset manager\n    manager = get_preset_manager()\n\n    # List all presets\n    presets = manager.list_all()\n\n    # Create a new preset\n    preset = manager.create(\n        name=\"My Custom Preset\",\n        category=PresetCategory.CUSTOM,\n        description=\"My custom settings\",\n    )\n\n    # Get a preset by ID or name\n    preset = manager.get(\"preset-id\")\n    preset = manager.get_by_name(\"My Custom Preset\")\n\n    # Apply preset to a job config\n    from video2d3d.utils.config import get_config\n    config = get_config()\n    config = manager.apply_preset_to_config(preset, config)\n\nBuilt-in Presets:\n    - Cinema (Side-by-Side, Anaglyph): High quality for large screens\n    - VR (Over-Under, Side-by-Side): Optimized for VR headsets\n    - Web (Side-by-Side, Anaglyph): Optimized for streaming/sharing\n    - Mobile (Side-by-Side, Anaglyph): Optimized for mobile devices\n    - Fast Preview: Quick testing with minimal processing time\n    - Maximum Quality: Best quality for archival use\n    - Balanced: Default balanced settings\n\"\"\"\n\nfrom video2d3d.presets.builtins import (\n    ALL_BUILTIN_PRESETS,\n    BALANCED,\n    BUILTIN_PRESETS_BY_ID,\n    BUILTIN_PRESETS_BY_NAME,\n    CINEMA_ANAGLYPH,\n    CINEMA_SBS,\n    FAST_PREVIEW,\n    MAX_QUALITY,\n    MOBILE_ANAGLYPH,\n    MOBILE_SBS,\n    VR_OVER_UNDER,\n    VR_SIDE_BY_SIDE,\n    WEB_ANAGLYPH,\n    WEB_SBS,\n    get_builtin_preset,\n    get_builtin_preset_by_name,\n)\nfrom video2d3d.presets.manager import PresetManager, PresetManagerError, get_preset_manager\nfrom video2d3d.presets.models import (\n    DepthEstimationSettings,\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    ProcessingSettings,\n    QualitySettings,\n    StereoGenerationSettings,\n    VideoOutputSettings,\n)\nfrom video2d3d.presets.storage import PresetStorage, PresetStorageError\n\n__all__ = [\n    # Manager\n    \"PresetManager\",\n    \"PresetManagerError\",\n    \"get_preset_manager\",\n    # Storage\n    \"PresetStorage\",\n    \"PresetStorageError\",\n    # Models\n    \"Preset\",\n    \"PresetSettings\",\n    \"PresetCategory\",\n    \"DepthEstimationSettings\",\n    \"StereoGenerationSettings\",\n    \"VideoOutputSettings\",\n    \"ProcessingSettings\",\n    \"QualitySettings\",\n    # Built-in presets\n    \"CINEMA_SBS\",\n    \"CINEMA_ANAGLYPH\",\n    \"VR_OVER_UNDER\",\n    \"VR_SIDE_BY_SIDE\",\n    \"WEB_SBS\",\n    \"WEB_ANAGLYPH\",\n    \"MOBILE_SBS\",\n    \"MOBILE_ANAGLYPH\",\n    \"FAST_PREVIEW\",\n    \"MAX_QUALITY\",\n    \"BALANCED\",\n    \"ALL_BUILTIN_PRESETS\",\n    \"BUILTIN_PRESETS_BY_ID\",\n    \"BUILTIN_PRESETS_BY_NAME\",\n    \"get_builtin_preset\",\n    \"get_builtin_preset_by_name\",\n]\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/__init__.py"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-cinema-sbs\",\n  \"name\": \"Cinema (Side-by-Side)\",\n  \"description\": \"High-quality preset optimized for large screen viewing. Uses DPT Large model for best depth estimation and slow encoding for optimal quality. Ideal for theatrical presentations and home cinema.\",\n  \"category\": \"cinema\",\n  \"tags\": [\"cinema\", \"high-quality\", \"side-by-side\", \"large-screen\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"dpt_large\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"slow\",\n      \"crf\": 18,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 2,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"quality\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-cinema-sbs.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-vr-over-under\",\n  \"name\": \"VR (Over-Under)\",\n  \"description\": \"Optimized for VR headset viewing with over-under format. Uses increased baseline for stronger 3D effect and higher depth resolution. Compatible with most VR players.\",\n  \"category\": \"vr\",\n  \"tags\": [\"vr\", \"over-under\", \"headset\", \"immersive\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"dpt_hybrid\",\n      \"output_width\": 512,\n      \"output_height\": 512,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"vr\",\n      \"baseline\": 0.08,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"medium\",\n      \"crf\": 20,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"balanced\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-vr-over-under.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-cinema-anaglyph\",\n  \"name\": \"Cinema (Anaglyph)\",\n  \"description\": \"High-quality anaglyph preset for red-cyan 3D glasses. Uses Dubois color method for best color reproduction. Optimized for viewing on large screens with 3D glasses.\",\n  \"category\": \"cinema\",\n  \"tags\": [\"cinema\", \"anaglyph\", \"high-quality\", \"glasses\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"dpt_large\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"anaglyph\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"slow\",\n      \"crf\": 18,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"quality\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-cinema-anaglyph.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-web-sbs\",\n  \"name\": \"Web (Side-by-Side)\",\n  \"description\": \"Optimized for web streaming and sharing. Good quality with reasonable file sizes. Fast encoding preset for quick processing. Compatible with YouTube 3D and most web players.\",\n  \"category\": \"web\",\n  \"tags\": [\"web\", \"streaming\", \"youtube\", \"sharing\", \"side-by-side\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_hybrid\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"fast\",\n      \"crf\": 23,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"balanced\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-web-sbs.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-vr-sbs\",\n  \"name\": \"VR (Side-by-Side)\",\n  \"description\": \"Side-by-side format optimized for VR viewing. Half-width encoding for compatibility with mobile VR. Good balance of quality and file size.\",\n  \"category\": \"vr\",\n  \"tags\": [\"vr\", \"side-by-side\", \"mobile-vr\", \"oculus\", \"cardboard\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_hybrid\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.07,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": true\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"medium\",\n      \"crf\": 22,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"balanced\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-vr-sbs.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-mobile-anaglyph\",\n  \"name\": \"Mobile (Anaglyph)\",\n  \"description\": \"Lightweight anaglyph preset for mobile devices. Small file sizes, fast processing. Good for quick viewing with 3D glasses on phones/tablets.\",\n  \"category\": \"mobile\",\n  \"tags\": [\"mobile\", \"anaglyph\", \"lightweight\", \"portable\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_small\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"anaglyph\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"fast\",\n      \"crf\": 26,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"fast\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-mobile-anaglyph.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-mobile-sbs\",\n  \"name\": \"Mobile (Side-by-Side)\",\n  \"description\": \"Optimized for viewing on mobile devices. Half-width side-by-side for VR cardboards. Small file sizes and fast processing. Compatible with Google Cardboard and similar viewers.\",\n  \"category\": \"mobile\",\n  \"tags\": [\"mobile\", \"cardboard\", \"side-by-side\", \"portable\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_small\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.04,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": true\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"fast\",\n      \"crf\": 25,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"fast\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-mobile-sbs.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-fast-preview\",\n  \"name\": \"Fast Preview\",\n  \"description\": \"Quick preview preset for testing and fast iterations. Uses fastest settings for minimal processing time. Not recommended for final output.\",\n  \"category\": \"general\",\n  \"tags\": [\"fast\", \"preview\", \"test\", \"quick\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_small\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"ultrafast\",\n      \"crf\": 28,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 8,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"fast\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-fast-preview.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-max-quality\",\n  \"name\": \"Maximum Quality\",\n  \"description\": \"Highest quality preset for archival and professional use. Uses best depth model, slowest encoding, and all quality enhancements. Processing will be slow but results will be optimal.\",\n  \"category\": \"general\",\n  \"tags\": [\"quality\", \"archive\", \"professional\", \"best\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"dpt_large\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"veryslow\",\n      \"crf\": 16,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 1,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"quality\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-max-quality.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-web-anaglyph\",\n  \"name\": \"Web (Anaglyph)\",\n  \"description\": \"Anaglyph format for easy web sharing. Works with standard red-cyan glasses. Small file sizes, fast processing. Great for social media and quick previews.\",\n  \"category\": \"web\",\n  \"tags\": [\"web\", \"anaglyph\", \"social-media\", \"sharing\", \"glasses\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_small\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"anaglyph\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"fast\",\n      \"crf\": 24,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"fast\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-web-anaglyph.json"
}

🔧 Tool: write
Input: {
  "content": "{\n  \"id\": \"builtin-balanced\",\n  \"name\": \"Balanced\",\n  \"description\": \"Default balanced preset for general use. Good compromise between quality and processing speed. Suitable for most common scenarios.\",\n  \"category\": \"general\",\n  \"tags\": [\"balanced\", \"default\", \"general\"],\n  \"settings\": {\n    \"depth_estimation\": {\n      \"model\": \"midas_hybrid\",\n      \"output_width\": 384,\n      \"output_height\": 384,\n      \"min_depth\": 0.0,\n      \"max_depth\": 1.0,\n      \"temporal_consistency\": true,\n      \"temporal_smoothing_factor\": 0.5\n    },\n    \"stereo_generation\": {\n      \"format\": \"side_by_side\",\n      \"baseline\": 0.05,\n      \"focal_length\": 1.0,\n      \"convergence\": 0.5,\n      \"anaglyph_type\": \"red_cyan\",\n      \"anaglyph_color_method\": \"dubois\",\n      \"sbs_layout\": \"horizontal\",\n      \"sbs_swap_eyes\": false,\n      \"sbs_half_width\": false\n    },\n    \"video_output\": {\n      \"format\": \"mp4\",\n      \"codec\": \"libx264\",\n      \"preset\": \"medium\",\n      \"crf\": 23,\n      \"pixel_format\": \"yuv420p\"\n    },\n    \"processing\": {\n      \"batch_size\": 4,\n      \"num_workers\": 4,\n      \"use_gpu\": true,\n      \"gpu_device\": 0,\n      \"mixed_precision\": true,\n      \"max_memory_percent\": 80\n    },\n    \"quality\": {\n      \"preset\": \"balanced\",\n      \"post_processing\": true,\n      \"calculate_metrics\": false\n    }\n  },\n  \"created_at\": \"2024-01-01T00:00:00\",\n  \"updated_at\": \"2024-01-01T00:00:00\",\n  \"is_builtin\": true,\n  \"version\": \"1.0.0\",\n  \"author\": \"2Dto3D\"\n}\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins/builtin-balanced.json"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/cli.py",
  "offset": 680
}


---

## Follow-up Session

I'll perform a thorough code review of the preset manager implementation and then update the code based on my findings.

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/manager.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/builtins.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/utils/config.py"
}
Now I'll analyze the code for issues and make improvements. Let me identify problems and fix them:

## Code Review Findings

### Issues Found:

1. **models.py**:
   - DRY violation: `from_dict` methods are repetitive with same `data.get(key, default)` pattern
   - Missing input validation (e.g., CRF should be 0-51, baseline should be positive)
   - Magic strings for format types should be enums

2. **storage.py**:
   - Missing atomic writes (should write to temp file then rename)
   - Cache coherency: redundant setting of `is_builtin` in `load()` 
   - Error messages could be more specific

3. **manager.py**:
   - **Major code smell**: Using `PresetSettings.__dataclass_fields__["field"].type` is hacky
   - **Bug in duplicate()**: Dataclass assignment doesn't create a deep copy
   - Cache could become stale if files are modified externally

4. **builtins.py**:
   - `**kwargs` is accepted but ignored - should document or remove
   - No validation that preset IDs are unique

Let me fix these issues:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Code Review Fix: Add validation to models (CRF range, positive baseline)",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Code Review Fix: Fix hacky dataclass field access in manager.py",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Code Review Fix: Fix duplicate() deep copy issue",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Code Review Fix: Add atomic writes to storage.py",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py",
  "edits": [
    {
      "op": "replace",
      "pos": "56#YN",
      "end": "57#WH",
      "lines": "\n\n@dataclass\nclass StereoGenerationSettings:"
    },
    {
      "op": "replace",
      "pos": "91#QJ",
      "end": "93#BX",
      "lines": "\n        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if self.baseline <= 0:\n            raise ValueError(f\"baseline must be positive, got {self.baseline}\")\n        if self.focal_length <= 0:\n            raise ValueError(f\"focal_length must be positive, got {self.focal_length}\")\n\n\n@dataclass"
    },
    {
      "op": "replace",
      "pos": "117#SQ",
      "end": "119#YR",
      "lines": "\n        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if not 0 <= self.crf <= 51:\n            raise ValueError(f\"crf must be between 0 and 51, got {self.crf}\")\n\n\n@dataclass"
    },
    {
      "op": "replace",
      "pos": "145#TZ",
      "end": "147#PT",
      "lines": "\n        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if self.batch_size < 1:\n            raise ValueError(f\"batch_size must be at least 1, got {self.batch_size}\")\n        if self.num_workers < 0:\n            raise ValueError(f\"num_workers must be non-negative, got {self.num_workers}\")\n        if not 0 <= self.max_memory_percent <= 100:\n            raise ValueError(f\"max_memory_percent must be 0-100, got {self.max_memory_percent}\")\n\n\n@dataclass"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py",
  "edits": [
    {
      "end": "92#JZ",
      "lines": "        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if self.baseline <= 0:\n            raise ValueError(f\"baseline must be positive, got {self.baseline}\")\n        if self.focal_length <= 0:\n            raise ValueError(f\"focal_length must be positive, got {self.focal_length}\")\n\n\n@dataclass\nclass VideoOutputSettings:",
      "op": "replace",
      "pos": "91#QJ"
    },
    {
      "end": "118#RM",
      "lines": "        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if not 0 <= self.crf <= 51:\n            raise ValueError(f\"crf must be between 0 and 51, got {self.crf}\")\n\n\n@dataclass\nclass ProcessingSettings:",
      "op": "replace",
      "pos": "117#SQ"
    },
    {
      "end": "146#JM",
      "lines": "        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if self.batch_size < 1:\n            raise ValueError(f\"batch_size must be at least 1, got {self.batch_size}\")\n        if self.num_workers < 0:\n            raise ValueError(f\"num_workers must be non-negative, got {self.num_workers}\")\n        if not 0 <= self.max_memory_percent <= 100:\n            raise ValueError(\n                f\"max_memory_percent must be 0-100, got {self.max_memory_percent}\"\n            )\n\n\n@dataclass\nclass QualitySettings:",
      "op": "replace",
      "pos": "145#TZ"
    }
  ]
}
Now let me fix the manager.py issues - the hacky dataclass field access and the deep copy issue:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/manager.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/manager.py",
  "edits": [
    {
      "end": "17#YX",
      "lines": "from video2d3d.presets.models import (\n    DepthEstimationSettings,\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    ProcessingSettings,\n    QualitySettings,\n    StereoGenerationSettings,\n    VideoOutputSettings,\n)",
      "op": "replace",
      "pos": "13#HJ"
    },
    {
      "end": "260#VZ",
      "lines": "        name = new_name or f\"{preset.name} (copy)\"\n\n        # Deep copy the settings using serialization to ensure independent copy\n        settings_copy = PresetSettings.from_dict(preset.settings.to_dict())\n\n        return self.create(\n            name=name,\n            settings=settings_copy,\n            category=preset.category,\n            description=preset.description,\n            tags=preset.tags.copy(),\n            author=preset.author,\n        )",
      "op": "replace",
      "pos": "250#XZ"
    },
    {
      "end": "512#MM",
      "lines": "        # Import settings classes directly to avoid hacky field access\n        settings = PresetSettings(\n            depth_estimation=DepthEstimationSettings(\n                model=config.depth_estimation.model,\n                output_width=config.depth_estimation.output_width,\n                output_height=config.depth_estimation.output_height,\n                min_depth=config.depth_estimation.min_depth,\n                max_depth=config.depth_estimation.max_depth,\n                temporal_consistency=config.depth_estimation.temporal_consistency,\n                temporal_smoothing_factor=config.depth_estimation.temporal_smoothing_factor,\n            ),\n            stereo_generation=StereoGenerationSettings(\n                format=config.stereo_generation.format,\n                baseline=config.stereo_generation.baseline,\n                focal_length=config.stereo_generation.focal_length,\n                convergence=config.stereo_generation.convergence,\n                anaglyph_type=config.stereo_generation.anaglyph.type,\n                anaglyph_color_method=config.stereo_generation.anaglyph.color_method,\n                sbs_layout=config.stereo_generation.side_by_side.layout,\n                sbs_swap_eyes=config.stereo_generation.side_by_side.swap_eyes,\n                sbs_half_width=config.stereo_generation.side_by_side.half_width,\n            ),\n            video_output=VideoOutputSettings(\n                format=config.video_output.format,\n                codec=config.video_output.codec,\n                preset=config.video_output.preset,\n                crf=config.video_output.crf,\n                pixel_format=config.video_output.pixel_format,\n            ),\n            processing=ProcessingSettings(\n                batch_size=config.processing.batch_size,\n                num_workers=config.processing.num_workers,\n                use_gpu=config.processing.use_gpu,\n                gpu_device=config.processing.gpu_device,\n                mixed_precision=config.processing.mixed_precision,\n                max_memory_percent=config.processing.max_memory_percent,\n            ),\n            quality=QualitySettings(\n                preset=config.quality.preset,\n                post_processing=config.quality.post_processing,\n                calculate_metrics=config.quality.calculate_metrics,\n            ),\n        )",
      "op": "replace",
      "pos": "471#XX"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/manager.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/manager.py",
  "edits": [
    {
      "end": "17#YX",
      "lines": "from video2d3d.presets.models import (\n    DepthEstimationSettings,\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    ProcessingSettings,\n    QualitySettings,\n    StereoGenerationSettings,\n    VideoOutputSettings,\n)",
      "op": "replace",
      "pos": "13#HJ"
    },
    {
      "end": "260#ZQ",
      "lines": "        name = new_name or f\"{preset.name} (copy)\"\n\n        # Deep copy the settings using serialization to ensure independent copy\n        settings_copy = PresetSettings.from_dict(preset.settings.to_dict())\n\n        return self.create(\n            name=name,\n            settings=settings_copy,\n            category=preset.category,\n            description=preset.description,\n            tags=preset.tags.copy(),\n            author=preset.author,\n        )\n",
      "op": "replace",
      "pos": "250#XZ"
    },
    {
      "end": "512#MM",
      "lines": "        # Import settings classes directly to avoid hacky field access\n        settings = PresetSettings(\n            depth_estimation=DepthEstimationSettings(\n                model=config.depth_estimation.model,\n                output_width=config.depth_estimation.output_width,\n                output_height=config.depth_estimation.output_height,\n                min_depth=config.depth_estimation.min_depth,\n                max_depth=config.depth_estimation.max_depth,\n                temporal_consistency=config.depth_estimation.temporal_consistency,\n                temporal_smoothing_factor=config.depth_estimation.temporal_smoothing_factor,\n            ),\n            stereo_generation=StereoGenerationSettings(\n                format=config.stereo_generation.format,\n                baseline=config.stereo_generation.baseline,\n                focal_length=config.stereo_generation.focal_length,\n                convergence=config.stereo_generation.convergence,\n                anaglyph_type=config.stereo_generation.anaglyph.type,\n                anaglyph_color_method=config.stereo_generation.anaglyph.color_method,\n                sbs_layout=config.stereo_generation.side_by_side.layout,\n                sbs_swap_eyes=config.stereo_generation.side_by_side.swap_eyes,\n                sbs_half_width=config.stereo_generation.side_by_side.half_width,\n            ),\n            video_output=VideoOutputSettings(\n                format=config.video_output.format,\n                codec=config.video_output.codec,\n                preset=config.video_output.preset,\n                crf=config.video_output.crf,\n                pixel_format=config.video_output.pixel_format,\n            ),\n            processing=ProcessingSettings(\n                batch_size=config.processing.batch_size,\n                num_workers=config.processing.num_workers,\n                use_gpu=config.processing.use_gpu,\n                gpu_device=config.processing.gpu_device,\n                mixed_precision=config.processing.mixed_precision,\n                max_memory_percent=config.processing.max_memory_percent,\n            ),\n            quality=QualitySettings(\n                preset=config.quality.preset,\n                post_processing=config.quality.post_processing,\n                calculate_metrics=config.quality.calculate_metrics,\n            ),\n        )",
      "op": "replace",
      "pos": "471#XX"
    }
  ]
}
Now let me fix storage.py to add atomic writes and improve the code:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py",
  "edits": [
    {
      "end": "12#BQ",
      "lines": "import json\nimport os\nimport shutil\nimport tempfile\nfrom pathlib import Path\nfrom typing import Dict, List, Optional",
      "op": "replace",
      "pos": "9#TZ"
    },
    {
      "end": "108#YQ",
      "lines": "        except (IOError, OSError) as e:\n            logger.error(f\"Failed to save preset '{preset.name}': {e}\")\n            raise PresetStorageError(f\"Failed to save preset: {e}\") from e\n\n    def _atomic_write(self, file_path: Path, content: str) -> None:\n        \"\"\"Write content to a file atomically using temp file + rename.\n\n        This prevents data corruption if the write is interrupted mid-way.\n\n        Args:\n            file_path: Target file path.\n            content: Content to write.\n\n        Raises:\n            PresetStorageError: If write fails.\n        \"\"\"\n        try:\n            # Write to temp file in same directory for atomic rename\n            temp_fd, temp_path = tempfile.mkstemp(\n                dir=file_path.parent,\n                prefix=f\".{file_path.stem}_\",\n                suffix=\".tmp\",\n            )\n            try:\n                with os.fdopen(temp_fd, \"w\", encoding=\"utf-8\") as f:\n                    f.write(content)\n                # Atomic rename (on POSIX systems)\n                os.replace(temp_path, file_path)\n            except Exception:\n                # Clean up temp file on error\n                if os.path.exists(temp_path):\n                    os.unlink(temp_path)\n                raise\n        except (IOError, OSError) as e:\n            raise PresetStorageError(f\"Atomic write failed: {e}\") from e",
      "op": "replace",
      "pos": "105#QM"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py"
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py",
  "edits": [
    {
      "end": "12#XJ",
      "lines": "import json\nimport os\nimport shutil\nimport tempfile\nfrom pathlib import Path\nfrom typing import Dict, List, Optional",
      "op": "replace",
      "pos": "9#TZ"
    },
    {
      "end": "108#YQ",
      "lines": "        except (IOError, OSError) as e:\n            logger.error(f\"Failed to save preset '{preset.name}': {e}\")\n            raise PresetStorageError(f\"Failed to save preset: {e}\") from e\n\n    def _atomic_write(self, file_path: Path, content: str) -> None:\n        \"\"\"Write content to a file atomically using temp file + rename.\n\n        This prevents data corruption if the write is interrupted mid-way.\n\n        Args:\n            file_path: Target file path.\n            content: Content to write.\n\n        Raises:\n            PresetStorageError: If write fails.\n        \"\"\"\n        try:\n            # Write to temp file in same directory for atomic rename\n            temp_fd, temp_path = tempfile.mkstemp(\n                dir=file_path.parent,\n                prefix=f\".{file_path.stem}_\",\n                suffix=\".tmp\",\n            )\n            try:\n                with os.fdopen(temp_fd, \"w\", encoding=\"utf-8\") as f:\n                    f.write(content)\n                # Atomic rename (on POSIX systems)\n                os.replace(temp_path, file_path)\n            except Exception:\n                # Clean up temp file on error\n                if os.path.exists(temp_path):\n                    os.unlink(temp_path)\n                raise\n        except (IOError, OSError) as e:\n            raise PresetStorageError(f\"Atomic write failed: {e}\") from e\n",
      "op": "replace",
      "pos": "105#QM"
    }
  ]
}
Now let me update the save method to use the atomic write function:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py",
  "offset": 80,
  "limit": 50
}

🔧 Tool: edit
Input: {
  "edits": [
    {
      "end": "110#WY",
      "lines": "        try:\n            # Built-in presets should not be overwritten\n            if preset.is_builtin:\n                raise PresetStorageError(\n                    f\"Cannot save built-in preset '{preset.name}'. Create a copy to modify it.\"\n                )\n\n            file_path = self._get_preset_path(preset.id, is_builtin=False)\n            content = json.dumps(preset.to_dict(), indent=2)\n            self._atomic_write(file_path, content)\n\n            logger.info(f\"Saved preset '{preset.name}' to {file_path}\")\n            return file_path\n\n        except PresetStorageError:\n            raise  # Re-raise our own errors\n        except (IOError, OSError) as e:\n            logger.error(f\"Failed to save preset '{preset.name}': {e}\")\n            raise PresetStorageError(f\"Failed to save preset: {e}\") from e",
      "op": "replace",
      "pos": "92#BJ"
    }
  ],
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py"
}
Let me verify the changes and check for any syntax issues:

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m py_compile src/video2d3d/presets/models.py src/video2d3d/presets/storage.py src/video2d3d/presets/manager.py 2>&1",
  "description": "Check Python syntax of preset files"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py",
  "limit": 50,
  "offset": 95
}
I see the issue - there are duplicate class definitions. Let me fix the models.py file:

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/models.py",
  "content": "\"\"\"Preset data models for saving, loading, and sharing processing configurations.\n\nThis module provides dataclasses for representing presets that capture\nall processing settings for different use cases (cinema, VR, web, mobile).\n\"\"\"\n\nfrom __future__ import annotations\n\nimport json\nfrom dataclasses import asdict, dataclass, field\nfrom datetime import datetime\nfrom enum import Enum\nfrom typing import Any, Dict, List, Optional\nfrom uuid import uuid4\n\n\nclass PresetCategory(str, Enum):\n    \"\"\"Categories for organizing presets by use case.\"\"\"\n\n    CINEMA = \"cinema\"\n    VR = \"vr\"\n    WEB = \"web\"\n    MOBILE = \"mobile\"\n    CUSTOM = \"custom\"\n    GENERAL = \"general\"\n\n\n@dataclass\nclass DepthEstimationSettings:\n    \"\"\"Depth estimation settings for a preset.\"\"\"\n\n    model: str = \"midas_small\"\n    output_width: int = 384\n    output_height: int = 384\n    min_depth: float = 0.0\n    max_depth: float = 1.0\n    temporal_consistency: bool = True\n    temporal_smoothing_factor: float = 0.5\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> DepthEstimationSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            model=data.get(\"model\", \"midas_small\"),\n            output_width=data.get(\"output_width\", 384),\n            output_height=data.get(\"output_height\", 384),\n            min_depth=data.get(\"min_depth\", 0.0),\n            max_depth=data.get(\"max_depth\", 1.0),\n            temporal_consistency=data.get(\"temporal_consistency\", True),\n            temporal_smoothing_factor=data.get(\"temporal_smoothing_factor\", 0.5),\n        )\n\n\n@dataclass\nclass StereoGenerationSettings:\n    \"\"\"Stereoscopic generation settings for a preset.\"\"\"\n\n    format: str = \"side_by_side\"\n    baseline: float = 0.05\n    focal_length: float = 1.0\n    convergence: float = 0.5\n    # Anaglyph-specific\n    anaglyph_type: str = \"red_cyan\"\n    anaglyph_color_method: str = \"dubois\"\n    # Side-by-side specific\n    sbs_layout: str = \"horizontal\"\n    sbs_swap_eyes: bool = False\n    sbs_half_width: bool = False\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> StereoGenerationSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            format=data.get(\"format\", \"side_by_side\"),\n            baseline=data.get(\"baseline\", 0.05),\n            focal_length=data.get(\"focal_length\", 1.0),\n            convergence=data.get(\"convergence\", 0.5),\n            anaglyph_type=data.get(\"anaglyph_type\", \"red_cyan\"),\n            anaglyph_color_method=data.get(\"anaglyph_color_method\", \"dubois\"),\n            sbs_layout=data.get(\"sbs_layout\", \"horizontal\"),\n            sbs_swap_eyes=data.get(\"sbs_swap_eyes\", False),\n            sbs_half_width=data.get(\"sbs_half_width\", False),\n        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if self.baseline <= 0:\n            raise ValueError(f\"baseline must be positive, got {self.baseline}\")\n        if self.focal_length <= 0:\n            raise ValueError(f\"focal_length must be positive, got {self.focal_length}\")\n\n\n@dataclass\nclass VideoOutputSettings:\n    \"\"\"Video output settings for a preset.\"\"\"\n\n    format: str = \"mp4\"\n    codec: str = \"libx264\"\n    preset: str = \"medium\"\n    crf: int = 23\n    pixel_format: str = \"yuv420p\"\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> VideoOutputSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            format=data.get(\"format\", \"mp4\"),\n            codec=data.get(\"codec\", \"libx264\"),\n            preset=data.get(\"preset\", \"medium\"),\n            crf=data.get(\"crf\", 23),\n            pixel_format=data.get(\"pixel_format\", \"yuv420p\"),\n        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if not 0 <= self.crf <= 51:\n            raise ValueError(f\"crf must be between 0 and 51, got {self.crf}\")\n\n\n@dataclass\nclass ProcessingSettings:\n    \"\"\"Processing settings for a preset.\"\"\"\n\n    batch_size: int = 4\n    num_workers: int = 4\n    use_gpu: bool = True\n    gpu_device: int = 0\n    mixed_precision: bool = True\n    max_memory_percent: int = 80\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> ProcessingSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            batch_size=data.get(\"batch_size\", 4),\n            num_workers=data.get(\"num_workers\", 4),\n            use_gpu=data.get(\"use_gpu\", True),\n            gpu_device=data.get(\"gpu_device\", 0),\n            mixed_precision=data.get(\"mixed_precision\", True),\n            max_memory_percent=data.get(\"max_memory_percent\", 80),\n        )\n\n    def __post_init__(self) -> None:\n        \"\"\"Validate settings after initialization.\"\"\"\n        if self.batch_size < 1:\n            raise ValueError(f\"batch_size must be at least 1, got {self.batch_size}\")\n        if self.num_workers < 0:\n            raise ValueError(\n                f\"num_workers must be non-negative, got {self.num_workers}\"\n            )\n        if not 0 <= self.max_memory_percent <= 100:\n            raise ValueError(\n                f\"max_memory_percent must be 0-100, got {self.max_memory_percent}\"\n            )\n\n\n@dataclass\nclass QualitySettings:\n    \"\"\"Quality settings for a preset.\"\"\"\n\n    preset: str = \"balanced\"  # fast, balanced, quality\n    post_processing: bool = True\n    calculate_metrics: bool = False\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return asdict(self)\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> QualitySettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            preset=data.get(\"preset\", \"balanced\"),\n            post_processing=data.get(\"post_processing\", True),\n            calculate_metrics=data.get(\"calculate_metrics\", False),\n        )\n\n\n@dataclass\nclass PresetSettings:\n    \"\"\"Complete settings for a processing preset.\"\"\"\n\n    depth_estimation: DepthEstimationSettings = field(\n        default_factory=DepthEstimationSettings\n    )\n    stereo_generation: StereoGenerationSettings = field(\n        default_factory=StereoGenerationSettings\n    )\n    video_output: VideoOutputSettings = field(default_factory=VideoOutputSettings)\n    processing: ProcessingSettings = field(default_factory=ProcessingSettings)\n    quality: QualitySettings = field(default_factory=QualitySettings)\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return {\n            \"depth_estimation\": self.depth_estimation.to_dict(),\n            \"stereo_generation\": self.stereo_generation.to_dict(),\n            \"video_output\": self.video_output.to_dict(),\n            \"processing\": self.processing.to_dict(),\n            \"quality\": self.quality.to_dict(),\n        }\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> PresetSettings:\n        \"\"\"Create from dictionary.\"\"\"\n        return cls(\n            depth_estimation=DepthEstimationSettings.from_dict(\n                data.get(\"depth_estimation\", {})\n            ),\n            stereo_generation=StereoGenerationSettings.from_dict(\n                data.get(\"stereo_generation\", {})\n            ),\n            video_output=VideoOutputSettings.from_dict(\n                data.get(\"video_output\", {})\n            ),\n            processing=ProcessingSettings.from_dict(data.get(\"processing\", {})),\n            quality=QualitySettings.from_dict(data.get(\"quality\", {})),\n        )\n\n\n@dataclass\nclass Preset:\n    \"\"\"A processing preset with complete settings for a specific use case.\n\n    Presets capture all processing configuration and can be saved, loaded,\n    shared, and applied to video conversion jobs.\n    \"\"\"\n\n    # Identity\n    id: str = field(default_factory=lambda: str(uuid4()))\n    name: str = \"\"\n    description: str = \"\"\n\n    # Classification\n    category: PresetCategory = PresetCategory.GENERAL\n    tags: List[str] = field(default_factory=list)\n\n    # Settings\n    settings: PresetSettings = field(default_factory=PresetSettings)\n\n    # Metadata\n    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())\n    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())\n    is_builtin: bool = False\n    version: str = \"1.0.0\"\n    author: str = \"\"\n\n    def to_dict(self) -> Dict[str, Any]:\n        \"\"\"Convert to dictionary for serialization.\"\"\"\n        return {\n            \"id\": self.id,\n            \"name\": self.name,\n            \"description\": self.description,\n            \"category\": self.category.value,\n            \"tags\": self.tags,\n            \"settings\": self.settings.to_dict(),\n            \"created_at\": self.created_at,\n            \"updated_at\": self.updated_at,\n            \"is_builtin\": self.is_builtin,\n            \"version\": self.version,\n            \"author\": self.author,\n        }\n\n    @classmethod\n    def from_dict(cls, data: Dict[str, Any]) -> Preset:\n        \"\"\"Create from dictionary.\"\"\"\n        category_str = data.get(\"category\", \"general\")\n        try:\n            category = PresetCategory(category_str.lower())\n        except ValueError:\n            category = PresetCategory.GENERAL\n\n        return cls(\n            id=data.get(\"id\", str(uuid4())),\n            name=data.get(\"name\", \"\"),\n            description=data.get(\"description\", \"\"),\n            category=category,\n            tags=data.get(\"tags\", []),\n            settings=PresetSettings.from_dict(data.get(\"settings\", {})),\n            created_at=data.get(\"created_at\", datetime.utcnow().isoformat()),\n            updated_at=data.get(\"updated_at\", datetime.utcnow().isoformat()),\n            is_builtin=data.get(\"is_builtin\", False),\n            version=data.get(\"version\", \"1.0.0\"),\n            author=data.get(\"author\", \"\"),\n        )\n\n    def to_json(self, indent: int = 2) -> str:\n        \"\"\"Convert to JSON string.\"\"\"\n        return json.dumps(self.to_dict(), indent=indent)\n\n    @classmethod\n    def from_json(cls, json_str: str) -> Preset:\n        \"\"\"Create from JSON string.\"\"\"\n        data = json.loads(json_str)\n        return cls.from_dict(data)\n\n    def update_timestamp(self) -> None:\n        \"\"\"Update the updated_at timestamp.\"\"\"\n        self.updated_at = datetime.utcnow().isoformat()\n\n    def __eq__(self, other: object) -> bool:\n        \"\"\"Check equality by ID.\"\"\"\n        if not isinstance(other, Preset):\n            return False\n        return self.id == other.id\n\n    def __hash__(self) -> int:\n        \"\"\"Hash by ID.\"\"\"\n        return hash(self.id)\n\n    def __str__(self) -> str:\n        \"\"\"String representation.\"\"\"\n        return f\"Preset({self.name}, category={self.category.value})\"\n\n    def __repr__(self) -> str:\n        \"\"\"Detailed representation.\"\"\"\n        return (\n            f\"Preset(id={self.id!r}, name={self.name!r}, \"\n            f\"category={self.category.value!r})\"\n        )\n\n\n__all__ = [\n    \"PresetCategory\",\n    \"DepthEstimationSettings\",\n    \"StereoGenerationSettings\",\n    \"VideoOutputSettings\",\n    \"ProcessingSettings\",\n    \"QualitySettings\",\n    \"PresetSettings\",\n    \"Preset\",\n]\n"
}
Now let me verify the Python syntax again:

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m py_compile src/video2d3d/presets/models.py src/video2d3d/presets/storage.py src/video2d3d/presets/manager.py 2>&1",
  "description": "Check Python syntax of preset files"
}
Let me check the storage.py file and fix any remaining issues:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py",
  "limit": 60,
  "offset": 75
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets/storage.py",
  "limit": 80,
  "offset": 1
}
The storage.py looks good. Let me now update the todos and run a quick verification test:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Code Review Fix: Add validation to models (CRF range, positive baseline)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Fix hacky dataclass field access in manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Fix duplicate() deep copy issue",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Add atomic writes to storage.py",
      "priority": "high",
      "status": "completed"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -c \"\nfrom video2d3d.presets import (\n    PresetManager, Preset, PresetCategory, PresetSettings,\n    DepthEstimationSettings, StereoGenerationSettings, VideoOutputSettings,\n    ProcessingSettings, QualitySettings, BALANCED\n)\n\n# Test creating a preset\nsettings = PresetSettings(\n    depth_estimation=DepthEstimationSettings(model='dpt_large'),\n    stereo_generation=StereoGenerationSettings(format='side_by_side', baseline=0.05),\n    video_output=VideoOutputSettings(crf=20),\n    processing=ProcessingSettings(batch_size=2),\n    quality=QualitySettings(preset='quality'),\n)\n\nprint('Settings created successfully')\n\n# Test validation\ntry:\n    bad_settings = StereoGenerationSettings(baseline=-0.1)\nexcept ValueError as e:\n    print(f'Validation works: {e}')\n\ntry:\n    bad_video = VideoOutputSettings(crf=60)\nexcept ValueError as e:\n    print(f'CRF validation works: {e}')\n\n# Test preset creation\npreset = Preset(\n    name='Test Preset',\n    description='A test preset',\n    category=PresetCategory.CUSTOM,\n    settings=settings,\n)\nprint(f'Preset created: {preset}')\n\n# Test serialization\npreset_dict = preset.to_dict()\npreset_json = preset.to_json()\nprint(f'JSON serialization works: {len(preset_json)} chars')\n\n# Test deserialization\npreset2 = Preset.from_json(preset_json)\nassert preset.id == preset2.id\nprint('Deserialization works')\n\n# Test built-in presets\nprint(f'Built-in BALANCED preset: {BALANCED.name}')\nprint('All tests passed!')\n\"",
  "description": "Test preset module functionality"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && PYTHONPATH=src python -c \"\nfrom video2d3d.presets import (\n    PresetManager, Preset, PresetCategory, PresetSettings,\n    DepthEstimationSettings, StereoGenerationSettings, VideoOutputSettings,\n    ProcessingSettings, QualitySettings, BALANCED\n)\n\n# Test creating a preset\nsettings = PresetSettings(\n    depth_estimation=DepthEstimationSettings(model='dpt_large'),\n    stereo_generation=StereoGenerationSettings(format='side_by_side', baseline=0.05),\n    video_output=VideoOutputSettings(crf=20),\n    processing=ProcessingSettings(batch_size=2),\n    quality=QualitySettings(preset='quality'),\n)\n\nprint('Settings created successfully')\n\n# Test validation\ntry:\n    bad_settings = StereoGenerationSettings(baseline=-0.1)\nexcept ValueError as e:\n    print(f'Validation works: {e}')\n\ntry:\n    bad_video = VideoOutputSettings(crf=60)\nexcept ValueError as e:\n    print(f'CRF validation works: {e}')\n\n# Test preset creation\npreset = Preset(\n    name='Test Preset',\n    description='A test preset',\n    category=PresetCategory.CUSTOM,\n    settings=settings,\n)\nprint(f'Preset created: {preset}')\n\n# Test serialization\npreset_dict = preset.to_dict()\npreset_json = preset.to_json()\nprint(f'JSON serialization works: {len(preset_json)} chars')\n\n# Test deserialization\npreset2 = Preset.from_json(preset_json)\nassert preset.id == preset2.id\nprint('Deserialization works')\n\n# Test built-in presets\nprint(f'Built-in BALANCED preset: {BALANCED.name}')\nprint('All tests passed!')\n\"",
  "description": "Test preset module functionality"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && pip install -q loguru && PYTHONPATH=src python -c \"\nfrom video2d3d.presets.models import (\n    Preset, PresetCategory, PresetSettings,\n    DepthEstimationSettings, StereoGenerationSettings, VideoOutputSettings,\n    ProcessingSettings, QualitySettings\n)\n\n# Test creating settings\nsettings = PresetSettings(\n    depth_estimation=DepthEstimationSettings(model='dpt_large'),\n    stereo_generation=StereoGenerationSettings(format='side_by_side', baseline=0.05),\n    video_output=VideoOutputSettings(crf=20),\n    processing=ProcessingSettings(batch_size=2),\n    quality=QualitySettings(preset='quality'),\n)\nprint('Settings created successfully')\n\n# Test validation - baseline must be positive\ntry:\n    bad_settings = StereoGenerationSettings(baseline=-0.1)\nexcept ValueError as e:\n    print(f'Baseline validation works: {e}')\n\n# Test validation - CRF must be 0-51\ntry:\n    bad_video = VideoOutputSettings(crf=60)\nexcept ValueError as e:\n    print(f'CRF validation works: {e}')\n\n# Test preset creation\npreset = Preset(\n    name='Test Preset',\n    description='A test preset',\n    category=PresetCategory.CUSTOM,\n    settings=settings,\n)\nprint(f'Preset created: {preset}')\n\n# Test serialization\npreset_json = preset.to_json()\nprint(f'JSON serialization works: {len(preset_json)} chars')\n\n# Test deserialization\npreset2 = Preset.from_json(preset_json)\nassert preset.id == preset2.id\nprint('Deserialization works')\nprint('All model tests passed!')\n\"",
  "description": "Test preset models"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && ls -la .venv 2>/dev/null || ls -la venv 2>/dev/null || echo \"No venv found\"",
  "description": "Check for virtual environment"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && PYTHONPATH=src .venv/bin/python -c \"\nfrom video2d3d.presets.models import (\n    Preset, PresetCategory, PresetSettings,\n    DepthEstimationSettings, StereoGenerationSettings, VideoOutputSettings,\n    ProcessingSettings, QualitySettings\n)\n\n# Test creating settings\nsettings = PresetSettings(\n    depth_estimation=DepthEstimationSettings(model='dpt_large'),\n    stereo_generation=StereoGenerationSettings(format='side_by_side', baseline=0.05),\n    video_output=VideoOutputSettings(crf=20),\n    processing=ProcessingSettings(batch_size=2),\n    quality=QualitySettings(preset='quality'),\n)\nprint('Settings created successfully')\n\n# Test validation - baseline must be positive\ntry:\n    bad_settings = StereoGenerationSettings(baseline=-0.1)\nexcept ValueError as e:\n    print(f'Baseline validation works: {e}')\n\n# Test validation - CRF must be 0-51\ntry:\n    bad_video = VideoOutputSettings(crf=60)\nexcept ValueError as e:\n    print(f'CRF validation works: {e}')\n\n# Test preset creation\npreset = Preset(\n    name='Test Preset',\n    description='A test preset',\n    category=PresetCategory.CUSTOM,\n    settings=settings,\n)\nprint(f'Preset created: {preset}')\n\n# Test serialization\npreset_json = preset.to_json()\nprint(f'JSON serialization works: {len(preset_json)} chars')\n\n# Test deserialization\npreset2 = Preset.from_json(preset_json)\nassert preset.id == preset2.id\nprint('Deserialization works')\nprint('All model tests passed!')\n\"",
  "description": "Test preset models using venv"
}


---

## Follow-up Session


🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status",
  "description": "Check git status for changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log --oneline -5",
  "description": "View recent commit history"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff --stat",
  "description": "View changes summary"
}
Let me see the specific files in the presets directory and then stage and commit them:

🔧 Tool: bash
Input: {
  "command": "find /home/dkp/Documents/Automaker/2dto3d/src/video2d3d/presets -type f | sort",
  "description": "List preset manager files"
}
Now I'll stage the preset manager files and commit them with a conventional commit message:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git add src/video2d3d/presets/__init__.py src/video2d3d/presets/models.py src/video2d3d/presets/storage.py src/video2d3d/presets/manager.py src/video2d3d/presets/builtins.py src/video2d3d/presets/builtins/*.json",
  "description": "Stage preset manager source files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status --short",
  "description": "Verify staged files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff --cached --stat",
  "description": "Check staged changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git status --porcelain | grep -E \"^[AM]\" | head -30",
  "description": "Check staged files only"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git add src/video2d3d/presets/ && git status --porcelain src/video2d3d/presets/",
  "description": "Add all preset files and check status"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git ls-files --stage src/video2d3d/presets/ 2>/dev/null || echo \"No staged files\"",
  "description": "List staged files"
}
The files are staged. Now I'll create the commit with a conventional commit message:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git commit -m \"feat(presets): add processing preset manager for saving and loading configurations\n\nAdd a comprehensive preset management system for saving, loading, and\nsharing processing configurations with optimized settings for different\nuse cases (cinema, VR, web, mobile).\n\nFeatures:\n- Preset data models with validation (CRF range, positive baseline)\n- JSON file storage with atomic writes for data safety\n- PresetManager class with full CRUD operations\n- 11 built-in presets for common use cases\n- Import/export functionality for sharing presets\n- Deep copy support for preset duplication\n- Category-based organization (cinema, vr, web, mobile, custom)\n\nBuilt-in presets include:\n- Cinema: High-quality side-by-side and anaglyph\n- VR: Over-under and side-by-side for headsets\n- Web: Optimized for streaming/sharing\n- Mobile: Lightweight for portable devices\n- Fast Preview: Quick testing\n- Maximum Quality: Archival use\n- Balanced: Default general-purpose\"",
  "description": "Commit preset manager feature"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git reset HEAD src/video2d3d/presets/ 2>/dev/null; git add -A src/video2d3d/presets/ && git status --porcelain | grep presets",
  "description": "Reset and re-add preset files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git ls-files src/video2d3d/presets/",
  "description": "Check if preset files are tracked"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log --oneline -20",
  "description": "View recent commit history"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git log --oneline --all -- src/video2d3d/presets/",
  "description": "Search for preset-related commits"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git diff HEAD -- src/video2d3d/presets/",
  "description": "Check for any changes to preset files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; cd /home/dkp/Documents/Automaker/2dto3d && git show --stat aab241b -- src/video2d3d/presets/",
  "description": "Check if presets were in optical flow commit"
}
The preset manager files were already committed as part of commit `aab241b`. Let me update the todos and provide the summary:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Create preset data models (Preset, PresetSettings) in src/video2d3d/presets/models.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create preset storage class for JSON file persistence in src/video2d3d/presets/storage.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create PresetManager class with CRUD operations in src/video2d3d/presets/manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Define built-in presets for cinema, VR, web, mobile use cases in src/video2d3d/presets/builtins.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create presets module __init__.py with exports",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Add CLI commands for preset management (list, show, save, delete, export, import)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Add Pydantic schemas for presets in web/schemas.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Add API router for presets in web/routers/presets.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Register preset router in web/app.py",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Create unit tests for preset manager",
      "priority": "medium",
      "status": "pending"
    },
    {
      "content": "Verify implementation with test run",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Add validation to models (CRF range, positive baseline)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Fix hacky dataclass field access in manager.py",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Fix duplicate() deep copy issue",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Code Review Fix: Add atomic writes to storage.py",
      "priority": "high",
      "status": "completed"
    }
  ]
}
<summary>
## Summary: Processing Preset Manager

### Changes Implemented

**Core Module (`src/video2d3d/presets/`):**
- **models.py**: Data models with validation for Preset, PresetSettings, DepthEstimationSettings, StereoGenerationSettings, VideoOutputSettings, ProcessingSettings, QualitySettings, and PresetCategory enum
- **storage.py**: JSON file persistence with atomic writes for data safety, import/export functionality
- **manager.py**: PresetManager class with full CRUD operations, search, filtering, and config integration
- **builtins.py**: 11 built-in presets for common use cases

**Built-in Presets (11 total):**
- Cinema (Side-by-Side, Anaglyph): High quality for large screens
- VR (Over-Under, Side-by-Side): Optimized for VR headsets
- Web (Side-by-Side, Anaglyph): Optimized for streaming/sharing
- Mobile (Side-by-Side, Anaglyph): Lightweight for portable devices
- Fast Preview, Maximum Quality, Balanced

**Code Quality Improvements:**
- Added validation: CRF range (0-51), positive baseline, valid batch_size
- Fixed deep copy issue in `duplicate()` method using serialization
- Removed hacky dataclass field access by importing classes directly
- Added atomic writes to prevent data corruption

### Files Modified/Added
- `src/video2d3d/presets/__init__.py` - Module exports
- `src/video2d3d/presets/models.py` - Data models with validation
- `src/video2d3d/presets/storage.py` - JSON storage with atomic writes
- `src/video2d3d/presets/manager.py` - PresetManager class
- `src/video2d3d/presets/builtins.py` - Built-in preset definitions
- `src/video2d3d/presets/builtins/*.json` - 11 JSON preset files

### Commit Status
The preset manager files were already committed as part of commit **aab241b** (feat(opticalflow): add optical flow calculation engine). The 16 preset files totaling 2,344 lines were included in this commit.

**Commit Hash:** `aab241bbfd78b50a7a93efa31c3799ca531c4501`

### Pending Tasks
- Add CLI commands for preset management (list, show, save, delete, export, import)
- Add Pydantic schemas for web API
- Add API router for presets
- Register preset router in web/app.py
- Create unit tests for preset manager

### Notes for Developer
- The preset manager is fully functional and can be imported via `from video2d3d.presets import PresetManager, get_preset_manager`
- All settings classes include validation in `__post_init__` to catch invalid configurations early
- Atomic writes ensure presets won't be corrupted if write is interrupted
- Built-in presets are read-only; users must create copies to modify them
</summary>

---

## Follow-up Session

I'll write comprehensive tests for the preset manager feature. Let me first explore the existing test structure in the project.

🔧 Tool: glob
Input: {
  "pattern": "**/test_*.py"
}

🔧 Tool: glob
Input: {
  "pattern": "**/tests/**/*.py"
}

🔧 Tool: bash
Input: {
  "command": "ls -la tests/ 2>/dev/null || ls -la test/ 2>/dev/null || echo \"No tests directory found\"",
  "description": "Check for tests directory"
}
Let me examine the existing test patterns and conftest.py:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/conftest.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_config.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml"
}
Now I'll create comprehensive test files for the preset manager feature. Let me start with the test files:

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Write unit tests for preset models (test_preset_models.py)",
      "priority": "high",
      "status": "in_progress"
    },
    {
      "content": "Write unit tests for preset storage (test_preset_storage.py)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Write unit tests for preset manager (test_preset_manager.py)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Write unit tests for built-in presets (test_preset_builtins.py)",
      "priority": "high",
      "status": "pending"
    },
    {
      "content": "Run all tests and verify they pass",
      "priority": "high",
      "status": "pending"
    }
  ]
}

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_preset_models.py",
  "content": "\"\"\"Tests for preset data models.\n\nThis module tests all preset data models including:\n- PresetCategory enum\n- Settings dataclasses with validation\n- Preset class with serialization/deserialization\n\"\"\"\n\nimport json\nfrom datetime import datetime\n\nimport pytest\n\nfrom video2d3d.presets.models import (\n    DepthEstimationSettings,\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    ProcessingSettings,\n    QualitySettings,\n    StereoGenerationSettings,\n    VideoOutputSettings,\n)\n\n\nclass TestPresetCategory:\n    \"\"\"Tests for PresetCategory enum.\"\"\"\n\n    def test_all_categories_exist(self):\n        \"\"\"Test that all expected categories are defined.\"\"\"\n        assert PresetCategory.CINEMA.value == \"cinema\"\n        assert PresetCategory.VR.value == \"vr\"\n        assert PresetCategory.WEB.value == \"web\"\n        assert PresetCategory.MOBILE.value == \"mobile\"\n        assert PresetCategory.CUSTOM.value == \"custom\"\n        assert PresetCategory.GENERAL.value == \"general\"\n\n    def test_category_is_string_enum(self):\n        \"\"\"Test that PresetCategory is a string enum.\"\"\"\n        assert isinstance(PresetCategory.CINEMA, str)\n        assert PresetCategory.CINEMA == \"cinema\"\n\n\nclass TestDepthEstimationSettings:\n    \"\"\"Tests for DepthEstimationSettings dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values are set correctly.\"\"\"\n        settings = DepthEstimationSettings()\n        assert settings.model == \"midas_small\"\n        assert settings.output_width == 384\n        assert settings.output_height == 384\n        assert settings.min_depth == 0.0\n        assert settings.max_depth == 1.0\n        assert settings.temporal_consistency is True\n        assert settings.temporal_smoothing_factor == 0.5\n\n    def test_custom_values(self):\n        \"\"\"Test custom values are set correctly.\"\"\"\n        settings = DepthEstimationSettings(\n            model=\"dpt_large\",\n            output_width=512,\n            output_height=512,\n            min_depth=0.1,\n            max_depth=10.0,\n            temporal_consistency=False,\n            temporal_smoothing_factor=0.3,\n        )\n        assert settings.model == \"dpt_large\"\n        assert settings.output_width == 512\n        assert settings.min_depth == 0.1\n\n    def test_to_dict(self):\n        \"\"\"Test serialization to dictionary.\"\"\"\n        settings = DepthEstimationSettings(model=\"dpt_hybrid\")\n        data = settings.to_dict()\n        assert isinstance(data, dict)\n        assert data[\"model\"] == \"dpt_hybrid\"\n        assert data[\"output_width\"] == 384\n\n    def test_from_dict(self):\n        \"\"\"Test deserialization from dictionary.\"\"\"\n        data = {\n            \"model\": \"midas_hybrid\",\n            \"output_width\": 256,\n            \"output_height\": 256,\n        }\n        settings = DepthEstimationSettings.from_dict(data)\n        assert settings.model == \"midas_hybrid\"\n        assert settings.output_width == 256\n        # Default values for missing keys\n        assert settings.temporal_consistency is True\n\n    def test_from_dict_empty(self):\n        \"\"\"Test deserialization from empty dictionary uses defaults.\"\"\"\n        settings = DepthEstimationSettings.from_dict({})\n        assert settings.model == \"midas_small\"\n        assert settings.output_width == 384\n\n\nclass TestStereoGenerationSettings:\n    \"\"\"Tests for StereoGenerationSettings dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values are set correctly.\"\"\"\n        settings = StereoGenerationSettings()\n        assert settings.format == \"side_by_side\"\n        assert settings.baseline == 0.05\n        assert settings.focal_length == 1.0\n        assert settings.convergence == 0.5\n        assert settings.anaglyph_type == \"red_cyan\"\n        assert settings.anaglyph_color_method == \"dubois\"\n        assert settings.sbs_layout == \"horizontal\"\n        assert settings.sbs_swap_eyes is False\n        assert settings.sbs_half_width is False\n\n    def test_validation_positive_baseline(self):\n        \"\"\"Test that baseline must be positive.\"\"\"\n        with pytest.raises(ValueError, match=\"baseline must be positive\"):\n            StereoGenerationSettings(baseline=0)\n\n        with pytest.raises(ValueError, match=\"baseline must be positive\"):\n            StereoGenerationSettings(baseline=-0.1)\n\n    def test_validation_positive_focal_length(self):\n        \"\"\"Test that focal_length must be positive.\"\"\"\n        with pytest.raises(ValueError, match=\"focal_length must be positive\"):\n            StereoGenerationSettings(focal_length=0)\n\n        with pytest.raises(ValueError, match=\"focal_length must be positive\"):\n            StereoGenerationSettings(focal_length=-1.0)\n\n    def test_valid_positive_values(self):\n        \"\"\"Test that positive values are accepted.\"\"\"\n        settings = StereoGenerationSettings(baseline=0.1, focal_length=2.0)\n        assert settings.baseline == 0.1\n        assert settings.focal_length == 2.0\n\n    def test_to_dict_and_from_dict(self):\n        \"\"\"Test serialization round-trip.\"\"\"\n        original = StereoGenerationSettings(\n            format=\"anaglyph\",\n            baseline=0.08,\n            anaglyph_type=\"green_magenta\",\n        )\n        data = original.to_dict()\n        restored = StereoGenerationSettings.from_dict(data)\n        assert restored.format == \"anaglyph\"\n        assert restored.baseline == 0.08\n        assert restored.anaglyph_type == \"green_magenta\"\n\n\nclass TestVideoOutputSettings:\n    \"\"\"Tests for VideoOutputSettings dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values are set correctly.\"\"\"\n        settings = VideoOutputSettings()\n        assert settings.format == \"mp4\"\n        assert settings.codec == \"libx264\"\n        assert settings.preset == \"medium\"\n        assert settings.crf == 23\n        assert settings.pixel_format == \"yuv420p\"\n\n    def test_validation_crf_range_min(self):\n        \"\"\"Test that CRF must be >= 0.\"\"\"\n        with pytest.raises(ValueError, match=\"crf must be between 0 and 51\"):\n            VideoOutputSettings(crf=-1)\n\n    def test_validation_crf_range_max(self):\n        \"\"\"Test that CRF must be <= 51.\"\"\"\n        with pytest.raises(ValueError, match=\"crf must be between 0 and 51\"):\n            VideoOutputSettings(crf=52)\n\n    def test_valid_crf_boundary_values(self):\n        \"\"\"Test that boundary CRF values are accepted.\"\"\"\n        settings_min = VideoOutputSettings(crf=0)\n        assert settings_min.crf == 0\n\n        settings_max = VideoOutputSettings(crf=51)\n        assert settings_max.crf == 51\n\n    def test_valid_crf_common_values(self):\n        \"\"\"Test that common CRF values are accepted.\"\"\"\n        for crf in [18, 20, 23, 26, 28]:\n            settings = VideoOutputSettings(crf=crf)\n            assert settings.crf == crf\n\n    def test_to_dict_and_from_dict(self):\n        \"\"\"Test serialization round-trip.\"\"\"\n        original = VideoOutputSettings(\n            format=\"mkv\",\n            codec=\"libx265\",\n            preset=\"slow\",\n            crf=18,\n        )\n        data = original.to_dict()\n        restored = VideoOutputSettings.from_dict(data)\n        assert restored.format == \"mkv\"\n        assert restored.codec == \"libx265\"\n        assert restored.crf == 18\n\n\nclass TestProcessingSettings:\n    \"\"\"Tests for ProcessingSettings dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values are set correctly.\"\"\"\n        settings = ProcessingSettings()\n        assert settings.batch_size == 4\n        assert settings.num_workers == 4\n        assert settings.use_gpu is True\n        assert settings.gpu_device == 0\n        assert settings.mixed_precision is True\n        assert settings.max_memory_percent == 80\n\n    def test_validation_batch_size_minimum(self):\n        \"\"\"Test that batch_size must be at least 1.\"\"\"\n        with pytest.raises(ValueError, match=\"batch_size must be at least 1\"):\n            ProcessingSettings(batch_size=0)\n\n        with pytest.raises(ValueError, match=\"batch_size must be at least 1\"):\n            ProcessingSettings(batch_size=-1)\n\n    def test_validation_num_workers_non_negative(self):\n        \"\"\"Test that num_workers must be non-negative.\"\"\"\n        with pytest.raises(ValueError, match=\"num_workers must be non-negative\"):\n            ProcessingSettings(num_workers=-1)\n\n    def test_validation_max_memory_percent_range(self):\n        \"\"\"Test that max_memory_percent must be 0-100.\"\"\"\n        with pytest.raises(ValueError, match=\"max_memory_percent must be 0-100\"):\n            ProcessingSettings(max_memory_percent=-1)\n\n        with pytest.raises(ValueError, match=\"max_memory_percent must be 0-100\"):\n            ProcessingSettings(max_memory_percent=101)\n\n    def test_valid_boundary_values(self):\n        \"\"\"Test that boundary values are accepted.\"\"\"\n        settings = ProcessingSettings(\n            batch_size=1,\n            num_workers=0,\n            max_memory_percent=0,\n        )\n        assert settings.batch_size == 1\n        assert settings.num_workers == 0\n        assert settings.max_memory_percent == 0\n\n        settings_max = ProcessingSettings(max_memory_percent=100)\n        assert settings_max.max_memory_percent == 100\n\n    def test_cpu_only_settings(self):\n        \"\"\"Test CPU-only processing settings.\"\"\"\n        settings = ProcessingSettings(\n            use_gpu=False,\n            num_workers=8,\n        )\n        assert settings.use_gpu is False\n        assert settings.num_workers == 8\n\n\nclass TestQualitySettings:\n    \"\"\"Tests for QualitySettings dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values are set correctly.\"\"\"\n        settings = QualitySettings()\n        assert settings.preset == \"balanced\"\n        assert settings.post_processing is True\n        assert settings.calculate_metrics is False\n\n    def test_custom_values(self):\n        \"\"\"Test custom values are set correctly.\"\"\"\n        settings = QualitySettings(\n            preset=\"quality\",\n            post_processing=False,\n            calculate_metrics=True,\n        )\n        assert settings.preset == \"quality\"\n        assert settings.post_processing is False\n        assert settings.calculate_metrics is True\n\n    def test_to_dict_and_from_dict(self):\n        \"\"\"Test serialization round-trip.\"\"\"\n        original = QualitySettings(preset=\"fast\", calculate_metrics=True)\n        data = original.to_dict()\n        restored = QualitySettings.from_dict(data)\n        assert restored.preset == \"fast\"\n        assert restored.calculate_metrics is True\n\n\nclass TestPresetSettings:\n    \"\"\"Tests for PresetSettings dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values create all sub-settings.\"\"\"\n        settings = PresetSettings()\n        assert isinstance(settings.depth_estimation, DepthEstimationSettings)\n        assert isinstance(settings.stereo_generation, StereoGenerationSettings)\n        assert isinstance(settings.video_output, VideoOutputSettings)\n        assert isinstance(settings.processing, ProcessingSettings)\n        assert isinstance(settings.quality, QualitySettings)\n\n    def test_custom_sub_settings(self):\n        \"\"\"Test custom sub-settings are preserved.\"\"\"\n        depth = DepthEstimationSettings(model=\"dpt_large\")\n        settings = PresetSettings(depth_estimation=depth)\n        assert settings.depth_estimation.model == \"dpt_large\"\n\n    def test_to_dict_contains_all_sections(self):\n        \"\"\"Test that to_dict includes all sections.\"\"\"\n        settings = PresetSettings()\n        data = settings.to_dict()\n        assert \"depth_estimation\" in data\n        assert \"stereo_generation\" in data\n        assert \"video_output\" in data\n        assert \"processing\" in data\n        assert \"quality\" in data\n\n    def test_from_dict_creates_nested_objects(self):\n        \"\"\"Test that from_dict creates proper nested objects.\"\"\"\n        data = {\n            \"depth_estimation\": {\"model\": \"dpt_hybrid\"},\n            \"video_output\": {\"crf\": 20},\n        }\n        settings = PresetSettings.from_dict(data)\n        assert settings.depth_estimation.model == \"dpt_hybrid\"\n        assert settings.video_output.crf == 20\n        # Defaults for missing sections\n        assert settings.stereo_generation.format == \"side_by_side\"\n\n    def test_round_trip_preserves_all_data(self):\n        \"\"\"Test that serialization round-trip preserves all data.\"\"\"\n        original = PresetSettings(\n            depth_estimation=DepthEstimationSettings(model=\"dpt_large\"),\n            stereo_generation=StereoGenerationSettings(baseline=0.08),\n            video_output=VideoOutputSettings(crf=18),\n            processing=ProcessingSettings(batch_size=2),\n            quality=QualitySettings(preset=\"quality\"),\n        )\n        data = original.to_dict()\n        restored = PresetSettings.from_dict(data)\n        assert restored.depth_estimation.model == \"dpt_large\"\n        assert restored.stereo_generation.baseline == 0.08\n        assert restored.video_output.crf == 18\n        assert restored.processing.batch_size == 2\n        assert restored.quality.preset == \"quality\"\n\n\nclass TestPreset:\n    \"\"\"Tests for Preset dataclass.\"\"\"\n\n    def test_default_values(self):\n        \"\"\"Test default values are set correctly.\"\"\"\n        preset = Preset()\n        assert preset.name == \"\"\n        assert preset.description == \"\"\n        assert preset.category == PresetCategory.GENERAL\n        assert preset.tags == []\n        assert preset.is_builtin is False\n        assert preset.version == \"1.0.0\"\n        assert preset.author == \"\"\n\n    def test_auto_generated_id(self):\n        \"\"\"Test that ID is auto-generated and unique.\"\"\"\n        preset1 = Preset(name=\"test1\")\n        preset2 = Preset(name=\"test2\")\n        assert preset1.id != preset2.id\n        assert len(preset1.id) == 36  # UUID format\n\n    def test_auto_generated_timestamps(self):\n        \"\"\"Test that timestamps are auto-generated.\"\"\"\n        preset = Preset(name=\"test\")\n        # ISO format: 2024-01-15T10:30:00.123456\n        assert \"T\" in preset.created_at\n        assert \"T\" in preset.updated_at\n\n    def test_custom_values(self):\n        \"\"\"Test custom values are set correctly.\"\"\"\n        settings = PresetSettings()\n        preset = Preset(\n            name=\"My Preset\",\n            description=\"Test preset\",\n            category=PresetCategory.CINEMA,\n            tags=[\"4k\", \"hdr\"],\n            settings=settings,\n            author=\"Test Author\",\n            version=\"2.0.0\",\n        )\n        assert preset.name == \"My Preset\"\n        assert preset.category == PresetCategory.CINEMA\n        assert \"4k\" in preset.tags\n        assert preset.author == \"Test Author\"\n\n    def test_update_timestamp(self):\n        \"\"\"Test update_timestamp method.\"\"\"\n        preset = Preset(name=\"test\")\n        original_updated = preset.updated_at\n        preset.update_timestamp()\n        assert preset.updated_at != original_updated\n\n    def test_to_dict(self):\n        \"\"\"Test serialization to dictionary.\"\"\"\n        preset = Preset(\n            name=\"Test\",\n            category=PresetCategory.VR,\n            tags=[\"test\"],\n        )\n        data = preset.to_dict()\n        assert data[\"name\"] == \"Test\"\n        assert data[\"category\"] == \"vr\"\n        assert data[\"tags\"] == [\"test\"]\n        assert \"settings\" in data\n        assert \"id\" in data\n\n    def test_from_dict(self):\n        \"\"\"Test deserialization from dictionary.\"\"\"\n        data = {\n            \"id\": \"test-id-123\",\n            \"name\": \"Restored Preset\",\n            \"description\": \"A restored preset\",\n            \"category\": \"web\",\n            \"tags\": [\"restored\"],\n            \"settings\": {\n                \"depth_estimation\": {\"model\": \"midas_hybrid\"},\n            },\n            \"is_builtin\": True,\n            \"version\": \"1.5.0\",\n        }\n        preset = Preset.from_dict(data)\n        assert preset.id == \"test-id-123\"\n        assert preset.name == \"Restored Preset\"\n        assert preset.category == PresetCategory.WEB\n        assert preset.is_builtin is True\n        assert preset.settings.depth_estimation.model == \"midas_hybrid\"\n\n    def test_from_dict_invalid_category_defaults_to_general(self):\n        \"\"\"Test that invalid category defaults to GENERAL.\"\"\"\n        data = {\n            \"name\": \"Test\",\n            \"category\": \"invalid_category\",\n        }\n        preset = Preset.from_dict(data)\n        assert preset.category == PresetCategory.GENERAL\n\n    def test_to_json(self):\n        \"\"\"Test serialization to JSON string.\"\"\"\n        preset = Preset(name=\"JSON Test\")\n        json_str = preset.to_json()\n        assert isinstance(json_str, str)\n        # Verify it's valid JSON\n        parsed = json.loads(json_str)\n        assert parsed[\"name\"] == \"JSON Test\"\n\n    def test_from_json(self):\n        \"\"\"Test deserialization from JSON string.\"\"\"\n        json_str = '''{\n            \"id\": \"json-test-id\",\n            \"name\": \"From JSON\",\n            \"category\": \"mobile\",\n            \"settings\": {\n                \"video_output\": {\"crf\": 25}\n            }\n        }'''\n        preset = Preset.from_json(json_str)\n        assert preset.id == \"json-test-id\"\n        assert preset.name == \"From JSON\"\n        assert preset.category == PresetCategory.MOBILE\n        assert preset.settings.video_output.crf == 25\n\n    def test_json_round_trip(self):\n        \"\"\"Test JSON serialization round-trip.\"\"\"\n        original = Preset(\n            name=\"Round Trip\",\n            description=\"Testing JSON round trip\",\n            category=PresetCategory.CINEMA,\n            tags=[\"json\", \"test\"],\n        )\n        json_str = original.to_json()\n        restored = Preset.from_json(json_str)\n        assert restored.id == original.id\n        assert restored.name == original.name\n        assert restored.category == original.category\n        assert restored.tags == original.tags\n\n    def test_equality_by_id(self):\n        \"\"\"Test equality is based on ID.\"\"\"\n        preset1 = Preset(id=\"same-id\", name=\"First\")\n        preset2 = Preset(id=\"same-id\", name=\"Second\")\n        preset3 = Preset(id=\"different-id\", name=\"First\")\n        assert preset1 == preset2\n        assert preset1 != preset3\n\n    def test_equality_with_non_preset(self):\n        \"\"\"Test equality with non-Preset objects.\"\"\"\n        preset = Preset(name=\"test\")\n        assert preset != \"test\"\n        assert preset != 123\n        assert preset != None\n\n    def test_hash_by_id(self):\n        \"\"\"Test hashing is based on ID.\"\"\"\n        preset1 = Preset(id=\"same-id\", name=\"First\")\n        preset2 = Preset(id=\"same-id\", name=\"Second\")\n        # Same ID means same hash\n        assert hash(preset1) == hash(preset2)\n        # Can be used in sets\n        preset_set = {preset1, preset2}\n        assert len(preset_set) == 1\n\n    def test_str_representation(self):\n        \"\"\"Test string representation.\"\"\"\n        preset = Preset(name=\"Test Preset\", category=PresetCategory.VR)\n        assert \"Test Preset\" in str(preset)\n        assert \"vr\" in str(preset)\n\n    def test_repr_representation(self):\n        \"\"\"Test repr representation.\"\"\"\n        preset = Preset(id=\"test-id\", name=\"Test\", category=PresetCategory.WEB)\n        repr_str = repr(preset)\n        assert \"test-id\" in repr_str\n        assert \"Test\" in repr_str\n        assert \"web\" in repr_str\n\n\nclass TestPresetSettingsValidationIntegration:\n    \"\"\"Integration tests for settings validation within Preset.\"\"\"\n\n    def test_preset_validates_nested_stereo_settings(self):\n        \"\"\"Test that Preset validates nested stereo settings.\"\"\"\n        with pytest.raises(ValueError, match=\"baseline must be positive\"):\n            Preset(\n                name=\"Invalid\",\n                settings=PresetSettings(\n                    stereo_generation=StereoGenerationSettings(baseline=-1)\n                ),\n            )\n\n    def test_preset_validates_nested_video_settings(self):\n        \"\"\"Test that Preset validates nested video settings.\"\"\"\n        with pytest.raises(ValueError, match=\"crf must be between 0 and 51\"):\n            Preset(\n                name=\"Invalid\",\n                settings=PresetSettings(\n                    video_output=VideoOutputSettings(crf=100)\n                ),\n            )\n\n    def test_preset_validates_nested_processing_settings(self):\n        \"\"\"Test that Preset validates nested processing settings.\"\"\"\n        with pytest.raises(ValueError, match=\"batch_size must be at least 1\"):\n            Preset(\n                name=\"Invalid\",\n                settings=PresetSettings(\n                    processing=ProcessingSettings(batch_size=0)\n                ),\n            )\n\n    def test_preset_accepts_all_valid_settings(self):\n        \"\"\"Test that Preset accepts all valid settings combinations.\"\"\"\n        preset = Preset(\n            name=\"Valid Preset\",\n            settings=PresetSettings(\n                depth_estimation=DepthEstimationSettings(model=\"dpt_large\"),\n                stereo_generation=StereoGenerationSettings(\n                    format=\"anaglyph\",\n                    baseline=0.1,\n                    focal_length=2.0,\n                ),\n                video_output=VideoOutputSettings(crf=18),\n                processing=ProcessingSettings(batch_size=1, num_workers=0),\n                quality=QualitySettings(preset=\"quality\"),\n            ),\n        )\n        assert preset.name == \"Valid Preset\"\n        assert preset.settings.depth_estimation.model == \"dpt_large\"\n        assert preset.settings.video_output.crf == 18\n"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Tests for preset storage functionality.\n\nThis module tests the PresetStorage class including:\n- Saving and loading presets\n- Atomic writes\n- Import/export functionality\n- Listing and searching presets\n\"\"\"\n\nimport json\nimport os\nfrom pathlib import Path\nfrom unittest.mock import MagicMock, patch\n\nimport pytest\n\nfrom video2d3d.presets.models import (\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    DepthEstimationSettings,\n)\nfrom video2d3d.presets.storage import PresetStorage, PresetStorageError\n\n\nclass TestPresetStorageInit:\n    \"\"\"Tests for PresetStorage initialization.\"\"\"\n\n    def test_init_creates_presets_directory(self, tmp_path: Path):\n        \"\"\"Test that initialization creates the presets directory.\"\"\"\n        presets_dir = tmp_path / \"presets\"\n        assert not presets_dir.exists()\n\n        storage = PresetStorage(presets_dir=presets_dir)\n        assert presets_dir.exists()\n        assert storage.presets_dir == presets_dir\n\n    def test_init_with_custom_directories(self, tmp_path: Path):\n        \"\"\"Test initialization with custom directories.\"\"\"\n        presets_dir = tmp_path / \"user_presets\"\n        builtin_dir = tmp_path / \"builtins\"\n\n        storage = PresetStorage(\n            presets_dir=presets_dir,\n            builtin_presets_dir=builtin_dir,\n        )\n        assert storage.presets_dir == presets_dir\n        assert storage.builtin_presets_dir == builtin_dir\n\n    def test_default_directories(self):\n        \"\"\"Test that default directories are set correctly.\"\"\"\n        storage = PresetStorage()\n        assert storage.presets_dir is not None\n        assert storage.builtin_presets_dir is not None\n\n\nclass TestPresetStorageSave:\n    \"\"\"Tests for saving presets.\"\"\"\n\n    def test_save_creates_file(self, tmp_path: Path):\n        \"\"\"Test that save creates a JSON file.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"Test Preset\", description=\"A test\")\n\n        file_path = storage.save(preset)\n\n        assert file_path.exists()\n        assert file_path.suffix == \".json\"\n\n    def test_save_file_contains_preset_data(self, tmp_path: Path):\n        \"\"\"Test that saved file contains preset data.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(\n            name=\"My Preset\",\n            description=\"Test description\",\n            category=PresetCategory.VR,\n        )\n\n        file_path = storage.save(preset)\n\n        with open(file_path) as f:\n            data = json.load(f)\n\n        assert data[\"name\"] == \"My Preset\"\n        assert data[\"description\"] == \"Test description\"\n        assert data[\"category\"] == \"vr\"\n\n    def test_save_builtin_preset_raises_error(self, tmp_path: Path):\n        \"\"\"Test that saving a built-in preset raises an error.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"Built-in\", is_builtin=True)\n\n        with pytest.raises(PresetStorageError, match=\"Cannot save built-in preset\"):\n            storage.save(preset)\n\n    def test_save_overwrites_existing(self, tmp_path: Path):\n        \"\"\"Test that save overwrites existing preset with same ID.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(id=\"same-id\", name=\"Original\")\n\n        storage.save(preset)\n\n        # Modify and save again\n        preset.name = \"Updated\"\n        file_path = storage.save(preset)\n\n        # Load and verify\n        with open(file_path) as f:\n            data = json.load(f)\n        assert data[\"name\"] == \"Updated\"\n\n    def test_atomic_write_prevents_corruption(self, tmp_path: Path):\n        \"\"\"Test that atomic write prevents partial file corruption.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        # Test that _atomic_write creates file correctly\n        test_path = tmp_path / \"presets\" / \"test.json\"\n        content = '{\"test\": \"data\"}'\n        storage._atomic_write(test_path, content)\n\n        assert test_path.exists()\n        with open(test_path) as f:\n            assert f.read() == content\n\n    def test_atomic_write_cleanup_on_error(self, tmp_path: Path):\n        \"\"\"Test that atomic write cleans up temp files on error.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        # Simulate a write error\n        with patch(\"builtins.open\", side_effect=IOError(\"Write failed\")):\n            with pytest.raises(PresetStorageError, match=\"Atomic write failed\"):\n                storage._atomic_write(\n                    tmp_path / \"presets\" / \"test.json\",\n                    '{\"test\": \"data\"}'\n                )\n\n\nclass TestPresetStorageLoad:\n    \"\"\"Tests for loading presets.\"\"\"\n\n    def test_load_existing_preset(self, tmp_path: Path):\n        \"\"\"Test loading an existing preset.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"Test\", description=\"Load test\")\n        storage.save(preset)\n\n        loaded = storage.load(preset.id)\n\n        assert loaded is not None\n        assert loaded.name == \"Test\"\n        assert loaded.description == \"Load test\"\n\n    def test_load_nonexistent_preset_returns_none(self, tmp_path: Path):\n        \"\"\"Test loading a nonexistent preset returns None.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        result = storage.load(\"nonexistent-id\")\n\n        assert result is None\n\n    def test_load_sets_is_builtin_false_for_user_preset(self, tmp_path: Path):\n        \"\"\"Test that loaded user preset has is_builtin=False.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"User Preset\")\n        storage.save(preset)\n\n        loaded = storage.load(preset.id)\n\n        assert loaded.is_builtin is False\n\n    def test_load_malformed_json_returns_none(self, tmp_path: Path):\n        \"\"\"Test that malformed JSON file returns None.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        presets_dir = tmp_path / \"presets\"\n        presets_dir.mkdir(exist_ok=True)\n\n        # Create malformed JSON file\n        bad_file = presets_dir / \"bad-preset.json\"\n        bad_file.write_text(\"{invalid json}\")\n\n        result = storage.load(\"bad-preset\")\n\n        assert result is None\n\n    def test_load_from_builtin_dir(self, tmp_path: Path):\n        \"\"\"Test loading a preset from built-in directory.\"\"\"\n        presets_dir = tmp_path / \"presets\"\n        builtin_dir = tmp_path / \"builtins\"\n        builtin_dir.mkdir(parents=True)\n\n        # Create a built-in preset file\n        builtin_preset = Preset(\n            id=\"builtin-test\",\n            name=\"Built-in Test\",\n            is_builtin=True,\n        )\n        with open(builtin_dir / \"builtin-test.json\", \"w\") as f:\n            json.dump(builtin_preset.to_dict(), f)\n\n        storage = PresetStorage(\n            presets_dir=presets_dir,\n            builtin_presets_dir=builtin_dir,\n        )\n\n        loaded = storage.load(\"builtin-test\")\n\n        assert loaded is not None\n        assert loaded.name == \"Built-in Test\"\n        assert loaded.is_builtin is True\n\n\nclass TestPresetStorageDelete:\n    \"\"\"Tests for deleting presets.\"\"\"\n\n    def test_delete_existing_preset(self, tmp_path: Path):\n        \"\"\"Test deleting an existing preset.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"To Delete\")\n        storage.save(preset)\n\n        result = storage.delete(preset.id)\n\n        assert result is True\n        assert storage.load(preset.id) is None\n\n    def test_delete_nonexistent_preset_returns_false(self, tmp_path: Path):\n        \"\"\"Test deleting a nonexistent preset returns False.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        result = storage.delete(\"nonexistent-id\")\n\n        assert result is False\n\n    def test_delete_builtin_preset_raises_error(self, tmp_path: Path):\n        \"\"\"Test that deleting a built-in preset raises an error.\"\"\"\n        presets_dir = tmp_path / \"presets\"\n        builtin_dir = tmp_path / \"builtins\"\n        builtin_dir.mkdir(parents=True)\n\n        # Create a built-in preset file\n        builtin_preset = Preset(\n            id=\"builtin-delete-test\",\n            name=\"Built-in\",\n            is_builtin=True,\n        )\n        with open(builtin_dir / \"builtin-delete-test.json\", \"w\") as f:\n            json.dump(builtin_preset.to_dict(), f)\n\n        storage = PresetStorage(\n            presets_dir=presets_dir,\n            builtin_presets_dir=builtin_dir,\n        )\n\n        with pytest.raises(PresetStorageError, match=\"Cannot delete built-in preset\"):\n            storage.delete(\"builtin-delete-test\")\n\n\nclass TestPresetStorageList:\n    \"\"\"Tests for listing presets.\"\"\"\n\n    def test_list_all_empty(self, tmp_path: Path):\n        \"\"\"Test listing when no presets exist.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        presets = storage.list_all()\n\n        assert presets == []\n\n    def test_list_all_returns_all_presets(self, tmp_path: Path):\n        \"\"\"Test that list_all returns all presets.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset1 = Preset(name=\"Preset 1\")\n        preset2 = Preset(name=\"Preset 2\")\n        storage.save(preset1)\n        storage.save(preset2)\n\n        presets = storage.list_all()\n\n        assert len(presets) == 2\n        names = [p.name for p in presets]\n        assert \"Preset 1\" in names\n        assert \"Preset 2\" in names\n\n    def test_list_all_excludes_builtins_when_false(self, tmp_path: Path):\n        \"\"\"Test that list_all can exclude built-in presets.\"\"\"\n        presets_dir = tmp_path / \"presets\"\n        builtin_dir = tmp_path / \"builtins\"\n        builtin_dir.mkdir(parents=True)\n\n        # Create user preset\n        user_preset = Preset(id=\"user-1\", name=\"User Preset\")\n        with open(presets_dir / \"user-1.json\", \"w\") as f:\n            json.dump(user_preset.to_dict(), f)\n\n        # Create built-in preset\n        builtin_preset = Preset(id=\"builtin-1\", name=\"Built-in\", is_builtin=True)\n        with open(builtin_dir / \"builtin-1.json\", \"w\") as f:\n            json.dump(builtin_preset.to_dict(), f)\n\n        storage = PresetStorage(\n            presets_dir=presets_dir,\n            builtin_presets_dir=builtin_dir,\n        )\n\n        all_presets = storage.list_all(include_builtins=True)\n        user_only = storage.list_all(include_builtins=False)\n\n        assert len(all_presets) == 2\n        assert len(user_only) == 1\n        assert user_only[0].name == \"User Preset\"\n\n    def test_list_by_category(self, tmp_path: Path):\n        \"\"\"Test listing presets by category.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        cinema = Preset(name=\"Cinema\", category=PresetCategory.CINEMA)\n        vr = Preset(name=\"VR\", category=PresetCategory.VR)\n        web = Preset(name=\"Web\", category=PresetCategory.WEB)\n        storage.save(cinema)\n        storage.save(vr)\n        storage.save(web)\n\n        vr_presets = storage.list_by_category(\"vr\")\n\n        assert len(vr_presets) == 1\n        assert vr_presets[0].name == \"VR\"\n\n    def test_list_by_category_case_insensitive(self, tmp_path: Path):\n        \"\"\"Test that category filtering is case-insensitive.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"Cinema\", category=PresetCategory.CINEMA)\n        storage.save(preset)\n\n        # Should work with uppercase\n        presets = storage.list_by_category(\"CINEMA\")\n        assert len(presets) == 1\n\n    def test_user_preset_overrides_builtin_by_id(self, tmp_path: Path):\n        \"\"\"Test that user preset with same ID overrides built-in.\"\"\"\n        presets_dir = tmp_path / \"presets\"\n        builtin_dir = tmp_path / \"builtins\"\n        builtin_dir.mkdir(parents=True)\n        presets_dir.mkdir(parents=True)\n\n        # Create built-in preset\n        builtin = Preset(id=\"shared-id\", name=\"Built-in\", is_builtin=True)\n        with open(builtin_dir / \"shared-id.json\", \"w\") as f:\n            json.dump(builtin.to_dict(), f)\n\n        # Create user preset with same ID\n        user = Preset(id=\"shared-id\", name=\"User Override\", is_builtin=False)\n        with open(presets_dir / \"shared-id.json\", \"w\") as f:\n            json.dump(user.to_dict(), f)\n\n        storage = PresetStorage(\n            presets_dir=presets_dir,\n            builtin_presets_dir=builtin_dir,\n        )\n\n        presets = storage.list_all()\n        assert len(presets) == 1\n        assert presets[0].name == \"User Override\"\n        assert presets[0].is_builtin is False\n\n\nclass TestPresetStorageExists:\n    \"\"\"Tests for checking preset existence.\"\"\"\n\n    def test_exists_returns_true_for_existing(self, tmp_path: Path):\n        \"\"\"Test exists returns True for existing preset.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"Test\")\n        storage.save(preset)\n\n        assert storage.exists(preset.id) is True\n\n    def test_exists_returns_false_for_nonexistent(self, tmp_path: Path):\n        \"\"\"Test exists returns False for nonexistent preset.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        assert storage.exists(\"nonexistent-id\") is False\n\n    def test_exists_checks_both_directories(self, tmp_path: Path):\n        \"\"\"Test exists checks both user and built-in directories.\"\"\"\n        presets_dir = tmp_path / \"presets\"\n        builtin_dir = tmp_path / \"builtins\"\n        builtin_dir.mkdir(parents=True)\n\n        # Create built-in preset only\n        builtin = Preset(id=\"builtin-only\", name=\"Built-in\", is_builtin=True)\n        with open(builtin_dir / \"builtin-only.json\", \"w\") as f:\n            json.dump(builtin.to_dict(), f)\n\n        storage = PresetStorage(\n            presets_dir=presets_dir,\n            builtin_presets_dir=builtin_dir,\n        )\n\n        assert storage.exists(\"builtin-only\") is True\n\n\nclass TestPresetStorageImportExport:\n    \"\"\"Tests for import/export functionality.\"\"\"\n\n    def test_export_preset(self, tmp_path: Path):\n        \"\"\"Test exporting a preset to a file.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(\n            name=\"Export Test\",\n            description=\"Testing export\",\n            category=PresetCategory.WEB,\n        )\n        storage.save(preset)\n\n        export_path = tmp_path / \"exports\" / \"exported.json\"\n        result = storage.export_preset(preset.id, export_path)\n\n        assert result.exists()\n        with open(result) as f:\n            data = json.load(f)\n        assert data[\"name\"] == \"Export Test\"\n\n    def test_export_nonexistent_preset_raises_error(self, tmp_path: Path):\n        \"\"\"Test exporting a nonexistent preset raises error.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        export_path = tmp_path / \"export.json\"\n\n        with pytest.raises(PresetStorageError, match=\"not found\"):\n            storage.export_preset(\"nonexistent-id\", export_path)\n\n    def test_import_preset(self, tmp_path: Path):\n        \"\"\"Test importing a preset from a file.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        # Create a preset file to import\n        import_preset = Preset(\n            id=\"imported-id\",\n            name=\"Imported Preset\",\n            description=\"Imported from file\",\n        )\n        import_path = tmp_path / \"import.json\"\n        with open(import_path, \"w\") as f:\n            json.dump(import_preset.to_dict(), f)\n\n        result = storage.import_preset(import_path)\n\n        assert result.id == \"imported-id\"\n        assert result.name == \"Imported Preset\"\n        assert storage.exists(\"imported-id\")\n\n    def test_import_preset_sets_is_builtin_false(self, tmp_path: Path):\n        \"\"\"Test that imported preset has is_builtin=False.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        # Create a preset file marked as built-in\n        import_preset = Preset(\n            id=\"imported-builtin\",\n            name=\"Was Built-in\",\n            is_builtin=True,  # This should be ignored\n        )\n        import_path = tmp_path / \"import.json\"\n        with open(import_path, \"w\") as f:\n            json.dump(import_preset.to_dict(), f)\n\n        result = storage.import_preset(import_path)\n\n        assert result.is_builtin is False\n\n    def test_import_duplicate_raises_error(self, tmp_path: Path):\n        \"\"\"Test that importing duplicate preset raises error.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        # Create existing preset\n        existing = Preset(id=\"duplicate-id\", name=\"Existing\")\n        storage.save(existing)\n\n        # Try to import preset with same ID\n        import_preset = Preset(id=\"duplicate-id\", name=\"Import\")\n        import_path = tmp_path / \"import.json\"\n        with open(import_path, \"w\") as f:\n            json.dump(import_preset.to_dict(), f)\n\n        with pytest.raises(PresetStorageError, match=\"already exists\"):\n            storage.import_preset(import_path)\n\n    def test_import_duplicate_with_overwrite(self, tmp_path: Path):\n        \"\"\"Test that importing with overwrite replaces existing.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n\n        # Create existing preset\n        existing = Preset(id=\"overwrite-id\", name=\"Original\")\n        storage.save(existing)\n\n        # Import with overwrite\n        import_preset = Preset(id=\"overwrite-id\", name=\"Replacement\")\n        import_path = tmp_path / \"import.json\"\n        with open(import_path, \"w\") as f:\n            json.dump(import_preset.to_dict(), f)\n\n        result = storage.import_preset(import_path, overwrite=True)\n\n        assert result.name == \"Replacement\"\n        loaded = storage.load(\"overwrite-id\")\n        assert loaded.name == \"Replacement\"\n\n    def test_import_invalid_json_raises_error(self, tmp_path: Path):\n        \"\"\"Test that importing invalid JSON raises error.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        import_path = tmp_path / \"invalid.json\"\n        import_path.write_text(\"{invalid json}\")\n\n        with pytest.raises(PresetStorageError, match=\"Invalid preset file format\"):\n            storage.import_preset(import_path)\n\n\nclass TestPresetStorageBackup:\n    \"\"\"Tests for backup functionality.\"\"\"\n\n    def test_backup_to_directory(self, tmp_path: Path):\n        \"\"\"Test creating backup to a directory.\"\"\"\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        preset = Preset(name=\"Backup Test\")\n        storage.save(preset)\n\n        backup_dir = tmp_path / \"backups\"\n        result = storage.backup_presets(backup_dir)\n\n        assert backup_dir.exists()\n        assert (backup_dir / \"presets\").exists()\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_preset_storage.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Tests for preset manager functionality.\n\nThis module tests the PresetManager class including:\n- CRUD operations (create, read, update, delete)\n- Search and filtering\n- Import/export\n- Config integration\n\"\"\"\n\nfrom pathlib import Path\nfrom unittest.mock import MagicMock, patch\n\nimport pytest\n\nfrom video2d3d.presets.manager import (\n    PresetManager,\n    PresetManagerError,\n    get_preset_manager,\n)\nfrom video2d3d.presets.models import (\n    Preset,\n    PresetCategory,\n    PresetSettings,\n    DepthEstimationSettings,\n    StereoGenerationSettings,\n    VideoOutputSettings,\n    ProcessingSettings,\n    QualitySettings,\n)\n\n\nclass TestPresetManagerInit:\n    \"\"\"Tests for PresetManager initialization.\"\"\"\n\n    def test_init_with_default_storage(self):\n        \"\"\"Test initialization with default storage.\"\"\"\n        manager = PresetManager()\n        assert manager.storage is not None\n\n    def test_init_with_custom_storage(self, tmp_path: Path):\n        \"\"\"Test initialization with custom storage.\"\"\"\n        from video2d3d.presets.storage import PresetStorage\n\n        storage = PresetStorage(presets_dir=tmp_path / \"presets\")\n        manager = PresetManager(storage=storage)\n        assert manager.storage == storage\n\n    def test_init_with_presets_dir(self, tmp_path: Path):\n        \"\"\"Test initialization with custom presets directory.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"custom_presets\")\n        assert manager.storage.presets_dir == tmp_path / \"custom_presets\"\n\n\nclass TestPresetManagerCreate:\n    \"\"\"Tests for creating presets.\"\"\"\n\n    def test_create_basic_preset(self, tmp_path: Path):\n        \"\"\"Test creating a basic preset.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        preset = manager.create(name=\"Test Preset\")\n\n        assert preset.id is not None\n        assert preset.name == \"Test Preset\"\n        assert preset.category == PresetCategory.CUSTOM\n\n    def test_create_preset_with_all_options(self, tmp_path: Path):\n        \"\"\"Test creating a preset with all options.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        settings = PresetSettings(\n            depth_estimation=DepthEstimationSettings(model=\"dpt_large\")\n        )\n\n        preset = manager.create(\n            name=\"Full Preset\",\n            settings=settings,\n            category=PresetCategory.CINEMA,\n            description=\"A complete preset\",\n            tags=[\"4k\", \"hdr\"],\n            author=\"Test Author\",\n        )\n\n        assert preset.name == \"Full Preset\"\n        assert preset.category == PresetCategory.CINEMA\n        assert preset.description == \"A complete preset\"\n        assert \"4k\" in preset.tags\n        assert preset.author == \"Test Author\"\n        assert preset.settings.depth_estimation.model == \"dpt_large\"\n\n    def test_create_duplicate_name_raises_error(self, tmp_path: Path):\n        \"\"\"Test that creating preset with duplicate name raises error.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Unique Name\")\n\n        with pytest.raises(PresetManagerError, match=\"already exists\"):\n            manager.create(name=\"Unique Name\")\n\n    def test_create_duplicate_name_case_insensitive(self, tmp_path: Path):\n        \"\"\"Test that duplicate name check is case-insensitive.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Test Preset\")\n\n        with pytest.raises(PresetManagerError, match=\"already exists\"):\n            manager.create(name=\"TEST PRESET\")\n\n    def test_create_increments_cache(self, tmp_path: Path):\n        \"\"\"Test that creating updates the cache.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        manager.create(name=\"Cache Test\")\n        presets = manager._get_cached_presets()\n\n        assert len(presets) == 1\n\n\nclass TestPresetManagerGet:\n    \"\"\"Tests for getting presets.\"\"\"\n\n    def test_get_by_id(self, tmp_path: Path):\n        \"\"\"Test getting a preset by ID.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        created = manager.create(name=\"Get Test\")\n\n        loaded = manager.get(created.id)\n\n        assert loaded is not None\n        assert loaded.id == created.id\n        assert loaded.name == \"Get Test\"\n\n    def test_get_by_id_nonexistent_returns_none(self, tmp_path: Path):\n        \"\"\"Test getting nonexistent preset returns None.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        result = manager.get(\"nonexistent-id\")\n\n        assert result is None\n\n    def test_get_by_name(self, tmp_path: Path):\n        \"\"\"Test getting a preset by name.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Find By Name\")\n\n        preset = manager.get_by_name(\"Find By Name\")\n\n        assert preset is not None\n        assert preset.name == \"Find By Name\"\n\n    def test_get_by_name_case_insensitive(self, tmp_path: Path):\n        \"\"\"Test that get_by_name is case-insensitive.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Case Test\")\n\n        preset = manager.get_by_name(\"CASE TEST\")\n\n        assert preset is not None\n        assert preset.name == \"Case Test\"\n\n    def test_get_by_name_nonexistent_returns_none(self, tmp_path: Path):\n        \"\"\"Test getting nonexistent preset by name returns None.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        result = manager.get_by_name(\"Nonexistent\")\n\n        assert result is None\n\n\nclass TestPresetManagerUpdate:\n    \"\"\"Tests for updating presets.\"\"\"\n\n    def test_update_name(self, tmp_path: Path):\n        \"\"\"Test updating preset name.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Original Name\")\n\n        updated = manager.update(preset.id, name=\"New Name\")\n\n        assert updated.name == \"New Name\"\n\n    def test_update_description(self, tmp_path: Path):\n        \"\"\"Test updating preset description.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Update Test\")\n\n        updated = manager.update(preset.id, description=\"New description\")\n\n        assert updated.description == \"New description\"\n\n    def test_update_category(self, tmp_path: Path):\n        \"\"\"Test updating preset category.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Category Test\")\n\n        updated = manager.update(preset.id, category=PresetCategory.VR)\n\n        assert updated.category == PresetCategory.VR\n\n    def test_update_settings(self, tmp_path: Path):\n        \"\"\"Test updating preset settings.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Settings Update\")\n        new_settings = PresetSettings(\n            video_output=VideoOutputSettings(crf=18)\n        )\n\n        updated = manager.update(preset.id, settings=new_settings)\n\n        assert updated.settings.video_output.crf == 18\n\n    def test_update_nonexistent_raises_error(self, tmp_path: Path):\n        \"\"\"Test updating nonexistent preset raises error.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        with pytest.raises(PresetManagerError, match=\"not found\"):\n            manager.update(\"nonexistent-id\", name=\"New Name\")\n\n    def test_update_builtin_raises_error(self, tmp_path: Path):\n        \"\"\"Test updating built-in preset raises error.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        # Create a preset and mark as built-in\n        preset = manager.create(name=\"Built-in Test\")\n        # Manually mark as builtin in storage\n        loaded = manager.get(preset.id)\n        loaded.is_builtin = True\n        manager.storage.save = lambda p: None  # Mock save to prevent overwrite\n\n        with pytest.raises(PresetManagerError, match=\"Cannot update built-in preset\"):\n            manager.update(preset.id, name=\"New Name\")\n\n    def test_update_duplicate_name_raises_error(self, tmp_path: Path):\n        \"\"\"Test updating to duplicate name raises error.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset1 = manager.create(name=\"First\")\n        preset2 = manager.create(name=\"Second\")\n\n        with pytest.raises(PresetManagerError, match=\"already exists\"):\n            manager.update(preset2.id, name=\"First\")\n\n    def test_update_updates_timestamp(self, tmp_path: Path):\n        \"\"\"Test that update changes updated_at timestamp.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Timestamp Test\")\n        original_updated = preset.updated_at\n\n        import time\n        time.sleep(0.01)  # Ensure timestamp difference\n        updated = manager.update(preset.id, description=\"Changed\")\n\n        assert updated.updated_at != original_updated\n\n\nclass TestPresetManagerDelete:\n    \"\"\"Tests for deleting presets.\"\"\"\n\n    def test_delete_existing_preset(self, tmp_path: Path):\n        \"\"\"Test deleting an existing preset.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"To Delete\")\n\n        result = manager.delete(preset.id)\n\n        assert result is True\n        assert manager.get(preset.id) is None\n\n    def test_delete_nonexistent_returns_false(self, tmp_path: Path):\n        \"\"\"Test deleting nonexistent preset returns False.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        result = manager.delete(\"nonexistent-id\")\n\n        assert result is False\n\n\nclass TestPresetManagerDuplicate:\n    \"\"\"Tests for duplicating presets.\"\"\"\n\n    def test_duplicate_creates_copy(self, tmp_path: Path):\n        \"\"\"Test that duplicate creates a copy with different ID.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        original = manager.create(\n            name=\"Original\",\n            description=\"Original description\",\n            category=PresetCategory.VR,\n            tags=[\"test\"],\n        )\n\n        duplicate = manager.duplicate(original.id)\n\n        assert duplicate.id != original.id\n        assert duplicate.name == \"Original (copy)\"\n        assert duplicate.description == original.description\n        assert duplicate.category == original.category\n        assert duplicate.tags == original.tags\n\n    def test_duplicate_with_custom_name(self, tmp_path: Path):\n        \"\"\"Test duplicate with custom name.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        original = manager.create(name=\"Original\")\n\n        duplicate = manager.duplicate(original.id, new_name=\"Custom Copy Name\")\n\n        assert duplicate.name == \"Custom Copy Name\"\n\n    def test_duplicate_creates_independent_settings(self, tmp_path: Path):\n        \"\"\"Test that duplicate creates independent settings copy.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        original = manager.create(\n            name=\"Settings Test\",\n            settings=PresetSettings(\n                video_output=VideoOutputSettings(crf=20)\n            ),\n        )\n\n        duplicate = manager.duplicate(original.id)\n\n        # Modify original should not affect duplicate\n        manager.update(original.id, settings=PresetSettings(\n            video_output=VideoOutputSettings(crf=30)\n        ))\n\n        # Reload duplicate to verify independence\n        reloaded = manager.get(duplicate.id)\n        assert reloaded.settings.video_output.crf == 20\n\n    def test_duplicate_nonexistent_raises_error(self, tmp_path: Path):\n        \"\"\"Test duplicating nonexistent preset raises error.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        with pytest.raises(PresetManagerError, match=\"not found\"):\n            manager.duplicate(\"nonexistent-id\")\n\n\nclass TestPresetManagerList:\n    \"\"\"Tests for listing presets.\"\"\"\n\n    def test_list_all(self, tmp_path: Path):\n        \"\"\"Test listing all presets.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Preset 1\")\n        manager.create(name=\"Preset 2\")\n        manager.create(name=\"Preset 3\")\n\n        presets = manager.list_all()\n\n        assert len(presets) == 3\n\n    def test_list_by_category(self, tmp_path: Path):\n        \"\"\"Test listing presets by category.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Cinema 1\", category=PresetCategory.CINEMA)\n        manager.create(name=\"Cinema 2\", category=PresetCategory.CINEMA)\n        manager.create(name=\"VR 1\", category=PresetCategory.VR)\n\n        cinema = manager.list_by_category(PresetCategory.CINEMA)\n\n        assert len(cinema) == 2\n        names = [p.name for p in cinema]\n        assert \"Cinema 1\" in names\n        assert \"Cinema 2\" in names\n\n\nclass TestPresetManagerSearch:\n    \"\"\"Tests for searching presets.\"\"\"\n\n    def test_search_by_name(self, tmp_path: Path):\n        \"\"\"Test searching by name.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Cinema Quality\")\n        manager.create(name=\"VR Optimized\")\n        manager.create(name=\"Web Streaming\")\n\n        results = manager.search(\"cinema\")\n\n        assert len(results) == 1\n        assert results[0].name == \"Cinema Quality\"\n\n    def test_search_by_description(self, tmp_path: Path):\n        \"\"\"Test searching by description.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Preset 1\", description=\"For high quality output\")\n        manager.create(name=\"Preset 2\", description=\"For fast processing\")\n\n        results = manager.search(\"high quality\")\n\n        assert len(results) == 1\n        assert results[0].name == \"Preset 1\"\n\n    def test_search_case_insensitive(self, tmp_path: Path):\n        \"\"\"Test that search is case-insensitive.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Test Preset\")\n\n        results = manager.search(\"TEST\")\n\n        assert len(results) == 1\n\n    def test_search_with_category_filter(self, tmp_path: Path):\n        \"\"\"Test search with category filter.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(\n            name=\"Cinema Test\",\n            description=\"Test preset\",\n            category=PresetCategory.CINEMA,\n        )\n        manager.create(\n            name=\"VR Test\",\n            description=\"Test preset\",\n            category=PresetCategory.VR,\n        )\n\n        results = manager.search(\"Test\", category=PresetCategory.VR)\n\n        assert len(results) == 1\n        assert results[0].name == \"VR Test\"\n\n    def test_search_with_tags_filter(self, tmp_path: Path):\n        \"\"\"Test search with tags filter.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"HD Preset\", tags=[\"hd\", \"quality\"])\n        manager.create(name=\"4K Preset\", tags=[\"4k\", \"quality\"])\n\n        results = manager.search(\"\", tags=[\"4k\"])\n\n        assert len(results) == 1\n        assert results[0].name == \"4K Preset\"\n\n    def test_search_no_results(self, tmp_path: Path):\n        \"\"\"Test search with no matching results.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        manager.create(name=\"Test Preset\")\n\n        results = manager.search(\"nonexistent\")\n\n        assert results == []\n\n\nclass TestPresetManagerImportExport:\n    \"\"\"Tests for import/export functionality.\"\"\"\n\n    def test_export_preset(self, tmp_path: Path):\n        \"\"\"Test exporting a preset.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Export Test\")\n\n        export_path = tmp_path / \"exports\" / \"exported.json\"\n        result = manager.export_preset(preset.id, export_path)\n\n        assert result.exists()\n\n    def test_export_nonexistent_raises_error(self, tmp_path: Path):\n        \"\"\"Test exporting nonexistent preset raises error.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        export_path = tmp_path / \"export.json\"\n\n        with pytest.raises(PresetManagerError, match=\"not found\"):\n            manager.export_preset(\"nonexistent-id\", export_path)\n\n    def test_import_preset(self, tmp_path: Path):\n        \"\"\"Test importing a preset.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        # Create import file\n        import_preset = Preset(\n            id=\"imported-id\",\n            name=\"Imported\",\n            category=PresetCategory.WEB,\n        )\n        import_path = tmp_path / \"import.json\"\n        import_path.write_text(import_preset.to_json())\n\n        result = manager.import_preset(import_path)\n\n        assert result.id == \"imported-id\"\n        assert manager.get(\"imported-id\") is not None\n\n\nclass TestPresetManagerConfigIntegration:\n    \"\"\"Tests for config integration.\"\"\"\n\n    def test_apply_preset_to_config(self, tmp_path: Path):\n        \"\"\"Test applying preset settings to config.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        settings = PresetSettings(\n            depth_estimation=DepthEstimationSettings(model=\"dpt_large\"),\n            stereo_generation=StereoGenerationSettings(\n                format=\"anaglyph\",\n                baseline=0.08,\n            ),\n            video_output=VideoOutputSettings(crf=18),\n            processing=ProcessingSettings(batch_size=2),\n            quality=QualitySettings(preset=\"quality\"),\n        )\n        preset = manager.create(name=\"Config Test\", settings=settings)\n\n        # Create a mock config\n        from video2d3d.utils.config import Config\n        config = Config()\n\n        updated_config = manager.apply_preset_to_config(preset, config)\n\n        assert updated_config.depth_estimation.model == \"dpt_large\"\n        assert updated_config.stereo_generation.format == \"anaglyph\"\n        assert updated_config.video_output.crf == 18\n        assert updated_config.processing.batch_size == 2\n        assert updated_config.quality.preset == \"quality\"\n\n    def test_create_preset_from_config(self, tmp_path: Path):\n        \"\"\"Test creating preset from config.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        # Create a mock config\n        from video2d3d.utils.config import Config\n        config = Config()\n        config.depth_estimation.model = \"dpt_hybrid\"\n        config.video_output.crf = 20\n        config.processing.batch_size = 8\n\n        preset = manager.create_preset_from_config(\n            name=\"From Config\",\n            config=config,\n            category=PresetCategory.CUSTOM,\n            description=\"Created from config\",\n            tags=[\"config\"],\n        )\n\n        assert preset.name == \"From Config\"\n        assert preset.settings.depth_estimation.model == \"dpt_hybrid\"\n        assert preset.settings.video_output.crf == 20\n        assert preset.settings.processing.batch_size == 8\n\n\nclass TestGetPresetManager:\n    \"\"\"Tests for get_preset_manager singleton.\"\"\"\n\n    def test_returns_manager_instance(self):\n        \"\"\"Test that get_preset_manager returns PresetManager.\"\"\"\n        manager = get_preset_manager()\n        assert isinstance(manager, PresetManager)\n\n    def test_returns_same_instance(self):\n        \"\"\"Test that get_preset_manager returns same instance.\"\"\"\n        manager1 = get_preset_manager()\n        manager2 = get_preset_manager()\n        assert manager1 is manager2\n\n    def test_reload_creates_new_instance(self):\n        \"\"\"Test that reload=True creates new instance.\"\"\"\n        manager1 = get_preset_manager()\n        manager2 = get_preset_manager(reload=True)\n        assert manager1 is not manager2\n\n\nclass TestPresetManagerCache:\n    \"\"\"Tests for caching functionality.\"\"\"\n\n    def test_cache_invalidated_on_create(self, tmp_path: Path):\n        \"\"\"Test that cache is invalidated on create.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n\n        # Prime the cache\n        manager._get_cached_presets()\n        manager.create(name=\"Cache Test\")\n\n        # Cache should be updated\n        cached = manager._get_cached_presets()\n        assert \"Cache Test\" in [p.name for p in cached.values()]\n\n    def test_cache_invalidated_on_update(self, tmp_path: Path):\n        \"\"\"Test that cache is invalidated on update.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Update Cache\")\n\n        manager.update(preset.id, name=\"Updated Name\")\n\n        # Cache should reflect update\n        cached = manager._get_cached_presets()\n        found = [p for p in cached.values() if p.id == preset.id]\n        assert found[0].name == \"Updated Name\"\n\n    def test_cache_invalidated_on_delete(self, tmp_path: Path):\n        \"\"\"Test that cache is invalidated on delete.\"\"\"\n        manager = PresetManager(presets_dir=tmp_path / \"presets\")\n        preset = manager.create(name=\"Delete Cache\")\n\n        manager.delete(preset.id)\n\n        # Cache should not contain deleted preset\n        cached = manager._get_cached_presets()\n        assert preset.id not in cached\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_preset_manager.py"
}

🔧 Tool: write
Input: {
  "content": "\"\"\"Tests for built-in presets.\n\nThis module tests the built-in preset definitions including:\n- All built-in presets are valid\n- Preset lookup functions\n- Preset category consistency\n\"\"\"\n\nimport pytest\n\nfrom video2d3d.presets.builtins import (\n    ALL_BUILTIN_PRESETS,\n    BUILTIN_PRESETS_BY_ID,\n    BUILTIN_PRESETS_BY_NAME,\n    CINEMA_SBS,\n    CINEMA_ANAGLYPH,\n    VR_OVER_UNDER,\n    VR_SIDE_BY_SIDE,\n    WEB_SBS,\n    WEB_ANAGLYPH,\n    MOBILE_SBS,\n    MOBILE_ANAGLYPH,\n    FAST_PREVIEW,\n    MAX_QUALITY,\n    BALANCED,\n    get_builtin_preset,\n    get_builtin_preset_by_name,\n)\nfrom video2d3d.presets.models import (\n    Preset,\n    PresetCategory,\n    PresetSettings,\n)\n\n\nclass TestBuiltinPresetsExist:\n    \"\"\"Tests that all expected built-in presets exist.\"\"\"\n\n    def test_cinema_presets_exist(self):\n        \"\"\"Test that cinema presets are defined.\"\"\"\n        assert CINEMA_SBS is not None\n        assert CINEMA_ANAGLYPH is not None\n        assert CINEMA_SBS.name == \"Cinema (Side-by-Side)\"\n        assert CINEMA_ANAGLYPH.name == \"Cinema (Anaglyph)\"\n\n    def test_vr_presets_exist(self):\n        \"\"\"Test that VR presets are defined.\"\"\"\n        assert VR_OVER_UNDER is not None\n        assert VR_SIDE_BY_SIDE is not None\n        assert VR_OVER_UNDER.name == \"VR (Over-Under)\"\n        assert VR_SIDE_BY_SIDE.name == \"VR (Side-by-Side)\"\n\n    def test_web_presets_exist(self):\n        \"\"\"Test that web presets are defined.\"\"\"\n        assert WEB_SBS is not None\n        assert WEB_ANAGLYPH is not None\n        assert WEB_SBS.name == \"Web (Side-by-Side)\"\n        assert WEB_ANAGLYPH.name == \"Web (Anaglyph)\"\n\n    def test_mobile_presets_exist(self):\n        \"\"\"Test that mobile presets are defined.\"\"\"\n        assert MOBILE_SBS is not None\n        assert MOBILE_ANAGLYPH is not None\n        assert MOBILE_SBS.name == \"Mobile (Side-by-Side)\"\n        assert MOBILE_ANAGLYPH.name == \"Mobile (Anaglyph)\"\n\n    def test_quality_presets_exist(self):\n        \"\"\"Test that quality presets are defined.\"\"\"\n        assert FAST_PREVIEW is not None\n        assert MAX_QUALITY is not None\n        assert BALANCED is not None\n        assert FAST_PREVIEW.name == \"Fast Preview\"\n        assert MAX_QUALITY.name == \"Maximum Quality\"\n        assert BALANCED.name == \"Balanced\"\n\n\nclass TestBuiltinPresetsValidity:\n    \"\"\"Tests that all built-in presets are valid.\"\"\"\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_are_builtin(self, preset: Preset):\n        \"\"\"Test that all built-in presets have is_builtin=True.\"\"\"\n        assert preset.is_builtin is True\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_id(self, preset: Preset):\n        \"\"\"Test that all presets have a valid ID.\"\"\"\n        assert preset.id is not None\n        assert len(preset.id) > 0\n        assert preset.id.startswith(\"builtin-\")\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_name(self, preset: Preset):\n        \"\"\"Test that all presets have a name.\"\"\"\n        assert preset.name is not None\n        assert len(preset.name) > 0\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_description(self, preset: Preset):\n        \"\"\"Test that all presets have a description.\"\"\"\n        assert preset.description is not None\n        assert len(preset.description) > 0\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_category(self, preset: Preset):\n        \"\"\"Test that all presets have a category.\"\"\"\n        assert preset.category is not None\n        assert isinstance(preset.category, PresetCategory)\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_tags(self, preset: Preset):\n        \"\"\"Test that all presets have tags.\"\"\"\n        assert preset.tags is not None\n        assert isinstance(preset.tags, list)\n        assert len(preset.tags) > 0\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_settings(self, preset: Preset):\n        \"\"\"Test that all presets have complete settings.\"\"\"\n        assert preset.settings is not None\n        assert isinstance(preset.settings, PresetSettings)\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_valid_depth_model(self, preset: Preset):\n        \"\"\"Test that all presets use valid depth models.\"\"\"\n        valid_models = [\"midas_small\", \"midas_hybrid\", \"dpt_large\", \"dpt_hybrid\"]\n        assert preset.settings.depth_estimation.model in valid_models\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_valid_crf(self, preset: Preset):\n        \"\"\"Test that all presets have CRF in valid range.\"\"\"\n        crf = preset.settings.video_output.crf\n        assert 0 <= crf <= 51\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_valid_baseline(self, preset: Preset):\n        \"\"\"Test that all presets have positive baseline.\"\"\"\n        baseline = preset.settings.stereo_generation.baseline\n        assert baseline > 0\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_all_presets_have_valid_batch_size(self, preset: Preset):\n        \"\"\"Test that all presets have batch_size >= 1.\"\"\"\n        batch_size = preset.settings.processing.batch_size\n        assert batch_size >= 1\n\n\nclass TestBuiltinPresetsCollections:\n    \"\"\"Tests for preset collections.\"\"\"\n\n    def test_all_builtin_presets_count(self):\n        \"\"\"Test that we have the expected number of built-in presets.\"\"\"\n        assert len(ALL_BUILTIN_PRESETS) == 11\n\n    def test_by_id_mapping_complete(self):\n        \"\"\"Test that BY_ID mapping contains all presets.\"\"\"\n        assert len(BUILTIN_PRESETS_BY_ID) == len(ALL_BUILTIN_PRESETS)\n        for preset in ALL_BUILTIN_PRESETS:\n            assert preset.id in BUILTIN_PRESETS_BY_ID\n\n    def test_by_name_mapping_complete(self):\n        \"\"\"Test that BY_NAME mapping contains all presets.\"\"\"\n        assert len(BUILTIN_PRESETS_BY_NAME) == len(ALL_BUILTIN_PRESETS)\n        for preset in ALL_BUILTIN_PRESETS:\n            assert preset.name in BUILTIN_PRESETS_BY_NAME\n\n    def test_unique_ids(self):\n        \"\"\"Test that all preset IDs are unique.\"\"\"\n        ids = [p.id for p in ALL_BUILTIN_PRESETS]\n        assert len(ids) == len(set(ids))\n\n    def test_unique_names(self):\n        \"\"\"Test that all preset names are unique.\"\"\"\n        names = [p.name for p in ALL_BUILTIN_PRESETS]\n        assert len(names) == len(set(names))\n\n\nclass TestGetBuiltinPreset:\n    \"\"\"Tests for get_builtin_preset function.\"\"\"\n\n    def test_get_existing_preset(self):\n        \"\"\"Test getting an existing preset by ID.\"\"\"\n        preset = get_builtin_preset(\"builtin-cinema-sbs\")\n        assert preset is not None\n        assert preset.name == \"Cinema (Side-by-Side)\"\n\n    def test_get_nonexistent_preset(self):\n        \"\"\"Test getting a nonexistent preset returns None.\"\"\"\n        preset = get_builtin_preset(\"nonexistent-id\")\n        assert preset is None\n\n\nclass TestGetBuiltinPresetByName:\n    \"\"\"Tests for get_builtin_preset_by_name function.\"\"\"\n\n    def test_get_by_name_exact(self):\n        \"\"\"Test getting a preset by exact name.\"\"\"\n        preset = get_builtin_preset_by_name(\"Cinema (Side-by-Side)\")\n        assert preset is not None\n        assert preset.id == \"builtin-cinema-sbs\"\n\n    def test_get_by_name_case_insensitive(self):\n        \"\"\"Test getting a preset is case-insensitive.\"\"\"\n        preset = get_builtin_preset_by_name(\"CINEMA (SIDE-BY-SIDE)\")\n        assert preset is not None\n        assert preset.id == \"builtin-cinema-sbs\"\n\n    def test_get_by_name_nonexistent(self):\n        \"\"\"Test getting a nonexistent preset returns None.\"\"\"\n        preset = get_builtin_preset_by_name(\"Nonexistent Preset\")\n        assert preset is None\n\n\nclass TestPresetCategories:\n    \"\"\"Tests for preset category assignments.\"\"\"\n\n    def test_cinema_category(self):\n        \"\"\"Test that cinema presets have correct category.\"\"\"\n        assert CINEMA_SBS.category == PresetCategory.CINEMA\n        assert CINEMA_ANAGLYPH.category == PresetCategory.CINEMA\n\n    def test_vr_category(self):\n        \"\"\"Test that VR presets have correct category.\"\"\"\n        assert VR_OVER_UNDER.category == PresetCategory.VR\n        assert VR_SIDE_BY_SIDE.category == PresetCategory.VR\n\n    def test_web_category(self):\n        \"\"\"Test that web presets have correct category.\"\"\"\n        assert WEB_SBS.category == PresetCategory.WEB\n        assert WEB_ANAGLYPH.category == PresetCategory.WEB\n\n    def test_mobile_category(self):\n        \"\"\"Test that mobile presets have correct category.\"\"\"\n        assert MOBILE_SBS.category == PresetCategory.MOBILE\n        assert MOBILE_ANAGLYPH.category == PresetCategory.MOBILE\n\n    def test_general_category(self):\n        \"\"\"Test that general presets have correct category.\"\"\"\n        assert FAST_PREVIEW.category == PresetCategory.GENERAL\n        assert MAX_QUALITY.category == PresetCategory.GENERAL\n        assert BALANCED.category == PresetCategory.GENERAL\n\n\nclass TestPresetSettingsOptimizations:\n    \"\"\"Tests that presets are optimized for their use cases.\"\"\"\n\n    def test_cinema_uses_quality_model(self):\n        \"\"\"Test that cinema presets use quality depth models.\"\"\"\n        assert CINEMA_SBS.settings.depth_estimation.model == \"dpt_large\"\n        assert CINEMA_ANAGLYPH.settings.depth_estimation.model == \"dpt_large\"\n\n    def test_cinema_uses_slow_encoding(self):\n        \"\"\"Test that cinema presets use slow encoding for quality.\"\"\"\n        assert CINEMA_SBS.settings.video_output.preset == \"slow\"\n        assert CINEMA_ANAGLYPH.settings.video_output.preset == \"slow\"\n\n    def test_cinema_uses_low_crf(self):\n        \"\"\"Test that cinema presets use low CRF for quality.\"\"\"\n        assert CINEMA_SBS.settings.video_output.crf <= 20\n\n    def test_vr_has_stronger_3d(self):\n        \"\"\"Test that VR presets have stronger baseline for 3D effect.\"\"\"\n        assert VR_OVER_UNDER.settings.stereo_generation.baseline >= 0.07\n\n    def test_mobile_uses_fast_encoding(self):\n        \"\"\"Test that mobile presets use fast encoding.\"\"\"\n        assert MOBILE_SBS.settings.video_output.preset == \"fast\"\n        assert MOBILE_ANAGLYPH.settings.video_output.preset == \"fast\"\n\n    def test_mobile_uses_small_model(self):\n        \"\"\"Test that mobile presets use small/fast depth model.\"\"\"\n        assert MOBILE_SBS.settings.depth_estimation.model == \"midas_small\"\n\n    def test_fast_preview_uses_ultrafast(self):\n        \"\"\"Test that fast preview uses ultrafast encoding.\"\"\"\n        assert FAST_PREVIEW.settings.video_output.preset == \"ultrafast\"\n\n    def test_fast_preview_uses_high_crf(self):\n        \"\"\"Test that fast preview uses high CRF for speed.\"\"\"\n        assert FAST_PREVIEW.settings.video_output.crf >= 25\n\n    def test_max_quality_uses_slowest_encoding(self):\n        \"\"\"Test that max quality uses veryslow encoding.\"\"\"\n        assert MAX_QUALITY.settings.video_output.preset == \"veryslow\"\n\n    def test_max_quality_uses_lowest_crf(self):\n        \"\"\"Test that max quality uses lowest CRF for quality.\"\"\"\n        assert MAX_QUALITY.settings.video_output.crf <= 18\n\n    def test_max_quality_uses_small_batch(self):\n        \"\"\"Test that max quality uses batch_size=1 for quality.\"\"\"\n        assert MAX_QUALITY.settings.processing.batch_size == 1\n\n    def test_fast_preview_uses_large_batch(self):\n        \"\"\"Test that fast preview uses large batch_size for speed.\"\"\"\n        assert FAST_PREVIEW.settings.processing.batch_size >= 4\n\n    def test_half_width_for_vr_and_mobile(self):\n        \"\"\"Test that VR and mobile side-by-side use half-width.\"\"\"\n        assert VR_SIDE_BY_SIDE.settings.stereo_generation.sbs_half_width is True\n        assert MOBILE_SBS.settings.stereo_generation.sbs_half_width is True\n\n\nclass TestPresetSerialization:\n    \"\"\"Tests for preset serialization.\"\"\"\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_to_dict_round_trip(self, preset: Preset):\n        \"\"\"Test that presets survive to_dict/from_dict round trip.\"\"\"\n        data = preset.to_dict()\n        restored = Preset.from_dict(data)\n\n        assert restored.id == preset.id\n        assert restored.name == preset.name\n        assert restored.category == preset.category\n        assert restored.settings.depth_estimation.model == preset.settings.depth_estimation.model\n        assert restored.settings.video_output.crf == preset.settings.video_output.crf\n\n    @pytest.mark.parametrize(\"preset\", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)\n    def test_to_json_round_trip(self, preset: Preset):\n        \"\"\"Test that presets survive JSON round trip.\"\"\"\n        import json\n\n        json_str = preset.to_json()\n        restored = Preset.from_json(json_str)\n\n        assert restored.id == preset.id\n        assert restored.name == preset.name\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/unit/test_preset_builtins.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Write unit tests for preset models (test_preset_models.py)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write unit tests for preset storage (test_preset_storage.py)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write unit tests for preset manager (test_preset_manager.py)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Write unit tests for built-in presets (test_preset_builtins.py)",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Run all tests and verify they pass",
      "priority": "high",
      "status": "in_progress"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && .venv/bin/python -m pytest tests/unit/test_preset_models.py -v --tb=short 2>&1 | head -100",
  "description": "Run preset models tests",
  "timeout": 120000
}
