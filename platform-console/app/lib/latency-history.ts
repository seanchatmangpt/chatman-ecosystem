/**
 * Real, persisted latency/performance-benchmark SNAPSHOT history -- the
 * missing piece lib/load-test.ts's own header comment identifies:
 * `runLoadTestAgainstTarget` already runs a real, concurrent-request load
 * test against one of the platform's own internal services, but only
 * ever on demand, at request time. A Fortune-5 platform-engineering
 * reviewer's actual question ("has p95 latency degraded over the last
 * quarter across our node pool") needs a durable, point-in-time trend
 * line, not a live one-shot number recomputed every time the page is
 * opened. This module is that record: one k8s ConfigMap
 * (`platform-console-latency-history`, `platform-console` namespace),
 * one key per `<orgId>:<targetId>` -> JSON array of
 * `LatencyBenchmarkSnapshot`, appended to by
 * POST /api/internal/latency-benchmark-snapshot (fired by the
 * "latency-benchmark-snapshot" lib/scheduled-jobs.ts CronJob command) and
 * read by GET /api/load-test/history for in-app charting.
 *
 * Same get-then-create-or-patch `getConfigMap`/`createOrUpdateConfigMap`
 * primitive, same "one JSON-stringified value per key" convention, and
 * same capped-append-only-list shape as lib/cost-report-history.ts's own
 * `listCostReportSnapshots`/`appendCostReportSnapshot` (itself following
 * lib/orgs.ts's registry-ConfigMap convention) -- no new storage pattern
 * introduced. Every number stored here traces back to a real
 * `runLoadTest` call against a real internal service at `capturedAt`,
 * never a fabricated/interpolated number.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { LatencyBenchmarkSnapshot } from "@/lib/load-test";

export const LATENCY_HISTORY_NAMESPACE = "platform-console";
export const LATENCY_HISTORY_CONFIGMAP = "platform-console-latency-history";

/** Most recent snapshots kept per `<orgId>:<targetId>` key -- same
 * reasoning as lib/cost-report-history.ts's own
 * MAX_SNAPSHOTS_PER_NAMESPACE: bounds each ConfigMap value well under
 * k8s's 1MiB ceiling (200 weekly snapshots is >3.5 years of weekly
 * history per target) while the durable long-lived record, if one is
 * ever needed beyond this, remains a future disclosed gap, same as that
 * module's own comment. */
export const MAX_SNAPSHOTS_PER_KEY = 200;

export type { LatencyBenchmarkSnapshot };

type SnapshotRegistry = Record<string, LatencyBenchmarkSnapshot[]>;

function registryKey(orgId: string, targetId: string): string {
  return `${orgId}:${targetId}`;
}

function isLatencyBenchmarkSnapshot(value: unknown): value is LatencyBenchmarkSnapshot {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.orgId === "string" &&
    typeof v.targetId === "string" &&
    typeof v.targetLabel === "string" &&
    typeof v.capturedAt === "string" &&
    typeof v.concurrency === "number" &&
    typeof v.durationSec === "number" &&
    typeof v.totalRequests === "number" &&
    typeof v.errorCount === "number" &&
    typeof v.errorRate === "number" &&
    typeof v.requestsPerSecond === "number" &&
    typeof v.p50Ms === "number" &&
    typeof v.p95Ms === "number" &&
    typeof v.p99Ms === "number"
  );
}

async function getRegistry(): Promise<K8sResult<SnapshotRegistry>> {
  const existing = await getConfigMap(LATENCY_HISTORY_NAMESPACE, LATENCY_HISTORY_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: SnapshotRegistry = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[key] = rows.filter(isLatencyBenchmarkSnapshot);
      }
    } catch {
      // A hand-edited or corrupt registry entry is skipped, not fatal --
      // same "one bad row doesn't break the whole list" discipline
      // lib/cost-report-history.ts's getRegistry already uses.
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Real, chronological (oldest first) snapshot history for one
 * `(orgId, targetId)` pair. `[]` -- not an error -- when there is no
 * history yet, same "empty list is not a failure" convention as
 * listCostReportSnapshots.
 */
export async function listLatencyBenchmarkSnapshots(
  orgId: string,
  targetId: string,
): Promise<K8sResult<LatencyBenchmarkSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[registryKey(orgId, targetId)] ?? [] };
}

/**
 * Real, chronological (oldest first) snapshot history for every target
 * belonging to one `orgId`, grouped by `targetId` -- the shape
 * GET /api/load-test/history returns for charting a full node pool's
 * trend line in one call rather than one request per target.
 */
export async function listLatencyBenchmarkHistoryForOrg(
  orgId: string,
): Promise<K8sResult<Record<string, LatencyBenchmarkSnapshot[]>>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const prefix = `${orgId}:`;
  const byTarget: Record<string, LatencyBenchmarkSnapshot[]> = {};
  for (const [key, rows] of Object.entries(registry.data)) {
    if (!key.startsWith(prefix)) continue;
    const targetId = key.slice(prefix.length);
    byTarget[targetId] = rows;
  }
  return { ok: true, data: byTarget };
}

/**
 * Appends one real snapshot per target, capped to the most recent
 * `MAX_SNAPSHOTS_PER_KEY` per `(orgId, targetId)` key. Called only from
 * POST /api/internal/latency-benchmark-snapshot, after that route has
 * already computed real `LatencyBenchmarkSnapshot`s via
 * `runScheduledLatencyBenchmark` -- this function performs no benchmark
 * computation of its own, only the
 * get-then-append-then-cap-then-patch persistence step, same split as
 * lib/cost-report-history.ts's own appendCostReportSnapshot.
 */
export async function appendLatencyBenchmarkSnapshots(
  snapshots: LatencyBenchmarkSnapshot[],
): Promise<K8sResult<Record<string, LatencyBenchmarkSnapshot[]>>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const updated: SnapshotRegistry = { ...registry.data };
  const patch: Record<string, string> = {};

  for (const snapshot of snapshots) {
    const key = registryKey(snapshot.orgId, snapshot.targetId);
    const existing = updated[key] ?? [];
    const merged = [...existing, snapshot].slice(-MAX_SNAPSHOTS_PER_KEY);
    updated[key] = merged;
    patch[key] = JSON.stringify(merged);
  }

  if (Object.keys(patch).length === 0) {
    return { ok: true, data: {} };
  }

  const result = await createOrUpdateConfigMap(
    LATENCY_HISTORY_NAMESPACE,
    LATENCY_HISTORY_CONFIGMAP,
    patch,
  );
  if (!result.ok) return result;

  const changed: Record<string, LatencyBenchmarkSnapshot[]> = {};
  for (const snapshot of snapshots) {
    const key = registryKey(snapshot.orgId, snapshot.targetId);
    changed[key] = updated[key];
  }
  return { ok: true, data: changed };
}
