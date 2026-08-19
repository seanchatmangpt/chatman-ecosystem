import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  getOrgPatchSlaBreaches,
  computePatchSlaCredit,
  markBreachesCreditApplied,
} from "@/lib/patch-sla";
import { requireApproval } from "@/lib/approval-workflow";
import { getStoredSubscription, applySlaCreditToStripeBalance } from "@/lib/stripe-billing";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real Contractual Patch-Timeliness SLA Tier (CVE Remediation Credits)
// report + credit-application route -- the sibling of
// app/api/orgs/[id]/sla-credits/route.ts (uptime SLA credits), scored
// against a DIFFERENT contracted commitment: `Org.patchSlaTier` and
// lib/tiers.ts's PATCH_SLA_COMMITTED_HOURS, not uptime%. Breach data
// comes from lib/patch-sla.ts's `patch_sla_breaches` table -- populated
// by the app/api/patch-sla/breaches cron walk, never computed inline
// here (this route reads what has already been recorded, same
// "GET reports, a separate scan writes" division of labor
// app/api/orgs/[id]/sla-credits/route.ts's own GET/computeMonthlyUptime
// split already establishes).
//
// Auth: same "any member of THIS org may read" floor as
// GET /api/orgs/[id]/sla-credits -- a patch-timeliness compliance report
// is not more sensitive than the breach data itself.

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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/patch-sla-credits`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  if (!org.patchSlaTier) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/patch-sla-credits`,
      status: 200,
      requestId,
    });
    return NextResponse.json({
      patchSlaTier: null,
      breaches: [],
      credit: null,
      message: "this org has no Patch-Timeliness SLA tier contracted",
    });
  }

  const breachesResult = await getOrgPatchSlaBreaches(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/patch-sla-credits`,
    status: breachesResult.ok ? 200 : 502,
    requestId,
  });
  if (!breachesResult.ok) {
    return NextResponse.json({ error: breachesResult.error }, { status: 502 });
  }

  const credit = computePatchSlaCredit(breachesResult.data, org.patchSlaTier);
  return NextResponse.json({ patchSlaTier: org.patchSlaTier, breaches: breachesResult.data, credit });
}

// POST -- applies this org's currently-owed patch-timeliness credit as a
// real, negative Stripe customer-balance transaction, reusing
// lib/stripe-billing.ts's applySlaCreditToStripeBalance WHOLESALE -- the
// exact same function, parameter shape, and Stripe integration
// POST /api/orgs/[id]/sla-credits already calls for uptime credits; this
// route only supplies a different `creditPctOfMonthlySpend` input (this
// capability's own scope, per its spec: "reusing credit application,
// invoicing, and Stripe integration as-is"). Same maker-checker-gated
// convention as every other money-moving route in this repo:
//   1. Caller must hold role >= owner IN THIS ORG's own namespace.
//   2. requireApproval checks for a fresh (<=24h) approved
//      `patch-sla.credit.apply` row for this org id. None exists on the
//      first call -- a pending request is created and this route returns
//      202.
//   3. A second, distinct owner approves via POST /api/approvals/[id].
//   4. The original caller retries POST -- requireApproval now finds the
//      fresh approved row, the credit is re-computed fresh against
//      whatever breaches are STILL uncredited at that moment (never
//      trusts a stale count from step 2), and -- only if a credit is
//      actually owed and a real Stripe customer/subscription is on file
//      -- the real Stripe balance transaction is created, then every
//      breach row that was actually credited is marked
//      `credit_applied_at` (lib/patch-sla.ts's markBreachesCreditApplied)
//      so a later re-run never double-credits the same breach.
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
  const path = `/api/orgs/${id}/patch-sla-credits`;

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  if (!org.patchSlaTier) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 422,
      requestId,
    });
    return NextResponse.json(
      { error: `org '${id}' has no Patch-Timeliness SLA tier contracted -- nothing to credit` },
      { status: 422 },
    );
  }

  const approval = await requireApproval({
    action: "patch-sla.credit.apply",
    targetId: id,
    requestedBy: actor,
    resourcePayload: {},
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
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
      method: "POST",
      path,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "patch-sla.credit.apply requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this credit, ` +
          "then retry POST.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists -- re-read the breaches fresh (never
  // trust whatever count was pending approval; a breach could have been
  // credited via a different, concurrent approval in the meantime, and
  // computePatchSlaCredit/markBreachesCreditApplied both already exclude
  // anything with a non-null credit_applied_at).
  const breachesResult = await getOrgPatchSlaBreaches(id);
  if (!breachesResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: breachesResult.error }, { status: 502 });
  }

  const credit = computePatchSlaCredit(breachesResult.data, org.patchSlaTier);
  if (!credit.owed) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 200,
      requestId,
    });
    return NextResponse.json({
      applied: false,
      reason: "no uncredited patch-timeliness SLA breaches for this org",
      breaches: breachesResult.data,
      credit,
    });
  }

  // Fails closed with an honest error -- never a fabricated transaction
  // id -- when no real Stripe customer/subscription is on file for this
  // org's namespace. Same guard POST /api/orgs/[id]/sla-credits already
  // performs before its own applySlaCreditToStripeBalance call.
  const subscriptionResult = await getStoredSubscription(org.namespace);
  if (!subscriptionResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: subscriptionResult.error }, { status: 502 });
  }
  const subscription = subscriptionResult.data;
  if (!subscription || !subscription.stripeCustomerId || !subscription.stripeSubscriptionId) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 422,
      requestId,
    });
    return NextResponse.json(
      { error: `no real Stripe customer/subscription on file for org '${id}' -- cannot apply a patch-timeliness SLA credit` },
      { status: 422 },
    );
  }

  const month = `${new Date().getUTCFullYear()}-${String(new Date().getUTCMonth() + 1).padStart(2, "0")}`;
  const stripeResult = await applySlaCreditToStripeBalance({
    customerId: subscription.stripeCustomerId,
    subscriptionId: subscription.stripeSubscriptionId,
    creditPctOfMonthlySpend: credit.creditPctOfMonthlySpend,
    month,
  });
  if (!stripeResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: stripeResult.error }, { status: 502 });
  }

  const markResult = await markBreachesCreditApplied(id);
  if (!markResult.ok) {
    // The real Stripe transaction already landed -- a failure to record
    // the idempotency guard afterward is a visible, retriable state (same
    // discipline POST /api/orgs/[id]/sla-credits's own header comment
    // already documents), not a reason to pretend the credit never
    // happened.
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 200,
      requestId,
      slaCreditStripeTransactionId: stripeResult.data.id,
      slaCreditAmountCents: stripeResult.data.amountCents,
    });
    return NextResponse.json({
      applied: true,
      transaction: stripeResult.data,
      breaches: breachesResult.data,
      credit,
      approvedBy: approval.approval.approvedBy,
      warning: `credit was applied to Stripe but marking breaches credit_applied_at failed: ${markResult.error}`,
    });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path,
    status: 200,
    requestId,
    slaCreditStripeTransactionId: stripeResult.data.id,
    slaCreditAmountCents: stripeResult.data.amountCents,
  });

  return NextResponse.json({
    applied: true,
    transaction: stripeResult.data,
    breachesCredited: markResult.data,
    credit,
    approvedBy: approval.approval.approvedBy,
  });
}
