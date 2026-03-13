# External Integrations

The implement skill can optionally integrate with external tools. Some are
bundled with Trellis, others are separate tools the user installs
independently. The implement skill detects their availability through
invocation modifiers or Phase 0 configuration questions.

## Ralph

**What it is:** A bundled loop script (`scripts/ralph-loop.sh`) that provides
context-fresh iteration for large implementations. Based on Geoffrey Huntley's
Ralph Wiggum methodology — each iteration runs in a fresh Claude Code context
window to avoid context degradation.

**How to use:** `/implement <feature> with ralph`

**How it works:** When `with ralph` is specified:
1. Phase 0 and Phase 1 run interactively in the current session (config
   questions, pipeline assembly, criteria extraction)
2. After `.implement-state.md` is written, the skill launches
   `scripts/ralph-loop.sh <feature-name>`
3. The loop script runs `claude -p` with `/trellis:implement <feature-name>`
   in each iteration
4. Between iterations, it parses `.implement-state.md` to check completion
5. Each iteration resumes from the next pending criterion via the state file
6. The loop stops when: all criteria pass, max iterations reached (default 10),
   or 3 consecutive failures occur without progress

**When to use:** Large implementations (10+ acceptance criteria, many files)
where context degradation is a concern. Skip for small implementations (2-3
criteria).

## Promptfoo

**What it is:** An eval framework for LLM outputs that supports assertions,
model comparison, and repeatable test suites.

**Where to find it:** [promptfoo.dev](https://www.promptfoo.dev/) — Install
via `npm install -g promptfoo`

**How it integrates:** When Promptfoo is enabled in Phase 0:
1. The implement skill generates a `promptfoo.yaml` config from acceptance
   criteria during Phase 1
2. `promptfoo eval` runs as an additional pipeline stage (after tests, before
   or alongside the judge)
3. Results are stored for the user to review

**When to use:** Teams that build similar features often and want to codify
judge criteria as repeatable evals, A/B test prompts, or run regression checks.

## Open Spec

**What it is:** A structured requirements format designed for agentic
interpretation, with machine-parseable fields like `validation_criteria`,
`constraints`, and `scope`.

**Where to find it:** [github.com/open-spec/open-spec](https://github.com/open-spec/open-spec)

**How it integrates:** If the spec uses Open Spec format (detected
automatically or indicated by the user in Phase 0), the implement skill uses
its structured fields directly rather than extracting criteria from prose.
This gives more reliable acceptance criteria extraction and explicit scope
boundaries.

**When to use:** Projects that have adopted Open Spec as their requirements
format. Pairs well with Ralph for context-resilient implementation.
