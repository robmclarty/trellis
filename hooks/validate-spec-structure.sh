#!/usr/bin/env bash
# PostToolUse hook for Write/Edit — validates spec document structure.
# Checks that documents under the specs directory have their minimum required sections.
# Receives tool input as JSON on stdin.
# Outputs warnings only (exit 0).

# Read specsDir from trellis.json, default to .specs
if [ -f "trellis.json" ]; then
  SPECS_DIR=$(sed -n 's/.*"specsDir"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' trellis.json)
fi
SPECS_DIR="${SPECS_DIR:-.specs}"

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Exit if parsing failed or no file path
if [ -z "$FILE" ]; then
  exit 0
fi

# Only check files under the specs directory
if [[ "$FILE" != *"$SPECS_DIR/"* ]]; then
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
