# 31. Compliance as Executable Evidence

## Compliance should emerge from operation

Compliance becomes scalable when the platform emits evidence while ordinary engineering and commercial work occurs. A certificate, audit report, or questionnaire can remain important, but it should not be the only representation of control behavior.

The durable object is a control-evidence graph:

```text
ControlObjective
  → ControlImplementation
  → Observation
  → Evidence
  → FrameworkProjection
```

Framework names sit at the projection layer. Access control, change control, backup, incident response, vulnerability handling, data retention, and segregation of duties remain canonical control objectives.

## Separate control from framework mapping

One control can support several requirements across SOC 2, ISO 27001, internal policy, customer questionnaires, and marketplace security reviews. The mapping must be explicit and scoped; sharing a keyword is not an equivalence proof.

```text
CanonicalControlEvidence
  → SOC 2 view
  → ISO 27001 view
  → Marketplace security view
  → Customer control matrix
```

This architecture reduces manual synchronization without claiming that one audit automatically satisfies every buyer.

## Continuous evidence

Useful machine evidence includes:

- exact identity of production artifacts;
- branch/protection and release-policy observations;
- access grants and revocations;
- policy admission decisions;
- backup/restore tests;
- vulnerability results tied to digests;
- incident/response timestamps;
- key rotation and certificate state;
- data-residency observations;
- commercial actuation receipts.

Evidence should be content-addressed or otherwise tamper-evident where practical, and every artifact should name the subject and period it proves.

## Exceptions are objects

A policy exception needs owner, authority, affected control, affected customer/product scope, compensating control, start, expiry, and review outcome. It should not exist as a comment in a ticket that future automation cannot discover.

## Certificates are bounded evidence

SOC or ISO reports have scope and period. They do not prove a newly introduced marketplace adapter, region, subprocessor, or package that sits outside that scope. The product graph must prevent a certificate from being projected more broadly than the source permits.

## Refusals

- `REFUSED:CERTIFICATE_AS_ALL_PRODUCT_PROOF`
- `REFUSED:MANUAL_SCREENSHOT_WITHOUT_PROVENANCE`
- `REFUSED:FRAMEWORK_MAPPING_BY_LABEL_SIMILARITY`
- `REFUSED:EVIDENCE_OUTLIVES_SUBJECT`
- `REFUSED:EXCEPTION_WITHOUT_OWNER_OR_EXPIRY`

## Operational exercise

Choose access control, change management, backup, vulnerability handling, and entitlement actuation. For each, define a canonical control objective and the machine evidence the platform can produce. Project those controls into two frameworks and one marketplace review without changing the underlying control identity.
