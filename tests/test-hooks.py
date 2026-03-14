#!/usr/bin/env python3
"""Tests for Trellis hook scripts in hooks/.

Run from project root: python3 tests/test-hooks.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "hooks")


def run_hook(name, stdin_data, cwd=None):
    """Run a hook script with JSON on stdin. Returns (returncode, stdout)."""
    cmd = [sys.executable, os.path.join(HOOKS, name)]
    result = subprocess.run(
        cmd,
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.returncode, result.stdout.strip()


class TestValidateStructure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_ignores_non_spec_files(self):
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": "/some/other/path/file.md"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_ignores_non_markdown(self):
        os.makedirs(os.path.join(self.tmp, ".specs"))
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": os.path.join(self.tmp, ".specs/config.json")}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_warns_missing_spec_sections(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("# Incomplete spec\n")
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("§1", out)
        self.assertIn("§8", out)

    def test_no_warnings_complete_spec(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("§1 Context\n§2 Overview\n§8 Criteria\n§9 Constraints\n")
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_warns_missing_pitch_sections(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        pitch_file = os.path.join(specs, "pitch.md")
        with open(pitch_file, "w") as f:
            f.write("# Empty pitch\n")
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": pitch_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("Problem", out)
        self.assertIn("No-Gos", out)

    def test_warns_missing_plan_sections(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        plan_file = os.path.join(specs, "plan.md")
        with open(plan_file, "w") as f:
            f.write("# Empty plan\n")
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": plan_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("§3", out)

    def test_warns_missing_tasks_phase(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        tasks_file = os.path.join(specs, "tasks.md")
        with open(tasks_file, "w") as f:
            f.write("# Tasks with no phases\n")
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": tasks_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("Phase", out)

    def test_custom_specs_dir(self):
        with open(os.path.join(self.tmp, "trellis.json"), "w") as f:
            json.dump({"specsDir": "design"}, f)
        specs = os.path.join(self.tmp, "design", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("# Incomplete\n")
        rc, out = run_hook("validate-structure.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("§1", out)


class TestCheckImplement(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_ignores_non_commit_commands(self):
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git status"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_silent_when_no_state_file(self):
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git commit -m test"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_warns_on_pending_criteria(self):
        state_dir = os.path.join(self.tmp, ".specs", ".state")
        os.makedirs(state_dir, exist_ok=True)
        state = os.path.join(state_dir, "implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            f.write("- [x] AC-1 (task 1.1): Done (done, iteration 1)\n")
            f.write("- [ ] AC-2 (task 1.2): Pending (pending)\n")
            f.write("- [ ] AC-3 (task 2.1): Also pending (pending)\n")
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git commit -m test"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("2 pending", out)

    def test_silent_when_all_done(self):
        state_dir = os.path.join(self.tmp, ".specs", ".state")
        os.makedirs(state_dir, exist_ok=True)
        state = os.path.join(state_dir, "implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            f.write("- [x] AC-1 (task 1.1): Done (done, iteration 1)\n")
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git commit -m test"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_ignores_git_add(self):
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git add ."}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_truncation_with_many_pending(self):
        state_dir = os.path.join(self.tmp, ".specs", ".state")
        os.makedirs(state_dir, exist_ok=True)
        state = os.path.join(state_dir, "implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            for i in range(1, 8):
                f.write(f"- [ ] AC-{i} (task 1.{i}): Criterion {i} (pending)\n")
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git commit -m test"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("7 pending", out)
        self.assertIn("and 2 more", out)

    def test_custom_specs_dir(self):
        with open(os.path.join(self.tmp, "trellis.json"), "w") as f:
            json.dump({"specsDir": "design"}, f)
        state_dir = os.path.join(self.tmp, "design", ".state")
        os.makedirs(state_dir, exist_ok=True)
        state = os.path.join(state_dir, "implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            f.write("- [ ] AC-1 (task 1.1): Pending (pending)\n")
        rc, out = run_hook("check-implement.py", {
            "tool_input": {"command": "git commit -m test"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("1 pending", out)


class TestCountMarkers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_ignores_non_spec_files(self):
        rc, out = run_hook("count-markers.py", {
            "tool_input": {"file_path": "/some/other/file.md"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_ignores_non_spec_md(self):
        rc, out = run_hook("count-markers.py", {
            "tool_input": {"file_path": os.path.join(self.tmp, ".specs/my-feature/pitch.md")}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_reports_clean_spec(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("# Clean spec\nNo markers.\n")
        rc, out = run_hook("count-markers.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("no unresolved", out)

    def test_reports_marker_count(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("[? PRIVACY: who?]\n[? DATA_OWNERSHIP: where?]\n")
        rc, out = run_hook("count-markers.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("2 unresolved", out)

    def test_category_breakdown_in_output(self):
        specs = os.path.join(self.tmp, ".specs", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("[? PRIVACY: one]\n[? PRIVACY: two]\n[? EDGE_CASE: three]\n")
        rc, out = run_hook("count-markers.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("PRIVACY: 2", out)
        self.assertIn("EDGE_CASE: 1", out)

    def test_custom_specs_dir(self):
        with open(os.path.join(self.tmp, "trellis.json"), "w") as f:
            json.dump({"specsDir": "design"}, f)
        specs = os.path.join(self.tmp, "design", "my-feature")
        os.makedirs(specs)
        spec_file = os.path.join(specs, "spec.md")
        with open(spec_file, "w") as f:
            f.write("[? PRIVACY: test marker]\n")
        rc, out = run_hook("count-markers.py", {
            "tool_input": {"file_path": spec_file}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("1 unresolved", out)


class TestSyncImplement(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_ignores_non_state_files(self):
        rc, out = run_hook("sync-implement.py", {
            "tool_input": {"file_path": "/some/other/file.md"}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_reports_progress(self):
        state = os.path.join(self.tmp, ".implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            f.write("- [x] AC-1 (task 1.1): Done (done, iteration 1)\n")
            f.write("- [ ] AC-2 (task 1.2): Pending (pending)\n")
        rc, out = run_hook("sync-implement.py", {
            "tool_input": {"file_path": state}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("1/2 criteria done", out)
        self.assertIn("AC-2", out)

    def test_all_criteria_done(self):
        state = os.path.join(self.tmp, ".implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            f.write("- [x] AC-1 (task 1.1): Done (done, iteration 1)\n")
            f.write("- [x] AC-2 (task 1.2): Also done (done, iteration 2)\n")
        rc, out = run_hook("sync-implement.py", {
            "tool_input": {"file_path": state}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertIn("2/2 criteria done", out)

    def test_empty_state_file_silent(self):
        state = os.path.join(self.tmp, ".implement-state.md")
        with open(state, "w") as f:
            f.write("")
        rc, out = run_hook("sync-implement.py", {
            "tool_input": {"file_path": state}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_non_implement_file_ignored(self):
        rc, out = run_hook("sync-implement.py", {
            "tool_input": {"file_path": os.path.join(self.tmp, ".specs/my-feature/spec.md")}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_production_path_not_matched(self):
        # The hook checks endswith(".implement-state.md") but the production
        # path .specs/.state/implement-state.md ends with "/implement-state.md",
        # not ".implement-state.md". This documents current behavior — the hook
        # only triggers for files literally named .implement-state.md.
        state_dir = os.path.join(self.tmp, ".specs", ".state")
        os.makedirs(state_dir, exist_ok=True)
        state = os.path.join(state_dir, "implement-state.md")
        with open(state, "w") as f:
            f.write("## Acceptance Criteria\n")
            f.write("- [x] AC-1 (task 1.1): Done (done, iteration 1)\n")
            f.write("- [ ] AC-2 (task 1.2): Pending (pending)\n")
        rc, out = run_hook("sync-implement.py", {
            "tool_input": {"file_path": state}
        }, cwd=self.tmp)
        self.assertEqual(rc, 0)
        # Path ends with "/implement-state.md", not ".implement-state.md"
        # so the hook silently exits — this may be a bug
        self.assertEqual(out, "")


class TestSessionStart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp)

    def test_silent_when_no_specs(self):
        cmd = [sys.executable, os.path.join(HOOKS, "session-start.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_shows_status(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "my-feature")
        os.makedirs(feat)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        cmd = [sys.executable, os.path.join(HOOKS, "session-start.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("pipeline status", result.stdout)
        self.assertIn("guidelines.md", result.stdout)
        self.assertIn("my-feature", result.stdout)

    def test_feature_all_stages_shows_ready(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "complete-feature")
        os.makedirs(feat)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        for artifact in ["pitch.md", "spec.md", "plan.md", "tasks.md"]:
            with open(os.path.join(feat, artifact), "w") as f:
                f.write(f"# {artifact}")
        cmd = [sys.executable, os.path.join(HOOKS, "session-start.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ready for /trellis:implement", result.stdout)

    def test_multiple_features(self):
        specs = os.path.join(self.tmp, ".specs")
        os.makedirs(specs, exist_ok=True)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        for name in ["alpha", "beta"]:
            feat = os.path.join(specs, name)
            os.makedirs(feat, exist_ok=True)
            with open(os.path.join(feat, "pitch.md"), "w") as f:
                f.write("# Pitch")
        cmd = [sys.executable, os.path.join(HOOKS, "session-start.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("alpha", result.stdout)
        self.assertIn("beta", result.stdout)

    def test_sketches_displayed(self):
        specs = os.path.join(self.tmp, ".specs")
        sketches = os.path.join(specs, "sketches")
        os.makedirs(sketches)
        with open(os.path.join(specs, "guidelines.md"), "w") as f:
            f.write("# Guidelines")
        for i in range(3):
            with open(os.path.join(sketches, f"sketch-{i}.md"), "w") as f:
                f.write(f"# Sketch {i}")
        cmd = [sys.executable, os.path.join(HOOKS, "session-start.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("3 sketch(es)", result.stdout)

    def test_guidelines_missing_shows_message(self):
        specs = os.path.join(self.tmp, ".specs")
        feat = os.path.join(specs, "my-feature")
        os.makedirs(feat)
        with open(os.path.join(feat, "pitch.md"), "w") as f:
            f.write("# Pitch")
        cmd = [sys.executable, os.path.join(HOOKS, "session-start.py")]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("/trellis:guidelines", result.stdout)


if __name__ == "__main__":
    unittest.main()
