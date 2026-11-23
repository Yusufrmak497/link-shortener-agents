#!/usr/bin/env bash
# Quality gate shared by the git pre-commit hook and humans/agents.
# Exits non-zero (blocking the commit) if lint, format, or tests fail.
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || dirname "$0"/..)"
PY_BIN=".venv/bin"
[ -x "$PY_BIN/pytest" ] || PY_BIN="$(dirname "$(command -v pytest)")"

status=0
echo "▶ ruff check";         "$PY_BIN/ruff" check .          || status=1
echo "▶ ruff format --check"; "$PY_BIN/ruff" format --check . || status=1
echo "▶ pytest";              "$PY_BIN/pytest" -q             || status=1

if [ "$status" -ne 0 ]; then
  echo "✖ quality gate FAILED: fix the errors above (do not use --no-verify)." >&2
else
  echo "✔ quality gate passed"
fi
exit "$status"
