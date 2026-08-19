import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { ALLOWED_PROMETHEUS_QUERIES, queryPrometheus } from "@/lib/prometheus";

// Allowlist now lives in lib/prometheus.ts (ALLOWED_PROMETHEUS_QUERIES) --
// shared with lib/dashboards.ts's saved promql widgets, so a dashboard
// widget can never run a query this route itself would refuse. This
// route is reachable by any authenticated console user and Prometheus's
// query language can be used for extraction/DoS-shaped abuse if fully
// open. Extend the allowlist deliberately, not by accepting arbitrary
// client-supplied PromQL.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const query = request.nextUrl.searchParams.get("query") ?? "up";
  if (!ALLOWED_PROMETHEUS_QUERIES.has(query)) {
    return NextResponse.json(
      { error: `query not in allowlist: ${[...ALLOWED_PROMETHEUS_QUERIES].join(", ")}` },
      { status: 400 },
    );
  }

  const result = await queryPrometheus(query);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/prometheus",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
