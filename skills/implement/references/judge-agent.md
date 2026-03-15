# Judge Sub-Agent

> **Note:** The canonical agent definition lives at `agents/judge/agent.md`. This reference documents usage from the implement skill's perspective.

The judge is the final gate after all tasks complete. It evaluates *intent alignment* — whether the implementation satisfies what the spec asked for, not just whether the code runs or tests pass.

## When to invoke

- After all tasks in tasks.json are processed (default, opt-out with `--no-judge`)
- The judge does NOT run per-task — it runs once at the end

## What the judge receives

The judge runs in an isolated context. Compose a message containing:

```markdown
## Specification
<paste spec.md content>

## Tasks and Status
<for each task in tasks.json, show: status, id, title, verify>

## Changes Made
<git diff --stat output showing all files created/modified>
```

In ralph mode, the loop script assembles this via `assemble-prompt.py judge <feature>` and the `templates/judge.txt` template.

In in-session mode, the implement skill composes the message directly.

## Interpreting judge output

The judge responds with:

```text
VERDICT: PASS | PARTIAL | FAIL

CRITERIA:
- 1.1: PASS | FAIL | UNCLEAR — <one-line explanation>
...

CONSTRAINT COMPLIANCE:
- <any violations>

SCOPE NOTES:
- <scope creep or missing scope>

RECOMMENDATIONS:
- <actionable items if PARTIAL or FAIL>
```

- **PASS:** Implementation complete. Report to user.
- **PARTIAL:** Fix specific issues, re-run check, re-submit to judge. Limit: 2 re-submissions.
- **FAIL:** Significant issues. If architectural, stop and report to user.

## Re-submission limits

2 re-submissions after PARTIAL or FAIL. After that, report to the user with the judge's feedback.
