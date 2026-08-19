import { NextRequest, NextResponse } from "next/server";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  applyReferralCredit,
  listAllReferralCredits,
  recordReferralCredit,
} from "@/lib/referral-ledger";

// Platform-admin partner/reseller referral-credit ledger endpoint -- the
// control a Fortune 5 buyer routing a purchase through a
// systems-integrator/reseller expects the platform itself to track
// (attribution + resulting credit against the referred org's own
// subscription), rather than an out-of-band spreadsheet. Auth model,
// same "app-level RBAC on top of the console's own ServiceAccount RBAC"
// boundary as every other route in this tree:
//   - GET: platform-admin only -- lists every credit across every org
//     (an org's own members see only their own org's rows, via
//     app/api/orgs/[id]/referral/route.ts's GET instead).
//   - POST: platform-admin only (lib/authz.ts's requirePlatformAdmin --
//     same platform-level "owner" role app/api/support/impersonate/
//     route.ts already gates on). Records a new referral credit and, by
//     default, immediately applies it against the referred org's real
//     Stripe customer balance -- pass `apply: false` to record without
//     applying (e.g. a credit still pending deal-desk approval).
//
// Every write is recorded through the SAME hash-chained audit_log every
// other privileged mutation in this app lands in (via
// lib/referral-ledger.ts's own writeAuditLogEntry calls), PLUS this
// route's own generic per-request entry below -- same double-entry
// convention every other route file in this tree already follows.

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

  const access = await requirePlatformAdmin(session);
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/admin/referrals",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listAllReferralCredits();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/admin/referrals",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ referralCredits: result.data });
}

export async function POST(request: NextRequest) {
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
      path: "/api/admin/referrals",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const referrerOrgId = typeof body?.referrerOrgId === "string" ? body.referrerOrgId.trim() : "";
  const referrerPartnerId =
    typeof body?.referrerPartnerId === "string" ? body.referrerPartnerId.trim() : "";
  const referredOrgId = typeof body?.referredOrgId === "string" ? body.referredOrgId.trim() : "";
  const creditAmountCents =
    typeof body?.creditAmountCents === "number" ? body.creditAmountCents : NaN;
  const currency = typeof body?.currency === "string" ? body.currency.trim() : "";
  const reason = typeof body?.reason === "string" ? body.reason.trim() : "";
  const apply = body?.apply !== false; // defaults to true -- "records ... and applies it"

  if (
    (!referrerOrgId && !referrerPartnerId) ||
    !referredOrgId ||
    !Number.isInteger(creditAmountCents) ||
    creditAmountCents <= 0 ||
    !currency ||
    !reason
  ) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/admin/referrals",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "referredOrgId, exactly one of referrerOrgId/referrerPartnerId, a positive integer creditAmountCents, currency, and reason are all required",
      },
      { status: 400 },
    );
  }

  const recordResult = await recordReferralCredit({
    actor,
    referrerOrgId: referrerOrgId || null,
    referrerPartnerId: referrerPartnerId || null,
    referredOrgId,
    creditAmountCents,
    currency,
    reason,
  });
  if (!recordResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/admin/referrals",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: recordResult.error }, { status: 400 });
  }

  let credit = recordResult.data;
  if (apply) {
    const applyResult = await applyReferralCredit(credit.id, actor);
    if (!applyResult.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/admin/referrals",
        status: 502,
        requestId,
      });
      // The credit itself was recorded (a real row exists and is
      // returned below) even though applying it against Stripe failed
      // (e.g. the referred org has no Stripe customer on file yet) --
      // an honest partial result, not a fabricated full success.
      return NextResponse.json(
        { referralCredit: credit, applyError: applyResult.error },
        { status: 502 },
      );
    }
    credit = applyResult.data;
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/admin/referrals",
    status: 200,
    requestId,
  });
  return NextResponse.json({ referralCredit: credit });
}
