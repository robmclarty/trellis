# FIPPA — Freedom of Information and Protection of Privacy Act (British Columbia)

## Applicability

Applies when a BC public body (including public school districts, universities, health authorities, and provincial government ministries) collects, uses, stores, or discloses personal information. Software vendors providing services to BC public bodies are subject to FIPPA through their contracts with those bodies.

## Core requirements

**Storage in Canada** — Personal information in the custody or control of a public body must be stored and accessed only in Canada. This includes backups, logs, caches, and any transient storage. Cloud infrastructure must be in Canadian regions.

**Collection limitation** — Personal information may only be collected if it relates directly to and is necessary for an operating program or activity of the public body. Collection must be authorized by the head of the public body.

**Purpose limitation** — Personal information may only be used for the purpose for which it was collected, or for a use consistent with that purpose. New uses require new authorization or consent.

**Access and correction** — Individuals have the right to request access to their personal information held by a public body, and to request corrections if the information is inaccurate.

**Privacy Impact Assessments (PIAs)** — Public bodies should conduct a PIA when implementing new systems or making significant changes to systems that handle personal information. While not always mandatory by statute, the BC OIPC strongly recommends them and they are standard practice.

**Disclosure** — Personal information may only be disclosed in limited circumstances: with consent, for the purpose for which it was collected, to the individual the information is about, to an officer or employee of the public body who needs it for their duties, or as required by law.

**Security safeguards** — Public bodies must protect personal information by making reasonable security arrangements against risks such as unauthorized access, collection, use, disclosure, or disposal.

## Key considerations for software vendors

1. All infrastructure must be in Canada (AWS ca-central-1, Azure Canada Central, GCP northamerica-northeast1, or Canadian colocations)
2. No data can transit through US or other non-Canadian servers, even temporarily
3. Support staff accessing data must be in Canada (or the public body must be informed and consent if access is from outside Canada)
4. Subprocessors must also comply with Canadian storage requirements
5. Encryption in transit and at rest is expected as a baseline security measure
6. The vendor must be able to support access requests and data deletion requests from the public body
7. Breach notification to the public body must be prompt and include details of the scope and nature of the breach

## Common compliance checkpoints for software systems

1. All data storage, processing, and backup infrastructure is in Canada
2. No third-party services transmit personal information outside Canada
3. Access controls limit personal information to authorized personnel
4. Audit trails exist for access to personal information
5. Data retention policies are defined and enforceable
6. The system supports data export and deletion to fulfill access/correction requests
7. Encryption is applied in transit (TLS) and at rest
