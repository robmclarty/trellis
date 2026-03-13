# Trellis

A Claude Code plugin that bundles composable skills for spec-driven development. Take a feature from problem framing through implementation using structured, repeatable phases.

## Install

```
/plugin marketplace add robmclarty/trellis
```

## Skills

Trellis provides 10 skills organized into three groups: foundation, specification pipeline, and execution.

### Foundation

| Skill | Command | Description |
|-------|---------|-------------|
| **Project Guidelines** | `/trellis:guidelines` | Establish project-wide stack, conventions, and principles at `.specs/guidelines.md`. Run this first. |
| **Technical Sketch** | `/trellis:sketch` | Run a timeboxed experiment to test a technical hypothesis. Produces a document in `.specs/sketches/`. |

### Specification pipeline

These skills run in sequence. Each builds on the output of the previous one.

| Skill | Command | Description |
|-------|---------|-------------|
| **Feature Pitch** | `/trellis:pitch` | Frame a problem with constraints, appetite, and solution shape. Produces `.specs/<feature>/pitch.md`. |
| **Functional Spec** | `/trellis:spec` | Write a full functional specification defining what the system does and why. Produces `.specs/<feature>/spec.md`. |
| **Spec Clarifier** | `/trellis:clarify` | Review the spec for ambiguities across six categories and resolve them in place. |
| **Compliance Review** | `/trellis:compliance` | Evaluate the spec against applicable regulations (GDPR, FERPA, FIPPA, COPPA, SOC 2). Produces `.specs/<feature>/compliance.md`. |
| **Implementation Plan** | `/trellis:plan` | Translate the spec into concrete architecture, technology, and code decisions. Produces `.specs/<feature>/plan.md`. |
| **Task Breakdown** | `/trellis:tasks` | Decompose the plan into discrete, ordered, verifiable units of work. Produces `.specs/<feature>/tasks.md`. |

### Execution

| Skill | Command | Description |
|-------|---------|-------------|
| **Spec Pipeline** | `/trellis:pipeline` | Orchestrate the full pipeline from pitch through tasks in one session. Supports interactive and automatic modes. |
| **Implement** | `/trellis:implement` | Turn specs, sketches, or freeform instructions into working code through iterative oracle-driven feedback loops. |

## Typical workflow

```
/trellis:guidelines          # once per project
/trellis:sketch              # optional: explore unknowns
/trellis:pitch               # frame the feature
/trellis:spec                # define what it does
/trellis:clarify             # resolve ambiguities
/trellis:compliance          # if regulated data is involved
/trellis:plan                # decide how to build it
/trellis:tasks               # break it into work items
/trellis:implement           # write the code
```

Or use `/trellis:pipeline` to run pitch through tasks in one pass.

## Project structure

All artifacts live under a specs directory in your project (`.specs/` by default):

```
.specs/
  guidelines.md
  sketches/
    drizzle-multi-tenant.md
    websocket-vs-polling.md
  my-feature/
    pitch.md
    spec.md
    compliance.md
    plan.md
    tasks.md
```

See `examples/` for a complete sample `.specs/` directory showing what finished pipeline output looks like.

### Custom specs directory

When you first run `/trellis:guidelines`, you'll be asked where to store spec artifacts. The default is `.specs/`, but you can provide any path (e.g., `docs/specs`, `design`). Your choice is saved to `trellis.json` at the project root:

```json
{
  "specsDir": ".specs"
}
```

All skills and hooks read from this file, falling back to `.specs/` if it doesn't exist.

## External integrations

The `implement` skill can optionally integrate with external tools:

### Ralph

[Ralph](https://github.com/anthropics/ralph) is a CLI tool that provides context-resilient iteration for long-running Claude Code sessions. It works by killing and restarting the agent's context window at iteration boundaries, using `.implement-state.md` as the handoff mechanism.

**When to use:** Large implementations with 10+ acceptance criteria or many files where context degradation becomes a concern.

**Install:** Follow the instructions at the Ralph repository. The `ralph` CLI must be available on your PATH.

**Invocation:** `ralph run --state .implement-state.md --command "/trellis:implement <feature-name>"`

### Promptfoo

[Promptfoo](https://www.promptfoo.dev/) is an eval framework for LLM outputs. The implement skill can generate Promptfoo configs from acceptance criteria for repeatable, versioned evaluation of implementation quality.

**When to use:** Teams that build similar features often and want to codify judge criteria, A/B test prompts, or run regression checks against spec criteria.

**Install:** `npm install -g promptfoo` or see the [Promptfoo docs](https://www.promptfoo.dev/docs/installation/).

### Open Spec

[Open Spec](https://github.com/open-spec/open-spec) is a structured requirements format designed for agentic interpretation. If your spec uses Open Spec format (fields like `validation_criteria`, `constraints`, `scope`), the implement skill uses its structure directly for more reliable criteria extraction.

## Agents

Trellis includes two built-in agents used by the implement skill:

| Agent | Description |
|-------|-------------|
| **Judge** | Reviews implementation against specifications for intent alignment. Final gate in the oracle pipeline. |
| **Test Writer** | Writes targeted tests for tricky logic from spec criteria before implementation exists. |

These agents are defined in `agents/` and can be referenced by name from the implement skill.

## Hooks

Trellis includes optional hooks for document validation and workflow enforcement:

| Hook | Trigger | Description |
|------|---------|-------------|
| `validate-spec-structure` | PostToolUse (Write/Edit) | Validates `.specs/` documents have required sections |
| `check-implement-state` | PreToolUse (git commit) | Warns if acceptance criteria are incomplete |
| `session-start` | SessionStart | Shows pipeline status for features in `.specs/` |

## License

MIT
