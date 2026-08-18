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

async function persistAuditLogEntry(entry: AuditLogEntry): Promise<void> {
  const pool = await resolvePool();
  if (!pool) return; // not configured / cluster DB unreachable -- the stdout line is still the real record for this environment
  await pool.query(
    `INSERT INTO platform_console.audit_log (request_id, ts, actor, method, path, status)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [entry.requestId, entry.timestamp, entry.actor, entry.method, entry.path, entry.status],
  );
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
