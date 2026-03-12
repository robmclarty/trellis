---
name: compliance
description: Creates a regulatory and privacy review at .specs/<feature-name>/compliance.md by evaluating the spec against applicable regulations. Use when a feature handles personal data, student data, health data, or financial data, when operating in a regulated jurisdiction, or when adding a new market. Triggers on "compliance review", "check for FERPA", "GDPR review", "privacy review", "does this meet FIPPA", "regulatory check", or any request to evaluate a spec against privacy or regulatory requirements.
context: fork
---

# Compliance

Create a regulatory and privacy review at `.specs/<feature-name>/compliance.md`.

## Purpose

Compliance reviews the spec through a regulatory lens. It identifies which regulations apply, evaluates the spec against their requirements, and flags anything that needs to change. This phase produces its own artifact rather than modifying the spec, because regulatory constraints are a distinct concern that may evolve independently as laws change or as the product enters new markets.

Not every feature needs a compliance review. A purely internal tool with no user data may skip this entirely. The compliance step applies only the regulations that are relevant.

## Prerequisites

- `.specs/<feature-name>/spec.md` must exist and have passed clarify (no unresolved `[? ...]` markers in the spec body)
- `.specs/guidelines.md` must exist

## What to ask the user

If the user runs `/compliance` without specifying which regulations apply, ask:

1. What kind of data does this feature handle? (Personal, student, health, financial, none)
2. What jurisdictions does this feature operate in? (Country, state/province)
3. Are there any organization-specific compliance requirements? (SOC 2, internal policies, contractual obligations)

Based on the answers, determine which regulations to evaluate against. Read the relevant reference files in `references/` for the core requirements of each applicable regulation.

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
