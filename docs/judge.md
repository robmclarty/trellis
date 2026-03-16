# Judge

The judge is a specification compliance reviewer that runs after all build tasks complete. Its job is to answer one question: _did the implementation satisfy the spec?_ Not whether the code is clean, not whether the tasks were completed — whether the thing that was built matches the thing that was asked for.

## Why the judge exists

Task completion is not the same as spec compliance. A builder can mark every task done and still produce something that drifts from the spec's intent. Tasks are an approximation of the spec — they break it into implementable units, but the decomposition can lose nuance, misinterpret constraints, or miss interactions between requirements. The judge closes this gap by evaluating the finished implementation directly against the spec's acceptance criteria.

The judge is also deliberately separated from the builder. It did not write the code. It has no investment in defending it. This separation is the point — the judge's only loyalty is to the spec.

## What the judge receives

The judge gets three inputs, assembled by `assemble-prompt.py` from the feature's spec artifacts:

1. **The full spec** (`spec.md`) — the source of truth for what should have been built, including all acceptance criteria and constraints.

2. **All tasks with status** — every task from `tasks.json` with its current status (done, blocked, or pending) and its `verify` field. This tells the judge what was attempted and what succeeded.

3. **A git diff stat** — the output of `git diff --stat`, showing which files were created or modified and how much changed. This gives the judge a scope map without requiring it to read every file.

The judge can also inspect the codebase directly using Read, Glob, and Grep. If the diff stat or task status isn't sufficient to determine whether a criterion was met, the judge reads the actual implementation.

## How the judge evaluates

For each acceptance criterion in the spec, the judge:

1. Determines whether the described changes plausibly satisfy it
2. Inspects code directly if the task status alone is ambiguous
3. Checks that the implementation respects stated constraints
4. Flags scope creep — work that wasn't asked for
5. Flags intent drift — code that is technically correct but misses the spirit of the requirement

## Output format

The judge produces a structured verdict:

```
VERDICT: PASS | PARTIAL | FAIL

CRITERIA:
- 1.1: PASS — User authentication redirects to login page
- 1.2: FAIL — Session timeout not implemented, spec requires 30-minute expiry
- 1.3: PASS — Role-based access enforced on all protected routes

CONSTRAINT COMPLIANCE:
- No violations found

SCOPE NOTES:
- Builder added a "remember me" checkbox not mentioned in spec

RECOMMENDATIONS:
- Implement session timeout per spec §4.2
- Remove or flag "remember me" feature for separate spec
```

**Verdict meanings:**

- **PASS** — all acceptance criteria satisfied, no constraint violations, implementation is complete
- **PARTIAL** — some criteria met, some not; the build is on track but has gaps
- **FAIL** — significant issues, possibly architectural; the implementation has fundamental problems

Each criterion also gets an individual assessment: PASS, FAIL, or UNCLEAR (when the judge can't determine compliance from available information).

## Where the judge sits in the pipeline

```
Task loop ──▶ Judge ──▶ Redefiner (if needed) ──▶ Polish (if complete)
                │              │
                │         rewrites blocked
                │         tasks, loops back
                │              │
                ▼              ▼
            PASS with      PARTIAL/FAIL
            no blocked     or blocked tasks
                │
                ▼
            polish or
              finish
```

The judge runs once after the task loop exhausts all pending tasks. What happens next depends on the verdict and the state of the tasks:

- **PASS with no blocked tasks** — build is functionally complete. Proceed to the polish phase (or finish if polish is disabled).
- **PARTIAL or FAIL, or blocked tasks remain** — the redefiner agent diagnoses what went wrong, rewrites blocked task definitions, and the loop re-executes. The judge runs again after the next task loop. This can happen up to 3 times before escalating to the user.

## The judge-redefiner feedback loop

The judge's verdict feeds directly into the redefiner. When the verdict is PARTIAL or FAIL, or tasks are blocked, the redefiner receives:

- The full judge output (verdict + per-criterion assessments + recommendations)
- Diagnostic logs for each blocked task (check output, implementation logs)
- The current tasks.json
- The spec and guidelines

The redefiner uses the judge's criterion-level assessments to understand _what_ failed, and the build logs to understand _why_. It rewrites blocked task `do` fields with lessons learned and adds new tasks for gaps the judge identified that no existing task covers. Blocked tasks are reset to pending, and the task loop runs again.

Each pass through this loop increments `redefinitionPass` in tasks.json. After 3 passes, the system stops and reports remaining issues to the user rather than continuing indefinitely.

## In-session vs ralph mode

**In-session mode** — the build skill invokes the judge agent within the user's conversation. The user sees the verdict directly. If PARTIAL or FAIL, the builder gets up to 2 re-submission attempts before reporting to the user with the judge's feedback.

**Ralph mode** — `ralph-loop.sh` orchestrates the judge as a Docker invocation. The prompt is assembled from `scripts/templates/judge.txt`, the judge runs in a fresh context, and the verdict is extracted from the log via `grep -m1 'VERDICT:'`. The judge output is always displayed to the user regardless of output mode (stream, tail, or silent). The redefiner loop is fully automated.

## Configuration

- **Default:** on. The `judge` field in tasks.json defaults to `true`.
- **Opt out:** `--no-judge` flag on the build command. This also implicitly disables the polish phase, since polish depends on the judge's verdict and build logs.
- **Model:** the judge agent runs on Opus for analytical depth. Unlike the generation agents (pitcher, specifier, planner) which run on Sonnet for cost efficiency, the judge needs to reason carefully about spec compliance.

## What the judge is not

The judge is not a code reviewer. It doesn't evaluate code quality, style, performance, or maintainability — those concerns belong to the polish phase's optimizer and improver agents. The judge evaluates one thing: did the implementation do what the spec said it should do?

The judge is also not a test runner. It doesn't execute the code or run the check command. The check command already ran during the task loop. The judge operates at a higher level — reading the spec's acceptance criteria and determining whether the implementation satisfies them, using code inspection when needed.
