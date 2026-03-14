---
name: implement
description: Pre-flight context loader for the implement skill. Use when beginning implementation of a feature.
allowed-tools: Bash(git:*), Read
user-invocable: true
---

## When to use

Trigger on: "start implementing", "trellis implement", or any request to begin implementation with pre-flight context.

## Behavior

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-prereqs.py implement <feature-name>` to resolve `specsDir` and validate that the feature folder exists. Abort if prerequisites are missing. Extract the `specsDir` value from the JSON output.

2. Check for existing state: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/parse-implement-state.py {specsDir}/.state/implement-state.md`
   - If state exists: this is a **resumption**. Present the state summary (done/pending criteria, current iteration) and delegate to `/trellis:implement` to resume from the next pending criterion.
   - If state does not exist (exit code 1, "File not found"): this is a **fresh start**. This is expected — do not treat it as an error.

3. For fresh starts, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-criteria.py {specsDir}/<feature-name>/tasks.md {specsDir}/<feature-name>/spec.md` to get structured acceptance criteria.

4. Present the pre-flight summary to the user:
   - Whether this is a fresh start or resumption
   - Criteria count and list (from extract-criteria output or existing state)
   - Artifact paths found

5. Delegate to `/trellis:implement` with the structured context. The implement skill will handle Phase 0 (config questions), Phase 1 (pipeline assembly), and Phase 2 (iteration).

This command provides pre-flight structured data so the implement skill starts with JSON context instead of doing filesystem exploration.
