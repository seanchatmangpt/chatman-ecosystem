import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { deleteProjectWithDatabase, getProject } from "@/lib/k8s";
import { requireRole } from "@/lib/authz";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Single-project DELETE, the teardown counterpart to POST /api/projects.
// Added for the /quickstart flow's real cleanup step: create a project,
// verify it, back it up, then tear it down again -- the same
// create/read/delete lifecycle a real hyperscaler "getting started"
// script leaves you with. Owner-gated, same as project creation
// (k8s/paas-rbac.yaml grants the console ServiceAccount `delete` on
// `projects`/`singledatabases` for exactly this route).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { name } = await params;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/projects/${name}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/projects/${name}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const result = await deleteProjectWithDatabase(projectResult.data);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/projects/${name}`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ deleted: name });
}
