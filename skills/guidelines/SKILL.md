---
name: guidelines
description: Creates or updates the project guidelines document at .specs/guidelines.md. Use when starting a new project, establishing stack and convention decisions, or when a fundamental technology or pattern decision has changed. Triggers on "set up guidelines", "update guidelines", "change our stack", "add a convention", or any request to establish or modify project-wide principles.
---

# Guidelines

Create or update the project guidelines document at `.specs/guidelines.md`.

## Purpose

Establish the non-negotiable principles that govern all work in this project. Guidelines are the foundation every other phase inherits from. They define how code should look, feel, and behave regardless of what feature is being built.

## Modes

This skill operates in two modes depending on whether `.specs/guidelines.md` already exists.

### Create mode (no existing guidelines)

If `.specs/guidelines.md` does not exist, this is a fresh project. Ask the user:

1. What is the tech stack? (language, runtime, framework, core libraries)
2. What architectural style do they prefer? (functional, OOP, procedural, hybrid)
3. Any hard conventions? (naming, file layout, error handling patterns)
4. What's the testing philosophy? (when to test, what to skip, coverage attitude)
5. Deployment and infrastructure constraints?

If the user provides a description or the project already has code, infer what you can and confirm with them.

### Update mode (existing guidelines)

If `.specs/guidelines.md` already exists, read it first. Then ask the user:

1. What changed? (new library, dropped dependency, revised convention, infrastructure shift)
2. Why? (one sentence is fine; this helps evaluate downstream impact)

Apply the changes surgically. Do not rewrite sections that haven't changed. For each change:

- Update the affected section in place
- If a new pattern or snippet is needed, add it alongside existing ones (or replace if the old pattern is obsolete)
- Add a brief changelog entry at the bottom of the document under a `## Changelog` section, formatted as:

```markdown
## Changelog

- **YYYY-MM-DD** — Replaced Express with Fastify as HTTP framework. Updated route pattern examples.
- **YYYY-MM-DD** — Added Zod validation conventions and example snippets.
```

After updating, scan the rest of the guidelines for anything that conflicts with the change. A stack swap (e.g., switching ORMs) may ripple into Patterns, Testing, and Infrastructure sections. Flag any inconsistencies and fix them.

**Downstream impact:** If the change affects existing feature specs or plans, note which features under `.specs/` might need review. Don't modify them automatically, but tell the user: "This change may affect the plan for `hall-pass-extraction` since it references the old ORM pattern in §4."

## Output: `.specs/guidelines.md`

Write a single markdown document with the following sections. Be concrete and opinionated. Every section should include examples, not just rules. A new contributor (or an LLM) reading this document should be able to write code that looks like it belongs in this project.

Reference the example files in this skill's `examples/` directory for the level of concreteness expected in the Patterns section. These are illustrative; the actual patterns should match the user's stack.

### Sections

**Stack** — Language, runtime, framework, core libraries. Name specific packages. "Fastify" not "a web framework." Include version constraints only if they matter.

**Architecture** — The structural patterns used across the project. Module organization, dependency direction, how layers communicate. If the project is a monorepo, describe the workspace layout. If it uses a specific pattern (hexagonal, layered, feature-sliced), name it and show a concrete example of how a module is structured.

**Conventions** — Naming (variables, functions, types, files, directories), code style preferences, import ordering, error handling approach. Show right and wrong examples side by side where helpful.

**Patterns** — 2-4 concrete code snippets showing the preferred way to do common things in this project. These are not abstract descriptions. They are copy-paste-and-adapt templates. Examples: how to define a route, how to define a schema, how to structure a service function, how to handle errors at boundaries.

**Testing** — When tests appear in the development process, what gets tested and what doesn't, preferred test structure, any frameworks or conventions. Be honest about the team's actual practice, not an aspirational ideal.

**Infrastructure** — Deployment model, CI/CD expectations, environment management, any cloud or hosting constraints.

## Quality gate

- [ ] Could a new developer read this and write code that matches the project's style?
- [ ] Are there concrete examples (not just rules) for every convention?
- [ ] Is every stack decision specific (named packages, not categories)?
- [ ] Does it avoid feature-specific content? (That belongs in specs, not guidelines.)
