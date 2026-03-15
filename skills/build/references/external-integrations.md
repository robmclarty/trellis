# External Integrations

The build skill can optionally integrate with external tools.

## Ralph (Docker-based implementation loop)

**What it is:** A bundled loop script (`scripts/ralph-loop.sh`) that runs each task in a fresh Claude Code context inside a Docker container. Based on Geoffrey Huntley's Ralph Wiggum methodology — fresh context per task prevents degradation on long implementations.

**How to use:** `/build <feature> with ralph [--silent|--tail|--no-judge]`

**Output modes:**

- *(default)* — Stream. Full Claude output visible in real-time via `tee`, also logged.
- `--silent` — Output goes to log files only. Between-task status (done/blocked/pending counts) is shown.
- `--tail` — Silent during task, shows last 50 lines of log after each task completes.

**How it works:** When `with ralph` is specified:

1. The build skill validates tasks.json exists and has a non-empty `check` field
2. The skill launches `scripts/ralph-loop.sh <feature-name>`
3. The loop script does ALL orchestration — it does NOT invoke the build skill inside Docker
4. For each pending task, the loop script:
   - Runs `should-write-tests.py` to decide if tests are needed (deterministic heuristic)
   - Runs `assemble-prompt.py` to build a prompt from templates + task data + spec artifacts
   - Sends the assembled prompt to `claude -p --dangerously-skip-permissions` inside Docker
   - The LLM writes tests or code only — no orchestration, no state management
   - Runs the `check` command on the host to validate
   - Runs `update-tasks.py` to mark the task done or blocked in tasks.json
   - Git commits the progress
5. After all tasks: optionally runs the judge agent for spec intent alignment review
6. The loop stops when: all tasks done, all remaining tasks blocked, or max iterations reached (default 10)

**Security model:** Each LLM invocation runs inside a Docker container with `--dangerously-skip-permissions`. Docker is the security boundary — the container can only access the bind-mounted project directory and the auth volume. The `check` command runs on the host (not in Docker), using the host's toolchain.

**Authentication:** Two modes, auto-detected:

- **API key:** If `ANTHROPIC_API_KEY` is set, it's passed into the container.
- **OAuth/subscription:** Run `ralph-loop.sh --login` once. Credentials stored in the `trellis-ralph-auth` Docker volume and reused across iterations.

**Requirements:**

- `docker` installed and daemon running
- One of: `ANTHROPIC_API_KEY` env var, or `ralph-loop.sh --login` completed
- Non-empty `check` field in tasks.json

**When to use:** Large implementations (5+ tasks, many files) where context degradation is a concern. Fire-and-forget: launch it and come back hours later.

**Resume from interruption:** Kill the process, re-run `/build <feature> with ralph`. The script reads tasks.json and picks up from the first pending task.

## Open Spec

**What it is:** A structured requirements format designed for agentic interpretation, with machine-parseable fields.

**Where to find it:** [github.com/open-spec/open-spec](https://github.com/open-spec/open-spec)

**How it integrates:** If the spec uses Open Spec format, the task-writer agent can use its structured fields directly for more reliable task generation.
