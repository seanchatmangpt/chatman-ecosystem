import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { findBlockingIncident, getFailoverStatus } from "@/lib/dr-failover";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real polling read for the DR Runbook panel's progress UI: any
// authenticated member of the org (viewer and up) can watch a failover in
// progress -- reading status is not privileged, same boundary GET
// /api/orgs/[id]/region already draws. Re-derives status live from the
// org's real region pin plus the real restore Job's batch/v1 status
// (?restoreJobName=<name>, the Job name POST /api/dr/initiate-failover
// returned) rather than a separately tracked "failover record".
//
// Also surfaces whether an open incident currently blocks OR would
// currently enable a failover away from the org's own pinned region, so
// the panel can render the precondition state without a second endpoint.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/dr/failover-status/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const restoreJobName = request.nextUrl.searchParams.get("restoreJobName") ?? undefined;

  const [statusResult, incidentResult] = await Promise.all([
    getFailoverStatus(orgId, restoreJobName),
    orgResult.data.region
      ? findBlockingIncident(orgId, orgResult.data.region)
      : Promise.resolve({ ok: true as const, data: null }),
  ]);

  const status = statusResult.ok && incidentResult.ok ? 200 : 502;
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/dr/failover-status/${orgId}`,
    status,
    requestId,
  });

  if (!statusResult.ok) {
    return NextResponse.json({ error: statusResult.error }, { status: 502 });
  }
  if (!incidentResult.ok) {
    return NextResponse.json({ error: incidentResult.error }, { status: 502 });
  }

  const restoreJobStatus = statusResult.data.restoreJob?.status ?? null;
  const overallStatus: "no_active_failover" | "in_progress" | "complete" | "failed" =
    !restoreJobName
      ? "no_active_failover"
      : restoreJobStatus === "Complete"
        ? "complete"
        : restoreJobStatus === "Failed"
          ? "failed"
          : "in_progress";

  return NextResponse.json({
    org: statusResult.data.org,
    regionPinned: statusResult.data.regionPinned,
    restoreJob: statusResult.data.restoreJob,
    overallStatus,
    blockingOrEnablingIncident: incidentResult.data,
    failoverEnabled: incidentResult.data !== null,
  });
}
