import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { listBreakGlassGrantsForOrg } from "@/lib/break-glass";

// Customer-facing compliance/trust endpoint: every break-glass emergency
// access grant (in progress or completed) that has ever touched THIS
// org's namespace -- who, when, why, for how long, and whether the
// mandatory post-hoc justification has been filed and countersigned --
// the visible half of the SIG/CAIQ "emergency access is logged AND
// disclosed to the customer" control. Same "reading your own org's
// compliance record is not a privileged action" convention as
// lib/impersonation.ts's own impersonation-log GET: any authenticated
// member of the org (viewer and up) may read it.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/break-glass-log`,
      status: 403,
      requestId,
      orgId: id,
    });
    return access.response!;
  }

  const result = await listBreakGlassGrantsForOrg(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/break-glass-log`,
    status: result.ok ? 200 : 502,
    requestId,
    orgId: id,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const now = Date.now();
  const grants = result.data.map((g) => ({
    ...g,
    active: !g.endedAt && new Date(g.expiresAt).getTime() > now,
    durationSeconds: Math.round(
      ((g.endedAt ? new Date(g.endedAt).getTime() : now) - new Date(g.startedAt).getTime()) / 1000,
    ),
    justificationOverdue:
      !!g.endedAt &&
      !g.justification &&
      now - new Date(g.endedAt).getTime() > 24 * 60 * 60 * 1000,
  }));

  return NextResponse.json({ grants });
}
