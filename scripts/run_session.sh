#!/usr/bin/env bash
# Runs a complete detection test session and immediately analyses the results.
# All arguments are forwarded to the detection test
# (--samples-num, --mic-num, --dist-max, and optional --audio-dir / --output-dir).
#
# Example:
#   ./scripts/run_session.sh --samples-num 20 --mic-num 2 --dist-max 30
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=scripts/drau_lib.sh
source scripts/drau_lib.sh

_require_env
_require_venv
_require_audio_data
_install_package

set +e
"$REPO_ROOT/.venv/bin/python" -m drau.detection_test "$@"
TEST_EXIT=$?
set -e

if [[ "$TEST_EXIT" -ne 0 ]]; then
  exit "$TEST_EXIT"
fi

OUTPUT_DIR="$DETECTION_OUTPUT_DIR"
LATEST_CSV="$(ls -t "$REPO_ROOT/$OUTPUT_DIR"/session_*.csv 2>/dev/null | head -1 || true)"

if [[ -z "$LATEST_CSV" ]]; then
  echo "No session CSV found in $OUTPUT_DIR/ — skipping analysis." >&2
  exit 1
fi

echo ""
"$REPO_ROOT/.venv/bin/python" -m drau.analysis "$LATEST_CSV"
