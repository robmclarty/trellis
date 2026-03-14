#!/usr/bin/env bash
# ralph-loop.sh — Context-fresh iteration loop for the Trellis implement skill.
#
# Usage: ralph-loop.sh <feature-name> [max-iterations] [--stream|--tail]
#
# Wraps `claude -p` in a loop, restarting with a fresh context on each
# iteration. Progress is tracked via {specsDir}/{feature}/implement-state.md
# and parsed by parse-implement-state.py between iterations.
#
# Output modes:
#   (default)  Silent — output goes to log file only, status shown between iterations
#   --stream   Full Claude output visible in real-time via tee (also logged)
#   --tail     Silent during iteration, show last 50 lines of log after completion
#
# Security: Runs without --dangerously-skip-permissions. Instead, generates
# a scoped .claude/settings.local.json that allowlists only the tools and
# commands needed for implementation. Pre-flight scripts run in the loop
# (outside Claude's context) so Claude needs no python3 access.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE="${1:?Usage: ralph-loop.sh <feature-name> [max-iterations] [--stream|--tail]}"
MAX_ITERATIONS="${2:-10}"
LOG_DIR="logs/ralph-${FEATURE}"
SETTINGS_FILE=".claude/settings.local.json"

# Parse optional output mode flags
OUTPUT_MODE="silent"
shift 2 2>/dev/null || shift $# 2>/dev/null || true
for arg in "$@"; do
  case "$arg" in
    --stream) OUTPUT_MODE="stream" ;;
    --tail)   OUTPUT_MODE="tail" ;;
  esac
done

# Resolve specs dir from trellis.json (default: .specs)
SPECS_DIR=$(python3 -c "
import json
try:
    with open('trellis.json') as f:
        print(json.load(f).get('specsDir', '.specs'))
except Exception:
    print('.specs')
" 2>/dev/null || echo ".specs")

STATE_FILE="${SPECS_DIR}/${FEATURE}/implement-state.md"
PREFLIGHT_FILE="${SPECS_DIR}/${FEATURE}/implement-preflight.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

mkdir -p "$LOG_DIR"

# Migrate legacy state file from .state/ to feature directory
LEGACY_STATE="${SPECS_DIR}/.state/implement-state.md"
if [[ -f "$LEGACY_STATE" ]] && [[ ! -f "$STATE_FILE" ]]; then
  # Check if the legacy file's Feature field matches this feature
  if grep -q "^- Feature: ${FEATURE}$" "$LEGACY_STATE" 2>/dev/null; then
    echo -e "${YELLOW}Migrating legacy state file to ${STATE_FILE}${RESET}"
    mv "$LEGACY_STATE" "$STATE_FILE"
    # Also migrate preflight if present
    LEGACY_PREFLIGHT="${SPECS_DIR}/.state/implement-preflight.json"
    if [[ -f "$LEGACY_PREFLIGHT" ]]; then
      mv "$LEGACY_PREFLIGHT" "$PREFLIGHT_FILE"
    fi
  fi
fi

# --- Helpers ---

parse_state() {
  # Parse state file into JSON, return via stdout
  python3 "${SCRIPT_DIR}/parse-implement-state.py" "$STATE_FILE" 2>/dev/null || echo '{}'
}

json_field() {
  # Extract a field from JSON on stdin. Usage: echo "$json" | json_field fieldName default
  local field="$1" default="${2:-}"
  python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('$field', '$default'))
" 2>/dev/null || echo "$default"
}

run_preflight() {
  # Run pre-flight scripts and write results to the preflight JSON file.
  # This runs OUTSIDE Claude's context — Claude reads the JSON file instead
  # of invoking python3 itself.
  local state_json

  # Parse current state
  state_json=$(parse_state)

  # Validate prerequisites
  local prereqs_json
  prereqs_json=$(python3 "${SCRIPT_DIR}/validate-prereqs.py" implement "$FEATURE" 2>/dev/null || echo '{"valid":false,"missing":["unknown"]}')

  # Extract criteria
  local criteria_json='{}'
  local tasks_path="${SPECS_DIR}/${FEATURE}/tasks.md"
  local spec_path="${SPECS_DIR}/${FEATURE}/spec.md"
  if [[ -f "$tasks_path" ]]; then
    criteria_json=$(python3 "${SCRIPT_DIR}/extract-criteria.py" "$tasks_path" "$spec_path" 2>/dev/null || echo '{}')
  fi

  # Assemble preflight JSON via stdin to avoid bash/python string escaping issues.
  # Each JSON blob is passed as an element of a JSON array through a pipe.
  python3 -c "
import json, sys

parts = json.load(sys.stdin)

preflight = {
    'specsDir': parts[0],
    'prereqs': parts[1],
    'state': parts[2],
    'criteria': parts[3],
}

with open(parts[4], 'w') as f:
    json.dump(preflight, f, indent=2)
    f.write('\n')
" <<< "$(python3 -c "
import json, sys
print(json.dumps([
    sys.argv[1],
    json.loads(sys.argv[2]),
    json.loads(sys.argv[3]),
    json.loads(sys.argv[4]),
    sys.argv[5],
]))
" "$SPECS_DIR" "$prereqs_json" "$state_json" "$criteria_json" "$PREFLIGHT_FILE")"

  echo -e "${CYAN}Pre-flight written to ${PREFLIGHT_FILE}${RESET}"
}

generate_permissions() {
  # Generate .claude/settings.local.json with scoped permissions from the
  # oracle pipeline commands stored in the implement state file.
  local state_json
  state_json=$(parse_state)

  python3 -c "
import json, sys

state = json.load(sys.stdin)
pipeline = state.get('pipeline', [])

allowed = [
    'Read', 'Write', 'Edit', 'Glob', 'Grep', 'Agent',
    'Bash(mkdir *)', 'Bash(cp *)', 'Bash(mv *)', 'Bash(ls *)', 'Bash(cat *)',
    'Bash(git branch *)', 'Bash(git checkout *)', 'Bash(git diff *)',
    'Bash(git status)', 'Bash(git log *)',
]

for stage in pipeline:
    cmd = stage.get('command')
    if cmd:
        allowed.append('Bash(' + cmd + ')')

config = state.get('config', {})
pkg_mgr = config.get('package_manager', '')
if pkg_mgr:
    allowed.append('Bash(' + pkg_mgr + ' *)')

settings = {
    'permissions': {
        'allow': allowed,
        'deny': []
    }
}

with open(sys.argv[1], 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print('Allowed tools:', len(allowed))
for tool in allowed:
    print('  ' + tool)
" "$SETTINGS_FILE" <<< "$state_json"

  echo -e "${CYAN}Permissions written to ${SETTINGS_FILE}${RESET}"
}

# shellcheck disable=SC2329  # invoked indirectly via trap
cleanup() {
  # Remove generated files on exit
  rm -f "$PREFLIGHT_FILE"
  echo -e "${YELLOW}Cleaned up ${PREFLIGHT_FILE}${RESET}"
  # Note: we leave .claude/settings.local.json in place so the user can
  # inspect/reuse it. They can delete it manually if desired.
}
trap cleanup EXIT

# --- Main loop ---

# Generate scoped permissions before starting iterations
if [[ -f "$STATE_FILE" ]]; then
  generate_permissions
else
  echo -e "${RED}No ${STATE_FILE} found. Run /implement ${FEATURE} with ralph interactively first.${RESET}"
  exit 1
fi

consecutive_failures=0

for ((i = 1; i <= MAX_ITERATIONS; i++)); do
  echo -e "${CYAN}${BOLD}═══ Ralph iteration ${i}/${MAX_ITERATIONS} ═══${RESET}"

  # Show current criteria status before starting
  if [[ -f "$STATE_FILE" ]]; then
    state_json=$(parse_state)
    done_count=$(echo "$state_json" | json_field doneCount "?")
    pending_count=$(echo "$state_json" | json_field pendingCount "?")
    echo -e "${YELLOW}Criteria: ${done_count} done, ${pending_count} pending${RESET}"
  fi

  # Run pre-flight for this iteration (outside Claude's context)
  run_preflight

  log_file="${LOG_DIR}/iteration-${i}.log"
  echo -e "${CYAN}Running iteration ${i}...${RESET}"

  # Run claude in headless mode with scoped permissions (no --dangerously-skip-permissions)
  case "$OUTPUT_MODE" in
    stream)
      if echo "/trellis:implement ${FEATURE}" | claude -p 2>&1 | tee "$log_file"; then
        echo -e "${GREEN}Iteration ${i} completed${RESET}"
        consecutive_failures=0
      else
        echo -e "${RED}Iteration ${i} exited with error${RESET}"
        consecutive_failures=$((consecutive_failures + 1))
      fi
      ;;
    *)
      if echo "/trellis:implement ${FEATURE}" | claude -p > "$log_file" 2>&1; then
        echo -e "${GREEN}Iteration ${i} completed${RESET}"
        consecutive_failures=0
      else
        echo -e "${RED}Iteration ${i} exited with error${RESET}"
        consecutive_failures=$((consecutive_failures + 1))
      fi
      if [[ "$OUTPUT_MODE" == "tail" ]]; then
        echo -e "${CYAN}--- Last 50 lines of iteration ${i} ---${RESET}"
        tail -50 "$log_file"
        echo -e "${CYAN}--- End iteration ${i} ---${RESET}"
      fi
      ;;
  esac

  # Check state after iteration
  if [[ ! -f "$STATE_FILE" ]]; then
    echo -e "${RED}No ${STATE_FILE} found after iteration ${i}. Aborting.${RESET}"
    exit 1
  fi

  state_json=$(parse_state)
  done_count=$(echo "$state_json" | json_field doneCount 0)
  pending_count=$(echo "$state_json" | json_field pendingCount 1)

  echo -e "${YELLOW}After iteration ${i}: ${done_count} done, ${pending_count} pending${RESET}"

  # Check completion
  if [[ "$pending_count" == "0" ]]; then
    echo -e "${GREEN}${BOLD}All acceptance criteria met after ${i} iteration(s).${RESET}"
    # Push final changes
    git add -A && git commit -m "ralph: iteration ${i} — all criteria complete for ${FEATURE}" 2>/dev/null || true
    git push 2>/dev/null || true
    exit 0
  fi

  # Check consecutive failures
  if [[ "$consecutive_failures" -ge 3 ]]; then
    echo -e "${RED}${BOLD}3 consecutive failures without progress. Aborting.${RESET}"
    echo -e "${RED}Check ${LOG_DIR}/ for iteration logs.${RESET}"
    exit 1
  fi

  # Push progress after each successful iteration
  git add -A && git commit -m "ralph: iteration ${i} progress for ${FEATURE}" 2>/dev/null || true
  git push 2>/dev/null || true

  # Brief pause for git sync
  sleep 2
done

echo -e "${YELLOW}${BOLD}Reached max iterations (${MAX_ITERATIONS}). ${done_count} done, ${pending_count} pending.${RESET}"
echo -e "${YELLOW}Check ${LOG_DIR}/ for iteration logs.${RESET}"
exit 1
