# Manual step-by-step

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
> /trellis:prep team-kudos
```

Decomposes the plan into phased, ordered, verifiable work items. Each task has a "do" field (what to build) and a "verify" field (how to confirm it's done). Produces `.specs/team-kudos/tasks.json`.

**9. Implement**

```text
> /trellis:implement team-kudos
```

Reads tasks.json, plan, spec, and guidelines. For each task: optionally writes tests (TDD), implements code, runs the check command, marks done or blocked. Judge review runs at the end for spec intent alignment.
