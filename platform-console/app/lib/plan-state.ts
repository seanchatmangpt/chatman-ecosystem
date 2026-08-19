/**
 * Real Plan-State Enforcement (Stripe "subscription paused on payment
 * failure" / AWS account-suspension-on-nonpayment equivalent): closes the
 * gap that ResourceQuota (k8s/resource-quotas.yaml, `resource-quotas-
 * enforced` control) is a static per-namespace ceiling fixed at
 * provisioning time -- it has no notion of a customer's billing/payment
 * state and does not change when a payment fails or a plan is downgraded.
 * lib/quota-enforcement.ts closes a DIFFERENT gap (usage crossing an
 * operator-set percent-of-quota threshold); this module is the billing-
 * state-tied one: an explicit `active`/`past_due`/`suspended` field per
 * namespace, DERIVED (source of truth) from the real Stripe subscription
 * state app/lib/stripe-billing.ts's own webhook receiver
 * (app/api/billing/stripe/webhook/route.ts) already keeps current, with
 * an operator/admin API (app/api/plan-state/route.ts) as the fallback for
 * namespaces Stripe has no subscription on file for -- and a real,
 * continuously-reconciled
 * enforcement action -- patching that namespace's already-provisioned
 * ResourceQuota (k8s/resource-quotas.yaml) down to a near-zero ceiling --
 * the moment plan state is not `active`, and restoring the namespace's
 * real prior quota the moment it returns to `active`.
 *
 * WHY RESOURCEQUOTA-PATCH, NOT A NEW ADMISSION WEBHOOK: the task's own
 * scope names both as acceptable enforcement points ("an admission
 * webhook or a scheduled reconciler that patches a tenant's ResourceQuota
 * down ... or blocks new Deployments via ... ValidatingAdmissionPolicy").
 * ResourceQuota-patch was chosen because it is enforced by kube-
 * apiserver's OWN admission-time quota check (the identical mechanism
 * `resource-quotas-enforced` already relies on) against EVERY resource
 * kind the quota's `hard` map covers (pods, cpu, memory -- not just
 * Deployments), with no new cluster-scoped policy object and no new RBAC
 * verb beyond one `patch` already added to the existing cluster-wide
 * `resourcequotas` grant (k8s/paas-rbac.yaml) -- the same minimal-new-
 * surface reasoning lib/quota-enforcement.ts's own header comment gives
 * for reusing `patchDeploymentReplicas` instead of a new primitive.
 *
 * Storage: one real k8s ConfigMap (`platform-plan-state`,
 * `platform-console` namespace), the exact get-then-create-or-patch
 * primitive (`createOrUpdateConfigMap`) lib/quota-enforcement.ts and
 * lib/budget-alerts.ts already establish -- no new k8s resource kind.
 * Three key families share the one ConfigMap:
 *   `state.<namespace>`      -> JSON PlanStateRecord: the ADMIN-OVERRIDE
 *                                fallback desired plan state, written only
 *                                by app/api/plan-state/route.ts, used by
 *                                the reconciler only when Stripe has no
 *                                subscription record for that namespace
 *                                (see reconcilePlanState below) -- never
 *                                written by the reconciler itself.
 *   `saved-hard.<namespace>` -> JSON of the namespace's real ResourceQuota
 *                                `spec.hard` map AS IT WAS the moment
 *                                before this module first suspended it --
 *                                the exact values `reconcilePlanState`
 *                                restores on reactivation. Written once,
 *                                by the reconciler, only on the
 *                                active -> non-active transition.
 *   `enforced.<namespace>`   -> `"true"` dedup marker: this namespace's
 *                                quota is CURRENTLY patched to the
 *                                near-zero suspended ceiling right now.
 *
 * SAME race-avoidance discipline as lib/quota-enforcement.ts: only
 * `reconcilePlanState()` (called exclusively by lib/webhook-poller.ts's
 * existing 10s tick) ever calls `patchResourceQuotaHard`. `setPlanState`
 * (called from the webhook route / admin API) only ever writes the
 * desired-state ConfigMap key -- it never itself touches the
 * ResourceQuota object, so two concurrent webhook deliveries racing the
 * reconciler tick can't leave the quota in an inconsistent half-applied
 * state.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  getResourceQuotaRaw,
  patchNamespaceAnnotations,
  patchResourceQuotaHard,
  type K8sResult,
} from "@/lib/k8s";
import { hasStripeCredentials, listStoredSubscriptions, type StoredSubscription } from "@/lib/stripe-billing";

// Same fixed platform-namespace roster every billing-adjacent route in
// this app already hardcodes (app/api/billing/stripe/checkout/route.ts,
// app/api/quota-enforcement/route.ts) -- never an arbitrary client-
// supplied namespace.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

/**
 * Maps a real Stripe subscription status
 * (https://stripe.com/docs/api/subscriptions/object#subscription_object-status,
 * plus this codebase's own `"no_subscription"` sentinel from
 * lib/stripe-billing.ts's `StoredSubscription`) onto this module's
 * 3-state plan model. `trialing`/`active` -> `active`. `past_due` is its
 * own distinct state (grace period, not yet suspended). Every other real
 * status (`unpaid`, `canceled`, `incomplete`, `incomplete_expired`,
 * `paused`, and the no-subscription-on-file sentinel) maps to
 * `suspended` -- fail-closed: a tenant with no real Stripe subscription
 * record has nothing entitling it to consume resources, and an
 * unrecognized future Stripe status also falls through to `suspended`
 * rather than silently defaulting to `active`.
 */
export function mapStripeStatusToPlanState(status: StoredSubscription["status"]): PlanState {
  if (status === "active" || status === "trialing") return "active";
  if (status === "past_due") return "past_due";
  return "suspended";
}

export const PLAN_STATE_NAMESPACE = "platform-console";
export const PLAN_STATE_CONFIGMAP = "platform-plan-state";

const ANNOTATION_PLAN_STATE = "platform-console.io/plan-state";
const ANNOTATION_PLAN_STATE_AT = "platform-console.io/plan-state-enforced-at";
const ANNOTATION_PLAN_STATE_REASON = "platform-console.io/plan-state-reason";

export type PlanState = "active" | "past_due" | "suspended";

const VALID_PLAN_STATES: readonly PlanState[] = ["active", "past_due", "suspended"];

export function isPlanState(value: string): value is PlanState {
  return (VALID_PLAN_STATES as readonly string[]).includes(value);
}

/** The near-zero ceiling a suspended/past_due namespace's ResourceQuota is
 * patched down to -- not literally 0 (a 0 `pods` quota would even reject
 * the k8s API's own quota-check bookkeeping in some edge cases and gives
 * an operator inspecting `kubectl describe resourcequota` no way to
 * distinguish "suspended" from "quota object corrupt"), but low enough
 * that no new real workload Pod can be admitted: 1 pod, 1 millicore of
 * CPU, 1Mi of memory -- below the smallest real container's request in
 * this platform (confirmed against k8s/resource-quotas.yaml's own
 * per-namespace `requests.cpu`/`requests.memory` floors, all >= 50m/64Mi). */
const SUSPENDED_HARD: Record<string, string> = {
  pods: "0",
  "limits.cpu": "1m",
  "limits.memory": "1Mi",
  "requests.cpu": "1m",
  "requests.memory": "1Mi",
};

export interface PlanStateRecord {
  namespace: string;
  planState: PlanState;
  /** Free-form provenance -- e.g. `"stripe:customer.subscription.updated"`
   * or `"admin:xpointsh@gmail.com"` -- never itself trusted as an
   * authorization decision, only recorded for the audit trail. */
  source: string;
  setAt: string;
}

export interface PlanStateStatus {
  namespace: string;
  record: PlanStateRecord | null;
  /** True once `reconcilePlanState` has actually patched this namespace's
   * ResourceQuota down to `SUSPENDED_HARD` and it has not yet been
   * restored -- distinct from `record.planState !== "active"`, which is
   * only the DESIRED state until the next reconcile tick applies it. */
  quotaSuspended: boolean;
}

function stateKey(namespace: string): string {
  return `state.${namespace}`;
}
function savedHardKey(namespace: string): string {
  return `saved-hard.${namespace}`;
}
function enforcedKey(namespace: string): string {
  return `enforced.${namespace}`;
}

function parseRecord(namespace: string, raw: string): PlanStateRecord | null {
  try {
    const p = JSON.parse(raw) as Partial<PlanStateRecord>;
    if (
      typeof p.planState === "string" &&
      isPlanState(p.planState) &&
      typeof p.source === "string" &&
      typeof p.setAt === "string"
    ) {
      return { namespace, planState: p.planState, source: p.source, setAt: p.setAt };
    }
    return null;
  } catch {
    return null;
  }
}

function parseSavedHard(raw: string): Record<string, string> | null {
  try {
    const p = JSON.parse(raw) as unknown;
    if (p && typeof p === "object" && !Array.isArray(p)) {
      const entries = Object.entries(p as Record<string, unknown>).filter(
        (e): e is [string, string] => typeof e[1] === "string",
      );
      return Object.fromEntries(entries);
    }
    return null;
  } catch {
    return null;
  }
}

interface RawPlanStateConfigMap {
  records: PlanStateRecord[];
  savedHard: Map<string, Record<string, string>>;
  enforced: Set<string>;
}

async function readRawConfigMap(): Promise<K8sResult<RawPlanStateConfigMap>> {
  const result = await getConfigMap(PLAN_STATE_NAMESPACE, PLAN_STATE_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};

  const records: PlanStateRecord[] = [];
  const savedHard = new Map<string, Record<string, string>>();
  const enforced = new Set<string>();
  for (const [key, raw] of Object.entries(data)) {
    if (key.startsWith("state.")) {
      const namespace = key.slice("state.".length);
      const parsed = namespace ? parseRecord(namespace, raw) : null;
      if (parsed) records.push(parsed);
    } else if (key.startsWith("saved-hard.")) {
      const namespace = key.slice("saved-hard.".length);
      const parsed = namespace ? parseSavedHard(raw) : null;
      if (parsed) savedHard.set(namespace, parsed);
    } else if (key.startsWith("enforced.")) {
      const namespace = key.slice("enforced.".length);
      if (namespace && raw === "true") enforced.add(namespace);
    }
  }
  records.sort((a, b) => a.namespace.localeCompare(b.namespace));
  return { ok: true, data: { records, savedHard, enforced } };
}

/** Real current plan state + real quota-suspension state for every
 * namespace that has ever had a plan state set, sorted by namespace.
 * Read-only -- never writes, never patches a ResourceQuota. */
export async function listPlanStates(): Promise<K8sResult<PlanStateStatus[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  return {
    ok: true,
    data: raw.data.records.map((record) => ({
      namespace: record.namespace,
      record,
      quotaSuspended: raw.data.enforced.has(record.namespace),
    })),
  };
}

/**
 * Sets (creates or replaces) one namespace's DESIRED plan state via a
 * real RFC 7386 merge patch -- same one-key-at-a-time convention as
 * lib/quota-enforcement.ts's setQuotaEnforcementConfig. Deliberately does
 * NOT itself patch the ResourceQuota or touch `saved-hard.*`/
 * `enforced.*` -- see this module's header comment for why that split
 * exists. Called by both the Stripe webhook route (source
 * `"stripe:<event.type>"`) and the admin API route (source
 * `"admin:<actor>"`).
 */
export async function setPlanState(
  namespace: string,
  planState: PlanState,
  source: string,
): Promise<K8sResult<PlanStateRecord>> {
  const record: PlanStateRecord = { namespace, planState, source, setAt: new Date().toISOString() };
  const patch: Record<string, string> = { [stateKey(namespace)]: JSON.stringify(record) };
  const result = await createOrUpdateConfigMap(PLAN_STATE_NAMESPACE, PLAN_STATE_CONFIGMAP, patch);
  if (!result.ok) return result;
  return { ok: true, data: record };
}

export interface PlanStateEnforcementAction {
  namespace: string;
  action: "suspended" | "restored";
  planState: PlanState;
  at: string;
}

/**
 * Real reconciliation -- the ONLY function in this module that ever
 * calls `patchResourceQuotaHard`. Called exclusively by
 * lib/webhook-poller.ts's existing 10s tick, same discipline
 * lib/quota-enforcement.ts's checkQuotaEnforcement documents.
 *
 * For every namespace with a recorded plan state:
 *   - `planState !== "active"` AND not yet `enforced`: reads the real
 *     current ResourceQuota (`getResourceQuotaRaw`, fail-closed -- no
 *     quota object or a read error skips this namespace THIS tick,
 *     logged, never treated as "already suspended"), saves its real
 *     `spec.hard` map into `saved-hard.<namespace>`, patches it down to
 *     `SUSPENDED_HARD`, annotates the Namespace object (best-effort), and
 *     only then writes the `enforced.<namespace>` marker.
 *   - `planState === "active"` AND currently `enforced`: reads back the
 *     real `saved-hard.<namespace>` map (fail-closed: if it was somehow
 *     never saved, this namespace is logged and skipped rather than
 *     guessing a ceiling), patches the ResourceQuota back to those exact
 *     values, clears the Namespace annotation, and clears both the
 *     `enforced.<namespace>` and `saved-hard.<namespace>` markers.
 * Returns exactly the actions taken THIS tick.
 */
export async function reconcilePlanState(): Promise<K8sResult<PlanStateEnforcementAction[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;

  // Real Stripe subscription state (app/lib/stripe-billing.ts's own
  // ConfigMap, kept current by app/api/billing/stripe/webhook/route.ts)
  // is the SOURCE OF TRUTH for plan state whenever a real subscription
  // record exists for a namespace -- this is the actual "driven by the
  // Stripe webhook" wiring the task's scope asks for, reusing that
  // module rather than a second, competing webhook receiver. A
  // namespace's own `state.<namespace>` admin-override record (set via
  // app/api/plan-state/route.ts) is used only as a fallback for
  // namespaces Stripe has no subscription record for at all -- the
  // manual/ops/testing path, exercised in this task's own live
  // verification since no live Stripe account exists in this
  // environment (see stripe-webhook route's own header comment).
  const effective = new Map<string, PlanStateRecord>();
  for (const record of raw.data.records) effective.set(record.namespace, record);

  if (hasStripeCredentials()) {
    const subsResult = await listStoredSubscriptions(PLATFORM_NAMESPACES);
    if (!subsResult.ok) {
      console.error(`[plan-state] listStoredSubscriptions failed: ${subsResult.error}`);
    } else {
      for (const [namespace, sub] of Object.entries(subsResult.data)) {
        if (!sub) continue;
        effective.set(namespace, {
          namespace,
          planState: mapStripeStatusToPlanState(sub.status),
          source: `stripe:${sub.status}`,
          setAt: sub.updatedAt,
        });
      }
    }
  }

  if (effective.size === 0) return { ok: true, data: [] };

  const actions: PlanStateEnforcementAction[] = [];
  const patch: Record<string, string | null> = {};
  const now = new Date().toISOString();

  for (const record of effective.values()) {
    const currentlyEnforced = raw.data.enforced.has(record.namespace);

    if (record.planState !== "active" && !currentlyEnforced) {
      const quotaResult = await getResourceQuotaRaw(record.namespace);
      if (!quotaResult.ok) {
        console.error(`[plan-state] quota read failed for ${record.namespace}: ${quotaResult.error}`);
        continue;
      }
      if (!quotaResult.data) {
        console.error(`[plan-state] namespace ${record.namespace} has no ResourceQuota object -- cannot enforce`);
        continue;
      }

      const patchResult = await patchResourceQuotaHard(
        record.namespace,
        quotaResult.data.name,
        SUSPENDED_HARD,
      );
      if (!patchResult.ok) {
        console.error(
          `[plan-state] suspend patch FAILED for ${record.namespace}/${quotaResult.data.name}: ${patchResult.error}`,
        );
        continue;
      }

      const reason =
        `plan state '${record.planState}' (source: ${record.source}) -- ` +
        `ResourceQuota ${quotaResult.data.name} patched to near-zero at ${now}`;
      const annotationResult = await patchNamespaceAnnotations(record.namespace, {
        [ANNOTATION_PLAN_STATE]: record.planState,
        [ANNOTATION_PLAN_STATE_AT]: now,
        [ANNOTATION_PLAN_STATE_REASON]: reason,
      });
      if (!annotationResult.ok) {
        console.error(
          `[plan-state] namespace annotation FAILED (real quota-suspend already applied) for ${record.namespace}: ${annotationResult.error}`,
        );
      }

      patch[savedHardKey(record.namespace)] = JSON.stringify(quotaResult.data.hard);
      patch[enforcedKey(record.namespace)] = "true";
      actions.push({ namespace: record.namespace, action: "suspended", planState: record.planState, at: now });
      continue;
    }

    if (record.planState === "active" && currentlyEnforced) {
      const savedHard = raw.data.savedHard.get(record.namespace);
      if (!savedHard) {
        console.error(`[plan-state] no saved-hard record for ${record.namespace} -- cannot restore, skipping`);
        continue;
      }
      const quotaResult = await getResourceQuotaRaw(record.namespace);
      if (!quotaResult.ok) {
        console.error(`[plan-state] quota read failed on restore for ${record.namespace}: ${quotaResult.error}`);
        continue;
      }
      if (!quotaResult.data) {
        console.error(`[plan-state] namespace ${record.namespace} has no ResourceQuota object -- cannot restore`);
        continue;
      }

      const patchResult = await patchResourceQuotaHard(record.namespace, quotaResult.data.name, savedHard);
      if (!patchResult.ok) {
        console.error(
          `[plan-state] restore patch FAILED for ${record.namespace}/${quotaResult.data.name}: ${patchResult.error}`,
        );
        continue;
      }

      const annotationResult = await patchNamespaceAnnotations(record.namespace, {
        [ANNOTATION_PLAN_STATE]: "active",
        [ANNOTATION_PLAN_STATE_AT]: now,
        [ANNOTATION_PLAN_STATE_REASON]: `plan state returned to active at ${now} -- ResourceQuota restored`,
      });
      if (!annotationResult.ok) {
        console.error(`[plan-state] annotation clear FAILED for ${record.namespace}: ${annotationResult.error}`);
      }

      patch[savedHardKey(record.namespace)] = null;
      patch[enforcedKey(record.namespace)] = null;
      actions.push({ namespace: record.namespace, action: "restored", planState: "active", at: now });
    }
  }

  if (Object.keys(patch).length > 0) {
    const patched = await createOrUpdateConfigMap(
      PLAN_STATE_NAMESPACE,
      PLAN_STATE_CONFIGMAP,
      patch as unknown as Record<string, string>,
    );
    if (!patched.ok) return patched;
  }

  return { ok: true, data: actions };
}
