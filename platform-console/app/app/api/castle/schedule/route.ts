import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { ALLOWED_CASTLE_VERBS, resolveCastleVerb } from "@/lib/castle";
import {
  cancelScheduledVerb,
  listScheduledVerbs,
  scheduleCastleVerb,
} from "@/lib/scheduled-verbs";

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

/**
 * GET: every real ScheduledVerb row this module has ever written --
 * "the listing IS the record", same convention GET /api/castle already
 * uses. No RBAC gate beyond authentication, same "viewing is member+ but
 * every session is at least viewer" posture GET /api/castle's own doc
 * comment already documents.
 */
export async function GET(request: NextRequest) {
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const result = await listScheduledVerbs();
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ scheduled: result.data });
}

/**
 * POST: member+ files a real, pending ScheduledVerb plus its own
 * lib/approval-workflow.ts maker-checker request (action
 * "castle.verb.schedule") -- never runs anything itself. A second,
 * distinct owner-role approver signs off via the existing generic
 * POST /api/approvals/[id]; the real execution only happens later, when
 * the CronJob lib/batch-jobs.ts's createCastleScheduleCronJob polls
 * POST /api/castle/schedule/run-due at (or after) `requestedFor`, and
 * only if a fresh approval is still on file at that moment.
 *
 * Body: { verbId, requestedFor } -- `requestedFor` must be a real,
 * parseable ISO timestamp strictly in the future.
 */
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
      path: "/api/castle/schedule",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const verbId = typeof body?.verbId === "string" ? body.verbId.trim() : "";
  const requestedFor = typeof body?.requestedFor === "string" ? body.requestedFor.trim() : "";

  if (!resolveCastleVerb(verbId)) {
    return NextResponse.json(
      { error: `verbId must be one of: ${Object.keys(ALLOWED_CASTLE_VERBS).join(", ")}` },
      { status: 400 },
    );
  }
  if (!requestedFor) {
    return NextResponse.json({ error: "requestedFor (ISO timestamp) is required" }, { status: 400 });
  }

  const result = await scheduleCastleVerb({ verbId, requestedFor, requestedBy: actor });

  if (!result.ok) {
    const status =
      result.error === "invalid_verb" || result.error === "invalid_requested_for" || result.error === "in_the_past"
        ? 400
        : 502;
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/castle/schedule",
      status,
      requestId,
    });
    const messages: Record<string, string> = {
      invalid_verb: "verbId is not in the castle verb allowlist",
      invalid_requested_for: "requestedFor must be a valid ISO timestamp",
      in_the_past: "requestedFor must be strictly in the future",
    };
    return NextResponse.json({ error: messages[result.error] ?? result.error }, { status });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/castle/schedule",
    status: 202,
    requestId,
  });

  return NextResponse.json(
    {
      status: "pending_approval",
      scheduled: result.scheduled,
      approval: result.approval,
      message:
        "castle.verb.schedule requires a second, distinct owner-role approver -- POST /api/approvals/" +
        `${result.approval.requestId} {decision:'approved'} to authorize this scheduled run. Once ` +
        "approved, it fires automatically at requestedFor -- no further action needed here.",
    },
    { status: 202 },
  );
}

/**
 * DELETE: cancels a real pending ScheduledVerb. `?id=<scheduledVerbId>`.
 * member+ (same role bar as POST/RUN) -- refused, not silently ignored,
 * once the row has already executed or was already cancelled
 * (lib/scheduled-verbs.ts's cancelScheduledVerb).
 */
export async function DELETE(request: NextRequest) {
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
      method: "DELETE",
      path: "/api/castle/schedule",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const id = request.nextUrl.searchParams.get("id")?.trim();
  if (!id) {
    return NextResponse.json({ error: "id query parameter is required" }, { status: 400 });
  }

  const result = await cancelScheduledVerb(id, actor);
  if (!result.ok) {
    const status = result.error === "not_found" ? 404 : result.error === "not_pending" ? 409 : 502;
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/castle/schedule",
      status,
      requestId,
    });
    const messages: Record<string, string> = {
      not_found: "scheduled verb not found",
      not_pending: "this scheduled verb is no longer pending -- it already ran or was already cancelled",
    };
    return NextResponse.json({ error: messages[result.error] ?? result.error }, { status });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/castle/schedule",
    status: 200,
    requestId,
  });
  return NextResponse.json({ scheduled: result.data });
}
