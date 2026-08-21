import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { DR_GAME_DAY_ACTION, recordDrGameDayResult, runDrGameDay } from "@/lib/dr-failover";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, queryAuditLog, writeAuditLogEntry } from "@/lib/audit-db";

// Real, on-demand trigger for the non-destructive DR game-day drill
// (lib/dr-failover.ts's runDrGameDay) -- the same maker-checker-free,
// viewer-can-read/owner-can-run posture GET /api/dr/failover-status
// already draws for reads, with POST scoped to "owner" the same way
// POST /api/dr/initiate-failover is, since triggering an unattended drill
// is still a real, deliberate action even though it writes nothing
// destructive. Unlike initiate-failover, this route needs no
// requireApproval maker-checker gate at all -- the entire reason this
// module exists is to be safe to run casually, on demand, by a single
// owner, as often as an auditor wants to see fresh evidence.
//
// GET returns this org's real drill history straight from the
// hash-chained audit_log table (queryAuditLog, path-filtered to this
// org's own DR_GAME_DAY rows) -- the auditor-facing evidence trail IS
// this query, not a separately maintained report.
//
// Body: { orgId, fromRegion, toRegion }.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = await request.json().catch(() => null);
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  const fromRegion = typeof body?.fromRegion === "string" ? body.fromRegion.trim() : "";
  const toRegion = typeof body?.toRegion === "string" ? body.toRegion.trim() : "";

  if (!orgId || !fromRegion || !toRegion) {
    return NextResponse.json(
      { error: "orgId, fromRegion, and toRegion are all required" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/dr/game-day/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const drillResult = await runDrGameDay(orgId, fromRegion, toRegion);
  if (!drillResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/dr/game-day/${orgId}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: drillResult.error }, { status: 502 });
  }

  await recordDrGameDayResult(actor, requestId, drillResult.data);

  return NextResponse.json({
    action: DR_GAME_DAY_ACTION,
    triggeredBy: actor,
    result: drillResult.data,
  });
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim() ?? "";
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
      path: `/api/dr/game-day/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const limitParam = Number(request.nextUrl.searchParams.get("limit") ?? "50");
  const limit = Number.isFinite(limitParam) && limitParam > 0 ? Math.min(limitParam, 200) : 50;

  const historyResult = await queryAuditLog({
    path: `/dr/game-day/${orgId}/`,
    orgId,
    limit,
    offset: 0,
  });

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/dr/game-day/${orgId}`,
    status: historyResult.ok ? 200 : 502,
    requestId,
  });

  if (!historyResult.ok) {
    return NextResponse.json({ error: historyResult.error }, { status: 502 });
  }

  // Each row's synthetic path carries the full DrDrillResult as a
  // `?detail=<encoded JSON>` query param (see recordDrGameDayResult) --
  // decoded back out here so the auditor-facing history reads as
  // structured drill results, not raw synthetic paths.
  const drills = historyResult.data.rows.map((row) => {
    const detailIndex = row.path.indexOf("?detail=");
    let result: unknown = null;
    if (detailIndex !== -1) {
      try {
        result = JSON.parse(decodeURIComponent(row.path.slice(detailIndex + "?detail=".length)));
      } catch {
        result = null;
      }
    }
    return {
      requestId: row.requestId,
      timestamp: row.ts,
      status: row.status,
      wouldSucceed: row.status === 200,
      result,
    };
  });

  return NextResponse.json({ orgId, total: historyResult.data.total, drills });
}
