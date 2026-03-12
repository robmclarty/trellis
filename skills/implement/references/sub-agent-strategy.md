# Sub-Agent Strategy

Spawn sub-agents to keep the main agent's context focused:

1. **Test writer** — Produces test files from spec criteria. Runs in isolation.
   Canonical definition: `agents/test-writer/agent.md`. Usage guide: `references/test-writer-agent.md`.
2. **Judge** — Reviews implementation against spec. Runs in isolation.
   Canonical definition: `agents/judge/agent.md`. Usage guide: `references/judge-agent.md`.
3. **Task implementor** (optional, for parallel work) — When tasks within a
   phase are marked `[parallel]` in tasks.md, you may spawn sub-agents to
   implement independent tasks concurrently. Each sub-agent receives:
   - The specific task(s) to implement
   - Relevant plan.md sections
   - Relevant spec.md sections
   - The project guidelines
   - The file structure from plan.md §6

   The main agent coordinates: it spawns the sub-agents, collects their output,
   writes files to disk, then runs the oracle pipeline against all changes.

Sub-agents do NOT share context with each other or with the main agent's
conversation history. They receive only what is explicitly passed to them.

## When to write tests

Tests are not the default starting point. Write tests when:

- `tasks.md` includes a task whose "Verify" requires running code
- `spec.md` §8 defines test scenarios as acceptance criteria
- The logic involves tricky edge cases that type-checking and linting won't catch
  (date math, permission logic, state machines, parsing)
- You need a regression guard for a bug fixed during iteration
- The criterion is behavioral and can't be verified by the judge alone

When tests are warranted, use the test writer sub-agent. Tests encode the spec's
intent, not the implementation's behavior.
