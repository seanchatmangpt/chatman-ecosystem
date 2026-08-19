import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getNamespaceUsageForecast } from "@/lib/usage-forecast";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real usage-forecasting / capacity-planning read endpoint (see
// lib/usage-forecast.ts's own header comment for the full method): turns
// the SAME real cpuCoreHours/memoryGiBHours Prometheus series
// lib/invoice-preview.ts already meters into a real least-squares
// projection of the date this org's namespace crosses its own configured
// lib/quota-enforcement.ts ProjectBudgetConfig cap -- "at current burn
// rate you hit your budget cap in N days", not just a current-window
// snapshot.
//
// Auth: any authenticated member of THIS org (viewer and up), same floor
// as GET /api/orgs/[id]/sla -- reading a forecast derived entirely from
// this org's own real metered usage and its own already-visible budget
// config is not a privileged action. Read-only: this route never writes
// anything (no ConfigMap patch, no k8s mutation) -- consistent with
// lib/usage-forecast.ts itself performing no writes.
//
// `?windowDays=` overrides the default 14-day trailing regression window
// (clamped to [2, 90]: fewer than 2 real daily buckets has no well-defined
// slope -- see fitLeastSquares's own doc comment -- and more than 90 days
// is well past what a daily-bucketed `increase()`/`avg_over_time()` range
// query over live Prometheus is meant to serve; a longer historical trend
// belongs in a real long-term metrics store, not this live cluster's
// Prometheus).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function parseWindowDays(request: NextRequest): number {
  const raw = request.nextUrl.searchParams.get("windowDays");
  if (!raw) return 14;
  const n = Number(raw);
  if (!Number.isFinite(n)) return 14;
  return Math.min(90, Math.max(2, Math.floor(n)));
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/usage-forecast`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const windowDays = parseWindowDays(request);
  const forecastResult = await getNamespaceUsageForecast(org.namespace, windowDays);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/usage-forecast`,
    status: forecastResult.ok ? 200 : 502,
    requestId,
  });

  if (!forecastResult.ok) {
    return NextResponse.json(
      {
        namespace: forecastResult.namespace,
        error: forecastResult.error,
        currentUsage: null,
        dailyRate: null,
        projectedBreachDate: null,
        daysRemaining: null,
      },
      { status: 502 },
    );
  }

  return NextResponse.json(forecastResult.data);
}
