#!/usr/bin/env bash
# ralph-loop.sh — Context-fresh iteration loop for the Trellis implement skill.
#
# Usage: ralph-loop.sh <feature-name> [max-iterations]
#
# Wraps `claude -p` in a loop, restarting with a fresh context on each
# iteration. Progress is tracked via {specsDir}/.state/implement-state.md
# and parsed by parse-implement-state.py between iterations.
#
# Security: Runs without --dangerously-skip-permissions. Instead, generates
# a scoped .claude/settings.local.json that allowlists only the tools and
# commands needed for implementation. Pre-flight scripts run in the loop
# (outside Claude's context) so Claude needs no python3 access.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE="${1:?Usage: ralph-loop.sh <feature-name> [max-iterations]}"
MAX_ITERATIONS="${2:-10}"
LOG_DIR="logs/ralph-${FEATURE}"
SETTINGS_FILE=".claude/settings.local.json"

# Resolve specs dir from trellis.json (default: .specs)
SPECS_DIR=$(python3 -c "
import json
try:
    with open('trellis.json') as f:
        print(json.load(f).get('specsDir', '.specs'))
except Exception:
    print('.specs')
" 2>/dev/null || echo ".specs")

STATE_FILE="${SPECS_DIR}/.state/implement-state.md"
PREFLIGHT_FILE="${SPECS_DIR}/.state/implement-preflight.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

mkdir -p "$LOG_DIR"
mkdir -p "${SPECS_DIR}/.state"

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
  local state_json preflight_json

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

  # Assemble preflight JSON
  python3 -c "
import json, sys

state = json.loads('''${state_json}''')
prereqs = json.loads('''${prereqs_json}''')
criteria = json.loads('''${criteria_json}''')

preflight = {
    'specsDir': '${SPECS_DIR}',
    'prereqs': prereqs,
    'state': state,
    'criteria': criteria,
}

with open('${PREFLIGHT_FILE}', 'w') as f:
    json.dump(preflight, f, indent=2)
    f.write('\n')
" 2>/dev/null

  echo -e "${CYAN}Pre-flight written to ${PREFLIGHT_FILE}${RESET}"
}

generate_permissions() {
  # Generate .claude/settings.local.json with scoped permissions from the
  # oracle pipeline commands stored in the implement state file.
  local state_json
  state_json=$(parse_state)

  python3 -c "
import json, sys

state = json.loads('''${state_json}''')
pipeline = state.get('pipeline', [])

# Start with file tools and agent (always needed)
allowed = [
    'Read',
    'Write',
    'Edit',
    'Glob',
    'Grep',
    'Agent',
    'Bash(mkdir *)',
    'Bash(cp *)',
    'Bash(mv *)',
    'Bash(ls *)',
    'Bash(cat *)',
    'Bash(git branch *)',
    'Bash(git checkout *)',
    'Bash(git diff *)',
    'Bash(git status)',
    'Bash(git log *)',
]

# Add oracle pipeline commands
for stage in pipeline:
    cmd = stage.get('command')
    if cmd:
        allowed.append('Bash(' + cmd + ')')

# Add package manager commands (extract from config if available)
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

with open('${SETTINGS_FILE}', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print('Allowed tools:', len(allowed))
for tool in allowed:
    print('  ' + tool)
" 2>/dev/null

  echo -e "${CYAN}Permissions written to ${SETTINGS_FILE}${RESET}"
}

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
  if echo "/trellis:implement ${FEATURE}" | claude -p > "$log_file" 2>&1; then
    echo -e "${GREEN}Iteration ${i} completed${RESET}"
    consecutive_failures=0
  else
    echo -e "${RED}Iteration ${i} exited with error${RESET}"
    consecutive_failures=$((consecutive_failures + 1))
  fi

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
