# Trellis

A Claude Code plugin that bundles composable skills for spec-driven development. Take a feature from problem framing through implementation using structured, repeatable phases.

## Install

```
claude plugin add robmclarty/trellis
```

## Skills

Trellis provides 10 skills organized into three groups: foundation, specification pipeline, and execution.

### Foundation

| Skill | Command | Description |
|-------|---------|-------------|
| **Guidelines** | `/guidelines` | Establish project-wide stack, conventions, and principles at `.specs/guidelines.md`. Run this first. |
| **Sketch** | `/sketch` | Run a timeboxed experiment to test a technical hypothesis. Produces a document in `.specs/sketches/`. |

### Specification pipeline

These skills run in sequence. Each builds on the output of the previous one.

| Skill | Command | Description |
|-------|---------|-------------|
| **Pitch** | `/pitch` | Frame a problem with constraints, appetite, and solution shape. Produces `.specs/<feature>/pitch.md`. |
| **Spec** | `/spec` | Write a full functional specification defining what the system does and why. Produces `.specs/<feature>/spec.md`. |
| **Clarify** | `/clarify` | Review the spec for ambiguities across six categories and resolve them in place. |
| **Compliance** | `/compliance` | Evaluate the spec against applicable regulations (GDPR, FERPA, FIPPA, COPPA, SOC 2). Produces `.specs/<feature>/compliance.md`. |
| **Plan** | `/plan` | Translate the spec into concrete architecture, technology, and code decisions. Produces `.specs/<feature>/plan.md`. |
| **Tasks** | `/tasks` | Decompose the plan into discrete, ordered, verifiable units of work. Produces `.specs/<feature>/tasks.md`. |

### Execution

| Skill | Command | Description |
|-------|---------|-------------|
| **Pipeline** | `/pipeline` | Orchestrate the full pipeline from pitch through tasks in one session. Supports interactive and automatic modes. |
| **Implement** | `/implement` | Turn specs, sketches, or freeform instructions into working code through iterative oracle-driven feedback loops. |

## Typical workflow

```
/guidelines          # once per project
/sketch              # optional: explore unknowns
/pitch               # frame the feature
/spec                # define what it does
/clarify             # resolve ambiguities
/compliance          # if regulated data is involved
/plan                # decide how to build it
/tasks               # break it into work items
/implement           # write the code
```

Or use `/pipeline` to run pitch through tasks in one pass.

## Project structure

All artifacts live under `.specs/` in your project:

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

## License

MIT
