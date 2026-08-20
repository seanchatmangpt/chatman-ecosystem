import { NextRequest, NextResponse } from "next/server";
import { newRequestId, queryOrgActivityDigest, renderOrgActivityDigestMarkdown, writeAuditLogEntry } from "@/lib/audit-db";
import { appendActivityDigestSnapshot } from "@/lib/audit-digest-history";
import { listOrgs } from "@/lib/orgs";
import { dispatchToRoutedTargets } from "@/lib/alert-routing";

// Real, unattended weekly poller for the customer-facing team-activity
// audit digest -- same shared-secret-header authentication pattern as
// app/api/cron/retention-purge/route.ts and app/api/cron/dr-game-day/
// route.ts (see either header comment for the one-time operator
// provisioning step: `kubectl create secret generic
// platform-audit-activity-digest-cron-secret --from-literal=secret=...`
// in the `platform-console` namespace, then setting
// AUDIT_ACTIVITY_DIGEST_CRON_SECRET on the console's own Deployment).
// Checked BEFORE any session cookie so the CronJob's Pod (which carries
// no session) can reach this route at all -- no session-based caller is
// ever expected to hit this route directly, it exists only for the
// scheduler. lib/scheduled-jobs.ts's createAuditActivityDigestCronJob
// provisions the real k8s CronJob object that fires this route.
//
// One platform-wide CronJob, same fan-out-over-listOrgs shape as
// app/api/cron/dr-game-day/route.ts: this single route computes ONE
// digest per org (via lib/audit-db.ts's queryOrgActivityDigest, scoped
// to the last 7 days) rather than one CronJob object per org -- the
// eligible set (every org) never needs re-provisioning the way
// dr-game-day's enterprise-tier/region-pinned set does, so a straight
// loop over listOrgs is the simplest correct shape.
//
// Push, not pull: GET /api/audit/activity-digest already lets a
// compliance officer pull a digest on demand, but the whole point of
// "reduce their own review burden" is not making them remember to ask.
// Every run does BOTH of the two delivery mechanisms the spec allows,
// additively:
//  1. Persists the digest via lib/audit-digest-history.ts's
//     appendActivityDigestSnapshot -- the same persisted-snapshot
//     pattern lib/cost-report-history.ts's cost & usage report history
//     already established, so "what did last week's filed digest say"
//     is answerable later without recomputing it.
//  2. Pushes it through lib/alert-routing.ts's existing channel matrix
//     (dispatchToRoutedTargets, eventType "security" -- who-did-what
//     visibility is a security-posture signal, the same taxonomy bucket
//     GET /api/audit's owner-only gate already treats it as) so an org
//     that has configured an email/Slack/webhook routing rule for
//     security events gets this digest pushed to that same destination,
//     with zero new routing UI. An org with no matching rule configured
//     gets zero deliveries here (dispatchToRoutedTargets's own
//     documented no-op), which is correct -- persistence (1) still runs
//     regardless, so the digest is never lost, only not proactively
//     pushed.
//
// A per-org failure (digest computation error, snapshot persistence
// error) is recorded and the loop continues to the next org -- one org's
// digest failing must never block every other org's weekly evidence
// artifact from being produced.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.AUDIT_ACTIVITY_DIGEST_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-audit-activity-digest-cron-secret");
  return presented === expected;
}

const AUDIT_ACTIVITY_DIGEST_SYSTEM_ACTOR = "audit-activity-digest-cron";
const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: AUDIT_ACTIVITY_DIGEST_SYSTEM_ACTOR,
      method: "POST",
      path: "/api/cron/audit-activity-digest",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgsResult.error }, { status: 502 });
  }

  const sinceDate = new Date(Date.now() - SEVEN_DAYS_MS).toISOString();

  const digested: Array<{ orgId: string; totalEvents: number; actorCount: number; pushed: number }> = [];
  const failed: Array<{ orgId: string; reason: string }> = [];

  for (const org of orgsResult.data) {
    const digestResult = await queryOrgActivityDigest(org.id, sinceDate);
    if (!digestResult.ok) {
      failed.push({ orgId: org.id, reason: `digest: ${digestResult.error}` });
      continue;
    }

    const persistResult = await appendActivityDigestSnapshot(digestResult.data);
    if (!persistResult.ok) {
      failed.push({ orgId: org.id, reason: `persist: ${persistResult.error}` });
      continue;
    }

    const dispatches = await dispatchToRoutedTargets(org.id, "security", {
      kind: "audit-activity-digest",
      sinceDate: digestResult.data.sinceDate,
      generatedAt: digestResult.data.generatedAt,
      totalEvents: digestResult.data.totalEvents,
      actors: digestResult.data.actors,
      markdown: renderOrgActivityDigestMarkdown(digestResult.data),
    });

    digested.push({
      orgId: org.id,
      totalEvents: digestResult.data.totalEvents,
      actorCount: digestResult.data.actors.length,
      pushed: dispatches.filter((d) => d.ok).length,
    });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: AUDIT_ACTIVITY_DIGEST_SYSTEM_ACTOR,
    method: "POST",
    path: "/api/cron/audit-activity-digest",
    status: 200,
    requestId,
  });

  return NextResponse.json({
    orgCount: orgsResult.data.length,
    digestedCount: digested.length,
    digested,
    failed,
  });
}
