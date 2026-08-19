import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getComplianceReport } from "@/lib/compliance-report";
import { streamAuditLogAsEcsNdjson } from "@/lib/audit-export";

// Real single-report download endpoint: GET .../[reportId]?format=json|
// csv|ndjson.
//
//   - format=json (default): the full stored ComplianceReport (metadata +
//     every real section) as one JSON document -- what an operator's GRC
//     tool ingests programmatically.
//   - format=csv: the report's own small, already-stored `csvSummary`
//     text, returned as `text/csv` with a `Content-Disposition:
//     attachment` filename -- a spreadsheet-ready flattened summary.
//   - format=ndjson: the FULL real audit trail for the report's own
//     `[periodStart, periodEnd]`, streamed live straight from Postgres via
//     lib/audit-export.ts's `streamAuditLogAsEcsNdjson` -- never stored in
//     the ConfigMap (see lib/compliance-report.ts's header comment on
//     why), but deterministically reconstructible for as long as
//     Postgres retains those rows, using the exact same period this
//     report's own `sections.auditEventCount` was computed against.
//
// Auth: any authenticated member of this org (viewer and up) -- same
// "reading a generated artifact isn't itself a privileged action" posture
// GET .../compliance-reports (the list) already uses.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; reportId: string }> },
) {
  const { id, reportId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const access = await requireRoleIn(session, namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/compliance-reports/${reportId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getComplianceReport(id, reportId);
  if (!result.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/compliance-reports/${reportId}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/compliance-reports/${reportId}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "report not found" }, { status: 404 });
  }
  const report = result.data;

  const format = request.nextUrl.searchParams.get("format") ?? "json";

  if (format === "csv") {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/compliance-reports/${reportId}`,
      status: 200,
      requestId,
    });
    return new NextResponse(report.csvSummary, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="compliance-report-${reportId}.csv"`,
      },
    });
  }

  if (format === "ndjson") {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/compliance-reports/${reportId}`,
      status: 200,
      requestId,
    });
    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        try {
          for await (const line of streamAuditLogAsEcsNdjson({
            from: report.periodStart,
            to: report.periodEnd,
          })) {
            controller.enqueue(encoder.encode(line));
          }
          controller.close();
        } catch (err) {
          controller.error(err);
        }
      },
    });
    return new NextResponse(stream, {
      status: 200,
      headers: {
        "Content-Type": "application/x-ndjson; charset=utf-8",
        "Content-Disposition": `attachment; filename="compliance-report-${reportId}-audit.ndjson"`,
      },
    });
  }

  if (format !== "json") {
    return NextResponse.json({ error: "format must be one of json, csv, ndjson" }, { status: 400 });
  }

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/compliance-reports/${reportId}`,
    status: 200,
    requestId,
  });
  return NextResponse.json({ report });
}
