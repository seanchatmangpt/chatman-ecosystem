import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import { getOrg, getOrgSsoGroupMappings } from "@/lib/orgs";
import { getOrgRoleAssignmentsIn } from "@/lib/authz";
import { computeSsoRoleDrift } from "@/lib/sso-role-drift";
import { appendSsoRoleDriftSnapshot, buildSsoRoleDriftSnapshot } from "@/lib/sso-role-drift-history";

// Real, unattended poller endpoint for continuous SSO/SCIM Role-Mapping
// Drift posture monitoring -- the scheduled counterpart to the on-demand
// GET /api/orgs/[id]/sso-role-drift. Authenticated the SAME
// shared-secret-header pattern as POST /api/internal/fault-scan-snapshot
// (see that route's own header comment for the one-time operator
// provisioning step: `kubectl create secret generic
// platform-sso-role-drift-cron-secret --from-literal=secret=...` in the
// `platform-console` namespace, then setting the matching
// `SSO_ROLE_DRIFT_CRON_SECRET` env on the console's own Deployment).
// Checked BEFORE anything else so a CronJob Pod (which carries no
// session) can reach this route at all -- no session-based caller is
// ever expected to hit this route directly.
//
// Runs the SAME diagnose-only computation GET /api/orgs/[id]/sso-role-
// drift already runs on demand (`computeSsoRoleDrift` over the real
// configured mappings + real role assignments, no new drift logic here)
// and only PERSISTS the real result via
// lib/sso-role-drift-history.ts's appendSsoRoleDriftSnapshot -- it never
// files approval requests and never mutates any mapping or role
// assignment, consistent with the on-demand route's own read-only
// boundary.
//
// Disclosed gap: unlike "fault-scan-snapshot" and
// "latency-benchmark-snapshot", this command is not yet registered in
// lib/scheduled-jobs.ts's `AllowedCommandId` union / buildContainerCommand
// switch, so no CronJob calls this route automatically today -- an
// operator (or a future pass wiring that registration) must invoke it,
// same shared-secret contract, to get a recurring schedule. The route
// itself is real and fully functional; only the self-service CronJob
// provisioning UI for this specific command is the stated gap.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.SSO_ROLE_DRIFT_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-sso-role-drift-cron-secret");
  return presented === expected;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // `orgId` travels as a header, same "namespace doubles as a registry
  // orgId" convention every other SCHEDULABLE_NAMESPACES-backed internal
  // cron route already relies on (see
  // POST /api/internal/fault-scan-snapshot's own header comment).
  const orgId = request.headers.get("x-sso-role-drift-org") ?? "";
  if (!isSchedulableNamespace(orgId)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "sso-role-drift-snapshot-cronjob",
      method: "POST",
      path: "/api/internal/sso-role-drift-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "x-sso-role-drift-org header must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "sso-role-drift-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/sso-role-drift-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const org = orgResult.data;
  if (!org) {
    return NextResponse.json({ error: `org not found: ${orgId}` }, { status: 404 });
  }

  const [mappingsResult, assignmentsResult] = await Promise.all([
    getOrgSsoGroupMappings(orgId),
    getOrgRoleAssignmentsIn(org.namespace),
  ]);

  const readsOk = mappingsResult.ok && assignmentsResult.ok;
  if (!mappingsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "sso-role-drift-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/sso-role-drift-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: mappingsResult.error }, { status: 502 });
  }
  if (!assignmentsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "sso-role-drift-snapshot-cronjob",
      orgId,
      method: "POST",
      path: "/api/internal/sso-role-drift-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: assignmentsResult.error }, { status: 502 });
  }

  const report = computeSsoRoleDrift(orgId, mappingsResult.data, assignmentsResult.data);
  const snapshot = buildSsoRoleDriftSnapshot(report);
  const appendResult = await appendSsoRoleDriftSnapshot(snapshot);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "sso-role-drift-snapshot-cronjob",
    orgId,
    method: "POST",
    path: "/api/internal/sso-role-drift-snapshot",
    status: readsOk && appendResult.ok ? 201 : 502,
    requestId,
  });

  if (!appendResult.ok) {
    return NextResponse.json({ error: appendResult.error }, { status: 502 });
  }
  return NextResponse.json({ snapshot }, { status: 201 });
}
