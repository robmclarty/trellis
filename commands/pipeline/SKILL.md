---
name: trellis:pipeline-start
description: Pre-flight context for pipeline skill
allowed-tools: Bash, Read
user-invocable: true
---

## When to use

Trigger on: "start the pipeline", "run the pipeline", "trellis pipeline", or any request to begin the full spec pipeline for a feature.

## Behavior

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pipeline-status.py` to get current state
2. Present the status summary to the user
3. Delegate to `/trellis:pipeline` with the structured context from the script output

This command provides pre-flight structured data so the pipeline skill starts with JSON context instead of doing filesystem exploration.
