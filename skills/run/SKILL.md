---
name: trellis:run
description: Orchestrates the spec-driven pipeline (pitch → spec → plan → build) with review gates between stages. Use when running the full feature pipeline or resuming from the last completed stage.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Run

## When to use

- "run the pipeline", "run", "take this from pitch to implementation"
- "full spec workflow", "resume"
- Any request to run the complete spec-driven process end-to-end
- When the user wants to go from a problem description to working code in one or more sessions

Orchestrate the full spec-driven development pipeline for a feature.

**Recommended effort: high.** Orchestration with judgment calls and review gates.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py run` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## Prerequisites

- `.specs/guidelines.md` must exist. If it doesn't, tell the user to run `/guidelines` first.
- Any sketches that should inform the pitch should already exist in `.specs/sketches/`. The pipeline does not create sketches; those are exploratory and happen before you commit to a feature.

## Feature resolution

Determine the feature name. If provided as an argument (e.g., `/run my-feature` or `/run spec my-feature`), use it. Otherwise, ask the user:

> **What's the feature name?** (kebab-case, becomes the folder name under the specs directory)

**Do NOT search for or auto-detect existing feature directories.** The feature name must come from the user's argument or by asking them directly. Do not scan the specs directory to find features — wait for the user to provide a name.

Once the feature name is known, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pipeline-status.py <feature-name>` to check whether the feature directory already exists and which artifacts are present.

### New feature (no existing directory)

Proceed to **Intake questions** below, then start the pipeline at Stage 1.

### Existing feature

Tell the user which stages are already completed, then ask:

1. **Resume** — Continue from the next incomplete stage. Skip intake questions — the existing artifacts contain the context.
2. **Start fresh** — Overwrite existing artifacts by restarting at Stage 1. Proceed to intake questions.
3. **Choose a different name** — Loop back and ask for a new feature name.

## Stage override

The run skill accepts an optional argument to force restart at a specific stage:

- `/run` — Resume from the next incomplete stage (default).
- `/run pitch` — Restart at pitch, regardless of existing artifacts.
- `/run spec` — Restart at spec.
- `/run plan` — Restart at plan.

When a stage override is provided with an existing feature, skip the resume/fresh/rename prompt — the user's intent is explicit. Run `pipeline-status.py` to determine the resumption point and proceed directly.

## Intake questions

Read `references/intake-questions.md` for the full list of questions to ask before starting Stage 1.

If resuming at a later stage, skip intake questions — the existing artifacts contain the context.

## Execution flow

### Stage 1: Pitch

Generate `.specs/<feature-name>/pitch.md` following the `/pitch` skill.

After generation, present the **review gate**:

1. Show the artifact path and a 3-5 sentence summary highlighting problem framing, appetite, no-gos, and rabbit holes.
2. Ask the user: **approve**, **edit**, or **redo**?
   - **approve** — Continue to Stage 2.
   - **edit** — End the run. Tell the user the file path and that they can re-invoke `/run` when ready.
   - **redo** — Delete pitch.md and regenerate. Re-present the gate. Limit: 3 redos per stage.

### Stage 2: Spec

Generate `.specs/<feature-name>/spec.md` following the `/spec` skill, reading from the confirmed pitch and guidelines.

After generation, present the **review gate**:

1. Show the artifact path and a 3-5 sentence summary highlighting key interfaces, data model entities, and open questions count (§10 items).
2. Ask the user: **approve**, **edit**, or **redo**?
   - **approve** — Continue to Stage 3.
   - **edit** — End the run. Tell the user the file path and that they can re-invoke `/run` when ready.
   - **redo** — Delete spec.md and regenerate. Re-present the gate. Limit: 3 redos per stage.

### Stage 3: Plan

Run the `/plan` skill, which automatically runs clarify and compliance as pre-steps before generating `.specs/<feature-name>/plan.md`.

After generation, present the **review gate**:

1. Show the artifact path and a 3-5 sentence summary highlighting architecture decisions, technology choices, whether compliance was run and what it found, and the file structure.
2. Ask the user: **approve**, **edit**, or **redo**?
   - **approve** — Continue to Stage 4.
   - **edit** — End the run. Tell the user the file path and that they can re-invoke `/run` when ready.
   - **redo** — Delete plan.md and regenerate. Re-present the gate. Limit: 3 redos per stage.

### Stage 4: Build

Before starting implementation, ask the user: **"OK to proceed with building?"**

This is a write-heavy operation that modifies source code. The user must explicitly confirm before it begins — especially important when the pipeline resumes and jumps directly to this stage.

- **If the user confirms:** Run the `/build` skill, which automatically runs prep (generating tasks.json) if it doesn't already exist.
- **If the user declines:** End the pipeline. Tell the user they can run `/trellis:build <feature-name>` when ready.

### Pipeline complete

After implementation finishes (or if the user declines to implement), summarize what was produced:

```text
.specs/<feature-name>/
  pitch.md       ✓
  spec.md        ✓
  compliance.md  ✓ (or skipped)
  plan.md        ✓
  tasks.json     ✓
```

Read `references/pipeline-control.md` for resumption logic.

## Quality gate

The pipeline is complete when:

- [ ] All generated artifacts pass their individual skill quality gates
- [ ] The spec has zero unresolved `[? ...]` markers (handled by plan's clarify pre-step)
- [ ] Compliance review is either completed or explicitly skipped (handled by plan's compliance pre-step)
- [ ] The user has confirmed each review gate
- [ ] Tasks reference specific spec and plan sections (traceability from task → plan → spec → pitch)
