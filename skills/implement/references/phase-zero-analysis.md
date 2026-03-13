# Phase 0: Input analysis, branch management, and summary

## Step 3: Analyze inputs and build checklist

Read all loaded artifacts fully, then extract into a structured checklist written
to `{specsDir}/.state/implement-state.md`:

**a) Acceptance criteria.** Sourced from:
- `tasks.md` — Each task's "Verify" section becomes a criterion.
- `spec.md` §8 (Success Criteria) — Each scenario becomes a criterion.
- Sketch verdicts — If implementing a sketch, the hypothesis itself is the
  criterion ("does this approach work?").
- Inline text — Extract anything that describes "done."

For each criterion, determine:
- A short identifier (e.g., `AC-1`, `AC-2`, or the task ID like `1.1`, `1.2`)
- A one-line summary
- Whether it's machine-verifiable (a script can check it) or judgment-based
  (needs the LLM judge)
- Status: `pending`

**b) Constraints.** Sourced from:
- `plan.md` §3 (Technology Decisions) — locked-in choices
- `spec.md` §9 (Constraints) — scope, technical, and operational limits
- `compliance.md` — regulatory constraints
- `guidelines.md` — project-wide conventions
- User's inline overrides

**c) Unknowns.** Anything ambiguous or unaddressed. If a `spec.md` still has
`[? ...]` markers or §10 has open questions, list them. If a sketch verdict is
"inconclusive" or "viable with caveats," surface the caveats.

If the input is too vague to extract any acceptance criteria, stop and ask the
user to clarify before proceeding.

## Step 4: Branch management (sketch implementations only)

When implementing from sketch files:

```bash
# Record the current branch
originalBranch=$(git branch --show-current)

# Create and switch to a new branch named after the sketch
git checkout -b sketch/<sketch-slug>
```

Store `originalBranch` in `{specsDir}/.state/implement-state.md` under `## Branch`. When
implementation is complete (or abandoned), report to the user but do NOT switch
back to the original branch automatically. The user decides when to merge,
rebase, or discard.

For feature folder implementations, do NOT create a branch unless the user
explicitly asks. Work on whatever branch is currently checked out.

## Step 5: Print summary and confirm

Present to the user before writing any code:
- Input source(s) identified (feature folder, sketch names, inline)
- How many acceptance criteria were extracted
- Which are machine-verifiable vs. judgment-based
- The oracle pipeline stages that will run, with the exact commands
- Branch status (if a new branch was created)
- Any unknowns or assumptions being flagged
- Ask for confirmation to proceed
