import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { listReferralCreditsForOrg } from "@/lib/referral-ledger";

// Customer-facing referral-credit ledger view: every partner/reseller
// credit that has ever accrued (and, once applied, the real Stripe
// balance-transaction id it resolved to) against THIS org's own
// subscription -- the in-console alternative to the out-of-band
// spreadsheet a channel deal would otherwise be tracked in. Any
// authenticated member of the org (viewer and up, checked against that
// org's own namespace-local `platform-console-org-roles` ConfigMap via
// requireRoleIn) may read it -- same "reading your own org's own record
// is not a privileged action" convention as
// app/api/orgs/[id]/impersonation-log/route.ts's GET.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/referral`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listReferralCreditsForOrg(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/referral`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ referralCredits: result.data });
}
