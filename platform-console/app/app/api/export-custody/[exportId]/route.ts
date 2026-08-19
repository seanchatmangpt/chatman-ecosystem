import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getExportCustodyRecord, toCertificate } from "@/lib/export-custody";

// Fetches one export-custody certificate, formatted for an auditor
// (lib/export-custody.ts's `ExportCustodyCertificate` shape) -- exportable
// to this repo's existing PDF pattern
// (app/api/orgs/[id]/compliance-reports/[reportId]/route.ts's own
// `?format=` convention) with no separate PDF-only data model, since this
// JSON already carries every field a certificate needs.
//
// The certificate itself carries `orgId` (it was minted by
// recordExportCustody against one specific org), so this route resolves
// the record FIRST, then org-scopes access against ITS orgId -- the same
// order GET /api/orgs/[id]/compliance-reports/[reportId] already uses,
// since `exportId` alone (unlike most of this tree's `/api/orgs/[id]/...`
// routes) does not carry the org id in the URL path.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ exportId: string }> },
) {
  const { exportId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const recordResult = await getExportCustodyRecord(exportId);
  if (!recordResult.ok) {
    return NextResponse.json({ error: recordResult.error }, { status: 502 });
  }
  if (!recordResult.data) {
    return NextResponse.json({ error: "export-custody certificate not found" }, { status: 404 });
  }
  const record = recordResult.data;

  const orgResult = await getOrg(record.orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: record.orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/export-custody/${exportId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  writeAuditLogEntry({
    orgId: record.orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/export-custody/${exportId}`,
    status: 200,
    requestId,
  });

  return NextResponse.json(toCertificate(record));
}
