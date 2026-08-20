import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { closeBreakGlassGrant, openBreakGlassGrant } from "@/lib/break-glass";

// Break-Glass Emergency Access start+end endpoint -- the bounded-TTL
// escape hatch platform on-call opens to touch a customer's namespace
// during an active incident, deliberately bypassing the normal
// lib/approval-workflow.ts maker-checker gate (see lib/break-glass.ts's
// header comment for the compensating back-end control). Same
// "app-level RBAC on top of the console's own ServiceAccount RBAC"
// boundary as every other route in this tree:
//   - POST: platform-admin only (lib/authz.ts's requirePlatformAdmin --
//     the platform's own `platform-console` namespace "owner" role,
//     never a per-org owner role, so an owner of a customer org can
//     never grant themselves emergency access to another org).
//   - DELETE: only the same on-call engineer who opened the grant may
//     close it early -- enforced inside lib/break-glass.ts's
//     closeBreakGlassGrant, not just this route's own role gate.
//
// Every open/close is written to the SAME hash-chained audit_log every
// other privileged mutation in this app lands in (via
// lib/break-glass.ts's own writeAuditLogEntryAwaited calls), PLUS this
// route's own generic per-request entry below -- same double-entry
// convention lib/impersonation.ts's own start/end route already follows.

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
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/support/break-glass",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const targetOrgId = typeof body?.targetOrgId === "string" ? body.targetOrgId.trim() : "";
  const incidentReason = typeof body?.incidentReason === "string" ? body.incidentReason.trim() : "";

  if (!targetOrgId || !incidentReason) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/support/break-glass",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "targetOrgId and incidentReason are both required" },
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
      path: "/api/support/break-glass",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "target org not found" }, { status: 404 });
  }

  const result = await openBreakGlassGrant({
    adminUserId: actor,
    targetOrgId,
    namespace: orgResult.data.namespace,
    incidentReason,
  });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/support/break-glass",
    status: result.ok ? 200 : 502,
    requestId,
    orgId: targetOrgId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ breakGlassGrant: result.data });
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
      path: "/api/support/break-glass",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const grantId = typeof body?.grantId === "string" ? body.grantId.trim() : "";
  if (!grantId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/support/break-glass",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "grantId is required" }, { status: 400 });
  }

  const result = await closeBreakGlassGrant(grantId, actor);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/support/break-glass",
    status: result.ok ? 200 : 400,
    requestId,
    orgId: result.ok ? result.data.targetOrgId : undefined,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ breakGlassGrant: result.data });
}
