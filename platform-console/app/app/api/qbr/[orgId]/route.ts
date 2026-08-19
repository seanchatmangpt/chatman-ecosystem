import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { listQbrBundlesForOrg } from "@/lib/qbr";

// Per-org Quarterly Business Review history -- the [orgId] counterpart to
// the cross-org latest-bundle list at GET /api/qbr. Platform-admin
// gated, same as the list route: a QBR bundle is a procurement/
// finance-adjacent exec artifact this repo treats the same way it treats
// contract renewals and budget thresholds, not a per-org self-service
// read an org's own owner can pull (it may quote spend/incident numbers
// a CSM has not yet shared externally).
//
// GET only here: every bundle ever generated for this org, newest
// quarter first. On-demand (re)generation is a distinct, more
// consequential action (it can overwrite an already-handed-to-a-VP
// bundle) and lives at its own route, POST /api/qbr/[orgId]/generate.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/qbr/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listQbrBundlesForOrg(orgId);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/qbr/${orgId}`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ bundles: result.data });
}
