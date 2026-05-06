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

if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  source ".env"
fi

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Error: .venv not found. Create it with: python3 -m venv .venv" >&2
  exit 1
fi

".venv/bin/python" -m pip install -e . >/dev/null

set +e
".venv/bin/python" -m drau.detection_test "$@"
TEST_EXIT=$?
set -e

if [[ "$TEST_EXIT" -ne 0 ]]; then
  exit "$TEST_EXIT"
fi

LATEST_CSV="$(ls -t ".data/detection-tests"/session_*.csv 2>/dev/null | head -1 || true)"

if [[ -z "$LATEST_CSV" ]]; then
  echo "No session CSV found in .data/detection-tests/ — skipping analysis." >&2
  exit 1
fi

echo ""
".venv/bin/python" -m drau.analysis "$LATEST_CSV"
