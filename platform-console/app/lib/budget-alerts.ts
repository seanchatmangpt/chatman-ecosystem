/**
 * Real Budget Alerts (AWS Budgets / GCP Billing Budgets equivalent): an
 * operator sets one real threshold per namespace (a CPU-core-hours ceiling,
 * or an illustrative-cost-USD ceiling, over the SAME trailing window
 * /billing and /usage already compute) and gets a real, HMAC-SHA256-signed
 * webhook the moment real measured usage genuinely crosses it -- reusing
 * lib/invoice-preview.ts's already-real Prometheus-derived per-namespace
 * metrics (no second query path, no simulated number) and
 * lib/webhooks.ts's already-real delivery mechanism, fired from
 * lib/webhook-poller.ts's existing 10s tick (see pollBudgetThresholds
 * there) rather than a second poller.
 *
 * Storage: one real k8s ConfigMap (`platform-budget-thresholds`,
 * `platform-console` namespace), reusing the exact get-then-create-or-patch
 * primitive lib/k8s.ts's Feature Flags module established
 * (`getConfigMap`/`createOrUpdateConfigMap`) -- no new k8s resource kind,
 * no new RBAC verb: the same `platform-console-feature-flags` Role
 * (k8s/paas-rbac.yaml) already grants get/list/create/update/patch on
 * `configmaps` in this namespace with no `resourceNames` restriction, so it
 * already covers this third ConfigMap (after Feature Flags and Webhooks)
 * with zero YAML changes.
 *
 * Two logically distinct key families share the one ConfigMap:
 *   `threshold.<namespace>`        -> JSON BudgetThreshold (operator config)
 *   `alerted.<namespace>.<metric>` -> JSON {crossedAt, value} (dedup marker)
 * A k8s namespace name is already a valid ConfigMap key
 * (`[-._a-zA-Z0-9]+` is a superset of the RFC 1123 label alphabet namespace
 * names use), so no escaping step like lib/authz.ts's encodeIdentifierKey
 * is ever needed here.
 *
 * checkBudgets() (the ONLY function that ever writes an `alerted.*` key) is
 * called exclusively by lib/webhook-poller.ts's pollBudgetThresholds --
 * never by the read-only GET /api/budget-alerts path, which calls
 * listBudgetUsages() instead. That split matters: if a page view could
 * also flip a namespace's alerted-state to true, an operator opening the
 * dashboard moments before the poller's own 10s tick would silently
 * swallow the one webhook delivery that tick was about to fire -- the
 * "already alerted" dedup would trip with zero real deliveries ever having
 * happened. Only the poller may observe-and-mark; every other caller only
 * observes.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import {
  computeLineItems,
  getNamespaceUsageMetrics,
  ILLUSTRATIVE_RATES,
  type NamespaceUsageMetrics,
} from "@/lib/invoice-preview";

export const BUDGET_NAMESPACE = "platform-console";
export const BUDGET_CONFIGMAP = "platform-budget-thresholds";

// Same trailing window /billing (app/billing/page.tsx) and /usage already
// use -- reusing it here means a budget threshold means exactly what the
// number already shown on /billing means, never a second, driftable
// definition of "usage".
export const BUDGET_WINDOW_LABEL = "1h";
export const BUDGET_WINDOW_HOURS = 1;

export type BudgetMetric = "cpu-core-hours" | "cost-usd";
export const BUDGET_METRICS: BudgetMetric[] = ["cpu-core-hours", "cost-usd"];

export interface BudgetThreshold {
  namespace: string;
  metric: BudgetMetric;
  threshold: number;
  setBy: string;
  setAt: string;
}

export interface BudgetUsage {
  namespace: string;
  metric: BudgetMetric;
  threshold: number;
  /** null only when the real Prometheus query for this namespace failed -- never a fabricated zero. */
  currentValue: number | null;
  overThreshold: boolean;
  alreadyAlerted: boolean;
  error: string | null;
}

export interface BudgetCrossing {
  namespace: string;
  metric: BudgetMetric;
  threshold: number;
  currentValue: number;
  crossedAt: string;
}

function isBudgetMetric(value: string): value is BudgetMetric {
  return value === "cpu-core-hours" || value === "cost-usd";
}

function thresholdKey(namespace: string): string {
  return `threshold.${namespace}`;
}
function alertedKey(namespace: string, metric: BudgetMetric): string {
  return `alerted.${namespace}.${metric}`;
}

function parseThreshold(namespace: string, raw: string): BudgetThreshold | null {
  try {
    const p = JSON.parse(raw) as Partial<BudgetThreshold>;
    if (
      typeof p.metric === "string" &&
      isBudgetMetric(p.metric) &&
      typeof p.threshold === "number" &&
      Number.isFinite(p.threshold) &&
      typeof p.setBy === "string" &&
      typeof p.setAt === "string"
    ) {
      return { namespace, metric: p.metric, threshold: p.threshold, setBy: p.setBy, setAt: p.setAt };
    }
    return null;
  } catch {
    return null;
  }
}

interface AlertedMarker {
  crossedAt: string;
  value: number;
}
function parseAlertedMarker(raw: string): AlertedMarker | null {
  try {
    const p = JSON.parse(raw) as Partial<AlertedMarker>;
    if (typeof p.crossedAt === "string" && typeof p.value === "number") {
      return { crossedAt: p.crossedAt, value: p.value };
    }
    return null;
  } catch {
    return null;
  }
}

interface RawBudgetConfigMap {
  thresholds: BudgetThreshold[];
  /** Keyed by the exact ConfigMap key (alertedKey(namespace, metric)). */
  alerted: Map<string, AlertedMarker>;
}

async function readRawConfigMap(): Promise<K8sResult<RawBudgetConfigMap>> {
  const result = await getConfigMap(BUDGET_NAMESPACE, BUDGET_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};

  const thresholds: BudgetThreshold[] = [];
  const alerted = new Map<string, AlertedMarker>();
  for (const [key, raw] of Object.entries(data)) {
    if (key.startsWith("threshold.")) {
      const namespace = key.slice("threshold.".length);
      const parsed = namespace ? parseThreshold(namespace, raw) : null;
      if (parsed) thresholds.push(parsed);
    } else if (key.startsWith("alerted.")) {
      const marker = parseAlertedMarker(raw);
      if (marker) alerted.set(key, marker);
    }
  }
  thresholds.sort((a, b) => a.namespace.localeCompare(b.namespace));
  return { ok: true, data: { thresholds, alerted } };
}

/** Real list of every configured threshold, sorted by namespace. */
export async function listBudgetThresholds(): Promise<K8sResult<BudgetThreshold[]>> {
  const result = await readRawConfigMap();
  if (!result.ok) return result;
  return { ok: true, data: result.data.thresholds };
}

/**
 * Sets (creates or replaces) one namespace's threshold via a real RFC 7386
 * merge patch -- same one-key-at-a-time convention as Feature Flags'
 * setFlag. Also clears any pre-existing `alerted.*` marker for this
 * namespace (both possible metrics): a freshly configured threshold starts
 * un-alerted, same "genuinely new incident" reasoning
 * lib/webhook-poller.ts's own pollAlertFirings comment documents for a
 * resolved-then-refiring Alertmanager alert. Only markers already present
 * in the real ConfigMap are ever included as `null` in the patch (read via
 * readRawConfigMap first) -- never speculatively, which would send an
 * invalid `null` data value on the very first-ever write, when
 * createOrUpdateConfigMap takes the CREATE branch (a ConfigMap's `data`
 * map cannot contain `null`, only the PATCH branch's RFC 7386 semantics
 * accept it as "remove this key").
 */
export async function setBudgetThreshold(
  namespace: string,
  metric: BudgetMetric,
  threshold: number,
  setBy: string,
): Promise<K8sResult<BudgetThreshold[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;

  const record: BudgetThreshold = { namespace, metric, threshold, setBy, setAt: new Date().toISOString() };
  const patch: Record<string, string | null> = {
    [thresholdKey(namespace)]: JSON.stringify(record),
  };
  for (const m of BUDGET_METRICS) {
    if (raw.data.alerted.has(alertedKey(namespace, m))) {
      patch[alertedKey(namespace, m)] = null;
    }
  }

  const result = await createOrUpdateConfigMap(
    BUDGET_NAMESPACE,
    BUDGET_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!result.ok) return result;
  return listBudgetThresholds();
}

/**
 * Deletes one namespace's threshold (and any alerted marker for it) via a
 * real RFC 7386 merge patch setting those keys' values to `null`. A no-op
 * (no k8s write at all) when the namespace has no threshold configured --
 * covers both "ConfigMap doesn't exist yet" and "namespace never had a
 * threshold" without ever risking a `null`-valued CREATE (see
 * setBudgetThreshold's comment).
 */
export async function deleteBudgetThreshold(namespace: string): Promise<K8sResult<null>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  if (!raw.data.thresholds.some((t) => t.namespace === namespace)) {
    return { ok: true, data: null };
  }

  const patch: Record<string, string | null> = { [thresholdKey(namespace)]: null };
  for (const m of BUDGET_METRICS) {
    if (raw.data.alerted.has(alertedKey(namespace, m))) {
      patch[alertedKey(namespace, m)] = null;
    }
  }

  const result = await createOrUpdateConfigMap(
    BUDGET_NAMESPACE,
    BUDGET_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/**
 * Real current value for one metric from one real
 * lib/invoice-preview.ts#NamespaceUsageMetrics fetch -- cpu-core-hours is
 * read directly; cost-usd reuses computeLineItems' exact arithmetic
 * (ILLUSTRATIVE_RATES) /billing already applies, over the same fetched
 * metrics, never a second Prometheus round trip.
 */
function valueForMetric(metric: BudgetMetric, metrics: NamespaceUsageMetrics): number {
  if (metric === "cpu-core-hours") return metrics.cpuCoreHours;
  return computeLineItems([metrics], ILLUSTRATIVE_RATES)[0].totalCost;
}

/**
 * Real current usage for every configured threshold, READ-ONLY: fetches
 * live Prometheus-derived metrics via the SAME lib/invoice-preview.ts
 * functions /billing and /usage already call (no second query path), and
 * never writes an `alerted.*` dedup marker. Safe to call from a page
 * render or a GET route as often as needed -- see this module's header
 * comment for why that separation from checkBudgets is load-bearing.
 */
export async function listBudgetUsages(): Promise<K8sResult<BudgetUsage[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;

  const usages = await Promise.all(
    raw.data.thresholds.map(async (t): Promise<BudgetUsage> => {
      const metricsResult = await getNamespaceUsageMetrics(t.namespace, BUDGET_WINDOW_LABEL, BUDGET_WINDOW_HOURS);
      const alreadyAlerted = raw.data.alerted.has(alertedKey(t.namespace, t.metric));
      if (!metricsResult.ok) {
        return {
          namespace: t.namespace,
          metric: t.metric,
          threshold: t.threshold,
          currentValue: null,
          overThreshold: false,
          alreadyAlerted,
          error: metricsResult.error,
        };
      }
      const currentValue = valueForMetric(t.metric, metricsResult.data);
      return {
        namespace: t.namespace,
        metric: t.metric,
        threshold: t.threshold,
        currentValue,
        overThreshold: currentValue >= t.threshold,
        alreadyAlerted,
        error: null,
      };
    }),
  );
  return { ok: true, data: usages };
}

/**
 * Real crossing-detection PLUS the real dedup-state write -- the ONLY
 * function in this module that touches `alerted.*` keys. Called
 * exclusively by lib/webhook-poller.ts's pollBudgetThresholds on its
 * existing 10s tick (never a second poller). Returns exactly the
 * namespace+metric pairs whose real usage is over threshold on THIS check
 * and were NOT already marked alerted -- i.e. exactly the set that should
 * fire a fresh "budget.threshold_crossed" webhook delivery. A namespace
 * that drops back under threshold has its marker cleared, so a later
 * re-crossing (a genuinely new incident from an operator's perspective)
 * fires again rather than being permanently suppressed -- same reasoning
 * lib/webhook-poller.ts's pollAlertFirings already applies to Alertmanager
 * fingerprints. A namespace whose real Prometheus query fails this tick is
 * skipped entirely (logged, never treated as a crossing or a clear) --
 * fail-closed, matching lib/invoice-preview.ts's own convention.
 */
export async function checkBudgets(): Promise<K8sResult<BudgetCrossing[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  if (raw.data.thresholds.length === 0) return { ok: true, data: [] };

  const crossings: BudgetCrossing[] = [];
  const patch: Record<string, string | null> = {};
  const now = new Date().toISOString();

  for (const t of raw.data.thresholds) {
    const metricsResult = await getNamespaceUsageMetrics(t.namespace, BUDGET_WINDOW_LABEL, BUDGET_WINDOW_HOURS);
    if (!metricsResult.ok) {
      console.error(`[budget-alerts] usage query failed for ${t.namespace}: ${metricsResult.error}`);
      continue;
    }
    const currentValue = valueForMetric(t.metric, metricsResult.data);
    const overThreshold = currentValue >= t.threshold;
    const key = alertedKey(t.namespace, t.metric);
    const alreadyAlerted = raw.data.alerted.has(key);

    if (overThreshold && !alreadyAlerted) {
      patch[key] = JSON.stringify({ crossedAt: now, value: currentValue });
      crossings.push({
        namespace: t.namespace,
        metric: t.metric,
        threshold: t.threshold,
        currentValue,
        crossedAt: now,
      });
    } else if (!overThreshold && alreadyAlerted) {
      patch[key] = null;
    }
  }

  if (Object.keys(patch).length > 0) {
    const patched = await createOrUpdateConfigMap(
      BUDGET_NAMESPACE,
      BUDGET_CONFIGMAP,
      patch as unknown as Record<string, string>,
    );
    if (!patched.ok) return patched;
  }

  return { ok: true, data: crossings };
}
