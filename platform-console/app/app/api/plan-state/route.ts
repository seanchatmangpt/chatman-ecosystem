import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { isPlanState, listPlanStates, setPlanState } from "@/lib/plan-state";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Owner-gated on every verb, same boundary as /api/quota-enforcement:
// this route's POST sets the ADMIN-OVERRIDE fallback plan state that
// lib/plan-state.ts's reconcilePlanState() only consults for a namespace
// Stripe has no subscription record for (see that function's own header
// comment) -- lib/webhook-poller.ts's existing 10s tick then acts on it
// by suspending (or restoring) that namespace's real ResourceQuota, same
// consequential-action class as quota enforcement's own config route.
// This is the manual/ops/testing path; app/api/billing/stripe/webhook/
// route.ts (app/lib/stripe-billing.ts) is the real, HMAC-verified source
// of truth whenever a Stripe subscription actually exists.

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

export async function GET(request: NextRequest) {
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
      method: "GET",
      path: "/api/plan-state",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // listPlanStates is the READ-ONLY path -- never patches a ResourceQuota
  // or writes an `enforced.*`/`saved-hard.*` marker, so a page view can
  // never race the poller's own reconcilePlanState() into a duplicate
  // enforcement action.
  const result = await listPlanStates();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/plan-state",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ namespaces: PLATFORM_NAMESPACES, statuses: result.data });
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
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/plan-state",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const planState = typeof body?.planState === "string" ? body.planState : "";

  if (!PLATFORM_NAMESPACES.includes(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!isPlanState(planState)) {
    return NextResponse.json(
      { error: "planState must be one of: active, past_due, suspended" },
      { status: 400 },
    );
  }

  const result = await setPlanState(namespace, planState, `admin:${actor}`);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/plan-state",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ record: result.data });
}
