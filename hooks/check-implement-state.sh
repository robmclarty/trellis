#!/usr/bin/env bash
# PreToolUse hook for Bash(git commit) — checks .implement-state.md
# Warns if acceptance criteria are incomplete. Exit 0 (warn only).
# Receives tool input as JSON on stdin.

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only check git commit commands
if [[ "$COMMAND" != *"git commit"* ]]; then
  exit 0
fi

STATE_FILE=".implement-state.md"

if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

PENDING=$(grep -c '^\- \[ \]' "$STATE_FILE" 2>/dev/null || true)

if [ "$PENDING" -gt 0 ]; then
  echo "⚠ .implement-state.md has $PENDING pending acceptance criteria."
  echo "  Consider completing all criteria before committing."
  grep '^\- \[ \]' "$STATE_FILE" | head -5
  if [ "$PENDING" -gt 5 ]; then
    echo "  ... and $((PENDING - 5)) more"
  fi
fi

exit 0
