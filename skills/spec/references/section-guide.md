# Spec Section Guide

Detailed definitions for each section of the spec. Read this before writing a spec.

---

## §1 — Context

A brief paragraph anchoring this spec to its pitch. Reference the pitch by path. Summarize the problem in one sentence and state what this spec defines. This section is for orientation, not persuasion.

## §2 — Functional Overview

What the system does, described in terms of user-facing behavior and capabilities. No architecture, no components, no libraries. If someone asked "what does this feature do?", this section is the answer. Organize by user workflows or capabilities, not by system internals.

## §3 — Actors and Permissions

Who interacts with the system and what each actor can do. Define roles explicitly. For each role, list their capabilities as concrete statements: "A teacher can view passes for students in their assigned classes. A teacher cannot view passes for students outside their classes." If the system has no auth or a single role, state that.

## §4 — Data Model

The persistent data structures the system manages. For each entity:

- All fields with types and nullability
- Primary keys, foreign keys, unique constraints
- Enum values listed exhaustively (closed sets, not examples)
- Required indexes and what queries they serve
- Relationships with explicit cardinality and ownership

If the data model is trivial, keep this section brief.

## §5 — Interfaces

The external contracts the system exposes: REST endpoints, MCP tools, CLI commands, event schemas, or any surface that consumers depend on. For each interface:

- Identifier (route path, tool name, command)
- What it does (natural language)
- Inputs with types, required/optional, defaults, validation
- Output shape on success
- Error cases specific to this interface
- Behavioral notes (idempotency, side effects, rate limits)

If the system has multiple interface layers that share underlying operations, define the behavior once and reference it from each layer.

## §6 — Business Rules

Logic, computations, and workflows that are independent of any specific interface. For each rule or workflow:

- Preconditions (what must be true before it runs)
- Steps it performs
- Postconditions (what is true after it succeeds)
- Edge cases and their handling

Skip this section if the system is straightforward CRUD and §5 already covers the logic.

## §7 — Failure Modes

Specific things that can go wrong and how the system should behave. Each failure mode should be a concrete scenario, not a generic category. For each:

- **Scenario**: What happens (e.g., "Database is unreachable at startup")
- **Expected behavior**: What the system does (e.g., "Fail to start with a clear error message including the redacted connection string")
- **How to verify**: A testable description (e.g., "Start the server with an invalid DATABASE_URL, verify it exits with code 1 and a message containing 'database unreachable'")

Focus on failures at system boundaries: database, external services, auth, concurrent access, invalid input.

## §8 — Success Criteria

How to determine if the implementation is correct and complete. Organized into:

- *Automated tests*: Specific scenarios with setup, action, and expected outcome. Concrete enough that an implementor can write the test directly from the description.
- *Integration tests*: Scenarios requiring the running system and possibly a real client. May be semi-automated or manual.
- *Architectural checks*: Properties of the codebase verified by review (layer separation, no logic duplication, dependency direction).

## §9 — Constraints

Hard limits on the implementation. Three categories:

- *Scope constraints*: What is explicitly excluded. Import these from the pitch's no-gos and add any new ones discovered during spec writing.
- *Technical constraints*: Inherited from guidelines. Only add constraints specific to this feature that go beyond the project-level guidelines.
- *Operational constraints*: Deployment model, scaling assumptions, infrastructure requirements specific to this feature.

## §10 — Open Questions

Things that are explicitly deferred. For each:

- The question
- Why it's deferred (out of scope, needs research, depends on learnings)
- Any preliminary thinking worth preserving

This section is a pressure valve. It prevents unresolved questions from silently disappearing or blocking the rest of the spec.

---

## Section selection guidance

**Always include**: §1 (Context), §2 (Functional Overview), §9 (Constraints), §8 (Success Criteria). These are the minimum. Without them, the implementor doesn't know what they're building, how to build it, or when they're done.

**Include for any system with persistence**: §4 (Data Model).

**Include for any system with users or external access**: §3 (Actors and Permissions), §5 (Interfaces).

**Include for complex logic**: §6 (Business Rules). Skip if the system is primarily CRUD.

**Include for anything that runs in production or will be iterated on**: §7 (Failure Modes).

**Include when there are unresolved decisions**: §10 (Open Questions). Skip only if everything is genuinely settled.

For a lightweight spec (a small tool, a focused feature), §1 + §2 + §9 + §8 might be enough, possibly in 1-2 pages.

For a full system spec (multi-component, multi-user, production-bound), include all sections. This will typically be 5-15 pages.
