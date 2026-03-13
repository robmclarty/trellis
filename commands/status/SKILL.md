---
name: status
description: Show pipeline status for all features
allowed-tools: Bash, Read
user-invocable: true
---

## When to use

Trigger on: "show status", "pipeline status", "what's the state of specs", "trellis status", or any request to see an overview of feature progress.

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pipeline-status.py` and capture the JSON output.

## Behavior

Format the JSON output as a user-friendly status display:

1. Show whether `guidelines.md` exists
2. For each feature, show which stages are complete (pitch, spec, plan, tasks, compliance) using checkmarks
3. If all core stages (pitch, spec, plan, tasks) are complete, note it's ready for `/trellis:implement`
4. Show sketch count if any exist

Present the output in a clear, readable format. Do not add commentary beyond the status data.
