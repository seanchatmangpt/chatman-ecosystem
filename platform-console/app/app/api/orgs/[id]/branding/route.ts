import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgBranding, setOrgBranding, validateBranding } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real per-org white-label branding endpoint: closes the gap orgs.ts's
// Org/OrgRegistryEntry had zero branding fields for -- every customer org
// saw the identical unbranded platform-console chrome. Backed by the
// SAME `platform-console-orgs` registry ConfigMap createOrg already
// writes (no new k8s object), one JSON value per org, `branding` merge-
// patched in alongside the existing name/namespace/ownerIdentifier/
// createdAt keys.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading a public-facing brand record is not a privileged action.
//   - PUT: owner of THIS org specifically, checked against that org's OWN
//     namespace-local `platform-console-org-roles` ConfigMap via
//     lib/authz.ts's requireRoleIn -- never the platform's own
//     `platform-console` namespace roles requireRole reads, so an owner
//     of org A can never rebrand org B.

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

  // Any authenticated member of this org (viewer and up) may read its
  // branding -- fail-closed against non-members via requireRoleIn's
  // "viewer" floor rather than a bare "is there any session" check.
  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/branding`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getOrgBranding(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/branding`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ branding: result.data });
}

export async function PUT(
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
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/branding`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const productName = typeof body?.productName === "string" ? body.productName.trim() : "";
  const logoUrl = typeof body?.logoUrl === "string" ? body.logoUrl.trim() : "";
  const accentColor = typeof body?.accentColor === "string" ? body.accentColor.trim() : "";

  const validationError = validateBranding({ productName, logoUrl, accentColor });
  if (validationError) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/branding`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const result = await setOrgBranding(id, { productName, logoUrl, accentColor });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/branding`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  return NextResponse.json({ org: result.data });
}
