# Changelog

All notable changes to Trellis are documented in this file.

## 0.7.6

- Rename plugincheck scripts to lint:plugin for consistency
- Resolve agnix warnings (scope Bash permissions, add trigger phrases, clean CLAUDE.md)
- Suppress agnix false-positive errors for trellis: namespace prefix
- Fix shellcheck warnings in ralph-loop.sh
- Fix markdownlint blanks-around-lists warnings
- Remove promptfoo test dependency

## 0.7.5

- Populate changelog entries from git log context in version skill

## 0.7.4

- Add CHANGELOG.md with full version history
- Update version skill to insert changelog entries and auto-commit

## 0.7.3

- Add document validation script for pitch, spec, and plan documents

## 0.7.2

- Simplify pipeline to 4 human-facing stages with review gates

## 0.7.1

- Rename `trellis:tasks` to `trellis:prep`, auto-detect missing `tasks.json`

## 0.7.0

- Simplify implement executor — replace oracle pipeline with single check command

## 0.6.6

- Harden ralphd plugin resolution inside Docker container

## 0.6.5

- Strengthen preflight check and purge legacy `.state/` paths

## 0.6.4

- Use fully qualified `/trellis:implement` in docs and skill invocation examples
- Document Ralph streaming flags and feature-specific state in README

## 0.6.3

- Add Ralph output streaming (`--stream`, `--tail`) and feature-specific state files

## 0.6.2

- Harden ralph loop scripts against escaping bugs and bash 3.2 compatibility
- Add cognitive sovereignty section to README

## 0.6.1

- Remove stale trigger phrases from implement and plan skills

## 0.6.0

- Restructure implement skill to prevent phase skipping and Ralph confusion

## 0.5.10

- Prevent implement skill from skipping oracle pipeline and judge

## 0.5.9

- Prefix skill names with `trellis:` namespace

## 0.5.8

- Flatten commands to `{name}.md` instead of `{name}/SKILL.md`
- Rename marketplace to robmclarty

## 0.5.7

- Rename marketplace to robmclarty

## 0.5.6

- Update marketplace name to trellis

## 0.5.5

- Resolve hook scripts via `installed_plugins.json` fallback

## 0.5.4

- Raise skill test budget and fix flaky assertions

## 0.5.3

- Add adversarial, negative, and E2E implement tests

## 0.5.2

- Add compliance skill test case

## 0.5.1

- Add `claude -p` skill test harness
- Expand test coverage from 47 to 96 tests with bats-core shell testing

## 0.4.9

- Resolve markdownlint warnings across markdown files

## 0.4.8

- Resolve shellcheck warnings across shell scripts
- Move implement state from `.claude/` to `{specsDir}/.state/`
- Move agnix target to config file
- Rename Agent to Task in skill allowed-tools
- Apply agnix auto-fixes to skills and agents
- Correct auto-fixer regressions in skill descriptions
- Drop `trellis:` prefix from skill names (temporary)

## 0.4.7

- Add `.claude` config with settings and skill definitions
- Add version bump skill

## 0.4.6

- Replace prettier with JSON syntax-only validator

## 0.4.5

- Use `CLAUDE_PLUGIN_ROOT` for hook paths
- Add linting toolchain (prettier, markdownlint, ruff, shellcheck)
- Simplify `plugin.json` manifest and add `package.json`
- Update Ralph section in README to reflect bundled loop scripts

## 0.4.3

- Add `with ralphd` modifier for Docker-sandboxed implementation loops

## 0.4.2

- Replace `--dangerously-skip-permissions` with scoped permissions in Ralph loop
- Move implement state files from project root to `.claude/`

## 0.4.0

- Add `with ralph` modifier to implement skill for automated loop execution

## 0.3.2

- Add guidelines.md as prerequisite for implement and clarify skills
- Add usage examples and self-hosting guide to README
- Replace skill tables with command-first bullet lists in README

## 0.3.1

- Synthesize guidelines in plan-writer instead of restating them

## 0.3.0

- Initial stable release of the full skill pipeline

## 0.2.2

- Add automated tests for hooks, snapshots, and promptfoo evals

## 0.2.1

- Replace jq dependency with python3 and sed in hook scripts

## 0.2.0

- Allow custom specs directory via `trellis.json`

## 0.1.5

- Namespace skill commands under trellis prefix and fix CLAUDE.md diagram alignment

## 0.1.4

- Correct install command in README and normalize plugin source path

## 0.1.3

- Add `hooks.json` for hook discovery
- Fix hook stdin parsing
- Remove `.DS_Store` files

## 0.1.2

- Namespace skill commands under trellis prefix and add supporting infrastructure

## 0.1.1

- Correct plugin and marketplace schema and fill in missing data
- Remove redundancies from manifests

## 0.1.0

- Initial release
