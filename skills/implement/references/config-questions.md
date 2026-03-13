# Implementation configuration questions

Before writing any code, collect the user's tooling context. Do not assume any
specific language, framework, linter, or type checker. Ask the following:

## Required questions

1. **What type-check command should the pipeline run?** Examples: `tsc --noEmit`,
   `pnpm tsc --noEmit`, `pyright`, `mypy --strict`, `flow check`, `none`. If the
   user says "none," skip the type-check stage entirely.

2. **What lint/format commands should the pipeline run?** The user may have one or
   more tools. Examples: `biome check --fix && biome check`, `eslint --fix . &&
   eslint .`, `prettier --write . && prettier --check .`, `ruff check --fix . &&
   ruff check .`, `oxlint`, `stylelint`, or any combination. Accept a list. If
   the user says "none," skip the lint stage.

3. **What build command should the pipeline run?** Examples: `pnpm build`,
   `npm run build`, `cargo build`, `go build ./...`, `none`. If "none," skip it.

4. **What test command should the pipeline run?** Examples: `vitest run`,
   `jest`, `pytest`, `go test ./...`, `none`. If "none," tests are only run
   when the test writer sub-agent creates them (scoped to the new test files).

## Optional questions (ask if relevant based on input type)

5. **Package manager?** `pnpm`, `npm`, `yarn`, `bun`, `cargo`, `pip`, `go mod`,
   etc. Needed for install commands and script invocation.

6. **Ralph mode** — Auto-detected from the `with ralph` invocation modifier.
   Do not ask this as a question. If `with ralph` was passed, set
   `Ralph mode: on` in `.implement-state.md`. Otherwise, set it to `off`.

7. **Enable Promptfoo?** If yes, generate Promptfoo eval configs alongside the
   judge for repeatable evaluations. See the Promptfoo section in
   `references/oracle-pipeline.md`.

8. **Open Spec format?** If the spec uses Open Spec structure (look for
   `validation_criteria`, `constraints`, `scope` fields), use its structure
   directly rather than re-analyzing.

Store all configuration answers in `.implement-state.md` under a `## Config`
section so they survive context resets.
