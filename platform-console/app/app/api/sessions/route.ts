import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { listActiveSessions, revokeSession } from "@/lib/active-sessions";

// Real Active Session Management (AWS IAM Identity Center active-session
// view / GCP Console "manage devices & activity" equivalent) -- see
// lib/active-sessions.ts for the full registry design. Owner-gated on
// every verb, same boundary as /api/audit and /api/api-keys: who's
// currently logged in, and the ability to force one of those sessions to
// stop working, is at least as sensitive as either of those.
//
// Runs on the Node.js runtime (default for route handlers) -- the `pg`
// driver lib/active-sessions.ts uses needs it.

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
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/sessions",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listActiveSessions();

  // Deliberately NOT logging this GET into the audit trail -- same
  // reasoning /api/audit's own GET follows: a read of "who's logged in"
  // shouldn't inflate the very trail an operator is trying to review.

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    sessions: result.data,
    // Tells the panel which row is "this browser tab's own session", so
    // the UI can flag it and warn before letting an owner revoke their
    // own currently-in-use session out from under themselves.
    currentSessionId: session.sessionId ?? null,
  });
}

export async function DELETE(request: NextRequest) {
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
      method: "DELETE",
      path: "/api/sessions",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const sessionId = request.nextUrl.searchParams.get("sessionId") ?? "";
  if (!sessionId) {
    return NextResponse.json({ error: "sessionId query param is required" }, { status: 400 });
  }

  const revokedBy = roleIdentifierFor(session);
  const result = await revokeSession(sessionId, revokedBy);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/sessions",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ session: result.data });
}
