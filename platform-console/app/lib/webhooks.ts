/**
 * Real hyperscaler-PaaS-style Outbound Webhooks / Event Notifications
 * primitive (AWS EventBridge / GCP Eventarc / Azure Event Grid
 * equivalent): an operator registers a URL to receive real HTTP POST
 * notifications when real platform events happen, with a real
 * HMAC-SHA256 signature (the GitHub `X-Hub-Signature-256` / Stripe
 * `Stripe-Signature` webhook-security convention) so a receiver can
 * independently verify authenticity.
 *
 * Subscriptions are backed by one real k8s ConfigMap
 * (`platform-console-webhooks`, `platform-console` namespace), reusing
 * the exact get-then-create-or-patch primitive lib/k8s.ts's Feature
 * Flags / Org Roles modules already established (`getConfigMap` /
 * `createOrUpdateConfigMap`) -- no new k8s resource kind, no new RBAC
 * verb: the `platform-console-feature-flags` Role (k8s/paas-rbac.yaml)
 * already grants get/list/create/update/patch on `configmaps` in the
 * `platform-console` namespace with no `resourceNames` restriction, so
 * it already covers this second ConfigMap with zero YAML changes --
 * same reasoning lib/authz.ts's own header comment documents for
 * `platform-console-org-roles`.
 *
 * One ConfigMap `data` key per subscription (a generated id -- a
 * ConfigMap key must match `[-._a-zA-Z0-9]+`, so the id alphabet below
 * is kept to exactly that set), value is one JSON-encoded subscription
 * record (eventType, url, secret, createdAt, createdBy). Deleting a
 * subscription is a real RFC 7386 merge patch with that key's value set
 * to `null` -- the merge-patch spec's own key-removal convention -- so
 * every other subscription already in the map is left untouched.
 */
import crypto from "node:crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { recordDeliveryAttempt, MAX_DELIVERY_ATTEMPTS } from "@/lib/webhook-deliveries";

export const WEBHOOKS_NAMESPACE = "platform-console";
export const WEBHOOKS_CONFIGMAP = "platform-console-webhooks";

/**
 * Real trigger points this console actually detects -- 2 of the 3 named
 * in the requirement, both wired end to end, never a fabricated 4th:
 *
 *  - "project.created": fires synchronously from the real
 *    `createProjectWithDatabase` success path (see
 *    app/api/projects/route.ts) the moment a Project + SingleDatabase
 *    pair is actually created.
 *  - "backup.completed": fires when a real backup Job
 *    (`lib/k8s.ts`'s `createBackupJob`) reaches `status.succeeded >= 1`
 *    -- detected by `lib/webhook-poller.ts` polling the exact same
 *    `listJobs` call the Backups module itself uses.
 *  - "alert.firing": the same real Alertmanager-backed trigger
 *    `lib/webhook-poller.ts` implements (a NEW alert fingerprint not
 *    present on the previous poll).
 *  - "budget.threshold_crossed": fires when a real per-namespace usage
 *    figure (lib/invoice-preview.ts's same Prometheus-derived
 *    cpu-core-hours/cost-usd /billing and /usage already compute) FIRST
 *    crosses an operator-configured threshold (lib/budget-alerts.ts) --
 *    detected by the same `lib/webhook-poller.ts` 10s tick, deduped by a
 *    real ConfigMap-persisted "already alerted" marker per
 *    namespace+metric so it fires once per crossing, not once per tick.
 *  - "quota.enforcement_triggered": fires the moment a real per-namespace
 *    ResourceQuota-percentage figure (lib/k8s.ts's `getResourceUsage`,
 *    the same one `/usage` already shows) FIRST crosses an
 *    operator-configured enforcement threshold (lib/quota-enforcement.ts)
 *    AND the real enforcement action (scaling the configured target
 *    Deployment to 0 replicas) has actually succeeded -- detected by the
 *    same `lib/webhook-poller.ts` 10s tick, fires exactly once per
 *    namespace since enforcement is never auto-reversed (see
 *    lib/quota-enforcement.ts's header comment).
 *  - "cost.anomaly_detected": fires the moment a real per-namespace
 *    trailing-15m spend figure (the same lib/invoice-preview.ts
 *    Prometheus-derived cost-usd number, over lib/cost.ts's shortest real
 *    trend window) FIRST deviates from that namespace's OWN real
 *    EWMA-smoothed baseline by more than a configurable percent
 *    (lib/cost-anomaly.ts) -- a statistical spike-vs-self signal distinct
 *    from budget.threshold_crossed's fixed operator-set ceiling, detected
 *    by the same `lib/webhook-poller.ts` 10s tick, deduped by a real
 *    ConfigMap-persisted baseline/state marker per namespace so it fires
 *    once per new anomaly, not once per tick.
 */
export type WebhookEventType =
  | "project.created"
  | "backup.completed"
  | "alert.firing"
  | "budget.threshold_crossed"
  | "quota.enforcement_triggered"
  | "plan_state.enforcement_triggered"
  | "cost.anomaly_detected"
  | "support.sla_breached"
  | "status.component_changed";
export const WEBHOOK_EVENT_TYPES: WebhookEventType[] = [
  "project.created",
  "backup.completed",
  "alert.firing",
  "budget.threshold_crossed",
  "quota.enforcement_triggered",
  "plan_state.enforcement_triggered",
  "cost.anomaly_detected",
  "support.sla_breached",
  "status.component_changed",
];

export interface WebhookSubscription {
  id: string;
  eventType: WebhookEventType;
  url: string;
  /** HMAC-SHA256 signing secret. Generated once at creation, never rotated
   * server-side; shown to the owner in the create response and again on
   * every list (this page is already owner-gated -- the same sensitivity
   * class as the URL itself, not a separate secret store). */
  secret: string;
  createdAt: string;
  createdBy: string;
}

function isWebhookEventType(value: string): value is WebhookEventType {
  return (WEBHOOK_EVENT_TYPES as string[]).includes(value);
}

function toSubscription(id: string, raw: string): WebhookSubscription | null {
  try {
    const parsed = JSON.parse(raw) as Partial<WebhookSubscription>;
    if (
      typeof parsed.eventType === "string" &&
      isWebhookEventType(parsed.eventType) &&
      typeof parsed.url === "string" &&
      typeof parsed.secret === "string" &&
      typeof parsed.createdAt === "string" &&
      typeof parsed.createdBy === "string"
    ) {
      return {
        id,
        eventType: parsed.eventType,
        url: parsed.url,
        secret: parsed.secret,
        createdAt: parsed.createdAt,
        createdBy: parsed.createdBy,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Real list of every registered subscription, newest first. */
export async function listWebhookSubscriptions(): Promise<K8sResult<WebhookSubscription[]>> {
  const result = await getConfigMap(WEBHOOKS_NAMESPACE, WEBHOOKS_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};
  const subscriptions = Object.entries(data)
    .map(([id, raw]) => toSubscription(id, raw))
    .filter((s): s is WebhookSubscription => s !== null)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { ok: true, data: subscriptions };
}

async function getWebhookSubscriptionsForEvent(
  eventType: WebhookEventType,
): Promise<K8sResult<WebhookSubscription[]>> {
  const all = await listWebhookSubscriptions();
  if (!all.ok) return all;
  return { ok: true, data: all.data.filter((s) => s.eventType === eventType) };
}

/** Real single-subscription lookup, used by the retry poller and the
 * manual replay route -- neither has the subscription object in hand
 * already (a retry/replay only carries a persisted deliveryId), and both
 * need the subscription's CURRENT secret + URL (which may have changed,
 * or the subscription may have been deleted, since the original
 * attempt). */
export async function getWebhookSubscriptionById(
  id: string,
): Promise<K8sResult<WebhookSubscription | null>> {
  const all = await listWebhookSubscriptions();
  if (!all.ok) return all;
  return { ok: true, data: all.data.find((s) => s.id === id) ?? null };
}

// ConfigMap data keys must match [-._a-zA-Z0-9]+ -- this alphabet
// (lowercase hex + hyphen) is a subset of that, so no encoding step is
// ever needed the way lib/authz.ts's identifier keys require.
function generateSubscriptionId(): string {
  return `sub-${Date.now().toString(36)}-${crypto.randomBytes(4).toString("hex")}`;
}

/**
 * Creates a real subscription: a fresh random id, a fresh random
 * 32-byte HMAC secret, written into the real ConfigMap via a real RFC
 * 7386 merge patch (or create, on first-ever subscription).
 */
export async function createWebhookSubscription(
  eventType: WebhookEventType,
  url: string,
  createdBy: string,
): Promise<K8sResult<WebhookSubscription>> {
  const subscription: WebhookSubscription = {
    id: generateSubscriptionId(),
    eventType,
    url,
    secret: crypto.randomBytes(32).toString("hex"),
    createdAt: new Date().toISOString(),
    createdBy,
  };
  const result = await createOrUpdateConfigMap(WEBHOOKS_NAMESPACE, WEBHOOKS_CONFIGMAP, {
    [subscription.id]: JSON.stringify(subscription),
  });
  if (!result.ok) return result;
  return { ok: true, data: subscription };
}

/**
 * Deletes one subscription via a real RFC 7386 merge patch setting that
 * key's value to `null` -- the merge-patch spec's own key-removal
 * semantics (the API server's merge, not this app's own filtering, is
 * what actually removes the entry). `createOrUpdateConfigMap`'s
 * `Record<string, string>` parameter type is deliberately widened here
 * with a cast since `null` is only ever valid on the patch path, never
 * on a fresh create.
 */
export async function deleteWebhookSubscription(id: string): Promise<K8sResult<null>> {
  const result = await createOrUpdateConfigMap(
    WEBHOOKS_NAMESPACE,
    WEBHOOKS_CONFIGMAP,
    { [id]: null } as unknown as Record<string, string>,
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

export interface WebhookDeliveryResult {
  subscriptionId: string;
  url: string;
  ok: boolean;
  status: number | null;
  error: string | null;
  durationMs: number;
  /** Hex HMAC-SHA256 digest actually sent in the
   * `x-platform-webhook-signature-256` header, over the exact bytes of
   * the request body -- recorded here so a caller (or this app's own
   * audit trail) can show the real value that was sent, not a
   * recomputed guess. */
  signature: string;
  deliveryId: string;
}

const DELIVERY_TIMEOUT_MS = 5000;

/**
 * Real, single HTTP POST attempt -- pure network I/O, no persistence.
 * Signs `body` (the EXACT bytes sent) with the subscription's current
 * secret using the same `sha256=<hex>` convention GitHub's
 * `X-Hub-Signature-256` uses, so any receiver can independently
 * recompute `HMAC-SHA256(secret, rawBody)` and compare, byte for byte.
 * Never throws -- a network error or timeout is captured into the
 * returned result exactly like a non-2xx HTTP response is, so every
 * caller (first attempt, scheduled retry, manual replay) handles both
 * the same way.
 */
/** Exported for reuse by lib/status-subscriptions.ts, which delivers
 * `status.component_changed` to webhook-type status subscribers using
 * this exact same signed-POST primitive (and lib/webhook-deliveries.ts's
 * same recordDeliveryAttempt ledger) rather than a second, divergent
 * HTTP-delivery implementation -- status subscriptions live in their own
 * ConfigMap (never the `platform-console-webhooks` registry this module
 * owns, since a status subscriber is unauthenticated/self-service, not
 * an owner-gated platform subscription), so they cannot go through
 * deliverWebhookEvent's listWebhookSubscriptions lookup, but they reuse
 * everything downstream of "subscription resolved to a URL+secret". */
export async function performHttpDelivery(
  url: string,
  body: string,
  secret: string,
  eventType: WebhookEventType,
  deliveryId: string,
): Promise<{ ok: boolean; status: number | null; error: string | null; durationMs: number; signature: string }> {
  const signature = crypto.createHmac("sha256", secret).update(body).digest("hex");
  const started = Date.now();
  const controller = new AbortController();
  const timeoutHandle = setTimeout(() => controller.abort(), DELIVERY_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "POST",
      signal: controller.signal,
      headers: {
        "content-type": "application/json",
        "x-platform-webhook-event": eventType,
        "x-platform-webhook-delivery": deliveryId,
        "x-platform-webhook-signature-256": `sha256=${signature}`,
      },
      body,
    });
    return {
      ok: res.ok,
      status: res.status,
      error: res.ok ? null : `HTTP ${res.status}`,
      durationMs: Date.now() - started,
      signature,
    };
  } catch (err) {
    return {
      ok: false,
      status: null,
      error: err instanceof Error ? err.message : String(err),
      durationMs: Date.now() - started,
      signature,
    };
  } finally {
    clearTimeout(timeoutHandle);
  }
}

/**
 * Real delivery: POSTs a real JSON payload
 * (`{ id, type, timestamp, data }`) to every subscriber URL registered
 * for `eventType`. Never throws past this function and never blocks the
 * caller on a slow or dead subscriber: every attempt is isolated in its
 * own try/catch (inside performHttpDelivery) with a real 5s timeout, and
 * one subscriber's failure never affects another's delivery or the
 * triggering action itself.
 *
 * Every attempt -- success or failure -- is persisted as attempt 1 of a
 * real delivery row (lib/webhook-deliveries.ts, on the same Postgres
 * lib/audit-db.ts already establishes). A failed attempt is NOT retried
 * inline here: it is left `pending_retry` with a real `nextAttemptAt`
 * (1m/5m/30m/2h exponential backoff, capped at 5 total attempts) for
 * lib/webhook-poller.ts's existing 10s tick to pick up, so a slow or
 * backoff-waiting subscriber never makes this function -- or the real
 * platform action that triggered it -- block longer than one real HTTP
 * attempt per subscriber.
 */
export async function deliverWebhookEvent(
  eventType: WebhookEventType,
  data: Record<string, unknown>,
): Promise<WebhookDeliveryResult[]> {
  const subscriptionsResult = await getWebhookSubscriptionsForEvent(eventType);
  if (!subscriptionsResult.ok || subscriptionsResult.data.length === 0) {
    return [];
  }

  const timestamp = new Date().toISOString();

  const results = await Promise.all(
    subscriptionsResult.data.map(async (subscription): Promise<WebhookDeliveryResult> => {
      const deliveryId = crypto.randomUUID();
      const body = JSON.stringify({ id: deliveryId, type: eventType, timestamp, data });
      const attempt = await performHttpDelivery(
        subscription.url,
        body,
        subscription.secret,
        eventType,
        deliveryId,
      );

      recordDeliveryAttempt({
        deliveryId,
        subscriptionId: subscription.id,
        eventType,
        url: subscription.url,
        body,
        ok: attempt.ok,
        httpStatus: attempt.status,
        error: attempt.error,
        durationMs: attempt.durationMs,
        attemptNumber: 1,
      }).catch((err) => {
        console.error(`[webhooks] failed to persist delivery attempt ${deliveryId}:`, err);
      });

      return {
        subscriptionId: subscription.id,
        url: subscription.url,
        ok: attempt.ok,
        status: attempt.status,
        error: attempt.error,
        durationMs: attempt.durationMs,
        signature: attempt.signature,
        deliveryId,
      };
    }),
  );

  for (const result of results) {
    if (result.ok) {
      console.log(
        `[webhooks] delivered ${eventType} -> ${result.url} (HTTP ${result.status}, ${result.durationMs}ms, delivery=${result.deliveryId})`,
      );
    } else {
      console.error(
        `[webhooks] delivery attempt 1 FAILED (will retry with backoff): ${eventType} -> ${result.url}: ${result.error}`,
      );
    }
  }

  return results;
}

/**
 * Redelivers ONE already-persisted event -- reused by both
 * lib/webhook-poller.ts's automatic-retry tick and
 * POST /api/webhooks/deliveries/[deliveryId]/replay's manual replay.
 * Looks up the subscription's CURRENT secret/URL fresh (never the
 * stored ones, since either may have changed or the subscription may
 * have been deleted since the original attempt) and resends the EXACT
 * persisted `body` bytes, so a receiver verifying the HMAC signature
 * sees the same signed content it would have on the original attempt.
 * Returns `null` (and dead-letters the row, since there is no longer a
 * valid destination) if the subscription no longer exists.
 */
export async function redeliverStoredEvent(params: {
  deliveryId: string;
  subscriptionId: string;
  eventType: WebhookEventType;
  body: string;
  attemptNumber: number;
}): Promise<WebhookDeliveryResult | null> {
  const subscriptionResult = await getWebhookSubscriptionById(params.subscriptionId);
  if (!subscriptionResult.ok || !subscriptionResult.data) {
    await recordDeliveryAttempt({
      deliveryId: params.deliveryId,
      subscriptionId: params.subscriptionId,
      eventType: params.eventType,
      url: "",
      body: params.body,
      ok: false,
      httpStatus: null,
      error: "subscription no longer exists",
      durationMs: 0,
      attemptNumber: MAX_DELIVERY_ATTEMPTS,
    }).catch((err) => console.error(`[webhooks] failed to persist dead-letter for ${params.deliveryId}:`, err));
    return null;
  }
  const subscription = subscriptionResult.data;

  const attempt = await performHttpDelivery(
    subscription.url,
    params.body,
    subscription.secret,
    params.eventType,
    params.deliveryId,
  );

  await recordDeliveryAttempt({
    deliveryId: params.deliveryId,
    subscriptionId: params.subscriptionId,
    eventType: params.eventType,
    url: subscription.url,
    body: params.body,
    ok: attempt.ok,
    httpStatus: attempt.status,
    error: attempt.error,
    durationMs: attempt.durationMs,
    attemptNumber: params.attemptNumber,
  }).catch((err) => console.error(`[webhooks] failed to persist delivery attempt ${params.deliveryId}:`, err));

  return {
    subscriptionId: subscription.id,
    url: subscription.url,
    ok: attempt.ok,
    status: attempt.status,
    error: attempt.error,
    durationMs: attempt.durationMs,
    signature: attempt.signature,
    deliveryId: params.deliveryId,
  };
}
