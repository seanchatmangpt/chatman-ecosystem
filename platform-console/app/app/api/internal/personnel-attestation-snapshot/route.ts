import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import { getOrg } from "@/lib/orgs";
import { appendPersonnelRosterSnapshot } from "@/lib/personnel-attestation";

// Real, unattended poller endpoint for continuous Workforce Security-
// Training & Background-Check roster trend tracking -- the scheduled
// counterpart to GET /api/compliance/personnel-attestation. Authenticated
// the SAME shared-secret-header pattern as POST /api/internal/sso-role-
// drift-snapshot / POST /api/internal/fault-scan-snapshot (see either
// route's own header comment for the one-time operator provisioning
// step: `kubectl create secret generic
// platform-personnel-attestation-cron-secret --from-literal=secret=...`
// in the `platform-console` namespace, then setting the matching
// `PERSONNEL_ATTESTATION_CRON_SECRET` env on the console's own
// Deployment). Checked BEFORE anything else so a CronJob Pod (which
// carries no session) can reach this route at all -- no session-based
// caller is ever expected to hit this route directly.
//
// Runs the SAME real IAM/audit-log join
// lib/personnel-attestation.ts's buildPersonnelRosterSnapshot already
// runs on demand and only PERSISTS a compact trend point via
// appendPersonnelRosterSnapshot -- it never files an approval request
// and never records/mutates an attestation, consistent with the
// on-demand GET route's own read-only boundary. Never a substitute for a
// human-attested PersonnelAttestationRecord.
//
// Disclosed gap: like sso-role-drift-snapshot, this command is not yet
// registered in lib/scheduled-jobs.ts's `AllowedCommandId` union /
// buildContainerCommand switch, so no CronJob calls this route
// automatically today -- an operator (or a future pass wiring that
// registration) must invoke it, same shared-secret contract, to get a
// recurring schedule. The route itself is real and fully functional;
// only the self-service CronJob provisioning UI for this specific
// command is the stated gap.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.PERSONNEL_ATTESTATION_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-personnel-attestation-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // `orgId` travels as a header, same "namespace doubles as a registry
  // orgId" convention every other SCHEDULABLE_NAMESPACES-backed internal
  // cron route already relies on (see POST /api/internal/sso-role-drift-
  // snapshot's own header comment).
  const orgId = request.headers.get("x-personnel-attestation-org") ?? "";
  if (!isSchedulableNamespace(orgId)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "personnel-attestation-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/personnel-attestation-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "x-personnel-attestation-org header must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "personnel-attestation-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/personnel-attestation-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const org = orgResult.data;
  if (!org) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "personnel-attestation-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/personnel-attestation-snapshot",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `org not found: ${orgId}` }, { status: 404 });
  }

  const appendResult = await appendPersonnelRosterSnapshot(orgId, org.namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "personnel-attestation-snapshot-cronjob",
    orgId,
    method: "POST",
    path: "/api/internal/personnel-attestation-snapshot",
    status: appendResult.ok ? 201 : 502,
    requestId,
  });

  if (!appendResult.ok) {
    return NextResponse.json({ error: appendResult.error }, { status: 502 });
  }
  return NextResponse.json({ snapshot: appendResult.data }, { status: 201 });
}
