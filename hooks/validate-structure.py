#!/usr/bin/env python3
"""PostToolUse hook for Write/Edit — validates spec document structure.

Checks that documents under the specs directory have their minimum required
sections. Self-contained: no script dependency. Receives tool input as JSON
on stdin. Outputs warnings only (exit 0).
"""

import json
import os
import re
import sys


def resolve_specs_dir():
    """Read specsDir from trellis.json, default to .specs/."""
    try:
        with open("trellis.json") as f:
            config = json.load(f)
            return config.get("specsDir", ".specs")
    except (FileNotFoundError, json.JSONDecodeError):
        return ".specs"


SECTION_CHECKS = {
    "spec.md": {
        "patterns": [r"§1", r"§2", r"§8", r"§9"],
        "label": "required section",
    },
    "pitch.md": {
        "patterns": [r"(?i)##\s*Problem", r"(?i)##\s*Appetite", r"(?i)##\s*Shape", r"(?i)##\s*No-Gos"],
        "label": "required section",
    },
    "plan.md": {
        "patterns": [r"§1", r"§2", r"§3", r"§6"],
        "label": "required section",
    },
    "tasks.md": {
        "patterns": [r"(?i)##\s*Phase"],
        "label": "at least one Phase section",
    },
}


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

    if not file_path.endswith(".md"):
        sys.exit(0)

    basename = os.path.basename(file_path)
    checks = SECTION_CHECKS.get(basename)
    if not checks:
        sys.exit(0)

    if not os.path.isfile(file_path):
        sys.exit(0)

    with open(file_path) as f:
        content = f.read()

    warnings = []
    for pattern in checks["patterns"]:
        if not re.search(pattern, content):
            # Extract a readable label from the pattern
            label = pattern.replace(r"(?i)", "").replace(r"##\s*", "").strip()
            warnings.append(f"  \u26a0 Missing {checks['label']}: {label}")

    if warnings:
        print(f"Spec structure warnings for {basename}:")
        for w in warnings:
            print(w)

    sys.exit(0)


if __name__ == "__main__":
    main()
