import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { queryAlerts } from "@/lib/alertmanager";

// Real current alert list from the in-cluster Alertmanager -- no allowlist
// needed here (unlike /api/prometheus) since GET /api/v2/alerts takes no
// query-language input to abuse; it always returns the full current alert
// set.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const result = await queryAlerts();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/alerts",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ alerts: result.data });
}
