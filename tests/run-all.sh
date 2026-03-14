#!/usr/bin/env bash
# Run all Trellis tests.
# Usage: bash tests/run-all.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAILED=0

echo "=== Script tests ==="
if python3 tests/test-scripts.py; then
  echo ""
else
  FAILED=1
  echo ""
fi

echo "=== Hook tests ==="
if python3 tests/test-hooks.py; then
  echo ""
else
  FAILED=1
  echo ""
fi

echo "=== Snapshot tests ==="
if bash tests/test-snapshots.sh; then
  echo ""
else
  FAILED=1
  echo ""
fi

echo "=== Shell tests ==="
if command -v bats &>/dev/null; then
  if bats tests/test-shell.bats; then
    echo ""
  else
    FAILED=1
    echo ""
  fi
else
  echo "  (skipped — bats not installed)"
  echo "  Install: brew install bats-core"
  echo ""
fi

echo "=== Promptfoo tests ==="
if command -v promptfoo &>/dev/null; then
  if promptfoo eval -c tests/promptfoo.yaml; then
    echo ""
  else
    FAILED=1
    echo ""
  fi
else
  echo "  (skipped — promptfoo not installed)"
  echo "  Install: npm install -g promptfoo"
  echo ""
fi

echo "=== Skill tests (claude -p) ==="
if command -v claude &>/dev/null && [ "${TRELLIS_LLM_TESTS:-}" = "1" ]; then
  if python3 tests/test-skills.py; then
    echo ""
  else
    FAILED=1
    echo ""
  fi
else
  echo "  (skipped — requires claude CLI and TRELLIS_LLM_TESTS=1)"
  echo ""
fi

if [ "$FAILED" -eq 0 ]; then
  echo "All test suites passed."
else
  echo "Some test suites failed."
  exit 1
fi
