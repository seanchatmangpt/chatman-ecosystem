import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import {
  newRequestId,
  writeAuditLogEntry,
  queryAuditLogForImpersonationSession,
} from "@/lib/audit-db";
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
      orgId: id,
    });
    return access.response!;
  }

  // Real reviewer drill-down: ?sessionId=<id> joins one specific
  // impersonation session (must belong to THIS org -- checked below, so
  // an org member can never pull another org's session's action list by
  // guessing a session id) against every audit_log row middleware.ts
  // actor-tagged with it -- "for one session id, the exact list of
  // actions taken", the spec's own phrasing for this control's proof.
  const sessionIdParam = request.nextUrl.searchParams.get("sessionId")?.trim();
  if (sessionIdParam) {
    const sessionsResult = await listImpersonationSessionsForOrg(id);
    if (!sessionsResult.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: `/api/orgs/${id}/impersonation-log`,
        status: 502,
        requestId,
        orgId: id,
      });
      return NextResponse.json({ error: sessionsResult.error }, { status: 502 });
    }
    const matchingSession = sessionsResult.data.find((s) => s.id === sessionIdParam);
    if (!matchingSession) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: `/api/orgs/${id}/impersonation-log`,
        status: 404,
        requestId,
        orgId: id,
      });
      return NextResponse.json(
        { error: "impersonation session not found for this org" },
        { status: 404 },
      );
    }

    const actionsResult = await queryAuditLogForImpersonationSession(sessionIdParam);
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/impersonation-log`,
      status: actionsResult.ok ? 200 : 502,
      requestId,
      orgId: id,
    });
    if (!actionsResult.ok) {
      return NextResponse.json({ error: actionsResult.error }, { status: 502 });
    }
    return NextResponse.json({ session: matchingSession, actions: actionsResult.data.rows });
  }

  const result = await listImpersonationSessionsForOrg(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/impersonation-log`,
    status: result.ok ? 200 : 502,
    requestId,
    orgId: id,
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
