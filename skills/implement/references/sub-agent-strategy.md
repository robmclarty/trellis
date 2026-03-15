# Sub-Agent Strategy

Two sub-agents support the implement skill:

1. **Test writer** — Writes failing tests before implementation (TDD). Runs per task.
   Canonical definition: `agents/test-writer/agent.md`. Usage guide: `references/test-writer-agent.md`.
2. **Judge** — Reviews full implementation against spec for intent alignment. Runs once at the end.
   Canonical definition: `agents/judge/agent.md`. Usage guide: `references/judge-agent.md`.

Sub-agents do NOT share context with each other or with the main agent's conversation history. They receive only what is explicitly passed to them.

## Test writer: when to spawn

The test-writer runs for each task where the `verify` field describes behavioral expectations. Use the `should-write-tests.py` script for deterministic classification, or evaluate manually:

**Spawn for:**

- Behavioral criteria: "rejects invalid input", "returns error when..."
- Edge cases: boundaries, limits, empty inputs, concurrent access
- Stateful logic: state transitions, expiration, deactivation
- Permission logic: different behavior by role

**Skip for:**

- Structural criteria: "file exists", "scaffold created", "config set"
- Compilation checks: "compiles clean", "no type errors"
- Schema matching: "schema matches spec exactly"

## Judge: when to spawn

The judge runs once after all tasks complete (default, opt-out with `--no-judge`). It does not run per-task. The judge evaluates intent alignment — did you build what the spec asked for, not just what the tasks described.

In ralph mode, the loop script handles judge invocation after the task loop completes. In in-session mode, the implement skill spawns it directly.
