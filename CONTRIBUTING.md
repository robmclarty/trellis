# Contributing to Trellis

## Prerequisites

- **Node.js** >= 20
- **Python 3** (for hooks and scripts)

### System tools

The linting setup uses two system-level tools not distributed through npm. Install them with Homebrew:

```bash
brew install ruff shellcheck
```

Or via other package managers:

| Tool       | pip                  | apt                       | Purpose                  |
|------------|----------------------|---------------------------|--------------------------|
| ruff       | `pip install ruff`   | `pip install ruff`        | Python linter & formatter |
| shellcheck | —                    | `apt install shellcheck`  | Shell script linter       |

## Setup

```bash
npm install
```

This installs all Node dependencies and runs a `postinstall` check that warns if `ruff` or `shellcheck` are missing.

## Linting

All linters are orchestrated through npm scripts. Run everything at once:

```bash
npm run lint
```

Or run individual linters:

| Command            | What it checks                     | Tool         |
|--------------------|------------------------------------|--------------|
| `npm run lint:json`| JSON formatting                    | Prettier     |
| `npm run lint:md`  | Markdown style                     | markdownlint |
| `npm run lint:py`  | Python lint (scripts, hooks, tests)| Ruff         |
| `npm run lint:sh`  | Shell scripts                      | ShellCheck   |

### Auto-fix

```bash
npm run lint:fix
```

This runs fixable linters (JSON, Markdown, Python). ShellCheck does not support auto-fix.

Individual fix commands are also available: `lint:json:fix`, `lint:md:fix`, `lint:py:fix`.

## Plugin validation

Trellis uses [agnix](https://github.com/nicobailon/agnix) to validate its Claude Code plugin structure:

```bash
npm run plugincheck
npm run plugincheck:fix
```
