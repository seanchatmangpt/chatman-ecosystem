import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { readExportArchive, verifyExportToken } from "@/lib/export-download-cache";

// Bearer-style download, same convention as
// app/api/projects/[name]/storage/download/route.ts: possession of a
// valid, unexpired signed token IS the authorization for this one
// archive, so this route is deliberately NOT behind requireSession --
// the token itself (HMAC-signed with this app's own AUTH_SECRET,
// lib/export-download-cache.ts) is the real access control, and every
// access attempt (allowed or denied) is written to the durable
// platform_console.audit_log the same way the storage download route
// does.

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const { name } = await params;
  const token = request.nextUrl.searchParams.get("token") ?? "";

  const verified = verifyExportToken(token);
  if (!verified.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "signed-url (unverified)",
      method: "GET",
      path: `/api/projects/${name}/export-all/download`,
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
      path: `/api/projects/${name}/export-all/download`,
      status: 404,
      requestId,
    });
    return NextResponse.json(
      { error: "export archive not found -- it may have expired or this process restarted since it was created" },
      { status: 404 },
    );
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: `${verified.identifier} (signed-url)`,
    method: "GET",
    path: `/api/projects/${name}/export-all/download (${archive.filename})`,
    status: 200,
    requestId,
  });

  return new NextResponse(archive.buffer, {
    status: 200,
    headers: {
      "content-type": "application/zip",
      "cache-control": "private, no-store",
      "content-disposition": `attachment; filename="${archive.filename}"`,
    },
  });
}
