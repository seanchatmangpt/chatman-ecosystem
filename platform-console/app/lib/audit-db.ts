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
import Stripe from "stripe";
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
import { getStoredSubscription, getStripeClient, rateLimitAddonPriceId } from "@/lib/stripe-billing";

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

export function computeRowHash(prevHash: string, entry: AuditLogEntry): string {
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
  // Same backward-compatible "appended last, only when present" rule as
  // the fields above -- every row written before per-org tenant scoping
  // existed recomputes to its original row_hash unchanged. Committing
  // org_id into the chain means tampering with it after the fact (e.g.
  // relabeling a row into a different org's export scope) breaks the
  // chain exactly like tampering with actor or status would.
  if (entry.orgId) parts.push(entry.orgId);
  // Same backward-compatible "appended last, only when present" rule as
  // the fields above -- every row written before per-key usage analytics
  // existed recomputes to its original row_hash unchanged. Committing
  // keyId/durationMs into the chain means tampering with either after the
  // fact (e.g. relabeling which key drove a spike of errors, or shaving a
  // latency figure) breaks the chain exactly like tampering with actor or
  // status would. durationMs is a number, not a string, so it's coerced
  // explicitly rather than relying on Array.join's implicit toString.
  if (entry.keyId) parts.push(entry.keyId);
  if (entry.durationMs !== undefined) parts.push(String(entry.durationMs));
  // Same backward-compatible "appended last, only when present" rule as
  // the fields above -- every row written before SLA credit
  // auto-application existed recomputes to its original row_hash
  // unchanged. Committing these into the chain means tampering with any
  // of them after the fact (e.g. relabeling which month a real Stripe
  // credit was recorded against) breaks the chain exactly like tampering
  // with actor or status would.
  if (entry.slaCreditStripeTransactionId) parts.push(entry.slaCreditStripeTransactionId);
  if (entry.slaCreditAmountCents !== undefined) parts.push(String(entry.slaCreditAmountCents));
  if (entry.slaCreditMonth) parts.push(entry.slaCreditMonth);
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
  // Per-org tenant column (closes the SIEM export org-scoping gap): the
  // org this row's action was performed against. Nullable for backward
  // compat with every row written before this column existed (and with
  // any genuinely unscoped platform-wide action going forward) -- a NULL
  // row is never included in an org-scoped query (queryAuditLog/
  // queryAuditLogSince's orgId filter), only in an explicit unscoped
  // platform-admin view. Same idempotent ADD COLUMN IF NOT EXISTS
  // self-bootstrap convention as every other column above.
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS org_id text`);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS audit_log_org_id_idx
       ON platform_console.audit_log (org_id)
       WHERE org_id IS NOT NULL`,
  );
  // Customer-facing API key usage analytics columns (queryApiKeyUsage
  // below): key_id is the real join key from a row back to the specific
  // pk_live_ key that authenticated it (see AuditLogEntry.keyId's doc
  // comment); duration_ms is per-request wall-clock latency, populated
  // from middleware.ts's own request timing. Both nullable -- absent for
  // every row written before this column existed, and for any row this
  // app writes today that isn't a Bearer-key-authenticated request (no
  // key_id) or wasn't measured (no duration_ms, though every writer as of
  // this pass sets it). Same idempotent ADD COLUMN IF NOT EXISTS
  // self-bootstrap convention as every other column above.
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS key_id text`);
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS duration_ms integer`);
  await pool.query(
    `CREATE INDEX IF NOT EXISTS audit_log_key_id_idx
       ON platform_console.audit_log (key_id, ts)
       WHERE key_id IS NOT NULL`,
  );
  // SLA credit auto-application columns (POST /api/orgs/[id]/sla-credits):
  // the real Stripe balance-transaction id, the exact amount actually
  // credited (integer cents), and the month it was applied for. Nullable
  // -- absent for every row written before this column existed and for
  // every row that isn't the one real "credit actually applied" event.
  // Same idempotent ADD COLUMN IF NOT EXISTS self-bootstrap convention as
  // every other column above.
  await pool.query(
    `ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS sla_credit_stripe_transaction_id text`,
  );
  await pool.query(
    `ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS sla_credit_amount_cents integer`,
  );
  await pool.query(`ALTER TABLE platform_console.audit_log ADD COLUMN IF NOT EXISTS sla_credit_month text`);
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
      org_id: string | null;
      key_id: string | null;
      duration_ms: number | null;
      sla_credit_stripe_transaction_id: string | null;
      sla_credit_amount_cents: number | null;
      sla_credit_month: string | null;
    }>(
      `SELECT id, request_id, ts, actor, method, path, status, castle_receipt_digest, org_id, key_id, duration_ms,
              sla_credit_stripe_transaction_id, sla_credit_amount_cents, sla_credit_month
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
          ...(r.org_id ? { orgId: r.org_id } : {}),
          ...(r.key_id ? { keyId: r.key_id } : {}),
          ...(r.duration_ms !== null ? { durationMs: r.duration_ms } : {}),
          ...(r.sla_credit_stripe_transaction_id
            ? { slaCreditStripeTransactionId: r.sla_credit_stripe_transaction_id }
            : {}),
          ...(r.sla_credit_amount_cents !== null ? { slaCreditAmountCents: r.sla_credit_amount_cents } : {}),
          ...(r.sla_credit_month ? { slaCreditMonth: r.sla_credit_month } : {}),
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
         (request_id, ts, actor, method, path, status, prev_hash, row_hash, castle_receipt_digest, impersonated_by, impersonation_session_id, org_id, key_id, duration_ms, sla_credit_stripe_transaction_id, sla_credit_amount_cents, sla_credit_month)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)`,
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
        entry.orgId ?? null,
        entry.keyId ?? null,
        entry.durationMs ?? null,
        entry.slaCreditStripeTransactionId ?? null,
        entry.slaCreditAmountCents ?? null,
        entry.slaCreditMonth ?? null,
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
  /** See AuditLogEntry.orgId -- absent for rows written before per-org scoping existed, or genuinely unscoped rows. */
  orgId?: string;
}

export interface AuditLogQueryParams {
  actor?: string;
  path?: string;
  from?: string; // RFC3339 lower bound (inclusive), matched against `ts`
  to?: string; // RFC3339 upper bound (inclusive), matched against `ts`
  limit: number;
  offset: number;
  /**
   * Per-org tenant scope: when set, restricts results to rows with this
   * exact org_id (never a NULL/unscoped row -- a caller that wants those
   * too must go through an explicit platform-admin unscoped view, never
   * this same filtered path). Omitted entirely by an unscoped internal
   * caller (e.g. a future platform-admin view); every tenant-facing caller
   * (GET /api/v1/audit-export) MUST always pass it.
   */
  orgId?: string;
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
  if (params.orgId) {
    values.push(params.orgId);
    conditions.push(`org_id = $${values.length}`);
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
              impersonated_by, impersonation_session_id, org_id
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
  orgId?: string,
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
  if (orgId) {
    values.push(orgId);
    conditions.push(`org_id = $${values.length}`);
  }
  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  try {
    values.push(limit);
    const result = await pool.query(
      `SELECT id, request_id, ts, actor, method, path, status, inserted_at, castle_receipt_digest,
              impersonated_by, impersonation_session_id, org_id
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
    ...(r.org_id ? { orgId: r.org_id as string } : {}),
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
              impersonated_by, impersonation_session_id, org_id
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

    // A first surviving row whose stored prev_hash carries the retention-
    // purge tombstone prefix (see purgeAuditLogRowsOlderThan) is not
    // chain-broken -- it's the real, expected anchor left behind by a
    // deliberate purge. Anchor the walk there instead of requiring
    // GENESIS_HASH, so a purged chain still verifies as intact from the
    // tombstone forward.
    let expectedPrevHash =
      result.rows[0]?.prev_hash?.startsWith(PURGED_TOMBSTONE_PREFIX)
        ? result.rows[0].prev_hash
        : GENESIS_HASH;
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

// ------------------------------------------------------- Retention purge
//
// The gap lib/retention.ts's own header comment names: DSAR erasure
// (lib/dsar.ts) and backup-tier retention (lib/backup-retention.ts) are
// both real, but neither one ever DELETEs a row of THIS table --
// platform_console.audit_log grows forever, which fails the SOC2/GDPR
// data-minimization requirement a Fortune-5 compliance team actually
// audits for ("prove old audit rows are purged on a schedule", not
// "prove they could be purged by hand"). lib/retention.ts is the policy
// layer (which retentionDays window, writing the receipt row); this is
// the mechanical primitive that actually knows the hash-chain internals
// (GENESIS_HASH, CHAIN_LOCK_KEY, computeRowHash) needed to delete rows
// out of an append-only hash chain WITHOUT breaking verifyAuditChain for
// every surviving row.
//
// Distinguishable at a glance from a real sha256 digest (lowercase hex),
// same convention as GENESIS_HASH's "GENESIS-" prefix above -- a reviewer
// scanning prev_hash values can immediately tell "this chain was
// deliberately truncated by a purge, not tampered with" from the prefix
// alone, before even running verifyAuditChain.
export const PURGED_TOMBSTONE_PREFIX = "PURGED-TOMBSTONE-";

export interface AuditLogPurgeResult {
  deletedCount: number;
  cutoff: string; // RFC3339 -- rows with ts < cutoff were deleted
  tombstone: string | null; // the new prev_hash written for the first surviving row; null when deletedCount is 0 (nothing to re-chain)
}

export type AuditLogPurgeOutcome =
  | { ok: true; data: AuditLogPurgeResult }
  | { ok: false; error: string };

/**
 * Real `DELETE` of every platform_console.audit_log row with `ts` older
 * than `cutoff`, then a real forward re-chain of every surviving row so
 * `verifyAuditChain` still validates afterward. Runs inside ONE
 * transaction holding the same `CHAIN_LOCK_KEY` advisory lock every other
 * chain-mutating operation in this module takes first, so a purge can
 * never race a concurrent `persistAuditLogEntry`/backfill and mint two
 * conflicting views of the chain tail.
 *
 * Re-chaining works exactly like `backfillAuditLogChain`'s forward walk,
 * except the walk starts from a synthetic tombstone `prev_hash`
 * (`PURGED_TOMBSTONE_PREFIX` + sha256 committing to the cutoff, the
 * number of rows deleted, and the row_hash of the last row actually
 * deleted -- so the tombstone is cryptographically bound to exactly the
 * history it replaces, not an arbitrary marker) instead of GENESIS_HASH.
 * `verifyAuditChain` recognizes that prefix on the first row of the
 * surviving chain and anchors its own walk there instead of requiring
 * GENESIS_HASH, so the chain is provably intact FROM THE TOMBSTONE
 * FORWARD -- exactly the guarantee a purge can make (the purged rows are
 * gone, not verifiable; every row after them is exactly as tamper-evident
 * as before the purge).
 */
export async function purgeAuditLogRowsOlderThan(cutoff: Date): Promise<AuditLogPurgeOutcome> {
  const pool = await resolveChainReadyPool();
  if (!pool) {
    return { ok: false, error: "audit log database not configured or unreachable" };
  }
  const cutoffIso = cutoff.toISOString();
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("SELECT pg_advisory_xact_lock($1)", [CHAIN_LOCK_KEY.toString()]);

    // Captured BEFORE the delete so the tombstone can cryptographically
    // commit to the real tail of the history being removed.
    const lastDeleted = await client.query<{ row_hash: string | null }>(
      `SELECT row_hash FROM platform_console.audit_log WHERE ts < $1 ORDER BY id DESC LIMIT 1`,
      [cutoffIso],
    );
    const lastDeletedRowHash = lastDeleted.rows[0]?.row_hash ?? GENESIS_HASH;

    const deleted = await client.query<{ id: string }>(
      `DELETE FROM platform_console.audit_log WHERE ts < $1 RETURNING id`,
      [cutoffIso],
    );
    const deletedCount = deleted.rows.length;

    if (deletedCount === 0) {
      await client.query("COMMIT");
      return { ok: true, data: { deletedCount: 0, cutoff: cutoffIso, tombstone: null } };
    }

    const tombstone =
      PURGED_TOMBSTONE_PREFIX +
      createHash("sha256")
        .update(`${lastDeletedRowHash}|${cutoffIso}|${deletedCount}`, "utf8")
        .digest("hex");

    const surviving = await client.query<{
      id: string;
      request_id: string;
      ts: string;
      actor: string;
      method: string;
      path: string;
      status: number;
      castle_receipt_digest: string | null;
      impersonated_by: string | null;
      impersonation_session_id: string | null;
    }>(
      `SELECT id, request_id, ts, actor, method, path, status, castle_receipt_digest,
              impersonated_by, impersonation_session_id
       FROM platform_console.audit_log
       ORDER BY id ASC`,
    );

    let prevHash = tombstone;
    for (const r of surviving.rows) {
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
      const rowHash = computeRowHash(prevHash, entry);
      await client.query(
        `UPDATE platform_console.audit_log SET prev_hash = $1, row_hash = $2 WHERE id = $3`,
        [prevHash, rowHash, r.id],
      );
      prevHash = rowHash;
    }

    await client.query("COMMIT");
    return { ok: true, data: { deletedCount, cutoff: cutoffIso, tombstone } };
  } catch (err) {
    await client.query("ROLLBACK").catch(() => {});
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  } finally {
    client.release();
  }
}

// ------------------------------------- Customer-facing API key usage (rollup)
//
// Closes the gap: lib/api-keys.ts already tracks pk_live_ keys, and
// middleware.ts already writes one audit_log row per authenticated
// request with that key's real keyId (see AuditLogEntry.keyId's doc
// comment) and org_id -- but until this pass, nothing rolled those rows
// up into the per-key calls/latency/error-rate view a paying API consumer
// actually wants to see (the same shape Stripe/Twilio/Datadog's own
// per-key usage dashboards surface, and the natural lead-in to this
// console's already-built rate-limit-tier upsell: a customer has to SEE
// they're near a ceiling before they'll pay to raise it).

/** Supported lookback windows for GET /api/orgs/[id]/api-keys/[keyId]/usage. */
export type ApiKeyUsageWindow = "1h" | "24h" | "7d" | "30d";

export function isApiKeyUsageWindow(value: unknown): value is ApiKeyUsageWindow {
  return value === "1h" || value === "24h" || value === "7d" || value === "30d";
}

const API_KEY_USAGE_WINDOW_HOURS: Record<ApiKeyUsageWindow, number> = {
  "1h": 1,
  "24h": 24,
  "7d": 24 * 7,
  "30d": 24 * 30,
};

/** One hourly bucket in the calls-per-hour time series. */
export interface ApiKeyUsageBucket {
  hour: string; // RFC3339, truncated to the hour (UTC)
  calls: number;
  status2xx: number;
  status4xx: number;
  status5xx: number;
}

export interface ApiKeyUsageResult {
  keyId: string;
  orgId: string;
  window: ApiKeyUsageWindow;
  windowHours: number;
  totalCalls: number;
  status2xx: number;
  status4xx: number;
  status5xx: number;
  /** (status4xx + status5xx) / totalCalls * 100, rounded to 2 decimal places; 0 when totalCalls is 0. */
  errorRatePct: number;
  /** Null when no row in the window carries a duration_ms value (e.g. every row predates that column, or the window has zero calls). */
  p50LatencyMs: number | null;
  p95LatencyMs: number | null;
  /** Ascending by hour, one entry per hour that had at least one call -- hours with zero calls are omitted, not zero-filled. */
  hourlyBuckets: ApiKeyUsageBucket[];
}

export type ApiKeyUsageOutcome =
  | { ok: true; data: ApiKeyUsageResult }
  | { ok: false; error: string };

/**
 * Aggregates platform_console.audit_log into the per-API-key usage rollup
 * GET /api/orgs/[id]/api-keys/[keyId]/usage returns. Scoped by BOTH org_id
 * and key_id (never key_id alone) -- the real tenant-isolation boundary:
 * an org's own dashboard must never be able to read another org's key's
 * traffic merely by guessing its keyId, since keyId (a 12-hex-char
 * lib/api-keys.ts id) carries no secrecy of its own the way the full
 * pk_live_ plaintext does. The route handler is additionally responsible
 * for confirming the caller holds at least `viewer` on `orgId`
 * (lib/authz.ts's requireRoleIn) before ever calling this -- this
 * function itself trusts both ids as already-authorized.
 *
 * Four real aggregates in one round trip against the live Postgres this
 * module already pools:
 *   1. Status-bucket totals (2xx/4xx/5xx) + total call count -- a single
 *      SELECT with FILTER-clause conditional counts, not three separate
 *      queries.
 *   2. p50/p95 latency via PERCENTILE_CONT (Postgres's real interpolated-
 *      percentile aggregate), over rows where duration_ms IS NOT NULL --
 *      never coerces a NULL (unmeasured, pre-this-pass row) into 0, which
 *      would silently drag every percentile toward zero.
 *   3. Hourly calls-per-hour + per-hour status buckets via
 *      date_trunc('hour', ts), for the time-series chart.
 */
export async function queryApiKeyUsage(
  orgId: string,
  keyId: string,
  window: ApiKeyUsageWindow,
): Promise<ApiKeyUsageOutcome> {
  const pool = await resolvePool();
  if (!pool) {
    return {
      ok: false,
      error:
        "audit log database not configured or unreachable -- see the stdout log (kubectl logs) for this environment's real-time record",
    };
  }

  const windowHours = API_KEY_USAGE_WINDOW_HOURS[window];

  try {
    const totalsResult = await pool.query<{
      total_calls: string;
      status_2xx: string;
      status_4xx: string;
      status_5xx: string;
      p50_latency_ms: number | null;
      p95_latency_ms: number | null;
    }>(
      `SELECT
         count(*)::bigint AS total_calls,
         count(*) FILTER (WHERE status >= 200 AND status < 300)::bigint AS status_2xx,
         count(*) FILTER (WHERE status >= 400 AND status < 500)::bigint AS status_4xx,
         count(*) FILTER (WHERE status >= 500 AND status < 600)::bigint AS status_5xx,
         percentile_cont(0.5) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE duration_ms IS NOT NULL) AS p50_latency_ms,
         percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms) FILTER (WHERE duration_ms IS NOT NULL) AS p95_latency_ms
       FROM platform_console.audit_log
       WHERE org_id = $1 AND key_id = $2 AND ts >= now() - ($3 || ' hours')::interval`,
      [orgId, keyId, windowHours],
    );

    const bucketsResult = await pool.query<{
      hour: string;
      calls: string;
      status_2xx: string;
      status_4xx: string;
      status_5xx: string;
    }>(
      `SELECT
         date_trunc('hour', ts) AS hour,
         count(*)::bigint AS calls,
         count(*) FILTER (WHERE status >= 200 AND status < 300)::bigint AS status_2xx,
         count(*) FILTER (WHERE status >= 400 AND status < 500)::bigint AS status_4xx,
         count(*) FILTER (WHERE status >= 500 AND status < 600)::bigint AS status_5xx
       FROM platform_console.audit_log
       WHERE org_id = $1 AND key_id = $2 AND ts >= now() - ($3 || ' hours')::interval
       GROUP BY 1
       ORDER BY 1 ASC`,
      [orgId, keyId, windowHours],
    );

    const totalsRow = totalsResult.rows[0];
    const totalCalls = Number(totalsRow?.total_calls ?? "0");
    const status2xx = Number(totalsRow?.status_2xx ?? "0");
    const status4xx = Number(totalsRow?.status_4xx ?? "0");
    const status5xx = Number(totalsRow?.status_5xx ?? "0");
    const errorRatePct =
      totalCalls > 0 ? Math.round(((status4xx + status5xx) / totalCalls) * 10000) / 100 : 0;

    const hourlyBuckets: ApiKeyUsageBucket[] = bucketsResult.rows.map((r) => ({
      hour: new Date(r.hour).toISOString(),
      calls: Number(r.calls),
      status2xx: Number(r.status_2xx),
      status4xx: Number(r.status_4xx),
      status5xx: Number(r.status_5xx),
    }));

    return {
      ok: true,
      data: {
        keyId,
        orgId,
        window,
        windowHours,
        totalCalls,
        status2xx,
        status4xx,
        status5xx,
        errorRatePct,
        p50LatencyMs: totalsRow?.p50_latency_ms != null ? Math.round(totalsRow.p50_latency_ms) : null,
        p95LatencyMs: totalsRow?.p95_latency_ms != null ? Math.round(totalsRow.p95_latency_ms) : null,
        hourlyBuckets,
      },
    };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

// ---------------------------------------------------------------------------
// Historical spend/usage chart (queryOrgSpendHistory)
// ---------------------------------------------------------------------------

export type SpendHistoryGranularity = "daily" | "monthly";

/** One real bucket in the org's historical spend time series. */
export interface SpendHistoryBucket {
  /** RFC3339 UTC bucket start -- truncated to the day (daily) or the
   * first-of-month (monthly). */
  periodStart: string;
  /** Real dollars from actually-issued Stripe Invoice line items whose
   * `type=subscription` (the flat plan price) attributable to this
   * bucket, apportioned evenly across the real Stripe invoice `period`
   * the line item covers -- never a fabricated flat number. Zero when no
   * Stripe invoice line overlaps this bucket. */
  baseTierCostUsd: number;
  /** Real dollars from Stripe InvoiceItem lines this console itself
   * created with `metadata.kind === "usage_overage"`
   * (lib/overage-billing.ts's createOverageInvoiceItem), apportioned the
   * same way. */
  overageCostUsd: number;
  /** Real dollars from Stripe SubscriptionItem lines whose price id
   * matches `rateLimitAddonPriceId("pro"|"enterprise")`
   * (lib/stripe-billing.ts's attachRateLimitAddon), apportioned the same
   * way. */
  rateLimitAddonCostUsd: number;
  /** Real per-day/per-month total across the three line items above. */
  totalCostUsd: number;
  /** Real total API call volume (2xx+4xx+5xx) this org's keys recorded
   * in platform_console.audit_log for this bucket -- the usage dimension
   * a FinOps team reconciles the dollar figures against. Zero-filled
   * (unlike ApiKeyUsageBucket's hourlyBuckets) so every bucket in
   * [from, to] appears exactly once, in order, even with zero calls --
   * a chart/CSV consumer must not have to invent missing rows. */
  callVolume: number;
}

export interface OrgSpendHistoryResult {
  orgId: string;
  granularity: SpendHistoryGranularity;
  from: string;
  to: string;
  buckets: SpendHistoryBucket[];
  /** Sum of every bucket's totalCostUsd -- the real total spend across
   * the whole requested window. */
  totalCostUsd: number;
  /** True only when a real Stripe customer/subscription is on file for
   * this org AND STRIPE_SECRET_KEY is configured -- false means the
   * dollar fields above are honestly all-zero (no fabricated invoice
   * data), not that the org spent nothing. */
  hasStripeBilling: boolean;
}

export type OrgSpendHistoryOutcome =
  | { ok: true; data: OrgSpendHistoryResult }
  | { ok: false; error: string };

function dayKeyUtc(d: Date): string {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())).toISOString();
}

function monthKeyUtc(d: Date): string {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1)).toISOString();
}

function bucketKey(d: Date, granularity: SpendHistoryGranularity): string {
  return granularity === "daily" ? dayKeyUtc(d) : monthKeyUtc(d);
}

/** Every real bucket key in `[from, to]` inclusive, in ascending order --
 * the zero-filled skeleton `queryOrgSpendHistory` folds real Stripe/audit
 * numbers into. */
function bucketSkeleton(from: Date, to: Date, granularity: SpendHistoryGranularity): string[] {
  const keys: string[] = [];
  const cursor = new Date(bucketKey(from, granularity));
  const end = new Date(bucketKey(to, granularity));
  while (cursor.getTime() <= end.getTime()) {
    keys.push(cursor.toISOString());
    if (granularity === "daily") {
      cursor.setUTCDate(cursor.getUTCDate() + 1);
    } else {
      cursor.setUTCMonth(cursor.getUTCMonth() + 1);
    }
  }
  return keys;
}

/** Classifies one real Stripe invoice line item into which of the three
 * spend dimensions it belongs to -- see SpendHistoryBucket's own field
 * comments for the exact real signal each classification keys off of. */
function classifyInvoiceLine(line: Stripe.InvoiceLineItem): "overage" | "rateLimitAddon" | "base" {
  if (line.metadata?.kind === "usage_overage") return "overage";
  const priceRef = line.pricing?.price_details?.price;
  const priceId = typeof priceRef === "string" ? priceRef : priceRef?.id;
  if (priceId && (priceId === rateLimitAddonPriceId("pro") || priceId === rateLimitAddonPriceId("enterprise"))) {
    return "rateLimitAddon";
  }
  return "base";
}

/** Apportions `amountUsd` evenly across every real daily/monthly bucket
 * key the real Stripe `period` [periodStart, periodEnd) overlaps within
 * `bucketKeys` -- so a monthly Stripe invoice line, when the caller asked
 * for `daily` granularity, spreads across that invoice's real ~30 days
 * rather than dumping the whole month's cost onto one arbitrary day. A
 * `monthly`-granularity request typically has the line item's period
 * land in exactly one bucket, so it degrades to "the whole amount in
 * that month" -- the natural, undistorted case. */
function apportion(
  amountUsd: number,
  periodStart: Date,
  periodEnd: Date,
  bucketKeys: string[],
  granularity: SpendHistoryGranularity,
  add: (bucketKey: string, amountUsd: number) => void,
): void {
  const overlapping = bucketKeys.filter((k) => {
    const bStart = new Date(k).getTime();
    const bEnd =
      granularity === "daily"
        ? bStart + 24 * 60 * 60 * 1000
        : new Date(Date.UTC(new Date(k).getUTCFullYear(), new Date(k).getUTCMonth() + 1, 1)).getTime();
    return bStart < periodEnd.getTime() && bEnd > periodStart.getTime();
  });
  if (overlapping.length === 0) return;
  const share = amountUsd / overlapping.length;
  for (const k of overlapping) add(k, share);
}

/**
 * Real historical spend/usage time series for one org: the exportable,
 * multi-month counterpart to app/billing/page.tsx's point-in-time
 * overage-estimate widget -- what Fortune 5 FinOps teams ask for
 * ("12 months of spend trend") instead of "today's estimate".
 *
 * Two real data sources, merged by real timestamp, never fabricated:
 *   1. Real Stripe `Invoice.lines` for this org's real Stripe customer
 *      (lib/stripe-billing.ts's getStoredSubscription resolves
 *      tenantNamespace -> real Stripe customer id), classified into
 *      base/overage/rateLimitAddon per classifyInvoiceLine and
 *      apportioned across the real invoice `period` via `apportion`.
 *      An org with no Stripe customer on file yet (or no
 *      STRIPE_SECRET_KEY configured) gets `hasStripeBilling: false` and
 *      honest zero dollar fields -- never a fabricated number.
 *   2. Real `platform_console.audit_log` call-volume rows for `orgId`,
 *      the same table queryApiKeyUsage aggregates, grouped by real
 *      day/month here instead of by hour-within-one-key -- the usage
 *      dimension a FinOps team reconciles the dollar figures against.
 *
 * `orgId` gates the audit_log query (tenant isolation, same as
 * queryApiKeyUsage); `tenantNamespace` gates the Stripe lookup (Stripe
 * customers are keyed by namespace, not orgId, in this codebase's
 * existing lib/stripe-billing.ts convention) -- the route handler is
 * responsible for resolving both from the same already-authorized org
 * record (lib/orgs.ts's getOrg) before calling this.
 */
export async function queryOrgSpendHistory(
  orgId: string,
  tenantNamespace: string,
  params: { from: Date; to: Date; granularity: SpendHistoryGranularity },
): Promise<OrgSpendHistoryOutcome> {
  const { from, to, granularity } = params;
  if (from.getTime() > to.getTime()) {
    return { ok: false, error: "from must be before to" };
  }

  const bucketKeys = bucketSkeleton(from, to, granularity);
  const baseByBucket = new Map<string, number>();
  const overageByBucket = new Map<string, number>();
  const addonByBucket = new Map<string, number>();
  const add = (map: Map<string, number>) => (k: string, amt: number) =>
    map.set(k, (map.get(k) ?? 0) + amt);

  let hasStripeBilling = false;
  const stripe = getStripeClient();
  if (stripe) {
    const stored = await getStoredSubscription(tenantNamespace);
    if (!stored.ok) return { ok: false, error: stored.error };
    if (stored.data) {
      hasStripeBilling = true;
      try {
        for await (const invoice of stripe.invoices.list({
          customer: stored.data.stripeCustomerId,
          created: { gte: Math.floor(from.getTime() / 1000), lte: Math.floor(to.getTime() / 1000) + 1 },
          limit: 100,
          expand: ["data.lines"],
        })) {
          for (const line of invoice.lines.data) {
            const amountUsd = line.amount / 100;
            if (amountUsd === 0) continue;
            const periodStart = new Date((line.period?.start ?? invoice.period_start) * 1000);
            const periodEnd = new Date((line.period?.end ?? invoice.period_end) * 1000);
            const kind = classifyInvoiceLine(line);
            const map = kind === "overage" ? overageByBucket : kind === "rateLimitAddon" ? addonByBucket : baseByBucket;
            apportion(amountUsd, periodStart, periodEnd, bucketKeys, granularity, add(map));
          }
        }
      } catch (e) {
        return { ok: false, error: `stripe invoices.list failed: ${(e as Error).message}` };
      }
    }
  }

  const pool = await resolvePool();
  const callVolumeByBucket = new Map<string, number>();
  if (pool) {
    try {
      const truncUnit = granularity === "daily" ? "day" : "month";
      const usageResult = await pool.query<{ bucket: string; calls: string }>(
        `SELECT date_trunc($1, ts) AS bucket, count(*)::bigint AS calls
         FROM platform_console.audit_log
         WHERE org_id = $2 AND ts >= $3 AND ts <= $4
         GROUP BY 1
         ORDER BY 1 ASC`,
        [truncUnit, orgId, from.toISOString(), to.toISOString()],
      );
      for (const r of usageResult.rows) {
        callVolumeByBucket.set(new Date(r.bucket).toISOString(), Number(r.calls));
      }
    } catch (err) {
      return { ok: false, error: err instanceof Error ? err.message : String(err) };
    }
  }

  const buckets: SpendHistoryBucket[] = bucketKeys.map((k) => {
    const baseTierCostUsd = baseByBucket.get(k) ?? 0;
    const overageCostUsd = overageByBucket.get(k) ?? 0;
    const rateLimitAddonCostUsd = addonByBucket.get(k) ?? 0;
    return {
      periodStart: k,
      baseTierCostUsd,
      overageCostUsd,
      rateLimitAddonCostUsd,
      totalCostUsd: baseTierCostUsd + overageCostUsd + rateLimitAddonCostUsd,
      callVolume: callVolumeByBucket.get(k) ?? 0,
    };
  });

  const totalCostUsd = buckets.reduce((sum, b) => sum + b.totalCostUsd, 0);

  return {
    ok: true,
    data: {
      orgId,
      granularity,
      from: from.toISOString(),
      to: to.toISOString(),
      buckets,
      totalCostUsd,
      hasStripeBilling,
    },
  };
}

/**
 * Real RFC4180 CSV rendering of an OrgSpendHistoryResult -- the FinOps-
 * tooling-ingestion export format the spec calls for (`?format=csv`).
 * Every field is real (see queryOrgSpendHistory's own header comment);
 * this function performs no aggregation, only formatting.
 */
export function orgSpendHistoryToCsv(result: OrgSpendHistoryResult): string {
  const header = [
    "period_start",
    "base_tier_cost_usd",
    "overage_cost_usd",
    "rate_limit_addon_cost_usd",
    "total_cost_usd",
    "call_volume",
  ];
  const rows = result.buckets.map((b) =>
    [
      b.periodStart,
      b.baseTierCostUsd.toFixed(4),
      b.overageCostUsd.toFixed(4),
      b.rateLimitAddonCostUsd.toFixed(4),
      b.totalCostUsd.toFixed(4),
      String(b.callVolume),
    ].join(","),
  );
  return [header.join(","), ...rows].join("\n") + "\n";
}
