# Changelog

All notable changes to Trellis are documented in this file.

## 0.8.1

- Add judge and polish phase documentation explaining goals, mechanics, and pipeline integration
- Document redefinition loop, polish phase, and updated ralph orchestration in build.md

## 0.8.0

- Add post-judge redefiner agent for automated task redefinition on blocked/failed builds
- Add post-judge polish phase with optimizer and improver agents (opt-out with `--no-polish`)
- Rename generation agents: guidelines-writer → guideliner, pitch-writer → pitcher, plan-writer → planner, sketch-writer → sketcher, spec-writer → specifier

## 0.7.18

- Rename `--max-iterations` flag to `--limit` in Ralph loop for clarity

## 0.7.17

- Fix Docker platform mismatch that blocked all Ralph tasks on macOS hosts
- Add anonymous volume overlays for dependency dirs (node_modules, vendor, .venv, target) to isolate container installs from host
- Add `host_dep_sync()` to reinstall host dependencies when manifest files (package.json, requirements.txt) change
- Harden builder, retry, and test-writer prompts to prohibit running install commands inside Docker
- Add preflight warning when package.json exists but node_modules is missing

## 0.7.16

- Add real-time progress visibility to Ralph loop via `status.json` and combined `output.log`
- Build skill now polls ralph every 60s showing elapsed time, current task, and recent output
- `/trellis:status` and session startup display active ralph progress inline
- Use environment variables in `write_status()` to prevent shell injection from task titles

## 0.7.15

- Fix Docker volume ownership mismatch that silently broke Ralph auth persistence
- Pre-create `/home/claude/.claude/` with correct ownership in Dockerfile so new volumes inherit `claude:claude`
- Run `clean_auth_volume` as root to handle root-owned stale files and fix volume ownership
- Fail loudly during `--login` if credentials weren't saved, with actionable remediation guidance

## 0.7.14

- Always rebuild Ralph Docker image with daily cache bust to prevent stale Claude Code versions
- Persist OAuth token (`~/.claude.json`) into auth volume during `--login` so it survives container exit
- Mount Docker-persisted OAuth token during task runs instead of host's keychain-backed copy

## 0.7.13

- Fix Ralph auth check using bare Docker invocation instead of full docker args, causing false auth failures
- Reorder Ralph init so settings and volume cleaning happen before auth check
- Stop cleaning `session-env/` and `cache/` from auth volume to preserve OAuth tokens

## 0.7.12

- Fix build skill calling validate-prereqs with wrong skill name (`implement` → `build`)
- Make streaming the default output mode for Ralph mode (add `--silent` flag for old behavior)
- Fix OAuth auth check false positives by using exit codes instead of output grepping

## 0.7.11

- Fix prep skill skipping user questions when auto-invoked from build during run pipeline

## 0.7.10

- Fix run skill auto-detecting feature names instead of asking the user when no argument is provided

## 0.7.9

- Add feature name conflict detection to run skill — resolve name before intake and offer resume/fresh/rename when a feature already exists

## 0.7.8

- Rename pipeline skill to run for shorter, more intuitive invocation (`/trellis:run`)
- Rename implement skill to build to read naturally in the pipeline flow
- Add init skill for project initialization; init now calls guidelines automatically
- Flip init/guidelines relationship so init is the entry point

## 0.7.7

- Add compliance skill documentation explaining privacy checks and /plan integration
- Add cognitive sovereignty essay on human decision-making in AI-assisted development
- Replace README ASCII art with chaos-to-order mosaic visualizing the pipeline progression
- Move examples to root directory and update for current API
- Fix README discrepancies: skill count, agent list, hook details, workflow steps
- Extract README examples into standalone docs

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

- Synthesize guidelines in planner instead of restating them

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
