#!/usr/bin/env bash
# ralph-loop.sh — Script-driven Docker implementation loop for Trellis.
#
# Usage: ralph-loop.sh <feature-name> [max-iterations] [--silent|--tail|--no-judge]
#        ralph-loop.sh --login
#        ralph-loop.sh --check-auth
#
# Runs each task in a fresh Claude Code context inside a Docker container.
# The loop script does ALL orchestration — it assembles prompts from templates
# and sends them to `claude -p` directly. The build skill is NOT invoked
# inside Docker. The LLM does only creative work: writing tests, writing code,
# fixing errors, judging alignment.
#
# Per-task loop:
#   1. Read tasks.json for next pending task (deterministic)
#   2. Run should-write-tests.py (deterministic heuristic)
#   3. If tests needed: assemble-prompt.py test-writer → claude -p in Docker
#   4. assemble-prompt.py builder → claude -p in Docker
#   5. Run check command on HOST (uses host toolchain)
#   6. Pass → update-tasks.py done / Fail → retry once → still fail → blocked
#   7. Git commit progress
#   8. Repeat until all done or all remaining blocked
#
# After all tasks: optionally run judge for spec intent alignment review.
#
# Output modes:
#   (default)  Stream — full Claude output visible in real-time via tee (also logged)
#   --silent   Output goes to log file only, status shown between tasks
#   --tail     Silent during task, show last 50 lines of log after completion
#
# Auth: Supports both API key (ANTHROPIC_API_KEY env var) and OAuth/subscription
# (stored in a named Docker volume). Run `ralph-loop.sh --login` once to
# authenticate — the OAuth session persists across tasks.
#
# Security: Each LLM invocation runs inside a Docker container with
# --dangerously-skip-permissions. Docker is the security boundary — the
# container can only access the bind-mounted project directory and the auth
# volume. The check command runs on the HOST (not in Docker) using the host's
# toolchain, which matches what the user configured.
#
# Requires: docker, python3

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="trellis-ralph"
DOCKERFILE="${SCRIPT_DIR}/Dockerfile.ralph"
AUTH_VOLUME="trellis-ralph-auth"

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

# Always rebuild the image. The Dockerfile is small (node + claude-code)
# and a stale image with an old Claude Code version causes hard-to-debug
# auth and runtime failures. Docker layer caching keeps rebuilds fast
# when nothing has changed.
build_image() {
  if [[ ! -f "$DOCKERFILE" ]]; then
    # Fall back to legacy Dockerfile name during migration
    if [[ -f "${SCRIPT_DIR}/Dockerfile.ralphd" ]]; then
      DOCKERFILE="${SCRIPT_DIR}/Dockerfile.ralphd"
    else
      echo -e "${RED}Dockerfile not found at ${DOCKERFILE}. Aborting.${RESET}"
      exit 1
    fi
  fi
  echo -e "${CYAN}Building Docker image ${IMAGE_NAME}...${RESET}"
  docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" \
    --build-arg "CACHE_BUST=$(date +%Y%m%d)" \
    "${SCRIPT_DIR}/.." || {
    echo -e "${RED}Docker build failed. Aborting.${RESET}"
    exit 1
  }
  echo -e "${GREEN}Image ${IMAGE_NAME} ready.${RESET}"
}

# Ensure the named auth volume exists.
# OAuth credentials persist here across tasks — one login, many runs.
ensure_auth_volume() {
  if ! docker volume inspect "$AUTH_VOLUME" &>/dev/null 2>&1; then
    docker volume create "$AUTH_VOLUME" >/dev/null
    echo -e "${CYAN}Created auth volume ${AUTH_VOLUME}.${RESET}"
  fi
}

# Clean stale files from the auth volume that compete with bind mounts.
# Previous container runs leave behind plugins/, settings.json, and projects/
# inside the volume. Stale files can cause plugin resolution failures if
# Claude Code reads the volume's copy before the overlay takes effect.
#
# IMPORTANT: Only remove files that are bind-mounted fresh from the host.
# Do NOT remove directories that may contain OAuth tokens stored by
# `claude login` inside Docker (e.g., statsig/, .credentials, etc.).
clean_auth_volume() {
  echo -e "${CYAN}Cleaning stale config from auth volume...${RESET}"
  # Run as root to ensure we can remove files regardless of ownership.
  # Also fix volume ownership so the claude user can write credentials.
  docker run --rm \
    --user root \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    --entrypoint sh \
    "$IMAGE_NAME" \
    -c '
      rm -rf /home/claude/.claude/plugins
      rm -f  /home/claude/.claude/settings.json
      rm -rf /home/claude/.claude/projects
      rm -rf /home/claude/.claude/shell-snapshots
      rm -rf /home/claude/.claude/backups
      rm -f  /home/claude/.claude/mcp-needs-auth-cache.json
      chown claude:claude /home/claude/.claude
    ' 2>/dev/null || true
}

# Generate a container-specific settings.json that keeps enabledPlugins but
# strips autoUpdate. This prevents Claude Code inside the container from
# trying to update plugins against the read-only bind mount.
CONTAINER_SETTINGS=""
generate_container_settings() {
  local host_settings="${HOME}/.claude/settings.json"
  if [[ ! -f "$host_settings" ]]; then
    return
  fi

  CONTAINER_SETTINGS=$(mktemp "${TMPDIR:-/tmp}/ralph-settings.XXXXXX")
  python3 -c "
import json, sys

with open(sys.argv[1]) as f:
    settings = json.load(f)

settings.pop('extraKnownMarketplaces', None)
settings['autoUpdates'] = False

with open(sys.argv[2], 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
" "$host_settings" "$CONTAINER_SETTINGS"
}

# Extract Docker-persisted .claude.json from the auth volume.
# The --login command copies ~/.claude.json into the volume as _claude.json.
# We extract it to a temp file so build_docker_run_args can mount it.
DOCKER_CLAUDE_JSON=""
extract_docker_claude_json() {
  DOCKER_CLAUDE_JSON=$(mktemp "${TMPDIR:-/tmp}/ralph-claude-json.XXXXXX")
  docker run --rm \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    --entrypoint sh \
    "$IMAGE_NAME" \
    -c 'cat /home/claude/.claude/_claude.json 2>/dev/null' > "$DOCKER_CLAUDE_JSON" 2>/dev/null || true
  if [[ ! -s "$DOCKER_CLAUDE_JSON" ]]; then
    rm -f "$DOCKER_CLAUDE_JSON"
    DOCKER_CLAUDE_JSON=""
  fi
}

# Build docker run arguments as a string.
# Bash 3.2 compatible — no readarray, no local -a with +=.
build_docker_run_args() {
  local args
  args="-v $(pwd):/workspace -v ${AUTH_VOLUME}:/home/claude/.claude"

  # Mount host's Claude config into the container so it can find installed
  # plugins and settings. Plugin paths in installed_plugins.json are absolute
  # (e.g., /Users/alice/.claude/plugins/cache/...), so we mount the host's
  # ~/.claude at BOTH the container home AND the original host-absolute path.
  local host_claude_dir="${HOME}/.claude"
  if [[ -d "${host_claude_dir}" ]]; then
    if [[ -d "${host_claude_dir}/plugins" ]]; then
      args="$args -v ${host_claude_dir}/plugins:/home/claude/.claude/plugins:ro"
      args="$args -v ${host_claude_dir}/plugins:${host_claude_dir}/plugins:ro"
    fi
    if [[ -n "$CONTAINER_SETTINGS" ]] && [[ -f "$CONTAINER_SETTINGS" ]]; then
      args="$args -v ${CONTAINER_SETTINGS}:/home/claude/.claude/settings.json:ro"
    elif [[ -f "${host_claude_dir}/settings.json" ]]; then
      args="$args -v ${host_claude_dir}/settings.json:/home/claude/.claude/settings.json:ro"
    fi
  fi

  # Mount .claude.json for account/auth data. Prefer the Docker-persisted
  # copy from --login (which has the Docker OAuth token) over the host's
  # copy (which has a macOS keychain-backed token unusable in Docker).
  if [[ -n "$DOCKER_CLAUDE_JSON" ]] && [[ -f "$DOCKER_CLAUDE_JSON" ]]; then
    args="$args -v ${DOCKER_CLAUDE_JSON}:/home/claude/.claude.json"
  elif [[ -f "${HOME}/.claude.json" ]]; then
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

  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo -e "${GREEN}ANTHROPIC_API_KEY is set.${RESET}"
    exit 0
  fi

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
  echo -e "${YELLOW}stored in the ${AUTH_VOLUME} volume and reused for all tasks.${RESET}"
  echo ""

  # Run login, then copy ~/.claude.json into the auth volume so the OAuth
  # token persists. Claude Code stores account/token data in ~/.claude.json
  # (a file at the home directory level), NOT inside ~/.claude/ (the volume).
  # Without this copy, the token is lost when the container exits.
  docker run --rm -it \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    --entrypoint sh \
    "$IMAGE_NAME" \
    -c 'claude login && cp ~/.claude.json ~/.claude/_claude.json'

  # Verify the token was actually persisted to the volume
  if docker run --rm \
    -v "${AUTH_VOLUME}:/home/claude/.claude" \
    --entrypoint sh \
    "$IMAGE_NAME" \
    -c 'test -s /home/claude/.claude/_claude.json'; then
    echo ""
    echo -e "${GREEN}${BOLD}Login complete. You can now run: ralph-loop.sh <feature-name>${RESET}"
  else
    echo ""
    echo -e "${RED}${BOLD}Login succeeded but credentials were not saved to the auth volume.${RESET}"
    echo -e "${YELLOW}This usually means the volume has wrong permissions. Try:${RESET}"
    echo -e "${YELLOW}  docker run --rm --user root -v ${AUTH_VOLUME}:/data --entrypoint sh ${IMAGE_NAME} -c 'chown -R claude:claude /data'${RESET}"
    echo -e "${YELLOW}Then re-run: ralph-loop.sh --login${RESET}"
    exit 1
  fi
  exit 0
fi

# --- Main loop mode ---

FEATURE="${1:?Usage: ralph-loop.sh <feature-name> [max-iterations] [--silent|--tail|--no-judge]  or  ralph-loop.sh --login}"
MAX_ITERATIONS="${2:-10}"

# Parse optional flags
OUTPUT_MODE="stream"
NO_JUDGE=false
shift 2 2>/dev/null || shift $# 2>/dev/null || true
for arg in "$@"; do
  case "$arg" in
    --silent)   OUTPUT_MODE="silent" ;;
    --stream)   OUTPUT_MODE="stream" ;;
    --tail)     OUTPUT_MODE="tail" ;;
    --no-judge) NO_JUDGE=true ;;
  esac
done

LOG_DIR="logs/ralph-${FEATURE}"

# Resolve specs dir from trellis.json (default: .specs)
SPECS_DIR=$(python3 -c "
import json
try:
    with open('trellis.json') as f:
        print(json.load(f).get('specsDir', '.specs'))
except Exception:
    print('.specs')
" 2>/dev/null || echo ".specs")

TASKS_JSON="${SPECS_DIR}/${FEATURE}/tasks.json"

mkdir -p "$LOG_DIR"

# --- Validate prerequisites ---

if [[ ! -f "$TASKS_JSON" ]]; then
  echo -e "${RED}No ${TASKS_JSON} found. Run /trellis:prep ${FEATURE} first.${RESET}"
  exit 1
fi

# The check command must be non-empty for ralph mode — without it there's
# no feedback signal to tell whether implementation succeeded.
CHECK_CMD=$(python3 -c "
import json
with open('$TASKS_JSON') as f:
    print(json.load(f).get('check', ''))
" 2>/dev/null || echo "")

if [[ -z "$CHECK_CMD" ]]; then
  echo -e "${RED}tasks.json has no check command. Ralph mode requires a non-empty check field.${RESET}"
  echo -e "${YELLOW}Add a check command to guidelines.md and re-run /trellis:prep.${RESET}"
  exit 1
fi

echo -e "${CYAN}Feature:  ${BOLD}${FEATURE}${RESET}"
echo -e "${CYAN}Check:    ${CHECK_CMD}${RESET}"
echo -e "${CYAN}Max iter: ${MAX_ITERATIONS}${RESET}"
echo ""

build_image
ensure_auth_volume

# --- Auth check ---

check_auth() {
  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo -e "${CYAN}Using ANTHROPIC_API_KEY for authentication.${RESET}"
    return 0
  fi

  echo -e "${CYAN}Checking authentication in Docker volume...${RESET}"

  # Use the same Docker args as actual task runs so the environment matches.
  # A bare invocation (auth volume only) can fail due to missing plugins or
  # settings, producing false auth failures.
  local run_args
  run_args=$(build_docker_run_args)

  local auth_output
  # shellcheck disable=SC2086  # intentional word splitting of run_args
  auth_output=$(echo "say ok" | docker run --rm -i \
    $run_args \
    "$IMAGE_NAME" \
    -p --dangerously-skip-permissions 2>&1) && true
  local auth_exit=$?

  if [[ $auth_exit -ne 0 ]]; then
    echo -e "${RED}Authentication check failed (exit code ${auth_exit}).${RESET}"
    echo -e "${RED}Output:${RESET}"
    echo "$auth_output" | head -20
    echo ""
    echo -e "${YELLOW}Run this first:  ${BOLD}ralph-loop.sh --login${RESET}"
    echo -e "${YELLOW}If you already ran --login and still see this, try setting${RESET}"
    echo -e "${YELLOW}ANTHROPIC_API_KEY as a fallback.${RESET}"
    exit 1
  fi

  echo -e "${GREEN}OAuth session verified in ${AUTH_VOLUME} volume.${RESET}"
}

# Order matters: generate settings, clean stale files, and extract
# Docker-persisted .claude.json BEFORE auth check, so check_auth
# runs with the same environment as actual task runs.
generate_container_settings
clean_auth_volume
extract_docker_claude_json
check_auth

# --- Helpers ---

# Get the next pending task ID from tasks.json.
# Returns empty string if no pending tasks remain.
get_next_pending_task() {
  python3 -c "
import json
with open('$TASKS_JSON') as f:
    data = json.load(f)
task = next((t for t in data['tasks'] if t['status'] == 'pending'), None)
print(task['id'] if task else '')
"
}

# Get current task counts for status display.
get_task_counts() {
  python3 -c "
import json
with open('$TASKS_JSON') as f:
    data = json.load(f)
tasks = data['tasks']
done = sum(1 for t in tasks if t['status'] == 'done')
pending = sum(1 for t in tasks if t['status'] == 'pending')
blocked = sum(1 for t in tasks if t['status'] == 'blocked')
total = len(tasks)
print(f'{done} done, {pending} pending, {blocked} blocked (of {total})')
"
}

# Run a prompt inside Docker and handle output modes.
# Arguments: $1=prompt_string $2=log_file $3=label
run_in_docker() {
  local prompt="$1"
  local log_file="$2"
  local label="$3"

  local run_args
  run_args=$(build_docker_run_args)

  # shellcheck disable=SC2086  # intentional word splitting of run_args
  case "$OUTPUT_MODE" in
    stream)
      echo "$prompt" | docker run --rm -i \
        $run_args \
        "$IMAGE_NAME" \
        -p --dangerously-skip-permissions 2>&1 | tee "$log_file"
      ;;
    *)
      echo "$prompt" | docker run --rm -i \
        $run_args \
        "$IMAGE_NAME" \
        -p --dangerously-skip-permissions > "$log_file" 2>&1
      if [[ "$OUTPUT_MODE" == "tail" ]]; then
        echo -e "${CYAN}--- Last 50 lines of ${label} ---${RESET}"
        tail -50 "$log_file"
        echo -e "${CYAN}--- End ${label} ---${RESET}"
      fi
      ;;
  esac
}

# shellcheck disable=SC2329  # invoked indirectly via trap
cleanup() {
  rm -f "$CONTAINER_SETTINGS"
  rm -f "$DOCKER_CLAUDE_JSON"
}
trap cleanup EXIT

# --- Main task loop ---
# Each iteration processes one task. This is different from the old loop
# which ran one full build skill invocation per iteration (processing
# multiple criteria). Here, each task gets its own Docker invocations for
# test-writing and implementation, with check running on the host between.

echo -e "${CYAN}${BOLD}Starting ralph loop for ${FEATURE}${RESET}"
echo -e "${YELLOW}Status: $(get_task_counts)${RESET}"
echo ""

for ((i = 1; i <= MAX_ITERATIONS; i++)); do
  TASK_ID=$(get_next_pending_task)

  if [[ -z "$TASK_ID" ]]; then
    echo -e "${GREEN}${BOLD}All tasks complete!${RESET}"
    echo -e "${YELLOW}Final: $(get_task_counts)${RESET}"
    break
  fi

  TASK_TITLE=$(python3 -c "
import json
with open('$TASKS_JSON') as f:
    data = json.load(f)
task = next(t for t in data['tasks'] if t['id'] == '$TASK_ID')
print(task['title'])
")

  echo -e "${CYAN}${BOLD}═══ Task ${TASK_ID}: ${TASK_TITLE} (iteration ${i}/${MAX_ITERATIONS}) ═══${RESET}"

  # --- Step 1: Test writer (conditional) ---
  # Deterministic heuristic decides if this task warrants test-first development.
  # Structural tasks (scaffold, config) skip this; behavioral tasks get tests.

  NEEDS_TESTS=$(python3 "${SCRIPT_DIR}/should-write-tests.py" "$TASKS_JSON" "$TASK_ID" | python3 -c "import json,sys; print(json.load(sys.stdin)['shouldWrite'])")

  if [[ "$NEEDS_TESTS" == "True" ]]; then
    echo -e "${CYAN}Writing tests for task ${TASK_ID}...${RESET}"
    PROMPT=$(python3 "${SCRIPT_DIR}/assemble-prompt.py" test-writer "$FEATURE" --task-id "$TASK_ID" | python3 -c "import json,sys; print(json.load(sys.stdin)['prompt'])")
    run_in_docker "$PROMPT" "${LOG_DIR}/task-${TASK_ID}-tests.log" "test-writer ${TASK_ID}"
    echo -e "${GREEN}Test-writer complete for ${TASK_ID}.${RESET}"
  else
    echo -e "${YELLOW}Skipping test-writer for ${TASK_ID} (structural task).${RESET}"
  fi

  # --- Step 2: Implementation ---
  # The builder receives the full task context: what to build, acceptance
  # criteria, the plan, guidelines, and what's already been built.

  echo -e "${CYAN}Building task ${TASK_ID}...${RESET}"
  PROMPT=$(python3 "${SCRIPT_DIR}/assemble-prompt.py" builder "$FEATURE" --task-id "$TASK_ID" | python3 -c "import json,sys; print(json.load(sys.stdin)['prompt'])")
  run_in_docker "$PROMPT" "${LOG_DIR}/task-${TASK_ID}-impl.log" "builder ${TASK_ID}"

  # --- Step 3: Check on host ---
  # The check command runs on the HOST, not in Docker. This uses the host's
  # toolchain (node, npm, cargo, etc.) which matches what the user configured.
  # The check output is captured for potential retry.

  CHECK_OUTPUT_FILE="${LOG_DIR}/task-${TASK_ID}-check.log"
  echo -e "${CYAN}Running check: ${CHECK_CMD}${RESET}"

  if eval "$CHECK_CMD" > "$CHECK_OUTPUT_FILE" 2>&1; then
    # --- Check passed: mark done ---
    echo -e "${GREEN}${BOLD}✓ Task ${TASK_ID} passed check.${RESET}"
    python3 "${SCRIPT_DIR}/update-tasks.py" "$TASKS_JSON" "$TASK_ID" "done" --iteration "$i" > /dev/null
    git add -A && git commit -m "ralph: task ${TASK_ID} done — ${TASK_TITLE}" 2>/dev/null || true
    echo -e "${YELLOW}Status: $(get_task_counts)${RESET}"
    echo ""
    continue
  fi

  # --- Step 4: Retry once ---
  # If check fails, assemble a retry prompt with the error output. The retry
  # prompt is focused: fix ONLY the errors shown, don't refactor or add features.

  echo -e "${YELLOW}Check failed for ${TASK_ID}. Retrying...${RESET}"

  PROMPT=$(python3 "${SCRIPT_DIR}/assemble-prompt.py" builder-retry "$FEATURE" --task-id "$TASK_ID" --check-output "$CHECK_OUTPUT_FILE" | python3 -c "import json,sys; print(json.load(sys.stdin)['prompt'])")
  run_in_docker "$PROMPT" "${LOG_DIR}/task-${TASK_ID}-retry.log" "retry ${TASK_ID}"

  # Re-run check after retry
  if eval "$CHECK_CMD" > "$CHECK_OUTPUT_FILE" 2>&1; then
    echo -e "${GREEN}${BOLD}✓ Task ${TASK_ID} passed check (after retry).${RESET}"
    python3 "${SCRIPT_DIR}/update-tasks.py" "$TASKS_JSON" "$TASK_ID" "done" --iteration "$i" > /dev/null
    git add -A && git commit -m "ralph: task ${TASK_ID} done (retry) — ${TASK_TITLE}" 2>/dev/null || true
  else
    echo -e "${RED}${BOLD}✗ Task ${TASK_ID} still failing after retry. Marking blocked.${RESET}"
    if [[ "$OUTPUT_MODE" != "stream" ]]; then
      echo -e "${CYAN}--- Check output ---${RESET}"
      tail -20 "$CHECK_OUTPUT_FILE"
      echo -e "${CYAN}--- End check output ---${RESET}"
    fi
    python3 "${SCRIPT_DIR}/update-tasks.py" "$TASKS_JSON" "$TASK_ID" blocked --iteration "$i" > /dev/null
    git add -A && git commit -m "ralph: task ${TASK_ID} blocked — ${TASK_TITLE}" 2>/dev/null || true
  fi

  echo -e "${YELLOW}Status: $(get_task_counts)${RESET}"
  echo ""

  # Check if all remaining tasks are blocked (no point continuing)
  REMAINING=$(python3 -c "
import json
with open('$TASKS_JSON') as f:
    data = json.load(f)
pending = sum(1 for t in data['tasks'] if t['status'] == 'pending')
print(pending)
")
  if [[ "$REMAINING" == "0" ]]; then
    echo -e "${YELLOW}${BOLD}No pending tasks remain.${RESET}"
    break
  fi
done

# --- Judge review ---
# The judge evaluates intent alignment: did you build what the spec asked for,
# not just what the tasks described. It runs once at the end, not per-task.
# Default is on; opt out with --no-judge.

JUDGE_ENABLED=$(python3 -c "
import json
with open('$TASKS_JSON') as f:
    data = json.load(f)
print(data.get('judge', True))
" 2>/dev/null || echo "True")

if [[ "$NO_JUDGE" == "true" ]]; then
  JUDGE_ENABLED="False"
fi

if [[ "$JUDGE_ENABLED" == "True" ]]; then
  echo -e "${CYAN}${BOLD}═══ Judge Review ═══${RESET}"
  PROMPT=$(python3 "${SCRIPT_DIR}/assemble-prompt.py" judge "$FEATURE" | python3 -c "import json,sys; print(json.load(sys.stdin)['prompt'])")
  run_in_docker "$PROMPT" "${LOG_DIR}/judge.log" "judge"

  # Show judge output regardless of mode — it's the final verdict
  echo -e "${CYAN}--- Judge verdict ---${RESET}"
  cat "${LOG_DIR}/judge.log"
  echo -e "${CYAN}--- End judge verdict ---${RESET}"
else
  echo -e "${YELLOW}Judge review skipped (--no-judge).${RESET}"
fi

# --- Final summary ---

echo ""
echo -e "${CYAN}${BOLD}═══ Ralph loop complete ═══${RESET}"
echo -e "${YELLOW}Final: $(get_task_counts)${RESET}"
echo -e "${CYAN}Logs:  ${LOG_DIR}/${RESET}"
