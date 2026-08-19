import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getServiceCatalogForOrg } from "@/lib/service-catalog";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real Customer-Facing Service Catalog / Entitlement Matrix endpoint (AWS
// Service Catalog / GCP Console "Enabled APIs" equivalent): a single,
// tier-scoped read answering "exactly what capabilities are enabled for
// us right now" without an enterprise buyer's procurement or technical
// evaluator having to cross-reference lib/tiers.ts, the live feature-flag
// ConfigMap, and support tickets by hand. See lib/service-catalog.ts's
// header comment for how each entry is assembled and why this is
// distinct from the public Trust/security-posture page and the in-app
// changelog.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other org-scoped route in this
// tree (e.g. app/api/orgs/[id]/sla/route.ts): the caller's Authorization:
// Bearer <api-key> (resolved to a session by middleware.ts) or session
// cookie must belong to a member (viewer and up) of the org whose catalog
// is being requested -- reading the current entitlement matrix is not a
// privileged action, but it IS org-scoped: an org's own tier/SLA/flag
// state must never leak to a session with no role in that org.
//
// orgId is a query parameter (`?orgId=...`), not a path segment, since
// this is a top-level console page (not nested under /api/orgs/[id]/...)
// that a session with access to exactly one org can call without first
// knowing its own org id from the URL.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgId = request.nextUrl.searchParams.get("orgId");
  if (!orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/service-catalog",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const catalogResult = await getServiceCatalogForOrg(orgId);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/service-catalog",
    status: catalogResult.ok ? 200 : catalogResult.status,
    requestId,
  });

  if (!catalogResult.ok) {
    return NextResponse.json({ error: catalogResult.error }, { status: catalogResult.status });
  }

  return NextResponse.json(catalogResult.data);
}
