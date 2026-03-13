#!/usr/bin/env python3
"""Extract ambiguity markers from a spec file.

Usage: extract-markers.py <path-to-spec.md>

Scans for [? CATEGORY: ...] markers and outputs structured JSON with
marker details, counts, and breakdown by category.
"""

import json
import re
import sys

MARKER_RE = re.compile(
    r"\[\?\s*(DATA_OWNERSHIP|PERMISSIONS|PRIVACY|UX_INTENT|INTEGRATION|EDGE_CASE)"
    r":\s*([^\]]*)\]"
)


def extract_markers(filepath):
    markers = []
    by_category = {}

    try:
        with open(filepath) as f:
            for line_num, line in enumerate(f, start=1):
                for match in MARKER_RE.finditer(line):
                    category = match.group(1)
                    text = match.group(0)
                    markers.append({
                        "category": category,
                        "text": text,
                        "line": line_num,
                    })
                    by_category[category] = by_category.get(category, 0) + 1
    except FileNotFoundError:
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    return {
        "file": filepath,
        "markers": markers,
        "count": len(markers),
        "byCategory": by_category,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: extract-markers.py <path-to-spec.md>", file=sys.stderr)
        sys.exit(2)

    result = extract_markers(sys.argv[1])
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
