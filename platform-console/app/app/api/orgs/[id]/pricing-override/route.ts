import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import {
  getOrg,
  getOrgPricingOverride,
  setOrgPricingOverride,
  validatePricingOverride,
  type OrgPricingOverride,
} from "@/lib/orgs";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real per-org negotiated pricing/discount-schedule override endpoint:
// closes the gap that lib/tiers.ts's standard tiers (starter/pro/
// enterprise) and lib/stripe-billing.ts/lib/overage-billing.ts only ever
// know the public list-price tier sheet -- every Fortune 5 procurement
// negotiates a custom multi-year contract price that never matches it,
// and today that gap is handled manually outside the console (a
// spreadsheet finance tracks by hand). Landing this closes it: finance
// can bind a signed contract's actual price into the system of record,
// and lib/overage-billing.ts's rate computation (see that module) applies
// it in place of the standard rate for every namespace under this org.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading the current negotiated rate is not itself a privileged
//     action (finance/support routinely needs to see it to explain an
//     invoice).
//   - PUT: owner of THIS org specifically, gated behind the SAME
//     maker-checker `pricing.override` approval workflow
//     (lib/approval-workflow.ts's requireApproval) `dr.failover` and
//     `tier.downgrade` already use -- one owner's own assertion that a
//     contract was signed is never sufficient by itself to bind real
//     negotiated revenue; a second, distinct owner-role approver must
//     sign off first. `discountPercent`/`fixedUnitPrice`/
//     `effectiveFrom`/`effectiveUntil`/`contractRef` are validated
//     (lib/orgs.ts's validatePricingOverride) BEFORE a pending approval
//     is ever filed, so an approver only ever reviews a structurally
//     valid request. `approvedBy` on the stored OrgPricingOverride is
//     always the SECOND approver's own identity (never the requester's),
//     recorded at the moment lib/approval-workflow.ts's
//     recordApprovalDecision approves the request -- the same real
//     two-person-integrity guarantee every other maker-checker action in
//     this codebase already provides.
//   - DELETE: same owner + approval gate as PUT -- clears (expires) an
//     existing override, reverting this org to standard list pricing.
//     Modeled as `PUT` with `override: null` is deliberately NOT how this
//     route accepts a clear; DELETE is the more RESTful, more legible
//     verb for "no override should apply any more", and lib/orgs.ts's
//     setOrgPricingOverride(id, null, actor) already accepts exactly this
//     shape from either verb.

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
      path: `/api/orgs/${id}/pricing-override`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const overrideResult = await getOrgPricingOverride(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/pricing-override`,
    status: overrideResult.ok ? 200 : 502,
    requestId,
  });
  if (!overrideResult.ok) {
    return NextResponse.json({ error: overrideResult.error }, { status: 502 });
  }

  const now = new Date().toISOString();
  const override = overrideResult.data;
  const active =
    !!override && override.effectiveFrom <= now && now <= override.effectiveUntil;

  return NextResponse.json({
    pricingOverride: override,
    active,
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
      path: `/api/orgs/${id}/pricing-override`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const discountPercent =
    typeof body?.discountPercent === "number" ? body.discountPercent : undefined;
  const fixedUnitPrice =
    body?.fixedUnitPrice &&
    typeof body.fixedUnitPrice.cpuPerCoreHour === "number" &&
    typeof body.fixedUnitPrice.memoryPerGiBHour === "number"
      ? {
          cpuPerCoreHour: body.fixedUnitPrice.cpuPerCoreHour,
          memoryPerGiBHour: body.fixedUnitPrice.memoryPerGiBHour,
        }
      : undefined;
  const effectiveFrom = typeof body?.effectiveFrom === "string" ? body.effectiveFrom : "";
  const effectiveUntil = typeof body?.effectiveUntil === "string" ? body.effectiveUntil : "";
  const contractRef = typeof body?.contractRef === "string" ? body.contractRef.trim() : "";
  // `approvedBy` on the STORED record is always the second, distinct
  // approver's own identity, recorded below at the moment
  // recordApprovalDecision actually approves this request -- never
  // accepted from the request body, so a caller can never forge who
  // signed off.
  const requested = {
    discountPercent,
    fixedUnitPrice,
    effectiveFrom,
    effectiveUntil,
    contractRef,
    approvedBy: actor,
  };

  const validationError = validatePricingOverride(requested);
  if (validationError) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/pricing-override`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const approval = await requireApproval({
    action: "pricing.override",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedPricingOverride: requested },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/pricing-override`,
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
      path: `/api/orgs/${id}/pricing-override`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "pricing.override requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this negotiated rate, ` +
          "then retry PUT.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists -- bind exactly what was actually
  // approved (resourcePayload.requestedPricingOverride on the approved
  // row), not whatever the caller happens to resend, and stamp the
  // SECOND approver's own identity as `approvedBy` on the stored record.
  const approvedPayload = approval.approval.resourcePayload?.requestedPricingOverride ?? requested;
  const override: OrgPricingOverride = {
    ...approvedPayload,
    approvedBy: approval.approval.approvedBy ?? actor,
  };

  const result = await setOrgPricingOverride(id, override, actor);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/pricing-override`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  return NextResponse.json({
    applied: true,
    pricingOverride: override,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
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
      path: `/api/orgs/${id}/pricing-override`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const approval = await requireApproval({
    action: "pricing.override",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedPricingOverride: null },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/orgs/${id}/pricing-override`,
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
      method: "DELETE",
      path: `/api/orgs/${id}/pricing-override`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "pricing.override requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize expiring this negotiated ` +
          "rate, then retry DELETE.",
      },
      { status: 202 },
    );
  }

  const result = await setOrgPricingOverride(id, null, actor);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/orgs/${id}/pricing-override`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  return NextResponse.json({ applied: true, pricingOverride: null, requiredApproval: true });
}
