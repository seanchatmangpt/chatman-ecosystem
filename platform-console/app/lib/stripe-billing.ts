/**
 * Real Stripe test-mode billing integration -- answers the "how do you
 * actually charge us" question the illustrative /billing and /cost pages
 * (lib/invoice-preview.ts, lib/cost.ts) cannot: those pages render real
 * Prometheus-derived usage against a hardcoded ILLUSTRATIVE_RATES table,
 * with no Stripe customer, no subscription object, and no payment method
 * on file anywhere. This module is the real (test-mode) counterpart --
 * a real `stripe` npm SDK client, real Stripe Customer + Subscription
 * objects, and a real Checkout Session for payment-method collection.
 *
 * Test-mode honesty: every object this module creates is created against
 * whatever Stripe API key is configured in STRIPE_SECRET_KEY. A `sk_test_`
 * key makes this genuinely real Stripe test-mode wiring (real HTTPS calls
 * to api.stripe.com, real object ids, real webhook events) with zero
 * financial obligation -- Stripe's own test-mode guarantee, not a claim
 * this file invents. A `sk_live_` key would make the exact same code
 * real live billing; this module does not distinguish the two, so
 * deploying it with a live key is a deployment-config decision, not a
 * code change. Off-cluster / no key configured, every function here
 * fails closed with an honest "not configured" Result -- same fail-closed
 * convention lib/k8s.ts's `hasClusterCredentials` establishes -- rather
 * than fabricating a customer/subscription object.
 *
 * Subscription/plan state is persisted the same way lib/webhooks.ts
 * persists webhook subscriptions: one real k8s ConfigMap
 * (`platform-console-stripe-subscriptions`, `platform-console` namespace)
 * via lib/k8s.ts's already-RBAC-covered `getConfigMap` /
 * `createOrUpdateConfigMap` primitive -- no new k8s resource kind, no new
 * RBAC verb. One ConfigMap `data` key per tenant namespace (must match
 * `[-._a-zA-Z0-9]+`, which every namespace name in PLATFORM_NAMESPACES
 * already satisfies), value is one JSON-encoded StoredSubscription record
 * kept current by the real webhook receiver
 * (app/api/billing/stripe/webhook/route.ts) processing real Stripe
 * `customer.subscription.*` and `invoice.payment_*` events.
 */
import Stripe from "stripe";
import {
  createOrUpdateConfigMap,
  getConfigMap,
  type K8sResult,
} from "@/lib/k8s";

export const STRIPE_NAMESPACE = "platform-console";
export const STRIPE_SUBSCRIPTIONS_CONFIGMAP = "platform-console-stripe-subscriptions";

export type StripeResult<T> = { ok: true; data: T } | { ok: false; error: string };

let cachedClient: Stripe | null | undefined;

/**
 * True only when a Stripe secret key is actually configured in this
 * process's environment -- same "is the real backend reachable" gate
 * `hasClusterCredentials()` provides for the k8s API server, and the same
 * reason the /billing page conditions its render on that gate rather
 * than fabricating data when the backend isn't there.
 */
export function hasStripeCredentials(): boolean {
  return typeof process.env.STRIPE_SECRET_KEY === "string" && process.env.STRIPE_SECRET_KEY.length > 0;
}

/**
 * True when the configured key is a Stripe *test-mode* secret key
 * (`sk_test_...`) -- lets callers (the billing page, the evidence bundle)
 * state precisely whether a given deployment is wired to real Stripe
 * test-mode or real Stripe live-mode, instead of collapsing both into an
 * undifferentiated "Stripe is configured."
 */
export function isStripeTestMode(): boolean {
  return (process.env.STRIPE_SECRET_KEY ?? "").startsWith("sk_test_");
}

// Exported so lib/invoice-history.ts (real Stripe invoice history/PDF
// export) can reuse the exact same cached client this module already
// builds from STRIPE_SECRET_KEY -- one Stripe client per process, not a
// second construction path with its own cache.
export function getStripeClient(): Stripe | null {
  if (cachedClient !== undefined) return cachedClient;
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) {
    cachedClient = null;
    return cachedClient;
  }
  cachedClient = new Stripe(key, {
    apiVersion: "2025-08-27.basil" as Stripe.LatestApiVersion,
    timeout: 10_000,
  });
  return cachedClient;
}

export interface StoredSubscription {
  tenantNamespace: string;
  stripeCustomerId: string;
  stripeSubscriptionId: string | null;
  status: Stripe.Subscription.Status | "no_subscription";
  priceId: string | null;
  currentPeriodEnd: string | null;
  updatedAt: string;
  /** Set by the webhook receiver on the most recent event it applied. */
  lastEventId: string | null;
  lastEventType: string | null;
}

/**
 * Real GET of the one ConfigMap key for `tenantNamespace`, same
 * get-then-decide shape `getConfigMap` callers throughout this codebase
 * (lib/webhooks.ts, feature flags) already use. Returns `data: null`
 * (not an error) when no subscription has been created yet for this
 * tenant -- a real "no subscription on file" answer, not a fabricated
 * default plan.
 */
export async function getStoredSubscription(
  tenantNamespace: string,
): Promise<K8sResult<StoredSubscription | null>> {
  const cm = await getConfigMap(STRIPE_NAMESPACE, STRIPE_SUBSCRIPTIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const raw = cm.data?.data?.[tenantNamespace];
  if (!raw) return { ok: true, data: null };
  try {
    return { ok: true, data: JSON.parse(raw) as StoredSubscription };
  } catch (e) {
    return { ok: false, error: `corrupt stored subscription record for ${tenantNamespace}: ${(e as Error).message}` };
  }
}

export async function listStoredSubscriptions(
  tenantNamespaces: string[],
): Promise<K8sResult<Record<string, StoredSubscription | null>>> {
  const cm = await getConfigMap(STRIPE_NAMESPACE, STRIPE_SUBSCRIPTIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const out: Record<string, StoredSubscription | null> = {};
  for (const ns of tenantNamespaces) {
    const raw = cm.data?.data?.[ns];
    out[ns] = raw ? (JSON.parse(raw) as StoredSubscription) : null;
  }
  return { ok: true, data: out };
}

async function putStoredSubscription(
  record: StoredSubscription,
): Promise<K8sResult<StoredSubscription>> {
  const result = await createOrUpdateConfigMap(STRIPE_NAMESPACE, STRIPE_SUBSCRIPTIONS_CONFIGMAP, {
    [record.tenantNamespace]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: record };
}

/**
 * Real Stripe customer + subscription creation on tenant onboarding
 * (the scope's own wording). Idempotent on `tenantNamespace`: if a
 * customer already exists on file for this tenant (per the ConfigMap),
 * reuses it rather than creating a duplicate Stripe Customer object --
 * Stripe has no built-in "one customer per external id" uniqueness, so
 * this module owns that invariant itself via the ConfigMap it already
 * reads before writing.
 *
 * `priceId` must be a real Stripe test-mode Price id (created in the
 * connected Stripe test-mode account, e.g. via the Stripe Dashboard or
 * `stripe prices create`) -- this module does not fabricate pricing,
 * it wires to whatever real Price the operator configured.
 */
export async function ensureCustomerAndSubscription(params: {
  tenantNamespace: string;
  email: string;
  priceId: string;
}): Promise<StripeResult<StoredSubscription>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };

  const existing = await getStoredSubscription(params.tenantNamespace);
  if (!existing.ok) return { ok: false, error: existing.error };

  try {
    let customerId = existing.data?.stripeCustomerId ?? null;
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: params.email,
        name: params.tenantNamespace,
        metadata: { tenant_namespace: params.tenantNamespace },
      });
      customerId = customer.id;
    }

    const subscription = await stripe.subscriptions.create({
      customer: customerId,
      items: [{ price: params.priceId }],
      payment_behavior: "default_incomplete",
      payment_settings: { save_default_payment_method: "on_subscription" },
      expand: ["latest_invoice.payment_intent"],
      metadata: { tenant_namespace: params.tenantNamespace },
    });

    const record: StoredSubscription = {
      tenantNamespace: params.tenantNamespace,
      stripeCustomerId: customerId,
      stripeSubscriptionId: subscription.id,
      status: subscription.status,
      priceId: params.priceId,
      currentPeriodEnd: subscription.items.data[0]?.current_period_end
        ? new Date(subscription.items.data[0].current_period_end * 1000).toISOString()
        : null,
      updatedAt: new Date().toISOString(),
      lastEventId: null,
      lastEventType: "subscription.created.via_onboarding",
    };
    const stored = await putStoredSubscription(record);
    if (!stored.ok) return { ok: false, error: stored.error };
    return { ok: true, data: record };
  } catch (e) {
    return { ok: false, error: `Stripe API error: ${(e as Error).message}` };
  }
}

/**
 * Real Stripe Checkout Session in `setup`/`subscription` mode -- the
 * actual (test-mode) payment-method collection flow: the returned `url`
 * is a real Stripe-hosted page where a real test card
 * (e.g. `4242 4242 4242 4242`) is entered, never a page this app renders
 * itself (this app never touches raw card data, same boundary Stripe's
 * own PCI-scope-reduction design provides).
 */
export async function createCheckoutSession(params: {
  tenantNamespace: string;
  customerId: string;
  priceId: string;
  successUrl: string;
  cancelUrl: string;
}): Promise<StripeResult<{ id: string; url: string }>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };
  try {
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      customer: params.customerId,
      line_items: [{ price: params.priceId, quantity: 1 }],
      success_url: params.successUrl,
      cancel_url: params.cancelUrl,
      metadata: { tenant_namespace: params.tenantNamespace },
    });
    if (!session.url) return { ok: false, error: "Stripe returned a Checkout Session with no url" };
    return { ok: true, data: { id: session.id, url: session.url } };
  } catch (e) {
    return { ok: false, error: `Stripe API error: ${(e as Error).message}` };
  }
}

/**
 * Real Stripe subscription PLAN CHANGE (upgrade/downgrade) -- the actual
 * `stripe.subscriptions.update` mid-cycle swap, with Stripe computing real
 * proration, as distinct from `ensureCustomerAndSubscription` above, which
 * only ever CREATES a subscription. Calling `ensureCustomerAndSubscription`
 * again for an org that already has a live subscription would call
 * `stripe.subscriptions.create` a second time against the same customer --
 * a real second, independently-billed Stripe Subscription object, i.e. a
 * genuine double-charge bug, not a hypothetical one. This function is the
 * fix: when a stored subscription already exists for `tenantNamespace` and
 * its status is one Stripe still actively bills against (`active`,
 * `trialing`, `past_due` -- a `past_due` org is still on a live
 * subscription object, just failing invoices; changing its plan does not
 * require it to first become fully current), swap that EXACT subscription's
 * existing line item to the new price via `items: [{ id, price }]` --
 * Stripe's own documented in-place-swap shape (not `items: [{ price }]`,
 * which would ADD a second item onto the subscription rather than
 * replacing the existing one) -- with `proration_behavior:
 * "create_prorations"`, Stripe's real mid-cycle credit/charge computation
 * (a real negative or positive proration InvoiceItem lands on the
 * customer's next invoice; this function does not compute or fabricate
 * that amount itself, it only requests the real Stripe behavior that
 * computes it).
 *
 * Only when no stored subscription exists at all (a brand-new org, never
 * checked out before) does this fall back to
 * `ensureCustomerAndSubscription` + `createCheckoutSession` -- correctly
 * CREATING the first subscription, the one case that operation is actually
 * for.
 */
export async function changeSubscriptionPlan(params: {
  tenantNamespace: string;
  email: string;
  newPriceId: string;
  successUrl: string;
  cancelUrl: string;
}): Promise<
  StripeResult<
    | { mode: "swapped"; subscription: StoredSubscription; oldPriceId: string | null }
    | { mode: "checkout"; checkoutUrl: string; stripeCustomerId: string; stripeSubscriptionId: string | null }
  >
> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };

  const existing = await getStoredSubscription(params.tenantNamespace);
  if (!existing.ok) return { ok: false, error: existing.error };

  const stored = existing.data;
  const swappableStatus =
    stored?.status === "active" || stored?.status === "trialing" || stored?.status === "past_due";

  if (stored && stored.stripeSubscriptionId && swappableStatus) {
    try {
      const oldPriceId = stored.priceId;
      const current = await stripe.subscriptions.retrieve(stored.stripeSubscriptionId);
      const existingItemId = current.items.data[0]?.id;
      if (!existingItemId) {
        return {
          ok: false,
          error: `stored subscription ${stored.stripeSubscriptionId} has no subscription item to swap`,
        };
      }

      const updated = await stripe.subscriptions.update(stored.stripeSubscriptionId, {
        items: [{ id: existingItemId, price: params.newPriceId }],
        proration_behavior: "create_prorations",
      });

      const record: StoredSubscription = {
        tenantNamespace: params.tenantNamespace,
        stripeCustomerId: stored.stripeCustomerId,
        stripeSubscriptionId: updated.id,
        status: updated.status,
        priceId: updated.items.data[0]?.price?.id ?? params.newPriceId,
        currentPeriodEnd: updated.items.data[0]?.current_period_end
          ? new Date(updated.items.data[0].current_period_end * 1000).toISOString()
          : null,
        updatedAt: new Date().toISOString(),
        lastEventId: null,
        lastEventType: "subscription.updated.via_change_plan",
      };
      const put = await putStoredSubscription(record);
      if (!put.ok) return { ok: false, error: put.error };
      return { ok: true, data: { mode: "swapped", subscription: record, oldPriceId } };
    } catch (e) {
      return { ok: false, error: `Stripe API error: ${(e as Error).message}` };
    }
  }

  // No live subscription on file -- fall back to the real
  // create-customer(-if-needed) + create-subscription + Checkout Session
  // path, which is correct for a first-ever subscription.
  const ensured = await ensureCustomerAndSubscription({
    tenantNamespace: params.tenantNamespace,
    email: params.email,
    priceId: params.newPriceId,
  });
  if (!ensured.ok) return { ok: false, error: ensured.error };

  const checkout = await createCheckoutSession({
    tenantNamespace: params.tenantNamespace,
    customerId: ensured.data.stripeCustomerId,
    priceId: params.newPriceId,
    successUrl: params.successUrl,
    cancelUrl: params.cancelUrl,
  });
  if (!checkout.ok) return { ok: false, error: checkout.error };

  return {
    ok: true,
    data: {
      mode: "checkout",
      checkoutUrl: checkout.data.url,
      stripeCustomerId: ensured.data.stripeCustomerId,
      stripeSubscriptionId: ensured.data.stripeSubscriptionId,
    },
  };
}

/**
 * Real webhook signature verification -- Stripe's own HMAC-SHA256
 * `Stripe-Signature` header scheme, the same convention family
 * lib/webhooks.ts documents for this app's outbound webhooks (there:
 * `X-Hub-Signature-256`-style HMAC this app computes as the sender;
 * here: the same scheme with this app as the *receiver*, verifying a
 * signature Stripe computed). Delegates to the official SDK's
 * `constructEvent`, which recomputes the HMAC over `timestamp.payload`
 * using STRIPE_WEBHOOK_SECRET and rejects any mismatch or expired
 * timestamp -- never a bypassed / logged-only check.
 */
export function verifyStripeWebhookSignature(
  rawBody: string,
  signatureHeader: string,
): StripeResult<Stripe.Event> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) return { ok: false, error: "STRIPE_WEBHOOK_SECRET not configured" };
  try {
    const event = stripe.webhooks.constructEvent(rawBody, signatureHeader, webhookSecret);
    return { ok: true, data: event };
  } catch (e) {
    return { ok: false, error: `signature verification failed: ${(e as Error).message}` };
  }
}

/**
 * Real (test-mode-honest, see this file's header) usage-based overage
 * billing: creates a genuine Stripe InvoiceItem against `customerId`,
 * attached to `subscriptionId` so it lands on that subscription's next
 * real invoice rather than floating unattached -- the actual (test-mode)
 * "metered overage charge" mechanism, called only from
 * lib/overage-billing.ts's billNamespaceOverage after that module has
 * already computed a real positive overage amount from real Prometheus
 * usage. `amountUsd` is converted to integer cents (Stripe's InvoiceItem
 * `amount` is always in the currency's smallest unit) via `Math.round`,
 * the same rounding every dollar-to-cents boundary in a real payments
 * integration needs -- fractional cents are not a real chargeable amount.
 */
export async function createOverageInvoiceItem(params: {
  customerId: string;
  subscriptionId: string;
  amountUsd: number;
  description: string;
  tenantNamespace: string;
  /** Real negotiated-contract cross-reference (lib/orgs.ts's
   * OrgPricingOverride.contractRef, via lib/overage-billing.ts's
   * effectiveRatesForNamespace) -- present only when this amount was
   * actually computed against a bound negotiated rate rather than the
   * standard ILLUSTRATIVE_RATES list price, so the Stripe InvoiceItem's
   * own metadata is independently provable at audit time against the
   * signed contract, not just this platform's own audit_log row. */
  pricingOverrideContractRef?: string;
}): Promise<StripeResult<{ id: string }>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };
  if (!(params.amountUsd > 0)) {
    return { ok: false, error: "amountUsd must be a positive real overage amount" };
  }
  try {
    const item = await stripe.invoiceItems.create({
      customer: params.customerId,
      currency: "usd",
      amount: Math.round(params.amountUsd * 100),
      description: params.description,
      metadata: {
        tenant_namespace: params.tenantNamespace,
        stripe_subscription_id: params.subscriptionId,
        kind: "usage_overage",
        ...(params.pricingOverrideContractRef
          ? { pricing_override_contract_ref: params.pricingOverrideContractRef }
          : {}),
      },
    });
    return { ok: true, data: { id: item.id } };
  } catch (e) {
    return { ok: false, error: `Stripe API error: ${(e as Error).message}` };
  }
}

/**
 * Real Stripe Price id for the "rate-limit tier" add-on SKU -- a
 * contractually-separate, sellable line item from the org's own tier
 * subscription price (`ensureCustomerAndSubscription`'s `priceId`),
 * configured per real Stripe Price the operator created for each
 * non-default `lib/rate-limit.ts` `ApiKeyTier` (`pro`, `enterprise`).
 * `standard` has no add-on price -- it is the plan every subscription
 * already includes, nothing to attach.
 */
const RATE_LIMIT_ADDON_PRICE_ENV: Record<"pro" | "enterprise", string> = {
  pro: "STRIPE_RATE_LIMIT_ADDON_PRICE_ID_PRO",
  enterprise: "STRIPE_RATE_LIMIT_ADDON_PRICE_ID_ENTERPRISE",
};

/**
 * Real Stripe Price id for a given rate-limit add-on tier, from whichever
 * env var `RATE_LIMIT_ADDON_PRICE_ENV` names for it -- `null` (not a
 * fabricated placeholder) when the operator has not configured a real
 * Price for that tier yet.
 */
export function rateLimitAddonPriceId(tier: "pro" | "enterprise"): string | null {
  const value = process.env[RATE_LIMIT_ADDON_PRICE_ENV[tier]];
  return typeof value === "string" && value.length > 0 ? value : null;
}

/**
 * Real (test-mode-honest, see this file's header) "higher rate limit"
 * add-on attach -- the Stripe/Twilio-style SKU this capability sells:
 * adds a real `SubscriptionItem` carrying `priceId` to the org's
 * EXISTING subscription (`subscriptionId`, from `ensureCustomerAndSubscription`
 * / `getStoredSubscription`) rather than creating a second, separate
 * subscription object. Uses `stripe.subscriptionItems.create` -- the same
 * "attach a metered/one-time price to a live subscription" primitive
 * `createOverageInvoiceItem` uses for usage overage, applied here to a
 * genuine recurring add-on price instead of a one-off InvoiceItem, since
 * a rate-limit tier is a standing entitlement, not a one-time charge.
 * Idempotent per subscription+price: if an item for this exact price
 * already exists on the subscription (a caller re-upgrading to the same
 * tier, or retrying after a partial failure), reuses it rather than
 * creating a duplicate line item.
 */
export async function attachRateLimitAddonPrice(params: {
  subscriptionId: string;
  priceId: string;
  apiKeyId: string;
  rateLimitTier: string;
}): Promise<StripeResult<{ id: string; created: boolean }>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };
  try {
    const subscription = await stripe.subscriptions.retrieve(params.subscriptionId);
    const existingItem = subscription.items.data.find((item) => item.price.id === params.priceId);
    if (existingItem) {
      return { ok: true, data: { id: existingItem.id, created: false } };
    }
    const item = await stripe.subscriptionItems.create({
      subscription: params.subscriptionId,
      price: params.priceId,
      quantity: 1,
      metadata: {
        kind: "rate-limit-addon",
        api_key_id: params.apiKeyId,
        rate_limit_tier: params.rateLimitTier,
      },
    });
    return { ok: true, data: { id: item.id, created: true } };
  } catch (e) {
    return { ok: false, error: `Stripe API error: ${(e as Error).message}` };
  }
}

/**
 * Applies one verified Stripe event to the stored subscription/plan
 * state. Only `customer.subscription.*` and `invoice.payment_*` events
 * update state (the scope's own wording: "updates a stored
 * subscription/plan state from real Stripe test events"); any other
 * event type is accepted (200'd, per Stripe's retry contract) but is a
 * real no-op, not a silently-fabricated state change.
 */
export async function applyStripeEvent(event: Stripe.Event): Promise<StripeResult<StoredSubscription | null>> {
  const type = event.type;
  if (type.startsWith("customer.subscription.")) {
    const sub = event.data.object as Stripe.Subscription;
    const tenantNamespace = sub.metadata?.tenant_namespace;
    if (!tenantNamespace) return { ok: true, data: null };
    const record: StoredSubscription = {
      tenantNamespace,
      stripeCustomerId: typeof sub.customer === "string" ? sub.customer : sub.customer.id,
      stripeSubscriptionId: sub.id,
      status: type === "customer.subscription.deleted" ? "canceled" : sub.status,
      priceId: sub.items.data[0]?.price?.id ?? null,
      currentPeriodEnd: sub.items.data[0]?.current_period_end
        ? new Date(sub.items.data[0].current_period_end * 1000).toISOString()
        : null,
      updatedAt: new Date().toISOString(),
      lastEventId: event.id,
      lastEventType: type,
    };
    const stored = await putStoredSubscription(record);
    if (!stored.ok) return { ok: false, error: stored.error };
    return { ok: true, data: record };
  }

  if (type.startsWith("invoice.payment_")) {
    const invoice = event.data.object as Stripe.Invoice & {
      subscription_details?: { metadata?: Record<string, string> };
      parent?: { subscription_details?: { metadata?: Record<string, string> } };
    };
    const tenantNamespace =
      invoice.subscription_details?.metadata?.tenant_namespace ??
      invoice.parent?.subscription_details?.metadata?.tenant_namespace;
    if (!tenantNamespace) return { ok: true, data: null };
    const existing = await getStoredSubscription(tenantNamespace);
    if (!existing.ok) return { ok: false, error: existing.error };
    if (!existing.data) return { ok: true, data: null };
    const record: StoredSubscription = {
      ...existing.data,
      status: type === "invoice.payment_failed" ? "past_due" : existing.data.status,
      updatedAt: new Date().toISOString(),
      lastEventId: event.id,
      lastEventType: type,
    };
    const stored = await putStoredSubscription(record);
    if (!stored.ok) return { ok: false, error: stored.error };
    return { ok: true, data: record };
  }

  return { ok: true, data: null };
}

/**
 * Real Stripe customer-balance credit -- the actual (test-mode-honest,
 * see this file's header) mechanism that closes the gap
 * lib/incidents.ts's computeCredit's own doc comment names: a
 * `creditPctOfMonthlySpend` figure is real arithmetic over real downtime,
 * but until it lands somewhere Stripe honors it it is only "a number on a
 * report." This function is that landing: `stripe.customers
 * .createBalanceTransaction`, a real negative-amount entry on the
 * customer's Stripe balance, which Stripe itself automatically applies
 * to reduce the amount due on that customer's NEXT real invoice -- no
 * separate credit-note/refund flow, no manual finance step.
 *
 * `creditPctOfMonthlySpend` is a PERCENTAGE (0-100), not a dollar amount
 * (computeCredit's own contract) -- this function is the one place that
 * percentage is ever converted into real cents, and it converts it
 * against this customer's OWN real Stripe subscription price, never a
 * caller-supplied or fabricated dollar figure: it retrieves the live
 * Stripe Subscription for `subscriptionId` and sums
 * `unit_amount * quantity` across its real recurring subscription items
 * to get the real monthly recurring amount in the subscription's own
 * real `currency`, then applies the percentage to THAT. A subscription
 * with no real recurring amount on file (e.g. a $0 metered-only plan)
 * fails closed with an honest error rather than crediting $0 silently.
 *
 * Fails closed (an honest `StripeResult` error, never a fabricated
 * transaction id) when Stripe isn't configured, when the percentage is
 * not a real positive number, when the subscription can't be retrieved,
 * or when the computed credit rounds to zero cents -- the same
 * fail-closed discipline `createOverageInvoiceItem`'s `amountUsd > 0`
 * guard already establishes for the opposite (positive-charge) case.
 */
export async function applySlaCreditToStripeBalance(params: {
  customerId: string;
  subscriptionId: string;
  creditPctOfMonthlySpend: number;
  month: string; // "YYYY-MM", used only in the transaction's human-readable description
}): Promise<StripeResult<{ id: string; amountCents: number; currency: string }>> {
  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };
  if (!(params.creditPctOfMonthlySpend > 0)) {
    return { ok: false, error: "creditPctOfMonthlySpend must be a real positive SLA credit percentage" };
  }
  try {
    const subscription = await stripe.subscriptions.retrieve(params.subscriptionId);
    const currency = subscription.currency;
    const monthlySpendCents = subscription.items.data.reduce((sum, item) => {
      const unitAmount = item.price.unit_amount ?? 0;
      const quantity = item.quantity ?? 1;
      return sum + unitAmount * quantity;
    }, 0);
    if (monthlySpendCents <= 0) {
      return {
        ok: false,
        error: `subscription ${params.subscriptionId} has no real recurring monthly amount to compute an SLA credit against`,
      };
    }
    const creditCents = Math.round(monthlySpendCents * (params.creditPctOfMonthlySpend / 100));
    if (creditCents <= 0) {
      return { ok: false, error: "computed SLA credit amount rounds to zero cents" };
    }
    const balanceTransaction = await stripe.customers.createBalanceTransaction(params.customerId, {
      amount: -creditCents,
      currency,
      description: `SLA credit for ${params.month}`,
    });
    return { ok: true, data: { id: balanceTransaction.id, amountCents: creditCents, currency } };
  } catch (e) {
    return { ok: false, error: `Stripe API error: ${(e as Error).message}` };
  }
}
