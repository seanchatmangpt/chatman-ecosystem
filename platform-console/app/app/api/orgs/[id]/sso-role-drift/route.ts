import { NextRequest, NextResponse } from "next/server";
import { getOrgRoleAssignmentsIn, requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgSsoGroupMappings } from "@/lib/orgs";
import { computeSsoRoleDrift } from "@/lib/sso-role-drift";
import { listSsoRoleDriftSnapshots } from "@/lib/sso-role-drift-history";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real SSO/SCIM Role-Mapping Drift Audit report -- the ConfigMap-backed
// evidence a Fortune-5 enterprise security review board asks for by name
// before granting this console SSO trust: a live diff of the org's own
// declared SSO group -> role mapping (lib/sso-role-mapping.ts, set via
// PUT /api/orgs/[id]/sso-role-mapping) against the real, live
// `platform-console-org-roles` ConfigMap assignments in this org's own
// namespace (lib/authz.ts's getOrgRoleAssignmentsIn) -- never fabricated
// data, both inputs are real reads of already-persisted cluster state.
// See lib/sso-role-drift.ts's module doc for the honest scope boundary:
// this report cannot see real IdP group MEMBERSHIP (this app has no live
// SCIM feed), so it flags "role in use with no configured mapping" and
// "configured mapping currently unused", not "user X's IdP group doesn't
// match their app role" -- the two real drift classes actually computable
// from real, already-persisted state.
//
// Owner-gated (not viewer, unlike GET /api/orgs/[id]/pricing-override
// and GET /api/orgs/[id]/saml-config): this report enumerates every real
// identifier and role assignment in the org, the same "who has what
// privilege" sensitivity as the org's own admin/roles page, not a
// read any member should get by default.
//
// `?history=1` returns the real, persisted snapshot trend
// (lib/sso-role-drift-history.ts) instead of computing a fresh report --
// the continuous-posture-monitoring counterpart POST
// /api/internal/sso-role-drift-snapshot appends to.

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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sso-role-drift`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  if (request.nextUrl.searchParams.get("history") === "1") {
    const historyResult = await listSsoRoleDriftSnapshots(id);
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sso-role-drift?history=1`,
      status: historyResult.ok ? 200 : 502,
      requestId,
    });
    if (!historyResult.ok) {
      return NextResponse.json({ error: historyResult.error }, { status: 502 });
    }
    return NextResponse.json({ snapshots: historyResult.data });
  }

  const [mappingsResult, assignmentsResult] = await Promise.all([
    getOrgSsoGroupMappings(id),
    getOrgRoleAssignmentsIn(org.namespace),
  ]);

  const ok = mappingsResult.ok && assignmentsResult.ok;
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/sso-role-drift`,
    status: ok ? 200 : 502,
    requestId,
  });
  if (!mappingsResult.ok) {
    return NextResponse.json({ error: mappingsResult.error }, { status: 502 });
  }
  if (!assignmentsResult.ok) {
    return NextResponse.json({ error: assignmentsResult.error }, { status: 502 });
  }

  const report = computeSsoRoleDrift(id, mappingsResult.data, assignmentsResult.data);
  return NextResponse.json({ report });
}
