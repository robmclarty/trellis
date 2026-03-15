#!/usr/bin/env python3
"""Assemble a fully-baked prompt from a template and spec artifacts.

Usage: assemble-prompt.py <template-name> <feature> [--task-id ID] [--check-output FILE]

Reads a prompt template from scripts/templates/, resolves {{variables}} by
reading spec artifacts (tasks.json, plan.md, spec.md, guidelines.md), and
outputs the assembled prompt as a JSON object to stdout.

This script exists so that the ralph loop script can do ALL orchestration
deterministically. The LLM receives a complete prompt with all context
pre-assembled — no skill loading, no orchestration instructions, no state
management. The LLM's only job is the creative work: writing tests, writing
code, fixing errors, or judging alignment.

Templates use {{variable}} syntax. Variables are resolved from:
- tasks.json: task fields, check command, completed task titles
- plan.md: full content (implementor needs architectural context)
- spec.md: full content (judge needs spec for alignment review)
- guidelines.md: full content + extracted test conventions
- git: diff stat (for judge)
- check output file: stderr/stdout from failed check (for retry)
"""

import argparse
import json
import os
import re
import subprocess
import sys


def resolve_specs_dir():
    """Read specsDir from trellis.json, default to .specs/."""
    try:
        with open("trellis.json") as f:
            return json.load(f).get("specsDir", ".specs")
    except (FileNotFoundError, json.JSONDecodeError):
        return ".specs"


def read_file_safe(path):
    """Read a file, returning empty string if it doesn't exist.

    We don't fail on missing files because not all templates need all
    artifacts. The test-writer template doesn't need spec.md, for instance.
    Missing content results in an empty variable, which the LLM handles fine.
    """
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def extract_test_conventions(guidelines_content):
    """Extract the Testing section from guidelines.md.

    The test-writer needs to know the project's test framework, file patterns,
    and conventions, but doesn't need the full guidelines. We extract just the
    Testing section to keep the prompt focused.
    """
    match = re.search(
        r"^## Testing\b.*?(?=^## |\Z)", guidelines_content, re.MULTILINE | re.DOTALL
    )
    return match.group(0).strip() if match else ""


def extract_check_command(guidelines_content):
    """Extract the check command from guidelines.md Check Command section.

    Falls back to tasks.json check field if guidelines doesn't have it.
    The check command is a fenced code block inside the Check Command section.
    """
    section = re.search(
        r"^## Check Command\b.*?(?=^## |\Z)",
        guidelines_content,
        re.MULTILINE | re.DOTALL,
    )
    if not section:
        return ""
    code_block = re.search(r"```(?:bash)?\n(.*?)\n```", section.group(0), re.DOTALL)
    return code_block.group(1).strip() if code_block else ""


def get_completed_tasks(tasks_data):
    """Build a summary of completed tasks for context.

    The implementor needs to know what's already been built so it doesn't
    recreate existing code. A list of completed task titles is enough —
    the LLM can infer what files/modules exist from the task descriptions.
    """
    completed = [t for t in tasks_data["tasks"] if t["status"] == "done"]
    if not completed:
        return "No tasks completed yet. This is the first task."
    lines = [f"- {t['id']}: {t['title']}" for t in completed]
    return "\n".join(lines)


def get_tasks_summary(tasks_data):
    """Build a full task status summary for the judge.

    The judge needs to see all tasks and their status to evaluate
    completeness and identify any gaps.
    """
    lines = []
    for t in tasks_data["tasks"]:
        status_icon = {"done": "DONE", "blocked": "BLOCKED", "pending": "PENDING"}[
            t["status"]
        ]
        lines.append(f"- [{status_icon}] {t['id']}: {t['title']}")
        lines.append(f"  Verify: {t['verify']}")
    return "\n".join(lines)


def get_git_diff_stat():
    """Get git diff --stat for the judge prompt.

    The judge uses this to understand the scope of changes made.
    We use --stat for a summary, not the full diff (which would bloat the prompt).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "Unable to get git diff"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "Unable to get git diff"


def assemble(template_name, feature, task_id=None, check_output_path=None):
    """Resolve all template variables and produce the final prompt.

    Each template type needs different variables. Rather than conditionally
    loading artifacts, we load everything and let unused variables resolve
    to empty strings. This keeps the logic simple and the templates flexible.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "templates", f"{template_name}.txt")

    template = read_file_safe(template_path)
    if not template:
        print(f"Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    specs_dir = resolve_specs_dir()
    feature_dir = os.path.join(specs_dir, feature)

    # Load artifacts
    tasks_path = os.path.join(feature_dir, "tasks.json")
    tasks_data = {}
    try:
        with open(tasks_path) as f:
            tasks_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    plan = read_file_safe(os.path.join(feature_dir, "plan.md"))
    spec = read_file_safe(os.path.join(feature_dir, "spec.md"))
    guidelines = read_file_safe(os.path.join(specs_dir, "guidelines.md"))

    # Task-specific variables
    task = None
    if task_id and tasks_data.get("tasks"):
        task = next((t for t in tasks_data["tasks"] if t["id"] == task_id), None)

    # Build variable map
    variables = {
        "task_do": task["do"] if task else "",
        "task_verify": task["verify"] if task else "",
        "task_title": task["title"] if task else "",
        "task_id": task_id or "",
        "plan": plan,
        "spec_excerpt": spec,
        "guidelines": guidelines,
        "check_command": tasks_data.get("check", ""),
        "check_output": read_file_safe(check_output_path) if check_output_path else "",
        "completed_tasks": get_completed_tasks(tasks_data) if tasks_data else "",
        "tasks_summary": get_tasks_summary(tasks_data) if tasks_data else "",
        "test_conventions": extract_test_conventions(guidelines),
        "git_diff_stat": get_git_diff_stat() if template_name == "judge" else "",
    }

    # Resolve template variables
    def replace_var(match):
        var_name = match.group(1)
        return variables.get(var_name, f"{{{{UNRESOLVED: {var_name}}}}}")

    prompt = re.sub(r"\{\{(\w+)\}\}", replace_var, template)

    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Assemble a prompt from template and spec artifacts"
    )
    parser.add_argument(
        "template",
        choices=["test-writer", "implementor", "implementor-retry", "judge"],
        help="Template name",
    )
    parser.add_argument("feature", help="Feature name")
    parser.add_argument("--task-id", help="Task ID (required for task-specific templates)")
    parser.add_argument("--check-output", help="Path to file with check command output")

    args = parser.parse_args()

    prompt = assemble(
        args.template, args.feature, args.task_id, args.check_output
    )

    result = {"prompt": prompt}
    json.dump(result, sys.stdout)
    print()


if __name__ == "__main__":
    main()
