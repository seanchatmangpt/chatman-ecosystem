import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import {
  createAuditExportToken,
  listAuditExportTokens,
  newRequestId,
  revokeAuditExportToken,
  writeAuditLogEntry,
} from "@/lib/audit-db";
import { getOrg } from "@/lib/orgs";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";

// Owner-issuance surface for GET /api/v1/audit-export's bearer credential
// (lib/audit-db.ts's audit_export_tokens table): the piece that makes
// "owner-issued export token" a real, usable flow rather than only a
// schema with no way to mint one. Session-gated like every other page
// route in this console (never itself reachable by an audit-export
// token -- minting/listing/revoking export credentials is a strictly
// more sensitive action than using one to read events, so it stays on
// the human-session/pk_live_-key auth path middleware.ts already gates).
//
// Gated on THIS org's own owner role (requireRoleIn against the org's
// namespace-local platform-console-org-roles ConfigMap), the same
// per-org boundary app/api/orgs/[id]/branding/route.ts's PUT already
// uses -- an owner of org A must never mint an export token readable
// against... well, nothing outside org A's own attribution, since the
// underlying audit_log table has no per-org column yet (see
// docs/AUDIT-EXPORT-SCHEMA.md's disclosed scope note); the token's
// orgId is still real, checked, and attributable in every audit-export
// call's own logged actor string.
//
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and the `pg` driver lib/audit-db.ts uses both need it.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

async function requireOrgOwner(
  request: NextRequest,
  orgId: string,
): Promise<
  | { ok: true; session: SessionPayload; namespace: string }
  | { ok: false; response: NextResponse }
> {
  const session = await requireSession(request);
  if (!session) {
    return { ok: false, response: NextResponse.json({ error: "unauthenticated" }, { status: 401 }) };
  }
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return { ok: false, response: NextResponse.json({ error: orgResult.error }, { status: 502 }) };
  }
  if (!orgResult.data) {
    return { ok: false, response: NextResponse.json({ error: "org not found" }, { status: 404 }) };
  }
  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    return { ok: false, response: access.response! };
  }
  return { ok: true, session, namespace: orgResult.data.namespace };
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: orgId } = await params;
  const requestId = newRequestId();
  const gate = await requireOrgOwner(request, orgId);
  if (!gate.ok) return gate.response;
  const actor = gate.session.sub;

  const result = await listAuditExportTokens(orgId);

  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${orgId}/audit-export-tokens`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ tokens: result.data });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: orgId } = await params;
  const requestId = newRequestId();
  const gate = await requireOrgOwner(request, orgId);
  if (!gate.ok) return gate.response;
  const actor = gate.session.sub;

  const result = await createAuditExportToken({
    orgId,
    createdBy: roleIdentifierFor(gate.session),
  });

  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${orgId}/audit-export-tokens`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  // The ONLY response, ever, that carries the plaintext token -- same
  // "shown once at creation, never persisted or retrievable again"
  // convention as POST /api/api-keys.
  return NextResponse.json(
    { plaintext: result.data.plaintext, token: result.data.record },
    { status: 201 },
  );
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: orgId } = await params;
  const requestId = newRequestId();
  const gate = await requireOrgOwner(request, orgId);
  if (!gate.ok) return gate.response;
  const actor = gate.session.sub;

  const idParam = Number(request.nextUrl.searchParams.get("id"));
  if (!Number.isFinite(idParam)) {
    return NextResponse.json({ error: "numeric id query param is required" }, { status: 400 });
  }

  const result = await revokeAuditExportToken(orgId, idParam);

  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/orgs/${orgId}/audit-export-tokens`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ token: result.data });
}
