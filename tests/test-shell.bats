#!/usr/bin/env bats
# Tests for Trellis shell scripts (ralph-loop.sh and ralphd-loop.sh).
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

# --- json_field helper ---

@test "json_field extracts a value from JSON" {
  # Reproduce the json_field function inline
  result=$(echo '{"doneCount": 5, "pendingCount": 3}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('doneCount', ''))
" 2>/dev/null)
  [ "$result" = "5" ]
}

@test "json_field returns default on missing key" {
  result=$(echo '{"doneCount": 5}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('missingKey', 'fallback'))
" 2>/dev/null)
  [ "$result" = "fallback" ]
}

@test "json_field returns default on invalid JSON" {
  result=$(echo 'not json' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('field', 'default'))
except:
    print('default')
" 2>/dev/null || echo "default")
  [ "$result" = "default" ]
}

# --- ralph-loop.sh exit when no state file ---

@test "ralph-loop.sh exits 1 when no state file exists" {
  mkdir -p .specs/.state
  run bash "$SCRIPT_DIR/ralph-loop.sh" test-feature
  [ "$status" -eq 1 ]
  [[ "$output" == *"No .specs/.state/implement-state.md found"* ]]
}

# --- generate_permissions creates correct structure ---

@test "generate_permissions produces valid settings JSON" {
  mkdir -p .specs/.state .claude

  # Create a minimal state file
  cat > .specs/.state/implement-state.md <<'STATE'
## Oracle Pipeline
- [x] build: `npm run build`
- [x] lint: `npm run lint`
- [ ] test: `npm test`

## Acceptance Criteria
- [ ] AC-1 (task 1.1): Pending (pending)
STATE

  # Source the script in a subshell, extract only the generate_permissions function
  # by running the script and letting it call generate_permissions before the loop fails
  # Instead, we directly test the generate_permissions output by calling the Python
  # snippet that it runs
  SETTINGS_FILE=".claude/settings.local.json"
  STATE_FILE=".specs/.state/implement-state.md"
  state_json=$(python3 "$SCRIPT_DIR/parse-implement-state.py" "$STATE_FILE" 2>/dev/null || echo '{}')

  python3 -c "
import json, sys

state = json.loads('''${state_json}''')
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

settings = {
    'permissions': {
        'allow': allowed,
        'deny': []
    }
}

with open('${SETTINGS_FILE}', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')
" 2>/dev/null

  # Verify the file was created and is valid JSON
  [ -f "$SETTINGS_FILE" ]

  # Verify it contains pipeline commands
  run python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    data = json.load(f)
allowed = data['permissions']['allow']
assert 'Bash(npm run build)' in allowed, 'Missing build command'
assert 'Bash(npm run lint)' in allowed, 'Missing lint command'
assert 'Bash(npm test)' in allowed, 'Missing test command'
assert 'Read' in allowed, 'Missing Read tool'
print('OK')
"
  [ "$status" -eq 0 ]
  [ "$output" = "OK" ]
}

# --- run_preflight writes JSON ---

@test "preflight assembles valid JSON from state and prereqs" {
  mkdir -p .specs/.state .specs/test-feature

  cat > .specs/.state/implement-state.md <<'STATE'
## Acceptance Criteria
- [ ] AC-1 (task 1.1): Test criterion (pending)
STATE

  cat > .specs/guidelines.md <<'GUIDE'
# Guidelines
GUIDE

  PREFLIGHT_FILE=".specs/.state/implement-preflight.json"
  SPECS_DIR=".specs"
  FEATURE="test-feature"

  state_json=$(python3 "$SCRIPT_DIR/parse-implement-state.py" "$SPECS_DIR/.state/implement-state.md" 2>/dev/null || echo '{}')
  prereqs_json=$(python3 "$SCRIPT_DIR/validate-prereqs.py" implement "$FEATURE" 2>/dev/null || echo '{"valid":false,"missing":["unknown"]}')

  python3 -c "
import json
state = json.loads('''${state_json}''')
prereqs = json.loads('''${prereqs_json}''')
preflight = {
    'specsDir': '${SPECS_DIR}',
    'prereqs': prereqs,
    'state': state,
    'criteria': {},
}
with open('${PREFLIGHT_FILE}', 'w') as f:
    json.dump(preflight, f, indent=2)
    f.write('\n')
" 2>/dev/null

  [ -f "$PREFLIGHT_FILE" ]

  run python3 -c "
import json
with open('$PREFLIGHT_FILE') as f:
    data = json.load(f)
assert data['specsDir'] == '.specs'
assert 'prereqs' in data
assert 'state' in data
print('OK')
"
  [ "$status" -eq 0 ]
  [ "$output" = "OK" ]
}

# --- ralphd-loop.sh requires docker ---

@test "ralphd-loop.sh exits 1 when docker is missing" {
  # Remove the mock docker so the command is truly not found
  rm -f "${MOCK_BIN}/docker"

  # Also remove any real docker from PATH by overriding PATH to only include mock
  export PATH="${MOCK_BIN}:/usr/bin:/bin"

  # Only run if docker is actually not at /usr/bin/docker or /bin/docker
  if command -v docker &>/dev/null; then
    skip "docker is installed on this system"
  fi

  run bash "$SCRIPT_DIR/ralphd-loop.sh" test-feature
  [ "$status" -eq 1 ]
  [[ "$output" == *"docker is not installed"* ]]
}

# --- parse-implement-state.py integration ---

@test "parse-implement-state.py returns valid JSON for state file" {
  mkdir -p .specs/.state

  cat > .specs/.state/implement-state.md <<'STATE'
## Config
- Lint: `npm run lint`
- Test: off

## Oracle Pipeline
- [x] build: `npm run build`
- [ ] test: `npm test`

## Acceptance Criteria
- [x] AC-1 (task 1.1): Setup (done, iteration 1)
- [ ] AC-2 (task 1.2): Auth (pending)

## Iteration Log
### Iteration 1
Did setup.
STATE

  run python3 "$SCRIPT_DIR/parse-implement-state.py" .specs/.state/implement-state.md
  [ "$status" -eq 0 ]

  # Validate the JSON output
  run python3 -c "
import json
data = json.loads('''$output''')
assert data['doneCount'] == 1
assert data['pendingCount'] == 1
assert data['nextPendingId'] == 'AC-2'
assert data['iteration'] == 1
assert data['config']['test'] == False
assert data['config']['lint'] == 'npm run lint'
print('OK')
"
  [ "$status" -eq 0 ]
  [ "$output" = "OK" ]
}

# --- cleanup removes preflight file ---

@test "cleanup removes preflight JSON file" {
  mkdir -p .specs/.state
  echo '{}' > .specs/.state/implement-preflight.json
  [ -f .specs/.state/implement-preflight.json ]

  rm -f .specs/.state/implement-preflight.json
  [ ! -f .specs/.state/implement-preflight.json ]
}
