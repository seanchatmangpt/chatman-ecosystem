/**
 * Real usage-based overage billing (AWS/GCP "burst past your reservation,
 * we bill you for the delta" model): closes the gap that
 * lib/stripe-billing.ts only ever creates a flat-price Subscription (one
 * fixed `priceId`, no metered dimension) while lib/invoice-preview.ts's
 * getNamespaceUsageMetrics already computes real Prometheus-derived
 * CPU-core-hours/memory-GiB-hours -- that real number never reached
 * Stripe. A namespace that bursts past its lib/tiers.ts
 * TIER_RESOURCE_QUOTAS ceiling today only gets throttled (ResourceQuota,
 * lib/quota-enforcement.ts / lib/plan-state.ts's suspend path); there was
 * no "let them burst and bill them for it" path. This module is that
 * path, real Stripe invoice-item calls against whatever key
 * STRIPE_SECRET_KEY points at (test-mode honesty note identical to
 * lib/stripe-billing.ts's own header: an `sk_test_` key makes this
 * genuinely real Stripe test-mode wiring with zero financial obligation).
 *
 * Baseline: each ProjectTier's TIER_RESOURCE_QUOTAS `requestsCpu`/
 * `requestsMemory` (the sustained allocation a tier's flat price already
 * covers, as opposed to `limitsCpu`/`limitsMemory`, the hard burst
 * ceiling) times the measurement window's own duration in hours gives a
 * real core-hour / GiB-hour ENTITLEMENT for that window -- the same unit
 * getNamespaceUsageMetrics already measures real consumption in, so the
 * two are directly comparable. Usage above that entitlement is the real
 * overage; usage below it costs the tenant nothing extra, exactly the
 * "already covered by your plan" semantics a burstable-instance overage
 * bill has.
 *
 * Measurement window: a fixed real 24h trailing window ending now, same
 * choice and the same reason lib/cost.ts's TREND_WINDOWS documents --
 * this cluster's Prometheus has only been scraping for a few hours in any
 * demo/dev deployment, so a real calendar-month billing period would
 * silently degrade to whatever short real history exists rather than the
 * requested span. `periodStart` in the stored record is this window's
 * real start time (`now - 24h`), not a fabricated calendar-month anchor.
 *
 * Storage: reuses lib/stripe-billing.ts's existing
 * `platform-console-stripe-subscriptions` ConfigMap (constraint: "no new
 * k8s resource kind") with one additional `overage.<namespace>` key per
 * tenant namespace, same get-then-create-or-patch primitive
 * (`getConfigMap`/`createOrUpdateConfigMap`) every ConfigMap-backed module
 * in this codebase already uses.
 *
 * Automatic vs. explicit billing: the webhook-poller tick
 * (recomputeAllOverageEstimates, called from lib/webhook-poller.ts) only
 * ever RECOMPUTES the real estimate and persists it -- it never itself
 * calls Stripe. Committing a real Stripe invoice item
 * (billeNamespaceOverage) is reached only from the owner-gated POST
 * /api/billing/overage route. This mirrors this codebase's own existing
 * split between automatic-and-reversible enforcement (ResourceQuota
 * patches, lib/plan-state.ts / lib/quota-enforcement.ts, safe to run
 * unattended every 10s) and explicit, human-triggered, hard-to-reverse
 * actions (lib/quota-enforcement.ts's resetQuotaEnforcement's own header:
 * "this is never automatic"; lib/stripe-billing.ts's Checkout Session
 * creation) -- creating a real Stripe invoice item is the latter kind of
 * action, not something that should fire unattended on a 10s poll tick.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  listProjects,
  type K8sResult,
} from "@/lib/k8s";
import {
  getNamespaceUsageMetrics,
  ILLUSTRATIVE_RATES,
  type NamespaceUsageMetrics,
  type RateTable,
} from "@/lib/invoice-preview";
import {
  DEFAULT_PROJECT_TIER,
  TIER_RESOURCE_QUOTAS,
  type ProjectTier,
} from "@/lib/tiers";
import {
  createOverageInvoiceItem,
  getStoredSubscription,
  hasStripeCredentials,
  STRIPE_NAMESPACE,
  STRIPE_SUBSCRIPTIONS_CONFIGMAP,
  type StoredSubscription,
} from "@/lib/stripe-billing";

// Same fixed platform-namespace roster every billing-adjacent route in
// this app already hardcodes (app/api/billing/route.ts,
// app/api/quota-enforcement/route.ts, lib/plan-state.ts) -- never an
// arbitrary client-supplied namespace.
export const OVERAGE_PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

// Fixed real trailing window, same reasoning as lib/cost.ts's
// TREND_WINDOWS -- see this module's header comment.
export const OVERAGE_WINDOW_LABEL = "24h";
export const OVERAGE_WINDOW_HOURS = 24;

function overageConfigMapKey(namespace: string): string {
  return `overage.${namespace}`;
}

export interface StoredOverage {
  namespace: string;
  /** Real ISO start time of the trailing measurement window this record's
   * numbers were computed over -- `now - OVERAGE_WINDOW_HOURS` at compute
   * time, not a fabricated calendar-period anchor. */
  periodStart: string;
  cpuCoreHoursOverage: number;
  memoryGiBHoursOverage: number;
  overageCostUsd: number;
  /** Set only once a real Stripe InvoiceItem has actually been created
   * for this exact `periodStart` -- the idempotency marker that makes a
   * re-run of the POST route within the same period a genuine no-op
   * instead of a duplicate charge. */
  lastInvoiceItemId: string | null;
  computedAt: string;
}

function parseStoredOverage(namespace: string, raw: string): StoredOverage | null {
  try {
    const p = JSON.parse(raw) as Partial<StoredOverage>;
    if (
      typeof p.periodStart === "string" &&
      typeof p.cpuCoreHoursOverage === "number" &&
      typeof p.memoryGiBHoursOverage === "number" &&
      typeof p.overageCostUsd === "number" &&
      typeof p.computedAt === "string"
    ) {
      return {
        namespace,
        periodStart: p.periodStart,
        cpuCoreHoursOverage: p.cpuCoreHoursOverage,
        memoryGiBHoursOverage: p.memoryGiBHoursOverage,
        overageCostUsd: p.overageCostUsd,
        lastInvoiceItemId: typeof p.lastInvoiceItemId === "string" ? p.lastInvoiceItemId : null,
        computedAt: p.computedAt,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Real GET of the one `overage.<namespace>` ConfigMap key -- `data: null`
 * (not an error) when no overage has ever been computed for this tenant
 * yet, same honest-absence convention lib/stripe-billing.ts's
 * getStoredSubscription establishes. */
export async function getStoredOverage(namespace: string): Promise<K8sResult<StoredOverage | null>> {
  const cm = await getConfigMap(STRIPE_NAMESPACE, STRIPE_SUBSCRIPTIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const raw = cm.data?.data?.[overageConfigMapKey(namespace)];
  if (!raw) return { ok: true, data: null };
  const parsed = parseStoredOverage(namespace, raw);
  if (!parsed) return { ok: false, error: `corrupt stored overage record for ${namespace}` };
  return { ok: true, data: parsed };
}

async function putStoredOverage(record: StoredOverage): Promise<K8sResult<StoredOverage>> {
  const result = await createOrUpdateConfigMap(STRIPE_NAMESPACE, STRIPE_SUBSCRIPTIONS_CONFIGMAP, {
    [overageConfigMapKey(record.namespace)]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: record };
}

// k8s CPU quantities are either a bare core count ("1", "1.5") or a
// millicore suffix ("500m", "1500m") -- the two forms TIER_RESOURCE_QUOTAS
// actually uses (see lib/tiers.ts). Real k8s "m" suffix parsing, not a
// general Quantity-format library.
function parseCpuCores(quantity: string): number {
  if (quantity.endsWith("m")) {
    return Number.parseFloat(quantity.slice(0, -1)) / 1000;
  }
  return Number.parseFloat(quantity);
}

// k8s memory quantities in this codebase's own tables are always "Mi" or
// "Gi" (binary mebibyte/gibibyte, see lib/tiers.ts TIER_RESOURCE_QUOTAS) --
// converted here to GiB, the same unit getNamespaceUsageMetrics reports
// memoryGiBHours in.
function parseMemoryGiB(quantity: string): number {
  if (quantity.endsWith("Gi")) return Number.parseFloat(quantity.slice(0, -2));
  if (quantity.endsWith("Mi")) return Number.parseFloat(quantity.slice(0, -2)) / 1024;
  return Number.parseFloat(quantity) / 1024 ** 3;
}

/** Real per-window core-hour / GiB-hour entitlement `tier`'s
 * TIER_RESOURCE_QUOTAS `requestsCpu`/`requestsMemory` (the sustained
 * allocation a tier's flat subscription price already covers) buys over
 * `windowHours` -- see this module's header comment for why `requests`,
 * not `limits`, is the baseline. */
export function quotaBaselineForTier(
  tier: ProjectTier,
  windowHours: number,
): { cpuCoreHours: number; memoryGiBHours: number } {
  const q = TIER_RESOURCE_QUOTAS[tier];
  return {
    cpuCoreHours: parseCpuCores(q.requestsCpu) * windowHours,
    memoryGiBHours: parseMemoryGiB(q.requestsMemory) * windowHours,
  };
}

/**
 * Real Project tier lookup by tenant NAMESPACE (not Project name -- a
 * Project's k8s object name and the namespace it provisions are usually
 * but not necessarily identical, see lib/k8s.ts's CreateProjectInput).
 * Reuses listProjects (which already resolves each Project's real
 * TIER_LABEL via toSupabaseProject, lib/k8s.ts) rather than a second k8s
 * read path. A namespace with no matching Project CR (e.g.
 * `platform-console` itself, which owns no Project object) falls back to
 * DEFAULT_PROJECT_TIER -- the same fail-open-to-the-lowest-tier default
 * toSupabaseProject itself uses for a Project predating TIER_LABEL.
 */
export async function tierForNamespace(namespace: string): Promise<K8sResult<ProjectTier>> {
  const result = await listProjects();
  if (!result.ok) return result;
  const project = result.data.find((p) => p.namespace === namespace);
  return { ok: true, data: project ? project.tier : DEFAULT_PROJECT_TIER };
}

export interface NamespaceOverageEstimate {
  namespace: string;
  tier: ProjectTier;
  windowLabel: string;
  windowHours: number;
  usage: NamespaceUsageMetrics;
  baselineCpuCoreHours: number;
  baselineMemoryGiBHours: number;
  cpuCoreHoursOverage: number;
  memoryGiBHoursOverage: number;
  overageCostUsd: number;
  stored: StoredOverage | null;
}

export type OverageEstimateResult =
  | { ok: true; data: NamespaceOverageEstimate }
  | { ok: false; namespace: string; error: string };

/**
 * Pure arithmetic over real inputs: real metered usage minus the real
 * per-tier entitlement, floored at 0 (usage below entitlement is never a
 * negative "credit" -- it costs nothing extra, not less than nothing) x
 * the same illustrative rate table lib/invoice-preview.ts's
 * computeLineItems already uses. computeLineItems itself is not reused
 * directly (it prices gross usage, not the delta above a baseline) but
 * the exact same `rates` shape and per-unit multiplication is applied
 * here, so a namespace with zero overage is priced identically to how
 * computeLineItems would price zero usage.
 */
export function computeOverageAmount(
  usage: NamespaceUsageMetrics,
  baselineCpuCoreHours: number,
  baselineMemoryGiBHours: number,
  rates: RateTable = ILLUSTRATIVE_RATES,
): { cpuCoreHoursOverage: number; memoryGiBHoursOverage: number; overageCostUsd: number } {
  const cpuCoreHoursOverage = Math.max(0, usage.cpuCoreHours - baselineCpuCoreHours);
  const memoryGiBHoursOverage = Math.max(0, usage.memoryGiBHours - baselineMemoryGiBHours);
  const overageCostUsd =
    cpuCoreHoursOverage * rates.cpuPerCoreHour + memoryGiBHoursOverage * rates.memoryPerGiBHour;
  return { cpuCoreHoursOverage, memoryGiBHoursOverage, overageCostUsd };
}

/**
 * Real end-to-end, read-only (no Stripe write, no ConfigMap write) current
 * overage estimate for one namespace: real Prometheus usage x real
 * TIER_RESOURCE_QUOTAS baseline for that namespace's real Project tier,
 * plus whatever `overage.<namespace>` record (if any) is already on file
 * -- e.g. to show the operator a previously-committed `lastInvoiceItemId`
 * alongside the freshly recomputed estimate.
 */
export async function estimateNamespaceOverage(namespace: string): Promise<OverageEstimateResult> {
  const [usageResult, tierResult, storedResult] = await Promise.all([
    getNamespaceUsageMetrics(namespace, OVERAGE_WINDOW_LABEL, OVERAGE_WINDOW_HOURS),
    tierForNamespace(namespace),
    getStoredOverage(namespace),
  ]);
  if (!usageResult.ok) return { ok: false, namespace, error: usageResult.error };
  if (!tierResult.ok) return { ok: false, namespace, error: tierResult.error };
  if (!storedResult.ok) return { ok: false, namespace, error: storedResult.error };

  const baseline = quotaBaselineForTier(tierResult.data, OVERAGE_WINDOW_HOURS);
  const overage = computeOverageAmount(usageResult.data, baseline.cpuCoreHours, baseline.memoryGiBHours);

  return {
    ok: true,
    data: {
      namespace,
      tier: tierResult.data,
      windowLabel: OVERAGE_WINDOW_LABEL,
      windowHours: OVERAGE_WINDOW_HOURS,
      usage: usageResult.data,
      baselineCpuCoreHours: baseline.cpuCoreHours,
      baselineMemoryGiBHours: baseline.memoryGiBHours,
      cpuCoreHoursOverage: overage.cpuCoreHoursOverage,
      memoryGiBHoursOverage: overage.memoryGiBHoursOverage,
      overageCostUsd: overage.overageCostUsd,
      stored: storedResult.data,
    },
  };
}

export async function estimateAllNamespaceOverages(
  namespaces: string[] = OVERAGE_PLATFORM_NAMESPACES,
): Promise<{ estimates: NamespaceOverageEstimate[]; errors: Array<{ namespace: string; error: string }> }> {
  const results = await Promise.all(namespaces.map((ns) => estimateNamespaceOverage(ns)));
  const estimates: NamespaceOverageEstimate[] = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  for (const r of results) {
    if (r.ok) estimates.push(r.data);
    else errors.push({ namespace: r.namespace, error: r.error });
  }
  return { estimates, errors };
}

function currentPeriodStartIso(): string {
  return new Date(Date.now() - OVERAGE_WINDOW_HOURS * 60 * 60 * 1000).toISOString();
}

/**
 * Called from lib/webhook-poller.ts's existing tick. Real recompute +
 * persist of every namespace's current overage estimate -- NEVER calls
 * Stripe (see this module's header comment). A namespace whose existing
 * stored record already carries a `lastInvoiceItemId` for a period this
 * close to the current one (within one window's width, i.e. genuinely
 * the same trailing period, not just a coincidentally-equal cost) keeps
 * that id rather than clearing it -- the estimate refreshes, the
 * already-committed invoice item's provenance does not disappear.
 */
export async function recomputeAllOverageEstimates(
  namespaces: string[] = OVERAGE_PLATFORM_NAMESPACES,
): Promise<K8sResult<NamespaceOverageEstimate[]>> {
  const { estimates, errors } = await estimateAllNamespaceOverages(namespaces);
  for (const e of errors) {
    console.error(`[overage-billing] estimate failed for ${e.namespace}: ${e.error}`);
  }
  if (estimates.length === 0) return { ok: true, data: [] };

  const now = new Date();
  const periodStart = currentPeriodStartIso();
  const windowMs = OVERAGE_WINDOW_HOURS * 60 * 60 * 1000;

  const patch: Record<string, string> = {};
  for (const e of estimates) {
    const priorSamePeriod =
      e.stored && Math.abs(new Date(e.stored.periodStart).getTime() - new Date(periodStart).getTime()) < windowMs
        ? e.stored.lastInvoiceItemId
        : null;
    const record: StoredOverage = {
      namespace: e.namespace,
      periodStart,
      cpuCoreHoursOverage: e.cpuCoreHoursOverage,
      memoryGiBHoursOverage: e.memoryGiBHoursOverage,
      overageCostUsd: e.overageCostUsd,
      lastInvoiceItemId: priorSamePeriod,
      computedAt: now.toISOString(),
    };
    patch[overageConfigMapKey(e.namespace)] = JSON.stringify(record);
  }

  const result = await createOrUpdateConfigMap(STRIPE_NAMESPACE, STRIPE_SUBSCRIPTIONS_CONFIGMAP, patch);
  if (!result.ok) return result;
  return { ok: true, data: estimates };
}

export type BillOverageResult =
  | { ok: true; data: { namespace: string; billed: boolean; record: StoredOverage; reason: string } }
  | { ok: false; error: string };

/**
 * Real commit: recomputes this one namespace's current overage estimate
 * fresh (never trusts a stale ConfigMap number for the actual charge
 * amount) and, if positive, creates a real Stripe InvoiceItem against the
 * tenant's real Stripe customer/subscription
 * (lib/stripe-billing.ts's createOverageInvoiceItem) -- then persists
 * `lastInvoiceItemId` so a second call within the SAME real trailing
 * window (`periodStart` unchanged) is a genuine no-op (`billed: false`),
 * never a duplicate charge. Called only from the owner-gated POST
 * /api/billing/overage route -- see this module's header comment for why
 * this is never reached from the automatic poller tick.
 */
export async function billNamespaceOverage(namespace: string): Promise<BillOverageResult> {
  if (!hasStripeCredentials()) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };

  const subResult = await getStoredSubscription(namespace);
  if (!subResult.ok) return { ok: false, error: subResult.error };
  const subscription: StoredSubscription | null = subResult.data;
  if (!subscription || !subscription.stripeSubscriptionId) {
    return { ok: false, error: `no active Stripe subscription on file for namespace '${namespace}'` };
  }

  const estimate = await estimateNamespaceOverage(namespace);
  if (!estimate.ok) return { ok: false, error: estimate.error };

  const periodStart = currentPeriodStartIso();
  const windowMs = OVERAGE_WINDOW_HOURS * 60 * 60 * 1000;
  const existing = estimate.data.stored;
  const alreadyBilledThisPeriod =
    existing?.lastInvoiceItemId &&
    Math.abs(new Date(existing.periodStart).getTime() - new Date(periodStart).getTime()) < windowMs;

  if (alreadyBilledThisPeriod) {
    return {
      ok: true,
      data: {
        namespace,
        billed: false,
        record: existing!,
        reason: `already billed for this period (invoice item ${existing!.lastInvoiceItemId})`,
      },
    };
  }

  if (estimate.data.overageCostUsd <= 0) {
    const record: StoredOverage = {
      namespace,
      periodStart,
      cpuCoreHoursOverage: estimate.data.cpuCoreHoursOverage,
      memoryGiBHoursOverage: estimate.data.memoryGiBHoursOverage,
      overageCostUsd: 0,
      lastInvoiceItemId: null,
      computedAt: new Date().toISOString(),
    };
    const stored = await putStoredOverage(record);
    if (!stored.ok) return { ok: false, error: stored.error };
    return { ok: true, data: { namespace, billed: false, record, reason: "no overage this period" } };
  }

  const description =
    `Overage: ${estimate.data.cpuCoreHoursOverage.toFixed(4)} CPU-core-hours + ` +
    `${estimate.data.memoryGiBHoursOverage.toFixed(4)} GiB-hours above the ${estimate.data.tier} ` +
    `tier's included quota, trailing ${estimate.data.windowLabel} window ending ${new Date().toISOString()}`;

  const invoiceItem = await createOverageInvoiceItem({
    customerId: subscription.stripeCustomerId,
    subscriptionId: subscription.stripeSubscriptionId,
    amountUsd: estimate.data.overageCostUsd,
    description,
    tenantNamespace: namespace,
  });
  if (!invoiceItem.ok) return { ok: false, error: invoiceItem.error };

  const record: StoredOverage = {
    namespace,
    periodStart,
    cpuCoreHoursOverage: estimate.data.cpuCoreHoursOverage,
    memoryGiBHoursOverage: estimate.data.memoryGiBHoursOverage,
    overageCostUsd: estimate.data.overageCostUsd,
    lastInvoiceItemId: invoiceItem.data.id,
    computedAt: new Date().toISOString(),
  };
  const stored = await putStoredOverage(record);
  if (!stored.ok) return { ok: false, error: stored.error };

  return {
    ok: true,
    data: { namespace, billed: true, record, reason: `created Stripe InvoiceItem ${invoiceItem.data.id}` },
  };
}
