import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, verifyAuditChain, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";

// Real tamper-evidence control for platform_console.audit_log: re-derives
// the entire hash chain live against the current table (lib/audit-db.ts's
// verifyAuditChain) and reports the first row, if any, whose stored
// row_hash no longer matches its recomputed digest -- the forensic
// "has this trail been silently rewritten" check a post-breach incident
// responder needs, and the exact thing a plain SELECT * FROM audit_log
// cannot answer. Owner-gated, same boundary as GET /api/audit itself
// (who-did-what and "has who-did-what been tampered with" are the same
// sensitivity class). Runs on the Node.js runtime (default for route
// handlers) -- lib/audit-db.ts's `pg` driver needs it.

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
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/audit/verify",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await verifyAuditChain();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/audit/verify",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
