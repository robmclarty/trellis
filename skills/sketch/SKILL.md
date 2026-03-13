---
name: sketch
description: Creates a lightweight experiment document at .specs/sketches/.md to test a technical hypothesis before committing to a larger initiative.
allowed-tools: Agent
---

# Sketch

## When to use

- "let's try", "I want to test whether", "spike on"
- "experiment with", "sketch out", "is this feasible"
- Any request to explore a technical idea cheaply before building it for real

Create a new sketch document at `.specs/sketches/<slug>.md`.

**Recommended effort: low.** Short output; the user provides most of the content, the skill just structures it.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py sketch` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## What to ask the user

If the user runs `/sketch` without enough context, ask:

1. What question are you trying to answer?
2. What are you going to try?
3. How long should this take? (Think hours, not days. If it's days, it might be too big for a sketch.)

If the user provides a description, extract the hypothesis from it. Every sketch must have a falsifiable hypothesis.

## Generation

After gathering all user input, spawn the `sketch-writer` agent. Pass it: the specs directory path and all user-provided context (hypothesis, approach, constraints, slug name). The agent will generate the sketch document.

## Quality gate

- [ ] Does the hypothesis state something falsifiable?
- [ ] Are the findings specific enough to be useful without re-running the experiment?
- [ ] Is the verdict one of the four defined values?
- [ ] Is it short? (If it's more than a page, it's probably too detailed for a sketch.)
