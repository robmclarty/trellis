#!/usr/bin/env python3
"""SessionStart hook — shows pipeline status for the specs directory.

Calls scripts/pipeline-status.py and formats the JSON output as a
user-friendly status display. Exits silently if no specs directory exists.
"""

import json
import os
import subprocess
import sys
import time

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

    DISPLAY_LABELS = {"build-ready": "ready"}

    for feature in data.get("features", []):
        parts = []
        for stage in ["pitch", "spec", "plan", "build-ready"]:
            label = DISPLAY_LABELS.get(stage, stage)
            if stage in feature["completedStages"]:
                parts.append(f"\u2713{label}")
            else:
                parts.append(f"\u2717{label}")

        status = " ".join(parts)
        name = feature["name"]

        # Check for active ralph run
        ralph = feature.get("ralphStatus")
        if ralph and ralph.get("active"):
            # Compute live elapsed from startTime for accuracy
            start_time = ralph.get("startTime", 0)
            elapsed = int(time.time()) - start_time if start_time else ralph.get("elapsed", 0)
            hours, remainder = divmod(elapsed, 3600)
            mins, secs = divmod(remainder, 60)
            if hours:
                time_str = f"{hours}h{mins:02d}m"
            else:
                time_str = f"{mins}m{secs:02d}s"
            idx = ralph.get("taskIndex", 0)
            total = ralph.get("total", 0)
            done = ralph.get("done", 0)
            blocked = ralph.get("blocked", 0)
            phase = ralph.get("currentPhase", "")
            ralph_info = f"ralph {time_str} | {idx}/{total} tasks | {done} done"
            if blocked:
                ralph_info += f", {blocked} blocked"
            if phase:
                ralph_info += f" [{phase}]"
            print(f"  {name}: {status} [{ralph_info}]")
        elif ralph and ralph.get("finished"):
            done = ralph.get("done", 0)
            total = ralph.get("total", 0)
            blocked = ralph.get("blocked", 0)
            exit_code = ralph.get("exitCode")
            ralph_info = f"ralph done: {done}/{total}"
            if blocked:
                ralph_info += f", {blocked} blocked"
            if exit_code and exit_code != 0:
                ralph_info += " (exited with error)"
            print(f"  {name}: {status} [{ralph_info}]")
        elif "build-ready" in feature["completedStages"]:
            print(f"  {name}: {status} (ready for /trellis:build)")
        elif all(
            s in feature["completedStages"] for s in ["pitch", "spec", "plan"]
        ):
            print(f"  {name}: {status} (run /trellis:build to generate tasks and start)")
        else:
            print(f"  {name}: {status}")

    sketch_count = data.get("sketchCount", 0)
    if sketch_count > 0:
        print(f"  sketches: {sketch_count} sketch(es)")

    sys.exit(0)


if __name__ == "__main__":
    main()
