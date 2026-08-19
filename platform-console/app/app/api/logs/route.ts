import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getPodLogs, listPods } from "@/lib/k8s";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Two shapes, both GET, distinguished by whether `pod` is present:
//   GET /api/logs?namespace=X            -> list real pods in that namespace
//   GET /api/logs?namespace=X&pod=Y      -> real tail of that pod's log
// No namespace allowlist is hardcoded here -- k8s/paas-rbac.yaml scopes the
// console's ServiceAccount to exactly the namespaces it should read pods/
// pods-log from, so any namespace outside that grant gets a real 403 from
// the API server (surfaced below as a 502 with the real message), same
// fail-closed convention as every other route in this file tree.

const MAX_TAIL_LINES = 5000;

async function requireActor(request: NextRequest): Promise<string | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  return session?.sub ?? null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  if (!namespace) {
    return NextResponse.json({ error: "namespace query param is required" }, { status: 400 });
  }

  const pod = request.nextUrl.searchParams.get("pod");

  if (!pod) {
    const result = await listPods(namespace);

    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/logs",
      status: result.ok ? 200 : 502,
      requestId,
    });

    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    return NextResponse.json({ pods: result.data });
  }

  const container = request.nextUrl.searchParams.get("container") ?? undefined;
  const tailLinesParam = request.nextUrl.searchParams.get("tailLines");
  const parsedTailLines = tailLinesParam ? Number.parseInt(tailLinesParam, 10) : 200;
  const tailLines =
    Number.isFinite(parsedTailLines) && parsedTailLines > 0
      ? Math.min(parsedTailLines, MAX_TAIL_LINES)
      : 200;

  const result = await getPodLogs(namespace, pod, { tailLines, container });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/logs",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ logs: result.data, tailLines, container: container ?? null });
}
