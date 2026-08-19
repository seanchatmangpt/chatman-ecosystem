import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  getSupportTicket,
  listSupportTicketMessages,
  postSupportTicketMessage,
  type SupportTicketMessageAuthorType,
} from "@/lib/support-tickets";

// Real ticket-thread messaging endpoint -- the piece missing between "SLA
// tier sold" and "SLA tier operable" per lib/support-tickets.ts's own
// module doc: app/api/orgs/[id]/tickets/[ticketId]/route.ts's PATCH only
// ever flips a status enum, with no message history behind it, so an
// enterprise support org could never actually run a ticket through this
// UI. This route is the two-way conversation thread that closes that
// gap, on the exact same org-scoped path family, auth model, and
// audit-log convention as the sibling tickets routes in this directory.
//
// Auth model matches app/api/orgs/[id]/tickets/route.ts exactly:
//   - GET: any authenticated member of THIS org (viewer and up) -- reading
//     the thread is not a privileged action.
//   - POST: any authenticated member of THIS org (viewer and up) may post
//     a message. `authorType` is never accepted from the request body --
//     it is derived server-side from the session the same way `actor` is
//     derived below, so a customer-role session can never post as
//     `support` and silently respond to their own ticket. Any session
//     that passes this org's `owner` role check is treated as `support`
//     (the same role floor app/api/orgs/[id]/tickets/[ticketId]/route.ts's
//     PATCH already uses for "the privileged act of responding"); every
//     other viewer-and-up session is treated as `customer`.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; ticketId: string }> },
) {
  const { id, ticketId } = await params;
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
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/tickets/${ticketId}/messages`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const ticketResult = await getSupportTicket(id, ticketId);
  if (!ticketResult.ok) {
    return NextResponse.json({ error: ticketResult.error }, { status: 502 });
  }
  if (!ticketResult.data) {
    return NextResponse.json({ error: "ticket not found" }, { status: 404 });
  }

  const messagesResult = await listSupportTicketMessages(ticketId);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/tickets/${ticketId}/messages`,
    status: messagesResult.ok ? 200 : 502,
    requestId,
  });
  if (!messagesResult.ok) {
    return NextResponse.json({ error: messagesResult.error }, { status: 502 });
  }
  return NextResponse.json({ messages: messagesResult.data });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; ticketId: string }> },
) {
  const { id, ticketId } = await params;
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
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tickets/${ticketId}/messages`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const requestBody = await request.json().catch(() => null);
  const body = typeof requestBody?.body === "string" ? requestBody.body.trim() : "";
  if (!body) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tickets/${ticketId}/messages`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "body is required" }, { status: 400 });
  }

  // authorType is derived server-side from role, never client-supplied
  // -- see module header comment.
  const supportAccess = await requireRoleIn(session, orgResult.data.namespace, "owner");
  const authorType: SupportTicketMessageAuthorType = supportAccess.ok ? "support" : "customer";

  const result = await postSupportTicketMessage({
    orgId: id,
    ticketId,
    authorType,
    authorId: actor,
    body,
  });
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/tickets/${ticketId}/messages`,
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    const notFound = result.error === "ticket not found";
    return NextResponse.json({ error: result.error }, { status: notFound ? 404 : 502 });
  }
  return NextResponse.json(
    { message: result.data.message, ticket: result.data.ticket },
    { status: 201 },
  );
}
