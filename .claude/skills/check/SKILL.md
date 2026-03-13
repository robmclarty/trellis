---
name: check
description: Use when user wants to Run all project checks (lint, tests, plugin validation)
disable-model-invocation: true
allowed-tools: Bash(npm run *), Bash(npm test *), Bash(python3 tests/*), Bash(bash tests/*)
---

Run all project checks in sequence and report a summary:

1. `npm run lint` — lint all file types
2. `npm test` — run the test suite
3. `npm run plugincheck` — validate plugin structure

If any step fails, continue running the remaining checks before reporting. Summarize all results at the end.
