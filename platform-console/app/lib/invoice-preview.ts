/**
 * Cost-preview calculation (AWS Cost Explorer "forecasted bill" / GCP
 * Billing cost-breakdown equivalent) computed over REAL metered Prometheus
 * data. This module is calculation and visibility only -- it never talks
 * to a payment processor, never collects card data, and creates no real
 * financial obligation anywhere. The rate table below (ILLUSTRATIVE_RATES)
 * is explicitly labeled illustrative, not a real contracted price; every
 * other number this module produces is real arithmetic over real metered
 * data, same fail-closed convention as lib/prometheus.ts and lib/k8s.ts:
 * a namespace whose Prometheus queries fail is reported as an error entry,
 * never silently zeroed or fabricated into the total.
 */
import { queryPrometheus } from "./prometheus";

/** Explicitly illustrative dollar rates -- not a real contracted price. */
export const ILLUSTRATIVE_RATES = {
  cpuPerCoreHour: 0.02,
  memoryPerGiBHour: 0.01,
} as const;

export type RateTable = typeof ILLUSTRATIVE_RATES;

export interface NamespaceUsageMetrics {
  namespace: string;
  /** Real accumulated CPU-core-hours consumed in the window. */
  cpuCoreHours: number;
  /** Real accumulated memory-GiB-hours (time-weighted average x window duration). */
  memoryGiBHours: number;
}

export type UsageMetricsResult =
  | { ok: true; data: NamespaceUsageMetrics }
  | { ok: false; namespace: string; error: string };

// container!="" and container!="POD" exclude the per-pod cgroup-aggregate
// series cAdvisor also exports under the same namespace (no `container`
// label) and the paused sandbox container, so a namespace's real
// containers are counted exactly once each, never double-counted.
const CONTAINER_FILTER = 'container!="",container!="POD"';

function firstScalar(result: Awaited<ReturnType<typeof queryPrometheus>>): number | null {
  if (!result.ok) return null;
  const raw = result.data.data?.result?.[0]?.value?.[1];
  if (raw === undefined) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Real accumulated CPU-core-hours and memory-GiB-hours for one namespace
 * over `windowLabel` (a PromQL duration literal, e.g. "1h", "24h"), read
 * live from this cluster's real Prometheus.
 *
 * CPU uses `increase()` over the real cumulative
 * `container_cpu_usage_seconds_total` counter -- the correct primitive for
 * a monotonic counter that can reset on container restart (a raw
 * `sum_over_time` of a counter would silently double-count across a
 * restart; `increase()` does not). The result is real CPU-seconds actually
 * consumed by every real container in the namespace over the window,
 * converted to CPU-core-hours by /3600.
 *
 * Memory uses `avg_over_time` (as a subquery, sampled at the cluster's
 * real 15s scrape interval) of the real `container_memory_working_set_bytes`
 * gauge, giving the real time-weighted average working set held over the
 * window; multiplying by the window's own duration in hours yields real
 * GiB-hours -- the same "capacity held over time" quantity a cloud
 * provider's memory-GB-hour billing dimension measures. No namespace with
 * zero real samples in the window is fabricated a nonzero value: an empty
 * Prometheus result vector is treated as a real, honest zero (a namespace
 * genuinely idle for the whole window), while an unreachable/erroring
 * Prometheus call is reported as `ok: false`, never silently zeroed.
 */
export async function getNamespaceUsageMetrics(
  namespace: string,
  windowLabel: string,
  windowHours: number,
): Promise<UsageMetricsResult> {
  const cpuQuery = `sum(increase(container_cpu_usage_seconds_total{namespace="${namespace}",${CONTAINER_FILTER}}[${windowLabel}]))`;
  const memQuery = `avg_over_time((sum(container_memory_working_set_bytes{namespace="${namespace}",${CONTAINER_FILTER}}))[${windowLabel}:15s])`;

  const [cpuResult, memResult] = await Promise.all([
    queryPrometheus(cpuQuery),
    queryPrometheus(memQuery),
  ]);

  if (!cpuResult.ok) return { ok: false, namespace, error: `cpu query: ${cpuResult.error}` };
  if (!memResult.ok) return { ok: false, namespace, error: `memory query: ${memResult.error}` };

  const cpuCoreSeconds = firstScalar(cpuResult) ?? 0;
  const avgMemoryBytes = firstScalar(memResult) ?? 0;

  const cpuCoreHours = cpuCoreSeconds / 3600;
  const memoryGiBHours = (avgMemoryBytes / 1024 ** 3) * windowHours;

  return { ok: true, data: { namespace, cpuCoreHours, memoryGiBHours } };
}

export interface InvoiceLineItem {
  namespace: string;
  cpuCoreHours: number;
  memoryGiBHours: number;
  cpuCost: number;
  memoryCost: number;
  totalCost: number;
}

export interface InvoicePreview {
  windowLabel: string;
  windowHours: number;
  rates: RateTable;
  lineItems: InvoiceLineItem[];
  totalCost: number;
  errors: Array<{ namespace: string; error: string }>;
  generatedAt: string;
}

/**
 * Pure arithmetic: real per-namespace metered usage x the illustrative
 * rate table -> real per-namespace line items and a real total. Takes no
 * network dependency, so it is trivially callable with hand-constructed
 * `NamespaceUsageMetrics` to check the math in isolation from Prometheus
 * reachability.
 */
export function computeLineItems(
  metrics: NamespaceUsageMetrics[],
  rates: RateTable = ILLUSTRATIVE_RATES,
): InvoiceLineItem[] {
  return metrics.map((m) => {
    const cpuCost = m.cpuCoreHours * rates.cpuPerCoreHour;
    const memoryCost = m.memoryGiBHours * rates.memoryPerGiBHour;
    return {
      namespace: m.namespace,
      cpuCoreHours: m.cpuCoreHours,
      memoryGiBHours: m.memoryGiBHours,
      cpuCost,
      memoryCost,
      totalCost: cpuCost + memoryCost,
    };
  });
}

/**
 * Real end-to-end preview for a fixed namespace roster: fetches real
 * accumulated usage per namespace from the live Prometheus (in parallel,
 * same `Promise.all` fan-out convention as app/usage/page.tsx), then
 * applies computeLineItems. A namespace whose Prometheus queries fail is
 * excluded from the total and surfaced in `errors` -- never zeroed
 * silently, matching the rest of this app's fail-closed convention.
 */
export async function getInvoicePreview(
  namespaces: string[],
  windowLabel: string,
  windowHours: number,
  rates: RateTable = ILLUSTRATIVE_RATES,
): Promise<InvoicePreview> {
  const results = await Promise.all(
    namespaces.map((namespace) => getNamespaceUsageMetrics(namespace, windowLabel, windowHours)),
  );

  const metrics: NamespaceUsageMetrics[] = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  for (const r of results) {
    if (r.ok) metrics.push(r.data);
    else errors.push({ namespace: r.namespace, error: r.error });
  }

  const lineItems = computeLineItems(metrics, rates);
  const totalCost = lineItems.reduce((sum, li) => sum + li.totalCost, 0);

  return {
    windowLabel,
    windowHours,
    rates,
    lineItems,
    totalCost,
    errors,
    generatedAt: new Date().toISOString(),
  };
}
