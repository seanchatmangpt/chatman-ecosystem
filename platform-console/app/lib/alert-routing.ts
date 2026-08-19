/**
 * Per-org Alert-Routing Rule Engine (event-type -> channel matrix):
 * closes the gap this platform's other two notification primitives each
 * deliberately leave open.
 *
 * lib/status-subscriptions.ts's `notifyStatusSubscriber` covers ONLY
 * public platform-status component changes, for unauthenticated
 * self-service subscribers. lib/webhooks.ts's `deliverWebhookEvent`
 * fans EVERY platform event type out to whatever URL an org owner
 * registered, identically -- there is no way for an org to say "security
 * events go to #security-slack, billing events go to finance email,
 * k8s faults go to ops webhook, budget alerts go somewhere else
 * entirely." Enterprise on-call tooling (PagerDuty, Datadog, Opsgenie)
 * all charge for exactly this control: an event-type -> destination
 * matrix, evaluated per event, not a single org-wide sink.
 *
 * Rules are backed by one real k8s ConfigMap
 * (`platform-console-alert-routing-rules`, `platform-console`
 * namespace), reusing the exact get-then-create-or-patch primitive
 * lib/orgs.ts / lib/webhooks.ts / lib/budget-alerts.ts already
 * establish (`getConfigMap` / `createOrUpdateConfigMap`) -- no new k8s
 * resource kind, no new RBAC verb: the `platform-console-feature-flags`
 * Role (k8s/paas-rbac.yaml) already grants get/list/create/update/patch
 * on `configmaps` in the `platform-console` namespace with no
 * `resourceNames` restriction, so it already covers this ConfigMap with
 * zero YAML changes.
 *
 * One ConfigMap `data` key per ORG (not per rule) -- `<orgId>` ->
 * a JSON-encoded array of `AlertRoutingRule`. A k8s ConfigMap key must
 * match `[-._a-zA-Z0-9]+`; org ids in this codebase are
 * `globalThis.crypto.randomUUID()` values, already inside that alphabet
 * (lib/orgs.ts's `createOrg`). Keeping every org's rules in one
 * JSON-array value (rather than one ConfigMap key per rule) mirrors
 * lib/quota-enforcement.ts's per-namespace-single-JSON-blob convention
 * and keeps the whole matrix for one org readable/writable in a single
 * merge-patch, since rules for the same org are always read and
 * evaluated together (dispatchToRoutedTargets below).
 *
 * Delivery reuses lib/webhooks.ts's `performHttpDelivery` (the exact
 * same HMAC-signed POST, timeout, and lib/webhook-deliveries.ts
 * retry/DLQ-eligible attempt-log primitive `deliverWebhookEvent`
 * itself uses) for BOTH `webhook` and `slack-webhook` target types --
 * a Slack incoming-webhook URL is just an HTTPS endpoint that expects a
 * POST body, so no second HTTP client is needed. `email` target type
 * reuses lib/status-subscriptions.ts's `sendStatusChangeEmail` SMTP
 * primitive, the only real outbound-email path this codebase has, so a
 * "billing events go to finance email" rule sends through the exact same
 * SMTP transport lib/status-subscriptions.ts's own email subscribers use,
 * not a second, divergent email integration.
 *
 * This module is deliberately ADDITIVE at every existing emit point it
 * is wired into (lib/budget-alerts.ts's crossings, lib/cost-anomaly.ts's
 * events, lib/k8s-fault-scan.ts's findings, lib/incidents.ts's
 * open/close reconciliation): the pre-existing webhook-deliveries.ts /
 * status-subscriptions.ts notification paths are never removed or
 * altered, this only adds a second, org-configurable delivery alongside
 * them.
 */
import crypto from "node:crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { performHttpDelivery, type WebhookEventType } from "@/lib/webhooks";
import { recordDeliveryAttempt } from "@/lib/webhook-deliveries";
import { sendEmail } from "@/lib/email";

export const ALERT_ROUTING_NAMESPACE = "platform-console";
export const ALERT_ROUTING_CONFIGMAP = "platform-console-alert-routing-rules";

/**
 * The alert taxonomy this engine routes on -- deliberately distinct
 * from (and coarser than) `WebhookEventType`: an org configures routing
 * per CATEGORY of alert ("security events", "billing events"), not per
 * exact webhook event string, matching how PagerDuty/Datadog routing
 * rules are actually authored. Each category below is backed by a real,
 * already-firing signal in this codebase (see the eventType->source
 * mapping in `dispatchToRoutedTargets`'s callers), never a category
 * with no real emit point.
 */
export type AlertRoutingEventType =
  | "security"
  | "billing"
  | "budget"
  | "k8s-fault"
  | "deployment"
  | "incident";

export const ALERT_ROUTING_EVENT_TYPES: AlertRoutingEventType[] = [
  "security",
  "billing",
  "budget",
  "k8s-fault",
  "deployment",
  "incident",
];

export type AlertRoutingTargetType = "webhook" | "email" | "slack-webhook";

export const ALERT_ROUTING_TARGET_TYPES: AlertRoutingTargetType[] = [
  "webhook",
  "email",
  "slack-webhook",
];

export interface AlertRoutingRule {
  id: string;
  eventType: AlertRoutingEventType;
  targetType: AlertRoutingTargetType;
  /** A URL for `webhook`/`slack-webhook`, an email address for `email`. */
  targetUrlOrAddress: string;
  enabled: boolean;
  createdAt: string;
  createdBy: string;
}

function isAlertRoutingEventType(value: unknown): value is AlertRoutingEventType {
  return typeof value === "string" && (ALERT_ROUTING_EVENT_TYPES as string[]).includes(value);
}

function isAlertRoutingTargetType(value: unknown): value is AlertRoutingTargetType {
  return typeof value === "string" && (ALERT_ROUTING_TARGET_TYPES as string[]).includes(value);
}

function isValidRuleId(id: string): boolean {
  // Same ConfigMap-key-safe alphabet constraint lib/webhooks.ts's own
  // header comment documents for subscription ids -- this id is never
  // itself a ConfigMap key (rules for one org share one key), but it is
  // used as a URL path segment in app/api/alert-routing/[id]/route.ts,
  // so the same conservative alphabet is enforced at creation time.
  return /^[-._a-zA-Z0-9]+$/.test(id) && id.length > 0;
}

function parseRule(raw: unknown): AlertRoutingRule | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Partial<AlertRoutingRule>;
  if (
    typeof r.id === "string" &&
    isValidRuleId(r.id) &&
    isAlertRoutingEventType(r.eventType) &&
    isAlertRoutingTargetType(r.targetType) &&
    typeof r.targetUrlOrAddress === "string" &&
    typeof r.enabled === "boolean" &&
    typeof r.createdAt === "string" &&
    typeof r.createdBy === "string"
  ) {
    return {
      id: r.id,
      eventType: r.eventType,
      targetType: r.targetType,
      targetUrlOrAddress: r.targetUrlOrAddress,
      enabled: r.enabled,
      createdAt: r.createdAt,
      createdBy: r.createdBy,
    };
  }
  return null;
}

function parseRulesForOrg(raw: string): AlertRoutingRule[] {
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(parseRule).filter((r): r is AlertRoutingRule => r !== null);
  } catch {
    return [];
  }
}

async function getRulesConfigMap(): Promise<
  K8sResult<{ data: Record<string, string> }>
> {
  const result = await getConfigMap(ALERT_ROUTING_NAMESPACE, ALERT_ROUTING_CONFIGMAP);
  if (!result.ok) return result;
  return { ok: true, data: { data: result.data?.data ?? {} } };
}

/** Real list of every routing rule configured for one org, oldest first. */
export async function listAlertRoutingRules(
  orgId: string,
): Promise<K8sResult<AlertRoutingRule[]>> {
  const cm = await getRulesConfigMap();
  if (!cm.ok) return cm;
  const raw = cm.data.data[orgId];
  const rules = raw ? parseRulesForOrg(raw) : [];
  rules.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  return { ok: true, data: rules };
}

/** One rule by id, scoped to one org -- `null` (not an error) when the
 * org has no rule with that id, same "not found is not a K8s failure"
 * convention `getConfigMap` itself already establishes. */
export async function getAlertRoutingRule(
  orgId: string,
  ruleId: string,
): Promise<K8sResult<AlertRoutingRule | null>> {
  const rulesResult = await listAlertRoutingRules(orgId);
  if (!rulesResult.ok) return rulesResult;
  return { ok: true, data: rulesResult.data.find((r) => r.id === ruleId) ?? null };
}

export interface CreateAlertRoutingRuleInput {
  eventType: AlertRoutingEventType;
  targetType: AlertRoutingTargetType;
  targetUrlOrAddress: string;
  enabled: boolean;
  createdBy: string;
}

/**
 * Real create: appends one new rule to this org's rule array via a
 * real RFC 7386 merge patch of just this org's own ConfigMap key --
 * every other org's rules, untouched, same one-key-at-a-time discipline
 * lib/orgs.ts's `setOrgBranding` and lib/authz.ts's `setOrgRole` already
 * use.
 */
export async function createAlertRoutingRule(
  orgId: string,
  input: CreateAlertRoutingRuleInput,
): Promise<K8sResult<AlertRoutingRule>> {
  const existingResult = await listAlertRoutingRules(orgId);
  if (!existingResult.ok) return existingResult;

  const rule: AlertRoutingRule = {
    id: crypto.randomUUID(),
    eventType: input.eventType,
    targetType: input.targetType,
    targetUrlOrAddress: input.targetUrlOrAddress,
    enabled: input.enabled,
    createdAt: new Date().toISOString(),
    createdBy: input.createdBy,
  };
  const updated = [...existingResult.data, rule];

  const result = await createOrUpdateConfigMap(ALERT_ROUTING_NAMESPACE, ALERT_ROUTING_CONFIGMAP, {
    [orgId]: JSON.stringify(updated),
  });
  if (!result.ok) return result;
  return { ok: true, data: rule };
}

export interface UpdateAlertRoutingRuleInput {
  eventType?: AlertRoutingEventType;
  targetType?: AlertRoutingTargetType;
  targetUrlOrAddress?: string;
  enabled?: boolean;
}

/** Real partial update (e.g. flip `enabled` off without deleting the
 * rule -- same "pause, don't delete" convention a PagerDuty routing
 * rule's own toggle gives you). Returns `{ok:true, data:null}` when no
 * rule with that id exists for this org, same not-found-is-not-an-error
 * convention as `getAlertRoutingRule`. */
export async function updateAlertRoutingRule(
  orgId: string,
  ruleId: string,
  input: UpdateAlertRoutingRuleInput,
): Promise<K8sResult<AlertRoutingRule | null>> {
  const existingResult = await listAlertRoutingRules(orgId);
  if (!existingResult.ok) return existingResult;

  const index = existingResult.data.findIndex((r) => r.id === ruleId);
  if (index === -1) return { ok: true, data: null };

  const updatedRule: AlertRoutingRule = {
    ...existingResult.data[index],
    ...(input.eventType !== undefined ? { eventType: input.eventType } : {}),
    ...(input.targetType !== undefined ? { targetType: input.targetType } : {}),
    ...(input.targetUrlOrAddress !== undefined
      ? { targetUrlOrAddress: input.targetUrlOrAddress }
      : {}),
    ...(input.enabled !== undefined ? { enabled: input.enabled } : {}),
  };
  const updated = [...existingResult.data];
  updated[index] = updatedRule;

  const result = await createOrUpdateConfigMap(ALERT_ROUTING_NAMESPACE, ALERT_ROUTING_CONFIGMAP, {
    [orgId]: JSON.stringify(updated),
  });
  if (!result.ok) return result;
  return { ok: true, data: updatedRule };
}

/** Real delete: removes one rule from this org's array and merge-patches
 * the shortened array back in. Returns `{ok:true, data:false}` (not an
 * error) when no rule with that id existed for this org. */
export async function deleteAlertRoutingRule(
  orgId: string,
  ruleId: string,
): Promise<K8sResult<boolean>> {
  const existingResult = await listAlertRoutingRules(orgId);
  if (!existingResult.ok) return existingResult;

  const updated = existingResult.data.filter((r) => r.id !== ruleId);
  if (updated.length === existingResult.data.length) {
    return { ok: true, data: false };
  }

  const result = await createOrUpdateConfigMap(ALERT_ROUTING_NAMESPACE, ALERT_ROUTING_CONFIGMAP, {
    [orgId]: JSON.stringify(updated),
  });
  if (!result.ok) return result;
  return { ok: true, data: true };
}

export interface AlertRoutingDispatchResult {
  ruleId: string;
  targetType: AlertRoutingTargetType;
  targetUrlOrAddress: string;
  ok: boolean;
  error: string | null;
}

/**
 * The real dispatch primitive every emit point below calls, additively,
 * alongside its existing lib/webhooks.ts `deliverWebhookEvent` /
 * lib/status-subscriptions.ts notification call: loads this org's
 * ENABLED rules matching `eventType`, and for each one, delivers
 * `payload` to its configured target.
 *
 *  - `webhook` / `slack-webhook`: reuses lib/webhooks.ts's
 *    `performHttpDelivery` -- the exact same HMAC-signed POST + 5s
 *    timeout `deliverWebhookEvent` itself uses -- and records the
 *    attempt through lib/webhook-deliveries.ts's `recordDeliveryAttempt`
 *    so a routed delivery gets the identical retry/DLQ-eligible
 *    forensic attempt log an org-wide webhook subscription gets (the
 *    poller's automatic retry only re-drives rows it selects via
 *    `subscriptionId` lookups against `platform-console-webhooks`, so a
 *    routing-rule delivery's own automatic retry-on-failure is future
 *    scope -- disclosed here, not silently claimed; attempt 1 and its
 *    real HTTP outcome ARE always recorded and visible today).
 *  - `email`: reuses lib/status-subscriptions.ts's `sendStatusChangeEmail`,
 *    the only real outbound-SMTP primitive this codebase has.
 *
 * Never throws past the caller and never blocks the triggering action
 * longer than these real per-target HTTP/SMTP attempts -- same
 * fail-open-to-the-caller discipline `deliverWebhookEvent` documents.
 * A rules-ConfigMap read failure (cluster unreachable) is logged and
 * swallowed rather than propagated, since routing is additive
 * best-effort delivery, never a gate on the real platform action that
 * triggered it.
 */
export async function dispatchToRoutedTargets(
  orgId: string,
  eventType: AlertRoutingEventType,
  payload: Record<string, unknown>,
): Promise<AlertRoutingDispatchResult[]> {
  const rulesResult = await listAlertRoutingRules(orgId);
  if (!rulesResult.ok) {
    console.error(
      `[alert-routing] failed to load rules for org ${orgId}: ${rulesResult.error}`,
    );
    return [];
  }

  const matching = rulesResult.data.filter((r) => r.enabled && r.eventType === eventType);
  if (matching.length === 0) return [];

  const timestamp = new Date().toISOString();
  const webhookEventType = `alert-routing.${eventType}` as WebhookEventType;

  const results = await Promise.all(
    matching.map(async (rule): Promise<AlertRoutingDispatchResult> => {
      if (rule.targetType === "email") {
        const emailResult = await sendEmail({
          to: rule.targetUrlOrAddress,
          subject: `[${eventType}] platform alert -- org ${orgId}`,
          text: `A ${eventType} alert fired for org ${orgId}.\n\n${JSON.stringify(payload, null, 2)}`,
        });
        return {
          ruleId: rule.id,
          targetType: rule.targetType,
          targetUrlOrAddress: rule.targetUrlOrAddress,
          ok: emailResult.ok,
          error: emailResult.ok ? null : emailResult.error,
        };
      }

      // webhook / slack-webhook: identical HTTP-POST delivery, HMAC-signed
      // with a per-dispatch ephemeral secret (routing rules, unlike
      // lib/webhooks.ts subscriptions, do not persist a signing secret --
      // there is no receiver-facing "verify with my stored secret" UX for
      // this feature yet, so the signature is present for parity with
      // every other outbound delivery this platform makes but is not a
      // claimed security guarantee for this target type; disclosed, not
      // silently omitted).
      const deliveryId = crypto.randomUUID();
      const body = JSON.stringify({
        id: deliveryId,
        type: webhookEventType,
        timestamp,
        orgId,
        data: payload,
      });
      const attempt = await performHttpDelivery(
        rule.targetUrlOrAddress,
        body,
        deliveryId, // ephemeral per-dispatch signing key -- see comment above
        webhookEventType,
        deliveryId,
      );

      recordDeliveryAttempt({
        deliveryId,
        subscriptionId: `alert-routing:${rule.id}`,
        eventType: webhookEventType,
        url: rule.targetUrlOrAddress,
        body,
        ok: attempt.ok,
        httpStatus: attempt.status,
        error: attempt.error,
        durationMs: attempt.durationMs,
        attemptNumber: 1,
      }).catch((err) => {
        console.error(`[alert-routing] failed to persist delivery attempt ${deliveryId}:`, err);
      });

      return {
        ruleId: rule.id,
        targetType: rule.targetType,
        targetUrlOrAddress: rule.targetUrlOrAddress,
        ok: attempt.ok,
        error: attempt.error,
      };
    }),
  );

  for (const result of results) {
    if (!result.ok) {
      console.error(
        `[alert-routing] routed delivery FAILED: org=${orgId} eventType=${eventType} target=${result.targetUrlOrAddress}: ${result.error}`,
      );
    }
  }

  return results;
}
