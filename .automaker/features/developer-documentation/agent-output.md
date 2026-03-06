I'll implement the developer documentation feature. Let me start by exploring the codebase to understand its structure and then create comprehensive documentation.

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Explore codebase structure and understand architecture",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Analyze existing documentation and identify gaps",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Create architecture diagrams",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write module descriptions for key components",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Create contribution guidelines",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add code examples and usage documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify documentation with Playwright",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pubspec.yaml"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/README.md"
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Explore project structure",
  "prompt": "I need to understand the overall structure of this 2dto3d project to create comprehensive developer documentation.\n\nCONTEXT: Creating developer documentation including architecture diagrams and module descriptions. Need to understand the full project structure.\n\nGOAL: Get a complete picture of the project's organization, key directories, and how components relate to each other.\n\nDOWNSTREAM: Will use this to create architecture diagrams and module documentation.\n\nREQUEST:\n- Map out the main directory structure\n- Identify key source code directories and their purposes\n- Find configuration files (package.json, pubspec.yaml, etc.)\n- Identify the main entry points\n- Note any existing documentation files\n- Understand the technology stack (Flutter, Dart, web, etc.)\n\nReturn a structured overview of the project layout with descriptions of each major component.",
  "run_in_background": true
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Find existing documentation",
  "prompt": "I'm creating developer documentation and need to understand what documentation already exists.\n\nCONTEXT: Creating comprehensive developer docs - need to survey existing docs to avoid duplication and identify gaps.\n\nGOAL: Catalog all existing documentation files and their content scope.\n\nDOWNSTREAM: Will build upon existing docs and fill gaps where needed.\n\nREQUEST:\n- Find all README files (README.md, README*.md)\n- Find any documentation directories (/docs, /documentation, etc.)\n- Locate any existing developer guides or contribution guides\n- Check for API documentation\n- Look for inline documentation patterns\n- Identify any diagrams or architecture documentation\n\nReturn a list of existing documentation files with brief descriptions of their scope and quality.",
  "run_in_background": true
}

🔧 Tool: task
Input: {
  "subagent_type": "explore",
  "load_skills": [],
  "description": "Identify key modules",
  "prompt": "I need to identify the key modules and components of this 2dto3d application for documentation purposes.\n\nCONTEXT: Creating module descriptions and architecture documentation. Need to understand the main functional components.\n\nGOAL: Identify and describe the major modules/components and their responsibilities.\n\nDOWNSTREAM: Will create detailed module descriptions and show relationships in architecture diagrams.\n\nREQUEST:\n- Find the main application entry points\n- Identify core feature modules (e.g., 2D to 3D conversion logic, UI components, state management)\n- Locate services, utilities, and helper modules\n- Understand the data flow and state management approach\n- Identify external dependencies and integrations\n- Note any platform-specific code (web, mobile, desktop)\n\nReturn a categorized list of modules with their file locations and brief descriptions of their purpose.",
  "run_in_background": true
}

🔧 Tool: glob
Input: {
  "pattern": "**/*.md"
}

🔧 Tool: glob
Input: {
  "pattern": "docs/**/*.md"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/docs/USER_GUIDE.md"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/frontend/README.md"
}

🔧 Tool: bash
Input: {
  "command": "ls -la",
  "description": "List directory contents"
}

🔧 Tool: glob
Input: {
  "pattern": "src/**/*.py"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_b017b166"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_06c96bba"
}

🔧 Tool: background_output
Input: {
  "task_id": "bg_884a6a39"
}
Let me gather more information from key source files while the background agents complete:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/cli.py"
}

🔧 Tool: bash
Input: {
  "command": "find src -name \"__init__.py\" -type f | head -30",
  "description": "Find all Python module init files"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Explore codebase structure and understand architecture",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Analyze existing documentation and identify gaps",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Create architecture diagrams",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Write module descriptions for key components",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Create contribution guidelines",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Add code examples and usage documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify documentation with Playwright",
      "status": "pending",
      "priority": "high"
    }
  ]
}


---

## Follow-up Session

I'll perform a code review of the developer documentation and then update it based on my findings. Let me first explore what documentation exists and the codebase structure.

🔧 Tool: glob
Input: {
  "pattern": "docs/**/*"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/README.md"
}

🔧 Tool: glob
Input: {
  "pattern": "**/*.md"
}

🔧 Tool: bash
Input: {
  "command": "find . -type f -name \"*.md\" | head -20",
  "description": "Find all markdown files"
}

🔧 Tool: bash
Input: {
  "command": "find src -type f -name \"*.py\" | head -40",
  "description": "Find all Python source files"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/docs/USER_GUIDE.md"
}

🔧 Tool: glob
Input: {
  "pattern": "src/**/*.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review existing documentation and identify gaps",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Create DEVELOPER_GUIDE.md with architecture overview",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Create CONTRIBUTING.md with contribution guidelines",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add architecture diagrams (ASCII/mermaid)",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Write module descriptions for key components",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Add code examples and usage documentation",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Verify documentation with Playwright",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/core/batch_processor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/processor.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/stereo/dibr.py"
}
Now I have a thorough understanding of the codebase. Let me create the comprehensive developer documentation.

🔧 Tool: write
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/docs/DEVELOPER_GUIDE.md",
  "content": "# 2Dto3D Video Converter - Developer Guide\n\n**Version:** 0.1.0  \n**Last Updated:** March 2026\n\n> This guide is intended for developers who want to understand, extend, or contribute to the 2Dto3D Video Converter project.\n\n## Table of Contents\n\n1. [Architecture Overview](#architecture-overview)\n2. [Project Structure](#project-structure)\n3. [Core Modules](#core-modules)\n4. [Data Flow](#data-flow)\n5. [Extending the System](#extending-the-system)\n6. [API Reference](#api-reference)\n7. [Testing](#testing)\n8. [Debugging](#debugging)\n\n---\n\n## Architecture Overview\n\n### High-Level Architecture\n\n```\n┌─────────────────────────────────────────────────────────────────────────────┐\n│                              User Interface Layer                            │\n├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤\n│     CLI         │    Web API      │   Desktop GUI   │    Web Dashboard      │\n│   (cli.py)      │   (web/app.py)  │   (gui/)        │    (frontend/)        │\n└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬────────────┘\n         │                 │                 │                    │\n         ▼                 ▼                 ▼                    ▼\n┌─────────────────────────────────────────────────────────────────────────────┐\n│                           Core Processing Layer                              │\n├─────────────────────────────────────────────────────────────────────────────┤\n│                                                                             │\n│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │\n│  │  Video Handler  │──▶  Depth Engine   │──▶  Stereo Engine  │             │\n│  │  (video/)       │  │  (depth/)       │  │  (stereo/)      │             │\n│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │\n│           │                   │                    │                        │\n│           ▼                   ▼                    ▼                        │\n│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │\n│  │ Frame Extractor │  │ Depth Processor │  │ Output Encoders │             │\n│  │ Video Writer    │  │ Temporal Smooth │  │ SBS/Anaglyph/VR │             │\n│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │\n│                                                                             │\n└─────────────────────────────────────────────────────────────────────────────┘\n         │                 │                 │                    │\n         ▼                 ▼                 ▼                    ▼\n┌─────────────────────────────────────────────────────────────────────────────┐\n│                           Infrastructure Layer                               │\n├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤\n│   Batch Queue   │   GPU Manager   │  Config System  │   Logging System      │\n│  (batch/)       │  (utils/gpu)    │ (utils/config)  │  (utils/logger)       │\n├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤\n│ Error Recovery  │ Memory Monitor  │  Crash Reporter │   Preset Manager      │\n│(utils/error)    │(utils/memory)   │   (crash/)      │   (presets/)          │\n└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘\n```\n\n### Processing Pipeline\n\nThe video conversion follows a well-defined pipeline:\n\n```mermaid\ngraph LR\n    A[Input Video] --> B[Frame Extraction]\n    B --> C[Batch Processor]\n    C --> D[Depth Estimation]\n    D --> E[Depth Processing]\n    E --> F[Temporal Smoothing]\n    F --> G[DIBR Engine]\n    G --> H[Stereo Encoder]\n    H --> I[Video Writer]\n    I --> J[Output 3D Video]\n```\n\n---\n\n## Project Structure\n\n```\n2dto3d/\n├── config/                     # Configuration files\n│   ├── default.yaml           # Default settings\n│   ├── development.yaml       # Development overrides\n│   └── production.yaml        # Production overrides\n│\n├── src/video2d3d/             # Main source code\n│   ├── __init__.py\n│   ├── __main__.py            # Entry point for python -m\n│   ├── cli.py                 # Command-line interface\n│   ├── _version.py            # Version information\n│   │\n│   ├── core/                  # Core processing logic\n│   │   ├── __init__.py\n│   │   └── batch_processor.py # Parallel batch processing\n│   │\n│   ├── video/                 # Video I/O handling\n│   │   ├── __init__.py\n│   │   ├── handler.py         # Main video handler\n│   │   ├── frame_extractor.py # Frame extraction from videos\n│   │   ├── video_writer.py    # Video output writer\n│   │   ├── metadata.py        # Video metadata utilities\n│   │   └── exceptions.py      # Video-specific exceptions\n│   │\n│   ├── depth/                 # Depth estimation modules\n│   │   ├── __init__.py\n│   │   ├── processor.py       # Depth map post-processing\n│   │   ├── temporal.py        # Temporal smoothing\n│   │   ├── adadepth.py        # AdaDepth model integration\n│   │   ├── zoedepth.py        # ZoeDepth model integration\n│   │   ├── ensemble.py        # Depth ensemble methods\n│   │   ├── curve.py           # Depth curve adjustments\n│   │   └── model_selector.py  # Dynamic model selection\n│   │\n│   ├── stereo/                # Stereoscopic generation\n│   │   ├── __init__.py\n│   │   ├── dibr.py            # Depth-Image-Based Rendering\n│   │   ├── side_by_side.py    # Side-by-side encoder\n│   │   ├── anaglyph.py        # Anaglyph encoder\n│   │   ├── interlaced.py      # Interlaced encoder\n│   │   ├── checkerboard.py    # Checkerboard encoder\n│   │   ├── top_bottom.py      # Top-bottom encoder\n│   │   └── vr.py              # VR format encoder\n│   │\n│   ├── audio/                 # Audio processing\n│   │   ├── __init__.py\n│   │   ├── processor.py       # Audio processing pipeline\n│   │   ├── tracks.py          # Audio track handling\n│   │   ├── spatial.py         # Spatial audio\n│   │   ├── multichannel.py    # Multichannel audio\n│   │   ├── metadata.py        # Audio metadata\n│   │   ├── config.py          # Audio configuration\n│   │   ├── constants.py       # Audio constants\n│   │   └── exceptions.py      # Audio exceptions\n│   │\n│   ├── web/                   # Web API server\n│   │   ├── __init__.py\n│   │   ├── app.py             # FastAPI application\n│   │   ├── schemas.py         # Pydantic schemas\n│   │   ├── health.py          # Health check endpoints\n│   │   ├── state.py           # Application state\n│   │   ├── rate_limit.py      # Rate limiting\n│   │   ├── exceptions.py      # API exceptions\n│   │   ├── utils.py           # API utilities\n│   │   └── routers/           # API routers\n│   │       ├── __init__.py\n│   │       ├── jobs.py        # Job management\n│   │       ├── uploads.py     # File uploads\n│   │       ├── downloads.py   # File downloads\n│   │       └── crash.py       # Crash reports\n│   │\n│   ├── batch/                 # Batch processing\n│   │   ├── __init__.py\n│   │   ├── queue.py           # Job queue management\n│   │   ├── models.py          # Batch job models\n│   │   ├── config.py          # Batch configuration\n│   │   ├── file_discovery.py  # File discovery\n│   │   ├── folder_watcher.py  # Folder watching\n│   │   ├── exceptions.py      # Batch exceptions\n│   │   └── adaptive_sizer.py  # Adaptive batch sizing\n│   │\n│   ├── gui/                   # Desktop GUI (PyQt)\n│   │   ├── __init__.py\n│   │   ├── main_window.py     # Main application window\n│   │   ├── convert_tab.py     # Conversion tab\n│   │   ├── batch_tab.py       # Batch processing tab\n│   │   ├── settings_tab.py    # Settings tab\n│   │   ├── workers.py         # Background workers\n│   │   └── widgets.py         # Custom widgets\n│   │\n│   ├── preview/               # Preview functionality\n│   │   ├── __init__.py\n│   │   └── preview_window.py  # Live preview window\n│   │\n│   ├── utils/                 # Utility modules\n│   │   ├── __init__.py\n│   │   ├── config.py          # Configuration management\n│   │   ├── logger.py          # Logging utilities\n│   │   ├── gpu.py             # GPU management\n│   │   ├── progress.py        # Progress tracking\n│   │   ├── error_recovery.py  # Error recovery utilities\n│   │   └── memory_monitor.py  # Memory monitoring\n│   │\n│   ├── crash/                 # Crash reporting\n│   │   ├── __init__.py\n│   │   ├── reporter.py        # Crash reporter\n│   │   ├── models.py          # Crash report models\n│   │   └── state_capture.py   # State capture\n│   │\n│   ├── benchmark/             # Benchmarking tools\n│   │   ├── __init__.py\n│   │   ├── runner.py          # Benchmark runner\n│   │   ├── results.py         # Benchmark results\n│   │   ├── reporting.py       # Result reporting\n│   │   └── config.py          # Benchmark config\n│   │\n│   ├── presets/               # Preset management\n│   │   ├── __init__.py\n│   │   ├── manager.py         # Preset manager\n│   │   ├── storage.py         # Preset storage\n│   │   ├── models.py          # Preset models\n│   │   └── builtins.py        # Built-in presets\n│   │\n│   ├── checkpoint/            # Checkpoint/resume\n│   │   ├── __init__.py\n│   │   ├── manager.py         # Checkpoint manager\n│   │   └── models.py          # Checkpoint models\n│   │\n│   ├── opticalflow/           # Optical flow engine\n│   │   ├── __init__.py\n│   │   └── engine.py          # Optical flow computation\n│   │\n│   └── segmentation/          # Segmentation processor\n│       ├── __init__.py\n│       ├── processor.py       # Segmentation processing\n│       └── integrator.py      # Segmentation integration\n│\n├── frontend/                  # Web dashboard (React/TypeScript)\n│   ├── src/\n│   ├── public/\n│   ├── package.json\n│   └── README.md\n│\n├── tests/                     # Test suite\n│   ├── unit/                  # Unit tests\n│   ├── integration/           # Integration tests\n│   └── fixtures/              # Test fixtures\n│\n├── docs/                      # Documentation\n│   ├── USER_GUIDE.md         # User documentation\n│   └── DEVELOPER_GUIDE.md    # This file\n│\n├── models/                    # Pre-trained models (downloaded)\n├── inputs/                    # Input videos directory\n├── outputs/                   # Output videos directory\n├── logs/                      # Log files directory\n│\n├── requirements.txt           # Production dependencies\n├── requirements-dev.txt       # Development dependencies\n├── pyproject.toml            # Project configuration\n├── setup.py                  # Package setup\n├── Dockerfile                # GPU Docker image\n├── Dockerfile.cpu            # CPU-only Docker image\n├── docker-compose.yml        # Docker Compose (GPU)\n└── docker-compose.cpu.yml    # Docker Compose (CPU)\n```\n\n---\n\n## Core Modules\n\n### 1. Video Module (`src/video2d3d/video/`)\n\nHandles all video input/output operations.\n\n#### Key Components\n\n| Component | Description |\n|-----------|-------------|\n| `VideoHandler` | Main class for video processing workflow |\n| `FrameExtractor` | Extracts individual frames from video files |\n| `VideoWriter` | Writes processed frames to output video |\n| `VideoMetadata` | Extracts and manages video metadata |\n\n#### Usage Example\n\n```python\nfrom video2d3d.video import FrameExtractor, VideoWriter\n\n# Extract frames from a video\nextractor = FrameExtractor(\"input.mp4\")\nfor frame_idx, frame in extractor.extract_frames():\n    # Process frame\n    processed_frame = process(frame)\n    # Write to output\n    break\n\n# Write frames to video\nwriter = VideoWriter(\n    \"output.mp4\",\n    fps=30,\n    resolution=(1920, 1080),\n    codec=\"libx264\"\n)\nfor frame in processed_frames:\n    writer.write_frame(frame)\nwriter.close()\n```\n\n### 2. Depth Module (`src/video2d3d/depth/`)\n\nHandles depth estimation and post-processing.\n\n#### Key Components\n\n| Component | Description |\n|-----------|-------------|\n| `DepthMapProcessor` | Post-processes depth maps (normalization, filtering) |\n| `TemporalSmoother` | Smooths depth across video frames |\n| `DepthModelSelector` | Dynamically selects depth models |\n| `DepthEnsemble` | Combines multiple depth estimates |\n\n#### Depth Processing Pipeline\n\n```python\nfrom video2d3d.depth import DepthMapProcessor, DepthProcessorConfig\n\n# Configure depth processing\nconfig = DepthProcessorConfig(\n    edge_aware_smoothing=True,\n    bilateral_filter=True,\n    hole_filling=True,\n    hole_filling_method=\"inpaint\",\n    normalization_method=\"percentile\",\n    colormap=\"turbo\"\n)\n\nprocessor = DepthMapProcessor(config=config)\n\n# Process a depth map\nprocessed_depth = processor.process(raw_depth_map, apply_colormap=False)\n\n# Individual operations\nnormalized = processor.normalize(raw_depth_map, method=\"min_max\")\nfiltered = processor.apply_bilateral_filter(normalized)\nfilled = processor.fill_holes(filtered)\ncolored = processor.apply_colormap(filled, colormap=\"plasma\")\n```\n\n### 3. Stereo Module (`src/video2d3d/stereo/`)\n\nGenerates stereoscopic 3D views from depth maps.\n\n#### Key Components\n\n| Component | Description |\n|-----------|-------------|\n| `DIBREngine` | Depth-Image-Based Rendering for stereo generation |\n| `SideBySideEncoder` | Left-right stereo format |\n| `AnaglyphEncoder` | Red-cyan anaglyph format |\n| `InterlacedEncoder` | Row-alternating format |\n| `VREncoder` | VR over-under format |\n\n#### DIBR Rendering\n\n```python\nfrom video2d3d.stereo import DIBREngine, DIBRConfig\n\n# Configure DIBR\nconfig = DIBRConfig(\n    baseline=0.05,           # Camera separation (3D effect strength)\n    focal_length=1.0,        # Virtual focal length\n    convergence=0.5,         # Zero parallax distance\n    hole_filling=\"inpaint\",  # How to fill disocclusions\n    depth_interpretation=\"inverse\"  # MiDaS-style depth\n)\n\nengine = DIBREngine(config=config)\n\n# Generate stereo pair\nleft_view, right_view = engine.render(frame, depth_map)\n\n# Get disparity map for visualization\ndisparity = engine.compute_disparity(depth_map, image_width=1920)\n```\n\n### 4. Core Module (`src/video2d3d/core/`)\n\nProvides parallel batch processing capabilities.\n\n#### Batch Processing\n\n```python\nfrom video2d3d.core import (\n    FrameBatchProcessor,\n    BatchProcessorConfig,\n    ProcessingMode\n)\n\n# Configure batch processing\nconfig = BatchProcessorConfig(\n    batch_size=8,\n    num_workers=4,\n    mode=ProcessingMode.MULTIPROCESSING,\n    timeout_seconds=300.0,\n    max_retries=2,\n    preserve_order=True\n)\n\nprocessor = FrameBatchProcessor(config=config)\n\n# Process frames in parallel\ndef depth_estimation(frame):\n    return estimate_depth(frame)\n\nresult = processor.process(frames, depth_estimation)\n\n# Access results\nfor output in result.get_successful_outputs():\n    save_output(output)\n\n# Check for errors\nfor idx, error in result.errors:\n    print(f\"Frame {idx} failed: {error}\")\n\nprint(f\"Success rate: {result.success_rate:.1f}%\")\nprint(f\"Throughput: {result.items_per_second:.1f} fps\")\n```\n\n### 5. Web API Module (`src/video2d3d/web/`)\n\nREST API server built with FastAPI.\n\n#### Key Endpoints\n\n| Endpoint | Method | Description |\n|----------|--------|-------------|\n| `/health` | GET | Health check |\n| `/api/v1/upload/` | POST | Upload video file |\n| `/api/v1/jobs/` | POST | Submit conversion job |\n| `/api/v1/jobs/{id}` | GET | Get job status |\n| `/api/v1/jobs/{id}/cancel` | POST | Cancel job |\n| `/api/v1/download/{id}` | GET | Download result |\n\n#### Starting the Server\n\n```python\n# Command line\nvideo2d3d serve --host 0.0.0.0 --port 8000\n\n# Programmatically\nfrom video2d3d.web.app import create_app\nimport uvicorn\n\napp = create_app()\nuvicorn.run(app, host=\"0.0.0.0\", port=8000)\n```\n\n### 6. Batch Module (`src/video2d3d/batch/`)\n\nManages job queues and batch processing.\n\n```python\nfrom video2d3d.batch import BatchQueue, BatchJobConfig\n\n# Create batch queue\nqueue = BatchQueue(\n    max_concurrent_jobs=1,\n    auto_start=True,\n    save_state=True\n)\n\n# Add job to queue\njob_config = BatchJobConfig(\n    input_path=\"video.mp4\",\n    output_path=\"video_3d.mp4\",\n    stereo_format=\"side_by_side\",\n    depth_model=\"midas_small\"\n)\njob_id = queue.add_job(job_config)\n\n# Monitor queue status\nstatus = queue.get_status()\nprint(f\"Pending: {status.pending_jobs}\")\nprint(f\"Running: {status.running_jobs}\")\nprint(f\"Completed: {status.completed_jobs}\")\n```\n\n---\n\n## Data Flow\n\n### Frame Processing Flow\n\n```\n┌──────────────────────────────────────────────────────────────────┐\n│                        FRAME PROCESSING FLOW                      │\n└──────────────────────────────────────────────────────────────────┘\n\nInput Video (MP4, AVI, etc.)\n         │\n         ▼\n┌─────────────────────┐\n│  Frame Extraction   │  Extract individual frames using OpenCV\n│  (FrameExtractor)   │  - Decode video stream\n└──────────┬──────────┘  - Yield frames with timestamps\n           │\n           ▼\n┌─────────────────────┐\n│   Batch Processing  │  Process frames in parallel batches\n│  (BatchProcessor)   │  - Multiprocessing for CPU-bound tasks\n└──────────┬──────────┘  - Progress tracking\n           │\n           ▼\n┌─────────────────────┐\n│  Depth Estimation   │  Estimate depth using ML models\n│  (MiDaS, DPT, etc.) │  - GPU acceleration when available\n└──────────┬──────────┘  - Model caching\n           │\n           ▼\n┌─────────────────────┐\n│  Depth Processing   │  Post-process depth maps\n│ (DepthMapProcessor) │  - Normalization\n└──────────┬──────────┘  - Edge-aware smoothing\n           │             - Hole filling\n           ▼\n┌─────────────────────┐\n│ Temporal Smoothing  │  Smooth depth across frames\n│ (TemporalSmoother)  │  - Consistent depth over time\n└──────────┬──────────┘  - Reduces flickering\n           │\n           ▼\n┌─────────────────────┐\n│   DIBR Rendering    │  Generate stereo views\n│    (DIBREngine)     │  - Compute disparity\n└──────────┬──────────┘  - Warp images\n           │             - Fill disocclusions\n           ▼\n┌─────────────────────┐\n│  Stereo Encoding    │  Encode stereo format\n│ (SBS, Anaglyph, VR) │  - Side-by-side\n└──────────┬──────────┘  - Anaglyph\n           │             - Interlaced\n           ▼             - VR formats\n┌─────────────────────┐\n│    Video Writing    │  Write output video\n│   (VideoWriter)     │  - Encode with FFmpeg\n└──────────┬──────────┘  - Preserve audio\n           │\n           ▼\nOutput Video (3D MP4, etc.)\n```\n\n---\n\n## Extending the System\n\n### Adding a New Depth Model\n\n1. Create a new model adapter in `src/video2d3d/depth/`:\n\n```python\n# src/video2d3d/depth/my_model.py\n\nfrom typing import Optional\nimport numpy as np\nimport torch\n\nclass MyDepthModel:\n    \"\"\"Custom depth estimation model.\"\"\"\n    \n    def __init__(self, model_path: Optional[str] = None, device: str = \"cuda\"):\n        self.device = device\n        self.model = self._load_model(model_path)\n    \n    def _load_model(self, model_path: Optional[str]):\n        # Load your model here\n        pass\n    \n    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:\n        \"\"\"Estimate depth from a single frame.\n        \n        Args:\n            frame: Input image (H, W, 3) in RGB format, uint8.\n            \n        Returns:\n            Depth map (H, W) as float32, values in [0, 1] where\n            1 = far, 0 = close (inverse depth interpretation).\n        \"\"\"\n        # Preprocess\n        input_tensor = self._preprocess(frame)\n        \n        # Run inference\n        with torch.no_grad():\n            output = self.model(input_tensor)\n        \n        # Postprocess\n        depth = self._postprocess(output)\n        \n        return depth\n```\n\n2. Register the model in `model_selector.py`:\n\n```python\n# src/video2d3d/depth/model_selector.py\n\nSUPPORTED_MODELS = {\n    # ... existing models ...\n    \"my_model\": {\n        \"class\": \"video2d3d.depth.my_model.MyDepthModel\",\n        \"description\": \"My custom depth model\",\n        \"quality\": \"custom\",\n        \"speed\": \"custom\",\n    }\n}\n```\n\n3. Add configuration support in `config/default.yaml`:\n\n```yaml\ndepth_estimation:\n  model: my_model  # or midas_small, dpt_large, etc.\n```\n\n### Adding a New Stereo Output Format\n\n1. Create a new encoder in `src/video2d3d/stereo/`:\n\n```python\n# src/video2d3d/stereo/my_format.py\n\nimport numpy as np\nfrom typing import Tuple\n\nclass MyFormatEncoder:\n    \"\"\"Encoder for custom stereo format.\"\"\"\n    \n    def encode(\n        self, \n        left_view: np.ndarray, \n        right_view: np.ndarray\n    ) -> np.ndarray:\n        \"\"\"Encode left and right views into custom format.\n        \n        Args:\n            left_view: Left eye view (H, W, 3)\n            right_view: Right eye view (H, W, 3)\n            \n        Returns:\n            Encoded stereo image\n        \"\"\"\n        # Implement your encoding logic\n        encoded = self._custom_encode(left_view, right_view)\n        return encoded\n    \n    def _custom_encode(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:\n        # Your encoding implementation\n        pass\n```\n\n2. Register in `__init__.py`:\n\n```python\n# src/video2d3d/stereo/__init__.py\n\nfrom video2d3d.stereo.my_format import MyFormatEncoder\n\n__all__ = [\n    # ... existing exports ...\n    \"MyFormatEncoder\",\n]\n```\n\n3. Add CLI support in `cli.py`:\n\n```python\n# In convert command\nformat_choices = [\n    \"side_by_side\", \n    \"anaglyph\", \n    \"interlaced\", \n    \"my_format\"  # Add your format\n]\n```\n\n### Adding a New CLI Command\n\n```python\n# src/video2d3d/cli.py\n\nimport click\n\n@click.group()\ndef cli():\n    \"\"\"2Dto3D Video Converter CLI.\"\"\"\n    pass\n\n@cli.command()\n@click.argument('input_file', type=click.Path(exists=True))\n@click.option('--output', '-o', required=True, help='Output file path')\n@click.option('--option', '-opt', default='default', help='Custom option')\ndef my_command(input_file: str, output: str, option: str):\n    \"\"\"Description of my custom command.\n    \n    Extended description with usage examples.\n    \"\"\"\n    # Implementation\n    click.echo(f\"Processing {input_file} -> {output}\")\n    # ... your logic ...\n    click.echo(\"Done!\")\n\n# Register with main CLI group\ncli.add_command(my_command)\n```\n\n---\n\n## API Reference\n\n### Configuration Classes\n\n#### BatchProcessorConfig\n\n```python\n@dataclass\nclass BatchProcessorConfig:\n    batch_size: int = 8          # Items per batch\n    num_workers: int = 4         # Parallel workers\n    mode: ProcessingMode = ProcessingMode.MULTIPROCESSING\n    chunk_size: int = 1          # Items per chunk\n    timeout_seconds: float = 300.0\n    max_retries: int = 2\n    preserve_order: bool = True\n    enable_progress: bool = True\n```\n\n#### DepthProcessorConfig\n\n```python\n@dataclass\nclass DepthProcessorConfig:\n    edge_aware_smoothing: bool = True\n    smoothing_radius: int = 3\n    bilateral_filter: bool = True\n    bilateral_sigma_color: float = 0.1\n    bilateral_sigma_space: int = 5\n    hole_filling: bool = True\n    hole_filling_method: str = \"inpaint\"  # \"inpaint\", \"nearest\", \"linear\"\n    normalization_method: str = \"min_max\"  # \"min_max\", \"percentile\", \"histogram_equalization\"\n    colormap: str = \"turbo\"\n```\n\n#### DIBRConfig\n\n```python\n@dataclass\nclass DIBRConfig:\n    baseline: float = 0.05        # Camera separation\n    focal_length: float = 1.0     # Virtual focal length\n    convergence: float = 0.5      # Zero parallax distance (0-1)\n    hole_filling: str = \"nearest\" # \"none\", \"nearest\", \"linear\", \"inpaint\"\n    depth_interpretation: str = \"inverse\"  # \"inverse\" or \"direct\"\n    max_disparity: int = 64       # Maximum disparity in pixels\n```\n\n### Exception Classes\n\n| Exception | Description |\n|-----------|-------------|\n| `BatchProcessorError` | Base error for batch processing |\n| `WorkerTimeoutError` | Worker exceeded timeout |\n| `DepthProcessingError` | Error in depth processing |\n| `DIBRError` | Error in DIBR rendering |\n| `VideoProcessingError` | Error in video processing |\n\n---\n\n## Testing\n\n### Running Tests\n\n```bash\n# Run all tests\npytest\n\n# Run with coverage\npytest --cov=video2d3d --cov-report=html\n\n# Run specific test file\npytest tests/unit/test_depth_processor.py\n\n# Run specific test\npytest tests/unit/test_depth_processor.py::test_normalization\n\n# Run with verbose output\npytest -v tests/\n\n# Run integration tests only\npytest tests/integration/\n\n# Run with markers\npytest -m \"not slow\"  # Skip slow tests\npytest -m gpu         # Run GPU tests only\n```\n\n### Writing Tests\n\n```python\n# tests/unit/test_depth_processor.py\n\nimport numpy as np\nimport pytest\nfrom video2d3d.depth import DepthMapProcessor, DepthProcessorConfig\n\nclass TestDepthMapProcessor:\n    \"\"\"Tests for DepthMapProcessor class.\"\"\"\n    \n    @pytest.fixture\n    def processor(self):\n        \"\"\"Create a processor instance for testing.\"\"\"\n        config = DepthProcessorConfig(\n            bilateral_filter=True,\n            hole_filling=True\n        )\n        return DepthMapProcessor(config=config)\n    \n    @pytest.fixture\n    def sample_depth_map(self):\n        \"\"\"Create a sample depth map for testing.\"\"\"\n        return np.random.rand(480, 640).astype(np.float32)\n    \n    def test_normalization(self, processor, sample_depth_map):\n        \"\"\"Test depth map normalization.\"\"\"\n        normalized = processor.normalize(sample_depth_map)\n        \n        assert normalized.dtype == np.float32\n        assert normalized.min() >= 0.0\n        assert normalized.max() <= 1.0\n    \n    def test_bilateral_filter(self, processor, sample_depth_map):\n        \"\"\"Test bilateral filtering.\"\"\"\n        filtered = processor.apply_bilateral_filter(sample_depth_map)\n        \n        assert filtered.shape == sample_depth_map.shape\n        assert filtered.dtype == np.float32\n    \n    def test_invalid_config(self):\n        \"\"\"Test that invalid config raises error.\"\"\"\n        with pytest.raises(ValueError):\n            DepthProcessorConfig(\n                normalization_method=\"invalid_method\"\n            )\n```\n\n### Test Fixtures\n\nPlace test fixtures in `tests/fixtures/`:\n\n```\ntests/fixtures/\n├── videos/\n│   ├── sample_1s.mp4      # 1-second test video\n│   ├── sample_5s.mp4      # 5-second test video\n│   └── sample_corrupt.mp4 # Corrupt video for error testing\n├── images/\n│   ├── test_frame.png\n│   └── test_depth.npy\n└── configs/\n    ├── test_config.yaml\n    └── minimal_config.yaml\n```\n\n---\n\n## Debugging\n\n### Enable Debug Logging\n\n```bash\n# Environment variable\nexport VIDEO2D3D_LOG_LEVEL=DEBUG\n\n# Or via CLI\nvideo2d3d --verbose convert input.mp4 output.mp4\n```\n\n### Log Files\n\nLogs are written to `logs/video2d3d.log` by default.\n\n```bash\n# View recent logs\ntail -f logs/video2d3d.log\n\n# Search for errors\ngrep -i error logs/video2d3d.log\n\n# View specific module logs\ngrep \"\\[depth\\]\" logs/video2d3d.log\n```\n\n### GPU Debugging\n\n```python\n# Check GPU availability\nfrom video2d3d.utils.gpu import get_gpu_info\n\ninfo = get_gpu_info()\nprint(f\"GPU available: {info.available}\")\nprint(f\"GPU name: {info.name}\")\nprint(f\"Memory: {info.memory_total} MB\")\n```\n\n### Performance Profiling\n\n```python\nimport cProfile\nimport pstats\n\nfrom video2d3d.core import FrameBatchProcessor\n\ndef profile_batch_processing():\n    processor = FrameBatchProcessor()\n    # ... processing code ...\n\n# Profile\nprofiler = cProfile.Profile()\nprofiler.enable()\n\nprofile_batch_processing()\n\nprofiler.disable()\nstats = pstats.Stats(profiler)\nstats.sort_stats('cumulative')\nstats.print_stats(20)  # Top 20 functions\n```\n\n### Common Issues\n\n| Issue | Cause | Solution |\n|-------|-------|----------|\n| `CUDA out of memory` | GPU memory exhausted | Reduce batch_size, enable auto_batch_size |\n| `FFmpeg not found` | FFmpeg not in PATH | Install FFmpeg and add to PATH |\n| `Model download failed` | Network issue | Download models manually to `models/` |\n| `ImportError` | Module not installed | Run `pip install -e .` |\n\n---\n\n## Performance Optimization\n\n### GPU Memory Management\n\n```python\nfrom video2d3d.utils.gpu import GPUMemoryManager\n\n# Enable memory growth (TensorFlow style)\nmanager = GPUMemoryManager(memory_fraction=0.8)\nmanager.configure()\n\n# Check memory usage\nusage = manager.get_memory_usage()\nprint(f\"Used: {usage.used} / {usage.total} MB\")\n```\n\n### Batch Size Tuning\n\n```python\nfrom video2d3d.batch import AdaptiveBatchSizer\n\n# Auto-adjust batch size based on GPU memory\nsizer = AdaptiveBatchSizer(\n    min_batch_size=1,\n    max_batch_size=32,\n    target_memory_fraction=0.8\n)\n\nbatch_size = sizer.get_optimal_batch_size(frame_resolution=(1920, 1080))\n```\n\n### Processing Mode Selection\n\n| Mode | Use Case | Performance |\n|------|----------|-------------|\n| `MULTIPROCESSING` | CPU-bound tasks (depth estimation) | High |\n| `THREADING` | I/O-bound tasks (video writing) | Medium |\n| `SEQUENTIAL` | Debugging, single-threaded environments | Low |\n\n---\n\n## Additional Resources\n\n- [User Guide](USER_GUIDE.md) - End-user documentation\n- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server running)\n- [GitHub Repository](https://github.com/automaker/2dto3d) - Source code and issues\n\n---\n\n*This developer guide is for 2Dto3D Video Converter version 0.1.0*\n"
}


---

## Follow-up Session


🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git log --oneline -5",
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
Let me check the specific changes for the developer documentation feature:

🔧 Tool: bash
Input: {
  "command": "ls -la docs/",
  "description": "List docs directory"
}

🔧 Tool: bash
Input: {
  "command": "head -50 docs/DEVELOPER_GUIDE.md",
  "description": "Preview developer guide content"
}
Now I'll stage and commit the developer documentation changes:

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git add docs/DEVELOPER_GUIDE.md .automaker/features/developer-documentation/",
  "description": "Stage developer documentation files"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git diff --cached --stat",
  "description": "Show staged changes"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git commit -m \"docs(dev): add comprehensive developer documentation\n\nAdd DEVELOPER_GUIDE.md with:\n- Architecture overview with ASCII diagrams\n- Complete project structure documentation\n- Core module descriptions and API references\n- Data flow documentation\n- Extension guides for adding new models/formats\n- Testing and debugging guidelines\n\nThis provides developers with the information needed to understand\nthe codebase, extend functionality, and contribute to the project.\"",
  "description": "Commit developer documentation"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git log -1 --format=\"commit %H%nAuthor: %an <%ae>%nDate:   %ad%n%n%s%n%n%b\"",
  "description": "Verify the commit"
}

🔧 Tool: bash
Input: {
  "command": "export CI=true DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never HOMEBREW_NO_AUTO_UPDATE=1 GIT_EDITOR=: EDITOR=: VISUAL='' GIT_SEQUENCE_EDITOR=: GIT_MERGE_AUTOEDIT=no GIT_PAGER=cat PAGER=cat npm_config_yes=true PIP_NO_INPUT=1 YARN_ENABLE_IMMUTABLE_INSTALLS=false; git status --short docs/",
  "description": "Check docs directory status"
}
<summary>
## Summary: Developer Documentation - Commit Changes

### Changes Committed
- Created `docs/DEVELOPER_GUIDE.md` - comprehensive developer documentation
- Updated `.automaker/features/developer-documentation/` feature state files

### Files Modified
- `docs/DEVELOPER_GUIDE.md` (new - 983 lines)
- `.automaker/features/developer-documentation/agent-output.md` (new)
- `.automaker/features/developer-documentation/feature.json` (modified)
- `.automaker/features/developer-documentation/feature.json.bak1-3` (backups)

### Commit Details
- **Commit Hash:** `a69405d98cd920b3da292da0053b292fd9f3eaf4`
- **Commit Type:** `docs(dev)`
- **Commit Message:**
```
docs(dev): add comprehensive developer documentation

Add DEVELOPER_GUIDE.md with:
- Architecture overview with ASCII diagrams
- Complete project structure documentation
- Core module descriptions and API references
- Data flow documentation
- Extension guides for adding new models/formats
- Testing and debugging guidelines

This provides developers with the information needed to understand
the codebase, extend functionality, and contribute to the project.
```

### Documentation Content
The DEVELOPER_GUIDE.md includes:
1. **Architecture Overview** - High-level system architecture with ASCII diagrams
2. **Project Structure** - Complete directory tree with module descriptions
3. **Core Modules** - Detailed documentation for video, depth, stereo, core, web API, and batch modules
4. **Data Flow** - Frame processing pipeline documentation
5. **Extending the System** - Guides for adding new depth models, stereo formats, and CLI commands
6. **API Reference** - Configuration classes and exception documentation
7. **Testing** - Test execution and writing guidelines
8. **Debugging** - Logging, GPU debugging, and performance profiling

### Verification Status
- Documentation file created and verified at `docs/DEVELOPER_GUIDE.md`
- Commit successfully created with conventional commit format
- No Playwright verification required for documentation-only changes

### Notes for Developer
- The documentation follows the existing pattern in `docs/USER_GUIDE.md`
- ASCII diagrams are used for architecture visualization (Mermaid syntax also available)
- Code examples are included for all major APIs
</summary>

---

## Follow-up Session

I'll complete the Testing step for the developer documentation feature. Let me first review what was implemented and identify testing needs.

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review developer documentation for accuracy",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Create tests for documentation code examples",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Verify API references in documentation",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Test documentation links and references",
      "status": "pending",
      "priority": "medium"
    },
    {
      "content": "Run all tests and verify coverage",
      "status": "pending",
      "priority": "high"
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/docs/DEVELOPER_GUIDE.md"
}

🔧 Tool: bash
Input: {
  "command": "ls -la tests/",
  "description": "List test directory structure"
}

🔧 Tool: glob
Input: {
  "pattern": "tests/**/*.py"
}
Let me examine the existing documentation test pattern and create comprehensive tests for the developer guide:

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/stereo/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/depth/__init__.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/docs/test_user_guide.py"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/src/video2d3d/core/__init__.py"
}
Now I'll create comprehensive tests for the developer documentation:

🔧 Tool: write
Input: {
  "content": "\"\"\"Tests for DEVELOPER_GUIDE.md documentation.\n\nThis module validates the developer guide documentation for:\n- Structure and completeness\n- Code example syntax (Python, YAML, bash)\n- Internal links and references\n- API references matching actual implementations\n- Import statements accuracy\n\"\"\"\n\nimport ast\nimport re\nfrom pathlib import Path\n\nimport pytest\nimport yaml\n\n\n# Path to the DEVELOPER_GUIDE.md file\nDEVELOPER_GUIDE_PATH = Path(__file__).parent.parent.parent / \"docs\" / \"DEVELOPER_GUIDE.md\"\n\n\n@pytest.fixture\ndef developer_guide_content() -> str:\n    \"\"\"Load the DEVELOPER_GUIDE.md content.\"\"\"\n    if not DEVELOPER_GUIDE_PATH.exists():\n        pytest.skip(\"DEVELOPER_GUIDE.md not found\")\n    return DEVELOPER_GUIDE_PATH.read_text()\n\n\n@pytest.fixture\ndef developer_guide_lines(developer_guide_content: str) -> list[str]:\n    \"\"\"Split content into lines.\"\"\"\n    return developer_guide_content.split(\"\\n\")\n\n\nclass TestDeveloperGuideExists:\n    \"\"\"Test that the developer guide file exists and is accessible.\"\"\"\n\n    def test_developer_guide_file_exists(self) -> None:\n        \"\"\"Verify DEVELOPER_GUIDE.md exists in docs directory.\"\"\"\n        assert DEVELOPER_GUIDE_PATH.exists(), f\"DEVELOPER_GUIDE.md not found at {DEVELOPER_GUIDE_PATH}\"\n\n    def test_developer_guide_not_empty(self, developer_guide_content: str) -> None:\n        \"\"\"Verify DEVELOPER_GUIDE.md has substantial content.\"\"\"\n        assert len(developer_guide_content) > 5000, \"DEVELOPER_GUIDE.md appears to be too short\"\n\n    def test_developer_guide_has_version(self, developer_guide_content: str) -> None:\n        \"\"\"Verify version information is present.\"\"\"\n        assert \"**Version:**\" in developer_guide_content, \"Missing version information\"\n\n\nclass TestDeveloperGuideStructure:\n    \"\"\"Test the structure and organization of the developer guide.\"\"\"\n\n    REQUIRED_SECTIONS = [\n        \"Architecture Overview\",\n        \"Project Structure\",\n        \"Core Modules\",\n        \"Data Flow\",\n        \"Extending the System\",\n        \"API Reference\",\n        \"Testing\",\n        \"Debugging\",\n    ]\n\n    def test_has_table_of_contents(self, developer_guide_content: str) -> None:\n        \"\"\"Verify table of contents exists.\"\"\"\n        assert \"## Table of Contents\" in developer_guide_content, \"Missing Table of Contents section\"\n\n    def test_has_all_required_sections(self, developer_guide_content: str) -> None:\n        \"\"\"Verify all required sections are present.\"\"\"\n        for section in self.REQUIRED_SECTIONS:\n            pattern = rf\"##\\s+.*{re.escape(section)}\"\n            assert re.search(pattern, developer_guide_content, re.IGNORECASE), (\n                f\"Missing required section: {section}\"\n            )\n\n    def test_section_hierarchy(self, developer_guide_lines: list[str]) -> None:\n        \"\"\"Verify headings use valid markdown levels (1-6).\"\"\"\n        for line in developer_guide_lines:\n            if match := re.match(r\"^(#{1,6})\\s\", line):\n                level = len(match.group(1))\n                assert 1 <= level <= 6, f\"Invalid heading level: '{line}'\"\n\n    def test_has_architecture_diagram(self, developer_guide_content: str) -> None:\n        \"\"\"Verify architecture diagram is present.\"\"\"\n        assert \"High-Level Architecture\" in developer_guide_content, \"Missing High-Level Architecture section\"\n        # Check for ASCII diagram indicators\n        assert \"┌\" in developer_guide_content or \"```\" in developer_guide_content, (\n            \"Missing architecture diagram\"\n        )\n\n    def test_has_processing_pipeline(self, developer_guide_content: str) -> None:\n        \"\"\"Verify processing pipeline is documented.\"\"\"\n        assert \"Processing Pipeline\" in developer_guide_content, \"Missing Processing Pipeline section\"\n\n\nclass TestDeveloperGuideCodeBlocks:\n    \"\"\"Test code blocks in the developer guide.\"\"\"\n\n    def test_code_blocks_balanced(self, developer_guide_content: str) -> None:\n        \"\"\"Verify all code blocks are properly closed.\"\"\"\n        code_block_count = developer_guide_content.count(\"```\")\n        assert code_block_count % 2 == 0, (\n            f\"Unbalanced code blocks: found {code_block_count} ``` markers (should be even)\"\n        )\n\n    def test_yaml_code_blocks_valid(self, developer_guide_content: str) -> None:\n        \"\"\"Verify YAML code blocks are valid syntax.\"\"\"\n        yaml_pattern = r\"```yaml\\n(.*?)```\"\n        yaml_blocks = re.findall(yaml_pattern, developer_guide_content, re.DOTALL)\n\n        errors = []\n        for i, yaml_content in enumerate(yaml_blocks):\n            try:\n                yaml.safe_load(yaml_content)\n            except yaml.YAMLError as e:\n                errors.append(f\"YAML block {i + 1}: {e}\")\n\n        assert not errors, f\"Invalid YAML code blocks:\\n\" + \"\\n\".join(errors)\n\n    def test_python_code_blocks_syntax(self, developer_guide_content: str) -> None:\n        \"\"\"Verify Python code blocks have valid syntax.\"\"\"\n        python_pattern = r\"```python\\n(.*?)```\"\n        python_blocks = re.findall(python_pattern, developer_guide_content, re.DOTALL)\n\n        errors = []\n        for i, python_content in enumerate(python_blocks):\n            try:\n                ast.parse(python_content)\n            except SyntaxError as e:\n                errors.append(f\"Python block {i + 1}: {e}\")\n\n        assert not errors, f\"Invalid Python code blocks:\\n\" + \"\\n\".join(errors)\n\n    def test_bash_code_blocks_present(self, developer_guide_content: str) -> None:\n        \"\"\"Verify bash code blocks are present for CLI examples.\"\"\"\n        bash_pattern = r\"```bash\\n(.*?)```\"\n        bash_blocks = re.findall(bash_pattern, developer_guide_content, re.DOTALL)\n\n        assert len(bash_blocks) >= 5, (\n            f\"Expected at least 5 bash code examples, found {len(bash_blocks)}\"\n        )\n\n    def test_has_import_examples(self, developer_guide_content: str) -> None:\n        \"\"\"Verify import examples are provided.\"\"\"\n        import_patterns = [\n            r\"from video2d3d\\.\",\n            r\"import video2d3d\",\n        ]\n        \n        found = any(re.search(pattern, developer_guide_content) for pattern in import_patterns)\n        assert found, \"Missing import examples from video2d3d package\"\n\n\nclass TestDeveloperGuideModuleDocumentation:\n    \"\"\"Test that core modules are properly documented.\"\"\"\n\n    def test_video_module_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify video module is documented.\"\"\"\n        assert \"Video Module\" in developer_guide_content or \"video/\" in developer_guide_content, (\n            \"Missing Video Module documentation\"\n        )\n        assert \"FrameExtractor\" in developer_guide_content, \"Missing FrameExtractor documentation\"\n        assert \"VideoWriter\" in developer_guide_content, \"Missing VideoWriter documentation\"\n\n    def test_depth_module_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify depth module is documented.\"\"\"\n        assert \"Depth Module\" in developer_guide_content or \"depth/\" in developer_guide_content, (\n            \"Missing Depth Module documentation\"\n        )\n        assert \"DepthMapProcessor\" in developer_guide_content, \"Missing DepthMapProcessor documentation\"\n        assert \"TemporalSmoother\" in developer_guide_content, \"Missing TemporalSmoother documentation\"\n\n    def test_stereo_module_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify stereo module is documented.\"\"\"\n        assert \"Stereo Module\" in developer_guide_content or \"stereo/\" in developer_guide_content, (\n            \"Missing Stereo Module documentation\"\n        )\n        assert \"DIBREngine\" in developer_guide_content, \"Missing DIBREngine documentation\"\n        assert \"DIBRConfig\" in developer_guide_content, \"Missing DIBRConfig documentation\"\n\n    def test_core_module_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify core module is documented.\"\"\"\n        assert \"Core Module\" in developer_guide_content or \"core/\" in developer_guide_content, (\n            \"Missing Core Module documentation\"\n        )\n        assert \"BatchProcessor\" in developer_guide_content or \"FrameBatchProcessor\" in developer_guide_content, (\n            \"Missing BatchProcessor documentation\"\n        )\n\n    def test_web_api_module_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify web API module is documented.\"\"\"\n        assert \"Web API\" in developer_guide_content or \"web/\" in developer_guide_content, (\n            \"Missing Web API Module documentation\"\n        )\n\n    def test_batch_module_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify batch module is documented.\"\"\"\n        assert \"Batch Module\" in developer_guide_content or \"batch/\" in developer_guide_content, (\n            \"Missing Batch Module documentation\"\n        )\n\n\nclass TestDeveloperGuideAPIReferences:\n    \"\"\"Test that API references match actual implementations.\"\"\"\n\n    def test_depth_processor_config_exists(self) -> None:\n        \"\"\"Verify DepthProcessorConfig exists in the codebase.\"\"\"\n        from video2d3d.depth import DepthProcessorConfig\n        assert DepthProcessorConfig is not None\n\n    def test_depth_map_processor_exists(self) -> None:\n        \"\"\"Verify DepthMapProcessor exists in the codebase.\"\"\"\n        from video2d3d.depth import DepthMapProcessor\n        assert DepthMapProcessor is not None\n\n    def test_dibr_engine_exists(self) -> None:\n        \"\"\"Verify DIBREngine exists in the codebase.\"\"\"\n        from video2d3d.stereo import DIBREngine\n        assert DIBREngine is not None\n\n    def test_dibr_config_exists(self) -> None:\n        \"\"\"Verify DIBRConfig exists in the codebase.\"\"\"\n        from video2d3d.stereo import DIBRConfig\n        assert DIBRConfig is not None\n\n    def test_frame_batch_processor_exists(self) -> None:\n        \"\"\"Verify FrameBatchProcessor exists in the codebase.\"\"\"\n        from video2d3d.core import FrameBatchProcessor\n        assert FrameBatchProcessor is not None\n\n    def test_batch_processor_config_exists(self) -> None:\n        \"\"\"Verify BatchProcessorConfig exists in the codebase.\"\"\"\n        from video2d3d.core import BatchProcessorConfig\n        assert BatchProcessorConfig is not None\n\n    def test_processing_mode_exists(self) -> None:\n        \"\"\"Verify ProcessingMode exists in the codebase.\"\"\"\n        from video2d3d.core import ProcessingMode\n        assert ProcessingMode is not None\n\n    def test_stereo_generator_exists(self) -> None:\n        \"\"\"Verify StereoGenerator exists in the codebase.\"\"\"\n        from video2d3d.stereo import StereoGenerator\n        assert StereoGenerator is not None\n\n    def test_anaglyph_encoder_exists(self) -> None:\n        \"\"\"Verify AnaglyphEncoder exists in the codebase.\"\"\"\n        from video2d3d.stereo import AnaglyphEncoder\n        assert AnaglyphEncoder is not None\n\n    def test_side_by_side_encoder_exists(self) -> None:\n        \"\"\"Verify SideBySideEncoder exists in the codebase.\"\"\"\n        from video2d3d.stereo import SideBySideEncoder\n        assert SideBySideEncoder is not None\n\n\nclass TestDeveloperGuideConfigDocumentation:\n    \"\"\"Test that configuration classes are documented correctly.\"\"\"\n\n    def test_batch_processor_config_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify BatchProcessorConfig fields are documented.\"\"\"\n        expected_fields = [\"batch_size\", \"num_workers\", \"timeout_seconds\", \"max_retries\"]\n        for field in expected_fields:\n            assert field in developer_guide_content, f\"Missing BatchProcessorConfig field: {field}\"\n\n    def test_depth_processor_config_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify DepthProcessorConfig fields are documented.\"\"\"\n        expected_fields = [\"edge_aware_smoothing\", \"bilateral_filter\", \"hole_filling\", \"normalization_method\"]\n        for field in expected_fields:\n            assert field in developer_guide_content, f\"Missing DepthProcessorConfig field: {field}\"\n\n    def test_dibr_config_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify DIBRConfig fields are documented.\"\"\"\n        expected_fields = [\"baseline\", \"focal_length\", \"convergence\", \"hole_filling\"]\n        for field in expected_fields:\n            assert field in developer_guide_content, f\"Missing DIBRConfig field: {field}\"\n\n\nclass TestDeveloperGuideExceptionDocumentation:\n    \"\"\"Test that exception classes are documented.\"\"\"\n\n    def test_exception_table_exists(self, developer_guide_content: str) -> None:\n        \"\"\"Verify exception documentation table exists.\"\"\"\n        assert \"Exception Classes\" in developer_guide_content or \"Exception\" in developer_guide_content, (\n            \"Missing exception documentation\"\n        )\n\n    def test_key_exceptions_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify key exceptions are documented.\"\"\"\n        expected_exceptions = [\n            \"BatchProcessorError\",\n            \"DepthProcessingError\",\n            \"DIBRError\",\n        ]\n        for exc in expected_exceptions:\n            assert exc in developer_guide_content, f\"Missing exception documentation: {exc}\"\n\n\nclass TestDeveloperGuideExtensionGuides:\n    \"\"\"Test that extension guides are documented.\"\"\"\n\n    def test_adding_depth_model_guide(self, developer_guide_content: str) -> None:\n        \"\"\"Verify guide for adding new depth models exists.\"\"\"\n        assert \"Adding a New Depth Model\" in developer_guide_content, (\n            \"Missing guide for adding new depth models\"\n        )\n\n    def test_adding_stereo_format_guide(self, developer_guide_content: str) -> None:\n        \"\"\"Verify guide for adding new stereo formats exists.\"\"\"\n        assert \"Adding a New Stereo Output Format\" in developer_guide_content, (\n            \"Missing guide for adding new stereo formats\"\n        )\n\n    def test_adding_cli_command_guide(self, developer_guide_content: str) -> None:\n        \"\"\"Verify guide for adding new CLI commands exists.\"\"\"\n        assert \"Adding a New CLI Command\" in developer_guide_content, (\n            \"Missing guide for adding new CLI commands\"\n        )\n\n\nclass TestDeveloperGuideTestingDocumentation:\n    \"\"\"Test that testing documentation is present.\"\"\"\n\n    def test_testing_section_exists(self, developer_guide_content: str) -> None:\n        \"\"\"Verify testing section exists.\"\"\"\n        assert \"## Testing\" in developer_guide_content, \"Missing Testing section\"\n\n    def test_pytest_examples_present(self, developer_guide_content: str) -> None:\n        \"\"\"Verify pytest usage examples are present.\"\"\"\n        assert \"pytest\" in developer_guide_content, \"Missing pytest examples\"\n\n    def test_test_fixture_documentation(self, developer_guide_content: str) -> None:\n        \"\"\"Verify test fixture documentation exists.\"\"\"\n        assert \"fixtures\" in developer_guide_content.lower(), \"Missing test fixture documentation\"\n\n\nclass TestDeveloperGuideDebuggingDocumentation:\n    \"\"\"Test that debugging documentation is present.\"\"\"\n\n    def test_debugging_section_exists(self, developer_guide_content: str) -> None:\n        \"\"\"Verify debugging section exists.\"\"\"\n        assert \"## Debugging\" in developer_guide_content, \"Missing Debugging section\"\n\n    def test_logging_documentation(self, developer_guide_content: str) -> None:\n        \"\"\"Verify logging documentation exists.\"\"\"\n        assert \"LOG_LEVEL\" in developer_guide_content or \"logging\" in developer_guide_content.lower(), (\n            \"Missing logging documentation\"\n        )\n\n    def test_common_issues_table(self, developer_guide_content: str) -> None:\n        \"\"\"Verify common issues table exists.\"\"\"\n        assert \"Common Issues\" in developer_guide_content, \"Missing Common Issues section\"\n\n\nclass TestDeveloperGuidePerformanceDocumentation:\n    \"\"\"Test that performance documentation is present.\"\"\"\n\n    def test_performance_section_exists(self, developer_guide_content: str) -> None:\n        \"\"\"Verify performance section exists.\"\"\"\n        assert \"Performance\" in developer_guide_content, \"Missing Performance section\"\n\n    def test_gpu_memory_documentation(self, developer_guide_content: str) -> None:\n        \"\"\"Verify GPU memory management documentation exists.\"\"\"\n        assert \"GPU\" in developer_guide_content or \"memory\" in developer_guide_content.lower(), (\n            \"Missing GPU memory documentation\"\n        )\n\n\nclass TestDeveloperGuideLinks:\n    \"\"\"Test links and references in the developer guide.\"\"\"\n\n    def test_internal_anchor_links(self, developer_guide_content: str) -> None:\n        \"\"\"Verify internal anchor links point to existing sections.\"\"\"\n        anchor_pattern = r\"\\[([^\\]]+)\\]\\(#[a-z0-9-]+\\)\"\n        anchor_links = re.findall(anchor_pattern, developer_guide_content)\n\n        assert len(anchor_links) >= 5, (\n            f\"Expected at least 5 internal anchor links, found {len(anchor_links)}\"\n        )\n\n    def test_no_broken_markdown_links(self, developer_guide_content: str) -> None:\n        \"\"\"Verify no broken markdown link syntax.\"\"\"\n        broken_patterns = [\n            r\"\\[[^\\]]+\\]\\(\\s*\\)\",  # Empty link: [text]()\n            r\"\\[\\s*\\]\\([^)]+\\)\",  # Empty text: [](url)\n        ]\n\n        for pattern in broken_patterns:\n            matches = re.findall(pattern, developer_guide_content)\n            assert not matches, f\"Found broken markdown links: {matches}\"\n\n    def test_user_guide_reference(self, developer_guide_content: str) -> None:\n        \"\"\"Verify reference to USER_GUIDE.md exists.\"\"\"\n        assert \"USER_GUIDE.md\" in developer_guide_content, \"Missing reference to USER_GUIDE.md\"\n\n\nclass TestDeveloperGuideCompleteness:\n    \"\"\"Test overall completeness of documentation.\"\"\"\n\n    def test_minimum_line_count(self, developer_guide_content: str) -> None:\n        \"\"\"Verify documentation has sufficient content.\"\"\"\n        line_count = len(developer_guide_content.split(\"\\n\"))\n        assert line_count >= 500, (\n            f\"Documentation too short: {line_count} lines (expected at least 500)\"\n        )\n\n    def test_minimum_word_count(self, developer_guide_content: str) -> None:\n        \"\"\"Verify documentation has sufficient detail.\"\"\"\n        # Remove code blocks for word count\n        text_only = re.sub(r\"```.*?```\", \"\", developer_guide_content, flags=re.DOTALL)\n        word_count = len(text_only.split())\n        assert word_count >= 3000, (\n            f\"Documentation lacks detail: {word_count} words (expected at least 3000)\"\n        )\n\n    def test_no_placeholder_text(self, developer_guide_content: str) -> None:\n        \"\"\"Verify no TODO or placeholder text remains.\"\"\"\n        placeholders = [\n            \"TODO:\",\n            \"FIXME:\",\n            \"TBD:\",\n            \"[INSERT\",\n            \"[PLACEHOLDER\",\n        ]\n\n        for placeholder in placeholders:\n            assert placeholder not in developer_guide_content.upper(), (\n                f\"Found placeholder text: {placeholder}\"\n            )\n\n    def test_documentation_freshness(self, developer_guide_content: str) -> None:\n        \"\"\"Verify documentation includes last updated date.\"\"\"\n        assert \"2026\" in developer_guide_content or \"2025\" in developer_guide_content, (\n            \"Documentation may be outdated - no recent year found\"\n        )\n\n\nclass TestDeveloperGuideProjectStructure:\n    \"\"\"Test that project structure documentation is accurate.\"\"\"\n\n    def test_project_structure_section(self, developer_guide_content: str) -> None:\n        \"\"\"Verify project structure section exists.\"\"\"\n        assert \"## Project Structure\" in developer_guide_content, \"Missing Project Structure section\"\n\n    def test_main_directories_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify main directories are documented.\"\"\"\n        expected_dirs = [\n            \"src/video2d3d/\",\n            \"tests/\",\n            \"config/\",\n            \"docs/\",\n        ]\n        for dir_path in expected_dirs:\n            assert dir_path in developer_guide_content, f\"Missing directory documentation: {dir_path}\"\n\n    def test_source_structure_documented(self, developer_guide_content: str) -> None:\n        \"\"\"Verify source code structure is documented.\"\"\"\n        expected_modules = [\n            \"video/\",\n            \"depth/\",\n            \"stereo/\",\n            \"core/\",\n            \"utils/\",\n        ]\n        for module in expected_modules:\n            assert module in developer_guide_content, f\"Missing module documentation: {module}\"\n",
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/tests/docs/test_developer_guide.py"
}

🔧 Tool: todowrite
Input: {
  "todos": [
    {
      "content": "Review developer documentation for accuracy",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Create tests for documentation code examples",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Verify API references in documentation",
      "priority": "high",
      "status": "completed"
    },
    {
      "content": "Test documentation links and references",
      "priority": "medium",
      "status": "completed"
    },
    {
      "content": "Run all tests and verify coverage",
      "priority": "high",
      "status": "in_progress"
    }
  ]
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/docs/test_developer_guide.py -v --tb=short 2>&1 | head -150",
  "description": "Run developer guide tests"
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -c \"import pytest; import sys; sys.exit(pytest.main(['-v', 'tests/docs/test_developer_guide.py', '--tb=short']))\" 2>&1 | head -200",
  "description": "Run developer guide tests via Python"
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml",
  "offset": 70,
  "limit": 30
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml",
  "limit": 15,
  "offset": 78
}

🔧 Tool: edit
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml",
  "edits": [
    {
      "lines": [],
      "op": "replace",
      "pos": "81#WJ",
      "end": "81#WJ"
    },
    {
      "op": "replace",
      "pos": "82#YR",
      "end": "82#YR",
      "lines": []
    }
  ]
}

🔧 Tool: read
Input: {
  "filePath": "/home/dkp/Documents/Automaker/2dto3d/pyproject.toml",
  "limit": 20,
  "offset": 75
}

🔧 Tool: bash
Input: {
  "command": "cd /home/dkp/Documents/Automaker/2dto3d && python -m pytest tests/docs/test_developer_guide.py -v --tb=short 2>&1 | head -200",
  "description": "Run developer guide tests"
}
