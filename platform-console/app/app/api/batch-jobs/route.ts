import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  ALLOWED_BATCH_COMMANDS,
  collectBatchResults,
  createBatchJob,
  deleteBatchJob,
  getBatchJob,
  isBatchableNamespace,
  isValidBatchJobName,
  isValidBatchSize,
  listBatchJobPods,
  listBatchJobs,
  resolveBatchCommand,
} from "@/lib/batch-jobs";

// Node.js runtime (default for route handlers) -- lib/k8s.ts's k8sRequest,
// which lib/batch-jobs.ts reuses, reads the ServiceAccount token/CA from
// disk, same constraint as /api/scheduled-jobs.

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
  const name = request.nextUrl.searchParams.get("name") ?? "";
  if (!namespace) {
    return NextResponse.json({ error: "namespace query param is required" }, { status: 400 });
  }
  if (!isBatchableNamespace(namespace)) {
    return NextResponse.json(
      { error: `namespace must be one of the platform's own namespaces: ${namespace}` },
      { status: 400 },
    );
  }

  // Detail view: namespace + name -> job status, real live per-index Pod
  // status (for the parallelism proof), and the aggregated real results
  // collected so far.
  if (name) {
    const [jobResult, podsResult] = await Promise.all([
      getBatchJob(namespace, name),
      listBatchJobPods(namespace, name),
    ]);

    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/batch-jobs",
      status: jobResult.ok && podsResult.ok ? 200 : 502,
      requestId,
    });

    if (!jobResult.ok) return NextResponse.json({ error: jobResult.error }, { status: 502 });
    if (!podsResult.ok) return NextResponse.json({ error: podsResult.error }, { status: 502 });
    if (!jobResult.data) return NextResponse.json({ error: "batch job not found" }, { status: 404 });

    const resultsResult = await collectBatchResults(namespace, name, jobResult.data.completions);
    if (!resultsResult.ok) return NextResponse.json({ error: resultsResult.error }, { status: 502 });

    return NextResponse.json({
      job: jobResult.data,
      pods: podsResult.data,
      results: resultsResult.data,
    });
  }

  const result = await listBatchJobs(namespace);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/batch-jobs",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
  return NextResponse.json({ jobs: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Same member+ boundary as /api/scheduled-jobs POST: launching a real
  // parallel workload is infrastructure self-service.
  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/batch-jobs",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const namespace = typeof body?.namespace === "string" ? body.namespace.trim() : "";
  const name = typeof body?.name === "string" ? body.name.trim() : "";
  const size = typeof body?.size === "number" ? body.size : Number(body?.size);
  const commandId = typeof body?.commandId === "string" ? body.commandId.trim() : "";

  if (!isBatchableNamespace(namespace)) {
    return NextResponse.json(
      { error: "namespace must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }
  if (!isValidBatchJobName(name)) {
    return NextResponse.json(
      { error: "name must be a valid RFC 1123 label (lowercase alphanumeric and '-', max 40 chars)" },
      { status: 400 },
    );
  }
  if (!isValidBatchSize(size)) {
    return NextResponse.json(
      { error: "size (parallelism == completions) must be an integer between 2 and 10" },
      { status: 400 },
    );
  }
  // Real security boundary: commandId resolved against the fixed,
  // server-side allowlist -- anything else rejected before any k8s API
  // call, same discipline as /api/scheduled-jobs.
  const command = resolveBatchCommand(commandId);
  if (!command) {
    return NextResponse.json(
      { error: `commandId must be one of: ${Object.keys(ALLOWED_BATCH_COMMANDS).join(", ")}` },
      { status: 400 },
    );
  }

  const result = await createBatchJob({ namespace, name, size, commandId: command.id });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/batch-jobs",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
  return NextResponse.json({ job: result.data }, { status: 201 });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/batch-jobs",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const namespace = request.nextUrl.searchParams.get("namespace") ?? "";
  const name = request.nextUrl.searchParams.get("name") ?? "";
  if (!isBatchableNamespace(namespace) || !name) {
    return NextResponse.json(
      { error: "namespace (one of the platform's own namespaces) and name query params are required" },
      { status: 400 },
    );
  }

  const result = await deleteBatchJob(namespace, name);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/batch-jobs",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) return NextResponse.json({ error: result.error }, { status: 502 });
  return NextResponse.json({ ok: true });
}
