#!/usr/bin/env python3
"""Check pipeline status for features in the specs directory.

Usage: pipeline-status.py [feature-name]

If feature-name is provided, checks only that feature.
Otherwise, scans all features under the specs directory.

Outputs JSON with completed stages, next stage, spec cleanliness,
and compliance necessity for each feature.
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


STAGE_ORDER = ["pitch", "spec", "plan", "build-ready"]

ARTIFACT_MAP = {
    "pitch": "pitch.md",
    "spec": "spec.md",
    "plan": "plan.md",
    "build-ready": "tasks.json",
}

MARKER_RE = re.compile(r"\[\?\s*\w+:")

SENSITIVE_KEYWORDS = re.compile(
    r"\b(PII|personal\s+data|student\s+data|health\s+data|"
    r"email|phone|address|SSN|social\s+security|"
    r"date\s+of\s+birth|medical|FERPA|GDPR|FIPPA|COPPA|HIPAA)\b",
    re.IGNORECASE,
)


def check_spec_clean(spec_path):
    """Check if spec.md has any unresolved [? ...] markers."""
    try:
        with open(spec_path) as f:
            content = f.read()
        return len(MARKER_RE.findall(content)) == 0
    except FileNotFoundError:
        return True


def check_compliance_needed(spec_path):
    """Scan spec for sensitive data keywords suggesting compliance review."""
    try:
        with open(spec_path) as f:
            content = f.read()
        return bool(SENSITIVE_KEYWORDS.search(content))
    except FileNotFoundError:
        return False


def check_ralph_status(feature_name):
    """Check for an active or completed ralph run."""
    status_path = os.path.join("logs", f"ralph-{feature_name}", "status.json")
    if not os.path.isfile(status_path):
        return None
    try:
        with open(status_path) as f:
            data = json.load(f)
        return {
            "active": not data.get("finished", False),
            "startTime": data.get("startTime", 0),
            "elapsed": data.get("elapsed", 0),
            "currentTaskId": data.get("currentTaskId", ""),
            "currentPhase": data.get("currentPhase", ""),
            "taskIndex": data.get("taskIndex", 0),
            "done": data.get("done", 0),
            "total": data.get("total", 0),
            "blocked": data.get("blocked", 0),
            "pending": data.get("pending", 0),
            "finished": data.get("finished", False),
            "exitCode": data.get("exitCode"),
        }
    except (json.JSONDecodeError, KeyError):
        return None


def analyze_feature(feature_dir, feature_name):
    """Analyze a single feature directory."""
    completed = []
    spec_path = os.path.join(feature_dir, "spec.md")

    for stage, artifact in ARTIFACT_MAP.items():
        path = os.path.join(feature_dir, artifact)
        if os.path.isfile(path):
            completed.append(stage)

    # Advisory fields — used by the plan skill to decide pre-steps
    spec_clean = check_spec_clean(spec_path) if "spec" in completed else True
    compliance_needed = check_compliance_needed(spec_path) if "spec" in completed else False
    compliance_completed = os.path.isfile(os.path.join(feature_dir, "compliance.md"))

    # Determine next stage — simple linear walk
    next_stage = None
    for stage in STAGE_ORDER:
        if stage not in completed:
            next_stage = stage
            break

    # Check for ralph run status
    ralph_status = check_ralph_status(feature_name)

    return {
        "name": feature_name,
        "completedStages": sorted(completed, key=lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 99),
        "nextStage": next_stage,
        "specClean": spec_clean,
        "complianceNeeded": compliance_needed,
        "complianceCompleted": compliance_completed,
        "ralphStatus": ralph_status,
    }


def count_sketches(specs_dir):
    """Count sketch files."""
    sketches_dir = os.path.join(specs_dir, "sketches")
    if not os.path.isdir(sketches_dir):
        return 0
    return len([f for f in os.listdir(sketches_dir) if f.endswith(".md")])


def main():
    feature_filter = sys.argv[1] if len(sys.argv) > 1 else None
    specs_dir = resolve_specs_dir()

    trellis_json_exist = os.path.isfile("trellis.json")

    if not os.path.isdir(specs_dir):
        result = {
            "specsDir": specs_dir,
            "trellisJsonExist": trellis_json_exist,
            "guidelinesExist": False,
            "features": [],
            "sketchCount": 0,
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return

    guidelines_exist = os.path.isfile(os.path.join(specs_dir, "guidelines.md"))
    features = []

    if feature_filter:
        feature_dir = os.path.join(specs_dir, feature_filter)
        if os.path.isdir(feature_dir):
            features.append(analyze_feature(feature_dir, feature_filter))
    else:
        for entry in sorted(os.listdir(specs_dir)):
            if entry == "sketches" or entry == "guidelines.md":
                continue
            feature_dir = os.path.join(specs_dir, entry)
            if os.path.isdir(feature_dir):
                features.append(analyze_feature(feature_dir, entry))

    result = {
        "specsDir": specs_dir,
        "trellisJsonExist": trellis_json_exist,
        "guidelinesExist": guidelines_exist,
        "features": features,
        "sketchCount": count_sketches(specs_dir),
    }

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
