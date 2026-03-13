#!/usr/bin/env bash
# ralph-loop.sh — Context-fresh iteration loop for the Trellis implement skill.
#
# Usage: ralph-loop.sh <feature-name> [max-iterations]
#
# Wraps `claude -p` in a loop, restarting with a fresh context on each
# iteration. Progress is tracked via .implement-state.md and parsed by
# parse-implement-state.py between iterations.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE="${1:?Usage: ralph-loop.sh <feature-name> [max-iterations]}"
MAX_ITERATIONS="${2:-10}"
LOG_DIR="logs/ralph-${FEATURE}"
STATE_FILE=".implement-state.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

mkdir -p "$LOG_DIR"

consecutive_failures=0

for ((i = 1; i <= MAX_ITERATIONS; i++)); do
  echo -e "${CYAN}${BOLD}═══ Ralph iteration ${i}/${MAX_ITERATIONS} ═══${RESET}"

  # Show current criteria status before starting
  if [[ -f "$STATE_FILE" ]]; then
    state_json=$(python3 "${SCRIPT_DIR}/parse-implement-state.py" "$STATE_FILE" 2>/dev/null || echo '{}')
    done_count=$(echo "$state_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('doneCount',0))" 2>/dev/null || echo "?")
    pending_count=$(echo "$state_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pendingCount',0))" 2>/dev/null || echo "?")
    echo -e "${YELLOW}Criteria: ${done_count} done, ${pending_count} pending${RESET}"
  fi

  log_file="${LOG_DIR}/iteration-${i}.log"
  echo -e "${CYAN}Running iteration ${i}...${RESET}"

  # Run claude in headless mode
  if echo "/trellis:implement ${FEATURE}" | claude -p --dangerously-skip-permissions > "$log_file" 2>&1; then
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

  state_json=$(python3 "${SCRIPT_DIR}/parse-implement-state.py" "$STATE_FILE" 2>/dev/null || echo '{}')
  done_count=$(echo "$state_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('doneCount',0))" 2>/dev/null || echo 0)
  pending_count=$(echo "$state_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pendingCount',0))" 2>/dev/null || echo 1)

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
