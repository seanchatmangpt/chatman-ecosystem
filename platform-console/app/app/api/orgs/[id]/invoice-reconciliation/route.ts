import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  decideInvoiceReconciliation,
  listInvoiceReconciliations,
  recordInvoiceReconciliation,
  validateInvoiceReconciliationInput,
} from "@/lib/invoice-reconciliation";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real Invoice / Purchase-Order Reconciliation Ledger endpoint: closes
// the gap that lib/overage-billing.ts's real, Stripe-billed usage
// overage (`StoredOverage.overageCostUsd`) and lib/contract-renewals.ts's
// real Stripe-derived contract period have never been joined against the
// customer's OWN procurement-side PO number / asserted contract cap --
// today that reconciliation happens off-platform, in a spreadsheet
// finance/procurement keeps by hand. Landing this closes it: finance can
// see, for any org, exactly how a real overage amount reconciles against
// what the customer's own PO says they owe, with a durable auditable
// record backing the eventual payment decision. See
// lib/invoice-reconciliation.ts for the full storage/approval contract.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree, and
// deliberately OWNER-gated on every verb (not the "viewer can read"
// carve-out app/api/orgs/[id]/pricing-override/route.ts's GET uses) --
// a reconciliation record exposes the exact real overage dollar amount
// and the customer's own PO reference together, which is financial
// detail this repo's existing convention (see that same
// pricing-override route's PUT/DELETE) reserves to the org's owner:
//   - GET: owner of THIS org -- lists every reconciliation record filed
//     for this org, most recently filed first.
//   - POST: owner of THIS org. Files ONE new reconciliation, computed
//     against the real current lib/overage-billing.ts StoredOverage for
//     the org's namespace. Filing itself never authorizes payment (no
//     approval gate) -- it only computes and durably stores the real
//     numbers a second approver reviews next.
//   - PUT: owner of THIS org, gated behind the SAME maker-checker
//     `invoice.reconciliation.approve` approval workflow
//     (lib/approval-workflow.ts's requireApproval) `pricing.override`
//     already uses -- one owner's own say-so is never sufficient by
//     itself to mark a real invoiced amount payable; a second, distinct
//     owner-role approver must sign off first.

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

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/invoice-reconciliation`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listInvoiceReconciliations(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/invoice-reconciliation`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ reconciliations: result.data });
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
      method: "POST",
      path: `/api/orgs/${id}/invoice-reconciliation`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const poNumber = typeof body?.poNumber === "string" ? body.poNumber : "";
  const contractCapUsd = typeof body?.contractCapUsd === "number" ? body.contractCapUsd : NaN;

  const validationError = validateInvoiceReconciliationInput({ poNumber, contractCapUsd });
  if (validationError) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/invoice-reconciliation`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const result = await recordInvoiceReconciliation({
    orgId: id,
    namespace: orgResult.data.namespace,
    poNumber,
    contractCapUsd,
    filedBy: actor,
  });
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/invoice-reconciliation`,
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ reconciliation: result.data }, { status: 201 });
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
      path: `/api/orgs/${id}/invoice-reconciliation`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const reconciliationId = typeof body?.reconciliationId === "string" ? body.reconciliationId.trim() : "";
  const decision = body?.decision === "approved" || body?.decision === "rejected" ? body.decision : "";
  const reason = typeof body?.reason === "string" ? body.reason : undefined;

  if (!reconciliationId) {
    return NextResponse.json({ error: "reconciliationId is required" }, { status: 400 });
  }
  if (!decision) {
    return NextResponse.json({ error: "decision must be 'approved' or 'rejected'" }, { status: 400 });
  }

  const approval = await requireApproval({
    action: "invoice.reconciliation.approve",
    targetId: reconciliationId,
    requestedBy: actor,
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/invoice-reconciliation`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/invoice-reconciliation`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "invoice.reconciliation.approve requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize this ` +
          "reconciliation decision, then retry PUT.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists -- a rejected `decision` from the caller
  // needs no second approver (declining payment is never a money-moving
  // action), but this route requires the SAME approval gate for both
  // outcomes so a caller cannot bypass maker-checker by always claiming
  // "rejected" and then re-filing; only the actually-approved decision
  // (recorded by the second approver via POST /api/approvals) is ever
  // trusted -- decideInvoiceReconciliation itself still enforces its own
  // "not_decidable" fail-closed check below.
  const result = await decideInvoiceReconciliation({
    id: reconciliationId,
    decision: decision === "approved" ? "approved_for_payment" : "rejected",
    decidedBy: approval.approval.approvedBy ?? actor,
    reason,
  });
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/invoice-reconciliation`,
    status: result.ok ? 200 : result.error === "not_found" ? 404 : 502,
    requestId,
  });
  if (!result.ok) {
    if (result.error === "not_found") {
      return NextResponse.json({ error: "reconciliation not found" }, { status: 404 });
    }
    if (result.error === "not_decidable") {
      return NextResponse.json(
        { error: "reconciliation is not pending_approval" },
        { status: 409 },
      );
    }
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ reconciliation: result.data, requiredApproval: true });
}
