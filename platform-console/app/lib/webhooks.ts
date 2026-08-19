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
 */
export type WebhookEventType =
  | "project.created"
  | "backup.completed"
  | "alert.firing"
  | "budget.threshold_crossed"
  | "quota.enforcement_triggered"
  | "plan_state.enforcement_triggered";
export const WEBHOOK_EVENT_TYPES: WebhookEventType[] = [
  "project.created",
  "backup.completed",
  "alert.firing",
  "budget.threshold_crossed",
  "quota.enforcement_triggered",
  "plan_state.enforcement_triggered",
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
 * Real delivery: POSTs a real JSON payload
 * (`{ id, type, timestamp, data }`) to every subscriber URL registered
 * for `eventType`, with a real HMAC-SHA256 signature computed over the
 * EXACT serialized body bytes -- the same `sha256=<hex>` convention
 * GitHub's `X-Hub-Signature-256` uses, so any receiver can independently
 * recompute `HMAC-SHA256(secret, rawBody)` and compare, byte for byte.
 * Never throws past this function and never blocks the caller on a slow
 * or dead subscriber: every attempt is isolated in its own try/catch
 * with a real 5s timeout, and one subscriber's failure never affects
 * another's delivery or the triggering action itself.
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
      const signature = crypto.createHmac("sha256", subscription.secret).update(body).digest("hex");
      const started = Date.now();
      const controller = new AbortController();
      const timeoutHandle = setTimeout(() => controller.abort(), DELIVERY_TIMEOUT_MS);
      try {
        const res = await fetch(subscription.url, {
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
          subscriptionId: subscription.id,
          url: subscription.url,
          ok: res.ok,
          status: res.status,
          error: res.ok ? null : `HTTP ${res.status}`,
          durationMs: Date.now() - started,
          signature,
          deliveryId,
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          subscriptionId: subscription.id,
          url: subscription.url,
          ok: false,
          status: null,
          error: message,
          durationMs: Date.now() - started,
          signature,
          deliveryId,
        };
      } finally {
        clearTimeout(timeoutHandle);
      }
    }),
  );

  for (const result of results) {
    if (result.ok) {
      console.log(
        `[webhooks] delivered ${eventType} -> ${result.url} (HTTP ${result.status}, ${result.durationMs}ms, delivery=${result.deliveryId})`,
      );
    } else {
      console.error(`[webhooks] delivery FAILED: ${eventType} -> ${result.url}: ${result.error}`);
    }
  }

  return results;
}
