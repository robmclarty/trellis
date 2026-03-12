# Plan Section Guide

Detailed definitions for each section of the plan. Read this before writing a plan.

---

## §1 — Technical Summary

A brief overview of the implementation approach. One paragraph that a technical lead could read and understand the strategy without reading the rest of the document. Name the key technology choices and the architectural pattern.

## §2 — Architecture

How the system is structured internally. Include:

- Component diagram (ASCII or mermaid) showing the major pieces and how they communicate
- For each component: its responsibility, the technology it uses, and its boundaries
- How the feature integrates with existing systems (if applicable). Be specific about protocols, shared databases, API calls, or event buses.
- If the feature is a new service, describe how it fits into the broader system topology

## §3 — Technology Decisions

Every library, tool, and infrastructure choice with a one-sentence rationale. Organize as a table:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| HTTP framework | Fastify | Project standard per guidelines |
| ORM | Drizzle | Project standard; schema-first, supports Postgres RLS |
| Validation | Zod | Shared schemas for validation and type inference |

If a choice diverges from the guidelines, explain why. If a choice was considered and rejected, include it with the reason (this prevents the implementor from re-evaluating a dead option).

## §4 — Data Access Patterns

How the application interacts with its data layer. This is not the data model (that's in the spec). This is the implementation strategy:

- How schemas are defined (Drizzle table definitions, Zod validation schemas)
- Query patterns for the main operations (which queries need joins, aggregations, or complex filters)
- Migration strategy (how the schema is versioned and deployed)
- Connection management (pooling, timeouts, retry behavior)
- If there are compliance constraints on data storage or access, show how the implementation satisfies them

Include concrete code snippets showing the preferred patterns. These should follow the project guidelines and serve as copy-paste templates for the implementor.

## §5 — Interface Implementation

How each interface from the spec is implemented. For REST APIs:

- Route organization (how routes map to files/modules)
- Request validation approach (Zod schemas on input, how they connect to Fastify's validation)
- Response formatting patterns
- Error response structure
- Authentication/authorization middleware placement

For MCP tools, CLI commands, or other interfaces: equivalent implementation details.

Include a concrete code snippet for one representative endpoint/tool showing the full request lifecycle from input to response.

## §6 — File Structure

The complete directory layout. Every directory and key file with a brief note about its purpose. Use a tree format. The structure should make the architecture visible. Group by architectural layer (data, services, routes, etc.) not by file type. This is the first thing an implementor creates before writing logic.

## §7 — Error Handling Strategy

How errors flow through the system:

- Where errors are caught vs. where they propagate
- Error type hierarchy (if any) or how errors are represented
- How errors at system boundaries (database, external services) are translated into API responses
- Logging strategy for errors (what gets logged, at what level, what context is included)

## §8 — Testing Strategy

What gets tested and how, informed by both the spec's success criteria and the project's testing philosophy from guidelines:

- Which tests are written and which are skipped (with reasoning)
- Test file organization and naming
- Any test fixtures, factories, or helpers needed
- Integration test setup (database provisioning, service mocking)

## §9 — Deployment and Infrastructure

How the feature is built, deployed, and operated:

- Build process (compilation, bundling, Docker image)
- Deployment target and strategy
- Environment variables (reference the spec's list if it has one, add any implementation-specific ones)
- Health checks and monitoring
- If there are compliance constraints on hosting or infrastructure, show how they're satisfied

## §10 — Migration Path

If this feature replaces or extends an existing system:

- How existing data is migrated
- How traffic is transitioned (blue-green, feature flag, gradual rollout)
- What the rollback strategy is
- How the old and new systems coexist during transition

Skip this section if the feature is greenfield with no migration concerns.
