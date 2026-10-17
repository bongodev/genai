#!/usr/bin/env bash
# Set up the product agent and run it.
#
#   ./run.sh           set up if needed, then run the app
#   ./run.sh setup     create the virtual environment, install deps, create .env
#   ./run.sh run       run the app (sets up first if needed)

set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR=".venv"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"
APP="product_agent.py"
MIN_PYTHON="3.10"

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

check_python() {
    command -v python3 >/dev/null 2>&1 || die "python3 not found. Install Python $MIN_PYTHON or newer."
    if ! python3 -c "import sys; sys.exit(sys.version_info < (3, 10))"; then
        die "Python $MIN_PYTHON or newer is required (found $(python3 --version))."
    fi
}

create_venv() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        info "Virtual environment already exists in $VENV_DIR"
    else
        info "Creating virtual environment in $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi
}

install_deps() {
    info "Installing dependencies"
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
    "$VENV_DIR/bin/python" -m pip install --quiet -r requirements.txt
}

create_env_file() {
    if [ -f "$ENV_FILE" ]; then
        info "$ENV_FILE already exists, leaving it alone"
    else
        info "Creating $ENV_FILE from $ENV_EXAMPLE"
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "    Edit $ENV_FILE and set GEMINI_API_KEY before running."
    fi
}

setup() {
    check_python
    create_venv
    install_deps
    create_env_file
    info "Setup complete"
}

load_env() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        # shellcheck disable=SC1090
        . "$ENV_FILE"
        set +a
    fi
    if [ -z "${GEMINI_API_KEY:-}" ] || [ "$GEMINI_API_KEY" = "your-key-here" ]; then
        die "GEMINI_API_KEY is not set. Edit $ENV_FILE and add your key."
    fi
}

run_app() {
    if [ ! -x "$VENV_DIR/bin/python" ]; then
        setup
    fi
    load_env
    info "Starting the product agent"
    exec "$VENV_DIR/bin/python" "$APP"
}

case "${1:-run}" in
    setup) setup ;;
    run) run_app ;;
    -h|--help|help)
        sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'
        ;;
    *) die "unknown command '$1'. Use: setup | run" ;;
esac
