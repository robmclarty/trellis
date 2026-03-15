---
name: trellis:init
description: Initialize a project for Trellis by creating trellis.json and the specs directory. Use when setting up Trellis for the first time.
allowed-tools: Read, Write, Bash(mkdir:*)
---

# Init

## When to use

- "initialize trellis", "set up trellis", "init"
- First time using Trellis in a project
- Called automatically by `/trellis:guidelines` in create mode

Initialize a project for Trellis by creating `trellis.json` and the specs directory.

**Recommended effort: minimal.** Single question, two file operations.

## Behavior

Check whether `trellis.json` exists at the project root.

### If `trellis.json` does not exist

Ask the user: "Where should Trellis store spec artifacts? The default is `.specs/` — press Enter to accept or provide a custom path (e.g., `docs/specs`, `design`)."

Write their choice (or the default) to `trellis.json` at the project root:

```json
{
  "specsDir": ".specs"
}
```

Create the specs directory if it doesn't exist.

Confirm to the user: "Trellis initialized — specs directory set to `<specsDir>/`."

### If `trellis.json` already exists

Read `specsDir` from it. Confirm to the user: "Trellis is already initialized — specs directory is `<specsDir>/`."

Create the specs directory if it doesn't exist.

Do not re-ask or overwrite.
