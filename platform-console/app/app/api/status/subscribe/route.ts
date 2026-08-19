import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  createStatusSubscription,
  deleteStatusSubscriptionByToken,
} from "@/lib/status-subscriptions";

// Deliberately no session check -- this is the public, self-service
// "Subscribe to updates" form on the public /status page (middleware.ts
// PUBLIC_PATHS already covers /status and /api/status; /api/status/
// subscribe is the same public posture, since a customer's NOC engineer
// subscribing to status changes has, by definition, no platform-console
// login). Same reasoning GET /api/status's own header comment documents.
export const dynamic = "force-dynamic";

interface SubscribeRequestBody {
  email?: unknown;
  webhookUrl?: unknown;
  componentFilter?: unknown;
}

function parseComponentFilter(value: unknown): { ok: true; data: string[] | null } | { ok: false } {
  if (value === undefined || value === null) return { ok: true, data: null };
  if (!Array.isArray(value) || !value.every((v) => typeof v === "string")) return { ok: false };
  return { ok: true, data: value.length > 0 ? value : null };
}

/**
 * Accepts an email OR a webhookUrl (exactly one -- mirrors
 * lib/status-subscriptions.ts's `StatusSubscriptionType` union), plus an
 * optional componentFilter, and returns the new subscription's id plus
 * its unsubscribeToken. Hand-written shape validation, same convention
 * every other route in this codebase uses at its boundary (no `zod`
 * dependency exists anywhere in this repo to reuse).
 */
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const body = (await request.json().catch(() => null)) as SubscribeRequestBody | null;

  if (!body || typeof body !== "object") {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }

  const hasEmail = typeof body.email === "string" && body.email.trim().length > 0;
  const hasWebhook = typeof body.webhookUrl === "string" && body.webhookUrl.trim().length > 0;

  if (hasEmail === hasWebhook) {
    // both or neither supplied
    return NextResponse.json(
      { error: "supply exactly one of email or webhookUrl" },
      { status: 400 },
    );
  }

  const filter = parseComponentFilter(body.componentFilter);
  if (!filter.ok) {
    return NextResponse.json(
      { error: "componentFilter must be an array of component id strings" },
      { status: 400 },
    );
  }

  const result = await createStatusSubscription({
    type: hasEmail ? "email" : "webhook",
    target: (hasEmail ? body.email : body.webhookUrl) as string,
    componentFilter: filter.data,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "public-status-subscriber",
    method: "POST",
    path: "/api/status/subscribe",
    status: result.ok ? 201 : result.status,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status });
  }

  return NextResponse.json(
    {
      subscriptionId: result.data.id,
      type: result.data.type,
      componentFilter: result.data.componentFilter,
      unsubscribeToken: result.data.unsubscribeToken,
    },
    { status: 201 },
  );
}

/**
 * Self-service unsubscribe: `DELETE /api/status/subscribe?unsubscribeToken=...`.
 * Possession of the token (returned once at creation, and embedded in
 * every notification lib/status-subscriptions.ts's notifyStatusSubscriber
 * sends) is the entire authorization -- see that module's header comment.
 * Idempotent: an already-removed or unknown token still returns 200 with
 * `removed: false`, never a 404/500, matching the "unsubscribe links
 * should never error on a second click" convention real status-page
 * products follow.
 */
export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.nextUrl.searchParams.get("unsubscribeToken");

  if (!token) {
    return NextResponse.json({ error: "unsubscribeToken query param required" }, { status: 400 });
  }

  const result = await deleteStatusSubscriptionByToken(token);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "public-status-subscriber",
    method: "DELETE",
    path: "/api/status/subscribe",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ removed: result.data.removed });
}
