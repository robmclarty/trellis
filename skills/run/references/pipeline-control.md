# Pipeline control: resumption and stage overrides

## Resumption

The pipeline is resumable across sessions. Each stage writes its artifact to disk, so the pipeline detects which artifacts exist and resumes from the next incomplete stage:

- No `pitch.md` → resume at Stage 1 (Pitch)
- `pitch.md` exists, no `spec.md` → resume at Stage 2 (Spec)
- `spec.md` exists, no `plan.md` → resume at Stage 3 (Plan)
- `plan.md` exists → resume at Stage 4 (Implement)

When resuming, tell the user where you're picking up and confirm they want to continue from that point.

## Stage overrides

The user can force the pipeline to restart at a specific stage:

- `/run pitch` — Restart at pitch regardless of existing artifacts
- `/run spec` — Restart at spec
- `/run plan` — Restart at plan

Overrides do not delete downstream artifacts. The stage's generation will overwrite its own artifact; downstream artifacts remain until their stages re-run.

## Review gates

Each document stage (pitch, spec, plan) presents a consistent gate after generation:

- **approve** — Continue to next stage
- **edit** — Pipeline ends; user edits the file and re-invokes later
- **redo** — Regenerate the document (max 3 redos per stage)

Stage 4 (implement) uses a simpler yes/no confirmation since it's a write-heavy operation.
