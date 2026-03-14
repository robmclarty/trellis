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

import os
import shutil
import subprocess
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
