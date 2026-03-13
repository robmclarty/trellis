#!/usr/bin/env python3
"""PostToolUse hook for Write/Edit — syncs implement state after updates.

After writes to .implement-state.md, calls scripts/parse-implement-state.py
and outputs a progress summary. Exits silently for other files.
"""

import json
import os
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    if not file_path.endswith(".implement-state.md"):
        sys.exit(0)

    script = os.path.join(PLUGIN_ROOT, "scripts", "parse-implement-state.py")
    result = subprocess.run(
        [sys.executable, script, file_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        sys.exit(0)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        sys.exit(0)

    done = data.get("doneCount", 0)
    total = done + data.get("pendingCount", 0)
    next_id = data.get("nextPendingId")

    if total == 0:
        sys.exit(0)

    msg = f"\U0001f4ca Implementation progress: {done}/{total} criteria done"
    if next_id:
        # Find the next pending criterion's task ref
        for c in data.get("criteria", []):
            if c.get("id") == next_id:
                task_ref = c.get("taskRef", "")
                if task_ref:
                    msg += f", next: {next_id} ({task_ref})"
                else:
                    msg += f", next: {next_id}"
                break

    print(msg)
    sys.exit(0)


if __name__ == "__main__":
    main()
