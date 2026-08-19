import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgSamlConfig, setOrgSamlConfig } from "@/lib/orgs";
import { validateSamlConfig } from "@/lib/saml-config";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Customer-facing SAML 2.0 metadata configuration surface (config-only,
// fail-closed) -- closes the named gap lib/oidc-federation.ts and
// lib/session.ts leave open: those prove OIDC federation is real and
// live, but Fortune-5 IT/security teams standardize enterprise app
// onboarding on SAML 2.0 (ADFS, Okta SAML apps, Azure AD SAML), not
// OIDC. This route lets an org admin configure and structurally validate
// their IdP's SAML metadata (Entity ID, SSO URL, x509 signing
// certificate) ahead of a later pass that wires the real SAML
// assertion-consumer-service endpoint.
//
// Explicitly fail-closed: this route's GET/PUT only ever read/write the
// `samlConfig` field lib/orgs.ts's registry entry now carries. No code
// path here -- or in lib/session.ts, or any auth callback route --
// consumes this config to authenticate a real session. The existing
// OIDC/Supabase login path is entirely unaffected by this route's
// existence. The settings page (app/orgs/[id]/sso/page.tsx) carries a
// status banner stating the same thing to the org admin, so this
// surface can never be mistaken for working SSO.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as app/api/orgs/[id]/branding/route.ts:
//   - GET: any authenticated member of THIS org (viewer and up) -- SAML
//     metadata is not a secret credential (it's the IdP's own public
//     signing certificate), same posture as branding.
//   - PUT: owner of THIS org specifically, checked against that org's OWN
//     namespace-local `platform-console-org-roles` ConfigMap via
//     lib/authz.ts's requireRoleIn -- never the platform's own
//     `platform-console` namespace roles requireRole reads, so an owner
//     of org A can never configure SAML for org B. (This codebase's real
//     role model is `viewer < member < owner` -- lib/authz.ts has no
//     separate "admin" role; "owner" is the admin-equivalent floor every
//     other privileged per-org write in this tree already uses.)

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

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/saml-config`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getOrgSamlConfig(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/saml-config`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    samlConfig: result.data,
    assertionConsumptionWired: false,
  });
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
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/saml-config`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const entityId = typeof body?.entityId === "string" ? body.entityId.trim() : "";
  const ssoUrl = typeof body?.ssoUrl === "string" ? body.ssoUrl.trim() : "";
  const certificatePem = typeof body?.certificatePem === "string" ? body.certificatePem.trim() : "";

  const validationError = validateSamlConfig({ entityId, ssoUrl, certificatePem });
  if (validationError) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/saml-config`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const result = await setOrgSamlConfig(id, { entityId, ssoUrl, certificatePem });
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/saml-config`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  return NextResponse.json({ org: result.data, assertionConsumptionWired: false });
}
