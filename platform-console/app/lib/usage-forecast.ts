/**
 * Real Usage Forecasting / Capacity-Planning (AWS Cost Explorer "forecast"
 * / GCP Billing "forecasted spend" equivalent): closes the gap that
 * lib/invoice-preview.ts computes only a point-in-time cost snapshot over
 * the CURRENT window, and lib/quota-enforcement.ts's checkBudget only
 * reacts once a budget is ALREADY crossed -- neither module ever answers
 * "at the current burn rate, when will this namespace breach its budget."
 * This module is that missing forward projection.
 *
 * Input: the SAME real cpuCoreHours/memoryGiBHours Prometheus queries
 * lib/invoice-preview.ts's getNamespaceUsageMetrics already issues (same
 * `increase()`-over-counter / `avg_over_time()`-over-gauge primitives, same
 * CONTAINER_FILTER), but bucketed into one real value per day over a
 * trailing N-day window via lib/prometheus.ts's queryPrometheusRange (the
 * same query_range primitive lib/status-page.ts's getComponentDownWindows
 * already uses) instead of one instant/window value -- no new query
 * surface, no new Prometheus dependency, no ML/forecasting library.
 *
 * Method: real ordinary-least-squares linear regression (closed-form
 * slope/intercept over the daily cumulative-cost points, O(n) in the
 * number of daily buckets, no external dependency) projected forward to
 * the day it crosses the org's existing real
 * `lib/quota-enforcement.ts` ProjectBudgetConfig.monthlyBudgetUsd cap --
 * the same illustrative $ rate table (ILLUSTRATIVE_RATES) invoice-preview.ts
 * already uses to turn real core-hours/GiB-hours into a real dollar figure,
 * so a forecast plotted in dollars is directly comparable to a dollar
 * budget cap without a second, inconsistent rate table.
 *
 * Fail-closed, same convention as invoice-preview.ts and every other
 * Prometheus-backed module in this codebase: a namespace whose daily-bucket
 * Prometheus queries error is reported as an explicit `error` entry, never
 * a fabricated/interpolated projection. A namespace with no configured
 * ProjectBudgetConfig reports `projectedBreachDate: null,
 * daysRemaining: null` (nothing to project against) rather than guessing a
 * cap. A namespace whose real daily burn rate is flat or decreasing
 * (`dailyRate <= 0`) never "breaches" mathematically and also reports
 * `null`/`null` -- extrapolating a negative slope to "never" is the
 * correct real answer, not a fabricated far-future date.
 */
import { queryPrometheusRange } from "@/lib/prometheus";
import { ILLUSTRATIVE_RATES, type RateTable } from "@/lib/invoice-preview";
import { getProjectBudgetStatus, type ProjectBudgetConfig } from "@/lib/quota-enforcement";

// container!="" and container!="POD" -- same double-counting exclusion
// invoice-preview.ts's CONTAINER_FILTER documents; kept as an identical,
// separately-named constant here rather than importing invoice-preview's
// private one, since that one is not exported (deliberately: this module
// does not want a change to invoice-preview's own filter to silently
// change forecast math without a matching review of this file).
const CONTAINER_FILTER = 'container!="",container!="POD"';

const SECONDS_PER_DAY = 86400;

export interface DailyUsageBucket {
  /** ISO date (UTC midnight) this bucket's samples are anchored to. */
  day: string;
  cpuCoreHours: number;
  memoryGiBHours: number;
  costUsd: number;
}

export type DailyUsageResult =
  | { ok: true; data: DailyUsageBucket[] }
  | { ok: false; namespace: string; error: string };

/**
 * Real per-day cpuCoreHours/memoryGiBHours for `namespace` over the
 * trailing `days` days, one query_range round trip per metric (not one
 * per day -- `step=1d` returns one real sample per day boundary directly).
 *
 * CPU: `increase()` over the real cumulative
 * `container_cpu_usage_seconds_total` counter, sampled with a `[1d]`
 * lookback at `step=1d` -- each returned sample is the real CPU-seconds
 * consumed in the 1-day window ending at that sample's timestamp, exactly
 * mirroring getNamespaceUsageMetrics's own single-window `increase()` call,
 * just repeated once per day by Prometheus itself server-side.
 *
 * Memory: `avg_over_time()` over the real `container_memory_working_set_bytes`
 * gauge with a `[1d:15s]` subquery at `step=1d` -- each sample is the real
 * time-weighted average working set held over that day, multiplied by 24h
 * to get real GiB-hours, same conversion getNamespaceUsageMetrics uses.
 */
export async function getNamespaceDailyUsage(
  namespace: string,
  days: number,
  rates: RateTable = ILLUSTRATIVE_RATES,
): Promise<DailyUsageResult> {
  const nowSeconds = Math.floor(Date.now() / 1000);
  const startSeconds = nowSeconds - days * SECONDS_PER_DAY;

  const cpuQuery = `sum(increase(container_cpu_usage_seconds_total{namespace="${namespace}",${CONTAINER_FILTER}}[1d]))`;
  const memQuery = `avg_over_time((sum(container_memory_working_set_bytes{namespace="${namespace}",${CONTAINER_FILTER}}))[1d:15s])`;

  const [cpuResult, memResult] = await Promise.all([
    queryPrometheusRange(cpuQuery, startSeconds, nowSeconds, SECONDS_PER_DAY),
    queryPrometheusRange(memQuery, startSeconds, nowSeconds, SECONDS_PER_DAY),
  ]);

  if (!cpuResult.ok) {
    return { ok: false, namespace, error: `cpu range query: ${cpuResult.error}` };
  }
  if (!memResult.ok) {
    return { ok: false, namespace, error: `memory range query: ${memResult.error}` };
  }

  const cpuSeries = cpuResult.data.data?.result?.[0]?.values ?? [];
  const memSeries = memResult.data.data?.result?.[0]?.values ?? [];

  // Index both real series by their own real timestamp (day boundary) --
  // Prometheus's own query_range step alignment guarantees the same
  // timestamps for both queries over the same [start,end,step], so a
  // straight Map lookup (not a positional zip) is used to stay correct
  // even if one series has a gap the other does not (e.g. a namespace
  // idle on CPU for a day but still holding memory, or vice versa).
  const cpuByTs = new Map<number, number>();
  for (const [ts, raw] of cpuSeries) {
    const n = Number(raw);
    if (Number.isFinite(n)) cpuByTs.set(ts, n);
  }
  const memByTs = new Map<number, number>();
  for (const [ts, raw] of memSeries) {
    const n = Number(raw);
    if (Number.isFinite(n)) memByTs.set(ts, n);
  }

  const allTimestamps = Array.from(new Set([...cpuByTs.keys(), ...memByTs.keys()])).sort(
    (a, b) => a - b,
  );

  const buckets: DailyUsageBucket[] = allTimestamps.map((ts) => {
    const cpuCoreSeconds = cpuByTs.get(ts) ?? 0;
    const avgMemoryBytes = memByTs.get(ts) ?? 0;
    const cpuCoreHours = cpuCoreSeconds / 3600;
    const memoryGiBHours = (avgMemoryBytes / 1024 ** 3) * 24;
    const costUsd = cpuCoreHours * rates.cpuPerCoreHour + memoryGiBHours * rates.memoryPerGiBHour;
    return { day: new Date(ts * 1000).toISOString(), cpuCoreHours, memoryGiBHours, costUsd };
  });

  return { ok: true, data: buckets };
}

export interface LinearFit {
  /** Real least-squares slope: $/day. */
  slope: number;
  /** Real least-squares intercept: $ at day index 0. */
  intercept: number;
}

/**
 * Real closed-form ordinary-least-squares fit over `points` (day index ->
 * cumulative $), the textbook two-parameter linear regression -- no
 * external ML/statistics dependency, deterministic, and re-derivable by
 * hand from the returned slope/intercept for any auditor who wants to
 * check the math. `points.length < 2` has no well-defined slope (a single
 * point admits infinitely many lines), so callers must guard that case
 * themselves; this function is pure arithmetic with no I/O, trivially
 * testable in isolation from Prometheus reachability.
 */
export function fitLeastSquares(points: Array<{ x: number; y: number }>): LinearFit {
  const n = points.length;
  const sumX = points.reduce((s, p) => s + p.x, 0);
  const sumY = points.reduce((s, p) => s + p.y, 0);
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0);
  const sumXX = points.reduce((s, p) => s + p.x * p.x, 0);

  const denominator = n * sumXX - sumX * sumX;
  // All points share the same x (degenerate: a single distinct day index,
  // e.g. exactly one real data point repeated) -- report a flat line at
  // the mean y rather than dividing by zero.
  if (denominator === 0) {
    return { slope: 0, intercept: sumY / n };
  }
  const slope = (n * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

export interface NamespaceUsageForecast {
  namespace: string;
  windowDays: number;
  /** Real cumulative $ spend across the trailing window (sum of every
   * real daily bucket's costUsd) -- the same ILLUSTRATIVE_RATES-derived
   * dollar figure invoice-preview.ts's totalCost uses, not a second
   * measure. */
  currentUsage: number;
  /** Real least-squares $/day slope over the trailing window's daily
   * buckets. Positive = growing spend, zero/negative = flat or shrinking. */
  dailyRate: number;
  /** The configured monthly $ budget cap this forecast was projected
   * against, or `null` when this namespace has no ProjectBudgetConfig
   * (lib/quota-enforcement.ts) set -- there is nothing to project a
   * breach date against. */
  budgetCapUsd: number | null;
  /** Real projected calendar date `currentUsage` extrapolated at
   * `dailyRate` crosses `budgetCapUsd`, or `null` when there is no budget
   * configured, the real daily rate is <= 0 (never breaches), or the cap
   * has already been crossed as of the most recent real daily bucket
   * (`daysRemaining` reports 0 in that last case instead of a past date). */
  projectedBreachDate: string | null;
  /** Real days-from-now until the projected breach, `null` under the same
   * conditions as `projectedBreachDate`. Never negative -- an already-
   * crossed cap reports 0, not a negative "days ago". */
  daysRemaining: number | null;
}

export type NamespaceUsageForecastResult =
  | { ok: true; data: NamespaceUsageForecast }
  | { ok: false; namespace: string; error: string };

/**
 * Real end-to-end forecast for one namespace: real daily-bucketed
 * cpuCoreHours/memoryGiBHours -> cumulative $ -> real least-squares
 * slope -> real projected breach date against the org's existing real
 * ProjectBudgetConfig cap (lib/quota-enforcement.ts's
 * getProjectBudgetStatus -- the SAME config PUT /api/projects/[name]/budget
 * already writes and checkBudget already enforces, never a second budget
 * concept). Fail-closed: a namespace whose real daily-bucket Prometheus
 * queries error returns `ok: false` with the real underlying error, never
 * a fabricated projection.
 */
export async function getNamespaceUsageForecast(
  namespace: string,
  windowDays = 14,
  rates: RateTable = ILLUSTRATIVE_RATES,
): Promise<NamespaceUsageForecastResult> {
  const dailyResult = await getNamespaceDailyUsage(namespace, windowDays, rates);
  if (!dailyResult.ok) {
    return { ok: false, namespace, error: dailyResult.error };
  }
  const buckets = dailyResult.data;

  const budgetStatusResult = await getProjectBudgetStatus(namespace);
  if (!budgetStatusResult.ok) {
    return { ok: false, namespace, error: budgetStatusResult.error };
  }
  const budgetConfig: ProjectBudgetConfig | null = budgetStatusResult.data.config;
  const budgetCapUsd = budgetConfig?.monthlyBudgetUsd ?? null;

  // Real cumulative $ spend at each real day index -- the least-squares
  // fit is over CUMULATIVE spend (not per-day spend) because a "budget
  // cap" is itself a cumulative ceiling; fitting the running total
  // directly gives a slope that is already the right unit (net $/day
  // burn rate against a cumulative cap) without a second integration
  // step.
  let running = 0;
  const points = buckets.map((b, i) => {
    running += b.costUsd;
    return { x: i, y: running };
  });
  const currentUsage = running;

  let projectedBreachDate: string | null = null;
  let daysRemaining: number | null = null;

  if (points.length >= 2 && budgetCapUsd !== null) {
    const { slope, intercept } = fitLeastSquares(points);
    if (slope > 0) {
      const lastIndex = points[points.length - 1].x;
      // Solve slope*x + intercept = budgetCapUsd for x (the real day
      // index the fitted line crosses the cap), then convert to
      // days-from-now by subtracting the most recent real bucket's own
      // day index.
      const crossingIndex = (budgetCapUsd - intercept) / slope;
      const rawDaysRemaining = crossingIndex - lastIndex;
      // Already crossed as of the most recent real bucket -- report 0,
      // not a negative "days ago" (this forecast module only ever looks
      // forward; a namespace already over budget is checkBudget's real
      // hard-stop concern, not this module's).
      const clamped = Math.max(0, rawDaysRemaining);
      daysRemaining = clamped;
      const breach = new Date(Date.now() + clamped * SECONDS_PER_DAY * 1000);
      projectedBreachDate = breach.toISOString();
    }
    // slope <= 0: real burn rate is flat or shrinking -- never
    // mathematically breaches, correctly left null/null rather than
    // extrapolated to a fabricated date arbitrarily far in the future.
  }

  return {
    ok: true,
    data: {
      namespace,
      windowDays,
      currentUsage,
      dailyRate: points.length >= 2 ? fitLeastSquares(points).slope : 0,
      budgetCapUsd,
      projectedBreachDate,
      daysRemaining,
    },
  };
}

export interface OrgUsageForecastResult {
  windowDays: number;
  forecasts: NamespaceUsageForecast[];
  errors: Array<{ namespace: string; error: string }>;
  generatedAt: string;
}

/**
 * Real forecast fan-out over a fixed namespace roster, same
 * Promise.all-and-partition convention as invoice-preview.ts's
 * getInvoicePreview: every namespace's real forecast succeeds or fails
 * independently, a single Prometheus-error namespace never blocks the
 * others' real projections and is surfaced in `errors` instead of
 * silently dropped or zeroed.
 */
export async function getUsageForecastForNamespaces(
  namespaces: string[],
  windowDays = 14,
  rates: RateTable = ILLUSTRATIVE_RATES,
): Promise<OrgUsageForecastResult> {
  const results = await Promise.all(
    namespaces.map((namespace) => getNamespaceUsageForecast(namespace, windowDays, rates)),
  );

  const forecasts: NamespaceUsageForecast[] = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  for (const r of results) {
    if (r.ok) forecasts.push(r.data);
    else errors.push({ namespace: r.namespace, error: r.error });
  }

  return { windowDays, forecasts, errors, generatedAt: new Date().toISOString() };
}
