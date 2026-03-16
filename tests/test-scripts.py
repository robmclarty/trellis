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

    def test_build_checks_feature_dir(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        with open(os.path.join(self.tmp, ".specs", "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        rc, data, _ = run_script("validate-prereqs.py", ["build", "my-feature"], cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])

    def test_run_requires_only_guidelines(self):
        rc, data, _ = run_script("validate-prereqs.py", ["run"], cwd=self.tmp)
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

    def test_spec_clean_advisory_field(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "clean-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("# Clean spec\nNo markers at all.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertTrue(feature["specClean"])
        # clarify is no longer a standalone stage
        self.assertNotIn("clarify", feature["completedStages"])

    def test_next_stage_determination(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "early-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertEqual(feature["nextStage"], "spec")

    def test_next_stage_after_spec_is_plan(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "mid-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("# Spec\nClean spec.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertEqual(feature["nextStage"], "plan")

    def test_compliance_completed_field(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "compliant-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "spec.md"), "w") as f:
            f.write("# Spec\nStores PII.\n")
        with open(os.path.join(feat, "compliance.md"), "w") as f:
            f.write("# Compliance\nReviewed.\n")
        rc, data, _ = run_script("pipeline-status.py", cwd=self.tmp)
        feature = data["features"][0]
        self.assertTrue(feature["complianceCompleted"])
        self.assertTrue(feature["complianceNeeded"])

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

    def test_assembles_builder_prompt(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["builder", "test-feature", "--task-id", "1.1"],
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


class TestAssemblePromptRedefiner(unittest.TestCase):
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
                "redefinitionPass": 0,
                "tasks": [
                    {"id": "1.1", "phase": 1, "title": "First task", "do": "Build it",
                     "verify": "It works", "status": "done", "iteration": 1},
                    {"id": "1.2", "phase": 1, "title": "Second task", "do": "Wire it up",
                     "verify": "Wiring works", "status": "blocked", "iteration": None},
                ],
            }, f)
        # Create mock logs
        log_dir = os.path.join(self.tmp, "logs", "ralph-test-feature")
        os.makedirs(log_dir)
        with open(os.path.join(log_dir, "judge.log"), "w") as f:
            f.write("VERDICT: PARTIAL\n\nCRITERIA:\n- 1.1: PASS — works\n- 1.2: FAIL — wiring broken\n\n"
                    "RECOMMENDATIONS:\n- Fix the wiring in component X\n")
        with open(os.path.join(log_dir, "task-1.2-check.log"), "w") as f:
            f.write("FAIL: Expected component to render but got null\n")
        with open(os.path.join(log_dir, "task-1.2-impl.log"), "w") as f:
            f.write("Created component file...\n" * 100)  # >80 lines
        with open(os.path.join(log_dir, "task-1.2-retry.log"), "w") as f:
            f.write("Attempted fix...\nStill broken.\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_assembles_redefiner_prompt(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature", "--redef-pass", "1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("prompt", data)
        prompt = data["prompt"]
        # Judge verdict included
        self.assertIn("VERDICT: PARTIAL", prompt)
        # Blocked task diagnostics included
        self.assertIn("Second task", prompt)
        self.assertIn("Expected component to render but got null", prompt)
        # tasks.json raw included
        self.assertIn('"feature": "test-feature"', prompt)
        # Spec included
        self.assertIn("Do the thing", prompt)
        # Guidelines included
        self.assertIn("Use Jest", prompt)
        # Pass number included
        self.assertIn("1 of 3", prompt)

    def test_redefiner_no_unresolved_variables(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature", "--redef-pass", "2"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertNotIn("UNRESOLVED", data["prompt"])

    def test_redefiner_truncates_long_impl_log(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature", "--redef-pass", "1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        # Impl log had 100 lines, should be truncated to 80
        impl_section = data["prompt"]
        # Count occurrences of the repeated line — should be 80 not 100
        self.assertEqual(impl_section.count("Created component file..."), 80)

    def test_redefiner_includes_retry_log(self):
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature", "--redef-pass", "1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("Attempted fix...", data["prompt"])
        self.assertIn("Still broken.", data["prompt"])

    def test_redefiner_no_blocked_tasks(self):
        """When no tasks are blocked, diagnostics say so."""
        specs = os.path.join(self.tmp, ".specs", "test-feature")
        with open(os.path.join(specs, "tasks.json"), "w") as f:
            json.dump({
                "feature": "test-feature",
                "check": "npm test",
                "tasks": [
                    {"id": "1.1", "phase": 1, "title": "First task", "do": "Build it",
                     "verify": "It works", "status": "done", "iteration": 1},
                ],
            }, f)
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature", "--redef-pass", "1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("No blocked tasks", data["prompt"])

    def test_redefiner_missing_logs_handled(self):
        """When log files don't exist, diagnostics handle gracefully."""
        # Remove the log files
        log_dir = os.path.join(self.tmp, "logs", "ralph-test-feature")
        os.remove(os.path.join(log_dir, "task-1.2-check.log"))
        os.remove(os.path.join(log_dir, "task-1.2-impl.log"))
        os.remove(os.path.join(log_dir, "task-1.2-retry.log"))
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature", "--redef-pass", "1"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("No check log found", data["prompt"])

    def test_redefiner_default_redef_pass(self):
        """--redef-pass defaults to 0."""
        rc, data, _ = run_script(
            "assemble-prompt.py",
            ["redefiner", "test-feature"],
            cwd=self.tmp,
        )
        self.assertEqual(rc, 0)
        self.assertIn("0 of 3", data["prompt"])


class TestValidateDoc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def _write(self, filename, content):
        path = os.path.join(self.tmp, filename)
        with open(path, "w") as f:
            f.write(content)
        return path

    # --- General ---

    def test_no_args(self):
        rc, _, _ = run_script("validate-doc.py", cwd=self.tmp)
        self.assertEqual(rc, 2)

    def test_file_not_found(self):
        rc, data, _ = run_script("validate-doc.py", ["/nonexistent/pitch.md"])
        self.assertEqual(rc, 0)
        self.assertFalse(data["valid"])
        self.assertIn("File not found", data["errors"][0])

    def test_unrecognized_filename(self):
        path = self._write("readme.md", "# Hello")
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])
        self.assertIsNone(data["type"])
        self.assertEqual(data["errors"], [])

    # --- Pitch ---

    def test_empty_pitch(self):
        path = self._write("pitch.md", "# Empty pitch\n")
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertEqual(rc, 0)
        self.assertFalse(data["valid"])
        self.assertEqual(data["type"], "pitch")
        # All 4 required sections missing
        missing = [e for e in data["errors"] if "Missing required" in e]
        self.assertEqual(len(missing), 4)

    def test_complete_pitch(self):
        content = (
            "# Pitch: Test\n\n"
            "## Problem\n\nUsers have no way to do the thing they need to do right now.\n\n"
            "## Appetite\n\n2-week effort for one developer, keep it simple.\n\n"
            "## Shape\n\nBuild a simple system that does the thing with REST endpoints.\n\n"
            "## No-Gos\n\n- No gamification mechanics\n- No external integrations\n\n"
            "## Rabbit Holes\n\n- Building a notification system. Resist the urge.\n"
        )
        path = self._write("pitch.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertEqual(rc, 0)
        self.assertTrue(data["valid"])
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["warnings"], [])

    def test_pitch_thin_section(self):
        content = (
            "## Problem\n\nShort.\n\n"
            "## Appetite\n\n2-week effort for one developer, keep it simple.\n\n"
            "## Shape\n\nBuild a simple system that does the thing with REST endpoints.\n\n"
            "## No-Gos\n\n- No gamification mechanics\n- No external integrations\n\n"
            "## Rabbit Holes\n\n- Building a notification system.\n"
        )
        path = self._write("pitch.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertTrue(any("too short" in e and "Problem" in e for e in data["errors"]))

    def test_pitch_missing_rabbit_holes(self):
        content = (
            "## Problem\n\nUsers have no way to do the thing they need.\n\n"
            "## Appetite\n\n2-week effort for one developer, keep it simple.\n\n"
            "## Shape\n\nBuild a simple system that does the thing with REST.\n\n"
            "## No-Gos\n\n- No gamification mechanics\n- No external integrations\n"
        )
        path = self._write("pitch.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertTrue(data["valid"])
        self.assertTrue(any("Rabbit Holes" in w for w in data["warnings"]))

    def test_pitch_out_of_order(self):
        content = (
            "## Shape\n\nBuild a simple system that does the thing with REST.\n\n"
            "## Problem\n\nUsers have no way to do the thing they need.\n\n"
            "## Appetite\n\n2-week effort for one developer, keep it simple.\n\n"
            "## No-Gos\n\n- No gamification mechanics\n- No external integrations\n"
        )
        path = self._write("pitch.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertTrue(any("out of order" in w for w in data["warnings"]))

    def test_pitch_no_gos_variants(self):
        for variant in ["No Gos", "NoGos", "No-Gos"]:
            content = (
                f"## Problem\n\nUsers have no way to do the thing they need.\n\n"
                f"## Appetite\n\n2-week effort for one developer.\n\n"
                f"## Shape\n\nBuild a simple system with REST endpoints.\n\n"
                f"## {variant}\n\n- No gamification mechanics\n- No external integrations\n"
            )
            path = self._write("pitch.md", content)
            rc, data, _ = run_script("validate-doc.py", [path])
            self.assertTrue(data["valid"], f"Failed for variant: {variant}")

    # --- Spec ---

    def test_empty_spec(self):
        path = self._write("spec.md", "# Empty spec\n")
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertEqual(data["type"], "spec")
        missing = [e for e in data["errors"] if "Missing required" in e]
        self.assertEqual(len(missing), 4)  # §1, §2, §8, §9

    def test_complete_spec(self):
        content = (
            "# Spec: Test\n\n"
            "## §1 — Context\n\nSee pitch.md. This spec defines a system for managing things.\n\n"
            "## §2 — Functional Overview\n\nThe system allows users to create and manage resources.\n\n"
            "## §3 — Actors and Permissions\n\nAll authenticated users can perform all actions.\n\n"
            "## §4 — Data Model\n\nSingle entity with id, name, and created_at fields.\n\n"
            "## §5 — Interfaces\n\nREST API with CRUD endpoints for managing resources.\n\n"
            "## §6 — Business Rules\n\nNames must be unique within the same organization context.\n\n"
            "## §7 — Failure Modes\n\nDatabase unreachable returns 503 with clear error message.\n\n"
            "## §8 — Success Criteria\n\nAll CRUD operations work correctly with proper validation.\n\n"
            "## §9 — Constraints\n\nNo external service dependencies beyond the database layer.\n\n"
            "## §10 — Open Questions\n\nN/A — all questions resolved during spec writing phase.\n"
        )
        path = self._write("spec.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertTrue(data["valid"])
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["warnings"], [])

    def test_spec_out_of_order(self):
        content = (
            "## §2 — Functional Overview\n\nThe system allows users to manage resources.\n\n"
            "## §1 — Context\n\nSee pitch.md. This spec defines something important.\n\n"
            "## §8 — Success Criteria\n\nAll operations work correctly with validation.\n\n"
            "## §9 — Constraints\n\nNo external service dependencies beyond database.\n"
        )
        path = self._write("spec.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertTrue(any("out of order" in e for e in data["errors"]))

    def test_spec_missing_optional_warns(self):
        content = (
            "## §1 — Context\n\nSee pitch.md. This spec defines a system for things.\n\n"
            "## §2 — Functional Overview\n\nThe system allows users to manage resources.\n\n"
            "## §8 — Success Criteria\n\nAll operations work correctly with validation.\n\n"
            "## §9 — Constraints\n\nNo external service dependencies beyond database.\n"
        )
        path = self._write("spec.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertTrue(data["valid"])
        # Should warn about missing §3-§7 and §10
        optional_warnings = [w for w in data["warnings"] if "Missing optional" in w]
        self.assertEqual(len(optional_warnings), 6)

    def test_spec_malformed_heading(self):
        content = (
            "## §1 Context\n\nMissing the em-dash separator in heading format.\n\n"
            "## §2 — Functional Overview\n\nThe system allows users to manage things.\n\n"
            "## §8 — Success Criteria\n\nAll operations work correctly with validation.\n\n"
            "## §9 — Constraints\n\nNo external deps beyond the database layer.\n"
        )
        path = self._write("spec.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertTrue(any("Malformed" in e for e in data["errors"]))

    def test_spec_duplicate_section(self):
        content = (
            "## §1 — Context\n\nFirst context section with enough content here.\n\n"
            "## §1 — Context\n\nDuplicate context section with enough content.\n\n"
            "## §2 — Functional Overview\n\nThe system allows users to manage resources.\n\n"
            "## §8 — Success Criteria\n\nAll operations work correctly with validation.\n\n"
            "## §9 — Constraints\n\nNo external service dependencies beyond database.\n"
        )
        path = self._write("spec.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertTrue(any("Duplicate" in e for e in data["errors"]))

    def test_spec_na_optional_section(self):
        content = (
            "## §1 — Context\n\nSee pitch.md. This spec defines a system for things.\n\n"
            "## §2 — Functional Overview\n\nThe system allows users to manage resources.\n\n"
            "## §10 — Open Questions\n\nN/A — all resolved.\n\n"
            "## §8 — Success Criteria\n\nAll operations work correctly with validation.\n\n"
            "## §9 — Constraints\n\nNo external service dependencies beyond database.\n"
        )
        path = self._write("spec.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        # §10 has N/A body — should NOT trigger "too short" warning
        thin_warnings = [w for w in data["warnings"] if "too short" in w and "§10" in w]
        self.assertEqual(len(thin_warnings), 0)

    # --- Plan ---

    def test_empty_plan(self):
        path = self._write("plan.md", "# Empty plan\n")
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertEqual(data["type"], "plan")
        missing = [e for e in data["errors"] if "Missing required" in e]
        self.assertEqual(len(missing), 4)  # §1, §2, §3, §6

    def test_complete_plan(self):
        content = (
            "# Plan: Test\n\n"
            "## §1 — Technical Summary\n\nA FastAPI service with REST endpoints backed by PostgreSQL.\n\n"
            "## §2 — Architecture\n\nSingle module with routes, services, models layers.\n\n"
            "## §3 — Technology Decisions\n\n| Decision | Choice | Rationale |\n|----------|--------|-----------|\n| Framework | FastAPI | Project standard |\n\n"
            "## §4 — Data Access Patterns\n\nStandard SQLAlchemy async queries with connection pooling.\n\n"
            "## §5 — Interface Implementation\n\nRoutes map to service functions, Pydantic for validation.\n\n"
            "## §6 — File Structure\n\napp/routes/, app/services/, app/models/, app/schemas/.\n\n"
            "## §7 — Error Handling Strategy\n\nResult types for business logic, HTTP exceptions at route boundary.\n\n"
            "## §8 — Testing Strategy\n\npytest with async fixtures, test database per session.\n\n"
            "## §9 — Deployment and Infrastructure\n\nDocker container with health check on /health endpoint.\n\n"
            "## §10 — Migration Path\n\nN/A — greenfield project with no migration concerns.\n"
        )
        path = self._write("plan.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertTrue(data["valid"])
        self.assertEqual(data["errors"], [])
        self.assertEqual(data["warnings"], [])

    def test_plan_no_table_in_s3(self):
        content = (
            "## §1 — Technical Summary\n\nA FastAPI service with REST endpoints backed by PostgreSQL.\n\n"
            "## §2 — Architecture\n\nSingle module with routes, services, models layers.\n\n"
            "## §3 — Technology Decisions\n\nWe will use FastAPI and PostgreSQL for this project.\n\n"
            "## §6 — File Structure\n\napp/routes/, app/services/, app/models/, app/schemas/.\n"
        )
        path = self._write("plan.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertTrue(data["valid"])
        self.assertTrue(any("table" in w and "§3" in w for w in data["warnings"]))

    def test_plan_out_of_order(self):
        content = (
            "## §3 — Technology Decisions\n\n| Decision | Choice | Rationale |\n|--|--|--|\n| FW | FastAPI | std |\n\n"
            "## §1 — Technical Summary\n\nA FastAPI service with REST endpoints backed by PostgreSQL.\n\n"
            "## §2 — Architecture\n\nSingle module with routes, services, models layers.\n\n"
            "## §6 — File Structure\n\napp/routes/, app/services/, app/models/, app/schemas/.\n"
        )
        path = self._write("plan.md", content)
        rc, data, _ = run_script("validate-doc.py", [path])
        self.assertFalse(data["valid"])
        self.assertTrue(any("out of order" in e for e in data["errors"]))


if __name__ == "__main__":
    unittest.main()
