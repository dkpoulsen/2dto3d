"""Configuration management using YAML files with environment variable support."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


def get_config_path() -> Path:
    """Get the configuration directory path."""
    # Check for custom config path in environment
    custom_path = get_env_var("VIDEO2D3D_CONFIG_PATH")
    if custom_path:
        return Path(custom_path)

    # Default to config/ directory relative to project root
    return Path(__file__).parent.parent.parent.parent / "config"


def get_environment() -> str:
    """Get the current environment (development, production, testing)."""
    return get_env_var("VIDEO2D3D_ENV", "development").lower()


@dataclass
class ProcessingConfig:
    """Processing configuration settings."""

    batch_size: int = 4
    num_workers: int = 4
    use_gpu: bool = True
    gpu_device: int = 0
    max_memory_percent: int = 80
    frame_buffer_size: int = 100
    mixed_precision: bool = True
    
    # GPU memory management
    auto_batch_size: bool = True
    min_batch_size: int = 1
    max_batch_size: int = 32
    memory_fraction: float = 0.8
    fallback_to_cpu: bool = True
    pinned_memory: bool = True
    
    # GPU optimization
    cudnn_benchmark: bool = True
    async_transfer: bool = True

@dataclass
class VideoInputConfig:
    """Video input configuration settings."""

    supported_formats: List[str] = field(
        default_factory=lambda: ["mp4", "avi", "mov", "mkv", "webm"]
    )
    default_width: int = 0
    default_height: int = 0
    default_fps: int = 0
    max_width: int = 3840
    max_height: int = 2160


@dataclass
class VideoOutputConfig:
    """Video output configuration settings."""

    format: str = "mp4"
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 23
    pixel_format: str = "yuv420p"


@dataclass
class DepthEstimationConfig:
    """Depth estimation configuration settings."""

    model: str = "midas_small"
    model_path: str = ""
    auto_download: bool = True
    output_width: int = 384
    output_height: int = 384
    min_depth: float = 0.0
    max_depth: float = 1.0
    temporal_consistency: bool = True
    temporal_smoothing_factor: float = 0.5


@dataclass
class AnaglyphConfig:
    """Anaglyph 3D configuration settings."""

    type: str = "red_cyan"
    color_method: str = "dubois"


@dataclass
class SideBySideConfig:
    """Side-by-side 3D configuration settings."""

    layout: str = "horizontal"
    swap_eyes: bool = False
    half_width: bool = False


@dataclass
class StereoGenerationConfig:
    """Stereoscopic generation configuration settings."""

    format: str = "side_by_side"
    baseline: float = 0.05
    focal_length: float = 1.0
    convergence: float = 0.5
    anaglyph: AnaglyphConfig = field(default_factory=AnaglyphConfig)
    side_by_side: SideBySideConfig = field(default_factory=SideBySideConfig)


@dataclass
class QualityConfig:
    """Quality configuration settings."""

    preset: str = "balanced"
    post_processing: bool = True
    calculate_metrics: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    file: str = "logs/video2d3d.log"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    rotation: str = "10 MB"
    retention: str = "7 days"
    colorize: bool = True


@dataclass
class WebApiConfig:
    """Web API configuration settings."""

    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    prefix: str = "/api/v1"
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    max_upload_size: int = 500
    upload_dir: str = "uploads"


@dataclass
class Config:
    """Main configuration class."""

    project_name: str = "2Dto3D Video Converter"
    version: str = "0.1.0"
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    video_input: VideoInputConfig = field(default_factory=VideoInputConfig)
    video_output: VideoOutputConfig = field(default_factory=VideoOutputConfig)
    depth_estimation: DepthEstimationConfig = field(default_factory=DepthEstimationConfig)
    stereo_generation: StereoGenerationConfig = field(default_factory=StereoGenerationConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    web_api: WebApiConfig = field(default_factory=WebApiConfig)


def deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update a dictionary with another dictionary."""
    result = base_dict.copy()
    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file and return its contents."""
    if not file_path.exists():
        return {}

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data else {}


def _parse_config_section(config_data: Dict[str, Any], section: str, config_class: type) -> Any:
    """Parse a configuration section into a dataclass instance."""
    section_data = config_data.get(section, {})
    if isinstance(section_data, dict):
        # Handle nested configs
        if section == "stereo_generation":
            if "anaglyph" in section_data:
                section_data["anaglyph"] = AnaglyphConfig(**section_data["anaglyph"])
            if "side_by_side" in section_data:
                section_data["side_by_side"] = SideBySideConfig(**section_data["side_by_side"])
        return config_class(**{k: v for k, v in section_data.items() if hasattr(config_class, k)})
    return config_class()


def load_config(
    config_path: Optional[Union[str, Path]] = None,
    environment: Optional[str] = None,
) -> Config:
    """
    Load configuration from YAML files with environment-specific overrides.

    Args:
        config_path: Path to configuration directory. Defaults to config/ directory.
        environment: Environment name (development, production, testing).
                     Defaults to VIDEO2D3D_ENV environment variable or 'development'.

    Returns:
        Config object with loaded settings.
    """
    # Determine config path
    if config_path is None:
        config_path = get_config_path()
    else:
        config_path = Path(config_path)

    # Determine environment
    if environment is None:
        environment = get_environment()

    # Load default configuration
    default_config = load_yaml_file(config_path / "default.yaml")

    # Load environment-specific configuration
    env_config_path = config_path / f"{environment}.yaml"
    env_config = load_yaml_file(env_config_path)

    # Merge configurations (environment overrides default)
    merged_config = deep_update(default_config, env_config)

    # Parse into Config object
    config = Config()

    if "project" in merged_config:
        config.project_name = merged_config["project"].get("name", config.project_name)
        config.version = merged_config["project"].get("version", config.version)

    if "processing" in merged_config:
        config.processing = _parse_config_section(merged_config, "processing", ProcessingConfig)

    if "video_input" in merged_config:
        config.video_input = _parse_config_section(merged_config, "video_input", VideoInputConfig)

    if "video_output" in merged_config:
        config.video_output = _parse_config_section(
            merged_config, "video_output", VideoOutputConfig
        )

    if "depth_estimation" in merged_config:
        config.depth_estimation = _parse_config_section(
            merged_config, "depth_estimation", DepthEstimationConfig
        )

    if "stereo_generation" in merged_config:
        config.stereo_generation = _parse_config_section(
            merged_config, "stereo_generation", StereoGenerationConfig
        )

    if "quality" in merged_config:
        config.quality = _parse_config_section(merged_config, "quality", QualityConfig)

    if "logging" in merged_config:
        config.logging = _parse_config_section(merged_config, "logging", LoggingConfig)

    if "web_api" in merged_config:
        config.web_api = _parse_config_section(merged_config, "web_api", WebApiConfig)

    return config


# Global configuration instance (lazy-loaded)
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get the global configuration instance.

    Args:
        reload: Force reload of configuration.

    Returns:
        Config object.
    """
    global _config
    if _config is None or reload:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Force reload of configuration."""
    return get_config(reload=True)
