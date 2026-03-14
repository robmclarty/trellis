# Skill Testing

Trellis includes a test harness for validating that skill prompts produce
structurally correct output. This document explains the two approaches
available, when to use each, and how to add new test cases.

## Background

Each Trellis skill (guidelines, pitch, spec, plan, tasks, sketch) is defined
by a `SKILL.md` file containing structured instructions. When Claude processes
these instructions along with user input, it should produce output containing
specific sections, headings, and keywords. Skill tests validate these
structural properties without checking exact wording.

## Two approaches

### Promptfoo (API key required)

[Promptfoo](https://www.promptfoo.dev/) is a dedicated LLM evaluation
framework. Trellis includes a promptfoo config at `tests/promptfoo.yaml`
with 7 test cases covering all 6 skills plus a cross-skill artifact
consistency check.

**Requirements:**

- `npm install -g promptfoo`
- `ANTHROPIC_API_KEY` environment variable set

**Run:**

```bash
npm run test:llm
# or
promptfoo eval -c tests/promptfoo.yaml
promptfoo view  # opens web UI with results
```

**Tradeoffs:**

| Aspect | Promptfoo |
|--------|-----------|
| Auth | Requires `ANTHROPIC_API_KEY` |
| Parallelism | Runs tests in parallel |
| Assertions | Built-in (`contains`, `icontains`, regex, JS functions) |
| Reporting | Web UI with diffs, history, and CI integration |
| Cost model | Pay per API token |
| Speed | Fast (parallel API calls, no process overhead) |
| Setup | Separate install (`npm install -g promptfoo`) |

Promptfoo is the better choice for teams with API access who want rich
reporting, parallel execution, and CI integration.

### Claude -p test harness (subscription only)

The `tests/test-skills.py` harness uses `claude -p` (pipe mode) to run skill
prompts through the locally installed Claude Code CLI. This works with Claude
Code subscription auth — no API key needed.

**Requirements:**

- `claude` CLI on PATH (included with Claude Code subscription)
- No additional dependencies

**Run:**

```bash
# Run all 7 skill tests
TRELLIS_LLM_TESTS=1 python3 tests/test-skills.py

# Via npm (env var is set automatically)
npm run test:skills

# Run a single test
TRELLIS_LLM_TESTS=1 python3 -m unittest \
  tests.test-skills.TestSkillOutput.test_pitch_sections
```

**Tradeoffs:**

| Aspect | Claude -p harness |
|--------|-------------------|
| Auth | Subscription auth (no API key) |
| Parallelism | Sequential (one test at a time) |
| Assertions | Python `unittest` (`assertIn`, case-insensitive helpers) |
| Reporting | Terminal output (standard unittest) |
| Cost model | Included in subscription |
| Speed | Slower (~15-60s per test, ~2-5 min total) |
| Setup | None beyond Claude Code |

The Claude -p harness is the better choice for individual developers with a
Claude Code subscription who want to validate skills without managing API keys.

## Comparison summary

| | Promptfoo | Claude -p harness |
|---|-----------|-------------------|
| Auth | `ANTHROPIC_API_KEY` | Subscription |
| Install | `npm install -g promptfoo` | Nothing extra |
| Speed | ~30s total (parallel) | ~2-5 min (sequential) |
| Reporting | Web UI | Terminal |
| CI-friendly | Yes | Possible (needs auth) |
| Cost | Per-token API pricing | Included in subscription |

## How it works

The test harness follows the same pattern as promptfoo:

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

## Test cases

All 8 test cases mirror the promptfoo config in `tests/promptfoo.yaml`:

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

### Skills not covered

Three skills are not testable with the pipe pattern:

- **clarify** — modifies spec.md in place rather than producing a new document
- **implement** — multi-phase orchestration that spawns agents and writes code
- **pipeline** — orchestrates sub-skills without invoking the model directly

All three require filesystem access and tool use that `claude -p` without
tools cannot provide.

## Adding a new test case

To add a test for a new skill or scenario:

### 1. Add to promptfoo.yaml

```yaml
- description: "new-skill: produces expected output"
  vars:
    skill_instructions: file://skills/new-skill/SKILL.md
    user_input: |
      Your test input here.
      Write the output now. Do not ask questions.
  assert:
    - type: icontains
      value: "## Expected Section"
    - type: contains
      value: "exact match"
```

### 2. Add to test-skills.py

Add a new method to `TestSkillOutput`:

```python
def test_new_skill_sections(self):
    output = run_skill("new-skill", """\
Your test input here.
Write the output now. Do not ask questions.""")

    assert_icontains(self, output, "## Expected Section")
    self.assertIn("exact match", output)
```

### Assertion mapping

| Promptfoo assertion | Python equivalent |
|---------------------|-------------------|
| `type: icontains` | `assert_icontains(self, output, value)` |
| `type: contains` | `self.assertIn(value, output)` |

## Non-determinism

LLM output is non-deterministic. The assertions are intentionally structural
(section headings, keywords) rather than exact-match. This means:

- Tests may occasionally fail if the model uses a slightly different heading
  format (e.g., `## Stack & Tools` instead of `## Stack`)
- If a test is consistently flaky, loosen the assertion rather than adding
  retries
- No retry logic is built in — a failure should surface for investigation

Both promptfoo (with `temperature: 0`) and the Claude -p harness use the same
structural assertion strategy, so flakiness rates should be comparable.
