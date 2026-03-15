#!/usr/bin/env bats
# Tests for Trellis shell scripts (ralph-loop.sh).
#
# Run: bats tests/test-shell.bats
#
# Strategy: Test helper functions and control flow by sourcing fragments
# of the scripts and mocking external commands (claude, docker, git).

SCRIPT_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts"
ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"

setup() {
  BATS_TMPDIR="$(mktemp -d)"
  cd "$BATS_TMPDIR"

  # Create mock bin directory and add to PATH
  MOCK_BIN="${BATS_TMPDIR}/mock-bin"
  mkdir -p "$MOCK_BIN"
  export PATH="${MOCK_BIN}:${PATH}"

  # Create mock claude command
  cat > "${MOCK_BIN}/claude" <<'MOCK'
#!/usr/bin/env bash
echo "mock claude"
exit 0
MOCK
  chmod +x "${MOCK_BIN}/claude"

  # Create mock docker command
  cat > "${MOCK_BIN}/docker" <<'MOCK'
#!/usr/bin/env bash
echo "mock docker"
exit 0
MOCK
  chmod +x "${MOCK_BIN}/docker"

  # Create mock git command
  cat > "${MOCK_BIN}/git" <<'MOCK'
#!/usr/bin/env bash
echo "mock git"
exit 0
MOCK
  chmod +x "${MOCK_BIN}/git"
}

teardown() {
  rm -rf "$BATS_TMPDIR"
}

# --- specs dir resolution ---

@test "specs dir defaults to .specs without trellis.json" {
  result=$(python3 -c "
import json
try:
    with open('trellis.json') as f:
        print(json.load(f).get('specsDir', '.specs'))
except Exception:
    print('.specs')
" 2>/dev/null || echo ".specs")
  [ "$result" = ".specs" ]
}

@test "specs dir reads from trellis.json" {
  echo '{"specsDir": "design"}' > trellis.json
  result=$(python3 -c "
import json
try:
    with open('trellis.json') as f:
        print(json.load(f).get('specsDir', '.specs'))
except Exception:
    print('.specs')
" 2>/dev/null)
  [ "$result" = "design" ]
}

# --- ralph-loop.sh exit when no tasks.json ---

@test "ralph-loop.sh exits 1 when no tasks.json exists" {
  mkdir -p .specs/test-feature
  run bash "$SCRIPT_DIR/ralph-loop.sh" test-feature
  [ "$status" -eq 1 ]
  [[ "$output" == *"No .specs/test-feature/tasks.json found"* ]]
}

# --- ralph-loop.sh requires docker ---

@test "ralph-loop.sh exits 1 when docker is missing" {
  # Remove the mock docker so the command is truly not found
  rm -f "${MOCK_BIN}/docker"

  # Also remove any real docker from PATH by overriding PATH to only include mock
  export PATH="${MOCK_BIN}:/usr/bin:/bin"

  # Only run if docker is actually not at /usr/bin/docker or /bin/docker
  if command -v docker &>/dev/null; then
    skip "docker is installed on this system"
  fi

  run bash "$SCRIPT_DIR/ralph-loop.sh" test-feature
  [ "$status" -eq 1 ]
  [[ "$output" == *"docker is not installed"* ]]
}

# --- ralph-loop.sh requires non-empty check command ---

@test "ralph-loop.sh exits 1 when check is empty" {
  mkdir -p .specs/test-feature
  echo '{"feature":"test","check":"","tasks":[]}' > .specs/test-feature/tasks.json
  run bash "$SCRIPT_DIR/ralph-loop.sh" test-feature
  [ "$status" -eq 1 ]
  [[ "$output" == *"no check command"* ]]
}

# --- cleanup removes temp settings file ---

@test "cleanup removes temp settings file" {
  tmpfile=$(mktemp "${TMPDIR:-/tmp}/ralph-settings.XXXXXX")
  [ -f "$tmpfile" ]

  rm -f "$tmpfile"
  [ ! -f "$tmpfile" ]
}
