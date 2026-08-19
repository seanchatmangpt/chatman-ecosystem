import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { createSupportTicket, listSupportTickets } from "@/lib/support-tickets";

// Real support-ticket SLA-timer endpoint: closes the gap that
// lib/tiers.ts's SlaTier (standard/priority/enterprise-247, with real
// slaResponseTimeHours of 24/4/1) had nothing in this repo starting a
// clock against it or tracking whether a real response happened. Backed
// by lib/support-tickets.ts's `platform_console.support_tickets` table on
// the same live demo-project Postgres lib/audit-db.ts already treats as
// this console's own operational store.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree (see
// app/api/orgs/[id]/sla/route.ts's own header comment for the full
// reasoning):
//   - GET: any authenticated member of THIS org (viewer and up) --
//     reading a support ticket list is not a privileged action.
//   - POST: any authenticated member of THIS org (viewer and up) can file
//     a ticket -- filing a support request is not a privileged action
//     either; the privileged action is RESPONDING to one (owner-gated on
//     the [ticketId] PATCH route).

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

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/tickets`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const ticketsResult = await listSupportTickets(id);
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/tickets`,
    status: ticketsResult.ok ? 200 : 502,
    requestId,
  });
  if (!ticketsResult.ok) {
    return NextResponse.json({ error: ticketsResult.error }, { status: 502 });
  }
  return NextResponse.json({ tickets: ticketsResult.data });
}

export async function POST(
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

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tickets`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const requestBody = await request.json().catch(() => null);
  const subject = typeof requestBody?.subject === "string" ? requestBody.subject.trim() : "";
  const body = typeof requestBody?.body === "string" ? requestBody.body.trim() : "";
  if (!subject || !body) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/tickets`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "subject and body are both required" }, { status: 400 });
  }

  const result = await createSupportTicket({ orgId: id, subject, body });
  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/tickets`,
    status: result.ok ? 201 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ticket: result.data }, { status: 201 });
}
