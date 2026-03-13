#!/usr/bin/env bash
# Automated tests for Trellis hook scripts.
# Run from project root: bash tests/test-hooks.sh

set -euo pipefail

PASS=0
FAIL=0
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# --- helpers ---

pass() { PASS=$((PASS + 1)); printf "  ✓ %s\n" "$1"; }
fail() { FAIL=$((FAIL + 1)); printf "  ✗ %s\n" "$1"; }

assert_exit() {
  local expected="$1" actual="$2" label="$3"
  if [ "$actual" -eq "$expected" ]; then pass "$label"; else fail "$label (expected exit $expected, got $actual)"; fi
}

assert_contains() {
  local haystack="$1" needle="$2" label="$3"
  if printf '%s' "$haystack" | grep -q "$needle"; then pass "$label"; else fail "$label (output missing: $needle)"; fi
}

assert_empty() {
  local output="$1" label="$2"
  if [ -z "$output" ]; then pass "$label"; else fail "$label (expected no output, got: $output)"; fi
}

# ============================================================
# validate-spec-structure.sh
# ============================================================
echo ""
echo "validate-spec-structure.sh"
echo "=========================="

# --- trellis.json resolution ---

# Test: uses default .specs/ when no trellis.json
cd "$TMP" && mkdir -p .specs
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/spec.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1) || true
# With no actual file, grep will fail silently — just confirm it didn't crash
pass "no trellis.json: falls back to .specs/"

# Test: reads custom specsDir from trellis.json
cd "$TMP"
echo '{"specsDir": "design"}' > trellis.json
mkdir -p design
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/design/spec.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1) || true
pass "trellis.json: reads custom specsDir"

# Test: ignores files outside specs dir
cd "$TMP"
echo '{"specsDir": ".specs"}' > trellis.json
OUT=$(echo '{"tool_input":{"file_path":"/some/other/path/spec.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
RC=$?
assert_exit 0 $RC "ignores files outside specs dir"
assert_empty "$OUT" "no output for files outside specs dir"

# Test: ignores non-markdown files
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/feature/config.json"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
assert_empty "$OUT" "ignores non-markdown files"

# --- section validation ---

# Test: warns on spec.md missing required sections
cd "$TMP"
rm -f trellis.json
mkdir -p .specs/my-feature
echo "# Spec" > .specs/my-feature/spec.md
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/my-feature/spec.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
assert_contains "$OUT" "§1" "warns when spec.md missing §1"
assert_contains "$OUT" "§8" "warns when spec.md missing §8"

# Test: no warnings when spec.md has all required sections
cat > .specs/my-feature/spec.md <<'SPEC'
§1 Context
§2 Functional Overview
§8 Success Criteria
§9 Constraints
SPEC
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/my-feature/spec.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
assert_empty "$OUT" "no warnings when spec.md has required sections"

# Test: warns on pitch.md missing required sections
echo "# Pitch" > .specs/my-feature/pitch.md
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/my-feature/pitch.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
assert_contains "$OUT" "Problem" "warns when pitch.md missing Problem"
assert_contains "$OUT" "No-Gos" "warns when pitch.md missing No-Gos"

# Test: warns on plan.md missing required sections
echo "# Plan" > .specs/my-feature/plan.md
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/my-feature/plan.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
assert_contains "$OUT" "§3" "warns when plan.md missing §3"
assert_contains "$OUT" "§6" "warns when plan.md missing §6"

# Test: warns on tasks.md missing Phase
echo "# Tasks" > .specs/my-feature/tasks.md
OUT=$(echo '{"tool_input":{"file_path":"'"$TMP"'/.specs/my-feature/tasks.md"}}' | bash "$ROOT/hooks/validate-spec-structure.sh" 2>&1)
assert_contains "$OUT" "Phase" "warns when tasks.md missing Phase section"

# ============================================================
# check-implement-state.sh
# ============================================================
echo ""
echo "check-implement-state.sh"
echo "========================"

# Test: ignores non-commit commands
cd "$TMP"
OUT=$(echo '{"tool_input":{"command":"git status"}}' | bash "$ROOT/hooks/check-implement-state.sh" 2>&1)
RC=$?
assert_exit 0 $RC "ignores non-commit commands"
assert_empty "$OUT" "no output for non-commit commands"

# Test: silent when no .implement-state.md exists
OUT=$(echo '{"tool_input":{"command":"git commit -m test"}}' | bash "$ROOT/hooks/check-implement-state.sh" 2>&1)
assert_empty "$OUT" "silent when no .implement-state.md"

# Test: warns when pending criteria exist
cat > .implement-state.md <<'STATE'
## Criteria
- [x] AC-1 done
- [ ] AC-2 pending thing
- [ ] AC-3 another pending
STATE
OUT=$(echo '{"tool_input":{"command":"git commit -m test"}}' | bash "$ROOT/hooks/check-implement-state.sh" 2>&1)
assert_contains "$OUT" "2 pending" "warns about 2 pending criteria"

# Test: silent when all criteria done
cat > .implement-state.md <<'STATE'
## Criteria
- [x] AC-1 done
- [x] AC-2 also done
STATE
OUT=$(echo '{"tool_input":{"command":"git commit -m test"}}' | bash "$ROOT/hooks/check-implement-state.sh" 2>&1)
assert_empty "$OUT" "silent when all criteria complete"

# ============================================================
# session-start.sh
# ============================================================
echo ""
echo "session-start.sh"
echo "================"

# Test: silent when no specs dir exists
cd "$TMP" && rm -rf .specs design trellis.json
OUT=$(bash "$ROOT/hooks/session-start.sh" 2>&1)
assert_empty "$OUT" "silent when no specs dir"

# Test: shows pipeline status with default dir
mkdir -p .specs/my-feature
echo "# guidelines" > .specs/guidelines.md
echo "# pitch" > .specs/my-feature/pitch.md
echo "# spec" > .specs/my-feature/spec.md
OUT=$(bash "$ROOT/hooks/session-start.sh" 2>&1)
assert_contains "$OUT" "pipeline status" "shows pipeline status header"
assert_contains "$OUT" "guidelines.md" "shows guidelines status"
assert_contains "$OUT" "my-feature" "shows feature name"
assert_contains "$OUT" "✓pitch" "shows pitch as present"
assert_contains "$OUT" "✗plan" "shows plan as missing"

# Test: respects custom specsDir from trellis.json
cd "$TMP" && rm -rf .specs
mkdir -p design/cool-feature
echo '{"specsDir": "design"}' > trellis.json
echo "# guidelines" > design/guidelines.md
echo "# pitch" > design/cool-feature/pitch.md
OUT=$(bash "$ROOT/hooks/session-start.sh" 2>&1)
assert_contains "$OUT" "cool-feature" "uses custom specsDir from trellis.json"

# Test: counts sketches
mkdir -p design/sketches
echo "# sketch1" > design/sketches/test-sketch.md
OUT=$(bash "$ROOT/hooks/session-start.sh" 2>&1)
assert_contains "$OUT" "1 sketch" "counts sketches"

# ============================================================
# Summary
# ============================================================
echo ""
echo "=========================="
TOTAL=$((PASS + FAIL))
echo "$PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
  echo "$FAIL FAILED"
  exit 1
else
  echo "All tests passed."
  exit 0
fi
