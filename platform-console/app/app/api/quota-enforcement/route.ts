import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  deleteQuotaEnforcementConfig,
  listQuotaEnforcementStatus,
  resetQuotaEnforcement,
  setQuotaEnforcementConfig,
} from "@/lib/quota-enforcement";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Owner-gated on every verb, same boundary as /api/budget-alerts: this
// route configures (and, via DELETE/reset, reverses) an action that
// suspends a real running workload -- strictly more consequential than a
// budget alert, which only ever sends a webhook.

// Same platform-namespace roster /api/budget-alerts and /api/billing
// already use -- the fixed set of namespaces this cluster actually
// meters, never an arbitrary client-supplied namespace string
// interpolated into a k8s API path.
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
      path: "/api/quota-enforcement",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // listQuotaEnforcementStatus is the READ-ONLY path (see
  // lib/quota-enforcement.ts's header comment) -- it never scales a
  // Deployment or writes the "enforced" dedup marker, so a page view can
  // never race the poller's own checkQuotaEnforcement() into a duplicate
  // enforcement action.
  const result = await listQuotaEnforcementStatus();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/quota-enforcement",
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
      path: "/api/quota-enforcement",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const thresholdPercent = typeof body?.thresholdPercent === "number" ? body.thresholdPercent : NaN;
  const targetDeployment =
    typeof body?.targetDeployment === "string" ? body.targetDeployment.trim() : "";

  if (!PLATFORM_NAMESPACES.includes(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of: ${PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }
  if (!Number.isFinite(thresholdPercent) || thresholdPercent <= 0) {
    return NextResponse.json({ error: "thresholdPercent must be a positive number" }, { status: 400 });
  }
  if (!/^[a-z0-9]([-a-z0-9]{0,61}[a-z0-9])?$/.test(targetDeployment)) {
    return NextResponse.json(
      { error: "targetDeployment must be a valid RFC 1123 label (lowercase alphanumeric and '-')" },
      { status: 400 },
    );
  }

  const result = await setQuotaEnforcementConfig(namespace, thresholdPercent, targetDeployment, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/quota-enforcement",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ configs: result.data });
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
      path: "/api/quota-enforcement",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  const reset = request.nextUrl.searchParams.get("reset") === "true";
  if (!namespace) {
    return NextResponse.json({ error: "namespace query param is required" }, { status: 400 });
  }

  // `?reset=true` performs the deliberate human undo (scale the target
  // Deployment back to 1, clear the enforced marker + namespace
  // annotations) -- see lib/quota-enforcement.ts's resetQuotaEnforcement
  // for why this is never automatic. Without it, DELETE only removes the
  // threshold config itself (stops future checks), matching
  // /api/budget-alerts's DELETE semantics.
  const result = reset
    ? await resetQuotaEnforcement(namespace)
    : await deleteQuotaEnforcementConfig(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/quota-enforcement",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true, data: result.data });
}
