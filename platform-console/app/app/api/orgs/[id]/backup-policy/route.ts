import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import {
  getBackupPolicy,
  setBackupPolicy,
  RETENTION_DEFAULT_DAYS,
  RETENTION_RANGE,
} from "@/lib/backup-retention";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real tiered backup-retention POLICY endpoint (see lib/backup-retention.ts
// for the full rationale). GET returns the org's effective policy --
// either its own explicit choice, or `RETENTION_DEFAULT_DAYS[tier]` for
// its current, live-derived ProjectTier (lib/orgs.ts's
// getOrgProjectTier), same "explicit value if set, else the tier's fixed
// default" split lib/orgs.ts's getOrgSla already establishes for
// SLA_TIER_DEFAULTS.
//
// PUT changes the retention window. Maker-checker gated the same way
// tier.downgrade already is (app/api/orgs/[id]/tier/route.ts) -- a
// retention change is a real compliance-evidence-affecting decision
// (shortening the window can destroy a customer's own regulatory
// evidence trail; lengthening it changes real storage cost), so it
// always requires a second, distinct owner-role approver, never applies
// on the first call. Same retry-based convention as every other
// requireApproval-gated route in this repo:
//   1. Caller must hold role >= owner IN THIS ORG's own namespace.
//   2. `retentionDays` must fall within `RETENTION_RANGE[tier]` for the
//      org's CURRENT tier -- checked before the approval request is even
//      created, so an out-of-range value is rejected with a real 400,
//      never silently clamped or queued for approval.
//   3. requireApproval checks for a fresh (<=24h) approved
//      `backup.retention.change` row for this org id. None exists on the
//      first call -- a pending request is created and this route returns
//      202.
//   4. A second, distinct owner approves via POST /api/approvals/[id].
//   5. The original caller retries PUT -- requireApproval now finds the
//      fresh approved row and the policy is actually written.

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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/backup-policy`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [tierResult, policyResult] = await Promise.all([
    getOrgProjectTier(org.namespace),
    getBackupPolicy(id),
  ]);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/backup-policy`,
    status: tierResult.ok && policyResult.ok ? 200 : 502,
    requestId,
  });

  if (!tierResult.ok) {
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }
  if (!policyResult.ok) {
    return NextResponse.json({ error: policyResult.error }, { status: 502 });
  }

  const tier = tierResult.data;
  const retentionDays = policyResult.data?.retentionDays ?? RETENTION_DEFAULT_DAYS[tier];

  return NextResponse.json({
    orgId: id,
    tier,
    retentionDays,
    isExplicit: policyResult.data !== null,
    allowedRange: RETENTION_RANGE[tier],
    defaultForTier: RETENTION_DEFAULT_DAYS[tier],
    policy: policyResult.data,
  });
}

export async function PUT(
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
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/backup-policy`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const retentionDaysRaw = body?.retentionDays;
  const retentionDays =
    typeof retentionDaysRaw === "number" && Number.isInteger(retentionDaysRaw)
      ? retentionDaysRaw
      : NaN;

  const tierResult = await getOrgProjectTier(org.namespace);
  if (!tierResult.ok) {
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }
  const tier = tierResult.data;
  const range = RETENTION_RANGE[tier];

  if (!Number.isInteger(retentionDays) || retentionDays < range.minDays || retentionDays > range.maxDays) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/backup-policy`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error: `retentionDays is required and must be an integer between ${range.minDays} and ${range.maxDays} for this org's '${tier}' tier`,
      },
      { status: 400 },
    );
  }

  const approval = await requireApproval({
    action: "backup.retention.change",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedRetentionDays: retentionDays },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/backup-policy`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/orgs/${id}/backup-policy`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "backup.retention.change requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this change, ` +
          "then retry PUT.",
      },
      { status: 202 },
    );
  }

  // A fresh approved row exists for THIS org's backup.retention.change --
  // apply the retention window that was actually approved
  // (resourcePayload.requestedRetentionDays on the approved row), not
  // whatever the caller happens to resend.
  const approvedDays = approval.approval.resourcePayload?.requestedRetentionDays ?? retentionDays;

  const result = await setBackupPolicy({
    orgId: id,
    tier,
    retentionDays: approvedDays,
    setBy: actor,
  });

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/orgs/${id}/backup-policy`,
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({
    policy: result.data,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
