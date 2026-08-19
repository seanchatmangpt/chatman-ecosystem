/**
 * Real Support-Ticket SLA Timer + Breach Escalation -- turns the already-
 * priced `SlaTier` (lib/tiers.ts's `standard`/`priority`/`enterprise-247`,
 * with real `slaResponseTimeHours` of 24/4/1 set per org via
 * `PUT /api/orgs/[id]/sla`) into an operational, auditable product
 * instead of a static label on the org record. Before this module,
 * nothing in this console started a clock against that number or
 * tracked whether a real response happened -- an Enterprise buyer paying
 * for a 1-hour response commitment had no way to see it measured, let
 * alone escalated on breach.
 *
 * Storage: a dedicated `platform_console.support_tickets` table on the
 * same live demo-project Postgres lib/audit-db.ts already treats as this
 * console's own operational store -- reuses that module's exact
 * single-flight, self-healing pool (`getAuditDbPool()`) rather than
 * standing up a second connection pool, and follows
 * lib/active-sessions.ts's own `CREATE TABLE IF NOT EXISTS`
 * self-bootstrap convention (idempotent on every pool resolution, so
 * this table exists the first time this module runs against a fresh
 * cluster, no manual `psql` step required).
 *
 * `priority` is captured on the ticket AT CREATION TIME from the org's
 * live SLA tier (via `getOrgSla`, the exact same lookup
 * `PUT /api/orgs/[id]/sla` already backs) -- a later SLA re-tier never
 * silently rewrites the clock on a ticket already in flight, the same
 * "computed once, from a fixed lookup table, never re-derived out from
 * under an in-flight record" discipline lib/orgs.ts's `setOrgSla`
 * established for `slaResponseTimeHours`/`slaUptimeTargetPct` themselves.
 *
 * Breach detection (`checkSupportTicketBreaches`) is called exclusively
 * by lib/support-ticket-poller.ts's own tick, the same
 * observe-and-mark-belongs-to-the-poller-only discipline
 * lib/quota-enforcement.ts's own header comment documents and for the
 * exact same reason: if a page view could also flip a ticket to
 * `breached`, an operator opening the dashboard moments before the
 * poller's own tick would race it.
 */
import type { Pool } from "pg";
import { getAuditDbPool } from "@/lib/audit-db";
import { getOrgSla } from "@/lib/orgs";
import { SLA_TIER_DEFAULTS, type SlaTier } from "@/lib/tiers";

export type SupportTicketStatus = "open" | "responded" | "resolved" | "breached";

export interface SupportTicket {
  id: string;
  orgId: string;
  subject: string;
  body: string;
  status: SupportTicketStatus;
  priority: SlaTier;
  createdAt: string; // RFC3339
  firstResponseDueAt: string; // RFC3339
  firstRespondedAt: string | null; // RFC3339
  resolvedAt: string | null; // RFC3339
}

export type SupportTicketOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

export type SupportTicketMessageAuthorType = "customer" | "support";

export interface SupportTicketMessage {
  id: string;
  ticketId: string;
  authorType: SupportTicketMessageAuthorType;
  authorId: string;
  body: string;
  createdAt: string; // RFC3339
}

async function ensureSupportTicketsTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.support_tickets (
      id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      org_id                 text NOT NULL,
      subject                text NOT NULL,
      body                   text NOT NULL,
      status                 text NOT NULL DEFAULT 'open',
      priority               text NOT NULL,
      created_at             timestamptz NOT NULL DEFAULT now(),
      first_response_due_at  timestamptz NOT NULL,
      first_responded_at     timestamptz,
      resolved_at            timestamptz
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS support_tickets_org_id_idx ON platform_console.support_tickets (org_id)`,
  );
  // gen_random_uuid() lives in pgcrypto on stock Postgres images; created
  // idempotently here rather than assumed pre-installed on the live
  // demo-project cluster this console shares with every other module's
  // self-bootstrap (active-sessions.ts, migrations.ts).
  await pool.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto`);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS support_tickets_breach_scan_idx
       ON platform_console.support_tickets (first_response_due_at)
       WHERE status = 'open'`,
  );
  // Real per-ticket message thread -- the piece missing between "SLA
  // tier sold" (this table's own status/priority/due-by columns) and
  // "SLA tier operable": an enterprise support org needs an actual
  // conversation history, not just a status field. Same schema, same
  // pool, same self-bootstrap discipline as support_tickets itself --
  // no new storage kind introduced.
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.support_ticket_messages (
      id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      ticket_id    uuid NOT NULL REFERENCES platform_console.support_tickets(id),
      author_type  text NOT NULL,
      author_id    text NOT NULL,
      body         text NOT NULL,
      created_at   timestamptz NOT NULL DEFAULT now()
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS support_ticket_messages_ticket_id_idx
       ON platform_console.support_ticket_messages (ticket_id, created_at)`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution cache
// convention as lib/active-sessions.ts's tableReady.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureSupportTicketsTable(pool);
  }
  await tableReady;
  return pool;
}

function toTicket(r: Record<string, unknown>): SupportTicket {
  return {
    id: r.id as string,
    orgId: r.org_id as string,
    subject: r.subject as string,
    body: r.body as string,
    status: r.status as SupportTicketStatus,
    priority: r.priority as SlaTier,
    createdAt: new Date(r.created_at as string).toISOString(),
    firstResponseDueAt: new Date(r.first_response_due_at as string).toISOString(),
    firstRespondedAt: r.first_responded_at ? new Date(r.first_responded_at as string).toISOString() : null,
    resolvedAt: r.resolved_at ? new Date(r.resolved_at as string).toISOString() : null,
  };
}

const SELECT_COLUMNS =
  "id, org_id, subject, body, status, priority, created_at, first_response_due_at, first_responded_at, resolved_at";

/**
 * Real ticket creation: computes `firstResponseDueAt` from the org's LIVE
 * SLA row (`getOrgSla`, the exact lookup `PUT /api/orgs/[id]/sla` already
 * backs) -- `priority` and the due-by clock are always derived
 * server-side from `SLA_TIER_DEFAULTS`, never accepted from the caller,
 * same "fixed lookup table, never a free-text/client-supplied number"
 * discipline `setOrgSla` established. Returns `{ok:false}` (never a
 * fabricated ticket) if the org's SLA row cannot be resolved.
 */
export async function createSupportTicket(params: {
  orgId: string;
  subject: string;
  body: string;
}): Promise<SupportTicketOutcome<SupportTicket>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }

  const slaResult = await getOrgSla(params.orgId);
  if (!slaResult.ok) return { ok: false, error: slaResult.error };
  if (!slaResult.data) return { ok: false, error: "org not found" };

  const priority = slaResult.data.slaTier;
  const responseHours =
    slaResult.data.slaResponseTimeHours ?? SLA_TIER_DEFAULTS[priority].slaResponseTimeHours;

  try {
    const result = await pool.query(
      `INSERT INTO platform_console.support_tickets
         (org_id, subject, body, status, priority, first_response_due_at)
       VALUES ($1, $2, $3, 'open', $4, now() + ($5 || ' hours')::interval)
       RETURNING ${SELECT_COLUMNS}`,
      [params.orgId, params.subject, params.body, priority, String(responseHours)],
    );
    return { ok: true, data: toTicket(result.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Real, org-scoped list, newest first -- backs GET /api/orgs/[id]/tickets. */
export async function listSupportTickets(orgId: string): Promise<SupportTicketOutcome<SupportTicket[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.support_tickets
       WHERE org_id = $1
       ORDER BY created_at DESC`,
      [orgId],
    );
    return { ok: true, data: result.rows.map(toTicket) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Real, single-ticket read, scoped to `orgId` so one org can never read
 * or mutate another org's ticket by guessing an id. */
export async function getSupportTicket(
  orgId: string,
  ticketId: string,
): Promise<SupportTicketOutcome<SupportTicket | null>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.support_tickets
       WHERE id = $1 AND org_id = $2`,
      [ticketId, orgId],
    );
    if (result.rowCount === 0) return { ok: true, data: null };
    return { ok: true, data: toTicket(result.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Real status transition: backs PATCH /api/orgs/[id]/tickets/[ticketId].
 * `responded` stamps `firstRespondedAt` (only if not already set -- a
 * second `responded` PATCH is a harmless no-op on the timestamp, same
 * idempotent-write discipline `recordSessionLogin`'s `ON CONFLICT DO
 * NOTHING` uses elsewhere in this codebase) and moves a `breached` ticket
 * back out of breach the moment a real response actually lands, since
 * `breached` only ever meant "no response was recorded before the due
 * time" -- a response recorded after breach is still a real response,
 * not something to hide. `resolved` stamps `resolvedAt` unconditionally
 * (the resolving action, not a fact that predates the PATCH).
 */
export async function updateSupportTicketStatus(params: {
  orgId: string;
  ticketId: string;
  status: "responded" | "resolved";
}): Promise<SupportTicketOutcome<SupportTicket | null>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }
  try {
    const result =
      params.status === "responded"
        ? await pool.query(
            `UPDATE platform_console.support_tickets
               SET status = 'responded',
                   first_responded_at = COALESCE(first_responded_at, now())
             WHERE id = $1 AND org_id = $2
             RETURNING ${SELECT_COLUMNS}`,
            [params.ticketId, params.orgId],
          )
        : await pool.query(
            `UPDATE platform_console.support_tickets
               SET status = 'resolved',
                   resolved_at = now(),
                   first_responded_at = COALESCE(first_responded_at, now())
             WHERE id = $1 AND org_id = $2
             RETURNING ${SELECT_COLUMNS}`,
            [params.ticketId, params.orgId],
          );
    if (result.rowCount === 0) return { ok: true, data: null };
    return { ok: true, data: toTicket(result.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export interface SupportTicketBreach {
  ticket: SupportTicket;
}

/**
 * Real breach-detection pass: flips every ticket still `open` whose
 * `first_response_due_at` has passed to `breached` in one real UPDATE,
 * and returns exactly the rows it flipped so the caller (
 * lib/support-ticket-poller.ts) can write one audit-log entry and fire
 * one `support.sla_breached` webhook event per newly-breached ticket --
 * never re-fired on a later tick, since a ticket already `breached`
 * (or already `responded`/`resolved`) no longer matches `status = 'open'`
 * and is excluded from the next pass's own WHERE clause. Called
 * exclusively by the poller's tick -- see module doc's "belongs to the
 * poller only" note.
 */
export async function checkSupportTicketBreaches(): Promise<SupportTicketOutcome<SupportTicketBreach[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `UPDATE platform_console.support_tickets
         SET status = 'breached'
       WHERE status = 'open'
         AND first_responded_at IS NULL
         AND first_response_due_at < now()
       RETURNING ${SELECT_COLUMNS}`,
    );
    return { ok: true, data: result.rows.map((r) => ({ ticket: toTicket(r) })) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

function toTicketMessage(r: Record<string, unknown>): SupportTicketMessage {
  return {
    id: r.id as string,
    ticketId: r.ticket_id as string,
    authorType: r.author_type as SupportTicketMessageAuthorType,
    authorId: r.author_id as string,
    body: r.body as string,
    createdAt: new Date(r.created_at as string).toISOString(),
  };
}

const MESSAGE_SELECT_COLUMNS = "id, ticket_id, author_type, author_id, body, created_at";

/**
 * Real, ordered thread read: backs GET /api/orgs/[id]/tickets/[ticketId]/messages.
 * Ordered by `created_at` (ties broken by `id`, since `now()` timestamps
 * can collide within the same statement) so the UI can render the
 * conversation top-to-bottom without re-sorting client-side.
 */
export async function listSupportTicketMessages(
  ticketId: string,
): Promise<SupportTicketOutcome<SupportTicketMessage[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${MESSAGE_SELECT_COLUMNS} FROM platform_console.support_ticket_messages
       WHERE ticket_id = $1
       ORDER BY created_at ASC, id ASC`,
      [ticketId],
    );
    return { ok: true, data: result.rows.map(toTicketMessage) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Real message post: appends one row to the thread AND flips the
 * ticket's own status per the existing `SupportTicketStatus` enum --
 * never a new state, so every other reader of `status` (the breach
 * poller, the SLA dashboard, the PATCH route) keeps working unchanged.
 *
 * Direction of the flip mirrors who is talking, the same "the action
 * IS the state transition" discipline `updateSupportTicketStatus`
 * already uses for the PATCH route:
 *   - `support` posts  -> ticket becomes `responded` (this reuses
 *     `updateSupportTicketStatus`'s own 'responded' branch, so
 *     `firstRespondedAt` gets stamped and a `breached` ticket comes back
 *     out of breach exactly like an explicit PATCH would -- a message
 *     IS a response).
 *   - `customer` posts on a ticket already `responded` -> ticket goes
 *     back to `open`, since the ball is back in support's court and a
 *     ticket sitting at `responded` while the customer is actually
 *     still waiting on support again would under-count real open work.
 *     A `customer` post never touches `resolved` or `breached` tickets'
 *     status -- reopening a resolved/breached ticket is a distinct,
 *     explicit action this function does not silently perform.
 *
 * The message insert and the status flip are not run in a single SQL
 * transaction against a second manually-managed client -- every other
 * write in this module already runs each statement as its own
 * autocommit query against the shared pool (see `getAuditDbPool`'s own
 * single-flight pool), so this follows the same convention rather than
 * introducing a new transactional pattern for one call site.
 */
export async function postSupportTicketMessage(params: {
  orgId: string;
  ticketId: string;
  authorType: SupportTicketMessageAuthorType;
  authorId: string;
  body: string;
}): Promise<SupportTicketOutcome<{ message: SupportTicketMessage; ticket: SupportTicket | null }>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "support ticket database not configured or unreachable" };
  }

  const existing = await getSupportTicket(params.orgId, params.ticketId);
  if (!existing.ok) return { ok: false, error: existing.error };
  if (!existing.data) return { ok: false, error: "ticket not found" };

  try {
    const inserted = await pool.query(
      `INSERT INTO platform_console.support_ticket_messages
         (ticket_id, author_type, author_id, body)
       VALUES ($1, $2, $3, $4)
       RETURNING ${MESSAGE_SELECT_COLUMNS}`,
      [params.ticketId, params.authorType, params.authorId, params.body],
    );
    const message = toTicketMessage(inserted.rows[0]);

    let ticket = existing.data;
    if (params.authorType === "support") {
      const statusResult = await updateSupportTicketStatus({
        orgId: params.orgId,
        ticketId: params.ticketId,
        status: "responded",
      });
      if (!statusResult.ok) return { ok: false, error: statusResult.error };
      if (statusResult.data) ticket = statusResult.data;
    } else if (params.authorType === "customer" && existing.data.status === "responded") {
      const reopened = await pool.query(
        `UPDATE platform_console.support_tickets
           SET status = 'open'
         WHERE id = $1 AND org_id = $2
         RETURNING ${SELECT_COLUMNS}`,
        [params.ticketId, params.orgId],
      );
      if (reopened.rowCount && reopened.rowCount > 0) ticket = toTicket(reopened.rows[0]);
    }

    return { ok: true, data: { message, ticket } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
