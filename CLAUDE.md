# Trellis — Plugin Context

Trellis is a Claude Code plugin for **spec-driven development**. It provides 10 composable skills that take a feature from problem framing through implementation.

## Philosophy

Every feature goes through structured phases. Each phase produces a durable markdown artifact in `.specs/`. Downstream phases inherit upstream artifacts — the spec references the pitch, the plan references the spec, tasks reference the plan, and implementation follows the tasks.

## Skill relationships

```
Foundation:     guidelines ──────────────────────────────────────────────┐
                sketch ─────────────────────────┐                       │
                                                │                       │
Pipeline:       pitch → spec → clarify → compliance → plan → tasks     │
                  │       │       │          │          │       │       │
                  └───────┴───────┴──────────┴──────────┴───────┘       │
                          ↑ all inherit from guidelines ────────────────┘

Orchestration:  pipeline (runs pitch → tasks in one session)
Execution:      implement (turns tasks into working code)
```

- **Guidelines** and **Sketch** are foundational — run before starting a feature pipeline
- **Pitch → Spec → Clarify → Compliance → Plan → Tasks** is the specification pipeline, each building on the previous
- **Pipeline** orchestrates the spec pipeline as a single session (interactive or auto mode)
- **Implement** executes the spec through an oracle-driven feedback loop with machine checks and an LLM judge

## Key design decisions

- **`context: fork`**: Clarify and Compliance run in isolated contexts. They cannot ask the user questions mid-run. The pipeline skill gathers user input upfront and embeds it in the spec before invoking forked skills.
- **`.implement-state.md`**: Filesystem-based memory for the implement skill. Survives context resets and enables Ralph mode (context-fresh iterations).
- **Agents**: Judge and Test Writer are defined in `agents/` and spawned by the implement skill as isolated sub-agents for spec compliance review and test generation.
- **Hooks**: Optional validators for `.specs/` document structure, implementation state checks, and session startup status.
