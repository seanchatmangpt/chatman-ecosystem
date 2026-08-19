import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listAttemptsForDelivery } from "@/lib/webhook-deliveries";

// Full, ordered, IMMUTABLE per-attempt history for one delivery -- the
// real forensic trail lib/webhook-deliveries.ts's
// webhook_delivery_attempts table exists for: every attempt's
// http_status/error/duration_ms exactly as it was recorded at the time,
// never overwritten by a later attempt. Owner-gated the same way
// GET /api/webhooks/[id]/deliveries already is: an attempt row's `url`
// and error text is exactly as sensitive as the delivery/subscription
// that produced it.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ deliveryId: string }> },
) {
  const { deliveryId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const path = `/api/webhooks/deliveries/${deliveryId}/attempts`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "GET", path, status: 403, requestId });
    return access.response!;
  }

  const result = await listAttemptsForDelivery(deliveryId);

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
  return NextResponse.json({ attempts: result.data });
}
