/**
 * Real Quota Enforcement (AWS Service Quotas breach-action / GCP Org
 * Policy "deny + remediate" equivalent): closes the gap that this
 * console's cost math (lib/invoice-preview.ts, lib/cost.ts) and its
 * ResourceQuota-percentage figure (lib/k8s.ts's `getResourceUsage`) were
 * both real, live-measured numbers with NOTHING downstream of them that
 * actually acted -- a namespace could sit at 300% of its configured
 * enforcement threshold indefinitely and nothing but a human staring at
 * a dashboard would ever know or do anything about it. This module is
 * that missing action: an operator configures one enforcement threshold
 * per namespace (a percent-of-ResourceQuota ceiling, evaluated against
 * the SAME real `getResourceUsage` figure `/usage` already shows -- no
 * second measurement path), and the moment real usage genuinely crosses
 * it, this module takes one concrete, real, observable k8s action:
 * scales an operator-named "enforcement target" Deployment in that
 * namespace to 0 replicas (lib/k8s.ts's `patchDeploymentReplicas`) and
 * annotates the Namespace object itself (`patchNamespaceAnnotations`)
 * with a human-readable enforcement record.
 *
 * Storage: one real k8s ConfigMap (`platform-quota-enforcement`,
 * `platform-console` namespace), reusing the exact
 * get-then-create-or-patch primitive lib/k8s.ts's Feature Flags module
 * established and lib/budget-alerts.ts already reuses for its own
 * threshold+dedup ConfigMap -- no new k8s resource kind, no new
 * configmaps RBAC verb (the existing `platform-console-feature-flags`
 * Role in k8s/paas-rbac.yaml already grants get/list/create/update/patch
 * on `configmaps` in this namespace with no `resourceNames`
 * restriction).
 *
 * Two logically distinct key families share the one ConfigMap, same
 * naming convention as lib/budget-alerts.ts:
 *   `threshold.<namespace>` -> JSON QuotaEnforcementConfig (operator config)
 *   `enforced.<namespace>`  -> JSON {enforcedAt, cpuPercent, memoryPercent}
 *     (dedup marker + the real evidence of what usage looked like at the
 *     moment enforcement fired)
 *
 * checkQuotaEnforcement() (the ONLY function that ever writes an
 * `enforced.*` key or ever calls patchDeploymentReplicas/
 * patchNamespaceAnnotations) is called exclusively by
 * lib/webhook-poller.ts's existing 10s tick -- same
 * observe-and-mark-belongs-to-the-poller-only discipline
 * lib/budget-alerts.ts's own header comment documents and for the exact
 * same reason: if a page view could also trigger enforcement, an
 * operator opening the dashboard moments before the poller's own tick
 * would race it. Every other caller (the GET route, the page) only
 * observes via listQuotaEnforcementStatus, which never writes.
 *
 * Once fired, enforcement is NOT auto-reversed when usage drops back
 * under threshold -- unlike lib/budget-alerts.ts's alert dedup marker,
 * which intentionally clears so a later re-crossing fires a fresh
 * webhook. A suspended workload staying suspended until a human
 * deliberately restores it (resetQuotaEnforcement) is the whole point of
 * "suspension" as an enforcement action; silently un-suspending the
 * moment metrics-server reports one lower reading would make the action
 * meaningless.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  getResourceUsage,
  patchDeploymentReplicas,
  patchNamespaceAnnotations,
  type K8sResult,
  type NamespaceResourceUsage,
} from "@/lib/k8s";
import { listCostAnomalyStatus } from "@/lib/cost-anomaly";

export const QUOTA_ENFORCEMENT_NAMESPACE = "platform-console";
export const QUOTA_ENFORCEMENT_CONFIGMAP = "platform-quota-enforcement";

const ANNOTATION_ENFORCED = "platform-console.io/quota-enforced";
const ANNOTATION_ENFORCED_AT = "platform-console.io/quota-enforced-at";
const ANNOTATION_ENFORCED_REASON = "platform-console.io/quota-enforced-reason";

export interface QuotaEnforcementConfig {
  namespace: string;
  /** Percent of ResourceQuota (CPU or memory, whichever is higher) at or
   * above which enforcement fires -- compared against the SAME
   * `cpuPercentOfQuota`/`memoryPercentOfQuota` figures `getResourceUsage`
   * (lib/k8s.ts) already computes for `/usage`, never a second metric. */
  thresholdPercent: number;
  /** The Deployment this config's enforcement action scales to 0 when
   * threshold is crossed -- must already exist in `namespace` at check
   * time (checkQuotaEnforcement fails closed, logs, and skips otherwise;
   * see its own comment). */
  targetDeployment: string;
  setBy: string;
  setAt: string;
}

export interface QuotaEnforcementRecord {
  enforcedAt: string;
  cpuPercent: number | null;
  memoryPercent: number | null;
  targetDeployment: string;
}

export interface QuotaEnforcementStatus {
  namespace: string;
  config: QuotaEnforcementConfig | null;
  usage: NamespaceResourceUsage | null;
  usageError: string | null;
  /** max(cpuPercentOfQuota, memoryPercentOfQuota) -- `null` when usage or
   * quota data is unavailable. This is the exact figure compared against
   * `config.thresholdPercent`. */
  currentPercent: number | null;
  overThreshold: boolean;
  enforced: QuotaEnforcementRecord | null;
}

function thresholdKey(namespace: string): string {
  return `threshold.${namespace}`;
}
function enforcedKey(namespace: string): string {
  return `enforced.${namespace}`;
}
function budgetKey(namespace: string): string {
  return `budget.${namespace}`;
}

function parseConfig(namespace: string, raw: string): QuotaEnforcementConfig | null {
  try {
    const p = JSON.parse(raw) as Partial<QuotaEnforcementConfig>;
    if (
      typeof p.thresholdPercent === "number" &&
      Number.isFinite(p.thresholdPercent) &&
      p.thresholdPercent > 0 &&
      typeof p.targetDeployment === "string" &&
      p.targetDeployment.length > 0 &&
      typeof p.setBy === "string" &&
      typeof p.setAt === "string"
    ) {
      return {
        namespace,
        thresholdPercent: p.thresholdPercent,
        targetDeployment: p.targetDeployment,
        setBy: p.setBy,
        setAt: p.setAt,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Per-project (per-namespace, same key granularity as `threshold.*`
 * above) FinOps hard-cap config -- the real block-not-just-alert
 * counterpart to lib/cost-anomaly.ts's alert-only EWMA detector and
 * lib/overage-billing.ts's bill-for-overage-but-never-block path.
 * `monthlyBudgetUsd` is the operator-set ceiling; `hardStop` decides
 * whether crossing it actually blocks new resource creation (checkBudget
 * below) or is purely informational (visible on the status/UI, enforces
 * nothing) -- mirrors QuotaEnforcementConfig's own
 * configured-but-not-yet-crossed vs. actually-enforced distinction.
 */
export interface ProjectBudgetConfig {
  namespace: string;
  monthlyBudgetUsd: number;
  hardStop: boolean;
  setBy: string;
  setAt: string;
}

export interface ProjectBudgetStatus {
  namespace: string;
  config: ProjectBudgetConfig | null;
  /** Real current spend, read from the exact same real EWMA-detector
   * current-spend figure lib/cost-anomaly.ts's listCostAnomalyStatus
   * already computes for /cost-anomaly -- no second cost calculation.
   * `null` only when that underlying Prometheus query failed this call,
   * never a fabricated zero. */
  currentSpendUsd: number | null;
  spendError: string | null;
  /** true only when a config exists, hardStop is true, and
   * currentSpendUsd is a real (non-null) number >= monthlyBudgetUsd --
   * the exact predicate checkBudget below gates resource creation on. */
  overBudget: boolean;
}

function parseBudgetConfig(namespace: string, raw: string): ProjectBudgetConfig | null {
  try {
    const p = JSON.parse(raw) as Partial<ProjectBudgetConfig>;
    if (
      typeof p.monthlyBudgetUsd === "number" &&
      Number.isFinite(p.monthlyBudgetUsd) &&
      p.monthlyBudgetUsd > 0 &&
      typeof p.hardStop === "boolean" &&
      typeof p.setBy === "string" &&
      typeof p.setAt === "string"
    ) {
      return {
        namespace,
        monthlyBudgetUsd: p.monthlyBudgetUsd,
        hardStop: p.hardStop,
        setBy: p.setBy,
        setAt: p.setAt,
      };
    }
    return null;
  } catch {
    return null;
  }
}

function parseRecord(raw: string): QuotaEnforcementRecord | null {
  try {
    const p = JSON.parse(raw) as Partial<QuotaEnforcementRecord>;
    if (
      typeof p.enforcedAt === "string" &&
      (typeof p.cpuPercent === "number" || p.cpuPercent === null) &&
      (typeof p.memoryPercent === "number" || p.memoryPercent === null) &&
      typeof p.targetDeployment === "string"
    ) {
      return {
        enforcedAt: p.enforcedAt,
        cpuPercent: p.cpuPercent ?? null,
        memoryPercent: p.memoryPercent ?? null,
        targetDeployment: p.targetDeployment,
      };
    }
    return null;
  } catch {
    return null;
  }
}

interface RawEnforcementConfigMap {
  configs: QuotaEnforcementConfig[];
  /** Keyed by namespace. */
  enforced: Map<string, QuotaEnforcementRecord>;
  /** Keyed by namespace -- the `budget.<namespace>` key family. */
  budgets: Map<string, ProjectBudgetConfig>;
}

async function readRawConfigMap(): Promise<K8sResult<RawEnforcementConfigMap>> {
  const result = await getConfigMap(QUOTA_ENFORCEMENT_NAMESPACE, QUOTA_ENFORCEMENT_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};

  const configs: QuotaEnforcementConfig[] = [];
  const enforced = new Map<string, QuotaEnforcementRecord>();
  const budgets = new Map<string, ProjectBudgetConfig>();
  for (const [key, raw] of Object.entries(data)) {
    if (key.startsWith("threshold.")) {
      const namespace = key.slice("threshold.".length);
      const parsed = namespace ? parseConfig(namespace, raw) : null;
      if (parsed) configs.push(parsed);
    } else if (key.startsWith("enforced.")) {
      const namespace = key.slice("enforced.".length);
      const parsed = namespace ? parseRecord(raw) : null;
      if (parsed) enforced.set(namespace, parsed);
    } else if (key.startsWith("budget.")) {
      const namespace = key.slice("budget.".length);
      const parsed = namespace ? parseBudgetConfig(namespace, raw) : null;
      if (parsed) budgets.set(namespace, parsed);
    }
  }
  configs.sort((a, b) => a.namespace.localeCompare(b.namespace));
  return { ok: true, data: { configs, enforced, budgets } };
}

/** Real list of every configured enforcement threshold, sorted by namespace. */
export async function listQuotaEnforcementConfigs(): Promise<K8sResult<QuotaEnforcementConfig[]>> {
  const result = await readRawConfigMap();
  if (!result.ok) return result;
  return { ok: true, data: result.data.configs };
}

/**
 * Sets (creates or replaces) one namespace's enforcement config via a
 * real RFC 7386 merge patch -- same one-key-at-a-time convention as
 * lib/budget-alerts.ts's setBudgetThreshold. Does NOT clear a pre-
 * existing `enforced.*` record: reconfiguring the threshold or target
 * after enforcement has already fired must not silently erase the real
 * evidence of that action -- an operator who wants to lift enforcement
 * calls resetQuotaEnforcement explicitly instead.
 */
export async function setQuotaEnforcementConfig(
  namespace: string,
  thresholdPercent: number,
  targetDeployment: string,
  setBy: string,
): Promise<K8sResult<QuotaEnforcementConfig[]>> {
  const record: QuotaEnforcementConfig = {
    namespace,
    thresholdPercent,
    targetDeployment,
    setBy,
    setAt: new Date().toISOString(),
  };
  const patch: Record<string, string> = { [thresholdKey(namespace)]: JSON.stringify(record) };
  const result = await createOrUpdateConfigMap(QUOTA_ENFORCEMENT_NAMESPACE, QUOTA_ENFORCEMENT_CONFIGMAP, patch);
  if (!result.ok) return result;
  return listQuotaEnforcementConfigs();
}

/**
 * Deletes one namespace's enforcement config via a real RFC 7386 merge
 * patch (`null` value). Leaves any existing `enforced.*` record and the
 * scaled-down Deployment/namespace annotation untouched -- deleting the
 * config stops FUTURE checks from re-evaluating this namespace, it does
 * not itself restore a workload already suspended (use
 * resetQuotaEnforcement for that).
 */
export async function deleteQuotaEnforcementConfig(namespace: string): Promise<K8sResult<null>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  if (!raw.data.configs.some((c) => c.namespace === namespace)) {
    return { ok: true, data: null };
  }
  const patch: Record<string, string | null> = { [thresholdKey(namespace)]: null };
  const result = await createOrUpdateConfigMap(
    QUOTA_ENFORCEMENT_NAMESPACE,
    QUOTA_ENFORCEMENT_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/** max(cpuPercentOfQuota, memoryPercentOfQuota), ignoring whichever side
 * is `null` -- `null` only when BOTH are `null` (no quota, or quota sets
 * neither `limits.cpu` nor `limits.memory`). */
function currentPercentOf(usage: NamespaceResourceUsage): number | null {
  const values = [usage.cpuPercentOfQuota, usage.memoryPercentOfQuota].filter(
    (v): v is number => v !== null,
  );
  if (values.length === 0) return null;
  return Math.max(...values);
}

/**
 * Real current status for every configured namespace, READ-ONLY: fetches
 * live usage via the SAME lib/k8s.ts `getResourceUsage` `/usage` already
 * calls, and never writes an `enforced.*` marker or touches any
 * Deployment/Namespace. Safe to call from a page render or a GET route
 * as often as needed -- see this module's header comment for why that
 * separation from checkQuotaEnforcement is load-bearing.
 */
export async function listQuotaEnforcementStatus(): Promise<K8sResult<QuotaEnforcementStatus[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;

  const statuses = await Promise.all(
    raw.data.configs.map(async (config): Promise<QuotaEnforcementStatus> => {
      const usageResult = await getResourceUsage(config.namespace);
      const enforced = raw.data.enforced.get(config.namespace) ?? null;
      if (!usageResult.ok) {
        return {
          namespace: config.namespace,
          config,
          usage: null,
          usageError: usageResult.error,
          currentPercent: null,
          overThreshold: false,
          enforced,
        };
      }
      const currentPercent = currentPercentOf(usageResult.data);
      return {
        namespace: config.namespace,
        config,
        usage: usageResult.data,
        usageError: null,
        currentPercent,
        overThreshold: currentPercent !== null && currentPercent >= config.thresholdPercent,
        enforced,
      };
    }),
  );
  return { ok: true, data: statuses };
}

/**
 * Sets (creates or replaces) one namespace's monthly budget config via a
 * real RFC 7386 merge patch -- same one-key-at-a-time convention as
 * setQuotaEnforcementConfig above and lib/budget-alerts.ts's
 * setBudgetThreshold. Backs PUT /api/projects/[name]/budget.
 */
export async function setProjectBudget(
  namespace: string,
  monthlyBudgetUsd: number,
  hardStop: boolean,
  setBy: string,
): Promise<K8sResult<ProjectBudgetConfig>> {
  const record: ProjectBudgetConfig = {
    namespace,
    monthlyBudgetUsd,
    hardStop,
    setBy,
    setAt: new Date().toISOString(),
  };
  const result = await createOrUpdateConfigMap(QUOTA_ENFORCEMENT_NAMESPACE, QUOTA_ENFORCEMENT_CONFIGMAP, {
    [budgetKey(namespace)]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: record };
}

/**
 * Real, read-only per-namespace budget status: the configured ceiling
 * (if any) next to a FRESH real current-spend read via
 * lib/cost-anomaly.ts's listCostAnomalyStatus -- the exact same real
 * EWMA-detector current-spend figure /cost-anomaly already reports, never
 * a second cost calculation. Backs GET /api/projects/[name]/budget and
 * checkBudget below; never writes anything.
 */
export async function getProjectBudgetStatus(namespace: string): Promise<K8sResult<ProjectBudgetStatus>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  const config = raw.data.budgets.get(namespace) ?? null;

  const spendResult = await listCostAnomalyStatus([namespace]);
  if (!spendResult.ok) return spendResult;
  const spend = spendResult.data[0] ?? null;
  const currentSpendUsd = spend?.currentSpend ?? null;
  const spendError = spend?.error ?? null;

  const overBudget =
    config !== null &&
    config.hardStop &&
    currentSpendUsd !== null &&
    currentSpendUsd >= config.monthlyBudgetUsd;

  return {
    ok: true,
    data: { namespace, config, currentSpendUsd, spendError, overBudget },
  };
}

export interface BudgetCheckResult {
  allowed: boolean;
  reason: string | null;
}

/**
 * The real FinOps hard-stop enforcement hook: additive to, never a
 * replacement for, the ResourceQuota-percent ceiling rejection this
 * module's own resource-provisioning callers already apply -- mirrors
 * that exact "fail closed only when a config genuinely says so" shape.
 * Called from POST /api/projects (and any other resource-creation path
 * for this namespace) BEFORE the real k8s create call, never after.
 *
 * No budget configured for `namespace`, or a configured budget with
 * `hardStop: false` (alert-only, matching lib/cost-anomaly.ts's own
 * alert-without-block guarantee), or a real current-spend query failure
 * (fail-open on a measurement error -- a broken Prometheus query must
 * never itself become an outage for legitimate provisioning, same
 * fail-closed-on-action/fail-open-on-observation-failure split
 * checkQuotaEnforcement's own header comment documents) all return
 * `allowed: true`. Only `hardStop: true` AND a real, successfully
 * measured `currentSpendUsd >= monthlyBudgetUsd` returns `allowed: false`
 * with a human-readable `reason`.
 */
export async function checkBudget(namespace: string): Promise<K8sResult<BudgetCheckResult>> {
  const statusResult = await getProjectBudgetStatus(namespace);
  if (!statusResult.ok) return statusResult;
  const status = statusResult.data;

  if (!status.overBudget) {
    return { ok: true, data: { allowed: true, reason: null } };
  }

  const reason =
    `monthly budget exceeded for namespace '${namespace}': ` +
    `current spend $${status.currentSpendUsd!.toFixed(2)} >= ` +
    `budget $${status.config!.monthlyBudgetUsd.toFixed(2)} (hard stop enabled)`;
  return { ok: true, data: { allowed: false, reason } };
}

export interface QuotaEnforcementAction {
  namespace: string;
  targetDeployment: string;
  cpuPercent: number | null;
  memoryPercent: number | null;
  thresholdPercent: number;
  enforcedAt: string;
}

/**
 * Real breach-detection PLUS the real enforcement action -- the ONLY
 * function in this module that ever scales a Deployment, annotates a
 * Namespace, or writes an `enforced.*` marker. Called exclusively by
 * lib/webhook-poller.ts's existing 10s tick (never a second poller).
 *
 * For every configured namespace not already enforced, re-fetches live
 * usage (fail-closed: a namespace whose real query fails this tick is
 * logged and skipped, never treated as a breach) and, when
 * `currentPercent >= thresholdPercent`, takes the real action in order:
 *   1. patchDeploymentReplicas(namespace, targetDeployment, 0) -- the
 *      actual throttling/suspension act. If this write fails (e.g. the
 *      configured target Deployment does not exist), enforcement is
 *      aborted for this namespace THIS tick -- no annotation, no dedup
 *      marker -- so a config typo fails loudly (logged) and retries next
 *      tick, rather than silently marking "enforced" with nothing
 *      actually throttled.
 *   2. patchNamespaceAnnotations -- best-effort human-readable record on
 *      the Namespace object itself; its failure does not roll back step
 *      1 (the real suspension already happened) but is logged.
 *   3. The `enforced.<namespace>` ConfigMap marker, written last, only
 *      once the real k8s action from step 1 is confirmed to have
 *      succeeded.
 * Returns exactly the actions taken THIS tick.
 */
export async function checkQuotaEnforcement(): Promise<K8sResult<QuotaEnforcementAction[]>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  if (raw.data.configs.length === 0) return { ok: true, data: [] };

  const actions: QuotaEnforcementAction[] = [];
  const patch: Record<string, string> = {};
  const now = new Date().toISOString();

  for (const config of raw.data.configs) {
    if (raw.data.enforced.has(config.namespace)) continue;

    const usageResult = await getResourceUsage(config.namespace);
    if (!usageResult.ok) {
      console.error(`[quota-enforcement] usage query failed for ${config.namespace}: ${usageResult.error}`);
      continue;
    }
    const currentPercent = currentPercentOf(usageResult.data);
    if (currentPercent === null || currentPercent < config.thresholdPercent) continue;

    const scaleResult = await patchDeploymentReplicas(config.namespace, config.targetDeployment, 0);
    if (!scaleResult.ok) {
      console.error(
        `[quota-enforcement] enforcement scale-to-0 FAILED for ${config.namespace}/${config.targetDeployment}: ${scaleResult.error}`,
      );
      continue;
    }

    const reason =
      `quota breach: usage reached ${currentPercent.toFixed(1)}% of ResourceQuota ` +
      `(threshold ${config.thresholdPercent}%) -- ${config.targetDeployment} scaled to 0 at ${now}`;
    const annotationResult = await patchNamespaceAnnotations(config.namespace, {
      [ANNOTATION_ENFORCED]: "true",
      [ANNOTATION_ENFORCED_AT]: now,
      [ANNOTATION_ENFORCED_REASON]: reason,
    });
    if (!annotationResult.ok) {
      console.error(
        `[quota-enforcement] namespace annotation FAILED (real scale-to-0 already applied) for ${config.namespace}: ${annotationResult.error}`,
      );
    }

    const record: QuotaEnforcementRecord = {
      enforcedAt: now,
      cpuPercent: usageResult.data.cpuPercentOfQuota,
      memoryPercent: usageResult.data.memoryPercentOfQuota,
      targetDeployment: config.targetDeployment,
    };
    patch[enforcedKey(config.namespace)] = JSON.stringify(record);
    actions.push({
      namespace: config.namespace,
      targetDeployment: config.targetDeployment,
      cpuPercent: record.cpuPercent,
      memoryPercent: record.memoryPercent,
      thresholdPercent: config.thresholdPercent,
      enforcedAt: now,
    });
  }

  if (Object.keys(patch).length > 0) {
    const patched = await createOrUpdateConfigMap(QUOTA_ENFORCEMENT_NAMESPACE, QUOTA_ENFORCEMENT_CONFIGMAP, patch);
    if (!patched.ok) return patched;
  }

  return { ok: true, data: actions };
}

/**
 * Explicit operator reset: scales `targetDeployment` back to 1 replica,
 * clears the `enforced.*` marker, and clears the Namespace's
 * enforcement annotations -- the deliberate, human-triggered undo this
 * module's header comment says checkQuotaEnforcement itself never
 * performs automatically. A no-op (no k8s write beyond the marker clear)
 * when the namespace has no `enforced.*` record.
 */
export async function resetQuotaEnforcement(
  namespace: string,
): Promise<K8sResult<{ namespace: string; restoredReplicas: number } | null>> {
  const raw = await readRawConfigMap();
  if (!raw.ok) return raw;
  const record = raw.data.enforced.get(namespace);
  if (!record) return { ok: true, data: null };

  const scaleResult = await patchDeploymentReplicas(namespace, record.targetDeployment, 1);
  if (!scaleResult.ok) return scaleResult;

  const annotationResult = await patchNamespaceAnnotations(namespace, {
    [ANNOTATION_ENFORCED]: null,
    [ANNOTATION_ENFORCED_AT]: null,
    [ANNOTATION_ENFORCED_REASON]: null,
  });
  if (!annotationResult.ok) {
    console.error(`[quota-enforcement] annotation clear FAILED for ${namespace}: ${annotationResult.error}`);
  }

  const patch: Record<string, string | null> = { [enforcedKey(namespace)]: null };
  const patched = await createOrUpdateConfigMap(
    QUOTA_ENFORCEMENT_NAMESPACE,
    QUOTA_ENFORCEMENT_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!patched.ok) return patched;

  return { ok: true, data: { namespace, restoredReplicas: 1 } };
}
