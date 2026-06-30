---
name: build-with-subagents
description: Execute a Trellis task list by dispatching each task to a Claude Code subagent in its own context window. Use when the user says "build with sub-agents", "build with subagents", or when a feature has 5-20 tasks with dependencies between them. Reads `.specs/<feature>/tasks.md` produced by the tasks skill. Each subagent gets focused context (guidelines + plan + task + learnings) and returns results to the orchestrating session. Supports parallel execution of independent tasks via background subagents with worktree isolation.
---

# Build with Subagents

Execute a Trellis task list by dispatching each task to a Claude Code subagent. Each task runs in its own fresh context window. The orchestrating session (you) coordinates dispatch order, tracks progress, and captures learnings.

## When to use

Use this for micro-spec-sized features: 5-20 tasks with dependency relationships where some tasks can run in parallel but others must wait. Typical example: adding a new API endpoint that touches the data model, service layer, route handler, and frontend component.

Do NOT use this for bulk migrations across hundreds of files (use `build-with-batch` instead) or for tiny task lists under 5 items (just execute inline).

## Input

The skill expects a completed task list at `.specs/<feature>/tasks.md`. If the user provides a feature name, look for it there. If no feature name is given, ask for one.

Also read:
- `.specs/guidelines.md` (project conventions)
- `.specs/<feature>/plan.md` (architecture decisions)
- `.specs/<feature>/tasks.md` (the task list to execute)
- `.specs/<feature>/learnings.md` (if it exists from prior runs)

## Step 1: Parse the task list

Read `tasks.md` and extract every task. Each task in the file has at minimum:
- A task identifier (number or ID)
- A description of what to implement
- Files likely to be touched
- Any dependencies on other tasks (which tasks must complete first)
- Acceptance criteria or verification steps

Build a dependency graph from this information. Identify which tasks are independent (can run in parallel) and which are blocked by others.

## Step 2: Prepare shared context

Assemble a context payload that every subagent will receive. Keep this lean. It should contain:

1. **Project guidelines** (from `.specs/guidelines.md`): stack, conventions, file structure rules. Truncate to essentials if the file is large. Target under 4,000 tokens.

2. **Plan summary**: The key architecture and technology decisions from `.specs/<feature>/plan.md`. Not the full document; extract the decisions that affect implementation. Target under 2,000 tokens.

3. **Learnings so far**: Contents of `.specs/<feature>/learnings.md` if it exists. This file accumulates notes from completed tasks that help subsequent tasks avoid pitfalls.

## Step 3: Dispatch tasks

Process tasks in dependency order. For each "wave" of independent tasks:

1. **For each task in the wave**, spawn a subagent using the Task tool with:
   - `subagent_type`: `general-purpose`
   - `run_in_background`: `true` (for parallel execution within a wave)
   - A prompt containing:
     - The shared context payload from Step 2
     - The specific task description, files to touch, and acceptance criteria
     - Clear instruction: "Implement this task. After implementation, run the verification steps listed in the acceptance criteria. If verification fails, fix the issue and re-verify. When done, respond with a SUMMARY of what you changed, any ISSUES encountered, and any NOTES that would help someone working on a related task."

2. **Wait for all subagents in the wave to complete** before dispatching the next wave.

3. **After each task completes**, append a brief entry to `.specs/<feature>/learnings.md`:
   ```
   ## Task <id>: <short description>
   - Status: complete | failed
   - Files changed: <list>
   - Notes: <anything the subagent flagged as useful for future tasks>
   ```

4. **If a task fails** (subagent reports verification failure or errors it could not resolve), log the failure in learnings.md and continue with tasks that don't depend on it. Report the failure to the user at the end.

## Step 4: Report results

After all waves complete, print a summary:
- Total tasks: N
- Completed: N
- Failed: N (with task IDs and brief failure reasons)
- Learnings file updated at `.specs/<feature>/learnings.md`

If any tasks failed, suggest the user review the failures and either fix manually or re-run with updated context.

## Subagent prompt template

Use this structure when constructing the prompt for each subagent:

```
You are implementing a single task from a feature specification.

PROJECT GUIDELINES:
<contents of guidelines summary>

PLAN DECISIONS:
<contents of plan summary>

LEARNINGS FROM PRIOR TASKS:
<contents of learnings.md>

YOUR TASK:
Task <id>: <description>
Files to touch: <file list>
Dependencies completed: <list of completed task IDs this one depends on>

ACCEPTANCE CRITERIA:
<criteria from tasks.md>

INSTRUCTIONS:
1. Implement the task as described.
2. Run the acceptance criteria verification steps (type-check, lint, test, etc.).
3. If verification fails, fix and re-verify up to 3 attempts.
4. Respond with:
   SUMMARY: What you changed and why.
   ISSUES: Any problems encountered (even if resolved).
   NOTES: Anything useful for tasks that come after this one.
```

## Important constraints

- Do NOT use worktree isolation for subagents in this skill unless the user explicitly requests it. Tasks within a single feature typically need to see each other's changes (task 3 reads the schema that task 1 created). Worktree isolation would hide those changes. Dependency ordering handles conflict avoidance instead.
- Keep the shared context payload under 8,000 tokens total. If guidelines or plan are too large, summarize them.
- If the task list has more than 20 tasks, warn the user that this technique may hit orchestration overhead limits and suggest `build-with-batch` for the bulk portion.
- Subagents cannot spawn further subagents. Each task gets one subagent invocation. If a task is too complex for a single context window, it should have been split further during the tasks phase.
