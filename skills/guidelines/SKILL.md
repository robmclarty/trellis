---
name: guidelines
description: Creates or updates .specs/guidelines.md with project-wide stack, conventions, and principles. Use when starting a project or when a fundamental technology decision has changed.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Task
---

# Guidelines

## When to use

- "set up guidelines", "update guidelines"
- "change our stack", "add a convention"
- Any request to establish or modify project-wide principles

Create or update the project guidelines document at `.specs/guidelines.md`.

**Recommended effort: medium.** Interview-driven with structured generation into a fixed section template.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py guidelines` and use the `specsDir` value from the JSON output. Abort if the output reports missing prerequisites.

## Modes

This skill operates in two modes depending on whether `.specs/guidelines.md` already exists.

### Create mode (no existing guidelines)

If `.specs/guidelines.md` does not exist, this is a fresh project.

#### Step 0: Choose specs directory

Before anything else, check whether `trellis.json` exists at the project root.

- **If `trellis.json` does not exist**, ask the user: "Where should Trellis store spec artifacts? The default is `.specs/` — press Enter to accept or provide a custom path (e.g., `docs/specs`, `design`)."
  - Write their choice (or the default) to `trellis.json` at the project root:
    ```json
    {
      "specsDir": ".specs"
    }
    ```
  - Create the directory if it doesn't exist.
- **If `trellis.json` already exists**, read `specsDir` from it and use that directory. Do not re-ask.

All references to `.specs/` in this skill (and all other Trellis skills) refer to the configured specs directory.

#### Step 1: Ask the user

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

## Generation

After gathering all user input via the interview, spawn the `guidelines-writer` agent. Pass it: the specs directory path and all interview responses. The agent will generate the guidelines document.

## Quality gate

- [ ] Could a new developer read this and write code that matches the project's style?
- [ ] Are there concrete examples (not just rules) for every convention?
- [ ] Is every stack decision specific (named packages, not categories)?
- [ ] Does it avoid feature-specific content? (That belongs in specs, not guidelines.)
