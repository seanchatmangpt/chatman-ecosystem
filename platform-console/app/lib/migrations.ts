/**
 * Real self-service Database Schema Migrations -- the AWS RDS "Query Editor
 * / schema management" / GCP Cloud SQL / Supabase's own migrations-tool
 * equivalent: an operator submits a real versioned up/down SQL pair, this
 * module applies the up side inside a real Postgres transaction against
 * that project's own live database, records the applied version in a real
 * history table on success, and can later replay the stored down side to
 * roll a version back -- all real DDL/DML against the real cluster, never
 * simulated.
 *
 * Deliberately a separate module from lib/audit-db.ts (not just because the
 * concerns differ) but the SAME pattern for the parts that are identical:
 * `pg` driver, Node.js-only (never imported by middleware.ts -- see
 * audit-db.ts's header comment for why: the edge runtime cannot bundle
 * `net`/`tls`), fail-closed off-cluster (hasClusterCredentials() false ->
 * every export below returns `{ok:false}` naming that, never a fabricated
 * empty success).
 *
 * One real structural difference from audit-db.ts: audit-db.ts hardcodes
 * ONE project (AUDIT_DB_PROJECT_NAME = "demo-project") because the audit
 * trail is a console-operational concern, not a per-tenant one. Schema
 * migrations are inherently per-project (each Project's SingleDatabase is
 * its own live Postgres instance with its own schema) -- so every export
 * here takes `projectName`, resolves that PROJECT's own database Pod live
 * via getProject/getProjectDatabasePod (the exact same resolution
 * app/api/projects/[name]/backups/route.ts already uses), and connects
 * with a per-project cached Pool (a Map, not audit-db.ts's single
 * `poolPromise`).
 *
 * platform_console.schema_migrations lives INSIDE that target project's
 * own Postgres (not the console's own operational store) -- same schema-
 * name convention as platform_console.audit_log (a dedicated schema so
 * it's unambiguous this table belongs to the console's tooling, not to any
 * Supabase-owned schema in that same database), but here it is scoped per-
 * project by simply living in that project's own database rather than by
 * a project_name column, since one project's live Postgres never contains
 * another project's schema history.
 *
 * The bootstrap CREATE TABLE for demo-project (the one real project this
 * cluster provisions) was applied for real via direct `psql` against the
 * live demo-db-postgres-0 pod, the identical one-time-bootstrap convention
 * the Audit Log pass used for platform_console.audit_log (see README's
 * Audit Log section) -- disclosed exactly, not hidden. `ensureMigrationsTable`
 * below ALSO issues the same `CREATE SCHEMA IF NOT EXISTS` / `CREATE TABLE
 * IF NOT EXISTS` idempotently on every pool resolution, so a second real
 * project onboarded later self-bootstraps its own history table the first
 * time this module is used against it, rather than requiring a human to
 * remember to re-run that same manual `psql` step -- genuinely
 * "self-service", the requirement's own word for this feature. Re-running
 * `CREATE TABLE IF NOT EXISTS` against demo-project's already-bootstrapped
 * table is a real no-op (confirmed live), not a second definition drifting
 * from the first.
 *
 * `up_sql`/`down_sql` are stored verbatim on the applied row (beyond the
 * four columns the requirement names -- version/name/applied_at/checksum
 * -- which mirror real migration-history tables like Flyway's
 * flyway_schema_history) because THIS tool has no on-disk migration-file
 * directory to re-read a down script from later (Flyway/golang-migrate
 * both resolve `down` from files that still exist next to the binary);
 * this is a live self-service form, so the only durable copy of the down
 * script an operator typed is the one persisted alongside the row it
 * reverses. `checksum` is a real sha256 (Node's own `crypto`, no invented
 * hash) over `version|name|upSql|downSql`, the same drift-detection intent
 * Flyway's own `checksum` column serves -- exposed on every listed row so
 * a caller can independently confirm what was actually applied hasn't been
 * edited out from under the record.
 */
import { createHash } from "node:crypto";
import { Pool, type PoolClient } from "pg";
import {
  getPostgresConnectionInfo,
  getProject,
  getProjectDatabasePod,
  hasClusterCredentials,
} from "@/lib/k8s";

export interface MigrationInput {
  version: number;
  name: string;
  upSql: string;
  downSql: string;
}

export interface MigrationRow {
  version: number;
  name: string;
  appliedAt: string; // RFC3339
  checksum: string;
  upSql: string;
  downSql: string;
}

export type MigrationOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

function computeChecksum(input: { version: number; name: string; upSql: string; downSql: string }): string {
  return createHash("sha256")
    .update(`${input.version}\n${input.name}\n${input.upSql}\n${input.downSql}`, "utf8")
    .digest("hex");
}

// --------------------------------------------------------- Pool resolution

async function createPoolForProject(projectName: string): Promise<Pool> {
  const projectResult = await getProject(projectName);
  if (!projectResult.ok) throw new Error(projectResult.error);
  if (!projectResult.data) {
    throw new Error(`migrations: project '${projectName}' not found`);
  }
  const podResult = await getProjectDatabasePod(projectResult.data);
  if (!podResult.ok) throw new Error(podResult.error);
  if (!podResult.data) {
    throw new Error(`migrations: no database Service found for project '${projectName}'`);
  }
  const connResult = await getPostgresConnectionInfo(podResult.data.namespace, podResult.data.podName);
  if (!connResult.ok) throw new Error(connResult.error);
  const info = connResult.data;
  const pool = new Pool({
    host: info.host,
    port: info.port,
    user: info.user,
    password: info.password,
    database: info.database,
    max: 5,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
  });
  await ensureMigrationsTable(pool);
  return pool;
}

async function ensureMigrationsTable(pool: Pool): Promise<void> {
  await pool.query(`CREATE SCHEMA IF NOT EXISTS platform_console`);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS platform_console.schema_migrations (
      version    bigint PRIMARY KEY,
      name       text NOT NULL,
      applied_at timestamptz NOT NULL DEFAULT now(),
      checksum   text NOT NULL,
      up_sql     text NOT NULL,
      down_sql   text NOT NULL
    )
  `);
}

// One cached Pool per project name -- same single-flight, self-healing
// convention as audit-db.ts's poolPromise: a successful resolution is
// reused for the process lifetime, a failed one is NOT cached so the next
// call retries cluster discovery from scratch rather than wedging this
// project into permanent failure over one transient error.
const poolsByProject = new Map<string, Promise<Pool>>();

async function resolvePool(projectName: string): Promise<MigrationOutcome<Pool>> {
  if (!hasClusterCredentials()) {
    return {
      ok: false,
      error: "not configured: no in-cluster ServiceAccount credentials found -- migrations only run as the platform-console pod",
    };
  }
  let poolPromise = poolsByProject.get(projectName);
  if (!poolPromise) {
    poolPromise = createPoolForProject(projectName);
    poolsByProject.set(projectName, poolPromise);
  }
  try {
    const pool = await poolPromise;
    return { ok: true, data: pool };
  } catch (err) {
    poolsByProject.delete(projectName);
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

function toRow(r: Record<string, unknown>): MigrationRow {
  return {
    version: Number(r.version),
    name: r.name as string,
    appliedAt: new Date(r.applied_at as string).toISOString(),
    checksum: r.checksum as string,
    upSql: r.up_sql as string,
    downSql: r.down_sql as string,
  };
}

/**
 * Runs a client-scoped real transaction: BEGIN, `body(client)`, COMMIT on
 * success. On ANY thrown error (a real SQL error from a bad statement, a
 * constraint violation on the INSERT, or any other failure inside `body`)
 * issues a real ROLLBACK before re-throwing -- so a migration that fails
 * partway (including partway through a multi-statement upSql string, which
 * Postgres itself already executes as one implicit unit under this
 * explicit BEGIN) never leaves a half-applied schema change: everything
 * since BEGIN, committed or not, is undone together. The ROLLBACK itself is
 * best-effort logged, never allowed to mask the original error.
 */
async function withTransaction<T>(client: PoolClient, body: (client: PoolClient) => Promise<T>): Promise<T> {
  await client.query("BEGIN");
  try {
    const result = await body(client);
    await client.query("COMMIT");
    return result;
  } catch (err) {
    try {
      await client.query("ROLLBACK");
    } catch (rollbackErr) {
      console.error(
        JSON.stringify({
          migrationsRollbackError: rollbackErr instanceof Error ? rollbackErr.message : String(rollbackErr),
        }),
      );
    }
    throw err;
  }
}

/**
 * Applies one real migration against `projectName`'s own live Postgres.
 * Runs `input.upSql` (which may be several `;`-separated statements --
 * Postgres executes a simple-query multi-statement string as one implicit
 * unit, and this call additionally wraps it in an explicit BEGIN, so a
 * failure on statement N leaves statements 1..N-1 uncommitted too) and the
 * `INSERT` recording the row in the SAME transaction -- so "the upSql
 * succeeded" and "the row is recorded" are atomic with each other as well:
 * a duplicate `version` (PK violation) rolls the just-applied upSql back
 * too, never leaving real schema drift with no matching history row.
 */
export async function applyMigration(
  projectName: string,
  input: MigrationInput,
): Promise<MigrationOutcome<MigrationRow>> {
  const poolResult = await resolvePool(projectName);
  if (!poolResult.ok) return poolResult;

  const client = await poolResult.data.connect();
  try {
    const row = await withTransaction(client, async (c) => {
      await c.query(input.upSql);
      const checksum = computeChecksum(input);
      const inserted = await c.query(
        `INSERT INTO platform_console.schema_migrations (version, name, checksum, up_sql, down_sql)
         VALUES ($1, $2, $3, $4, $5)
         RETURNING version, name, applied_at, checksum, up_sql, down_sql`,
        [input.version, input.name, checksum, input.upSql, input.downSql],
      );
      return toRow(inserted.rows[0]);
    });
    return { ok: true, data: row };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  } finally {
    client.release();
  }
}

/** Reads the real applied-migration history for `projectName`, newest version first. */
export async function listMigrations(projectName: string): Promise<MigrationOutcome<MigrationRow[]>> {
  const poolResult = await resolvePool(projectName);
  if (!poolResult.ok) return poolResult;

  try {
    const result = await poolResult.data.query(
      `SELECT version, name, applied_at, checksum, up_sql, down_sql
       FROM platform_console.schema_migrations
       ORDER BY version DESC`,
    );
    return { ok: true, data: result.rows.map(toRow) };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/**
 * Rolls back one already-applied migration: reads its stored `down_sql`
 * (the durable copy of what the operator submitted at apply time -- see
 * this module's header comment for why it's stored on the row rather than
 * re-read from a file), runs it, and deletes the history row, all inside
 * one real transaction -- a down script that fails partway leaves neither
 * the schema change nor the history row touched, the same atomicity
 * guarantee applyMigration gives the forward direction.
 */
export async function rollbackMigration(
  projectName: string,
  version: number,
): Promise<MigrationOutcome<{ version: number }>> {
  const poolResult = await resolvePool(projectName);
  if (!poolResult.ok) return poolResult;

  const client = await poolResult.data.connect();
  try {
    await withTransaction(client, async (c) => {
      const existing = await c.query(
        `SELECT down_sql FROM platform_console.schema_migrations WHERE version = $1 FOR UPDATE`,
        [version],
      );
      if (existing.rowCount === 0) {
        throw new Error(`migration version ${version} is not recorded as applied for this project`);
      }
      const downSql = existing.rows[0].down_sql as string;
      await c.query(downSql);
      await c.query(`DELETE FROM platform_console.schema_migrations WHERE version = $1`, [version]);
    });
    return { ok: true, data: { version } };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  } finally {
    client.release();
  }
}
