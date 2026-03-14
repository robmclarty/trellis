#!/usr/bin/env python3
"""PreToolUse hook for Bash(git commit) — checks implement state file.

Warns if acceptance criteria are incomplete before committing.
Calls scripts/parse-implement-state.py for structured data.
Exit 0 (warn only).
"""

import json
import os
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    script = os.path.join(PLUGIN_ROOT, "scripts", "parse-implement-state.py")

    # Find all implement-state.md files across feature directories
    import glob

    state_files = glob.glob(os.path.join(specs_dir, "*", "implement-state.md"))

    # Also check legacy location for backward compatibility
    legacy_state = os.path.join(specs_dir, ".state", "implement-state.md")
    if os.path.isfile(legacy_state):
        state_files.append(legacy_state)

    if not state_files:
        sys.exit(0)

    for state_file in state_files:
        result = subprocess.run(
            [sys.executable, script, state_file],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            continue

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue

        pending = data.get("pendingCount", 0)
        if pending > 0:
            print(f"\u26a0 {state_file} has {pending} pending acceptance criteria.")
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
