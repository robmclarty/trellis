#!/usr/bin/env python3
"""Validate prerequisites for a Trellis skill.

Usage: validate-prereqs.py <skill-name> [feature-name]

Resolves the specs directory from trellis.json (default: .specs/) and checks
that required prerequisite files exist for the given skill. Outputs JSON to
stdout with the resolved specsDir, validation result, and any missing files.

Exit 0 if all prerequisites are met, exit 1 if any are missing.
"""

import json
import os
import sys


def resolve_specs_dir():
    """Read specsDir from trellis.json, default to .specs/."""
    try:
        with open("trellis.json") as f:
            config = json.load(f)
            return config.get("specsDir", ".specs")
    except (FileNotFoundError, json.JSONDecodeError):
        return ".specs"


# Map of skill name -> list of required file patterns.
# Patterns use {feature} as a placeholder for the feature name.
# Entries prefixed with ? are optional (checked but not required).
PREREQS = {
    "guidelines": [],
    "sketch": ["guidelines.md"],
    "pitch": ["guidelines.md"],
    "spec": ["guidelines.md", "{feature}/pitch.md"],
    "clarify": ["{feature}/spec.md"],
    "compliance": ["{feature}/spec.md", "guidelines.md"],
    "plan": ["{feature}/spec.md", "guidelines.md"],
    "tasks": ["{feature}/plan.md", "{feature}/spec.md"],
    "implement": ["{feature}/"],
    "pipeline": ["guidelines.md"],
}


def check_prereqs(skill, feature, specs_dir):
    patterns = PREREQS.get(skill)
    if patterns is None:
        print(f"Unknown skill: {skill}", file=sys.stderr)
        return None

    missing = []
    for pattern in patterns:
        if "{feature}" in pattern and not feature:
            missing.append(pattern.replace("{feature}", "<feature-name>"))
            continue

        path = os.path.join(specs_dir, pattern.replace("{feature}", feature or ""))

        if pattern.endswith("/"):
            if not os.path.isdir(path):
                missing.append(pattern.replace("{feature}", feature or ""))
        else:
            if not os.path.isfile(path):
                missing.append(pattern.replace("{feature}", feature or ""))

    return missing


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-prereqs.py <skill-name> [feature-name]", file=sys.stderr)
        sys.exit(2)

    skill = sys.argv[1]
    feature = sys.argv[2] if len(sys.argv) > 2 else None

    specs_dir = resolve_specs_dir()
    missing = check_prereqs(skill, feature, specs_dir)

    if missing is None:
        sys.exit(2)

    result = {
        "specsDir": specs_dir,
        "skill": skill,
        "feature": feature,
        "valid": len(missing) == 0,
        "missing": missing,
    }

    json.dump(result, sys.stdout, indent=2)
    print()

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
