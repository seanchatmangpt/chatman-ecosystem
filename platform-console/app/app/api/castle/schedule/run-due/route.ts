import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { runDueScheduledVerbs } from "@/lib/scheduled-verbs";

// Real, unattended poller endpoint the CronJob
// lib/batch-jobs.ts's createCastleScheduleCronJob creates fires every 5
// minutes -- authenticated the SAME shared-secret-header pattern
// lib/scheduled-jobs.ts's createComplianceReportCronJob /
// createExportSubscriptionCronJob already establish (see either header
// comment for the one-time operator provisioning step: `kubectl create
// secret generic platform-castle-schedule-cron-secret
// --from-literal=secret=...` in the `platform-console` namespace),
// checked BEFORE any session cookie so the CronJob's Pod (which carries
// no session) can reach this route at all. No session-based caller is
// ever expected to hit this route directly -- it exists only for the
// poller, so it deliberately never falls back to session auth.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.CASTLE_SCHEDULE_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-castle-schedule-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const actor = "castle-schedule-cronjob";
  const result = await runDueScheduledVerbs(actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/castle/schedule/run-due",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ results: result.data });
}
