#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
fi

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Error: .venv not found. Create it with: python3 -m venv .venv" >&2
  exit 1
fi

".venv/bin/python" -m pip install -e . >/dev/null
".venv/bin/python" -m drau.data \
  --cache-dir ".data/drone-audio-detection-samples" \
  --audio-dir ".data/drone-audio-detection-samples/audio"

