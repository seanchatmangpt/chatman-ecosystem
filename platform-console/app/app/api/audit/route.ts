import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, queryAuditLog, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";

// Real hyperscaler CloudTrail / GCP Audit Logs / Azure Monitor Activity Log
// query surface: reads platform_console.audit_log on the live demo-project
// Postgres (lib/audit-db.ts) -- the durable counterpart to the real
// stdout line every authenticated request already produces
// (lib/audit-log.ts, still tailable via the /logs module or `kubectl
// logs`). Owner-gated (requireRole "owner"), not just member+ like most
// other GETs in this console: who-did-what visibility is itself
// sensitive, same reasoning /org already applies to role assignments.
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and the `pg` driver lib/audit-db.ts uses both need it.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 200;

export async function GET(request: NextRequest) {
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
      method: "GET",
      path: "/api/audit",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const params = request.nextUrl.searchParams;
  const actorFilter = params.get("actor")?.trim() || undefined;
  const pathFilter = params.get("path")?.trim() || undefined;
  const from = params.get("from")?.trim() || undefined;
  const to = params.get("to")?.trim() || undefined;
  const orgIdFilter = params.get("orgId")?.trim() || undefined;

  const limitParam = Number(params.get("limit"));
  const limit =
    Number.isFinite(limitParam) && limitParam > 0
      ? Math.min(Math.floor(limitParam), MAX_LIMIT)
      : DEFAULT_LIMIT;

  const pageParam = Number(params.get("page"));
  const page = Number.isFinite(pageParam) && pageParam > 0 ? Math.floor(pageParam) : 1;
  const offset = (page - 1) * limit;

  const result = await queryAuditLog({
    actor: actorFilter,
    path: pathFilter,
    from,
    to,
    limit,
    offset,
    orgId: orgIdFilter,
  });

  // Deliberately NOT logging this GET itself into the audit trail it just
  // read -- avoids every page load of /audit inflating its own result set
  // (the same reasoning /logs's tail endpoint follows). The 403 path above
  // still logs, since a denied access attempt is exactly the kind of event
  // this trail exists to capture.

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    entries: result.data.rows,
    total: result.data.total,
    page,
    limit,
  });
}
