"""Configuration management using YAML files with environment variable support."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# ============================================================================
# Constants
# ============================================================================

FORMAT_JSON = "json"
FORMAT_YAML = "yaml"
SUPPORTED_EXPORT_FORMATS = (FORMAT_JSON, FORMAT_YAML)


# Public API
# Public API
__all__ = [
    "Config",
    "ProcessingConfig",
    "VideoInputConfig",
    "VideoOutputConfig",
    "DepthEstimationConfig",
    "AnaglyphConfig",
    "SideBySideConfig",
    "StereoGenerationConfig",
    "QualityConfig",
    "LoggingConfig",
    "RateLimitConfig",
    "WebApiConfig",
    "PreviewConfig",
    "ProgressTrackingConfig",
    "UpscalerConfig",
    "VideoDenoisingConfig",
    "export_config",
    "import_config",
    "export_current_config",
    "import_and_apply_config",
    "load_config",
    "get_config",
    "reload_config",
    "FORMAT_JSON",
    "FORMAT_YAML",
    "SUPPORTED_EXPORT_FORMATS",
]

# Load environment variables from .env file
load_dotenv()


def get_env_var(key: str, default: str | None = None) -> str | None:
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class VideoInputConfig:
    """Video input configuration settings."""

    supported_formats: list[str] = field(
        default_factory=lambda: ["mp4", "avi", "mov", "mkv", "webm"]
    )
    default_width: int = 0
    default_height: int = 0
    default_fps: int = 0
    max_width: int = 3840
    max_height: int = 2160

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class VideoOutputConfig:
    """Video output configuration settings."""

    format: str = "mp4"
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 23
    pixel_format: str = "yuv420p"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnaglyphConfig:
    """Anaglyph 3D configuration settings."""

    type: str = "red_cyan"
    color_method: str = "dubois"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SideBySideConfig:
    """Side-by-side 3D configuration settings."""

    layout: str = "horizontal"
    swap_eyes: bool = False
    half_width: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StereoGenerationConfig:
    """Stereoscopic generation configuration settings."""

    format: str = "side_by_side"
    baseline: float = 0.05
    focal_length: float = 1.0
    convergence: float = 0.5
    anaglyph: AnaglyphConfig = field(default_factory=AnaglyphConfig)
    side_by_side: SideBySideConfig = field(default_factory=SideBySideConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class QualityConfig:
    """Quality configuration settings."""

    preset: str = "balanced"
    post_processing: bool = True
    calculate_metrics: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: str = "INFO"
    file: str = "logs/video2d3d.log"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    rotation: str = "10 MB"
    retention: str = "7 days"
    colorize: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration settings.

    Attributes:
        enabled: Whether rate limiting is enabled.
        requests_per_minute: Maximum requests allowed per minute per client.
        requests_per_hour: Maximum requests allowed per hour per client.
        upload_requests_per_minute: Maximum upload requests per minute (stricter).
        storage_uri: Storage backend URI (memory:// or redis://host:port).
        whitelist_ips: List of IP addresses exempt from rate limiting.
    """

    enabled: bool = True
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    upload_requests_per_minute: int = 10
    storage_uri: str = "memory://"
    whitelist_ips: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if self.requests_per_hour <= 0:
            raise ValueError("requests_per_hour must be positive")
        if self.upload_requests_per_minute <= 0:
            raise ValueError("upload_requests_per_minute must be positive")
        if self.requests_per_hour < self.requests_per_minute:
            raise ValueError("requests_per_hour must be >= requests_per_minute")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WebApiConfig:
    """Web API configuration settings."""

    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    prefix: str = "/api/v1"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    max_upload_size: int = 500
    upload_dir: str = "uploads"
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PreviewConfig:
    """Preview window configuration settings."""

    enabled: bool = False
    window_name: str = "2Dto3D Preview"
    layout: str = "horizontal"  # Options: horizontal, vertical, grid
    scale: float = 0.5
    show_fps: bool = True
    show_frame_info: bool = True
    auto_resize: bool = True
    max_width: int = 1920
    max_height: int = 1080
    update_interval_ms: int = 33

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProgressTrackingConfig:
    """Progress tracking configuration settings.

    Attributes:
        enabled: Whether progress tracking is enabled.
        show_speed: Show processing speed (frames/sec).
        show_eta: Show estimated time remaining.
        show_elapsed: Show elapsed time.
        show_percent: Show percentage complete.
        show_overall: Show overall progress across all stages.
        refresh_rate: Display refresh rate in seconds.
        transient: Whether progress bars disappear after completion.
    """

    enabled: bool = True
    show_speed: bool = True
    show_eta: bool = True
    show_elapsed: bool = True
    show_percent: bool = True
    show_overall: bool = True
    refresh_rate: float = 0.1
    transient: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class UpscalerConfig:
    """AI video upscaling configuration settings.

    Attributes:
        enabled: Whether AI upscaling is enabled.
        model_type: Type of upscaling model (esrgan, realesrgan-x4plus, etc.).
        use_gpu: Whether to use GPU acceleration.
        tile_size: Size of processing tiles (0 = auto).
        denoise_strength: Denoising strength (0-1).
    """

    enabled: bool = False
    model_type: str = "realesrgan-x4plus"
    use_gpu: bool = True
    tile_size: int = 0
    denoise_strength: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class VideoDenoisingConfig:
    """Video denoising configuration settings.

    Attributes:
        enabled: Whether video denoising is enabled.
        model_type: Type of denoising model (fastdvdnet, basicvsr_plusplus).
        use_gpu: Whether to use GPU acceleration.
        num_frames: Number of frames for temporal context.
        noise_level: Default noise level for denoising.
        fallback_to_cpu: Whether to fallback to CPU on GPU error.
    """

    enabled: bool = False
    model_type: str = "fastdvdnet"
    use_gpu: bool = True
    num_frames: int = 5
    noise_level: float = 30.0
    fallback_to_cpu: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


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
    preview: PreviewConfig = field(default_factory=PreviewConfig)
    progress: ProgressTrackingConfig = field(default_factory=ProgressTrackingConfig)
    upscaler: UpscalerConfig = field(default_factory=UpscalerConfig)
    video_denoising: VideoDenoisingConfig = field(default_factory=VideoDenoisingConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert the entire configuration to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create a Config instance from a dictionary.

        Args:
            data: Dictionary containing configuration values.

        Returns:
            Config object with the specified values.

        Raises:
            ValueError: If configuration data is invalid.
        """
        config = cls()

        try:
            if "project_name" in data:
                config.project_name = data["project_name"]
            if "version" in data:
                config.version = data["version"]

            if "processing" in data:
                config.processing = cls._parse_simple_section(data["processing"], ProcessingConfig)

            if "video_input" in data:
                config.video_input = cls._parse_simple_section(
                    data["video_input"], VideoInputConfig
                )

            if "video_output" in data:
                config.video_output = cls._parse_simple_section(
                    data["video_output"], VideoOutputConfig
                )

            if "depth_estimation" in data:
                config.depth_estimation = cls._parse_simple_section(
                    data["depth_estimation"], DepthEstimationConfig
                )

            if "stereo_generation" in data:
                config.stereo_generation = cls._parse_stereo_generation(data["stereo_generation"])

            if "quality" in data:
                config.quality = cls._parse_simple_section(data["quality"], QualityConfig)

            if "logging" in data:
                config.logging = cls._parse_simple_section(data["logging"], LoggingConfig)

            if "web_api" in data:
                config.web_api = cls._parse_web_api(data["web_api"])

            if "preview" in data:
                config.preview = cls._parse_simple_section(data["preview"], PreviewConfig)

            if "progress" in data:
                config.progress = cls._parse_simple_section(
                    data["progress"], ProgressTrackingConfig
                )

            if "video_denoising" in data:
                config.video_denoising = cls._parse_simple_section(
                    data["video_denoising"], VideoDenoisingConfig
                )

        except (TypeError, KeyError) as e:
            raise ValueError(f"Invalid configuration data: {e}") from e

        return config

    @staticmethod
    def _parse_simple_section(section_data: dict[str, Any], config_class: type) -> Any:
        """Parse a simple (non-nested) configuration section.

        Args:
            section_data: Dictionary containing section configuration.
            config_class: The dataclass to instantiate.

        Returns:
            Instantiated configuration object.

        Raises:
            ValueError: If a value does not match the field type.
        """
        import dataclasses
        import typing

        field_types = {f.name: f.type for f in dataclasses.fields(config_class)}
        try:
            hints = typing.get_type_hints(config_class)
        except Exception:
            hints = {}

        filtered_data = {}
        for key, value in section_data.items():
            if not hasattr(config_class, key):
                continue
            expected = hints.get(key, field_types.get(key))
            if expected is not None:
                if isinstance(expected, type) and not isinstance(value, expected):
                    raise ValueError(
                        f"Invalid value for '{key}': expected {expected.__name__}, "
                        f"got {type(value).__name__}"
                    )
            filtered_data[key] = value
        return config_class(**filtered_data)

    @staticmethod
    def _parse_stereo_generation(sg_data: dict[str, Any]) -> StereoGenerationConfig:
        """Parse stereo_generation section with nested configs."""
        anaglyph = AnaglyphConfig(**sg_data.get("anaglyph", {}))
        side_by_side = SideBySideConfig(**sg_data.get("side_by_side", {}))
        filtered_data = {
            k: v
            for k, v in sg_data.items()
            if k not in ("anaglyph", "side_by_side") and hasattr(StereoGenerationConfig, k)
        }
        return StereoGenerationConfig(anaglyph=anaglyph, side_by_side=side_by_side, **filtered_data)

    @staticmethod
    def _parse_web_api(web_data: dict[str, Any]) -> WebApiConfig:
        """Parse web_api section with nested rate_limit config."""
        rate_limit = RateLimitConfig(**web_data.get("rate_limit", {}))
        filtered_data = {
            k: v for k, v in web_data.items() if k != "rate_limit" and hasattr(WebApiConfig, k)
        }
        return WebApiConfig(rate_limit=rate_limit, **filtered_data)


def deep_update(base_dict: dict[str, Any], update_dict: dict[str, Any]) -> dict[str, Any]:
    """Recursively update a dictionary with another dictionary."""
    result = base_dict.copy()
    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_update(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml_file(file_path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    if not file_path.exists():
        return {}

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data if data else {}


def _parse_config_section(config_data: dict[str, Any], section: str, config_class: type) -> Any:
    """Parse a configuration section into a dataclass instance."""
    section_data = config_data.get(section, {})
    if isinstance(section_data, dict):
        # Handle nested configs
        if section == "stereo_generation":
            if "anaglyph" in section_data:
                section_data["anaglyph"] = AnaglyphConfig(**section_data["anaglyph"])
            if "side_by_side" in section_data:
                section_data["side_by_side"] = SideBySideConfig(**section_data["side_by_side"])
        if section == "web_api" and "rate_limit" in section_data:
            section_data["rate_limit"] = RateLimitConfig(**section_data["rate_limit"])
        return config_class(**{k: v for k, v in section_data.items() if hasattr(config_class, k)})
    return config_class()


def load_config(
    config_path: str | Path | None = None,
    environment: str | None = None,
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
    config_path = get_config_path() if config_path is None else Path(config_path)

    # Determine environment
    if environment is None:
        environment = get_environment()

    # Load default configuration
    if config_path.is_file():
        # A single file was passed: use it as the entire configuration
        merged_config = load_yaml_file(config_path)
        env_config_path = None
    else:
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

    if "preview" in merged_config:
        config.preview = _parse_config_section(merged_config, "preview", PreviewConfig)

    if "progress" in merged_config:
        config.progress = _parse_config_section(merged_config, "progress", ProgressTrackingConfig)

    if "upscaler" in merged_config:
        config.upscaler = _parse_config_section(merged_config, "upscaler", UpscalerConfig)

    if "video_denoising" in merged_config:
        config.video_denoising = _parse_config_section(
            merged_config, "video_denoising", VideoDenoisingConfig
        )

    return config


# Global configuration instance (lazy-loaded)
_config: Config | None = None


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


# ============================================================================
# Configuration Export/Import Functions
# ============================================================================


def export_config(
    config: Config,
    output_path: str | Path,
    format: str = FORMAT_JSON,
) -> Path:
    """Export configuration to a file.

    Args:
        config: Configuration object to export.
        output_path: Path where the configuration will be saved.
        format: Output format - 'json' or 'yaml'.

    Returns:
        Path to the exported configuration file.

    Raises:
        ValueError: If format is not 'json' or 'yaml'.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    config_dict = config.to_dict()

    format_lower = format.lower()
    if format_lower == FORMAT_JSON:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
    elif format_lower == FORMAT_YAML:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    else:
        raise ValueError(f"Unsupported format: {format}. Use {SUPPORTED_EXPORT_FORMATS}.")

    return output_path


def import_config(
    input_path: str | Path,
) -> Config:
    """Import configuration from a file.

    Args:
        input_path: Path to the configuration file (JSON or YAML).

    Returns:
        Config object with imported settings.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file format is not supported or content is invalid.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {input_path}")

    suffix = input_path.suffix.lower()

    try:
        if suffix == ".json":
            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)
        elif suffix in (".yaml", ".yml"):
            data = load_yaml_file(input_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .json, .yaml, or .yml.")

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid configuration file: expected a dictionary, got {type(data).__name__}"
            )

        return Config.from_dict(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}") from e


def export_current_config(
    output_path: str | Path,
    format: str = FORMAT_JSON,
) -> Path:
    """Export the current (global) configuration to a file.

    Args:
        output_path: Path where the configuration will be saved.
        format: Output format - 'json' or 'yaml'.

    Returns:
        Path to the exported configuration file.
    """
    config = get_config()
    return export_config(config, output_path, format)


def import_and_apply_config(
    input_path: str | Path,
) -> Config:
    """Import configuration from a file and apply it as the global config.

    Args:
        input_path: Path to the configuration file (JSON or YAML).

    Returns:
        Config object with imported settings (now the global config).
    """
    global _config
    _config = import_config(input_path)
    return _config
