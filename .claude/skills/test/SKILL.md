---
name: test
description: Run the project test suite. Use when verifying correctness after changes.
disable-model-invocation: true
allowed-tools: Bash(npm test *), Bash(npm run test *), Bash(python3 tests/*)
---

Run `npm test` and report the results. If tests fail, analyze the failures and suggest fixes.

Additional test scripts:
- `python3 tests/test-scripts.py` — unit tests for Python scripts
- `python3 tests/test-hooks.py` — unit tests for Python hooks
- `bash tests/run-all.sh` — run all test suites
- `bash tests/test-snapshots.sh` — snapshot tests for generated artifacts
