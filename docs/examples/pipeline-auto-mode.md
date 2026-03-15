# Pipeline auto mode

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

The pipeline runs pitch → spec → clarify → compliance (skipped) → plan → prep without pausing. When it finishes, it presents:

- A summary of all generated artifacts
- A list of every `[AUTO]` decision it made, grouped by artifact

```text
Pipeline complete:
  .specs/team-kudos/pitch.md       ✓
  .specs/team-kudos/spec.md        ✓
  .specs/team-kudos/compliance.md  skipped (no regulated data)
  .specs/team-kudos/plan.md        ✓
  .specs/team-kudos/tasks.json     ✓

Auto decisions requiring review:
  spec.md §10:
  - [AUTO] Assumed kudos are visible to all team members, not just sender/recipient.
  - [AUTO] Assumed 280-character limit for kudos message body.
```

Review the `[AUTO]` items, adjust any artifacts that need changes, then run `/trellis:implement team-kudos`.
