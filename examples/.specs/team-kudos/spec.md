# Spec: Team Kudos

## §1 — Context

See `pitch.md`. Team members need a lightweight way to recognize each other. This spec defines a kudos system with a shared feed and manager-facing stats.

## §2 — Functional Overview

- Any authenticated team member can send a kudos to another team member
- Kudos appear on a chronological feed visible to all team members
- Managers can view aggregated kudos statistics filtered by time range
- Kudos are immutable once sent (no editing, but senders can delete their own)

## §3 — Actors and Permissions

| Actor | Can do |
|-------|--------|
| **Team Member** | Send kudos, view feed, delete own kudos |
| **Manager** | Everything a team member can do, plus view stats dashboard |

All authenticated users are team members. Manager role is additive.

## §4 — Data Model

**Kudos**
| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK, generated |
| sender_id | UUID | FK → User, NOT NULL |
| recipient_id | UUID | FK → User, NOT NULL, ≠ sender_id |
| message | text | 1–280 characters, NOT NULL |
| category | enum | teamwork, technical, mentoring, above_and_beyond |
| created_at | timestamptz | NOT NULL, server-generated |

## §5 — Interfaces

**POST /api/kudos** — Create a kudos
- Input: `{ recipient_id, message, category }`
- Output: `201` with created kudos object
- Errors: `400` invalid input, `404` recipient not found, `422` self-kudos

**GET /api/kudos** — Feed (paginated)
- Query: `?cursor=<id>&limit=<n>` (default limit 20, max 100)
- Output: `200` with `{ items: Kudos[], next_cursor: string | null }`

**DELETE /api/kudos/:id** — Delete own kudos
- Output: `204`
- Errors: `403` not the sender, `404` not found

**GET /api/kudos/stats** — Manager stats
- Query: `?from=<date>&to=<date>&group_by=recipient|category`
- Output: `200` with `{ stats: [{ key, count }] }`
- Errors: `403` not a manager

## §6 — Business Rules

- A user cannot send kudos to themselves
- Message length: 1–280 characters (enforced at API level)
- Category must be one of the defined enum values
- Feed ordering: newest first (descending `created_at`)
- Stats aggregation respects the time range filter; defaults to last 30 days

## §7 — Failure Modes

- Recipient not found → 404 with clear message
- Self-kudos attempt → 422 with explanation
- Invalid category → 400 with allowed values listed
- Concurrent deletes → idempotent (second delete returns 204)

## §8 — Success Criteria

- [ ] A team member can send a kudos and see it appear on the feed
- [ ] The feed paginates correctly with cursor-based navigation
- [ ] A sender can delete their own kudos; others get 403
- [ ] A manager can view stats grouped by recipient or category
- [ ] A non-manager gets 403 on the stats endpoint
- [ ] Self-kudos are rejected with a clear error

## §9 — Constraints

- Scope: API only. No frontend in this iteration.
- Deployed in ca-central-1 (FIPPA consideration from guidelines)
- No external service dependencies
- No rate limiting in v1 (acceptable for internal team use)

## §10 — Open Questions

- Should there be a daily limit on kudos sent per person? (Deferred: start without limits, revisit if gaming becomes an issue.)
- Should deleted kudos be soft-deleted or hard-deleted? (Deferred: hard delete for simplicity in v1.)
