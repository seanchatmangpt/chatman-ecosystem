/**
 * Node.js-only durable persistence for the audit log -- the real
 * hyperscaler CloudTrail / GCP Audit Logs / Azure Monitor Activity Log
 * equivalent: a queryable "who did what" history, not just the ephemeral
 * pod-log line lib/audit-log.ts already writes (real, but gone the moment
 * a pod restarts).
 *
 * Deliberately a SEPARATE module from lib/audit-log.ts. Originally never
 * imported by middleware.ts, because middleware ran on the Next.js edge
 * runtime and the `pg` driver this module uses pulls in real Node.js
 * `net`/`tls` core modules the edge runtime cannot bundle -- the exact
 * same reason lib/credentials.ts (bcryptjs) was kept out of middleware.
 * middleware.ts now opts into `export const runtime = "nodejs"` (see its
 * own header comment, added to resolve Bearer API keys via lib/k8s.ts),
 * which makes this module safe to import there too -- middleware.ts's
 * generic per-request line ("authenticated and forwarded") now goes
 * through THIS module so it lands in the same durable, hash-chained
 * `platform_console.audit_log` table (with impersonation actor-tagging
 * attached when it applies) instead of only the ephemeral stdout line.
 * Every actual API action still ALSO logs its own, more specific entry
 * through this module from its own route handler.
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
import { createHash, randomBytes } from "node:crypto";

// Genesis value the first real row's prev_hash commits to -- distinguishable
// at a glance from any real sha256 digest (which is lowercase hex).
const GENESIS_HASH = "GENESIS-" + "0".repeat(56);

function computeRowHash(prevHash: string, entry: AuditLogEntry): string {
  const parts = [prevHash, entry.requestId, entry.timestamp, entry.actor, entry.method, entry.path, String(entry.status)];
  // Appended LAST, and only when present, so every row written before this
  // field existed recomputes to the exact same row_hash it always had --
  // backward-compatible with the chain already persisted. When present, it
  // is committed into this row's row_hash (and therefore into every row
  // hash after it), which is what makes it "cryptographically
  // cross-referenced": tampering with the recorded castle receipt digest
  // after the fact breaks this chain the same way tampering with actor or
  // status would.
  if (entry.castleReceiptDigest) parts.push(entry.castleReceiptDigest);
  // Same backward-compatible "appended last, only when present" rule as
  // castleReceiptDigest above -- every row written before impersonation
  // actor-tagging existed recomputes to its original row_hash unchanged.
  // Committing both fields into the chain means tampering with either one
  // after the fact (e.g. stripping impersonatedBy off a row to make a
  // support action look like normal customer activity) breaks the chain
  // exactly like tampering with actor or status would.
  if (entry.impersonatedBy) parts.push(entry.impersonatedBy);
  if (entry.impersonationSessionId) parts.push(entry.impersonationSessionId);
  const material = parts.join(" ");
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
  // Nullable, absent for every row that isn't a castle GymAct run -- see
  // AuditLogEntry.castleReceiptDigest's doc comment in lib/audit-log.ts.
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS castle_receipt_digest text`);
  // Impersonation actor-tagging columns -- same idempotent ADD COLUMN IF
  // NOT EXISTS self-bootstrap convention as every other column above and
  // as lib/impersonation.ts's own ensureImpersonationTable. Nullable,
  // absent for every non-impersonated row.
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS impersonated_by text`);
  await pool.query(
    `ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS impersonation_session_id text`,
  );
  await pool.query(
    `CREATE INDEX IF NOT EXISTS audit_log_impersonation_session_id_idx
       ON platform_console.audit_log (impersonation_session_id)
       WHERE impersonation_session_id IS NOT NULL`,
  );
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
      castle_receipt_digest: string | null;
    }>(
      `SELECT id, request_id, ts, actor, method, path, status, castle_receipt_digest
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
          ...(r.castle_receipt_digest ? { castleReceiptDigest: r.castle_receipt_digest } : {}),
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
      `INSERT INTO platform_console.audit_log
         (request_id, ts, actor, method, path, status, prev_hash, row_hash, castle_receipt_digest, impersonated_by, impersonation_session_id)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
      [
        entry.requestId,
        entry.timestamp,
        entry.actor,
        entry.method,
        entry.path,
        entry.status,
        prevHash,
        rowHash,
        entry.castleReceiptDigest ?? null,
        entry.impersonatedBy ?? null,
        entry.impersonationSessionId ?? null,
      ],
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

// ---------------------------------------------- Audit export tokens (SIEM)
//
// A narrowly-scoped bearer credential distinct from both the session
// cookie (lib/session.ts) and the general-purpose lib/api-keys.ts
// `pk_live_...` key: a Fortune-5 security team's Splunk/Datadog/Sentinel
// forwarder needs to poll GET /api/v1/audit-export on an unattended
// schedule, forever, with a credential that can be handed to that
// forwarder and revoked independently of any human's own API key or
// session -- never a credential that also happens to carry that human's
// full role (viewer/member/owner) over the rest of this console. Scope is
// therefore fixed at mint time to the single literal `"audit:read"`
// string (no other scope exists yet; the column is a real, checked value
// rather than an assumed one so a future second scope doesn't silently
// widen every already-issued token). Stored HASHED (SHA-256, one-way),
// same convention as lib/api-keys.ts's ApiKeyRecord.hash -- the plaintext
// token is shown exactly once, in the mint response, and never persisted.
//
// Table lives in the SAME `platform_console` schema/Postgres this module
// already owns (not a new k8s Secret) because the export flow this token
// gates -- queryAuditLog / verifyAuditChain -- already lives here, and a
// SIEM forwarder's credential lookup is a hot path (every scheduled poll)
// best served by a single indexed SELECT against a table already backed
// by a live connection pool, not a k8s Secret GET per request.
export type AuditExportScope = "audit:read";

export interface AuditExportTokenRecord {
  id: number;
  orgId: string;
  prefix: string; // shown in listings -- e.g. "aet_AbCd1234..." -- never the full token
  scope: AuditExportScope;
  createdBy: string;
  createdAt: string; // RFC3339
  revokedAt: string | null;
}

const AUDIT_EXPORT_TOKEN_PREFIX = "aet_live_";

async function ensureAuditExportTokensTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.audit_export_tokens (
      id          bigserial PRIMARY KEY,
      org_id      text NOT NULL,
      token_hash  text NOT NULL UNIQUE,
      prefix      text NOT NULL,
      scope       text NOT NULL,
      created_by  text NOT NULL,
      created_at  timestamptz NOT NULL DEFAULT now(),
      revoked_at  timestamptz
    )
  `);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS audit_export_tokens_org_id_idx
       ON platform_console.audit_export_tokens (org_id)`,
  );
}

let auditExportTokensTableReady: Promise<void> | null = null;

async function resolveAuditExportTokensPool(): Promise<Pool | null> {
  const pool = await resolvePool();
  if (!pool) return null;
  if (!auditExportTokensTableReady) {
    auditExportTokensTableReady = ensureAuditExportTokensTable(pool);
  }
  await auditExportTokensTableReady;
  return pool;
}

function toAuditExportTokenRecord(r: {
  id: string | number;
  org_id: string;
  prefix: string;
  scope: string;
  created_by: string;
  created_at: string;
  revoked_at: string | null;
}): AuditExportTokenRecord {
  return {
    id: Number(r.id),
    orgId: r.org_id,
    prefix: r.prefix,
    scope: r.scope as AuditExportScope,
    createdBy: r.created_by,
    createdAt: new Date(r.created_at).toISOString(),
    revokedAt: r.revoked_at ? new Date(r.revoked_at).toISOString() : null,
  };
}

export interface CreateAuditExportTokenResult {
  plaintext: string;
  record: AuditExportTokenRecord;
}

/**
 * Mints one new, owner-issued audit-export token for `orgId`. Real
 * cryptographically random material (`crypto.randomBytes(32)`,
 * base64url-encoded, 256 bits of entropy), same generation discipline as
 * lib/api-keys.ts's generateKeyMaterial -- only the prefix differs
 * (`aet_live_`, distinguishing this credential class from `pk_live_`
 * session-equivalent API keys at a glance in any log line that leaks a
 * prefix). Scope is always `"audit:read"` -- there is no broader scope to
 * request yet.
 */
export async function createAuditExportToken(input: {
  orgId: string;
  createdBy: string;
}): Promise<{ ok: true; data: CreateAuditExportTokenResult } | { ok: false; error: string }> {
  const pool = await resolveAuditExportTokensPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }
  const plaintext = `${AUDIT_EXPORT_TOKEN_PREFIX}${randomBytes(32).toString("base64url")}`;
  const hash = createHash("sha256").update(plaintext, "utf8").digest("hex");
  const prefix = `${plaintext.slice(0, AUDIT_EXPORT_TOKEN_PREFIX.length + 8)}...`;
  try {
    const result = await pool.query<{
      id: string;
      org_id: string;
      prefix: string;
      scope: string;
      created_by: string;
      created_at: string;
      revoked_at: string | null;
    }>(
      `INSERT INTO platform_console.audit_export_tokens
         (org_id, token_hash, prefix, scope, created_by)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, org_id, prefix, scope, created_by, created_at, revoked_at`,
      [input.orgId, hash, prefix, "audit:read", input.createdBy],
    );
    return {
      ok: true,
      data: { plaintext, record: toAuditExportTokenRecord(result.rows[0]) },
    };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export async function listAuditExportTokens(
  orgId: string,
): Promise<{ ok: true; data: AuditExportTokenRecord[] } | { ok: false; error: string }> {
  const pool = await resolveAuditExportTokensPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `SELECT id, org_id, prefix, scope, created_by, created_at, revoked_at
       FROM platform_console.audit_export_tokens
       WHERE org_id = $1
       ORDER BY created_at DESC`,
      [orgId],
    );
    return { ok: true, data: result.rows.map(toAuditExportTokenRecord) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export async function revokeAuditExportToken(
  orgId: string,
  id: number,
): Promise<{ ok: true; data: AuditExportTokenRecord } | { ok: false; error: string }> {
  const pool = await resolveAuditExportTokensPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }
  try {
    const result = await pool.query(
      `UPDATE platform_console.audit_export_tokens
       SET revoked_at = now()
       WHERE id = $1 AND org_id = $2 AND revoked_at IS NULL
       RETURNING id, org_id, prefix, scope, created_by, created_at, revoked_at`,
      [id, orgId],
    );
    if (result.rows.length === 0) {
      const existing = await pool.query(
        `SELECT id, org_id, prefix, scope, created_by, created_at, revoked_at
         FROM platform_console.audit_export_tokens WHERE id = $1 AND org_id = $2`,
        [id, orgId],
      );
      if (existing.rows.length === 0) {
        return { ok: false, error: `no audit export token found with id '${id}' for org '${orgId}'` };
      }
      return { ok: true, data: toAuditExportTokenRecord(existing.rows[0]) };
    }
    return { ok: true, data: toAuditExportTokenRecord(result.rows[0]) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export interface ResolvedAuditExportAuth {
  orgId: string;
  scope: AuditExportScope;
  tokenId: number;
}

/**
 * Resolves a presented `Authorization: Bearer aet_live_...` token into the
 * org+scope it authenticates as -- `null` on wrong prefix, no matching
 * hash, or a revoked token. Hash comparison uses `crypto.timingSafeEqual`
 * (via safeEqualHexDigests below), same timing-attack discipline as
 * lib/api-keys.ts's resolveApiKeyAuth.
 */
export async function resolveAuditExportToken(
  presentedToken: string,
): Promise<ResolvedAuditExportAuth | null> {
  if (!presentedToken.startsWith(AUDIT_EXPORT_TOKEN_PREFIX)) return null;
  const pool = await resolveAuditExportTokensPool();
  if (!pool) return null;
  const hash = createHash("sha256").update(presentedToken, "utf8").digest("hex");
  try {
    const result = await pool.query<{
      id: string;
      org_id: string;
      scope: string;
      revoked_at: string | null;
    }>(
      `SELECT id, org_id, scope, revoked_at
       FROM platform_console.audit_export_tokens
       WHERE token_hash = $1`,
      [hash],
    );
    const row = result.rows[0];
    if (!row || row.revoked_at) return null;
    return { orgId: row.org_id, scope: row.scope as AuditExportScope, tokenId: Number(row.id) };
  } catch {
    return null;
  }
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
  /** See AuditLogEntry.castleReceiptDigest -- absent for non-castle-GymAct rows. */
  castleReceiptDigest?: string;
  /** See AuditLogEntry.impersonatedBy/impersonationSessionId -- both absent for non-impersonated rows. */
  impersonatedBy?: string;
  impersonationSessionId?: string;
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
      `SELECT id, request_id, ts, actor, method, path, status, inserted_at, castle_receipt_digest,
              impersonated_by, impersonation_session_id
       FROM platform_console.audit_log
       ${where}
       ORDER BY ts DESC, id DESC
       LIMIT $${values.length + 1} OFFSET $${values.length + 2}`,
      [...values, params.limit, params.offset],
    );

    const rows: AuditLogRow[] = rowsResult.rows.map(toAuditLogRow);

    return { ok: true, data: { rows, total } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export interface AuditLogSinceResult {
  rows: AuditLogRow[];
  /** RFC3339 `ts` + row id of the last row returned, encoded as `<ts>|<id>` -- pass straight back as `since` on the next call. `undefined` when the batch was empty. */
  nextCursor?: string;
}

/**
 * Real keyset-paginated read for GET /api/v1/audit-export: every row with
 * `(ts, id) > since` (or every row, when `since` is omitted -- a fresh
 * SIEM forwarder's very first poll), oldest first, capped at `limit`.
 * Ordered ascending (unlike queryAuditLog's DESC, which serves the
 * human-facing /audit browser's "most recent first" page) because a SIEM
 * forwarder ingests a bounded window and must resume from exactly where
 * it left off -- ASC + `(ts, id) > cursor` is the same keyset-pagination
 * shape lib/audit-export.ts's fetchBatch already uses for its NDJNSON
 * export, applied here to the JSON/cursor contract this route needs
 * instead of that module's streaming NDJSON one.
 */
export async function queryAuditLogSince(
  since: string | undefined,
  limit: number,
): Promise<{ ok: true; data: AuditLogSinceResult } | { ok: false; error: string }> {
  const pool = await resolvePool();
  if (!pool) {
    return {
      ok: false,
      error:
        "audit log database not configured or unreachable -- see the stdout log (kubectl logs) for this environment's real-time record",
    };
  }

  let cursorTs: string | null = null;
  let cursorId: number | null = null;
  if (since) {
    const sepIdx = since.lastIndexOf("|");
    if (sepIdx > 0) {
      cursorTs = since.slice(0, sepIdx);
      cursorId = Number(since.slice(sepIdx + 1));
    } else {
      // Bare RFC3339 timestamp with no encoded row id -- treat as "every
      // row with ts > since", id unconstrained. Accepted so a caller can
      // hand-construct a `since` value from a wall-clock time, not only
      // from a previously-returned next_cursor.
      cursorTs = since;
      cursorId = null;
    }
  }

  const conditions: string[] = [];
  const values: unknown[] = [];
  if (cursorTs !== null && cursorId !== null && Number.isFinite(cursorId)) {
    values.push(cursorTs, cursorId);
    conditions.push(`(ts, id) > ($${values.length - 1}, $${values.length})`);
  } else if (cursorTs !== null) {
    values.push(cursorTs);
    conditions.push(`ts > $${values.length}`);
  }
  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  try {
    values.push(limit);
    const result = await pool.query(
      `SELECT id, request_id, ts, actor, method, path, status, inserted_at, castle_receipt_digest,
              impersonated_by, impersonation_session_id
       FROM platform_console.audit_log
       ${where}
       ORDER BY ts ASC, id ASC
       LIMIT $${values.length}`,
      values,
    );
    const rows: AuditLogRow[] = result.rows.map(toAuditLogRow);
    const last = rows[rows.length - 1];
    return {
      ok: true,
      data: { rows, nextCursor: last ? `${last.ts}|${last.id}` : undefined },
    };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

function toAuditLogRow(r: Record<string, unknown>): AuditLogRow {
  return {
    id: Number(r.id),
    requestId: r.request_id as string,
    ts: new Date(r.ts as string).toISOString(),
    actor: r.actor as string,
    method: r.method as string,
    path: r.path as string,
    status: Number(r.status),
    insertedAt: new Date(r.inserted_at as string).toISOString(),
    ...(r.castle_receipt_digest ? { castleReceiptDigest: r.castle_receipt_digest as string } : {}),
    ...(r.impersonated_by ? { impersonatedBy: r.impersonated_by as string } : {}),
    ...(r.impersonation_session_id
      ? { impersonationSessionId: r.impersonation_session_id as string }
      : {}),
  };
}

/**
 * Real, per-session read: every audit_log row tagged with one specific
 * impersonation_session_id, oldest first -- backs the "for one session
 * id, the exact list of actions taken" reviewer view on
 * GET /api/orgs/[id]/impersonation-log?sessionId=... . Distinct from
 * queryAuditLog above (which filters by actor/path/time and is meant for
 * the general /audit browser) -- this is the exact-match, no-pagination
 * lookup a reviewer wants when they already have one session id in hand
 * from listImpersonationSessionsForOrg.
 */
export async function queryAuditLogForImpersonationSession(
  impersonationSessionId: string,
): Promise<AuditLogQueryOutcome> {
  const pool = await resolvePool();
  if (!pool) {
    return {
      ok: false,
      error:
        "audit log database not configured or unreachable -- see the stdout log (kubectl logs) for this environment's real-time record",
    };
  }
  try {
    const rowsResult = await pool.query(
      `SELECT id, request_id, ts, actor, method, path, status, inserted_at, castle_receipt_digest,
              impersonated_by, impersonation_session_id
       FROM platform_console.audit_log
       WHERE impersonation_session_id = $1
       ORDER BY ts ASC, id ASC`,
      [impersonationSessionId],
    );
    const rows: AuditLogRow[] = rowsResult.rows.map(toAuditLogRow);
    return { ok: true, data: { rows, total: rows.length } };
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
      castle_receipt_digest: string | null;
      impersonated_by: string | null;
      impersonation_session_id: string | null;
    }>(
      `SELECT id, request_id, ts, actor, method, path, status, prev_hash, row_hash, castle_receipt_digest,
              impersonated_by, impersonation_session_id
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
        ...(r.castle_receipt_digest ? { castleReceiptDigest: r.castle_receipt_digest } : {}),
        ...(r.impersonated_by ? { impersonatedBy: r.impersonated_by } : {}),
        ...(r.impersonation_session_id
          ? { impersonationSessionId: r.impersonation_session_id }
          : {}),
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
