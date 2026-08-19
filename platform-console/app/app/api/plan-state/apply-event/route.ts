import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { applyEntitlementEvent, isPlanState } from "@/lib/plan-state";

// Same owner-gated session boundary as app/api/plan-state/route.ts's POST
// (the ADMIN-OVERRIDE fallback route this one is a sibling of) -- this
// route is the manual-invoice ops path: it exists for enterprise
// customers billed OUTSIDE self-service Stripe checkout (a negotiated
// annual PO/invoice, the norm at Fortune-5 deal size), who therefore
// have no Stripe subscription record for reconcilePlanState() to ever
// read (see lib/plan-state.ts's own header). Ops applies their
// entitlement change here, through the SAME applyEntitlementEvent
// generic entrypoint the Stripe webhook route now calls -- so the change
// drives the exact same reconcilePlanState -> patchResourceQuotaHard
// enforcement path a Stripe-billed tenant's payment events drive,
// without a second enforcement code path.
//
// Deliberately restricted to `source: "manual-invoice"` only -- `admin`
// stays app/api/plan-state/route.ts's own POST, and `stripe` stays the
// webhook route's own signature-verified call site; this route does not
// let a caller impersonate either of those provenances.

const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/plan-state/apply-event",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const source = typeof body?.source === "string" ? body.source : "";
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const state = typeof body?.state === "string" ? body.state : "";
  const reason = typeof body?.reason === "string" ? body.reason.trim() : "";

  if (source !== "manual-invoice") {
    return NextResponse.json(
      { error: "source must be 'manual-invoice' -- 'stripe' and 'admin' are reserved for their own routes" },
      { status: 400 },
    );
  }
  if (!PLATFORM_NAMESPACES.includes(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!isPlanState(state)) {
    return NextResponse.json(
      { error: "state must be one of: active, past_due, suspended" },
      { status: 400 },
    );
  }
  if (!reason) {
    return NextResponse.json({ error: "reason is required" }, { status: 400 });
  }

  const result = await applyEntitlementEvent("manual-invoice", {
    namespace,
    state,
    reason: `${actor}: ${reason}`,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/plan-state/apply-event",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ record: result.data });
}
