import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  ALLOWED_COMMANDS,
  createCronJob,
  deleteCronJob,
  isSchedulableNamespace,
  isValidCronSchedule,
  isValidJobName,
  listCronJobs,
  resolveCommand,
} from "@/lib/scheduled-jobs";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// (which lib/scheduled-jobs.ts's k8sRequest reuse depends on) reads the
// ServiceAccount token/CA from disk, which the edge runtime cannot do.

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

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  if (!namespace) {
    return NextResponse.json({ error: "namespace query param is required" }, { status: 400 });
  }
  if (!isSchedulableNamespace(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of the platform's own namespaces: ${namespace}` },
      { status: 400 },
    );
  }

  const result = await listCronJobs(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/scheduled-jobs",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ jobs: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Real app-level RBAC boundary: creating a CronJob is infrastructure
  // self-service, the same class of action as creating a Secret -- needs
  // at least "member". See lib/authz.ts.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/scheduled-jobs",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const name = typeof body?.name === "string" ? body.name.trim() : "";
  const schedule = typeof body?.schedule === "string" ? body.schedule.trim() : "";
  const commandId = typeof body?.commandId === "string" ? body.commandId.trim() : "";

  if (!isSchedulableNamespace(namespace)) {
    return NextResponse.json(
      { error: "namespace must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }
  if (!isValidJobName(name)) {
    return NextResponse.json(
      { error: "name must be a valid RFC 1123 label (lowercase alphanumeric and '-', max 52 chars)" },
      { status: 400 },
    );
  }
  if (!isValidCronSchedule(schedule)) {
    return NextResponse.json(
      { error: "schedule must be a valid 5-field cron expression (minute hour dom month dow)" },
      { status: 400 },
    );
  }
  // The real security boundary: commandId is resolved against a fixed,
  // small, server-side allowlist (lib/scheduled-jobs.ts's
  // ALLOWED_COMMANDS) -- anything else is rejected right here, before any
  // k8s API call, and no raw command text is ever accepted from the
  // request body at all (there is no such field).
  const command = resolveCommand(commandId);
  if (!command) {
    return NextResponse.json(
      {
        error: `commandId must be one of: ${Object.keys(ALLOWED_COMMANDS).join(", ")}`,
      },
      { status: 400 },
    );
  }

  const result = await createCronJob({ namespace, name, schedule, commandId: command.id });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/scheduled-jobs",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ job: result.data }, { status: 201 });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Same member+ boundary as POST above.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/scheduled-jobs",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  const name = request.nextUrl.searchParams.get("name") ?? "";
  if (!isSchedulableNamespace(namespace) || !name) {
    return NextResponse.json(
      { error: "namespace (one of the platform's own namespaces) and name query params are required" },
      { status: 400 },
    );
  }

  const result = await deleteCronJob(namespace, name);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/scheduled-jobs",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
