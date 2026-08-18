import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { sunsetCastle } from "@/lib/castle";

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

/**
 * SUNSET: owner-only, same boundary as DEPLOY -- tearing down cluster
 * workloads is infrastructure lifecycle, not member-level self-service.
 * Deletes every real Job this module created plus the deploy-state
 * ConfigMap; the response IS the real teardown record (which Jobs were
 * actually deleted, whether a deployment record existed at all) --
 * combined with the audit log entry below, this is what the evidence
 * bundle entry for this action is built from.
 */
export async function POST(request: NextRequest) {
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
      method: "POST",
      path: "/api/castle/sunset",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await sunsetCastle();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/castle/sunset",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ sunset: result.data });
}
