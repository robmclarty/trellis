#!/usr/bin/env bash
# PostToolUse hook for Write/Edit — validates .specs/ document structure.
# Checks that documents under .specs/ have their minimum required sections.
# Outputs warnings only (exit 0).

FILE="$1"

# Only check files under .specs/
if [[ "$FILE" != *".specs/"* ]]; then
  exit 0
fi

# Only check markdown files
if [[ "$FILE" != *.md ]]; then
  exit 0
fi

BASENAME=$(basename "$FILE")
WARNINGS=""

case "$BASENAME" in
  spec.md)
    for section in "§1" "§2" "§8" "§9"; do
      if ! grep -q "$section" "$FILE" 2>/dev/null; then
        WARNINGS="${WARNINGS}  ⚠ Missing required section $section\n"
      fi
    done
    ;;
  pitch.md)
    for section in "Problem" "Appetite" "Shape" "No-Gos"; do
      if ! grep -qi "## *$section" "$FILE" 2>/dev/null; then
        WARNINGS="${WARNINGS}  ⚠ Missing required section: $section\n"
      fi
    done
    ;;
  plan.md)
    for section in "§1" "§2" "§3" "§6"; do
      if ! grep -q "$section" "$FILE" 2>/dev/null; then
        WARNINGS="${WARNINGS}  ⚠ Missing required section $section\n"
      fi
    done
    ;;
  tasks.md)
    if ! grep -qi "## Phase" "$FILE" 2>/dev/null; then
      WARNINGS="${WARNINGS}  ⚠ Missing at least one Phase section\n"
    fi
    ;;
esac

if [ -n "$WARNINGS" ]; then
  echo "Spec structure warnings for $BASENAME:"
  printf "$WARNINGS"
fi

exit 0
