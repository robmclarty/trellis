# SOC 2 — Service Organization Control 2

## Applicability

SOC 2 is not a law but a voluntary compliance framework based on the AICPA Trust Services Criteria. It applies when a service organization wants to demonstrate that it has effective controls over security, availability, processing integrity, confidentiality, and/or privacy. Many enterprise and education customers require SOC 2 reports from their vendors as a condition of procurement.

## Trust Services Criteria

SOC 2 is organized around five categories. Not all are required; the organization selects which criteria to include in the audit.

**Security (Common Criteria)** — Always included. Covers protection of information and systems against unauthorized access. Includes access controls, encryption, monitoring, incident response, and vulnerability management.

**Availability** — The system is available for operation and use as committed. Covers uptime, disaster recovery, backup, and capacity planning.

**Processing Integrity** — System processing is complete, valid, accurate, timely, and authorized. Covers data validation, error handling, and processing monitoring.

**Confidentiality** — Information designated as confidential is protected as committed. Covers data classification, encryption, access restrictions, and secure disposal.

**Privacy** — Personal information is collected, used, retained, disclosed, and disposed of in conformity with the entity's privacy notice and criteria. Overlaps significantly with regulatory requirements like GDPR and FERPA.

## Common compliance checkpoints for software systems

1. Access controls enforce least-privilege principles
2. Authentication uses strong methods (MFA where applicable)
3. Encryption is applied in transit (TLS 1.2+) and at rest (AES-256 or equivalent)
4. Audit logging captures access, changes, and administrative actions
5. Logs are retained for the defined period and protected against tampering
6. Vulnerability scanning and patching processes are documented
7. Incident response procedures are defined and tested
8. Backup and recovery procedures are documented and tested
9. Change management processes exist for code and infrastructure changes
10. Vendor/subprocessor management policies are in place
