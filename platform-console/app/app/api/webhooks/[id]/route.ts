import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { deleteWebhookSubscription, getWebhookSubscriptionById } from "@/lib/webhooks";

// Real single-subscription-by-id handler -- GET /api/webhooks/[id] lets
// callers (e.g. a "view subscription" detail panel) fetch one
// subscription without pulling the whole listWebhookSubscriptions() page.
// DELETE /api/webhooks/[id] mirrors DELETE /api/webhooks (which takes the
// id as a ?id= query param) but as a path-scoped verb, both ultimately
// calling the same lib/webhooks.ts primitives. Owner-gated on every verb,
// same boundary as the parent /api/webhooks route and
// /api/webhooks/[id]/deliveries -- a webhook subscription's url/secret is
// exactly as sensitive here as it is there.
//
// No PATCH here: lib/webhooks.ts has no update primitive (no
// updateWebhookSubscription), and there's no decided business rule yet
// for what an "edit" should mean -- rotate the secret? change the URL
// in place (silently invalidating in-flight signature verification on
// the receiver's end)? change the eventType? Adding a PATCH would mean
// inventing that semantics rather than implementing a real one, so it's
// intentionally left out; the existing pattern (DELETE + POST a new
// subscription) is the only supported way to change one today.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
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
  const actor = session.sub;
  const path = `/api/webhooks/${id}`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "GET", path, status: 403, requestId });
    return access.response!;
  }

  const result = await getWebhookSubscriptionById(id);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path,
    status: result.ok ? (result.data ? 200 : 404) : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "subscription not found" }, { status: 404 });
  }
  return NextResponse.json({ subscription: result.data });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const path = `/api/webhooks/${id}`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "DELETE", path, status: 403, requestId });
    return access.response!;
  }

  const existing = await getWebhookSubscriptionById(id);
  if (existing.ok && !existing.data) {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "DELETE", path, status: 404, requestId });
    return NextResponse.json({ error: "subscription not found" }, { status: 404 });
  }

  const result = await deleteWebhookSubscription(id);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
