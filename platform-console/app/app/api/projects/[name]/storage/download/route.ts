import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getProject, getProjectStorageService } from "@/lib/k8s";
import { fetchStorageObject } from "@/lib/storage-api";
import { verifyStorageDownloadToken } from "@/lib/storage-signed-url";

// Runs on the Node.js runtime (default for route handlers) -- same reason
// every other lib/k8s.ts-backed route in this file tree does.
//
// Deliberately NOT behind requireSession/requireRole: a signed download
// URL is bearer-style by design (AWS S3 presigned URL / GCP Signed URL
// convention) -- the whole point of control storage-signed-url-expiry-
// enforced is that possession of a valid, unexpired token IS the
// authorization for that one object, so this route can be handed to a
// reviewer or a downstream tool that never has a platform-console session
// cookie. What replaces the session check is real: the HMAC signature
// (lib/storage-signed-url.ts, signed with this app's own AUTH_SECRET) and
// the server-checked expiry -- an invalid or expired token gets a real 403
// here, never a fallback "allow".
//
// Every access attempt -- allowed or denied -- is written to the real,
// durable platform_console.audit_log via writeAuditLogEntry (lib/audit-
// db.ts), the same table GET /api/audit reads: this is the download-audit-
// trail half of the control, not just the expiry half.

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const { name } = await params;
  const token = request.nextUrl.searchParams.get("token") ?? "";

  const verified = verifyStorageDownloadToken(token, name);
  if (!verified.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "signed-url (unverified)",
      method: "GET",
      path: `/api/projects/${name}/storage/download`,
      status: 403,
      requestId,
    });
    return NextResponse.json(
      { error: `signed URL rejected: ${verified.reason}` },
      { status: 403 },
    );
  }

  const actor = `${verified.identifier} (signed-url)`;

  const projectResult = await getProject(name);
  if (!projectResult.ok || !projectResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/projects/${name}/storage/download`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const svcResult = await getProjectStorageService(projectResult.data);
  if (!svcResult.ok || !svcResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/projects/${name}/storage/download`,
      status: 502,
      requestId,
    });
    return NextResponse.json(
      { error: !svcResult.ok ? svcResult.error : `no storage Service found for project '${name}'` },
      { status: 502 },
    );
  }

  const objectResult = await fetchStorageObject(
    svcResult.data.dns,
    svcResult.data.port,
    verified.bucket,
    verified.objectPath,
  );

  if (!objectResult.ok) {
    const status = objectResult.notConfigured ? 501 : objectResult.status;
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/projects/${name}/storage/download (${verified.bucket}/${verified.objectPath})`,
      status,
      requestId,
    });
    return NextResponse.json(
      { error: objectResult.notConfigured ? "storage service-role key not configured" : objectResult.error },
      { status },
    );
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/projects/${name}/storage/download (${verified.bucket}/${verified.objectPath})`,
    status: 200,
    requestId,
  });

  return new NextResponse(objectResult.body, {
    status: 200,
    headers: {
      "content-type": objectResult.contentType,
      "cache-control": "private, no-store",
      "content-disposition": `attachment; filename="${verified.objectPath.split("/").pop()}"`,
    },
  });
}
