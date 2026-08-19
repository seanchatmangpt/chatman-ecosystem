import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getExportCustodyRecord, verifyExportCustody } from "@/lib/export-custody";

// Tamper-evidence check for one export-custody certificate: recomputes the
// audit-log hash-chain segment for the exact row this certificate points
// at (lib/export-custody.ts's `verifyExportCustody`, reusing the same
// `computeRowHash` primitive `verifyAuditChain` uses for the full-chain
// control) and confirms `datasetHash`/`auditLogEntryId` are still
// consistent. Returns `verified: true/false` -- never a boolean the
// caller has to re-derive itself from a raw hash comparison.
//
// Same org-scoped access floor as GET /api/export-custody/[exportId]:
// resolves the certificate's own orgId first (exportId doesn't carry it
// in the URL), then requires viewer-and-up membership in that org.

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
      path: `/api/export-custody/${exportId}/verify`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await verifyExportCustody(exportId);
  writeAuditLogEntry({
    orgId: record.orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/export-custody/${exportId}/verify`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
