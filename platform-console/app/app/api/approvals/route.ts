import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import {
  ACTIONS_REQUIRING_APPROVAL,
  createApprovalRequest,
  listApprovals,
  type ApprovalAction,
} from "@/lib/approval-workflow";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real maker-checker approval-workflow endpoints -- the second half of
// the "second approver" control lib/approval-workflow.ts implements.
// POST is normally called INTERNALLY by a guarded route (e.g. DELETE
// /api/orgs/[id]) the moment it finds no fresh approved row for its
// target, but is also exposed here so an owner can pre-file a request
// for an action that hasn't been attempted yet. GET lists every
// pending/recent approval so the /approvals UI has something to render.
//
// Auth model: any authenticated session may list (an approver needs to
// see what's pending before deciding); creating a request requires
// "member" and up -- the same floor every other mutating action in this
// console requires -- never "viewer", since a request that can be filed
// by an unauthenticated-equivalent identity would make the whole gate
// pointless.

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

  const result = await listApprovals();
  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/approvals",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ approvals: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/approvals",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const action = typeof body?.action === "string" ? body.action : "";
  const targetId = typeof body?.targetId === "string" ? body.targetId.trim() : "";

  if (!ACTIONS_REQUIRING_APPROVAL.includes(action as ApprovalAction)) {
    return NextResponse.json(
      { error: `action must be one of: ${ACTIONS_REQUIRING_APPROVAL.join(", ")}` },
      { status: 400 },
    );
  }
  if (!targetId) {
    return NextResponse.json({ error: "targetId is required" }, { status: 400 });
  }

  const result = await createApprovalRequest({
    action: action as ApprovalAction,
    targetId,
    requestedBy: actor,
  });
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/approvals",
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ approval: result.data }, { status: 201 });
}
