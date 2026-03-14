# The `{specsDir}/{feature}/implement-state.md` file

This is the canonical record of the implementation session. It serves as
persistent memory across context resets.

## Structure

```markdown
# Implementation State

## Input
- Type: feature-folder | sketch | inline | hybrid
- Feature: <folder name or "N/A">
- Sketches: <list of sketch slugs or "N/A">
- Paths: <list of artifact paths loaded>

## Branch
- Original: <branch name before implementation>
- Working: <current branch, e.g., sketch/drizzle-multi-tenant>

## Config
- Package manager: pnpm
- Type-check: `pnpm tsc --noEmit`
- Lint: `biome check --fix && biome check`
- Build: `pnpm build`
- Test: `vitest run`
- Ralph mode: off
- Promptfoo: off

## Oracle Pipeline
- [x] typecheck: `pnpm tsc --noEmit`
- [x] lint: `biome check --fix && biome check`
- [x] build: `pnpm build`
- [ ] test: (enabled when test writer creates files)
- [x] judge: sub-agent

## Acceptance Criteria
- [x] AC-1 (task 1.1): Scaffold project directory (done, iteration 1)
- [x] AC-2 (task 1.2): Set up database connection (done, iteration 1)
- [ ] AC-3 (task 2.1): Define Drizzle schemas (pending)

## Constraints
- TypeScript strict mode
- Fastify framework
- Functional style, no classes
- ...

## Unknowns / Assumptions
- Assumed X because spec didn't specify
- ...

## Iteration Log
### Iteration 1
- Scope: tasks 1.1, 1.2 (foundation)
- Result: pass, both tasks completed
- Oracle output: typecheck clean, lint had 2 auto-fixed issues, build clean
```

## JSON interchange format

Third-party tools can consume the state file as structured JSON by running:

```bash
python3 scripts/parse-implement-state.py {specsDir}/{feature}/implement-state.md
```

The output conforms to `schemas/implement-state.schema.json`. Key fields:

- `criteria[]` — Array of `{ id, taskRef, summary, status, iteration }`
- `pendingCount` / `doneCount` — Quick completion check
- `nextPendingId` — The next criterion to work on
- `pipeline[]` — Oracle stages with commands and enabled state
- `config` — User-provided toolchain configuration
- `iteration` — Number of completed iterations
