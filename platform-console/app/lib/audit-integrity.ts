/**
 * Real, on-demand hash-chain integrity ATTESTATION for one org's slice of
 * `platform_console.audit_log` -- distinct from both:
 *
 *  - lib/audit-export.ts / GET /api/v1/audit-export (the SIEM export):
 *    streams the raw events for a forwarder to re-derive its own
 *    conclusions from. A Fortune-5 SOC2/forensic-readiness reviewer does
 *    not want the raw chain re-derive -- they want a computed verification
 *    RESULT they can drop straight into an audit workpaper.
 *  - lib/audit-db.ts's verifyAuditChain (the platform-wide control used by
 *    GET /api/audit/verify and inlined into /api/v1/audit-export's
 *    `chain_verified` field): walks the ENTIRE table across every org, and
 *    additionally checks prev_hash CONTINUITY between consecutive rows
 *    (row N's stored prev_hash must equal row N-1's stored row_hash).
 *    That continuity check is meaningless once the walk is filtered down
 *    to one org's rows: two audit_log rows adjacent in the ORG-SCOPED
 *    result set are almost never adjacent in the real, table-wide
 *    insertion order (every other org's rows sit between them), so row
 *    N's real prev_hash legitimately points at some OTHER org's row, not
 *    at row N-1 of this org's slice. Comparing them would report false
 *    breaks on every multi-tenant chain that has ever interleaved writes
 *    across orgs -- i.e. every real one.
 *
 * What THIS module verifies instead, per row, independently of every
 * other row: does the row's own stored `row_hash` equal
 * `computeRowHash(stored prev_hash, this row's own fields)`? That is
 * exactly the per-row tamper-evidence guarantee the hash chain was built
 * to provide (see lib/audit-db.ts's computeRowHash doc comment) -- ANY
 * post-insertion edit to request_id/ts/actor/method/path/status or any of
 * the optional committed fields (castleReceiptDigest, impersonation
 * actor-tagging, orgId, keyId/durationMs, SLA credit fields) changes the
 * recomputed digest and is caught here, org-scoped, with no dependency on
 * rows outside the org's own slice or on the platform-wide walk order.
 * What it deliberately does NOT catch (and the report result's shape
 * makes no claim otherwise): a whole row belonging to this org being
 * deleted out-of-band, or the org's rows being reordered relative to each
 * other without touching their own stored fields -- that class of
 * cross-row tampering is exactly what the platform-wide
 * lib/audit-db.ts#verifyAuditChain control (GET /api/audit/verify) exists
 * to catch, and remains the authoritative full-chain-continuity control.
 * This module answers a narrower, org-scoped question a tenant-facing
 * attestation can actually make good on: "every event this org's auditor
 * can see is exactly as it was written."
 *
 * Every call is a fresh, live re-derivation against the current table --
 * no caching, no persistence of the result. A stale cached "chain was
 * intact as of last Tuesday" answer is worse than useless to a forensic
 * reviewer asking "is it intact right now"; this recomputes every time,
 * matching the same "the control is the live computation, not a summary
 * of it" discipline lib/audit-db.ts's own verifyAuditChain doc comment
 * states for the platform-wide control.
 */
import { computeRowHash, getAuditDbPool, type AuditLogEntry } from "@/lib/audit-db";

export interface HashChainVerificationResult {
  verified: boolean;
  rowsChecked: number;
  /** RFC3339 `ts` of the first row whose stored row_hash does not match its
   * recomputed digest (or that has no hash-chain columns at all, i.e. was
   * written before the chain existed and never backfilled) -- `null` when
   * `verified` is true. */
  firstBreakAt: string | null;
}

export type HashChainVerificationOutcome =
  | { ok: true; data: HashChainVerificationResult }
  | { ok: false; error: string };

interface AuditIntegrityRow {
  id: string;
  request_id: string;
  ts: string;
  actor: string;
  method: string;
  path: string;
  status: number;
  prev_hash: string | null;
  row_hash: string | null;
  castle_receipt_digest: string | null;
  impersonated_by: string | null;
  impersonation_session_id: string | null;
  org_id: string | null;
  key_id: string | null;
  duration_ms: number | null;
  sla_credit_stripe_transaction_id: string | null;
  sla_credit_amount_cents: number | null;
  sla_credit_month: string | null;
}

/**
 * Real, live per-row hash-chain re-derivation over `orgId`'s slice of
 * `platform_console.audit_log`, optionally bounded to `[from, to]`
 * (RFC3339, both inclusive, matched against `ts` -- same bound semantics
 * as lib/audit-db.ts's queryAuditLog `from`/`to`). Walks rows oldest
 * first (`ORDER BY id ASC`, the real hash-chain insertion order) and
 * stops at the first row whose recomputed digest disagrees with the
 * stored one, reporting that row's own timestamp as `firstBreakAt` --
 * every row up to and including the break is counted in `rowsChecked`,
 * matching how a forensic reviewer reads "we checked N rows and the
 * break was at row N" as one fact, not two independent counters that
 * could silently disagree.
 */
export async function verifyHashChain(
  orgId: string,
  from?: string,
  to?: string,
): Promise<HashChainVerificationOutcome> {
  const pool = await getAuditDbPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }

  const conditions: string[] = ["org_id = $1"];
  const values: unknown[] = [orgId];
  if (from) {
    values.push(from);
    conditions.push(`ts >= $${values.length}`);
  }
  if (to) {
    values.push(to);
    conditions.push(`ts <= $${values.length}`);
  }
  const where = `WHERE ${conditions.join(" AND ")}`;

  try {
    const result = await pool.query<AuditIntegrityRow>(
      `SELECT id, request_id, ts, actor, method, path, status, prev_hash, row_hash, castle_receipt_digest,
              impersonated_by, impersonation_session_id, org_id, key_id, duration_ms,
              sla_credit_stripe_transaction_id, sla_credit_amount_cents, sla_credit_month
       FROM platform_console.audit_log
       ${where}
       ORDER BY id ASC`,
      values,
    );

    let rowsChecked = 0;
    let firstBreakAt: string | null = null;

    for (const r of result.rows) {
      rowsChecked += 1;
      const rowTs = new Date(r.ts).toISOString();

      // A row written before the hash chain existed and never backfilled
      // (see lib/audit-db.ts's backfillAuditLogChain) has no prev_hash/
      // row_hash to verify against -- it cannot be attested as tamper-
      // evident, so it counts as the break rather than being silently
      // skipped.
      if (r.prev_hash === null || r.row_hash === null) {
        firstBreakAt = rowTs;
        break;
      }

      const entry: AuditLogEntry = {
        requestId: r.request_id,
        timestamp: rowTs,
        actor: r.actor,
        method: r.method,
        path: r.path,
        status: Number(r.status),
        ...(r.castle_receipt_digest ? { castleReceiptDigest: r.castle_receipt_digest } : {}),
        ...(r.impersonated_by ? { impersonatedBy: r.impersonated_by } : {}),
        ...(r.impersonation_session_id
          ? { impersonationSessionId: r.impersonation_session_id }
          : {}),
        ...(r.org_id ? { orgId: r.org_id } : {}),
        ...(r.key_id ? { keyId: r.key_id } : {}),
        ...(r.duration_ms !== null ? { durationMs: r.duration_ms } : {}),
        ...(r.sla_credit_stripe_transaction_id
          ? { slaCreditStripeTransactionId: r.sla_credit_stripe_transaction_id }
          : {}),
        ...(r.sla_credit_amount_cents !== null
          ? { slaCreditAmountCents: r.sla_credit_amount_cents }
          : {}),
        ...(r.sla_credit_month ? { slaCreditMonth: r.sla_credit_month } : {}),
      };

      const recomputed = computeRowHash(r.prev_hash, entry);
      if (recomputed !== r.row_hash) {
        firstBreakAt = rowTs;
        break;
      }
    }

    return {
      ok: true,
      data: {
        verified: firstBreakAt === null,
        rowsChecked,
        firstBreakAt,
      },
    };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
