#!/usr/bin/env bash
# ralphd-loop.sh — Docker-sandboxed context-fresh iteration loop for the
# Trellis implement skill.
#
# Usage: ralphd-loop.sh <feature-name> [max-iterations]
#        ralphd-loop.sh --login
#
# Like ralph-loop.sh, but each Claude iteration runs inside a Docker container
# with --dangerously-skip-permissions. Docker is the security boundary — the
# container is disposable and isolated from the host beyond the bind-mounted
# project directory.
#
# Auth: Supports both API key (ANTHROPIC_API_KEY env var) and OAuth/subscription
# (stored in a named Docker volume). Run `ralphd-loop.sh --login` once to
# authenticate with a subscription — the OAuth session persists across iterations.
#
# Requires: docker
#
# Security: The container can only touch files in the bind-mounted project
# directory. No scoped permissions are generated — the Docker sandbox replaces
# the allowlist model used by ralph-loop.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="trellis-ralphd"
DOCKERFILE="${SCRIPT_DIR}/Dockerfile.ralphd"
AUTH_VOLUME="trellis-ralphd-auth"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# --- Preflight: Docker ---

if ! command -v docker &>/dev/null; then
  echo -e "${RED}docker is not installed or not in PATH. Aborting.${RESET}"
  exit 1
fi

if ! docker info &>/dev/null 2>&1; then
  echo -e "${RED}Docker daemon is not running. Start Docker and retry.${RESET}"
  exit 1
fi

# Build the image if it doesn't exist
build_image() {
  if ! docker image inspect "$IMAGE_NAME" &>/dev/null 2>&1; then
    echo -e "${CYAN}Building Docker image ${IMAGE_NAME}...${RESET}"
    docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" "${SCRIPT_DIR}/.." || {
      echo -e "${RED}Docker build failed. Aborting.${RESET}"
      exit 1
    }
    echo -e "${GREEN}Image ${IMAGE_NAME} built successfully.${RESET}"
  else
    echo -e "${CYAN}Docker image ${IMAGE_NAME} already exists.${RESET}"
  fi
}

# Ensure the named auth volume exists
ensure_auth_volume() {
  if ! docker volume inspect "$AUTH_VOLUME" &>/dev/null 2>&1; then
    docker volume create "$AUTH_VOLUME" >/dev/null
    echo -e "${CYAN}Created auth volume ${AUTH_VOLUME}.${RESET}"
  fi
}

# Build docker run arguments as a string.
# Bash 3.2 compatible — no readarray, no local -a with +=.
build_docker_run_args() {
  local args="-v $(pwd):/workspace -v ${AUTH_VOLUME}:/home/claude/.claude"

  # Mount host's Claude config into the container so it can find installed
  # plugins and settings. Plugin paths in installed_plugins.json are absolute
  # (e.g., /Users/alice/.claude/plugins/cache/...), so we mount the host's
  # ~/.claude at BOTH the container home AND the original host-absolute path.
  # This ensures path references resolve correctly regardless of the host user.
  local host_claude_dir="${HOME}/.claude"
  if [[ -d "${host_claude_dir}" ]]; then
    # Overlay plugin files onto the auth volume
    if [[ -d "${host_claude_dir}/plugins" ]]; then
      args="$args -v ${host_claude_dir}/plugins:/home/claude/.claude/plugins:ro"
      # Also mount at the host-absolute path so installed_plugins.json paths resolve
      args="$args -v ${host_claude_dir}/plugins:${host_claude_dir}/plugins:ro"
    fi
    if [[ -f "${host_claude_dir}/settings.json" ]]; then
      args="$args -v ${host_claude_dir}/settings.json:/home/claude/.claude/settings.json:ro"
    fi
  fi
  if [[ -f "${HOME}/.claude.json" ]]; then
    args="$args -v ${HOME}/.claude.json:/home/claude/.claude.json"
  fi

  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    args="$args -e ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
  fi

  if [[ -n "${CLAUDE_CODE_USE_BEDROCK:-}" ]]; then
    args="$args -e CLAUDE_CODE_USE_BEDROCK=${CLAUDE_CODE_USE_BEDROCK}"
  fi
  if [[ -n "${CLAUDE_CODE_USE_VERTEX:-}" ]]; then
    args="$args -e CLAUDE_CODE_USE_VERTEX=${CLAUDE_CODE_USE_VERTEX}"
  fi

  echo "$args"
}

# --- Check-auth subcommand (non-interactive probe) ---

if [[ "${1:-}" == "--check-auth" ]]; then
  build_image
  ensure_auth_volume

  # API key takes precedence
  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo -e "${GREEN}ANTHROPIC_API_KEY is set.${RESET}"
    exit 0
  fi

  # Check if the auth volume has a valid session by running claude --version
  # with the volume mounted. If the volume is empty or has no credentials,
  # a subsequent `claude -p` would fail, so we look for credential files.
  if docker run --rm \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    "$IMAGE_NAME" \
    --version &>/dev/null && \
    docker run --rm \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    --entrypoint sh \
    "$IMAGE_NAME" \
    -c 'test -d /home/claude/.claude && find /home/claude/.claude -maxdepth 1 -type f | grep -q .' 2>/dev/null; then
    echo -e "${GREEN}OAuth session found in ${AUTH_VOLUME} volume.${RESET}"
    exit 0
  fi

  echo -e "${RED}No valid authentication found.${RESET}"
  exit 1
fi

# --- Login subcommand ---

if [[ "${1:-}" == "--login" ]]; then
  build_image
  ensure_auth_volume

  echo -e "${CYAN}${BOLD}Opening interactive Claude login inside Docker...${RESET}"
  echo -e "${YELLOW}Complete the OAuth flow in your browser. The session will be${RESET}"
  echo -e "${YELLOW}stored in the ${AUTH_VOLUME} volume and reused for all iterations.${RESET}"
  echo ""

  # Interactive login — needs -it for the browser prompt
  docker run --rm -it \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    "$IMAGE_NAME" \
    login

  echo ""
  echo -e "${GREEN}${BOLD}Login complete. You can now run: ralphd-loop.sh <feature-name>${RESET}"
  exit 0
fi

# --- Main loop mode ---

FEATURE="${1:?Usage: ralphd-loop.sh <feature-name> [max-iterations]  or  ralphd-loop.sh --login}"
MAX_ITERATIONS="${2:-10}"
LOG_DIR="logs/ralphd-${FEATURE}"

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

mkdir -p "$LOG_DIR"
mkdir -p "${SPECS_DIR}/.state"

build_image
ensure_auth_volume

# --- Auth check ---
# Verify that either ANTHROPIC_API_KEY is set or the auth volume has credentials

check_auth() {
  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo -e "${CYAN}Using ANTHROPIC_API_KEY for authentication.${RESET}"
    return 0
  fi

  # Check if the auth volume has credentials by running a quick test
  # The volume is mounted at /home/claude/.claude — if it has auth files,
  # `claude -p` will pick them up. We check by looking for any credential
  # files in the volume.
  docker run --rm \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    "$IMAGE_NAME" \
    --version 2>/dev/null || true

  # If `claude --version` works, the binary is fine. But we need to check
  # if auth is configured. Try a minimal prompt — if it fails with an auth
  # error, we know login is needed.
  echo -e "${CYAN}Checking authentication in Docker volume...${RESET}"
  if echo "say ok" | docker run --rm -i \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    "$IMAGE_NAME" \
    -p --dangerously-skip-permissions 2>&1 | head -5 | grep -qi "error\|unauthorized\|login\|authenticate"; then
    echo -e "${RED}No valid authentication found in Docker volume.${RESET}"
    echo -e "${YELLOW}Run this first:  ${BOLD}ralphd-loop.sh --login${RESET}"
    exit 1
  fi

  echo -e "${GREEN}OAuth session found in ${AUTH_VOLUME} volume.${RESET}"
}

check_auth

# --- Helpers ---

parse_state() {
  python3 "${SCRIPT_DIR}/parse-implement-state.py" "$STATE_FILE" 2>/dev/null || echo '{}'
}

json_field() {
  local field="$1" default="${2:-}"
  python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('$field', '$default'))
" 2>/dev/null || echo "$default"
}

run_preflight() {
  local state_json

  state_json=$(parse_state)

  local prereqs_json
  prereqs_json=$(python3 "${SCRIPT_DIR}/validate-prereqs.py" implement "$FEATURE" 2>/dev/null || echo '{"valid":false,"missing":["unknown"]}')

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

# shellcheck disable=SC2329  # invoked indirectly via trap
cleanup() {
  rm -f "$PREFLIGHT_FILE"
  echo -e "${YELLOW}Cleaned up ${PREFLIGHT_FILE}${RESET}"
}
trap cleanup EXIT

# --- Main loop ---

if [[ ! -f "$STATE_FILE" ]]; then
  echo -e "${RED}No ${STATE_FILE} found. Run /implement ${FEATURE} with ralphd interactively first.${RESET}"
  exit 1
fi

consecutive_failures=0

for ((i = 1; i <= MAX_ITERATIONS; i++)); do
  echo -e "${CYAN}${BOLD}═══ Ralphd iteration ${i}/${MAX_ITERATIONS} ═══${RESET}"

  if [[ -f "$STATE_FILE" ]]; then
    state_json=$(parse_state)
    done_count=$(echo "$state_json" | json_field doneCount "?")
    pending_count=$(echo "$state_json" | json_field pendingCount "?")
    echo -e "${YELLOW}Criteria: ${done_count} done, ${pending_count} pending${RESET}"
  fi

  run_preflight

  log_file="${LOG_DIR}/iteration-${i}.log"
  echo -e "${CYAN}Running iteration ${i} in Docker container...${RESET}"

  # Build docker run arguments (bash 3.2 compatible — no arrays)
  run_args=$(build_docker_run_args)

  # Run Claude inside Docker with --dangerously-skip-permissions.
  # The container is the security boundary:
  #   - Bind-mount the project directory (read-write)
  #   - Named volume for auth (persists across iterations)
  #   - Ephemeral container (--rm) — destroyed after each iteration
  #   - No network restrictions (Claude needs API access)
  #   - No host filesystem access beyond the mounts
  # shellcheck disable=SC2086  # intentional word splitting of run_args
  if echo "/trellis:implement ${FEATURE}" | docker run --rm -i \
    $run_args \
    "$IMAGE_NAME" \
    -p --dangerously-skip-permissions > "$log_file" 2>&1; then
    echo -e "${GREEN}Iteration ${i} completed${RESET}"
    consecutive_failures=0
  else
    echo -e "${RED}Iteration ${i} exited with error${RESET}"
    consecutive_failures=$((consecutive_failures + 1))
  fi

  if [[ ! -f "$STATE_FILE" ]]; then
    echo -e "${RED}No ${STATE_FILE} found after iteration ${i}. Aborting.${RESET}"
    exit 1
  fi

  state_json=$(parse_state)
  done_count=$(echo "$state_json" | json_field doneCount 0)
  pending_count=$(echo "$state_json" | json_field pendingCount 1)

  echo -e "${YELLOW}After iteration ${i}: ${done_count} done, ${pending_count} pending${RESET}"

  if [[ "$pending_count" == "0" ]]; then
    echo -e "${GREEN}${BOLD}All acceptance criteria met after ${i} iteration(s).${RESET}"
    git add -A && git commit -m "ralphd: iteration ${i} — all criteria complete for ${FEATURE}" 2>/dev/null || true
    git push 2>/dev/null || true
    exit 0
  fi

  if [[ "$consecutive_failures" -ge 3 ]]; then
    echo -e "${RED}${BOLD}3 consecutive failures without progress. Aborting.${RESET}"
    echo -e "${RED}Check ${LOG_DIR}/ for iteration logs.${RESET}"
    exit 1
  fi

  git add -A && git commit -m "ralphd: iteration ${i} progress for ${FEATURE}" 2>/dev/null || true
  git push 2>/dev/null || true

  sleep 2
done

echo -e "${YELLOW}${BOLD}Reached max iterations (${MAX_ITERATIONS}). ${done_count} done, ${pending_count} pending.${RESET}"
echo -e "${YELLOW}Check ${LOG_DIR}/ for iteration logs.${RESET}"
exit 1
