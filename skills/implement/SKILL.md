---
name: trellis:implement
description: Executes implementation from spec-driven artifacts or freeform instructions through iterative oracle-driven feedback loops until all acceptance criteria are met.
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent
---

## When to use

- "implement this", "build this", "/implement"
- Passing a feature folder, sketch name, or inline instructions expecting working code
- After completing the spec pipeline and wanting to move from planning to execution
- Supports Ralph mode, Open Spec format, and Promptfoo for repeatable evaluations

# Implement

Turn specifications, sketches, or freeform instructions into working code through
iterative oracle-driven feedback loops. The input artifacts are the source of truth.

**Recommended effort: high.** Multi-phase coordination with oracle-driven feedback loops and error recovery.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py implement <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

If `.implement-state.md` exists, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/parse-implement-state.py` to get structured state data for resumption.

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-criteria.py <specs-dir>/<feature-name>/tasks.md <specs-dir>/<feature-name>/spec.md` to get structured acceptance criteria.

A pipeline of machine-readable checks is the termination signal. An LLM judge
verifies alignment with intent.

Read `references/oracle-pipeline.md` before starting any implementation. It
contains the full mechanics of the feedback loop, the judge sub-agent prompt, and
notes on integration with external tools like Ralph and Promptfoo. See
`references/external-integrations.md` for details on what these tools are, where
to find them, and how they integrate with the implement skill.

## Invocation

```
/implement <input>
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

Read `references/config-questions.md` for the full list of configuration questions to ask.

### Steps 3–5: Analyze inputs, branch management, and summary

Read `references/phase-zero-analysis.md` for the detailed process of building the acceptance criteria checklist, managing branches for sketch implementations, and presenting the summary for user confirmation.

## Phase 1 — Oracle pipeline assembly

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

Write the assembled pipeline to `.implement-state.md`.

The pipeline is not fixed. If the user's project needs stages not listed here
(e.g., a migration check, an MCP manifest validation, a Docker build), add them.
The user's tooling answers are the authority.

## Phase 2 — Implement and iterate

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

If multiple sources conflict, flag the conflict in `.implement-state.md` and
follow the most specific source (tasks > plan > spec > guidelines).

### Step 3: Run the oracle pipeline

Execute each enabled stage in order. Stop at the first failure.

```
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
`.implement-state.md`:
- Mark completed criteria as `done`
- Record which iteration completed them
- If working from tasks.md, check the task checkbox
- Note any new unknowns that surfaced

### Step 5: Check termination

If all acceptance criteria are `done`, proceed to Phase 3.
If criteria remain, return to Step 1 for the next iteration.

**Global iteration limit: 10.** If you hit 10 iterations without completing all
criteria, stop and report what's done, what's remaining, and why you stalled.

### Ralph mode iteration (when enabled)

When the user enables Ralph mode, the iteration loop changes. Instead of running
all iterations in a single context, each iteration (or small batch) uses a fresh
context via Ralph:

```bash
# Ralph handles the context reset. The implement skill writes state to disk,
# Ralph kills the context, restarts, and the skill resumes from .implement-state.md.

ralph run --state .implement-state.md --command "/implement <feature-name>"
```

The `.implement-state.md` file is the handoff mechanism. On each fresh context:

1. Read `.implement-state.md`
2. Read the spec/plan/tasks from the recorded paths
3. Check which criteria are done vs. pending
4. Re-run the oracle pipeline to validate current state
5. Resume from the next pending criterion

Use Ralph mode for large implementations (10+ acceptance criteria, many files).
For small implementations (2-3 criteria), the overhead of context resets isn't
worth it.

## Phase 3 — Judge review (final gate)

Spawn a sub-agent with the judge prompt from `references/judge-agent.md`.

The judge receives:
- The original spec (full text) or sketch content
- The acceptance criteria checklist from `.implement-state.md`
- A summary of all files created or modified (`git diff --stat`, `find`, or
  `ls -la` on the relevant directories)
- The key implementation decisions made

The judge produces a structured verdict:

```
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

See `references/implement-state-format.md` for the canonical `.implement-state.md` structure.

See `references/git-usage.md` for git usage rules during implementation.

See `references/sub-agent-strategy.md` for sub-agent spawning strategy and test-writing heuristics.

See `references/error-recovery.md` for context reset recovery procedure.

## Reporting

When implementation is complete (or when stopping due to limits), report:

1. **What was built**: Files created/modified, brief summary of architecture
2. **Criteria status**: The final checklist from `.implement-state.md`
3. **Iterations used**: How many loops it took
4. **Decisions made**: Any unknowns you resolved and how
5. **Branch status**: Which branch you're on, whether the user should review
   before merging (sketch implementations) or committing (feature implementations)
6. **Remaining work**: Anything not done, with explanation
