#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=scripts/drau_lib.sh
source scripts/drau_lib.sh

_require_env
_require_venv
_require_audio_data
_install_package

"$REPO_ROOT/.venv/bin/python" -m drau.detection_test "$@"
