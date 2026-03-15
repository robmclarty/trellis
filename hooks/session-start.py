#!/usr/bin/env python3
"""SessionStart hook — shows pipeline status for the specs directory.

Calls scripts/pipeline-status.py and formats the JSON output as a
user-friendly status display. Exits silently if no specs directory exists.
"""

import json
import os
import subprocess
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    script = os.path.join(PLUGIN_ROOT, "scripts", "pipeline-status.py")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        sys.exit(0)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        sys.exit(0)

    if (
        not data.get("trellisJsonExist")
        and not data.get("guidelinesExist")
        and not data.get("features")
    ):
        sys.exit(0)

    print("\U0001f4cb Trellis pipeline status:")

    if data.get("trellisJsonExist"):
        print("  \u2713 trellis.json")
    else:
        print("  \u2717 trellis.json (run /trellis:init to initialize)")

    if data.get("guidelinesExist"):
        print("  \u2713 guidelines.md")
    else:
        print("  \u2717 guidelines.md (run /trellis:guidelines)")

    DISPLAY_LABELS = {"implement-ready": "ready"}

    for feature in data.get("features", []):
        parts = []
        for stage in ["pitch", "spec", "plan", "implement-ready"]:
            label = DISPLAY_LABELS.get(stage, stage)
            if stage in feature["completedStages"]:
                parts.append(f"\u2713{label}")
            else:
                parts.append(f"\u2717{label}")

        status = " ".join(parts)
        name = feature["name"]

        all_core = all(
            s in feature["completedStages"] for s in ["pitch", "spec", "plan"]
        )
        if "implement-ready" in feature["completedStages"]:
            print(f"  {name}: {status} (ready for /trellis:implement)")
        elif all_core:
            print(f"  {name}: {status} (run /trellis:implement to generate tasks and start)")
        else:
            print(f"  {name}: {status}")

    sketch_count = data.get("sketchCount", 0)
    if sketch_count > 0:
        print(f"  sketches: {sketch_count} sketch(es)")

    sys.exit(0)


if __name__ == "__main__":
    main()
