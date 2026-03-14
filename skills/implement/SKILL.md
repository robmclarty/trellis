---
name: trellis:implement
description: Executes implementation from spec-driven artifacts or freeform instructions through iterative oracle-driven feedback loops. Use when all spec artifacts are ready and implementation should begin.
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Task
---

## When to use

- "implement this", "build this"
- Passing a feature folder, sketch name, or inline instructions expecting working code
- After completing the spec pipeline and wanting to move from planning to execution
- Supports Ralph mode, Open Spec format, and Promptfoo for repeatable evaluations

# Implement

Turn specifications, sketches, or freeform instructions into working code through
iterative oracle-driven feedback loops. The input artifacts are the source of truth.

**Recommended effort: high.** Multi-phase coordination with oracle-driven feedback loops and error recovery.

## Step 0 — Parse invocation modifiers

**Do this FIRST, before any pre-flight scripts or file reads.**

Parse the user's invocation for the `with <modifier>` suffix:

- **`with ralph`** → Set `ralphMode = "ralph"`. Ralph is a **bundled loop script** for context-fresh iteration. It is NOT a person, collaborator, or external tool. See `references/external-integrations.md` for details.
- **`with ralphd`** → Set `ralphMode = "ralphd"`. Docker-sandboxed variant of Ralph. Same concept, different execution model.
- **No modifier** → Set `ralphMode = "off"`. All phases run in the current session.

**IMPORTANT:** If the user wrote `with ralph` or `with ralphd`, you MUST recognize it as an execution mode modifier. Never ask "what is ralph?" or treat it as an unknown term.

## Pre-flight

**If `{specsDir}/.state/implement-preflight.json` exists** (Ralph resumption — the loop script writes this before each iteration), read it directly. It contains `specsDir`, `prereqs`, `state`, and `criteria`. Skip the python3 calls below — they've already been run outside your context. Also skip Phase 0 and Phase 1 — go directly to Phase 2.

**Otherwise** (fresh start or interactive mode), run these scripts:

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py implement <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

If `{specsDir}/.state/implement-state.md` exists, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/parse-implement-state.py` to get structured state data for resumption.

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-criteria.py <specs-dir>/<feature-name>/tasks.md <specs-dir>/<feature-name>/spec.md` to get structured acceptance criteria.

A pipeline of machine-readable checks is the termination signal. An LLM judge
verifies alignment with intent.

Read `references/oracle-pipeline.md` before starting any implementation. It
contains the full mechanics of the feedback loop, the judge sub-agent prompt, and
notes on integration with tools like Ralph and Promptfoo. See
`references/external-integrations.md` for details on what these tools are and
how they integrate with the implement skill.

## Invocation

```text
/implement <input> [with <modifier>]
```

`<input>` is one of the following (or a combination):

- **Feature folder name** — A name under `.specs/` (e.g., `hall-pass-extraction`).
  The skill reads `spec.md`, `plan.md`, `tasks.md`, and optionally `pitch.md` and
  `compliance.md` from `.specs/<name>/`.
- **Sketch file name(s)** — One or more names under `.specs/sketches/` (e.g.,
  `drizzle-multi-tenant`). The skill reads the corresponding `.md` files.
- **Inline text** — Freeform instructions for lightweight tasks that don't have
  formal artifacts.

These can be combined. For instance, a user might pass a feature folder plus an
additional inline instruction like "start with Phase 2 tasks only" or "skip the
MCP layer for now."

### Modifiers

The optional `with <modifier>` suffix activates special execution modes:

- **`with ralph`** — After Phase 0 and Phase 1 complete interactively, hand off
  Phase 2 to `scripts/ralph-loop.sh` for context-fresh iterations. Each iteration
  runs in a new Claude Code context, using `{specsDir}/.state/implement-state.md` as filesystem
  memory. Use for large implementations (10+ acceptance criteria, many files).
- **`with ralphd`** — Same as `with ralph`, but each iteration runs inside a
  Docker container with `--dangerously-skip-permissions`. Docker is the security
  boundary — no scoped permissions needed. Requires `docker` on the host.
  Supports both API key (`ANTHROPIC_API_KEY`) and OAuth/subscription auth
  (one-time `ralphd-loop.sh --login`). The image is built automatically on
  first run.

## Phase 0 — Input intake and configuration

### Step 1: Load inputs

Determine what the user provided:

1. **Feature folder.** If the input matches a folder under `.specs/`, load all
   artifacts that exist:
   - `tasks.md` — Primary driver. Each task becomes a unit of work.
   - `plan.md` — Technical decisions, file structure, patterns. The "how."
   - `spec.md` — Functional requirements, success criteria. The "what."
   - `pitch.md` — Problem context, appetite, no-gos. The "why."
   - `compliance.md` — Regulatory constraints (if present).

   The task list from `tasks.md` is the execution backbone. Each task already has
   a "Do" and "Verify" section derived from the plan and spec. The implement skill
   executes them in order.

2. **Sketch file(s).** If the input references one or more sketch names, load
   each from `.specs/sketches/<name>.md`. Sketches are lighter-weight. They have a
   hypothesis, method, and verdict but no formal task breakdown. The skill must
   synthesize implementation steps from the sketch content.

3. **Inline text.** Treat as a lightweight spec. Extract what you can.

4. **Hybrid.** If the user provides a feature folder plus inline overrides (like
   "only implement Phase 1" or "use a different database"), the inline text takes
   precedence for the specific override while the artifacts remain the baseline.

### Step 2: Ask configuration questions

**MANDATORY — DO NOT SKIP.** The oracle pipeline cannot be assembled without the user's tooling answers. You MUST ask these questions and wait for the user's answers before proceeding to Step 3.

**STOP here and ask the user.** Do not infer commands from the project structure. Do not guess. Do not proceed to Phase 1 or write any code until you have received explicit answers.

Read `references/config-questions.md` for the full list of configuration questions to ask.

### Steps 3–5: Analyze inputs, branch management, and summary

Read `references/phase-zero-analysis.md` for the detailed process of building the acceptance criteria checklist, managing branches for sketch implementations, and presenting the summary for user confirmation.

## Phase 1 — Oracle pipeline assembly

**MANDATORY — DO NOT SKIP.** Phase 2 cannot start without a configured pipeline written to `{specsDir}/.state/implement-state.md`. You MUST assemble the pipeline and write the state file before proceeding. Do NOT write any implementation code until this file exists.

**Gate check:** If `{specsDir}/.state/implement-state.md` does not exist after this phase, you have a bug. Stop and fix it.

Build the oracle pipeline from the user's configuration answers. The pipeline is
an ordered list of check stages, cheapest/fastest first:

| Stage | Purpose | Source | Enabled when |
|-------|---------|--------|--------------|
| 1. Type-check | Structural correctness | User-provided command | User gave a command |
| 2. Lint + fix | Style and basic errors | User-provided command(s) | User gave command(s) |
| 3. Build | Compilation / bundling | User-provided command | User gave a command |
| 4. Schema check | Runtime shape validation | Custom validation script | Spec mentions schemas |
| 5. Tests | Behavioral correctness | User-provided command | Tests exist or are created |
| 6. Custom checks | Spec-specific validation | Any command | Spec defines checks |
| 7. Judge | Intent alignment | Sub-agent review | Always the final gate |

Write the assembled pipeline to `{specsDir}/.state/implement-state.md`.

The pipeline is not fixed. If the user's project needs stages not listed here
(e.g., a migration check, an MCP manifest validation, a Docker build), add them.
The user's tooling answers are the authority.

## Ralph/Ralphd handoff gate (between Phase 1 and Phase 2)

**Check this IMMEDIATELY after writing `{specsDir}/.state/implement-state.md` in Phase 1.**

If `ralphMode` (from Step 0) is `"ralph"`:

1. Inform the user that Ralph mode is handing off to the loop script.
2. Launch `bash ${CLAUDE_PLUGIN_ROOT}/scripts/ralph-loop.sh <feature-name>` via the Bash tool.
3. **STOP HERE.** The current interactive session ends. The loop script takes over. Do NOT proceed to Phase 2 in this session.

If `ralphMode` is `"ralphd"`:

1. Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/ralphd-loop.sh --check-auth` via Bash. If it exits non-zero, run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/ralphd-loop.sh --login` so the user can complete OAuth.
2. Inform the user that Ralphd mode is handing off to the Docker loop script.
3. Launch `bash ${CLAUDE_PLUGIN_ROOT}/scripts/ralphd-loop.sh <feature-name>` via the Bash tool.
4. **STOP HERE.** The current interactive session ends.

If `ralphMode` is `"off"`: Proceed to Phase 2 below.

## Phase 2 — Implement and iterate

**Entry guard:** Before entering the iteration loop, verify that `{specsDir}/.state/implement-state.md` exists and contains a `## Config` section and an `## Oracle Pipeline` section. If it does not, you skipped Phase 0 or Phase 1 — go back and complete them. Do not proceed without the state file.

This is the core loop. The iteration strategy depends on the input type:

- **Feature folder with tasks.md:** Follow the task list. Each task (or small
  group of tightly related tasks) is one iteration. Tasks are already ordered
  with dependencies resolved.
- **Sketch files:** Synthesize 2-5 implementation steps from the sketch content.
  Each step is one iteration.
- **Inline text:** Break into coherent units yourself. One feature, one module,
  or one acceptance criterion per iteration.

### Step 1: Plan the iteration

Before writing code, write a brief plan (2-5 bullets) of what this iteration
will accomplish. If working from `tasks.md`, reference the specific task IDs.
If working from the plan, reference the relevant `plan.md` sections for patterns
and file structure.

Scope each iteration to a coherent, small unit of work. Do not try to implement
everything in a single pass.

### Step 1.5: Spawn test writer (conditional)

If any criteria in this iteration's scope are behavioral, edge-heavy, stateful,
permission-dependent, or otherwise non-obvious (see `references/test-writer-agent.md`
for the full heuristic), spawn the test writer sub-agent to produce targeted
tests before writing implementation code.

The test writer runs in an isolated context. Pass it only:

- The relevant criteria (from tasks.md "Verify" or spec.md §8)
- The expected module path (from plan.md §6)
- Project test conventions (from the user's config and guidelines.md)
- Any existing types or schemas

It returns a complete test file. Write it to disk and scope the test command to
run only the new file during this iteration.

The tests will fail initially. That's the point. They become part of the oracle
pipeline, and the implementation is done when they pass alongside the other
stages.

Skip the test writer for criteria that are purely structural (type-checker catches
it) or intent-based (judge catches it).

### Step 2: Write the code

Implement the planned change. Follow this priority for guidance:

1. `tasks.md` "Do" section for the current task — most specific instructions
2. `plan.md` for technical patterns, file structure, and architecture
3. `spec.md` for functional requirements and data model
4. `guidelines.md` for project-wide conventions
5. Existing code in the project for style consistency

If multiple sources conflict, flag the conflict in `{specsDir}/.state/implement-state.md` and
follow the most specific source (tasks > plan > spec > guidelines).

### Step 3: Run the oracle pipeline

Execute each enabled stage in order. Stop at the first failure.

```text
→ typecheck  → PASS → lint → PASS → build → PASS → test → PASS → judge → PASS
                ↓              ↓              ↓             ↓              ↓
              FAIL           FAIL           FAIL          FAIL           FAIL
                ↓              ↓              ↓             ↓              ↓
           Read errors,   Read errors,   Read errors,  Read errors,  Read judge
           fix, re-run    fix, re-run    fix, re-run   fix, re-run   feedback,
           this stage     this stage     this stage    this stage    revise code
```

For each failing stage:

- Parse the structured error output
- Fix the specific issues identified
- Re-run from the failing stage (not from the beginning, unless the fix was
  structural enough to warrant it)

**Per-stage retry limit: 3 attempts.** If a single stage fails 3 times in a row,
pause and report to the user. Include:

- Which stage is failing
- The error output from the last attempt
- What you've tried
- Your best guess at what's wrong

### Step 4: Update state

After the pipeline passes for this iteration's scope, update
`{specsDir}/.state/implement-state.md`:

- Mark completed criteria as `done`
- Record which iteration completed them
- If working from tasks.md, check the task checkbox
- Note any new unknowns that surfaced

### Step 5: Check termination

If all acceptance criteria are `done`, proceed to Phase 3.
If criteria remain, return to Step 1 for the next iteration.

**Global iteration limit: 10.** If you hit 10 iterations without completing all
criteria, stop and report what's done, what's remaining, and why you stalled.

### Ralph/Ralphd resumption (context-fresh iterations)

When this skill is invoked inside a Ralph or Ralphd loop iteration (detected by
`{specsDir}/.state/implement-preflight.json` existing — see Pre-flight section):

- Pre-flight data is already loaded from the JSON file (no python3 calls)
- Phase 0 and Phase 1 were already completed in the original interactive session
- Pick up from the next pending criterion in the state file
- Complete ONE iteration (one task or small batch), update `{specsDir}/.state/implement-state.md`, and exit
- The loop script handles the next iteration in a fresh context

The initial handoff from Phase 1 to the loop script is handled by the
"Ralph/Ralphd handoff gate" section above Phase 2. See
`references/external-integrations.md` for full details on how the loop scripts
work.

## Phase 3 — Judge review (final gate)

Spawn a sub-agent with the judge prompt from `references/judge-agent.md`.

The judge receives:

- The original spec (full text) or sketch content
- The acceptance criteria checklist from `{specsDir}/.state/implement-state.md`
- A summary of all files created or modified (`git diff --stat`, `find`, or
  `ls -la` on the relevant directories)
- The key implementation decisions made

The judge produces a structured verdict:

```text
VERDICT: PASS | PARTIAL | FAIL

For each acceptance criterion:
  AC-X: PASS | FAIL — <one-line explanation>

Overall notes:
  <any concerns, drift from spec, or suggestions>
```

If the judge says PASS, report completion to the user.

If the judge says PARTIAL or FAIL, extract the specific failures, fix them,
re-run the oracle pipeline, and re-submit to the judge. Limit: 2 judge
re-submissions. After that, report to the user with the judge's feedback.

See `references/implement-state-format.md` for the canonical `{specsDir}/.state/implement-state.md` structure.

See `references/git-usage.md` for git usage rules during implementation.

See `references/sub-agent-strategy.md` for sub-agent spawning strategy and test-writing heuristics.

See `references/error-recovery.md` for context reset recovery procedure.

## Reporting

When implementation is complete (or when stopping due to limits), report:

1. **What was built**: Files created/modified, brief summary of architecture
2. **Criteria status**: The final checklist from `{specsDir}/.state/implement-state.md`
3. **Iterations used**: How many loops it took
4. **Decisions made**: Any unknowns you resolved and how
5. **Branch status**: Which branch you're on, whether the user should review
   before merging (sketch implementations) or committing (feature implementations)
6. **Remaining work**: Anything not done, with explanation
