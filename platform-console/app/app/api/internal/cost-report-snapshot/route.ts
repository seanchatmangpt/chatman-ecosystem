import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import { ILLUSTRATIVE_RATES, getNamespaceUsageMetrics } from "@/lib/invoice-preview";
import { appendCostReportSnapshot, type CostReportSnapshot } from "@/lib/cost-report-history";

// Real, unattended poller endpoint the "cost-report-snapshot"
// lib/scheduled-jobs.ts CronJob command fires -- authenticated the SAME
// shared-secret-header pattern as POST /api/cron/retention-purge and
// POST /api/orgs/[id]/compliance-reports (see either route's own header
// comment for the one-time operator provisioning step: `kubectl create
// secret generic platform-cost-report-cron-secret
// --from-literal=secret=...` in the `platform-console` namespace, then
// setting the matching `COST_REPORT_CRON_SECRET` env on the console's own
// Deployment). Checked BEFORE anything else so the CronJob's Pod (which
// carries no session) can reach this route at all -- no session-based
// caller is ever expected to hit this route directly, it exists only for
// the scheduler.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.COST_REPORT_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-cost-report-cron-secret");
  return presented === expected;
}

// The window a single snapshot covers -- fixed at 24h, matching the
// smallest sane recurring cadence a FinOps trend line needs (a
// once-daily CronJob schedule); an operator scheduling this command more
// often than daily still gets one real, honest 24h-accumulated figure
// per firing, never an artificially shorter/longer window silently
// inferred from firing cadence.
const SNAPSHOT_WINDOW_LABEL = "24h";
const SNAPSHOT_WINDOW_HOURS = 24;

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // `namespace` travels as a header, threaded in by
  // lib/scheduled-jobs.ts's buildContainerCommand ("cost-report-snapshot"
  // case) from this CronJob's OWN namespace -- validated here against the
  // same fixed `SCHEDULABLE_NAMESPACES` allowlist the CronJob itself was
  // created against, never trusted as free-form request text.
  const namespace = request.headers.get("x-cost-report-namespace") ?? "";
  if (!isSchedulableNamespace(namespace)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "cost-report-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/cost-report-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "x-cost-report-namespace header must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  const windowEnd = new Date();
  const windowStart = new Date(windowEnd.getTime() - SNAPSHOT_WINDOW_HOURS * 60 * 60 * 1000);

  // Reuses the exact real, metered-from-Prometheus computation
  // lib/invoice-preview.ts's on-demand cost preview already exposes --
  // this route never re-implements the PromQL, it only calls the same
  // primitive and persists the result as one point-in-time record.
  const metricsResult = await getNamespaceUsageMetrics(
    namespace,
    SNAPSHOT_WINDOW_LABEL,
    SNAPSHOT_WINDOW_HOURS,
  );

  if (!metricsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "cost-report-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/cost-report-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: metricsResult.error }, { status: 502 });
  }

  const { cpuCoreHours, memoryGiBHours } = metricsResult.data;
  const illustrativeCost =
    cpuCoreHours * ILLUSTRATIVE_RATES.cpuPerCoreHour + memoryGiBHours * ILLUSTRATIVE_RATES.memoryPerGiBHour;

  const snapshot: CostReportSnapshot = {
    namespace,
    windowStart: windowStart.toISOString(),
    windowEnd: windowEnd.toISOString(),
    cpuCoreHours,
    memoryGiBHours,
    illustrativeCost,
    capturedAt: windowEnd.toISOString(),
  };

  const appendResult = await appendCostReportSnapshot(snapshot);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "cost-report-snapshot-cronjob",
    method: "POST",
    path: "/api/internal/cost-report-snapshot",
    status: appendResult.ok ? 201 : 502,
    requestId,
  });

  if (!appendResult.ok) {
    return NextResponse.json({ error: appendResult.error }, { status: 502 });
  }
  return NextResponse.json({ snapshot }, { status: 201 });
}
