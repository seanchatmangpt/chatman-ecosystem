import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { applyStripeEvent, verifyStripeWebhookSignature } from "@/lib/stripe-billing";

// No session cookie check here on purpose -- this endpoint is called by
// Stripe's own servers, not a browser with this app's session cookie.
// Authenticity is instead established the way every real Stripe
// integration establishes it: `verifyStripeWebhookSignature` recomputes
// the real HMAC-SHA256 over `timestamp.rawBody` using
// STRIPE_WEBHOOK_SECRET and rejects anything that doesn't match --
// the same signature-verification discipline lib/webhooks.ts documents
// for this app's own outbound webhooks, applied here as the receiver.
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const signatureHeader = request.headers.get("stripe-signature");
  if (!signatureHeader) {
    return NextResponse.json({ error: "missing Stripe-Signature header" }, { status: 400 });
  }

  // Raw body, not request.json(): signature verification is over the
  // exact bytes Stripe signed -- re-serializing a parsed object would
  // not reproduce the same bytes and would make every signature fail.
  const rawBody = await request.text();

  const verified = verifyStripeWebhookSignature(rawBody, signatureHeader);
  if (!verified.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "stripe-webhook",
      method: "POST",
      path: "/api/billing/stripe/webhook",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: verified.error }, { status: 400 });
  }

  const applied = await applyStripeEvent(verified.data);
  if (!applied.ok) {
    // Signature was valid; applying the event to stored state failed
    // (e.g. k8s API unreachable). Return 500 so Stripe retries delivery
    // per its own retry contract, rather than silently dropping it.
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "stripe-webhook",
      method: "POST",
      path: "/api/billing/stripe/webhook",
      status: 500,
      requestId,
    });
    return NextResponse.json({ error: applied.error }, { status: 500 });
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "stripe-webhook",
    method: "POST",
    path: "/api/billing/stripe/webhook",
    status: 200,
    requestId,
  });

  return NextResponse.json({ received: true, eventType: verified.data.type, eventId: verified.data.id });
}
