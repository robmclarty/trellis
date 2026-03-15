# Cognitive Sovereignty

There is a quiet failure mode in AI-assisted work. It doesn't look like failure — it looks like productivity. The tool suggests, the human accepts. The tool proposes a structure, the human follows it. The tool generates a plan, the human executes it. At no point does the human stop to ask whether this is what they actually wanted. The tool that was supposed to augment thinking has replaced it.

Trellis is designed to resist this.

## What Cognitive Sovereignty Means

Cognitive sovereignty is the principle that humans retain authorship over the decisions that matter. Not authorship over every keystroke — that's busywork, not thinking. Authorship over direction, scope, priority, and meaning. The choices that determine whether the thing being built is the right thing.

AI, or at least what we currently call AI, cannot make these choices. Not because the technology is immature, but because relevance — the judgment of what matters in a given context — is not a pattern that can be extracted from training data. Training data encodes billions of prior human decisions, and a language model can interpolate between them with remarkable fluency. But interpolation is not judgment. The model doesn't know what matters to you, in your situation, right now. It can only approximate what mattered to people in situations that looked similar.

This is the fundamental asymmetry: humans provide the creativity, the novelty, the innovation, and most importantly, the relevance. AI provides speed, breadth, and tireless execution of granular detail. Trellis is built around this asymmetry.

## The Human Role in Trellis

Trellis gives the human a specific role at every stage of development. Not a passive role — not "review this and click approve" — but the role that actually determines the outcome.

### Steering the AI

The pitch phase is where the human defines the problem. Not the solution — the problem. What's broken, who it affects, how much effort it deserves, and what's explicitly out of scope. These four inputs — problem, audience, appetite, and no-gos — constrain everything downstream. The AI generates within these boundaries. It doesn't set them.

When the human skips this step or provides vague input, the AI fills in the gaps with plausible-sounding guesses. Trellis marks every such guess with an `[AUTO]` tag so the human can find and override them later. The system never hides its own uncertainty.

### Conducting the Orchestra

The pipeline moves through four stages — pitch, spec, plan, build — and each stage ends with a review gate. The human reads a summary of what was generated and chooses one of three options:

- **Approve** — the output reflects their intent; continue to the next stage.
- **Edit** — the output is close but needs manual adjustment; the pipeline pauses while they reshape the artifact.
- **Redo** — the output missed the mark; regenerate from scratch.

This isn't a rubber stamp. The review gate is where the human exercises judgment about whether the AI understood the assignment. Each gate is a course correction opportunity — small adjustments early prevent expensive rework later.

### Validating the Blueprint

The spec and plan are not implementation artifacts. They're blueprints — human-readable markdown documents that describe what a system does and how it will be built. They exist so that a human can read them, understand them, and decide whether they represent the right approach.

The spec preserves ambiguity honestly. When the AI encounters something it can't resolve from context, it doesn't guess silently — it inserts a typed marker (`[? CATEGORY: ...]`) that surfaces the ambiguity for human resolution. The clarify phase resolves what it can from existing artifacts and moves the rest to an open questions section for the human to address.

The plan translates spec requirements into technical decisions. But the human provides the constraints first: what technology choices are already locked in, what the team's skill set looks like, what performance targets matter. The AI plans within these constraints. It doesn't override them.

### Focusing the Spotlight

Not every feature needs a compliance review. Not every spec has ambiguities worth resolving. Trellis uses lightweight detection — keyword scanning, artifact existence checks — to determine which pre-steps are relevant and skips the rest. The human's attention is directed only where it's needed.

When compliance is relevant, it runs automatically as a pre-step of planning, producing a structured review that classifies data, maps regulatory requirements, and recommends specific spec changes. The human decides which recommendations to accept. The AI identifies the risks; the human weighs them against the project's actual context.

### Directing the Workers

Implementation in Trellis is task-driven. The plan is decomposed into discrete, ordered tasks, each with a description of what to do and how to verify it. A single check command — lint, typecheck, test — runs after every task to confirm the code works.

But the human defines that check command. The human chose the testing strategy. The human wrote (or approved) the spec that generated the acceptance criteria the judge evaluates against. The AI executes the tasks and runs the checks, but the definition of "correct" was set by the human at every upstream stage.

When the judge evaluates the finished implementation, it doesn't ask "does the code work?" It asks "does the code satisfy the intent expressed in the spec?" Intent is a human concept. The spec is a human artifact. The judge is measuring AI output against human decisions.

## What Trellis Automates (and What It Doesn't)

Trellis automates the granular: generating document drafts, scanning for regulatory keywords, resolving unambiguous spec questions, decomposing plans into tasks, running check commands, evaluating implementation against acceptance criteria.

Trellis does not automate the consequential: defining problems, setting scope, choosing constraints, accepting or rejecting generated artifacts, deciding what's in and what's out, weighing tradeoffs that depend on context the AI doesn't have.

This distinction is the architecture. Every skill in Trellis is designed around it. The AI proposes; the human disposes. The AI drafts; the human directs. The artifacts are durable, readable, and editable — not opaque model outputs that can only be accepted or regenerated wholesale.

## Why This Matters

The risk of AI in software development is not that it writes bad code. It's that it writes plausible code that solves the wrong problem, and the human never notices because they stopped choosing three steps ago.

Cognitive sovereignty is the antidote. Not by slowing things down — Trellis accelerates development considerably — but by ensuring that the acceleration happens on a trajectory the human chose. The human sets the direction. The AI covers the distance. When the direction needs to change, the human changes it, and every downstream artifact adapts.

This is what it means to enhance the human experience rather than replace it: automate the details without hiding the decisions. Move fast without losing the ability to steer. Build with AI without forgetting that the point was always to build what matters — and only humans can say what that is.
