import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { getProject, listNamespaceServices } from "@/lib/k8s";
import { invokeEdgeFunction } from "@/lib/functions-api";
import { requireRole } from "@/lib/authz";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Real invoke, not a client-side simulation: resolves the project's real
// functions Service (same lookup app/projects/[name]/functions/page.tsx
// already does), then does a real POST to that Service's real port via
// lib/functions-api.ts. Response status/body returned here are exactly
// what the edge-functions pod sent back -- never fabricated, never
// short-circuited on a guessed "success".

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Real app-level RBAC boundary: invoking a function runs real code
  // against a real project -- same "member" floor app/api/secrets/route.ts
  // uses for app-config writes, not viewer-readable.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/projects/[name]/functions/invoke",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const { name } = await params;
  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const functionSlug = typeof body?.functionSlug === "string" ? body.functionSlug.trim() : "";
  const payload = body?.payload ?? {};

  if (!functionSlug) {
    return NextResponse.json({ error: "functionSlug is required" }, { status: 400 });
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }
  const project = projectResult.data;

  const servicesResult = await listNamespaceServices(project.namespace);
  if (!servicesResult.ok) {
    return NextResponse.json({ error: servicesResult.error }, { status: 502 });
  }
  const functionsService = servicesResult.data.find(
    (s) =>
      s.labels["app.kubernetes.io/component"] === "functions" &&
      s.labels["app.kubernetes.io/instance"] === project.name,
  );
  if (!functionsService || !functionsService.ports[0]) {
    return NextResponse.json(
      { error: `no functions Service found in namespace ${project.namespace}` },
      { status: 404 },
    );
  }

  const result = await invokeEdgeFunction(
    functionsService.dns,
    functionsService.ports[0].port,
    functionSlug,
    payload,
  );

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/functions/invoke (${functionSlug})`,
    status: result.ok ? result.status : 502,
    requestId,
  });

  if (!result.ok) {
    if (result.notConfigured) {
      return NextResponse.json(
        { error: "not configured: SUPABASE_SERVICE_ROLE_KEY is not set for this console" },
        { status: 501 },
      );
    }
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  return NextResponse.json({
    functionSlug,
    status: result.status,
    body: result.body,
    durationMs: result.durationMs,
  });
}
