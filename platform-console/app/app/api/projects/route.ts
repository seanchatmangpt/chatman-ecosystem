import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { createProjectWithDatabase, listProjects } from "@/lib/k8s";
import { requireRole } from "@/lib/authz";
import { deliverWebhookEvent } from "@/lib/webhooks";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.

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

  const result = await listProjects();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/projects",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ projects: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Real app-level RBAC boundary: creating infrastructure (a Supabase
  // Project + its backing database) is owner-only, layered on top of --
  // not replacing -- the console ServiceAccount's own k8s RBAC. See
  // lib/authz.ts.
  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/projects",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const name = typeof body?.name === "string" ? body.name.trim() : "";
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const databaseRefName =
    typeof body?.databaseRefName === "string" && body.databaseRefName.trim()
      ? body.databaseRefName.trim()
      : `${name}-db`;
  const hostname =
    typeof body?.hostname === "string" && body.hostname.trim()
      ? body.hostname.trim()
      : `${name}.supabase.local`;
  const protocol = body?.protocol === "https" ? "https" : "http";
  const dbStorageSize =
    typeof body?.dbStorageSize === "string" && body.dbStorageSize.trim()
      ? body.dbStorageSize.trim()
      : "1Gi";

  if (!name || !namespace) {
    return NextResponse.json(
      { error: "name and namespace are required" },
      { status: 400 },
    );
  }

  const result = await createProjectWithDatabase({
    name,
    namespace,
    databaseRefName,
    hostname,
    protocol,
    dbStorageSize,
  });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/projects",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  // Real "project.created" Outbound Webhook trigger (lib/webhooks.ts):
  // fires straight off this real createProjectWithDatabase success --
  // never a separate/simulated event. Deliberately not awaited into the
  // response path (delivery has its own 5s-per-subscriber timeout and
  // never throws past deliverWebhookEvent) so a slow or dead subscriber
  // can never delay or fail the actual project-creation response; any
  // delivery outcome is logged by deliverWebhookEvent itself.
  void deliverWebhookEvent("project.created", {
    name: result.data.name,
    namespace: result.data.namespace,
    databaseRefName: result.data.databaseRefName,
    hostname: result.data.hostname,
    createdAt: result.data.createdAt,
  });

  return NextResponse.json({ project: result.data }, { status: 201 });
}
