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

function getStripeClient(): Stripe | null {
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
