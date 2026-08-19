import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { readExportArchive, verifyExportToken } from "@/lib/export-download-cache";

// Bearer-style DSAR bundle download -- same convention as
// app/api/projects/[name]/export-all/download/route.ts: possession of a
// valid, unexpired signed token IS the authorization for this one
// bundle, so this route is deliberately NOT behind requireSession. Every
// access attempt (allowed or denied) is written to the durable
// platform_console.audit_log the same way that route's own download
// endpoint does.

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.nextUrl.searchParams.get("token") ?? "";

  const verified = verifyExportToken(token);
  if (!verified.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "signed-url (unverified)",
      method: "GET",
      path: "/api/privacy/download",
      status: 403,
      requestId,
    });
    return NextResponse.json({ error: `signed URL rejected: ${verified.reason}` }, { status: 403 });
  }

  const archive = readExportArchive(verified.id);
  if (!archive) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: `${verified.identifier} (signed-url)`,
      method: "GET",
      path: "/api/privacy/download",
      status: 404,
      requestId,
    });
    return NextResponse.json(
      { error: "DSAR bundle not found -- it may have expired or this process restarted since it was created" },
      { status: 404 },
    );
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: `${verified.identifier} (signed-url)`,
    method: "GET",
    path: `/api/privacy/download (${archive.filename})`,
    status: 200,
    requestId,
  });

  return new NextResponse(archive.buffer, {
    status: 200,
    headers: {
      "content-type": "application/x-ndjson",
      "cache-control": "private, no-store",
      "content-disposition": `attachment; filename="${archive.filename}"`,
    },
  });
}
