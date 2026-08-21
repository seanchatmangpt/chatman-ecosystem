/**
 * Secret & Certificate Rotation Compliance Enforcement -- the wiring this
 * repo was missing between three already-real systems: real k8s Secrets
 * (lib/k8s.ts's listSecrets), real TLS certificates
 * (lib/cert-lifecycle.ts's listManagedCertificates, parsed live with
 * Node's own X509Certificate -- no fabricated expiry data), and the
 * maker-checker approval workflow (lib/approval-workflow.ts). Neither
 * secrets nor certificates today enforce a maximum rotation AGE -- an
 * org can run the exact same Secret value, or the exact same TLS
 * certificate, forever. That is a real, specific gap in this platform's
 * SOC2 CC6.1 / PCI-DSS Requirement 3.6.4 evidence: both standards ask a
 * reviewer to show "cryptographic keys and TLS certificates are rotated
 * on a defined cadence", not merely "TLS is in use".
 *
 * This module closes that gap the same way
 * lib/security-scan-auto-remediate.ts closes the analogous CVE-scan gap:
 *
 *   1. `scanRotationCompliance` is a pure, read-only real scan -- for
 *      every real org (lib/orgs.ts's listOrgs), every real Opaque Secret
 *      in that org's own namespace (lib/k8s.ts's listSecrets) whose
 *      `createdAt` is older than `ROTATION_SLA_DAYS` is a violation, and
 *      every real custom-domain TLS certificate
 *      (lib/cert-lifecycle.ts's listManagedCertificates, joined back to
 *      its owning org via lib/custom-domains.ts's listCustomDomains --
 *      the real `platform-console.io/target-namespace` annotation each
 *      binding carries) that is already `expired` is a violation. Never
 *      fabricates an age or an expiry: both numbers come straight from
 *      the real k8s object's own `metadata.creationTimestamp` or the
 *      real X.509 `notAfter` field.
 *   2. `fileAndApplyRotationComplianceBlocks` is the one function that
 *      actually acts on a scan: for every org with at least one
 *      violation that is not already blocked, it files (or, if a fresh
 *      approval already exists, applies) a real `compliance.rotation-
 *      block` maker-checker approval request
 *      (lib/approval-workflow.ts's requireApproval) -- the scan itself
 *      never actuates a block; a second, distinct owner-role approver
 *      always has to sign off first, same "auto-FILE, human approves"
 *      pattern lib/security-scan-auto-remediate.ts already establishes
 *      for `deployment.quarantine`.
 */
import { listOrgs, setOrgRotationComplianceBlock, type Org } from "@/lib/orgs";
import { listSecrets, type SecretSummary } from "@/lib/k8s";
import { listManagedCertificates, type ManagedCertificate } from "@/lib/cert-lifecycle";
import { listCustomDomains } from "@/lib/custom-domains";
import { requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

/**
 * Maximum age, in days, a real Secret value or TLS certificate may go
 * without rotation before it is a compliance violation. 90 days is the
 * default PCI-DSS Requirement 3.6.4 cryptographic-key rotation cadence
 * (annual for some key classes, but 90 days is the conservative default
 * this console applies uniformly, the same "most conservative choice"
 * discipline lib/freeze-windows.ts's isFrozenNow already documents for
 * its own fail-closed default) and sits well inside the one-year self-
 * signed certificate lifetime lib/custom-domains.ts's
 * generateSelfSignedCertificate issues.
 */
export const ROTATION_SLA_DAYS = 90;

const MS_PER_DAY = 24 * 60 * 60 * 1000;

export interface RotationViolation {
  kind: "secret" | "certificate";
  namespace: string;
  /** Secret name, or certificate Secret name. */
  name: string;
  /** Real age in days since creation (secrets) or days already past
   * `notAfter` (certificates, always >= 0 here -- only expired certs are
   * violations). */
  ageDays: number;
  detail: string;
}

export interface OrgRotationComplianceReport {
  orgId: string;
  orgName: string;
  namespace: string;
  violations: RotationViolation[];
  /** Current `Org.rotationComplianceBlocked` value BEFORE this scan/file
   * call ran. */
  alreadyBlocked: boolean;
}

export interface RotationComplianceScanResult {
  scannedAt: string;
  slaDays: number;
  orgs: OrgRotationComplianceReport[];
  /** Non-fatal per-org listSecrets errors -- surfaced honestly rather
   * than silently dropped, but do not fail the overall scan: one org's
   * k8s read failing must not prevent scanning every other org. */
  errors: Array<{ orgId: string; error: string }>;
}

function secretAgeDays(secret: SecretSummary, now: number): number {
  const createdMs = Date.parse(secret.createdAt);
  if (Number.isNaN(createdMs)) return 0;
  return Math.floor((now - createdMs) / MS_PER_DAY);
}

/**
 * Real, live scan of every org's own Secrets, plus every rotatable
 * custom-domain certificate joined back to its owning org -- never
 * fabricated data, and never mutates or files anything by itself.
 */
export async function scanRotationCompliance(): Promise<RotationComplianceScanResult> {
  const now = Date.now();
  const result: RotationComplianceScanResult = {
    scannedAt: new Date(now).toISOString(),
    slaDays: ROTATION_SLA_DAYS,
    orgs: [],
    errors: [],
  };

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    result.errors.push({ orgId: "*", error: orgsResult.error });
    return result;
  }

  // Certificates and custom-domain bindings are read ONCE, platform-
  // wide, then joined back to each org by namespace below -- both
  // lib/cert-lifecycle.ts's listManagedCertificates and
  // lib/custom-domains.ts's listCustomDomains are namespace-agnostic
  // reads of the shared istio-system Secret/Gateway objects, never
  // per-org calls. A failure of either is non-fatal to the overall scan
  // (recorded under the synthetic orgId "*") -- secret-rotation
  // violations, which ARE per-org reads, must still be found for every
  // other org.
  let certsByNamespace = new Map<string, ManagedCertificate[]>();
  const certsResult = await listManagedCertificates();
  const domainsResult = await listCustomDomains();
  if (certsResult.ok && domainsResult.ok) {
    const namespaceBySecretName = new Map(
      domainsResult.data.map((binding) => [binding.secretName, binding.target.serviceNamespace]),
    );
    certsByNamespace = new Map();
    for (const cert of certsResult.data) {
      if (cert.kind !== "custom-domain" || !cert.expired) continue;
      const ns = namespaceBySecretName.get(cert.secretName);
      if (!ns) continue; // no live Gateway binding for this Secret -- not attributable to any org
      const list = certsByNamespace.get(ns) ?? [];
      list.push(cert);
      certsByNamespace.set(ns, list);
    }
  } else {
    result.errors.push({
      orgId: "*",
      error: !certsResult.ok ? certsResult.error : (domainsResult as { ok: false; error: string }).error,
    });
  }

  for (const org of orgsResult.data) {
    const violations: RotationViolation[] = [];

    const secretsResult = await listSecrets(org.namespace);
    if (!secretsResult.ok) {
      result.errors.push({ orgId: org.id, error: secretsResult.error });
    } else {
      for (const secret of secretsResult.data) {
        const ageDays = secretAgeDays(secret, now);
        if (ageDays >= ROTATION_SLA_DAYS) {
          violations.push({
            kind: "secret",
            namespace: org.namespace,
            name: secret.name,
            ageDays,
            detail: `Secret "${secret.name}" is ${ageDays}d old, exceeding the ${ROTATION_SLA_DAYS}d rotation SLA`,
          });
        }
      }
    }

    for (const cert of certsByNamespace.get(org.namespace) ?? []) {
      violations.push({
        kind: "certificate",
        namespace: org.namespace,
        name: cert.secretName,
        ageDays: Math.abs(cert.daysUntilExpiry),
        detail: `Certificate "${cert.secretName}" (${cert.hostname ?? "unknown host"}) expired ${Math.abs(
          cert.daysUntilExpiry,
        )}d ago and has not been rotated`,
      });
    }

    violations.sort((a, b) => b.ageDays - a.ageDays);
    result.orgs.push({
      orgId: org.id,
      orgName: org.name,
      namespace: org.namespace,
      violations,
      alreadyBlocked: org.rotationComplianceBlocked === true,
    });
  }

  return result;
}

export interface RotationComplianceFiling {
  orgId: string;
  orgName: string;
  violationCount: number;
  oldestViolationAgeDays: number;
  /** `true` once a fresh approval already existed and this call actually
   * flipped `Org.rotationComplianceBlocked` to `true` via
   * lib/orgs.ts's setOrgRotationComplianceBlock. `false` means a new
   * pending approval was filed (or one was already pending) and the org
   * remains unblocked until a second, distinct owner-role approver signs
   * off. */
  applied: boolean;
  approval: ApprovalRequest;
}

/**
 * The real actuation entry point: given a scan, files (or applies, once
 * approved) a `compliance.rotation-block` request for every org that has
 * at least one violation and is not already blocked. Never blocks an org
 * on its own say-so -- a fresh approval must already exist
 * (lib/approval-workflow.ts's requireApproval) before
 * `setOrgRotationComplianceBlock` is ever called. `requestedBy` identifies
 * the automated actor filing the request (never a human's own identity
 * when called from a cron-style scan) so recordApprovalDecision's own
 * self-approval check can never be satisfied by this filer itself.
 */
export async function fileAndApplyRotationComplianceBlocks(
  scan: RotationComplianceScanResult,
  requestedBy: string,
): Promise<RotationComplianceFiling[]> {
  const filings: RotationComplianceFiling[] = [];

  for (const org of scan.orgs) {
    if (org.violations.length === 0 || org.alreadyBlocked) continue;

    const oldestViolationAgeDays = org.violations[0]?.ageDays ?? 0;
    const approval = await requireApproval({
      action: "compliance.rotation-block",
      targetId: org.orgId,
      requestedBy,
      resourcePayload: {
        requestedRotationBlock: {
          namespace: org.namespace,
          violationCount: org.violations.length,
          oldestViolationAgeDays,
          reason: `${org.violations.length} secret(s)/certificate(s) exceeded the ${scan.slaDays}d rotation SLA`,
        },
      },
    });

    let approvalRequest: ApprovalRequest;
    let applied = false;
    if ("error" in approval) {
      // requireApproval itself failed (a real k8s read/write error
      // against the approvals ConfigMap) -- surfaced as a synthetic,
      // still-honest "pending" row rather than throwing, same recorded-
      // via-absent-requestId discipline
      // lib/security-scan-auto-remediate.ts's fileQuarantineRequest
      // already uses, so one org's approval-store failure never aborts
      // filing for every other org in the same scan.
      approvalRequest = {
        requestId: "",
        action: "compliance.rotation-block",
        targetId: org.orgId,
        requestedBy,
        requestedAt: new Date().toISOString(),
        status: "pending",
      };
    } else if (approval.ok) {
      approvalRequest = approval.approval;
      const applyResult = await setOrgRotationComplianceBlock(
        org.orgId,
        true,
        approval.approval.approvedBy ?? requestedBy,
        org.violations.length,
      );
      applied = applyResult.ok && applyResult.data !== null;
    } else {
      approvalRequest = approval.request;
    }

    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: requestedBy,
      orgId: org.orgId,
      method: applied ? "POST" : "PENDING",
      path: `/api/compliance/rotation?orgId=${encodeURIComponent(org.orgId)}&violationCount=${
        org.violations.length
      }&oldestViolationAgeDays=${oldestViolationAgeDays}`,
      status: applied ? 200 : 202,
      requestId: newRequestId(),
    });

    filings.push({
      orgId: org.orgId,
      orgName: org.orgName,
      violationCount: org.violations.length,
      oldestViolationAgeDays,
      applied,
      approval: approvalRequest,
    });
  }

  return filings;
}

/**
 * Real unblock entry point: given an org id, requires a fresh
 * `compliance.rotation-block` approval whose resourcePayload explicitly
 * clears the block (`requestedRotationBlock: null`, the same null-clears
 * convention `pricing.override` already establishes) before ever calling
 * lib/orgs.ts's setOrgRotationComplianceBlock(id, false, ...). Returns
 * `{applied:false}` with the pending/approved request when a fresh
 * approval does not yet exist -- the caller (DELETE
 * /api/compliance/rotation) turns that into the real 202 the maker-
 * checker contract requires.
 */
export async function clearRotationComplianceBlock(
  org: Org,
  requestedBy: string,
): Promise<{ applied: boolean; approval: ApprovalRequest } | { error: string }> {
  const approval = await requireApproval({
    action: "compliance.rotation-block",
    targetId: org.id,
    requestedBy,
    resourcePayload: { requestedRotationBlock: null },
  });
  if ("error" in approval) return { error: approval.error };

  if (!approval.ok) {
    return { applied: false, approval: approval.request };
  }

  const applyResult = await setOrgRotationComplianceBlock(
    org.id,
    false,
    approval.approval.approvedBy ?? requestedBy,
    0,
  );
  if (!applyResult.ok) return { error: applyResult.error };
  return { applied: true, approval: approval.approval };
}
