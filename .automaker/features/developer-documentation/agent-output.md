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
