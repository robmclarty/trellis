#!/usr/bin/env python3
"""Extract acceptance criteria from tasks.md and optionally spec.md.

Usage: extract-criteria.py <path-to-tasks.md> [path-to-spec.md]

Parses tasks.md for task items with Verify blocks and spec.md §8 for
success criteria. Outputs structured JSON.
"""

import json
import re
import sys


def parse_tasks(filepath):
    """Parse tasks.md and extract criteria from Verify blocks."""
    criteria = []
    current_task_id = None
    current_task_title = None
    in_verify = False
    verify_lines = []

    # Pattern: - [ ] 1.1 — Title  or  - [x] 1.1 -- Title
    task_re = re.compile(r"^- \[([ x])\] (\d+\.\d+)\s*[—–-]+\s*(.+)")
    verify_re = re.compile(r"^\s+\*\*Verify:\*\*\s*(.*)")

    try:
        with open(filepath) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    def flush_verify():
        if current_task_id and verify_lines:
            summary = " ".join(line.strip() for line in verify_lines).strip()
            criteria.append({
                "id": f"AC-{len(criteria) + 1}",
                "taskId": current_task_id,
                "taskTitle": current_task_title,
                "summary": summary,
                "status": "pending",
            })

    for line in lines:
        task_match = task_re.match(line)
        if task_match:
            flush_verify()
            in_verify = False
            verify_lines = []
            current_task_id = task_match.group(2)
            current_task_title = task_match.group(3).strip()
            continue

        verify_match = verify_re.match(line)
        if verify_match:
            flush_verify()
            in_verify = True
            verify_lines = [verify_match.group(1)]
            continue

        if in_verify:
            stripped = line.strip()
            if stripped and not stripped.startswith("**") and not stripped.startswith("- ["):
                verify_lines.append(stripped)
            else:
                in_verify = False

    flush_verify()
    return criteria


def parse_spec_criteria(filepath):
    """Parse spec.md §8 for success criteria."""
    criteria = []
    in_section_8 = False

    criterion_re = re.compile(r"^- \[([ x])\]\s+(.+)")

    try:
        with open(filepath) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []

    for line in lines:
        if "§8" in line and ("#" in line or "Success Criteria" in line):
            in_section_8 = True
            continue

        if in_section_8 and line.startswith("## "):
            break

        if in_section_8:
            match = criterion_re.match(line)
            if match:
                criteria.append({
                    "id": f"SC-{len(criteria) + 1}",
                    "source": "spec-§8",
                    "summary": match.group(2).strip(),
                    "status": "pending",
                })

    return criteria


def main():
    if len(sys.argv) < 2:
        print("Usage: extract-criteria.py <tasks.md> [spec.md]", file=sys.stderr)
        sys.exit(2)

    tasks_path = sys.argv[1]
    spec_path = sys.argv[2] if len(sys.argv) > 2 else None

    task_criteria = parse_tasks(tasks_path)
    spec_criteria = parse_spec_criteria(spec_path) if spec_path else []

    result = {
        "taskCriteria": task_criteria,
        "specCriteria": spec_criteria,
        "totalCount": len(task_criteria) + len(spec_criteria),
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
