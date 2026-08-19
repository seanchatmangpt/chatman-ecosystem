import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, ROLES, roleIdentifierFor, type Role } from "@/lib/authz";
import { createApiKey, listApiKeysForOrg } from "@/lib/api-keys";
import { getOrg } from "@/lib/orgs";
import { isApiKeyTier } from "@/lib/rate-limit";

// Org-scoped counterpart to /api/api-keys: same owner-gated, real
// crypto-random-key-material, hash-only-storage discipline as
// lib/api-keys.ts's createApiKey/listApiKeys, just scoped to one org's
// own namespace via requireRoleIn (the same boundary
// /api/orgs/[id]/route.ts's DELETE and /api/orgs/[id]/branding's PUT
// already use for "owner of THIS org", not "owner of the platform
// console"). Every key minted through this route carries a formal
// `orgId` (lib/api-keys.ts's ApiKeyRecord.orgId) equal to the URL's org
// id -- the field this route exists to make possible to set correctly,
// since the global /api/api-keys route has no natural org context of its
// own beyond whatever the caller supplies in the body.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/api-keys`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listApiKeysForOrg(id);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/api-keys`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ keys: result.data });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/api-keys`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const requestedRole =
    typeof body?.role === "string" && ROLES.includes(body.role as Role)
      ? (body.role as Role)
      : undefined;
  const name = typeof body?.name === "string" ? body.name : "";
  const requestedTier = isApiKeyTier(body?.tier) ? body.tier : undefined;

  const result = await createApiKey({
    identifier: actor,
    orgId: id,
    creatorRole: access.role,
    createdBy: actor,
    requestedRole,
    name,
    tier: requestedTier,
  });

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/api-keys`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  // The only response, ever, that carries the plaintext key -- same
  // "shown once" discipline as /api/api-keys's POST.
  return NextResponse.json(
    { plaintext: result.data.plaintext, key: result.data.key },
    { status: 201 },
  );
}
