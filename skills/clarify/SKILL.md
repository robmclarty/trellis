---
name: clarify
description: Reviews a spec for ambiguities across six structured categories and resolves them. Modifies the spec in place. Use after writing or revising a spec, when ambiguity markers exist in a spec, or when you want a fresh completeness review. Triggers on "clarify the spec", "review for gaps", "check for ambiguities", "are there any open questions in the spec", or any request to verify a spec is complete and unambiguous.
context: fork
---

# Clarify

Review the spec for ambiguities and resolve them. Modifies `.specs/<feature-name>/spec.md` in place.

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

### Step 3: Present findings

Present all findings to the user, grouped by category. For each finding:

1. State the issue clearly
2. Suggest a resolution if you have enough context
3. Ask the user to confirm, revise, or defer to open questions

### Step 4: Apply resolutions

For findings the user resolves:
- Remove the `[? ...]` marker and replace it with the resolved content
- Or add new content to the appropriate spec section

For findings the user defers:
- Move them to §10 (Open Questions) with the reason for deferral

For findings that require substantial spec revision:
- Tell the user which sections need rework and suggest they re-run `/spec` with the new context, then come back to `/clarify`

### Step 5: Final check

After all resolutions are applied, do one more scan. The spec should have zero `[? ...]` markers remaining. Any unresolved items should be in §10 with clear deferral reasoning.

## Output

Modified `spec.md` in place. No separate artifact. The clarify phase is a refinement of the spec, not a document of its own.

## Quality gate

- [ ] Zero `[? ...]` markers remain in the spec body (all resolved or moved to §10)
- [ ] Every category was checked, not just the ones with explicit markers
- [ ] Deferred items in §10 have a reason and any preliminary thinking
- [ ] The user confirmed each resolution (no silent assumptions)
