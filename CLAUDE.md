# Trellis — Plugin Context

Trellis is a Claude Code plugin for **spec-driven development**. It provides 10 composable skills that take a feature from problem framing through implementation.

## Philosophy

Every feature goes through structured phases. Each phase produces a durable markdown artifact in the specs directory (`.specs/` by default, configurable via `trellis.json`). Downstream phases inherit upstream artifacts — the spec references the pitch, the plan references the spec, tasks reference the plan, and implementation follows the tasks.

## Skill relationships

```
Foundation:     guidelines ─────────────────────────────────────────────┐
                sketch ─────────────────────────┐                       │
                                                │                       │
Pipeline:       pitch → spec → clarify → compliance → plan → tasks      │
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
- **Agents**: Generation agents (pitch-writer, spec-writer, plan-writer, task-writer, guidelines-writer, sketch-writer) run on Sonnet for cost-efficient document generation. Judge and Test Writer run on Opus for analytical tasks. All defined in `agents/` and spawned by their parent skills.
- **Scripts**: Deterministic work (prereq validation, marker extraction, criteria parsing, pipeline status, state parsing) lives in `scripts/` as standalone Python scripts that output JSON. Skills call these in pre-flight; hooks call them for event-driven checks.
- **Hooks**: Python-based validators in `hooks/` for spec structure, ambiguity markers, implementation state, and session startup status. Two-layer architecture: hooks handle orchestration (stdin JSON, relevance filtering, formatting), scripts handle data processing.
- **`trellis.json`**: Stores the configured specs directory (`specsDir`). Created by `/guidelines` on first run. All skills and hooks read from it, falling back to `.specs/` if absent.
