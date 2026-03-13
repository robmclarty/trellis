#!/usr/bin/env python3
"""Tests for Trellis data scripts in scripts/.

Run from project root: python3 tests/test-scripts.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def run_script(name, args=None, cwd=None):
    """Run a script and return (returncode, parsed_json_or_None, raw_stdout)."""
    cmd = [sys.executable, os.path.join(SCRIPTS, name)] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    try:
        data = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        data = None
    return result.returncode, data, result.stdout


class TestValidatePrereqs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_no_args(self):
        rc, _, _ = run_script("validate-prereqs.py", cwd=self.tmp)
        self.assertEqual(rc, 2)

    def test_unknown_skill(self):
        rc, _, _ = run_script("validate-prereqs.py", ["bogus"], cwd=self.tmp)
        self.assertEqual(rc, 2)

    def test_guidelines_no_prereqs(self):
        rc, data, _ = run_script("validate-prereqs.py", ["guidelines"], cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])
        self.assertEqual(data["missing"], [])
        self.assertEqual(data["specsDir"], ".specs")

    def test_custom_specs_dir(self):
        with open(os.path.join(self.tmp, "trellis.json"), "w") as f:
            json.dump({"specsDir": "design"}, f)
        rc, data, _ = run_script("validate-prereqs.py", ["guidelines"], cwd=self.tmp)
        self.assertEqual(data["specsDir"], "design")

    def test_pitch_missing_guidelines(self):
        rc, data, _ = run_script("validate-prereqs.py", ["pitch"], cwd=self.tmp)
        self.assertEqual(rc, 1)
        self.assertFalse(data["valid"])
        self.assertIn("guidelines.md", data["missing"])

    def test_pitch_with_guidelines(self):
        specs = os.path.join(self.tmp, ".specs")
        os.makedirs(specs)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        rc, data, _ = run_script("validate-prereqs.py", ["pitch"], cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])

    def test_spec_missing_feature_prereqs(self):
        specs = os.path.join(self.tmp, ".specs")
        os.makedirs(specs)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        rc, data, _ = run_script("validate-prereqs.py", ["spec", "my-feature"], cwd=self.tmp)
        self.assertEqual(rc, 1)
        self.assertIn("my-feature/pitch.md", data["missing"])

    def test_spec_all_present(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "my-feature")
        os.makedirs(feat)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        rc, data, _ = run_script("validate-prereqs.py", ["spec", "my-feature"], cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])

    def test_implement_checks_feature_dir(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        with open(os.path.join(self.tmp, ".specs", "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        rc, data, _ = run_script("validate-prereqs.py", ["implement", "my-feature"], cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])


class TestExtractMarkers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_no_args(self):
        rc, _, _ = run_script("extract-markers.py", cwd=self.tmp)
        self.assertEqual(rc, 2)

    def test_file_not_found(self):
        rc, _, _ = run_script("extract-markers.py", ["/nonexistent/file.md"])
        self.assertEqual(rc, 1)

    def test_no_markers(self):
        spec = os.path.join(self.tmp, "spec.md")
        with open(spec, "w") as f:
            f.write("# Clean spec\nNo markers here.\n")
        rc, data, _ = run_script("extract-markers.py", [spec])
        self.assertEqual(rc, 0)
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["markers"], [])

    def test_finds_markers(self):
        spec = os.path.join(self.tmp, "spec.md")
        with open(spec, "w") as f:
            f.write("line one\n")
            f.write("[? DATA_OWNERSHIP: who owns this?]\n")
            f.write("line three\n")
            f.write("[? PRIVACY: is this PII?]\n")
            f.write("[? PRIVACY: another one]\n")
        rc, data, _ = run_script("extract-markers.py", [spec])
        self.assertEqual(rc, 0)
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["byCategory"]["DATA_OWNERSHIP"], 1)
        self.assertEqual(data["byCategory"]["PRIVACY"], 2)
        self.assertEqual(data["markers"][0]["line"], 2)

    def test_ignores_unknown_categories(self):
        spec = os.path.join(self.tmp, "spec.md")
        with open(spec, "w") as f:
            f.write("[? UNKNOWN: not recognized]\n")
        rc, data, _ = run_script("extract-markers.py", [spec])
        self.assertEqual(data["count"], 0)


class TestExtractCriteria(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_no_args(self):
        rc, _, _ = run_script("extract-criteria.py", cwd=self.tmp)
        self.assertEqual(rc, 2)

    def test_basic_task_criteria(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n\n")
            f.write("- [ ] 1.1 -- Set up project\n")
            f.write("  **Verify:** Project builds successfully\n")
            f.write("\n")
            f.write("- [ ] 1.2 -- Add auth\n")
            f.write("  **Verify:** Login returns JWT token\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks])
        self.assertEqual(rc, 0)
        self.assertEqual(len(data["taskCriteria"]), 2)
        self.assertEqual(data["taskCriteria"][0]["id"], "AC-1")
        self.assertEqual(data["taskCriteria"][0]["taskId"], "1.1")
        self.assertIn("builds successfully", data["taskCriteria"][0]["summary"])

    def test_spec_criteria(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n")
        spec = os.path.join(self.tmp, "spec.md")
        with open(spec, "w") as f:
            f.write("## §8 Success Criteria\n\n")
            f.write("- [ ] Users can log in\n")
            f.write("- [ ] Dashboard loads in <2s\n")
            f.write("\n## §9 Constraints\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks, spec])
        self.assertEqual(rc, 0)
        self.assertEqual(len(data["specCriteria"]), 2)
        self.assertEqual(data["specCriteria"][0]["id"], "SC-1")

    def test_missing_spec_returns_empty(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks, "/nonexistent/spec.md"])
        self.assertEqual(rc, 0)
        self.assertEqual(data["specCriteria"], [])


class TestPipelineStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_no_specs_dir(self):
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertFalse(data["guidelinesExist"])
        self.assertEqual(data["features"], [])

    def test_with_guidelines_and_feature(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "my-feature")
        os.makedirs(feat)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("# Spec\nClean spec with no markers.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertTrue(data["guidelinesExist"])
        self.assertEqual(len(data["features"]), 1)
        feature = data["features"][0]
        self.assertEqual(feature["name"], "my-feature")
        self.assertIn("pitch", feature["completedStages"])
        self.assertIn("spec", feature["completedStages"])
        self.assertTrue(feature["specClean"])

    def test_spec_with_markers_not_clean(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "dirty-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("[? PRIVACY: who handles this?]\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertFalse(feature["specClean"])

    def test_compliance_needed(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "pii-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("# Spec\nThis stores PII and email addresses.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertTrue(feature["complianceNeeded"])

    def test_counts_sketches(self):
        specs = os.path.join(self.tmp, ".specs")
        sketches = os.path.join(specs, "sketches")
        os.makedirs(sketches)
        for i in range(3):
            with open(os.path.join(sketches, f"sketch-{i}.md"), "w") as f:
                f.write(f"# Sketch {i}")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        self.assertEqual(data["sketchCount"], 3)

    def test_feature_filter(self):
        specs = os.path.join(self.tmp, ".specs")
        for name in ["alpha", "beta"]:
            feat = os.path.join(specs, name)
            os.makedirs(feat)
            with open(os.path.join(feat, "pitch.md"), "w") as f:
                f.write("# Pitch")
        rc, data, _ = run_script("pipeline-status.py", ["alpha"], cwd=self.tmp)
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["name"], "alpha")


class TestParseImplementState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_file_not_found(self):
        rc, data, _ = run_script("parse-implement-state.py", ["/nonexistent/file.md"])
        self.assertEqual(rc, 1)
        self.assertIn("error", data)

    def test_basic_state_parsing(self):
        state = os.path.join(self.tmp, ".implement-state.md")
        with open(state, "w") as f:
            f.write("""# Implementation State

## Input
- Feature: my-feature
- Source: spec-driven

## Branch
- name: feat/my-feature
- base: main

## Config
- Type-check: `npm run typecheck`
- Lint: `npm run lint`
- Test: off

## Oracle Pipeline
- [x] build: `npm run build`
- [x] lint: `npm run lint`
- [ ] test: `npm test`

## Acceptance Criteria
- [x] AC-1 (task 1.1): Set up project (done, iteration 1)
- [ ] AC-2 (task 1.2): Add auth endpoint (pending)
- [ ] AC-3 (task 2.1): Dashboard layout (pending)

## Iteration Log
### Iteration 1
Built the project.
### Iteration 2
Added auth.
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(data["doneCount"], 1)
        self.assertEqual(data["pendingCount"], 2)
        self.assertEqual(data["nextPendingId"], "AC-2")
        self.assertEqual(data["iteration"], 2)
        self.assertEqual(data["branch"]["name"], "feat/my-feature")
        self.assertEqual(len(data["pipeline"]), 3)
        self.assertEqual(data["criteria"][0]["status"], "done")
        self.assertEqual(data["criteria"][1]["status"], "pending")

    def test_all_done(self):
        state = os.path.join(self.tmp, ".implement-state.md")
        with open(state, "w") as f:
            f.write("""## Acceptance Criteria
- [x] AC-1 (task 1.1): Done thing (done, iteration 1)
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(data["pendingCount"], 0)
        self.assertEqual(data["doneCount"], 1)
        self.assertIsNone(data["nextPendingId"])


if __name__ == "__main__":
    unittest.main()
