---
name: pitch
description: Creates a pitch document at .specs//pitch.md defining a problem domain with constraints, appetite, and solution shape. Use to frame a feature before writing a spec.
allowed-tools: Agent
---

# Pitch

## When to use

- "pitch this", "frame this problem", "let's scope this"
- "write a pitch for", "propose"
- Any request to define a problem and solution direction before committing to a full specification
- Synthesizing sketch results into a coherent initiative

Create a pitch document at `.specs/<feature-name>/pitch.md`.

**Recommended effort: medium.** Synthesis from user input into a well-defined template.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py pitch <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## Feature naming

The pitch creates a new feature folder under `.specs/`. Ask the user for a short kebab-case name that describes the initiative: `hall-pass-extraction`, `kudos-mcp`, `student-search-api`. This folder will hold all subsequent artifacts (spec, compliance, plan, tasks) for this initiative.

## What to ask the user

If the user runs `/pitch` without enough context, ask:

1. What problem are you solving? Who has this problem?
2. How much time and effort is this worth? (A week? Six weeks? Is there a hard deadline?)
3. What sketches, if any, informed this pitch?
4. What's explicitly out of scope?

## Generation

After gathering all user input, spawn the `pitch-writer` agent. Pass it: the feature name, specs directory path, and all user-provided context (problem description, appetite, solution shape, no-gos, rabbit holes). The agent will read prerequisite files and generate the pitch document.

## Quality gate

After the agent produces the pitch, verify:

- [ ] Is the problem described from the user's/stakeholder's perspective, not the system's?
- [ ] Does the appetite set a clear constraint on effort?
- [ ] Are no-gos specific enough to say "no" to concrete requests?
- [ ] Could someone who wasn't in the room evaluate whether this pitch is worth pursuing?
- [ ] Does the shape give enough direction without over-specifying?
- [ ] Are rabbit holes identified with pragmatic alternatives?
