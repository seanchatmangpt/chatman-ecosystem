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
import { listNamespaceEgressMetrics, type NamespaceEgressMetrics } from "./network-usage";

/** Explicitly illustrative dollar rates -- not a real contracted price. */
export const ILLUSTRATIVE_RATES = {
  cpuPerCoreHour: 0.02,
  memoryPerGiBHour: 0.01,
  // Egress rate: illustrative only, chosen in the ballpark of a real
  // hyperscaler's per-GB Data Transfer Out charge to make the line item
  // legible, not a real contracted price. See lib/network-usage.ts's
  // header comment for the "shape claim, not scale claim" disclosure the
  // underlying byte count carries (real cross-namespace bytes on one
  // physical host, standing in for real inter-region/internet egress).
  egressPerGb: 0.09,
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
  type: "compute";
  namespace: string;
  cpuCoreHours: number;
  memoryGiBHours: number;
  cpuCost: number;
  memoryCost: number;
  totalCost: number;
}

/**
 * Real per-namespace network-egress line item (docs/SCOPE-AND-LIMITATIONS.md
 * "shape claim, not scale claim" convention -- see lib/network-usage.ts's
 * header comment for the full disclosure). `egressGb` is real metered
 * cross-namespace `istio_tcp_sent_bytes_total` traffic, converted from
 * bytes (1024**3 divisor, same binary-GiB-as-"GB" convention
 * memoryGiBHours already uses in this module) and multiplied by the
 * illustrative `egressPerGb` rate to produce `egressCost`.
 */
export interface NetworkEgressLineItem {
  type: "network_egress";
  namespace: string;
  egressBytes: number;
  egressGb: number;
  egressCost: number;
  totalCost: number;
}

/**
 * Real per-namespace Committed-Use Capacity Reservation input to
 * `computeLineItems`/`computeReservedCapacityDiscountLineItems` below
 * (lib/capacity-reservations.ts's own CapacityReservation, reduced to
 * exactly the numbers this module's arithmetic needs and converted to
 * the SAME core-hour/GiB-hour unit `NamespaceUsageMetrics` measures
 * usage in -- `committedCpuCores * windowHours`,
 * `committedMemoryGi * windowHours` -- so a reservation's committed
 * amount is directly comparable to real metered usage over the same
 * window, never a raw core/GiB count compared against an hours figure).
 */
export interface ReservedCapacityInput {
  committedCpuCoreHours: number;
  committedMemoryGiBHours: number;
  discountPct: number;
}

/**
 * Real "Reserved capacity discount" line item (Committed-Use Capacity
 * Reservations): the dollar amount a namespace's committed reservation
 * actually saved versus the standard rate over this window, shown as its
 * own informational line alongside the (already-discounted)
 * `InvoiceLineItem` for the same namespace -- the same "show the
 * discount as its own line, not folded silently into the total" shape
 * AWS Cost Explorer's own RI/Savings Plans "Amortized cost" breakdown
 * uses. `totalCost` is always <= 0 (a real savings, shown as a real
 * credit against the bill), never a positive charge.
 */
export interface ReservedCapacityDiscountLineItem {
  type: "reserved_capacity_discount";
  namespace: string;
  discountPct: number;
  cpuCoreHoursDiscounted: number;
  memoryGiBHoursDiscounted: number;
  totalCost: number;
}

export type AnyInvoiceLineItem = InvoiceLineItem | NetworkEgressLineItem | ReservedCapacityDiscountLineItem;

export interface InvoicePreview {
  windowLabel: string;
  windowHours: number;
  rates: RateTable;
  lineItems: InvoiceLineItem[];
  networkLineItems: NetworkEgressLineItem[];
  reservationLineItems: ReservedCapacityDiscountLineItem[];
  totalCost: number;
  networkTotalCost: number;
  reservationDiscountTotalCost: number;
  errors: Array<{ namespace: string; error: string }>;
  networkErrors: Array<{ namespace: string; error: string }>;
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
  reservations: Record<string, ReservedCapacityInput> = {},
): InvoiceLineItem[] {
  return metrics.map((m) => {
    const reservation = reservations[m.namespace];
    if (!reservation) {
      const cpuCost = m.cpuCoreHours * rates.cpuPerCoreHour;
      const memoryCost = m.memoryGiBHours * rates.memoryPerGiBHour;
      return {
        type: "compute",
        namespace: m.namespace,
        cpuCoreHours: m.cpuCoreHours,
        memoryGiBHours: m.memoryGiBHours,
        cpuCost,
        memoryCost,
        totalCost: cpuCost + memoryCost,
      };
    }

    // Real Committed-Use Capacity Reservation pricing: usage up to the
    // committed amount is billed at the discounted rate; usage above it
    // is billed at the standard rate -- the exact same "already covered
    // by your plan below the line, standard rate above it" shape
    // lib/overage-billing.ts's computeOverageAmount already established
    // for the tier-baseline case, applied here against a committed
    // reservation amount instead of a tier's default entitlement.
    const cpuWithinCommit = Math.min(m.cpuCoreHours, reservation.committedCpuCoreHours);
    const cpuAboveCommit = Math.max(0, m.cpuCoreHours - reservation.committedCpuCoreHours);
    const memoryWithinCommit = Math.min(m.memoryGiBHours, reservation.committedMemoryGiBHours);
    const memoryAboveCommit = Math.max(0, m.memoryGiBHours - reservation.committedMemoryGiBHours);
    const discountMultiplier = 1 - reservation.discountPct / 100;

    const cpuCost =
      cpuWithinCommit * rates.cpuPerCoreHour * discountMultiplier + cpuAboveCommit * rates.cpuPerCoreHour;
    const memoryCost =
      memoryWithinCommit * rates.memoryPerGiBHour * discountMultiplier +
      memoryAboveCommit * rates.memoryPerGiBHour;

    return {
      type: "compute",
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
 * Real "Reserved capacity discount" line items -- one real, informational
 * credit per namespace whose committed reservation actually reduced its
 * `computeLineItems` cost versus the standard (undiscounted) rate over
 * this same window. A namespace with a reservation but zero usage within
 * the committed amount (e.g. a brand-new commitment with no usage yet)
 * produces no line item -- there is no real savings to report, never a
 * fabricated $0.00 row.
 */
export function computeReservedCapacityDiscountLineItems(
  metrics: NamespaceUsageMetrics[],
  rates: RateTable = ILLUSTRATIVE_RATES,
  reservations: Record<string, ReservedCapacityInput> = {},
): ReservedCapacityDiscountLineItem[] {
  const items: ReservedCapacityDiscountLineItem[] = [];
  for (const m of metrics) {
    const reservation = reservations[m.namespace];
    if (!reservation) continue;

    const cpuWithinCommit = Math.min(m.cpuCoreHours, reservation.committedCpuCoreHours);
    const memoryWithinCommit = Math.min(m.memoryGiBHours, reservation.committedMemoryGiBHours);
    const discountAmount =
      cpuWithinCommit * rates.cpuPerCoreHour * (reservation.discountPct / 100) +
      memoryWithinCommit * rates.memoryPerGiBHour * (reservation.discountPct / 100);

    if (discountAmount <= 0) continue;

    items.push({
      type: "reserved_capacity_discount",
      namespace: m.namespace,
      discountPct: reservation.discountPct,
      cpuCoreHoursDiscounted: cpuWithinCommit,
      memoryGiBHoursDiscounted: memoryWithinCommit,
      totalCost: -discountAmount,
    });
  }
  return items;
}

/**
 * Same pure-arithmetic shape as computeLineItems, for the new
 * `network_egress` line item type: real per-namespace metered egress
 * bytes x the illustrative `egressPerGb` rate -> real per-namespace
 * egress line items. Takes no network dependency itself, so it is
 * trivially callable with hand-constructed `NamespaceEgressMetrics` to
 * check the math in isolation from Prometheus reachability, same as
 * computeLineItems.
 */
export function computeEgressLineItems(
  metrics: NamespaceEgressMetrics[],
  rates: RateTable = ILLUSTRATIVE_RATES,
): NetworkEgressLineItem[] {
  return metrics.map((m) => {
    const egressGb = m.egressBytes / 1024 ** 3;
    const egressCost = egressGb * rates.egressPerGb;
    return {
      type: "network_egress",
      namespace: m.namespace,
      egressBytes: m.egressBytes,
      egressGb,
      egressCost,
      totalCost: egressCost,
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
  const [results, egress, reservations] = await Promise.all([
    Promise.all(
      namespaces.map((namespace) => getNamespaceUsageMetrics(namespace, windowLabel, windowHours)),
    ),
    listNamespaceEgressMetrics(namespaces, windowLabel, windowHours),
    reservedCapacityInputsByNamespace(windowHours),
  ]);

  const metrics: NamespaceUsageMetrics[] = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  for (const r of results) {
    if (r.ok) metrics.push(r.data);
    else errors.push({ namespace: r.namespace, error: r.error });
  }

  const lineItems = computeLineItems(metrics, rates, reservations);
  const totalCost = lineItems.reduce((sum, li) => sum + li.totalCost, 0);

  const networkLineItems = computeEgressLineItems(egress.metrics, rates);
  const networkTotalCost = networkLineItems.reduce((sum, li) => sum + li.totalCost, 0);

  const reservationLineItems = computeReservedCapacityDiscountLineItems(metrics, rates, reservations);
  const reservationDiscountTotalCost = reservationLineItems.reduce((sum, li) => sum + li.totalCost, 0);

  return {
    windowLabel,
    windowHours,
    rates,
    lineItems,
    networkLineItems,
    reservationLineItems,
    totalCost,
    networkTotalCost,
    reservationDiscountTotalCost,
    errors,
    networkErrors: egress.errors,
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Real per-namespace `ReservedCapacityInput` map, built from every
 * currently-stored Committed-Use Capacity Reservation
 * (lib/capacity-reservations.ts's listReservations) converted from
 * `committedCpuCores`/`committedMemoryGi` into this window's own
 * core-hour/GiB-hour unit (`committed * windowHours`) -- the real
 * conversion this module's own header comment on `ReservedCapacityInput`
 * documents. A reservations-list failure (ConfigMap unreachable) fails
 * OPEN on this optional pricing input only -- an invoice preview still
 * renders standard-rate line items rather than a hard 502, the same
 * "this is pricing visibility, never a payment obligation" posture this
 * module's own header comment already establishes for Prometheus
 * failures (surfaced per-namespace in `errors`, never fabricated).
 * Reservations for a namespace outside `namespaces` are simply never
 * looked up here (the map is namespace-keyed, read via
 * `reservations[m.namespace]` in computeLineItems), so this never
 * over-applies a discount to a namespace this preview wasn't asked
 * about.
 */
async function reservedCapacityInputsByNamespace(
  windowHours: number,
): Promise<Record<string, ReservedCapacityInput>> {
  const { listReservations } = await import("@/lib/capacity-reservations");
  const result = await listReservations();
  if (!result.ok) return {};

  const now = Date.now();
  const map: Record<string, ReservedCapacityInput> = {};
  for (const reservation of result.data) {
    if (Date.parse(reservation.endDate) <= now) continue; // expired -- no discount applies
    map[reservation.namespace] = {
      committedCpuCoreHours: reservation.committedCpuCores * windowHours,
      committedMemoryGiBHours: reservation.committedMemoryGi * windowHours,
      discountPct: reservation.discountPct,
    };
  }
  return map;
}
