import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { listContractRenewals } from "@/lib/contract-renewals";

// Platform-admin contract-renewal dashboard endpoint -- procurement
// visibility across every org's Stripe-derived renewal date, plus the
// documented renewal/non-renewal decision trail SOC2/vendor-management
// requires (see lib/contract-renewals.ts's header comment). Same
// platform-wide "owner" gate app/api/admin/referrals/route.ts and
// app/api/budget-alerts/route.ts already use for a cross-org admin view
// with no single-org boundary to check membership against.
//
// GET only here: lists every org's synced renewal record,
// days-until-renewal ascending (closest churn risk first). Per-org writes
// (autoRenew/noticeThresholdDays/decision) live at
// POST /api/contract-renewals/[orgId] instead, matching this repo's own
// list-route-is-read-only / [id]-route-is-the-mutation convention (see
// GET /api/budget-alerts vs its own POST for the one exception where a
// list route also writes -- that one is a flat config set, this one is
// genuinely per-org).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
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

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/contract-renewals",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listContractRenewals();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/contract-renewals",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ renewals: result.data });
}
