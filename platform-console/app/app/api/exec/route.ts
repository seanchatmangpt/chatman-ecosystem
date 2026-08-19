import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listPods } from "@/lib/k8s";
import {
  ALLOWED_EXEC_COMMANDS,
  execAllowedCommand,
  isExecNamespace,
} from "@/lib/container-exec";

// Runs on the Node.js runtime (default for route handlers) -- both
// lib/k8s.ts (ServiceAccount token/CA from disk) and lib/container-exec.ts
// (the `ws` WebSocket client) require it, same constraint every other
// Node-runtime route in this file tree already documents.
//
// Owner-only, both verbs: this is real command execution, the single most
// sensitive capability in the console, so unlike Logs (any authenticated
// session) it gets the same "owner" floor as Canary Deploy and Audit Log.
// GET populates the picker (namespace's real pods/containers + the fixed
// command allowlist); POST runs one allowlisted command and returns the
// full buffered stdout/stderr once the real k8s exec session closes -- a
// second, independent, non-streaming execution path alongside server.js's
// `/ws/exec` live relay, both ultimately calling the exact same
// lib/container-exec.ts#execAllowedCommand, never two different
// implementations of "which commands are allowed to run".

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
      path: "/api/exec",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const commands = Object.values(ALLOWED_EXEC_COMMANDS);

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  if (!namespace) {
    // No namespace yet -- just the fixed command allowlist, so the UI can
    // render the command picker before a namespace is chosen.
    return NextResponse.json({ pods: [], commands });
  }
  if (!isExecNamespace(namespace)) {
    return NextResponse.json(
      { error: "namespace must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  const result = await listPods(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/exec",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ pods: result.data, commands });
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
      path: "/api/exec",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const pod = typeof body?.pod === "string" ? body.pod.trim() : "";
  const container = typeof body?.container === "string" ? body.container.trim() : "";
  const commandId = typeof body?.commandId === "string" ? body.commandId.trim() : "";

  if (!isExecNamespace(namespace)) {
    return NextResponse.json(
      { error: "namespace must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }
  if (!pod || !container) {
    return NextResponse.json({ error: "pod and container are required" }, { status: 400 });
  }
  // The real security boundary: commandId is resolved against a fixed,
  // small, server-side allowlist (lib/container-exec.ts's
  // ALLOWED_EXEC_COMMANDS) INSIDE execAllowedCommand -- rejected there,
  // before any k8s WebSocket connection is ever opened, on anything
  // outside it. There is no free-text command field anywhere in this
  // route or the request body it accepts.
  const result = await execAllowedCommand(namespace, pod, container, commandId);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/exec",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ result: result.data });
}
