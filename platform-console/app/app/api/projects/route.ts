import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { createProjectWithDatabase, listProjects } from "@/lib/k8s";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.

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
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
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
  return NextResponse.json({ project: result.data }, { status: 201 });
}
