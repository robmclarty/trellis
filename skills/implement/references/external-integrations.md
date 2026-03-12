# External Integrations

The implement skill can optionally integrate with external tools. These are
**not bundled with Trellis** — they are separate tools the user installs
independently. The implement skill detects their availability through the
Phase 0 configuration questions.

## Ralph

**What it is:** A CLI tool that provides context-resilient iteration for
long-running Claude Code sessions. It kills and restarts the agent's context
window at iteration boundaries, using a state file as the handoff mechanism.

**Where to find it:** [github.com/anthropics/ralph](https://github.com/anthropics/ralph)

**How it integrates:** When Ralph mode is enabled in Phase 0:
- The implement skill writes all progress to `.implement-state.md` at each
  iteration boundary
- Ralph manages the context lifecycle: kill → restart → resume
- On restart, the skill reads `.implement-state.md` and resumes from the next
  pending criterion

**Invocation:** `ralph run --state .implement-state.md --command "/trellis:implement <feature-name>"`

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
