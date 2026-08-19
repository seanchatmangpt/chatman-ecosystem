import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { getApproval, recordApprovalDecision } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real second-approver decision endpoint: the caller must be a DISTINCT
// identity from whoever filed the request AND hold role >= owner --
// exactly the maker-checker two-person-integrity control this whole
// module exists for. lib/approval-workflow.ts's recordApprovalDecision
// already refuses a same-identity decision server-side (never trusting a
// client claim); this route turns that refusal into the real 403 the
// spec requires.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const result = await getApproval(id);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "approval request not found" }, { status: 404 });
  }
  return NextResponse.json({ approval: result.data });
}

export async function POST(
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

  // Approving/rejecting a high-risk action is itself an owner-level
  // decision -- "role >= owner" per the spec, checked against this
  // console's own platform-console-org-roles ConfigMap the same way
  // every other owner-gated route in this repo (lib/authz.ts's
  // requireRole) already does.
  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/approvals/${id}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const decision = body?.decision;
  if (decision !== "approved" && decision !== "rejected") {
    return NextResponse.json(
      { error: "decision must be 'approved' or 'rejected'" },
      { status: 400 },
    );
  }
  const reason = typeof body?.reason === "string" ? body.reason.trim() : undefined;

  const result = await recordApprovalDecision({
    requestId: id,
    decision,
    approvedBy: actor,
    reason,
  });

  if (!result.ok) {
    if (result.error === "not_found") {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: `/api/approvals/${id}`,
        status: 404,
        requestId,
      });
      return NextResponse.json({ error: "approval request not found" }, { status: 404 });
    }
    if (result.error === "already_decided") {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: `/api/approvals/${id}`,
        status: 409,
        requestId,
      });
      return NextResponse.json(
        { error: "this approval request has already been decided" },
        { status: 409 },
      );
    }
    if (result.error === "self_approval") {
      // Real two-person integrity: the SAME identity that filed the
      // request may never be the one who approves or rejects it.
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: `/api/approvals/${id}`,
        status: 403,
        requestId,
      });
      return NextResponse.json(
        { error: "forbidden: the requester cannot approve or reject their own request" },
        { status: 403 },
      );
    }
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/approvals/${id}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/approvals/${id}`,
    status: 200,
    requestId,
  });
  return NextResponse.json({ approval: result.data });
}
