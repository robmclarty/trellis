# Polish Phase

The polish phase is an automated review-and-improve pass that runs after a build is functionally complete. Two agents — the **optimizer** and the **improver** — examine the finished implementation, identify targeted improvements, and create new tasks that execute through the same task pipeline used during the build itself.

## Why polish exists where it does

The build pipeline has a natural completion point: the judge has evaluated the implementation against the spec, and either everything passed or the redefinition loop exhausted its attempts. At this point the code is _functionally correct_ — it does what the spec asked for. But functional correctness isn't the whole picture.

Builders working under task-scoped constraints tend to produce code that works but doesn't reflect the full picture. A builder implementing task 2.3 doesn't revisit task 1.1's approach even if it's now obviously redundant. Retry cycles during the build may have papered over fragile patterns rather than addressing root causes. These are the kinds of issues that a human reviewer would catch in a code review — and that's exactly what the polish phase automates.

Polish runs _after_ the judge rather than before it because the judge's verdict and the build logs are inputs to the improver. The judge tells you what's misaligned with intent; the build logs tell you what was fragile in practice. Neither signal exists until the build is done.

## The two agents

### Optimizer

The optimizer reviews the finished code for localized performance and simplification opportunities across four categories:

- **Function-level simplification** — unnecessary complexity, verbose logic, redundant branches
- **Redundant computation** — repeated calculations, unnecessary transforms
- **Component efficiency** — unnecessary re-renders, missing memoization
- **Cross-module interactions** — chatty interfaces, redundant serialization, batching opportunities

Hard constraints: no architectural changes, no new features, no schema changes, no API restructuring. Maximum 5 tasks. The optimizer can create zero tasks if the implementation is already clean.

### Improver

The improver reviews the implementation _and_ the build logs to identify robustness improvements based on evidence from the build process:

- **Fragile patterns** — code that required retries during the build, suggesting brittleness
- **Edge case gaps** — situations the builder encountered that revealed missing handling
- **Error handling completeness** — thin catch blocks, swallowed errors, generic error paths
- **Robustness patterns** — missing input validation, boundary conditions, defensive checks

The improver runs after the optimizer and reads the updated tasks.json, so it won't duplicate optimizer tasks. It also receives the judge's verdict and a summary of all build logs — full check output per task, plus the last 30 lines of implementation and retry logs.

Hard constraints: stays within spec scope, no new features, no overlap with optimizer tasks. Maximum 5 tasks.

## How polish re-uses the task pipeline

Polish tasks are structurally identical to regular build tasks. They use the same schema, the same execution path, and the same check command. The only addition is a `source` field for traceability:

```json
{
  "id": "4.1",
  "phase": 4,
  "title": "Simplify response serialization",
  "do": "In src/api/serializer.ts, serializeResponse() calls JSON.stringify twice per request. Combine into a single pass.",
  "verify": "All existing tests pass. No functional changes to response format.",
  "parallel": false,
  "status": "pending",
  "iteration": null,
  "source": "optimizer"
}
```

The `source` field is either `"optimizer"` or `"improver"`. Regular build tasks don't have this field.

Phase numbering continues from where the original build left off. If the build had phases 1–3, optimizer tasks become phase 4 and improver tasks become phase 5. The improver sees the optimizer's additions in tasks.json and adjusts its phase numbering accordingly.

Once both agents have written their tasks, the ralph loop calls the same `execute_pending_tasks()` function used during the main build. Each pending polish task goes through the same cycle: optionally write tests, implement, run check, mark done or blocked. The test-writer heuristic (`should-write-tests.py`) applies to polish tasks the same way it applies to build tasks — behavioral tasks get tests, structural tasks skip them.

The key difference: **no judge or redefiner runs after polish tasks**. Polish is a single pass. Tasks either succeed or get marked blocked and stop. This prevents an infinite improvement loop — the build is already functionally complete, and polish is a bounded refinement.

## Plan documentation

Both agents append sections to plan.md documenting what they added:

- **§11 — Optimization Additions** — written by the optimizer, listing each task and its rationale
- **§12 — Improvement Additions** — written by the improver, listing each task with references to log evidence

Both sections are always written, even when no tasks are created. An empty section reads "No optimizations identified" or "No improvements identified" rather than being omitted. This makes it unambiguous whether the agent ran.

## Orchestration in ralph mode

Polish is orchestrated entirely by `ralph-loop.sh`. The build skill is not invoked inside Docker for polish — like the rest of ralph mode, the loop script assembles prompts from templates and sends them to `claude -p` directly.

The sequence:

1. **Optimizer prompt assembly** — `assemble-prompt.py optimizer` resolves `{{tasks_json_raw}}`, `{{plan}}`, `{{spec_excerpt}}`, `{{guidelines}}`, and `{{tasks_summary}}` into `scripts/templates/optimizer.txt`
2. **Optimizer runs in Docker** — fresh context, reads implementation, writes tasks.json and plan.md §11
3. **JSON validation** — ralph loop validates that tasks.json is still valid JSON; if not, polish aborts gracefully
4. **Improver prompt assembly** — `assemble-prompt.py improver` resolves the same variables plus `{{judge_verdict}}` and `{{all_logs_summary}}`
5. **Improver runs in Docker** — fresh context, reads implementation + logs, writes tasks.json and plan.md §12
6. **JSON validation** — same check
7. **Task execution** — if any pending tasks exist, `execute_pending_tasks()` runs them through the standard pipeline
8. **Commit** — polish results are committed

If either agent produces invalid JSON in tasks.json, the polish phase aborts and the build completes with original results. The user sees the build output without polish rather than a corrupted state.

## When polish doesn't run

- **`--no-polish` flag** — explicitly opted out
- **`--no-judge` flag** — polish depends on the judge's verdict and build logs, so skipping the judge implicitly skips polish
- **In-session mode** — polish is ralph-mode only; interactive builds don't run it

## Status tracking

During polish, `status.json` updates its `currentPhase` field to `"optimizing"` and then `"improving"`, so `--tail` and `--stream` output modes can show progress. Logs are written to `logs/ralph-<feature>/optimizer.log` and `logs/ralph-<feature>/improver.log`.
