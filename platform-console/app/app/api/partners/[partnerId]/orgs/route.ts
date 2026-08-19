import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getPartner, getPartnerOrgsRollup } from "@/lib/partners";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// The consolidated, single-audit-trail view a Partner/MSP needs before
// signing a reseller agreement: one JSON rollup across every org this
// partner manages, fanned out over the SAME per-org readers a human
// would otherwise open one org dashboard at a time to see --
// getOrgProjectTier (lib/orgs.ts), getUsageBenchmark
// (lib/usage-benchmarks.ts), and a real open-incident count
// (lib/incidents.ts). No new data source -- see lib/partners.ts's
// getPartnerOrgsRollup for the real fan-out.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ partnerId: string }> },
) {
  const { partnerId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  // Same platform-admin boundary as every other Partner route -- a
  // reseller rollup surfaces aggregate usage/billing/incident data
  // across MULTIPLE customer orgs at once, so it is gated at least as
  // strictly as a single-org owner view, never more loosely.
  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/partners/${partnerId}/orgs`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const partnerResult = await getPartner(partnerId);
  if (!partnerResult.ok) {
    return NextResponse.json({ error: partnerResult.error }, { status: 502 });
  }
  if (!partnerResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/partners/${partnerId}/orgs`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "partner not found" }, { status: 404 });
  }

  const rows = await getPartnerOrgsRollup(partnerResult.data);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/partners/${partnerId}/orgs`,
    status: 200,
    requestId,
  });
  return NextResponse.json({ partnerId, orgs: rows });
}
