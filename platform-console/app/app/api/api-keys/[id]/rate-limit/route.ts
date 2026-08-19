import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { updateApiKeyTier } from "@/lib/api-keys";
import { API_KEY_TIERS, isApiKeyTier, type ApiKeyTier } from "@/lib/rate-limit";
import {
  attachRateLimitAddonPrice,
  getStoredSubscription,
  hasStripeCredentials,
  rateLimitAddonPriceId,
} from "@/lib/stripe-billing";

// Same platform-namespace roster app/api/billing/stripe/checkout/route.ts
// already validates against -- only a tenant namespace this console
// actually manages can carry a real Stripe subscription an add-on price
// gets attached to.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

/**
 * PUT /api/api-keys/[id]/rate-limit
 *
 * Upgrades (or downgrades) one API key's rate-limit tier -- the
 * "documented, contractually-different rate limit for a production key"
 * add-on, orthogonal to a Project's own `lib/tiers.ts` `ProjectTier`
 * (compute/quota) and to the key's `lib/authz.ts`-bound `role` (app-level
 * RBAC). `owner`-gated, same minimum every other API-keys mutation and
 * every other billing-adjacent mutation (checkout, overage) in this
 * console already requires -- this both changes enforced request
 * throughput for a live credential AND, on an upgrade to a paid tier,
 * attaches a real recurring Stripe add-on price to the org's
 * subscription (real money, in whatever mode STRIPE_SECRET_KEY is in).
 *
 * On upgrade to `pro`/`enterprise` (a real move UP `API_KEY_TIERS`'
 * ordering from the key's current tier), a `tenantNamespace` naming the
 * org's already-onboarded Stripe subscription (`ensureCustomerAndSubscription`)
 * is required in the body, and `attachRateLimitAddonPrice` must succeed
 * before the key's tier is actually changed -- so a key's enforced limit
 * is never widened without the matching Stripe line item existing (no
 * "upgrade now, bill later" gap). A downgrade, or a same-tier no-op,
 * needs no billing call: nothing new is being sold.
 */
export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/api-keys/${id}/rate-limit`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const requestedTier = body?.tier;
  if (!isApiKeyTier(requestedTier)) {
    return NextResponse.json(
      { error: `tier must be one of: ${API_KEY_TIERS.join(", ")}` },
      { status: 400 },
    );
  }
  const tier = requestedTier as ApiKeyTier;

  const currentTierRank = (t: ApiKeyTier) => API_KEY_TIERS.indexOf(t);
  const isPaidAddonTier = (t: ApiKeyTier): t is "pro" | "enterprise" =>
    t === "pro" || t === "enterprise";

  // Real upgrade to a paid rate-limit tier: attach the real Stripe add-on
  // price to the org's already-onboarded subscription BEFORE the key's
  // enforced ceiling is ever widened. Downgrades and same-tier requests
  // skip this block entirely -- reverting to `default` or re-selecting
  // the current tier sells nothing new.
  if (isPaidAddonTier(tier)) {
    if (!hasStripeCredentials()) {
      return NextResponse.json(
        { error: "Stripe not configured: STRIPE_SECRET_KEY is not set for this deployment" },
        { status: 503 },
      );
    }
    const tenantNamespace = body?.tenantNamespace;
    if (typeof tenantNamespace !== "string" || !PLATFORM_NAMESPACES.includes(tenantNamespace)) {
      return NextResponse.json(
        { error: `tenantNamespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
        { status: 400 },
      );
    }
    const priceId = rateLimitAddonPriceId(tier);
    if (!priceId) {
      return NextResponse.json(
        {
          error: `no Stripe Price configured for the '${tier}' rate-limit add-on -- set STRIPE_RATE_LIMIT_ADDON_PRICE_ID_${tier.toUpperCase()}`,
        },
        { status: 503 },
      );
    }

    const subscription = await getStoredSubscription(tenantNamespace);
    if (!subscription.ok) {
      return NextResponse.json({ error: subscription.error }, { status: 502 });
    }
    if (!subscription.data?.stripeSubscriptionId) {
      return NextResponse.json(
        { error: `no Stripe subscription on file for tenant namespace '${tenantNamespace}' -- onboard billing first` },
        { status: 409 },
      );
    }

    const attached = await attachRateLimitAddonPrice({
      subscriptionId: subscription.data.stripeSubscriptionId,
      priceId,
      apiKeyId: id,
      rateLimitTier: tier,
    });
    if (!attached.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "PUT",
        path: `/api/api-keys/${id}/rate-limit`,
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: attached.error }, { status: 502 });
    }
  }

  const result = await updateApiKeyTier(id, tier);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/api-keys/${id}/rate-limit`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ key: result.data, wasUpgrade: currentTierRank(tier) > 0 });
}
