---
name: trellis:prep
description: Prepare implementation by decomposing a plan into an ordered task breakdown at .specs/{feature}/tasks.json. Creates discrete, verifiable units of work organized in phases.
allowed-tools: Read, Glob, Grep, Task
---

# Prep

Prepare a feature for implementation by decomposing its plan into ordered, verifiable tasks.

## When to use

- "prep this for implementation", "prepare tasks", "break this into tasks"
- "what do I build first", "generate work items", "create task breakdown"
- Any request to decompose a technical plan into actionable steps or prepare work items for execution
- Called automatically by `/trellis:implement` when `tasks.json` doesn't exist yet

Create an ordered task breakdown at `.specs/<feature-name>/tasks.json`.

**Recommended effort: medium.** Mechanical decomposition of the plan into ordered tasks.

**Re-running this skill overwrites tasks.json**, resetting all task statuses to "pending". This is how you reset an implementation.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py prep <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## What to ask the user

If the user runs `/prep` without additional context:

1. Are there any ordering constraints beyond what the plan implies? (e.g., "I need the API working before the MCP layer so I can demo it")
2. Should tasks be sized for a human developer or for an AI coding agent? (This affects granularity. Agent tasks can be smaller and more mechanical. Human tasks should be more self-contained.)

If invoked automatically from `/trellis:implement` (no user present), skip questions and use defaults (agent-sized tasks, plan-implied ordering).

## Generation

After gathering all user input, spawn the `task-writer` agent. Pass it: the feature name, specs directory path, and all user-provided context. The agent will read prerequisite files (plan.md, spec.md, guidelines.md) and generate tasks.json.

## Quality gate

After the agent completes, verify the generated `tasks.json`:

- [ ] Valid JSON that conforms to `schemas/tasks.schema.json`
- [ ] Every plan section maps to at least one task
- [ ] Every spec interface has at least one task that implements it
- [ ] Every task has a concrete "verify" field
- [ ] Tasks are ordered so that each task's dependencies are completed in earlier tasks
- [ ] No task requires reading the full plan to understand (it references specific sections)
- [ ] The first phase produces something runnable (even if minimal)
- [ ] The `check` field is populated from guidelines.md (or empty string if not available)
