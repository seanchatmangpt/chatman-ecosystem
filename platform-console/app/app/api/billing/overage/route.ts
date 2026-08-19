import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  billNamespaceOverage,
  estimateAllNamespaceOverages,
  OVERAGE_PLATFORM_NAMESPACES,
} from "@/lib/overage-billing";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and lib/stripe-billing.ts both need Node's fs/https, which the edge
// runtime cannot provide.
//
// GET: pure computation, real Prometheus usage x real TIER_RESOURCE_QUOTAS
// baseline, no Stripe write -- readable by any authenticated session (the
// same "estimate" visibility every other /billing, /cost page already
// gives every session, no owner gate needed to look at a number).
//
// POST: owner-only (this creates a real Stripe InvoiceItem, i.e. a real
// financial action against a real Stripe test-mode/live customer -- the
// same class of action app/api/quota-enforcement/route.ts and
// app/api/plan-state/route.ts already gate to "owner").

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

  const { estimates, errors } = await estimateAllNamespaceOverages(OVERAGE_PLATFORM_NAMESPACES);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/billing/overage",
    status: 200,
    requestId,
  });

  return NextResponse.json({ namespaces: OVERAGE_PLATFORM_NAMESPACES, estimates, errors });
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
      path: "/api/billing/overage",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  if (!OVERAGE_PLATFORM_NAMESPACES.includes(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of: ${OVERAGE_PLATFORM_NAMESPACES.join(", ")}` },
      { status: 400 },
    );
  }

  const result = await billNamespaceOverage(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/billing/overage",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
