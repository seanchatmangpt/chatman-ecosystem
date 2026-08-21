import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import {
  addAffectedOrgs,
  fileChangeOfControlTrigger,
  listChangeOfControlStatus,
  recordOrgNotification,
  validateChangeOfControlTriggerInput,
  type ChangeOfControlEventType,
} from "@/lib/change-of-control-notifications";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real, session-authed Change-of-Control / M&A Notification Register
// endpoints -- see lib/change-of-control-notifications.ts's own header
// comment for the full compliance rationale and the trigger-vs.-
// notification-row write-path split.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: platform "owner" only (lib/authz.ts's requireRole), NOT
//     "member" -- same bar lib/le-requests.ts's own register sets: a row
//     here names a real customer org and a real, potentially
//     market-sensitive M&A event, not a static public compliance list
//     like lib/subprocessors.ts's registry.
//   - POST: platform "owner", files a new trigger. A real,
//     non-customer-facing record-keeping action (mirrors lib/le-
//     requests.ts's own ingest-vs.-act split: filing is unprivileged-
//     relative-to-owner, ACTING -- PUT below -- is the maker-checker-
//     gated step) -- not gated behind approval of its own.
//   - PATCH: platform "owner", widens an existing trigger's affected-org
//     list. Same non-customer-facing record-keeping bar as POST.
//   - PUT: platform "owner", gated behind the SAME maker-checker
//     `change-of-control.notify` approval workflow (lib/approval-
//     workflow.ts's requireApproval) `le-request.respond`/`denied-party
//     .override` already use -- one owner's own say-so is never
//     sufficient by itself to record, in a compliance ledger legal
//     relies on, that a Fortune 5 customer's contractual notice was
//     actually delivered.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const EVENT_TYPES = ["acquisition", "merger", "ownership_change"] as const;
function isEventType(value: unknown): value is ChangeOfControlEventType {
  return typeof value === "string" && (EVENT_TYPES as readonly string[]).includes(value);
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/change-of-control",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const triggerId = request.nextUrl.searchParams.get("triggerId") ?? undefined;
  const result = await listChangeOfControlStatus(triggerId);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/owner/change-of-control",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    rows: result.data,
    breachCount: result.data.filter((r) => r.inBreach).length,
  });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/change-of-control",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const eventType = v?.eventType;
  const description = typeof v?.description === "string" ? v.description : "";
  const triggerDate = typeof v?.triggerDate === "string" ? v.triggerDate : "";
  const noticeWindowDays = typeof v?.noticeWindowDays === "number" ? v.noticeWindowDays : undefined;
  const affectedOrgIds = Array.isArray(v?.affectedOrgIds)
    ? v.affectedOrgIds.filter((o): o is string => typeof o === "string")
    : [];

  const validationError = validateChangeOfControlTriggerInput({
    eventType,
    description,
    triggerDate,
    noticeWindowDays,
    affectedOrgIds,
  });
  if (validationError) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/change-of-control",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: validationError }, { status: 400 });
  }

  const result = await fileChangeOfControlTrigger({
    eventType: eventType as ChangeOfControlEventType,
    description,
    triggerDate,
    noticeWindowDays,
    affectedOrgIds,
    filedBy: actor,
  });

  if (!result.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/change-of-control",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  return NextResponse.json({ trigger: result.data }, { status: 201 });
}

export async function PATCH(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: "/api/owner/change-of-control",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const triggerId = typeof v?.triggerId === "string" ? v.triggerId : "";
  const orgIds = Array.isArray(v?.orgIds) ? v.orgIds.filter((o): o is string => typeof o === "string") : [];

  if (!triggerId || orgIds.length === 0) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: "/api/owner/change-of-control",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "triggerId and a non-empty orgIds array are required" },
      { status: 400 },
    );
  }

  const result = await addAffectedOrgs({ triggerId, orgIds, actor });
  if (!result.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: "/api/owner/change-of-control",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: "/api/owner/change-of-control",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `no change-of-control trigger found with id '${triggerId}'` }, { status: 404 });
  }

  return NextResponse.json({ trigger: result.data });
}

export async function PUT(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/change-of-control",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const triggerId = typeof v?.triggerId === "string" ? v.triggerId : "";
  const orgId = typeof v?.orgId === "string" ? v.orgId : "";
  const notificationMethod = typeof v?.notificationMethod === "string" ? v.notificationMethod.trim() : "";

  if (!triggerId || !orgId || !notificationMethod) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/change-of-control",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "triggerId, orgId, and notificationMethod are required" },
      { status: 400 },
    );
  }

  const targetId = `${triggerId}.${orgId}`;
  const approval = await requireApproval({
    action: "change-of-control.notify",
    targetId,
    requestedBy: actor,
    resourcePayload: { requestedChangeOfControlNotification: { triggerId, orgId, notificationMethod } },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/change-of-control",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/change-of-control",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "change-of-control.notify requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize recording ` +
          "this notification, then retry PUT with the same triggerId, orgId, and notificationMethod.",
      },
      { status: 202 },
    );
  }

  const approvedNotification = approval.approval.resourcePayload?.requestedChangeOfControlNotification ?? {
    triggerId,
    orgId,
    notificationMethod,
  };
  const result = await recordOrgNotification({
    triggerId: approvedNotification.triggerId,
    orgId: approvedNotification.orgId,
    notificationMethod: approvedNotification.notificationMethod,
    recordedBy: actor,
    approvedBy: approval.approval.approvedBy ?? actor,
  });

  if (!result.ok) {
    const status = result.error === "not_found" ? 404 : result.error === "already_notified" ? 409 : 502;
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/change-of-control",
      status,
      requestId,
    });
    return NextResponse.json({ error: result.error }, { status });
  }

  return NextResponse.json({
    applied: true,
    notification: result.data,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
