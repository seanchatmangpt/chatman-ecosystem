import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import {
  getLeRequest,
  listLeRequests,
  markLeRequestUnderReview,
  recordLeRequestResponse,
} from "@/lib/le-requests";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";

// Real, session-authed Law-Enforcement / Government Data Request
// register endpoints -- see lib/le-requests.ts's own header comment for
// the full compliance rationale and the "ingest vs. act" write-path
// split.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: platform "owner" only (lib/authz.ts's requireRole), NOT
//     "member" -- unlike lib/subprocessors.ts's own registry (a static
//     compliance list every customer contact may reasonably see), a
//     single row here can name a real requesting government authority,
//     jurisdiction, and free-text summary of what was demanded about a
//     specific customer org; the public, aggregate-only rollup a
//     procurement reviewer actually needs pre-signature lives instead at
//     GET /api/trust (lib/trust-page.ts, sourced from
//     lib/le-requests.ts's own summarizeLeRequestsForTrustPage).
//   - PATCH: platform "owner", moves a row to "under_review" -- a real,
//     non-sensitive status transition (see lib/le-requests.ts's own
//     markLeRequestUnderReview doc comment for why this is not gated
//     behind maker-checker).
//   - PUT: platform "owner", gated behind the SAME maker-checker
//     `le-request.respond` approval workflow (lib/approval-workflow.ts's
//     requireApproval) `subprocessor.registry.update`/`dsar.erasure`
//     already use -- one owner's own say-so is never sufficient by
//     itself to record that customer data was actually disclosed to a
//     government requester.

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

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/le-requests",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId") ?? undefined;
  const result = await listLeRequests(orgId);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    ...(orgId ? { orgId } : {}),
    method: "GET",
    path: "/api/owner/le-requests",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ requests: result.data });
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
      path: "/api/owner/le-requests",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const targetRequestId = typeof (body as Record<string, unknown> | null)?.requestId === "string"
    ? (body as Record<string, string>).requestId
    : "";
  if (!targetRequestId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: "/api/owner/le-requests",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "requestId is required" }, { status: 400 });
  }

  const result = await markLeRequestUnderReview(targetRequestId);
  const status = !result.ok ? (result.error === "not_found" ? 404 : result.error === "already_responded" ? 409 : 502) : 200;

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor,
    method: "PATCH",
    path: "/api/owner/le-requests",
    status,
    requestId,
    leRequestId: targetRequestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status });
  }
  return NextResponse.json({ request: result.data });
}

const RESPONSE_STATUSES = ["disclosed", "narrowed", "objected", "rejected"] as const;
type ResponseStatus = (typeof RESPONSE_STATUSES)[number];
function isResponseStatus(value: unknown): value is ResponseStatus {
  return typeof value === "string" && (RESPONSE_STATUSES as readonly string[]).includes(value);
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
      path: "/api/owner/le-requests",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const targetRequestId = typeof v?.requestId === "string" ? v.requestId : "";
  const status = v?.status;
  const responseSummary = typeof v?.responseSummary === "string" ? v.responseSummary.trim() : "";

  if (!targetRequestId || !isResponseStatus(status) || !responseSummary) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/le-requests",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "requestId, status ('disclosed'|'narrowed'|'objected'|'rejected'), and responseSummary are required",
      },
      { status: 400 },
    );
  }

  const existing = await getLeRequest(targetRequestId);
  if (!existing.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/le-requests",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/le-requests",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `no LE request found with id '${targetRequestId}'` }, { status: 404 });
  }

  const approval = await requireApproval({
    action: "le-request.respond",
    targetId: targetRequestId,
    requestedBy: actor,
    resourcePayload: { requestedLeResponse: { status, responseSummary } },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/le-requests",
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
      path: "/api/owner/le-requests",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "le-request.respond requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize recording ` +
          "this response, then retry PUT with the same status and responseSummary.",
      },
      { status: 202 },
    );
  }

  const approvedResponse = approval.approval.resourcePayload?.requestedLeResponse ?? {
    status,
    responseSummary,
  };
  const result = await recordLeRequestResponse({
    requestId: targetRequestId,
    status: approvedResponse.status,
    responseSummary: approvedResponse.responseSummary,
    respondedBy: actor,
    approvedBy: approval.approval.approvedBy ?? actor,
  });

  if (!result.ok) {
    const respStatus = result.error === "not_found" ? 404 : result.error === "already_responded" ? 409 : 502;
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/le-requests",
      status: respStatus,
      requestId,
      leRequestId: targetRequestId,
    });
    return NextResponse.json({ error: result.error }, { status: respStatus });
  }

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor,
    ...(result.data.orgId ? { orgId: result.data.orgId } : {}),
    method: "PUT",
    path: "/api/owner/le-requests",
    status: 200,
    requestId,
    leRequestAction: "responded",
    leRequestId: targetRequestId,
    leRequestType: result.data.requestType,
  });

  return NextResponse.json({
    applied: true,
    request: result.data,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
