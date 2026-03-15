#!/usr/bin/env python3
"""Decide whether the test-writer agent should run for a given task.

Usage: should-write-tests.py <tasks.json> <task-id>

Outputs JSON to stdout: { "shouldWrite": true/false, "reason": "..." }

This is a deterministic heuristic — no LLM needed. The decision is based on
the task's "verify" text. Structural tasks (scaffold a directory, create a
config file) don't have meaningful behavioral assertions, so writing tests
for them wastes tokens. Behavioral tasks (validates input, returns error on
invalid data, handles edge cases) benefit from test-first development because
the tests encode expected behavior before the implementation exists.
"""

import json
import re
import sys

# Keywords that indicate behavioral verification — the test-writer should run.
# These suggest the task involves logic with observable inputs/outputs, edge
# cases, or state transitions that can be meaningfully tested.
BEHAVIORAL_KEYWORDS = [
    r"\brejects?\b",
    r"\breturns?\s+(error|40[0-9]|50[0-9]|null|false|empty)",
    r"\bvalidat(es?|ion)\b",
    r"\bedge\s*case",
    r"\bboundar(y|ies)\b",
    r"\bpermission",
    r"\bexpires?\b",
    r"\bconcurren",
    r"\btimeout",
    r"\bthrows?\b",
    r"\bfails?\b",
    r"\berror\b",
    r"\binvalid\b",
    r"\bunauthorized\b",
    r"\bforbidden\b",
    r"\bduplicate\b",
    r"\bconflict\b",
    r"\blimit\b",
    r"\boverflow\b",
    r"\bempty\b",
    r"\bmissing\b",
    r"\bmalformed\b",
    r"\btruncate",
    r"\brollback\b",
    r"\bretry\b",
    r"\brace\s*condition",
    r"\bstate\s*(transition|machine|change)",
    r"\btest\s+passes\b",
]

# Keywords that indicate purely structural verification — no tests needed.
# These tasks produce artifacts (files, configs, directories) whose existence
# is the verification, not their runtime behavior.
STRUCTURAL_KEYWORDS = [
    r"\bfile\s+exists\b",
    r"\bdirectory\s+(exists|created|structure)\b",
    r"\bscaffold",
    r"\bconfig(uration)?\s+(file|set|created)",
    r"\bpackage\.json\b",
    r"\btsconfig\b",
    r"\binstall\s+succeeds\b",
    r"\bnpm\s+install\b",
    r"\bcompiles?\s+(with\s+no\s+errors|clean|success)",
    r"\bno\s+(type\s+)?errors\b",
    r"\bexports?\s+(type|interface|module)",
    r"\bschema\s+matches\b",
    r"\bmigrations?\s+(generate|apply|run)\s+(clean|success)",
    r"\binitialize",
]


def should_write_tests(verify_text):
    """Determine if a task's verify text warrants test generation.

    The heuristic checks for behavioral keywords first (positive signal),
    then structural keywords (negative signal). Behavioral wins if both
    are present, because a task that involves both structure and behavior
    should still get tests for the behavioral parts.

    Returns (should_write: bool, reason: str).
    """
    verify_lower = verify_text.lower()

    behavioral_matches = []
    for pattern in BEHAVIORAL_KEYWORDS:
        if re.search(pattern, verify_lower):
            behavioral_matches.append(pattern)

    structural_matches = []
    for pattern in STRUCTURAL_KEYWORDS:
        if re.search(pattern, verify_lower):
            structural_matches.append(pattern)

    if behavioral_matches:
        return True, f"behavioral verification detected ({len(behavioral_matches)} signals)"

    if structural_matches and not behavioral_matches:
        return False, f"purely structural verification ({len(structural_matches)} signals)"

    # Default: write tests. When uncertain, err on the side of testing.
    # A skipped test costs more than a redundant one.
    return True, "no clear signal, defaulting to write tests"


def main():
    if len(sys.argv) < 3:
        print("Usage: should-write-tests.py <tasks.json> <task-id>", file=sys.stderr)
        sys.exit(2)

    tasks_path = sys.argv[1]
    task_id = sys.argv[2]

    with open(tasks_path) as f:
        data = json.load(f)

    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if task is None:
        print(f"Task {task_id} not found in {tasks_path}", file=sys.stderr)
        sys.exit(1)

    should_write, reason = should_write_tests(task["verify"])

    result = {"shouldWrite": should_write, "reason": reason, "taskId": task_id}
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
