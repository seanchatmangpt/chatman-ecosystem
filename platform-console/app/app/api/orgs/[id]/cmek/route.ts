import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, type CmekProvider } from "@/lib/orgs";
import { getCmekStatus, requestCmekKeyBinding, clearCmekKeyBinding } from "@/lib/cmek";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real Customer-Managed Encryption Key (CMEK/BYOK) binding endpoint
// (lib/cmek.ts, lib/orgs.ts's CmekKeyBinding) -- the specific control a
// Fortune 5 security review asks for before this platform is trusted to
// store regulated data: proof that this org's real live Secrets/PVCs are
// encrypted under a customer-supplied KMS key reference, not the
// platform's shared default, and that a second, distinct human signed off
// before that key reference was ever bound or rotated.
//
// Auth model (mirrors app/api/orgs/[id]/pricing-override/route.ts
// exactly):
//   - GET: any authenticated member of THIS org (viewer and up) -- the
//     current binding plus a live compliance-enforcement scan
//     (lib/cmek.ts's scanCmekEnforcement, real listSecrets/
//     listNamespacePvcs annotation reads) is not itself a privileged
//     action; a security reviewer or the org's own operators routinely
//     need to see it.
//   - PUT: owner of THIS org specifically, gated behind the SAME
//     maker-checker `cmek.key-binding` approval workflow
//     (lib/approval-workflow.ts's requireApproval) `pricing.override`/
//     `compliance.rotation-block` already use -- one owner's own
//     assertion that a customer key should be bound is never sufficient
//     by itself; a second, distinct owner-role approver must sign off
//     first. Binds (first key) or rotates (replaces an existing key)
//     depending on whether a binding already exists.
//   - DELETE: same owner + approval gate as PUT -- clears an existing
//     binding, reverting the org to the platform's own default
//     encryption key.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/cmek`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const statusResult = await getCmekStatus(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/cmek`,
    status: statusResult.ok ? 200 : 502,
    requestId,
  });
  if (!statusResult.ok) {
    return NextResponse.json({ error: statusResult.error }, { status: 502 });
  }

  return NextResponse.json({
    binding: statusResult.data.binding,
    compliant: statusResult.data.binding !== null && statusResult.data.violations.length === 0,
    secretsChecked: statusResult.data.secretsChecked,
    pvcsChecked: statusResult.data.pvcsChecked,
    violations: statusResult.data.violations,
    scannedAt: statusResult.data.scannedAt,
  });
}

export async function PUT(
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
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/cmek`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const provider = typeof body?.provider === "string" ? (body.provider as CmekProvider) : ("" as CmekProvider);
  const keyRef = typeof body?.keyRef === "string" ? body.keyRef.trim() : "";
  const reason = typeof body?.reason === "string" ? body.reason.trim() : "";

  const outcome = await requestCmekKeyBinding(orgResult.data, { provider, keyRef, reason }, actor);

  if ("error" in outcome) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/cmek`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: outcome.error }, { status: 400 });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/cmek`,
    status: outcome.applied ? 200 : 202,
    requestId,
  });

  if (!outcome.applied) {
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: outcome.approval,
        message:
          "cmek.key-binding requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${outcome.approval.requestId} {decision:'approved'} to authorize this key binding, then retry PUT.`,
      },
      { status: 202 },
    );
  }

  return NextResponse.json({
    applied: true,
    binding: outcome.binding,
    approvedBy: outcome.approval.approvedBy,
    reannotated: outcome.reannotated,
    reannotateErrors: outcome.reannotateErrors,
  });
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
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}/cmek`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const outcome = await clearCmekKeyBinding(orgResult.data, actor);

  if ("error" in outcome) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}/cmek`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: outcome.error }, { status: 502 });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/orgs/${id}/cmek`,
    status: outcome.applied ? 200 : 202,
    requestId,
  });

  if (!outcome.applied) {
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: outcome.approval,
        message:
          "cmek.key-binding requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${outcome.approval.requestId} {decision:'approved'} to authorize clearing this org's CMEK ` +
          "binding, then retry DELETE.",
      },
      { status: 202 },
    );
  }

  return NextResponse.json({
    applied: true,
    binding: null,
    reannotated: outcome.reannotated,
    reannotateErrors: outcome.reannotateErrors,
  });
}
