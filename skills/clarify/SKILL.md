---
name: trellis:clarify
description: Reviews a spec for ambiguities across six structured categories and resolves them in place. Use after writing or revising a spec, or for a fresh completeness review.
context: fork
---

# Clarify

## When to use

- "clarify the spec", "review for gaps", "check for ambiguities"
- "are there any open questions in the spec"
- Any request to verify a spec is complete and unambiguous
- After writing or revising a spec, when ambiguity markers (`[? ...]`) exist

Review the spec for ambiguities and resolve them. Modifies `.specs/<feature-name>/spec.md` in place.

**Recommended effort: high.** Analytical judgment across six ambiguity categories, requires careful reading.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py clarify <feature-name>` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-markers.py <specs-dir>/<feature-name>/spec.md` to get a structured count of existing ambiguity markers before starting the review.

## Purpose

Clarify is a structured review pass over the spec. It finds every unresolved ambiguity (both explicit markers and implicit gaps), categorizes them, and either resolves them directly or flags them for the user to decide. This phase exists because specs written in a single pass almost always contain assumptions that need to be surfaced and tested.

Clarify can loop. If the review reveals gaps that require substantial spec changes, the right move is to revise the spec and re-run clarify, not to patch around the gaps.

## Prerequisites

- `.specs/<feature-name>/spec.md` must exist

## Process

### Step 1: Scan for explicit markers

Find every `[? CATEGORY: ...]` marker in the spec. List them grouped by category.

### Step 2: Scan for implicit gaps

Read the spec section by section and check for each of the six ambiguity categories, even where no marker exists. The spec author may have made assumptions without realizing it. Specifically check:

**DATA_OWNERSHIP**
- Is it clear where every piece of data originates?
- Is it clear who can create, read, update, and delete each entity?
- Are data lifecycle questions answered? (What happens to data when a user is removed? When a parent entity is deleted?)

**PERMISSIONS**
- Are all actors defined with explicit capability lists?
- Are there actions where the permission boundary is fuzzy? (e.g., "managers can view reports" but which reports?)
- Are there implicit role hierarchies that should be explicit?

**PRIVACY**
- Does the spec handle any personally identifiable information?
- Is it clear which fields are sensitive and how they're protected?
- Are data retention and deletion policies addressed?

**UX_INTENT**
- For each user-facing workflow, is the intended experience clear?
- Are there interactions where the "happy path" is defined but the experience of error states or edge states is not?
- Would a designer have enough information to build the UI from this spec?

**INTEGRATION**
- Are all external system dependencies identified?
- For each integration point, is the contract explicit (protocol, auth, data format)?
- Are failure modes at integration boundaries covered?

**EDGE_CASE**
- Are concurrent access scenarios addressed?
- Are boundary conditions covered? (Empty lists, max limits, Unicode, timezone handling)
- Are migration or transition states handled? (What happens during rollout, partial deployment, data migration?)

### Step 3: Resolve findings

Since this skill runs in an isolated context (`context: fork`) without access to conversation history, it cannot interactively ask the user for input. Instead:

**For findings resolvable from available context** (the spec itself, guidelines, pitch):
- Resolve them directly. Remove the `[? ...]` marker and replace it with the resolved content, or add new content to the appropriate spec section.

**For findings that require user judgment:**
- Move them to §10 (Open Questions) with a clear description and a suggested resolution. Tag each with the ambiguity category: `[CLARIFY:PERMISSIONS] Should managers see reports from other departments? Suggested: no, scope to own department.`

**For findings that require substantial spec revision:**
- Note which sections need rework in §10 and recommend the user re-run `/spec` then `/clarify`.

> **Note:** When invoked through `/pipeline`, the pipeline skill gathers user context upfront (in interactive mode via review pauses, in auto mode via extended intake questions). This context is passed to clarify, enabling better resolution. When invoked standalone, clarify works from the spec and available artifacts only.

### Step 4: Apply resolutions

For all resolved findings:
- Remove the `[? ...]` marker and replace it with the resolved content
- Or add new content to the appropriate spec section

For all deferred findings:
- Move them to §10 (Open Questions) with the reason for deferral and suggested resolution

### Step 5: Final check

After all resolutions are applied, do one more scan. The spec should have zero `[? ...]` markers remaining. Any unresolved items should be in §10 with clear deferral reasoning.

## Output

Modified `spec.md` in place. No separate artifact. The clarify phase is a refinement of the spec, not a document of its own.

## Quality gate

- [ ] Zero `[? ...]` markers remain in the spec body (all resolved or moved to §10)
- [ ] Every category was checked, not just the ones with explicit markers
- [ ] Deferred items in §10 have a reason and any preliminary thinking
- [ ] Unresolvable items are in §10 with suggested resolutions and category tags
