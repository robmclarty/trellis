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

    def test_multiline_verify_block(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n\n")
            f.write("- [ ] 1.1 -- Set up project\n")
            f.write("  **Verify:** First line of verify\n")
            f.write("  continuation of verify block\n")
            f.write("  another continuation line\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks])
        self.assertEqual(len(data["taskCriteria"]), 1)
        self.assertIn("First line", data["taskCriteria"][0]["summary"])
        self.assertIn("continuation", data["taskCriteria"][0]["summary"])

    def test_em_dash_separator(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n\n")
            f.write("- [ ] 1.1 \u2014 Set up with em dash\n")
            f.write("  **Verify:** It works\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks])
        self.assertEqual(len(data["taskCriteria"]), 1)
        self.assertEqual(data["taskCriteria"][0]["taskId"], "1.1")

    def test_checked_task_still_extracted(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n\n")
            f.write("- [x] 1.1 -- Already done\n")
            f.write("  **Verify:** Should still appear\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks])
        self.assertEqual(len(data["taskCriteria"]), 1)
        self.assertEqual(data["taskCriteria"][0]["status"], "pending")

    def test_empty_tasks_file(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n\nNo tasks here.\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks])
        self.assertEqual(rc, 0)
        self.assertEqual(data["taskCriteria"], [])
        self.assertEqual(data["totalCount"], 0)

    def test_spec_section8_stops_at_next_section(self):
        tasks = os.path.join(self.tmp, "tasks.md")
        with open(tasks, "w") as f:
            f.write("## Phase 1\n")
        spec = os.path.join(self.tmp, "spec.md")
        with open(spec, "w") as f:
            f.write("## \u00a78 Success Criteria\n\n")
            f.write("- [ ] Criterion in section 8\n")
            f.write("\n## \u00a79 Constraints\n\n")
            f.write("- [ ] This should NOT be extracted\n")
        rc, data, _ = run_script("extract-criteria.py", [tasks, spec])
        self.assertEqual(len(data["specCriteria"]), 1)
        self.assertIn("section 8", data["specCriteria"][0]["summary"])


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

    def test_empty_file(self):
        state = os.path.join(self.tmp, "empty-state.md")
        with open(state, "w") as f:
            f.write("")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(data["pendingCount"], 0)
        self.assertEqual(data["doneCount"], 0)
        self.assertEqual(data["criteria"], [])
        self.assertEqual(data["pipeline"], [])
        self.assertEqual(data["config"], {})
        self.assertIsNone(data["nextPendingId"])

    def test_missing_sections(self):
        state = os.path.join(self.tmp, "partial-state.md")
        with open(state, "w") as f:
            f.write("""## Acceptance Criteria
- [ ] AC-1 (task 1.1): Only criteria here (pending)
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(data["pendingCount"], 1)
        self.assertEqual(data["branch"], {})
        self.assertEqual(data["input"], {})
        self.assertEqual(data["pipeline"], [])
        self.assertEqual(data["iteration"], 0)

    def test_config_boolean_parsing(self):
        state = os.path.join(self.tmp, "config-state.md")
        with open(state, "w") as f:
            f.write("""## Config
- Type-check: off
- Lint: on
- Test: false
- Build: true
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertFalse(data["config"]["type-check"])
        self.assertTrue(data["config"]["lint"])
        self.assertFalse(data["config"]["test"])
        self.assertTrue(data["config"]["build"])

    def test_config_backtick_stripping(self):
        state = os.path.join(self.tmp, "backtick-state.md")
        with open(state, "w") as f:
            f.write("""## Config
- Lint: `npm run lint`
- Build: `npm run build`
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(data["config"]["lint"], "npm run lint")
        self.assertEqual(data["config"]["build"], "npm run build")

    def test_pipeline_mixed_status(self):
        state = os.path.join(self.tmp, "pipeline-state.md")
        with open(state, "w") as f:
            f.write("""## Oracle Pipeline
- [x] build: `npm run build`
- [ ] test: `npm test`
- [x] lint: `npm run lint`
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(len(data["pipeline"]), 3)
        self.assertEqual(data["pipeline"][0]["status"], "enabled")
        self.assertEqual(data["pipeline"][0]["command"], "npm run build")
        self.assertEqual(data["pipeline"][1]["status"], "pending")
        self.assertEqual(data["pipeline"][2]["status"], "enabled")

    def test_criteria_with_task_ref(self):
        state = os.path.join(self.tmp, "taskref-state.md")
        with open(state, "w") as f:
            f.write("""## Acceptance Criteria
- [ ] AC-1 (task 1.1): Some criterion (pending)
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(data["criteria"][0]["taskRef"], "task 1.1")

    def test_criteria_without_task_ref(self):
        state = os.path.join(self.tmp, "notaskref-state.md")
        with open(state, "w") as f:
            f.write("""## Acceptance Criteria
- [ ] AC-1: Some criterion without task ref (pending)
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertIsNone(data["criteria"][0]["taskRef"])

    def test_iteration_count_zero(self):
        state = os.path.join(self.tmp, "no-iter-state.md")
        with open(state, "w") as f:
            f.write("""## Iteration Log
No iterations yet.
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(data["iteration"], 0)

    def test_iteration_count_many(self):
        state = os.path.join(self.tmp, "many-iter-state.md")
        with open(state, "w") as f:
            f.write("## Iteration Log\n")
            for i in range(1, 6):
                f.write(f"### Iteration {i}\nDid stuff.\n")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(data["iteration"], 5)

    def test_malformed_criteria_line_skipped(self):
        state = os.path.join(self.tmp, "malformed-state.md")
        with open(state, "w") as f:
            f.write("""## Acceptance Criteria
- [x] AC-1 (task 1.1): Valid criterion (done, iteration 1)
- This is not a valid criteria line
- Also not valid
- [ ] AC-2 (task 1.2): Second valid (pending)
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(len(data["criteria"]), 2)
        self.assertEqual(data["criteria"][0]["id"], "AC-1")
        self.assertEqual(data["criteria"][1]["id"], "AC-2")

    def test_input_section_na_value(self):
        state = os.path.join(self.tmp, "na-state.md")
        with open(state, "w") as f:
            f.write("""## Input
- Feature: my-feature
- Freeform: N/A
""")
        rc, data, _ = run_script("parse-implement-state.py", [state])
        self.assertEqual(rc, 0)
        self.assertEqual(data["input"]["feature"], "my-feature")
        self.assertIsNone(data["input"]["freeform"])


if __name__ == "__main__":
    unittest.main()
