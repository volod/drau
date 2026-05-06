#!/usr/bin/env bash
# Shared helpers for drau scripts.  REPO_ROOT must be set before sourcing.

_load_env() {
  if [[ -f "$REPO_ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
  fi
}

_require_env() {
  if [[ -f "$REPO_ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
  else
    echo "Error: .env not found.  Create it with:  cp .env.example .env" >&2
    exit 1
  fi
}

_require_venv() {
  if [[ ! -x "$REPO_ROOT/.venv/bin/python" ]]; then
    echo "Error: .venv not found.  Create it with:  make venv" >&2
    exit 1
  fi
}

_require_audio_data() {
  if [[ ! -d "$REPO_ROOT/$DETECTION_AUDIO_DIR" ]]; then
    echo "Error: $DETECTION_AUDIO_DIR not found.  Run:  make cache-data" >&2
    exit 1
  fi
}

_install_package() {
  "$REPO_ROOT/.venv/bin/python" -m pip install -e . >/dev/null
}
