---
name: implement
description: Pre-flight context loader for the implement skill. Use when beginning implementation of a feature.
allowed-tools: Bash(git:*), Read
user-invocable: true
---

## When to use

Trigger on: "start implementing", "trellis implement", or any request to begin implementation with pre-flight context.

## Behavior

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/parse-implement-state.py` to check for existing state
2. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-criteria.py` with the feature's tasks.md to get acceptance criteria
3. Present the pre-flight summary to the user (existing state, criteria count, pending items)
4. Delegate to `/trellis:implement` with the structured context

This command provides pre-flight structured data so the implement skill starts with JSON context instead of doing filesystem exploration.
