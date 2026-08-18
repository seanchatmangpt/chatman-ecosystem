# SOC2 Trust Services Criteria Control Mapping

Last updated: 2026-08-18

## What this document is, and is not

This document maps each of the 63 controls recorded in
`evidence/control-evidence-bundle.json` to the AICPA 2017 Trust Services Criteria (TSC)
framework, as structured in `ggen-marketplace/packs/soc2-audit-pack/ontology.ttl` (the
reference doctrine this ecosystem already maintains for SOC2 engagements).

**This is a self-assessed mapping, not a SOC2 report, not an auditor's opinion, and not a
compliance determination.** Only a licensed CPA firm, after an independent audit, can issue
a SOC2 report or an opinion on control operating effectiveness. This document carries
forward the same disclaimer already stated in `evidence/control-evidence-bundle.json`:
evidence-bundle-complete, never "compliant." What this document adds is structure: for a
compliance team asking "which Trust Services Criteria does this platform's control set
actually cover," this gives a starting point -- self-assessed coverage, gaps included --
instead of zero.

Mapping a control to a TSC category here means: this control, as evidenced in the bundle,
is relevant to that category's control objective. It does NOT mean the control has been
tested for operating effectiveness over a period (a real SOC2 Type II requirement), nor
that the mapping has been reviewed by an auditor or compliance professional. Controls with
no honest, defensible mapping are marked **Not mapped** rather than force-fit into a
category.

## Reference framework

Per `ggen-marketplace/packs/soc2-audit-pack/ontology.ttl`, the AICPA TSC framework defines
5 Trust Services Categories:

| Category | Notation | Scope |
|---|---|---|
| Security (Common Criteria) | TSC-SECURITY | Mandatory in every SOC2 engagement. Subdivides into CC1-CC9 (Control Environment, Communication & Information, Risk Assessment, Monitoring Activities, Control Activities, Logical & Physical Access Controls, System Operations, Change Management, Risk Mitigation). |
| Availability | TSC-AVAILABILITY | A1.1-A1.3: availability commitments, environmental/backup/capacity protections, **tested** recovery procedures. |
| Confidentiality | TSC-CONFIDENTIALITY | C1.1-C1.2: data classification, protection mechanisms. |
| Processing Integrity | TSC-PROCESSING-INTEGRITY | PI1.1-PI1.5: inputs/processing/outputs/storage are complete, accurate, timely, authorized. |
| Privacy | TSC-PRIVACY | P1-P8: notice through collection, use, access, disclosure, quality, monitoring/enforcement of personal information. |

Security is scoped in for every control set below where relevant. The other 4 categories
are scoped in only where this platform's control genuinely touches that category's
objective -- consistent with `ggen-marketplace/packs/soc2-audit-pack`'s own doctrine that
Availability/Confidentiality/Processing Integrity/Privacy are scoped per engagement, not
assumed.

This platform does not process customer payment data and does not hold third-party PII
subject to a documented privacy program (see `docs/SCOPE-AND-LIMITATIONS.md`), so Privacy
mappings below are sparse and, where present, mark only the narrow slice of a control that
touches personal-data handling -- not a claim of a Privacy program.

## Mapping

Each row cites the control's index in `evidence/control-evidence-bundle.json`'s `controls[]`
array (1-based) and its `control` field verbatim.

| # | Control | TSC Category | Sub-criterion | Rationale |
|---|---|---|---|---|
| 1 | `resource-quotas-enforced` | Availability | A1.2 | Capacity monitoring/enforcement via live-verified ResourceQuota admission rejection. |
| 2 | `network-segmentation` | Security | CC6 | Logical access control via NetworkPolicy. |
| 3 | `least-privilege-rbac` | Security | CC6 | Logical access controls, least-privilege enforcement. |
| 4 | `audit-logging` | Security | CC7 | System operations monitoring/logging. |
| 5 | `self-service-project-provisioning` | Security | CC8 | Change management -- provisioning is a controlled change. |
| 6 | `observability-proxy-least-privilege` | Security | CC6 | Least-privilege access to observability data. |
| 7 | `gitops-read-only-visibility` | Security | CC6 | Read-only access enforcement (least privilege). |
| 8 | `mtls-enforced` | Security | CC6 | Logical access control -- transport authentication. |
| 8 | `mtls-enforced` | Confidentiality | C1.2 | Protection mechanism for data in transit. |
| 9 | `autoscaling-enforced` | Availability | A1.2 | Capacity monitoring/scaling. |
| 10 | `load-test-drives-real-autoscale-event` | Availability | A1.2 | Live-verified capacity response under load. |
| 11 | `secrets-never-logged-or-rendered` | Confidentiality | C1.2 | Protection mechanism -- secret redaction. |
| 12 | `least-privilege-per-namespace-secrets-rbac` | Security | CC6 | Least-privilege access to secrets. |
| 12 | `least-privilege-per-namespace-secrets-rbac` | Confidentiality | C1.2 | Access restriction as a protection mechanism. |
| 13 | `registry-visibility-least-privilege` | Security | CC6 | Least-privilege access control. |
| 14 | `backup-job-verified-nonempty` | Availability | A1.2 | Backup verification. |
| 15 | `rate-limiting-enforced` | Availability | A1.2 | Capacity/availability protection under load. |
| 16 | `usage-metrics-real-not-fabricated` | Processing Integrity | PI1.1 | Inputs (usage metrics) verified complete and accurate, not fabricated. |
| 17 | `alerting-pipeline-verified-live` | Security | CC4 | Monitoring activities. |
| 17 | `alerting-pipeline-verified-live` | Availability | A1.2 | Capacity/incident monitoring. |
| 18 | `service-discovery-dns-resolves-live` | Availability | A1.1 | System availability -- live-verified service reachability. |
| 19 | `feature-flag-live-toggle-verified` | Not mapped | -- | Product configuration mechanism; no defensible TSC objective without a documented change-approval process around flag changes (see `resource-tagging-filter-matches-real-label-selector` note below for the same caveat pattern). |
| 20 | `topology-visualization-real-data` | Not mapped | -- | Read-only visualization of already-covered infrastructure (network-segmentation, mtls-enforced); mapping the view itself would double-count the same objective under a new control name. |
| 21 | `identity-federation-live-verified` | Security | CC6 | Logical access control -- identity verification. |
| 22 | `application-rbac-role-enforced` | Security | CC6 | Logical access control, least privilege at the application layer. |
| 23 | `restore-recovers-real-deleted-data` | Availability | A1.3 | Tested recovery procedure (the TSC point of focus that explicitly requires testing, not just a written plan). |
| 24 | `edge-function-invocation-verified` | Processing Integrity | PI1.3 | Processing is complete, accurate, timely, authorized -- live-verified function execution. |
| 25 | `multi-project-tenancy-verified` | Security | CC6 | Tenant isolation is an access-control objective. |
| 25 | `multi-project-tenancy-verified` | Confidentiality | C1.2 | Cross-tenant data isolation as a protection mechanism. |
| 26 | `audit-log-durable-and-queryable` | Security | CC7 | System operations -- durable, queryable audit trail. |
| 27 | `iac-export-reappliable-and-drift-detected` | Security | CC8 | Change management -- drift detection against declared state. |
| 28 | `status-page-slo-reflects-real-state` | Availability | A1.1 | Availability commitment reporting reflecting real state. |
| 29 | `webhook-delivery-verified-with-valid-signature` | Processing Integrity | PI1.3 | Delivery correctness and authorization (signature validation). |
| 29 | `webhook-delivery-verified-with-valid-signature` | Security | CC6 | Signature validation is an access/authenticity control. |
| 30 | `api-key-auth-enforces-bound-role` | Security | CC6 | Logical access control, least privilege bound to a role. |
| 31 | `network-topology-matches-real-enforcement` | Security | CC6 | Verifies displayed access-control state matches real enforcement (supports #2's evidentiary integrity). |
| 32 | `usage-billing-math-verified-real` | Processing Integrity | PI1.3 | Processing (billing computation) verified complete, accurate. |
| 33 | `scheduled-job-fires-on-real-schedule` | Processing Integrity | PI1.3 | Processing is timely -- live-verified schedule adherence. |
| 34 | `canary-traffic-split-measured-real` | Availability | A1.2 | Capacity/traffic management verified against real measurement. |
| 35 | `global-search-finds-real-cross-resource-matches` | Not mapped | -- | Product feature-correctness control (search relevance); no TSC objective it defensibly supports without stretching. |
| 36 | `mtls-gated-route-rejects-untrusted-clients` | Security | CC6 | Logical access control -- untrusted-client rejection. |
| 37 | `realtime-notification-pushed-not-polled` | Not mapped | -- | Delivery-mechanism/UX control (push vs. poll), not a control objective under any TSC category. |
| 38 | `disaster-recovery-runbook-tested` | Availability | A1.3 | Tested recovery procedure. |
| 39 | `quickstart-script-runs-clean-end-to-end` | Not mapped | -- | Developer-experience/onboarding verification; not a control objective under any TSC category. |
| 40 | `container-exec-output-matches-kubectl` | Processing Integrity | PI1.3 | Verifies platform-reported output matches ground truth (accuracy). |
| 41 | `batch-job-parallel-fanout-verified` | Processing Integrity | PI1.3 | Processing completeness under parallel execution. |
| 42 | `schema-migration-transactional-and-reversible` | Processing Integrity | PI1.5 | Storage/processing integrity -- transactional, reversible migration. |
| 43 | `audit-export-valid-ndjson-matches-source` | Security | CC7 | Audit-trail export integrity supporting system operations monitoring. |
| 44 | `custom-domain-tls-cert-matches-hostname` | Security | CC6 | Access-control/authenticity via correct certificate binding. |
| 44 | `custom-domain-tls-cert-matches-hostname` | Confidentiality | C1.2 | TLS as a data-in-transit protection mechanism. |
| 45 | `resource-tagging-filter-matches-real-label-selector` | Not mapped | -- | UI-filter/data-fidelity control; supports operational usability, not a distinct TSC control objective. |
| 46 | `budget-alert-fires-once-on-real-threshold-crossing` | Processing Integrity | PI1.3 | Alert processing correctness (fires once, on real threshold). |
| 47 | `session-revocation-enforced-before-jwt-expiry` | Security | CC6 | Logical access control -- session/credential lifecycle. |
| 48 | `certificate-rotation-zero-downtime-verified` | Security | CC6 | Credential/certificate lifecycle management. |
| 48 | `certificate-rotation-zero-downtime-verified` | Availability | A1.2 | Zero-downtime rotation supports availability during a maintenance operation. |
| 49 | `admission-policy-rejects-noncompliant-deployment` | Security | CC8 | Change management -- policy gate on deployments. |
| 50 | `vulnerability-scan-detects-real-findings-in-control-image` | Security | CC3 | Risk assessment -- vulnerability detection. |
| 51 | `external-oidc-federation-verified-real-signature` | Security | CC6 | Logical access control -- verified external identity signature. |
| 52 | `dashboard-widgets-render-live-not-stale-data` | Security | CC4 | Monitoring activities -- dashboard data freshness supports effective monitoring. |
| 53 | `isoflow-view-matches-deckgl-view-node-count` | Not mapped | -- | Internal UI cross-consistency check between two visualization surfaces; not a distinct TSC control objective. |
| 54 | `pod-security-admission-enforced` | Security | CC6 | Logical (and workload) access control enforcement. |
| 55 | `secrets-encrypted-at-rest-in-etcd` | Confidentiality | C1.2 | Data-at-rest protection mechanism. |
| 55 | `secrets-encrypted-at-rest-in-etcd` | Security | CC6 | Access control over encrypted secret material. |
| 56 | `vuln-scan-critical-admission-gate` | Security | CC3 | Risk assessment -- admission gate on critical findings. |
| 57 | `platform-console-namespace-podsecurity-restricted` | Security | CC6 | Access/workload control enforcement on the platform's own namespace. |
| 58 | `audit-log-tamper-evident-hash-chain` | Security | CC7 | System operations -- tamper-evident audit trail. |
| 59 | `castle-deploy-run-sunset-lifecycle-real-jobs` | Security | CC8 | Change management -- deploy/run/sunset lifecycle control. |
| 60 | `storage-signed-url-expiry-enforced` | Security | CC6 | Time-bound access control on stored objects. |
| 60 | `storage-signed-url-expiry-enforced` | Confidentiality | C1.2 | Expiring access as a protection mechanism. |
| 61 | `audit-log-tamper-evident-hash-chain` (duplicate control name; see note below) | Security | CC7 | Same rationale as #58. |
| 62 | `managed-cache-provisioned-and-reachable` | Availability | A1.1 | Live-verified service availability. |
| 63 | `managed-queue-provisioned-and-reachable` | Availability | A1.1 | Live-verified service availability. |

## Coverage summary

- **63** controls in the evidence bundle, **62** distinct control names (`audit-log-tamper-evident-hash-chain`
  appears twice at indices 58 and 61 in `evidence/control-evidence-bundle.json` -- both entries
  carry distinct evidence text and `observed_at` timestamps, so both are mapped identically here
  rather than silently dropped; this duplication is noted as-is and not resolved by this
  document, which only maps controls, it does not alter the evidence bundle's contents).
- **54** controls carry at least one TSC mapping; **9** are marked **Not mapped**
  (`feature-flag-live-toggle-verified`, `topology-visualization-real-data`,
  `global-search-finds-real-cross-resource-matches`, `realtime-notification-pushed-not-polled`,
  `quickstart-script-runs-clean-end-to-end`, `resource-tagging-filter-matches-real-label-selector`,
  `isoflow-view-matches-deckgl-view-node-count`) -- 7 unique names, all product/UX/dev-experience
  verifications rather than control objectives under any TSC category.
- By category (counting a control once per row it appears in, since several controls
  legitimately span more than one category): **Security** dominates (expected -- it is the
  mandatory Common Criteria category and this platform's control set is majority
  access-control/change-management/monitoring in nature), followed by **Availability**,
  **Processing Integrity**, and **Confidentiality**. **Privacy** has zero mappings: this
  platform's evidenced controls do not touch personal-data notice, consent, collection, or
  disclosure lifecycle (see `docs/SCOPE-AND-LIMITATIONS.md`) -- Privacy is out of scope for
  this control set the same way `ggen-marketplace/packs/soc2-audit-pack/ontology.ttl` notes
  Processing Integrity and Privacy were out of scope for its own Stage 1 case study before a
  later rescale brought them in.

## What this mapping cannot substitute for

- **No operating-effectiveness testing over a period.** Every control here is evidenced as
  observed-once-at-a-point-in-time (`observed_at` per control in the bundle), consistent
  with `evidence/control-evidence-bundle.json`'s own framing. SOC2 Type II requires testing
  across an observation window (typically 3-12 months); this bundle and this mapping are
  Type-I-shaped at best, and neither bundle nor mapping have been reviewed by an auditor.
- **No control-design review by a qualified assessor.** The TSC-category assignments above
  are this platform's own good-faith reading of `ggen-marketplace/packs/soc2-audit-pack`'s
  reference doctrine, not a reviewed mapping.
- **No coverage claim beyond what is evidenced.** Where a control has no defensible mapping
  it is marked Not mapped rather than assigned a plausible-sounding category -- consistent
  with `evidence/control-evidence-bundle.json`'s existing disclaimer and
  `docs/SCOPE-AND-LIMITATIONS.md`'s existing per-module honesty convention.

## See also

- `evidence/control-evidence-bundle.json` -- the underlying 63-control evidence bundle this
  document maps, including its own disclaimer and blake3 digest.
- `docs/SCOPE-AND-LIMITATIONS.md` -- the honest, module-by-module counterpart to
  platform-wide claims (single control-plane node, single-machine deployment, no customer
  SLA, and other limitations that bound what any SOC2 conversation grounded in this platform
  can claim).
- `ggen-marketplace/packs/soc2-audit-pack/ontology.ttl` -- the reference TSC/Common Criteria
  doctrine this mapping is built against.
- `SONY-READINESS-GAP-CLOSURE.md` -- records this mapping as the closure of the "no SOC2/ISO
  control mapping" item on its "Still Open" list.
