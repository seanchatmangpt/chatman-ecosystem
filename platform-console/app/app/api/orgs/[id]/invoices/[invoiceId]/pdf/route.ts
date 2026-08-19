import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getInvoiceForOrg } from "@/lib/invoice-history";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real invoice PDF export: redirects to Stripe's own `invoice_pdf` URL
// for the requested invoice, after verifying (a) the caller is a member
// of this org and (b) the invoice actually belongs to this org's Stripe
// customer (lib/invoice-history.ts's getInvoiceForOrg enforces the
// latter server-side). No local PDF rendering -- Stripe already
// generates the PDF natively; this route only gates access to the link.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; invoiceId: string }> },
) {
  const { id, invoiceId } = await params;
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
      path: `/api/orgs/${id}/invoices/${invoiceId}/pdf`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const invoiceResult = await getInvoiceForOrg(org.namespace, invoiceId);
  if (!invoiceResult.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/invoices/${invoiceId}/pdf`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: invoiceResult.error }, { status: 502 });
  }
  if (!invoiceResult.data || !invoiceResult.data.invoicePdf) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/invoices/${invoiceId}/pdf`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "invoice not found for this org" }, { status: 404 });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/invoices/${invoiceId}/pdf`,
    status: 302,
    requestId,
  });
  return NextResponse.redirect(invoiceResult.data.invoicePdf, { status: 302 });
}
