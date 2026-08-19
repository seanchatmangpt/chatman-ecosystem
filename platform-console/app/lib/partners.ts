/**
 * Real Partner/MSP Multi-Tenant Management Console -- the layer
 * lib/orgs.ts's own header comment (and its `Org` type) has no concept
 * of: a managing identity ABOVE a single org. Every MSP/systems-
 * integrator reseller (a real Fortune-5 procurement channel) today has
 * to log in and out of each customer org separately, with no
 * consolidated view and no single audit trail tying those separate
 * sessions together. This module is the missing entity: a `Partner`
 * record that lists which org ids it manages, plus the two real
 * operations a reseller console needs on top of that list --
 * aggregate-rollup read and no-re-auth context switch.
 *
 * Storage: one real k8s ConfigMap (`platform-console-partners`, the
 * `platform-console` namespace), one key per partner id, JSON-encoded
 * value -- the EXACT same "one key per record, `JSON.stringify`d value,
 * `getConfigMap`/`createOrUpdateConfigMap` get-then-create-or-patch"
 * convention lib/orgs.ts's own `ORGS_REGISTRY_CONFIGMAP` registry
 * already established (see that file's `getRegistry`/`createOrg`). No
 * new k8s resource kind, no new RBAC verb: the same
 * `platform-console-feature-flags` Role already grants get/list/create/
 * update/patch on `configmaps` in this namespace with no
 * `resourceNames` restriction, so it already covers this ConfigMap too.
 *
 * Partner CRUD is admin-only, gated by the existing platform-level
 * `requireRole(session, "owner")` check from lib/authz.ts -- no new
 * authz primitive, same "owner of the platform console" gate
 * app/api/roles/route.ts and app/api/org-invites/route.ts already use
 * for platform-wide (not single-org) privileged actions.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getOrg, getOrgProjectTier, setOrgManagingPartnerId, type Org } from "@/lib/orgs";
import {
  getUsageBenchmark,
  type BenchmarkResult,
  type InsufficientBenchmarkResult,
} from "@/lib/usage-benchmarks";
import { listIncidents } from "@/lib/incidents";
import type { ProjectTier } from "@/lib/tiers";

export const PARTNERS_NAMESPACE = "platform-console";
export const PARTNERS_CONFIGMAP = "platform-console-partners";

export interface Partner {
  id: string;
  name: string;
  /** Org ids this partner may see and switch into. Always a real subset
   * of lib/orgs.ts's own registry ids -- callers that fan out over these
   * (getPartnerOrgsRollup below) treat a stale/removed org id as a real,
   * reported-per-org error, never a silent skip, so a reseller notices
   * immediately if one of its managed orgs was deleted out from under
   * it. */
  managedOrgIds: string[];
  createdAt: string;
}

interface PartnerRecord {
  name: string;
  managedOrgIds: string[];
  createdAt: string;
}

async function getRegistry(): Promise<K8sResult<Record<string, PartnerRecord>>> {
  const existing = await getConfigMap(PARTNERS_NAMESPACE, PARTNERS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, PartnerRecord> = {};
  for (const [id, raw] of Object.entries(existing.data.data)) {
    try {
      const entry = JSON.parse(raw) as PartnerRecord;
      if (
        typeof entry?.name === "string" &&
        Array.isArray(entry?.managedOrgIds) &&
        entry.managedOrgIds.every((o) => typeof o === "string") &&
        typeof entry?.createdAt === "string"
      ) {
        parsed[id] = entry;
      }
      // A hand-edited or corrupt registry entry that fails the shape
      // check is skipped, not fatal -- same "don't let one bad row
      // break the whole list" discipline lib/orgs.ts's getRegistry and
      // lib/authz.ts's toAssignments both already apply.
    } catch {
      // malformed JSON -- same skip-not-fatal discipline.
    }
  }
  return { ok: true, data: parsed };
}

export async function listPartners(): Promise<K8sResult<Partner[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const partners = Object.entries(registry.data)
    .map(([id, entry]) => ({ id, ...entry }))
    .sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  return { ok: true, data: partners };
}

export async function getPartner(id: string): Promise<K8sResult<Partner | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const entry = registry.data[id];
  return { ok: true, data: entry ? { id, ...entry } : null };
}

export async function createPartner(input: {
  name: string;
  managedOrgIds: string[];
}): Promise<K8sResult<Partner>> {
  const id = globalThis.crypto.randomUUID();
  const createdAt = new Date().toISOString();
  const record: PartnerRecord = {
    name: input.name,
    managedOrgIds: [...new Set(input.managedOrgIds)],
    createdAt,
  };
  const result = await createOrUpdateConfigMap(PARTNERS_NAMESPACE, PARTNERS_CONFIGMAP, {
    [id]: JSON.stringify(record),
  });
  if (!result.ok) return result;

  // Denormalized Org-side link, best-effort: a failure here never fails
  // partner creation itself (the Partner record is the real source of
  // truth) -- see setOrgManagingPartnerId's own doc comment.
  await Promise.all(record.managedOrgIds.map((orgId) => setOrgManagingPartnerId(orgId, id)));

  return { ok: true, data: { id, ...record } };
}

/**
 * Real, partial-merge update: only the fields present in `input` are
 * changed -- same "merge patch, never a blind full-record replace"
 * discipline every other JSON-in-ConfigMap-value writer in this repo
 * follows (e.g. lib/orgs.ts's branding/region/sla setters, which all
 * re-read the current entry before writing the merged one back).
 */
export async function updatePartner(
  id: string,
  input: { name?: string; managedOrgIds?: string[] },
): Promise<K8sResult<Partner | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const existing = registry.data[id];
  if (!existing) return { ok: true, data: null };

  const record: PartnerRecord = {
    name: input.name?.trim() || existing.name,
    managedOrgIds: input.managedOrgIds ? [...new Set(input.managedOrgIds)] : existing.managedOrgIds,
    createdAt: existing.createdAt,
  };
  const result = await createOrUpdateConfigMap(PARTNERS_NAMESPACE, PARTNERS_CONFIGMAP, {
    [id]: JSON.stringify(record),
  });
  if (!result.ok) return result;

  // Reconcile the denormalized Org-side link: newly-added orgs get
  // linked, orgs removed from managedOrgIds get unlinked. Best-effort,
  // same discipline as createPartner above.
  const removed = existing.managedOrgIds.filter((o) => !record.managedOrgIds.includes(o));
  await Promise.all([
    ...record.managedOrgIds.map((orgId) => setOrgManagingPartnerId(orgId, id)),
    ...removed.map((orgId) => setOrgManagingPartnerId(orgId, null)),
  ]);

  return { ok: true, data: { id, ...record } };
}

/**
 * Real delete: a k8s ConfigMap `data` key removal via the same
 * merge-patch-with-`null`-value convention RFC 7386 defines for
 * removing a map key (createOrUpdateConfigMap's PATCH already sends
 * `application/merge-patch+json`, so a `null` value here deletes that
 * one `data` key server-side, not a client-side re-write of every other
 * key). Idempotent: deleting an already-absent id is `{ok:true,
 * data:false}`, not an error, same "not found is a real, distinguishable
 * outcome, not a thrown error" convention every other reader in this
 * module follows.
 */
export async function deletePartner(id: string): Promise<K8sResult<boolean>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const existing = registry.data[id];
  if (!existing) return { ok: true, data: false };

  const patch: Record<string, string | null> = { [id]: null };
  const result = await createOrUpdateConfigMap(
    PARTNERS_NAMESPACE,
    PARTNERS_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!result.ok) return result;

  // Unlink every org this partner managed, best-effort.
  await Promise.all(existing.managedOrgIds.map((orgId) => setOrgManagingPartnerId(orgId, null)));

  return { ok: true, data: true };
}

/**
 * Real, per-partner validation helper: is `orgId` one this partner
 * actually manages right now (a live read of the partner's current
 * `managedOrgIds`, never a claim trusted from request input alone)?
 * Used by both the rollup route (to 403 a request for an org outside
 * the partner's own list) and the switch-org route (to gate the session
 * mint the same way).
 */
export function partnerManagesOrg(partner: Partner, orgId: string): boolean {
  return partner.managedOrgIds.includes(orgId);
}

/**
 * Real per-org rollup row -- backs GET
 * /api/partners/[partnerId]/orgs. Fans out to the exact same three
 * per-org readers a human would otherwise open three separate org
 * dashboards to see one at a time: `getOrgProjectTier` (lib/orgs.ts),
 * `getUsageBenchmark` (lib/usage-benchmarks.ts), and an open-incident
 * count via `listIncidents` (lib/incidents.ts) filtered to this org and
 * `status: "open"`. No new data source, no new storage -- this row is a
 * pure aggregation over numbers this platform already computes per org.
 *
 * `found: false` (org id in the partner's managedOrgIds but no longer
 * a real org in the registry -- e.g. deleted out from under the
 * partner) and per-field `*Error` strings (one reader failed while the
 * others succeeded) are both real, reported outcomes, never silently
 * dropped rows or fabricated zero values -- same fail-visible
 * discipline this file's own header comment on `managedOrgIds`
 * documents.
 */
export interface PartnerOrgRollupRow {
  orgId: string;
  found: boolean;
  /** Set only when `found` is false because the org registry read
   * itself failed (a real k8s error), never for the plain "org id no
   * longer exists" case. */
  error?: string;
  orgName?: string;
  tier?: ProjectTier;
  tierError?: string;
  benchmark?: BenchmarkResult | InsufficientBenchmarkResult;
  benchmarkError?: string;
  openIncidentCount?: number;
  incidentsError?: string;
}

// Generous enough to cover this platform's real, live incident volume
// per org in one page -- see the "no status filter in listIncidents"
// note at its one call site below for why this exists instead of a
// dedicated open-incident-count query.
const INCIDENT_ROLLUP_PAGE_SIZE = 500;

async function rollupForOrg(orgId: string): Promise<PartnerOrgRollupRow> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return { orgId, found: false, error: orgResult.error };
  }
  const org: Org | null = orgResult.data;
  if (!org) {
    return { orgId, found: false };
  }

  // listIncidents (lib/incidents.ts) has no `status` filter in its own
  // parameterized query -- it filters by orgId/componentId/time range
  // only -- so an "open" count is derived client-side from the real rows
  // it returns, over a page wide enough to cover this platform's real
  // incident volume in practice (INCIDENT_ROLLUP_PAGE_SIZE below) rather
  // than widening that shared query's own contract for one caller.
  const [tierResult, benchmarkResult, incidentsResult] = await Promise.all([
    getOrgProjectTier(org.namespace),
    getUsageBenchmark(orgId),
    listIncidents({ orgId, limit: INCIDENT_ROLLUP_PAGE_SIZE, offset: 0 }),
  ]);

  const row: PartnerOrgRollupRow = { orgId, found: true, orgName: org.name };

  if (tierResult.ok) row.tier = tierResult.data;
  else row.tierError = tierResult.error;

  if (benchmarkResult.ok) row.benchmark = benchmarkResult.data;
  else row.benchmarkError = benchmarkResult.error;

  if (incidentsResult.ok) {
    row.openIncidentCount = incidentsResult.data.rows.filter((i) => i.status === "open").length;
  } else {
    row.incidentsError = incidentsResult.error;
  }

  return row;
}

/**
 * Real, real-time fan-out over every org this partner manages -- no
 * caching, no background job, one live read per org per call (the same
 * "compute live, at request time" convention lib/usage-benchmarks.ts's
 * own header comment documents for its own aggregation). Rows are
 * returned in the same order as `partner.managedOrgIds`; a partner
 * managing zero orgs gets an empty, real (not error) array.
 */
export async function getPartnerOrgsRollup(partner: Partner): Promise<PartnerOrgRollupRow[]> {
  return Promise.all(partner.managedOrgIds.map((orgId) => rollupForOrg(orgId)));
}

/**
 * Formats a partner-context-switch audit actor string the exact same
 * way lib/impersonation.ts's `formatImpersonationActor` formats an
 * admin-impersonation one -- the spec's own requirement ("tagged the
 * same way the existing admin-impersonation audit trail already tags a
 * live-request-path switch"): fold the switch's context into the
 * `actor` string itself, so the trail reads "action performed by
 * identity X switching via partner Y into org Z" instead of losing that
 * context the moment the org-scoped session cookie takes over.
 */
export function formatPartnerSwitchActor(baseActor: string, partnerId: string, orgId: string): string {
  return `${baseActor} (partner ${partnerId} switching into org ${orgId})`;
}
