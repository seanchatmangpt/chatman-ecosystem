/**
 * Real Auto-Generated Quarterly Business Review (QBR) Bundle: the single
 * exec-facing artifact Fortune 5 procurement/vendor-management teams
 * require as a renewal/expansion gate. Every number this module reports
 * already exists somewhere in this console's live dashboards --
 * lib/overage-billing.ts (usage/spend), lib/incidents.ts (incident count/
 * severity + real monthly uptime attainment vs. lib/tiers.ts's
 * SLA_TIER_DEFAULTS), lib/patch-sla.ts (patch-SLA breach count),
 * lib/cost-anomaly.ts (cost-anomaly count), lib/contract-renewals.ts
 * (renewal date) -- but a CSM has never had one single artifact to hand a
 * VP or attach to a renewal deal. This module assembles that artifact and
 * persists it, one bundle per org per quarter, so the history survives a
 * pod restart and a CSM can pull last quarter's number on a live call
 * without re-deriving it from five separate pages.
 *
 * Storage: one real k8s ConfigMap (`platform-qbr-bundles`,
 * `platform-console` namespace), reusing the exact
 * get-then-create-or-patch primitive lib/k8s.ts's Feature Flags module
 * established (`getConfigMap`/`createOrUpdateConfigMap`) -- the same
 * primitive lib/contract-renewals.ts and lib/budget-alerts.ts already
 * reuse for their own ConfigMaps, so this needs zero new k8s resource
 * kind and zero new RBAC verb (the `platform-console-feature-flags` Role
 * already grants get/list/create/update/patch on `configmaps` in this
 * namespace with no `resourceNames` restriction). One key per
 * `<orgId>.<quarter>` (e.g. `acme-corp.2026-Q3`) so every generated
 * bundle is its own immutable-until-regenerated record and the full
 * per-org history is a single ConfigMap read away.
 *
 * Rendering: deliberately introduces NO new PDF library. This module
 * only ever produces a deterministic, JSON-serializable `QbrBundle` --
 * the same "compute the real numbers as plain data, let the existing
 * render path turn them into a document" split lib/orgs.ts's own export
 * pattern (lib/export-all.ts, lib/cost-report-history.ts) already
 * establishes for invoice/receipt history. A caller that wants a PDF
 * reuses that same existing render path over this bundle's JSON, rather
 * than this module hand-rolling a second PDF pipeline.
 *
 * Quarter identifiers are always "YYYY-Qn" (n in 1..4) -- validated by
 * `parseQuarter`, never a free-text date range, so "the Q3 QBR" means the
 * exact same calendar window (UTC) every time it is asked for, and a
 * bundle already generated for a quarter is addressed by that same
 * stable key on every later read.
 *
 * `scanQbrGeneration()` is the unattended entry point --
 * lib/webhook-poller.ts's existing tick calls it, mirroring
 * lib/contract-renewals.ts's `scanContractRenewalReminders` /
 * lib/patch-sla.ts's `runPatchSlaBreachScan` "one function is the cron
 * body, the poller just calls it" convention. It generates a bundle for
 * every org whose CURRENT calendar quarter has none on file yet --
 * idempotent by construction (an org that already has this quarter's
 * bundle is skipped, never silently regenerated/overwritten by the
 * automatic scan; only the explicit, admin-gated
 * `generateQbrBundle(orgId, quarter, {force: true})` path -- reached from
 * POST /api/qbr/[orgId]/generate -- ever overwrites an existing bundle,
 * for the "regenerate on demand for a live customer call" case the spec
 * calls out).
 *
 * Every generation (automatic or forced) writes one real audit_log entry
 * via lib/audit-db.ts from the CALLER (the route handler / the poller's
 * own wrapper), same division of labor lib/contract-renewals.ts's own
 * header comment documents ("the caller is responsible for the
 * audit-log entry") -- this module only ever performs the real
 * aggregation + the one real k8s write.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getOrg, listOrgs, type Org } from "@/lib/orgs";
import { estimateNamespaceOverage } from "@/lib/overage-billing";
import { computeMonthlyUptime, listIncidents, type Incident } from "@/lib/incidents";
import { getOrgPatchSlaBreaches, type PatchSlaBreach } from "@/lib/patch-sla";
import { listCostAnomalyStatus, type CostAnomalyStatus } from "@/lib/cost-anomaly";
import { getContractRenewal, type ContractRenewalWithStatus } from "@/lib/contract-renewals";
import { DEFAULT_SLA_TIER, SLA_TIER_DEFAULTS, type SlaTier } from "@/lib/tiers";

export const QBR_NAMESPACE = "platform-console";
export const QBR_CONFIGMAP = "platform-qbr-bundles";

/** "YYYY-Qn", n in 1..4 -- the one quarter-identifier format this module
 * ever accepts or emits. */
export type QuarterId = string;

const QUARTER_RE = /^(\d{4})-Q([1-4])$/;

export interface QuarterRange {
  quarter: QuarterId;
  /** Real UTC quarter-start, inclusive. */
  start: Date;
  /** Real UTC quarter-end (start of the NEXT quarter), exclusive. */
  end: Date;
}

/** Parses "YYYY-Qn" into its real UTC calendar boundaries -- the ONLY
 * place this module ever turns a quarter label into concrete dates, so
 * every caller (generation, scan, and a future report re-render) agrees
 * on exactly what date range "Q3" means. Returns null on anything that
 * isn't the exact "YYYY-Qn" shape rather than guessing at a looser date
 * format. */
export function parseQuarter(quarter: string): QuarterRange | null {
  const m = QUARTER_RE.exec(quarter);
  if (!m) return null;
  const year = Number(m[1]);
  const q = Number(m[2]);
  const startMonth = (q - 1) * 3; // 0-based
  const start = new Date(Date.UTC(year, startMonth, 1, 0, 0, 0));
  const end = new Date(Date.UTC(year, startMonth + 3, 1, 0, 0, 0));
  return { quarter, start, end };
}

/** The real current calendar quarter (UTC), as "YYYY-Qn" -- what
 * `scanQbrGeneration` generates for any org missing it. */
export function currentQuarter(now: Date = new Date()): QuarterId {
  const year = now.getUTCFullYear();
  const q = Math.floor(now.getUTCMonth() / 3) + 1;
  return `${year}-Q${q}`;
}

/** The three real "YYYY-MM" months a quarter range spans -- the unit
 * lib/incidents.ts's `computeMonthlyUptime` already accepts, so this
 * module derives its quarterly uptime by summing three real monthly
 * computations rather than re-implementing month math a second time. */
function monthsInQuarter(range: QuarterRange): string[] {
  const months: string[] = [];
  const cursor = new Date(range.start);
  while (cursor.getTime() < range.end.getTime()) {
    const y = cursor.getUTCFullYear();
    const m = String(cursor.getUTCMonth() + 1).padStart(2, "0");
    months.push(`${y}-${m}`);
    cursor.setUTCMonth(cursor.getUTCMonth() + 1);
  }
  return months;
}

function configMapKey(orgId: string, quarter: QuarterId): string {
  return `${orgId}.${quarter}`;
}

export interface QbrUsageSpend {
  namespace: string;
  windowLabel: string;
  cpuCoreHoursOverage: number;
  memoryGiBHoursOverage: number;
  overageCostUsd: number;
  /** True only when the real overage estimate could be computed (a live
   * Prometheus query succeeded). A false here means the numbers above are
   * zeroed placeholders, not a genuine zero-overage reading -- the bundle
   * carries this flag through rather than silently reporting "$0" for a
   * namespace whose usage this run genuinely could not observe. */
  available: boolean;
  error: string | null;
}

export interface QbrIncidentSummary {
  count: number;
  bySeverity: { minor: number; major: number; critical: number };
  meanTimeToResolveMinutes: number | null;
  incidents: Incident[];
}

export interface QbrSlaAttainment {
  slaTier: SlaTier;
  slaUptimeTargetPct: number;
  months: Array<{ month: string; actualUptimePct: number; metTarget: boolean; downtimeMinutes: number }>;
  /** Real quarter-wide uptime%, computed from the SAME totalMinutes/
   * downtimeMinutes each month contributes -- not an average of three
   * percentages (which would misweight months of different length). */
  quarterUptimePct: number;
  metTargetAllMonths: boolean;
}

export interface QbrPatchSlaSummary {
  patchSlaTier: SlaTier | null;
  breachCount: number;
  breaches: PatchSlaBreach[];
}

export interface QbrCostAnomalySummary {
  count: number;
  anomalies: CostAnomalyStatus[];
}

export interface QbrContractRenewal {
  renewalDate: string | null;
  daysUntilRenewal: number | null;
  decision: string | null;
  autoRenew: boolean | null;
}

export interface QbrBundle {
  orgId: string;
  orgName: string;
  quarter: QuarterId;
  periodStart: string; // ISO 8601, real UTC quarter start
  periodEnd: string; // ISO 8601, real UTC quarter end (exclusive)
  generatedAt: string; // ISO 8601
  generatedBy: string;
  usageSpend: QbrUsageSpend;
  incidents: QbrIncidentSummary;
  slaAttainment: QbrSlaAttainment;
  patchSla: QbrPatchSlaSummary;
  costAnomalies: QbrCostAnomalySummary;
  contractRenewal: QbrContractRenewal;
}

export type QbrOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

function parseBundle(raw: string): QbrBundle | null {
  try {
    const p = JSON.parse(raw) as Partial<QbrBundle>;
    if (
      typeof p.orgId === "string" &&
      typeof p.quarter === "string" &&
      typeof p.periodStart === "string" &&
      typeof p.periodEnd === "string" &&
      typeof p.generatedAt === "string" &&
      typeof p.generatedBy === "string" &&
      p.usageSpend &&
      p.incidents &&
      p.slaAttainment &&
      p.patchSla &&
      p.costAnomalies &&
      p.contractRenewal
    ) {
      return p as QbrBundle;
    }
    return null;
  } catch {
    return null;
  }
}

async function readAllBundles(): Promise<K8sResult<Map<string, QbrBundle>>> {
  const cm = await getConfigMap(QBR_NAMESPACE, QBR_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, QbrBundle>();
  for (const [key, raw] of Object.entries(data)) {
    const parsed = parseBundle(raw);
    if (parsed) out.set(key, parsed);
  }
  return { ok: true, data: out };
}

async function putBundle(bundle: QbrBundle): Promise<K8sResult<QbrBundle>> {
  const result = await createOrUpdateConfigMap(QBR_NAMESPACE, QBR_CONFIGMAP, {
    [configMapKey(bundle.orgId, bundle.quarter)]: JSON.stringify(bundle),
  });
  if (!result.ok) return result;
  return { ok: true, data: bundle };
}

/** Real, read-only history for one org, newest quarter first -- backs
 * GET /api/qbr/[orgId]. */
export async function listQbrBundlesForOrg(orgId: string): Promise<K8sResult<QbrBundle[]>> {
  const all = await readAllBundles();
  if (!all.ok) return all;
  const rows = Array.from(all.data.values())
    .filter((b) => b.orgId === orgId)
    .sort((a, b) => b.quarter.localeCompare(a.quarter));
  return { ok: true, data: rows };
}

export async function getQbrBundle(orgId: string, quarter: QuarterId): Promise<K8sResult<QbrBundle | null>> {
  const all = await readAllBundles();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(configMapKey(orgId, quarter)) ?? null };
}

export interface QbrLatestRow {
  orgId: string;
  orgName: string;
  latest: QbrBundle | null;
}

/** Real cross-org view: every org's single most-recent bundle (by
 * quarter label, descending), or `latest: null` for an org that has never
 * had one generated -- backs GET /api/qbr. */
export async function listLatestQbrBundles(): Promise<K8sResult<QbrLatestRow[]>> {
  const [orgsResult, allResult] = await Promise.all([listOrgs(), readAllBundles()]);
  if (!orgsResult.ok) return orgsResult;
  if (!allResult.ok) return allResult;

  const byOrg = new Map<string, QbrBundle[]>();
  for (const bundle of allResult.data.values()) {
    const list = byOrg.get(bundle.orgId) ?? [];
    list.push(bundle);
    byOrg.set(bundle.orgId, list);
  }

  const rows: QbrLatestRow[] = orgsResult.data.map((org) => {
    const bundles = (byOrg.get(org.id) ?? []).sort((a, b) => b.quarter.localeCompare(a.quarter));
    return { orgId: org.id, orgName: org.name, latest: bundles[0] ?? null };
  });
  return { ok: true, data: rows };
}

function meanTtrMinutes(incidents: Incident[]): number | null {
  const resolved = incidents.filter((i) => i.resolvedAt !== null);
  if (resolved.length === 0) return null;
  const totalMinutes = resolved.reduce(
    (sum, i) => sum + (new Date(i.resolvedAt as string).getTime() - new Date(i.startedAt).getTime()) / 60_000,
    0,
  );
  return totalMinutes / resolved.length;
}

/**
 * Real, side-effect-free assembly of every real number this quarter's
 * bundle reports, for one org -- reads (a) overage-billing.ts's current
 * real overage estimate for the org's namespace (the freshest real
 * usage/spend signal that module tracks; see its own header comment on
 * why it only ever holds one live trailing-window snapshot rather than a
 * stored quarter-long integral -- this bundle reports that snapshot,
 * taken AT GENERATION TIME, honestly labeled by `available`/`error`
 * rather than fabricating a quarter-long total that was never metered),
 * (b) incidents.ts's real incident rows for the quarter window, (c) three
 * real computeMonthlyUptime calls (one per month in the quarter) against
 * the org's real SLA_TIER_DEFAULTS target, (d) patch-sla.ts's real open
 * breach rows on file for the org, (e) cost-anomaly.ts's real current
 * anomaly status for the org's namespace, (f) contract-renewals.ts's real
 * synced renewal date. Never writes anything -- `generateQbrBundle` is
 * the only function in this module that persists the result.
 */
export async function assembleQbrBundle(
  org: Org,
  quarter: QuarterId,
  generatedBy: string,
): Promise<QbrOutcome<QbrBundle>> {
  const range = parseQuarter(quarter);
  if (!range) return { ok: false, error: `quarter must be 'YYYY-Qn' (n in 1..4), got '${quarter}'` };

  const months = monthsInQuarter(range);
  const slaTier: SlaTier = org.slaTier ?? DEFAULT_SLA_TIER;

  const [overageResult, incidentsResult, monthlyUptimeResults, breachesResult, anomalyResult, renewalResult] =
    await Promise.all([
      estimateNamespaceOverage(org.namespace),
      listIncidents({
        orgId: org.id,
        from: range.start.toISOString(),
        to: new Date(range.end.getTime() - 1).toISOString(),
        limit: 500,
        offset: 0,
      }),
      Promise.all(months.map((month) => computeMonthlyUptime(org.id, month, slaTier))),
      getOrgPatchSlaBreaches(org.id),
      org.namespace ? listCostAnomalyStatus([org.namespace]) : Promise.resolve({ ok: true as const, data: [] }),
      getContractRenewal(org.id),
    ]);

  const usageSpend: QbrUsageSpend = overageResult.ok
    ? {
        namespace: org.namespace,
        windowLabel: overageResult.data.windowLabel,
        cpuCoreHoursOverage: overageResult.data.cpuCoreHoursOverage,
        memoryGiBHoursOverage: overageResult.data.memoryGiBHoursOverage,
        overageCostUsd: overageResult.data.overageCostUsd,
        available: true,
        error: null,
      }
    : {
        namespace: org.namespace,
        windowLabel: "unavailable",
        cpuCoreHoursOverage: 0,
        memoryGiBHoursOverage: 0,
        overageCostUsd: 0,
        available: false,
        error: overageResult.error,
      };

  if (!incidentsResult.ok) return { ok: false, error: incidentsResult.error };
  const incidentRows = incidentsResult.data.rows;
  const incidents: QbrIncidentSummary = {
    count: incidentRows.length,
    bySeverity: {
      minor: incidentRows.filter((i) => i.severity === "minor").length,
      major: incidentRows.filter((i) => i.severity === "major").length,
      critical: incidentRows.filter((i) => i.severity === "critical").length,
    },
    meanTimeToResolveMinutes: meanTtrMinutes(incidentRows),
    incidents: incidentRows,
  };

  const monthlyReports = [];
  for (const r of monthlyUptimeResults) {
    if (!r.ok) return { ok: false, error: r.error };
    monthlyReports.push(r.data);
  }
  const totalMinutes = monthlyReports.reduce((s, r) => s + r.totalMinutesInMonth, 0);
  const totalDowntime = monthlyReports.reduce((s, r) => s + r.downtimeMinutes, 0);
  const target = SLA_TIER_DEFAULTS[slaTier].slaUptimeTargetPct;
  const quarterUptimePct = totalMinutes > 0 ? Math.max(0, (1 - totalDowntime / totalMinutes) * 100) : 100;
  const slaAttainment: QbrSlaAttainment = {
    slaTier,
    slaUptimeTargetPct: target,
    months: monthlyReports.map((r) => ({
      month: r.month,
      actualUptimePct: r.actualUptimePct,
      metTarget: r.metTarget,
      downtimeMinutes: r.downtimeMinutes,
    })),
    quarterUptimePct,
    metTargetAllMonths: monthlyReports.every((r) => r.metTarget),
  };

  if (!breachesResult.ok) return { ok: false, error: breachesResult.error };
  const quarterBreaches = breachesResult.data.filter((b) => {
    const t = new Date(b.breachedAt).getTime();
    return t >= range.start.getTime() && t < range.end.getTime();
  });
  const patchSla: QbrPatchSlaSummary = {
    patchSlaTier: org.patchSlaTier ?? null,
    breachCount: quarterBreaches.length,
    breaches: quarterBreaches,
  };

  if (!anomalyResult.ok) return { ok: false, error: anomalyResult.error };
  const anomalies = anomalyResult.data.filter((a) => a.isAnomaly);
  const costAnomalies: QbrCostAnomalySummary = { count: anomalies.length, anomalies };

  if (!renewalResult.ok) return { ok: false, error: renewalResult.error };
  const contractRenewal: QbrContractRenewal = renewalResult.data
    ? {
        renewalDate: renewalResult.data.renewalDate,
        daysUntilRenewal: renewalResult.data.daysUntilRenewal,
        decision: renewalResult.data.decision,
        autoRenew: renewalResult.data.autoRenew,
      }
    : { renewalDate: null, daysUntilRenewal: null, decision: null, autoRenew: null };

  return {
    ok: true,
    data: {
      orgId: org.id,
      orgName: org.name,
      quarter,
      periodStart: range.start.toISOString(),
      periodEnd: range.end.toISOString(),
      generatedAt: new Date().toISOString(),
      generatedBy,
      usageSpend,
      incidents,
      slaAttainment,
      patchSla,
      costAnomalies,
      contractRenewal,
    },
  };
}

export interface GenerateQbrOptions {
  /** When true, overwrites an existing bundle for this org+quarter --
   * the explicit, admin-gated "regenerate on demand" path. Default false:
   * a bundle already on file for this org+quarter is returned as-is
   * rather than silently recomputed, so the automatic quarterly scan
   * (`scanQbrGeneration`) never clobbers a bundle a CSM already handed to
   * a VP. */
  force?: boolean;
}

/**
 * Real generate-and-persist: assembles the bundle (`assembleQbrBundle`)
 * and writes it to the `platform-qbr-bundles` ConfigMap. Idempotent by
 * default -- an existing bundle for this exact org+quarter is returned
 * unchanged unless `options.force` is set, matching this module's own
 * header comment on why only the explicit on-demand path ever
 * overwrites.
 */
export async function generateQbrBundle(
  orgId: string,
  quarter: QuarterId,
  generatedBy: string,
  options: GenerateQbrOptions = {},
): Promise<QbrOutcome<QbrBundle>> {
  const range = parseQuarter(quarter);
  if (!range) return { ok: false, error: `quarter must be 'YYYY-Qn' (n in 1..4), got '${quarter}'` };

  if (!options.force) {
    const existing = await getQbrBundle(orgId, quarter);
    if (!existing.ok) return existing;
    if (existing.data) return { ok: true, data: existing.data };
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) return orgResult;
  if (!orgResult.data) return { ok: false, error: `org not found: ${orgId}` };

  const assembled = await assembleQbrBundle(orgResult.data, quarter, generatedBy);
  if (!assembled.ok) return assembled;

  const written = await putBundle(assembled.data);
  if (!written.ok) return written;
  return { ok: true, data: written.data };
}

export interface QbrScanResult {
  generated: QbrBundle[];
  skipped: string[]; // orgIds that already had this quarter's bundle on file
  errors: Array<{ orgId: string; error: string }>;
}

/**
 * Real, unattended quarterly scan -- called from lib/webhook-poller.ts's
 * existing tick, same "one function is the cron body, the poller just
 * calls it and audit-logs the result" convention
 * lib/contract-renewals.ts's `scanContractRenewalReminders` /
 * lib/patch-sla.ts's `runPatchSlaBreachScan` already establish. Walks
 * every org (lib/orgs.ts's `listOrgs`) and generates the CURRENT calendar
 * quarter's bundle for any org that does not already have one on file --
 * never regenerates an existing quarter's bundle (see
 * `generateQbrBundle`'s own header comment on why only the explicit
 * force path does that). One org's aggregation failing is recorded on
 * that org's own result and never aborts the whole scan, same
 * "one org's failure never blocks every other org" discipline
 * lib/patch-sla.ts's `runPatchSlaBreachScan` already establishes.
 */
export async function scanQbrGeneration(now: Date = new Date()): Promise<QbrOutcome<QbrScanResult>> {
  const quarter = currentQuarter(now);
  const orgsResult = await listOrgs();
  if (!orgsResult.ok) return orgsResult;

  const report: QbrScanResult = { generated: [], skipped: [], errors: [] };

  for (const org of orgsResult.data) {
    const existing = await getQbrBundle(org.id, quarter);
    if (!existing.ok) {
      report.errors.push({ orgId: org.id, error: existing.error });
      continue;
    }
    if (existing.data) {
      report.skipped.push(org.id);
      continue;
    }
    const result = await generateQbrBundle(org.id, quarter, "system:qbr-quarterly-scan");
    if (!result.ok) {
      report.errors.push({ orgId: org.id, error: result.error });
      continue;
    }
    report.generated.push(result.data);
  }

  return { ok: true, data: report };
}
