#!/usr/bin/env python3
"""PreToolUse hook for Bash(git commit) — checks .implement-state.md.

Warns if acceptance criteria are incomplete before committing.
Calls scripts/parse-implement-state.py for structured data.
Exit 0 (warn only).
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

    command = hook_input.get("tool_input", {}).get("command", "")
    if "git commit" not in command:
        sys.exit(0)

    state_file = ".implement-state.md"
    if not os.path.isfile(state_file):
        sys.exit(0)

    script = os.path.join(PLUGIN_ROOT, "scripts", "parse-implement-state.py")
    result = subprocess.run(
        [sys.executable, script, state_file],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        sys.exit(0)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        sys.exit(0)

    pending = data.get("pendingCount", 0)
    if pending > 0:
        print(f"\u26a0 .implement-state.md has {pending} pending acceptance criteria.")
        print("  Consider completing all criteria before committing.")

        criteria = data.get("criteria", [])
        pending_items = [c for c in criteria if c.get("status") == "pending"]
        for item in pending_items[:5]:
            summary = item.get("summary", "")
            crit_id = item.get("id", "")
            print(f"  - [ ] {crit_id}: {summary}")

        if pending > 5:
            print(f"  ... and {pending - 5} more")

    sys.exit(0)


if __name__ == "__main__":
    main()
