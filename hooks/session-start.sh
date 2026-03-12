#!/usr/bin/env bash
# SessionStart hook — shows pipeline status for features in .specs/
# Exits silently if no .specs/ directory exists.

SPECS_DIR=".specs"

if [ ! -d "$SPECS_DIR" ]; then
  exit 0
fi

echo "📋 Trellis pipeline status:"

# Check guidelines
if [ -f "$SPECS_DIR/guidelines.md" ]; then
  echo "  ✓ guidelines.md"
else
  echo "  ✗ guidelines.md (run /trellis:guidelines first)"
fi

# Check each feature directory
for dir in "$SPECS_DIR"/*/; do
  [ -d "$dir" ] || continue
  FEATURE=$(basename "$dir")
  [ "$FEATURE" = "sketches" ] && continue

  STATUS=""
  COMPLETE=true
  for artifact in pitch.md spec.md plan.md tasks.md; do
    if [ -f "$dir/$artifact" ]; then
      STATUS="${STATUS} ✓${artifact%.md}"
    else
      STATUS="${STATUS} ✗${artifact%.md}"
      COMPLETE=false
    fi
  done

  # Check for optional compliance
  if [ -f "$dir/compliance.md" ]; then
    STATUS="${STATUS} ✓compliance"
  fi

  if [ "$COMPLETE" = true ]; then
    echo "  $FEATURE: ${STATUS} (ready for /trellis:implement)"
  else
    echo "  $FEATURE: ${STATUS}"
  fi
done

# Check sketches
SKETCH_COUNT=$(find "$SPECS_DIR/sketches" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$SKETCH_COUNT" -gt 0 ]; then
  echo "  sketches: $SKETCH_COUNT sketch(es)"
fi

exit 0
