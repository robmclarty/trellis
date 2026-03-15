---
name: version
description: Bump the project version (major, minor, or patch) across all manifest files and add a changelog entry. Use when preparing a release.
allowed-tools: Read, Edit, Bash
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
4. `CHANGELOG.md` — new version section inserted at the top

## Steps

1. If no argument is provided, ask the user which bump type they want (major, minor, or patch).
2. Read `package.json` to get the current version.
3. Compute the new version according to the semver rules above.
4. Tell the user: "Bumping version from X.Y.Z to A.B.C"
5. Update all three manifest files using the Edit tool.
6. Run `git log --format='%s%n%n%b' <last-bump-hash>..HEAD` where `<last-bump-hash>` is the most recent commit matching `chore: bump version to` (find it with `git log --oneline --grep='chore: bump version to' -1`). Use the commit subjects and body descriptions as context to write a concise bullet-point list of significant changes for the new version entry.
7. Read `CHANGELOG.md` and insert a new version section immediately after the `# Changelog` heading (before the first existing `##` entry) using the Edit tool:
   ```
   ## A.B.C

   - Summary of change 1
   - Summary of change 2
   ```
8. Report the updated version.
9. Stage the changed files and commit with the message: `chore: bump version to A.B.C`
