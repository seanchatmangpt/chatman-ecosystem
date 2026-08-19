import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import { getOrg } from "@/lib/orgs";
import { collectClusterStateForOrg, hasK8sFaultScanner, runK8sFaultScan } from "@/lib/k8s-fault-scan";
import { appendFaultScanSnapshot, buildFaultScanSnapshot } from "@/lib/k8s-fault-scan-history";

// Real, unattended poller endpoint the "fault-scan-snapshot"
// lib/scheduled-jobs.ts CronJob command fires -- authenticated the SAME
// shared-secret-header pattern as POST /api/internal/latency-benchmark-snapshot
// (see that route's own header comment for the one-time operator
// provisioning step: `kubectl create secret generic
// platform-fault-scan-cron-secret --from-literal=secret=...` in the
// `platform-console` namespace, then setting the matching
// `FAULT_SCAN_CRON_SECRET` env on the console's own Deployment). Checked
// BEFORE anything else so the CronJob's Pod (which carries no session)
// can reach this route at all -- no session-based caller is ever
// expected to hit this route directly, it exists only for the
// scheduler.
//
// Stated plainly, matching lib/k8s-fault-scan.ts's own scope discipline:
// this route runs the SAME diagnose-only scan POST /api/k8s-fault-scan
// already runs on demand (`collectClusterStateForOrg` +
// `runK8sFaultScan`, no new scan logic here) and only PERSISTS the real
// result via lib/k8s-fault-scan-history.ts's appendFaultScanSnapshot --
// it never files approval requests and never remediates/actuates
// anything, consistent with the on-demand route's own "diagnose, never
// remediate" boundary. Continuous posture monitoring is the persisted
// trend line this snapshot produces, nothing more.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.FAULT_SCAN_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-fault-scan-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // `orgId` travels as a header, threaded in by lib/scheduled-jobs.ts's
  // buildContainerCommand ("fault-scan-snapshot" case) from this
  // CronJob's OWN namespace -- validated here against the same fixed
  // `SCHEDULABLE_NAMESPACES` allowlist the CronJob itself was created
  // against, never trusted as free-form request text. Same "namespace
  // doubles as a registry orgId" convention every other
  // SCHEDULABLE_NAMESPACES-backed internal cron route already relies on
  // (lib/orgs.ts's getOrg falls back to treating an unregistered id as
  // the namespace itself).
  const orgId = request.headers.get("x-fault-scan-org") ?? "";
  if (!isSchedulableNamespace(orgId)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "fault-scan-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/fault-scan-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "x-fault-scan-org header must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  if (!hasK8sFaultScanner()) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "fault-scan-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/fault-scan-snapshot",
      status: 503,
      requestId,
    });
    return NextResponse.json(
      { error: "autofde-lab k8s-fault-taxonomy analysis not yet available: scanner CLI not found" },
      { status: 503 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "fault-scan-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/fault-scan-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const org = orgResult.data;
  if (!org) {
    return NextResponse.json({ error: `org not found: ${orgId}` }, { status: 404 });
  }
  if (!org.enableFaultScan) {
    // Not scanned, not an error -- same "opt-in gate, silently skip
    // rather than fail the CronJob run" reasoning
    // POST /api/k8s-fault-scan's own 403 already documents for the
    // on-demand path, adapted for an unattended poller: a namespace
    // that hasn't opted in yet is a normal, expected daily no-op, not a
    // scheduler failure.
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "fault-scan-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/fault-scan-snapshot",
      status: 204,
      requestId,
    });
    return new NextResponse(null, { status: 204 });
  }

  const clusterState = await collectClusterStateForOrg(org.namespace);
  const scanResult = runK8sFaultScan(clusterState);
  if (!scanResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "fault-scan-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/fault-scan-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: scanResult.error }, { status: 502 });
  }

  const snapshot = buildFaultScanSnapshot(orgId, scanResult.data);
  const appendResult = await appendFaultScanSnapshot(snapshot);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "fault-scan-snapshot-cronjob",
    orgId,
    method: "POST",
    path: "/api/internal/fault-scan-snapshot",
    status: appendResult.ok ? 201 : 502,
    requestId,
  });

  if (!appendResult.ok) {
    return NextResponse.json({ error: appendResult.error }, { status: 502 });
  }
  return NextResponse.json({ snapshot }, { status: 201 });
}
