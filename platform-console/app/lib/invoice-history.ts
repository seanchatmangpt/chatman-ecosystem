/**
 * Real per-org invoice/receipt history -- the actual-billed-and-paid
 * counterpart to lib/invoice-preview.ts's Prometheus-derived forecast
 * (explicitly an ESTIMATE of what a period WOULD cost, never a real
 * financial record) and to lib/stripe-billing.ts's checkout/subscription
 * flow (creates the Customer/Subscription, but exposes no history once
 * billing cycles start firing).
 *
 * Every invoice returned here is a real `Stripe.Invoice` object Stripe
 * itself generated on a real subscription billing cycle (or a one-off
 * invoice) for the real Stripe Customer already created by
 * `ensureCustomerAndSubscription` (lib/stripe-billing.ts) and recorded in
 * the `platform-console-stripe-subscriptions` ConfigMap via
 * `getStoredSubscription`. This module does not create, price, or render
 * anything -- it lists and re-serves the id/number/status/PDF-link fields
 * Stripe already computed, same "no local PDF rendering" posture the spec
 * calls for: `invoicePdf` and `hostedInvoiceUrl` are Stripe's own URLs.
 *
 * Fails closed exactly like lib/stripe-billing.ts: no STRIPE_SECRET_KEY
 * configured, or no Stripe customer on file yet for this tenant, both
 * return an honest `ok:false` / empty result -- never a fabricated
 * invoice.
 */
import { getStripeClient, getStoredSubscription, type StripeResult } from "@/lib/stripe-billing";
import type Stripe from "stripe";

export interface InvoiceRecord {
  id: string;
  number: string | null;
  amountPaid: number;
  amountDue: number;
  currency: string;
  status: Stripe.Invoice.Status | null;
  created: string;
  hostedInvoiceUrl: string | null;
  invoicePdf: string | null;
}

function toInvoiceRecord(invoice: Stripe.Invoice): InvoiceRecord {
  return {
    id: invoice.id ?? "",
    number: invoice.number ?? null,
    amountPaid: invoice.amount_paid,
    amountDue: invoice.amount_due,
    currency: invoice.currency,
    status: invoice.status ?? null,
    created: new Date(invoice.created * 1000).toISOString(),
    hostedInvoiceUrl: invoice.hosted_invoice_url ?? null,
    invoicePdf: invoice.invoice_pdf ?? null,
  };
}

/**
 * Real `stripe.invoices.list({customer: ...})` against the tenant's real
 * Stripe customer id, newest first (Stripe's own default ordering).
 * Returns an empty list (not an error) when the tenant has a stored
 * subscription record but Stripe has not yet generated any invoice for
 * it (e.g. a brand-new subscription before its first billing cycle).
 */
export async function listInvoicesForOrg(
  tenantNamespace: string,
): Promise<StripeResult<InvoiceRecord[]>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };

  const stored = await getStoredSubscription(tenantNamespace);
  if (!stored.ok) return { ok: false, error: stored.error };
  if (!stored.data) {
    // No Stripe customer on file for this tenant yet -- a real, honest
    // "no billing history" answer, not a fabricated empty-looking error.
    return { ok: true, data: [] };
  }

  try {
    const invoices: Stripe.Invoice[] = [];
    for await (const invoice of stripe.invoices.list({
      customer: stored.data.stripeCustomerId,
      limit: 100,
    })) {
      invoices.push(invoice);
    }
    return { ok: true, data: invoices.map(toInvoiceRecord) };
  } catch (e) {
    return { ok: false, error: `stripe invoices.list failed: ${(e as Error).message}` };
  }
}

/**
 * Real single-invoice lookup, scoped to the tenant: fetches the invoice
 * by id from Stripe and verifies its `customer` id matches this tenant's
 * stored Stripe customer id before returning it, so one org can never be
 * handed another org's invoice PDF link by guessing an invoice id.
 */
export async function getInvoiceForOrg(
  tenantNamespace: string,
  invoiceId: string,
): Promise<StripeResult<InvoiceRecord | null>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };

  const stored = await getStoredSubscription(tenantNamespace);
  if (!stored.ok) return { ok: false, error: stored.error };
  if (!stored.data) return { ok: true, data: null };

  try {
    const invoice = await stripe.invoices.retrieve(invoiceId);
    const invoiceCustomerId =
      typeof invoice.customer === "string" ? invoice.customer : invoice.customer?.id;
    if (invoiceCustomerId !== stored.data.stripeCustomerId) {
      // Belongs to a different Stripe customer -- treat exactly like
      // "not found" for this org rather than leaking a cross-tenant hit.
      return { ok: true, data: null };
    }
    return { ok: true, data: toInvoiceRecord(invoice) };
  } catch (e) {
    return { ok: false, error: `stripe invoices.retrieve failed: ${(e as Error).message}` };
  }
}
