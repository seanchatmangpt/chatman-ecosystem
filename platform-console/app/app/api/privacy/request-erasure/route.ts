import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { requireApproval } from "@/lib/approval-workflow";
import { createDsarRequest, runDsarErasure } from "@/lib/dsar";

// Real GDPR Art.17 / CCPA "right to delete" erasure-request endpoint --
// maker-checker gated exactly like DELETE /api/orgs/[id]: erasure is
// irreversible and mutates durable state (the audit trail, the org's own
// membership record), the same "destructive action a second, distinct
// owner-role approver must sign off on" bar lib/approval-workflow.ts's
// header comment names DSAR erasure as a textbook fit for.
//
// Flow, mirroring DELETE /api/orgs/[id] exactly:
//   1. Caller must hold role >= owner IN THIS ORG's own namespace.
//   2. requireApproval checks for a fresh (<=24h) approved row for
//      (action: "dsar.erasure", targetId: "<orgId>:<subjectEmail>").
//      None exists on the first call -- a pending approval is created
//      and this route returns 202 with it, WITHOUT creating a DSAR
//      request row yet (nothing has been authorized to happen).
//   3. A SECOND, distinct owner-role identity calls
//      POST /api/approvals/[id] {decision:"approved"}.
//   4. The original caller retries POST -- requireApproval now finds the
//      fresh approved row; this route creates the real DSAR erasure
//      request row and runs it to completion synchronously
//      (lib/dsar.ts's runDsarErasure -- bounded work, unlike export).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function targetIdFor(orgId: string, subjectEmail: string): string {
  return `${orgId}:${subjectEmail}`;
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
  const subjectEmail = typeof body?.subjectEmail === "string" ? body.subjectEmail.trim() : "";

  if (!orgId) {
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }
  if (!subjectEmail || !EMAIL_RE.test(subjectEmail)) {
    return NextResponse.json({ error: "subjectEmail is required and must be a valid email" }, { status: 400 });
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
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/privacy/request-erasure (org=${orgId})`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const approval = await requireApproval({
    action: "dsar.erasure",
    targetId: targetIdFor(orgId, subjectEmail),
    requestedBy: actor,
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/privacy/request-erasure (org=${orgId})`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/privacy/request-erasure (org=${orgId})`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "dsar.erasure requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this erasure, ` +
          "then retry POST /api/privacy/request-erasure with the same orgId/subjectEmail.",
      },
      { status: 202 },
    );
  }

  const created = await createDsarRequest({
    orgId,
    subjectEmail,
    kind: "erasure",
    requestedBy: actor,
  });
  if (!created.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/privacy/request-erasure (org=${orgId})`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: created.error }, { status: 502 });
  }

  const result = await runDsarErasure(created.data.requestId);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/privacy/request-erasure (org=${orgId})`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ status: "complete", request: result.data, approvedBy: approval.approval.approvedBy });
}
