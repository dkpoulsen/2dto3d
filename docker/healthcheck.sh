#!/bin/bash
# =============================================================================
# 2Dto3D Video Converter - Docker Health Check Script
# =============================================================================
# This script checks the health of the container and its services.
# Used by Docker's HEALTHCHECK instruction.
#
# Exit codes:
#   0 - Healthy (at least half of checks pass)
#   1 - Unhealthy
# =============================================================================

# Don't use set -e because we want to handle errors gracefully
set -uo pipefail

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
readonly DEFAULT_API_HOST="localhost"
readonly DEFAULT_API_PORT=8000
readonly DEFAULT_TIMEOUT=5
readonly MIN_DISK_SPACE_KB=1048576  # 1GB in KB

# Configuration (allow override via environment)
API_HOST="${API_HOST:-${DEFAULT_API_HOST}}"
API_PORT="${API_PORT:-${DEFAULT_API_PORT}}"
HEALTH_ENDPOINT="http://${API_HOST}:${API_PORT}/health"
TIMEOUT="${HEALTHCHECK_TIMEOUT:-${DEFAULT_TIMEOUT}}"

# -----------------------------------------------------------------------------
# Health Check Functions
# -----------------------------------------------------------------------------

# Check if curl is available
check_curl() {
    if command -v curl &>/dev/null; then
        return 0
    fi
    return 1
}

# Check if API server is running and responding
check_api_server() {
    # First check if curl is available
    if ! check_curl; then
        return 1
    fi
    
    # Try to hit the health endpoint
    local response
    response=$(curl --silent --connect-timeout "${TIMEOUT}" --max-time "${TIMEOUT}" \
        "${HEALTH_ENDPOINT}" 2>/dev/null) || return 1
    
    # Check if response contains status field
    if echo "${response}" | grep -q '"status"'; then
        return 0
    fi
    return 1
}

# Check if video2d3d CLI command is available
check_cli() {
    if command -v video2d3d &>/dev/null; then
        return 0
    fi
    return 1
}

# Check if required directories exist
check_directories() {
    local dirs=(
        "/app/inputs"
        "/app/outputs"
        "/app/logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "${dir}" ]]; then
            return 1
        fi
    done
    return 0
}

# Check if there's sufficient disk space (fail if less than 1GB free)
check_disk_space() {
    # Check if df is available
    if ! command -v df &>/dev/null; then
        return 0  # Skip check if df not available
    fi
    
    local available_kb
    available_kb=$(df -k /app 2>/dev/null | awk 'NR==2 {print $4}') || return 0
    
    # Handle case where df output is empty or invalid
    if [[ ! "${available_kb}" =~ ^[0-9]+$ ]]; then
        return 0  # Skip check if we can't parse df output
    fi
    
    if [[ "${available_kb}" -ge "${MIN_DISK_SPACE_KB}" ]]; then
        return 0
    fi
    return 1
}

# Check if Python and required modules are available
check_python() {
    if command -v python &>/dev/null; then
        return 0
    fi
    return 1
}

# -----------------------------------------------------------------------------
# Main Health Check Logic
# -----------------------------------------------------------------------------
main() {
    local checks_passed=0
    local total_checks=4
    local check_mode="${1:-}"
    
    # Check 1: CLI availability
    if check_cli; then
        ((checks_passed++)) || true
    fi
    
    # Check 2: Directory structure
    if check_directories; then
        ((checks_passed++)) || true
    fi
    
    # Check 3: Disk space
    if check_disk_space; then
        ((checks_passed++)) || true
    fi
    
    # Check 4: Python availability
    if check_python; then
        ((checks_passed++)) || true
    fi
    
    # Check 5: API server (only if in serve/api mode)
    if [[ "${check_mode}" == "api" ]] || [[ "${check_mode}" == "serve" ]]; then
        ((total_checks++)) || true
        if check_api_server; then
            ((checks_passed++)) || true
        fi
    fi
    
    # Calculate minimum required checks (half of total, rounded up)
    local min_required
    min_required=$(( (total_checks + 1) / 2 ))
    
    # Return success if enough checks pass
    if [[ "${checks_passed}" -ge "${min_required}" ]]; then
        exit 0
    else
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Run Health Check
# -----------------------------------------------------------------------------
main "$@"
