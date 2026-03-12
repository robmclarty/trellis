# GDPR — General Data Protection Regulation (EU/EEA)

## Applicability

Applies when processing personal data of individuals in the EU/EEA, regardless of where the processing organization is located. If your system has users in the EU or processes data about EU residents, GDPR applies.

## Core requirements

**Lawful basis** — Every processing activity must have a lawful basis: consent, contract performance, legal obligation, vital interests, public task, or legitimate interests. The basis must be identified before processing begins.

**Data minimization** — Collect and process only the personal data that is necessary for the specified purpose. No "just in case" data collection.

**Purpose limitation** — Data collected for one purpose cannot be used for a different, incompatible purpose without new consent or another lawful basis.

**Right to erasure (right to be forgotten)** — Individuals can request deletion of their personal data when it is no longer necessary, when they withdraw consent, or when processing is unlawful. The controller must comply without undue delay (generally within 30 days).

**Right to data portability** — Individuals can request their data in a structured, commonly used, machine-readable format and have it transmitted to another controller.

**Right of access** — Individuals can request a copy of all personal data being processed about them, along with information about the purposes, categories, recipients, and retention periods.

**Data Protection Impact Assessment (DPIA)** — Required when processing is likely to result in a high risk to individuals, including systematic monitoring, large-scale processing of sensitive data, or automated decision-making with legal effects.

**Breach notification** — The supervisory authority must be notified within 72 hours of becoming aware of a personal data breach. Affected individuals must be notified without undue delay if the breach is likely to result in a high risk.

**Data Processing Agreements (DPAs)** — Controllers must have a written agreement with any processor (vendor) that processes data on their behalf, specifying the subject matter, duration, nature, and purpose of processing.

**International transfers** — Personal data may not be transferred outside the EEA unless the receiving country has an adequacy decision, or appropriate safeguards (Standard Contractual Clauses, Binding Corporate Rules) are in place.

## Common compliance checkpoints for software systems

1. A lawful basis is identified for each category of personal data processed
2. Consent mechanisms are granular, specific, and withdrawable
3. The system supports data export (portability) in a standard format (JSON, CSV)
4. The system supports data deletion with verification
5. Access request workflows can produce a complete data report per user
6. Data retention policies are automated where possible
7. Breach detection and notification processes are defined
8. International data transfers have appropriate safeguards
9. Processing activities are documented (Article 30 records)
