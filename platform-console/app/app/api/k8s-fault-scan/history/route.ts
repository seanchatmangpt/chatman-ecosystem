import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listFaultScanSnapshots } from "@/lib/k8s-fault-scan-history";

// Runs on the Node.js runtime (default for route handlers) -- lib/audit-db.ts's
// `pg` driver requires it, same reasoning every other /api/* route documents.
//
// Read-only: returns the persisted, scheduled K8s Fault-Scan snapshot
// history (lib/k8s-fault-scan-history.ts, appended to by the
// "fault-scan-snapshot" CronJob command via
// POST /api/internal/fault-scan-snapshot, and also by POST
// /api/k8s-fault-scan's own on-demand scan) for one org, oldest-first,
// for in-app trend charting -- the continuous-posture-monitoring
// question ("has our structural-anomaly count trended up over the last
// quarter") the on-demand scan alone cannot answer. Any authenticated
// session with at least "viewer" may read it, same minimum role
// GET /api/load-test/history already uses for read-only history.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: session.sub,
      method: "GET",
      path: "/api/k8s-fault-scan/history",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId query param is required" }, { status: 400 });
  }

  const result = await listFaultScanSnapshots(orgId);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    orgId,
    method: "GET",
    path: "/api/k8s-fault-scan/history",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ orgId, snapshots: result.data });
}
