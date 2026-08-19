import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { applyStripeEvent, verifyStripeWebhookSignature } from "@/lib/stripe-billing";
import { applyEntitlementEvent, mapStripeStatusToPlanState } from "@/lib/plan-state";
import { syncRenewalDateFromStripe } from "@/lib/contract-renewals";

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
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
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

  // Proactively drive lib/plan-state.ts's plan-state ConfigMap through
  // the SAME generic entrypoint applyEntitlementEvent('stripe', ...)
  // that a non-Stripe billing path (e.g. the manual-invoice admin route)
  // uses too, rather than only via reconcilePlanState's own
  // listStoredSubscriptions() read on its next 10s poller tick. This is
  // a best-effort immediacy improvement, not a new source of truth --
  // reconcilePlanState still re-derives from live Stripe subscription
  // data every tick, so a failure here does not desync enforcement.
  if (applied.data) {
    const entitlementResult = await applyEntitlementEvent("stripe", {
      namespace: applied.data.tenantNamespace,
      state: mapStripeStatusToPlanState(applied.data.status),
      reason: `${verified.data.type} (event ${verified.data.id})`,
    });
    if (!entitlementResult.ok) {
      console.error(`[stripe-webhook] applyEntitlementEvent failed: ${entitlementResult.error}`);
    }

    // Real renewal-date resync (lib/contract-renewals.ts): re-derives the
    // org's tracked renewalDate from THIS SAME applied event's real
    // Stripe currentPeriodEnd -- best-effort, same non-fatal posture as
    // the entitlement sync above. A failure here never fails the webhook
    // response (Stripe would otherwise retry an event this app already
    // durably applied to plan state).
    const renewalResult = await syncRenewalDateFromStripe(
      applied.data.tenantNamespace,
      applied.data.currentPeriodEnd,
    );
    if (!renewalResult.ok) {
      console.error(`[stripe-webhook] syncRenewalDateFromStripe failed: ${renewalResult.error}`);
    }
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
