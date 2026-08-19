import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  BUDGET_METRICS,
  deleteBudgetThreshold,
  listBudgetThresholds,
  listBudgetUsages,
  setBudgetThreshold,
  type BudgetMetric,
} from "@/lib/budget-alerts";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Owner-gated on every verb, same boundary as /api/webhooks: a budget
// threshold is a real financial-adjacent setting (it governs when this
// console fires a real webhook about namespace spend), even though no
// real payment method or processor is ever involved anywhere in this
// platform.

// Same platform-namespace roster /api/billing and app/billing/page.tsx
// already use -- the fixed set of namespaces this cluster actually meters,
// never an arbitrary client-supplied namespace string interpolated into a
// PromQL selector.
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
      path: "/api/budget-alerts",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // listBudgetUsages is the READ-ONLY path (see lib/budget-alerts.ts's
  // header comment) -- it never writes the "already alerted" dedup marker,
  // so a page view can never swallow a webhook delivery the poller's own
  // checkBudgets() was about to fire.
  const [thresholdsResult, usagesResult] = await Promise.all([
    listBudgetThresholds(),
    listBudgetUsages(),
  ]);

  const status = thresholdsResult.ok && usagesResult.ok ? 200 : 502;
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/budget-alerts",
    status,
    requestId,
  });

  if (!thresholdsResult.ok) {
    return NextResponse.json({ error: thresholdsResult.error }, { status: 502 });
  }
  if (!usagesResult.ok) {
    return NextResponse.json({ error: usagesResult.error }, { status: 502 });
  }
  return NextResponse.json({
    namespaces: PLATFORM_NAMESPACES,
    metrics: BUDGET_METRICS,
    thresholds: thresholdsResult.data,
    usages: usagesResult.data,
  });
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
      path: "/api/budget-alerts",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const metric = typeof body?.metric === "string" ? (body.metric as BudgetMetric) : ("" as BudgetMetric);
  const threshold = typeof body?.threshold === "number" ? body.threshold : NaN;

  if (!PLATFORM_NAMESPACES.includes(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!BUDGET_METRICS.includes(metric)) {
    return NextResponse.json(
      { error: `metric must be one of: ${BUDGET_METRICS.join(", ")}` },
      { status: 400 },
    );
  }
  if (!Number.isFinite(threshold) || threshold <= 0) {
    return NextResponse.json({ error: "threshold must be a positive number" }, { status: 400 });
  }

  const result = await setBudgetThreshold(namespace, metric, threshold, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/budget-alerts",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ thresholds: result.data });
}

export async function DELETE(request: NextRequest) {
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
      method: "DELETE",
      path: "/api/budget-alerts",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  if (!namespace) {
    return NextResponse.json({ error: "namespace query param is required" }, { status: 400 });
  }

  const result = await deleteBudgetThreshold(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/budget-alerts",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
