---
name: build-with-batch
description: Execute a Trellis task list using Claude Code's /batch command for bulk, patterned changes across many files. Use when the user says "build with batch" or when a feature involves repetitive changes across dozens or hundreds of files (e.g., migrating from one library to another, applying naming conventions, adding error handling patterns). Reads `.specs/<feature>/tasks.md` produced by the tasks skill. Translates the task list into one or more /batch invocations with worktree-isolated parallel agents.
---

# Build with Batch

Execute a Trellis task list using Claude Code's built-in `/batch` command. This skill translates structured task lists into `/batch` instructions for bulk, patterned changes across many files in parallel.

## When to use

Use this for large-scale, repetitive changes where:
- The same pattern of change applies across dozens or hundreds of files
- Each file's changes are independent of the others (no ordering dependencies)
- The changes follow a recognizable pattern with local variations per file

Classic examples: ORM migration (Sequelize to Drizzle), dependency swaps (lodash to native), convention enforcement (adding error handling to all endpoints), import path updates after a restructure.

Do NOT use this for:
- Features with tight inter-task dependencies (use `build-with-subagents` instead)
- Tasks where file A's changes depend on file B's new output
- Exploratory refactoring where the end state isn't well-defined
- Fewer than 5 files to change (just execute inline)

## Input

The skill expects:
- `.specs/<feature>/tasks.md` — the task list (may describe the pattern + a manifest of affected files, or may describe the change abstractly and let /batch discover affected files)
- `.specs/guidelines.md` — project conventions
- `.specs/<feature>/plan.md` — architecture decisions relevant to the migration

## Step 1: Analyze the task list

Read `tasks.md` and determine the migration shape:

**Pattern extraction:** Identify the repeating pattern. What is being replaced with what? What are the rules? For example: "Replace all `Model.findAll()` calls with `repo.findMany()`, update imports from `@models/` to `@repos/`, preserve where clauses and ordering."

**Scope assessment:** Determine roughly how many files are affected. If the task list includes an explicit manifest of files, use it. If not, note that `/batch` will discover them during its research phase.

**Chunk decision:** `/batch` handles 5-30 units per invocation. If the scope clearly exceeds 30 units (e.g., 200 files across 40 packages), plan multiple `/batch` runs. Group by package, directory, or logical module.

## Step 2: Build the batch instruction

Construct a single, precise natural language instruction for `/batch`. This instruction should include:

1. **The overall goal** in one sentence.
2. **The specific transformation rules** — every pattern mapping, written as concrete before/after examples.
3. **What to preserve** — explicitly state what should NOT change (e.g., "preserve all existing where clauses, transaction wrappers, and error handling").
4. **Verification** — what each worker should check after making changes (e.g., "run type-check on the modified file", "ensure no remaining imports from the old module").
5. **Conventions** — any project-specific rules from guidelines.md that affect the transformation (naming conventions, import ordering, etc.).

Keep the instruction under 2,000 tokens. `/batch` workers each get their own copy, so brevity matters for token efficiency.

### Example instruction format

```
Replace all Sequelize ORM usage with repository layer calls backed by Drizzle.

TRANSFORMATION RULES:
- Model.findAll({ where, order }) → repo.findMany({ where, orderBy })
- Model.findOne({ where }) → repo.findOne({ where })
- Model.findByPk(id) → repo.findById(id)
- Model.create(data) → repo.create(data)
- Model.update(data, { where }) → repo.update({ where, data })
- Model.destroy({ where }) → repo.remove({ where })
- Sequelize.Op operators → Drizzle equivalents (Op.gt → gt(), Op.in → inArray(), etc.)
- Include associations → use repo join methods or separate queries per plan.md

IMPORTS:
- Remove: import { ModelName } from '@models/modelName'
- Add: import { modelNameRepo } from '@repos/modelName'

PRESERVE:
- All existing transaction wrappers (convert sequelize.transaction to db.transaction)
- Error handling and try/catch blocks
- Business logic and control flow

VERIFY:
- Run `npx tsc --noEmit` on the modified file
- Ensure zero remaining imports from @models/ or sequelize
```

## Step 3: Execute

**If scope fits in one /batch run (≤30 units):**

Tell the user:
```
I'll now run /batch with the following instruction. Review the plan it
proposes before approving execution.
```

Then invoke `/batch` with the constructed instruction. `/batch` will:
1. Research the codebase and decompose into units
2. Present a plan for approval
3. Spawn parallel workers in isolated worktrees
4. Each worker implements, verifies, commits, and opens a PR

**If scope exceeds 30 units (multiple /batch runs needed):**

1. Present the chunking plan to the user: "This migration spans approximately N files across M packages. I'll run /batch in K chunks, grouped by [grouping strategy]."
2. Execute chunk 1 via `/batch`.
3. After chunk 1 completes, capture learnings:
   - Which patterns worked cleanly?
   - Which patterns needed manual intervention?
   - Any unexpected variations discovered?
4. Append learnings to `.specs/<feature>/learnings.md`.
5. If patterns were discovered that require updating the instruction, refine it for the next chunk.
6. Execute subsequent chunks, incorporating accumulated learnings into each instruction.
7. After all chunks complete, collect any failed units across all runs into a retry manifest.

## Step 4: Report results

After all `/batch` runs complete, summarize:
- Total files changed: N
- Successful PRs: N (with links if available)
- Failed units: N (with file paths and failure reasons)
- Learnings captured at `.specs/<feature>/learnings.md`

If failed units exist, suggest either:
- Re-running `/batch` on just the failed files with a more specific instruction informed by the failure reasons
- Manual intervention for edge cases that don't fit the pattern

## Pre-scan optimization (optional)

For very large migrations, a deterministic pre-scan can save significant tokens by giving `/batch` an explicit file manifest instead of making it discover affected files:

```bash
# Example: find all files importing from sequelize
grep -rl "from 'sequelize'" src/ --include='*.ts' > /tmp/sequelize-files.txt
wc -l /tmp/sequelize-files.txt
```

If you can determine the affected files cheaply via grep/ripgrep, do so and include the file list in the `/batch` instruction: "Apply the following changes to these specific files: [list]". This makes the research phase faster and more accurate.

## Important constraints

- `/batch` requires that each unit of work be independently mergeable. If your migration has a "shared foundation" step (e.g., creating the repository layer that all files will import), do that in a regular session FIRST, merge it, and THEN run `/batch` for the bulk file-by-file changes.
- Each `/batch` worker runs in its own git worktree. Workers cannot see each other's changes. This is fine for independent file transformations but breaks if file A needs to import something that file B creates.
- The user must approve the plan before `/batch` spawns workers. Don't skip this step.
- `/batch` workers can open PRs automatically. If the project doesn't use PR-based workflow, instruct workers to commit to their worktree branches without PR creation, and the user can merge manually.
- Token cost scales linearly with the number of units. Each worker opens its own context window. For 30 units, expect roughly 30x the cost of a single implementation session. Warn the user about approximate costs for large runs.
