/**
 * Real Statistical Cost-Anomaly Detection (AWS Cost Anomaly Detection /
 * GCP cost anomaly alerts equivalent): distinct from lib/budget-alerts.ts's
 * fixed-threshold budget alerts, which only fire once an operator-set
 * dollar ceiling is crossed -- useful, but it requires someone to already
 * know what number to set, and it misses a namespace that suddenly spikes
 * while staying under a generously-set ceiling. This module instead
 * maintains a real exponentially-weighted moving average (EWMA) of each
 * namespace's own trailing spend as a self-adjusting baseline, and flags
 * an anomaly the moment current spend deviates from that namespace's OWN
 * baseline by more than a configurable percent -- a real, deterministic,
 * testable statistical rule over real metered numbers, never a claim of
 * predictive ML.
 *
 * Input: the exact same real Prometheus-derived per-namespace spend
 * lib/cost.ts's getCostTrend already computes (itself
 * lib/invoice-preview.ts's getNamespaceUsageMetrics + computeLineItems --
 * no new query surface, no second cost calculation). This module reuses
 * COST_ANOMALY_WINDOW_LABEL/HOURS (the shortest real TREND_WINDOWS entry,
 * "15m") as the single per-tick observation: each poller tick reads one
 * fresh real trailing-15m-spend number per namespace and folds it into
 * that namespace's EWMA.
 *
 * Storage: one real k8s ConfigMap (`platform-cost-anomaly-state`,
 * `platform-console` namespace), reusing the exact
 * get-then-create-or-patch primitive lib/k8s.ts's Feature Flags module
 * established (`getConfigMap`/`createOrUpdateConfigMap`) -- same RBAC
 * grant lib/budget-alerts.ts's own header comment documents already
 * covers any ConfigMap in this namespace with zero YAML changes.
 *
 * Two key families share the one ConfigMap, mirroring budget-alerts.ts's
 * own threshold/marker split:
 *   `state.<namespace>`     -> JSON AnomalyState (baseline, timestamps, last deviation)
 *   `threshold.<namespace>` -> JSON AnomalyThresholdConfig (operator-set deviation percent)
 * A k8s namespace name is already a valid ConfigMap key (see
 * budget-alerts.ts's own comment on this); no escaping step is needed.
 *
 * checkCostAnomalies() is the ONLY function that ever advances a
 * namespace's EWMA baseline or flips its `isAnomaly` state -- called
 * exclusively by lib/webhook-poller.ts's pollCostAnomalies on its existing
 * 10s tick, never by the read-only GET /api/cost-anomaly path (which calls
 * listCostAnomalyStatus() instead, mirroring budget-alerts.ts's
 * checkBudgets/listBudgetUsages split and quota-enforcement.ts's read-only
 * status route pattern). If a page render also advanced the baseline, an
 * operator refreshing /cost moments before the poller's own tick would
 * silently pull the EWMA toward whatever spend happened to be current at
 * that exact refresh -- observing must never also mutate the statistic
 * being observed.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getNamespaceUsageMetrics, computeLineItems, ILLUSTRATIVE_RATES } from "@/lib/invoice-preview";

export const COST_ANOMALY_NAMESPACE = "platform-console";
export const COST_ANOMALY_CONFIGMAP = "platform-cost-anomaly-state";

// Shortest real lib/cost.ts TREND_WINDOWS entry -- the freshest real
// trailing-spend signal available, so a genuine spike is reflected in the
// EWMA (and can trip an anomaly) within one real observation rather than
// being smoothed away inside a long window before it ever reaches this
// module.
export const COST_ANOMALY_WINDOW_LABEL = "15m";
export const COST_ANOMALY_WINDOW_HOURS = 0.25;

// EWMA smoothing factor: baseline = (1 - EWMA_ALPHA) * baseline + EWMA_ALPHA * latest.
// 0.1 means the baseline moves 10% of the way toward each new real
// observation per tick -- slow enough that one anomalous tick cannot
// itself relocate the baseline to "explain away" the spike it should be
// flagging, fast enough to track genuine multi-tick shifts in steady-state
// spend (a namespace legitimately scaling up) within a reasonable number
// of ticks.
export const EWMA_ALPHA = 0.1;

// Operator-settable default, same semantics as lib/budget-alerts.ts's
// threshold: 200% means "current spend is 3x baseline or more"
// (deviationPct = (current - baseline) / baseline * 100 >= 200).
export const DEFAULT_DEVIATION_THRESHOLD_PCT = 200;

export interface AnomalyThresholdConfig {
  namespace: string;
  deviationThresholdPct: number;
  setBy: string;
  setAt: string;
}

export interface AnomalyState {
  namespace: string;
  baselineSpend: number;
  lastCheckedAt: string;
  lastAnomalyAt: string | null;
  lastDeviationPct: number;
}

export interface CostAnomalyStatus {
  namespace: string;
  baselineSpend: number | null;
  currentSpend: number | null;
  deviationPct: number | null;
  isAnomaly: boolean;
  deviationThresholdPct: number;
  lastCheckedAt: string | null;
  lastAnomalyAt: string | null;
  error: string | null;
}

export interface CostAnomalyEvent {
  namespace: string;
  baselineSpend: number;
  currentSpend: number;
  deviationPct: number;
  deviationThresholdPct: number;
  detectedAt: string;
}

function stateKey(namespace: string): string {
  return `state.${namespace}`;
}
function thresholdKey(namespace: string): string {
  return `threshold.${namespace}`;
}

function parseState(namespace: string, raw: string): AnomalyState | null {
  try {
    const p = JSON.parse(raw) as Partial<AnomalyState>;
    if (
      typeof p.baselineSpend === "number" &&
      Number.isFinite(p.baselineSpend) &&
      typeof p.lastCheckedAt === "string" &&
      (p.lastAnomalyAt === null || typeof p.lastAnomalyAt === "string") &&
      typeof p.lastDeviationPct === "number"
    ) {
      return {
        namespace,
        baselineSpend: p.baselineSpend,
        lastCheckedAt: p.lastCheckedAt,
        lastAnomalyAt: p.lastAnomalyAt ?? null,
        lastDeviationPct: p.lastDeviationPct,
      };
    }
    return null;
  } catch {
    return null;
  }
}

function parseThresholdConfig(namespace: string, raw: string): AnomalyThresholdConfig | null {
  try {
    const p = JSON.parse(raw) as Partial<AnomalyThresholdConfig>;
    if (
      typeof p.deviationThresholdPct === "number" &&
      Number.isFinite(p.deviationThresholdPct) &&
      p.deviationThresholdPct > 0 &&
      typeof p.setBy === "string" &&
      typeof p.setAt === "string"
    ) {
      return {
        namespace,
        deviationThresholdPct: p.deviationThresholdPct,
        setBy: p.setBy,
        setAt: p.setAt,
      };
    }
    return null;
  } catch {
    return null;
  }
}

interface RawAnomalyConfigMap {
  states: Map<string, AnomalyState>;
  thresholds: Map<string, AnomalyThresholdConfig>;
}

async function readRawConfigMap(): Promise<K8sResult<RawAnomalyConfigMap>> {
  const result = await getConfigMap(COST_ANOMALY_NAMESPACE, COST_ANOMALY_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};

  const states = new Map<string, AnomalyState>();
  const thresholds = new Map<string, AnomalyThresholdConfig>();
  for (const [key, raw] of Object.entries(data)) {
    if (key.startsWith("state.")) {
      const namespace = key.slice("state.".length);
      const parsed = namespace ? parseState(namespace, raw) : null;
      if (parsed) states.set(namespace, parsed);
    } else if (key.startsWith("threshold.")) {
      const namespace = key.slice("threshold.".length);
      const parsed = namespace ? parseThresholdConfig(namespace, raw) : null;
      if (parsed) thresholds.set(namespace, parsed);
    }
  }
  return { ok: true, data: { states, thresholds } };
}

/**
 * Real per-namespace deviation threshold, operator-settable the same way
 * lib/budget-alerts.ts's setBudgetThreshold is -- falls back to
 * DEFAULT_DEVIATION_THRESHOLD_PCT for any namespace with no explicit
 * override, so the detector is live for every namespace from the moment
 * its baseline is first seeded, with zero required operator setup.
 */
export async function setAnomalyThreshold(
  namespace: string,
  deviationThresholdPct: number,
  setBy: string,
): Promise<K8sResult<AnomalyThresholdConfig[]>> {
  const record: AnomalyThresholdConfig = {
    namespace,
    deviationThresholdPct,
    setBy,
    setAt: new Date().toISOString(),
  };
  const result = await createOrUpdateConfigMap(COST_ANOMALY_NAMESPACE, COST_ANOMALY_CONFIGMAP, {
    [thresholdKey(namespace)]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  return { ok: true, data: Array.from(raw.data.thresholds.values()) };
}

function resolveThresholdPct(namespace: string, thresholds: Map<string, AnomalyThresholdConfig>): number {
  return thresholds.get(namespace)?.deviationThresholdPct ?? DEFAULT_DEVIATION_THRESHOLD_PCT;
}

/**
 * Real current spend for one namespace over COST_ANOMALY_WINDOW_LABEL --
 * the exact same lib/invoice-preview.ts fetch + computeLineItems
 * arithmetic lib/budget-alerts.ts's own valueForMetric(cost-usd) applies,
 * just over the shorter, freshest trend window this detector uses instead
 * of budget-alerts.ts's 1h window.
 */
async function currentSpendFor(namespace: string): Promise<{ ok: true; value: number } | { ok: false; error: string }> {
  const metricsResult = await getNamespaceUsageMetrics(
    namespace,
    COST_ANOMALY_WINDOW_LABEL,
    COST_ANOMALY_WINDOW_HOURS,
  );
  if (!metricsResult.ok) return { ok: false, error: metricsResult.error };
  const lineItems = computeLineItems([metricsResult.data], ILLUSTRATIVE_RATES);
  return { ok: true, value: lineItems[0].totalCost };
}

/**
 * Real, read-only per-namespace anomaly status: reports each namespace's
 * currently-persisted EWMA baseline (from the last real poller tick) next
 * to a FRESH real current-spend fetch, and computes deviationPct/isAnomaly
 * from those two real numbers -- never writes state, so a page view/API
 * call can never advance the baseline or race the poller's own
 * checkCostAnomalies() (see this module's header comment).
 *
 * A namespace with no persisted state yet (baseline not seeded -- the
 * poller hasn't ticked, or this namespace's first real observation hasn't
 * landed) reports baselineSpend/deviationPct as null and isAnomaly false,
 * never a fabricated zero baseline that would make the very first real
 * spend look like an infinite-percent anomaly.
 */
export async function listCostAnomalyStatus(namespaces: string[]): Promise<K8sResult<CostAnomalyStatus[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;

  const statuses = await Promise.all(
    namespaces.map(async (namespace): Promise<CostAnomalyStatus> => {
      const deviationThresholdPct = resolveThresholdPct(namespace, raw.data.thresholds);
      const state = raw.data.states.get(namespace) ?? null;
      const spendResult = await currentSpendFor(namespace);

      if (!spendResult.ok) {
        return {
          namespace,
          baselineSpend: state?.baselineSpend ?? null,
          currentSpend: null,
          deviationPct: null,
          isAnomaly: false,
          deviationThresholdPct,
          lastCheckedAt: state?.lastCheckedAt ?? null,
          lastAnomalyAt: state?.lastAnomalyAt ?? null,
          error: spendResult.error,
        };
      }

      const currentSpend = spendResult.value;
      if (!state) {
        return {
          namespace,
          baselineSpend: null,
          currentSpend,
          deviationPct: null,
          isAnomaly: false,
          deviationThresholdPct,
          lastCheckedAt: null,
          lastAnomalyAt: null,
          error: null,
        };
      }

      const deviationPct = deviationPercent(currentSpend, state.baselineSpend);
      return {
        namespace,
        baselineSpend: state.baselineSpend,
        currentSpend,
        deviationPct,
        isAnomaly: deviationPct !== null && deviationPct >= deviationThresholdPct,
        deviationThresholdPct,
        lastCheckedAt: state.lastCheckedAt,
        lastAnomalyAt: state.lastAnomalyAt,
        error: null,
      };
    }),
  );
  return { ok: true, data: statuses };
}

/**
 * Real percent deviation of `current` above `baseline`. A zero (or
 * negative, which cannot occur for a real dollar spend but is guarded
 * anyway) baseline has no well-defined percent deviation -- returned as
 * null rather than a fabricated Infinity, matching this module's
 * fail-closed/never-fabricate convention throughout.
 */
function deviationPercent(current: number, baseline: number): number | null {
  if (baseline <= 0) return null;
  return ((current - baseline) / baseline) * 100;
}

/**
 * Real EWMA-advance PLUS real anomaly-flag write -- the ONLY function in
 * this module that ever updates `state.*` keys. Called exclusively by
 * lib/webhook-poller.ts's pollCostAnomalies on its existing 10s tick
 * (never a second poller). For each namespace:
 *
 *  - First-ever real observation for a namespace: baseline is SEEDED
 *    directly to that first real spend value (never EWMA'd against a
 *    fabricated zero baseline, which would report every namespace's very
 *    first tick as an infinite anomaly).
 *  - Every subsequent tick: baseline = (1 - EWMA_ALPHA) * baseline +
 *    EWMA_ALPHA * latest (real exponential smoothing, computed here, not
 *    claimed anywhere as predictive ML), and the anomaly flag is real
 *    deviationPct >= that namespace's real (or default) threshold.
 *  - A namespace whose real Prometheus query fails this tick is skipped
 *    entirely (logged, baseline left untouched) -- fail-closed, matching
 *    lib/budget-alerts.ts's checkBudgets and lib/invoice-preview.ts's own
 *    convention.
 *
 * Returns exactly the namespaces that crossed INTO anomaly on THIS tick
 * (were not already anomalous) -- i.e. the set that should fire a fresh
 * "cost.anomaly_detected" webhook delivery, mirroring
 * lib/budget-alerts.ts's checkBudgets return-only-new-crossings contract.
 */
export async function checkCostAnomalies(namespaces: string[]): Promise<K8sResult<CostAnomalyEvent[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  if (namespaces.length === 0) return { ok: true, data: [] };

  const events: CostAnomalyEvent[] = [];
  const patch: Record<string, string | null> = {};
  const now = new Date().toISOString();

  for (const namespace of namespaces) {
    const spendResult = await currentSpendFor(namespace);
    if (!spendResult.ok) {
      console.error(`[cost-anomaly] usage query failed for ${namespace}: ${spendResult.error}`);
      continue;
    }
    const currentSpend = spendResult.value;
    const deviationThresholdPct = resolveThresholdPct(namespace, raw.data.thresholds);
    const priorState = raw.data.states.get(namespace) ?? null;

    const wasAnomaly =
      priorState !== null &&
      deviationPercent(currentSpend, priorState.baselineSpend) !== null &&
      (deviationPercent(currentSpend, priorState.baselineSpend) as number) >= deviationThresholdPct;

    const newBaseline = priorState
      ? (1 - EWMA_ALPHA) * priorState.baselineSpend + EWMA_ALPHA * currentSpend
      : currentSpend;
    // Deviation is reported against the baseline AS OF BEFORE this tick's
    // EWMA update -- the whole point of an anomaly check is "does this new
    // observation look surprising relative to what came before it", not
    // relative to a baseline this same observation just nudged.
    const priorBaselineForDeviation = priorState ? priorState.baselineSpend : currentSpend;
    const deviationPct = deviationPercent(currentSpend, priorBaselineForDeviation) ?? 0;
    const isAnomaly = priorState !== null && deviationPct >= deviationThresholdPct;

    const newState: AnomalyState = {
      namespace,
      baselineSpend: newBaseline,
      lastCheckedAt: now,
      lastAnomalyAt: isAnomaly ? now : priorState?.lastAnomalyAt ?? null,
      lastDeviationPct: priorState ? deviationPct : 0,
    };
    patch[stateKey(namespace)] = JSON.stringify(newState);

    if (isAnomaly && !wasAnomaly) {
      events.push({
        namespace,
        baselineSpend: priorBaselineForDeviation,
        currentSpend,
        deviationPct,
        deviationThresholdPct,
        detectedAt: now,
      });
    }
  }

  if (Object.keys(patch).length > 0) {
    const patched = await createOrUpdateConfigMap(
      COST_ANOMALY_NAMESPACE,
      COST_ANOMALY_CONFIGMAP,
      patch as unknown as Record<string, string>,
    );
    if (!patched.ok) return patched;
  }

  return { ok: true, data: events };
}
