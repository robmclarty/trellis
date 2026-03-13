#!/usr/bin/env bash
# Snapshot tests for Trellis spec artifacts.
#
# Compares files in examples/.specs/ against snapshots in tests/snapshots/.
# On first run (or with --update), copies examples/ as the baseline.
# On subsequent runs, diffs against the baseline and fails on any change.
#
# Usage:
#   bash tests/test-snapshots.sh           # compare against baseline
#   bash tests/test-snapshots.sh --update  # update baseline from examples/

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLES="$ROOT/examples/.specs"
SNAPSHOTS="$ROOT/tests/snapshots"
PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf "  ✓ %s\n" "$1"; }
fail() { FAIL=$((FAIL + 1)); printf "  ✗ %s\n" "$1"; }

# --- update mode ---
if [ "${1:-}" = "--update" ]; then
  rm -rf "$SNAPSHOTS"
  mkdir -p "$SNAPSHOTS"
  cp -R "$EXAMPLES"/ "$SNAPSHOTS"/
  echo "Snapshots updated from examples/.specs/"
  FILE_COUNT=$(find "$SNAPSHOTS" -name "*.md" | wc -l | tr -d ' ')
  echo "$FILE_COUNT files captured."
  exit 0
fi

# --- compare mode ---
if [ ! -d "$SNAPSHOTS" ]; then
  echo "No snapshots found. Run with --update first:"
  echo "  bash tests/test-snapshots.sh --update"
  exit 1
fi

echo ""
echo "Snapshot comparison"
echo "==================="

# Check every snapshot file still matches examples/
while IFS= read -r snap_file; do
  rel="${snap_file#$SNAPSHOTS/}"
  example_file="$EXAMPLES/$rel"

  if [ ! -f "$example_file" ]; then
    fail "$rel — file removed from examples/"
    continue
  fi

  if diff -q "$snap_file" "$example_file" >/dev/null 2>&1; then
    pass "$rel"
  else
    fail "$rel — changed since snapshot"
    diff -u "$snap_file" "$example_file" | head -20
    echo "  ..."
  fi
done < <(find "$SNAPSHOTS" -name "*.md" | sort)

# Check for new files in examples/ not in snapshots
while IFS= read -r example_file; do
  rel="${example_file#$EXAMPLES/}"
  snap_file="$SNAPSHOTS/$rel"

  if [ ! -f "$snap_file" ]; then
    fail "$rel — new file not in snapshots (run --update)"
  fi
done < <(find "$EXAMPLES" -name "*.md" | sort)

# --- structure validation ---
echo ""
echo "Structure validation"
echo "===================="

# Every feature dir should have the core artifacts
for dir in "$EXAMPLES"/*/; do
  [ -d "$dir" ] || continue
  feature=$(basename "$dir")
  [ "$feature" = "sketches" ] && continue

  for artifact in pitch.md spec.md plan.md tasks.md; do
    if [ -f "$dir/$artifact" ]; then
      pass "$feature/$artifact exists"
    else
      fail "$feature/$artifact missing"
    fi
  done
done

# Guidelines should exist
if [ -f "$EXAMPLES/guidelines.md" ]; then
  pass "guidelines.md exists"
else
  fail "guidelines.md missing"
fi

# --- content validation (same checks as the hook) ---
echo ""
echo "Content validation"
echo "=================="

for dir in "$EXAMPLES"/*/; do
  [ -d "$dir" ] || continue
  feature=$(basename "$dir")
  [ "$feature" = "sketches" ] && continue

  # spec.md sections
  if [ -f "$dir/spec.md" ]; then
    for section in "§1" "§2" "§8" "§9"; do
      if grep -q "$section" "$dir/spec.md"; then
        pass "$feature/spec.md has $section"
      else
        fail "$feature/spec.md missing $section"
      fi
    done
  fi

  # pitch.md sections
  if [ -f "$dir/pitch.md" ]; then
    for section in "Problem" "Appetite" "Shape" "No-Gos"; do
      if grep -qi "## *$section" "$dir/pitch.md"; then
        pass "$feature/pitch.md has $section"
      else
        fail "$feature/pitch.md missing $section"
      fi
    done
  fi

  # plan.md sections
  if [ -f "$dir/plan.md" ]; then
    for section in "§1" "§2" "§3" "§6"; do
      if grep -q "$section" "$dir/plan.md"; then
        pass "$feature/plan.md has $section"
      else
        fail "$feature/plan.md missing $section"
      fi
    done
  fi

  # tasks.md phases
  if [ -f "$dir/tasks.md" ]; then
    if grep -qi "## Phase" "$dir/tasks.md"; then
      pass "$feature/tasks.md has Phase sections"
    else
      fail "$feature/tasks.md missing Phase sections"
    fi
  fi
done

# --- summary ---
echo ""
echo "===================="
TOTAL=$((PASS + FAIL))
echo "$PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
  echo "$FAIL FAILED"
  exit 1
else
  echo "All tests passed."
  exit 0
fi
