#!/usr/bin/env python3
"""PostToolUse hook for Write/Edit — validates spec document structure.

Delegates to scripts/validate-doc.py for pitch.md, spec.md, and plan.md files
under the specs directory. Outputs errors and warnings. Always exits 0.
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
    specs_dir = resolve_specs_dir()

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    if specs_dir not in file_path:
        sys.exit(0)

    basename = os.path.basename(file_path)
    if basename not in ("pitch.md", "spec.md", "plan.md"):
        sys.exit(0)

    if not os.path.isfile(file_path):
        sys.exit(0)

    script = os.path.join(PLUGIN_ROOT, "scripts", "validate-doc.py")
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

    errors = data.get("errors", [])
    warnings = data.get("warnings", [])

    if not errors and not warnings:
        sys.exit(0)

    print(f"Document validation for {basename}:")
    for e in errors:
        print(f"  \u2717 {e}")
    for w in warnings:
        print(f"  \u26a0 {w}")

    sys.exit(0)


if __name__ == "__main__":
    main()
