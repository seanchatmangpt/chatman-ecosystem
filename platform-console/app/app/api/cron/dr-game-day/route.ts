import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { listOrgs, getOrgProjectTier } from "@/lib/orgs";
import { listNodeRegions } from "@/lib/k8s";
import { tierAtLeast } from "@/lib/tiers";
import { recordDrGameDayResult, runDrGameDay, DR_GAME_DAY_SYSTEM_ACTOR } from "@/lib/dr-failover";

// Real, unattended monthly poller for the DR game-day drill -- same
// shared-secret-header authentication pattern as
// app/api/cron/retention-purge/route.ts and lib/scheduled-jobs.ts's
// createExportSubscriptionCronJob (see either header comment for the
// one-time operator provisioning step: `kubectl create secret generic
// platform-dr-game-day-cron-secret --from-literal=secret=...` in the
// `platform-console` namespace, then setting DR_GAME_DAY_CRON_SECRET on
// the console's own Deployment). Checked BEFORE any session cookie so
// the CronJob's Pod (which carries no session) can reach this route at
// all -- no session-based caller is ever expected to hit this route
// directly, it exists only for the scheduler.
//
// One platform-wide CronJob, same shape as
// createExportSubscriptionCronJob/POST /api/orgs/_cron/export-subscription:
// this single route fans out across every org, rather than one CronJob
// object per org, since the eligible set (enterprise-tier, region-pinned)
// changes over time and re-provisioning a per-org CronJob on every tier/
// region change would be real extra k8s churn for no benefit -- listOrgs
// is cheap and already the source of truth every other cross-org sweep in
// this repo (e.g. lib/s3-export-subscription.ts's runDueExportSubscriptions)
// reads from directly.
//
// Only orgs that are BOTH enterprise-tier (getOrgProjectTier + tierAtLeast,
// the same gate setOrgRegion enforces at write time) AND already have a
// region pinned (org.region set) are drilled -- an org that has never
// pinned a region has no `fromRegion` to drill FROM, and a sub-enterprise
// org could never have passed setOrgRegion's own tier gate to get one.
// `toRegion` is picked as any OTHER real, live cluster node region
// (listNodeRegions) -- an org with only one live region available in the
// whole cluster is skipped (recorded, never silently dropped) since there
// is no real failover target to drill against.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.DR_GAME_DAY_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-dr-game-day-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: DR_GAME_DAY_SYSTEM_ACTOR,
      method: "POST",
      path: "/api/cron/dr-game-day",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgsResult.error }, { status: 502 });
  }

  const regionsResult = await listNodeRegions();
  if (!regionsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: DR_GAME_DAY_SYSTEM_ACTOR,
      method: "POST",
      path: "/api/cron/dr-game-day",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: regionsResult.error }, { status: 502 });
  }
  const liveRegions = regionsResult.data;

  const drilled: Array<{ orgId: string; wouldSucceed: boolean }> = [];
  const skipped: Array<{ orgId: string; reason: string }> = [];

  for (const org of orgsResult.data) {
    if (!org.region) {
      continue; // never pinned a region -- nothing to drill FROM, not an eligible enterprise DR customer yet
    }
    const tierResult = await getOrgProjectTier(org.namespace);
    if (!tierResult.ok || !tierAtLeast(tierResult.data, "enterprise")) {
      continue; // sub-enterprise org can never have a real region pin (setOrgRegion's own gate) -- defensive, should not occur
    }
    const toRegion = liveRegions.find((r) => r !== org.region);
    if (!toRegion) {
      skipped.push({ orgId: org.id, reason: `no other live cluster region besides '${org.region}' to drill against` });
      continue;
    }

    const drillResult = await runDrGameDay(org.id, org.region, toRegion);
    if (!drillResult.ok) {
      skipped.push({ orgId: org.id, reason: drillResult.error });
      continue;
    }
    await recordDrGameDayResult(DR_GAME_DAY_SYSTEM_ACTOR, newRequestId(), drillResult.data);
    drilled.push({ orgId: org.id, wouldSucceed: drillResult.data.wouldSucceed });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: DR_GAME_DAY_SYSTEM_ACTOR,
    method: "POST",
    path: `/api/cron/dr-game-day?drilled=${drilled.length}&skipped=${skipped.length}`,
    status: 200,
    requestId,
  });

  return NextResponse.json({ drilled, skipped });
}
