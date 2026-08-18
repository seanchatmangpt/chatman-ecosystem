/**
 * Real Active Session Management -- the AWS IAM Identity Center "active
 * sessions" view / GCP Console "manage devices & activity" equivalent.
 *
 * Before this module, this app's sessions were stateless HS256 JWTs
 * (lib/session.ts): once issued, nothing server-side recorded which
 * sessions existed, and there was no way to see who was logged in or force
 * a specific session to stop working before its own 8h expiry -- a JWT is
 * self-verifying by design, so "delete the cookie" is the only thing a
 * client-side logout can ever do, and a stolen/leaked cookie stays valid
 * until it naturally expires no matter what an operator does.
 *
 * This module adds the one thing a pure JWT scheme structurally cannot
 * provide: a real, server-side, revocable registry row per session, keyed
 * by a new `sessionId` claim (lib/session.ts) minted at login time and
 * distinct from the JWT's own `sub`/`role`/etc. claims. Every session-
 * bearing request now costs one extra registry lookup (see
 * `checkAndTouchSession`, called from middleware.ts on every authenticated
 * request) -- the real, unavoidable price of making revocation real instead
 * of decorative; a stateless JWT alone can never be force-expired, only a
 * server-side check like this one can reject it before its own exp claim
 * says it should stop working.
 *
 * Storage: a dedicated `platform_console.active_sessions` table on the
 * same live demo-project Postgres lib/audit-db.ts already treats as this
 * console's own operational store -- reuses that module's exact
 * single-flight, self-healing pool (`getAuditDbPool()`) rather than
 * standing up a second connection pool, and follows migrations.ts's own
 * `CREATE TABLE IF NOT EXISTS` self-bootstrap convention (idempotent on
 * every pool resolution, so this table exists the first time this module
 * is used against a fresh cluster, no manual `psql` step required).
 *
 * Disclosed simplification, the same fail-open-on-unreachable-store
 * convention audit-db.ts's own writeAuditLogEntry already uses for its
 * non-blocking stdout+DB dual write: if the registry's Postgres is
 * genuinely unreachable when `checkAndTouchSession` runs, the request is
 * allowed through rather than rejected -- failing every authenticated
 * request platform-wide shut on a transient DB hiccup would be a worse
 * outcome than a session that (in that narrow window only) can't be
 * force-revoked. The moment the DB is reachable again, revocation is
 * enforced on the very next request. A session actually confirmed revoked
 * in a reachable registry is ALWAYS rejected -- that check never degrades.
 *
 * `sessionId` is stable per real login for the two cookie-issuing paths
 * (local-admin, gotrue) -- one fresh `crypto.randomUUID()` minted once at
 * `/api/login` / `/api/auth/gotrue-login` / `/api/auth/gotrue-signup` time,
 * carried unchanged for that cookie's whole life. The API-key auth path
 * (middleware.ts's Bearer-token branch) has no separate login step -- it
 * mints a fresh app-local session JWT on literally every request -- so its
 * `sessionId` is instead deterministic (`apikey-<keyId>`), making every
 * request authenticated by the same API key resolve to the same registry
 * row; `checkAndTouchSession`'s self-heal-create branch below IS that key's
 * "login" moment (its first-ever observed use), and revoking that row from
 * `/sessions` blocks the key on every subsequent request even though
 * lib/api-keys.ts's own `revoked` flag (a different, independent
 * revocation path with the same effect) is untouched -- real
 * defense-in-depth, not a redundant duplicate: either revocation blocks
 * the key.
 */
import type { Pool } from "pg";
import { getAuditDbPool } from "@/lib/audit-db";

export type AuthProviderKind = "local-admin" | "gotrue" | "api-key";

export interface ActiveSessionRecord {
  sessionId: string;
  identifier: string;
  authProvider: AuthProviderKind;
  createdAt: string; // RFC3339
  lastSeenAt: string; // RFC3339
  ip: string | null;
  userAgent: string | null;
  revoked: boolean;
  revokedAt: string | null;
  revokedBy: string | null;
}

export type ActiveSessionOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

// Registry rows are touched at most this often per session -- cheap real
// throttling (a single indexed UPDATE with a WHERE-clause age guard, not a
// write on every single request) rather than an unconditional write on
// every authenticated hit.
const TOUCH_THROTTLE = "1 minute";

async function ensureActiveSessionsTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.active_sessions (
      session_id    text PRIMARY KEY,
      identifier    text NOT NULL,
      auth_provider text NOT NULL,
      created_at    timestamptz NOT NULL DEFAULT now(),
      last_seen_at  timestamptz NOT NULL DEFAULT now(),
      ip            text,
      user_agent    text,
      revoked       boolean NOT NULL DEFAULT false,
      revoked_at    timestamptz,
      revoked_by    text
    )
  `);
}

// Ensured at most once per resolved pool (mirrors migrations.ts's own
// per-pool-resolution idempotent bootstrap) -- re-running `CREATE TABLE IF
// NOT EXISTS` on every request would be a harmless no-op but a wasted round
// trip; this cache just skips the repeat.
let tableReady: Promise<void> | null = null;

async function resolveReadyPool(): Promise<Pool | null> {
  const pool = await getAuditDbPool();
  if (!pool) return null;
  if (!tableReady) {
    tableReady = ensureActiveSessionsTable(pool);
  }
  await tableReady;
  return pool;
}

function toRecord(r: Record<string, unknown>): ActiveSessionRecord {
  return {
    sessionId: r.session_id as string,
    identifier: r.identifier as string,
    authProvider: r.auth_provider as AuthProviderKind,
    createdAt: new Date(r.created_at as string).toISOString(),
    lastSeenAt: new Date(r.last_seen_at as string).toISOString(),
    ip: (r.ip as string) ?? null,
    userAgent: (r.user_agent as string) ?? null,
    revoked: r.revoked as boolean,
    revokedAt: r.revoked_at ? new Date(r.revoked_at as string).toISOString() : null,
    revokedBy: (r.revoked_by as string) ?? null,
  };
}

export interface RecordSessionLoginInput {
  sessionId: string;
  identifier: string;
  authProvider: AuthProviderKind;
  ip: string | null;
  userAgent: string | null;
}

/**
 * Real registry INSERT at the moment a session is actually minted -- called
 * from /api/login, /api/auth/gotrue-login, and /api/auth/gotrue-signup
 * immediately after each mints its own session JWT with the exact same
 * `sessionId`. `ON CONFLICT DO NOTHING` is a defensive no-op (a fresh
 * `crypto.randomUUID()` per login should never collide) rather than a
 * required part of the design -- unlike the API-key path's deliberately
 * stable id, these ids are always freshly random.
 */
export async function recordSessionLogin(
  input: RecordSessionLoginInput,
): Promise<ActiveSessionOutcome<ActiveSessionRecord>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "active session registry not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `INSERT INTO platform_console.active_sessions
         (session_id, identifier, auth_provider, ip, user_agent)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (session_id) DO NOTHING
       RETURNING session_id, identifier, auth_provider, created_at, last_seen_at,
                 ip, user_agent, revoked, revoked_at, revoked_by`,
      [input.sessionId, input.identifier, input.authProvider, input.ip, input.userAgent],
    );
    if (result.rowCount === 0) {
      // Real conflict (id already registered) -- read back the existing row
      // rather than silently reporting success with no row.
      const existing = await pool.query(
        `SELECT session_id, identifier, auth_provider, created_at, last_seen_at,
                ip, user_agent, revoked, revoked_at, revoked_by
         FROM platform_console.active_sessions WHERE session_id = $1`,
        [input.sessionId],
      );
      if (existing.rowCount === 0) {
        return { ok: false, error: `session '${input.sessionId}' could not be recorded` };
      }
      return { ok: true, data: toRecord(existing.rows[0]) };
    }
    return { ok: true, data: toRecord(result.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export interface CheckAndTouchResult {
  revoked: boolean;
  record: ActiveSessionRecord | null;
}

/**
 * The real per-request enforcement check middleware.ts calls for every
 * session-bearing request: is this `sessionId` marked revoked in the real
 * registry? Also the throttled `last_seen_at` heartbeat write, and (for the
 * API-key auth path's stable, request-independent id) the lazy first-touch
 * INSERT that stands in for that path's missing separate login step -- see
 * module doc.
 *
 * Returns `{ok:false}` only when the registry's Postgres is genuinely
 * unreachable -- callers must fail OPEN on that outcome (see module doc's
 * "Disclosed simplification"). A `{ok:true}` result's `revoked` flag is the
 * real, current, load-bearing security decision.
 */
export async function checkAndTouchSession(
  sessionId: string,
  fallbackMeta: { identifier: string; authProvider: AuthProviderKind; ip: string | null; userAgent: string | null },
): Promise<ActiveSessionOutcome<CheckAndTouchResult>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "active session registry not configured or unreachable" };
  }
  try {
    const existing = await pool.query(
      `SELECT session_id, identifier, auth_provider, created_at, last_seen_at,
              ip, user_agent, revoked, revoked_at, revoked_by
       FROM platform_console.active_sessions WHERE session_id = $1`,
      [sessionId],
    );

    if (existing.rowCount === 0) {
      // First time this sessionId has ever been seen by the registry --
      // either the API-key auth path's very first request on this key
      // (its real "login" moment, see module doc), or a cookie session
      // whose original login-time INSERT never landed (registry was
      // unreachable at that moment) -- self-heal by creating it now rather
      // than treating "not yet registered" as "revoked".
      const inserted = await pool.query(
        `INSERT INTO platform_console.active_sessions
           (session_id, identifier, auth_provider, ip, user_agent)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (session_id) DO UPDATE SET last_seen_at = now()
         RETURNING session_id, identifier, auth_provider, created_at, last_seen_at,
                   ip, user_agent, revoked, revoked_at, revoked_by`,
        [sessionId, fallbackMeta.identifier, fallbackMeta.authProvider, fallbackMeta.ip, fallbackMeta.userAgent],
      );
      const record = toRecord(inserted.rows[0]);
      return { ok: true, data: { revoked: record.revoked, record } };
    }

    const record = toRecord(existing.rows[0]);
    if (!record.revoked) {
      // Throttled heartbeat -- only writes when the last write is older
      // than TOUCH_THROTTLE, so an active session doesn't cost a write on
      // every single request.
      await pool.query(
        `UPDATE platform_console.active_sessions
         SET last_seen_at = now()
         WHERE session_id = $1 AND last_seen_at < now() - interval '${TOUCH_THROTTLE}'`,
        [sessionId],
      );
    }
    return { ok: true, data: { revoked: record.revoked, record } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Real, queryable "who's logged in" list for GET /api/sessions -> /sessions. */
export async function listActiveSessions(): Promise<ActiveSessionOutcome<ActiveSessionRecord[]>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "active session registry not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT session_id, identifier, auth_provider, created_at, last_seen_at,
              ip, user_agent, revoked, revoked_at, revoked_by
       FROM platform_console.active_sessions
       ORDER BY last_seen_at DESC
       LIMIT 200`,
    );
    return { ok: true, data: result.rows.map(toRecord) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * The real revocation write for DELETE /api/sessions -- what makes a
 * specific already-issued, unexpired JWT stop working before its own `exp`
 * claim says it should. `revokedBy` is the acting owner's own identifier
 * (never fabricated), recorded on the row for a real audit trail of who
 * revoked what.
 */
export async function revokeSession(
  sessionId: string,
  revokedBy: string,
): Promise<ActiveSessionOutcome<ActiveSessionRecord>> {
  const pool = await resolveReadyPool();
  if (!pool) {
    return { ok: false, error: "active session registry not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `UPDATE platform_console.active_sessions
       SET revoked = true, revoked_at = now(), revoked_by = $2
       WHERE session_id = $1
       RETURNING session_id, identifier, auth_provider, created_at, last_seen_at,
                 ip, user_agent, revoked, revoked_at, revoked_by`,
      [sessionId, revokedBy],
    );
    if (result.rowCount === 0) {
      return { ok: false, error: `no session found with id '${sessionId}'` };
    }
    return { ok: true, data: toRecord(result.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
