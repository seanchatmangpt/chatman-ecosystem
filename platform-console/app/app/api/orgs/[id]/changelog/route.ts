import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import { tierAtLeast } from "@/lib/tiers";
import { CHANGELOG_ENTRIES } from "@/lib/changelog";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real in-app changelog / release-notes feed, scoped by this org's real,
// live-derived Project tier (lib/orgs.ts's getOrgProjectTier -- same
// "always re-derived from the real Project CR label, never a separate
// stored field" source of truth every other tier-aware route in this
// tree already reads from). Turns the existing, already-enforced
// TIER_GATED_FLAGS / setOrgRegion / TIER_RESOURCE_QUOTAS tier ceilings
// (lib/tiers.ts, lib/orgs.ts) into a visible self-serve upsell surface: a
// tier-capped org sees every entry, including ones it hasn't unlocked
// yet, each carrying a real `unlocked` boolean computed from the SAME
// `tierAtLeast` comparison the actual enforcement code uses -- never a
// separate/looser check that could drift from what's really gated.
//
// Auth model, same "any authenticated member of THIS org, viewer and up"
// floor as GET /api/orgs/[id]/sla and GET /api/orgs/[id]/backup-policy --
// reading which capabilities exist (locked or not) is not itself a
// privileged action; only the underlying capability writes stay gated by
// their own routes.

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

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/changelog`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const tierResult = await getOrgProjectTier(org.namespace);
  if (!tierResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/changelog`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }
  const tier = tierResult.data;

  const entries = CHANGELOG_ENTRIES.map((entry) => ({
    ...entry,
    unlocked: tierAtLeast(tier, entry.minimumTier),
  }));

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/changelog`,
    status: 200,
    requestId,
  });

  return NextResponse.json({ tier, entries });
}
