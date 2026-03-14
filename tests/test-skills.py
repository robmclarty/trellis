#!/usr/bin/env python3
"""Skill output validation tests using claude -p (pipe mode).

These tests mirror the promptfoo test cases in tests/promptfoo.yaml but use
claude -p with subscription auth instead of the Anthropic API directly.

Gated behind:
  1. claude binary on PATH
  2. TRELLIS_LLM_TESTS=1 environment variable

Run:  TRELLIS_LLM_TESTS=1 python3 tests/test-skills.py
      npm run test:skills
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")

CLAUDE_AVAILABLE = shutil.which("claude") is not None
LLM_TESTS_ENABLED = os.environ.get("TRELLIS_LLM_TESTS") == "1"

if not CLAUDE_AVAILABLE:
    SKIP_REASON = "claude not found on PATH"
elif not LLM_TESTS_ENABLED:
    SKIP_REASON = "set TRELLIS_LLM_TESTS=1 to enable"
else:
    SKIP_REASON = None

TIMEOUT = 120
MAX_BUDGET = "0.05"
MODEL = "sonnet"


def run_skill(skill_name, user_input):
    """Pipe SKILL.md + user_input to claude -p, return output text."""
    skill_path = os.path.join(SKILLS, skill_name, "SKILL.md")
    with open(skill_path) as f:
        prompt = f.read() + "\n\n---\n\n" + user_input

    result = subprocess.run(
        [
            "claude", "-p",
            "--model", MODEL,
            "--no-session-persistence",
            "--max-budget-usd", MAX_BUDGET,
        ],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        cwd=ROOT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (rc={result.returncode}):\n"
            f"stderr: {result.stderr[:500]}"
        )

    return result.stdout


def assert_icontains(test_case, output, value):
    """Case-insensitive contains (matches promptfoo 'icontains')."""
    test_case.assertIn(
        value.lower(), output.lower(),
        f"Expected output to contain (case-insensitive): {value!r}"
    )


def assert_not_icontains(test_case, output, value):
    """Case-insensitive NOT contains."""
    test_case.assertNotIn(
        value.lower(), output.lower(),
        f"Expected output to NOT contain (case-insensitive): {value!r}"
    )


def extract_section(output, heading):
    """Extract text between a ## heading and the next ## heading."""
    pattern = rf"(?:^|\n)##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def assert_any_icontains(test_case, output, values):
    """Assert that output contains at least one of the given values (case-insensitive)."""
    lower = output.lower()
    found = any(v.lower() in lower for v in values)
    test_case.assertTrue(
        found,
        f"Expected output to contain at least one of: {values!r}"
    )


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestSkillOutput(unittest.TestCase):
    """Validates that each skill produces structurally correct output."""

    def test_guidelines_sections(self):
        output = run_skill("guidelines", """\
I want to set up guidelines for my project.

Here's the context:
- Stack: TypeScript, Node.js 22, Fastify, Drizzle ORM, Zod, PostgreSQL 16
- Architecture: layered (routes → services → models)
- Conventions: camelCase for code, kebab-case for files, ESM only
- Testing: vitest, real database via testcontainers, no mocks
- Infrastructure: Docker on Fly.io, GitHub Actions CI

The specs directory is ".specs/" (default).
Write the guidelines file content now. Do not ask questions.""")

        for section in [
            "## Stack", "## Architecture", "## Conventions",
            "## Patterns", "## Testing", "## Infrastructure",
        ]:
            assert_icontains(self, output, section)
        assert_icontains(self, output, "Fastify")
        assert_icontains(self, output, "Drizzle")

    def test_pitch_sections(self):
        output = run_skill("pitch", """\
Guidelines exist at .specs/guidelines.md.
Feature name: user-invitations

Problem: Admins currently add users manually via a SQL console. This is
error-prone and doesn't scale. We need a self-service invitation flow.

Appetite: 3 weeks, one developer.
No-gos: no SSO integration, no bulk import, no role assignment during invite.

Write the pitch now. Do not ask questions.""")

        for section in [
            "## Problem", "## Appetite", "## Shape",
            "## No-Gos", "## Rabbit Holes",
        ]:
            assert_icontains(self, output, section)
        assert_icontains(self, output, "invitation")

    def test_spec_sections(self):
        output = run_skill("spec", """\
Guidelines exist at .specs/guidelines.md (TypeScript/Fastify/Drizzle stack).
Pitch exists at .specs/user-invitations/pitch.md.

The pitch says:
- Problem: Admins add users via SQL. Need self-service invitations.
- Appetite: 3 weeks.
- Shape: Admin sends invite email with token. Recipient clicks link, creates account.
- No-gos: no SSO, no bulk import, no role assignment at invite time.

Write the spec now. Do not ask questions. Use numbered sections (§1-§10).""")

        for marker in ["§1", "§2", "§8", "§9"]:
            self.assertIn(marker, output, f"Expected output to contain: {marker!r}")
        assert_icontains(self, output, "Success Criteria")
        assert_icontains(self, output, "Constraints")

    def test_plan_sections(self):
        output = run_skill("plan", """\
Guidelines: TypeScript, Fastify, Drizzle ORM, Zod, PostgreSQL.
Spec exists with: invite creation endpoint, token validation endpoint,
account creation endpoint. Data model: invitations table with token,
email, status, expiry.

Write the plan now. Do not ask questions. Use numbered sections (§1-§10).""")

        for marker in ["§1", "§2", "§3", "§6"]:
            self.assertIn(marker, output, f"Expected output to contain: {marker!r}")
        assert_icontains(self, output, "File Structure")

    def test_tasks_sections(self):
        output = run_skill("tasks", """\
Plan exists with: Fastify routes, Drizzle schemas, Zod validation,
3 endpoints (create invite, validate token, create account).
File structure: src/routes/, src/services/, src/models/, src/schemas/.

Spec success criteria:
1. Admin can send invitation email
2. Recipient can create account via token
3. Expired tokens are rejected
4. Duplicate emails are rejected

Write the tasks now. Do not ask questions. Use Phase sections.""")

        assert_icontains(self, output, "## Phase 1")
        assert_icontains(self, output, "## Phase 2")
        assert_icontains(self, output, "**Do:**")
        assert_icontains(self, output, "**Verify:**")
        self.assertIn("- [ ]", output, "Expected output to contain: '- [ ]'")

    def test_sketch_sections(self):
        output = run_skill("sketch", """\
Guidelines exist. I want to sketch whether Resend can handle
transactional invite emails with link tracking at our scale
(~500 invites/month).

Slug: resend-invite-emails
Hypothesis: Resend's free tier handles 500 emails/month with
delivery tracking and we can integrate it in under a day.

Method: Read the docs, check rate limits, write a small test
script that sends 5 emails via the API.

Findings: Free tier allows 3000 emails/month. API is simple REST.
Delivery webhooks work. SDK is 50 lines to integrate.

Verdict: Viable.

Write the sketch document now. Do not ask questions.""")

        for section in [
            "## Hypothesis", "## Method", "## Findings", "## Verdict",
        ]:
            assert_icontains(self, output, section)
        assert_icontains(self, output, "Viable")

    def test_compliance_sections(self):
        output = run_skill("compliance", """\
Guidelines exist at .specs/guidelines.md.
Spec exists at .specs/user-invitations/spec.md.

The spec says:
- §4 Data Model: invitations table with columns: id, email (PII),
  token (secret), status, created_at, expires_at. Users table with
  name, email, password_hash.
- §9 Constraints: Deployed in Canada (ca-central-1). Serves users
  in the EU and Canada. Must comply with GDPR and FIPPA.

The guidelines say:
- Infrastructure: AWS ca-central-1, Docker on Fly.io
- No third-party analytics or tracking

Write the compliance review now. Do not ask questions.""")

        for section in [
            "Applicable Regulations", "Data Classification",
            "Requirement Mapping", "Data Flow Concerns",
            "Recommended Spec Changes", "Residual Risks",
        ]:
            assert_icontains(self, output, section)
        assert_icontains(self, output, "GDPR")
        assert_icontains(self, output, "FIPPA")
        assert_icontains(self, output, "email")

    def test_cross_skill_spec_refs_pitch(self):
        output = run_skill("spec", """\
Guidelines exist at .specs/guidelines.md.
Pitch exists at .specs/user-invitations/pitch.md.

The pitch says:
- Problem: Manual user onboarding via SQL console.
- No-gos: no SSO, no bulk import.

Write the spec. Ensure §1 references the pitch and §9 preserves
the no-gos. Do not ask questions.""")

        self.assertIn("§1", output, "Expected output to contain: '§1'")
        self.assertIn("§9", output, "Expected output to contain: '§9'")
        assert_icontains(self, output, "pitch")
        assert_icontains(self, output, "SSO")
        assert_icontains(self, output, "bulk")


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestAdversarialSkillOutput(unittest.TestCase):
    """Tests that probe LLM judgment quality with tricky inputs."""

    def test_pitch_reframes_solution_as_problem(self):
        output = run_skill("pitch", """\
Guidelines exist at .specs/guidelines.md.
Feature name: api-caching

Problem: We need to add a Redis cache layer in front of our API responses.

Appetite: 2 weeks, one developer.
No-gos: no cache invalidation UI, no multi-region cache sync.

Write the pitch now. Do not ask questions.""")

        assert_icontains(self, output, "## Problem")
        problem_section = extract_section(output, "Problem")
        assert_any_icontains(self, problem_section, [
            "slow", "latency", "response time", "performance",
            "wait", "delay", "timeout", "speed", "load",
        ])
        assert_not_icontains(self, problem_section, "redis")

    def test_spec_flags_contradictory_constraints(self):
        output = run_skill("spec", """\
Guidelines exist at .specs/guidelines.md (TypeScript/Fastify/Drizzle stack).
Pitch exists at .specs/user-invitations/pitch.md.

The pitch says:
- Problem: Admins add users via SQL. Need self-service invitations.
- Appetite: 3 weeks, one developer.
- Shape: Simple invite form, email with token link, account creation page.
- No-gos: no SSO, no bulk import.

Additional constraint from stakeholders:
Must support 10 million concurrent users from day one with zero downtime
and sub-10ms p99 latency globally.

Write the spec now. Do not ask questions. Use numbered sections (§1-§10).""")

        assert_any_icontains(self, output, [
            "tension", "conflict", "ambitious", "unrealistic",
            "trade-off", "contradiction", "risk", "infeasible",
            "scope", "challenge", "concern", "impractical",
        ])

    def test_compliance_minimal_for_no_pii(self):
        output = run_skill("compliance", """\
Guidelines exist at .specs/guidelines.md.
Spec exists at .specs/static-site-builder/spec.md.

The spec says:
- §4 Data Model: templates table (id, name, html_content) and builds
  table (id, timestamp, status). No user accounts. No authentication.
  No PII of any kind.
- §9 Constraints: Static site generator. No user-facing data. No cookies.
  No analytics. No tracking. Deployed on a private CI server.

The guidelines say:
- Infrastructure: Private CI server, no public cloud
- No user accounts or authentication

Write the compliance review now. Do not ask questions.""")

        assert_any_icontains(self, output, [
            "no regulations apply", "not applicable", "no personal data",
            "no PII", "none identified", "does not apply", "minimal",
            "low risk", "no compliance", "not required",
        ])

    def test_tasks_concretizes_vague_criteria(self):
        output = run_skill("tasks", """\
Plan exists with: Fastify routes, Drizzle schemas, Zod validation,
3 endpoints (create invite, validate token, create account).
File structure: src/routes/, src/services/, src/models/, src/schemas/.

Spec success criteria:
1. System should be fast
2. UI should be intuitive
3. Admin can send invitation email
4. Expired tokens are rejected

Write the tasks now. Do not ask questions. Use Phase sections.""")

        assert_icontains(self, output, "**Verify:**")
        # Extract all Verify blocks
        verify_blocks = re.findall(
            r"\*\*Verify:\*\*\s*\n(.*?)(?=\n\*\*Do:\*\*|\n##|\Z)",
            output, re.DOTALL | re.IGNORECASE,
        )
        all_verify_text = "\n".join(verify_blocks).lower()
        measurable = any(term in all_verify_text for term in [
            "ms", "millisecond", "second", "< ", "under ",
            "response time", "latency", "assert", "test",
            "benchmark", "measure", "curl", "run", "check",
        ])
        self.assertTrue(measurable,
            "Expected Verify blocks to contain measurable/testable language")
        self.assertNotIn("system should be fast", all_verify_text,
            "Vague criterion should not appear verbatim in Verify blocks")

    def test_sketch_rejects_bad_hypothesis(self):
        output = run_skill("sketch", """\
Guidelines exist. I want to sketch whether SQLite can handle our
write-heavy workload.

Slug: sqlite-concurrent-writes
Hypothesis: SQLite handles 10,000 concurrent write transactions per
second on a single node without contention.

Method: Benchmarked with 100 concurrent writers using WAL mode on a
4-core VM. Measured throughput and lock contention.

Findings: SQLite maxed out at ~50 writes/sec under concurrency due
to file-level locking. WAL mode helped reads but writes still
serialized. 10,000 writes/sec is impossible on a single node.

Verdict: Not viable.

Write the sketch document now. Do not ask questions.""")

        assert_icontains(self, output, "## Verdict")
        verdict_section = extract_section(output, "Verdict")
        assert_not_icontains(self, verdict_section, "viable")
        assert_any_icontains(self, verdict_section, [
            "not viable", "busted", "inconclusive", "disproven",
            "rejected", "fail", "infeasible", "impossible",
        ])


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestNegativeAssertions(unittest.TestCase):
    """Tests that skills do NOT produce inappropriate content."""

    def test_pitch_no_code_blocks(self):
        output = run_skill("pitch", """\
Guidelines exist at .specs/guidelines.md.
Feature name: user-invitations

Problem: Admins currently add users manually via a SQL console. This is
error-prone and doesn't scale. We need a self-service invitation flow.

Appetite: 3 weeks, one developer.
No-gos: no SSO integration, no bulk import, no role assignment during invite.

Write the pitch now. Do not ask questions.""")

        self.assertNotIn("```", output,
            "Pitch should not contain code blocks")

    def test_spec_constraints_no_functional_requirements(self):
        output = run_skill("spec", """\
Guidelines exist at .specs/guidelines.md (TypeScript/Fastify/Drizzle stack).
Pitch exists at .specs/user-invitations/pitch.md.

The pitch says:
- Problem: Admins add users via SQL. Need self-service invitations.
- Appetite: 3 weeks.
- Shape: Admin sends invite email with token. Recipient clicks link, creates account.
- No-gos: no SSO, no bulk import, no role assignment at invite time.

Write the spec now. Do not ask questions. Use numbered sections (§1-§10).""")

        constraints_section = extract_section(output, "Constraints")
        if constraints_section:
            for phrase in ["endpoint", "shall return", "must implement", "API route"]:
                assert_not_icontains(self, constraints_section, phrase)

    def test_plan_no_unlisted_technologies(self):
        output = run_skill("plan", """\
Guidelines: TypeScript, Fastify, Drizzle ORM, Zod, PostgreSQL.
Spec exists with: invite creation endpoint, token validation endpoint,
account creation endpoint. Data model: invitations table with token,
email, status, expiry.

Write the plan now. Do not ask questions. Use numbered sections (§1-§10).""")

        for tech in ["MongoDB", "MySQL", "DynamoDB", "SQLite"]:
            assert_not_icontains(self, output, tech)

    def test_compliance_no_gdpr_applies_for_no_pii(self):
        output = run_skill("compliance", """\
Guidelines exist at .specs/guidelines.md.
Spec exists at .specs/static-site-builder/spec.md.

The spec says:
- §4 Data Model: templates table (id, name, html_content) and builds
  table (id, timestamp, status). No user accounts. No authentication.
  No PII of any kind.
- §9 Constraints: Static site generator. No user-facing data. No cookies.
  No analytics. No tracking. Deployed on a private CI server.

The guidelines say:
- Infrastructure: Private CI server, no public cloud
- No user accounts or authentication

Write the compliance review now. Do not ask questions.""")

        for phrase in ["GDPR applies", "subject to GDPR", "must comply with GDPR"]:
            assert_not_icontains(self, output, phrase)

    def test_guidelines_no_feature_specific_content(self):
        output = run_skill("guidelines", """\
I want to set up guidelines for my project.

Here's the context:
- Stack: TypeScript, Node.js 22, Fastify, Drizzle ORM, Zod, PostgreSQL 16
- Architecture: layered (routes → services → models)
- Conventions: camelCase for code, kebab-case for files, ESM only
- Testing: vitest, real database via testcontainers, no mocks
- Infrastructure: Docker on Fly.io, GitHub Actions CI

The specs directory is ".specs/" (default).
Write the guidelines file content now. Do not ask questions.""")

        for term in ["invitation", "user registration", "onboarding"]:
            assert_not_icontains(self, output, term)


# ============================================================
# E2E Implement Smoke Test
# ============================================================

E2E_TESTS_ENABLED = os.environ.get("TRELLIS_E2E_TESTS") == "1"

if SKIP_REASON:
    E2E_SKIP_REASON = SKIP_REASON
elif not E2E_TESTS_ENABLED:
    E2E_SKIP_REASON = "set TRELLIS_E2E_TESTS=1 to enable"
else:
    E2E_SKIP_REASON = None


@unittest.skipIf(E2E_SKIP_REASON, E2E_SKIP_REASON or "")
class TestImplementE2E(unittest.TestCase):
    """End-to-end smoke test for the implement skill."""

    def test_implement_creates_code_and_updates_state(self):
        tmpdir = tempfile.mkdtemp(prefix="trellis-e2e-")
        try:
            self._setup_fixture(tmpdir)
            self._run_implement(tmpdir)
            self._assert_results(tmpdir)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _setup_fixture(self, tmpdir):
        """Create a minimal Node.js project with pre-filled state."""
        # package.json
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            json.dump({
                "name": "smoke",
                "version": "1.0.0",
                "scripts": {"test": "node test.js"},
            }, f)

        # trellis.json
        with open(os.path.join(tmpdir, "trellis.json"), "w") as f:
            json.dump({"specsDir": ".specs"}, f)

        # test.js
        with open(os.path.join(tmpdir, "test.js"), "w") as f:
            f.write("""\
const add = require('./src/add');
const assert = require('assert');
assert.strictEqual(add(2, 3), 5, 'add(2,3) should equal 5');
assert.strictEqual(add(0, 0), 0, 'add(0,0) should equal 0');
assert.strictEqual(add(-1, 1), 0, 'add(-1,1) should equal 0');
console.log('All tests passed');
""")

        # .specs directory structure
        specs_dir = os.path.join(tmpdir, ".specs", "smoke-test")
        state_dir = os.path.join(tmpdir, ".specs", ".state")
        os.makedirs(specs_dir)
        os.makedirs(state_dir)

        # guidelines.md
        with open(os.path.join(tmpdir, ".specs", "guidelines.md"), "w") as f:
            f.write("""\
# Project Guidelines

## Stack
- JavaScript (CommonJS)
- Node.js

## Architecture
- Single module in src/

## Conventions
- CommonJS modules (module.exports)
- No external dependencies

## Patterns
- Pure functions

## Testing
- node test.js (assert module)

## Infrastructure
- Local only
""")

        # spec.md
        with open(os.path.join(specs_dir, "spec.md"), "w") as f:
            f.write("""\
# Spec: smoke-test

## §1 Overview
A simple add function for smoke testing the implement skill.

## §8 Success Criteria
1. `add(2, 3)` returns `5`
2. `add(0, 0)` returns `0`

## §9 Constraints
- JavaScript only, no external dependencies
- CommonJS module format
""")

        # plan.md
        with open(os.path.join(specs_dir, "plan.md"), "w") as f:
            f.write("""\
# Plan: smoke-test

## §1 Overview
Create a single file `src/add.js` exporting an `add` function.

## §6 File Structure
```
src/
  add.js    # exports add(a, b) => a + b
```
""")

        # tasks.md
        with open(os.path.join(specs_dir, "tasks.md"), "w") as f:
            f.write("""\
# Tasks: smoke-test

## Phase 1: Foundation

### Task 1.1: Create add module

**Do:**
- Create `src/add.js` with `module.exports = function add(a, b) { return a + b; }`

**Verify:**
- `node -e "require('./src/add')"` runs without error

### Task 1.2: Verify tests pass

**Do:**
- Run `node test.js`

**Verify:**
- Exit code 0, output contains "All tests passed"

- [ ] Task 1.1
- [ ] Task 1.2
""")

        # implement-state.md (pre-filled to skip Phase 0/1)
        with open(os.path.join(state_dir, "implement-state.md"), "w") as f:
            f.write("""\
# Implementation State

## Input
- Type: feature-folder
- Feature: smoke-test
- Sketches: N/A
- Paths: .specs/smoke-test/spec.md, .specs/smoke-test/plan.md, .specs/smoke-test/tasks.md

## Branch
- Original: main
- Working: main

## Config
- Package manager: npm
- Type-check: none
- Lint: none
- Build: none
- Test: `node test.js`
- Ralph mode: off
- Promptfoo: off

## Oracle Pipeline
- [x] test: `node test.js`

## Acceptance Criteria
- [ ] AC-1 (task 1.1): add function exports correctly from src/add.js (pending)
- [ ] AC-2 (task 1.2): add function returns correct sum (pending)

## Constraints
- JavaScript only, no external dependencies

## Unknowns / Assumptions
- None

## Iteration Log
""")

    def _run_implement(self, tmpdir):
        """Run the implement skill via claude -p."""
        skill_path = os.path.join(SKILLS, "implement", "SKILL.md")
        with open(skill_path) as f:
            skill_instructions = f.read()

        prompt = skill_instructions + "\n\n---\n\n" + """\
Implement the smoke-test feature. The state file already exists at
.specs/.state/implement-state.md with config and oracle pipeline filled.
Skip Phase 0 and Phase 1 — go directly to Phase 2 (iterate).

The project is in the current directory. Create src/add.js so that
`node test.js` passes. Update the state file when done."""

        result = subprocess.run(
            [
                "claude", "-p",
                "--model", MODEL,
                "--no-session-persistence",
                "--max-budget-usd", "2.00",
                "--dangerously-skip-permissions",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=tmpdir,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"claude -p failed (rc={result.returncode}):\n"
                f"stderr: {result.stderr[:1000]}"
            )

    def _assert_results(self, tmpdir):
        """Verify implement created code and updated state."""
        # src/add.js exists and is non-empty
        add_path = os.path.join(tmpdir, "src", "add.js")
        self.assertTrue(os.path.isfile(add_path),
            "Expected src/add.js to be created")
        self.assertGreater(os.path.getsize(add_path), 0,
            "Expected src/add.js to be non-empty")

        # State file still exists
        state_path = os.path.join(
            tmpdir, ".specs", ".state", "implement-state.md")
        self.assertTrue(os.path.isfile(state_path),
            "Expected implement-state.md to still exist")

        with open(state_path) as f:
            state = f.read()
        self.assertIn("## Acceptance Criteria", state)
        self.assertIn("## Oracle Pipeline", state)

        # At least one AC marked done
        ac_done = re.findall(r"\[x\]\s*AC-", state, re.IGNORECASE)
        self.assertGreater(len(ac_done), 0,
            "Expected at least one acceptance criterion marked [x]")

        # Optional: verify tests actually pass
        test_result = subprocess.run(
            ["node", "test.js"],
            capture_output=True, text=True,
            timeout=30, cwd=tmpdir,
        )
        self.assertEqual(test_result.returncode, 0,
            f"node test.js failed:\n{test_result.stderr[:500]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
