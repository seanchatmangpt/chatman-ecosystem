import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listCostAnomalyStatus, setAnomalyThreshold } from "@/lib/cost-anomaly";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Owner-gated on every verb, same boundary as /api/budget-alerts: cost
// anomaly state governs a real financial-adjacent signal even though no
// real payment method or processor is ever involved anywhere in this
// platform.

// Same platform-namespace roster /api/budget-alerts, /api/billing, and
// app/cost/page.tsx already use -- the fixed set of namespaces this
// cluster actually meters, never an arbitrary client-supplied namespace
// string interpolated into a PromQL selector.
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

/**
 * GET-only, mirroring lib/quota-enforcement.ts's read-only status route
 * pattern: this detector is entirely poller-driven (see
 * lib/webhook-poller.ts's pollCostAnomalies), so there is no POST to
 * trigger a check -- only setAnomalyThreshold's per-namespace operator
 * override, exposed here as GET's sibling PUT verb, matching
 * /api/budget-alerts's own threshold-set convention.
 */
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
      path: "/api/cost-anomaly",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // listCostAnomalyStatus is the READ-ONLY path (see lib/cost-anomaly.ts's
  // header comment) -- it never advances a namespace's EWMA baseline, so a
  // page view/API call can never race the poller's own
  // checkCostAnomalies() into skewing the statistic being observed.
  const result = await listCostAnomalyStatus(PLATFORM_NAMESPACES);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/cost-anomaly",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ namespaces: PLATFORM_NAMESPACES, statuses: result.data });
}

export async function PUT(request: NextRequest) {
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
      method: "PUT",
      path: "/api/cost-anomaly",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const deviationThresholdPct =
    typeof body?.deviationThresholdPct === "number" ? body.deviationThresholdPct : NaN;

  if (!PLATFORM_NAMESPACES.includes(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!Number.isFinite(deviationThresholdPct) || deviationThresholdPct <= 0) {
    return NextResponse.json(
      { error: "deviationThresholdPct must be a positive number" },
      { status: 400 },
    );
  }

  const result = await setAnomalyThreshold(namespace, deviationThresholdPct, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: "/api/cost-anomaly",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ thresholds: result.data });
}
