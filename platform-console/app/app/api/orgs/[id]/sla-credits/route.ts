import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgSla, setOrgLastSlaCreditAppliedMonth } from "@/lib/orgs";
import { computeCredit, computeMonthlyUptime } from "@/lib/incidents";
import { requireApproval } from "@/lib/approval-workflow";
import { getStoredSubscription, applySlaCreditToStripeBalance } from "@/lib/stripe-billing";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real monthly SLA-compliance + service-credit report -- the number
// procurement/legal actually need: real downtime minutes (from
// lib/incidents.ts's Postgres-backed incident ledger, itself derived from
// real Prometheus `up` spans) vs. this org's contracted
// SLA_TIER_DEFAULTS[slaTier].slaUptimeTargetPct, plus the illustrative
// credit owed if missed (lib/incidents.ts's computeCredit -- explicitly
// labeled `illustrative: true`, same convention as
// lib/invoice-preview.ts's ILLUSTRATIVE_RATES). Replaces
// GET /api/orgs/[id]/sla's own `currentlyMeetingSla: true` /
// `uptimeDataSource: "no-incident-tracking"` placeholder for THIS org/
// month with a real computed report -- that route is left unmodified
// (still reports the always-compliant default for callers who only ask
// "what's the current tier", not "did we meet it last month"), this is
// the dedicated endpoint for the real historical answer.
//
// Auth: same "any member of THIS org may read" floor as
// GET /api/orgs/[id]/sla -- an SLA-compliance report is not more
// sensitive than the SLA tier itself, and enterprise buyers reviewing
// their own compliance record need viewer-level access to see it.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const MONTH_RE = /^\d{4}-\d{2}$/;

function currentMonth(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
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
      path: `/api/orgs/${id}/sla-credits`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const { searchParams } = new URL(request.url);
  const month = searchParams.get("month") ?? currentMonth();
  if (!MONTH_RE.test(month)) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla-credits`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "month must be 'YYYY-MM'" }, { status: 400 });
  }

  const slaResult = await getOrgSla(id);
  if (!slaResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla-credits`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: slaResult.error }, { status: 502 });
  }
  if (!slaResult.data) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/sla-credits`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const reportResult = await computeMonthlyUptime(id, month, slaResult.data.slaTier);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/sla-credits`,
    status: reportResult.ok ? 200 : 502,
    requestId,
  });
  if (!reportResult.ok) {
    return NextResponse.json({ error: reportResult.error }, { status: 502 });
  }

  const credit = computeCredit(reportResult.data);
  return NextResponse.json({ report: reportResult.data, credit });
}

// POST -- the real "closes the loop" action GET's own header comment
// names: applies this org's already-computed SLA credit (the exact same
// computeCredit math GET reports) as a real, negative Stripe
// customer-balance transaction (lib/stripe-billing.ts's
// applySlaCreditToStripeBalance), so it actually reduces the amount due
// on that org's next real Stripe invoice -- no support ticket, no manual
// finance step. Same maker-checker-gated, retry-based convention as
// every other money-moving/destructive route in this repo
// (backup-policy PUT, org tier PUT):
//   1. Caller must hold role >= owner IN THIS ORG's own namespace.
//   2. `month` must be 'YYYY-MM' and this org must not already have had a
//      credit applied for it (org.lastSlaCreditAppliedMonth) -- checked
//      BEFORE the approval request is even created, so a duplicate
//      request is rejected with a real 409, never silently queued for a
//      second approver to accidentally double-credit.
//   3. requireApproval checks for a fresh (<=24h) approved
//      `sla.credit.apply` row for this org id. None exists on the first
//      call -- a pending request is created and this route returns 202.
//   4. A second, distinct owner approves via POST /api/approvals/[id].
//   5. The original caller retries POST -- requireApproval now finds the
//      fresh approved row, computeCredit is re-run fresh (never trusts a
//      stale percentage from step 2), and -- only if a credit is
//      actually owed and a real Stripe customer/subscription is on file
//      -- the real Stripe balance transaction is created.
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
  const path = `/api/orgs/${id}/sla-credits`;

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

  const body = await request.json().catch(() => null);
  const month = typeof body?.month === "string" ? body.month : currentMonth();
  if (!MONTH_RE.test(month)) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "month must be 'YYYY-MM'" }, { status: 400 });
  }

  if (org.lastSlaCreditAppliedMonth === month) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 409,
      requestId,
    });
    return NextResponse.json(
      { error: `an SLA credit has already been applied for ${month}` },
      { status: 409 },
    );
  }

  const approval = await requireApproval({
    action: "sla.credit.apply",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedSlaCreditMonth: month },
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
          "sla.credit.apply requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this credit, ` +
          "then retry POST.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists for THIS org's sla.credit.apply -- apply
  // the credit for the month that was actually approved
  // (resourcePayload.requestedSlaCreditMonth on the approved row), not
  // whatever the caller happens to resend.
  const approvedMonth = approval.approval.resourcePayload?.requestedSlaCreditMonth ?? month;

  // Re-check the idempotency guard against the APPROVED month -- a
  // second, unrelated sla.credit.apply for a different month could have
  // been approved and applied in the time between this route's step 3
  // and step 5 retry.
  const freshOrgResult = await getOrg(id);
  if (!freshOrgResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: freshOrgResult.error }, { status: 502 });
  }
  if (!freshOrgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  if (freshOrgResult.data.lastSlaCreditAppliedMonth === approvedMonth) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 409,
      requestId,
    });
    return NextResponse.json(
      { error: `an SLA credit has already been applied for ${approvedMonth}` },
      { status: 409 },
    );
  }

  const slaResult = await getOrgSla(id);
  if (!slaResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: slaResult.error }, { status: 502 });
  }
  if (!slaResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const reportResult = await computeMonthlyUptime(id, approvedMonth, slaResult.data.slaTier);
  if (!reportResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: reportResult.error }, { status: 502 });
  }

  const credit = computeCredit(reportResult.data);
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
      reason: `no SLA credit owed for ${approvedMonth} -- the org's contracted uptime target was met`,
      report: reportResult.data,
      credit,
    });
  }

  // Fails closed with an honest error -- never a fabricated transaction
  // id -- when no real Stripe customer/subscription is on file for this
  // org's namespace.
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
      { error: `no real Stripe customer/subscription on file for org '${id}' -- cannot apply an SLA credit` },
      { status: 422 },
    );
  }

  const stripeResult = await applySlaCreditToStripeBalance({
    customerId: subscription.stripeCustomerId,
    subscriptionId: subscription.stripeSubscriptionId,
    creditPctOfMonthlySpend: credit.creditPctOfMonthlySpend,
    month: approvedMonth,
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

  const recordResult = await setOrgLastSlaCreditAppliedMonth(id, approvedMonth);
  if (!recordResult.ok) {
    // The real Stripe transaction already landed -- a failure to record
    // the idempotency guard afterward is a visible, retriable state (same
    // "leave partial state for a human/retry, never silently roll back a
    // real external side effect" discipline lib/orgs.ts's createOrg
    // header comment already documents), not a reason to pretend the
    // credit never happened.
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
      slaCreditMonth: approvedMonth,
    });
    return NextResponse.json({
      applied: true,
      transaction: stripeResult.data,
      report: reportResult.data,
      credit,
      approvedBy: approval.approval.approvedBy,
      warning: `credit was applied to Stripe but recording lastSlaCreditAppliedMonth failed: ${recordResult.error}`,
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
    slaCreditMonth: approvedMonth,
  });

  return NextResponse.json({
    applied: true,
    transaction: stripeResult.data,
    report: reportResult.data,
    credit,
    approvedBy: approval.approval.approvedBy,
  });
}
