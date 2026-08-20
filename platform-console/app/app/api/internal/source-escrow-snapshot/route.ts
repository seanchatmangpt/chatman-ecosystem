import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requestSourceEscrowSnapshot, SOURCE_ESCROW_NAMESPACE } from "@/lib/source-escrow-attestation";

// Real, unattended poller endpoint the "source-escrow-snapshot"
// scheduled CronJob fires -- authenticated the SAME shared-secret-header
// pattern as every other /api/internal/* poller (see
// fault-scan-snapshot/route.ts's own header comment for the one-time
// operator provisioning step: `kubectl create secret generic
// platform-source-escrow-cron-secret --from-literal=secret=...` in the
// `platform-console` namespace, then setting the matching
// `SOURCE_ESCROW_CRON_SECRET` env on the console's own Deployment).
// Checked BEFORE anything else so the CronJob's Pod (which carries no
// session) can reach this route at all.
//
// This route never signs or persists an attestation on its own say-so:
// it calls the exact same lib/source-escrow-attestation.ts's
// `requestSourceEscrowSnapshot` an owner's own POST
// /api/compliance/source-escrow does, which files (or, once a fresh
// approval already exists, applies) a real `source-escrow.snapshot`
// maker-checker approval request -- same "auto-FILE, human approves"
// pattern lib/rotation-compliance.ts's poller path already establishes
// for `compliance.rotation-block`. The periodic cadence this route
// exists for is the collection of a fresh, real release snapshot on a
// schedule; the actual signing/escrow of that snapshot still always
// requires a second, distinct owner-role human sign-off.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.SOURCE_ESCROW_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-source-escrow-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const result = await requestSourceEscrowSnapshot("source-escrow-snapshot-cronjob", SOURCE_ESCROW_NAMESPACE);

  if (!result.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "source-escrow-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/source-escrow-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "source-escrow-snapshot-cronjob",
    method: "POST",
    path: "/api/internal/source-escrow-snapshot",
    status: result.data.applied ? 201 : 202,
    requestId,
  });

  return NextResponse.json(
    {
      applied: result.data.applied,
      approval: result.data.approval,
      record: result.data.record,
    },
    { status: result.data.applied ? 201 : 202 },
  );
}
