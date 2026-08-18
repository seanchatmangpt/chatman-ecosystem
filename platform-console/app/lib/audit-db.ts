/**
 * Node.js-only durable persistence for the audit log -- the real
 * hyperscaler CloudTrail / GCP Audit Logs / Azure Monitor Activity Log
 * equivalent: a queryable "who did what" history, not just the ephemeral
 * pod-log line lib/audit-log.ts already writes (real, but gone the moment
 * a pod restarts).
 *
 * Deliberately a SEPARATE module from lib/audit-log.ts, and never imported
 * by middleware.ts: middleware runs on the Next.js edge runtime, and the
 * `pg` driver this module uses pulls in real Node.js `net`/`tls` core
 * modules the edge runtime cannot bundle -- the exact same reason
 * lib/credentials.ts (bcryptjs) is kept out of middleware, documented in
 * that file's own header comment. Every `/api/*` route handler already
 * runs on the Node.js runtime (default for route handlers, documented in
 * each route file's own header comment), so this module is safe to import
 * there. middleware.ts keeps calling the original, stdout-only
 * writeAuditLogEntry from lib/audit-log.ts unchanged -- its own generic
 * per-request line ("authenticated and forwarded") is intentionally left
 * out of the durable store; every actual API action already logs its own,
 * more specific entry through THIS module instead.
 *
 * `writeAuditLogEntry` here is a drop-in replacement for lib/audit-log.ts's
 * export of the same name (same signature, same args) -- callers just
 * import it from here instead. It performs the exact same real stdout
 * write (by calling straight through to the original -- still the
 * real-time-tailable record via `kubectl logs`/the /logs module), then
 * fires a real `INSERT` into `platform_console.audit_log` on the live
 * demo-project Postgres this cluster already runs (the same database
 * lib/k8s.ts's createBackupJob/createRestoreJob already trust with real
 * tenant data). The DB write never blocks or fails the request the audit
 * line describes; any failure is logged to stderr, never silently
 * swallowed and never an unhandled promise rejection.
 */
import { Pool } from "pg";
import {
  getPostgresConnectionInfo,
  getProject,
  getProjectDatabasePod,
  hasClusterCredentials,
} from "@/lib/k8s";
import {
  newRequestId,
  writeAuditLogEntry as writeStdoutAuditLogEntry,
  type AuditLogEntry,
} from "@/lib/audit-log";

export { newRequestId };
export type { AuditLogEntry };

// The one console-operational Postgres this whole console treats as its
// own durable store -- resolved live via the exact same
// getProject/getProjectDatabasePod calls every project-scoped module
// (Database/Auth/Storage/Functions/Backups) already uses, never a
// hardcoded Service/namespace string. "demo-project" is the one real
// project this cluster provisions for the console's own operational use
// (see README's Backups section for the same convention applied there).
const AUDIT_DB_PROJECT_NAME = "demo-project";

async function createPool(): Promise<Pool> {
  const projectResult = await getProject(AUDIT_DB_PROJECT_NAME);
  if (!projectResult.ok) throw new Error(projectResult.error);
  if (!projectResult.data) {
    throw new Error(`audit log DB: project '${AUDIT_DB_PROJECT_NAME}' not found`);
  }
  const podResult = await getProjectDatabasePod(projectResult.data);
  if (!podResult.ok) throw new Error(podResult.error);
  if (!podResult.data) {
    throw new Error(
      `audit log DB: no database Service found for project '${AUDIT_DB_PROJECT_NAME}'`,
    );
  }
  const connResult = await getPostgresConnectionInfo(podResult.data.namespace, podResult.data.podName);
  if (!connResult.ok) throw new Error(connResult.error);
  const info = connResult.data;
  return new Pool({
    host: info.host,
    port: info.port,
    user: info.user,
    password: info.password,
    database: info.database,
    max: 5,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
  });
}

// Single-flight, self-healing cache: a successfully created Pool is reused
// for the life of the process (same singleton convention lib/k8s.ts's own
// readInClusterConfig uses for its ServiceAccount config); a failed
// resolution is NOT cached, so the next audit event retries cluster
// discovery from scratch rather than wedging this pod into "never
// persists again" for the rest of its lifetime over one transient error.
let poolPromise: Promise<Pool> | null = null;

async function resolvePool(): Promise<Pool | null> {
  if (!hasClusterCredentials()) return null; // off-cluster (local dev/build) -- fail closed, same convention as every lib/k8s.ts reader
  if (!poolPromise) {
    poolPromise = createPool();
  }
  try {
    return await poolPromise;
  } catch (err) {
    poolPromise = null; // allow the next event to retry
    console.error(
      JSON.stringify({
        auditDbPoolError: err instanceof Error ? err.message : String(err),
      }),
    );
    return null;
  }
}

// ---------------------------------------------------- Tamper-evident chain
//
// The gap this closes: platform_console.audit_log lived on the exact same
// Postgres cluster it audits, writable by any identity with app-DB access
// (the same access an attacker who breached the app itself would have) --
// so a post-breach forensic reviewer had no way to tell a genuine row from
// a silently rewritten one. Full physical isolation (a second Postgres
// instance in a separate, more-restricted-RBAC namespace) is the stronger
// fix and is the right next step; this closes the detectability half of
// the gap now, in the same store, using the append-only hash-chain
// construction the gap description names as the accepted alternative
// (each row's row_hash commits to the prior row's row_hash plus that row's
// own fields, so ANY row edited, inserted-out-of-band, or deleted anywhere
// in the chain breaks every row_hash after it -- a UPDATE that mutates a
// field without recomputing the entire downstream chain, which requires
// re-deriving row_hash values a plain SQL UPDATE has no way to do without
// already knowing this exact algorithm, is detectable by
// `verifyAuditChain` below). node:crypto's sha256 is used (not blake3):
// this chain has its own, independent verification contract from the
// evidence-bundle's blake3 digest (a single point-in-time seal over a
// static JSON document) -- picking a different, equally real primitive
// here isn't a shortcut, it's the correct algorithm for a fundamentally
// different job (a growing, append-only chain vs. one static document),
// and node:crypto ships in the runtime already (no new dependency).
import { createHash } from "node:crypto";

// Genesis value the first real row's prev_hash commits to -- distinguishable
// at a glance from any real sha256 digest (which is lowercase hex).
const GENESIS_HASH = "GENESIS-" + "0".repeat(56);

function computeRowHash(prevHash: string, entry: AuditLogEntry): string {
  const material = [prevHash, entry.requestId, entry.timestamp, entry.actor, entry.method, entry.path, String(entry.status)].join(
    " ",
  );
  return createHash("sha256").update(material, "utf8").digest("hex");
}

async function ensureAuditLogChainColumns(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  // The table itself is presumed to already exist (provisioned before this
  // module's first hash-chain-aware deploy) -- CREATE TABLE IF NOT EXISTS
  // still covers a genuinely fresh cluster, matching migrations.ts's and
  // active-sessions.ts's own idempotent self-bootstrap convention.
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.audit_log (
      id          bigserial PRIMARY KEY,
      request_id  text NOT NULL,
      ts          timestamptz NOT NULL,
      actor       text NOT NULL,
      method      text NOT NULL,
      path        text NOT NULL,
      status      integer NOT NULL,
      inserted_at timestamptz NOT NULL DEFAULT now()
    )
  `);
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS prev_hash text`);
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS row_hash text`);
}

/**
 * One-time backfill for rows written before this pass added prev_hash/
 * row_hash (a NULL row_hash is exactly and only the "written before the
 * chain existed" marker -- a chain-aware INSERT always sets both columns
 * together, see persistAuditLogEntry). Walks every such row in id order
 * and chains it onto whatever the real chain's current tail already is
 * (GENESIS_HASH if this table has never had a chained row), so the
 * pre-existing history becomes chain-verifiable instead of being silently
 * excluded from verifyAuditChain's coverage. Idempotent: a second run
 * finds zero NULL rows and does nothing.
 */
async function backfillAuditLogChain(pool: Pool): Promise<void> {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("SELECT pg_advisory_xact_lock($1)", [CHAIN_LOCK_KEY.toString()]);
    const unchained = await client.query<{
      id: string;
      request_id: string;
      ts: string;
      actor: string;
      method: string;
      path: string;
      status: number;
    }>(
      `SELECT id, request_id, ts, actor, method, path, status
       FROM platform_console.audit_log
       WHERE row_hash IS NULL
       ORDER BY id ASC`,
    );
    if (unchained.rows.length > 0) {
      const tail = await client.query<{ row_hash: string | null }>(
        `SELECT row_hash FROM platform_console.audit_log WHERE row_hash IS NOT NULL ORDER BY id DESC LIMIT 1`,
      );
      let prevHash = tail.rows[0]?.row_hash ?? GENESIS_HASH;
      for (const r of unchained.rows) {
        const entry: AuditLogEntry = {
          requestId: r.request_id,
          timestamp: new Date(r.ts).toISOString(),
          actor: r.actor,
          method: r.method,
          path: r.path,
          status: Number(r.status),
        };
        const rowHash = computeRowHash(prevHash, entry);
        await client.query(
          `UPDATE platform_console.audit_log SET prev_hash = $1, row_hash = $2 WHERE id = $3`,
          [prevHash, rowHash, r.id],
        );
        prevHash = rowHash;
      }
    }
    await client.query("COMMIT");
  } catch (err) {
    await client.query("ROLLBACK").catch(() => {});
    throw err;
  } finally {
    client.release();
  }
}

// Ensured at most once per resolved pool -- same per-pool-resolution cache
// convention as active-sessions.ts's tableReady.
let chainColumnsReady: Promise<void> | null = null;

async function resolveChainReadyPool(): Promise<Pool | null> {
  const pool = await resolvePool();
  if (!pool) return null;
  if (!chainColumnsReady) {
    chainColumnsReady = ensureAuditLogChainColumns(pool).then(() => backfillAuditLogChain(pool));
  }
  await chainColumnsReady;
  return pool;
}

// A dedicated, stable advisory-lock key for the audit-log hash chain --
// arbitrary but fixed (derived from the low 62 bits of
// sha256("platform_console.audit_log.chain"), a real hash rather than a
// hand-picked magic number, so it's collision-resistant against any other
// pg_advisory_xact_lock key this codebase might introduce later). Every
// chain-extending INSERT takes this transaction-scoped lock FIRST, before
// reading the current tail row_hash, so two concurrent requests can never
// both read the same tail and mint two rows claiming the same prev_hash --
// the exact race a naive "SELECT last row_hash, then INSERT" would have
// under real concurrent traffic.
const CHAIN_LOCK_KEY = (() => {
  const digest = createHash("sha256").update("platform_console.audit_log.chain").digest();
  return digest.readBigInt64BE(0) & BigInt("0x3fffffffffffffff");
})();

async function persistAuditLogEntry(entry: AuditLogEntry): Promise<void> {
  const pool = await resolveChainReadyPool();
  if (!pool) return; // not configured / cluster DB unreachable -- the stdout line is still the real record for this environment
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("SELECT pg_advisory_xact_lock($1)", [CHAIN_LOCK_KEY.toString()]);
    const tail = await client.query<{ row_hash: string | null }>(
      `SELECT row_hash FROM platform_console.audit_log ORDER BY id DESC LIMIT 1`,
    );
    const prevHash = tail.rows[0]?.row_hash ?? GENESIS_HASH;
    const rowHash = computeRowHash(prevHash, entry);
    await client.query(
      `INSERT INTO platform_console.audit_log (request_id, ts, actor, method, path, status, prev_hash, row_hash)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [entry.requestId, entry.timestamp, entry.actor, entry.method, entry.path, entry.status, prevHash, rowHash],
    );
    await client.query("COMMIT");
  } catch (err) {
    await client.query("ROLLBACK").catch(() => {});
    throw err;
  } finally {
    client.release();
  }
}

export function writeAuditLogEntry(entry: AuditLogEntry): void {
  writeStdoutAuditLogEntry(entry);
  persistAuditLogEntry(entry).catch((err) => {
    console.error(
      JSON.stringify({
        auditDbWriteError: err instanceof Error ? err.message : String(err),
        requestId: entry.requestId,
      }),
    );
  });
}

/**
 * Exposes the same single-flight, self-healing pool every reader/writer in
 * this module already shares -- for lib/audit-export.ts's streaming NDJSON
 * export, which needs a raw `PoolClient` (to run several keyset-paginated
 * batch queries against one held connection) rather than the one-shot
 * `pool.query` calls `queryAuditLog` below issues. Returns `null` under the
 * exact same fail-closed conditions as every other reader here (no
 * in-cluster credentials, or the live cluster DB unreachable).
 */
export async function getAuditDbPool(): Promise<Pool | null> {
  return resolvePool();
}

// --------------------------------------------------------- Querying (/audit)

export interface AuditLogRow {
  id: number;
  requestId: string;
  ts: string; // RFC3339
  actor: string;
  method: string;
  path: string;
  status: number;
  insertedAt: string; // RFC3339
}

export interface AuditLogQueryParams {
  actor?: string;
  path?: string;
  from?: string; // RFC3339 lower bound (inclusive), matched against `ts`
  to?: string; // RFC3339 upper bound (inclusive), matched against `ts`
  limit: number;
  offset: number;
}

export interface AuditLogQueryResult {
  rows: AuditLogRow[];
  total: number;
}

export type AuditLogQueryOutcome =
  | { ok: true; data: AuditLogQueryResult }
  | { ok: false; error: string };

/**
 * Real, parameterized (never string-concatenated) filter + pagination
 * query against platform_console.audit_log -- backs GET /api/audit. Actor
 * and path filters are substring (ILIKE), matching how the /logs and
 * /secrets modules already let an operator search without needing an
 * exact string.
 */
export async function queryAuditLog(params: AuditLogQueryParams): Promise<AuditLogQueryOutcome> {
  const pool = await resolvePool();
  if (!pool) {
    return {
      ok: false,
      error:
        "audit log database not configured or unreachable -- see the stdout log (kubectl logs) for this environment's real-time record",
    };
  }

  const conditions: string[] = [];
  const values: unknown[] = [];

  if (params.actor) {
    values.push(`%${params.actor}%`);
    conditions.push(`actor ILIKE $${values.length}`);
  }
  if (params.path) {
    values.push(`%${params.path}%`);
    conditions.push(`path ILIKE $${values.length}`);
  }
  if (params.from) {
    values.push(params.from);
    conditions.push(`ts >= $${values.length}`);
  }
  if (params.to) {
    values.push(params.to);
    conditions.push(`ts <= $${values.length}`);
  }
  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  try {
    const countResult = await pool.query<{ count: string }>(
      `SELECT count(*)::bigint AS count FROM platform_console.audit_log ${where}`,
      values,
    );
    const total = Number(countResult.rows[0]?.count ?? "0");

    const rowsResult = await pool.query(
      `SELECT id, request_id, ts, actor, method, path, status, inserted_at
       FROM platform_console.audit_log
       ${where}
       ORDER BY ts DESC, id DESC
       LIMIT $${values.length + 1} OFFSET $${values.length + 2}`,
      [...values, params.limit, params.offset],
    );

    const rows: AuditLogRow[] = rowsResult.rows.map((r) => ({
      id: Number(r.id),
      requestId: r.request_id as string,
      ts: new Date(r.ts as string).toISOString(),
      actor: r.actor as string,
      method: r.method as string,
      path: r.path as string,
      status: Number(r.status),
      insertedAt: new Date(r.inserted_at as string).toISOString(),
    }));

    return { ok: true, data: { rows, total } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

// ------------------------------------------------- Chain verification (control)

export interface AuditChainVerification {
  valid: boolean;
  rowsChecked: number;
  /** id of the first row whose stored row_hash does not match its recomputed
   * digest -- undefined when `valid` is true. */
  brokenAtId?: number;
  reason?: string;
}

export type AuditChainVerifyOutcome =
  | { ok: true; data: AuditChainVerification }
  | { ok: false; error: string };

/**
 * Real, live re-derivation of the entire hash chain -- reads every row in
 * insertion order, recomputes each row_hash from its own fields plus the
 * PRECEDING ROW'S STORED prev_hash (not the recomputed one, so a single
 * corrupted row is reported at exactly the row it was tampered, not
 * cascaded onto every row after it as "also broken" -- though the caller
 * can trivially see the cascade too: every row after the first break has
 * a prev_hash that no longer matches the (correctly recomputed) row
 * before it, once one is inspected). No caching, no sampling -- this is
 * the control itself, not a summary of it, so it always reads the live
 * table fresh.
 */
export async function verifyAuditChain(): Promise<AuditChainVerifyOutcome> {
  const pool = await resolveChainReadyPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }
  try {
    const result = await pool.query<{
      id: string;
      request_id: string;
      ts: string;
      actor: string;
      method: string;
      path: string;
      status: number;
      prev_hash: string | null;
      row_hash: string | null;
    }>(
      `SELECT id, request_id, ts, actor, method, path, status, prev_hash, row_hash
       FROM platform_console.audit_log
       ORDER BY id ASC`,
    );

    let expectedPrevHash = GENESIS_HASH;
    for (const r of result.rows) {
      const entry: AuditLogEntry = {
        requestId: r.request_id,
        timestamp: new Date(r.ts).toISOString(),
        actor: r.actor,
        method: r.method,
        path: r.path,
        status: Number(r.status),
      };
      if (r.prev_hash !== expectedPrevHash) {
        return {
          ok: true,
          data: {
            valid: false,
            rowsChecked: result.rows.length,
            brokenAtId: Number(r.id),
            reason: `row ${r.id}: stored prev_hash does not match the preceding row's stored row_hash -- a row was inserted, deleted, or reordered out of band`,
          },
        };
      }
      const recomputed = computeRowHash(expectedPrevHash, entry);
      if (recomputed !== r.row_hash) {
        return {
          ok: true,
          data: {
            valid: false,
            rowsChecked: result.rows.length,
            brokenAtId: Number(r.id),
            reason: `row ${r.id}: recomputed row_hash does not match the stored row_hash -- one or more of request_id/ts/actor/method/path/status was modified after insertion`,
          },
        };
      }
      expectedPrevHash = r.row_hash as string;
    }

    return { ok: true, data: { valid: true, rowsChecked: result.rows.length } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
