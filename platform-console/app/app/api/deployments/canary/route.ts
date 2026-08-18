import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { getCanaryState, promoteCanary, rollbackCanary, setCanaryWeights } from "@/lib/canary";

// Backs the owner-only /deployments/canary page (app/deployments/canary/
// page.tsx). Both GET and POST here are owner-gated -- not just the
// page's own UI check -- so the real enforcement boundary is this route:
// shifting production traffic (and, on promote/rollback, deleting a real
// Deployment) is a genuinely consequential action, same reasoning
// app/api/org/roles/route.ts already documents for role changes. Runs on
// the Node.js runtime (default for route handlers), same as every other
// /api/* route that calls into lib/k8s.ts.

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
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/deployments/canary",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getCanaryState();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/deployments/canary",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Shifting production traffic (and, on promote/rollback, deleting a
  // real Deployment) is owner-gated -- same requireRole boundary as
  // /api/org/roles's own role-change action.
  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/deployments/canary",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const action = typeof body?.action === "string" ? body.action : "";

  let result;
  if (action === "set-weight") {
    const stableWeight = Number(body?.stableWeight);
    const canaryWeight = Number(body?.canaryWeight);
    result = await setCanaryWeights(stableWeight, canaryWeight).then(async (r) =>
      r.ok ? getCanaryState() : r,
    );
  } else if (action === "promote") {
    result = await promoteCanary();
  } else if (action === "rollback") {
    result = await rollbackCanary();
  } else {
    return NextResponse.json(
      { error: "action must be one of: set-weight, promote, rollback" },
      { status: 400 },
    );
  }

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/deployments/canary",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
