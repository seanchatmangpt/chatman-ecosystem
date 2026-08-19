import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import {
  findOrgByCustomDomain,
  getOrg,
  getOrgCustomDomain,
  setOrgCustomDomain,
  setOrgCustomDomainStatus,
} from "@/lib/orgs";
import { isValidCustomDomainHostname } from "@/lib/custom-domains";
import { createOrgCertificate, getCertificateStatus, orgCertificateSecretName } from "@/lib/k8s";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real per-org custom domain + TLS self-service endpoint: the standard
// AWS Amplify/Vercel/Retool "custom domain" enterprise-tier upsell,
// layered directly on top of the white-label branding this repo already
// ships (/api/orgs/[id]/branding) -- branding changes the CHROME served,
// this changes the URL it's served on. An org owner names a hostname
// (e.g. console.customer.com, DNS/CNAME pointed at this cluster's ingress
// by the customer themselves -- no DNS automation here, disclosed by the
// spec this route implements), this route confirms no OTHER org already
// claims it (lib/orgs.ts's findOrgByCustomDomain, a real scan of the
// live `platform-console-orgs` registry, never a side index that could
// drift), persists the binding on this org's own registry entry, and
// creates a real `cert-manager.io/v1` Certificate CR (lib/k8s.ts's
// createOrgCertificate) requesting a cert for that hostname against this
// cluster's configured ClusterIssuer.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading the current binding/status is not a privileged action. Also
//     re-syncs `customDomainStatus` against a fresh, live read of the
//     Certificate CR's own status.conditions before responding, so a UI
//     polling this endpoint always sees cert-manager's real, current
//     state, not a stale write-time snapshot.
//   - POST: owner of THIS org specifically, checked against that org's OWN
//     namespace-local `platform-console-org-roles` ConfigMap via
//     lib/authz.ts's requireRoleIn -- never platform-console's own
//     namespace roles, so an owner of org A can never bind org B's domain.

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
      path: `/api/orgs/${id}/custom-domain`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const boundResult = await getOrgCustomDomain(id);
  if (!boundResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/custom-domain`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: boundResult.error }, { status: 502 });
  }

  if (!boundResult.data) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/custom-domain`,
      status: 200,
      requestId,
    });
    return NextResponse.json({ customDomain: null, customDomainStatus: null });
  }

  // Live re-sync: only the Certificate CR's OWN status.conditions decide
  // whether stored status changes -- a `getCertificateStatus` failure
  // (e.g. cert-manager/RBAC not configured on this cluster, or the CR was
  // never created) leaves the last persisted status untouched rather than
  // overwriting a real prior state with a fabricated one.
  let status = boundResult.data.customDomainStatus;
  const certStatusResult = await getCertificateStatus(id);
  if (certStatusResult.ok && certStatusResult.data.status !== status) {
    status = certStatusResult.data.status;
    await setOrgCustomDomainStatus(id, status);
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/custom-domain`,
    status: 200,
    requestId,
  });
  return NextResponse.json({
    customDomain: boundResult.data.customDomain,
    customDomainStatus: status,
    certificateReason: certStatusResult.ok ? certStatusResult.data.reason : null,
    certificateMessage: certStatusResult.ok ? certStatusResult.data.message : null,
  });
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
      path: `/api/orgs/${id}/custom-domain`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const hostname = typeof body?.hostname === "string" ? body.hostname.trim().toLowerCase() : "";

  if (!isValidCustomDomainHostname(hostname)) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/custom-domain`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: `"${hostname}" is not a valid DNS hostname (need at least two dot-separated RFC 1123 labels)` },
      { status: 400 },
    );
  }

  const claimResult = await findOrgByCustomDomain(hostname, id);
  if (!claimResult.ok) {
    return NextResponse.json({ error: claimResult.error }, { status: 502 });
  }
  if (claimResult.data) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/custom-domain`,
      status: 409,
      requestId,
    });
    return NextResponse.json(
      { error: `"${hostname}" is already bound to a different org` },
      { status: 409 },
    );
  }

  // Write the binding first (status: pending) so a caller sees a real
  // "in progress" record even if the Certificate CR creation below fails
  // partway -- re-submitting the same hostname is always safe (a fresh
  // POST get-then-delete-then-create replaces any prior Certificate CR,
  // see lib/k8s.ts's createOrgCertificate comment).
  const pendingResult = await setOrgCustomDomain(id, hostname, "pending");
  if (!pendingResult.ok) {
    return NextResponse.json({ error: pendingResult.error }, { status: 502 });
  }
  if (!pendingResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const certResult = await createOrgCertificate(id, hostname);
  if (!certResult.ok) {
    await setOrgCustomDomainStatus(id, "failed");
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/custom-domain`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: `certificate issuance failed: ${certResult.error}` }, { status: 502 });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/custom-domain`,
    status: 200,
    requestId,
  });
  return NextResponse.json({
    org: pendingResult.data,
    customDomain: hostname,
    customDomainStatus: "pending",
    certificateSecretName: orgCertificateSecretName(id),
  });
}
