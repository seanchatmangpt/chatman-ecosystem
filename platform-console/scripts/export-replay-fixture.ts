/**
 * ce-replay/1: exports the tail of the REAL platform_console.audit_log
 * hash chain as a standalone JSON fixture, for the cross-party test named
 * in docs/jira/v26.8.19/09-CE-REPLAY-1.md's "Real, scoped gap" section --
 * could an unrelated process, with no access to this codebase's database
 * credentials or its lib/audit-db.ts hash-chain implementation, take just
 * this one JSON file and independently confirm the chain is intact?
 *
 * This script is the ONLY half of that test allowed to depend on this
 * codebase: it reuses the real, already-running connection pool
 * (`getAuditDbPool` from app/lib/audit-db.ts) and issues a real SELECT
 * against the live `platform_console.audit_log` table -- it never
 * fabricates rows. scripts/verify-replay-fixture.ts is the other half: a
 * genuinely dependency-free verifier that imports nothing from this
 * module or from lib/audit-db.ts (beyond the hash algorithm itself,
 * necessarily re-implemented rather than imported, since "no shared code"
 * is the point of the test).
 *
 * Usage: `npx tsx scripts/export-replay-fixture.ts [N]` from
 * platform-console/ (N defaults to 20). Requires the same in-cluster
 * credentials/env every other app/lib/audit-db.ts reader requires
 * (hasClusterCredentials() in app/lib/k8s.ts) -- when those aren't
 * present (e.g. this script run outside the cluster), it prints exactly
 * that and exits nonzero rather than writing a fixture built from
 * anything but real rows.
 */
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { Pool } from "pg";
import { getAuditDbPool } from "../app/lib/audit-db";

const FIXTURE_PATH = join(__dirname, "fixtures", "replay-fixture-sample.json");

/**
 * Row shape as exported to the fixture -- exactly the columns
 * lib/audit-db.ts's own chain-verification query (`verifyAuditChain`)
 * reads plus `id`/`inserted_at` for human-readable context, using the
 * same snake_case column names the live table uses (deliberately NOT
 * lib/audit-db.ts's camelCase `AuditLogRow` shape, so the fixture's field
 * names read as "raw table columns," not "this codebase's internal
 * type") -- an external verifier reading this JSON should be able to map
 * it straight onto a `SELECT * FROM platform_console.audit_log` mental
 * model without needing to know this codebase's naming conventions.
 */
interface FixtureRow {
  id: number;
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
}

interface Fixture {
  fixtureFormat: "ce-replay-1/audit-log-chain-tail/v1";
  exportedAt: string;
  source: {
    table: "platform_console.audit_log";
    query: string;
  };
  rowCount: number;
  hashAlgorithm: {
    name: "sha256-hex";
    /**
     * The exact field-ordering rule computeRowHash (app/lib/audit-db.ts)
     * applies, spelled out here in prose so an external verifier can
     * reimplement it without reading that source file -- the fixture is
     * meant to be self-describing, not merely self-consistent.
     */
    material: string;
    genesisHash: string;
    purgedTombstonePrefix: string;
  };
  rows: FixtureRow[];
}

async function main(): Promise<void> {
  const n = Number(process.argv[2] ?? "20");
  const limit = Number.isFinite(n) && n > 0 ? Math.floor(n) : 20;

  let pool: Pool | null;
  try {
    pool = await getAuditDbPool();
  } catch (err) {
    console.error(
      `export-replay-fixture: failed resolving the audit DB pool: ${
        err instanceof Error ? err.message : String(err)
      }`,
    );
    process.exit(1);
  }

  if (!pool) {
    console.error(
      "export-replay-fixture: audit log database not configured or unreachable in this " +
        "environment (no in-cluster credentials -- see app/lib/k8s.ts's hasClusterCredentials). " +
        "No fixture was written. This script does not fabricate rows.",
    );
    process.exit(1);
  }

  const query = `
    SELECT id, request_id, ts, actor, method, path, status, prev_hash, row_hash,
           castle_receipt_digest, impersonated_by, impersonation_session_id
    FROM platform_console.audit_log
    ORDER BY id DESC
    LIMIT $1
  `;

  let rows: FixtureRow[];
  try {
    const result = await pool.query(query, [limit]);
    // DESC (most recent first) is the natural "most recent N" query, but
    // a hash-chain fixture must be walkable in chain order (oldest ->
    // newest, so each row's stored prev_hash matches the row immediately
    // before it in the array) -- reverse to ASC before writing.
    rows = result.rows
      .map((r: Record<string, unknown>) => ({
        id: Number(r.id),
        request_id: r.request_id as string,
        ts: new Date(r.ts as string).toISOString(),
        actor: r.actor as string,
        method: r.method as string,
        path: r.path as string,
        status: Number(r.status),
        prev_hash: (r.prev_hash as string | null) ?? null,
        row_hash: (r.row_hash as string | null) ?? null,
        castle_receipt_digest: (r.castle_receipt_digest as string | null) ?? null,
        impersonated_by: (r.impersonated_by as string | null) ?? null,
        impersonation_session_id: (r.impersonation_session_id as string | null) ?? null,
      }))
      .reverse();
  } catch (err) {
    console.error(
      `export-replay-fixture: query failed: ${err instanceof Error ? err.message : String(err)}`,
    );
    process.exit(1);
    return;
  }

  if (rows.length === 0) {
    console.error(
      "export-replay-fixture: query succeeded but platform_console.audit_log returned zero rows " +
        "-- nothing to export. No fixture was written.",
    );
    process.exit(1);
  }

  const fixture: Fixture = {
    fixtureFormat: "ce-replay-1/audit-log-chain-tail/v1",
    exportedAt: new Date().toISOString(),
    source: {
      table: "platform_console.audit_log",
      query: query.trim().replace(/\s+/g, " "),
    },
    rowCount: rows.length,
    hashAlgorithm: {
      name: "sha256-hex",
      material:
        "sha256(prev_hash + ' ' + request_id + ' ' + ts + ' ' + actor + ' ' + method + ' ' + " +
        "path + ' ' + String(status) [+ ' ' + castle_receipt_digest, if present] " +
        "[+ ' ' + impersonated_by, if present] [+ ' ' + impersonation_session_id, if present])." +
        " Fields are space-joined in exactly this order; optional fields are omitted " +
        "entirely (not empty-string) from the joined material when absent on that row. " +
        "This fixture's rows only ever carry request_id/ts/actor/method/path/status/" +
        "castle_receipt_digest/impersonated_by/impersonation_session_id as chain-committed " +
        "fields (org_id/key_id/duration_ms/sla_credit_* are also chain-committed in the live " +
        "table per app/lib/audit-db.ts's computeRowHash, but are not selected into this " +
        "narrower fixture format -- a row using any of those fields will not independently " +
        "reverify from this fixture alone; this exporter selects the same column set " +
        "verifyAuditChain itself reads).",
      genesisHash: "GENESIS-" + "0".repeat(56),
      purgedTombstonePrefix: "PURGED-TOMBSTONE-",
    },
    rows,
  };

  writeFileSync(FIXTURE_PATH, JSON.stringify(fixture, null, 2) + "\n", "utf8");
  console.log(
    `export-replay-fixture: wrote ${rows.length} real row(s) from platform_console.audit_log to ${FIXTURE_PATH}`,
  );
  await pool.end().catch(() => {});
}

main().catch((err) => {
  console.error(`export-replay-fixture: unexpected error: ${err instanceof Error ? err.stack : String(err)}`);
  process.exit(1);
});
