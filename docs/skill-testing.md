# Skill Testing

Trellis includes a test harness for validating that skill prompts produce
structurally correct output.

## Background

Each Trellis skill (guidelines, pitch, spec, plan, prep, sketch) is defined
by a `SKILL.md` file containing structured instructions. When Claude processes
these instructions along with user input, it should produce output containing
specific sections, headings, and keywords. Skill tests validate these
structural properties without checking exact wording.

## Claude -p test harness

The `tests/test-skills.py` harness uses `claude -p` (pipe mode) to run skill
prompts through the locally installed Claude Code CLI. This works with Claude
Code subscription auth — no API key needed.

**Requirements:**

- `claude` CLI on PATH (included with Claude Code subscription)
- No additional dependencies

**Run:**

```bash
# Run all skill tests (structural + adversarial + negative)
TRELLIS_LLM_TESTS=1 python3 tests/test-skills.py

# Via npm (env var is set automatically)
npm run test:skills

# Run a single test
TRELLIS_LLM_TESTS=1 python3 -m unittest \
  tests.test-skills.TestSkillOutput.test_pitch_sections
```

## How it works

1. Read the skill's `SKILL.md` file
2. Concatenate it with user input using a `---` separator
3. Pipe the combined prompt to `claude -p` via subprocess
4. Assert structural properties of the output

```text
┌─────────────┐     ┌───────────┐     ┌──────────────┐
│  SKILL.md   │────▶│           │────▶│              │
│  + user     │     │ claude -p │     │  assertions  │
│    input    │     │           │     │  (assertIn)  │
└─────────────┘     └───────────┘     └──────────────┘
      stdin              CLI              unittest
```

### CLI flags used

- `--model sonnet` — use Sonnet for cost-efficient generation
- `--no-session-persistence` — don't save session state between tests
- `--max-budget-usd 0.05` — safety cap per test (~$0.35 total for all 7)

### Gating

Tests are double-gated to prevent accidental runs:

1. `claude` binary must be on PATH
2. `TRELLIS_LLM_TESTS=1` environment variable must be set

Without both conditions met, all tests are skipped with a descriptive message.
The `npm run test:skills` script sets the env var automatically, so running
that command opts you in. The `npm test` runner (via `run-all.sh`) does not
set the env var — skill tests only run there if you export it yourself.

### Timeout and budget

Each test has a 120-second timeout. If Claude is under heavy load, a test
may time out rather than hang indefinitely. The budget cap of $0.05 per test
prevents runaway costs — actual cost per test is typically $0.005-$0.015
on Sonnet.

## Test categories

Tests are organized into four categories, each testing a different
dimension of skill quality.

### Structural tests (`TestSkillOutput`)

Validate that skills produce output with the correct sections, headings,
and keywords. These are the baseline — if a skill doesn't produce the
right structure, nothing else matters.

| Test | Skill | What it checks |
|------|-------|----------------|
| `test_guidelines_sections` | guidelines | All 6 required sections + tech keywords |
| `test_pitch_sections` | pitch | Problem, Appetite, Shape, No-Gos, Rabbit Holes |
| `test_spec_sections` | spec | Section numbers (§1-§9), Success Criteria, Constraints |
| `test_plan_sections` | plan | Section numbers (§1-§6), File Structure |
| `test_tasks_sections` | tasks | Phase headings, Do/Verify blocks, checkboxes |
| `test_sketch_sections` | sketch | Hypothesis, Method, Findings, Verdict |
| `test_compliance_sections` | compliance | All 6 required sections + GDPR, FIPPA keywords |
| `test_cross_skill_spec_refs_pitch` | spec | Pitch referenced in §1, no-gos preserved in §9 |

### Adversarial tests (`TestAdversarialSkillOutput`)

Probe LLM judgment quality with tricky inputs that expose common failure
modes — solution-as-problem framing, contradictory constraints, vague
criteria, and disproven hypotheses.

| Test | Skill | What it checks |
|------|-------|----------------|
| `test_pitch_reframes_solution_as_problem` | pitch | Problem section describes user pain, not "add Redis" |
| `test_spec_flags_contradictory_constraints` | spec | Output flags tension between 3-week appetite and 10M users |
| `test_compliance_minimal_for_no_pii` | compliance | Recognizes no regulations apply to a static site with no PII |
| `test_tasks_concretizes_vague_criteria` | tasks | Verify blocks contain measurable language, not "should be fast" |
| `test_sketch_rejects_bad_hypothesis` | sketch | Verdict rejects SQLite at 10K writes/sec given 50/sec findings |

### Negative assertions (`TestNegativeAssertions`)

Assert that skills do NOT produce inappropriate content — hallucinated
technologies, code blocks in prose documents, functional requirements
in constraints sections, or feature-specific content in guidelines.

| Test | Skill | What it checks |
|------|-------|----------------|
| `test_pitch_no_code_blocks` | pitch | No triple-backtick code blocks |
| `test_spec_constraints_no_functional_requirements` | spec | §9 has no "endpoint", "shall return", etc. |
| `test_plan_no_unlisted_technologies` | plan | No MongoDB/MySQL/DynamoDB/SQLite when PostgreSQL specified |
| `test_compliance_no_gdpr_applies_for_no_pii` | compliance | No "GDPR applies" for a project with zero PII |
| `test_guidelines_no_feature_specific_content` | guidelines | No "invitation"/"onboarding" when none were in input |

### E2E implement smoke test (`TestImplementE2E`)

End-to-end test that verifies the implement skill can create code from
spec artifacts. Uses a minimal Node.js project (an `add` function) with
a pre-filled state file to skip Phase 0/1 and go directly to Phase 2.

| Test | Skill | What it checks |
|------|-------|----------------|
| `test_implement_creates_code_and_updates_state` | implement | Creates src/add.js, updates state file, tests pass |

**Triple-gated:** requires `claude` on PATH + `TRELLIS_LLM_TESTS=1` +
`TRELLIS_E2E_TESTS=1`. Run with:

```bash
npm run test:e2e
# or
TRELLIS_LLM_TESTS=1 TRELLIS_E2E_TESTS=1 python3 -m unittest \
  tests.test-skills.TestImplementE2E
```

This test uses `--dangerously-skip-permissions` and a $2.00 budget cap.
It runs in a temporary directory and cleans up after itself.

### Skills not covered

Two skills are not testable with the pipe pattern:

- **clarify** — modifies spec.md in place rather than producing a new document
- **pipeline** — orchestrates sub-skills without invoking the model directly

Both require filesystem access and tool use that `claude -p` without
tools cannot provide. The implement skill is covered by the E2E smoke
test above.

## Adding a new test case

Add a new method to `TestSkillOutput`:

```python
def test_new_skill_sections(self):
    output = run_skill("new-skill", """\
Your test input here.
Write the output now. Do not ask questions.""")

    assert_icontains(self, output, "## Expected Section")
    self.assertIn("exact match", output)
```

### Assertion helpers

| Helper | Usage |
|--------|-------|
| `assert_icontains(self, output, value)` | Case-insensitive contains |
| `self.assertIn(value, output)` | Exact contains |
| `assert_not_icontains(self, output, value)` | Case-insensitive not-contains |
| `self.assertNotIn(value, output)` | Exact not-contains |
| `assert_any_icontains(self, output, values)` | Any value matches (case-insensitive) |

## Non-determinism

LLM output is non-deterministic. The assertions are intentionally structural
(section headings, keywords) rather than exact-match. This means:

- Tests may occasionally fail if the model uses a slightly different heading
  format (e.g., `## Stack & Tools` instead of `## Stack`)
- If a test is consistently flaky, loosen the assertion rather than adding
  retries
- No retry logic is built in — a failure should surface for investigation
