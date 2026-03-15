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

    def test_pipeline_requires_only_guidelines(self):
        rc, data, _ = run_script("validate-prereqs.py", ["pipeline"], cwd=self.tmp)
        self.assertEqual(rc, 1)
        self.assertIn("guidelines.md", data["missing"])
        self.assertEqual(len(data["missing"]), 1)

    def test_sketch_requires_guidelines(self):
        rc, data, _ = run_script("validate-prereqs.py", ["sketch"], cwd=self.tmp)
        self.assertEqual(rc, 1)
        self.assertIn("guidelines.md", data["missing"])


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

    def test_all_valid_categories(self):
        spec = os.path.join(self.tmp, "spec.md")
        categories = [
            "DATA_OWNERSHIP", "PERMISSIONS", "PRIVACY",
            "UX_INTENT", "INTEGRATION", "EDGE_CASE",
        ]
        with open(spec, "w") as f:
            for cat in categories:
                f.write(f"[? {cat}: test marker]\n")
        rc, data, _ = run_script("extract-markers.py", [spec])
        self.assertEqual(data["count"], 6)
        for cat in categories:
            self.assertEqual(data["byCategory"][cat], 1)

    def test_multiple_markers_on_same_line(self):
        spec = os.path.join(self.tmp, "spec.md")
        with open(spec, "w") as f:
            f.write("[? PRIVACY: first] and [? PRIVACY: second]\n")
        rc, data, _ = run_script("extract-markers.py", [spec])
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["byCategory"]["PRIVACY"], 2)


class TestShouldWriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _write_tasks(self, verify_text):
        tasks = os.path.join(self.tmp, "tasks.json")
        data = {
            "feature": "test",
            "check": "npm test",
            "tasks": [
                {
                    "id": "1.1",
                    "phase": 1,
                    "title": "Test task",
                    "do": "Build something",
                    "verify": verify_text,
                    "status": "pending",
                    "iteration": None,
                }
            ],
        }
        with open(tasks, "w") as f:
            json.dump(data, f)
        return tasks

    def test_behavioral_verify_returns_true(self):
        tasks = self._write_tasks("Rejects invalid input with 400 error")
        rc, data, _ = run_script("should-write-tests.py", [tasks, "1.1"])
        self.assertEqual(rc, 0)
        self.assertTrue(data["shouldWrite"])

    def test_structural_verify_returns_false(self):
        tasks = self._write_tasks("File exists at src/config.ts and compiles clean")
        rc, data, _ = run_script("should-write-tests.py", [tasks, "1.1"])
        self.assertEqual(rc, 0)
        self.assertFalse(data["shouldWrite"])

    def test_unknown_defaults_to_true(self):
        tasks = self._write_tasks("The system works correctly")
        rc, data, _ = run_script("should-write-tests.py", [tasks, "1.1"])
        self.assertEqual(rc, 0)
        self.assertTrue(data["shouldWrite"])

    def test_missing_task_id_exits_1(self):
        tasks = self._write_tasks("Some verify")
        rc, _, _ = run_script("should-write-tests.py", [tasks, "9.9"])
        self.assertEqual(rc, 1)


class TestUpdateTasks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _write_tasks(self):
        tasks = os.path.join(self.tmp, "tasks.json")
        data = {
            "feature": "test",
            "check": "npm test",
            "tasks": [
                {"id": "1.1", "phase": 1, "title": "First", "do": "Do first",
                 "verify": "Verify first", "status": "pending", "iteration": None},
                {"id": "1.2", "phase": 1, "title": "Second", "do": "Do second",
                 "verify": "Verify second", "status": "pending", "iteration": None},
            ],
        }
        with open(tasks, "w") as f:
            json.dump(data, f)
        return tasks

    def test_marks_task_done(self):
        tasks = self._write_tasks()
        rc, data, _ = run_script("update-tasks.py", [tasks, "1.1", "done", "--iteration", "1"])
        self.assertEqual(rc, 0)
        self.assertTrue(data["updated"])
        self.assertEqual(data["doneCount"], 1)
        self.assertEqual(data["pendingCount"], 1)

        # Verify file was updated in place
        with open(tasks) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk["tasks"][0]["status"], "done")
        self.assertEqual(on_disk["tasks"][0]["iteration"], 1)

    def test_marks_task_blocked(self):
        tasks = self._write_tasks()
        rc, data, _ = run_script("update-tasks.py", [tasks, "1.2", "blocked"])
        self.assertEqual(rc, 0)
        self.assertTrue(data["updated"])
        self.assertEqual(data["blockedCount"], 1)

    def test_missing_task_exits_1(self):
        tasks = self._write_tasks()
        rc, data, _ = run_script("update-tasks.py", [tasks, "9.9", "done"])
        self.assertEqual(rc, 1)
        self.assertFalse(data["updated"])


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

    def test_clarify_auto_complete(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "clean-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("# Clean spec\nNo markers at all.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertIn("clarify", feature["completedStages"])

    def test_next_stage_determination(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "early-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertEqual(feature["nextStage"], "spec")

    def test_state_dir_listed_as_feature(self):
        specs = os.path.join(self.tmp, ".specs")
        os.makedirs(os.path.join(specs, ".state"))
        feat = os.path.join(specs, "real-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        names = [f["name"] for f in data["features"]]
        # .state is not filtered — it shows as an empty feature
        self.assertIn(".state", names)
        self.assertIn("real-feature", names)

    def test_custom_specs_dir(self):
        design = os.path.join(self.tmp, "design")
        feat = os.path.join(design, "my-feat")
        os.makedirs(feat)
        with open(os.path.join(design, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        with open(os.path.join(self.tmp, "trellis.json"), "w") as f:
            json.dump({"specsDir": "design"}, f)
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        self.assertEqual(data["specsDir"], "design")
        self.assertTrue(data["guidelinesExist"])
        self.assertEqual(len(data["features"]), 1)

    def test_compliance_keywords_individually(self):
        specs = os.path.join(self.tmp, ".specs")
        for keyword in ["GDPR", "FERPA", "HIPAA", "COPPA", "SSN", "medical"]:
            feat = os.path.join(specs, f"feat-{keyword}")
            os.makedirs(feat, exist_ok=True)
            with open(os.path.join(feat, "spec.md"), "w") as f:
                f.write(f"# Spec\nThis involves {keyword} compliance.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        for feature in data["features"]:
            self.assertTrue(
                feature["complianceNeeded"],
                f"Expected complianceNeeded=True for {feature['name']}",
            )


class TestAssemblePrompt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Create minimal spec artifacts
        specs = os.path.join(self.tmp, ".specs", "test-feature")
        os.makedirs(specs)
        with open(os.path.join(self.tmp, ".specs", "guidelines.md"), "w") as f:
            f.write("# Guidelines\n\n## Testing\nUse Jest.\n\n## Check Command\n\n```bash\nnpm test\n```\n")
        with open(os.path.join(specs, "plan.md"), "w") as f:
            f.write("# Plan\nBuild the thing.")
        with open(os.path.join(specs, "spec.md"), "w") as f:
            f.write("# Spec\nDo the thing.")
        with open(os.path.join(specs, "tasks.json"), "w") as f:
            json.dump({
                "feature": "test-feature",
                "check": "npm test",
                "tasks": [
                    {"id": "1.1", "phase": 1, "title": "First task", "do": "Build it",
                     "verify": "It works", "status": "pending", "iteration": None}
                ],
            }, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_assembles_implementor_prompt(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["implementor", "test-feature", "--task-id", "1.1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("prompt", data)
        self.assertIn("Build it", data["prompt"])
        self.assertIn("First task", data["prompt"])

    def test_assembles_test_writer_prompt(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["test-writer", "test-feature", "--task-id", "1.1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("It works", data["prompt"])

    def test_assembles_judge_prompt(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["judge", "test-feature"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("Spec", data["prompt"])


if __name__ == "__main__":
    unittest.main()
