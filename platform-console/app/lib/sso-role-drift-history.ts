/**
 * Real, persisted SSO/SCIM Role-Mapping Drift snapshot history -- the
 * scheduled, continuous-posture-monitoring counterpart to
 * lib/sso-role-drift.ts's on-demand computation. A security review
 * board's actual procurement question ("show us this posture over the
 * last quarter, not just right now") needs a durable, point-in-time
 * trend line, same reasoning lib/k8s-fault-scan-history.ts's own module
 * doc gives for that capability. This module is that record: one k8s
 * ConfigMap (`platform-console-sso-role-drift-history`,
 * `platform-console` namespace), one key per `orgId` -> capped JSON
 * array of `SsoRoleDriftSnapshot`, appended to by
 * POST /api/internal/sso-role-drift-snapshot and read by
 * GET /api/orgs/[id]/sso-role-drift?history=1 for in-app trend display.
 *
 * Same get-then-create-or-patch `getConfigMap`/`createOrUpdateConfigMap`
 * primitive, same "one JSON-stringified value per key" convention, and
 * same capped-append-only-list shape as
 * lib/k8s-fault-scan-history.ts's listFaultScanSnapshots/
 * appendFaultScanSnapshot -- no new storage pattern introduced.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { SsoRoleDriftFinding, SsoRoleDriftFindingKind, SsoRoleDriftReport } from "@/lib/sso-role-drift";

export const SSO_ROLE_DRIFT_HISTORY_NAMESPACE = "platform-console";
export const SSO_ROLE_DRIFT_HISTORY_CONFIGMAP = "platform-console-sso-role-drift-history";

/** Most recent snapshots kept per `orgId` key -- same bound-the-
 * ConfigMap-value-under-1MiB reasoning as
 * lib/k8s-fault-scan-history.ts's MAX_SNAPSHOTS_PER_KEY. */
export const MAX_SNAPSHOTS_PER_KEY = 200;

export interface SsoRoleDriftSnapshot {
  orgId: string;
  scannedAt: string;
  unmappedRoleInUseCount: number;
  unusedMappingCount: number;
  /** The real, unmodified `SsoRoleDriftFinding[]` this snapshot
   * summarizes -- reuses the existing report's finding shape exactly,
   * never a re-encoded/lossy copy. */
  findings: SsoRoleDriftFinding[];
}

type SnapshotRegistry = Record<string, SsoRoleDriftSnapshot[]>;

const DRIFT_FINDING_KINDS: SsoRoleDriftFindingKind[] = ["unmapped_role_in_use", "unused_mapping"];

function isSsoRoleDriftFinding(value: unknown): value is SsoRoleDriftFinding {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.role === "string" &&
    typeof v.kind === "string" &&
    (DRIFT_FINDING_KINDS as string[]).includes(v.kind) &&
    (v.identifier === undefined || typeof v.identifier === "string") &&
    (v.ssoGroup === undefined || typeof v.ssoGroup === "string")
  );
}

function isSsoRoleDriftSnapshot(value: unknown): value is SsoRoleDriftSnapshot {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.orgId === "string" &&
    typeof v.scannedAt === "string" &&
    typeof v.unmappedRoleInUseCount === "number" &&
    typeof v.unusedMappingCount === "number" &&
    Array.isArray(v.findings) &&
    v.findings.every(isSsoRoleDriftFinding)
  );
}

async function getRegistry(): Promise<K8sResult<SnapshotRegistry>> {
  const existing = await getConfigMap(SSO_ROLE_DRIFT_HISTORY_NAMESPACE, SSO_ROLE_DRIFT_HISTORY_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: SnapshotRegistry = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[key] = rows.filter(isSsoRoleDriftSnapshot);
      }
    } catch {
      // A hand-edited or corrupt registry entry is skipped, not fatal --
      // same "one bad row doesn't break the whole list" discipline
      // lib/k8s-fault-scan-history.ts's getRegistry already uses.
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Real, chronological (oldest first) snapshot history for one `orgId`.
 * `[]` -- not an error -- when there is no history yet, same
 * "empty list is not a failure" convention as
 * listFaultScanSnapshots.
 */
export async function listSsoRoleDriftSnapshots(
  orgId: string,
): Promise<K8sResult<SsoRoleDriftSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[orgId] ?? [] };
}

/**
 * Builds the real `SsoRoleDriftSnapshot` for one already-computed
 * report -- pure summarization, no drift computation of its own.
 */
export function buildSsoRoleDriftSnapshot(report: SsoRoleDriftReport): SsoRoleDriftSnapshot {
  return {
    orgId: report.orgId,
    scannedAt: report.generatedAt,
    unmappedRoleInUseCount: report.unmappedRoleInUseCount,
    unusedMappingCount: report.unusedMappingCount,
    findings: report.findings,
  };
}

/**
 * Appends one real snapshot, capped to the most recent
 * `MAX_SNAPSHOTS_PER_KEY` per `orgId` key -- same get-then-append-then-
 * cap-then-patch persistence step as
 * lib/k8s-fault-scan-history.ts's appendFaultScanSnapshot.
 */
export async function appendSsoRoleDriftSnapshot(
  snapshot: SsoRoleDriftSnapshot,
): Promise<K8sResult<SsoRoleDriftSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const existing = registry.data[snapshot.orgId] ?? [];
  const merged = [...existing, snapshot].slice(-MAX_SNAPSHOTS_PER_KEY);

  const result = await createOrUpdateConfigMap(
    SSO_ROLE_DRIFT_HISTORY_NAMESPACE,
    SSO_ROLE_DRIFT_HISTORY_CONFIGMAP,
    { [snapshot.orgId]: JSON.stringify(merged) },
  );
  if (!result.ok) return result;
  return { ok: true, data: merged };
}
