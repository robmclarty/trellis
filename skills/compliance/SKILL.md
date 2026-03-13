---
name: trellis:compliance
description: Creates a regulatory and privacy review at .specs/<feature>/compliance.md by evaluating the spec against applicable regulations (GDPR, FERPA, FIPPA, COPPA, SOC 2).
context: fork
---

# Compliance

## When to use

- "compliance review", "check for FERPA", "GDPR review", "privacy review"
- "does this meet FIPPA", "regulatory check"
- When a feature handles personal data, student data, health data, or financial data
- When operating in a regulated jurisdiction or adding a new market

Create a regulatory and privacy review at `.specs/<feature-name>/compliance.md`.

## Specs directory resolution

Before starting, read `trellis.json` from the project root. If it exists and has a `specsDir` field, use that value as the specs directory. Otherwise, default to `.specs/`. All references to `.specs/` in this document refer to the resolved specs directory.

## Purpose

Compliance reviews the spec through a regulatory lens. It identifies which regulations apply, evaluates the spec against their requirements, and flags anything that needs to change. This phase produces its own artifact rather than modifying the spec, because regulatory constraints are a distinct concern that may evolve independently as laws change or as the product enters new markets.

Not every feature needs a compliance review. A purely internal tool with no user data may skip this entirely. The compliance step applies only the regulations that are relevant.

## Prerequisites

- `.specs/<feature-name>/spec.md` must exist and have passed clarify (no unresolved `[? ...]` markers in the spec body)
- `.specs/guidelines.md` must exist

## Determining applicable regulations

Since this skill runs in an isolated context (`context: fork`) without access to conversation history, it cannot interactively ask the user questions. Instead, determine applicable regulations from the available artifacts:

1. **From the spec's §4 (Data Model):** Identify data categories — personal data, student records, health data, financial data. Each category implies specific regulations.
2. **From the spec's §9 (Constraints):** Look for jurisdiction or deployment constraints (e.g., "deployed in Canada" → FIPPA, "serves EU users" → GDPR).
3. **From `guidelines.md`:** Check for infrastructure constraints that imply jurisdiction (e.g., `ca-central-1`).
4. **From the pitch:** Check for mentions of target users (e.g., "K-12 schools" → FERPA/COPPA).

If the data model contains no sensitive categories and no jurisdictional constraints are found, note that no regulations apply and produce a minimal compliance document explaining why.

> **Note:** When invoked through `/pipeline`, the pipeline skill asks the user about compliance requirements upfront (interactive mode question 3, auto mode question 10). This context is embedded in the spec's §9 or the pitch before compliance runs, enabling accurate regulation selection. When invoked standalone, compliance infers from artifacts only — if regulation scope is ambiguous, list the ambiguity in the Residual Risks section.

Read the relevant reference files in `references/` for the core requirements of each applicable regulation.

## Output: `.specs/<feature-name>/compliance.md`

### Sections

**Applicable Regulations** — List which regulations apply and why. For each, a one-sentence justification. If a regulation was considered but doesn't apply, note that briefly so future reviewers don't re-evaluate it.

**Data Classification** — Categorize every data entity from the spec's §4 (Data Model):

- *Public*: No restrictions on access or storage
- *Internal*: Restricted to authorized users, no regulatory sensitivity
- *Sensitive*: Subject to regulatory requirements (PII, education records, health data)
- *Restricted*: Highest sensitivity, strict access controls and audit requirements

For sensitive and restricted data, identify which specific fields trigger the classification and which regulation governs them.

**Requirement Mapping** — For each applicable regulation, evaluate the spec against its requirements. Organize as a list of specific requirements with a status:

- *Satisfied*: The spec already addresses this. Reference the relevant spec section.
- *Gap*: The spec does not address this. Describe what's missing.
- *Partial*: The spec partially addresses this. Describe what's covered and what's not.

**Data Flow Concerns** — Trace how sensitive data moves through the system. Identify any points where data crosses a boundary that creates regulatory risk: leaving the country, being shared with a third party, being logged or cached in a way that violates retention policies, being accessible to users who shouldn't see it.

**Recommended Spec Changes** — A concrete list of changes the spec needs. Each item should reference the specific spec section to modify and describe the change. These feed back into a `/spec` revision.

**Residual Risks** — Compliance concerns that cannot be fully resolved by spec changes alone. Examples: vendor compliance certifications needed, legal review required, organizational policy decisions outside this feature's scope. Each risk should have a suggested owner or next step.

## Loopback

If the "Recommended Spec Changes" section is non-empty, the spec needs revision. Tell the user which changes are needed and suggest they update the spec with `/spec`, then re-run `/clarify` and `/compliance` to verify the changes resolve the issues.

## Quality gate

- [ ] Every regulation considered is listed with a clear apply/not-apply justification
- [ ] Every data entity from the spec is classified
- [ ] Every applicable regulation has its requirements mapped with statuses
- [ ] Gaps are specific enough that a spec author knows exactly what to add or change
- [ ] Data flow concerns trace actual paths from the spec, not hypothetical ones
- [ ] Recommended changes reference specific spec sections
