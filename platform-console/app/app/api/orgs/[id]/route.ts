import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { deleteOrg, getOrg } from "@/lib/orgs";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real, maker-checker-gated org deletion. `org.delete` is one of
// lib/approval-workflow.ts's ACTIONS_REQUIRING_APPROVAL: deleting a
// tenant's Namespace is irreversible and takes down every real Project,
// Database, Secret, and ConfigMap that customer owns, exactly the
// "can take down production" class of action Fortune 5 change-management
// policy requires a second, distinct approver for -- lib/authz.ts's
// requireRoleIn alone (an owner acting alone) is not that control.
//
// Flow:
//   1. Caller must hold role >= owner IN THIS ORG's own namespace (same
//      boundary branding's PUT already uses) -- an owner is required to
//      even file the request, not just to approve it.
//   2. requireApproval checks for a fresh (<=24h) status:"approved" row
//      for (action: "org.delete", targetId: org id). None exists on the
//      first call -- a new pending request is created and this route
//      returns 202 with it instead of deleting anything.
//   3. A SECOND, distinct owner-role identity calls
//      POST /api/approvals/[id] {decision:"approved"} (recordApprovalDecision
//      refuses same-identity approval server-side).
//   4. The original caller retries DELETE -- requireApproval now finds
//      the fresh approved row and the real deleteOrg runs.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const approval = await requireApproval({
    action: "org.delete",
    targetId: id,
    requestedBy: actor,
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    // No fresh second-approver sign-off yet: a pending approval request
    // was just created (or already existed) -- the real action does NOT
    // run. 202 Accepted, not 200/201: the request was accepted, not
    // completed.
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "org.delete requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this deletion, ` +
          "then retry DELETE.",
      },
      { status: 202 },
    );
  }

  const result = await deleteOrg(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/orgs/${id}`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ deleted: true, approvedBy: approval.approval.approvedBy });
}
