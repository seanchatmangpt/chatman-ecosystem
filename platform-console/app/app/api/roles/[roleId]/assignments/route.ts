import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { addOrgToRole, getCustomRole, removeOrgFromRole } from "@/lib/custom-roles";

// Multi-org selector management for one already-defined custom role:
// add/remove orgIds from its assignment set without re-entering the
// role's name/permissions. Same owner-only guard as /api/roles's
// upsert-role/delete-role/set-grants actions (requireRole(session,
// "owner")) -- assigning a role's scope to another subsidiary org is as
// privileged as defining the role in the first place. Same
// requireSession discipline as every other /api/* route in this app:
// middleware.ts already exchanges a Bearer API key for the same
// SESSION_COOKIE_NAME cookie before the request reaches this handler
// (see middleware.ts's forwardHeaders.set("cookie", ...)), so reading
// the cookie here covers both a browser session and a Bearer-API-key
// session -- no separate Authorization-header parsing needed.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

type AssignmentsPostBody = { orgId: unknown };

/**
 * POST /api/roles/[roleId]/assignments -- adds one orgId to the role's
 * assignment set (idempotent: an already-assigned orgId is a 200 no-op,
 * not an error).
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ roleId: string }> },
) {
  const requestId = newRequestId();
  const { roleId } = await params;

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      // org-agnostic: this 403 branch fires before body.orgId is parsed below
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/roles/${roleId}/assignments`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = (await request.json().catch(() => null)) as Partial<AssignmentsPostBody> | null;
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  if (!roleId || !orgId) {
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }

  const existing = await getCustomRole(roleId);
  if (!existing.ok) {
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data) {
    return NextResponse.json({ error: `custom role '${roleId}' not found` }, { status: 404 });
  }

  const result = await addOrgToRole(roleId, orgId);

  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/roles/${roleId}/assignments`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ role: result.data });
}

/**
 * DELETE /api/roles/[roleId]/assignments?orgId=<id> -- removes one
 * orgId from the role's assignment set. Refuses (400) to drop the last
 * remaining orgId -- lib/custom-roles.ts's removeOrgFromRole returns a
 * real, specific error rather than ever producing an orgIds: [] role;
 * retiring a role entirely is deleteCustomRole's existing tombstone
 * path, not this one.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ roleId: string }> },
) {
  const requestId = newRequestId();
  const { roleId } = await params;

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      // org-agnostic: this 403 branch fires before ?orgId= is parsed below
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/roles/${roleId}/assignments`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim() || "";
  if (!roleId || !orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const existing = await getCustomRole(roleId);
  if (!existing.ok) {
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data) {
    return NextResponse.json({ error: `custom role '${roleId}' not found` }, { status: 404 });
  }

  const result = await removeOrgFromRole(roleId, orgId);

  const status = result.ok ? 200 : 400;
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/roles/${roleId}/assignments`,
    status,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ role: result.data });
}
