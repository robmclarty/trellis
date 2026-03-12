# Project Guidelines

## Stack

- **Language:** Python 3.12
- **Runtime:** CPython
- **Framework:** FastAPI 0.110+
- **ORM:** SQLAlchemy 2.0 (async)
- **Validation:** Pydantic v2
- **Database:** PostgreSQL 16
- **Test framework:** pytest with pytest-asyncio
- **Package manager:** uv

## Architecture

Layered architecture with clear separation:

```
app/
  routes/       # FastAPI routers — validation, HTTP concerns only
  services/     # Business logic — plain async functions, no HTTP awareness
  models/       # SQLAlchemy models — persistence
  schemas/      # Pydantic models — validation at boundaries
  dependencies/ # FastAPI dependency injection
```

Dependencies flow inward: routes → services → models. Services never import from routes.

## Conventions

- **Naming:** snake_case everywhere. Files, functions, variables.
- **Imports:** stdlib → third-party → local, separated by blank lines.
- **Error handling:** Services return Result types (`Ok | Err`). Routes translate to HTTP status codes. Exceptions are for truly unexpected failures only.
- **No classes for business logic.** Plain functions with explicit parameters.

## Patterns

See the example files in the `guidelines` skill's `examples/` directory for concrete FastAPI/SQLAlchemy/Pydantic patterns.

## Testing

- Test business logic in services, not routes.
- Use real database (test container) for integration tests. No mocking the DB.
- pytest fixtures for database sessions and test data.
- Aim for behavioral coverage, not line coverage.

## Infrastructure

- Docker container deployed to AWS ECS in ca-central-1.
- CI via GitHub Actions: lint (ruff) → typecheck (pyright) → test → build → deploy.
- Environment variables for all configuration. No config files in production.
