---
name: trellis:plan
description: Use when user wants to Creates a technical plan at .specs/{feature}/plan.md translating a spec's functional requirements into architecture, technology, and code decisions.
allowed-tools: Read, Glob, Grep, Task
---

# Plan

## When to use

- "plan the implementation", "how should we build this"
- "create a technical plan", "architect this"
- Any request to translate a spec into actionable technical decisions
- Making technology decisions, defining file structure, or creating an implementation strategy

Create a technical implementation plan at `.specs/<feature-name>/plan.md`.

**Recommended effort: medium.** Template-driven but references multiple input artifacts.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py plan <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## Pre-steps: Clarify and Compliance

Before generating the plan, ensure the spec is ready. These steps run automatically — the user does not need to invoke them separately.

### Step A: Clarify

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-markers.py <specsDir>/<feature-name>/spec.md` to check for unresolved `[? ...]` markers.

- **If zero markers:** Skip clarify — the spec is already clean.
- **If markers exist:** Run the `/clarify` skill against the spec. Since clarify runs in a forked context (isolated, no user interaction), it resolves what it can and moves user-judgment items to §10 (Open Questions). Re-check markers after each pass. **Loop limit: 3 passes.** After 3, move any remaining markers to §10 and continue.

### Step B: Compliance (conditional)

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pipeline-status.py <feature-name>` and check the `complianceNeeded` and `complianceCompleted` fields.

- **If `complianceNeeded` is false:** Skip compliance.
- **If `complianceCompleted` is true** (compliance.md already exists): Skip compliance.
- **Otherwise:** Run the `/compliance` skill. Since compliance runs in a forked context, ensure any user-provided regulation context is embedded in the spec's §9 (Constraints) before invoking. If compliance recommends spec changes, apply them, re-run clarify on modified sections, then re-run compliance. **Loop limit: 2.** After 2 loops, document remaining gaps as residual risks in compliance.md and continue.

After pre-steps complete, proceed to plan generation below.

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
- [ ] A builder could set up the project skeleton from §6 and start coding from §5 without further questions
