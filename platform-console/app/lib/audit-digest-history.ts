/**
 * Real, persisted weekly activity-digest SNAPSHOT history -- same missing
 * piece lib/cost-report-history.ts's own header comment identifies, applied
 * to the audit-activity-digest capability instead of cost & usage: GET
 * /api/audit/activity-digest computes a real, summarized digest on demand,
 * but a compliance officer's actual weekly evidence-filing workflow needs
 * a durable, point-in-time record they can reopen later -- "what did the
 * digest we filed on 2026-08-10 actually say" -- not only ever a live
 * recomputation. This module is that record: one k8s ConfigMap
 * (`platform-console-audit-digests`, `platform-console` namespace), one
 * key per org id -> JSON array of `PersistedActivityDigest`, appended to
 * by POST /api/cron/audit-activity-digest (the "audit-activity-digest"
 * weekly CronJob) and read back by GET /api/audit/activity-digest when a
 * caller passes `?history=true`.
 *
 * Same get-then-create-or-patch `getConfigMap`/`createOrUpdateConfigMap`
 * primitive, same "one JSON-stringified value per key, capped-append-only
 * list" convention as lib/cost-report-history.ts's
 * appendCostReportSnapshot/listCostReportSnapshots -- no new storage
 * pattern introduced. Every snapshot stored here is the direct output of
 * lib/audit-db.ts's queryOrgActivityDigest against real
 * platform_console.audit_log rows, never a fabricated or interpolated
 * figure.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { ActivityDigestActorSummary, OrgActivityDigestResult } from "@/lib/audit-db";

export const AUDIT_DIGEST_NAMESPACE = "platform-console";
export const AUDIT_DIGEST_CONFIGMAP = "platform-console-audit-digests";

/** Most recent snapshots kept per org -- same reasoning as
 * lib/cost-report-history.ts's MAX_SNAPSHOTS_PER_NAMESPACE: bounds the
 * ConfigMap value well under k8s's 1MiB ceiling (52 weekly snapshots is a
 * full year of weekly history per org) while the durable long-lived
 * record, if one is ever needed beyond this, remains
 * platform_console.audit_log itself -- the true system of record this
 * digest only ever summarizes. */
export const MAX_DIGEST_SNAPSHOTS_PER_ORG = 52;

export type PersistedActivityDigest = OrgActivityDigestResult;

function isActorSummary(value: unknown): value is ActivityDigestActorSummary {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.actor === "string" &&
    typeof v.totalActions === "number" &&
    typeof v.logins === "number" &&
    typeof v.configChanges === "number" &&
    typeof v.deployments === "number" &&
    typeof v.approvals === "number" &&
    typeof v.deletions === "number" &&
    typeof v.other === "number" &&
    typeof v.firstActionAt === "string" &&
    typeof v.lastActionAt === "string"
  );
}

function isPersistedDigest(value: unknown): value is PersistedActivityDigest {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.orgId === "string" &&
    typeof v.sinceDate === "string" &&
    typeof v.generatedAt === "string" &&
    typeof v.totalEvents === "number" &&
    Array.isArray(v.actors) &&
    (v.actors as unknown[]).every(isActorSummary)
  );
}

type DigestRegistry = Record<string, PersistedActivityDigest[]>;

async function getRegistry(): Promise<K8sResult<DigestRegistry>> {
  const existing = await getConfigMap(AUDIT_DIGEST_NAMESPACE, AUDIT_DIGEST_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: DigestRegistry = {};
  for (const [orgId, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[orgId] = rows.filter(isPersistedDigest);
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
 * Real, chronological (oldest first) digest snapshot history for one org.
 * `[]` -- not an error -- for an org with no persisted digests yet, same
 * "empty list is not a failure" convention as listCostReportSnapshots.
 */
export async function listActivityDigestSnapshots(
  orgId: string,
): Promise<K8sResult<PersistedActivityDigest[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[orgId] ?? [] };
}

/**
 * Appends one real digest snapshot for `orgId`, capped to the most recent
 * MAX_DIGEST_SNAPSHOTS_PER_ORG. Called only from POST
 * /api/cron/audit-activity-digest, after that route has already computed
 * a real OrgActivityDigestResult via queryOrgActivityDigest -- this
 * function performs no summarization of its own, only the
 * get-then-append-then-cap-then-patch persistence step.
 */
export async function appendActivityDigestSnapshot(
  digest: OrgActivityDigestResult,
): Promise<K8sResult<PersistedActivityDigest[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const existing = registry.data[digest.orgId] ?? [];
  const updated = [...existing, digest].slice(-MAX_DIGEST_SNAPSHOTS_PER_ORG);

  const result = await createOrUpdateConfigMap(AUDIT_DIGEST_NAMESPACE, AUDIT_DIGEST_CONFIGMAP, {
    [digest.orgId]: JSON.stringify(updated),
  });
  if (!result.ok) return result;

  return { ok: true, data: updated };
}
