import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { requireApproval } from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  getExportSubscription,
  listExportSubscriptionRuns,
  upsertExportSubscription,
  runExportSubscription,
  runDueExportSubscriptions,
  isExportCadence,
  isExportScope,
  isEncryptionConfigured,
  EXPORT_SUBSCRIPTION_CRON_SCHEDULE,
  safeCompareSecret,
  type ExportSubscription,
} from "@/lib/s3-export-subscription";

// Real "bring your own bucket" scheduled export subscription endpoint
// (lib/s3-export-subscription.ts) -- the recurring, unattended
// counterpart to POST /api/projects/[name]/export-all and
// GET /api/audit/export, both of which only ever hand a payload back to
// the calling browser once. This route configures a per-org subscription
// that ships either the audit-log NDJSON export or the full tenant
// export bundle to a customer-owned S3-compatible bucket on a daily or
// weekly schedule.
//
// `id` resolution follows the exact same convention every other
// `/api/orgs/[id]/*` route in this tree already uses (see
// compliance-reports/route.ts's own header comment): resolve against the
// real `platform-console-orgs` registry first; when `id` doesn't resolve
// there, `id` is used directly as both the org id AND the k8s namespace.
//
// One reserved id, `_cron`, is NOT a real org -- it is the fan-out target
// lib/scheduled-jobs.ts's `createExportSubscriptionCronJob` curls on a
// fixed schedule (see that module's header comment), authenticated by a
// real shared secret (`x-export-subscription-cron-secret` matching this
// pod's own `process.env.EXPORT_SUBSCRIPTION_CRON_SECRET`) rather than a
// session cookie, the same "checked before the session cookie so the
// CronJob's sessionless Pod can reach this route at all" pattern
// compliance-reports/route.ts's own `isCronAuthenticated` already
// establishes. A POST to `/api/orgs/_cron/export-subscription` runs
// `runDueExportSubscriptions` (every enabled, due subscription across
// every org) instead of touching any single org's config.
//
// Auth model for a real org id:
//   - GET: any authenticated member of this org (viewer and up) -- same
//     posture as region/branding's own GET. Never returns decrypted
//     credentials (getExportSubscription's own stored shape has no
//     plaintext credential field to leak in the first place).
//   - POST (create/update): owner of THIS org, AND maker-checker-gated
//     via lib/approval-workflow.ts's `export-subscription.update` action
//     -- this is a standing, recurring data-exfiltration control, so
//     saving it requires a second, distinct owner-role approver, same
//     "owner required to even file the request, not just to approve it"
//     shape DELETE /api/orgs/[id] already establishes for org.delete.
//   - POST with `{"action":"run"}`: owner-only, runs the subscription
//     immediately (no approval gate -- it can only ever execute the
//     ALREADY-approved, already-saved config, never change it).

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.EXPORT_SUBSCRIPTION_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-export-subscription-cron-secret");
  if (!presented) return false;
  return safeCompareSecret(presented, expected);
}

/** Never includes the two encrypted credential fields -- a GET response
 * body is the one place this route could accidentally round-trip
 * ciphertext back to a client for no reason; this shape is the
 * deliberate allowlist of exactly what the UI needs to render the form
 * and status. */
function toPublicSubscription(subscription: ExportSubscription) {
  return {
    orgId: subscription.orgId,
    bucketEndpoint: subscription.bucketEndpoint,
    bucketName: subscription.bucketName,
    prefix: subscription.prefix,
    cadence: subscription.cadence,
    scope: subscription.scope,
    enabled: subscription.enabled,
    lastRunAt: subscription.lastRunAt,
    lastRunStatus: subscription.lastRunStatus,
    updatedAt: subscription.updatedAt,
    updatedBy: subscription.updatedBy,
    hasCredentials: Boolean(subscription.accessKeyIdEncrypted && subscription.secretAccessKeyEncrypted),
  };
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();

  if (id === "_cron") {
    return NextResponse.json({ error: "GET is not supported for the cron fan-out target" }, { status: 400 });
  }

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  const namespace = orgResult.data ? orgResult.data.namespace : id;

  const access = await requireRoleIn(session, namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/export-subscription`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [subscriptionResult, runsResult] = await Promise.all([
    getExportSubscription(id),
    listExportSubscriptionRuns(id),
  ]);

  const status = subscriptionResult.ok && runsResult.ok ? 200 : 502;
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/export-subscription`,
    status,
    requestId,
  });

  if (!subscriptionResult.ok) return NextResponse.json({ error: subscriptionResult.error }, { status: 502 });
  if (!runsResult.ok) return NextResponse.json({ error: runsResult.error }, { status: 502 });

  return NextResponse.json({
    subscription: subscriptionResult.data ? toPublicSubscription(subscriptionResult.data) : null,
    runs: runsResult.data,
    cronSchedule: subscriptionResult.data ? EXPORT_SUBSCRIPTION_CRON_SCHEDULE[subscriptionResult.data.cadence] : null,
    encryptionConfigured: isEncryptionConfigured(),
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();

  // ---------------------------------------------------- cron fan-out
  if (id === "_cron") {
    if (!isCronAuthenticated(request)) {
      return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
    }
    const result = await runDueExportSubscriptions();
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "export-subscription-cronjob",
      method: "POST",
      path: `/api/orgs/_cron/export-subscription`,
      status: result.ok ? 200 : 502,
      requestId,
    });
    if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
    return NextResponse.json(result.data);
  }

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
  const namespace = orgResult.data.namespace;

  const access = await requireRoleIn(session, namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/export-subscription`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = (await request.json().catch(() => null)) as Record<string, unknown> | null;
  if (!body) {
    return NextResponse.json({ error: "request body must be valid JSON" }, { status: 400 });
  }

  // ------------------------------------------------- run-now (no gate)
  if (body.action === "run") {
    const runResult = await runExportSubscription(id);
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/export-subscription`,
      status: runResult.ok ? 200 : 502,
      requestId,
    });
    if (!runResult.ok) return NextResponse.json({ error: runResult.error }, { status: 502 });
    return NextResponse.json({ run: runResult.data });
  }

  // ------------------------------------------------- create/update
  const bucketEndpoint = typeof body.bucketEndpoint === "string" ? body.bucketEndpoint.trim() : "";
  const bucketName = typeof body.bucketName === "string" ? body.bucketName.trim() : "";
  const accessKeyId = typeof body.accessKeyId === "string" ? body.accessKeyId : "";
  const secretAccessKey = typeof body.secretAccessKey === "string" ? body.secretAccessKey : "";
  const prefix = typeof body.prefix === "string" ? body.prefix.trim() : "";
  const cadence = typeof body.cadence === "string" ? body.cadence : "";
  const scope = typeof body.scope === "string" ? body.scope : "";
  const enabled = typeof body.enabled === "boolean" ? body.enabled : true;

  if (!isExportCadence(cadence)) {
    return NextResponse.json({ error: "cadence must be 'daily' or 'weekly'" }, { status: 400 });
  }
  if (!isExportScope(scope)) {
    return NextResponse.json({ error: "scope must be 'audit-log' or 'full-export'" }, { status: 400 });
  }

  const approval = await requireApproval({
    action: "export-subscription.update",
    targetId: id,
    requestedBy: actor,
    resourcePayload: {
      requestedExportSubscription: { bucketEndpoint, bucketName, prefix, cadence, scope, enabled },
    },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/export-subscription`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    // No fresh second-approver sign-off yet -- the real write does NOT
    // happen, and the credentials this request carried are never
    // persisted anywhere (not even the pending approval row -- see
    // ApprovalResourcePayload.requestedExportSubscription's own doc
    // comment). 202 Accepted, matching DELETE /api/orgs/[id]'s own
    // "accepted, not completed" convention.
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/export-subscription`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "export-subscription.update requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${approval.request.requestId} {decision:'approved'} to authorize this change, then retry POST with ` +
          "the same bucket config to save it.",
      },
      { status: 202 },
    );
  }

  const result = await upsertExportSubscription({
    orgId: id,
    bucketEndpoint,
    bucketName,
    accessKeyId,
    secretAccessKey,
    prefix,
    cadence,
    scope,
    enabled,
    updatedBy: actor,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/export-subscription`,
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ subscription: toPublicSubscription(result.data), approvedBy: approval.approval.approvedBy });
}
