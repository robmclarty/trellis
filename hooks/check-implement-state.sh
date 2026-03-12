#!/usr/bin/env bash
# PreToolUse hook for Bash(git commit) — checks .implement-state.md
# Warns if acceptance criteria are incomplete. Exit 0 (warn only).

STATE_FILE=".implement-state.md"

if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

PENDING=$(grep -c '^\- \[ \]' "$STATE_FILE" 2>/dev/null || echo "0")

if [ "$PENDING" -gt 0 ]; then
  echo "⚠ .implement-state.md has $PENDING pending acceptance criteria."
  echo "  Consider completing all criteria before committing."
  grep '^\- \[ \]' "$STATE_FILE" | head -5
  if [ "$PENDING" -gt 5 ]; then
    echo "  ... and $((PENDING - 5)) more"
  fi
fi

exit 0
