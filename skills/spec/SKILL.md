---
name: Functional Spec
description: Creates a full functional specification at .specs/<feature>/spec.md defining what a system does and why. Use to write or revise feature requirements.
---

# Spec

## When to use

- "write a spec", "spec this out", "define the requirements", "specify"
- "what should this system do"
- Any request to produce a complete, unambiguous description of a feature's behavior, data, interfaces, and constraints
- Turning a pitch into a detailed specification

Create a functional specification at `.specs/<feature-name>/spec.md`.

## Purpose

The spec is the source of truth for what the system does. It is a complete, unambiguous description of the feature's behavior, data, interfaces, and constraints. Everything downstream (compliance review, technical plan, tasks, implementation) derives from the spec. If the spec is wrong, everything built on it is wrong.

The spec focuses on *what* and *why*, not *how*. Technical implementation decisions belong in the plan. The spec should be stable even if the implementation approach changes entirely.

## Prerequisites

- `.specs/<feature-name>/pitch.md` must exist. The spec builds on the pitch's problem definition, shape, and no-gos.
- `.specs/guidelines.md` must exist. The spec inherits guidelines but does not restate them.

## What to ask the user

If the user runs `/spec` without providing details, ask:

1. Which feature folder? (List existing ones under `.specs/` or create a new one.)
2. Walk me through what this system does from the user's perspective.
3. What data does it manage?
4. Who interacts with it and what can each person do?

If the user provides a description, extract as much structure as you can and confirm gaps. Prefer over-asking to under-asking. The spec is where precision matters most.

5. Are there compliance or regulatory concerns? (Jurisdictions, data sensitivity — this context will be embedded in §9 so that downstream `/clarify` and `/compliance` skills, which run in isolated contexts, can resolve issues without interactive access to the user.)
6. Any known ambiguities about data ownership, permissions, or integrations? (These will be captured as `[? CATEGORY: ...]` markers for `/clarify` to resolve.)

## Reading the pitch

Before writing, read the pitch carefully. Extract:

- The problem framing (this becomes the spec's context, not restated but referenced)
- The no-gos (these become the spec's "out of scope" constraints)
- The shape (this is the starting outline the spec fills in)
- The rabbit holes (these may surface as open questions or things to explicitly defer)

## Output: `.specs/<feature-name>/spec.md`

The spec uses ten sections (§1–§10). Not every spec needs every section. Skip sections that don't apply and note why if it's not obvious. Section numbering is stable: even if you skip §4, the next section is still §5.

**Read `references/section-guide.md` for the detailed definition of each section**, including what to include, what level of detail is expected, and examples of good vs. bad content. The sections are:

- **§1 — Context** — Anchors this spec to its pitch
- **§2 — Functional Overview** — What the system does in terms of user-facing behavior
- **§3 — Actors and Permissions** — Who interacts and what each can do
- **§4 — Data Model** — Persistent data structures with full field definitions
- **§5 — Interfaces** — External contracts (REST, MCP, CLI, events)
- **§6 — Business Rules** — Logic and workflows independent of interfaces
- **§7 — Failure Modes** — Specific things that can go wrong and expected behavior
- **§8 — Success Criteria** — How to verify the implementation is correct
- **§9 — Constraints** — Scope, technical, and operational limits
- **§10 — Open Questions** — Explicitly deferred decisions

## Ambiguity markers

When writing the spec, if you encounter something ambiguous that you cannot resolve from the pitch or conversation context, insert a typed marker:

```
[? CATEGORY: specific question]
```

Where CATEGORY is one of:

- `DATA_OWNERSHIP` — Who owns this data? Where does it live? Who can delete it?
- `PERMISSIONS` — Who can do this? What are the authorization boundaries?
- `PRIVACY` — Does this involve PII? What regulations apply? What's the data lifecycle?
- `UX_INTENT` — What is the user actually trying to accomplish? What should the experience feel like?
- `INTEGRATION` — How does this connect to other systems? What are the contracts?
- `EDGE_CASE` — What happens in this unusual scenario?

These markers are resolved during the `/clarify` phase. Do not guess. A wrong assumption baked into the spec is worse than an explicit question.

## Quality gate

- [ ] Could an implementor build this system from the spec alone, without access to the pitch or any prior conversation?
- [ ] Is every interface fully defined (inputs, outputs, errors)?
- [ ] Are all enum values and allowed states listed exhaustively, not by example?
- [ ] Are ambiguities marked with typed `[? CATEGORY: ...]` markers rather than silently guessed?
- [ ] Does the spec avoid implementation details? (No library names, no architecture decisions. Those go in the plan.)
- [ ] Are the no-gos from the pitch preserved in §9?
- [ ] Is §10 populated? (A spec with zero open questions is suspicious.)
