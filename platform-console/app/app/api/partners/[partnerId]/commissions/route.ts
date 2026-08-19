import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import {
  computePartnerCommission,
  getPartner,
  isValidCommissionPeriod,
  listPartnerCommissions,
} from "@/lib/partners";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Partner revenue-share / commission ledger -- GET lists every period
// already computed for this partner (the historical, immutable ledger a
// partner's finance team audits payouts against); POST computes (or, for
// an already-computed period, returns the existing immutable row for)
// one period. Same platform-admin boundary every other Partner route
// uses -- see app/api/partners/[partnerId]/orgs/route.ts's own comment
// on why this is gated at least as strictly as a single-org owner view.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ partnerId: string }> },
) {
  const { partnerId } = await params;
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
      path: `/api/partners/${partnerId}/commissions`,
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
      path: `/api/partners/${partnerId}/commissions`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "partner not found" }, { status: 404 });
  }

  const result = await listPartnerCommissions(partnerId);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/partners/${partnerId}/commissions`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ partnerId, commissions: result.data });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ partnerId: string }> },
) {
  const { partnerId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/partners/${partnerId}/commissions`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const period = typeof body?.period === "string" ? body.period.trim() : "";
  if (!period || !isValidCommissionPeriod(period)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/partners/${partnerId}/commissions`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: 'period is required, format "YYYY-MM"' }, { status: 400 });
  }

  const partnerResult = await getPartner(partnerId);
  if (!partnerResult.ok) {
    return NextResponse.json({ error: partnerResult.error }, { status: 502 });
  }
  if (!partnerResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/partners/${partnerId}/commissions`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "partner not found" }, { status: 404 });
  }

  const result = await computePartnerCommission(partnerResult.data, period);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/partners/${partnerId}/commissions`,
    status: result.ok ? 200 : 400,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ commission: result.data });
}
