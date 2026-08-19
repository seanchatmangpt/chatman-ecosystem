/**
 * Real Partner/Reseller Referral-Credit Ledger -- the missing control a
 * Fortune 5 buyer's procurement/channel team asks for the moment a
 * purchase is routed through a systems-integrator or reseller
 * relationship: "show us, in the platform itself, who gets credited for
 * this deal and what that resolved to on our bill" instead of an
 * out-of-band spreadsheet a partner-ops person maintains by hand. No
 * referral/partner/reseller concept existed anywhere in this repo before
 * this module.
 *
 * Storage: a dedicated `platform_console.referral_ledger` table on the
 * exact same live demo-project Postgres lib/audit-db.ts and
 * lib/impersonation.ts already treat as this console's own operational
 * store -- reuses that module's single-flight, self-healing
 * `getAuditDbPool()` rather than standing up a second connection pool,
 * and follows migrations.ts's/impersonation.ts's own
 * `CREATE TABLE IF NOT EXISTS` self-bootstrap convention.
 *
 * Two real actions:
 *   - `recordReferralCredit` -- platform-admin only. Writes one ledger
 *     row (accrued, not yet applied) plus one entry into the SAME
 *     hash-chained `platform_console.audit_log` every other privileged
 *     mutation in this app lands in (via lib/audit-db.ts's
 *     writeAuditLogEntry), so a referral credit's existence is provable
 *     the same way an impersonation session or a billing change already
 *     is.
 *   - `applyReferralCredit` -- calls Stripe's real Customer Balance API
 *     (`stripe.customers.createBalanceTransaction`, the same "apply a
 *     credit against whatever this org's next invoice will be" primitive
 *     lib/stripe-billing.ts's own real (test-mode) Stripe wiring already
 *     uses elsewhere in this codebase) against the referred org's own
 *     `stripeCustomerId` (resolved live via lib/stripe-billing.ts's
 *     `getStoredSubscription`, never a new customer-lookup path), then
 *     marks the row `appliedAt` with the real Stripe balance-transaction
 *     id. A negative `amount` to Stripe's API is a credit to the
 *     customer -- this module always sends `-creditAmountCents`, so a
 *     ledger row can never accidentally become a debit.
 *
 * Fail-closed, same convention as every other lib/*.ts module here:
 * off-cluster / no audit DB pool -> `{ok:false}` naming that; no
 * STRIPE_SECRET_KEY configured -> `{ok:false}` naming that, row stays
 * un-applied rather than silently marked applied.
 */
import type { Pool } from "pg";
import { getAuditDbPool, newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getOrg } from "@/lib/orgs";
import { getStoredSubscription, getStripeClient } from "@/lib/stripe-billing";

export type ReferralLedgerOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

export interface ReferralCredit {
  id: string;
  referrerOrgId: string | null;
  referrerPartnerId: string | null;
  referredOrgId: string;
  creditAmountCents: number;
  currency: string; // lowercase ISO 4217, same convention as lib/stripe-billing.ts
  reason: string;
  createdAt: string; // RFC3339
  appliedAt: string | null; // RFC3339, set once the real Stripe balance transaction lands
  stripeBalanceTransactionId: string | null;
}

async function ensureReferralLedgerTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.referral_ledger (
      id                            text PRIMARY KEY,
      referrer_org_id                text,
      referrer_partner_id            text,
      referred_org_id                text NOT NULL,
      credit_amount_cents            bigint NOT NULL,
      currency                       text NOT NULL,
      reason                         text NOT NULL,
      created_at                     timestamptz NOT NULL DEFAULT now(),
      applied_at                     timestamptz,
      stripe_balance_transaction_id  text,
      CONSTRAINT referral_ledger_referrer_chk
        CHECK (
          (referrer_org_id IS NOT NULL AND referrer_partner_id IS NULL) OR
          (referrer_org_id IS NULL AND referrer_partner_id IS NOT NULL)
        )
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS referral_ledger_referred_org_id_idx
       ON platform_console.referral_ledger (referred_org_id)`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution cache
// convention as impersonation.ts's tableReady / active-sessions.ts's own.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureReferralLedgerTable(pool);
  }
  await tableReady;
  return pool;
}

const SELECT_COLUMNS =
  "id, referrer_org_id, referrer_partner_id, referred_org_id, credit_amount_cents, currency, reason, created_at, applied_at, stripe_balance_transaction_id";

function toReferralCredit(r: Record<string, unknown>): ReferralCredit {
  return {
    id: r.id as string,
    referrerOrgId: (r.referrer_org_id as string | null) ?? null,
    referrerPartnerId: (r.referrer_partner_id as string | null) ?? null,
    referredOrgId: r.referred_org_id as string,
    creditAmountCents: Number(r.credit_amount_cents),
    currency: r.currency as string,
    reason: r.reason as string,
    createdAt: new Date(r.created_at as string).toISOString(),
    appliedAt: r.applied_at ? new Date(r.applied_at as string).toISOString() : null,
    stripeBalanceTransactionId: (r.stripe_balance_transaction_id as string | null) ?? null,
  };
}

/**
 * Records a new referral credit -- platform-admin only (enforced by the
 * caller, app/api/admin/referrals/route.ts's POST, via
 * lib/authz.ts's requirePlatformAdmin, same boundary
 * app/api/support/impersonate/route.ts already uses). Exactly one of
 * `referrerOrgId` (an existing org acting as the referring reseller/SI)
 * or `referrerPartnerId` (a free-text partner identifier for a reseller
 * with no org of its own in this console) must be set -- enforced both
 * here and by the table's own CHECK constraint, so a row can never be
 * ambiguous about who gets the credit.
 */
export async function recordReferralCredit(params: {
  actor: string;
  referrerOrgId?: string | null;
  referrerPartnerId?: string | null;
  referredOrgId: string;
  creditAmountCents: number;
  currency: string;
  reason: string;
}): Promise<ReferralLedgerOutcome<ReferralCredit>> {
  const referrerOrgId = params.referrerOrgId?.trim() || null;
  const referrerPartnerId = params.referrerPartnerId?.trim() || null;
  const referredOrgId = params.referredOrgId.trim();
  const reason = params.reason.trim();
  const currency = params.currency.trim().toLowerCase();

  if ((referrerOrgId && referrerPartnerId) || (!referrerOrgId && !referrerPartnerId)) {
    return {
      ok: false,
      error: "exactly one of referrerOrgId or referrerPartnerId is required",
    };
  }
  if (!referredOrgId) {
    return { ok: false, error: "referredOrgId is required" };
  }
  if (!Number.isInteger(params.creditAmountCents) || params.creditAmountCents <= 0) {
    return { ok: false, error: "creditAmountCents must be a positive integer" };
  }
  if (!currency) {
    return { ok: false, error: "currency is required" };
  }
  if (!reason) {
    return { ok: false, error: "reason is required" };
  }

  const orgResult = await getOrg(referredOrgId);
  if (!orgResult.ok) return { ok: false, error: orgResult.error };
  if (!orgResult.data) return { ok: false, error: `referred org '${referredOrgId}' not found` };

  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "referral ledger store not configured or unreachable" };
  }

  const id = globalThis.crypto.randomUUID();
  try {
    const result = await pool.query(
      `INSERT INTO platform_console.referral_ledger
         (id, referrer_org_id, referrer_partner_id, referred_org_id, credit_amount_cents, currency, reason)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING ${SELECT_COLUMNS}`,
      [id, referrerOrgId, referrerPartnerId, referredOrgId, params.creditAmountCents, currency, reason],
    );
    const credit = toReferralCredit(result.rows[0]);
    writeAuditLogEntry({
      requestId: newRequestId(),
      timestamp: new Date().toISOString(),
      actor: params.actor,
      method: "POST",
      path: `/referral-ledger/record/${credit.id}`,
      status: 200,
    });
    return { ok: true, data: credit };
  } catch (e) {
    return { ok: false, error: `referral ledger insert failed: ${(e as Error).message}` };
  }
}

/**
 * Applies an already-recorded, not-yet-applied referral credit against
 * the referred org's real Stripe customer balance. Requires that org to
 * already have a stored Stripe subscription/customer on file (the exact
 * same `getStoredSubscription` lib/stripe-billing.ts's own billing pages
 * already use) -- no new billing-account dependency, per spec. A row
 * that is already applied is returned as-is (idempotent second call),
 * never double-credited.
 */
export async function applyReferralCredit(
  id: string,
  actor: string,
): Promise<ReferralLedgerOutcome<ReferralCredit>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "referral ledger store not configured or unreachable" };
  }

  const existingResult = await pool.query(`SELECT ${SELECT_COLUMNS} FROM platform_console.referral_ledger WHERE id = $1`, [id]);
  if (existingResult.rows.length === 0) {
    return { ok: false, error: `referral credit '${id}' not found` };
  }
  const existing = toReferralCredit(existingResult.rows[0]);
  if (existing.appliedAt) {
    return { ok: true, data: existing };
  }

  const stripe = getStripeClient();
  if (!stripe) return { ok: false, error: "STRIPE_SECRET_KEY not configured" };

  const orgResult = await getOrg(existing.referredOrgId);
  if (!orgResult.ok) return { ok: false, error: orgResult.error };
  if (!orgResult.data) return { ok: false, error: `referred org '${existing.referredOrgId}' not found` };

  const subResult = await getStoredSubscription(orgResult.data.namespace);
  if (!subResult.ok) return { ok: false, error: subResult.error };
  const customerId = subResult.data?.stripeCustomerId;
  if (!customerId) {
    return {
      ok: false,
      error: `org '${existing.referredOrgId}' has no Stripe customer on file yet -- cannot apply credit`,
    };
  }

  try {
    // Negative amount = credit to the customer's balance (Stripe's own
    // sign convention for CustomerBalanceTransaction.amount) -- reduces
    // what that org owes on its next invoice by exactly
    // creditAmountCents, the real (test-mode) counterpart of the
    // "$X off your next invoice" a channel deal promises.
    const balanceTx = await stripe.customers.createBalanceTransaction(customerId, {
      amount: -existing.creditAmountCents,
      currency: existing.currency,
      description: `Referral credit: ${existing.reason}`,
    });

    const updateResult = await pool.query(
      `UPDATE platform_console.referral_ledger
         SET applied_at = now(), stripe_balance_transaction_id = $2
       WHERE id = $1
       RETURNING ${SELECT_COLUMNS}`,
      [id, balanceTx.id],
    );
    const applied = toReferralCredit(updateResult.rows[0]);
    writeAuditLogEntry({
      requestId: newRequestId(),
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/referral-ledger/apply/${id}`,
      status: 200,
    });
    return { ok: true, data: applied };
  } catch (e) {
    return { ok: false, error: `Stripe balance transaction failed: ${(e as Error).message}` };
  }
}

/**
 * Lists every referral credit -- accrued or applied -- where the given
 * org is the one that WAS referred (i.e. the org whose subscription the
 * credit reduces). Newest first. Used by
 * app/api/orgs/[id]/referral/route.ts's GET, gated there to that org's
 * own members (viewer and up) via lib/authz.ts's requireRoleIn -- same
 * "reading your own org's own record is not a privileged action"
 * convention as impersonation-log's GET.
 */
export async function listReferralCreditsForOrg(
  orgId: string,
): Promise<ReferralLedgerOutcome<ReferralCredit[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "referral ledger store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.referral_ledger
       WHERE referred_org_id = $1
       ORDER BY created_at DESC`,
      [orgId],
    );
    return { ok: true, data: result.rows.map(toReferralCredit) };
  } catch (e) {
    return { ok: false, error: `referral ledger query failed: ${(e as Error).message}` };
  }
}

/**
 * Platform-admin-facing listing across every org -- backs
 * app/api/admin/referrals/route.ts's own read path if/when needed and
 * gives the admin route something real to return alongside the record
 * it just wrote. Newest first, unbounded (same convention as
 * lib/impersonation.ts's listImpersonationSessionsForOrg -- this
 * console's ledgers are not yet large enough to need pagination).
 */
export async function listAllReferralCredits(): Promise<ReferralLedgerOutcome<ReferralCredit[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "referral ledger store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.referral_ledger ORDER BY created_at DESC`,
    );
    return { ok: true, data: result.rows.map(toReferralCredit) };
  } catch (e) {
    return { ok: false, error: `referral ledger query failed: ${(e as Error).message}` };
  }
}
