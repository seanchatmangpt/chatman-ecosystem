import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { readNamespaceStateUnderGrant, requireActiveBreakGlassGrant } from "@/lib/break-glass";

// The actual "touch a customer's namespace" read: a real, live GET of
// the target org's own Pods + Deployments (via lib/break-glass.ts's
// readNamespaceStateUnderGrant, backed by the same k8sRequest primitive
// lib/k8s-fault-scan.ts already uses -- never fabricated data), gated on
// the caller currently holding an active break-glass grant for that org
// (lib/break-glass.ts's requireActiveBreakGlassGrant). Every call is
// itself audit-logged with the grant id attached inside
// readNamespaceStateUnderGrant, on top of this route's own generic
// per-request entry -- same double-entry convention every other route
// in this tree follows.

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

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/support/break-glass/access",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const targetOrgId = request.nextUrl.searchParams.get("targetOrgId")?.trim();
  if (!targetOrgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/support/break-glass/access",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "targetOrgId query param is required" }, { status: 400 });
  }

  const grantCheck = await requireActiveBreakGlassGrant(actor, targetOrgId);
  if (!grantCheck.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/support/break-glass/access",
      status: 403,
      requestId,
      orgId: targetOrgId,
    });
    return NextResponse.json({ error: grantCheck.error }, { status: 403 });
  }

  const stateResult = await readNamespaceStateUnderGrant(grantCheck.grant);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/support/break-glass/access",
    status: stateResult.ok ? 200 : 502,
    requestId,
    orgId: targetOrgId,
  });
  if (!stateResult.ok) {
    return NextResponse.json({ error: stateResult.error }, { status: 502 });
  }
  return NextResponse.json({ grant: grantCheck.grant, state: stateResult.data });
}
