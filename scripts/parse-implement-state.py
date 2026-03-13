#!/usr/bin/env python3
"""Parse implement-state.md into structured JSON.

Usage: parse-implement-state.py [path-to-implement-state.md]

Defaults to .specs/.state/implement-state.md in the current directory.
Outputs JSON with config, criteria, counts, and iteration info.
"""

import json
import re
import sys


def parse_state_file(filepath):
    """Parse the implement state file into structured data."""
    try:
        with open(filepath) as f:
            content = f.read()
    except FileNotFoundError:
        return None

    sections = split_sections(content)

    config = parse_config(sections.get("Config", ""))
    criteria = parse_criteria(sections.get("Acceptance Criteria", ""))
    input_info = parse_input(sections.get("Input", ""))
    branch = parse_branch(sections.get("Branch", ""))
    pipeline = parse_pipeline(sections.get("Oracle Pipeline", ""))
    iterations = count_iterations(sections.get("Iteration Log", ""))

    pending = [c for c in criteria if c["status"] == "pending"]
    done = [c for c in criteria if c["status"] == "done"]

    return {
        "input": input_info,
        "branch": branch,
        "config": config,
        "pipeline": pipeline,
        "criteria": criteria,
        "pendingCount": len(pending),
        "doneCount": len(done),
        "nextPendingId": pending[0]["id"] if pending else None,
        "iteration": iterations,
    }


def split_sections(content):
    """Split markdown content into sections by ## headers."""
    sections = {}
    current_name = None
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_name:
                sections[current_name] = "\n".join(current_lines)
            current_name = line[3:].strip()
            current_lines = []
        elif current_name:
            current_lines.append(line)

    if current_name:
        sections[current_name] = "\n".join(current_lines)

    return sections


def parse_config(text):
    """Parse Config section: key-value pairs like '- Key: value'."""
    config = {}
    for line in text.strip().split("\n"):
        match = re.match(r"^- (.+?):\s*(.+)", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip().strip("`")
            if value.lower() in ("off", "false", "no"):
                value = False
            elif value.lower() in ("on", "true", "yes"):
                value = True
            config[key] = value
    return config


def parse_input(text):
    """Parse Input section."""
    info = {}
    for line in text.strip().split("\n"):
        match = re.match(r"^- (.+?):\s*(.+)", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            if value == "N/A":
                value = None
            info[key] = value
    return info


def parse_branch(text):
    """Parse Branch section."""
    branch = {}
    for line in text.strip().split("\n"):
        match = re.match(r"^- (.+?):\s*(.+)", line)
        if match:
            key = match.group(1).strip().lower()
            branch[key] = match.group(2).strip()
    return branch


def parse_pipeline(text):
    """Parse Oracle Pipeline section: checkbox list with commands."""
    stages = []
    for line in text.strip().split("\n"):
        match = re.match(r"^- \[([ x])\] (\w+):\s*(.*)", line)
        if match:
            stages.append({
                "name": match.group(2),
                "enabled": True,
                "command": match.group(3).strip().strip("`") or None,
                "status": "enabled" if match.group(1) == "x" else "pending",
            })
    return stages


def parse_criteria(text):
    """Parse Acceptance Criteria section: checkbox list with status."""
    criteria = []
    for line in text.strip().split("\n"):
        match = re.match(
            r"^- \[([ x])\] ([\w-]+)\s*(?:\(([^)]*)\))?:\s*(.*)", line
        )
        if match:
            done = match.group(1) == "x"
            crit_id = match.group(2)
            task_ref = match.group(3) or ""
            rest = match.group(4).strip()

            # Extract status annotation like (done, iteration 1) or (pending)
            status_match = re.search(r"\((\w+)(?:,\s*iteration\s*(\d+))?\)\s*$", rest)
            iteration = None
            if status_match:
                iteration = int(status_match.group(2)) if status_match.group(2) else None
                rest = rest[:status_match.start()].strip()

            criteria.append({
                "id": crit_id,
                "taskRef": task_ref.strip() if task_ref else None,
                "summary": rest,
                "status": "done" if done else "pending",
                "iteration": iteration,
            })
    return criteria


def count_iterations(text):
    """Count iteration headers in the Iteration Log."""
    return len(re.findall(r"^### Iteration \d+", text, re.MULTILINE))


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else ".specs/.state/implement-state.md"
    result = parse_state_file(filepath)

    if result is None:
        json.dump({"error": f"File not found: {filepath}"}, sys.stdout, indent=2)
        print()
        sys.exit(1)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
