import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listCustomDomains, registerCustomDomain, unbindCustomDomain } from "@/lib/custom-domains";

// Backs the owner-only /custom-domains page. Every method here is
// owner-gated server-side, not just the page's own rendering check --
// binding a new PUBLIC hostname to a real backend Service, with a real
// generated TLS cert, is exactly the kind of consequential action
// /api/deployments/canary and /api/org/roles already hold to the same
// "owner" floor. Runs on the Node.js runtime (default for route
// handlers) -- lib/custom-domains.ts shells out to a real openssl
// subprocess and reads the ServiceAccount token from disk via
// lib/k8s.ts, neither of which the edge runtime can do.

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
      path: "/api/custom-domains",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listCustomDomains();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/custom-domains",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ bindings: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Registering a new public hostname -- a real generated TLS cert plus a
  // real Istio Gateway/VirtualService that starts routing live traffic --
  // is owner-gated, same requireRole boundary as canary traffic-shifting.
  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/custom-domains",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const hostname = typeof body?.hostname === "string" ? body.hostname.trim().toLowerCase() : "";
  const serviceName = typeof body?.serviceName === "string" ? body.serviceName.trim() : "";
  const serviceNamespace =
    typeof body?.serviceNamespace === "string" ? body.serviceNamespace.trim() : "";
  const servicePort = Number(body?.servicePort);

  if (!hostname || !serviceName || !serviceNamespace || !Number.isInteger(servicePort)) {
    return NextResponse.json(
      { error: "hostname, serviceName, serviceNamespace, and servicePort are required" },
      { status: 400 },
    );
  }

  const result = await registerCustomDomain(hostname, { serviceName, serviceNamespace, servicePort });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/custom-domains",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ binding: result.data }, { status: 201 });
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
      path: "/api/custom-domains",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const hostname = request.nextUrl.searchParams.get("hostname")?.trim().toLowerCase() ?? "";
  if (!hostname) {
    return NextResponse.json({ error: "hostname query param is required" }, { status: 400 });
  }

  const result = await unbindCustomDomain(hostname);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/custom-domains",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
