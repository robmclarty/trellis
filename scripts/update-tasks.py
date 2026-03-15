#!/usr/bin/env python3
"""Update task status in tasks.json in-place.

Usage: update-tasks.py <tasks.json> <task-id> <done|blocked> [--iteration N]

Modifies tasks.json directly — tasks.json IS the execution state, there is no
separate state file. This script replaces the old parse-implement-state.py and
extract-criteria.py by making tasks.json the single source of truth.

Outputs JSON to stdout with the update result and current counts, so the
calling loop script can check progress without re-reading the file.
"""

import argparse
import json
import sys


def update_task(tasks_path, task_id, new_status, iteration=None):
    """Update a single task's status and iteration in tasks.json.

    Modifies the file in-place because tasks.json serves as both the task
    definition and execution state. The loop script calls this after each
    task completes (or gets blocked), and the updated file is the resume
    point if the process is interrupted.

    Returns a dict with update result and current task counts.
    """
    with open(tasks_path) as f:
        data = json.load(f)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        return {"updated": False, "error": f"Task {task_id} not found"}

    task["status"] = new_status
    if iteration is not None:
        task["iteration"] = iteration

    with open(tasks_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    # Count current state for the loop script. Outputting this avoids a
    # separate file read — the loop script gets counts immediately.
    pending = sum(1 for t in data["tasks"] if t["status"] == "pending")
    done = sum(1 for t in data["tasks"] if t["status"] == "done")
    blocked = sum(1 for t in data["tasks"] if t["status"] == "blocked")

    return {
        "updated": True,
        "taskId": task_id,
        "newStatus": new_status,
        "pendingCount": pending,
        "doneCount": done,
        "blockedCount": blocked,
    }


def main():
    parser = argparse.ArgumentParser(description="Update task status in tasks.json")
    parser.add_argument("tasks_json", help="Path to tasks.json")
    parser.add_argument("task_id", help="Task ID to update (e.g., '1.1')")
    parser.add_argument("status", choices=["done", "blocked"], help="New status")
    parser.add_argument("--iteration", type=int, default=None, help="Iteration number")

    args = parser.parse_args()
    result = update_task(args.tasks_json, args.task_id, args.status, args.iteration)

    json.dump(result, sys.stdout, indent=2)
    print()

    sys.exit(0 if result.get("updated") else 1)


if __name__ == "__main__":
    main()
