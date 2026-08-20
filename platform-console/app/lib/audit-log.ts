/**
 * The real, mechanical "access is logged" control: one JSON line per
 * authenticated request, written to stdout via console.log, in a fixed
 * schema. This is a log line, not a compliance claim -- see app/compliance
 * for the honest framing of what evidence this actually constitutes.
 */
export interface AuditLogEntry {
  timestamp: string; // RFC3339
  actor: string; // session subject (username), or "anonymous"
  method: string;
  path: string;
  status: number;
  requestId: string;
  /**
   * Cross-reference to castle's own independent chain: the BLAKE3
   * `receipt_digest` (castle.rs's `Receipt.receipt_digest`, castle.rs:513-522)
   * of a `ReceiptedOcelLog` (castle.rs:683-687) produced by a GymAct-invoking
   * castle run, when one was found in that run's Job output. Optional and
   * absent for every non-GymAct verb (today, every verb in
   * `ALLOWED_CASTLE_VERBS` -- see lib/castle.ts) and for every non-castle
   * audit entry. Recording this field never merges the two chains: castle's
   * BLAKE3 receipt chain and this table's own sha256 row-hash chain remain
   * independently verifiable end to end; this field only lets a reviewer
   * walk from one to the other.
   */
  castleReceiptDigest?: string;
  /**
   * Impersonation actor-tagging (SOC2/ISO27001 "prove exactly what an
   * engineer touched while impersonating", not just "we logged the
   * start/end of the session"): set by middleware.ts on every request
   * made while an active lib/impersonation.ts session's targetOrgId
   * matches the org this request is scoped to. `impersonatedBy` is the
   * real admin identity that started the session (never the target
   * org's own actor -- `actor` above stays whatever it already was, this
   * field is additive, not a replacement, so existing readers of `actor`
   * are unaffected); `impersonationSessionId` cross-references the exact
   * row in `platform_console.impersonation_sessions` this action
   * happened under. Both absent for every normal, non-impersonated
   * request -- the overwhelming majority of rows.
   */
  impersonatedBy?: string;
  impersonationSessionId?: string;
  /**
   * Custom RBAC (lib/custom-roles.ts) cross-reference: the fine-grained
   * Permission a request was gated on when the decision came from
   * lib/authz.ts's hasPermission fallback (a custom-role grant) rather
   * than the built-in viewer/member/owner rank -- lets a reviewer see
   * exactly which narrower, least-privilege grant authorized (or denied)
   * an action, on top of the existing role-rank audit trail. Absent for
   * every request gated purely by the built-in rank.
   */
  requiredPermission?: string;
  /**
   * Per-org tenant scope (SIEM export org-scoping): the org this action was
   * performed against, when the request resolved to one (most routes have
   * it via getProject/getOrg/session context). Absent for genuinely
   * unscoped/platform-wide actions (e.g. a route with no single-org
   * subject). Nullable at the storage layer for backward compatibility
   * with rows written before this field existed -- see audit-db.ts's
   * ensureAuditLogChainColumns and computeRowHash.
   */
  orgId?: string;
  /**
   * Customer-facing API key usage analytics (queryApiKeyUsage in
   * lib/audit-db.ts): the real join key from an audit row back to the
   * specific `pk_live_...` key that authenticated it (lib/api-keys.ts's
   * ResolvedApiKeyAuth.keyId). Set by middleware.ts only on requests
   * authenticated via `Authorization: Bearer pk_live_...` -- absent for
   * every session-cookie-authenticated request, since a browser session
   * isn't bound to any one key. `actor` alone can't disambiguate between
   * two keys minted for the same bound identity; `keyId` can.
   */
  keyId?: string;
  /**
   * Customer-facing API key usage analytics: wall-clock request latency
   * in whole milliseconds, measured by middleware.ts from the start of
   * this request's own middleware invocation to the point the response
   * was ready to forward. Optional and absent for any row written before
   * this field existed -- queryApiKeyUsage's p50/p95 latency aggregation
   * skips NULLs rather than treating them as zero.
   */
  durationMs?: number;
  /**
   * SLA credit auto-application (POST /api/orgs/[id]/sla-credits): the
   * real Stripe customer-balance transaction id
   * (lib/stripe-billing.ts's applySlaCreditToStripeBalance), the exact
   * amount actually credited in integer cents, and the "YYYY-MM" month
   * it was applied for -- present only on the one audit row that records
   * a real credit actually landing on a customer's Stripe balance, so a
   * reviewer can cross-reference this platform's own hash-chained audit
   * trail against Stripe's own dashboard/API record of the same
   * transaction. All three are set together or not at all.
   */
  slaCreditStripeTransactionId?: string;
  slaCreditAmountCents?: number;
  slaCreditMonth?: string;
  /**
   * Per-org negotiated pricing/discount-schedule override
   * (PUT /api/orgs/[id]/pricing-override, lib/orgs.ts's
   * setOrgPricingOverride): `pricingOverrideAction` distinguishes a real
   * negotiated rate being bound (`"set"`) from one being cleared
   * (`"expire"`, an org reverting to standard list pricing), and
   * `pricingOverrideContractRef` is the signed contract this rate traces
   * to -- so this platform's own audit trail is what proves, at audit
   * time, exactly which contracted rate was in force and when, rather
   * than a spreadsheet finance tracks by hand. Both absent for every
   * non-pricing-override audit row.
   */
  pricingOverrideAction?: "set" | "expire";
  pricingOverrideContractRef?: string;
  /**
   * Incident postmortem / RCA document (lib/postmortems.ts,
   * POST/PATCH /api/incidents/[id]/postmortem): `postmortemIncidentId`
   * cross-references the exact incident this compliance artifact was
   * generated for or finalized for, and `postmortemAction` distinguishes
   * the two auditable events -- `"postmortem_generated"` (the automatic
   * timeline/duration/severity/credit draft was produced or refreshed)
   * vs. `"postmortem_finalized"` (a human-authored rootCause/remediation
   * was recorded and the document was marked customer-deliverable),
   * logged as separate audit rows the same way this repo already
   * separates "credit computed" (GET) from "credit applied" (POST) on
   * the SLA-credit route above. Both absent for every non-postmortem
   * audit row.
   */
  postmortemIncidentId?: string;
  postmortemAction?: "postmortem_generated" | "postmortem_finalized";
  /**
   * Invoice / Purchase-Order Reconciliation Ledger
   * (POST/PUT /api/orgs/[id]/invoice-reconciliation,
   * lib/invoice-reconciliation.ts's recordInvoiceReconciliation /
   * decideInvoiceReconciliation): `reconciliationAction` distinguishes the
   * three real, durably-logged events in this ledger's lifecycle --
   * `"filed"` (a PO number + contract cap was reconciled against a real
   * lib/overage-billing.ts StoredOverage record), `"approved_for_payment"`
   * (a second, distinct owner-role approver signed off, same
   * maker-checker bar `pricing.override` sets), and `"rejected"` (the
   * approver declined, e.g. the PO number does not match what the
   * customer actually submitted). `reconciliationPoNumber` and
   * `reconciliationVarianceUsd` are the two numbers finance/procurement
   * actually need to see in this durable trail without cross-referencing
   * the ConfigMap record itself -- the customer's own submitted PO
   * reference, and the real signed dollar delta (overage billed minus
   * contract cap; positive means the customer was billed more than their
   * cap covers). All three fields absent for every non-reconciliation
   * audit row.
   */
  reconciliationAction?: "filed" | "approved_for_payment" | "rejected";
  reconciliationPoNumber?: string;
  reconciliationVarianceUsd?: number;
  /**
   * Sub-processor Registry (lib/subprocessors.ts,
   * POST/PUT/DELETE /api/subprocessors[/[id]]): `subprocessorAction`
   * records which real, maker-checker-approved mutation actually landed
   * (`"added"`/`"updated"`/`"removed"`), `subprocessorId` cross-references
   * the exact sub-processor entry, and `subprocessorNotifiedOrgCount` is
   * the real count of orgs a change-notice email was actually sent to
   * (lib/subprocessors.ts's `applySubprocessorChange`) -- so this
   * platform's own durable audit trail is what proves, at audit time,
   * that the GDPR Art. 28(2) "opportunity to object" notice was actually
   * dispatched, and to how many recipients, rather than a claim taken on
   * faith. All three absent for every non-subprocessor-registry audit
   * row.
   */
  subprocessorAction?: "added" | "updated" | "removed";
  subprocessorId?: string;
  subprocessorNotifiedOrgCount?: number;
  /**
   * Customer-Managed Encryption Key (CMEK/BYOK) binding
   * (PUT/DELETE /api/orgs/[id]/cmek, lib/orgs.ts's setOrgCmekBinding):
   * `cmekAction` distinguishes an org's first-ever key binding (`"bind"`)
   * from rotating to a new key reference (`"rotate"`) from reverting to
   * the platform default (`"unbind"`) -- the exact SOC2 CC6.1 /
   * PCI-DSS 3.6.4-adjacent, Fortune-5-security-review-required evidence
   * that a customer's own KMS key reference, not the platform's shared
   * default, actually governed this org's at-rest encryption during a
   * given window. `cmekProvider`/`cmekKeyRef` record which external KMS
   * and which key reference (never key material) applied. All three
   * absent for every non-CMEK audit row.
   */
  cmekAction?: "bind" | "rotate" | "unbind";
  cmekProvider?: string;
  cmekKeyRef?: string;
  /**
   * Law-Enforcement / Government Data Request register (transparency
   * log, lib/le-requests.ts): `leRequestAction` distinguishes the two
   * real, durably-logged events in this register's lifecycle -- `"logged"`
   * (a new subpoena/warrant/court-order/NSL was received and recorded,
   * POST /api/internal/le-requests) and `"responded"` (a second, distinct
   * owner-role approver signed off on the platform's real
   * disclosed/narrowed/objected/rejected response, same maker-checker bar
   * `subprocessor.registry.update`/`dsar.erasure` already set). Both
   * `leRequestId` (the register row's own id) and `leRequestType`
   * (subpoena/warrant/court_order/national_security_letter/other) are set
   * on every such row, so this platform's own audit trail is what proves,
   * at audit time, that every government data request received was
   * actually logged and how it was actually handled -- rather than a
   * claim taken on faith. All three absent for every non-LE-request audit
   * row.
   */
  leRequestAction?: "logged" | "responded";
  leRequestId?: string;
  leRequestType?: "subpoena" | "warrant" | "court_order" | "national_security_letter" | "other";
  /**
   * Denied-Party / Export-Control Screening Register
   * (POST/PUT /api/owner/[orgId]/denied-party-screening,
   * lib/denied-party-screening.ts): `screeningAction` distinguishes the
   * two real, durably-logged events in this register's lifecycle --
   * `"screened"` (a contact was actually run against the maintained
   * denied-party list, POST) and `"override_recorded"` (a second,
   * distinct owner-role approver signed off on a "potential_match"
   * result, PUT, same maker-checker bar `le-request.respond`/
   * `subprocessor.registry.update` already set). `screeningRecordId`
   * cross-references the exact row in the org's screening register,
   * `screeningResult` is the real match/no-match outcome computed at
   * screening time, and `screeningContactRole` is which of
   * org_admin/billing_contact/technical_contact was screened -- so this
   * platform's own durable audit trail is what proves, at audit time,
   * that every named contact was actually screened and how any match
   * was actually resolved, rather than a claim taken on faith. All four
   * absent for every non-screening audit row.
   */
  screeningAction?: "screened" | "override_recorded";
  screeningRecordId?: string;
  screeningResult?: "clear" | "potential_match";
  screeningContactRole?: "org_admin" | "billing_contact" | "technical_contact";
  /**
   * Change-of-Control / M&A Notification Register
   * (POST/PATCH/PUT /api/owner/change-of-control,
   * lib/change-of-control-notifications.ts): `changeOfControlAction`
   * distinguishes the three real, durably-logged events in this ledger's
   * lifecycle -- `"trigger_filed"` (a new acquisition/merger/ownership-
   * change event was recorded and the notice-window clock started for
   * every named org), `"affected_orgs_added"` (an existing trigger's
   * affected-org list was widened), and `"org_notified"` (a second,
   * distinct owner-role approver signed off that a specific customer org
   * was actually given contractual notice, same maker-checker bar
   * `le-request.respond`/`denied-party.override` already set).
   * `changeOfControlTriggerId` cross-references the exact trigger row,
   * and `changeOfControlAffectedOrgCount` (set on the first two actions
   * only) is the real count of orgs the write actually applied to -- so
   * this platform's own durable audit trail is what proves, at audit
   * time, that every M&A notification obligation was actually tracked
   * and discharged, rather than a claim taken on legal's own memory. All
   * three absent for every non-change-of-control audit row.
   */
  changeOfControlAction?: "trigger_filed" | "affected_orgs_added" | "org_notified";
  changeOfControlTriggerId?: string;
  changeOfControlAffectedOrgCount?: number;
  /**
   * Certificate of Insurance (COI) On-Demand Attestation
   * (lib/insurance-attestation.ts, PUT/POST /api/owner/insurance-
   * attestation): `insuranceAction` distinguishes a real, maker-checker-
   * approved policy metadata version being recorded (`"policy_recorded"`)
   * from a COI PDF summary being generated (`"attestation_generated"`) --
   * the two real, durably-logged events in this capability's lifecycle.
   * `insuranceCoverageType` cross-references which of the three coverage
   * types (cyber/E&O/general-liability) the row is about, and
   * `insuranceAttestationId` cross-references the exact generated-
   * attestation manifest id (set on `"attestation_generated"` rows only)
   * -- so this platform's own audit trail is what proves, at audit time,
   * exactly which insurance claim was made to a counterparty and when,
   * rather than a PDF someone can no longer account for. All three
   * absent for every non-insurance-attestation audit row.
   */
  insuranceAction?: "policy_recorded" | "attestation_generated";
  insuranceCoverageType?: "cyber" | "errors_omissions" | "general_liability";
  insuranceAttestationId?: string;
  /**
   * Workforce Security-Training & Background-Check Attestation
   * (lib/personnel-attestation.ts, POST/GET
   * /api/compliance/personnel-attestation): `personnelAttestationAction`
   * records the one real, maker-checker-approved mutation this
   * capability performs (`"recorded"` -- a second, distinct owner-role
   * approver signed off, same maker-checker bar
   * `insurance.policy.update`/`subprocessor.registry.update` already
   * set), `personnelAttestationTrainingCompletionPercent` and
   * `personnelAttestationPrivilegedBackgroundCheckClearedPercent` are the
   * two real percentages actually attested -- so this platform's own
   * durable audit trail is what proves, at audit time, exactly what
   * personnel-control posture was claimed to a counterparty and when,
   * rather than a claim taken on faith. All three absent for every
   * non-personnel-attestation audit row.
   */
  personnelAttestationAction?: "recorded";
  personnelAttestationTrainingCompletionPercent?: number;
  personnelAttestationPrivilegedBackgroundCheckClearedPercent?: number;
  /**
   * Third-Party Penetration-Test Attestation Register
   * (lib/pentest-attestation.ts, POST/PUT /api/compliance/pentest[/[findingId]]):
   * the real lifecycle event -- an engagement or finding filed, a finding
   * moved to remediation-in-progress, or a finding resolved/accepted-risk
   * -- backing the citable pentest evidence record a Fortune-5 security
   * review asks for. Mirrors the same "durable, externally-relied-upon
   * compliance-evidence write" audit shape `reconciliationAction`/
   * `screeningAction` already establish for their own registers. All four
   * absent for every non-pentest audit row.
   */
  pentestAction?:
    | "engagement_filed"
    | "finding_filed"
    | "finding_remediation_in_progress"
    | "finding_resolved"
    | "finding_accepted_risk";
  pentestEngagementId?: string;
  pentestFindingId?: string;
  pentestFindingSeverity?: string;
  pentestTesterFirm?: string;
  /**
   * Vendor Offboarding Data-Return/Destruction Attestation
   * (lib/vendor-offboarding-attestation.ts, POST
   * /api/owner/vendor-offboarding): the one real, maker-checker-approved
   * mutation this capability performs (`"attestation_issued"` -- a
   * second, distinct owner-role approver signed off, same maker-checker
   * bar `data-destruction.certificate.issue`/`insurance.policy.update`
   * already set), fail-closed against real
   * lib/export-custody.ts/lib/data-destruction-certificate.ts evidence.
   * `vendorOffboardingAttestationId` cross-references the exact issued
   * attestation -- so this platform's own durable audit trail is what
   * proves, at audit time, exactly which data-return/destruction claim
   * was made to a terminating customer's procurement/legal team and
   * when, rather than a manual doc no one can account for. Both absent
   * for every non-vendor-offboarding audit row.
   */
  vendorOffboardingAction?: "attestation_issued";
  vendorOffboardingAttestationId?: string;
  /**
   * Legal Hold on audit/retention purge (lib/legal-hold.ts,
   * POST /api/owner/legal-hold): `legalHoldAction` records the four real,
   * durably-logged events in this control's lifecycle -- `"placed"` (a
   * new hold started restricting destruction, never approval-gated --
   * see lib/legal-hold.ts's header comment), `"released"` (a second,
   * distinct owner-role approver signed off on lifting it, same
   * maker-checker bar `dsar.erasure`/`dr.failover` already set), and
   * `"purge_blocked"` / `"erasure_blocked"` (a scheduled retention purge
   * or a DSAR erasure request was actually refused because an active
   * hold covered its scope) -- this last pair is the specific evidence
   * "nothing was destroyed while under hold" that opposing counsel and
   * outside litigation holds require. `legalHoldId` cross-references the
   * exact hold row, `legalHoldScope` distinguishes a platform-wide hold
   * from one scoped to a single org, and `legalHoldOrgId` is that org's
   * id (absent for a platform-wide hold). All four absent for every
   * non-legal-hold audit row.
   */
  legalHoldAction?: "placed" | "released" | "purge_blocked" | "erasure_blocked";
  legalHoldId?: string;
  legalHoldScope?: "platform" | "org";
  legalHoldOrgId?: string;
  /**
   * Geofenced Data-Residency Access Enforcement
   * (lib/geofence-enforcement.ts, PUT/POST /api/owner/geofence-policy):
   * `geofenceAction` distinguishes the real, durably-logged events in
   * this control's lifecycle -- `"policy_set"` (an org's contracted
   * regions / CIDR-region map / enforcement mode were declared or
   * changed, never itself maker-checker-gated), `"exception_granted"`
   * (a second, distinct owner-role approver signed off on a bounded-TTL
   * bypass, same maker-checker bar `cmek.key-binding`/
   * `compliance.rotation-block` already set), and `"access_flagged"` /
   * `"access_rejected"` (a real request from outside the org's
   * contracted region was observed and either let through with a
   * durable flag, or actually refused, depending on the policy's own
   * `enforcementMode`) -- the exact evidence that turns the paper
   * residency attestation (lib/data-residency-attestation.ts) into an
   * enforced control. `geofenceResolvedRegion` is the region this
   * request's own caller IP resolved to against the org's admin-
   * maintained CIDR map (absent when it could not be resolved at all),
   * and `geofenceContractedRegions` is a snapshot of the policy's own
   * allowed-region list at the moment of the check, so a reviewer never
   * has to reconstruct what the policy said at the time from its
   * current, possibly since-changed state. `orgId` above (not a new
   * field here) carries which org's policy this row is about. All three
   * fields absent for every non-geofence audit row.
   */
  geofenceAction?: "policy_set" | "exception_granted" | "access_flagged" | "access_rejected";
  geofenceResolvedRegion?: string;
  geofenceContractedRegions?: string[];
}

export function writeAuditLogEntry(entry: AuditLogEntry): void {
  // Deliberately a single console.log call producing exactly one JSON line
  // per entry -- straightforward to grep/parse/ship from stdout in any
  // container log pipeline (kubectl logs, Fluent Bit, etc.).
  console.log(JSON.stringify(entry));
}

export function newRequestId(): string {
  return crypto.randomUUID();
}
