#!/usr/bin/env bash
# Validate JSON syntax (no formatting opinions).
# Usage: lint-json.sh [file …]
# With no arguments, finds all *.json files under the project root.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
errors=0

if [ $# -gt 0 ]; then
  for f in "$@"; do
    if ! python3 -c "import json, sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
      echo "Invalid JSON: $f"
      errors=$((errors + 1))
    fi
  done
else
  while IFS= read -r f; do
    if ! python3 -c "import json, sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
      echo "Invalid JSON: $f"
      errors=$((errors + 1))
    fi
  done < <(find "$ROOT" -name '*.json' -not -path '*/node_modules/*' -not -name 'package-lock.json')
fi

if [ "$errors" -gt 0 ]; then
  echo "$errors file(s) with invalid JSON"
  exit 1
else
  echo "All JSON files are valid"
fi
