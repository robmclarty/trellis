# Pipeline control: loop limits and resumption

## Loop limits

| Loop | Max iterations | On exceed (interactive) | On exceed (auto) |
|------|---------------|------------------------|-------------------|
| Clarify → Spec | 3 | Pause, present issues to user | Move to §10 as `[AUTO]`, continue |
| Compliance → Spec | 2 | Pause, present issues to user | Document as residual risks, continue |
| User review → any stage | No limit | User is always in control | N/A (no pauses) |

## Interruption and resumption

If the user stops the pipeline mid-run (or the conversation ends), the pipeline is resumable. Because each stage writes its artifact to disk, the pipeline can detect which artifacts exist and resume from the next incomplete stage:

- `pitch.md` exists but not `spec.md` → resume at Stage 2
- `spec.md` exists but has `[? ...]` markers → resume at Stage 3 (clarify)
- `spec.md` is clean, no `compliance.md` and compliance is needed → resume at Stage 5
- `compliance.md` exists but not `plan.md` → resume at Stage 6
- `plan.md` exists but not `tasks.md` → resume at Stage 7

When resuming, tell the user where you're picking up and confirm they want to continue from that point. If the original run was in auto mode, ask if they want to continue in auto mode or switch to interactive.
