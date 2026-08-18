import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { createOrUpdateConfigMap, getConfigMap } from "@/lib/k8s";
import { requireRole } from "@/lib/authz";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do. Same pattern as app/api/secrets/route.ts.

const FLAGS_NAMESPACE = "platform-console";
const FLAGS_CONFIGMAP = "platform-feature-flags";

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

  const result = await getConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/feature-flags",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ flags: result.data?.data ?? {} });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Real app-level RBAC boundary: toggling a feature flag needs at least
  // "member". See lib/authz.ts.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/feature-flags",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const key = typeof body?.key === "string" ? body.key.trim() : "";
  const value = typeof body?.value === "string" ? body.value : "";

  if (!key) {
    return NextResponse.json({ error: "key is required" }, { status: 400 });
  }

  // A real RFC 7386 merge patch (lib/k8s.ts's createOrUpdateConfigMap) --
  // sending only the one changed key leaves every other flag already in
  // the ConfigMap untouched.
  const result = await createOrUpdateConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP, { [key]: value });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/feature-flags",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ flags: result.data.data });
}
