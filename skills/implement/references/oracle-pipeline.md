# Oracle Pipeline Reference

This document covers the mechanics of the feedback loop, the judge sub-agent,
and integration with external tools.

## Pipeline execution mechanics

### How the pipeline is configured

The oracle pipeline is NOT auto-discovered. It is assembled from the user's
answers during Phase 0, Step 2. The user tells us what tools they use for
type-checking, linting, building, and testing. We run exactly those commands,
nothing more.

This makes the pipeline language- and framework-agnostic. A TypeScript project
using Biome, a Python project using Ruff and MyPy, a Rust project using
`cargo clippy`, and a Go project using `golangci-lint` all work the same way:
the user provides the commands, and we run them.

### Parsing oracle output

Each oracle stage produces structured output. The key skill is extracting
actionable feedback, not just detecting pass/fail.

**Type-checker output (varies by tool):**

TypeScript (tsc):
```
src/routes/passes.ts(42,7): error TS2345: Argument of type 'string' is not
assignable to parameter of type 'number'.
```

Python (mypy):
```
src/services/auth.py:18: error: Argument 1 to "verify" has incompatible
type "str"; expected "int"  [arg-type]
```

Python (pyright):
```
src/services/auth.py:18:5 - error: Argument of type "str" is not assignable
to parameter of type "int"
```

In all cases, extract: file, line, error message. Fix the specific line. Do not
rewrite the whole file to fix a type error.

**Linter output (varies by tool):**

Biome:
```
src/services/auth.ts:18:5 lint/suspicious/noExplicitAny ━━━━━━━━━
  Unexpected any. Specify a different type.
```

ESLint:
```
src/services/auth.ts:18:5  error  Unexpected any value  @typescript-eslint/no-explicit-any
```

Ruff:
```
src/services/auth.py:18:5: E501 Line too long (120 > 88)
```

OxLint:
```
× eslint(no-unused-vars): 'foo' is defined but never used.
  ╭─[src/services/auth.ts:18:5]
```

Extract: file, line, rule name. If the auto-fix pass didn't resolve it, the fix
requires a judgment call.

**Build output:**
Build errors are usually downstream of type errors. If the build fails but
type-check passed, the problem is likely in the build config, not the code.
Read the build error carefully before changing source files.

**Test output:**
```
 FAIL  src/services/passes.test.ts > createPass > rejects expired pass type
   AssertionError: expected 'active' to be 'rejected'
```
Extract: test name, expected vs. actual, file. This tells you exactly what
behavior is wrong.

### Stage interaction rules

- **Lint-fix before lint.** Always run the auto-fixer first, then the checker.
  The user's lint config may include both as a combined command (e.g.,
  `biome check --fix && biome check`). If they gave separate commands, run fix
  first.
- **Don't skip ahead.** If type-check fails, don't run the build. Fix types
  first. The pipeline is ordered so that later stages assume earlier stages
  pass.
- **Re-run from the fixed stage, not from the top,** unless your fix changed
  something structural (new files, moved modules, changed exports). Use
  judgment.

### Timeout handling

If any oracle stage takes longer than 60 seconds, something is likely wrong
(infinite loop, missing dependency, misconfigured build). Kill it and report
the issue rather than waiting.

---

## The judge sub-agent

See `references/judge-agent.md` for the full judge specification, system
prompt, output format, and interpretation guide.

---

## Integration with external tools

The implement skill is designed as a self-contained loop, but it can compose
with external tools for better performance or consistency. These integrations
are opt-in: the user enables them during Phase 0 configuration.

### Ralph mode

The Ralph pattern addresses context rot by restarting the agent with a fresh
context window on each iteration. The implement skill supports this through
the `.implement-state.md` file, which serves as filesystem-based memory.

**How it works when enabled:**

Ralph mode is activated via `/implement <feature> with ralph`. After Phase 0
and Phase 1 complete interactively, the skill launches the bundled loop script
(`scripts/ralph-loop.sh`), which manages the iteration lifecycle:

1. Before each iteration, the loop script runs pre-flight scripts and writes
   `.implement-preflight.json` — Claude reads this instead of running python3
2. The loop script generates `.claude/settings.local.json` with scoped
   permissions derived from the oracle pipeline config
3. Each iteration runs `claude -p` (no `--dangerously-skip-permissions`) with
   `/trellis:implement <feature-name>`
4. The implement skill writes all progress to `.implement-state.md` before
   completing each iteration
5. The loop script parses `.implement-state.md` between iterations to check
   completion
6. On restart, the skill reads `.implement-preflight.json`, finds pending
   criteria, and resumes

**When to use it:** Large implementations with 10+ acceptance criteria or work
spanning many files. For small implementations (2-3 criteria), skip it.

**What Ralph adds:** Protection against context degradation and least-privilege
security. Quality stays consistent across all iterations because each one
starts fresh, and scoped permissions prevent unintended command execution.

### Promptfoo

Promptfoo is an eval framework that can supplement or replace the LLM judge
for repeatable checks. The user enables it during Phase 0.

Where Promptfoo fits in:

- **Replacing the judge for repeatable checks.** If the team builds similar
  features often, codify the judge's criteria as Promptfoo assertions and run
  them as a pipeline stage.
- **A/B testing prompts.** If acceptance criteria are subjective (e.g., "error
  messages should be clear"), Promptfoo can compare implementations using
  `llm-rubric` assertions.
- **Regression testing specs.** After implementation, export the acceptance
  criteria as a Promptfoo eval config. Future changes can be tested against
  the same criteria to catch drift.

Example Promptfoo config generated from the acceptance criteria:

```yaml
prompts:
  - file://spec-judge-prompt.txt

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514

tests:
  - vars:
      spec: file://specs/my-spec.md
      changes: file://current-changes.txt
    assert:
      - type: llm-rubric
        value: |
          All acceptance criteria from the spec are satisfied.
          No constraint violations. No scope creep.
      - type: contains
        value: "VERDICT: PASS"
```

When Promptfoo is enabled, the implement skill:
1. Generates a `promptfoo.yaml` config from the acceptance criteria during
   Phase 1
2. Runs `promptfoo eval` as an additional pipeline stage (after tests, before
   or alongside the judge)
3. Stores results for the user to review

**What Promptfoo adds:** Repeatability, history tracking, CI/CD integration.
The judge sub-agent gives a one-shot answer. Promptfoo gives a versioned record.

### Open Spec format

Open Spec is a structured requirements format designed for agentic
interpretation. If the user indicates their spec uses Open Spec format (or the
skill detects fields like `validation_criteria`, `constraints`, `scope`), use
its structure directly rather than re-analyzing.

What Open Spec gives you:

- **Machine-parseable acceptance criteria.** Open Spec's `validation_criteria`
  section has explicit pass/fail conditions. Phase 0 can extract these more
  reliably than from prose.
- **Explicit scope boundaries.** Prevents the "guess at scope" problem.
- **Composability with Ralph.** Open Spec + Ralph work well as a pair: the
  spec provides the "what" and Ralph provides the iteration resilience.
  Use `/implement <feature> with ralph` to activate.

---

## Tuning the pipeline for specific projects

The pipeline adapts based on the user's configuration. Here are patterns for
common setups.

### Monorepo (NX, Turborepo)

Scope checks to the affected packages. Instead of `pnpm build`, the user
should provide something like `pnpm nx run <project>:build` or
`pnpm turbo run build --filter=<package>`.

### No type system

If the user says "none" for type-check, lean more heavily on the linter and
the judge. Consider suggesting a `node --check` or `python -m py_compile`
stage to catch syntax errors if the user doesn't already have something.

### Projects with extensive existing tests

If the test command runs hundreds of tests, suggest the user provide a scoped
test command. Instead of `vitest run` (all tests), use something like
`vitest run src/services/newModule.test.ts`. Only run the full suite in
Phase 3 as a final regression check.

### Database migrations

If the spec involves schema changes, suggest the user add a migration check
as a custom stage:
```bash
pnpm drizzle-kit generate  # should succeed
pnpm drizzle-kit check     # should report no drift
```

### MCP servers

If the spec is for an MCP server, suggest a validation stage that starts the
server and calls `tools/list` to verify the tool manifest matches what the
spec defines.

### CSS / styling projects

If the user's lint config includes stylelint, it runs as part of the lint
stage alongside any other linters. Multiple lint tools run in sequence as a
single stage.
