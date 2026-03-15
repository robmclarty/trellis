#!/usr/bin/env python3
"""Validate structure and content of Trellis spec documents.

Usage: validate-doc.py <file-path>

Auto-detects document type from filename (pitch.md, spec.md, plan.md).
Outputs JSON to stdout with validation results. Always exits 0.
"""

import json
import os
import re
import sys

MIN_SECTION_CHARS = 20

# Canonical section titles for spec and plan documents.
SPEC_TITLES = {
    1: "Context",
    2: "Functional Overview",
    3: "Actors and Permissions",
    4: "Data Model",
    5: "Interfaces",
    6: "Business Rules",
    7: "Failure Modes",
    8: "Success Criteria",
    9: "Constraints",
    10: "Open Questions",
}

PLAN_TITLES = {
    1: "Technical Summary",
    2: "Architecture",
    3: "Technology Decisions",
    4: "Data Access Patterns",
    5: "Interface Implementation",
    6: "File Structure",
    7: "Error Handling Strategy",
    8: "Testing Strategy",
    9: "Deployment and Infrastructure",
    10: "Migration Path",
}

# Expected order of pitch sections (for ordering check).
PITCH_ORDER = ["Problem", "Appetite", "Sketches", "Shape", "No-Gos", "Rabbit Holes"]

# Pitch section name normalization: map variants to canonical names.
PITCH_ALIASES = {
    "no gos": "No-Gos",
    "no-gos": "No-Gos",
    "nogos": "No-Gos",
    "rabbit holes": "Rabbit Holes",
    "rabbit-holes": "Rabbit Holes",
    "rabbitholes": "Rabbit Holes",
}


def detect_type(filepath):
    """Return document type based on filename, or None."""
    basename = os.path.basename(filepath)
    if basename == "pitch.md":
        return "pitch"
    if basename == "spec.md":
        return "spec"
    if basename == "plan.md":
        return "plan"
    return None


def strip_len(text):
    """Count non-whitespace characters in text."""
    return len(re.sub(r"\s", "", text))


def parse_heading_sections(content):
    """Parse content into sections split by ## headings.

    Returns list of (heading_text, body) tuples.
    """
    pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(content))
    if not matches:
        return []

    sections = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append((heading, body))
    return sections


def parse_numbered_sections(content):
    """Parse content into numbered sections using §N — Title format.

    Returns list of (number, title, body, raw_heading) tuples.
    """
    pattern = re.compile(r"^##\s*§(\d+)\s*[—–-]\s*(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(content))
    if not matches:
        return []

    sections = []
    for i, match in enumerate(matches):
        num = int(match.group(1))
        title = match.group(2).strip()
        raw = match.group(0).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append((num, title, body, raw))
    return sections


def normalize_pitch_name(heading):
    """Normalize a pitch section heading to its canonical name."""
    lower = heading.lower().strip()
    if lower in PITCH_ALIASES:
        return PITCH_ALIASES[lower]
    # Title-case match for standard names
    for name in PITCH_ORDER:
        if lower == name.lower():
            return name
    return heading


def validate_pitch(content):
    """Validate a pitch document. Returns (errors, warnings)."""
    errors = []
    warnings = []

    sections = parse_heading_sections(content)
    found = {}
    found_order = []

    for heading, body in sections:
        canonical = normalize_pitch_name(heading)
        if canonical in found:
            errors.append(f"Duplicate section: {canonical}")
            continue
        found[canonical] = body
        found_order.append(canonical)

    # Check required sections
    required = ["Problem", "Appetite", "Shape", "No-Gos"]
    for name in required:
        if name not in found:
            errors.append(f"Missing required section: {name}")
        elif strip_len(found[name]) < MIN_SECTION_CHARS:
            errors.append(f"Section too short: {name} (needs {MIN_SECTION_CHARS}+ non-whitespace chars)")

    # Warn on missing optional sections (Rabbit Holes only; Sketches is fully optional)
    if "Rabbit Holes" not in found:
        warnings.append("Missing optional section: Rabbit Holes")

    # Check ordering
    expected_positions = {name: i for i, name in enumerate(PITCH_ORDER)}
    ordered_found = [name for name in found_order if name in expected_positions]
    for i in range(len(ordered_found) - 1):
        if expected_positions[ordered_found[i]] > expected_positions[ordered_found[i + 1]]:
            warnings.append(
                f"Sections out of order: {ordered_found[i]} appears before {ordered_found[i + 1]}"
            )
            break

    return errors, warnings


def validate_numbered_doc(content, required_nums, titles, doc_type):
    """Validate a numbered-section document (spec or plan).

    Returns (errors, warnings).
    """
    errors = []
    warnings = []

    sections = parse_numbered_sections(content)

    # Also check for ## headings that don't match §N format (malformed)
    all_h2 = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    numbered_headings = {s[3] for s in sections}  # raw heading strings
    for h2 in all_h2:
        full = f"## {h2}"
        if full not in numbered_headings:
            # Check if it looks like it's trying to be a numbered section
            if re.search(r"§\d+", h2):
                errors.append(f"Malformed section heading: {full} (expected format: ## §N — Title)")

    found_nums = set()
    prev_num = 0

    for num, title, body, raw in sections:
        # Duplicate check
        if num in found_nums:
            errors.append(f"Duplicate section: §{num}")
            continue
        found_nums.add(num)

        # Order check
        if num < prev_num:
            errors.append(f"Section out of order: §{num} appears after §{prev_num}")
        prev_num = num

        # Content check
        is_required = num in required_nums
        body_is_na = body.strip().upper().startswith("N/A")

        if is_required and strip_len(body) < MIN_SECTION_CHARS:
            errors.append(
                f"Section too short: §{num} — {titles.get(num, title)} "
                f"(needs {MIN_SECTION_CHARS}+ non-whitespace chars)"
            )
        elif not is_required and not body_is_na and strip_len(body) < MIN_SECTION_CHARS:
            warnings.append(
                f"Section too short: §{num} — {titles.get(num, title)} "
                f"(needs {MIN_SECTION_CHARS}+ non-whitespace chars)"
            )

    # Missing required sections
    for num in sorted(required_nums):
        if num not in found_nums:
            errors.append(f"Missing required section: §{num} — {titles.get(num, '?')}")

    # Missing optional sections
    all_nums = set(titles.keys())
    optional_nums = all_nums - required_nums
    for num in sorted(optional_nums):
        if num not in found_nums:
            warnings.append(f"Missing optional section: §{num} — {titles.get(num, '?')}")

    return errors, warnings


def validate_spec(content):
    """Validate a spec document."""
    return validate_numbered_doc(content, {1, 2, 8, 9}, SPEC_TITLES, "spec")


def validate_plan(content):
    """Validate a plan document."""
    errors, warnings = validate_numbered_doc(content, {1, 2, 3, 6}, PLAN_TITLES, "plan")

    # Extra check: §3 should contain a markdown table
    sections = parse_numbered_sections(content)
    for num, title, body, raw in sections:
        if num == 3 and "|" not in body:
            warnings.append("§3 — Technology Decisions: expected a markdown table (no | found)")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-doc.py <file-path>", file=sys.stderr)
        sys.exit(2)

    filepath = sys.argv[1]

    doc_type = detect_type(filepath)
    if doc_type is None:
        json.dump({"type": None, "file": filepath, "valid": True, "errors": [], "warnings": []}, sys.stdout)
        print()
        sys.exit(0)

    if not os.path.isfile(filepath):
        json.dump(
            {"type": None, "file": filepath, "valid": False, "errors": [f"File not found: {filepath}"], "warnings": []},
            sys.stdout,
        )
        print()
        sys.exit(0)

    with open(filepath) as f:
        content = f.read()

    validators = {
        "pitch": validate_pitch,
        "spec": validate_spec,
        "plan": validate_plan,
    }

    errors, warnings = validators[doc_type](content)

    result = {
        "type": doc_type,
        "file": filepath,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }

    json.dump(result, sys.stdout, indent=2)
    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
