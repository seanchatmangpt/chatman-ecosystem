import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { currentQuarter, generateQbrBundle, parseQuarter } from "@/lib/qbr";

// Real on-demand (re)generation -- lets an admin force-regenerate a
// bundle mid-quarter for a live customer call, the one case
// lib/qbr.ts's `generateQbrBundle` accepts `force: true` for. Distinct
// route from GET /api/qbr/[orgId] (read-only history) and POST-gated the
// same way every other actuating platform-admin write in this repo is
// (see POST /api/contract-renewals/[orgId]).
//
// Body: { quarter?: "YYYY-Qn" } -- defaults to the real current calendar
// quarter (lib/qbr.ts's `currentQuarter`) when omitted, so "regenerate
// the QBR" on a call defaults to the quarter actually in progress
// without the caller having to compute the label themselves.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/qbr/${orgId}/generate`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/qbr/${orgId}/generate`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/qbr/${orgId}/generate`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const body = await request.json().catch(() => null);
  const quarter =
    typeof body?.quarter === "string" && body.quarter.length > 0 ? body.quarter : currentQuarter();

  if (!parseQuarter(quarter)) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/qbr/${orgId}/generate`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "quarter must be 'YYYY-Qn' (n in 1..4)" }, { status: 400 });
  }

  const result = await generateQbrBundle(orgId, quarter, actor, { force: true });
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/qbr/${orgId}/generate`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ bundle: result.data });
}
