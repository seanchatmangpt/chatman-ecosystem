/**
 * Real webhook delivery reliability: retry-with-backoff + dead-letter
 * queue + persisted delivery history -- the gap lib/webhooks.ts's own
 * header comment names (it models itself on Stripe/GitHub/Twilio, which
 * all treat retry+DLQ+delivery log as table stakes) but never actually
 * closed: deliverWebhookEvent used to make exactly one POST attempt with
 * a try/catch that only logged to console, so a customer's integration
 * team had no way to see which deliveries failed or replay them.
 *
 * Deliberately a separate module from lib/webhooks.ts, same split
 * lib/audit-db.ts keeps from lib/audit-log.ts: this module owns the real
 * Postgres persistence, lib/webhooks.ts keeps owning HMAC signing and the
 * actual `fetch` POST. Reuses the exact same pg `Pool` lib/audit-db.ts
 * already resolves against the live demo-project Postgres
 * (`getAuditDbPool`) -- no second cluster credential path, no second
 * connection-discovery flow, same "off-cluster / DB unreachable fails
 * closed, never throws past a caller" convention as every other
 * audit-db.ts reader.
 *
 * The record of truth is `platform_console.webhook_delivery_attempts`:
 * one IMMUTABLE row per attempt, pure INSERT, never UPDATE, never
 * overwritten -- attempt 1's http_status/error/duration_ms survives
 * forever even after attempt 2, 3, ... run. This is what a SOC2 CC7 /
 * PCI DSS logging review actually asks for: a full, tamper-evident,
 * attempt-by-attempt forensic trail for every outbound webhook, not just
 * whatever the most recent attempt happened to be.
 *
 * Every attempt this module records originates from this platform's
 * published static outbound IP ranges -- see lib/egress-ips.ts
 * (`PLATFORM_EGRESS_CIDRS`), surfaced on the public trust page
 * (app/api/trust/route.ts) and on GET app/api/webhooks/route.ts so a
 * customer's InfoSec team can whitelist exactly the source IPs these
 * deliveries come from in their own inbound firewall.
 *

 * `platform_console.webhook_deliveries` remains, but is now explicitly a
 * DERIVED / SUMMARY PROJECTION of that attempt log, not the record of
 * truth -- one row per LOGICAL delivery (one event to one subscription),
 * upserted in place purely as a cheap "current status" read (used by the
 * retry poller's due-queue and the subscription-level delivery list).
 * Every field on it is reconstructible at any time by
 * `SELECT ... FROM webhook_delivery_attempts WHERE delivery_id = $1
 * ORDER BY attempt_number DESC LIMIT 1` -- it is a materialized
 * convenience, never the source GET .../attempts reads from.
 */
import { Pool } from "pg";
import { getAuditDbPool } from "@/lib/audit-db";

export type WebhookDeliveryStatus = "delivered" | "pending_retry" | "dead_letter";

/** Exponential backoff schedule: index 0 is the delay applied after
 * attempt 1 fails (before attempt 2), index 3 after attempt 4 fails
 * (before attempt 5, the final one) -- 1m, 5m, 30m, 2h, matching the
 * spec exactly. MAX_ATTEMPTS caps total attempts at 5; a 5th failed
 * attempt has no further schedule entry and is dead-lettered instead. */
const BACKOFF_SCHEDULE_MS = [60_000, 5 * 60_000, 30 * 60_000, 2 * 60 * 60_000];
export const MAX_DELIVERY_ATTEMPTS = BACKOFF_SCHEDULE_MS.length + 1; // 5

export interface WebhookDeliveryRow {
  deliveryId: string;
  subscriptionId: string;
  eventType: string;
  url: string;
  status: WebhookDeliveryStatus;
  httpStatus: number | null;
  error: string | null;
  durationMs: number | null;
  attemptNumber: number;
  maxAttempts: number;
  nextAttemptAt: string | null; // RFC3339, null once delivered or dead-lettered
  createdAt: string; // RFC3339
  updatedAt: string; // RFC3339
}

/** Everything needed to retry or replay a delivery without re-deriving
 * the event -- the exact request body bytes are persisted so a retry or
 * a manual replay sends byte-identical content to the original attempt
 * (the signature is recomputed from these bytes against the
 * subscription's current secret at retry/replay time, since the secret
 * itself is never persisted here). */
export interface WebhookDeliveryRecord extends WebhookDeliveryRow {
  body: string;
}

/** One immutable row per delivery attempt -- the actual record of
 * truth. `attempt_id` is a plain serial surrogate key (no natural
 * uniqueness requirement is asserted across the pair, since a caller
 * could in principle log the same attempt_number twice under retry
 * races; the forensic trail should keep both rather than silently drop
 * one), with `(delivery_id, attempt_number)` indexed for ordered
 * per-delivery reads. There is deliberately no `ON CONFLICT` clause
 * anywhere this table is written -- every write is a pure INSERT. */
export interface WebhookDeliveryAttemptRow {
  attemptId: number;
  deliveryId: string;
  subscriptionId: string;
  eventType: string;
  url: string;
  status: WebhookDeliveryStatus;
  httpStatus: number | null;
  error: string | null;
  durationMs: number | null;
  attemptNumber: number;
  createdAt: string; // RFC3339
}

async function ensureWebhookDeliveriesTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.webhook_delivery_attempts (
      attempt_id       bigserial PRIMARY KEY,
      delivery_id      text NOT NULL,
      subscription_id  text NOT NULL,
      event_type       text NOT NULL,
      url              text NOT NULL,
      status           text NOT NULL,
      http_status      integer,
      error            text,
      duration_ms      integer,
      attempt_number   integer NOT NULL,
      created_at       timestamptz NOT NULL DEFAULT now()
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS webhook_delivery_attempts_delivery_idx
       ON platform_console.webhook_delivery_attempts (delivery_id, attempt_number)`,
  );
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.webhook_deliveries (
      id               bigserial PRIMARY KEY,
      delivery_id      text NOT NULL UNIQUE,
      subscription_id  text NOT NULL,
      event_type       text NOT NULL,
      url              text NOT NULL,
      body             text NOT NULL,
      status           text NOT NULL,
      http_status      integer,
      error            text,
      duration_ms      integer,
      attempt_number   integer NOT NULL DEFAULT 1,
      max_attempts     integer NOT NULL DEFAULT ${MAX_DELIVERY_ATTEMPTS},
      next_attempt_at  timestamptz,
      created_at       timestamptz NOT NULL DEFAULT now(),
      updated_at       timestamptz NOT NULL DEFAULT now()
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS webhook_deliveries_subscription_idx
       ON platform_console.webhook_deliveries (subscription_id, created_at DESC)`,
  );
  await pool.query(
    `CREATE INDEX IF NOT EXISTS webhook_deliveries_due_retry_idx
       ON platform_console.webhook_deliveries (status, next_attempt_at)
       WHERE status = 'pending_retry'`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution
// cache convention as audit-db.ts's chainColumnsReady / active-sessions.ts's
// tableReady.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureWebhookDeliveriesTable(pool);
  }
  await tableReady;
  return pool;
}

function toRow(r: Record<string, unknown>): WebhookDeliveryRow {
  return {
    deliveryId: r.delivery_id as string,
    subscriptionId: r.subscription_id as string,
    eventType: r.event_type as string,
    url: r.url as string,
    status: r.status as WebhookDeliveryStatus,
    httpStatus: r.http_status === null || r.http_status === undefined ? null : Number(r.http_status),
    error: (r.error as string | null) ?? null,
    durationMs:
      r.duration_ms === null || r.duration_ms === undefined ? null : Number(r.duration_ms),
    attemptNumber: Number(r.attempt_number),
    maxAttempts: Number(r.max_attempts),
    nextAttemptAt: r.next_attempt_at ? new Date(r.next_attempt_at as string).toISOString() : null,
    createdAt: new Date(r.created_at as string).toISOString(),
    updatedAt: new Date(r.updated_at as string).toISOString(),
  };
}

function toRecord(r: Record<string, unknown>): WebhookDeliveryRecord {
  return { ...toRow(r), body: r.body as string };
}

function toAttemptRow(r: Record<string, unknown>): WebhookDeliveryAttemptRow {
  return {
    attemptId: Number(r.attempt_id),
    deliveryId: r.delivery_id as string,
    subscriptionId: r.subscription_id as string,
    eventType: r.event_type as string,
    url: r.url as string,
    status: r.status as WebhookDeliveryStatus,
    httpStatus: r.http_status === null || r.http_status === undefined ? null : Number(r.http_status),
    error: (r.error as string | null) ?? null,
    durationMs:
      r.duration_ms === null || r.duration_ms === undefined ? null : Number(r.duration_ms),
    attemptNumber: Number(r.attempt_number),
    createdAt: new Date(r.created_at as string).toISOString(),
  };
}

/** Given the attempt number that just FAILED, returns the next status +
 * retry time: `pending_retry` with a real `nextAttemptAt` while under
 * MAX_DELIVERY_ATTEMPTS, `dead_letter` (no further retry) once the
 * schedule is exhausted. */
function nextStateAfterFailure(
  attemptNumber: number,
): { status: WebhookDeliveryStatus; nextAttemptAt: string | null } {
  const delay = BACKOFF_SCHEDULE_MS[attemptNumber - 1];
  if (delay === undefined) {
    return { status: "dead_letter", nextAttemptAt: null };
  }
  return { status: "pending_retry", nextAttemptAt: new Date(Date.now() + delay).toISOString() };
}

export interface AttemptOutcome {
  deliveryId: string;
  subscriptionId: string;
  eventType: string;
  url: string;
  body: string;
  ok: boolean;
  httpStatus: number | null;
  error: string | null;
  durationMs: number;
  attemptNumber: number;
}

/**
 * Records one delivery attempt. Two writes happen, in order:
 *
 *  1. A pure INSERT (no ON CONFLICT, ever) into
 *     `webhook_delivery_attempts` -- the immutable forensic row for
 *     THIS attempt. Attempt 1's http_status/error/duration_ms is never
 *     touched again once attempt 2 is recorded; both rows persist side
 *     by side forever.
 *  2. An upsert of `webhook_deliveries`, the derived "current status"
 *     projection -- purely a cheap-read cache of the latest attempt, kept
 *     for the existing due-retry poller query and the per-subscription
 *     delivery list. If this row were dropped entirely, it could be
 *     rebuilt in full from `webhook_delivery_attempts` via
 *     `DISTINCT ON (delivery_id) ... ORDER BY delivery_id, attempt_number DESC`.
 *
 * Never throws past the caller -- a failed persist is logged to stderr
 * and swallowed, same fail-open convention lib/audit-db.ts's
 * writeAuditLogEntry uses, so a DB hiccup never blocks or fails the
 * actual webhook delivery this describes.
 */
export async function recordDeliveryAttempt(outcome: AttemptOutcome): Promise<void> {
  const pool = await resolveReadyPool();
  if (!pool) return; // not configured / cluster DB unreachable -- console log is still the real record for this environment

  const status: WebhookDeliveryStatus = outcome.ok
    ? "delivered"
    : nextStateAfterFailure(outcome.attemptNumber).status;
  const nextAttemptAt = outcome.ok ? null : nextStateAfterFailure(outcome.attemptNumber).nextAttemptAt;
  const error = outcome.ok ? null : outcome.error;

  try {
    // (1) Immutable attempt log -- pure INSERT, never UPDATE.
    await pool.query(
      `INSERT INTO platform_console.webhook_delivery_attempts
         (delivery_id, subscription_id, event_type, url, status, http_status, error,
          duration_ms, attempt_number)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [
        outcome.deliveryId,
        outcome.subscriptionId,
        outcome.eventType,
        outcome.url,
        status,
        outcome.httpStatus,
        error,
        outcome.durationMs,
        outcome.attemptNumber,
      ],
    );
  } catch (err) {
    console.error(
      JSON.stringify({
        webhookDeliveryAttemptPersistError: err instanceof Error ? err.message : String(err),
        deliveryId: outcome.deliveryId,
      }),
    );
  }

  try {
    // (2) Derived current-status projection -- upsert is fine here, this
    // is explicitly documented as NOT the record of truth.
    await pool.query(
      `INSERT INTO platform_console.webhook_deliveries
         (delivery_id, subscription_id, event_type, url, body, status, http_status, error,
          duration_ms, attempt_number, max_attempts, next_attempt_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, now())
       ON CONFLICT (delivery_id) DO UPDATE SET
         status = EXCLUDED.status, http_status = EXCLUDED.http_status, error = EXCLUDED.error,
         duration_ms = EXCLUDED.duration_ms, attempt_number = EXCLUDED.attempt_number,
         next_attempt_at = EXCLUDED.next_attempt_at, updated_at = now()`,
      [
        outcome.deliveryId,
        outcome.subscriptionId,
        outcome.eventType,
        outcome.url,
        outcome.body,
        status,
        outcome.httpStatus,
        error,
        outcome.durationMs,
        outcome.attemptNumber,
        MAX_DELIVERY_ATTEMPTS,
        nextAttemptAt,
      ],
    );
  } catch (err) {
    console.error(
      JSON.stringify({
        webhookDeliveryPersistError: err instanceof Error ? err.message : String(err),
        deliveryId: outcome.deliveryId,
      }),
    );
  }
}

/** Real delivery history for one subscription, newest first -- backs
 * GET /api/webhooks/[id]/deliveries. */
export type WebhookDeliveriesOutcome =
  | { ok: true; data: WebhookDeliveryRow[] }
  | { ok: false; error: string };

export async function listDeliveriesForSubscription(
  subscriptionId: string,
): Promise<WebhookDeliveriesOutcome> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return {
      ok: false,
      error: "webhook delivery log database not configured or unreachable",
    };
  }
  try {
    const result = await pool.query(
      `SELECT delivery_id, subscription_id, event_type, url, status, http_status, error,
              duration_ms, attempt_number, max_attempts, next_attempt_at, created_at, updated_at
       FROM platform_console.webhook_deliveries
       WHERE subscription_id = $1
       ORDER BY created_at DESC
       LIMIT 200`,
      [subscriptionId],
    );
    return { ok: true, data: result.rows.map(toRow) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Every delivery currently due for an automatic retry
 * (`status = 'pending_retry' AND next_attempt_at <= now()`) -- backs
 * lib/webhook-poller.ts's tick, so retries are driven by the exact same
 * 10s poll loop as every other real trigger in this console, not a
 * separate queue/cron system. */
export type WebhookDeliveryRecordsOutcome =
  | { ok: true; data: WebhookDeliveryRecord[] }
  | { ok: false; error: string };

export async function listDueRetries(): Promise<WebhookDeliveryRecordsOutcome> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "webhook delivery log database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT delivery_id, subscription_id, event_type, url, body, status, http_status, error,
              duration_ms, attempt_number, max_attempts, next_attempt_at, created_at, updated_at
       FROM platform_console.webhook_deliveries
       WHERE status = 'pending_retry' AND next_attempt_at <= now()
       ORDER BY next_attempt_at ASC
       LIMIT 100`,
    );
    return { ok: true, data: result.rows.map(toRecord) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** One delivery record by id, including its stored body -- needed by
 * POST /api/webhooks/deliveries/[deliveryId]/replay to redeliver the
 * exact original bytes. Only a `dead_letter` row is eligible for replay
 * (checked by the caller); this read itself has no status restriction so
 * a caller can distinguish "not dead-lettered" from "not found". */
export type WebhookDeliveryRecordOutcome =
  | { ok: true; data: WebhookDeliveryRecord | null }
  | { ok: false; error: string };

export async function getDeliveryRecord(deliveryId: string): Promise<WebhookDeliveryRecordOutcome> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "webhook delivery log database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT delivery_id, subscription_id, event_type, url, body, status, http_status, error,
              duration_ms, attempt_number, max_attempts, next_attempt_at, created_at, updated_at
       FROM platform_console.webhook_deliveries
       WHERE delivery_id = $1`,
      [deliveryId],
    );
    return { ok: true, data: result.rows[0] ? toRecord(result.rows[0]) : null };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Full, ordered, never-overwritten attempt history for one delivery --
 * the actual forensic record a SOC2/PCI logging reviewer wants, backing
 * GET /api/webhooks/deliveries/[deliveryId]/attempts. Reads directly
 * from `webhook_delivery_attempts`, oldest attempt first, so a viewer
 * can see exactly how the delivery evolved attempt by attempt (including
 * every earlier failure's http_status/error/duration_ms, which the
 * `webhook_deliveries` projection alone can no longer show once a later
 * attempt has overwritten its own row). */
export type WebhookDeliveryAttemptsOutcome =
  | { ok: true; data: WebhookDeliveryAttemptRow[] }
  | { ok: false; error: string };

export async function listAttemptsForDelivery(
  deliveryId: string,
): Promise<WebhookDeliveryAttemptsOutcome> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "webhook delivery log database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT attempt_id, delivery_id, subscription_id, event_type, url, status, http_status,
              error, duration_ms, attempt_number, created_at
       FROM platform_console.webhook_delivery_attempts
       WHERE delivery_id = $1
       ORDER BY attempt_number ASC, attempt_id ASC`,
      [deliveryId],
    );
    return { ok: true, data: result.rows.map(toAttemptRow) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
