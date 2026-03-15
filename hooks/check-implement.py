#!/usr/bin/env python3
"""PreToolUse hook for Bash(git commit) — checks tasks.json status.

Warns if tasks are still pending before committing.
Reads tasks.json directly (no external script dependency).
Exit 0 (warn only).
"""

import glob
import json
import os
import sys


def resolve_specs_dir():
    """Read specsDir from trellis.json, default to .specs/."""
    try:
        with open("trellis.json") as f:
            return json.load(f).get("specsDir", ".specs")
    except (FileNotFoundError, json.JSONDecodeError):
        return ".specs"


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    if "git commit" not in command:
        sys.exit(0)

    specs_dir = resolve_specs_dir()

    # Find all tasks.json files across feature directories
    task_files = glob.glob(os.path.join(specs_dir, "*", "tasks.json"))

    if not task_files:
        sys.exit(0)

    for task_file in task_files:
        try:
            with open(task_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            continue

        tasks = data.get("tasks", [])
        pending = [t for t in tasks if t.get("status") == "pending"]
        blocked = [t for t in tasks if t.get("status") == "blocked"]

        if pending:
            print(f"\u26a0 {task_file} has {len(pending)} pending tasks.")
            print("  Consider completing all tasks before committing.")

            for t in pending[:5]:
                print(f"  - [ ] {t.get('id', '?')}: {t.get('title', '')}")

            if len(pending) > 5:
                print(f"  ... and {len(pending) - 5} more")

        if blocked:
            print(f"\u26a0 {task_file} has {len(blocked)} blocked tasks.")

    sys.exit(0)


if __name__ == "__main__":
    main()
