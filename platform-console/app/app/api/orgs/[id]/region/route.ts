import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgProjectTier, getOrgRegion, setOrgRegion } from "@/lib/orgs";
import { listNodeRegions } from "@/lib/k8s";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { tierAtLeast } from "@/lib/tiers";

// Real data residency / region pinning endpoint: regulated Fortune 5
// buyers (finance, healthcare, EU subsidiaries) routinely require
// contractual guarantees that a tenant's workloads/data stay pinned to a
// named region -- a standard enterprise-tier line item on every major
// cloud console (AWS/GCP/Azure) and a hard GDPR-localization / US
// financial data-residency blocker otherwise. Backed by the SAME
// `platform-console-orgs` registry ConfigMap createOrg/setOrgBranding
// already write (no new k8s object) plus a real, live
// `topology.kubernetes.io/region` node-label read (lib/k8s.ts's
// listNodeRegions) -- never a fabricated static region list.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading the current pin plus the live region list is not a
//     privileged action.
//   - PUT: owner of THIS org specifically, checked against that org's OWN
//     namespace-local `platform-console-org-roles` ConfigMap via
//     lib/authz.ts's requireRoleIn -- never platform-console's own
//     namespace roles, so an owner of org A can never pin org B.
//     Additionally gated to 403 when this org's real Project tier
//     (getOrgProjectTier) is below "enterprise", or when the requested
//     region is not one `listNodeRegions` currently reports live -- both
//     checks are re-enforced inside setOrgRegion itself (fail closed even
//     if a future caller skips this route).

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
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/region`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [regionResult, availableResult, tierResult] = await Promise.all([
    getOrgRegion(id),
    listNodeRegions(),
    getOrgProjectTier(orgResult.data.namespace),
  ]);

  const status = regionResult.ok && availableResult.ok && tierResult.ok ? 200 : 502;
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/region`,
    status,
    requestId,
  });

  if (!regionResult.ok) return NextResponse.json({ error: regionResult.error }, { status: 502 });
  if (!availableResult.ok) return NextResponse.json({ error: availableResult.error }, { status: 502 });
  if (!tierResult.ok) return NextResponse.json({ error: tierResult.error }, { status: 502 });

  return NextResponse.json({
    region: regionResult.data,
    availableRegions: availableResult.data,
    tier: tierResult.data,
    enterpriseEligible: tierAtLeast(tierResult.data, "enterprise"),
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
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/region`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const region = typeof body?.region === "string" ? body.region.trim() : "";
  if (!region) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/region`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "region is required" }, { status: 400 });
  }

  // Real, cluster-checked tier gate -- returned as 403 (a permission
  // failure, matching the requireRoleIn 403s above), distinct from the
  // 400s validateBranding-style input-shape failures return.
  const tierResult = await getOrgProjectTier(orgResult.data.namespace);
  if (!tierResult.ok) {
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }
  if (!tierAtLeast(tierResult.data, "enterprise")) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/region`,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      { error: "region pinning requires this org's Project tier to be enterprise" },
      { status: 403 },
    );
  }

  const regionsResult = await listNodeRegions();
  if (!regionsResult.ok) {
    return NextResponse.json({ error: regionsResult.error }, { status: 502 });
  }
  if (!regionsResult.data.includes(region)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/region`,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      {
        error: `region must be one of the cluster's live node regions: ${regionsResult.data.join(", ") || "(none detected)"}`,
      },
      { status: 403 },
    );
  }

  const result = await setOrgRegion(id, region);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/region`,
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
