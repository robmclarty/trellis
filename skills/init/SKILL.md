---
name: trellis:init
description: Initialize a project for Trellis by creating trellis.json, the specs directory, and guidelines. Use when setting up Trellis for the first time.
allowed-tools: Read, Write, Bash(mkdir:*)
---

# Init

## When to use

- "initialize trellis", "set up trellis", "init"
- First time using Trellis in a project

Initialize a project for Trellis by creating `trellis.json` and the specs directory, then run `/trellis:guidelines` to establish project guidelines.

**Recommended effort: minimal.** Single question, two file operations, then hand off to guidelines.

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

## Next step

After `trellis.json` and the specs directory are in place, run the `/trellis:guidelines` skill to create or update project guidelines.
