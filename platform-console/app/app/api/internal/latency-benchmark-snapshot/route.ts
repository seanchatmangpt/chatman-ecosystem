import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import { runScheduledLatencyBenchmark } from "@/lib/load-test";
import { appendLatencyBenchmarkSnapshots } from "@/lib/latency-history";

// Real, unattended poller endpoint the "latency-benchmark-snapshot"
// lib/scheduled-jobs.ts CronJob command fires -- authenticated the SAME
// shared-secret-header pattern as POST /api/internal/cost-report-snapshot
// (see that route's own header comment for the one-time operator
// provisioning step: `kubectl create secret generic
// platform-latency-benchmark-cron-secret --from-literal=secret=...` in
// the `platform-console` namespace, then setting the matching
// `LATENCY_BENCHMARK_CRON_SECRET` env on the console's own Deployment).
// Checked BEFORE anything else so the CronJob's Pod (which carries no
// session) can reach this route at all -- no session-based caller is
// ever expected to hit this route directly, it exists only for the
// scheduler.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.LATENCY_BENCHMARK_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-latency-benchmark-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // `orgId` travels as a header, threaded in by lib/scheduled-jobs.ts's
  // buildContainerCommand ("latency-benchmark-snapshot" case) from this
  // CronJob's OWN namespace -- validated here against the same fixed
  // `SCHEDULABLE_NAMESPACES` allowlist the CronJob itself was created
  // against, never trusted as free-form request text.
  const orgId = request.headers.get("x-latency-benchmark-org") ?? "";
  if (!isSchedulableNamespace(orgId)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "latency-benchmark-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/latency-benchmark-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "x-latency-benchmark-org header must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  // Reuses the exact real runLoadTest primitive lib/load-test.ts's
  // on-demand benchmark already exposes -- this route never re-implements
  // load generation, it only calls the same primitive across the whole
  // fixed LOAD_TEST_TARGETS allowlist and persists the results.
  const snapshots = await runScheduledLatencyBenchmark(orgId);

  const appendResult = await appendLatencyBenchmarkSnapshots(snapshots);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "latency-benchmark-snapshot-cronjob",
    method: "POST",
    path: "/api/internal/latency-benchmark-snapshot",
    status: appendResult.ok ? 201 : 502,
    requestId,
  });

  if (!appendResult.ok) {
    return NextResponse.json({ error: appendResult.error }, { status: 502 });
  }
  return NextResponse.json({ snapshots }, { status: 201 });
}
