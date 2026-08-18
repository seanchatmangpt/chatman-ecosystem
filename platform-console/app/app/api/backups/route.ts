import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-log";
import { createBackupJob, listJobs } from "@/lib/k8s";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Deliberately hardcoded to the one real backup target on this cluster
// (demo-db-postgres-0 in supabase-demo) rather than accepting an arbitrary
// namespace/pod from the request body -- k8s/paas-rbac.yaml's
// platform-console-backups Role only grants batch/jobs and
// persistentvolumeclaims verbs in supabase-demo, so any other target
// would fail with a real 403 from the API server anyway; naming it here
// makes that scope explicit rather than discovered by trial and error.

const BACKUP_NAMESPACE = "supabase-demo";
const BACKUP_DB_POD = "demo-db-postgres-0";

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

  const result = await listJobs(BACKUP_NAMESPACE, "app=platform-backups");

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/backups",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  // Newest first -- the list a human wants when checking "did the last
  // backup succeed" is the one at the top.
  const jobs = [...result.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return NextResponse.json({ jobs, namespace: BACKUP_NAMESPACE, dbPodName: BACKUP_DB_POD });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const result = await createBackupJob(BACKUP_NAMESPACE, BACKUP_DB_POD);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/backups",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ job: result.data }, { status: 201 });
}
