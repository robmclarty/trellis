# Test Writer Sub-Agent

> **Note:** The canonical agent definition lives at `agents/test-writer/agent.md`. This reference documents usage from the implement skill's perspective.

The test-writer produces failing tests before implementation code exists (TDD). It runs per task, in isolation, receiving only the task's verify criteria and test conventions.

## When to spawn

For each task, evaluate the `verify` field. Use `scripts/should-write-tests.py` for deterministic classification:

- **Spawn** for behavioral, edge-heavy, stateful, or permission-dependent criteria
- **Skip** for purely structural criteria (file exists, config set, compiles clean)

See `references/sub-agent-strategy.md` for the full heuristic.

## What the test writer receives

In in-session mode, compose a message with:

```markdown
## Spec Excerpt
<the task's verify field and any related constraints>

## Module Under Test
<expected file path and brief description>

## Project Context
<test framework, conventions, file paths from guidelines.md>

## Existing Types (if available)
<relevant type definitions or schemas>
```

In ralph mode, the loop script assembles this via `assemble-prompt.py test-writer <feature> --task-id <id>` and the `templates/test-writer.txt` template.

## What to do with the output

1. Write the test file to the appropriate path
2. The tests should FAIL initially (the implementation doesn't exist yet)
3. The implementor writes code until the check command passes (which includes running these tests)
4. This is the TDD loop: test-writer produces red, implementor produces green, check validates

## Isolation

The test-writer runs in an isolated context. It does NOT see:

- The main conversation history
- Implementation code (it doesn't exist yet)
- Prior test files

This isolation is deliberate — it prevents confirmation bias. The test-writer writes tests from the spec, not from the implementation.
