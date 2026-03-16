# Loops

Trellis is built from nested feedback loops. Each loop has a single responsibility, clear entry and exit conditions, and bounded iteration. Understanding how they nest — and where they don't — is the key to understanding how a feature goes from spec to working code.

## The nesting

```
Pipeline loop (pitch → spec → plan → build)
│
├── Clarify loop (0–3 passes, inside plan)
├── Compliance loop (0–2 passes, inside plan)
│
└── Build
    ├── Task loop (for each pending task)
    │   ├── Test-writer (conditional)
    │   ├── Builder
    │   ├── Check
    │   └── Retry (conditional, 1 attempt)
    │
    ├── Judge (once)
    │
    ├── Redefine loop (0–3 passes)
    │   └── Task loop → Judge → decide
    │
    └── Polish loop (once, optional)
        ├── Optimizer (creates 0–5 tasks)
        ├── Improver (creates 0–5 tasks)
        └── Task loop (final pass, no judge/redefiner)
```

Not all loops nest inside each other. Clarify and compliance are pre-steps of the plan skill, completely separate from the build loops. The pipeline loop (via `/run`) sequences the four stages but each stage is independent — the loops within plan don't know about the loops within build.

## Task loop

The innermost loop. Executes one task at a time from `tasks.json`.

**Cycle:** test → implement → check → done or retry → done or blocked

For each task where `status == "pending"`:

1. **Test-writer decision** — `should-write-tests.py` runs a keyword heuristic on the task's `verify` field. Behavioral tasks get tests; structural tasks skip. The test-writer is a separate LLM invocation that cannot see the implementation — it writes tests that must initially fail.

2. **Implementation** — The builder receives the task's `do` field, acceptance criteria, plan, guidelines, and a list of completed tasks. It writes code only — no orchestration, no state management.

3. **Check** — The check command runs on the host (not in Docker). A typical chain: `npm run lint && npm run typecheck && npm run build && npm test`. The `&&` chain provides stop-on-failure.

4. **Outcome** — Pass marks the task `done`. Fail triggers one retry where the builder sees the check output and is told to fix only those errors. Still failing after retry marks `blocked`. Either way, progress is committed to git and the loop advances to the next pending task.

**Exits when:** no pending tasks remain, or the per-run task limit is reached (default 10).

**Key property:** the task loop is stateless between tasks. Each task gets a fresh builder context (in ralph mode). The only shared state is `tasks.json` on disk and the git working tree.

## Judge

Not a loop — a single evaluation that runs once after the task loop completes. But it's a critical decision point that determines which loop runs next.

The judge evaluates intent alignment: did the implementation satisfy the spec? Not whether tasks were completed — whether the thing that was built matches the thing that was asked for. It receives the full spec, all task statuses, and a git diff stat. It outputs a verdict: `PASS`, `PARTIAL`, or `FAIL`, with per-criterion assessments.

**What happens after:**

- `PASS` with no blocked tasks → polish loop (or finish)
- `PARTIAL`, `FAIL`, or blocked tasks remain → redefine loop
- `--no-judge` → finish (also skips polish)

See [judge.md](judge.md) for the full evaluation model.

## Redefine loop

The outer feedback loop around the task loop and judge. When something goes wrong — tasks blocked, judge finds gaps — the redefiner diagnoses root causes and rewrites task definitions so a fresh attempt can succeed.

**Cycle:** task loop → judge → redefine → task loop → judge → ...

The redefiner categorizes each blocked task's failure:

- **Convention mismatch** — task described patterns that conflict with project conventions
- **Environment limitation** — Docker missing deps, permissions issues
- **Logic error** — genuine bug or spec mismatch
- **Test fragility** — non-deterministic behavior (timezones, DOM queries, ordering)

It rewrites each blocked task's `do` field with lessons learned: acknowledging files that already exist, encoding correct conventions explicitly, naming anti-patterns to avoid. If the judge identified gaps not covered by any task, it adds new tasks. All blocked tasks are reset to `pending`. Done tasks are never touched.

**Exits when:** judge says `PASS` with no blocked tasks, or 3 redefinition passes are exhausted. After 3 passes, remaining issues escalate to the user.

**Key property:** each pass through the redefine loop re-runs the full task loop and judge. The redefiner doesn't fix code — it fixes instructions. The builder in the next pass gets better instructions and starts fresh.

## Polish loop

A bounded refinement pass that runs after the build is functionally complete. Two review agents run sequentially, then any tasks they created execute in a single task loop pass.

**Sequence:** optimizer → improver → task loop (one pass)

### Optimizer

Reviews the finished implementation for localized performance and simplification. Creates up to 5 tasks. Hard constraints: no architectural changes, no new features, no schema changes. Appends §11 to plan.md.

### Improver

Reviews the implementation AND build logs — full check output per task, implementation logs, retry logs, judge verdict. Identifies robustness improvements based on evidence from the build process: code that required retries, edge cases revealed by failures, thin error handling. Creates up to 5 tasks. Sees the optimizer's additions to avoid duplication. Appends §12 to plan.md.

### Execution

If either agent created tasks, they execute through the standard task loop — same cycle of test → implement → check. But no judge or redefiner runs afterward. Polish is a single pass. Tasks either succeed or get marked blocked and stop.

**Exits when:** the single task pass completes. Always runs at most once.

**Key property:** polish is opt-out (`--no-polish`), not opt-in. It's also skipped if the judge was disabled, since the improver depends on the judge's verdict and build logs.

See [polish.md](polish.md) for details on how both agents work and how polish tasks re-use the task pipeline.

## Clarify loop

A pre-step of the plan skill that removes ambiguity from the spec before planning begins.

**Cycle:** scan for markers → resolve → re-scan → ...

The spec author writes `[? CATEGORY: question]` markers for decisions they couldn't make alone. The clarify skill (running in a forked context with no user interaction) resolves what it can from the spec and guidelines, and moves user-judgment items to §10 (Open Questions).

After each pass, `extract-markers.py` re-checks for remaining markers. If markers persist, clarify runs again.

**Exits when:** zero `[? ...]` markers remain in the spec body (all moved to §10), or 3 passes are exhausted.

**Key property:** clarify runs in a forked context — it cannot ask the user questions. This is intentional. The plan skill ensures any user context is embedded in the spec before invoking clarify. Items that genuinely require user judgment are deferred to §10, not blocked on.

## Compliance loop

A conditional pre-step of the plan skill that runs after clarify, if the spec handles sensitive data or jurisdictional constraints.

**Cycle:** evaluate regulations → recommend spec changes → re-run clarify → re-evaluate → ...

`pipeline-status.py` determines whether compliance is needed based on the spec's data model and constraints. If needed, the compliance skill evaluates the spec against applicable regulations (GDPR, FERPA, FIPPA, COPPA, SOC 2) and produces `compliance.md` with a requirement mapping, data flow concerns, and recommended spec changes.

If the compliance review recommends changes, those changes are applied to the spec, clarify re-runs on the modified sections, then compliance re-evaluates.

**Exits when:** no recommended spec changes remain, or 2 loops are exhausted. Remaining gaps are documented as residual risks in compliance.md.

**Key property:** like clarify, compliance runs in a forked context. The plan skill is responsible for ensuring all regulation context the user provided is embedded in §9 (Constraints) before compliance runs.

## Pipeline loop

The outermost loop, orchestrated by `/trellis:run`. It sequences the four stages — pitch → spec → plan → build — with a review gate after each document stage.

This isn't a feedback loop in the same sense as the others. It's a linear pipeline with human checkpoints. After each stage produces its artifact, the user can:

- **Approve** — continue to the next stage
- **Edit** — revise the artifact and re-run the stage
- **Redo** — discard and regenerate

The pipeline also supports resume. If interrupted, `/run` checks which artifacts exist and picks up from the next incomplete stage. `tasks.json` serves as the resume point for the build stage — the task loop reads it and starts from the first pending task.

**Key property:** the pipeline loop is the only loop with a human in it. Every other loop is fully automated with bounded iteration. The pipeline loop is unbounded — the user decides when to move forward.

## Ralph vs in-session

Both modes execute the same loops, but ralph mode has fuller automation:

| Loop | In-session | Ralph |
|------|-----------|-------|
| Task loop | Orchestrated by SKILL.md in conversation | Orchestrated by `ralph-loop.sh`, each task in fresh Docker context |
| Judge | Agent spawned in conversation | Docker invocation, verdict extracted from log |
| Redefine | Up to 2 re-submissions | Up to 3 automated passes |
| Polish | Not available | Optimizer + improver + final task pass |
| Clarify | Runs as plan pre-step | Same |
| Compliance | Runs as plan pre-step | Same |

The key difference in ralph mode: each LLM invocation gets a fresh context window. Prompts are assembled from templates by `assemble-prompt.py` with all context pre-baked. No skill loading, no orchestration instructions inside the container. The check command runs on the host, using the host's toolchain. Docker is the security boundary.

## Why bounded iteration matters

Every automated loop has a hard limit:

| Loop | Max iterations | Escalation |
|------|---------------|------------|
| Task loop | 10 per run (configurable) | Continues in next run |
| Redefine | 3 passes | Escalates to user |
| Polish | 1 pass | Stops |
| Clarify | 3 passes | Remaining markers moved to §10 |
| Compliance | 2 loops | Remaining gaps documented as residual risks |

Without bounds, any feedback loop can cycle indefinitely — especially when LLMs are generating both the work and the evaluation. The bounds are conservative. Three redefinition passes is usually enough to surface whether a problem is solvable with better instructions or requires human judgment. One polish pass prevents the optimizer and improver from chasing diminishing returns.

When a loop hits its limit, it doesn't fail silently. It produces a durable artifact (§10 open questions, residual risks, blocked task status) that tells the user exactly where automation stopped and why. The human picks up where the loop left off.
