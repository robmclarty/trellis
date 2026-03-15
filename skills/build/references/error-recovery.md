# Error Recovery

If a context reset or interruption occurs mid-implementation:

1. Read `{specsDir}/{feature}/tasks.json`
2. Find the first task with `status: "pending"`
3. Resume from that task

tasks.json on disk IS the resume point. There is no separate state file. The conversation history is not needed — the task's `do` and `verify` fields plus the plan and guidelines contain all necessary context.

In ralph mode, the loop script handles this automatically: it reads tasks.json at the start of each iteration and picks up from the first pending task.
