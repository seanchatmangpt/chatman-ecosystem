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
 * One row per LOGICAL delivery (one event to one subscription), not one
 * row per attempt -- the row is mutated in place as attempts happen
 * (attempt_number increments, http_status/error/duration_ms reflect the
 * most recent attempt), with `next_attempt_at` as the retry queue's own
 * due-time column. This is what makes GET .../deliveries a real, bounded
 * "current state of every delivery" history rather than an
 * ever-multiplying attempt log, while `attempt_number` and `status`
 * still let a viewer see exactly how many times a delivery was tried and
 * whether it is still in flight, delivered, or dead-lettered.
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

async function ensureWebhookDeliveriesTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
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
 * Inserts a fresh delivery row for attempt 1 (first-ever attempt for a
 * deliveryId), or updates the existing row in place for attempt 2+
 * (retries/replays). Never throws past the caller -- a failed persist is
 * logged to stderr and swallowed, same fail-open convention
 * lib/audit-db.ts's writeAuditLogEntry uses, so a DB hiccup never blocks
 * or fails the actual webhook delivery this describes.
 */
export async function recordDeliveryAttempt(outcome: AttemptOutcome): Promise<void> {
  const pool = await resolveReadyPool();
  if (!pool) return; // not configured / cluster DB unreachable -- console log is still the real record for this environment
  try {
    if (outcome.ok) {
      await pool.query(
        `INSERT INTO platform_console.webhook_deliveries
           (delivery_id, subscription_id, event_type, url, body, status, http_status, error,
            duration_ms, attempt_number, max_attempts, next_attempt_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, 'delivered', $6, NULL, $7, $8, $9, NULL, now())
         ON CONFLICT (delivery_id) DO UPDATE SET
           status = 'delivered', http_status = EXCLUDED.http_status, error = NULL,
           duration_ms = EXCLUDED.duration_ms, attempt_number = EXCLUDED.attempt_number,
           next_attempt_at = NULL, updated_at = now()`,
        [
          outcome.deliveryId,
          outcome.subscriptionId,
          outcome.eventType,
          outcome.url,
          outcome.body,
          outcome.httpStatus,
          outcome.durationMs,
          outcome.attemptNumber,
          MAX_DELIVERY_ATTEMPTS,
        ],
      );
      return;
    }

    const { status, nextAttemptAt } = nextStateAfterFailure(outcome.attemptNumber);
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
        outcome.error,
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
