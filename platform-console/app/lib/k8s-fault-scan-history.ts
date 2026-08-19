/**
 * Real, persisted K8s Fault-Scan SNAPSHOT history -- the scheduled,
 * continuous-posture-monitoring counterpart to lib/k8s-fault-scan.ts's
 * existing on-demand, diagnose-only scanner. That module already
 * DIAGNOSES a live org namespace on request (real `K8sFaultFinding`
 * records, classified against a real SREGym fault taxonomy or
 * `UNCLASSIFIED`) but only at request time -- a Fortune-5 SRE buyer's
 * actual procurement question ("has our structural-anomaly posture
 * degraded over the last quarter") needs a durable, point-in-time trend
 * line, not a one-shot number recomputed only when someone opens the
 * page. This module is that record: one k8s ConfigMap
 * (`platform-console-fault-scan-history`, `platform-console` namespace),
 * one key per `orgId` -> capped JSON array of `FaultScanSnapshot`,
 * appended to by POST /api/internal/fault-scan-snapshot (fired by the
 * "fault-scan-snapshot" lib/scheduled-jobs.ts CronJob command, daily)
 * and read by GET /api/k8s-fault-scan/history for in-app trend
 * charting.
 *
 * Same get-then-create-or-patch `getConfigMap`/`createOrUpdateConfigMap`
 * primitive, same "one JSON-stringified value per key" convention, and
 * same capped-append-only-list shape as lib/latency-history.ts's own
 * listLatencyBenchmarkSnapshots/appendLatencyBenchmarkSnapshots -- no
 * new storage pattern introduced.
 *
 * Stated plainly, matching lib/k8s-fault-scan.ts's own scope discipline:
 * this module persists DIAGNOSTIC snapshots only. It runs no new scan
 * logic of its own (every `findingsSummary` entry is a real
 * `K8sFaultFinding` produced by lib/k8s-fault-scan.ts's existing
 * `runK8sFaultScan`, passed in by the caller) and takes no remediation
 * or actuation action -- it is a pure persistence layer over an
 * already-computed, already-diagnose-only scan result, same "diagnose,
 * never actuate" boundary POST /api/k8s-fault-scan's own header comment
 * already states.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { K8sFaultFinding } from "@/lib/k8s-fault-scan";

export const FAULT_SCAN_HISTORY_NAMESPACE = "platform-console";
export const FAULT_SCAN_HISTORY_CONFIGMAP = "platform-console-fault-scan-history";

/** Most recent snapshots kept per `orgId` key -- same reasoning as
 * lib/latency-history.ts's own MAX_SNAPSHOTS_PER_KEY: bounds each
 * ConfigMap value well under k8s's 1MiB ceiling (200 daily snapshots is
 * >6.5 months of daily history per org) while a durable long-lived
 * record, if one is ever needed beyond this, remains a future disclosed
 * gap, same as that module's own comment. */
export const MAX_SNAPSHOTS_PER_KEY = 200;

/** Real severity buckets, derived -- never guessed -- from
 * `K8sFaultFinding.relation_class`: a `declared_vs_observed` finding is
 * exactly the class POST /api/k8s-fault-scan's own route already treats
 * as warranting a human-reviewed `k8s-fault.remediate-suggest` approval
 * filing (see that route's header comment), so it is bucketed `high`
 * here for the same, already-established reason; every other real
 * relation class the scanner emits (`dangling_reference`,
 * `insufficient_capability`, `aggregate_threshold`) is a structural
 * anomaly worth surfacing but not one this app already treats as
 * approval-worthy, so it is bucketed `info`. This is a disclosed
 * severity derivation over real scanner output, not a fabricated
 * severity field the underlying scanner does not itself compute. */
export type FaultScanFindingSeverity = "high" | "info";

export function severityForFinding(finding: K8sFaultFinding): FaultScanFindingSeverity {
  return finding.relation_class === "declared_vs_observed" ? "high" : "info";
}

export interface FaultScanSnapshot {
  orgId: string;
  scannedAt: string;
  findingsCount: number;
  findingsBySeverity: Record<FaultScanFindingSeverity, number>;
  /** The real, unmodified `K8sFaultFinding[]` this snapshot summarizes --
   * reuses the existing diagnose-only scan result shape exactly, never a
   * re-encoded/lossy copy. */
  findingsSummary: K8sFaultFinding[];
}

type SnapshotRegistry = Record<string, FaultScanSnapshot[]>;

function isK8sFaultFinding(value: unknown): value is K8sFaultFinding {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.kind === "string" &&
    typeof v.object_name === "string" &&
    typeof v.namespace === "string" &&
    typeof v.relation_class === "string" &&
    typeof v.field === "string" &&
    typeof v.observed === "string" &&
    (v.expected === null || typeof v.expected === "string") &&
    typeof v.detail === "string" &&
    typeof v.taxonomy === "string"
  );
}

function isFaultScanSnapshot(value: unknown): value is FaultScanSnapshot {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  if (
    typeof v.orgId !== "string" ||
    typeof v.scannedAt !== "string" ||
    typeof v.findingsCount !== "number" ||
    !v.findingsBySeverity ||
    typeof v.findingsBySeverity !== "object" ||
    !Array.isArray(v.findingsSummary)
  ) {
    return false;
  }
  const bySeverity = v.findingsBySeverity as Record<string, unknown>;
  if (typeof bySeverity.high !== "number" || typeof bySeverity.info !== "number") {
    return false;
  }
  return v.findingsSummary.every(isK8sFaultFinding);
}

async function getRegistry(): Promise<K8sResult<SnapshotRegistry>> {
  const existing = await getConfigMap(FAULT_SCAN_HISTORY_NAMESPACE, FAULT_SCAN_HISTORY_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: SnapshotRegistry = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[key] = rows.filter(isFaultScanSnapshot);
      }
    } catch {
      // A hand-edited or corrupt registry entry is skipped, not fatal --
      // same "one bad row doesn't break the whole list" discipline
      // lib/latency-history.ts's getRegistry already uses.
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Real, chronological (oldest first) snapshot history for one `orgId`.
 * `[]` -- not an error -- when there is no history yet, same
 * "empty list is not a failure" convention as
 * listLatencyBenchmarkSnapshots.
 */
export async function listFaultScanSnapshots(
  orgId: string,
): Promise<K8sResult<FaultScanSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[orgId] ?? [] };
}

/**
 * Builds the real `FaultScanSnapshot` for one already-completed scan --
 * pure summarization of an already-computed `K8sFaultFinding[]`, no
 * scan logic of its own. `scannedAt` defaults to "now" (real wall-clock
 * time of the append), matching every other snapshot module's own
 * capturedAt/scannedAt convention.
 */
export function buildFaultScanSnapshot(
  orgId: string,
  findings: K8sFaultFinding[],
  scannedAt: string = new Date().toISOString(),
): FaultScanSnapshot {
  const findingsBySeverity: Record<FaultScanFindingSeverity, number> = { high: 0, info: 0 };
  for (const finding of findings) {
    findingsBySeverity[severityForFinding(finding)] += 1;
  }
  return {
    orgId,
    scannedAt,
    findingsCount: findings.length,
    findingsBySeverity,
    findingsSummary: findings,
  };
}

/**
 * Appends one real snapshot, capped to the most recent
 * `MAX_SNAPSHOTS_PER_KEY` per `orgId` key. Performs no scan computation
 * of its own -- the caller (POST /api/internal/fault-scan-snapshot,
 * fired by the scheduled CronJob command, or POST /api/k8s-fault-scan's
 * own on-demand route) has already run the real, existing
 * `runK8sFaultScan` and passes its real output in -- this function
 * performs only the get-then-append-then-cap-then-patch persistence
 * step, same split as lib/latency-history.ts's own
 * appendLatencyBenchmarkSnapshots.
 */
export async function appendFaultScanSnapshot(
  snapshot: FaultScanSnapshot,
): Promise<K8sResult<FaultScanSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const existing = registry.data[snapshot.orgId] ?? [];
  const merged = [...existing, snapshot].slice(-MAX_SNAPSHOTS_PER_KEY);

  const result = await createOrUpdateConfigMap(FAULT_SCAN_HISTORY_NAMESPACE, FAULT_SCAN_HISTORY_CONFIGMAP, {
    [snapshot.orgId]: JSON.stringify(merged),
  });
  if (!result.ok) return result;

  return { ok: true, data: merged };
}
