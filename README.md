# Trellis

A Claude Code plugin that bundles composable skills for spec-driven development. Take a feature from problem framing through implementation using structured, repeatable phases.

## Cognitive sovereignty

There is a growing trend among AI users: at some point, people stop choosing and start following whatever the LLM suggests. The tool that was supposed to augment human thinking quietly replaces it. Trellis is designed to resist this.

The pipeline moves deliberately from vague to specific, from high-level framing to concrete implementation details. At each stage — pitch, spec, clarify, compliance, plan, tasks — you produce a human-readable artifact that you can audit, edit, and reshape before anything downstream consumes it. The LLM drafts; you decide.

This matters because the artifacts are written in plain language, not code. You don't need to trace execution paths or parse diffs to understand what's being proposed. A pitch is a paragraph about a problem. A spec is a structured description of behavior. You can read them, disagree with them, and rewrite them — either by editing the markdown directly or by vibing with the LLM to refine its output. Every question Trellis asks during guidelines setup, every answer you give during a pipeline run, every small tweak you make to a spec section — these are the control surfaces that keep human intention in the driver's seat.

Your role shifts, but it doesn't shrink. You are no longer the one writing every line of code — you are the one conducting the entire effort. Like a construction foreman who doesn't lay every brick but ensures the building matches the blueprint, or a conductor who doesn't play every instrument but shapes the performance, your job is to orchestrate the whole symphony, not just play one of its measures. The work is still yours. The vision is still yours. The decisions that matter are still yours.

Trellis makes this practical by giving you meaningful checkpoints where your input actually changes the outcome. Skip them and the LLM will fill in the blanks with its best guess (every autonomous decision is tagged `[AUTO]` so you can find them). Engage with them and you steer generation toward your intent at every level of detail. The choice is always yours — and that's the point.

## Install

```bash
/plugin marketplace add robmclarty/trellis
```

## Skills

Trellis provides 10 skills organized into three groups: foundation, specification pipeline, and execution.

### Foundation

- `/trellis:guidelines`
  Establish project-wide stack, conventions, and principles at `.specs/guidelines.md`. Run this first.
- `/trellis:sketch`
  Run a timeboxed experiment to test a technical hypothesis. Produces a document in `.specs/sketches/`.

### Specification pipeline

These skills run in sequence. Each builds on the output of the previous one.

- `/trellis:pitch`
  Frame a problem with constraints, appetite, and solution shape. Produces `.specs/<feature>/pitch.md`.
- `/trellis:spec`
  Write a full functional specification defining what the system does and why. Produces `.specs/<feature>/spec.md`.
- `/trellis:clarify`
  Review the spec for ambiguities across six categories and resolve them in place.
- `/trellis:compliance`
  Evaluate the spec against applicable regulations (GDPR, FERPA, FIPPA, COPPA, SOC 2). Produces `.specs/<feature>/compliance.md`.
- `/trellis:plan`
  Translate the spec into concrete architecture, technology, and code decisions. Produces `.specs/<feature>/plan.md`.
- `/trellis:tasks`
  Decompose the plan into discrete, ordered, verifiable units of work. Produces `.specs/<feature>/tasks.md`.

### Execution

- `/trellis:pipeline`
  Orchestrate the full pipeline from pitch through tasks in one session. Supports interactive and automatic modes.
- `/trellis:implement`
  Turn specs, sketches, or freeform instructions into working code through iterative oracle-driven feedback loops.

## Typical workflow

```bash
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

```text
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
    implement-state.md      # created during /trellis:implement, tracks progress
    implement-preflight.json # ephemeral, used by Ralph iterations
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

A bundled loop script (`scripts/ralph-loop.sh`) that provides context-fresh iteration for large implementations. Based on Geoffrey Huntley's Ralph Wiggum methodology — each iteration runs in a fresh Claude Code context window, using `{specsDir}/{feature}/implement-state.md` as filesystem memory between iterations. Each feature has its own state file, stored alongside its other artifacts.

**When to use:** Large implementations with 10+ acceptance criteria or many files where context degradation becomes a concern.

**Invocation:** `/trellis:implement <feature-name> with ralph [--stream|--tail]`

Phase 0 and Phase 1 run interactively (config questions, pipeline assembly), then the loop script takes over. Each iteration runs with scoped permissions — only the specific toolchain commands configured during setup are allowed. The loop stops when all criteria pass, max iterations are reached (default 10), or 3 consecutive failures occur.

**Output modes:**

| Flag | Behavior |
|------|----------|
| *(default)* | Silent — output goes to log files only. Between-iteration status (criteria counts) is shown. |
| `--stream` | Full Claude output visible in real-time via `tee`, also logged to file. |
| `--tail` | Silent during iteration, shows last 50 lines of log after each iteration completes. |

### Ralphd (Docker-sandboxed Ralph)

A variant of Ralph that runs each iteration inside a Docker container with `--dangerously-skip-permissions`. Docker is the security boundary — no scoped permission allowlists needed. Supports the same `--stream` and `--tail` output modes as Ralph.

**When to use:** Same scenarios as Ralph, plus when scoped permissions are too restrictive or when you want full command access inside a sandboxed environment.

**Requirements:** `docker` installed and running. Supports both API key (`ANTHROPIC_API_KEY` env var) and OAuth/subscription auth (one-time `scripts/ralphd-loop.sh --login`).

**Invocation:** `/trellis:implement <feature-name> with ralphd [--stream|--tail]`

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

## Testing

Trellis includes test suites for scripts, hooks, shell integration, artifact
snapshots, and skill output validation. Run all suites with:

```bash
npm test
```

Skill output tests validate that each skill prompt produces structurally
correct output (required sections, headings, keywords). Two approaches are
available depending on your auth setup:

- **Promptfoo** (`npm run test:llm`) — requires `ANTHROPIC_API_KEY`, runs in
  parallel with a web UI for results
- **Claude -p harness** (`npm run test:skills`) — works with Claude Code
  subscription auth, no API key needed

See [docs/skill-testing.md](docs/skill-testing.md) for details, design
rationale, and instructions for adding new test cases.

## Examples

### Manual step-by-step

Walk through the full pipeline manually, reviewing and adjusting each artifact before moving on. This example builds an API for team kudos — lightweight peer recognition messages.

**1. Set up guidelines (once per project)**

```text
> /trellis:guidelines

Stack: Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL 16, Pydantic, pytest
Architecture: layered — routes → services → models
Conventions: snake_case, 88-char line length, Google-style docstrings
Testing: pytest with real database via testcontainers, no mocks
Infrastructure: Docker on Fly.io, GitHub Actions CI
```

This creates `.specs/guidelines.md` and `trellis.json`.

**2. Sketch (optional — explore a technical unknown)**

```text
> /trellis:sketch

Slug: cursor-pagination
Hypothesis: SQLAlchemy async supports keyset (cursor) pagination with UUID v7
  primary keys without custom query wrappers.
Method: Built a minimal prototype with 10k rows, benchmarked offset vs cursor.
Findings: Cursor pagination is 40x faster at page 500. UUID v7 sorts correctly
  by insertion time. No custom wrappers needed — standard WHERE + ORDER BY.
Verdict: Viable
```

Creates `.specs/sketches/cursor-pagination.md`.

**3. Pitch the feature**

```text
> /trellis:pitch

Feature name: team-kudos
Problem: Team members have no lightweight way to recognize each other's
  contributions. Recognition only happens in quarterly reviews.
Appetite: 2 weeks, one developer.
Sketches: cursor-pagination (Viable)
No-gos: No gamification, no leaderboards, no external notifications.
```

Creates `.specs/team-kudos/pitch.md`. Review the problem framing, appetite, and no-gos. Adjust if needed before continuing.

**4. Write the spec**

```text
> /trellis:spec team-kudos
```

Reads the pitch and guidelines, then generates `.specs/team-kudos/spec.md` with sections §1–§10: context, functional overview, actors, data model, interfaces, business rules, failure modes, success criteria, constraints, and open questions.

Review the spec. This is the most important human checkpoint — everything downstream flows from it.

**5. Clarify ambiguities**

```text
> /trellis:clarify team-kudos
```

Scans the spec for implicit gaps across six categories (data ownership, permissions, privacy, UX intent, integration, edge cases). Resolves what it can from context, moves unresolvable items to §10 with reasoning.

**6. Compliance review (if needed)**

```text
> /trellis:compliance team-kudos
```

Skip this for team kudos (no PII, no regulated data). For features handling personal data, health data, or student data, this step evaluates the spec against applicable regulations and produces `.specs/team-kudos/compliance.md`.

**7. Create the plan**

```text
> /trellis:plan team-kudos
```

Translates the spec into technical decisions: architecture, technology choices specific to this feature, data access patterns, interface implementation details, file structure, error handling, and testing strategy. Produces `.specs/team-kudos/plan.md`.

Review the plan. This is your last chance to adjust implementation details before they get decomposed into tasks.

**8. Break into tasks**

```text
> /trellis:tasks team-kudos
```

Decomposes the plan into phased, ordered, verifiable work items. Each task has a "Do" section (what to build) and a "Verify" section (how to confirm it's done). Produces `.specs/team-kudos/tasks.md`.

**9. Implement**

```text
> /trellis:implement team-kudos
```

Reads the tasks, plan, spec, and guidelines. Asks for your tooling commands (type-check, lint, build, test), then iterates: write code, run the oracle pipeline (type-check → lint → build → tests → judge), fix failures, repeat until all acceptance criteria pass.

### Pipeline auto mode

Run the entire specification pipeline in one pass. Auto mode gathers all context upfront, makes best-guess decisions at every point where interactive mode would pause, and documents every autonomous decision as an `[AUTO]` tag for your review.

```text
> /trellis:pipeline auto

Feature name: team-kudos
Problem: Team members have no lightweight way to recognize each other's
  contributions. Recognition only happens in quarterly reviews.
Appetite: 2 weeks, one developer.
No-gos: No gamification, no leaderboards, no external notifications.
Compliance: No — no PII or regulated data involved.
Technical constraints: Must integrate with existing user model. Cursor-based
  pagination for the feed (validated in sketch).
```

The pipeline runs pitch → spec → clarify → compliance (skipped) → plan → tasks without pausing. When it finishes, it presents:

- A summary of all generated artifacts
- A list of every `[AUTO]` decision it made, grouped by artifact

```text
Pipeline complete:
  .specs/team-kudos/pitch.md       ✓
  .specs/team-kudos/spec.md        ✓
  .specs/team-kudos/compliance.md  skipped (no regulated data)
  .specs/team-kudos/plan.md        ✓
  .specs/team-kudos/tasks.md       ✓

Auto decisions requiring review:
  spec.md §10:
  - [AUTO] Assumed kudos are visible to all team members, not just sender/recipient.
  - [AUTO] Assumed 280-character limit for kudos message body.
```

Review the `[AUTO]` items, adjust any artifacts that need changes, then run `/trellis:implement team-kudos`.

## Self-hosting the plugin

If your team wants to avoid depending on an external GitHub repository in your development workflow, you can vendor Trellis directly into your project or organization.

### Option 1: Vendor into your project

Copy the plugin into your repo and register it as a local plugin:

```bash
# From your project root
git subtree add --prefix .claude/plugins/trellis \
  https://github.com/robmclarty/trellis.git main --squash

# Register as a local plugin in your project's .claude/settings.json
cat <<'EOF' >> .claude/settings.json
{
  "plugins": [".claude/plugins/trellis"]
}
EOF
```

To pull updates later:

```bash
git subtree pull --prefix .claude/plugins/trellis \
  https://github.com/robmclarty/trellis.git main --squash
```

### Option 2: Fork to your organization

```bash
# Fork on GitHub, then clone your org's copy
gh repo fork robmclarty/trellis --org your-org --clone

# Team members install from your org's fork
# In Claude Code:
/plugin marketplace add your-org/trellis
```

This gives your team full control over updates — review changes in PRs before merging upstream updates.

### Option 3: Copy the files directly

Trellis is just markdown files and Python scripts with no build step or external dependencies. The simplest approach:

```bash
# Copy into your project
cp -r /path/to/trellis .claude/plugins/trellis

# Or download a specific release
curl -L https://github.com/robmclarty/trellis/archive/refs/tags/v0.3.0.tar.gz \
  | tar xz --strip-components=1 -C .claude/plugins/trellis
```

Register it the same way as Option 1. Since there's no package manager involved, you control exactly what's on disk.

### What to review

Whichever option you choose, the security-relevant surface is small:

- **`hooks/`** — Python scripts that run automatically on Claude Code events. Read these first.
- **`scripts/`** — Python scripts called by skills during pre-flight validation. No network access, no side effects beyond stdout.
- **`skills/`** and **`agents/`** — Markdown prompt files. They instruct Claude but don't execute code themselves.

No dependencies, no `node_modules`, no build artifacts. Everything is readable plaintext.

## License

MIT
