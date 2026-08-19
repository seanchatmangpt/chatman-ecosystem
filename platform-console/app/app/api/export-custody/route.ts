import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { listExportCustodyRecords } from "@/lib/export-custody";

// Real Per-Org Data-Export Chain-of-Custody Certificate listing -- distinct
// compliance artifact from lib/dsar.ts's per-subject GDPR/CCPA export (see
// lib/export-custody.ts's header comment). Lists every bulk-export
// certificate this org has (scheduled S3 subscription runs and manual
// admin CSV pulls alike), newest first.
//
// GET only here, org-scoped by required `?orgId=` query param, matching
// this repo's own list-route-is-read-only convention (see GET
// /api/contract-renewals's header comment) -- per-certificate reads live
// at GET /api/export-custody/[exportId] instead.
//
// Auth: any authenticated member of the org (viewer and up) -- same floor
// as GET /api/orgs/[id]/billing/spend-history: reading this org's own
// already-generated compliance certificates is not a privileged action
// beyond ordinary org membership, and Fortune-5 compliance teams are
// typically viewer-role members pulling evidence, not owners.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim();
  if (!orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
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
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/export-custody",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listExportCustodyRecords(orgId);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/export-custody",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ certificates: result.data });
}
