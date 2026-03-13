---
name: trellis:plan
description: Creates a technical plan at .specs/<feature>/plan.md translating a spec's functional requirements into architecture, technology, and code decisions.
allowed-tools: Read, Glob, Grep, Agent
---

# Plan

## When to use

- "write a plan", "plan the implementation", "how should we build this"
- "create a technical plan", "architect this"
- Any request to translate a spec into actionable technical decisions
- Making technology decisions, defining file structure, or creating an implementation strategy

Create a technical implementation plan at `.specs/<feature-name>/plan.md`.

**Recommended effort: medium.** Template-driven but references multiple input artifacts.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py plan <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## What to ask the user

If the user runs `/plan` without additional context, check if the prerequisites exist. Then ask:

1. Are there any technical decisions you've already made that should be locked in?
2. Are there any constraints beyond what's in the guidelines? (Performance targets, budget limits, team skill considerations)
3. Is there an existing codebase this integrates into? If so, describe the integration points.

## Generation

After gathering all user input, spawn the `plan-writer` agent. Pass it: the feature name, specs directory path, and all user-provided context. The agent will read prerequisite files and generate the plan document.

## Quality gate

- [ ] Every interface in the spec has a corresponding implementation plan
- [ ] Every data entity in the spec has a data access pattern
- [ ] Every compliance constraint (if applicable) is addressed with a specific technical approach
- [ ] The file structure matches the architecture
- [ ] Code snippets follow the project guidelines
- [ ] Technology decisions include rejected alternatives where relevant
- [ ] An implementor could set up the project skeleton from §6 and start coding from §5 without further questions
