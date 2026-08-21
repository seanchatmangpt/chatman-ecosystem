/**
 * Real, scheduled data-retention/purge policy enforcement -- the gap this
 * closes: lib/dsar.ts's erasure flow and lib/backup-retention.ts's tiered
 * backup-retention window are both real, but BOTH are on-demand/manual
 * (a DSAR subject request, or a human hitting GET /api/orgs/[id]/backups
 * which happens to run cleanupExpiredBackups as a side effect of being
 * viewed). Neither one is a standing, scheduled control that runs
 * whether or not a human ever looks at the page -- which is exactly what
 * a SOC2/GDPR data-minimization audit actually checks for: proof that
 * stale rows are purged automatically, on a schedule, with a receipt,
 * not "we could purge them by hand if asked."
 *
 * This module is the policy layer for platform_console.audit_log
 * specifically: it decides the retention window (reusing the same
 * per-ProjectTier day counts lib/backup-retention.ts already established
 * against lib/tiers.ts's ProjectTier type -- audit_log has no per-row org
 * scoping today, so the platform-wide purge uses the longest
 * (`enterprise`) tier window as its default floor, never a shorter one,
 * so an org paying for a longer regulatory retention window never has
 * its audit trail purged out from under it early), calls down into
 * lib/audit-db.ts's purgeAuditLogRowsOlderThan (which owns the actual
 * hash-chain mechanics -- deleting rows and re-chaining the survivors so
 * verifyAuditChain still validates), and writes the compliance receipt
 * row this capability exists to produce: count deleted, the exact cutoff
 * timestamp, and the actor that ran it -- into a new,
 * platform_console.retention_purge_log table, on the SAME live
 * console-operational Postgres lib/audit-db.ts already owns (not a new
 * connection, not a new k8s resource kind).
 */
import type { Pool } from "pg";
import {
  getAuditDbPool,
  newRequestId,
  purgeAuditLogRowsOlderThan,
  writeAuditLogEntryAwaited,
  type AuditLogPurgeResult,
} from "@/lib/audit-db";
import { RETENTION_DEFAULT_DAYS } from "@/lib/backup-retention";
import type { ProjectTier } from "@/lib/tiers";
import { computeLegalHoldPurgeGuard } from "@/lib/legal-hold";

// The actor string every automated purge receipt is stamped with --
// distinguishable at a glance from a real human/service identifier
// (roleIdentifierFor's email/`"admin"` shapes, or an API-key-bound
// identifier), same "system:" prefix convention this repo's other
// automation-attributed audit rows already use for non-human actors
// (e.g. "castle-schedule-cronjob", "export-subscription-cronjob" in
// lib/scheduled-jobs.ts/app/api/*/route.ts) -- this one additionally
// carries the "system:" prefix so a compliance reviewer scanning
// retention_purge_log.actor can tell at a glance this was never a human
// action, without cross-referencing a separate CronJob-name allowlist.
export const RETENTION_PURGE_SYSTEM_ACTOR = "system:retention-purge";

/**
 * The platform-wide default retention window for platform_console.audit_log
 * -- no per-row org scoping exists on that table today, so this can't
 * simply look up one org's effective policy the way
 * lib/backup-retention.ts's effectiveRetentionDays does for a single
 * org's backups. Defaults to the `enterprise` tier's window
 * (`RETENTION_DEFAULT_DAYS.enterprise`, currently 365 days) -- the
 * LONGEST configured tier window, not the shortest -- so a platform
 * serving even one enterprise-tier org never purges audit history that
 * org's own regulatory retention requirement still needs, just because a
 * cron run used a shorter tier's default. A caller that knows the exact
 * window it wants (an operator-configured platform policy, or a specific
 * tier) should pass `retentionDays` explicitly instead of relying on
 * this fallback.
 */
export function defaultAuditRetentionDays(tier: ProjectTier = "enterprise"): number {
  return RETENTION_DEFAULT_DAYS[tier];
}

async function ensureRetentionPurgeLogTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.retention_purge_log (
      id             bigserial PRIMARY KEY,
      ran_at         timestamptz NOT NULL DEFAULT now(),
      cutoff         timestamptz NOT NULL,
      retention_days integer NOT NULL,
      deleted_count  integer NOT NULL,
      tombstone      text,
      actor          text NOT NULL
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS retention_purge_log_ran_at_idx
       ON platform_console.retention_purge_log (ran_at DESC)`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution
// cache convention as lib/audit-db.ts's own chainColumnsReady.
let purgeLogTableReady: Promise<void> | null = null;

async function resolveRetentionPurgeLogPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!purgeLogTableReady) {
    purgeLogTableReady = ensureRetentionPurgeLogTable(pool);
  }
  await purgeLogTableReady;
  return pool;
}

export interface RetentionPurgeReceipt {
  id: number;
  ranAt: string; // RFC3339
  cutoff: string; // RFC3339 -- rows with ts < cutoff were deleted
  retentionDays: number;
  deletedCount: number;
  tombstone: string | null;
  actor: string;
}

export type RetentionPurgeOutcome =
  | { ok: true; data: RetentionPurgeReceipt }
  | { ok: false; error: string };

function toReceipt(r: {
  id: string | number;
  ran_at: string;
  cutoff: string;
  retention_days: number;
  deleted_count: number;
  tombstone: string | null;
  actor: string;
}): RetentionPurgeReceipt {
  return {
    id: Number(r.id),
    ranAt: new Date(r.ran_at).toISOString(),
    cutoff: new Date(r.cutoff).toISOString(),
    retentionDays: Number(r.retention_days),
    deletedCount: Number(r.deleted_count),
    tombstone: r.tombstone,
    actor: r.actor,
  };
}

/**
 * The real, scheduled enforcement action: DELETEs every
 * platform_console.audit_log row older than `retentionDays`, re-chains
 * the hash sequence forward from the new oldest surviving row (see
 * lib/audit-db.ts's purgeAuditLogRowsOlderThan for the tombstone/re-chain
 * mechanics), and writes ONE receipt row into
 * platform_console.retention_purge_log recording the count deleted, the
 * exact cutoff, and `actor` (defaults to the fixed
 * RETENTION_PURGE_SYSTEM_ACTOR for the CronJob-triggered path; a caller
 * exercising this manually/on-demand may pass a real human/service actor
 * instead). The receipt is written even when `deletedCount` is 0 -- a
 * run that found nothing to purge is still real, auditable evidence the
 * schedule fired, not a silent no-op a compliance reviewer has no record
 * of.
 */
export async function purgeExpiredAuditRows(
  retentionDays: number,
  actor: string = RETENTION_PURGE_SYSTEM_ACTOR,
): Promise<RetentionPurgeOutcome> {
  if (!Number.isFinite(retentionDays) || retentionDays <= 0) {
    return { ok: false, error: "retentionDays must be a positive number" };
  }

  const pool = await resolveRetentionPurgeLogPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }

  // Legal Hold check -- BEFORE any DELETE is ever issued (see
  // lib/legal-hold.ts's header comment). A platform-wide hold refuses
  // this purge entirely; an org-scoped hold narrows it to exclude that
  // org's own tagged rows. Never advisory.
  const guard = await computeLegalHoldPurgeGuard();
  if (!guard.ok) {
    return { ok: false, error: guard.error };
  }

  if (guard.data.blockedEntirely) {
    const blockingHold = guard.data.activeHolds.find((h) => h.scope === "platform");
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/cron/retention-purge (blocked by legal hold)",
      status: 200,
      requestId: newRequestId(),
      legalHoldAction: "purge_blocked",
      ...(blockingHold ? { legalHoldId: blockingHold.holdId, legalHoldScope: blockingHold.scope } : {}),
    });
    return {
      ok: false,
      error:
        `retention purge refused: an active platform-wide legal hold (${blockingHold?.holdId ?? "unknown"}` +
        `, "${blockingHold?.name ?? "unnamed"}") is in force -- nothing was destroyed`,
    };
  }

  const cutoff = new Date(Date.now() - retentionDays * 24 * 60 * 60 * 1000);

  const purgeResult = await purgeAuditLogRowsOlderThan(cutoff, guard.data.excludeOrgIds);
  if (!purgeResult.ok) {
    return { ok: false, error: purgeResult.error };
  }
  const { deletedCount, cutoff: cutoffIso, tombstone }: AuditLogPurgeResult = purgeResult.data;

  if (guard.data.excludeOrgIds.length > 0) {
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/cron/retention-purge (legal-hold-excluded orgs=${guard.data.excludeOrgIds.join(",")})`,
      status: 200,
      requestId: newRequestId(),
      legalHoldAction: "purge_blocked",
      legalHoldScope: "org",
    });
  }

  try {
    const inserted = await pool.query<{
      id: string;
      ran_at: string;
      cutoff: string;
      retention_days: number;
      deleted_count: number;
      tombstone: string | null;
      actor: string;
    }>(
      `INSERT INTO platform_console.retention_purge_log
         (cutoff, retention_days, deleted_count, tombstone, actor)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, ran_at, cutoff, retention_days, deleted_count, tombstone, actor`,
      [cutoffIso, retentionDays, deletedCount, tombstone, actor],
    );
    return { ok: true, data: toReceipt(inserted.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Real, chronological read of past purge receipts -- the compliance
 * evidence trail a SOC2/GDPR auditor actually wants to see ("show me
 * every time this control fired"), not just the most recent run.
 */
export async function listRetentionPurgeReceipts(
  limit: number = 100,
): Promise<{ ok: true; data: RetentionPurgeReceipt[] } | { ok: false; error: string }> {
  const pool = await resolveRetentionPurgeLogPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT id, ran_at, cutoff, retention_days, deleted_count, tombstone, actor
       FROM platform_console.retention_purge_log
       ORDER BY ran_at DESC
       LIMIT $1`,
      [limit],
    );
    return { ok: true, data: result.rows.map(toReceipt) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
