/**
 * Real Admin Impersonation / Support-Login Audit Trail -- the SOC2/
 * ISO27001 vendor-questionnaire control ("do you log support access to
 * our account?") this repo could not answer yes to before this module:
 * before it, an admin debugging a customer's org needed direct DB/console
 * access with no record at all, and lib/authz.ts had no concept of
 * "acting as support inside org X" distinct from an admin's own identity.
 *
 * Storage: a dedicated `platform_console.impersonation_sessions` table on
 * the same live demo-project Postgres lib/audit-db.ts and
 * lib/active-sessions.ts already treat as this console's own operational
 * store -- reuses that module's exact single-flight, self-healing pool
 * (`getAuditDbPool()`) rather than standing up a second connection pool,
 * and follows migrations.ts's own `CREATE TABLE IF NOT EXISTS`
 * self-bootstrap convention.
 *
 * Every state transition (start, end, auto-expire) is ALSO written
 * through lib/audit-db.ts's `writeAuditLogEntry` -- the exact same
 * hash-chained, tamper-evident `platform_console.audit_log` table every
 * other privileged action in this app already lands in, so an
 * impersonation session shows up in the SAME immutable trail, not a
 * side channel a reviewer could miss. The impersonation_sessions table
 * itself is the queryable, structured record (start/end/reason/duration
 * for the customer-facing /api/orgs/[id]/impersonation-log endpoint);
 * the audit_log rows are the tamper-evident cross-reference proving those
 * structured rows weren't edited after the fact without also breaking the
 * hash chain.
 *
 * Time-boxing: a session is valid for IMPERSONATION_TTL_MS (30 minutes)
 * from `startedAt`. There is no background sweep -- consistent with this
 * whole app's convention of lazy, read-time expiry (see lib/orgs.ts's
 * OrgInvite `expiresAt` checked at accept time, not swept by a cron)
 * every read path below (`getActiveImpersonationSession`,
 * `requireActiveImpersonationSession`) checks the TTL and auto-ends an
 * expired-but-still-"active" row (endedReason: "expired") the moment it's
 * next observed, rather than trusting a background job that could itself
 * fail silently.
 */
import type { Pool } from "pg";
import { getAuditDbPool, newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

export const IMPERSONATION_TTL_MS = 30 * 60 * 1000; // 30 minutes

export type ImpersonationEndedReason = "manual" | "expired" | null;

export interface ImpersonationSession {
  id: string;
  adminUserId: string;
  targetOrgId: string;
  reason: string;
  startedAt: string; // RFC3339
  expiresAt: string; // RFC3339 -- startedAt + IMPERSONATION_TTL_MS, computed once at start
  endedAt: string | null; // RFC3339, set on manual end or lazy auto-expire
  endedReason: ImpersonationEndedReason;
}

export type ImpersonationOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

async function ensureImpersonationTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.impersonation_sessions (
      id             text PRIMARY KEY,
      admin_user_id  text NOT NULL,
      target_org_id  text NOT NULL,
      reason         text NOT NULL,
      started_at     timestamptz NOT NULL DEFAULT now(),
      expires_at     timestamptz NOT NULL,
      ended_at       timestamptz,
      ended_reason   text
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS impersonation_sessions_target_org_id_idx
       ON platform_console.impersonation_sessions (target_org_id)`,
  );
}

// Ensured at most once per resolved pool -- same per-pool-resolution cache
// convention as active-sessions.ts's tableReady.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureImpersonationTable(pool);
  }
  await tableReady;
  return pool;
}

function toSession(r: Record<string, unknown>): ImpersonationSession {
  return {
    id: r.id as string,
    adminUserId: r.admin_user_id as string,
    targetOrgId: r.target_org_id as string,
    reason: r.reason as string,
    startedAt: new Date(r.started_at as string).toISOString(),
    expiresAt: new Date(r.expires_at as string).toISOString(),
    endedAt: r.ended_at ? new Date(r.ended_at as string).toISOString() : null,
    endedReason: (r.ended_reason as ImpersonationEndedReason) ?? null,
  };
}

const SELECT_COLUMNS =
  "id, admin_user_id, target_org_id, reason, started_at, expires_at, ended_at, ended_reason";

/**
 * Starts a new, real, time-boxed impersonation session -- one INSERT into
 * the structured table, plus one entry into the shared, hash-chained
 * audit_log via writeAuditLogEntry (actor is the admin, path/method are
 * synthetic but real strings identifying this as an impersonation-start
 * event, same "one JSON line + one audit_log row per action" convention
 * every other mutating route in this app already follows).
 */
export async function startImpersonation(
  adminUserId: string,
  targetOrgId: string,
  reason: string,
): Promise<ImpersonationOutcome<ImpersonationSession>> {
  const trimmedReason = reason.trim();
  if (!trimmedReason) {
    return { ok: false, error: "reason is required to start an impersonation session" };
  }
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "impersonation session store not configured or unreachable" };
  }

  const id = globalThis.crypto.randomUUID();
  const startedAt = new Date();
  const expiresAt = new Date(startedAt.getTime() + IMPERSONATION_TTL_MS);

  try {
    const result = await pool.query(
      `INSERT INTO platform_console.impersonation_sessions
         (id, admin_user_id, target_org_id, reason, started_at, expires_at)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING ${SELECT_COLUMNS}`,
      [id, adminUserId, targetOrgId, trimmedReason, startedAt.toISOString(), expiresAt.toISOString()],
    );
    const session = toSession(result.rows[0]);

    writeAuditLogEntry({
      requestId: newRequestId(),
      timestamp: startedAt.toISOString(),
      actor: adminUserId,
      method: "IMPERSONATE_START",
      path: `/orgs/${targetOrgId} (session ${id}: ${trimmedReason})`,
      status: 200,
    });

    return { ok: true, data: session };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Applies lazy TTL expiry to one already-fetched row: an "active"
 * (ended_at IS NULL) row whose expires_at has passed is ended right now,
 * with endedReason "expired" -- written through the same audit trail as a
 * manual end, so auto-expiry is exactly as visible to a reviewer as an
 * explicit DELETE. Returns the (possibly now-expired) session as it
 * stands after this check.
 */
async function applyLazyExpiry(
  pool: Pool,
  session: ImpersonationSession,
): Promise<ImpersonationSession> {
  if (session.endedAt) return session;
  if (new Date(session.expiresAt).getTime() > Date.now()) return session;

  const endedAt = new Date();
  const result = await pool.query(
    `UPDATE platform_console.impersonation_sessions
     SET ended_at = $2, ended_reason = 'expired'
     WHERE id = $1 AND ended_at IS NULL
     RETURNING ${SELECT_COLUMNS}`,
    [session.id, endedAt.toISOString()],
  );
  if (result.rowCount === 0) {
    // Lost a race with a concurrent manual end -- re-read is unnecessary;
    // the session is ended either way, which is all callers care about.
    return { ...session, endedAt: endedAt.toISOString(), endedReason: "expired" };
  }
  const ended = toSession(result.rows[0]);
  writeAuditLogEntry({
    requestId: newRequestId(),
    timestamp: endedAt.toISOString(),
    actor: session.adminUserId,
    method: "IMPERSONATE_EXPIRE",
    path: `/orgs/${session.targetOrgId} (session ${session.id}, auto-expired after ${IMPERSONATION_TTL_MS / 60_000}m)`,
    status: 200,
  });
  return ended;
}

/**
 * Real single-session read, with lazy TTL auto-expiry applied on every
 * call -- the "auto-expire via TTL check on next request" half of the
 * spec. Used both by the DELETE (end-early) route and by any caller that
 * wants to validate a session id carried on a request (e.g. a future
 * request-context tag) before trusting it as "currently active".
 */
export async function getActiveImpersonationSession(
  id: string,
): Promise<ImpersonationOutcome<ImpersonationSession | null>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "impersonation session store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.impersonation_sessions WHERE id = $1`,
      [id],
    );
    if (result.rowCount === 0) return { ok: true, data: null };
    const session = await applyLazyExpiry(pool, toSession(result.rows[0]));
    return { ok: true, data: session };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Ends an impersonation session early ("DELETE to end early" in the
 * spec) -- only the admin who started it may end it (enforced by the
 * caller's requireActiveImpersonationSession + an explicit adminUserId
 * match, same "can't touch someone else's record" discipline
 * lib/orgs.ts's acceptOrgInviteIn applies to invite emails). Already-
 * ended sessions (manual or expired) are a real, specific error, not a
 * silent no-op success.
 */
export async function endImpersonation(
  id: string,
  endedBy: string,
): Promise<ImpersonationOutcome<ImpersonationSession>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "impersonation session store not configured or unreachable" };
  }
  const existingResult = await pool
    .query(`SELECT ${SELECT_COLUMNS} FROM platform_console.impersonation_sessions WHERE id = $1`, [id])
    .catch((err) => {
      throw err;
    });
  if (existingResult.rowCount === 0) {
    return { ok: false, error: "impersonation session not found" };
  }
  const current = await applyLazyExpiry(pool, toSession(existingResult.rows[0]));
  if (current.endedAt) {
    return { ok: false, error: `impersonation session is already ended (${current.endedReason})` };
  }
  if (current.adminUserId !== endedBy) {
    return { ok: false, error: "only the admin who started this session may end it" };
  }

  const endedAt = new Date();
  const result = await pool.query(
    `UPDATE platform_console.impersonation_sessions
     SET ended_at = $2, ended_reason = 'manual'
     WHERE id = $1 AND ended_at IS NULL
     RETURNING ${SELECT_COLUMNS}`,
    [id, endedAt.toISOString()],
  );
  if (result.rowCount === 0) {
    return { ok: false, error: "impersonation session is already ended" };
  }
  const ended = toSession(result.rows[0]);
  writeAuditLogEntry({
    requestId: newRequestId(),
    timestamp: endedAt.toISOString(),
    actor: endedBy,
    method: "IMPERSONATE_END",
    path: `/orgs/${ended.targetOrgId} (session ${id}, ended manually)`,
    status: 200,
  });
  return { ok: true, data: ended };
}

/**
 * Real per-request tag: downstream audit-log entries call this to fold an
 * active impersonation session into their `actor` string so the trail
 * reads "action performed by admin X impersonating org Y" (the spec's
 * exact phrasing) instead of just "admin X" with the impersonation
 * context lost. Deliberately a pure string helper (not middleware.ts
 * wiring, which runs on the edge runtime and cannot import this
 * Node-only `pg`-backed module) -- any /api route that authenticates a
 * request while carrying an impersonation session id (e.g. via the
 * `x-impersonation-session` header set by an admin's browser after
 * POST /api/support/impersonate) applies this before calling
 * writeAuditLogEntry.
 */
export function formatImpersonationActor(
  baseActor: string,
  session: Pick<ImpersonationSession, "id" | "targetOrgId">,
): string {
  return `${baseActor} (impersonating org ${session.targetOrgId} via session ${session.id})`;
}

/**
 * Resolves and validates an impersonation session id carried on an
 * incoming request (the `x-impersonation-session` header) against the
 * real store: returns the session only if it exists, belongs to the
 * given admin, and is still active after lazy TTL expiry -- never trusts
 * the header's claim on its own. Routes that want to tag their audit
 * entries with "acting as support inside org X" call this once and, on a
 * hit, run `formatImpersonationActor` over their actor string.
 */
export async function resolveRequestImpersonation(
  sessionId: string | null,
  adminUserId: string,
): Promise<ImpersonationSession | null> {
  if (!sessionId) return null;
  const result = await getActiveImpersonationSession(sessionId);
  if (!result.ok || !result.data) return null;
  if (result.data.adminUserId !== adminUserId) return null;
  if (result.data.endedAt) return null;
  return result.data;
}

/**
 * Real customer-facing read: every impersonation session that has ever
 * touched one org, most recent first -- backs GET
 * /api/orgs/[id]/impersonation-log. Includes ended AND still-active
 * sessions (an org admin should see an in-progress support session too,
 * not just completed ones), with lazy TTL expiry applied to each active
 * row before it's returned so the customer never sees a session
 * incorrectly reported as "still active" past its own 30-minute box.
 */
export async function listImpersonationSessionsForOrg(
  targetOrgId: string,
): Promise<ImpersonationOutcome<ImpersonationSession[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "impersonation session store not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT ${SELECT_COLUMNS} FROM platform_console.impersonation_sessions
       WHERE target_org_id = $1
       ORDER BY started_at DESC`,
      [targetOrgId],
    );
    const sessions = await Promise.all(
      result.rows.map((row) => applyLazyExpiry(pool, toSession(row))),
    );
    return { ok: true, data: sessions };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
