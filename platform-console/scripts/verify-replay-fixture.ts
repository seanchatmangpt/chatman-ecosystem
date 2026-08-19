/**
 * ce-replay/1's cross-party verifier. Deliberately dependency-free: no
 * database connection, no import from app/lib/audit-db.ts or any other
 * platform-console module, no `pg`, no application config. Its only
 * inputs are the fixture JSON file (produced by
 * scripts/export-replay-fixture.ts, or hand-constructed) and Node's
 * built-in `crypto`/`fs` modules -- the same runtime primitives any
 * outside party's own script would have, with or without ever having
 * seen this repository.
 *
 * This is the actual test ce-replay/1 names: can a party who has never
 * read lib/audit-db.ts take just the JSON file and get a real answer
 * about whether the receipt chain it describes is internally consistent?
 * The hash algorithm itself is necessarily re-implemented here (from the
 * fixture's own self-describing `hashAlgorithm.material` field, not from
 * reading lib/audit-db.ts's source) -- re-deriving the same well-known
 * primitive (sha256 over a documented, ordered concatenation) from a
 * written spec is what an independent verifier does; it is not the same
 * thing as sharing code with the exporter.
 *
 * Usage: `npx tsx scripts/verify-replay-fixture.ts <fixture.json>` --
 * exits 0 and prints "VALID" if every row's stored row_hash matches its
 * independently recomputed digest and the prev_hash chain is unbroken;
 * exits 1 and prints exactly which row broke, otherwise.
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

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
  fixtureFormat: string;
  rowCount: number;
  hashAlgorithm: {
    name: string;
    genesisHash: string;
    purgedTombstonePrefix: string;
  };
  rows: FixtureRow[];
}

/**
 * Independent reimplementation of the row-hash algorithm, built only from
 * the fixture's own documented field order (see
 * export-replay-fixture.ts's `hashAlgorithm.material` string) -- not by
 * importing lib/audit-db.ts's `computeRowHash`. sha256-hex over the
 * space-joined fields, optional fields appended last and only when
 * present.
 */
function recomputeRowHash(prevHash: string, row: FixtureRow): string {
  const parts = [
    prevHash,
    row.request_id,
    row.ts,
    row.actor,
    row.method,
    row.path,
    String(row.status),
  ];
  if (row.castle_receipt_digest) parts.push(row.castle_receipt_digest);
  if (row.impersonated_by) parts.push(row.impersonated_by);
  if (row.impersonation_session_id) parts.push(row.impersonation_session_id);
  const material = parts.join(" ");
  return createHash("sha256").update(material, "utf8").digest("hex");
}

function fail(message: string): never {
  console.error(`INVALID: ${message}`);
  process.exit(1);
}

function main(): void {
  const fixturePath = process.argv[2];
  if (!fixturePath) {
    console.error("usage: npx tsx scripts/verify-replay-fixture.ts <fixture.json>");
    process.exit(2);
  }

  let raw: string;
  try {
    raw = readFileSync(fixturePath, "utf8");
  } catch (err) {
    fail(`could not read fixture file '${fixturePath}': ${err instanceof Error ? err.message : String(err)}`);
  }

  let fixture: Fixture;
  try {
    fixture = JSON.parse(raw);
  } catch (err) {
    fail(`fixture file is not valid JSON: ${err instanceof Error ? err.message : String(err)}`);
  }

  if (!Array.isArray(fixture.rows) || fixture.rows.length === 0) {
    fail("fixture has no rows to verify");
  }

  const genesis = fixture.hashAlgorithm?.genesisHash ?? "GENESIS-" + "0".repeat(56);
  const purgedPrefix = fixture.hashAlgorithm?.purgedTombstonePrefix ?? "PURGED-TOMBSTONE-";

  const rows = fixture.rows;
  let expectedPrevHash = rows[0].prev_hash?.startsWith(purgedPrefix) ? rows[0].prev_hash : genesis;

  for (const row of rows) {
    if (row.prev_hash !== expectedPrevHash) {
      fail(
        `row ${row.id}: stored prev_hash ('${row.prev_hash}') does not match the preceding ` +
          `row's stored row_hash ('${expectedPrevHash}') -- a row was inserted, deleted, or ` +
          `reordered out of band`,
      );
    }
    const recomputed = recomputeRowHash(expectedPrevHash, row);
    if (recomputed !== row.row_hash) {
      fail(
        `row ${row.id}: recomputed row_hash ('${recomputed}') does not match the stored ` +
          `row_hash ('${row.row_hash}') -- one or more of request_id/ts/actor/method/path/` +
          `status/castle_receipt_digest/impersonated_by/impersonation_session_id was modified ` +
          `after this fixture's row_hash was originally computed`,
      );
    }
    expectedPrevHash = row.row_hash as string;
  }

  console.log(
    `VALID: ${rows.length} row(s) verified, hash chain intact from ` +
      `${rows[0].prev_hash?.startsWith(purgedPrefix) ? "purge tombstone" : "genesis"} through row ${
        rows[rows.length - 1].id
      } (row_hash ${rows[rows.length - 1].row_hash}).`,
  );
  process.exit(0);
}

main();
