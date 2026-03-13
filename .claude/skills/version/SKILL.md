---
name: version
description: Bump the project version (major, minor, or patch) across all manifest files. Use when preparing a release.
allowed-tools: Read, Edit
---

Bump the project version using semver. Accepts one argument: `major`, `minor`, or `patch`.

## Semver rules

Given a version `MAJOR.MINOR.PATCH`:
- `patch` → increment PATCH, e.g. 0.4.6 → 0.4.7
- `minor` → increment MINOR, reset PATCH, e.g. 0.4.6 → 0.5.0
- `major` → increment MAJOR, reset MINOR and PATCH, e.g. 0.4.6 → 1.0.0

## Files to update

All three files must be updated to the new version:

1. `package.json` — top-level `"version"` field
2. `.claude-plugin/plugin.json` — top-level `"version"` field
3. `.claude-plugin/marketplace.json` — `"version"` inside `plugins[0]`

## Steps

1. If no argument is provided, ask the user which bump type they want (major, minor, or patch).
2. Read `package.json` to get the current version.
3. Compute the new version according to the semver rules above.
4. Tell the user: "Bumping version from X.Y.Z to A.B.C"
5. Update all three files using the Edit tool.
6. Report the updated version.

Do NOT commit the changes — the user will decide when to commit.
