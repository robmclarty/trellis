---
name: lint
description: Run all project linters (JSON, Markdown, Python, shell). Use when checking code style and formatting.
disable-model-invocation: true
allowed-tools: Bash(npm run lint*), Bash(npm run plugincheck*)
---

Run `npm run lint` to check all file types. Report the results.

If there are fixable errors and the user asks to fix them, run `npm run lint:fix`.

Individual linters can also be run:
- `npm run lint:json` — JSON syntax validation
- `npm run lint:md` — markdownlint on Markdown files
- `npm run lint:py` — Ruff on Python files
- `npm run lint:sh` — ShellCheck on shell scripts
- `npm run plugincheck` — agnix plugin structure validation
