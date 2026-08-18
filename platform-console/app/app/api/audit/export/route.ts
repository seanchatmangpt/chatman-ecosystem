import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { streamAuditLogAsEcsNdjson } from "@/lib/audit-export";

// Real bulk SIEM export -- the AWS CloudTrail "export to S3" / GCP Cloud
// Logging "log sink export" equivalent for this console's own durable
// audit trail (platform_console.audit_log, lib/audit-db.ts). Owner-gated
// (requireRole "owner"), same boundary as GET /api/audit itself -- bulk
// export is at least as sensitive as browsing the same data one page at a
// time, arguably more so since the whole history leaves this cluster in
// one file. Runs on the Node.js runtime (default for route handlers) --
// lib/k8s.ts and the `pg` driver lib/audit-db.ts/lib/audit-export.ts use
// both need it.
//
// Unlike GET /api/audit's own read (which deliberately does not log
// itself, to avoid every page view of /audit inflating its own result
// set), a bulk export IS logged here: it is a distinct, higher-sensitivity
// action ("the whole trail, or a whole date range of it, just left this
// cluster"), not a page-through read, and CloudTrail/Cloud Logging both
// log their own export/sink-creation management events for the identical
// reason.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/audit/export",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const params = request.nextUrl.searchParams;
  const from = params.get("from")?.trim() || undefined;
  const to = params.get("to")?.trim() || undefined;

  // Real validation, matching the exact failure mode a malformed `from`/`to`
  // would otherwise hit deep inside the SQL layer: reject up front with a
  // real 400, never pass an un-parseable string through to Postgres.
  for (const [label, value] of [["from", from] as const, ["to", to] as const]) {
    if (value !== undefined && Number.isNaN(Date.parse(value))) {
      return NextResponse.json({ error: `invalid ${label}: not a parseable date` }, { status: 400 });
    }
  }

  let generator: AsyncGenerator<string, void, unknown>;
  try {
    generator = streamAuditLogAsEcsNdjson({ from, to });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 502 },
    );
  }

  const encoder = new TextEncoder();
  let rowCount = 0;

  // Real streaming response: each NDJSON line is pulled from Postgres (in
  // lib/audit-export.ts's own bounded keyset-paginated batches) and
  // enqueued as soon as it is produced -- the full export is never
  // materialized in this route handler's memory at once, so an export
  // covering the whole audit_log table streams in roughly constant memory
  // regardless of row count.
  const stream = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        const { value, done } = await generator.next();
        if (done) {
          controller.close();
          writeAuditLogEntry({
            timestamp: new Date().toISOString(),
            actor,
            method: "GET",
            path: `/api/audit/export (${rowCount} rows${from ? `, from=${from}` : ""}${to ? `, to=${to}` : ""})`,
            status: 200,
            requestId,
          });
          return;
        }
        rowCount += 1;
        controller.enqueue(encoder.encode(value));
      } catch (err) {
        controller.error(err);
        writeAuditLogEntry({
          timestamp: new Date().toISOString(),
          actor,
          method: "GET",
          path: "/api/audit/export",
          status: 502,
          requestId,
        });
      }
    },
    async cancel() {
      await generator.return();
    },
  });

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "application/x-ndjson",
      "Content-Disposition": `attachment; filename="audit-log-export-${stamp}.ndjson"`,
      "Cache-Control": "no-store",
    },
  });
}
