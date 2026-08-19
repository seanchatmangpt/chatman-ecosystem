/**
 * Real, persisted cost & usage report SNAPSHOT history -- the missing
 * piece lib/invoice-preview.ts's own header comment identifies:
 * getInvoicePreview/getNamespaceUsageMetrics already compute a real,
 * metered-from-Prometheus usage figure, but only ever on demand, at
 * request time. A Fortune-5 FinOps reviewer's actual question ("what did
 * usage/cost look like last week vs. this week") needs a durable,
 * point-in-time record, not a live recomputation every time the page is
 * opened. This module is that record: one k8s ConfigMap
 * (`platform-console-cost-reports`, `platform-console` namespace), one
 * key per namespace -> JSON array of `CostReportSnapshot`, appended to by
 * POST /api/internal/cost-report-snapshot (fired by the
 * "cost-report-snapshot" lib/scheduled-jobs.ts CronJob command) and read
 * by GET /api/orgs/[id]/cost-reports for in-app charting/CSV export.
 *
 * Same get-then-create-or-patch `getConfigMap`/`createOrUpdateConfigMap`
 * primitive, same "one JSON-stringified value per key" convention, and
 * same capped-append-only-list shape as
 * lib/s3-export-subscription.ts's `recordRunHistory`/`MAX_RUNS_KEPT`
 * (itself following lib/orgs.ts's registry-ConfigMap convention) -- no
 * new storage pattern introduced. Every number stored here traces back to
 * a real `getNamespaceUsageMetrics` call over real Prometheus data at
 * `capturedAt`, multiplied by the same `ILLUSTRATIVE_RATES` table
 * lib/invoice-preview.ts already declares explicitly illustrative --
 * never a fabricated/interpolated number.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const COST_REPORTS_NAMESPACE = "platform-console";
export const COST_REPORTS_CONFIGMAP = "platform-console-cost-reports";

/** Most recent snapshots kept per namespace -- same reasoning as
 * lib/s3-export-subscription.ts's MAX_RUNS_KEPT: bounds the ConfigMap
 * value well under k8s's 1MiB ceiling (200 daily snapshots is >6 months
 * of daily history) while the durable long-lived record, if one is ever
 * needed beyond this, remains a future disclosed gap, same as that
 * module's own comment about audit_log being the true system of record
 * for anything longer-lived than its own run log. */
export const MAX_SNAPSHOTS_PER_NAMESPACE = 200;

export interface CostReportSnapshot {
  namespace: string;
  windowStart: string;
  windowEnd: string;
  cpuCoreHours: number;
  memoryGiBHours: number;
  illustrativeCost: number;
  capturedAt: string;
}

type SnapshotRegistry = Record<string, CostReportSnapshot[]>;

function isCostReportSnapshot(value: unknown): value is CostReportSnapshot {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.namespace === "string" &&
    typeof v.windowStart === "string" &&
    typeof v.windowEnd === "string" &&
    typeof v.cpuCoreHours === "number" &&
    typeof v.memoryGiBHours === "number" &&
    typeof v.illustrativeCost === "number" &&
    typeof v.capturedAt === "string"
  );
}

async function getRegistry(): Promise<K8sResult<SnapshotRegistry>> {
  const existing = await getConfigMap(COST_REPORTS_NAMESPACE, COST_REPORTS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: SnapshotRegistry = {};
  for (const [namespace, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[namespace] = rows.filter(isCostReportSnapshot);
      }
    } catch {
      // A hand-edited or corrupt registry entry is skipped, not fatal --
      // same "one bad row doesn't break the whole list" discipline
      // lib/orgs.ts's getRegistry and lib/s3-export-subscription.ts's
      // getRunHistoryRegistry both already use.
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Real, chronological (oldest first) snapshot history for one namespace.
 * `[]` -- not an error -- for a namespace with no snapshots yet, same
 * "empty list is not a failure" convention as
 * listExportSubscriptionRuns.
 */
export async function listCostReportSnapshots(
  namespace: string,
): Promise<K8sResult<CostReportSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[namespace] ?? [] };
}

/**
 * Appends one real snapshot for `namespace`, capped to the most recent
 * `MAX_SNAPSHOTS_PER_NAMESPACE`. Called only from
 * POST /api/internal/cost-report-snapshot, after that route has already
 * computed a real `CostReportSnapshot` from live metered Prometheus data
 * -- this function performs no computation of its own, only the
 * get-then-append-then-cap-then-patch persistence step.
 */
export async function appendCostReportSnapshot(
  snapshot: CostReportSnapshot,
): Promise<K8sResult<CostReportSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const existing = registry.data[snapshot.namespace] ?? [];
  const updated = [...existing, snapshot].slice(-MAX_SNAPSHOTS_PER_NAMESPACE);

  const result = await createOrUpdateConfigMap(COST_REPORTS_NAMESPACE, COST_REPORTS_CONFIGMAP, {
    [snapshot.namespace]: JSON.stringify(updated),
  });
  if (!result.ok) return result;

  return { ok: true, data: updated };
}
