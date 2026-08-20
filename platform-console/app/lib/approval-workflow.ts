/**
 * Real role-based multi-party (maker-checker) approval workflow for
 * high-risk provisioning actions -- the specific human-in-the-loop
 * control SOC2/ISO27001 auditors and enterprise security review
 * checklists ask for by name that this repo did not previously provide.
 * lib/authz.ts gates by a single actor's OWN role rank (an owner can act
 * entirely alone); lib/policy.ts is read-only; lib/quota-enforcement.ts
 * enforces automatically. None of the three ever requires a SECOND,
 * DISTINCT human identity to sign off before a destructive or
 * money-moving action executes. This module adds exactly that, as a real
 * gate a guarded route handler calls BEFORE performing the action -- not
 * a UI-only affordance.
 *
 * Storage: one real k8s ConfigMap (`platform-console-approvals`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo (lib/authz.ts,
 * lib/budget-alerts.ts, lib/orgs.ts) already uses -- no new k8s resource
 * kind, no new RBAC verb: the same `platform-console-feature-flags` Role
 * already grants get/list/create/update/patch on `configmaps` in this
 * namespace with no `resourceNames` restriction.
 *
 * Key shape: one key per approval request, `requestId` (a
 * `crypto.randomUUID()`) -> JSON ApprovalRequest. A k8s ConfigMap `data`
 * key must match `[-._a-zA-Z0-9]+` -- a UUID already satisfies that, so
 * no escaping step like lib/authz.ts's encodeIdentifierKey is ever
 * needed here.
 *
 * Two-person integrity is enforced at TWO points, neither of which trusts
 * the client:
 *   1. recordApprovalDecision refuses (403, enforced by the caller) a
 *      decision from the same identifier that created the request --
 *      approver !== requester is checked against the REQUEST'S OWN
 *      stored `requestedBy`, never a client-supplied claim.
 *   2. findApprovedRequest only matches rows with status "approved" AND
 *      approvedAt within the last APPROVAL_TTL_HOURS hours -- a stale
 *      approval (or one for a different target) can never silently
 *      satisfy a new attempt at the guarded action.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { ProjectTier } from "@/lib/tiers";
import type { Environment } from "@/lib/environments";
import type { SsoGroupRoleMapping } from "@/lib/sso-role-mapping";
import type { SubprocessorChangeAction, SubprocessorRecord } from "@/lib/subprocessors";
import type { CmekProvider } from "@/lib/orgs";

export const APPROVALS_NAMESPACE = "platform-console";
export const APPROVALS_CONFIGMAP = "platform-console-approvals";

// Freshness window an approval remains valid for after being granted --
// same "trailing window" discipline lib/budget-alerts.ts's
// BUDGET_WINDOW_HOURS documents: a 24h-old "approved" no longer proves
// the second approver would still say yes to retrying the SAME action
// today, so it must not silently authorize it.
export const APPROVAL_TTL_HOURS = 24;

export type ApprovalAction =
  | "org.delete"
  | "quota.override"
  | "tier.downgrade"
  | "backup.retention.change"
  | "export-subscription.update"
  | "dr.failover"
  | "dsar.erasure"
  | "castle.verb.schedule"
  | "freeze.override"
  | "environment.promote"
  | "deployment.quarantine"
  | "sla.credit.apply"
  | "patch-sla.credit.apply"
  | "k8s-fault.remediate-suggest"
  | "pricing.override"
  | "invoice.reconciliation.approve"
  | "sso.role-mapping.update"
  | "compliance.rotation-block"
  | "break-glass.justification-review"
  | "subprocessor.registry.update"
  | "cmek.key-binding"
  | "le-request.respond"
  | "data-destruction.certificate.issue"
  | "denied-party.override"
  | "change-of-control.notify"
  | "insurance.policy.update"
  | "personnel.attestation.record"
  | "source-escrow.snapshot"
  | "pentest.finding.resolve"
  | "vendor-offboarding.attestation.issue"
  | "legal-hold.release"
  | "geofence.exception.grant";
export const ACTIONS_REQUIRING_APPROVAL: ApprovalAction[] = [
  "org.delete",
  "quota.override",
  "tier.downgrade",
  "backup.retention.change",
  // A K8s Fault Diagnosis finding (lib/k8s-fault-scan.ts, wrapping
  // autofde-lab's real structural-anomaly scanner) that plausibly
  // warrants an actuated fix (e.g. a `declared_vs_observed` replica-count
  // anomaly on a live Deployment) files THIS action -- never a
  // remediation itself. The underlying scanner diagnoses only; no code
  // path anywhere produces a remediation plan, so this is deliberately
  // named "remediate-suggest", not "remediate" -- a second human still
  // has to approve it, and approving it here authorizes nothing beyond
  // "a human agreed the suggestion is worth acting on manually," same
  // "auto-FILE, human approves" pattern `deployment.quarantine` already
  // establishes for vuln-scan findings.
  "k8s-fault.remediate-suggest",
  // A scheduled export subscription is a real, standing data-
  // exfiltration control: once saved, it recurringly ships this org's
  // audit log or full export bundle to a bucket a THIRD PARTY (the
  // customer's own SIEM/data-lake pipeline) controls, completely
  // unattended. That is exactly the "can quietly move data out of the
  // platform on an ongoing basis" class of change org.delete's own
  // header comment already documents the bar for -- one owner acting
  // alone (lib/authz.ts's requireRoleIn) is not sufficient; a second,
  // distinct owner-role approver must sign off before bucket
  // credentials + schedule are ever accepted.
  "export-subscription.update",
  // Multi-region DR failover: re-pins an org's real data-residency region
  // AND triggers a real destructive restore Job that overwrites the
  // target database Pod's live table data (lib/k8s.ts's createRestoreJob
  // header comment) -- the same "destructive, high-blast-radius,
  // requires a second distinct human" bar org.delete already sets. See
  // lib/dr-failover.ts.
  "dr.failover",
  // GDPR Art.17 / CCPA erasure: redacts a real data subject's identity
  // out of the durable audit trail and their per-org membership record.
  // Irreversible (a redacted actor value cannot be un-redacted -- the
  // original email is gone, by design) and, unlike a plain access
  // export, changes durable state -- the same "irreversible,
  // destructive, one owner acting alone is not enough" bar org.delete
  // and dr.failover already set. See lib/dsar.ts.
  "dsar.erasure",
  // Maintenance-Window-Gated Castle Verb Scheduling
  // (lib/scheduled-verbs.ts): scheduleCastleVerb queues a real castle
  // actuation verb (a real batch/v1 Job -- see lib/castle.ts's
  // runCastleVerb) to run unattended, later, inside a pre-announced
  // maintenance window, with no human present to review the actual
  // moment it fires. That is exactly the "can execute later, unattended,
  // with no one watching" class of risk org.delete and dr.failover's own
  // header comments already set the bar for -- the requester's own
  // maker-checker sign-off is not sufficient; a second, distinct
  // owner-role approver must sign off BEFORE the entry is ever eligible
  // for the poller to run it, same as every other action in this list.
  "castle.verb.schedule",
  // Declared change-freeze window override (lib/freeze-windows.ts, ITIL
  // / SOC2 CC8 change-management control): a freeze window whose
  // `allowEmergencyOverride` is true lets a mutating action (a castle
  // verb Run, a project tier change, a quota patch) still execute during
  // the window, but only after a SECOND, distinct owner-role approver
  // signs off on breaking a freeze the org itself declared -- the
  // requester's own judgment that "this is an emergency" is not
  // sufficient by itself, same maker-checker bar every other action in
  // this list sets. A freeze window with `allowEmergencyOverride: false`
  // never reaches this at all -- checkFreezeGuard refuses to create an
  // override request for it, it is a hard block.
  "freeze.override",
  // Environment-promotion pipeline (dev -> staging -> prod, SOC2 CC8
  // change-management control -- the same family as the freeze windows
  // just above): moving a Project's ENVIRONMENT_LABEL forward a stage is
  // exactly the "deploy artifact X from staging to prod" moment a
  // regulated buyer's procurement checklist requires a second, distinct
  // approver for -- the requester's own judgment that a promotion is
  // ready is not sufficient by itself, same maker-checker bar every other
  // action in this list sets. See app/api/projects/[name]/promote/route.ts.
  "environment.promote",
  // Vulnerability-scan-triggered auto-remediation
  // (app/api/security-scan/auto-remediate/route.ts): a CRITICAL-severity
  // Trivy finding (lib/vuln-scan.ts) tied to a live `apps/v1` Deployment
  // in a customer org's namespace can request that Deployment be
  // quarantined -- scaled to 0 replicas via lib/k8s.ts's
  // quarantineDeployment, the same real, cluster-observable action
  // quota-enforcement's scale-to-zero already performs. This is exactly
  // the "can take a live customer workload down, automatically, off a
  // scanner's own verdict" class of blast radius org.delete and
  // dr.failover's own header comments set the bar for -- an automated
  // scan result is never sufficient by itself to actuate; a second,
  // distinct owner-role approver must sign off before the Deployment is
  // ever actually scaled down, same maker-checker bar every other action
  // in this list sets. Auto-filing the REQUEST (never the action itself)
  // is additionally gated per-org behind `Org.autoRemediateCritical`
  // (lib/orgs.ts, default `false`) so this never files uninvited on an
  // existing customer.
  "deployment.quarantine",
  // SLA credit auto-application to Stripe customer balance
  // (POST /api/orgs/[id]/sla-credits, lib/stripe-billing.ts's
  // applySlaCreditToStripeBalance): the single action in this codebase
  // that moves real money OFF a customer's Stripe balance/next invoice
  // with no human review of the exact dollar amount first -- the same
  // "can quietly move money/data on an ongoing or one-shot basis" class
  // of blast radius `export-subscription.update` and the overage-billing
  // path already require a second human for. Unlike `deployment
  // .quarantine`'s per-org opt-in gate, this one has NO opt-out: any
  // owner filing the request still requires a second, distinct owner to
  // sign off before Stripe is ever called, same maker-checker bar every
  // other money-moving or destructive action in this list sets. `targetId`
  // on the ApprovalRequest itself is the org's own id; see
  // `requestedSlaCreditMonth` on ApprovalResourcePayload below for the
  // month a second approver actually reviews before signing off.
  "sla.credit.apply",
  // Real Contractual Patch-Timeliness SLA Tier (CVE Remediation Credits,
  // lib/patch-sla.ts / POST /api/orgs/[id]/patch-sla-credits): the exact
  // same "moves real money off a customer's Stripe balance with no
  // per-transaction human review of the amount" blast radius as
  // `sla.credit.apply` immediately above -- reuses
  // applySlaCreditToStripeBalance wholesale, so it earns the identical
  // maker-checker bar, no opt-out.
  "patch-sla.credit.apply",
  // Per-org negotiated pricing/discount-schedule override
  // (PUT /api/orgs/[id]/pricing-override, lib/orgs.ts's
  // setOrgPricingOverride): binds a real, signed-contract negotiated
  // rate that lib/overage-billing.ts's rate computation and future
  // Stripe invoicing will apply IN PLACE OF the standard tiers.ts list
  // price for this org, going forward and until it expires -- exactly
  // the "can quietly move real money on an ongoing basis" class of blast
  // radius `sla.credit.apply`/`export-subscription.update` already earn
  // this bar for. The requester's own assertion that a contract was
  // signed is not sufficient by itself; a second, distinct owner-role
  // approver must sign off before the negotiated rate is ever bound,
  // same maker-checker bar every other money-moving action in this list
  // sets. No opt-out, same as `sla.credit.apply`.
  "pricing.override",
  // Invoice / Purchase-Order Reconciliation Ledger
  // (POST /api/orgs/[id]/invoice-reconciliation, lib/invoice-reconciliation.ts):
  // approving a reconciliation record is the exact signal finance/
  // procurement uses to release payment against a real Stripe-derived
  // overage invoice -- the same "authorizes a real dollar amount to move"
  // class of risk `sla.credit.apply`/`patch-sla.credit.apply` already earn
  // this bar for (those move money OFF a customer's balance; this one
  // clears money TO be collected FROM the customer, but the underlying
  // risk -- one person's own say-so binding a real invoiced amount with no
  // independent check -- is identical). The requester (whoever filed the
  // reconciliation, reading the customer's submitted PO number and
  // contract cap against lib/overage-billing.ts's own real StoredOverage
  // record) is never sufficient alone; a second, distinct owner-role
  // approver must sign off before the record is marked
  // `"approved_for_payment"`. No opt-out, same as `sla.credit.apply`.
  "invoice.reconciliation.approve",
  // SSO/SCIM Role-Mapping update (PUT /api/orgs/[id]/sso-role-mapping,
  // lib/orgs.ts's setOrgSsoGroupMappings): binds the org's own declared
  // SSO group -> app role intent, the exact record GET
  // /api/orgs/[id]/sso-role-drift diffs against real assigned roles to
  // decide who is over-privileged or orphaned -- silently widening this
  // mapping (e.g. quietly pointing a broad IdP group at "owner") is
  // exactly the "can quietly grant elevated privilege on an ongoing
  // basis" class of risk `roles.manage`-gated actions already carry, and
  // an incorrect mapping directly undermines the security-review-board
  // evidence this whole capability exists to produce. The requester's
  // own say-so is not sufficient by itself; a second, distinct
  // owner-role approver must sign off before the new mapping set is
  // ever bound, same maker-checker bar every other privilege-governing
  // action in this list sets. No opt-out.
  "sso.role-mapping.update",
  // Secret & Certificate Rotation Compliance Enforcement
  // (POST/DELETE /api/compliance/rotation, lib/rotation-compliance.ts):
  // flags an org whose real, live k8s Secrets or TLS certificates
  // (lib/k8s.ts's listSecrets / lib/cert-lifecycle.ts's
  // listManagedCertificates) have exceeded ROTATION_SLA_DAYS without
  // being rotated -- the exact SOC2 CC6.1 / PCI-DSS 3.6.4 rotation-
  // cadence control a Fortune-5 security review asks for evidence of --
  // and BLOCKS that org (`Org.rotationComplianceBlocked`,
  // lib/orgs.ts's setOrgRotationComplianceBlock) once approved. This is
  // the same "can quietly restrict a live customer's own service" class
  // of blast radius `deployment.quarantine` already earns this bar for
  // (a blocked org's own operators see the violation and the block, but
  // cannot self-clear it), just triggered by a stale-rotation finding
  // instead of a CVE scan. The scan itself (scanRotationCompliance) never
  // actuates a block by itself; a second, distinct owner-role approver
  // must sign off before `rotationComplianceBlocked` is ever flipped,
  // same maker-checker bar every other action in this list sets.
  // `resourcePayload.requestedRotationBlock: null` requests CLEARING an
  // existing block (an org whose secrets/certs have since been rotated),
  // same null-clears convention `pricing.override` already establishes.
  "compliance.rotation-block",
  // Sub-processor Registry (lib/subprocessors.ts, POST/PUT/DELETE
  // /api/subprocessors[/[id]]): the platform's own declared list of WHO
  // processes every customer's personal data (cloud regions, third-party
  // services) -- the exact list an enterprise DPA's own Schedule requires
  // and GDPR Art. 28(2) requires affected orgs be notified of any change
  // to. Adding, updating, or removing an entry is exactly the "can
  // quietly widen or narrow a real compliance/security posture on an
  // ongoing basis, with every customer org auto-notified of the result"
  // class of risk `pricing.override`/`sso.role-mapping.update` already
  // earn this bar for -- one owner's own say-so is not sufficient by
  // itself; a second, distinct owner-role approver must sign off before
  // the registry ever changes or a notification is ever sent. No
  // opt-out. `targetId` on the ApprovalRequest itself is the
  // sub-processor's own id.
  "subprocessor.registry.update",
  // Break-Glass Emergency Access post-hoc justification review
  // (lib/break-glass.ts's fileBreakGlassJustification, POST
  // /api/orgs/[id]/break-glass/[grantId]/justify): break-glass grants are
  // deliberately opened WITHOUT going through this same maker-checker gate
  // -- an active incident cannot wait on a second approver -- so this
  // action is the compensating control that runs on the BACK end instead:
  // once the on-call engineer's grant has ended, THEY file the mandatory
  // justification, and a second, distinct owner-role approver must review
  // and countersign it, same two-person-integrity bar every other action
  // in this list sets, just moved from before the action to after it.
  // `targetId` on the ApprovalRequest itself is the break-glass grant's own
  // id (`BreakGlassGrant.id`).
  "break-glass.justification-review",
  // Customer-Managed Encryption Key (CMEK/BYOK) binding
  // (PUT/DELETE /api/orgs/[id]/cmek, lib/orgs.ts's setOrgCmekBinding): binds
  // or rotates the real external KMS key reference (AWS KMS/GCP Cloud KMS/
  // Azure Key Vault/Vault) an org's live Secrets/PVCs are annotated as being
  // protected under -- the specific control a Fortune 5 security review
  // asks for before this platform is trusted to store regulated data,
  // because it moves the ability to revoke access to a customer's own data
  // at rest from the platform vendor to the customer. This is exactly the
  // "can quietly change a live customer org's own security/compliance
  // posture on an ongoing basis" class of risk `compliance.rotation-block`/
  // `pricing.override` already earn this bar for -- one owner's own say-so
  // that a customer key should be bound (or that an existing binding should
  // be cleared, reverting the org to the platform's shared default
  // encryption key) is never sufficient by itself; a second, distinct
  // owner-role approver must sign off before lib/orgs.ts's
  // setOrgCmekBinding is ever called and before lib/cmek.ts ever
  // re-annotates a single live Secret or PVC. No opt-out. `targetId` on the
  // ApprovalRequest itself is the org's own id.
  "cmek.key-binding",
  // Law-Enforcement / Government Data Request register response
  // (PUT /api/owner/le-requests, lib/le-requests.ts's
  // recordLeRequestResponse): recording that this platform actually
  // DISCLOSED customer data to a government/law-enforcement requester (or
  // narrowed/objected/rejected the demand) is the exact "a single
  // compromised or coerced employee could quietly hand over customer
  // data, or quietly under-report having done so" class of risk
  // `dsar.erasure`/`subprocessor.registry.update` already earn this bar
  // for -- one owner's own say-so that a disclosure was warranted is
  // never sufficient by itself; a second, distinct owner-role approver
  // must sign off before the register's response is ever recorded. No
  // opt-out. `targetId` on the ApprovalRequest itself is the LeRequest's
  // own id (`LeRequest.requestId`, lib/le-requests.ts). Logging that a
  // request was RECEIVED is a separate, non-sensitive action
  // (POST /api/internal/le-requests) and is deliberately NOT gated here
  // -- see lib/le-requests.ts's own header comment for why.
  "le-request.respond",
  // Certificate of Data Destruction (POST /api/owner/data-destruction,
  // lib/data-destruction-certificate.ts's issueDataDestructionCertificate):
  // the signed, timestamped artifact finance/legal/security hand a
  // Fortune-5 customer at contract termination proving every real piece
  // of that org's infrastructure -- PVCs, backups -- was actually torn
  // down per contractual retention terms. This is exactly the "one
  // person's own say-so binds a durable, externally-relied-upon
  // compliance attestation" class of risk `compliance.rotation-block`/
  // `subprocessor.registry.update` already earn this bar for: the
  // requester's own live verification read is never sufficient by
  // itself to mint the certificate; a second, distinct owner-role
  // approver must sign off before it is issued. No opt-out. `targetId`
  // on the ApprovalRequest itself is the org's own id.
  "data-destruction.certificate.issue",
  // Denied-Party / Export-Control Screening Register override
  // (PUT /api/owner/[orgId]/denied-party-screening,
  // lib/denied-party-screening.ts's recordScreeningOverride): a real
  // "potential_match" screening result -- an org admin, billing
  // contact, or named technical contact's name matched an entry on this
  // platform's own maintained denied-party list -- is exactly the "one
  // person's own say-so binds a durable, externally-relied-upon
  // compliance determination" class of risk `compliance.rotation-block`/
  // `data-destruction.certificate.issue` already earn this bar for: the
  // requester who ran the screening is never sufficient alone to decide
  // a match was a false positive and clear the org to proceed; a
  // second, distinct owner-role approver must sign off before the
  // override is ever recorded. No opt-out. `targetId` on the
  // ApprovalRequest itself is the screening record's own id
  // (`ScreeningRecord.id`).
  "denied-party.override",
  // Change-of-Control / M&A Notification Register
  // (PUT /api/owner/change-of-control, lib/change-of-control-
  // notifications.ts's recordOrgNotification): the durable compliance
  // ledger row Fortune 5 customers' own legal teams rely on to prove
  // their MSA's contractual "notify within N days of an acquisition,
  // merger, or change of ownership" clause was actually honored. This is
  // exactly the "one person's own say-so binds a durable, externally-
  // relied-upon compliance attestation" class of risk `data-destruction
  // .certificate.issue`/`denied-party.override` already earn this bar
  // for: the requester's own claim that notice was sent is never
  // sufficient by itself to record it in this ledger; a second, distinct
  // owner-role approver must sign off before the notification row is
  // ever written. No opt-out. `targetId` on the ApprovalRequest itself
  // is `<triggerId>.<orgId>`, matching the notification row's own id.
  "change-of-control.notify",
  // Certificate of Insurance (COI) policy metadata (PUT
  // /api/owner/insurance-attestation, lib/insurance-attestation.ts's
  // recordInsurancePolicyVersion): the carrier/policy-number/coverage-
  // limit/expiry facts this platform attests to a Fortune-5 counterparty
  // in a generated COI PDF -- exactly the "one person's own say-so binds
  // a durable, externally-relied-upon compliance claim" class of risk
  // `denied-party.override`/`subprocessor.registry.update` already earn
  // this bar for: a single owner unilaterally widening a declared
  // coverage limit or silently shortening an expiry is never acceptable
  // on one person's own say-so. No opt-out. `targetId` on the
  // ApprovalRequest itself is the coverage type
  // (`InsuranceCoverageType`).
  "insurance.policy.update",
  "personnel.attestation.record",
  // Source-Code / Build-Artifact Escrow Attestation
  // (POST /api/compliance/source-escrow, lib/source-escrow-
  // attestation.ts's requestSourceEscrowSnapshot): mints a signed,
  // durable in-toto-style statement over the exact git commit SHA,
  // manifest set (real Deployments + Flux Kustomizations/HelmReleases),
  // and runtime-resolved image digests currently deployed -- the
  // business-continuity/vendor-lock-in escrow artifact a Fortune-5
  // legal team's MSA clause points to as proof this platform could
  // hand over exactly what was running. This is exactly the "one
  // person's own say-so binds a durable, externally-relied-upon
  // compliance attestation" class of risk `data-destruction
  // .certificate.issue`/`insurance.policy.update` already earn this bar
  // for: the requester's own live cluster read is never sufficient by
  // itself to sign and persist a record legal will later rely on; a
  // second, distinct owner-role approver must sign off before it is
  // ever signed or stored. No opt-out. `targetId` on the
  // ApprovalRequest itself is the manifest namespace (always
  // `platform-console` today -- this platform's own release, not a
  // per-customer-org artifact).
  "source-escrow.snapshot",
  // Third-Party Penetration-Test Attestation Register (PUT
  // /api/compliance/pentest/[findingId], lib/pentest-attestation.ts's
  // resolveFinding): marking a real filed pentest finding
  // `resolved`/`accepted_risk` is exactly the "one person's own say-so
  // binds a durable, externally-relied-upon compliance attestation"
  // class of risk `compliance.rotation-block`/`data-destruction
  // .certificate.issue`/`source-escrow.snapshot` already earn this bar
  // for -- the requester who believes a fix landed is never sufficient
  // alone to close the finding a Fortune-5 security reviewer will later
  // cite as evidence the vulnerability was actually remediated; a
  // second, distinct owner-role approver must sign off before the
  // register's own status can move to a terminal state. Filing a NEW
  // engagement or finding is deliberately NOT gated here (see
  // lib/pentest-attestation.ts's own header comment) -- only closing the
  // loop is. No opt-out. `targetId` on the ApprovalRequest itself is the
  // finding's own id (`PentestFinding.id`).
  "pentest.finding.resolve",
  // Vendor Offboarding Data-Return/Destruction Attestation: the signed,
  // timestamped document handed to a Fortune-5 customer's procurement/
  // legal team at contract termination, attesting every piece of their
  // data was either exported back to them or destroyed within the
  // contractual SLA. Same "durable compliance artifact a counterparty
  // relies on" bar `data-destruction.certificate.issue`/
  // `insurance.policy.update` already set -- one platform owner's own
  // say-so is never sufficient by itself to hand a customer a signed
  // attestation closing their offboarding checklist. No opt-out.
  // `targetId` on the ApprovalRequest itself is the org's own id.
  "vendor-offboarding.attestation.issue",
  // Legal Hold RELEASE (lib/legal-hold.ts): lifting a hold is what
  // RESUMES eligibility for the scheduled retention purge and DSAR
  // erasure to actually destroy data in the released scope -- the exact
  // "resumes an irreversible, destructive automated action" moment
  // `dsar.erasure`/`dr.failover` already earn this bar for. Deliberately
  // asymmetric with PLACING a hold, which is never gated (see
  // lib/legal-hold.ts's header comment) -- a legal team member acting
  // alone must always be able to stop destruction immediately; only
  // resuming it requires a second, distinct owner-role approver. No
  // opt-out. `targetId` on the ApprovalRequest itself is the hold's own
  // id (`LegalHold.holdId`).
  "legal-hold.release",
  // Geofenced Data-Residency Access Enforcement exception
  // (lib/geofence-enforcement.ts's applyGeofenceException, POST
  // /api/owner/geofence-policy): a bounded-TTL carve-out letting one
  // named identifier or IP CIDR bypass an org's own contracted-region
  // geofence policy -- exactly the "one person's own say-so quietly
  // widens a live customer org's own security/compliance posture" class
  // of risk `cmek.key-binding`/`compliance.rotation-block` already earn
  // this bar for: the requester's own judgment that an exception is
  // warranted (e.g. a support engineer traveling outside the contracted
  // region) is never sufficient by itself; a second, distinct owner-role
  // approver must sign off before the exception is ever recorded and
  // starts bypassing enforcement. No opt-out. `targetId` on the
  // ApprovalRequest itself is the org's own id.
  "geofence.exception.grant",
];

export type ApprovalStatus = "pending" | "approved" | "rejected";

/**
 * Real, action-specific detail carried alongside the generic
 * requester/target/status fields every ApprovalRequest already had --
 * lets an approver see WHAT they're signing off on (the exact new quota
 * ceiling, or the exact tier the org would move to) instead of just an
 * opaque targetId. Optional and additive: `org.delete` (the original
 * guarded action) sets neither field and round-trips through
 * JSON.parse/stringify unchanged, same forward-compatible-optional-field
 * discipline lib/orgs.ts's OrgBranding/region fields already establish.
 */
export interface ApprovalResourcePayload {
  /** quota.override: the requested `ResourceQuota.spec.hard` map --
   * same key shape (`pods`, `requests.cpu`, `limits.memory`, ...)
   * lib/tiers.ts's resourceQuotaHardFor/lib/k8s.ts's patchResourceQuotaHard
   * already use. */
  requestedHard?: Record<string, string>;
  /** tier.downgrade: the tier the Project would move to once approved. */
  requestedTier?: ProjectTier;
  /** backup.retention.change: the retention window (in days) the org's
   * backup policy would move to once approved. */
  requestedRetentionDays?: number;
  /** export-subscription.update: the non-secret shape of the requested
   * bucket subscription -- bucket endpoint/name/prefix/cadence/scope --
   * so a second approver can see WHERE this org's data would be shipped
   * and how often before signing off. Deliberately excludes the access
   * key id and secret access key: an approval request row lives in the
   * same platform-console-approvals ConfigMap every other approval type
   * does, and credential material must never be readable there even in
   * transit through a pending approval -- lib/s3-export-subscription.ts's
   * own encrypted-at-rest storage is the only place those two fields are
   * ever persisted. */
  requestedExportSubscription?: {
    bucketEndpoint: string;
    bucketName: string;
    prefix: string;
    cadence: string;
    scope: string;
    enabled: boolean;
  };
  /** dr.failover: the non-secret shape of the requested failover -- which
   * region this org would move FROM/TO and the human-supplied reason --
   * so a second approver can see exactly what they're authorizing before
   * signing off on a destructive, live-data-overwriting restore. */
  requestedFailover?: {
    fromRegion: string;
    toRegion: string;
    reason: string;
  };
  /** castle.verb.schedule: the non-secret shape of the requested
   * scheduled castle verb -- which allowlisted verb, and the exact ISO
   * timestamp it is requested to fire at -- so a second approver can see
   * exactly what will run, and when, before signing off. `targetId` on
   * the ApprovalRequest itself is the ScheduledVerb's own id
   * (lib/scheduled-verbs.ts), not the verb id, so this is the field an
   * approver actually reads to know which castle verb is in play. */
  /** freeze.override: the non-secret shape of the freeze window being
   * overridden -- which window (by id) and its human-supplied reason --
   * so a second approver can see exactly which declared freeze they are
   * being asked to authorize breaking. */
  requestedFreezeId?: string;
  requestedFreezeReason?: string;
  requestedScheduledVerb?: {
    verbId: string;
    requestedFor: string;
  };
  /** environment.promote: the non-secret shape of the requested promotion
   * -- which environment the Project is moving FROM and TO -- so a second
   * approver can see exactly which stage transition they are authorizing
   * before signing off. `targetId` on the ApprovalRequest itself is the
   * Project's own name (lib/k8s.ts's SupabaseProject.name). */
  fromEnvironment?: Environment;
  targetEnvironment?: Environment;
  /** deployment.quarantine: the non-secret shape of the requested
   * quarantine -- which namespace/Deployment, which CVE triggered it, and
   * the scanned image ref -- so a second approver can see exactly what
   * they're authorizing before signing off on scaling a live customer
   * workload to 0. `targetId` on the ApprovalRequest itself is
   * `<namespace>/<deploymentName>`, matching lib/k8s.ts's
   * quarantineDeployment argument shape. */
  requestedQuarantine?: {
    namespace: string;
    deploymentName: string;
    cveId: string;
    imageRef: string;
    severity: string;
  };
  /** sla.credit.apply: the "YYYY-MM" month a real SLA credit is being
   * requested for, so a second approver can see exactly which month's
   * computed shortfall they are authorizing Stripe money to move
   * against -- before this route ever calls
   * lib/stripe-billing.ts's applySlaCreditToStripeBalance. */
  requestedSlaCreditMonth?: string;
  /** k8s-fault.remediate-suggest: the non-secret shape of the requested
   * fault-diagnosis-triggered suggestion -- which namespace/kind/object
   * the anomaly was found on, its relation class, the real SREGym
   * taxonomy label (or `UNCLASSIFIED`), and the scanner's own `detail`
   * string -- so a second approver can see exactly what was diagnosed
   * before agreeing a manual fix is warranted. `targetId` on the
   * ApprovalRequest itself is `<namespace>/<kind>/<objectName>/<field>`,
   * matching one anomaly key. Never a remediation plan: no field here
   * describes an actuated fix, because lib/k8s-fault-scan.ts's
   * underlying scanner produces none. */
  requestedFaultSuggestion?: {
    namespace: string;
    kind: string;
    objectName: string;
    field: string;
    relationClass: string;
    taxonomy: string;
    detail: string;
  };
  /** pricing.override: the non-secret shape of the requested negotiated
   * pricing override -- discount percent OR flat fixed unit price,
   * effective window, and the contract reference / approving identity
   * being asserted -- so a second approver can see the EXACT rate they
   * are authorizing before it is ever bound to this org's billing. Mirrors
   * `OrgPricingOverride` (lib/orgs.ts) field-for-field. `targetId` on the
   * ApprovalRequest itself is the org's own id. `null` requests clearing
   * (expiring) an existing override. */
  requestedPricingOverride?: {
    discountPercent?: number;
    fixedUnitPrice?: { cpuPerCoreHour: number; memoryPerGiBHour: number };
    effectiveFrom: string;
    effectiveUntil: string;
    contractRef: string;
    approvedBy: string;
  } | null;
  /** invoice.reconciliation.approve: the non-secret shape of the
   * reconciliation being approved -- the customer-submitted PO number,
   * the org's asserted contract cap, the real overage amount the
   * reconciliation was computed against (lib/overage-billing.ts's own
   * StoredOverage.overageCostUsd), and the resulting variance -- so a
   * second approver can see exactly which invoiced dollar amount they
   * are authorizing finance/procurement to collect before it is ever
   * marked payable. `targetId` on the ApprovalRequest itself is the
   * reconciliation's own id (`<orgId>.<namespace>.<periodStart>`). */
  requestedReconciliation?: {
    orgId: string;
    namespace: string;
    poNumber: string;
    contractCapUsd: number;
    overageCostUsd: number;
    varianceUsd: number;
    periodStart: string;
  };
  /** sso.role-mapping.update: the full requested SSO group -> role
   * mapping SET this org's owner is asking to bind, replacing whatever
   * mapping set (if any) exists today -- so a second approver can see
   * exactly which groups would grant which roles, including any newly
   * widened grant (e.g. a group newly pointed at `"owner"`), before it
   * is ever bound and starts governing GET
   * /api/orgs/[id]/sso-role-drift's own drift computation. `targetId`
   * on the ApprovalRequest itself is the org's own id. Mirrors
   * `SsoGroupRoleMapping[]` (lib/sso-role-mapping.ts) field-for-field. */
  requestedSsoGroupMappings?: SsoGroupRoleMapping[];
  /** compliance.rotation-block: the non-secret shape of the requested
   * rotation-SLA block -- which namespace, how many real Secrets/
   * certificates were found past `ROTATION_SLA_DAYS`, the single oldest
   * violation's age in days, and a human-readable reason -- so a second
   * approver can see exactly what triggered the block before signing off
   * on restricting a live customer org. `targetId` on the
   * ApprovalRequest itself is the org's own id.
   * `requestedRotationBlock: null` requests CLEARING an existing block
   * (the org's secrets/certs have since been rotated), same null-clears
   * convention `requestedPricingOverride` above establishes. */
  requestedRotationBlock?: {
    namespace: string;
    violationCount: number;
    oldestViolationAgeDays: number;
    reason: string;
  } | null;
  /** subprocessor.registry.update: the non-secret shape of the requested
   * sub-processor registry change -- which action (add/update/remove) and
   * the FULL proposed record (name, category, regions, purpose, data
   * categories) -- so a second approver can see exactly which
   * sub-processor entry would change, and how, before it is ever applied
   * and every org is auto-notified. `targetId` on the ApprovalRequest
   * itself is the sub-processor's own id. */
  requestedSubprocessorChange?: {
    action: SubprocessorChangeAction;
    record: SubprocessorRecord;
  };
  /** break-glass.justification-review: the non-secret shape of the
   * emergency-access grant being justified after the fact -- which org and
   * namespace were touched, the incident reason given when the grant was
   * OPENED, the on-call engineer's own post-hoc justification, and the
   * grant's real start/end timestamps -- so a second approver can see
   * exactly what happened, why, and for how long before countersigning
   * that the emergency access was warranted. `targetId` on the
   * ApprovalRequest itself is the break-glass grant's own id
   * (`BreakGlassGrant.id`, lib/break-glass.ts). */
  requestedBreakGlassJustification?: {
    targetOrgId: string;
    namespace: string;
    incidentReason: string;
    justification: string;
    grantStartedAt: string;
    grantEndedAt: string;
  };
  /** cmek.key-binding: the non-secret shape of the requested CMEK/BYOK key
   * binding or rotation -- which external KMS provider, the new key
   * reference (never key material), the key reference it would replace
   * (absent for an org's first-ever binding), and the human-supplied
   * justification -- so a second approver can see exactly which customer
   * key they are authorizing before it is ever bound and before any live
   * Secret/PVC is re-annotated. `targetId` on the ApprovalRequest itself is
   * the org's own id. `requestedCmekBinding: null` requests CLEARING an
   * existing binding (reverting to the platform default encryption key),
   * same null-clears convention `requestedPricingOverride`/
   * `requestedRotationBlock` above establish. */
  requestedCmekBinding?: {
    provider: CmekProvider;
    keyRef: string;
    previousKeyRef?: string;
    reason: string;
  } | null;
  /** le-request.respond: the non-secret shape of the requested register
   * response -- the real response status being recorded and a summary of
   * what was actually disclosed/narrowed/objected/rejected -- so a
   * second approver can see exactly what disclosure decision they are
   * authorizing before it is ever written to the register. `targetId` on
   * the ApprovalRequest itself is the LeRequest's own id. */
  requestedLeResponse?: {
    status: "disclosed" | "narrowed" | "objected" | "rejected";
    responseSummary: string;
  };
  /** data-destruction.certificate.issue: the non-secret shape of the
   * teardown state a second approver reviews before signing off --
   * the org's real namespace, whether it (or any PVC inside it) still
   * exists, and how many backup records remain unpurged -- the exact
   * fields lib/data-destruction-certificate.ts's `verifyDataDestruction`
   * computed moments before this request was filed. Mirrors
   * `DataDestructionVerification` field-for-field (minus its own
   * `reasons`, which is derived, not new information). `targetId` on the
   * ApprovalRequest itself is the org's own id. */
  requestedDataDestruction?: {
    namespace: string;
    namespaceExists: boolean;
    remainingPvcNames: string[];
    backupRecordsUndeleted: string[];
  };
  /** denied-party.override: the non-secret shape of the screening match
   * being reviewed -- the contact's role/name/email, every matched
   * denied-party list entry, and the decision being requested -- so a
   * second approver can see exactly which match they are being asked to
   * clear (or confirm) before it is ever recorded. `targetId` on the
   * ApprovalRequest itself is the screening record's own id
   * (`ScreeningRecord.id`, lib/denied-party-screening.ts). */
  requestedScreeningOverride?: {
    orgId: string;
    contactRole: "org_admin" | "billing_contact" | "technical_contact";
    contactName: string;
    contactEmail: string;
    matches: { listEntryId: string; matchedName: string; matchedAgainst: string }[];
    decision: "cleared_to_proceed" | "confirmed_blocked";
    justification: string;
  };
  /** change-of-control.notify: the non-secret shape of the notification
   * being recorded -- which trigger and org, and how notice was actually
   * delivered -- so a second approver can see exactly what compliance
   * fact they are authorizing before it is written to the ledger.
   * `targetId` on the ApprovalRequest itself is `<triggerId>.<orgId>`,
   * the notification row's own id (lib/change-of-control-
   * notifications.ts's OrgNotification.id). */
  requestedChangeOfControlNotification?: {
    triggerId: string;
    orgId: string;
    notificationMethod: string;
  };
  /** insurance.policy.update: the FULL proposed policy record (carrier,
   * policy number, coverage limit, effective/expiry dates, optional
   * carrier rating) -- so a second approver can see exactly what this
   * platform would attest to a counterparty before it is ever recorded.
   * `targetId` on the ApprovalRequest itself is the coverage type
   * (`InsuranceCoverageType`). Mirrors `InsurancePolicyRecord`
   * (lib/insurance-attestation.ts) field-for-field. */
  requestedInsurancePolicy?: {
    coverageType: "cyber" | "errors_omissions" | "general_liability";
    carrier: string;
    policyNumber: string;
    coverageLimitUsd: number;
    effectiveDate: string;
    expiryDate: string;
    amBestRating?: string;
  };
  /** personnel.attestation.record: the FULL proposed roster overrides
   * (per-identifier training-completion and, for privileged/`owner`
   * identifiers, background-check status) plus the attestation
   * statement -- so a second approver can see exactly what personnel-
   * control claim this platform would attest to a counterparty before
   * it is ever recorded. `targetId` on the ApprovalRequest itself is the
   * orgId. Mirrors lib/personnel-attestation.ts's
   * CompletePersonnelAttestationInput's `overrides`/`attestationStatement`
   * field-for-field. */
  requestedPersonnelAttestation?: {
    orgId: string;
    attestationStatement: string;
    overrides: Array<{
      identifier: string;
      securityTrainingCompleted: boolean;
      securityTrainingCompletedAt?: string;
      backgroundCheckStatus?: "cleared" | "pending" | "not_required";
    }>;
  };
  /** source-escrow.snapshot: the non-secret shape of the collected
   * release snapshot -- which namespace, the real deploy-time git commit
   * SHA (or `null` when no CI/CD env var stamped one), and how many real
   * Deployments/images were captured -- so a second approver can see
   * exactly what release identity they are authorizing this platform to
   * sign and durably escrow before it is ever attested. `targetId` on
   * the ApprovalRequest itself is the manifest namespace. Mirrors
   * lib/source-escrow-attestation.ts's `SourceEscrowManifest` summary
   * fields, never the full manifest (which travels separately, already
   * collected, straight into `generateSourceEscrowSnapshot` once
   * approved -- keeping this ConfigMap row small). */
  requestedSourceEscrowSnapshot?: {
    namespace: string;
    gitCommitSha: string | null;
    deploymentCount: number;
    imageCount: number;
  };
  /** pentest.finding.resolve: the non-secret shape of the finding being
   * closed -- which org/engagement it was filed against, its severity
   * and title, the requested terminal status (resolved vs.
   * accepted-risk), and the requester's own resolution notes -- so a
   * second approver can see exactly which finding they are authorizing
   * to mark closed, and why, before the register's own status changes.
   * `targetId` on the ApprovalRequest itself is the finding's own id
   * (`PentestFinding.id`, lib/pentest-attestation.ts). */
  requestedPentestFindingResolution?: {
    orgId: string;
    engagementId: string;
    severity: string;
    title: string;
    resolution: "resolved" | "accepted_risk";
    resolutionNotes: string;
  };
  /** vendor-offboarding.attestation.issue: the non-secret shape of the
   * data-return/destruction evidence a second approver reviews before
   * signing off -- the contractual SLA deadline, whether any qualifying
   * post-termination export exists, and the most recent data-destruction
   * certificate's own all-clear/tamper-verified state -- the exact
   * fields lib/vendor-offboarding-attestation.ts's
   * `computeVendorOffboardingEvidence` computed moments before this
   * request was filed. Mirrors `VendorOffboardingEvidence` field-for-
   * field (minus its own `reasons`, which is derived, not new
   * information). `targetId` on the ApprovalRequest itself is the org's
   * own id. */
  requestedVendorOffboardingEvidence?: {
    terminationDate: string;
    contractualSlaDays: number;
    slaDeadline: string;
    qualifyingExportRecordIds: string[];
    destructionCertificateId: string | null;
    destructionCertificateAllClear: boolean;
    destructionCertificateVerified: boolean;
    dataAccountedFor: boolean;
    withinSla: boolean;
  };
  /** legal-hold.release: the non-secret shape of the hold being lifted
   * -- its scope (platform-wide vs. one org), which org (absent for a
   * platform-wide hold), and the human-supplied reason litigation
   * concluded/no longer requires this hold -- so a second approver can
   * see exactly what destruction eligibility they are authorizing to
   * resume before it is ever released. `targetId` on the
   * ApprovalRequest itself is the hold's own id (`LegalHold.holdId`,
   * lib/legal-hold.ts). */
  requestedLegalHoldRelease?: {
    holdId: string;
    scope: "platform" | "org";
    orgId: string | null;
    releaseReason: string;
  };
  /** geofence.exception.grant: the non-secret shape of the requested
   * geofence bypass -- the exact identifier or CIDR being granted, the
   * requester's own justification, and the bounded TTL (in hours) the
   * exception would be valid for -- so a second approver can see exactly
   * what they are authorizing to bypass an org's own contracted-region
   * policy before it is ever recorded. `targetId` on the ApprovalRequest
   * itself is the org's own id (`GeofencePolicy.orgId`,
   * lib/geofence-enforcement.ts). */
  requestedGeofenceException?: {
    identifierOrCidr: string;
    reason: string;
    ttlHours: number;
  };
}

export interface ApprovalRequest {
  requestId: string;
  action: ApprovalAction;
  targetId: string;
  requestedBy: string;
  requestedAt: string;
  status: ApprovalStatus;
  approvedBy?: string;
  approvedAt?: string;
  reason?: string;
  resourcePayload?: ApprovalResourcePayload;
}

function isApprovalAction(value: string): value is ApprovalAction {
  return (ACTIONS_REQUIRING_APPROVAL as string[]).includes(value);
}

function isApprovalStatus(value: string): value is ApprovalStatus {
  return value === "pending" || value === "approved" || value === "rejected";
}

function isApprovalRequest(value: unknown): value is ApprovalRequest {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.requestId === "string" &&
    typeof v.action === "string" &&
    isApprovalAction(v.action) &&
    typeof v.targetId === "string" &&
    typeof v.requestedBy === "string" &&
    typeof v.requestedAt === "string" &&
    typeof v.status === "string" &&
    isApprovalStatus(v.status)
  );
}

async function getAll(): Promise<K8sResult<Record<string, ApprovalRequest>>> {
  const existing = await getConfigMap(APPROVALS_NAMESPACE, APPROVALS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, ApprovalRequest> = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      if (isApprovalRequest(row)) parsed[key] = row;
      // A hand-edited or corrupt row is skipped, not fatal -- same
      // "don't let one bad row break the whole list" discipline
      // lib/orgs.ts's getRegistry and lib/authz.ts's toAssignments use.
    } catch {
      // ignore -- malformed JSON for this key, same skip discipline.
    }
  }
  return { ok: true, data: parsed };
}

export async function listApprovals(): Promise<K8sResult<ApprovalRequest[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  return {
    ok: true,
    data: Object.values(all.data).sort((a, b) => b.requestedAt.localeCompare(a.requestedAt)),
  };
}

export async function getApproval(requestId: string): Promise<K8sResult<ApprovalRequest | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data[requestId] ?? null };
}

/**
 * Creates one real pending approval request. Called internally by every
 * guarded route (e.g. DELETE /api/orgs/[id]) the moment it detects no
 * fresh approved row exists for the target, and directly by POST
 * /api/approvals for the same purpose.
 */
export async function createApprovalRequest(input: {
  action: ApprovalAction;
  targetId: string;
  requestedBy: string;
  resourcePayload?: ApprovalResourcePayload;
}): Promise<K8sResult<ApprovalRequest>> {
  const requestId = globalThis.crypto.randomUUID();
  const request: ApprovalRequest = {
    requestId,
    action: input.action,
    targetId: input.targetId,
    requestedBy: input.requestedBy,
    requestedAt: new Date().toISOString(),
    status: "pending",
    ...(input.resourcePayload ? { resourcePayload: input.resourcePayload } : {}),
  };
  const result = await createOrUpdateConfigMap(APPROVALS_NAMESPACE, APPROVALS_CONFIGMAP, {
    [requestId]: JSON.stringify(request),
  });
  if (!result.ok) return result;
  return { ok: true, data: request };
}

export type RecordDecisionError = "not_found" | "already_decided" | "self_approval";

/**
 * Records a real approve/reject decision via the same one-key-at-a-time
 * merge-patch every other ConfigMap writer in this repo uses. Enforces
 * real two-person integrity server-side: an approver identifier equal to
 * the request's OWN stored `requestedBy` is refused with
 * "self_approval" -- the caller (POST /api/approvals/[id]) turns that
 * into the real 403 the spec requires, never a client-trusted check.
 * Also refuses a decision on a request that is no longer "pending" --
 * a decision is recorded exactly once, never silently overwritten.
 */
export async function recordApprovalDecision(input: {
  requestId: string;
  decision: "approved" | "rejected";
  approvedBy: string;
  reason?: string;
}): Promise<K8sResult<ApprovalRequest> | { ok: false; error: RecordDecisionError }> {
  const existing = await getApproval(input.requestId);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "not_found" };
  if (existing.data.status !== "pending") return { ok: false, error: "already_decided" };
  if (existing.data.requestedBy === input.approvedBy) return { ok: false, error: "self_approval" };

  const updated: ApprovalRequest = {
    ...existing.data,
    status: input.decision,
    approvedBy: input.approvedBy,
    approvedAt: new Date().toISOString(),
    reason: input.reason,
  };
  const result = await createOrUpdateConfigMap(APPROVALS_NAMESPACE, APPROVALS_CONFIGMAP, {
    [input.requestId]: JSON.stringify(updated),
  });
  if (!result.ok) return result;
  return { ok: true, data: updated };
}

/**
 * The real enforcement primitive a guarded route calls: is there a
 * status:"approved" row for this exact (action, targetId) pair, approved
 * within the last APPROVAL_TTL_HOURS hours? Returns the matching request
 * (most recently approved first) or null -- never a boolean alone, so the
 * caller can echo the approving identity/timestamp back if it wants to.
 */
export async function findApprovedRequest(
  action: ApprovalAction,
  targetId: string,
): Promise<K8sResult<ApprovalRequest | null>> {
  const all = await listApprovals();
  if (!all.ok) return all;

  const cutoff = Date.now() - APPROVAL_TTL_HOURS * 60 * 60 * 1000;
  const match = all.data
    .filter(
      (r) =>
        r.action === action &&
        r.targetId === targetId &&
        r.status === "approved" &&
        r.approvedAt !== undefined &&
        Date.parse(r.approvedAt) >= cutoff,
    )
    .sort((a, b) => (b.approvedAt ?? "").localeCompare(a.approvedAt ?? ""))[0];

  return { ok: true, data: match ?? null };
}

/**
 * requireApproval: the one call a guarded route handler makes. If a
 * fresh approved row already exists for this (action, targetId), returns
 * `{ok: true}` and the route proceeds with the real action. Otherwise it
 * creates a new pending request (idempotent-ish -- a second call while
 * one is already pending just creates a second row visible in the
 * approvals list; it does not synthesize a fake "approved") and returns
 * `{ok: false, request}` so the route can return the real 202 the spec
 * requires instead of performing the action.
 */
export async function requireApproval(input: {
  action: ApprovalAction;
  targetId: string;
  requestedBy: string;
  resourcePayload?: ApprovalResourcePayload;
}): Promise<
  | { ok: true; approval: ApprovalRequest }
  | { ok: false; request: ApprovalRequest }
  | { ok: false; error: string }
> {
  const approved = await findApprovedRequest(input.action, input.targetId);
  if (!approved.ok) return { ok: false, error: approved.error };
  if (approved.data) return { ok: true, approval: approved.data };

  const created = await createApprovalRequest(input);
  if (!created.ok) return { ok: false, error: created.error };
  return { ok: false, request: created.data };
}
