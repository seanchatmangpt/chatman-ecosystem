import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { listImpersonationSessionsForOrg } from "@/lib/impersonation";

// Customer-facing compliance/trust endpoint: every impersonation session
// (in progress or completed) that has ever touched THIS org -- who, when,
// why, and how long -- the visible half of the SOC2/ISO27001 "support
// access is logged AND disclosed to the customer" control. Any
// authenticated member of the org (viewer and up, checked against that
// org's OWN namespace-local `platform-console-org-roles` ConfigMap via
// requireRoleIn) may read it -- same "reading your own org's compliance
// record is not a privileged action" convention as branding's GET and
// app/org/compliance's report list.

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
      path: `/api/orgs/${id}/impersonation-log`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listImpersonationSessionsForOrg(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/impersonation-log`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const now = Date.now();
  const sessions = result.data.map((s) => ({
    ...s,
    active: !s.endedAt && new Date(s.expiresAt).getTime() > now,
    durationSeconds: Math.round(
      ((s.endedAt ? new Date(s.endedAt).getTime() : now) - new Date(s.startedAt).getTime()) / 1000,
    ),
  }));

  return NextResponse.json({ sessions });
}
