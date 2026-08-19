/**
 * Real Status-Page Change Subscription (statuspage.io "Subscribe to
 * updates" equivalent): a customer (no login required -- this is a
 * public self-service form on the public /status page, same
 * unauthenticated posture as GET /api/status itself) registers an email
 * address or an outbound webhook URL, optionally scoped to a subset of
 * component ids, and is notified the moment lib/status-page.ts's real
 * Prometheus-derived component state actually changes -- detected by
 * POST /api/cron/status-change-notify diffing getStatusPageData()
 * against a persisted last-snapshot on every cron tick (see that
 * route's header comment for why this is cron-driven rather than a
 * second in-process poller).
 *
 * Storage: one real k8s ConfigMap (`platform-console-status-subscriptions`,
 * `platform-console` namespace), the same get-then-create-or-patch
 * primitive lib/k8s.ts's Feature Flags / Webhooks / Budget Alerts modules
 * already established (`getConfigMap`/`createOrUpdateConfigMap`) -- no
 * new k8s resource kind, no new RBAC verb: the
 * `platform-console-feature-flags` Role (k8s/paas-rbac.yaml) already
 * grants get/list/create/update/patch on `configmaps` in this namespace
 * with no `resourceNames` restriction, so this Nth ConfigMap needs zero
 * YAML changes, same reasoning every sibling module's header comment
 * documents.
 *
 * One ConfigMap `data` key per subscription (a generated id, restricted
 * to the `[-._a-zA-Z0-9]+` alphabet a ConfigMap key must match), value is
 * one JSON-encoded StatusSubscription record. Deleting a subscription
 * (self-service, via the unsubscribe token embedded in every
 * notification) is a real RFC 7386 merge patch with that key's value set
 * to `null` -- the merge-patch spec's own key-removal convention, same
 * one lib/webhooks.ts's deleteWebhookSubscription already uses.
 *
 * Webhook-type subscribers are delivered through lib/webhooks.ts's real
 * `performHttpDelivery` signed-POST primitive and
 * lib/webhook-deliveries.ts's real retry-with-backoff / DLQ / immutable
 * per-attempt ledger (the exact infrastructure every other event type
 * already uses) under the `status.component_changed` event type -- never
 * a second, divergent delivery mechanism. Email-type subscribers are
 * delivered through lib/email.ts's real SMTP client; email has no
 * retry/backoff pipeline here (SMTP submission is itself synchronous
 * accept/reject at the target MTA, and there is no equivalent DLQ
 * concept for a fire-and-forget outbound message) -- a send failure is
 * logged and the notification is not retried, which is disclosed here
 * rather than silently implied to have the same durability as the
 * webhook path.
 */
import crypto from "node:crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { isPlausibleEmail, sendEmail } from "@/lib/email";
import { performHttpDelivery } from "@/lib/webhooks";
import { recordDeliveryAttempt } from "@/lib/webhook-deliveries";
import type { StatusComponent } from "@/lib/status-page";

export const STATUS_SUBSCRIPTIONS_NAMESPACE = "platform-console";
export const STATUS_SUBSCRIPTIONS_CONFIGMAP = "platform-console-status-subscriptions";

export type StatusSubscriptionType = "email" | "webhook";

export interface StatusSubscription {
  id: string;
  type: StatusSubscriptionType;
  /** Email address (type "email") or destination URL (type "webhook"). */
  target: string;
  /** HMAC-SHA256 signing secret for webhook-type subscriptions, generated
   * once at creation -- null for email-type subscriptions, which have no
   * analogous signature convention. */
  secret: string | null;
  /** Component ids this subscriber wants notified about. `null` means
   * "all components" (no filter). */
  componentFilter: string[] | null;
  /** Random token, returned once at creation, that authenticates a
   * self-service DELETE with no session/login required -- the same
   * "possession of the token is the authorization" convention a
   * mailing-list unsubscribe link uses. */
  unsubscribeToken: string;
  createdAt: string;
}

function isStatusSubscriptionType(value: unknown): value is StatusSubscriptionType {
  return value === "email" || value === "webhook";
}

function toSubscription(id: string, raw: string): StatusSubscription | null {
  try {
    const parsed = JSON.parse(raw) as Partial<StatusSubscription>;
    if (
      isStatusSubscriptionType(parsed.type) &&
      typeof parsed.target === "string" &&
      typeof parsed.unsubscribeToken === "string" &&
      typeof parsed.createdAt === "string" &&
      (parsed.secret === null || typeof parsed.secret === "string") &&
      (parsed.componentFilter === null ||
        (Array.isArray(parsed.componentFilter) &&
          parsed.componentFilter.every((c) => typeof c === "string")))
    ) {
      return {
        id,
        type: parsed.type,
        target: parsed.target,
        secret: parsed.secret ?? null,
        componentFilter: parsed.componentFilter ?? null,
        unsubscribeToken: parsed.unsubscribeToken,
        createdAt: parsed.createdAt,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Real list of every registered status subscription, newest first. Used
 * both by POST /api/cron/status-change-notify (to fan out a real change)
 * and could back a future admin list view; no route currently exposes
 * this list publicly (a subscriber's own record is only ever returned to
 * them once, at creation, plus reachable again only via their own
 * unsubscribe token -- never a public enumeration of every subscriber's
 * email/URL). */
export async function listStatusSubscriptions(): Promise<K8sResult<StatusSubscription[]>> {
  const result = await getConfigMap(STATUS_SUBSCRIPTIONS_NAMESPACE, STATUS_SUBSCRIPTIONS_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};
  const subscriptions = Object.entries(data)
    .map(([id, raw]) => toSubscription(id, raw))
    .filter((s): s is StatusSubscription => s !== null)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { ok: true, data: subscriptions };
}

export async function getStatusSubscriptionById(
  id: string,
): Promise<K8sResult<StatusSubscription | null>> {
  const all = await listStatusSubscriptions();
  if (!all.ok) return all;
  return { ok: true, data: all.data.find((s) => s.id === id) ?? null };
}

// ConfigMap data keys must match [-._a-zA-Z0-9]+; lowercase hex + hyphen
// is a subset. Prefixed distinctly from lib/webhooks.ts's `sub-...` ids
// (`statussub-...`) so a subscriptionId alone unambiguously identifies
// which ConfigMap/registry a retry (lib/webhook-poller.ts's
// pollWebhookRetries) should resolve it against.
function generateSubscriptionId(): string {
  return `statussub-${Date.now().toString(36)}-${crypto.randomBytes(4).toString("hex")}`;
}

function generateUnsubscribeToken(): string {
  return crypto.randomBytes(24).toString("hex");
}

export interface CreateStatusSubscriptionInput {
  type: StatusSubscriptionType;
  target: string;
  componentFilter: string[] | null;
}

export type CreateStatusSubscriptionOutcome =
  | { ok: true; data: StatusSubscription }
  | { ok: false; error: string; status: number };

/**
 * Validates and creates one real subscription. Validation here is the
 * same hand-written `typeof`/regex shape check every other module in
 * this codebase uses at its API boundary (lib/webhooks.ts's
 * isWebhookEventType, lib/budget-alerts.ts's threshold checks, etc.) --
 * this codebase has no `zod` dependency installed anywhere, so this
 * follows the actual established convention rather than introducing a
 * new one for a single route.
 */
export async function createStatusSubscription(
  input: CreateStatusSubscriptionInput,
): Promise<CreateStatusSubscriptionOutcome> {
  if (input.type === "email") {
    if (!isPlausibleEmail(input.target)) {
      return { ok: false, error: "invalid email address", status: 400 };
    }
  } else if (input.type === "webhook") {
    try {
      const parsed = new URL(input.target);
      if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
        return { ok: false, error: "webhookUrl must be http(s)", status: 400 };
      }
    } catch {
      return { ok: false, error: "invalid webhookUrl", status: 400 };
    }
  } else {
    return { ok: false, error: "type must be 'email' or 'webhook' (or supply email/webhookUrl)", status: 400 };
  }

  const subscription: StatusSubscription = {
    id: generateSubscriptionId(),
    type: input.type,
    target: input.target,
    secret: input.type === "webhook" ? crypto.randomBytes(32).toString("hex") : null,
    componentFilter:
      input.componentFilter && input.componentFilter.length > 0 ? input.componentFilter : null,
    unsubscribeToken: generateUnsubscribeToken(),
    createdAt: new Date().toISOString(),
  };

  const result = await createOrUpdateConfigMap(
    STATUS_SUBSCRIPTIONS_NAMESPACE,
    STATUS_SUBSCRIPTIONS_CONFIGMAP,
    { [subscription.id]: JSON.stringify(subscription) },
  );
  if (!result.ok) return { ok: false, error: result.error, status: 502 };
  return { ok: true, data: subscription };
}

/**
 * Self-service unsubscribe: deletes the one subscription whose
 * `unsubscribeToken` matches, via the same real RFC 7386
 * null-value merge patch lib/webhooks.ts's deleteWebhookSubscription
 * uses. Possession of the token (returned once at creation, and
 * embedded in every notification this module sends) is the entire
 * authorization -- no session required, matching every real status-page
 * product's own unsubscribe-link convention.
 */
export async function deleteStatusSubscriptionByToken(
  token: string,
): Promise<K8sResult<{ removed: boolean }>> {
  const all = await listStatusSubscriptions();
  if (!all.ok) return all;
  const match = all.data.find((s) => s.unsubscribeToken === token);
  if (!match) return { ok: true, data: { removed: false } };

  const result = await createOrUpdateConfigMap(
    STATUS_SUBSCRIPTIONS_NAMESPACE,
    STATUS_SUBSCRIPTIONS_CONFIGMAP,
    { [match.id]: null } as unknown as Record<string, string>,
  );
  if (!result.ok) return result;
  return { ok: true, data: { removed: true } };
}

export interface StatusChangeNotificationResult {
  subscriptionId: string;
  type: StatusSubscriptionType;
  ok: boolean;
  error: string | null;
}

/**
 * Notifies one subscriber of a real set of changed components (already
 * filtered by componentFilter by the caller -- see
 * app/api/cron/status-change-notify/route.ts). Webhook-type delivery
 * reuses lib/webhooks.ts's real signed-POST primitive plus
 * lib/webhook-deliveries.ts's real attempt ledger under attempt 1/
 * `status.component_changed`, so a failed first attempt is left
 * `pending_retry` for lib/webhook-poller.ts's existing 10s tick to pick
 * up exactly like any other event type (see that poller's
 * pollWebhookRetries, extended to resolve `statussub-...` ids against
 * this module instead of lib/webhooks.ts's registry). Email-type
 * delivery is a single real SMTP send with no retry (see this module's
 * header comment for why).
 */
export async function notifyStatusSubscriber(
  subscription: StatusSubscription,
  changedComponents: StatusComponent[],
  generatedAt: string,
): Promise<StatusChangeNotificationResult> {
  if (subscription.type === "email") {
    const lines = changedComponents.map(
      (c) => `- ${c.label} (${c.id}): now ${c.state}${c.up === null ? "" : c.up ? " (up)" : " (down)"}`,
    );
    const result = await sendEmail({
      to: subscription.target,
      subject: `Platform status change: ${changedComponents.map((c) => c.label).join(", ")}`,
      text:
        `The following platform component(s) changed status as of ${generatedAt}:\n\n` +
        `${lines.join("\n")}\n\n` +
        `To stop receiving these notifications, visit:\n` +
        `/api/status/subscribe?unsubscribeToken=${subscription.unsubscribeToken}\n`,
    });
    return {
      subscriptionId: subscription.id,
      type: "email",
      ok: result.ok,
      error: result.ok ? null : result.error,
    };
  }

  const deliveryId = crypto.randomUUID();
  const body = JSON.stringify({
    id: deliveryId,
    type: "status.component_changed",
    timestamp: generatedAt,
    data: {
      changedComponents,
      unsubscribeToken: subscription.unsubscribeToken,
    },
  });
  const attempt = await performHttpDelivery(
    subscription.target,
    body,
    subscription.secret ?? "",
    "status.component_changed",
    deliveryId,
  );

  recordDeliveryAttempt({
    deliveryId,
    subscriptionId: subscription.id,
    eventType: "status.component_changed",
    url: subscription.target,
    body,
    ok: attempt.ok,
    httpStatus: attempt.status,
    error: attempt.error,
    durationMs: attempt.durationMs,
    attemptNumber: 1,
  }).catch((err) => {
    console.error(`[status-subscriptions] failed to persist delivery attempt ${deliveryId}:`, err);
  });

  return {
    subscriptionId: subscription.id,
    type: "webhook",
    ok: attempt.ok,
    error: attempt.error,
  };
}

/**
 * Redelivers ONE already-persisted `status.component_changed` webhook
 * event -- the status-subscription analog of lib/webhooks.ts's
 * redeliverStoredEvent, called by lib/webhook-poller.ts's
 * pollWebhookRetries whenever a due retry's `subscriptionId` is a
 * `statussub-...` id (i.e. it belongs to this registry, not the
 * `platform-console-webhooks` one). Looks up the subscription's CURRENT
 * secret/URL fresh, exactly like redeliverStoredEvent, since either may
 * have changed (impossible for a secret today, since this module never
 * exposes a rotate endpoint, but the URL is gone the moment the
 * subscriber unsubscribes) since the original attempt.
 */
export async function redeliverStatusSubscriptionEvent(params: {
  deliveryId: string;
  subscriptionId: string;
  body: string;
  attemptNumber: number;
}): Promise<StatusChangeNotificationResult | null> {
  const subscriptionResult = await getStatusSubscriptionById(params.subscriptionId);
  if (!subscriptionResult.ok || !subscriptionResult.data || subscriptionResult.data.type !== "webhook") {
    await recordDeliveryAttempt({
      deliveryId: params.deliveryId,
      subscriptionId: params.subscriptionId,
      eventType: "status.component_changed",
      url: "",
      body: params.body,
      ok: false,
      httpStatus: null,
      error: "status subscription no longer exists",
      durationMs: 0,
      attemptNumber: 5,
    }).catch((err) =>
      console.error(`[status-subscriptions] failed to persist dead-letter for ${params.deliveryId}:`, err),
    );
    return null;
  }
  const subscription = subscriptionResult.data;

  const attempt = await performHttpDelivery(
    subscription.target,
    params.body,
    subscription.secret ?? "",
    "status.component_changed",
    params.deliveryId,
  );

  await recordDeliveryAttempt({
    deliveryId: params.deliveryId,
    subscriptionId: params.subscriptionId,
    eventType: "status.component_changed",
    url: subscription.target,
    body: params.body,
    ok: attempt.ok,
    httpStatus: attempt.status,
    error: attempt.error,
    durationMs: attempt.durationMs,
    attemptNumber: params.attemptNumber,
  }).catch((err) =>
    console.error(`[status-subscriptions] failed to persist delivery attempt ${params.deliveryId}:`, err),
  );

  return {
    subscriptionId: subscription.id,
    type: "webhook",
    ok: attempt.ok,
    error: attempt.error,
  };
}
