# Plan: Team Kudos

## §1 — Technical Summary

A FastAPI service with four REST endpoints backed by PostgreSQL via SQLAlchemy async. Follows the project's layered architecture (routes → services → models). Pydantic for validation, pytest for testing.

## §2 — Architecture

```
app/
  routes/kudos.py          # FastAPI router with 4 endpoints
  services/kudos_service.py # Business logic functions
  models/kudos_model.py     # SQLAlchemy model
  schemas/kudos_schemas.py  # Pydantic input/output schemas
```

Single module, no cross-service dependencies. The kudos service depends only on the database session and the user model (assumed to exist).

## §3 — Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pagination | Cursor-based (keyset) | Better performance than offset for chronological feeds |
| ID generation | UUID v7 | Sortable by time, works as cursor |
| Stats aggregation | SQL GROUP BY | Simple counts don't need materialized views |
| Enum storage | PostgreSQL native ENUM | Type safety at DB level |

## §4 — Data Access Patterns

- **Create kudos:** Insert with FK validation (recipient exists, ≠ sender)
- **Feed:** `SELECT ... ORDER BY created_at DESC` with cursor filter `WHERE id < cursor`
- **Delete:** `DELETE WHERE id = ? AND sender_id = ?` (ownership enforced in query)
- **Stats:** `SELECT recipient_id|category, COUNT(*) GROUP BY ... WHERE created_at BETWEEN`

## §5 — Interface Implementation

Each spec §5 endpoint maps to a route function in `routes/kudos.py` that validates via Pydantic schema, calls a service function, and returns the response. See guidelines route-example.py for the pattern.

## §6 — File Structure

```
app/
  routes/kudos.py
  services/kudos_service.py
  models/kudos_model.py
  schemas/kudos_schemas.py
tests/
  test_kudos_service.py
  test_kudos_routes.py
alembic/
  versions/001_create_kudos_table.py
```

## §7 — Error Handling Strategy

Services return `Result[T]` types (see guidelines service-example.py). Routes translate:
- `Ok` → appropriate 2xx
- `Err(not_found)` → 404
- `Err(forbidden)` → 403
- `Err(validation)` → 422

## §8 — Testing Strategy

- **Service tests:** Test business logic (self-kudos rejection, ownership check, stats aggregation) against a real test database using pytest fixtures.
- **Route tests:** FastAPI TestClient for endpoint integration tests (status codes, response shapes, auth).
- Skip: No unit tests for Pydantic schemas (framework handles validation).

## §9 — Deployment and Infrastructure

N/A — deploys within existing infrastructure.

## §10 — Migration Path

N/A — greenfield feature, no migration concerns.
