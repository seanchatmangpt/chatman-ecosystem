import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  defaultAuditRetentionDays,
  purgeExpiredAuditRows,
  RETENTION_PURGE_SYSTEM_ACTOR,
} from "@/lib/retention";
import { isProjectTier } from "@/lib/tiers";

// Real, unattended poller endpoint a per-org (or platform-wide) CronJob
// hits on a schedule -- authenticated the SAME shared-secret-header
// pattern lib/scheduled-jobs.ts's createComplianceReportCronJob /
// createExportSubscriptionCronJob and app/api/castle/schedule/run-due/
// route.ts already establish (see any of those header comments for the
// one-time operator provisioning step: `kubectl create secret generic
// platform-retention-purge-cron-secret --from-literal=secret=...` in the
// `platform-console` namespace, then setting
// RETENTION_PURGE_CRON_SECRET on the console's own Deployment). Checked
// BEFORE any session cookie so the CronJob's Pod (which carries no
// session) can reach this route at all -- no session-based caller is
// ever expected to hit this route directly, it exists only for the
// scheduler.
//
// platform_console.audit_log has no per-row org scoping (see
// lib/retention.ts's header comment), so unlike the per-org backup/
// compliance CronJobs this is a single platform-wide purge -- one
// CronJob fires this route, which purges the whole table against one
// retentionDays window, same "one platform-wide CronJob" shape
// createExportSubscriptionCronJob already established for its own
// platform-wide fan-out.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.RETENTION_PURGE_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-retention-purge-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // Optional body lets an operator override the default window (e.g. a
  // platform-wide policy change, or exercising a specific tier's
  // shorter window) without redeploying the CronJob -- absent/invalid
  // falls back to defaultAuditRetentionDays()'s enterprise-tier floor,
  // never a shorter, silently-assumed default.
  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  const requestedTier = typeof body?.tier === "string" ? body.tier : null;
  const requestedDays = typeof body?.retentionDays === "number" ? body.retentionDays : null;

  const retentionDays =
    requestedDays && Number.isFinite(requestedDays) && requestedDays > 0
      ? requestedDays
      : defaultAuditRetentionDays(
          requestedTier && isProjectTier(requestedTier) ? requestedTier : "enterprise",
        );

  const result = await purgeExpiredAuditRows(retentionDays, RETENTION_PURGE_SYSTEM_ACTOR);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: RETENTION_PURGE_SYSTEM_ACTOR,
    method: "POST",
    path: "/api/cron/retention-purge",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ receipt: result.data });
}
