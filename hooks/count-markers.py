#!/usr/bin/env python3
"""PostToolUse hook for Write/Edit — counts ambiguity markers in spec files.

After writes to spec.md files, calls scripts/extract-markers.py and reports
a marker count summary. Exits silently for non-spec files.
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
            config = json.load(f)
            return config.get("specsDir", ".specs")
    except (FileNotFoundError, json.JSONDecodeError):
        return ".specs"


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    specs_dir = resolve_specs_dir()
    if specs_dir not in file_path:
        sys.exit(0)

    if not file_path.endswith("spec.md"):
        sys.exit(0)

    script = os.path.join(PLUGIN_ROOT, "scripts", "extract-markers.py")
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

    count = data.get("count", 0)
    if count == 0:
        print("\u2713 spec.md: no unresolved [? ...] markers")
    else:
        by_cat = data.get("byCategory", {})
        breakdown = ", ".join(f"{cat}: {n}" for cat, n in sorted(by_cat.items()))
        print(f"\u26a0 spec.md: {count} unresolved [? ...] marker(s) ({breakdown})")

    sys.exit(0)


if __name__ == "__main__":
    main()
