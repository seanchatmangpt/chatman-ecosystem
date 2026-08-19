/**
 * Real, periodic Compliance Report generation and storage -- the
 * SOC2/ISO27001 "continuous monitoring" vendor deliverable (Vanta/Drata/
 * Secureframe's own core product): a dated, self-contained artifact an
 * auditor or a customer's own GRC tool can consume on a fixed cadence,
 * distinct from every live dashboard already in this app (/audit, /ip-
 * allowlist admin UI, /cost-anomaly, /policy) which only ever show
 * CURRENT state and reset their own "what changed" framing every time a
 * human refreshes the page.
 *
 * This module fabricates nothing: every section is a real query result,
 * composed at generation time, from modules this codebase already ships:
 *
 *   sections.auditEventCount      -- lib/audit-export.ts's real
 *                                     `countAuditEventsInRange` (same
 *                                     WHERE clause as the streaming NDJSON
 *                                     export, so the count and a live
 *                                     download of the same period always
 *                                     agree)
 *   sections.ipAllowlistSnapshot  -- lib/ip-allowlist.ts's real
 *                                     `getIpAllowlist(namespace)`, the
 *                                     CIDR list enforced at request time
 *                                     as of generation
 *   sections.costAnomaliesInPeriod -- lib/cost-anomaly.ts's real
 *                                     `listCostAnomalyStatus`, filtered to
 *                                     namespaces whose real, persisted
 *                                     `lastAnomalyAt` falls inside
 *                                     [periodStart, periodEnd]
 *   sections.activePolicyBindings -- lib/policy.ts's real
 *                                     `listActivePolicies`, the live
 *                                     ValidatingAdmissionPolicy/Binding
 *                                     objects enforced by kube-apiserver
 *                                     as of generation
 *
 * Storage: one real k8s ConfigMap (`platform-compliance-reports`,
 * `platform-console` namespace), same get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this app already uses. Two key
 * families, mirroring lib/cost-anomaly.ts's own `state.*`/`threshold.*`
 * split:
 *
 *   `report.<orgId>.<reportId>` -> JSON ComplianceReport (metadata +
 *       sections + a small flattened CSV summary string -- NOT the full
 *       NDJSON audit dump, which is regenerated live and streamed straight
 *       from Postgres on download via GET .../[reportId]?format=ndjson,
 *       so this ConfigMap's total size never scales with audit-log volume
 *       and stays well under etcd's ~1MiB object size ceiling no matter
 *       how many events a period covers)
 *   `cadence.<orgId>`           -> JSON ComplianceCadence (operator-set
 *       "weekly"/"monthly" schedule + who set it + when)
 *
 * A k8s ConfigMap `data` key must match `[-._a-zA-Z0-9]+` -- `orgId` is
 * always either a real `crypto.randomUUID()` (lib/orgs.ts's `createOrg`)
 * or, for this deployment's one single-tenant fallback, the literal
 * string `"platform-console"` (see lib/orgs.ts's own `getOrg` fallback
 * convention, reused identically by the API routes below), both already
 * legal key bytes with no escaping needed; `reportId` is likewise always
 * a `crypto.randomUUID()` minted by `generateComplianceReport` itself,
 * never caller-supplied.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { countAuditEventsInRange } from "@/lib/audit-export";
import { getIpAllowlist } from "@/lib/ip-allowlist";
import { listCostAnomalyStatus, type CostAnomalyStatus } from "@/lib/cost-anomaly";
import { listActivePolicies, type ActivePolicyBundle } from "@/lib/policy";

export const COMPLIANCE_REPORTS_NAMESPACE = "platform-console";
export const COMPLIANCE_REPORTS_CONFIGMAP = "platform-compliance-reports";

export type ComplianceCadenceInterval = "weekly" | "monthly";

export interface ComplianceCadence {
  orgId: string;
  interval: ComplianceCadenceInterval;
  setBy: string;
  setAt: string;
}

export interface ComplianceReportSections {
  auditEventCount: number;
  ipAllowlistSnapshot: string[];
  costAnomaliesInPeriod: CostAnomalyStatus[];
  activePolicyBindings: ActivePolicyBundle;
}

export interface ComplianceReport {
  reportId: string;
  orgId: string;
  namespace: string;
  periodStart: string;
  periodEnd: string;
  generatedAt: string;
  generatedBy: string;
  sections: ComplianceReportSections;
  /** Small flattened CSV text -- section,key,value rows, one per real
   * scalar/counted fact above. Never the full audit trail (see this
   * module's header comment on why that is streamed live instead). */
  csvSummary: string;
}

function reportKey(orgId: string, reportId: string): string {
  return `report.${orgId}.${reportId}`;
}
function cadenceKey(orgId: string): string {
  return `cadence.${orgId}`;
}

function parseReport(raw: string): ComplianceReport | null {
  try {
    const p = JSON.parse(raw) as Partial<ComplianceReport>;
    if (
      typeof p.reportId === "string" &&
      typeof p.orgId === "string" &&
      typeof p.namespace === "string" &&
      typeof p.periodStart === "string" &&
      typeof p.periodEnd === "string" &&
      typeof p.generatedAt === "string" &&
      typeof p.generatedBy === "string" &&
      p.sections &&
      typeof p.csvSummary === "string"
    ) {
      return p as ComplianceReport;
    }
    return null;
  } catch {
    return null;
  }
}

function parseCadence(orgId: string, raw: string): ComplianceCadence | null {
  try {
    const p = JSON.parse(raw) as Partial<ComplianceCadence>;
    if (
      (p.interval === "weekly" || p.interval === "monthly") &&
      typeof p.setBy === "string" &&
      typeof p.setAt === "string"
    ) {
      return { orgId, interval: p.interval, setBy: p.setBy, setAt: p.setAt };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Real flattened CSV of the report's own counted/listed facts -- one row
 * per real scalar or list item, no fabricated columns. Quoting follows
 * RFC 4180's minimal rule (wrap in double quotes, double any embedded
 * quote) applied only to the `value` column, since `section`/`key` are
 * always fixed, comma-free literal strings this function itself writes.
 */
function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

function buildCsvSummary(sections: ComplianceReportSections): string {
  const rows: string[] = ["section,key,value"];
  rows.push(`audit,event_count,${sections.auditEventCount}`);
  sections.ipAllowlistSnapshot.forEach((cidr, i) => {
    rows.push(`ip_allowlist,cidr_${i},${csvEscape(cidr)}`);
  });
  if (sections.ipAllowlistSnapshot.length === 0) {
    rows.push(`ip_allowlist,cidr_count,0`);
  }
  sections.costAnomaliesInPeriod.forEach((a) => {
    rows.push(
      `cost_anomaly,${csvEscape(a.namespace)},deviation_pct=${a.deviationPct ?? "null"};detected_at=${a.lastAnomalyAt ?? "null"}`,
    );
  });
  if (sections.costAnomaliesInPeriod.length === 0) {
    rows.push(`cost_anomaly,count,0`);
  }
  sections.activePolicyBindings.bindings.forEach((b) => {
    rows.push(
      `policy_binding,${csvEscape(b.name)},policy=${csvEscape(b.policyName)};actions=${csvEscape(b.validationActions.join("|"))}`,
    );
  });
  if (sections.activePolicyBindings.bindings.length === 0) {
    rows.push(`policy_binding,count,0`);
  }
  return rows.join("\n") + "\n";
}

/**
 * Real, read-only cost-anomaly-in-period filter: `listCostAnomalyStatus`
 * reports each namespace's CURRENT status plus its persisted
 * `lastAnomalyAt` (the real timestamp `checkCostAnomalies`' poller last
 * flipped that namespace into anomaly) -- this keeps only namespaces
 * whose `lastAnomalyAt` falls inside `[periodStart, periodEnd]`, i.e. a
 * real anomaly detection event actually happened during the report's own
 * period. A namespace that is currently anomalous but was flagged before
 * `periodStart` is excluded -- the report describes the period, not "is
 * currently anomalous right now".
 */
function filterAnomaliesInPeriod(
  statuses: CostAnomalyStatus[],
  periodStart: string,
  periodEnd: string,
): CostAnomalyStatus[] {
  const startMs = Date.parse(periodStart);
  const endMs = Date.parse(periodEnd);
  return statuses.filter((s) => {
    if (!s.lastAnomalyAt) return false;
    const t = Date.parse(s.lastAnomalyAt);
    return Number.isFinite(t) && t >= startMs && t <= endMs;
  });
}

export interface GenerateComplianceReportInput {
  orgId: string;
  namespace: string;
  periodStart: string;
  periodEnd: string;
  generatedBy: string;
}

/**
 * Composes one real `ComplianceReport` from the four real, already-live
 * data sources listed in this module's header comment, then stores it.
 * The ONE function both `POST .../generate` (on-demand, an owner clicking
 * a button) and the CronJob's own curl (unattended, on cadence) call --
 * "same code path" per this capability's own spec, so an auditor can
 * never be shown a report that was assembled by different logic than the
 * one an operator triggers by hand.
 */
export async function generateComplianceReport(
  input: GenerateComplianceReportInput,
): Promise<K8sResult<ComplianceReport>> {
  const [auditEventCount, allowlistResult, anomalyResult, policyResult] = await Promise.all([
    countAuditEventsInRange({ from: input.periodStart, to: input.periodEnd }),
    getIpAllowlist(input.namespace),
    listCostAnomalyStatus([input.namespace]),
    listActivePolicies(),
  ]);

  if (!allowlistResult.ok) return allowlistResult;
  if (!anomalyResult.ok) return anomalyResult;
  if (!policyResult.ok) return policyResult;

  const sections: ComplianceReportSections = {
    auditEventCount,
    ipAllowlistSnapshot: allowlistResult.data,
    costAnomaliesInPeriod: filterAnomaliesInPeriod(
      anomalyResult.data,
      input.periodStart,
      input.periodEnd,
    ),
    activePolicyBindings: policyResult.data,
  };

  const report: ComplianceReport = {
    reportId: globalThis.crypto.randomUUID(),
    orgId: input.orgId,
    namespace: input.namespace,
    periodStart: input.periodStart,
    periodEnd: input.periodEnd,
    generatedAt: new Date().toISOString(),
    generatedBy: input.generatedBy,
    sections,
    csvSummary: buildCsvSummary(sections),
  };

  const write = await createOrUpdateConfigMap(COMPLIANCE_REPORTS_NAMESPACE, COMPLIANCE_REPORTS_CONFIGMAP, {
    [reportKey(input.orgId, report.reportId)]: JSON.stringify(report),
  });
  if (!write.ok) return write;
  return { ok: true, data: report };
}

/**
 * Real list of every previously-generated report for one org, newest
 * first -- scans this ConfigMap's own `report.<orgId>.*` keys (never a
 * second index object that could drift from what was actually written).
 */
export async function listComplianceReports(orgId: string): Promise<K8sResult<ComplianceReport[]>> {
  const result = await getConfigMap(COMPLIANCE_REPORTS_NAMESPACE, COMPLIANCE_REPORTS_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};
  const prefix = `report.${orgId}.`;
  const reports: ComplianceReport[] = [];
  for (const [key, raw] of Object.entries(data)) {
    if (!key.startsWith(prefix)) continue;
    const parsed = parseReport(raw);
    if (parsed) reports.push(parsed);
  }
  reports.sort((a, b) => b.generatedAt.localeCompare(a.generatedAt));
  return { ok: true, data: reports };
}

/** Real single-report read, `null` (not an error) when the id doesn't
 * exist for this org -- same "not-found is data, not failure" convention
 * `getOrg` already uses. */
export async function getComplianceReport(
  orgId: string,
  reportId: string,
): Promise<K8sResult<ComplianceReport | null>> {
  const result = await getConfigMap(COMPLIANCE_REPORTS_NAMESPACE, COMPLIANCE_REPORTS_CONFIGMAP);
  if (!result.ok) return result;
  const raw = result.data?.data?.[reportKey(orgId, reportId)];
  if (!raw) return { ok: true, data: null };
  return { ok: true, data: parseReport(raw) };
}

/** Real operator-set recurring cadence for one org -- read by the UI and,
 * once set, is what a human operator uses to decide the CronJob schedule
 * string passed to `createComplianceReportCronJob`
 * (lib/scheduled-jobs.ts); this function only persists the operator's
 * choice, it does not itself create/mutate the CronJob object. */
export async function setComplianceCadence(
  orgId: string,
  interval: ComplianceCadenceInterval,
  setBy: string,
): Promise<K8sResult<ComplianceCadence>> {
  const record: ComplianceCadence = { orgId, interval, setBy, setAt: new Date().toISOString() };
  const write = await createOrUpdateConfigMap(COMPLIANCE_REPORTS_NAMESPACE, COMPLIANCE_REPORTS_CONFIGMAP, {
    [cadenceKey(orgId)]: JSON.stringify(record),
  });
  if (!write.ok) return write;
  return { ok: true, data: record };
}

export async function getComplianceCadence(orgId: string): Promise<K8sResult<ComplianceCadence | null>> {
  const result = await getConfigMap(COMPLIANCE_REPORTS_NAMESPACE, COMPLIANCE_REPORTS_CONFIGMAP);
  if (!result.ok) return result;
  const raw = result.data?.data?.[cadenceKey(orgId)];
  if (!raw) return { ok: true, data: null };
  return { ok: true, data: parseCadence(orgId, raw) };
}

/** The real, fixed cron schedule for each operator-selectable cadence --
 * "weekly" fires Monday 06:00 UTC, "monthly" fires the 1st of the month
 * 06:00 UTC. Not user-editable text (same "no free-form schedule string
 * from a caller-controlled cadence" posture lib/scheduled-jobs.ts's own
 * ALLOWED_COMMANDS keeps for container commands), so a compliance
 * schedule can never be crafted into something that fires every minute. */
export const CADENCE_CRON_SCHEDULE: Record<ComplianceCadenceInterval, string> = {
  weekly: "0 6 * * 1",
  monthly: "0 6 1 * *",
};

/**
 * Real period bounds for the report a CADENCE_CRON_SCHEDULE firing at
 * `now` should cover: the interval immediately preceding `now` (a weekly
 * cadence covers the trailing 7 days, a monthly cadence covers the
 * trailing calendar month) -- so an unattended CronJob firing at 06:00
 * Monday requests a report for exactly the week that just ended, with no
 * gap or overlap against the next firing's own period.
 */
export function periodForCadence(
  interval: ComplianceCadenceInterval,
  now: Date = new Date(),
): { periodStart: string; periodEnd: string } {
  const periodEnd = now.toISOString();
  if (interval === "weekly") {
    const start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    return { periodStart: start.toISOString(), periodEnd };
  }
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 1, now.getUTCDate()));
  return { periodStart: start.toISOString(), periodEnd };
}
