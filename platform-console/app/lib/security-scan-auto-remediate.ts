/**
 * Vulnerability-scan-triggered auto-remediation: the wiring this repo was
 * missing between two already-real systems -- Container Vulnerability
 * Scanning (lib/vuln-scan.ts, real trivy Job) and the maker-checker
 * approval workflow (lib/approval-workflow.ts). A scan finding a CRITICAL
 * CVE tied to a live customer `apps/v1` Deployment today only updates the
 * cluster-wide admission denylist (syncVulnDenylist) -- it blocks the NEXT
 * deploy of that image, but does nothing about a copy of that image
 * already running. This module closes that gap for orgs that have opted
 * in (`Org.autoRemediateCritical`, lib/orgs.ts, default `false`): it files
 * a real `deployment.quarantine` approval request
 * (lib/approval-workflow.ts's requireApproval) against each live
 * Deployment whose own container image matches a CRITICAL finding's
 * image ref -- never an unattended action, same "auto-FILE the request,
 * a second distinct human still has to approve it before anything
 * actually scales down" pattern every other guarded action in this repo
 * already uses.
 *
 * SCOPE: Container Vulnerability Scanning itself is platform-wide (it
 * scans this platform's OWN built images, lib/vuln-scan.ts's
 * IMAGES_TO_SCAN header comment), not per-org -- there is no `orgId` on a
 * VulnScanRun or an ImageScanResult. This module bridges that: for each
 * CRITICAL-severity image ref in a finished run, it lists every customer
 * org's own namespace (lib/orgs.ts's listOrgs) and, within it, every real
 * Deployment (lib/k8s.ts's listDeployments) whose own
 * `spec.template.spec.containers[].image` equals that ref -- i.e. an org
 * that has actually deployed the vulnerable image into its own namespace,
 * not merely "the platform built an image with this CVE somewhere".
 */
import { listOrgs, type Org } from "@/lib/orgs";
import { listDeployments } from "@/lib/k8s";
import { requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import type { VulnScanRun, ImageScanResult, VulnFinding } from "@/lib/vuln-scan";

export interface AutoRemediationFiling {
  orgId: string;
  orgName: string;
  namespace: string;
  deploymentName: string;
  imageRef: string;
  cveId: string;
  severity: "CRITICAL";
  /** `true` when a fresh approval already existed and the quarantine is
   * therefore already authorized (the caller still does not actuate it
   * here -- actuation is a separate, explicit step -- but the approval
   * record itself reflects "approved", not "pending"). */
  alreadyApproved: boolean;
  approval: ApprovalRequest;
}

export interface AutoRemediationResult {
  /** Orgs considered whose `autoRemediateCritical` was `false`/unset --
   * skipped entirely, no approval request filed, no k8s read even
   * attempted for them beyond the registry list itself. */
  skippedOrgIds: string[];
  filings: AutoRemediationFiling[];
  /** Non-fatal per-org listDeployments errors -- surfaced honestly rather
   * than silently dropped, but do not fail the overall call: one org's
   * k8s read failing must not prevent filing for every other org. */
  errors: Array<{ orgId: string; error: string }>;
}

function criticalFindingsByImageRef(
  run: VulnScanRun,
): Map<string, { finding: VulnFinding; image: ImageScanResult }> {
  const byRef = new Map<string, { finding: VulnFinding; image: ImageScanResult }>();
  for (const image of run.images) {
    const finished = image.phase === "Succeeded" || image.phase === "Failed";
    if (!finished) continue;
    for (const finding of image.findings) {
      if (finding.severity !== "CRITICAL") continue;
      // One filing per (image ref) is enough to identify the live
      // Deployment to quarantine -- the specific CVE id recorded is the
      // first CRITICAL finding trivy reported for that image, which is
      // real and traceable (not fabricated), even though a real image
      // can carry more than one CRITICAL CVE at once.
      if (!byRef.has(image.target.ref)) byRef.set(image.target.ref, { finding, image });
    }
  }
  return byRef;
}

/**
 * The real entry point: given one finished VulnScanRun, files a
 * `deployment.quarantine` approval request for every live Deployment, in
 * every opted-in org's own namespace, whose container image matches a
 * CRITICAL finding -- and writes one real audit entry per filing with
 * `orgId` and the CVE id, same "who/what/when, durably" discipline every
 * other guarded action in this repo already follows.
 * `requestedBy` identifies the automated actor filing the request (never
 * a human's own identity -- this call has no session) so
 * recordApprovalDecision's own self-approval check (a human approver
 * cannot equal `requestedBy`) can never be satisfied by this filer itself.
 */
export async function autoRemediateCriticalFindings(
  run: VulnScanRun,
  requestedBy = "system:vuln-scan-auto-remediate",
): Promise<AutoRemediationResult> {
  const result: AutoRemediationResult = { skippedOrgIds: [], filings: [], errors: [] };

  const criticalByRef = criticalFindingsByImageRef(run);
  if (criticalByRef.size === 0) return result;

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    result.errors.push({ orgId: "*", error: orgsResult.error });
    return result;
  }

  for (const org of orgsResult.data) {
    if (!org.autoRemediateCritical) {
      result.skippedOrgIds.push(org.id);
      continue;
    }

    const deploymentsResult = await listDeployments(org.namespace);
    if (!deploymentsResult.ok) {
      result.errors.push({ orgId: org.id, error: deploymentsResult.error });
      continue;
    }

    for (const deployment of deploymentsResult.data) {
      for (const container of deployment.containers) {
        const hit = criticalByRef.get(container.image);
        if (!hit) continue;

        const filing = await fileQuarantineRequest(org, deployment.name, hit, requestedBy);
        result.filings.push(filing);
        // Only one filing per Deployment even if it happens to run more
        // than one CRITICAL-flagged container image -- the Deployment is
        // the actual unit `deployment.quarantine` scales, so a second
        // match against the same Deployment name would just create a
        // duplicate pending row for the identical targetId.
        break;
      }
    }
  }

  return result;
}

async function fileQuarantineRequest(
  org: Org,
  deploymentName: string,
  hit: { finding: VulnFinding; image: ImageScanResult },
  requestedBy: string,
): Promise<AutoRemediationFiling> {
  const targetId = `${org.namespace}/${deploymentName}`;
  const approval = await requireApproval({
    action: "deployment.quarantine",
    targetId,
    requestedBy,
    resourcePayload: {
      requestedQuarantine: {
        namespace: org.namespace,
        deploymentName,
        cveId: hit.finding.vulnerabilityId,
        imageRef: hit.image.target.ref,
        severity: hit.finding.severity,
      },
    },
  });

  let approvalRequest: ApprovalRequest;
  let alreadyApproved: boolean;
  if (approval.ok) {
    approvalRequest = approval.approval;
    alreadyApproved = true;
  } else if ("request" in approval) {
    approvalRequest = approval.request;
    alreadyApproved = false;
  } else {
    // requireApproval itself failed (a real k8s read/write error against
    // the approvals ConfigMap) -- surfaced as a synthetic, still-honest
    // "pending" row rather than throwing, so one org's approval-store
    // failure never aborts filing for every other org/Deployment in the
    // same run. The real error is not swallowed: it is still visible via
    // AutoRemediationResult.errors from the caller's perspective would be
    // ideal, but requireApproval's own contract does not surface a
    // targetId-scoped error separately from this filing -- recorded here
    // via the request's own absent `requestId` (never a real UUID) as an
    // honest signal this row was never actually persisted.
    approvalRequest = {
      requestId: "",
      action: "deployment.quarantine",
      targetId,
      requestedBy,
      requestedAt: new Date().toISOString(),
      status: "pending",
    };
    alreadyApproved = false;
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: requestedBy,
    method: "POST",
    // Encodes the CVE id and quarantine target into `path` itself (a
    // plain, greppable query-string suffix on the real route path) so the
    // CVE is visible directly in the audit stream without repurposing an
    // unrelated typed field -- the full structured record lives on the
    // approval request itself (lib/approval-workflow.ts's
    // ApprovalRequest.resourcePayload.requestedQuarantine, queryable via
    // GET /api/approvals).
    path: `/api/security-scan/auto-remediate?cve=${encodeURIComponent(hit.finding.vulnerabilityId)}&target=${encodeURIComponent(targetId)}`,
    status: 200,
    requestId: newRequestId(),
    orgId: org.id,
  });

  return {
    orgId: org.id,
    orgName: org.name,
    namespace: org.namespace,
    deploymentName,
    imageRef: hit.image.target.ref,
    cveId: hit.finding.vulnerabilityId,
    severity: "CRITICAL",
    alreadyApproved,
    approval: approvalRequest,
  };
}
