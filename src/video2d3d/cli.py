"""CLI entry point for the video2d3d application."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from video2d3d import __version__
from video2d3d.utils.config import get_config
from video2d3d.utils.logger import (
    LogLevel,
    configure_logging,
    get_logger,
    log_exception,
)

# ============================================================================
# Constants
# ============================================================================

# Available depth estimation models with metadata
DEPTH_MODELS: dict[str, dict[str, str]] = {
    "midas_small": {
        "description": "MiDaS v2.1 Small - Fast, good for preview",
        "quality": "Medium",
        "speed": "Fast",
    },
    "midas_hybrid": {
        "description": "MiDaS v3.1 Hybrid - Balanced quality/speed",
        "quality": "Good",
        "speed": "Medium",
    },
    "dpt_large": {
        "description": "DPT Large - Highest quality",
        "quality": "Best",
        "speed": "Slow",
    },
    "dpt_hybrid": {
        "description": "DPT Hybrid - Good quality, faster than large",
        "quality": "Good",
        "speed": "Medium",
    },
}

# Available 3D output formats
OUTPUT_FORMATS: dict[str, str] = {
    "side_by_side": "Side-by-side (left-right) stereoscopic view",
    "anaglyph": "Anaglyph (red-cyan glasses required)",
    "interlaced": "Interlaced (row-alternating)",
    "vr": "VR format (over-under)",
}

# Valid choices for CLI options
VALID_MODELS = list(DEPTH_MODELS.keys())
VALID_FORMATS = list(OUTPUT_FORMATS.keys())

# ============================================================================
# CLI Application Setup
# ============================================================================

app = typer.Typer(
    name="video2d3d",
    help="Convert 2D videos to 3D using deep learning depth estimation",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Display version information and exit.

    Args:
        value: Whether the version flag was passed.

    Raises:
        typer.Exit: Always raised after displaying version.
    """
    if value:
        console.print(f"[bold blue]video2d3d[/bold blue] version: [green]{__version__}[/green]")
        raise typer.Exit()


def validate_file_exists(file_path: str, param_name: str = "file") -> Path:
    """Validate that a file exists.

    Args:
        file_path: Path to the file.
        param_name: Name of the parameter for error messages.

    Returns:
        Path object if file exists.

    Raises:
        typer.BadParameter: If file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise typer.BadParameter(f"{param_name} '{file_path}' does not exist")
    if not path.is_file():
        raise typer.BadParameter(f"{param_name} '{file_path}' is not a file")
    return path


def validate_model(model: str) -> str:
    """Validate that the model name is valid.

    Args:
        model: Model name to validate.

    Returns:
        Validated model name.

    Raises:
        typer.BadParameter: If model name is invalid.
    """
    if model not in VALID_MODELS:
        valid_options = ", ".join(VALID_MODELS)
        raise typer.BadParameter(f"Invalid model '{model}'. Valid options: {valid_options}")
    return model


def validate_output_format(output_format: str) -> str:
    """Validate that the output format is valid.

    Args:
        output_format: Format name to validate.

    Returns:
        Validated format name.

    Raises:
        typer.BadParameter: If format name is invalid.
    """
    if output_format not in VALID_FORMATS:
        valid_options = ", ".join(VALID_FORMATS)
        raise typer.BadParameter(
            f"Invalid format '{output_format}'. Valid options: {valid_options}"
        )
    return output_format


@app.callback()
def _setup_global_options(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging (DEBUG level)",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
    log_file: str | None = typer.Option(
        None,
        "--log-file",
        help="Path to log file (default: logs/video2d3d.log)",
    ),
) -> None:
    """2Dto3D Video Converter - Convert 2D videos to 3D using deep learning.

    This application uses machine learning models to estimate depth from 2D video
    frames and generates stereoscopic 3D video output.

    Args:
        version: Show version and exit.
        verbose: Enable verbose (DEBUG) logging.
        log_level: Set the logging level.
        log_file: Custom path for log file.
    """
    # Configure logging
    level = LogLevel.DEBUG if verbose else log_level.upper()
    config = get_config()
    configure_logging(
        config=config.logging,
        log_level=level,
        log_file=log_file,
    )
    logger = get_logger("cli")
    logger.debug(f"Logging initialized at {level} level")


@app.command()
def convert(
    input_file: str = typer.Argument(..., help="Path to input 2D video file", metavar="INPUT_FILE"),
    output_file: str = typer.Argument(
        ..., help="Path to output 3D video file", metavar="OUTPUT_FILE"
    ),
    output_format: str = typer.Option(
        "side_by_side",
        "--format",
        "-f",
        help=f"3D output format. Options: {', '.join(VALID_FORMATS)}",
    ),
    model: str = typer.Option(
        "midas_small",
        "--model",
        "-m",
        help=f"Depth estimation model. Options: {', '.join(VALID_MODELS)}",
    ),
    gpu: bool = typer.Option(True, "--gpu/--no-gpu", help="Use GPU acceleration"),
    config_path: str | None = typer.Option(None, "--config", "-c", help="Path to config file"),
) -> None:
    """Convert a 2D video to 3D.

    This command takes a 2D video file and generates a stereoscopic 3D version
    using deep learning depth estimation.

    Examples:
        video2d3d convert input.mp4 output_3d.mp4
        video2d3d convert input.mp4 output_3d.mp4 --format anaglyph
        video2d3d convert input.mp4 output_3d.mp4 --model dpt_large --no-gpu
    """
    logger = get_logger("convert")

    # Validate inputs
    try:
        validate_file_exists(input_file, "Input file")
        model = validate_model(model)
        output_format = validate_output_format(output_format)
    except typer.BadParameter:
        raise  # Re-raise to show error to user

    logger.info(f"Starting conversion: {input_file} -> {output_file}")
    logger.debug(f"Format: {output_format}, Model: {model}, GPU: {gpu}")

    console.print(f"[bold blue]Converting:[/bold blue] {input_file} -> {output_file}")
    console.print(f"[bold]Format:[/bold] {output_format}, [bold]Model:[/bold] {model}")

    try:
        # TODO: Implement actual conversion
        logger.warning("Conversion not yet implemented - placeholder execution")
        console.print("[yellow]Conversion not yet implemented[/yellow]")
    except FileNotFoundError as e:
        log_exception("Input file not found", exception=e, input_file=input_file)
        console.print(f"[red]Error: Input file not found: {e}[/red]")
        raise typer.Exit(code=1)
    except PermissionError as e:
        log_exception("Permission denied", exception=e, output_file=output_file)
        console.print(f"[red]Error: Permission denied: {e}[/red]")
        raise typer.Exit(code=1)
    except RuntimeError as e:
        log_exception(
            "Conversion failed",
            exception=e,
            input_file=input_file,
            output_file=output_file,
        )
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        log_exception(
            "Unexpected error during conversion",
            exception=e,
            input_file=input_file,
            output_file=output_file,
        )
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def info() -> None:
    """Display configuration and system information."""
    logger = get_logger("info")
    logger.info("Displaying system information")

    config = get_config()

    console.print("\n[bold blue]2Dto3D Video Converter - System Information[/bold blue]\n")

    # Project info
    table = Table(title="Project Information", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Name", config.project_name)
    table.add_row("Version", __version__)
    table.add_row(
        "Environment",
        get_config.__module__.split(".")[0] if hasattr(get_config, "__module__") else "unknown",
    )
    console.print(table)
    logger.debug(f"Displayed project info: {config.project_name} v{__version__}")

    # Processing settings
    proc_table = Table(title="Processing Settings")
    proc_table.add_column("Setting", style="cyan")
    proc_table.add_column("Value", style="green")
    proc_table.add_row("Batch Size", str(config.processing.batch_size))
    proc_table.add_row("Workers", str(config.processing.num_workers))
    proc_table.add_row("GPU Enabled", str(config.processing.use_gpu))
    proc_table.add_row("Mixed Precision", str(config.processing.mixed_precision))
    console.print(proc_table)

    # Depth estimation settings
    depth_table = Table(title="Depth Estimation")
    depth_table.add_column("Setting", style="cyan")
    depth_table.add_column("Value", style="green")
    depth_table.add_row("Model", config.depth_estimation.model)
    depth_table.add_row(
        "Output Size",
        f"{config.depth_estimation.output_width}x{config.depth_estimation.output_height}",
    )
    depth_table.add_row("Temporal Consistency", str(config.depth_estimation.temporal_consistency))
    console.print(depth_table)

    # Logging settings
    log_table = Table(title="Logging Settings")
    log_table.add_column("Setting", style="cyan")
    log_table.add_column("Value", style="green")
    log_table.add_row("Level", config.logging.level)
    log_table.add_row("Log File", config.logging.file)
    log_table.add_row("Rotation", config.logging.rotation)
    log_table.add_row("Retention", config.logging.retention)
    console.print(log_table)


@app.command("list-models")
def list_models() -> None:
    """List available depth estimation models.

    Displays a table of all supported depth estimation models with their
    descriptions, quality ratings, and relative processing speeds.
    """
    logger = get_logger("list_models")
    logger.info("Listing available models")

    console.print("\n[bold blue]Available Depth Estimation Models[/bold blue]\n")

    table = Table()
    table.add_column("Model", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Quality", style="yellow")
    table.add_column("Speed", style="yellow")

    for model_id, info in DEPTH_MODELS.items():
        table.add_row(model_id, info["description"], info["quality"], info["speed"])

    console.print(table)
    console.print(f"\n[dim]Default model: midas_small[/dim]")


@app.command("list-formats")
def list_formats() -> None:
    """List available 3D output formats.

    Displays a table of all supported stereoscopic 3D output formats
    with their descriptions.
    """
    logger = get_logger("list_formats")
    logger.info("Listing available formats")

    console.print("\n[bold blue]Available 3D Output Formats[/bold blue]\n")

    table = Table()
    table.add_column("Format", style="cyan")
    table.add_column("Description", style="green")

    for format_id, description in OUTPUT_FORMATS.items():
        table.add_row(format_id, description)

    console.print(table)
    console.print(f"\n[dim]Default format: side_by_side[/dim]")


def main() -> None:
    """Main entry point for the CLI application.

    This function serves as the primary entry point defined in pyproject.toml.
    It invokes the Typer application which handles command parsing and execution.
    """
    app()


def run() -> None:
    """Run the CLI application.

    This is an alias for main() provided for backward compatibility and
    programmatic invocation.
    """
    main()


if __name__ == "__main__":
    main()
