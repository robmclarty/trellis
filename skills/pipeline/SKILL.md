---
name: pipeline
description: Orchestrates the full spec-driven development pipeline for a feature, running pitch, spec, clarify, compliance, plan, and tasks in sequence with automatic feedback loops. Use when the user wants to go from a problem description to a complete task breakdown in one session. Triggers on "run the pipeline", "pipeline", "take this from pitch to tasks", "full spec workflow", or any request to run the complete spec-driven process end-to-end.
disable-model-invocation: true
---

# Pipeline

Orchestrate the full spec-driven development pipeline for a feature, from pitch through tasks.

## Purpose

The pipeline drives all feature-specific phases in sequence, handling the feedback loops between them. Instead of running `/pitch`, then `/spec`, then `/clarify`, then `/compliance`, then `/plan`, then `/tasks` manually, you run `/pipeline` once and it manages the progression, loopbacks, and gating.

## Prerequisites

- `.specs/guidelines.md` must exist. If it doesn't, tell the user to run `/guidelines` first.
- Any sketches that should inform the pitch should already exist in `.specs/sketches/`. The pipeline does not create sketches; those are exploratory and happen before you commit to a feature.

## Modes

The pipeline accepts an optional argument to control its mode:

- `/pipeline` — **Interactive mode** (default). Pauses for user review after each major stage.
- `/pipeline auto` — **Automatic mode**. Gathers all context upfront, then runs the entire pipeline without pausing. Makes best-guess decisions at every point where interactive mode would ask the user.

### Interactive mode: upfront questions

Ask:

1. What problem are you solving? (This seeds the pitch.)
2. What's the feature name? (kebab-case, becomes the folder name under `.specs/`)
3. Does this feature have compliance requirements? (If yes, which regulations? If unsure, the pipeline will try to detect this from the spec's data model.)

### Auto mode: extended upfront questions

Ask all of the above, plus:

4. Walk me through the user experience. What does someone do with this feature, step by step?
5. What's the appetite? (Timeframe, team size, complexity budget)
6. Are there any specific technical decisions you've already made?
7. Does this integrate with an existing system? If so, describe the integration points.
8. Are there any known no-gos I should encode?
9. Any rabbit holes I should flag?
10. Anything else I should know that might affect the spec, plan, or compliance review?

Be thorough in this intake. Every question you skip here becomes a guess later. If the user's answers are thin in any area, push for more detail before proceeding. Once you start the auto run, you're committed to making all decisions yourself.

## Execution flow

> In the descriptions below, **interactive** behavior is the default. **Auto** behavior is noted where it differs. In auto mode, every pause becomes a self-review: make the best decision you can from available context and keep moving.

### Stage 1: Pitch

Generate `.specs/<feature-name>/pitch.md` following the `/pitch` skill.

**Interactive:** Pause for user review. Present the pitch and ask:
- Does the problem framing match your understanding?
- Is the appetite right?
- Are the no-gos and rabbit holes complete?

If the user requests changes, revise the pitch and re-present. Only proceed when the user confirms the pitch.

**Auto:** Self-review the pitch against the upfront context. Verify the problem, appetite, no-gos, and rabbit holes are consistent with what the user described. If anything feels underspecified, make a reasonable choice, document the assumption inline (e.g., "Assuming 4-week appetite based on described scope"), and continue.

### Stage 2: Spec

Generate `.specs/<feature-name>/spec.md` following the `/spec` skill, reading from the confirmed pitch and guidelines.

Do NOT pause for user review yet. Move directly to clarify. (Same in both modes.)

### Stage 3: Clarify (automatic, may loop)

Run the `/clarify` skill against the spec. This is an internal review pass.

**If clarify finds issues that can be resolved from available context:** resolve them in place and continue. (Same in both modes.)

**Interactive — if clarify finds issues that require user input:** pause and present the findings grouped by category. For each finding, present a suggested resolution and ask the user to confirm, revise, or defer. Apply the user's decisions.

**Auto — if clarify finds issues that require user input:** resolve them using your best judgment based on the upfront context, the guidelines, and the pitch. For each auto-resolved issue, add a brief note in §10 (Open Questions) tagged `[AUTO]`: `[AUTO] Assumed teacher role cannot delete passes. Verify with stakeholders.` This gives the user a clear list of every decision you made on their behalf.

**If clarify determines the spec needs substantial revision:** revise the spec incorporating the clarify findings, then re-run clarify. Limit to 3 loops. **Interactive:** if still unclean after 3 passes, pause for user. **Auto:** if still unclean after 3 passes, move remaining issues to §10 as `[AUTO]` items and continue.

**Exit condition:** Zero `[? ...]` markers remain in the spec body. All deferred items are in §10.

### Stage 4: User spec review

**Interactive:** Pause for user review. Present the clarified spec and ask:
- Does this capture what you want to build?
- Any sections that feel wrong or incomplete?

If the user requests changes, revise the spec and re-run clarify (Stage 3). Only proceed when the user confirms the spec.

**Auto:** Skip. The clarify pass in Stage 3 serves as the quality check. Continue to compliance.

### Stage 5: Compliance (conditional, may loop)

**Skip if:** The user said no compliance requirements and the spec's data model contains no PII, student data, health data, or other sensitive categories. (Same in both modes.)

**Run if:** The user specified regulations, OR the data model contains entities that likely require compliance review. (Same in both modes.)

Generate `.specs/<feature-name>/compliance.md` following the `/compliance` skill.

**If compliance finds no gaps:** continue to plan. (Same in both modes.)

**Interactive — if compliance recommends spec changes:** present the recommended changes to the user. If the user agrees, revise the spec, re-run clarify on modified sections, then re-run compliance. Limit to 2 loops. If issues persist, pause for user.

**Auto — if compliance recommends spec changes:** apply the recommended changes to the spec, re-run clarify on modified sections, then re-run compliance. Limit to 2 loops. If issues persist after 2 loops, document the remaining gaps as residual risks in `compliance.md` and continue. Add an `[AUTO]` note in the spec's §10 for each compliance-driven change that was applied without user confirmation.

**Exit condition:** Compliance review shows all requirements either satisfied or explicitly accepted as residual risks.

### Stage 6: Plan

Generate `.specs/<feature-name>/plan.md` following the `/plan` skill, reading from the spec, compliance (if present), and guidelines.

**Interactive:** Pause for user review. Present the plan and ask:
- Do the technology decisions look right?
- Does the architecture match your mental model?
- Anything missing from the file structure or deployment strategy?

If the user requests changes, revise the plan. No need to re-run earlier stages unless the user identifies a spec-level problem (in which case, loop back to Stage 4).

**Auto:** Self-review the plan for consistency with guidelines and spec. Verify every spec interface has a corresponding implementation approach. Continue.

### Stage 7: Tasks

Generate `.specs/<feature-name>/tasks.md` following the `/tasks` skill, reading from the plan and spec.

**Interactive:** Pause for user review. Present the tasks and ask:
- Is the phasing right?
- Are tasks sized appropriately?
- Any ordering issues?

If the user requests changes, revise the tasks. The pipeline is complete once the user confirms the task breakdown.

**Auto:** Self-review the tasks for completeness (every plan section and spec interface is covered) and ordering (dependencies respected). Continue.

### Pipeline complete

Summarize what was produced:

```
.specs/<feature-name>/
  pitch.md       ✓
  spec.md        ✓
  compliance.md  ✓ (or skipped)
  plan.md        ✓
  tasks.md       ✓
```

**Interactive:** Tell the user they can now run `/implement` against the tasks.

**Auto:** Tell the user the pipeline is complete, then present a summary of every `[AUTO]` decision made during the run. Group them by artifact and category. This is the user's review checklist: the list of assumptions they should verify before running `/implement`. Example:

```
## Auto decisions requiring review

### spec.md §10
- [AUTO] Assumed teacher role cannot delete passes. Verify with stakeholders.
- [AUTO] Assumed session data is owned by the school, not the student.

### compliance.md — Residual Risks
- [AUTO] FIPPA storage requirement satisfied by ca-central-1 deployment. Verify provider compliance certification.
```

## Loop limits

| Loop | Max iterations | On exceed (interactive) | On exceed (auto) |
|------|---------------|------------------------|-------------------|
| Clarify → Spec | 3 | Pause, present issues to user | Move to §10 as `[AUTO]`, continue |
| Compliance → Spec | 2 | Pause, present issues to user | Document as residual risks, continue |
| User review → any stage | No limit | User is always in control | N/A (no pauses) |

## Interruption and resumption

If the user stops the pipeline mid-run (or the conversation ends), the pipeline is resumable. Because each stage writes its artifact to disk, the pipeline can detect which artifacts exist and resume from the next incomplete stage:

- `pitch.md` exists but not `spec.md` → resume at Stage 2
- `spec.md` exists but has `[? ...]` markers → resume at Stage 3 (clarify)
- `spec.md` is clean, no `compliance.md` and compliance is needed → resume at Stage 5
- `compliance.md` exists but not `plan.md` → resume at Stage 6
- `plan.md` exists but not `tasks.md` → resume at Stage 7

When resuming, tell the user where you're picking up and confirm they want to continue from that point. If the original run was in auto mode, ask if they want to continue in auto mode or switch to interactive.

## Quality gate

The pipeline is complete when:

- [ ] All generated artifacts pass their individual skill quality gates
- [ ] The spec has zero unresolved `[? ...]` markers
- [ ] Compliance review is either completed or explicitly skipped with justification
- [ ] **(Interactive)** The user has confirmed each pause point
- [ ] **(Auto)** All autonomous decisions are documented as `[AUTO]` items and presented in the final summary
- [ ] Tasks reference specific spec and plan sections (traceability from task → plan → spec → pitch)
