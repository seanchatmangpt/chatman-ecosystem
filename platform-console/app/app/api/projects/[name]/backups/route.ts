import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  createBackupJob,
  createRestoreJob,
  getBackupsPvc,
  getProject,
  getProjectDatabasePod,
  listJobs,
} from "@/lib/k8s";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Project-scoped (unlike the retired top-level /api/backups, which
// hardcoded BACKUP_NAMESPACE="supabase-demo"/BACKUP_DB_POD=
// "demo-db-postgres-0"): the target namespace + Postgres Pod are resolved
// live for whichever project's `[name]` route param this request names,
// via getProjectDatabasePod (lib/k8s.ts) -- the exact same
// component=database Service lookup app/projects/[name]/database/page.tsx
// already renders. No project name ever appears in this file as a
// literal.
//
// RBAC still real, still least-privilege (k8s/paas-rbac.yaml's
// platform-console-backups Role): it grants batch/jobs +
// persistentvolumeclaims only in the supabase-demo namespace, so a
// project whose namespace is anything else gets a real 403 straight from
// the API server here -- this route never fabricates success outside that
// scope, it just no longer hardcodes it as the only project that can be
// named.
//
// Cross-tenant isolation, the reason this route does NOT just call
// listJobs(namespace, "app=platform-backups") the way the old
// /api/backups did: multiple Projects can share one namespace (this
// console's own self-service form lets any namespace be reused for a
// second Project+SingleDatabase pair), so the label selector below adds
// `database=<stem>` -- the same per-database label createBackupJob/
// createRestoreJob already stamp onto every Job they create -- to keep
// one project's backup/restore inventory from leaking another project's
// Jobs just because they happen to live in the same namespace.

async function requireActor(request: NextRequest): Promise<string | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  return session?.sub ?? null;
}

const BACKUPS_PVC_NAME = "platform-backups-pvc";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const { name } = await params;
  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }
  const project = projectResult.data;

  const dbPodResult = await getProjectDatabasePod(project);
  if (!dbPodResult.ok) {
    return NextResponse.json({ error: dbPodResult.error }, { status: 502 });
  }
  if (!dbPodResult.data) {
    return NextResponse.json({
      jobs: [],
      restoreJobs: [],
      namespace: project.namespace,
      dbPodName: null,
      pvc: null,
      notConfigured: `no database Service found for project '${name}' in namespace ${project.namespace} yet`,
    });
  }
  const { namespace, podName, serviceName: stem } = dbPodResult.data;

  const [jobsResult, restoreJobsResult, pvcResult] = await Promise.all([
    listJobs(namespace, `app=platform-backups,database=${stem}`),
    listJobs(namespace, `app=platform-restores,database=${stem}`),
    getBackupsPvc(namespace, BACKUPS_PVC_NAME),
  ]);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/projects/${name}/backups`,
    status: jobsResult.ok && restoreJobsResult.ok ? 200 : 502,
    requestId,
  });

  if (!jobsResult.ok) {
    return NextResponse.json({ error: jobsResult.error }, { status: 502 });
  }
  if (!restoreJobsResult.ok) {
    return NextResponse.json({ error: restoreJobsResult.error }, { status: 502 });
  }
  const jobs = [...jobsResult.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const restoreJobs = [...restoreJobsResult.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return NextResponse.json({
    jobs,
    restoreJobs,
    namespace,
    dbPodName: podName,
    pvc: pvcResult.ok ? pvcResult.data : null,
    pvcError: pvcResult.ok ? null : pvcResult.error,
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const { name } = await params;
  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }
  const project = projectResult.data;

  const dbPodResult = await getProjectDatabasePod(project);
  if (!dbPodResult.ok) {
    return NextResponse.json({ error: dbPodResult.error }, { status: 502 });
  }
  if (!dbPodResult.data) {
    return NextResponse.json(
      { error: `no database Service found for project '${name}' in namespace ${project.namespace}` },
      { status: 404 },
    );
  }
  const { namespace, podName, serviceName: stem } = dbPodResult.data;

  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const action = typeof body?.action === "string" ? body.action : "backup";

  if (action === "restore") {
    const backupJobName = typeof body?.backupJobName === "string" ? body.backupJobName : "";
    const confirm = typeof body?.confirm === "string" ? body.confirm : "";
    if (!backupJobName) {
      return NextResponse.json({ error: "backupJobName is required" }, { status: 400 });
    }
    if (confirm !== backupJobName) {
      return NextResponse.json(
        { error: "confirmation text does not match the backup job name -- restore refused" },
        { status: 400 },
      );
    }

    // Cross-tenant guard: the named backup Job must actually belong to
    // THIS project's database (same `database=<stem>` label createBackupJob
    // stamped it with) before a restore into this project's Pod is allowed
    // -- otherwise a project sharing a namespace with another could restore
    // a stranger's backup job name into its own database just by knowing
    // (or guessing) that Job's name.
    const ownJobsResult = await listJobs(namespace, `app=platform-backups,database=${stem}`);
    if (!ownJobsResult.ok) {
      return NextResponse.json({ error: ownJobsResult.error }, { status: 502 });
    }
    if (!ownJobsResult.data.some((j) => j.name === backupJobName)) {
      return NextResponse.json(
        { error: `backup Job '${backupJobName}' does not belong to project '${name}'s database -- restore refused` },
        { status: 403 },
      );
    }

    const result = await createRestoreJob(namespace, backupJobName, podName);

    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/backups (restore)`,
      status: result.ok ? 201 : 502,
      requestId,
    });

    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    return NextResponse.json({ job: result.data }, { status: 201 });
  }

  const result = await createBackupJob(namespace, podName);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/backups`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ job: result.data }, { status: 201 });
}
