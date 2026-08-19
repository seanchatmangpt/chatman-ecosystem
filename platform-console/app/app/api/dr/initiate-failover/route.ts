import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { findBlockingIncident, initiateFailover } from "@/lib/dr-failover";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real, maker-checker-gated multi-region DR failover trigger. Same shape
// as DELETE /api/orgs/[id] (org.delete): an owner of the target org files
// the request, requireApproval creates a pending row on the first call
// (202, nothing runs yet), a SECOND distinct owner approves via
// POST /api/approvals/[id], then a retry of this same POST finds the
// fresh approval and lib/dr-failover.ts's initiateFailover actually runs
// -- which itself unconditionally re-checks the open-incident
// precondition regardless of what already got approved.
//
// Body: { orgId, fromRegion, toRegion, reason }.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const body = await request.json().catch(() => null);
  const orgId = typeof body?.orgId === "string" ? body.orgId.trim() : "";
  const fromRegion = typeof body?.fromRegion === "string" ? body.fromRegion.trim() : "";
  const toRegion = typeof body?.toRegion === "string" ? body.toRegion.trim() : "";
  const reason = typeof body?.reason === "string" ? body.reason.trim() : "";

  if (!orgId || !fromRegion || !toRegion || !reason) {
    return NextResponse.json(
      { error: "orgId, fromRegion, toRegion, and reason are all required" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/dr/initiate-failover/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // Fail-closed pre-check surfaced early with a clear 412, before even
  // creating an approval request -- the SAME precondition
  // initiateFailover itself re-enforces unconditionally, so this is a
  // convenience, not the only enforcement point.
  const blockingIncident = await findBlockingIncident(orgId, fromRegion);
  if (!blockingIncident.ok) {
    return NextResponse.json({ error: blockingIncident.error }, { status: 502 });
  }
  if (!blockingIncident.data) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/dr/initiate-failover/${orgId}`,
      status: 412,
      requestId,
    });
    return NextResponse.json(
      {
        error: `refusing failover: no open incident referencing region '${fromRegion}' exists -- open/annotate one first`,
      },
      { status: 412 },
    );
  }

  const approval = await requireApproval({
    action: "dr.failover",
    targetId: orgId,
    requestedBy: actor,
    resourcePayload: { requestedFailover: { fromRegion, toRegion, reason } },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/dr/initiate-failover/${orgId}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/dr/initiate-failover/${orgId}`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "dr.failover requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this failover, ` +
          "then retry this request.",
      },
      { status: 202 },
    );
  }

  const result = await initiateFailover(orgId, fromRegion, toRegion, reason, actor);
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/dr/initiate-failover/${orgId}`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    initiated: true,
    approvedBy: approval.approval.approvedBy,
    org: result.data.org,
    incident: result.data.incident,
    restoreJob: result.data.restoreJob,
    sourceBackupJob: result.data.sourceBackupJob,
  });
}
