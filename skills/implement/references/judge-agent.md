# Judge Sub-Agent

> **Note:** The canonical agent definition lives at `agents/judge/agent.md`. This reference documents usage from the implement skill's perspective.

This file defines the sub-agent that reviews implementation work against the
original specification. The judge is the final gate in the oracle pipeline and
the only stage that evaluates *intent alignment* rather than structural
correctness.

## When to invoke the judge

- After the full oracle pipeline passes for a given iteration (for incremental
  judgment on whether you're on track)
- In Phase 3 as the final gate (required)
- When you're unsure whether a design decision aligns with the spec's intent

The judge is not a replacement for the earlier pipeline stages. It assumes the
code already compiles, lints, and builds. It's checking whether what you built
is what the spec *asked* for, not whether the code runs.

## What the judge receives

The judge runs in an isolated context window. It does not share the
implementation conversation's history. It receives only what you explicitly
pass to it.

Compose a message containing exactly these sections:

```markdown
## Source Artifacts
<paste the relevant content here — this varies by input type:
  - Feature folder: paste spec.md (or the relevant sections) and
    the current task(s) from tasks.md
  - Sketch: paste the full sketch content
  - Inline: paste the original instructions>

## Acceptance Criteria Checklist
<paste the current checklist from .claude/.implement-state.md>

## Changes Made
<summary of files created or modified with brief notes about each file's
purpose. `git diff --stat` works well here for an overview. Alternatively,
use `find` or `ls -la` output on the relevant directories.>

## Key Decisions
<any assumptions, tradeoffs, or interpretations you made where the input
was ambiguous>

## Specific Questions (optional)
<if you want the judge to evaluate something specific, ask here>
```

Keep the message focused. If the spec is long and the iteration only touches a
subset of criteria, trim to the relevant sections but always include the full
acceptance criteria checklist so the judge can see overall progress.

If the judge returns UNCLEAR verdicts because it can't tell what changed from
a file listing alone, re-submit with actual code snippets for the ambiguous
criteria.

## Judge system prompt

Use this as the system prompt when spawning the judge sub-agent:

```
You are a specification compliance reviewer. Your job is to determine whether
an implementation satisfies a given specification.

You are not the implementor. You did not write this code. You have no
investment in defending it. Your job is to find gaps, drift, and
misinterpretation.

You may be reviewing against a full spec with tasks, a lightweight sketch,
or freeform instructions. Regardless of the input format, evaluate whether
the described changes satisfy the stated acceptance criteria.

For each acceptance criterion in the checklist:
1. Determine whether the described changes plausibly satisfy it
2. If you can't tell from the file listing alone, say so — don't assume
3. Check that the implementation respects stated constraints
4. Flag any scope creep (work done that the input didn't ask for)
5. Flag any intent drift (implementation that technically satisfies the
   letter of a criterion but misses the spirit)

Respond in this exact format:

VERDICT: PASS | PARTIAL | FAIL

CRITERIA:
- AC-1: PASS | FAIL | UNCLEAR — <one-line explanation>
- AC-2: PASS | FAIL | UNCLEAR — <one-line explanation>
...

CONSTRAINT COMPLIANCE:
- <any constraint violations or concerns>

SCOPE NOTES:
- <any scope creep or missing scope>

RECOMMENDATIONS:
- <specific, actionable items if PARTIAL or FAIL>

Be terse. Do not praise the implementation. Focus only on gaps and risks.
```

## Interpreting judge output

- **PASS:** All criteria satisfied, no constraint violations. Proceed to
  completion.
- **PARTIAL:** Some criteria met, some not. Extract the FAIL/UNCLEAR items
  from the CRITERIA list, treat them as remaining work, and iterate.
- **FAIL:** Significant issues. Read the RECOMMENDATIONS carefully. If the
  judge flags fundamental architectural misalignment, pause and report to
  the user rather than trying to patch it.
- **UNCLEAR:** The judge couldn't determine compliance from the information
  provided. This usually means you need to give it more detail (actual code
  snippets, not just file names).

## Re-submission limits

If the judge returns PARTIAL or FAIL, fix the specific issues, re-run the
oracle pipeline, and re-submit. Limit: 2 re-submissions. After that, report
to the user with the judge's feedback and let them decide.

If the judge returns UNCLEAR on specific criteria across multiple submissions,
that's a signal the criterion itself is ambiguous. Flag it as an unknown in
`.claude/.implement-state.md` and report it rather than guessing.

## What the main agent does with the output

1. Parse the VERDICT line to determine pass/fail
2. For each criterion marked FAIL or UNCLEAR, add the judge's explanation to
   the iteration log in `.claude/.implement-state.md`
3. If PARTIAL: return to Phase 2 with the failing criteria as the next
   iteration's scope
4. If PASS: report completion to the user
5. If FAIL with architectural concerns: stop and report — don't try to patch
   a fundamental misalignment

## Example: submitting to the judge (feature folder)

```markdown
## Source Artifacts

### From spec.md
A REST endpoint that allows teachers to create hall passes for students.
The endpoint validates that the teacher has permission for the requested
room, that the student doesn't already have an active pass, and that the
pass type hasn't expired. Returns the created pass with a UUID and
timestamp.

### From tasks.md (current scope)
- Task 2.1: Implement room permission check
- Task 2.2: Implement active pass validation

## Acceptance Criteria Checklist
- [x] AC-1 (task 1.1): POST /api/passes creates a pass and returns 201 (done, iteration 1)
- [x] AC-2 (task 2.1): Rejects request if teacher lacks room permission (done, iteration 2)
- [x] AC-3 (task 2.2): Rejects request if student has active pass (done, iteration 2)
- [ ] AC-4 (task 2.3): Rejects request if pass type is expired (pending)

## Changes Made
src/routes/passes.ts          — POST handler with validation pipeline
src/services/passService.ts   — Business logic for pass creation
src/services/permissions.ts   — Room permission check using auth module

## Key Decisions
- Used a service layer between route and database rather than inline queries
- Permission check calls an existing hasRoomAccess() function from the
  auth module rather than re-implementing
- "Active pass" defined as: status === 'active' AND endTime > now()

## Specific Questions
- AC-3 defines "active pass" but the spec doesn't say what happens if the
  student has a pass with status 'paused'. I treated paused as not-active.
  Is that correct?
```

## Example: submitting to the judge (sketch)

```markdown
## Source Artifacts

### From sketch: drizzle-multi-tenant
Hypothesis: Drizzle can handle multi-tenant schema isolation using
Postgres RLS without custom query wrappers.

Method: Built a small prototype with two tenants, applied RLS policies,
tested CRUD operations through Drizzle's query builder.

## Acceptance Criteria Checklist
- [x] AC-1: Drizzle queries respect RLS policies without manual tenant filtering (done, iteration 1)
- [x] AC-2: Tenant A cannot read Tenant B's data through any Drizzle query path (done, iteration 2)
- [ ] AC-3: Performance overhead of RLS is under 10% vs. unprotected queries (pending)

## Changes Made
src/db/schema.ts         — Table definitions with tenant_id columns
src/db/rls.ts            — RLS policy application helper
src/db/connection.ts     — Connection pool with tenant context setting
test/rls.test.ts         — Integration tests for tenant isolation

## Key Decisions
- Set tenant context via SET LOCAL at transaction start rather than
  per-query parameters
- Used a connection pool per tenant rather than a shared pool with
  session variables
```
