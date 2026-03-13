# Tasks: Team Kudos

## Phase 1: Foundation
> Milestone: Kudos table exists, model and schemas defined, migration applied.

- [ ] 1.1 — Create SQLAlchemy model for kudos
  **Do:** Create `app/models/kudos_model.py` with the Kudos model matching spec §4. Include the KudosCategory enum. Follow the pattern in guidelines schema-example.py.
  **Verify:** Model imports without errors. Alembic can generate a migration from it.

- [ ] 1.2 — Create Pydantic schemas
  **Do:** Create `app/schemas/kudos_schemas.py` with `CreateKudosInput`, `KudosResponse`, and `KudosStatsResponse`. Reference spec §5 for field definitions.
  **Verify:** Schemas validate correct input and reject invalid input (wrong category, missing fields, self-kudos).

- [ ] 1.3 — Generate and apply Alembic migration
  **Do:** Run `alembic revision --autogenerate -m "create kudos table"`. Review the generated migration. Apply with `alembic upgrade head`.
  **Verify:** `kudos` table exists in the database with correct columns, constraints, and enum type.

## Phase 2: Core API
> Milestone: All four endpoints work end-to-end.

- [ ] 2.1 — Implement create kudos endpoint
  **Do:** Create `app/services/kudos_service.py` with `create_kudos()` and `app/routes/kudos.py` with `POST /api/kudos`. Validate recipient exists and ≠ sender (spec §6). Follow guidelines route-example.py and service-example.py patterns.
  **Verify:** POST creates a kudos and returns 201. Self-kudos returns 422. Missing recipient returns 404.

- [ ] 2.2 — Implement feed endpoint  [parallel]
  **Do:** Add `get_feed()` to the service and `GET /api/kudos` to the router. Implement cursor-based pagination per plan §4.
  **Verify:** Returns kudos in newest-first order. Cursor pagination works: second page returns different results. Empty feed returns empty array.

- [ ] 2.3 — Implement delete endpoint  [parallel]
  **Do:** Add `delete_kudos()` to the service and `DELETE /api/kudos/:id` to the router. Enforce ownership in the query (plan §4).
  **Verify:** Sender can delete own kudos (204). Non-sender gets 403. Already-deleted returns 204 (idempotent).

- [ ] 2.4 — Implement stats endpoint
  **Do:** Add `get_stats()` to the service and `GET /api/kudos/stats` to the router. Manager role check. GROUP BY with time range filter (plan §4).
  **Verify:** Manager sees counts grouped by recipient or category. Non-manager gets 403. Time range filter works correctly.

## Phase 3: Testing
> Milestone: All tests pass, full coverage of spec §8 success criteria.

- [ ] 3.1 — Write service tests
  **Do:** Create `tests/test_kudos_service.py`. Test all business logic: create, self-kudos rejection, feed pagination, ownership delete, stats aggregation. Use real test database.
  **Verify:** `pytest tests/test_kudos_service.py` passes.

- [ ] 3.2 — Write route integration tests
  **Do:** Create `tests/test_kudos_routes.py`. Test all endpoints via FastAPI TestClient: correct status codes, response shapes, auth enforcement on stats.
  **Verify:** `pytest tests/test_kudos_routes.py` passes. All spec §8 success criteria are covered.
