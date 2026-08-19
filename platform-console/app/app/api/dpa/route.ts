import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { listOrgs } from "@/lib/orgs";
import { listOrgsMissingCurrentDpa } from "@/lib/dpa-records";

// Platform-wide compliance-dashboard-widget feed: every org that does
// NOT currently have a "signed" DPA record on file (lib/dpa-records.ts).
// Platform-level owner-gated (requireRole, not requireRoleIn -- this
// spans every org's namespace, so it's the same platform-admin boundary
// GET /api/orgs itself uses, not any one org's own owner check).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/dpa",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    return NextResponse.json({ error: orgsResult.error }, { status: 502 });
  }

  const missingResult = await listOrgsMissingCurrentDpa(orgsResult.data.map((o) => o.id));
  if (!missingResult.ok) {
    return NextResponse.json({ error: missingResult.error }, { status: 502 });
  }

  const orgById = new Map(orgsResult.data.map((o) => [o.id, o]));
  const missing = missingResult.data.map((row) => ({
    orgId: row.orgId,
    orgName: orgById.get(row.orgId)?.name ?? row.orgId,
    currentStatus: row.currentStatus,
  }));

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/dpa (missing=${missing.length})`,
    status: 200,
    requestId,
  });

  return NextResponse.json({ orgsMissingCurrentDpa: missing });
}
