import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getUsageBenchmark, orgMeetsBenchmarkTier } from "@/lib/usage-benchmarks";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Anonymized Cross-Org Usage Benchmarking Marketplace read endpoint (see
// lib/usage-benchmarks.ts's own header comment for the full method and
// anonymization guarantees). Real, live, pure aggregation over every
// org's own lib/cost.ts-equivalent NamespaceCostRow figures -- no new
// storage, no caching, no synthetic peer data.
//
// Auth: any authenticated member of THIS org (viewer and up), same floor
// as GET /api/orgs/[id]/usage-forecast -- reading a benchmark derived
// from this org's own real usage plus an already-anonymized peer
// distribution is not a privileged write action. Additionally gated
// behind this org's own real Project tier being at least "pro"
// (tierAtLeast, lib/tiers.ts) -- the same tier-gating pattern already
// established for TIER_GATED_FLAGS and for GET .../region's enterprise
// gate, applied here as the paid-add-on-report boundary this capability
// is monetized behind.
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
      path: `/api/orgs/${id}/usage-benchmark`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const tierCheck = await orgMeetsBenchmarkTier(org.namespace, "pro");
  if (!tierCheck.ok) {
    return NextResponse.json({ error: tierCheck.error }, { status: 502 });
  }
  if (!tierCheck.eligible) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/usage-benchmark`,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "cross-org usage benchmarking requires this org's Project tier to be pro or higher",
        tier: tierCheck.tier,
      },
      { status: 403 },
    );
  }

  const benchmarkResult = await getUsageBenchmark(id);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/usage-benchmark`,
    status: benchmarkResult.ok ? 200 : 502,
    requestId,
  });

  if (!benchmarkResult.ok) {
    return NextResponse.json({ error: benchmarkResult.error }, { status: 502 });
  }

  return NextResponse.json(benchmarkResult.data);
}
