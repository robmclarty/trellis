---
name: trellis:sketch
description: Creates a lightweight experiment document at .specs/sketches/<slug>.md to test a technical hypothesis before committing to a larger initiative.
---

# Sketch

## When to use

- "let's try", "I want to test whether", "spike on"
- "experiment with", "sketch out", "is this feasible"
- Any request to explore a technical idea cheaply before building it for real

Create a new sketch document at `.specs/sketches/<slug>.md`.

## Purpose

A sketch is a small, timeboxed experiment to test a hypothesis. It exists to answer a specific question cheaply before committing to a larger initiative. Sketches are disposable by nature but their findings are durable. A pitch may reference zero or more sketches to justify its approach.

## Prerequisites

- `.specs/guidelines.md` must exist. Sketches should respect the project's stack and conventions even when experimenting. If the sketch deliberately violates a guideline (e.g., testing a library outside the standard stack), note that explicitly.

## What to ask the user

If the user runs `/sketch` without enough context, ask:

1. What question are you trying to answer?
2. What are you going to try?
3. How long should this take? (Think hours, not days. If it's days, it might be too big for a sketch.)

If the user provides a description, extract the hypothesis from it. Every sketch must have a falsifiable hypothesis.

## Naming

The slug should be a short kebab-case name describing the experiment: `drizzle-multi-tenant`, `local-llm-formatting`, `websocket-vs-polling`. Ask the user or infer from context.

## Output: `.specs/sketches/<slug>.md`

A lightweight markdown document with four sections. Keep it short. A sketch is a lab notebook entry, not a report.

### Sections

**Hypothesis** — One or two sentences stating what you believe to be true and what you're testing. Frame it as falsifiable: "Drizzle can handle multi-tenant schema isolation using Postgres RLS without custom query wrappers." Not: "Explore Drizzle multi-tenancy."

**Method** — What you actually did or plan to do. Concrete steps: built a small prototype, read the docs and found X, wrote a benchmark, tried it in a branch. If code was written, note where it lives (branch name, throwaway repo, inline snippet). Keep this brief.

**Findings** — What you learned. Include specifics: performance numbers, API limitations discovered, patterns that worked or didn't. If the hypothesis was wrong, explain what was surprising. Findings should be useful to someone who didn't run the experiment.

**Verdict** — One of four values:

- **Viable** — The hypothesis held. This approach can move forward.
- **Viable with caveats** — It works, but with tradeoffs or constraints that a pitch should account for. List the caveats.
- **Not viable** — The hypothesis was falsified. Explain why. This is a valuable outcome.
- **Inconclusive** — The experiment didn't produce enough signal. Note what would be needed to get a clearer answer.

## Quality gate

- [ ] Does the hypothesis state something falsifiable?
- [ ] Are the findings specific enough to be useful without re-running the experiment?
- [ ] Is the verdict one of the four defined values?
- [ ] Is it short? (If it's more than a page, it's probably too detailed for a sketch.)
