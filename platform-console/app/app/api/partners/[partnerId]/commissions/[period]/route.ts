import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getPartner, getPartnerCommission } from "@/lib/partners";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real, auditable per-period breakdown: the per-org spend lines that
// produced a period's already-computed commission total (lib/partners.ts's
// getPartnerCommission), so a partner's finance team can reconcile the
// total against the actual managed-org spend it was derived from -- not
// just trust the number. Same platform-admin boundary every other
// Partner route uses.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ partnerId: string; period: string }> },
) {
  const { partnerId, period } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/partners/${partnerId}/commissions/${period}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const partnerResult = await getPartner(partnerId);
  if (!partnerResult.ok) {
    return NextResponse.json({ error: partnerResult.error }, { status: 502 });
  }
  if (!partnerResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/partners/${partnerId}/commissions/${period}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "partner not found" }, { status: 404 });
  }

  const result = await getPartnerCommission(partnerId, period);
  if (!result.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/partners/${partnerId}/commissions/${period}`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  if (!result.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/partners/${partnerId}/commissions/${period}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "commission not yet computed for this period" }, { status: 404 });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/partners/${partnerId}/commissions/${period}`,
    status: 200,
    requestId,
  });
  return NextResponse.json({ commission: result.data });
}
