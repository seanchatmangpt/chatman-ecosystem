/**
 * Anonymized Cross-Org Usage Benchmarking Marketplace (Flexera/CloudHealth
 * and Databricks-style peer cost benchmarking, paid pro/enterprise
 * add-on): every existing cost/usage view in this repo -- lib/cost.ts's
 * NamespaceCostRow dashboard, lib/cost-anomaly.ts, lib/invoice-preview.ts
 * -- is single-org: "what did WE spend". This module is the first
 * cross-org comparative view: "are we spending more per workload than
 * comparable orgs on this platform", computed live, at request time, from
 * the SAME real per-namespace cost/usage figures lib/cost.ts already
 * derives from lib/invoice-preview.ts's live Prometheus queries. No new
 * storage, no new metric, no synthetic data -- this is a pure aggregation
 * over numbers this platform already computes for every org's own
 * dashboard, reshaped into an anonymized peer-percentile distribution.
 *
 * Window honesty note: same trailing-window caveat lib/cost.ts's own
 * header comment already discloses for TREND_WINDOWS -- this cluster has
 * no persisted historical billing ledger, so there is no real 30
 * *calendar*-day bucket to query. This module uses the longest real
 * window lib/cost.ts already exposes (TREND_WINDOWS's last entry, "24h"
 * today) as the trailing bucket, rather than fabricate a 30-day figure
 * Prometheus cannot actually answer. If TREND_WINDOWS is ever extended to
 * a genuine 30d live window, this module picks that up automatically
 * (BENCHMARK_WINDOW is derived from TREND_WINDOWS, never a separately
 * hardcoded duration).
 *
 * Anonymization: the returned BenchmarkResult never carries another org's
 * name, id, or namespace -- only the numeric distribution (percentile
 * band values) and the caller's own value/rank within it. A cohort of
 * fewer than MIN_COHORT_SIZE orgs is refused with `insufficientData:
 * true` instead of a real percentile, because with e.g. 2-3 orgs in the
 * distribution a requester can trivially back out a specific peer's exact
 * number from p25/p50/p75/p90 alone (the same small-cohort
 * re-identification risk k-anonymity literature names) -- refusing to
 * answer is the closing move, not an afterthought.
 */
import { getOrgProjectTier, listOrgs, type Org } from "@/lib/orgs";
import { getNamespaceUsageMetrics } from "@/lib/invoice-preview";
import { computeLineItems, type InvoiceLineItem } from "@/lib/invoice-preview";
import { listPods } from "@/lib/k8s";
import { TREND_WINDOWS } from "@/lib/cost";
import { tierAtLeast, type ProjectTier } from "@/lib/tiers";

/** Same longest-real-window convention lib/cost.ts's getCostTrend already
 * iterates over -- the last (longest) entry in TREND_WINDOWS, not a
 * separately hardcoded duration, so this module never drifts from what
 * lib/cost.ts itself considers its longest live trailing bucket. */
export const BENCHMARK_WINDOW = TREND_WINDOWS[TREND_WINDOWS.length - 1];

/** Cohorts smaller than this refuse to return a real percentile --
 * closes the small-cohort re-identification gap named in this module's
 * header comment. */
export const MIN_COHORT_SIZE = 5;

export type BenchmarkMetric = "cost_per_pod_hour";

export interface BenchmarkBands {
  p25: number;
  p50: number;
  p75: number;
  p90: number;
}

export interface BenchmarkResult {
  metric: BenchmarkMetric;
  windowLabel: string;
  windowHours: number;
  yourValue: number;
  yourPercentileRank: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
  sampleSize: number;
  insufficientData: false;
  generatedAt: string;
}

export interface InsufficientBenchmarkResult {
  metric: BenchmarkMetric;
  insufficientData: true;
  sampleSize: number;
  minRequired: number;
  generatedAt: string;
}

export type BenchmarkOrError =
  | { ok: true; data: BenchmarkResult | InsufficientBenchmarkResult }
  | { ok: false; error: string };

/**
 * Real cost-per-pod-hour for one namespace at the benchmark window: the
 * SAME real InvoiceLineItem.totalCost lib/cost.ts's NamespaceCostRow
 * already joins, divided by a real live pod count (lib/k8s.ts's
 * listPods) times the window's hours. Pod count is a real
 * point-in-time-at-request snapshot (k8s has no time-weighted
 * pod-hour series exposed anywhere in this codebase, unlike
 * cpuCoreHours/memoryGiBHours which ARE time-weighted Prometheus
 * integrals) -- an honest current-fleet-size proxy for "pod-hours in the
 * window", not a fabricated time-weighted figure. Returns null when the
 * namespace has zero real pods (division by zero would produce a
 * meaningless Infinity, not a real cost-per-pod figure) or when either
 * real query fails.
 */
async function costPerPodHourFor(
  namespace: string,
): Promise<{ namespace: string; value: number } | null> {
  const [metricsResult, podsResult] = await Promise.all([
    getNamespaceUsageMetrics(namespace, BENCHMARK_WINDOW.label, BENCHMARK_WINDOW.hours),
    listPods(namespace),
  ]);
  if (!metricsResult.ok || !podsResult.ok) return null;
  const podCount = podsResult.data.length;
  if (podCount <= 0) return null;

  const lineItems: InvoiceLineItem[] = computeLineItems([metricsResult.data]);
  const lineItem = lineItems[0];
  if (!lineItem) return null;

  const podHours = podCount * BENCHMARK_WINDOW.hours;
  if (podHours <= 0) return null;

  return { namespace, value: lineItem.totalCost / podHours };
}

/** Sorted-array percentile-rank calculation: fraction of the cohort's
 * real values strictly below `value`, expressed 0-100 -- the standard
 * "what percentile are you in" definition (ties counted as at-or-below,
 * so a value equal to every other value in the cohort ranks at the 100th
 * percentile rather than understating it). */
export function percentileRank(sorted: number[], value: number): number {
  if (sorted.length === 0) return 0;
  let countAtOrBelow = 0;
  for (const v of sorted) {
    if (v <= value) countAtOrBelow += 1;
  }
  return Math.round((countAtOrBelow / sorted.length) * 100);
}

/** Real sorted-array percentile-value lookup (nearest-rank method) over
 * `sorted` (already ascending). */
function percentileValue(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[idx];
}

/**
 * Computes the requesting org's real peer-percentile standing for
 * `metric` among every other org on this platform, gated (by the caller,
 * via tierAtLeast) behind pro tier -- see
 * app/api/orgs/[id]/usage-benchmark/route.ts. Pulls every org's real
 * cost.ts-equivalent NamespaceCostRow figures live at request time (no
 * caching, no persisted distribution -- the trailing window this reuses
 * is already itself a rolling live aggregate, so there is nothing stale
 * to cache), strips every peer org's identity before returning, and
 * refuses to answer (insufficientData: true) when fewer than
 * MIN_COHORT_SIZE orgs have a real, non-null value for this metric.
 */
export async function getUsageBenchmark(orgId: string): Promise<BenchmarkOrError> {
  const orgsResult = await listOrgs();
  if (!orgsResult.ok) return { ok: false, error: orgsResult.error };

  const requestingOrg = orgsResult.data.find((o) => o.id === orgId);
  if (!requestingOrg) return { ok: false, error: "org not found" };

  const perOrg = await Promise.all(
    orgsResult.data.map(async (org: Org) => {
      const point = await costPerPodHourFor(org.namespace);
      return point ? { orgId: org.id, value: point.value } : null;
    }),
  );

  const real = perOrg.filter((p): p is { orgId: string; value: number } => p !== null);
  const mine = real.find((p) => p.orgId === orgId);

  const generatedAt = new Date().toISOString();

  if (real.length < MIN_COHORT_SIZE || !mine) {
    return {
      ok: true,
      data: {
        metric: "cost_per_pod_hour",
        insufficientData: true,
        sampleSize: real.length,
        minRequired: MIN_COHORT_SIZE,
        generatedAt,
      },
    };
  }

  const sortedValues = real.map((p) => p.value).sort((a, b) => a - b);

  return {
    ok: true,
    data: {
      metric: "cost_per_pod_hour",
      windowLabel: BENCHMARK_WINDOW.label,
      windowHours: BENCHMARK_WINDOW.hours,
      yourValue: mine.value,
      yourPercentileRank: percentileRank(sortedValues, mine.value),
      p25: percentileValue(sortedValues, 25),
      p50: percentileValue(sortedValues, 50),
      p75: percentileValue(sortedValues, 75),
      p90: percentileValue(sortedValues, 90),
      sampleSize: real.length,
      insufficientData: false,
      generatedAt,
    },
  };
}

/** Thin re-export so the route handler can gate on tier without importing
 * lib/tiers.ts's full surface directly -- matches the existing
 * `tierAtLeast`/`getOrgProjectTier` pairing every other tier-gated route
 * in this tree (e.g. app/api/orgs/[id]/region/route.ts) already uses. */
export async function orgMeetsBenchmarkTier(
  namespace: string,
  minimum: ProjectTier = "pro",
): Promise<{ ok: true; eligible: boolean; tier: ProjectTier } | { ok: false; error: string }> {
  const tierResult = await getOrgProjectTier(namespace);
  if (!tierResult.ok) return { ok: false, error: tierResult.error };
  return { ok: true, eligible: tierAtLeast(tierResult.data, minimum), tier: tierResult.data };
}
