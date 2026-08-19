import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getDsarRequest, listDsarRequests } from "@/lib/dsar";

// Real DSAR status read: GET ?requestId=... returns one real request row
// (including its downloadToken once an export completes -- the caller
// turns that into a GET /api/privacy/download?token=... link, same
// bearer-signed-token convention as export-all's own download route);
// GET ?orgId=... (no requestId) lists every DSAR request ever filed for
// that org, newest first, for the DSAR panel to render as a history
// table. Owner-gated on the ORG the request belongs to -- resolved from
// the row/org itself, never trusted from the query string alone.

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

  const params = request.nextUrl.searchParams;
  const dsarRequestId = params.get("requestId")?.trim();
  const orgIdParam = params.get("orgId")?.trim();

  if (dsarRequestId) {
    const result = await getDsarRequest(dsarRequestId);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    if (!result.data) {
      return NextResponse.json({ error: "DSAR request not found" }, { status: 404 });
    }

    const orgResult = await getOrg(result.data.orgId);
    if (!orgResult.ok) {
      return NextResponse.json({ error: orgResult.error }, { status: 502 });
    }
    if (!orgResult.data) {
      return NextResponse.json({ error: "org not found" }, { status: 404 });
    }

    const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
    if (!access.ok) {
      writeAuditLogEntry({
        orgId: result.data.orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: `/api/privacy/status?requestId=${dsarRequestId}`,
        status: 403,
        requestId,
      });
      return access.response!;
    }

    return NextResponse.json({ request: result.data });
  }

  if (!orgIdParam) {
    return NextResponse.json({ error: "requestId or orgId is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgIdParam);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: orgIdParam,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/privacy/status?orgId=${orgIdParam}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listDsarRequests(orgIdParam);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ requests: result.data });
}
