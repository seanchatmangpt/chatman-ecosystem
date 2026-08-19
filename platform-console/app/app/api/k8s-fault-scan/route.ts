import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  collectClusterStateForOrg,
  hasK8sFaultScanner,
  runK8sFaultScan,
  type K8sFaultFinding,
} from "@/lib/k8s-fault-scan";
import { requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";

// K8s Fault Diagnosis -- wraps autofde-lab's real structural-anomaly
// scanner (lib/k8s-fault-scan.ts's own header comment has the full
// provenance/discipline). Stated plainly per this feature's real scope:
// this route DIAGNOSES a live org namespace (produces structured
// `K8sFaultFinding` records classified against a real SREGym fault
// taxonomy, or `UNCLASSIFIED`) -- it never REMEDIATES. Findings that
// plausibly warrant a manual fix (today: any `declared_vs_observed`
// finding, the same class covered by the `INJECT_SCALE_PODS_TO_ZERO`/
// `INJECT_MISCONFIG_K8S` taxonomy labels the underlying scanner already
// classifies) file a `k8s-fault.remediate-suggest` maker-checker
// approval request (lib/approval-workflow.ts) -- a second, distinct
// human must approve it before anyone acts on it, and approving it
// authorizes nothing beyond "worth a human looking at," never an
// actuated change. No fabricated finding is ever returned: if the
// autofde-lab scanner CLI is not present at `AUTOFDE_LAB_PROJECT_DIR`,
// or the org has not opted in, or the subprocess itself fails, this
// route reports that honestly instead of inventing output.
//
// Owner-only, same floor POST /api/security-scan/auto-remediate uses --
// scanning a live customer namespace and filing approval requests
// against it is a privileged, org-scoped action.
//
// POST { orgId }: opt-in-gated (`Org.enableFaultScan`, default `false`),
// collects that org's real cluster state (lib/k8s-fault-scan.ts's
// collectClusterStateForOrg), runs the real scanner subprocess, and
// files one approval request per `declared_vs_observed` finding.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export interface K8sFaultScanFiling {
  finding: K8sFaultFinding;
  alreadyApproved: boolean;
  approval: ApprovalRequest;
}

export interface K8sFaultScanResponse {
  orgId: string;
  namespace: string;
  findings: K8sFaultFinding[];
  filings: K8sFaultScanFiling[];
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/k8s-fault-scan",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "request body must be valid JSON" }, { status: 400 });
  }
  const orgId =
    body && typeof body === "object" && "orgId" in body && typeof (body as { orgId: unknown }).orgId === "string"
      ? (body as { orgId: string }).orgId
      : null;
  if (!orgId) {
    return NextResponse.json({ error: "orgId (string) is required" }, { status: 400 });
  }

  if (!hasK8sFaultScanner()) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      orgId,
      method: "POST",
      path: "/api/k8s-fault-scan",
      status: 503,
      requestId,
    });
    return NextResponse.json(
      { error: "autofde-lab k8s-fault-taxonomy analysis not yet available: scanner CLI not found" },
      { status: 503 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      orgId,
      method: "POST",
      path: "/api/k8s-fault-scan",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const org = orgResult.data;
  if (!org) {
    return NextResponse.json({ error: `org not found: ${orgId}` }, { status: 404 });
  }
  if (!org.enableFaultScan) {
    return NextResponse.json(
      { error: `K8s Fault Diagnosis is not enabled for org ${orgId} (Org.enableFaultScan is false)` },
      { status: 403 },
    );
  }

  const clusterState = await collectClusterStateForOrg(org.namespace);
  const scanResult = runK8sFaultScan(clusterState);
  if (!scanResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      orgId,
      method: "POST",
      path: "/api/k8s-fault-scan",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: scanResult.error }, { status: 502 });
  }

  const findings = scanResult.data;
  const filings: K8sFaultScanFiling[] = [];
  for (const finding of findings) {
    if (finding.relation_class !== "declared_vs_observed") continue;
    const targetId = `${org.namespace}/${finding.kind}/${finding.object_name}/${finding.field}`;
    const approval = await requireApproval({
      action: "k8s-fault.remediate-suggest",
      targetId,
      requestedBy: actor,
      resourcePayload: {
        requestedFaultSuggestion: {
          namespace: finding.namespace,
          kind: finding.kind,
          objectName: finding.object_name,
          field: finding.field,
          relationClass: finding.relation_class,
          taxonomy: finding.taxonomy,
          detail: finding.detail,
        },
      },
    });
    if (approval.ok) {
      filings.push({ finding, approval: approval.approval, alreadyApproved: true });
    } else if ("request" in approval) {
      filings.push({ finding, approval: approval.request, alreadyApproved: false });
    }
    // requireApproval failing outright (a real k8s read/write error
    // against the approvals ConfigMap) is skipped for that one finding
    // rather than failing the whole scan response -- the real findings
    // themselves are still returned below regardless.
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    orgId,
    method: "POST",
    path: "/api/k8s-fault-scan",
    status: 200,
    requestId,
  });

  const response: K8sFaultScanResponse = {
    orgId,
    namespace: org.namespace,
    findings,
    filings,
  };
  return NextResponse.json(response);
}
