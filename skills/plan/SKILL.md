---
name: trellis:plan
description: Creates a technical plan at .specs/<feature>/plan.md translating a spec's functional requirements into architecture, technology, and code decisions.
---

# Plan

## When to use

- "write a plan", "plan the implementation", "how should we build this"
- "create a technical plan", "architect this"
- Any request to translate a spec into actionable technical decisions
- Making technology decisions, defining file structure, or creating an implementation strategy

Create a technical implementation plan at `.specs/<feature-name>/plan.md`.

## Specs directory resolution

Before starting, read `trellis.json` from the project root. If it exists and has a `specsDir` field, use that value as the specs directory. Otherwise, default to `.specs/`. All references to `.specs/` in this document refer to the resolved specs directory.

## Purpose

The plan translates the spec's *what* into *how*. It makes every technical decision the implementor needs: architecture, libraries, file structure, data access patterns, integration approaches, and deployment strategy. The spec says "the system exposes a REST API for managing passes." The plan says "Fastify server with route modules under `src/routes/`, Drizzle for data access, Zod schemas shared between validation and type inference, deployed as a Docker container to ECS in ca-central-1."

The plan is where the project's guidelines meet the feature's spec. Guidelines provide the default stack and patterns. The spec provides the functional requirements. The plan resolves any tension between them and fills in every technical gap.

## Prerequisites

- `.specs/<feature-name>/spec.md` must exist with zero unresolved `[? ...]` markers
- `.specs/guidelines.md` must exist
- `.specs/<feature-name>/compliance.md` must exist if the feature has compliance requirements. The plan must respect all compliance constraints.

## What to ask the user

If the user runs `/plan` without additional context, check if the prerequisites exist. Then ask:

1. Are there any technical decisions you've already made that should be locked in?
2. Are there any constraints beyond what's in the guidelines? (Performance targets, budget limits, team skill considerations)
3. Is there an existing codebase this integrates into? If so, describe the integration points.

## Reading inputs

Before writing, read all three inputs and extract:

From **guidelines.md**: The default stack, patterns, conventions, and testing philosophy. These are inherited unless the plan explicitly overrides them (with justification).

From **spec.md**: The functional requirements, data model, interfaces, business rules, failure modes, and success criteria. The plan must account for all of these.

From **compliance.md** (if present): Data classification, storage requirements, access control constraints, audit requirements, and any data flow restrictions.

## Output: `.specs/<feature-name>/plan.md`

The plan uses ten sections (§1–§10). **Read `references/section-guide.md` for the detailed definition of each section.** The sections are:

- **§1 — Technical Summary** — One-paragraph strategy overview
- **§2 — Architecture** — Component diagram and system structure
- **§3 — Technology Decisions** — Every library/tool/infra choice with rationale
- **§4 — Data Access Patterns** — How the app interacts with its data layer
- **§5 — Interface Implementation** — How each spec interface is built
- **§6 — File Structure** — Complete directory layout
- **§7 — Error Handling Strategy** — How errors flow through the system
- **§8 — Testing Strategy** — What gets tested, how, and what's skipped
- **§9 — Deployment and Infrastructure** — Build, deploy, operate
- **§10 — Migration Path** — (If applicable) How to transition from the old system

Include concrete code snippets showing preferred patterns. These should follow the project guidelines and serve as copy-paste templates for the implementor.

## Quality gate

- [ ] Every interface in the spec has a corresponding implementation plan
- [ ] Every data entity in the spec has a data access pattern
- [ ] Every compliance constraint (if applicable) is addressed with a specific technical approach
- [ ] The file structure matches the architecture
- [ ] Code snippets follow the project guidelines
- [ ] Technology decisions include rejected alternatives where relevant
- [ ] An implementor could set up the project skeleton from §6 and start coding from §5 without further questions
