/**
 * Real SIEM-format export for the durable audit trail (lib/audit-db.ts's
 * `platform_console.audit_log`) -- the AWS CloudTrail "S3/log export" /
 * GCP Cloud Logging "log sink export" equivalent: a bulk, machine-readable
 * dump an operator can pull into an external SIEM (Splunk, Datadog, the
 * Elastic Stack, ...), not just browse in this console's own /audit page.
 *
 * Format chosen: newline-delimited JSON (NDJSON), one self-contained JSON
 * object per line, each shaped per the Elastic Common Schema (ECS) --
 * https://www.elastic.co/guide/en/ecs/current/ecs-field-reference.html --
 * the same field-naming convention Filebeat/Logstash/Elastic Agent already
 * emit and that Splunk's HEC and Datadog's Logs API both ingest as plain
 * JSON without needing ECS-awareness (ECS is a *convention* for which keys
 * mean what, not a wire protocol only Elastic understands). Real fields
 * used here, each with a real, standard meaning:
 *
 *   @timestamp              -- ECS's own reserved top-level timestamp key
 *   event.dataset            -- source of the event ("platform_console.audit_log")
 *   event.action              -- what happened ("GET /api/audit")
 *   event.outcome             -- "success" | "failure", derived from HTTP status
 *   event.id                  -- this audit trail's own requestId (a real UUID)
 *   user.name                 -- the authenticated actor (session subject)
 *   http.request.method        -- HTTP method
 *   http.response.status_code   -- HTTP status code
 *   url.path                    -- request path
 *   ecs.version                 -- the ECS schema revision this document conforms to
 *
 * Streaming, not buffering: rows are pulled from Postgres in bounded
 * batches via real keyset pagination (`WHERE (ts, id) > (cursor)`, never
 * OFFSET, which degrades on large exports) and each row is turned into one
 * NDJSON line as soon as it arrives -- the caller (the /api/audit/export
 * route) can pipe these lines straight into a Node ReadableStream without
 * ever holding the full export in memory.
 */
import type { PoolClient } from "pg";
import { getAuditDbPool, type AuditLogRow } from "@/lib/audit-db";

/** The ECS schema revision every exported document declares itself as conforming to. */
const ECS_VERSION = "8.11.0";

/** One audit_log row, reshaped into a real ECS-conformant document. */
export interface EcsAuditEvent {
  "@timestamp": string;
  event: {
    dataset: string;
    action: string;
    outcome: "success" | "failure";
    id: string;
  };
  user: { name: string };
  http: {
    request: { method: string };
    response: { status_code: number };
  };
  url: { path: string };
  ecs: { version: string };
}

/**
 * Maps one real `platform_console.audit_log` row to one real ECS document.
 * `event.action` mirrors what an operator would actually want to grep for
 * in a SIEM ("METHOD path"), and `event.outcome` follows ECS's own stated
 * convention (https://www.elastic.co/guide/en/ecs/current/ecs-event.html):
 * any HTTP status below 400 is "success", 400+ is "failure" -- the same
 * threshold AuditLogPanel.tsx already uses to color-code the status column.
 */
export function rowToEcsEvent(row: AuditLogRow): EcsAuditEvent {
  return {
    "@timestamp": row.ts,
    event: {
      dataset: "platform_console.audit_log",
      action: `${row.method} ${row.path}`,
      outcome: row.status < 400 ? "success" : "failure",
      id: row.requestId,
    },
    user: { name: row.actor },
    http: {
      request: { method: row.method },
      response: { status_code: row.status },
    },
    url: { path: row.path },
    ecs: { version: ECS_VERSION },
  };
}

export interface AuditExportParams {
  from?: string; // RFC3339 lower bound (inclusive), matched against `ts`
  to?: string; // RFC3339 upper bound (inclusive), matched against `ts`
}

const BATCH_SIZE = 500;

interface CursorRow {
  id: number;
  request_id: string;
  ts: string;
  actor: string;
  method: string;
  path: string;
  status: number;
}

function toAuditLogRow(r: CursorRow): AuditLogRow {
  return {
    id: Number(r.id),
    requestId: r.request_id,
    ts: new Date(r.ts).toISOString(),
    actor: r.actor,
    method: r.method,
    path: r.path,
    status: Number(r.status),
    insertedAt: new Date(r.ts).toISOString(), // insertedAt not needed by the exporter; ts is the real ordering/display field
  };
}

/**
 * Real keyset-paginated batch fetch, ordered `(ts, id) ASC` so cursoring
 * never skips or repeats a row even if two entries share the same `ts`
 * (real concurrent requests routinely do, down to the millisecond).
 * `cursor` is `null` for the first batch, then the last row's own
 * `(ts, id)` for every subsequent batch -- the same "keep resolving state
 * from what was actually returned last time, not an assumed offset"
 * discipline audit-db.ts's own connection-pool caching already follows.
 */
async function fetchBatch(
  client: PoolClient,
  params: AuditExportParams,
  cursor: { ts: string; id: number } | null,
): Promise<AuditLogRow[]> {
  const conditions: string[] = [];
  const values: unknown[] = [];

  if (params.from) {
    values.push(params.from);
    conditions.push(`ts >= $${values.length}`);
  }
  if (params.to) {
    values.push(params.to);
    conditions.push(`ts <= $${values.length}`);
  }
  if (cursor) {
    values.push(cursor.ts, cursor.id);
    conditions.push(`(ts, id) > ($${values.length - 1}, $${values.length})`);
  }
  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

  values.push(BATCH_SIZE);
  const result = await client.query<CursorRow>(
    `SELECT id, request_id, ts, actor, method, path, status
     FROM platform_console.audit_log
     ${where}
     ORDER BY ts ASC, id ASC
     LIMIT $${values.length}`,
    values,
  );
  return result.rows.map(toAuditLogRow);
}

/**
 * The real streaming export: an async generator yielding one complete
 * NDJSON line (including its trailing `\n`) per audit_log row in the given
 * date range, oldest first. Pulls from Postgres in bounded batches of
 * `BATCH_SIZE` rows at a time via `fetchBatch`'s keyset cursor -- never
 * loads the full result set into memory at once, so the /api/audit/export
 * route can pipe this straight into a ReadableStream for an export
 * covering an arbitrarily large date range.
 */
export async function* streamAuditLogAsEcsNdjson(
  params: AuditExportParams,
): AsyncGenerator<string, void, unknown> {
  const pool = await getAuditDbPool();
  if (!pool) {
    throw new Error(
      "audit log database not configured or unreachable -- see the stdout log (kubectl logs) for this environment's real-time record",
    );
  }
  const client = await pool.connect();
  try {
    let cursor: { ts: string; id: number } | null = null;
    for (;;) {
      const batch = await fetchBatch(client, params, cursor);
      if (batch.length === 0) break;
      for (const row of batch) {
        yield JSON.stringify(rowToEcsEvent(row)) + "\n";
      }
      const last = batch[batch.length - 1];
      cursor = { ts: last.ts, id: last.id };
      if (batch.length < BATCH_SIZE) break;
    }
  } finally {
    client.release();
  }
}
