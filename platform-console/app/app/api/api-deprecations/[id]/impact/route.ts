import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { computeDeprecationImpact } from "@/lib/api-deprecations";

// Per-org API deprecation impact report -- closes the gap between
// lib/api-deprecations.ts's generic, org-agnostic customer-facing feed
// (GET /api/api-deprecations, org-agnostic same as a status-page widget)
// and the question an enterprise platform team actually needs answered
// before a sunset date: "which of MY org's own API keys are calling this
// specific deprecated endpoint, how many times, and how recently." Same
// class of "turn a passive announcement into an actionable, audit-ready
// per-account impact report" surface AWS Trusted Advisor / GCP
// Deprecation Insights ship.
//
// GET-only, viewer-and-up gated against the target org's own
// namespace-local `platform-console-org-roles` ConfigMap (lib/authz.ts's
// requireRoleIn) -- same floor as the sibling
// GET /api/orgs/[id]/api-keys/[keyId]/usage route: reading your own
// org's usage of a deprecated endpoint isn't a privileged write, but it
// must still be scoped to a real, authenticated member of that specific
// org. `orgId` is a required query param (this route's own path only
// carries the deprecation notice's id, not an org id) resolved through
// lib/orgs.ts's getOrg the same way the usage route resolves its own
// `[id]` path segment, so an unknown orgId 404s before any audit-log
// query ever runs.
//
// The actual impact computation (matching this org's own logged
// requests against the notice's endpointPattern+method within the real
// 30-day lookback window, grouped by the api key id that made them) is
// entirely lib/api-deprecations.ts's computeDeprecationImpact -- this
// route is pure auth/resolution plumbing around it, same "route shapes
// the response, lib/ does the real query" split every other route in
// this tree uses.

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
  const path = `/api/api-deprecations/${id}/impact`;

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgId = request.nextUrl.searchParams.get("orgId");
  if (!orgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "'orgId' query param is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 502,
      requestId,
      orgId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 404,
      requestId,
      orgId,
    });
    return NextResponse.json({ error: `no org found with id '${orgId}'` }, { status: 404 });
  }

  // Any authenticated member of this org (viewer and up) may read its
  // own deprecation-impact report -- same floor as the sibling
  // api-keys/[keyId]/usage GET, since this is a read-only view of this
  // org's own traffic, not a privileged action.
  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 403,
      requestId,
      orgId,
    });
    return access.response!;
  }

  const impactResult = await computeDeprecationImpact(orgId, id);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path,
    status: impactResult.ok ? 200 : 502,
    requestId,
    orgId,
  });

  if (!impactResult.ok) {
    const status = impactResult.error.startsWith("no api deprecation notice found") ? 404 : 502;
    return NextResponse.json({ error: impactResult.error }, { status });
  }

  return NextResponse.json(
    { report: impactResult.data },
    { headers: { "cache-control": "no-store" } },
  );
}
