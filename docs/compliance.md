# Compliance: Privacy-Aware AI Development

Trellis includes a built-in compliance skill that evaluates every feature spec against applicable privacy regulations **before** any code is written. The goal is straightforward: enable AI-driven innovation without increasing PII risk.

## The Problem

AI-assisted code generation is fast. That speed becomes a liability when the generated code handles personal data — student records, health information, contact details — without accounting for privacy regulations. By the time a manual review catches a GDPR violation or a FIPPA storage requirement, the feature is already built and the fix is expensive.

Trellis solves this by making compliance review a **structural part of the development pipeline**, not an afterthought.

## How Compliance Works

The compliance skill reads a feature's functional spec and evaluates it against five regulatory frameworks:

| Regulation | Scope |
|-----------|-------|
| **GDPR** | Personal data of individuals in the EU/EEA |
| **FERPA** | Student education records in US federally-funded schools |
| **FIPPA** | Personal information held by BC public bodies (requires Canadian storage) |
| **COPPA** | Online collection from children under 13 |
| **SOC 2** | Voluntary trust framework often required by enterprise customers |

Each framework is defined as a reference document with specific requirements, checkpoints, and common pitfalls. The skill cross-references these against the spec's data model and constraints to produce a structured review.

### What the Review Covers

The output (`compliance.md`) contains six sections:

1. **Applicable Regulations** — Which frameworks apply and why, with justification for each. Frameworks considered but not applicable are noted so the reasoning is auditable.

2. **Data Classification** — Every data entity from the spec is classified as Public, Internal, Sensitive, or Restricted. Sensitive and Restricted fields identify the governing regulation and trigger fields.

3. **Requirement Mapping** — Each applicable regulation's requirements are evaluated against the spec. Every requirement gets a status: *Satisfied* (with spec section reference), *Gap* (what's missing), or *Partial* (what's covered and what isn't).

4. **Data Flow Concerns** — Traces sensitive data through the system to identify boundary crossings: data leaving the country, shared with third parties, logged or cached in violation of retention policies, or accessible to unauthorized users.

5. **Recommended Spec Changes** — Concrete changes needed, each referencing the specific spec section to modify. These feed back into spec revision.

6. **Residual Risks** — Concerns that can't be resolved by spec changes alone (vendor certifications, legal review, organizational policy decisions), each with a suggested owner or next step.

## Integration with the Plan Skill

Compliance doesn't run in isolation. It's wired into the pipeline as an **automatic pre-step of the plan skill**.

When you run `/trellis:plan`, the following happens before any technical planning begins:

```
/plan invoked
  │
  ├── Step A: Run /clarify (resolve spec ambiguities)
  │
  ├── Step B: Check compliance
  │     │
  │     ├── Does the spec mention PII, personal data, student data,
  │     │   health data, email, SSN, FERPA, GDPR, etc.?
  │     │     │
  │     │     ├── No  → Skip compliance (no sensitive data detected)
  │     │     └── Yes → Has compliance.md already been generated?
  │     │           │
  │     │           ├── Yes → Skip (already complete)
  │     │           └── No  → Run compliance skill
  │     │
  │     └── If compliance finds gaps:
  │           ├── Apply recommended spec changes
  │           ├── Re-run clarify on modified spec
  │           ├── Re-run compliance (max 2 loops)
  │           └── After 2 loops, document remaining issues as residual risks
  │
  └── Step C: Generate plan.md (reads compliance.md for constraints)
```

The detection is keyword-based — a regex scan for terms like `PII`, `personal data`, `student data`, `health data`, `email`, `SSN`, `FERPA`, `GDPR`, `FIPPA`, `COPPA`, and `HIPAA`. This keeps it fast while catching the common cases. Users can also declare compliance requirements explicitly when writing the spec.

### Why It Runs Before Planning

Technical decisions depend on compliance constraints. If FIPPA applies, infrastructure must use Canadian data centers. If COPPA applies, behavioral advertising is prohibited. If GDPR applies, the architecture needs erasure and portability endpoints. These aren't details you bolt on later — they shape the plan from the start.

The plan-writer agent reads `compliance.md` and incorporates its constraints into the technical architecture (storage decisions, access controls, data retention, audit logging). Every compliance constraint must be addressed with a specific technical approach in the plan.

## Privacy Checks Without Friction

The system is designed so that privacy protection happens automatically:

**No extra steps for developers.** Compliance runs as part of `/plan`. If there's no sensitive data, it skips silently. If there is, it runs without requiring manual invocation.

**No interactive prompts mid-review.** The compliance skill runs in an isolated context (`context: fork`). It works entirely from the spec and guidelines — no back-and-forth questions. This means it can run unattended and produces deterministic, repeatable results.

**Spec changes feed back upstream.** When compliance identifies gaps, the recommended changes target specific spec sections. The spec gets revised, clarify re-runs to check consistency, and compliance re-runs to verify. This loop is capped at 2 iterations to prevent churn; anything unresolved becomes a documented residual risk.

**Pipeline status tracks compliance.** The pipeline status script exposes two fields — `complianceNeeded` and `complianceCompleted` — so you always know whether compliance has been addressed for a given feature.

## Enabling Innovation, Reducing Risk

The compliance skill exists because moving fast and handling data responsibly aren't contradictory goals — they just require the right structure.

By embedding regulatory review into the spec pipeline:

- **PII risks surface early**, during planning rather than after implementation, when fixes are cheap and architectural.
- **Regulatory knowledge is encoded**, not tribal. The reference documents for GDPR, FERPA, FIPPA, COPPA, and SOC 2 are maintained alongside the skills, making compliance accessible to teams without dedicated privacy counsel.
- **AI-generated code inherits compliance constraints.** Because the plan and tasks are shaped by compliance findings, every downstream implementation decision — from database schema to API design to logging configuration — accounts for privacy requirements.
- **Audit trails are built in.** The compliance.md artifact documents what was evaluated, what was found, and what was decided. This is valuable for internal review, vendor assessments, and regulatory inquiries.

The result: teams can use AI to accelerate development while maintaining — and in many cases improving — their privacy posture. The compliance review catches what humans skip under time pressure, and it does so at the point in the process where the findings have the most impact.
