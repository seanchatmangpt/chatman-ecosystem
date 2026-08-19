import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, revokeOrgInviteIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// DELETE revokes a pending invite -- owner-of-THIS-org-gated, same
// requireRoleIn boundary as every other org-scoped mutation in this
// tree. `inviteId` is the invite's real token (the same value returned
// by POST /api/orgs/[id]/invites and listed by GET), not a separate id
// space -- there is no second identifier to keep in sync.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; inviteId: string }> },
) {
  const { id, inviteId } = await params;
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
  const namespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}/invites/${inviteId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await revokeOrgInviteIn(namespace, inviteId);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/orgs/${id}/invites/${inviteId}`,
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ invite: result.data });
}
