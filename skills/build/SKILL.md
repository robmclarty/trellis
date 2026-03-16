---
name: trellis:build
description: Executes implementation from tasks.json through a check-driven feedback loop. Use when all spec artifacts are ready and implementation should begin.
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Task
---

# Build

Turn specifications into working code through a task-by-task feedback loop. Each task gets tests first (TDD), then implementation, then a check command validates correctness.

## When to use

- "build this", "implement this"
- After completing the spec pipeline (pitch → spec → plan → prep)
- When `tasks.json` exists (or plan.md exists — tasks.json will be auto-generated)

## Step 0 — Parse invocation modifiers

**Do this FIRST, before any pre-flight scripts or file reads.**

Parse the user's invocation for the `with ralph` suffix and optional flags:

- **`with ralph`** → Set `ralphMode = "ralph"`. Ralph is a Docker-based loop script that runs each task in a fresh context. Fire-and-forget: the user walks away and comes back when it's done.
- **No modifier** → Set `ralphMode = "off"`. All tasks run in the current session.

Optional flags (only meaningful in ralph mode):

- **`--silent`** → Output goes to log files only; status shown between tasks.
- **`--tail`** → Show last 50 lines of each iteration's log after it completes.
- **`--no-judge`** → Skip the judge review at the end.
- **Neither** → Stream mode (default) — full Claude output visible in real-time.

**IMPORTANT:** If the user wrote `with ralph`, you MUST recognize it as an execution mode modifier. Never ask "what is ralph?" or treat it as an unknown term.

## Pre-flight

1. Read `trellis.json` to get `specsDir` (default: `.specs`)
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py build <feature-name>` and use the `specsDir` value from the JSON output. Abort if prerequisites are missing.
3. Check if `{specsDir}/{feature}/tasks.json` exists.
   - **If missing:** Tell the user "No tasks.json found — running `/trellis:prep` to generate it." Then invoke `/trellis:prep <feature-name>`. After prep completes, continue with the generated tasks.json.
   - **If present:** Read it and continue.
4. If all tasks have status `"done"` → report completion and stop.
5. If the `check` field is empty → ask the user: "What command should pass for code to be correct? (e.g., `npm run lint && npm run typecheck && npm run build && npm run test`)" Write their answer into tasks.json's `check` field.

## Ralph handoff

If `ralphMode == "ralph"`:

1. Verify the `check` field in tasks.json is non-empty. If empty, abort with: "Ralph mode requires a check command. Set it in guidelines.md or run `/trellis:build <feature>` interactively first."
2. Launch ralph in the background:
   ```
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/ralph-loop.sh <feature-name> [limit] [flags]
   ```
   Use `run_in_background: true` on the Bash tool.

3. **Enter monitoring loop.** Ralph writes progress to `logs/ralph-<feature>/status.json` and output to `logs/ralph-<feature>/output.log`. Poll every 60 seconds:

   a. Read `logs/ralph-<feature>/status.json`. If the file does not exist yet, ralph is still starting up — wait and retry.
   b. Display a compact progress block (no extra commentary):
      ```
      Ralph: <feature> | <Xm Ys> elapsed
      Task <index>/<total> (<id>): <title> [<phase>]
      Done: <N> | Blocked: <N> | Pending: <N>
      ```
   c. Read the last 10 lines of `logs/ralph-<feature>/output.log` using `tail -10` and display them in a fenced code block labeled "Recent output".
   d. If `status.json` shows `"finished": true`, exit the monitoring loop.
   e. If the background process is no longer running (check via TaskOutput) AND `status.json` does not show `"finished": true`, assume ralph crashed. Display the last 30 lines of `output.log` and report the failure.
   f. Sleep 60 seconds between polls using the Bash tool.

4. **Final summary.** When ralph finishes:
   - Read final `status.json` for exit code and counts.
   - Display done/blocked/pending totals.
   - If any tasks are blocked, list them with IDs and titles from tasks.json.
   - If the judge ran, mention the verdict is in `logs/ralph-<feature>/judge.log`.
   - If `exitCode` is non-zero, show the last 30 lines of `output.log`.

If `ralphMode == "off"`: Proceed to the execution loop below.

## Execution loop (in-session mode)

For each task in tasks.json where `status == "pending"`, in order:

### Step 0: Precondition check

Run the check command from tasks.json. This verifies all previous work is still green.

- If this is the first task and check fails, that's expected (nothing built yet). Skip.
- If this is a subsequent task and check fails, prior work regressed. Fix the regression before proceeding to the next task.

### Step 1: Write tests (test-writer agent)

Evaluate the task's `verify` field. If it describes behavioral expectations (validates input, returns errors, handles edge cases, state transitions), spawn the test-writer agent:

- **Input:** The task's `verify` and `do` fields, plus test conventions from guidelines.md
- **Output:** Test file(s) written to disk. The tests should FAIL (the implementation doesn't exist yet).

Skip the test-writer for purely structural verify text (file exists, scaffold created, config set, compiles clean). Use `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/should-write-tests.py` if unsure.

### Step 2: Implement the task

Write the code described in the task's `do` field. Follow this priority for guidance:

1. The task's `do` field — most specific instructions
2. `plan.md` — technical patterns, file structure, architecture
3. `guidelines.md` — project-wide conventions
4. Existing code — style consistency

### Step 3: Run check

Run the check command from tasks.json:

- **Pass** → Update the task's `status` to `"done"` in tasks.json. Git commit. Proceed to next task.
- **Fail** → Read the error output. Fix the specific issues. Run check again.
  - **Pass on retry** → Mark done, commit, next task.
  - **Fail on retry** → Mark the task's `status` as `"blocked"` in tasks.json. Git commit. Move to the next task.

### Step 4: Write updated tasks.json

After each task, write the updated tasks.json to disk. This is the resume point — if the session is interrupted, re-running `/trellis:build <feature>` picks up from the first pending task.

## Judge review

After all tasks are processed (unless `--no-judge` was passed):

Spawn the judge agent with:

- `spec.md` — the full specification
- `tasks.json` — showing which tasks are done, blocked, or pending
- `git diff --stat` — summary of all changes made

The judge evaluates **intent alignment**: did the implementation satisfy what the spec asked for, not just what the tasks described? It returns a structured verdict (PASS / PARTIAL / FAIL) with per-task assessments and recommendations.

If the judge says PARTIAL or FAIL, fix the specific issues and re-run the check. Limit: 2 judge re-submissions. After that, report to the user with the judge's feedback.

## Post-judge redefinition (ralph mode)

In ralph mode, after the judge completes, an automated redefinition loop kicks in if blocked tasks remain or the judge returns PARTIAL/FAIL:

1. The **redefiner agent** reads failure logs and the judge verdict, diagnoses root causes (convention mismatch, environment limitation, logic error, test fragility), and rewrites blocked task `do` fields with lessons learned.
2. The redefiner may add new tasks for judge-identified gaps (using phase N+1 numbering).
3. Blocked tasks are reset to `"pending"` and the task loop re-executes.
4. Maximum **3 redefinition passes**. After that, ralph stops and reports remaining issues — they likely require human judgment.

During redefinition, `status.json` shows `"currentPhase": "redefining"` and includes a `redefinitionPass` field. Redefiner logs are written to `logs/ralph-<feature>/redefiner-pass-N.log`.

## Reporting

When done (or when stopping due to blocked tasks), report:

1. **Tasks completed / blocked / remaining**
2. **Files created/modified** — brief summary
3. **Judge verdict** — if run
4. **Remaining work** — what's blocked and why

## References

- `references/external-integrations.md` — How Ralph mode works
- `references/git-usage.md` — Git rules during implementation
- `references/sub-agent-strategy.md` — Test-writer and judge spawning
- `references/error-recovery.md` — Resume from interruption
