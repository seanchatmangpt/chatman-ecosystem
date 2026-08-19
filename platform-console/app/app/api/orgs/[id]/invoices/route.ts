import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { listInvoicesForOrg } from "@/lib/invoice-history";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real per-org invoice/receipt history -- the self-service, downloadable
// billing record Fortune 5 procurement/AP departments need for expense
// reconciliation and SOX documentation, without opening a support ticket.
// Unlike /billing (lib/invoice-preview.ts, a Prometheus-derived cost
// FORECAST) and the checkout flow (lib/stripe-billing.ts), this lists
// real Stripe `Invoice` objects Stripe already generated on this org's
// real subscription billing cycles. Gated behind the same org-membership
// check every other /api/orgs/[id]/* route uses -- any member (viewer or
// above) may view billing history; only owner-role actions elsewhere
// (tier downgrades, org deletion) require the higher bar.

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
      path: `/api/orgs/${id}/invoices`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const invoicesResult = await listInvoicesForOrg(org.namespace);
  if (!invoicesResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/invoices`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: invoicesResult.error }, { status: 502 });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/invoices`,
    status: 200,
    requestId,
  });
  return NextResponse.json({ invoices: invoicesResult.data });
}
