import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { getProject } from "@/lib/k8s";
import {
  getQueueConnectionInfo,
  getQueueStatus,
  provisionProjectQueue,
  queueResourceName,
  teardownProjectQueue,
} from "@/lib/queue";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Per-project Managed Queue (NATS/JetStream) route -- mirrors
// app/api/projects/[name]/cache/route.ts exactly: GET is read-only
// (status; the real password is only ever included when `?reveal=1` is
// passed, gated member+), POST provisions, DELETE tears down.
// Provision/teardown are owner-only (same app-level RBAC boundary as the
// cache route -- creating/destroying real infrastructure), viewing
// status/connection info is member+ (same rung as the cache route).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const { name } = await params;

  const access = await requireRole(session, "member");
  if (!access.ok) {
    return access.response!;
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const statusResult = await getQueueStatus(projectResult.data);
  if (!statusResult.ok) {
    return NextResponse.json({ error: statusResult.error }, { status: 502 });
  }

  const reveal = request.nextUrl.searchParams.get("reveal") === "1";
  if (!reveal || !statusResult.data.provisioned) {
    return NextResponse.json({ status: statusResult.data, connection: null });
  }

  const connResult = await getQueueConnectionInfo(projectResult.data);
  if (!connResult.ok) {
    return NextResponse.json({ error: connResult.error }, { status: 502 });
  }
  return NextResponse.json({ status: statusResult.data, connection: connResult.data });
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
  const { name } = await params;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/queue`,
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
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const result = await provisionProjectQueue(projectResult.data);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/queue`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ status: result.data }, { status: 201 });
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
      path: `/api/projects/${name}/queue`,
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
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const result = await teardownProjectQueue(projectResult.data);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/projects/${name}/queue`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ deleted: queueResourceName(name) });
}
