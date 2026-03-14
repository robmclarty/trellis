---
name: trellis:tasks
description: Use when user wants to Creates an ordered task breakdown at .specs/{feature}/tasks.md that decomposes a plan into discrete, verifiable units of work organized in phases.
allowed-tools: Read, Glob, Grep, Task
---

# Tasks

## When to use

- "break this into tasks", "create tasks", "task breakdown"
- "what do I build first", "generate work items"
- Any request to decompose a technical plan into actionable steps or prepare work items for execution

Create an ordered task breakdown at `.specs/<feature-name>/tasks.md`.

**Recommended effort: medium.** Mechanical decomposition of the plan into ordered tasks.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py tasks <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## What to ask the user

If the user runs `/tasks` without additional context:

1. Are there any ordering constraints beyond what the plan implies? (e.g., "I need the API working before the MCP layer so I can demo it")
2. Should tasks be sized for a human developer or for an AI coding agent? (This affects granularity. Agent tasks can be smaller and more mechanical. Human tasks should be more self-contained.)

## Generation

After gathering all user input, spawn the `task-writer` agent. Pass it: the feature name, specs directory path, and all user-provided context. The agent will read prerequisite files and generate the tasks document.

## Quality gate

After the agent completes, verify the generated `tasks.md`:

- [ ] Every plan section maps to at least one task
- [ ] Every spec interface has at least one task that implements it
- [ ] Every task has a concrete "Verify" step
- [ ] Tasks are ordered so that each task's dependencies are completed in earlier tasks
- [ ] No task requires reading the full plan to understand (it references specific sections)
- [ ] Phase milestones describe an observable, testable state
- [ ] The first phase produces something runnable (even if minimal)
