#!/usr/bin/env bash
# Create (or recreate) .venv and install all requirements from pyproject.toml.
#
# Usage:
#   ./scripts/setup.sh              # interactive: prompts if .venv already exists
#   ./scripts/setup.sh --recreate   # always remove and recreate .venv
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

RECREATE=false
if [[ "${1:-}" == "--recreate" ]]; then
    RECREATE=true
fi

# ── Python version check ──────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found." >&2; exit 1
fi
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    FOUND=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "Error: Python >= 3.11 required, found $FOUND." >&2; exit 1
fi

# ── Handle existing .venv ─────────────────────────────────────────────────────
if [[ -d ".venv" ]]; then
    if [[ "$RECREATE" == "true" ]]; then
        echo "Removing existing .venv..."
        rm -rf .venv
    elif [[ -t 0 ]]; then
        printf ".venv already exists. Recreate? [y/N] "
        read -r ans
        if [[ "${ans,,}" == "y" ]]; then
            rm -rf .venv
        else
            echo "Keeping existing .venv. Updating requirements..."
            .venv/bin/python -m pip install -e . -q
            echo "Done."
            exit 0
        fi
    else
        echo ".venv already exists; updating requirements (pass --recreate to force rebuild)."
        .venv/bin/python -m pip install -e . -q
        exit 0
    fi
fi

# ── Create and populate .venv ─────────────────────────────────────────────────
echo "Creating .venv..."
python3 -m venv .venv
.venv/bin/python -m pip install -U pip -q
echo "Installing requirements from pyproject.toml..."
.venv/bin/python -m pip install -e . -q
echo "Done.  Activate with:  . .venv/bin/activate"
