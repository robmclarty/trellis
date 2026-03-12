# Pitch: Team Kudos

## Problem

Team members have no lightweight way to recognize each other's contributions. Good work goes unacknowledged unless a manager happens to notice. This hurts morale and makes it harder for managers to identify who's consistently helping the team. Currently, recognition only happens in quarterly reviews — too infrequent to reinforce day-to-day behaviors.

## Appetite

2-week effort for one developer. This is a small, self-contained feature. Keep it simple: no gamification, no rewards system, no integration with HR tools.

## Sketches

- `websocket-vs-polling` — Tested whether real-time feed updates justify WebSocket complexity. Verdict: Not viable for this scope. Polling every 30s is sufficient for a kudos feed.

## Shape

A simple kudos system: any team member can send a kudos to any other team member with a short message and a category (teamwork, technical, mentoring, above-and-beyond). Kudos appear on a shared feed visible to the whole team. Managers get a stats dashboard showing kudos counts by person and category over configurable time ranges.

The feed is the core experience. It should feel lightweight — sending a kudos takes under 10 seconds.

## No-Gos

- No points, badges, or gamification mechanics
- No integration with Slack, email, or external notification systems (not this time)
- No anonymous kudos — attribution is the point
- No approval workflow — kudos post immediately

## Rabbit Holes

- **Building a notification system.** Tempting to notify recipients via email or push. Resist. The feed is the notification. If people want notifications, that's a separate pitch.
- **Analytics beyond counts.** Sentiment analysis, trend detection, or ML-powered insights are interesting but premature. Start with simple counts grouped by person and category.
