import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import { listLatencyBenchmarkHistoryForOrg } from "@/lib/latency-history";

// Runs on the Node.js runtime (default for route handlers) -- lib/audit-db.ts's
// `pg` driver requires it, same reasoning every other /api/* route documents.
//
// Read-only: returns the persisted, scheduled latency-benchmark time
// series (lib/latency-history.ts, appended to by the
// "latency-benchmark-snapshot" CronJob command via
// POST /api/internal/latency-benchmark-snapshot) for one org, grouped by
// target, for in-app charting -- the SLA-evidence trend line
// (`has p95 latency degraded over the last quarter across our node
// pool`) app/app/api/load-test/route.ts's ad hoc POST cannot answer on
// its own. Any authenticated session with at least "viewer" may read it,
// same minimum role GET /api/ocel-log and GET /api/incidents already use
// for read-only history.

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
      path: "/api/load-test/history",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // `orgId` is a required query param, validated against the same fixed
  // `SCHEDULABLE_NAMESPACES` allowlist the scheduled benchmark itself
  // persists snapshots under (lib/load-test.ts's
  // runScheduledLatencyBenchmark is only ever invoked with one of these
  // via the CronJob path) -- never free-form request text used as a
  // ConfigMap key lookup.
  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!isSchedulableNamespace(orgId)) {
    return NextResponse.json(
      { error: "orgId query param is required and must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  const result = await listLatencyBenchmarkHistoryForOrg(orgId);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/load-test/history",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ orgId, byTarget: result.data });
}
