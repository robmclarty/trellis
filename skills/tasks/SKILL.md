---
name: trellis:tasks
description: Creates an ordered task breakdown at .specs/<feature>/tasks.md that decomposes a plan into discrete, verifiable units of work organized in phases.
---

# Tasks

## When to use

- "break this into tasks", "create tasks", "task breakdown"
- "what do I build first", "generate work items"
- Any request to decompose a technical plan into actionable steps or prepare work items for execution

Create an ordered task breakdown at `.specs/<feature-name>/tasks.md`.

## Purpose

Tasks decomposes the plan into discrete, ordered units of work. Each task is small enough to be completed in a single focused session (roughly 1-4 hours of work) and produces a verifiable result. An implementor (human or LLM) should be able to pick up a task, understand what to do without reading the entire plan, and know when they're done.

Tasks are the bridge between planning and execution. The plan says "build a Fastify server with these routes." Tasks say "1. Scaffold the project directory. 2. Set up the database connection module. 3. Create the Zod schemas for pass entities. 4. Implement the GET /passes route..."

## Prerequisites

- `.specs/<feature-name>/plan.md` must exist
- `.specs/<feature-name>/spec.md` must exist (tasks reference spec sections for acceptance criteria)

## What to ask the user

If the user runs `/tasks` without additional context:

1. Are there any ordering constraints beyond what the plan implies? (e.g., "I need the API working before the MCP layer so I can demo it")
2. Should tasks be sized for a human developer or for an AI coding agent? (This affects granularity. Agent tasks can be smaller and more mechanical. Human tasks should be more self-contained.)

## Reading inputs

From **plan.md**: The architecture, file structure, technology decisions, and implementation patterns. Each plan section becomes one or more task groups.

From **spec.md**: The success criteria and interface definitions. These provide the acceptance criteria for each task. A task isn't done until its corresponding spec requirements are met.

## Output: `.specs/<feature-name>/tasks.md`

### Structure

Tasks are organized into **phases**. Each phase groups related tasks that build toward a milestone. Phases are sequential: you complete one phase before starting the next. Within a phase, tasks are also ordered, but tasks marked `[parallel]` can be worked on simultaneously.

```markdown
# Tasks: <feature-name>

## Phase 1: Foundation
> Milestone: Project skeleton exists, dependencies installed, database connection verified.

- [ ] 1.1 — Scaffold project directory
  **Do:** Create the directory structure from plan §6. Initialize package.json, tsconfig, and any config files.
  **Verify:** `npm install` succeeds. TypeScript compiles with no errors on an empty project.

- [ ] 1.2 — Set up database connection
  **Do:** Create the database connection module using Drizzle. Define the connection config reading from environment variables.
  **Verify:** A simple query (SELECT 1) succeeds against the local database.

## Phase 2: Data Layer
> Milestone: All schemas defined, migrations run, basic CRUD operations work.

- [ ] 2.1 — Define Drizzle schemas  [parallel]
  **Do:** Create table definitions for all entities in spec §4. Include all constraints, indexes, and enums.
  **Verify:** Migrations generate and apply cleanly. Schema matches spec §4 exactly.
```

### Task format

Each task has three parts:

**Title** — A short, action-oriented description. Start with a verb: "Create," "Implement," "Configure," "Add," "Wire up."

**Do** — What the implementor needs to build or change. Reference specific plan sections for patterns to follow and spec sections for requirements. Be concrete: name files to create, functions to write, configurations to set. An implementor should not need to re-read the full plan to execute a single task.

**Verify** — How to confirm the task is done. This should be a concrete, observable check: a test passes, a command produces expected output, a file exists with specific content, an API endpoint returns the expected response.

### Ordering principles

1. **Infrastructure before logic.** Scaffolding, database setup, and configuration come first.
2. **Data layer before service layer.** Schemas and basic queries before business rules.
3. **Core path before edge cases.** Happy path end-to-end first, then error handling and edge cases.
4. **Internal before external.** Get the system working locally before deployment and integration.
5. **Tests alongside, not after.** Each task that creates testable logic includes writing the corresponding test.

### Granularity

A well-sized task takes 1-4 hours for a human developer or produces a coherent, reviewable diff. If a task's "Do" section requires more than 5-6 sentences, it's probably too big. Split it.

For AI agent execution, tasks can be smaller and more mechanical. A task like "Implement the GET /passes endpoint" might split into "Create the route handler skeleton" and "Add query logic and response formatting."

## Quality gate

- [ ] Every plan section maps to at least one task
- [ ] Every spec interface has at least one task that implements it
- [ ] Every task has a concrete "Verify" step
- [ ] Tasks are ordered so that each task's dependencies are completed in earlier tasks
- [ ] No task requires reading the full plan to understand (it references specific sections)
- [ ] Phase milestones describe an observable, testable state
- [ ] The first phase produces something runnable (even if minimal)
