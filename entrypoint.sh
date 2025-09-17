#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_DIR="${APP_DIR:-/app}"
readonly LOG_LEVEL="${LOG_LEVEL:-info}"
readonly HOST="${HOST:-0.0.0.0}"
readonly PORT="${PORT:-8000}"
readonly WORKERS="${WORKERS:-1}"
readonly MAX_REQUESTS="${MAX_REQUESTS:-1000}"
readonly MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-100}"
readonly TIMEOUT="${TIMEOUT:-30}"
readonly KEEPALIVE="${KEEPALIVE:-2}"
readonly ENVIRONMENT="${ENVIRONMENT:-production}"

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_debug() {
    if [[ "${LOG_LEVEL}" == "debug" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
    fi
}

error_exit() {
    log_error "$1"
    exit "${2:-1}"
}

cleanup() {
    local exit_code=$?
    log_info "Cleaning up..."
    jobs -p | xargs -r kill 2>/dev/null || true
    exit $exit_code
}

trap cleanup EXIT INT TERM

health_check() {
    local service="$1"
    local host="$2"
    local port="$3"
    local timeout="${4:-5}"

    log_debug "Checking $service at $host:$port"

    if timeout "$timeout" bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        log_info "$service is available at $host:$port"
        return 0
    else
        log_warn "$service is not available at $host:$port"
        return 1
    fi
}

wait_for_service() {
    local service="$1"
    local host="$2"
    local port="$3"
    local max_attempts="${4:-30}"
    local attempt=1

    log_info "Waiting for $service to be ready..."

    while [[ $attempt -le $max_attempts ]]; do
        if health_check "$service" "$host" "$port" 2; then
            log_info "$service is ready after $attempt attempts"
            return 0
        fi

        log_debug "Attempt $attempt/$max_attempts failed, waiting 2 seconds..."
        sleep 2
        ((attempt++))
    done

    error_exit "$service failed to become available after $max_attempts attempts"
}

validate_environment() {
    log_info "Validating environment..."

    local required_vars=(
        "DATABASE_URL"
        "MONGODB_URL"
        "SECRET_KEY"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
        log_debug "$var is set"
    done

    if ! command -v python3 &> /dev/null; then
        error_exit "Python3 is not installed"
    fi

    cd "$APP_DIR"
    if ! python3 -c "import sys; sys.path.insert(0, '.'); from src.main import app" 2>/dev/null; then
        if ! python3 -c "from main import app" 2>/dev/null; then
            error_exit "Cannot import FastAPI app. Check your Python path and dependencies."
        fi
    fi

    log_info "Environment validation completed"
}

setup_application() {
    log_info "Setting up application..."

    export PYTHONPATH="$APP_DIR:${PYTHONPATH:-}"

    cd "$APP_DIR" || error_exit "Cannot change to app directory: $APP_DIR"

    log_debug "Current directory: $(pwd)"
    log_debug "Python path: $PYTHONPATH"

    if [[ "$LOG_LEVEL" == "debug" ]]; then
        log_debug "Directory contents:"
        ls -la

        log_debug "Python files structure:"
        find . -name "*.py" -type f | head -20
    fi

    log_info "Application setup completed"
}

wait_for_dependencies() {
    log_info "Waiting for external dependencies..."

    local db_host db_port mongo_host mongo_port

    if [[ "${DATABASE_URL:-}" =~ postgresql://.*@([^:/]+):?([0-9]+)?/ ]]; then
        db_host="${BASH_REMATCH[1]}"
        db_port="${BASH_REMATCH[2]:-5432}"

        wait_for_service "PostgreSQL" "$db_host" "$db_port"
    else
        log_warn "Cannot parse DATABASE_URL for connection check"
    fi

    if [[ "${MONGODB_URL:-}" =~ mongodb://.*@?([^:/]+):?([0-9]+)?/ ]]; then
        mongo_host="${BASH_REMATCH[1]}"
        mongo_port="${BASH_REMATCH[2]:-27017}"

        wait_for_service "MongoDB" "$mongo_host" "$mongo_port"
    elif [[ "${MONGODB_URL:-}" =~ mongodb://([^:/]+):?([0-9]+)?/ ]]; then
        mongo_host="${BASH_REMATCH[1]}"
        mongo_port="${BASH_REMATCH[2]:-27017}"

        wait_for_service "MongoDB" "$mongo_host" "$mongo_port"
    else
        log_warn "Cannot parse MONGODB_URL for connection check"
    fi

    log_info "All dependencies are ready"
}

get_app_module() {
    cd "$APP_DIR"

    if [[ -f "src/main.py" ]]; then
        echo "src.main:app"
    elif [[ -f "main.py" ]]; then
        echo "main:app"
    else
        error_exit "Cannot find main.py in expected locations"
    fi
}

run_migrations() {
    log_info "Running database migrations..."

    cd "$APP_DIR"

    if command -v aerich &> /dev/null && [[ -f "pyproject.toml" ]]; then
        log_info "Running Aerich migrations..."
        aerich upgrade || log_warn "Aerich migration failed, continuing anyway"
    else
        log_debug "Aerich not available or configured, skipping migrations"
    fi
}

bootstrap_initial() {
    log_info "Bootstrapping default user ..."

    cd "$APP_DIR"

    if [[ -f "src/bootstrap_initial.py" ]]; then
        python3 src/bootstrap_initial.py || log_warn "User initial bootstrap failed, continuing anyway"
        log_info "User initial bootstrap completed"
    else
        log_warn "src/bootstrap_initial.py not found, skipping User creation"
    fi
}

start_application() {
    local app_module
    app_module=$(get_app_module)

    log_info "Starting Support System API..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Host: $HOST"
    log_info "Port: $PORT"
    log_info "Workers: $WORKERS"
    log_info "App module: $app_module"

    cd "$APP_DIR"

    if [[ "$ENVIRONMENT" == "development" ]]; then
        log_info "Starting in development mode with auto-reload"
        exec uvicorn "$app_module" \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --log-level "$LOG_LEVEL"
    else
        log_info "Starting in production mode with Uvicorn"
        exec uvicorn "$app_module" \
            --host "$HOST" \
            --port "$PORT" \
            --workers "$WORKERS" \
            --log-level "$LOG_LEVEL" \
            --access-log \
            --no-use-colors \
            --loop uvloop
    fi
}

preflight_checks() {
    log_info "Running pre-flight checks..."

    local available_space
    available_space=$(df /tmp | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 1048576 ]]; then
        log_warn "Low disk space available: ${available_space}KB"
    fi

    if [[ -f /proc/meminfo ]]; then
        local available_memory
        available_memory=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
        if [[ $available_memory -lt 524288 ]]; then
            log_warn "Low memory available: ${available_memory}KB"
        fi
    fi

    if lsof -Pi ":$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        error_exit "Port $PORT is already in use"
    fi

    log_info "Pre-flight checks completed"
}

main() {
    log_info "=== Support System API Entrypoint ==="
    log_info "Starting initialization sequence..."

    validate_environment
    setup_application
    preflight_checks
    wait_for_dependencies
    run_migrations
    bootstrap_initial
    start_application
}

main "$@"