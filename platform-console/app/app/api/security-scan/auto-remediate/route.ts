import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { getVulnScanRun } from "@/lib/vuln-scan";
import { autoRemediateCriticalFindings } from "@/lib/security-scan-auto-remediate";

// Owner-only, same floor as POST/GET/DELETE /api/security-scan (this
// route's own header comment there): scanning and now auto-remediation
// filing both sit in the same "most sensitive capability" class -- this
// one can cause a live customer Deployment to be scaled to 0 pending a
// second approver's sign-off.
//
// POST { jobName }: reads the real, already-completed scan run
// (lib/vuln-scan.ts's getVulnScanRun -- the exact same read
// GET /api/security-scan itself performs) and, for every CRITICAL
// finding tied to a live Deployment in an org that has opted in
// (`Org.autoRemediateCritical`, lib/orgs.ts, default `false`), files a
// real `deployment.quarantine` maker-checker approval request
// (lib/approval-workflow.ts) -- never actuates the quarantine itself.
// Called by GET /api/security-scan's own handler as the natural next
// step after syncVulnDenylist on a completed run, and directly callable
// here for re-filing against an already-scanned run without re-running
// the scan.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
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
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/security-scan/auto-remediate",
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
  const jobName =
    body && typeof body === "object" && "jobName" in body && typeof (body as { jobName: unknown }).jobName === "string"
      ? (body as { jobName: string }).jobName
      : "";
  if (!jobName) {
    return NextResponse.json({ error: "jobName is required" }, { status: 400 });
  }

  const runResult = await getVulnScanRun(jobName);
  if (!runResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/security-scan/auto-remediate",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: runResult.error }, { status: 502 });
  }
  if (!runResult.data.complete) {
    return NextResponse.json(
      { error: "scan run is not yet complete -- auto-remediation only runs against a finished run" },
      { status: 409 },
    );
  }

  const remediation = await autoRemediateCriticalFindings(runResult.data);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/security-scan/auto-remediate",
    status: 200,
    requestId,
  });

  return NextResponse.json({
    jobName,
    filings: remediation.filings,
    skippedOrgIds: remediation.skippedOrgIds,
    errors: remediation.errors,
  });
}
