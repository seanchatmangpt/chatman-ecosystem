/**
 * Reserved-capacity / idle-waste rightsizing recommendations (AWS Trusted
 * Advisor "low utilization EC2 instances" / GCP Recommender
 * "VM rightsizing" equivalent, scoped to a namespace instead of an
 * instance). Distinct from lib/cost-anomaly.ts (which flags a SPIKE
 * relative to a namespace's own recent baseline) and from the spend
 * history chart (which shows how much was SPENT, not how much of what was
 * *reserved* went unused): this module diffs what a namespace's live Pods
 * ask the scheduler to reserve (`sum(container.resources.requests)`,
 * real k8s.ts::getNamespacePodRequests) against what those Pods actually
 * consumed on average over the trailing window (the SAME real Prometheus
 * `avg_over_time`/`increase()` queries lib/invoice-preview.ts already
 * issues for its cost figures, via lib/invoice-preview.ts::
 * getNamespaceUsageMetrics), and -- where the gap is large and sustained
 * -- estimates a dollar figure for the idle reservation using the same
 * ILLUSTRATIVE_RATES table invoice-preview.ts uses for its cost figures.
 *
 * Computed live on every GET, never persisted -- same "no new storage,
 * no new ConfigMap, no new k8s RBAC verb" discipline
 * app/api/orgs/[id]/usage-forecast/route.ts's own header comment
 * documents for its capability: this is a read-only analytical VIEW over
 * data every other cost/usage module in this tree already fetches
 * (Pod specs, PodMetrics indirectly via Prometheus, ResourceQuota), not a
 * new subsystem with its own state.
 */
import { getNamespacePodRequests } from "./k8s";
import { getNamespaceUsageMetrics } from "./invoice-preview";
import { ILLUSTRATIVE_RATES, type RateTable } from "./invoice-preview";

/** A namespace is flagged only when it is idle by more than this fraction
 * of its own reservation, sustained across the whole trailing window --
 * a namespace that merely dips below 100% utilization for a moment (every
 * namespace, always) is not a recommendation; one that reserves 4 cores
 * and averages under 2.4 cores used for a full week is. */
export const IDLE_THRESHOLD_FRACTION = 0.4;

export type RightsizingResource = "cpu" | "memory";

export interface RightsizingRecommendation {
  namespace: string;
  resource: RightsizingResource;
  /** Real current reservation -- sum of live Pods' `resources.requests`,
   * in the resource's natural unit (millicores for cpu, MiB for memory). */
  requestedAmount: number;
  /** Real trailing-window average actual consumption, same unit. */
  actualUsedAvg: number;
  /** `requestedAmount - actualUsedAvg`, floored at 0 (a namespace using
   * MORE than it requests -- e.g. burstable limits above request -- is
   * never reported as "negative waste"). */
  wastedAmount: number;
  /** `wastedAmount` as a fraction of `requestedAmount`, in [0, 1]. */
  idleFraction: number;
  /** Illustrative dollar estimate of `wastedAmount` held for a full
   * 730-hour month, via ILLUSTRATIVE_RATES -- same illustrative-not-
   * contracted disclosure as lib/invoice-preview.ts's own figures. */
  estimatedMonthlySavingsUsd: number;
}

export interface NamespaceRightsizingResult {
  namespace: string;
  windowLabel: string;
  windowHours: number;
  recommendations: RightsizingRecommendation[];
  /** Real reservation + real trailing usage this namespace's
   * recommendations (if any) were computed from -- included even when
   * `recommendations` is empty so a caller can see "checked, and this
   * namespace is well-utilized" vs. "never checked". */
  requested: { cpuMillicores: number; memoryMiB: number };
  actualAvg: { cpuMillicores: number; memoryMiB: number };
}

export type RightsizingResult =
  | { ok: true; data: NamespaceRightsizingResult }
  | { ok: false; namespace: string; error: string };

const HOURS_PER_MONTH = 730;

/**
 * Pure arithmetic core: given one namespace's real current reservation and
 * real trailing-window average usage (already fetched), computes the
 * idle-waste recommendation for one resource, or `null` when the idle
 * fraction doesn't clear `IDLE_THRESHOLD_FRACTION` (or there is nothing
 * reserved to be idle in). Takes no network dependency so the threshold
 * math is checkable in isolation from k8s/Prometheus reachability.
 */
export function computeResourceRecommendation(
  namespace: string,
  resource: RightsizingResource,
  requestedAmount: number,
  actualUsedAvg: number,
  rates: RateTable = ILLUSTRATIVE_RATES,
): RightsizingRecommendation | null {
  if (requestedAmount <= 0) return null;
  const wastedAmount = Math.max(0, requestedAmount - actualUsedAvg);
  const idleFraction = wastedAmount / requestedAmount;
  if (idleFraction <= IDLE_THRESHOLD_FRACTION) return null;

  const estimatedMonthlySavingsUsd =
    resource === "cpu"
      ? (wastedAmount / 1000) * rates.cpuPerCoreHour * HOURS_PER_MONTH
      : (wastedAmount / 1024) * rates.memoryPerGiBHour * HOURS_PER_MONTH;

  return {
    namespace,
    resource,
    requestedAmount,
    actualUsedAvg,
    wastedAmount,
    idleFraction,
    estimatedMonthlySavingsUsd,
  };
}

/**
 * Real end-to-end recommendation for one namespace: fetches the real live
 * Pod-request sum (k8s.ts::getNamespacePodRequests) and the real
 * trailing-`windowLabel` average usage (invoice-preview.ts::
 * getNamespaceUsageMetrics -- the identical Prometheus queries the cost
 * preview already issues) in parallel, converts usage into the same
 * millicore/MiB units the request sum is already in (average CPU
 * core-hours over the window / window-hours = average cores; average
 * GiB-hours over the window / window-hours = average GiB, both real
 * time-weighted averages, not just an endpoint sample), then evaluates
 * both resources against `IDLE_THRESHOLD_FRACTION`. A namespace whose k8s
 * or Prometheus call fails is reported as `ok: false`, never silently
 * skipped or zeroed -- same fail-closed convention as
 * invoice-preview.ts::getInvoicePreview.
 */
export async function getNamespaceRightsizing(
  namespace: string,
  windowLabel: string,
  windowHours: number,
  rates: RateTable = ILLUSTRATIVE_RATES,
): Promise<RightsizingResult> {
  const [requestsResult, usageResult] = await Promise.all([
    getNamespacePodRequests(namespace),
    getNamespaceUsageMetrics(namespace, windowLabel, windowHours),
  ]);

  if (!requestsResult.ok) {
    return { ok: false, namespace, error: `pod requests: ${requestsResult.error}` };
  }
  if (!usageResult.ok) {
    return { ok: false, namespace, error: usageResult.error };
  }

  const requested = {
    cpuMillicores: requestsResult.data.cpuRequestMillicores,
    memoryMiB: requestsResult.data.memoryRequestMiB,
  };
  const actualAvg = {
    // core-hours over windowHours -> average cores -> millicores
    cpuMillicores: (usageResult.data.cpuCoreHours / windowHours) * 1000,
    // GiB-hours over windowHours -> average GiB -> MiB
    memoryMiB: (usageResult.data.memoryGiBHours / windowHours) * 1024,
  };

  const recommendations: RightsizingRecommendation[] = [];
  const cpuRec = computeResourceRecommendation(
    namespace,
    "cpu",
    requested.cpuMillicores,
    actualAvg.cpuMillicores,
    rates,
  );
  if (cpuRec) recommendations.push(cpuRec);
  const memRec = computeResourceRecommendation(
    namespace,
    "memory",
    requested.memoryMiB,
    actualAvg.memoryMiB,
    rates,
  );
  if (memRec) recommendations.push(memRec);

  return {
    ok: true,
    data: { namespace, windowLabel, windowHours, recommendations, requested, actualAvg },
  };
}

export interface RightsizingDigest {
  windowLabel: string;
  windowHours: number;
  rates: RateTable;
  results: NamespaceRightsizingResult[];
  errors: Array<{ namespace: string; error: string }>;
  totalEstimatedMonthlySavingsUsd: number;
  generatedAt: string;
}

/**
 * Org-scoped digest across one or more namespaces (mirrors
 * invoice-preview.ts::getInvoicePreview's own multi-namespace fan-out
 * convention: `Promise.all`, per-namespace `ok`/error partition, a real
 * summed total). Today's callers pass a single-namespace org's own
 * namespace, but the digest is namespace-plural so a future
 * multi-namespace org resolves the same way invoice-preview.ts's own
 * multi-namespace callers already do.
 */
export async function getRightsizingDigest(
  namespaces: string[],
  windowLabel: string,
  windowHours: number,
  rates: RateTable = ILLUSTRATIVE_RATES,
): Promise<RightsizingDigest> {
  const outcomes = await Promise.all(
    namespaces.map((namespace) => getNamespaceRightsizing(namespace, windowLabel, windowHours, rates)),
  );

  const results: NamespaceRightsizingResult[] = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  for (const outcome of outcomes) {
    if (outcome.ok) results.push(outcome.data);
    else errors.push({ namespace: outcome.namespace, error: outcome.error });
  }

  const totalEstimatedMonthlySavingsUsd = results.reduce(
    (sum, r) =>
      sum + r.recommendations.reduce((s, rec) => s + rec.estimatedMonthlySavingsUsd, 0),
    0,
  );

  return {
    windowLabel,
    windowHours,
    rates,
    results,
    errors,
    totalEstimatedMonthlySavingsUsd,
    generatedAt: new Date().toISOString(),
  };
}
