import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  changeSubscriptionPlan,
  getStoredSubscription,
  hasStripeCredentials,
  isStripeTestMode,
} from "@/lib/stripe-billing";

// Same platform-namespace roster /api/billing/stripe/checkout already
// enforces -- only a tenant namespace this console actually manages can
// have its subscription changed.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

/**
 * POST /api/billing/stripe/change-plan
 * Real Stripe self-service plan upgrade/downgrade: for a tenant namespace
 * that already has a live (active/trialing/past_due) Stripe subscription
 * on file, swaps that EXACT subscription's price via
 * `stripe.subscriptions.update` with real Stripe-computed proration
 * (`proration_behavior: "create_prorations"`) instead of the double-charge
 * bug `/api/billing/stripe/checkout` alone would produce (it unconditionally
 * calls `stripe.subscriptions.create`, so re-running it against an
 * already-subscribed org creates a second, independently-billed
 * subscription). For a namespace with no subscription on file yet, falls
 * back to the same create-subscription + Checkout Session path
 * `/api/billing/stripe/checkout` already uses. `owner` role only, same
 * minimum as the checkout route, since this mutates a live billing object.
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
  const newPriceId = body?.newPriceId;
  if (typeof tenantNamespace !== "string" || !PLATFORM_NAMESPACES.includes(tenantNamespace)) {
    return NextResponse.json(
      { error: `tenantNamespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (typeof newPriceId !== "string" || !newPriceId.startsWith("price_")) {
    return NextResponse.json({ error: "newPriceId must be a real Stripe Price id (price_...)" }, { status: 400 });
  }

  const before = await getStoredSubscription(tenantNamespace);
  const oldPriceIdBefore = before.ok ? before.data?.priceId ?? null : null;

  const origin = request.nextUrl.origin;
  const result = await changeSubscriptionPlan({
    tenantNamespace,
    email: session.sub,
    newPriceId,
    successUrl: `${origin}/billing?checkout=success`,
    cancelUrl: `${origin}/billing?checkout=cancelled`,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const oldPriceId = result.data.mode === "swapped" ? result.data.oldPriceId : oldPriceIdBefore;

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "POST",
    path: `/api/billing/stripe/change-plan (tenantNamespace=${tenantNamespace}, oldPriceId=${
      oldPriceId ?? "none"
    }, newPriceId=${newPriceId}, mode=${result.data.mode})`,
    status: 200,
    requestId,
  });

  if (result.data.mode === "swapped") {
    return NextResponse.json({
      testMode: isStripeTestMode(),
      mode: "swapped",
      tenantNamespace,
      oldPriceId,
      newPriceId,
      subscription: result.data.subscription,
    });
  }

  return NextResponse.json({
    testMode: isStripeTestMode(),
    mode: "checkout",
    tenantNamespace,
    oldPriceId,
    newPriceId,
    checkoutUrl: result.data.checkoutUrl,
    stripeCustomerId: result.data.stripeCustomerId,
    stripeSubscriptionId: result.data.stripeSubscriptionId,
  });
}
