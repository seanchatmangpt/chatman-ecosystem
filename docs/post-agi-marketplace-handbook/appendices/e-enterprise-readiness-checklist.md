# Appendix E — Enterprise Readiness Checklist

Use this as an admission queue, not a marketing checklist. An unchecked item is not automatically a defect; it is `UNKNOWN`, `UNSUPPORTED`, `BLOCKED`, or an explicit non-goal until classified.

## Product and commerce

- [ ] Canonical product/version identity exists.
- [ ] Plans and feature rights are machine-readable.
- [ ] Public/private offer rules are explicit.
- [ ] Entitlement lifecycle is idempotent.
- [ ] Fulfillment is separate from entitlement.
- [ ] Meter dimensions and units are versioned.
- [ ] Billing route prevents double charging.
- [ ] Settlement reconciliation exists.
- [ ] Renewal, cancellation, and termination are tested.

## Security

- [ ] Tenant isolation is demonstrated.
- [ ] Workload and human identity are separated.
- [ ] Least privilege is enforced.
- [ ] Secrets are managed and rotated.
- [ ] Encryption boundaries are documented.
- [ ] Customer-managed key support is truthfully classified.
- [ ] Private connectivity is truthfully classified.
- [ ] SBOM and artifact provenance exist.
- [ ] Vulnerability handling has SLO/ownership.
- [ ] Incident evidence is retained.

## Privacy and data governance

- [ ] Data classes are defined.
- [ ] Residency rules are enforceable.
- [ ] Cross-border processing is mapped.
- [ ] Subprocessors are versioned.
- [ ] Retention and deletion are implemented.
- [ ] Backup retention is consistent with deletion promises.
- [ ] Model/AI use of customer data is explicit.

## Reliability and support

- [ ] SLIs are measurable.
- [ ] SLOs match architecture.
- [ ] SLA promises are versioned with commercial plans.
- [ ] RTO/RPO are exercised.
- [ ] Support severity and response semantics exist.
- [ ] Service-credit calculation is evidence-backed.

## Procurement and legal evidence

- [ ] Seller legal entity is admitted.
- [ ] Tax/banking marketplace prerequisites are owned.
- [ ] Insurance/certifications have expiry tracking.
- [ ] EULA/terms are approved by proper authority.
- [ ] DPA/subprocessor materials are available.
- [ ] Marketplace terms vs negotiated terms are mapped.
- [ ] Export/regional restrictions are classified.

## Standing

- [ ] Exact marketplace subject is named.
- [ ] Sandbox behavior executed.
- [ ] Live behavior executed where required.
- [ ] Receipts verify.
- [ ] Replay/reconstruction matches.
- [ ] Exclusions are published.
