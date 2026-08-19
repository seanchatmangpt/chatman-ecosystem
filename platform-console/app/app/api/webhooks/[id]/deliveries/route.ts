import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listDeliveriesForSubscription } from "@/lib/webhook-deliveries";

// Real delivery history for one webhook subscription -- backs the
// "View deliveries" panel in components/WebhookDeliveryLog.tsx. Owner
// gated the same way GET /api/webhooks itself is: a delivery row's `url`
// and HTTP status/error is exactly as sensitive as the subscription that
// produced it.

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
  const path = `/api/webhooks/${id}/deliveries`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "GET", path, status: 403, requestId });
    return access.response!;
  }

  const result = await listDeliveriesForSubscription(id);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ deliveries: result.data });
}
