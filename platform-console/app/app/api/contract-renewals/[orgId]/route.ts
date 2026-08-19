import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requirePlatformAdmin, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  getContractRenewal,
  setContractRenewalPolicy,
  type ContractRenewalDecision,
} from "@/lib/contract-renewals";

// Per-org contract-renewal read/write -- the [orgId] counterpart to the
// cross-org list at GET /api/contract-renewals. Platform-admin gated,
// same as the list route: renewal/non-renewal decisions are a
// procurement/finance-adjacent record this repo treats the same way it
// treats budget thresholds and referral credits, not a per-org
// self-service setting an org's own owner can flip.
//
// POST records autoRenew/noticeThresholdDays/decision (each
// independently optional -- a partial update) and writes one real
// audit-db.ts entry, same "audit-logged like every other org.*
// mutation" convention as lib/orgs.ts's own setOrgSla/setOrgRegion
// routes. No maker-checker approval step (lib/approval-workflow.ts) --
// this is an informational decision record, not an actuating mutation
// (it never itself cancels/creates a Stripe subscription), matching the
// spec's own "maker-checker not required here" wording.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isDecision(value: unknown): value is ContractRenewalDecision {
  return value === "pending" || value === "renewed" || value === "declined";
}

export async function GET(
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
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/contract-renewals/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getContractRenewal(orgId);
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/contract-renewals/${orgId}`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "no contract renewal record for this org" }, { status: 404 });
  }
  return NextResponse.json({ renewal: result.data });
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
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/contract-renewals/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/contract-renewals/${orgId}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/contract-renewals/${orgId}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const body = await request.json().catch(() => null);
  const hasAutoRenew = typeof body?.autoRenew === "boolean";
  const hasNoticeThresholdDays =
    typeof body?.noticeThresholdDays === "number" &&
    Number.isFinite(body.noticeThresholdDays) &&
    body.noticeThresholdDays > 0;
  const hasDecision = typeof body?.decision === "string" && isDecision(body.decision);

  if (
    (body?.autoRenew !== undefined && !hasAutoRenew) ||
    (body?.noticeThresholdDays !== undefined && !hasNoticeThresholdDays) ||
    (body?.decision !== undefined && !hasDecision) ||
    (!hasAutoRenew && !hasNoticeThresholdDays && !hasDecision)
  ) {
    writeAuditLogEntry({
      orgId: orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/contract-renewals/${orgId}`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "at least one of autoRenew (boolean), noticeThresholdDays (positive number), decision ('pending'|'renewed'|'declined') is required, and any provided field must be well-formed",
      },
      { status: 400 },
    );
  }

  const result = await setContractRenewalPolicy(
    orgId,
    {
      autoRenew: hasAutoRenew ? (body.autoRenew as boolean) : undefined,
      noticeThresholdDays: hasNoticeThresholdDays ? (body.noticeThresholdDays as number) : undefined,
      decision: hasDecision ? (body.decision as ContractRenewalDecision) : undefined,
    },
    actor,
  );

  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/contract-renewals/${orgId}`,
    status: !result.ok ? 502 : result.data ? 200 : 404,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json(
      { error: "no contract renewal record for this org -- it has not yet synced a Stripe renewal date" },
      { status: 404 },
    );
  }
  return NextResponse.json({ renewal: result.data });
}
