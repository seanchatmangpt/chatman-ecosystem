import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { endImpersonation, startImpersonation } from "@/lib/impersonation";

// Real Admin Impersonation / Support-Login start+end endpoint -- the
// control this codebase could not answer "yes" to on a SOC2/ISO27001
// vendor questionnaire ("do you log support access to our account?")
// before this route existed. Auth model, same "app-level RBAC on top of
// the console's own ServiceAccount RBAC" boundary as every other route in
// this tree:
//   - POST: platform-admin only (lib/authz.ts's requirePlatformAdmin --
//     the platform's own `platform-console` namespace "owner" role,
//     never a per-org owner role, so an owner of a customer org can never
//     grant themselves an impersonation session over another org).
//   - DELETE: the SAME admin who started the session may end it early --
//     enforced inside lib/impersonation.ts's endImpersonation, not just
//     by this route's own role gate, so a different platform-admin can't
//     silently close someone else's active support session.
//
// Every start/end is written to the SAME hash-chained audit_log every
// other privileged mutation in this app lands in (via
// lib/impersonation.ts's own writeAuditLogEntry calls), PLUS this route's
// own generic per-request entry below -- same double-entry convention
// every other route file in this tree already follows (a specific action
// entry from the lib layer, a generic method/path/status entry from the
// route layer).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/support/impersonate",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const targetOrgId = typeof body?.targetOrgId === "string" ? body.targetOrgId.trim() : "";
  const reason = typeof body?.reason === "string" ? body.reason.trim() : "";

  if (!targetOrgId || !reason) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/support/impersonate",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "targetOrgId and reason are both required" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(targetOrgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/support/impersonate",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "target org not found" }, { status: 404 });
  }

  const result = await startImpersonation(actor, targetOrgId, reason);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/support/impersonate",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ impersonationSession: result.data });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/support/impersonate",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const sessionId = typeof body?.sessionId === "string" ? body.sessionId.trim() : "";
  if (!sessionId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/support/impersonate",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "sessionId is required" }, { status: 400 });
  }

  const result = await endImpersonation(sessionId, actor);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/support/impersonate",
    status: result.ok ? 200 : 400,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ impersonationSession: result.data });
}
