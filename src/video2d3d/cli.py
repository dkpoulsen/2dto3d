"""CLI entry point for the video2d3d application."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from video2d3d import __version__
from video2d3d.utils.config import get_config
from video2d3d.utils.logger import LogLevel, configure_logging, get_logger, log_exception
from video2d3d.utils.progress import ProgressConfig, VideoConversionProgress

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
    "checkerboard": "Checkerboard pattern (3D displays)",
    "top_bottom": "Top-bottom (over-under) stereoscopic",
    "vr": "VR format - side-by-side 360° equirectangular (Oculus, Vive, Quest)",
    "vr_top_bottom": "VR format - top-bottom 360° equirectangular",
    "vr180": "VR180 format - 180° field of view (Oculus, Vive)",
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
    preview: bool = typer.Option(
        False, "--preview", "-p", help="Enable live preview during processing"
    ),
    no_progress: bool = typer.Option(
        False, "--no-progress", help="Disable progress tracking display"
    ),
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
    logger.debug(f"Format: {output_format}, Model: {model}, GPU: {gpu}, Preview: {preview}")

    console.print(f"[bold blue]Converting:[/bold blue] {input_file} -> {output_file}")
    console.print(f"[bold]Format:[/bold] {output_format}, [bold]Model:[/bold] {model}")
    if preview:
        console.print("[bold green]Preview:[/bold green] Enabled (press Q or ESC to close)")

    # Initialize progress tracking
    config = get_config()
    progress_config = ProgressConfig(
        enabled=config.progress.enabled and not no_progress,
        show_speed=config.progress.show_speed,
        show_eta=config.progress.show_eta,
        show_elapsed=config.progress.show_elapsed,
        show_percent=config.progress.show_percent,
        show_overall=config.progress.show_overall,
        refresh_rate=config.progress.refresh_rate,
        transient=config.progress.transient,
    )
    progress = VideoConversionProgress(
        total_frames=0,  # Will be updated when conversion is implemented
        config=progress_config,
        input_file=input_file,
        output_file=output_file,
        console=console,
    )

    try:
        with progress:
            # TODO: Implement actual conversion with progress tracking
            # Example flow:
            # 1. progress.start_stage(ProgressStage.EXTRACT, total=frame_count)
            # 2. progress.start_stage(ProgressStage.PROCESS, total=frame_count)
            # 3. progress.start_stage(ProgressStage.WRITE, total=frame_count)
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
    console.print("\n[dim]Default model: midas_small[/dim]")


@app.command("list-formats")
def list_formats() -> None:
    """List available 3D output formats.

    Displays a table of all supported stereoscopic 3D output formats
    with their descriptions.
    """
    logger = get_logger("list_formats")
    logger.info("Listing available formats")

    console.print("\n[bold blue]Available 3D Output Formats[/bold blue]\n")


@app.command("batch-convert")
def batch_convert(
    input_path: str = typer.Argument(
        ..., help="Path to input file, directory, or wildcard pattern", metavar="INPUT"
    ),
    output_dir: str | None = typer.Option(
        None, "--output-dir", "-o", help="Output directory for converted files"
    ),
    pattern: str | None = typer.Option(
        None, "--pattern", "-p", help="Wildcard pattern for file matching (e.g., '*.mp4')"
    ),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", help="Search directories recursively"
    ),
    format: str = typer.Option(
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
    concurrent: int = typer.Option(
        1, "--concurrent", "-c", help="Number of concurrent jobs to process"
    ),
    skip_existing: bool = typer.Option(
        True, "--skip-existing/--no-skip-existing", help="Skip files that already have output"
    ),
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Watch folder for new files (continuous mode)"
    ),
    list_file: str | None = typer.Option(
        None, "--list", "-l", help="Path to text file containing list of videos to process"
    ),
) -> None:
    from pathlib import Path

    from video2d3d.batch import BatchJobResult, BatchQueueConfig, BatchVideoQueue

    logger = get_logger("batch_convert")
    output_format = validate_output_format(format)
    validated_model = validate_model(model)

    console.print("[bold blue]Batch Video Conversion[/bold blue]")
    console.print(f"[bold]Format:[/bold] {format}, [bold]Model:[/bold] {model}")
    console.print(f"[bold]Concurrent:[/bold] {concurrent}, [bold]Recursive:[/bold] {recursive}")

    config = BatchQueueConfig(
        max_concurrent_jobs=concurrent,
        skip_existing=skip_existing,
        output_directory=Path(output_dir) if output_dir else None,
    )

    if watch:
        config.folder_watcher.enabled = True
        config.folder_watcher.watch_paths = [Path(input_path)]

    def dummy_processor(input_path: Path, output_path: Path) -> BatchJobResult:
        return BatchJobResult(
            success=True, output_path=output_path, metadata={"format": format, "model": model}
        )

    queue = BatchVideoQueue(config=config, processor=dummy_processor)

    try:
        input_p = Path(input_path)

        if list_file:
            jobs = queue.add_jobs_from_list(
                list(Path(line.strip()) for line in open(list_file) if line.strip())
            )
        elif pattern:
            jobs = queue.add_jobs_from_pattern(
                pattern, base_dir=input_p if input_p.is_dir() else None
            )
        elif input_p.is_dir():
            jobs = queue.add_jobs_from_directory(input_p, recursive=recursive)
        else:
            job = queue.add_job(input_p)
            jobs = [job]

        console.print(f"[green]Added {len(jobs)} jobs to queue[/green]")

        if not watch:
            queue.start()

            import time

            while queue.running_count > 0 or queue.pending_count > 0:
                stats = queue.get_stats()
                console.print(
                    f"\r[bold]Progress:[/bold] {stats.completed_jobs}/{stats.total_jobs} "
                    f"completed, {stats.running_jobs} running, {stats.pending_jobs} pending",
                    end="",
                )
                time.sleep(1.0)

            console.print()
            stats = queue.get_stats()
            console.print("\n[bold green]Batch complete![/bold green]")
            console.print(f"  Completed: {stats.completed_jobs}")
            console.print(f"  Failed: {stats.failed_jobs}")
            console.print(f"  Skipped: {stats.skipped_jobs}")
            console.print(f"  Success rate: {stats.success_rate:.1f}%")

            queue.stop()
        else:
            console.print("[yellow]Watching for new files... Press Ctrl+C to stop[/yellow]")
            queue.start()
            try:
                import time

                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping...[/yellow]")
                queue.stop()

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        log_exception("Batch conversion failed", exception=e)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("queue-status")
def queue_status(
    state_file: str | None = typer.Option(
        None, "--state-file", "-s", help="Path to queue state file"
    ),
    watch: bool = typer.Option(False, "--watch", "-w", help="Continuously monitor queue status"),
    clear_completed: bool = typer.Option(False, "--clear", help="Clear completed jobs from queue"),
) -> None:
    import json
    from pathlib import Path

    from video2d3d.batch import BatchQueueConfig

    logger = get_logger("queue_status")
    config = BatchQueueConfig()
    state_path = Path(state_file) if state_file else Path("logs/batch_queue_state.json")

    if not state_path.exists():
        console.print(f"[yellow]No queue state file found at {state_path}[/yellow]")
        console.print("[dim]Start a batch conversion to create a queue.[/dim]")
        return

    try:
        with open(state_path) as f:
            state = json.load(f)

        console.print("\n[bold blue]Batch Queue Status[/bold blue]")
        console.print(f"[dim]State file: {state_path}[/dim]")
        console.print(f"[dim]Saved at: {state.get('saved_at', 'unknown')}[/dim]\n")

        jobs = state.get("jobs", [])

        stats = {
            "total": len(jobs),
            "pending": sum(1 for j in jobs if j["status"] == "pending"),
            "running": sum(1 for j in jobs if j["status"] == "running"),
            "completed": sum(1 for j in jobs if j["status"] == "completed"),
            "failed": sum(1 for j in jobs if j["status"] == "failed"),
            "cancelled": sum(1 for j in jobs if j["status"] == "cancelled"),
            "skipped": sum(1 for j in jobs if j["status"] == "skipped"),
        }

        table = Table(title="Queue Statistics")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="green")
        table.add_row("Total", str(stats["total"]))
        table.add_row("Pending", str(stats["pending"]))
        table.add_row("Running", str(stats["running"]))
        table.add_row("Completed", str(stats["completed"]))
        table.add_row("Failed", str(stats["failed"]))
        table.add_row("Cancelled", str(stats["cancelled"]))
        table.add_row("Skipped", str(stats["skipped"]))
        console.print(table)

        if stats["total"] > 0:
            success_rate = (
                (stats["completed"] / (stats["completed"] + stats["failed"])) * 100
                if (stats["completed"] + stats["failed"]) > 0
                else 0
            )
            console.print(f"\n[bold]Success Rate:[/bold] {success_rate:.1f}%")

        if watch:
            console.print("\n[yellow]Monitoring... Press Ctrl+C to stop[/yellow]")
            import time

            try:
                while True:
                    time.sleep(2.0)
                    console.clear()
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopped.[/yellow]")

    except json.JSONDecodeError as e:
        console.print(f"[red]Error reading state file: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        log_exception("Failed to get queue status", exception=e)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("serve")
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host address to bind the server",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port number to bind the server",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development",
    ),
    workers: int = typer.Option(
        1,
        "--workers",
        "-w",
        help="Number of worker processes",
    ),
    log_level: str = typer.Option(
        "info",
        "--log-level",
        "-l",
        help="Log level (debug, info, warning, error, critical)",
    ),
) -> None:
    """Start the REST API server.

    This command starts a FastAPI-based REST API server that provides
    endpoints for video upload, job submission, status checking, and
    result download.

    Examples:
        video2d3d serve
        video2d3d serve --host 127.0.0.1 --port 8080
        video2d3d serve --reload  # Development mode with auto-reload
    """
    logger = get_logger("serve")

    try:
        import uvicorn
    except ImportError:
        console.print("[red]Error: uvicorn is not installed.[/red]")
        console.print("[yellow]Install with: pip install uvicorn[standard][/yellow]")
        raise typer.Exit(code=1)

    config = get_config()

    console.print("[bold blue]Starting 2Dto3D API Server[/bold blue]")
    console.print(f"[bold]Host:[/bold] {host}")
    console.print(f"[bold]Port:[/bold] {port}")
    console.print(f"[bold]Workers:[/bold] {workers}")
    console.print(f"[bold]API Docs:[/bold] http://{host}:{port}/docs")
    console.print(f"[bold]ReDoc:[/bold] http://{host}:{port}/redoc")
    console.print()
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")

    logger.info(f"Starting API server on {host}:{port}")

    try:
        uvicorn.run(
            "video2d3d.web.app:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # Reload doesn't work with multiple workers
            log_level=log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")
    except Exception as e:
        log_exception("Server error", exception=e)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("config-export")
def config_export(
    output_file: str = typer.Argument(
        ...,
        help="Path to output configuration file (e.g., config.json or config.yaml)",
        metavar="OUTPUT_FILE",
    ),
    format: str = typer.Option(
        "auto",
        "--format",
        "-f",
        help="Output format: json, yaml, or auto (detect from file extension)",
    ),
) -> None:
    """Export the current configuration to a JSON or YAML file.

    This command exports all configuration parameters, including processing
    settings, depth estimation options, stereo generation settings, and more.

    Examples:
        video2d3d config-export my-config.json
        video2d3d config-export my-config.yaml
        video2d3d config-export config.json --format json
    """
    from pathlib import Path

    from video2d3d.utils.config import export_current_config

    logger = get_logger("config_export")

    output_path = Path(output_file)

    # Determine format
    if format == "auto":
        suffix = output_path.suffix.lower()
        if suffix == ".json":
            actual_format = "json"
        elif suffix in (".yaml", ".yml"):
            actual_format = "yaml"
        else:
            console.print(f"[red]Cannot auto-detect format from extension '{suffix}'[/red]")
            console.print("[yellow]Use --format json or --format yaml[/yellow]")
            raise typer.Exit(code=1)
    else:
        actual_format = format.lower()

    try:
        export_current_config(output_path, actual_format)
        console.print(f"[green]Configuration exported to:[/green] {output_path}")
        logger.info(f"Configuration exported to {output_path}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        log_exception("Failed to export configuration", exception=e)
        console.print(f"[red]Error exporting configuration: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("config-import")
def config_import(
    input_file: str = typer.Argument(
        ..., help="Path to configuration file to import (JSON or YAML)", metavar="INPUT_FILE"
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        "-a",
        help="Apply imported configuration as the global (active) configuration",
    ),
) -> None:
    """Import configuration from a JSON or YAML file.

    This command imports configuration from a file. By default, it validates
    the configuration and displays a summary. Use --apply to make it the
    active configuration.

    Examples:
        video2d3d config-import my-config.json
        video2d3d config-import my-config.yaml --apply
    """
    from pathlib import Path

    from video2d3d.utils.config import import_and_apply_config, import_config

    logger = get_logger("config_import")

    input_path = Path(input_file)

    if not input_path.exists():
        console.print(f"[red]Error: File not found: {input_path}[/red]")
        raise typer.Exit(code=1)

    try:
        config = import_and_apply_config(input_path) if apply else import_config(input_path)

        if apply:
            console.print(f"[green]Configuration imported and applied from:[/green] {input_path}")
            logger.info(f"Configuration imported and applied from {input_path}")
        else:
            console.print(f"[green]Configuration imported from:[/green] {input_path}")
            logger.info(f"Configuration imported from {input_path}")

        # Display summary
        console.print("\n[bold]Configuration Summary:[/bold]")
        console.print(f"  Project: {config.project_name}")
        console.print(f"  Version: {config.version}")
        console.print(
            f"  Processing: batch_size={config.processing.batch_size}, workers={config.processing.num_workers}"
        )
        console.print(f"  Depth Model: {config.depth_estimation.model}")
        console.print(f"  Output Format: {config.stereo_generation.format}")

        if not apply:
            console.print("\n[dim]Use --apply to make this the active configuration[/dim]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        log_exception("Failed to import configuration", exception=e)
        console.print(f"[red]Error importing configuration: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("gui")
def gui() -> None:
    """Launch the desktop GUI application.

    This command starts the graphical user interface for video conversion.
    The GUI provides an easy-to-use interface for single and batch video conversion.

    Examples:
        video2d3d gui
    """
    logger = get_logger("gui")
    logger.info("Launching GUI application")

    try:
        from video2d3d.gui import run_gui

        exit_code = run_gui()
        raise typer.Exit(code=exit_code)
    except ImportError as e:
        console.print("[red]Error: PyQt6 is not installed.[/red]")
        console.print("[yellow]Install with: pip install PyQt6[/yellow]")
        console.print(f"[dim]{e}[/dim]")
        raise typer.Exit(code=1)
    except Exception as e:
        log_exception("Failed to launch GUI", exception=e)
        console.print(f"[red]Error launching GUI: {e}[/red]")
        raise typer.Exit(code=1)


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
