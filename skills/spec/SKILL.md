---
name: spec
description: Creates a full functional specification at .specs/<feature>/spec.md defining what a system does and why. Use to write or revise feature requirements.
allowed-tools: Read, Write, Edit, Glob, Grep, Agent
---

# Spec

## When to use

- "write a spec", "spec this out", "define the requirements", "specify"
- "what should this system do"
- Any request to produce a complete, unambiguous description of a feature's behavior, data, interfaces, and constraints
- Turning a pitch into a detailed specification

Create a functional specification at `.specs/<feature-name>/spec.md`.

**Recommended effort: high.** Most complex output, cross-references multiple input artifacts.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py spec <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## What to ask the user

If the user runs `/spec` without providing details, ask:

1. Which feature folder? (List existing ones under `.specs/` or create a new one.)
2. Walk me through what this system does from the user's perspective.
3. What data does it manage?
4. Who interacts with it and what can each person do?

If the user provides a description, extract as much structure as you can and confirm gaps. Prefer over-asking to under-asking. The spec is where precision matters most.

5. Are there compliance or regulatory concerns? (Jurisdictions, data sensitivity — this context will be embedded in §9 so that downstream `/clarify` and `/compliance` skills, which run in isolated contexts, can resolve issues without interactive access to the user.)
6. Any known ambiguities about data ownership, permissions, or integrations? (These will be captured as `[? CATEGORY: ...]` markers for `/clarify` to resolve.)

## Generation

After gathering all user input, spawn the `spec-writer` agent. Pass it: the feature name, specs directory path, and all user-provided context. The agent will read prerequisite files (guidelines.md, pitch.md) and generate the spec document.

## Quality gate

- [ ] Could an implementor build this system from the spec alone, without access to the pitch or any prior conversation?
- [ ] Is every interface fully defined (inputs, outputs, errors)?
- [ ] Are all enum values and allowed states listed exhaustively, not by example?
- [ ] Are ambiguities marked with typed `[? CATEGORY: ...]` markers rather than silently guessed?
- [ ] Does the spec avoid implementation details? (No library names, no architecture decisions. Those go in the plan.)
- [ ] Are the no-gos from the pitch preserved in §9?
- [ ] Is §10 populated? (A spec with zero open questions is suspicious.)
