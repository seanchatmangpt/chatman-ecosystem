import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { getDeliveryRecord } from "@/lib/webhook-deliveries";
import { redeliverStoredEvent, type WebhookEventType } from "@/lib/webhooks";

// Real manual replay of a dead-lettered delivery: resends the EXACT
// persisted request body (see lib/webhooks.ts's redeliverStoredEvent) to
// the subscription's CURRENT url/secret, on demand, once automatic
// retries have been exhausted. Owner-gated the same way every other
// webhooks route is -- a replay is a real outbound HTTP POST, same
// exfiltration-adjacent sensitivity class as creating a subscription in
// the first place.
//
// Only a `dead_letter` row is eligible: a `delivered` row has nothing to
// replay, and a `pending_retry` row already has an automatic retry
// scheduled (lib/webhook-poller.ts's pollWebhookRetries) -- replaying it
// here too would just be a second, redundant attempt racing the
// scheduled one.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
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
  const path = `/api/webhooks/deliveries/${deliveryId}/replay`;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "POST", path, status: 403, requestId });
    return access.response!;
  }

  const recordResult = await getDeliveryRecord(deliveryId);
  if (!recordResult.ok) {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "POST", path, status: 502, requestId });
    return NextResponse.json({ error: recordResult.error }, { status: 502 });
  }
  const delivery = recordResult.data;
  if (!delivery) {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "POST", path, status: 404, requestId });
    return NextResponse.json({ error: "delivery not found" }, { status: 404 });
  }
  if (delivery.status !== "dead_letter") {
    writeAuditLogEntry({ timestamp: new Date().toISOString(), actor, method: "POST", path, status: 409, requestId });
    return NextResponse.json(
      { error: `delivery is '${delivery.status}', only a dead-lettered delivery can be replayed` },
      { status: 409 },
    );
  }

  const outcome = await redeliverStoredEvent({
    deliveryId: delivery.deliveryId,
    subscriptionId: delivery.subscriptionId,
    eventType: delivery.eventType as WebhookEventType,
    body: delivery.body,
    attemptNumber: delivery.attemptNumber + 1,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path,
    status: outcome ? (outcome.ok ? 200 : 502) : 404,
    requestId,
  });

  if (!outcome) {
    return NextResponse.json({ error: "subscription no longer exists" }, { status: 404 });
  }
  if (!outcome.ok) {
    return NextResponse.json(
      { error: outcome.error ?? "replay attempt failed", delivery: outcome },
      { status: 502 },
    );
  }
  return NextResponse.json({ delivery: outcome });
}
