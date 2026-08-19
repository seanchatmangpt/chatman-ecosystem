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
import type { Pool } from "pg";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getOrg, getOrgProjectTier, setOrgManagingPartnerId, type Org } from "@/lib/orgs";
import {
  getUsageBenchmark,
  type BenchmarkResult,
  type InsufficientBenchmarkResult,
} from "@/lib/usage-benchmarks";
import { listIncidents } from "@/lib/incidents";
import { getAuditDbPool, queryOrgSpendHistory } from "@/lib/audit-db";
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
  /**
   * Optional recurring channel/reseller commission rate, as a percentage
   * (e.g. `15` = 15%) of this partner's total managed-org spend for a
   * period -- the standard AWS/Azure/GCP partner-program shape (a
   * percentage-of-managed-spend cut), distinct from the one-time
   * referral-signup credit lib/referral-ledger.ts already tracks.
   * Same optional/forward-compatible-field round-trip discipline
   * lib/orgs.ts's `Org.branding` establishes: absent on every partner
   * created before this field existed, round-trips through
   * `createPartner`/`updatePartner` untouched with `commissionRatePct:
   * undefined`, and `computePartnerCommission` below refuses (a real,
   * reported error, never a fabricated 0%) to compute a commission for a
   * partner that has never had a rate set.
   */
  commissionRatePct?: number;
  createdAt: string;
}

interface PartnerRecord {
  name: string;
  managedOrgIds: string[];
  commissionRatePct?: number;
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
        typeof entry?.createdAt === "string" &&
        (entry.commissionRatePct === undefined || typeof entry.commissionRatePct === "number")
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
  commissionRatePct?: number;
}): Promise<K8sResult<Partner>> {
  const id = globalThis.crypto.randomUUID();
  const createdAt = new Date().toISOString();
  const record: PartnerRecord = {
    name: input.name,
    managedOrgIds: [...new Set(input.managedOrgIds)],
    ...(input.commissionRatePct !== undefined ? { commissionRatePct: input.commissionRatePct } : {}),
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
  input: { name?: string; managedOrgIds?: string[]; commissionRatePct?: number },
): Promise<K8sResult<Partner | null>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  const existing = registry.data[id];
  if (!existing) return { ok: true, data: null };

  const record: PartnerRecord = {
    name: input.name?.trim() || existing.name,
    managedOrgIds: input.managedOrgIds ? [...new Set(input.managedOrgIds)] : existing.managedOrgIds,
    commissionRatePct: input.commissionRatePct !== undefined ? input.commissionRatePct : existing.commissionRatePct,
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

// ---------------------------------------------------------------------------
// Partner revenue-share / commission ledger
// ---------------------------------------------------------------------------

/**
 * Real recurring channel/reseller commission ledger -- the piece the
 * rollup above (getPartnerOrgsRollup) and the one-time referral-signup
 * credit (lib/referral-ledger.ts) both leave open: neither computes an
 * ONGOING percentage-of-managed-spend payout, the standard AWS/Azure/GCP
 * partner-program shape a Fortune-5 channel deal is actually priced on.
 *
 * Storage: a new `platform_console.partner_commissions` Postgres table
 * on the SAME audit-db.ts pool, `CREATE TABLE IF NOT EXISTS`
 * self-bootstrap convention lib/incidents.ts's `ensureIncidentsTable` and
 * lib/patch-sla.ts's `ensurePatchSlaTables` both already establish -- one
 * IMMUTABLE row per (partner_id, period): `UNIQUE (partner_id, period)`
 * means a period that has already been computed is never silently
 * recomputed with different numbers later (a re-run of
 * `computePartnerCommission` for an already-recorded period returns the
 * SAME persisted row, not a fresh recomputation), the exact auditability
 * guarantee a partner's finance/procurement team needs before it will
 * sign a channel agreement against this ledger.
 */
export type PartnerCommissionPeriod = string; // "YYYY-MM", UTC calendar month

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

export function isValidCommissionPeriod(value: string): value is PartnerCommissionPeriod {
  return PERIOD_PATTERN.test(value);
}

/** [start, end) UTC month bounds for a "YYYY-MM" period string. */
function periodBounds(period: PartnerCommissionPeriod): { from: Date; to: Date } {
  const [yearStr, monthStr] = period.split("-");
  const year = Number(yearStr);
  const monthIndex = Number(monthStr) - 1; // 0-based for Date.UTC
  const from = new Date(Date.UTC(year, monthIndex, 1));
  const to = new Date(Date.UTC(year, monthIndex + 1, 1));
  return { from, to };
}

/** One managed org's real contribution to a partner's total managed
 * spend for the period -- the per-org breakdown a partner's finance team
 * audits the commission total against. */
export interface PartnerCommissionOrgLine {
  orgId: string;
  orgName?: string;
  /** Real Stripe-invoice-derived spend for this org over the period,
   * from lib/audit-db.ts's `queryOrgSpendHistory` -- the SAME real
   * dollar source lib/audit-db.ts's own /orgs/[id]/spend-history route
   * already exposes for a single org, reused here across every org a
   * partner manages rather than re-derived. `null` when the org has no
   * Stripe billing on file or the underlying query failed -- excluded
   * from the total, never fabricated as zero. */
  spendUsd: number | null;
  error?: string;
}

export interface PartnerCommissionResult {
  partnerId: string;
  period: PartnerCommissionPeriod;
  commissionRatePct: number;
  /** Sum of every line's real, non-null spendUsd -- orgs with a query
   * error or no Stripe billing on file are excluded from this total,
   * never zeroed into it. */
  totalManagedSpendUsd: number;
  /** totalManagedSpendUsd * commissionRatePct / 100, rounded to cents --
   * the amount owed to the partner for this period. Illustrative in the
   * same sense lib/patch-sla.ts's computePatchSlaCredit and
   * lib/incidents.ts's computeCredit are: real arithmetic over real
   * spend data, but NOT a Stripe payout -- this module computes and
   * persists the owed amount only, no payout automation. */
  commissionOwedUsd: number;
  orgLines: PartnerCommissionOrgLine[];
  computedAt: string;
}

async function ensurePartnerCommissionsTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.partner_commissions (
      id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      partner_id              text NOT NULL,
      period                  text NOT NULL,
      commission_rate_pct     double precision NOT NULL,
      total_managed_spend_usd double precision NOT NULL,
      commission_owed_usd     double precision NOT NULL,
      org_lines               jsonb NOT NULL,
      computed_at             timestamptz NOT NULL DEFAULT now(),
      -- Immutable-per-period: a period already computed for this partner
      -- is never silently recomputed to a different number later.
      UNIQUE (partner_id, period)
    )
  `);
  await pool.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto`).catch(() => {});
  await pool.query(
    `CREATE INDEX IF NOT EXISTS partner_commissions_partner_idx ON platform_console.partner_commissions (partner_id, period)`,
  );
}

let commissionsTableReady: Promise<void> | null = null;

async function resolveCommissionsPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!commissionsTableReady) {
    commissionsTableReady = ensurePartnerCommissionsTable(pool);
  }
  await commissionsTableReady;
  return pool;
}

function toCommissionResult(r: Record<string, unknown>): PartnerCommissionResult {
  return {
    partnerId: r.partner_id as string,
    period: r.period as string,
    commissionRatePct: r.commission_rate_pct as number,
    totalManagedSpendUsd: r.total_managed_spend_usd as number,
    commissionOwedUsd: r.commission_owed_usd as number,
    orgLines: (typeof r.org_lines === "string"
      ? JSON.parse(r.org_lines)
      : r.org_lines) as PartnerCommissionOrgLine[],
    computedAt: new Date(r.computed_at as string).toISOString(),
  };
}

export type PartnerCommissionOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

/**
 * Real per-org spend line for one org in a partner's managed set, over
 * one UTC calendar-month period -- reuses `queryOrgSpendHistory`
 * (lib/audit-db.ts), the SAME real Stripe-invoice-derived monthly spend
 * figure `getPartnerOrgsRollup` already fans out per-org readers to
 * compute a live rollup from, at `monthly` granularity so exactly one
 * bucket covers the whole requested period.
 */
async function spendLineForOrg(
  orgId: string,
  period: PartnerCommissionPeriod,
): Promise<PartnerCommissionOrgLine> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return { orgId, spendUsd: null, error: orgResult.error };
  }
  const org = orgResult.data;
  if (!org) {
    return { orgId, spendUsd: null, error: "org not found" };
  }

  const { from, to } = periodBounds(period);
  const historyResult = await queryOrgSpendHistory(orgId, org.namespace, { from, to, granularity: "monthly" });
  if (!historyResult.ok) {
    return { orgId, orgName: org.name, spendUsd: null, error: historyResult.error };
  }

  return { orgId, orgName: org.name, spendUsd: historyResult.data.totalCostUsd };
}

/**
 * Real commission computation, immutable-per-period: reuses the exact
 * per-org fan-out shape `getPartnerOrgsRollup` already established
 * (Promise.all over `partner.managedOrgIds`), but sources each org's
 * dollar figure from `queryOrgSpendHistory`'s real Stripe-invoice-backed
 * monthly spend rather than the benchmark's cost-per-pod-hour metric --
 * a commission is owed on actual billed spend, not a normalized
 * per-pod-hour comparison figure.
 *
 * If this (partnerId, period) has already been computed, the SAME
 * persisted row is returned (never recomputed to a possibly-different
 * number from a later, possibly-different live spend read) -- the
 * auditable-ledger guarantee this capability exists for. A partner with
 * no `commissionRatePct` set is a real, reported error, never a silent
 * 0%.
 */
export async function computePartnerCommission(
  partner: Partner,
  period: PartnerCommissionPeriod,
): Promise<PartnerCommissionOutcome<PartnerCommissionResult>> {
  if (!isValidCommissionPeriod(period)) {
    return { ok: false, error: `invalid period "${period}" -- expected "YYYY-MM"` };
  }
  if (partner.commissionRatePct === undefined) {
    return { ok: false, error: `partner ${partner.id} has no commissionRatePct set` };
  }

  const pool = await resolveCommissionsPool();
  if (!pool) return { ok: false, error: "partner-commissions store not configured or unreachable" };

  const existing = await pool.query(
    `SELECT * FROM platform_console.partner_commissions WHERE partner_id = $1 AND period = $2`,
    [partner.id, period],
  );
  if (existing.rows[0]) {
    return { ok: true, data: toCommissionResult(existing.rows[0]) };
  }

  const orgLines = await Promise.all(partner.managedOrgIds.map((orgId) => spendLineForOrg(orgId, period)));
  const totalManagedSpendUsd = orgLines.reduce((sum, line) => sum + (line.spendUsd ?? 0), 0);
  const commissionOwedUsd = Math.round(totalManagedSpendUsd * (partner.commissionRatePct / 100) * 100) / 100;
  const computedAt = new Date().toISOString();

  const inserted = await pool.query(
    `INSERT INTO platform_console.partner_commissions
       (partner_id, period, commission_rate_pct, total_managed_spend_usd, commission_owed_usd, org_lines, computed_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     ON CONFLICT (partner_id, period) DO NOTHING
     RETURNING *`,
    [partner.id, period, partner.commissionRatePct, totalManagedSpendUsd, commissionOwedUsd, JSON.stringify(orgLines), computedAt],
  );

  if (inserted.rows[0]) {
    return { ok: true, data: toCommissionResult(inserted.rows[0]) };
  }

  // Lost the race to a concurrent computation of the same period --
  // read back the row it wrote, same "the persisted row wins" guarantee.
  const winner = await pool.query(
    `SELECT * FROM platform_console.partner_commissions WHERE partner_id = $1 AND period = $2`,
    [partner.id, period],
  );
  if (winner.rows[0]) {
    return { ok: true, data: toCommissionResult(winner.rows[0]) };
  }
  return { ok: false, error: "commission insert raced and no row could be read back" };
}

/** Real, immutable list of every period already computed for this
 * partner, most recent first -- backs GET
 * /api/partners/[partnerId]/commissions. */
export async function listPartnerCommissions(
  partnerId: string,
): Promise<PartnerCommissionOutcome<PartnerCommissionResult[]>> {
  const pool = await resolveCommissionsPool();
  if (!pool) return { ok: false, error: "partner-commissions store not configured or unreachable" };
  const result = await pool.query(
    `SELECT * FROM platform_console.partner_commissions WHERE partner_id = $1 ORDER BY period DESC`,
    [partnerId],
  );
  return { ok: true, data: result.rows.map(toCommissionResult) };
}

/** Real read of one already-computed period's full breakdown (the
 * per-org spend lines that produced the total) -- backs GET
 * /api/partners/[partnerId]/commissions/[period]. Returns `data: null`
 * (not an error) when that period has never been computed for this
 * partner. */
export async function getPartnerCommission(
  partnerId: string,
  period: string,
): Promise<PartnerCommissionOutcome<PartnerCommissionResult | null>> {
  if (!isValidCommissionPeriod(period)) {
    return { ok: false, error: `invalid period "${period}" -- expected "YYYY-MM"` };
  }
  const pool = await resolveCommissionsPool();
  if (!pool) return { ok: false, error: "partner-commissions store not configured or unreachable" };
  const result = await pool.query(
    `SELECT * FROM platform_console.partner_commissions WHERE partner_id = $1 AND period = $2`,
    [partnerId, period],
  );
  const row = result.rows[0];
  return { ok: true, data: row ? toCommissionResult(row) : null };
}
