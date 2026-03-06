#!/bin/bash
# =============================================================================
# 2Dto3D Video Converter - Docker Entrypoint Script
# =============================================================================
# This script handles initialization and command routing for the Docker container.
# It supports multiple modes: CLI, API server, and batch processing.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Signal Handling for Graceful Shutdown
# -----------------------------------------------------------------------------
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    
    # Kill any child processes
    if [[ -n "${CHILD_PID:-}" ]]; then
        kill -TERM "${CHILD_PID}" 2>/dev/null || true
        wait "${CHILD_PID}" 2>/dev/null || true
    fi
    
    log_success "Cleanup complete"
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
readonly SCRIPT_NAME="entrypoint.sh"
readonly APP_DIR="/app"
readonly DEFAULT_API_PORT=8000

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Logging Functions
# -----------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# -----------------------------------------------------------------------------
# Print Banner
# -----------------------------------------------------------------------------
print_banner() {
    echo ""
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║           2Dto3D Video Converter - Docker Container           ║"
    echo "  ║                                                               ║"
    echo "  ║  Convert 2D videos to 3D using deep learning depth estimation ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

# -----------------------------------------------------------------------------
# Check GPU Availability
# -----------------------------------------------------------------------------
check_gpu() {
    if [[ -n "${VIDEO2D3D_NO_GPU:-}" ]]; then
        log_info "GPU disabled by environment variable"
        return 1
    fi
    
    if ! command -v nvidia-smi &>/dev/null; then
        log_warning "No NVIDIA GPU detected - running in CPU mode"
        export VIDEO2D3D_NO_GPU=1
        return 1
    fi
    
    if nvidia-smi &>/dev/null; then
        log_success "NVIDIA GPU detected"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
        return 0
    else
        log_warning "NVIDIA GPU detected but not accessible - running in CPU mode"
        export VIDEO2D3D_NO_GPU=1
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Create Required Directories
# -----------------------------------------------------------------------------
setup_directories() {
    log_info "Setting up directories..."
    
    local dirs=(
        "${APP_DIR}/inputs"
        "${APP_DIR}/outputs"
        "${APP_DIR}/logs"
        "${APP_DIR}/models"
        "${APP_DIR}/config"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "${dir}" ]]; then
            mkdir -p "${dir}" || {
                log_error "Failed to create directory: ${dir}"
                return 1
            }
        fi
    done
    
    # Ensure proper permissions if running as root
    if [[ "$(id -u)" -eq 0 ]]; then
        chown -R video2d3d:video2d3d "${APP_DIR}/inputs" "${APP_DIR}/outputs" "${APP_DIR}/logs" "${APP_DIR}/models" 2>/dev/null || true
    fi
    
    log_success "Directories ready"
}

# -----------------------------------------------------------------------------
# Load Environment Variables from .env File
# -----------------------------------------------------------------------------
load_env() {
    local env_file="${APP_DIR}/.env"
    
    if [[ ! -f "${env_file}" ]]; then
        return 0
    fi
    
    log_info "Loading environment from .env file..."
    
    # Read and export variables, handling values with spaces and special chars
    while IFS= read -r line || [[ -n "${line}" ]]; do
        # Skip empty lines and comments
        [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
        
        # Extract variable name and value
        if [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            local name="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            
            # Remove surrounding quotes if present
            if [[ "${value}" =~ ^\"(.*)\"$ ]] || [[ "${value}" =~ ^\'(.*)\'$ ]]; then
                value="${BASH_REMATCH[1]}"
            fi
            
            # Export the variable
            export "${name}=${value}"
        fi
    done < "${env_file}"
    
    log_success "Environment loaded"
}

# -----------------------------------------------------------------------------
# Get API Port (with fallback)
# -----------------------------------------------------------------------------
get_api_port() {
    echo "${API_PORT:-${PORT:-${DEFAULT_API_PORT}}}"
}

# -----------------------------------------------------------------------------
# Command Handlers
# -----------------------------------------------------------------------------
run_serve() {
    local port
    port=$(get_api_port)
    log_info "Starting API server on port ${port}..."
    shift
    
    # Use exec to replace shell with the process, but track PID for cleanup
    exec video2d3d serve --host 0.0.0.0 --port "${port}" "$@"
}

run_batch() {
    log_info "Starting batch conversion..."
    shift
    exec video2d3d batch-convert "$@"
}

run_convert() {
    log_info "Starting single file conversion..."
    shift
    exec video2d3d convert "$@"
}

run_queue_status() {
    log_info "Checking queue status..."
    shift
    exec video2d3d queue-status "$@"
}

run_shell() {
    log_info "Starting interactive shell..."
    shift
    exec /bin/bash "$@"
}

run_python() {
    log_info "Starting Python..."
    shift
    exec python "$@"
}

run_help() {
    exec video2d3d --help
}

run_default() {
    if [[ -n "${1:-}" ]]; then
        exec video2d3d "$@"
    else
        # No command specified - show help
        exec video2d3d --help
    fi
}

# -----------------------------------------------------------------------------
# Main Entrypoint Logic
# -----------------------------------------------------------------------------
main() {
    print_banner
    
    # Setup
    setup_directories || log_warning "Directory setup had issues"
    load_env
    
    # Check GPU if not in CPU-only mode
    check_gpu
    
    # Route command
    local cmd="${1:-}"
    
    case "${cmd}" in
        serve|server|api)
            run_serve "$@"
            ;;
        batch|batch-convert)
            run_batch "$@"
            ;;
        convert)
            run_convert "$@"
            ;;
        queue-status)
            run_queue_status "$@"
            ;;
        info)
            exec video2d3d info
            ;;
        list-models)
            exec video2d3d list-models
            ;;
        list-formats)
            exec video2d3d list-formats
            ;;
        shell|bash|sh)
            run_shell "$@"
            ;;
        python)
            run_python "$@"
            ;;
        help|--help|-h)
            run_help
            ;;
        *)
            run_default "$@"
            ;;
    esac
}

# -----------------------------------------------------------------------------
# Run Main
# -----------------------------------------------------------------------------
main "$@"
