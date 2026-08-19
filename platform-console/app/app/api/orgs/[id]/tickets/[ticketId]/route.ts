import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getSupportTicket, updateSupportTicketStatus } from "@/lib/support-tickets";

// PATCH-only companion to app/api/orgs/[id]/tickets/route.ts's GET/POST --
// the owner-role-gated "respond to" / "resolve" action against one real
// ticket already filed against this org. Owner-gated because responding
// to (or resolving) a support ticket is the exact privileged action this
// module exists to prove happens inside the SLA-tier's paid response-time
// commitment -- the same "org-admin/platform-admin only" floor
// app/api/orgs/[id]/sla/route.ts's own PUT already uses for the
// equivalent-weight action on this org.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function PATCH(
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/orgs/${id}/tickets/${ticketId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const requestBody = await request.json().catch(() => null);
  const status = requestBody?.status;
  if (status !== "responded" && status !== "resolved") {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/orgs/${id}/tickets/${ticketId}`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "status is required and must be one of: responded, resolved" },
      { status: 400 },
    );
  }

  const existing = await getSupportTicket(id, ticketId);
  if (!existing.ok) {
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "PATCH",
      path: `/api/orgs/${id}/tickets/${ticketId}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "ticket not found" }, { status: 404 });
  }

  const result = await updateSupportTicketStatus({ orgId: id, ticketId, status });
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "PATCH",
    path: `/api/orgs/${id}/tickets/${ticketId}`,
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "ticket not found" }, { status: 404 });
  }
  return NextResponse.json({ ticket: result.data });
}
