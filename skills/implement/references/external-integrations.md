# External Integrations

The implement skill can optionally integrate with external tools. Some are
bundled with Trellis, others are separate tools the user installs
independently. The implement skill detects their availability through
invocation modifiers or Phase 0 configuration questions.

## Ralph

**What it is:** A bundled loop script (`scripts/ralph-loop.sh`) that provides
context-fresh iteration for large implementations. Based on Geoffrey Huntley's
Ralph Wiggum methodology — each iteration runs in a fresh Claude Code context
window to avoid context degradation.

**How to use:** `/implement <feature> with ralph`

**How it works:** When `with ralph` is specified:
1. Phase 0 and Phase 1 run interactively in the current session (config
   questions, pipeline assembly, criteria extraction)
2. After `.claude/.implement-state.md` is written, the skill launches
   `scripts/ralph-loop.sh <feature-name>`
3. Before each iteration, the loop script runs pre-flight scripts
   (`validate-prereqs.py`, `parse-implement-state.py`, `extract-criteria.py`)
   and writes results to `.claude/.implement-preflight.json` so Claude doesn't need
   python3 access
4. The loop script generates `.claude/settings.local.json` with scoped
   permissions derived from the oracle pipeline config — only the user's
   specific toolchain commands, file tools, and git reads are allowed
5. Each iteration runs `claude -p` (without `--dangerously-skip-permissions`)
   with `/trellis:implement <feature-name>`
6. Between iterations, it parses `.claude/.implement-state.md` to check completion
7. Each iteration resumes from the next pending criterion via the state file
8. The loop stops when: all criteria pass, max iterations reached (default 10),
   or 3 consecutive failures occur without progress

**Security model:** Ralph iterations run with least-privilege permissions.
The loop script generates an allowlist from the oracle pipeline commands
configured during Phase 1. Claude can only execute the specific type-check,
lint, build, and test commands the user provided, plus file operations and
git reads. No `--dangerously-skip-permissions`, no arbitrary command execution.
If Claude needs a command not on the allowlist, the iteration fails safely
and the user can add it to the config.

**When to use:** Large implementations (10+ acceptance criteria, many files)
where context degradation is a concern. Skip for small implementations (2-3
criteria).

## Ralphd (Docker-sandboxed Ralph)

**What it is:** A variant of Ralph that runs each iteration inside a Docker
container with `--dangerously-skip-permissions`. Uses Docker as the security
boundary instead of scoped permission allowlists.

**How to use:** `/implement <feature> with ralphd`

**How it works:** When `with ralphd` is specified:
1. Phase 0 and Phase 1 run interactively (same as Ralph)
2. After `.claude/.implement-state.md` is written, the skill launches
   `scripts/ralphd-loop.sh <feature-name>`
3. On first run, the script builds the `trellis-ralphd` Docker image from
   `scripts/Dockerfile.ralphd` (Node.js 22 + Claude Code + git + python3)
4. Before each iteration, pre-flight scripts run on the host (same as Ralph)
5. Each iteration runs `docker run --rm -i` with the project directory
   bind-mounted and a named auth volume (`trellis-ralphd-auth`) providing
   credentials at `/home/claude/.claude`
6. `claude -p --dangerously-skip-permissions` runs inside the container
7. Between iterations, state is parsed on the host (same as Ralph)
8. Same termination conditions as Ralph

**Authentication:** Two modes, auto-detected:
- **API key:** If `ANTHROPIC_API_KEY` is set, it's passed into the container.
  No extra setup needed.
- **OAuth/subscription:** Run `ralphd-loop.sh --login` once. This opens an
  interactive container where you complete the OAuth flow in your browser. The
  session is stored in the `trellis-ralphd-auth` Docker volume and reused by
  all subsequent iterations — no re-login needed unless the token expires.

**Security model:** Docker container isolation replaces the scoped-permissions
model. The container can only access the bind-mounted project directory and
the auth volume — no host filesystem, no host processes.
`--dangerously-skip-permissions` is safe because the blast radius is the
container. No `.claude/settings.local.json` is generated.

**Requirements:**
- `docker` installed and daemon running
- One of: `ANTHROPIC_API_KEY` env var, or `ralphd-loop.sh --login` completed
- Sufficient disk space for the Docker image (~500MB)

**When to use:** Same scenarios as Ralph, plus:
- When scoped permissions are too restrictive (e.g., the implementation needs
  commands that are hard to predict in advance)
- When you want full `--dangerously-skip-permissions` behavior without
  exposing the host filesystem
- CI/CD environments where Docker is available and host isolation is preferred

**Trade-offs vs. Ralph:**
- **Pros:** No permission allowlist to maintain, Claude can run any command it
  needs, simpler security model
- **Cons:** Docker overhead per iteration (~2-5s startup), requires Docker
  installed, image build on first run, container filesystem is ephemeral
  (only the bind-mount persists)

## Promptfoo

**What it is:** An eval framework for LLM outputs that supports assertions,
model comparison, and repeatable test suites.

**Where to find it:** [promptfoo.dev](https://www.promptfoo.dev/) — Install
via `npm install -g promptfoo`

**How it integrates:** When Promptfoo is enabled in Phase 0:
1. The implement skill generates a `promptfoo.yaml` config from acceptance
   criteria during Phase 1
2. `promptfoo eval` runs as an additional pipeline stage (after tests, before
   or alongside the judge)
3. Results are stored for the user to review

**When to use:** Teams that build similar features often and want to codify
judge criteria as repeatable evals, A/B test prompts, or run regression checks.

## Open Spec

**What it is:** A structured requirements format designed for agentic
interpretation, with machine-parseable fields like `validation_criteria`,
`constraints`, and `scope`.

**Where to find it:** [github.com/open-spec/open-spec](https://github.com/open-spec/open-spec)

**How it integrates:** If the spec uses Open Spec format (detected
automatically or indicated by the user in Phase 0), the implement skill uses
its structured fields directly rather than extracting criteria from prose.
This gives more reliable acceptance criteria extraction and explicit scope
boundaries.

**When to use:** Projects that have adopted Open Spec as their requirements
format. Pairs well with Ralph for context-resilient implementation.
