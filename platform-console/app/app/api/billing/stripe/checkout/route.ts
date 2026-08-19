import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  createCheckoutSession,
  ensureCustomerAndSubscription,
  hasStripeCredentials,
  isStripeTestMode,
} from "@/lib/stripe-billing";

// Same platform-namespace roster /billing and /api/billing already use --
// only a tenant namespace this console actually manages can have a
// subscription created for it.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

/**
 * POST /api/billing/stripe/checkout
 * Real Stripe test-mode onboarding: creates (or reuses) a Stripe Customer
 * + Subscription for the requested tenant namespace, then a real
 * Checkout Session for payment-method collection, and returns the real
 * Stripe-hosted `url` for the caller to redirect to. `owner` role only --
 * same minimum this console already requires for other billing-adjacent
 * mutations (e.g. lib/budget-alerts.ts thresholds), since this actually
 * creates a subscription object.
 */
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const roleCheck = await requireRole(session, "owner");
  if (!roleCheck.ok) return roleCheck.response;

  if (!hasStripeCredentials()) {
    return NextResponse.json(
      { error: "Stripe not configured: STRIPE_SECRET_KEY is not set for this deployment" },
      { status: 503 },
    );
  }

  const body = await request.json().catch(() => null);
  const tenantNamespace = body?.tenantNamespace;
  const priceId = body?.priceId;
  if (typeof tenantNamespace !== "string" || !PLATFORM_NAMESPACES.includes(tenantNamespace)) {
    return NextResponse.json(
      { error: `tenantNamespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (typeof priceId !== "string" || !priceId.startsWith("price_")) {
    return NextResponse.json({ error: "priceId must be a real Stripe Price id (price_...)" }, { status: 400 });
  }

  const ensured = await ensureCustomerAndSubscription({
    tenantNamespace,
    email: session.sub,
    priceId,
  });
  if (!ensured.ok) {
    return NextResponse.json({ error: ensured.error }, { status: 502 });
  }

  const origin = request.nextUrl.origin;
  const checkout = await createCheckoutSession({
    tenantNamespace,
    customerId: ensured.data.stripeCustomerId,
    priceId,
    successUrl: `${origin}/billing?checkout=success`,
    cancelUrl: `${origin}/billing?checkout=cancelled`,
  });
  if (!checkout.ok) {
    return NextResponse.json({ error: checkout.error }, { status: 502 });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "POST",
    path: "/api/billing/stripe/checkout",
    status: 200,
    requestId,
  });

  return NextResponse.json({
    testMode: isStripeTestMode(),
    checkoutUrl: checkout.data.url,
    stripeCustomerId: ensured.data.stripeCustomerId,
    stripeSubscriptionId: ensured.data.stripeSubscriptionId,
  });
}
