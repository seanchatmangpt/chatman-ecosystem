import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import { listProjects } from "@/lib/k8s";
import {
  listBackupRecords,
  runOrgBackup,
  syncBackupRecordStatus,
  cleanupExpiredBackups,
  RETENTION_DEFAULT_DAYS,
} from "@/lib/backup-retention";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real backup HISTORY endpoint -- compliance evidence for a 7yr
// financial-record / HIPAA retention requirement is exactly this: a
// provable list of "which backup, taken when, how large, expires when,
// current status" a customer or auditor can point to. See
// lib/backup-retention.ts for the storage/status model this reads.
//
// GET: any authenticated member of THIS org (viewer and up) -- reading
// backup history is not itself a privileged action, same posture GET
// .../sla already takes. Every returned record's status is
// reconciled against the real, live k8s Job it names
// (syncBackupRecordStatus) before being returned, so "completed" here
// always reflects a real observed Job completion, never a stale guess --
// and any record whose retainUntil has already passed is swept by
// cleanupExpiredBackups (real Job delete + ConfigMap row removal) before
// the list is built, so an expired backup is never shown as still
// available to restore from.
//
// POST: owner of THIS org -- triggers a real, on-demand `pg_dump` Job
// against one of this org's real Projects (runOrgBackup, reusing the
// same createBackupJob primitive app/api/projects/[name]/backups/
// route.ts already exposes per-project) and records a BackupRecord whose
// retainUntil is computed from this org's CURRENT effective retention
// policy. `projectName` must name a real Project inside this org's own
// namespace -- never an arbitrary caller-supplied namespace/project
// pair, same cross-tenant guard app/api/projects/[name]/backups/route.ts
// already enforces for restores.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/orgs/${id}/backups`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  // Enforce the retention window before listing: real, tiered cleanup,
  // not just a read-time filter -- an expired record's underlying Job is
  // actually deleted here, not merely hidden from this response.
  const cleanupResult = await cleanupExpiredBackups(id);
  if (!cleanupResult.ok) {
    return NextResponse.json({ error: cleanupResult.error }, { status: 502 });
  }

  const [recordsResult, tierResult] = await Promise.all([
    listBackupRecords(id),
    getOrgProjectTier(org.namespace),
  ]);

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/orgs/${id}/backups`,
    status: recordsResult.ok && tierResult.ok ? 200 : 502,
    requestId,
  });

  if (!recordsResult.ok) {
    return NextResponse.json({ error: recordsResult.error }, { status: 502 });
  }
  if (!tierResult.ok) {
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }

  // Real status reconciliation against each record's own live k8s Job
  // before returning -- sequential, not Promise.all, so one slow/failed
  // Job lookup never risks overwhelming the k8s API with a burst for an
  // org with a long backup history.
  const records = [];
  for (const record of recordsResult.data) {
    const synced = await syncBackupRecordStatus(record);
    records.push(synced.ok ? synced.data : record);
  }

  const now = Date.now();
  const withAge = records.map((r) => ({
    ...r,
    ageDays: Math.floor((now - Date.parse(r.takenAt)) / (24 * 60 * 60 * 1000)),
    daysUntilExpiry: Math.ceil((Date.parse(r.retainUntil) - now) / (24 * 60 * 60 * 1000)),
  }));

  return NextResponse.json({
    orgId: id,
    tier: tierResult.data,
    defaultRetentionDays: RETENTION_DEFAULT_DAYS[tierResult.data],
    backups: withAge,
    cleanedUp: cleanupResult.data,
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const access = await requireRoleIn(session, org.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId: id,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/orgs/${id}/backups`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const projectName = typeof body?.projectName === "string" ? body.projectName.trim() : "";
  if (!projectName) {
    return NextResponse.json({ error: "projectName is required" }, { status: 400 });
  }

  // Cross-tenant guard: the named Project must actually belong to THIS
  // org's own namespace before a backup Job is triggered against it --
  // otherwise an owner of org A could name a Project in org B's
  // namespace and trigger a backup Job there.
  const projectsResult = await listProjects();
  if (!projectsResult.ok) {
    return NextResponse.json({ error: projectsResult.error }, { status: 502 });
  }
  const belongsToOrg = projectsResult.data.some(
    (p) => p.name === projectName && p.namespace === org.namespace,
  );
  if (!belongsToOrg) {
    return NextResponse.json(
      { error: `project '${projectName}' does not belong to org '${id}'s namespace -- refusing` },
      { status: 403 },
    );
  }

  const tierResult = await getOrgProjectTier(org.namespace);
  if (!tierResult.ok) {
    return NextResponse.json({ error: tierResult.error }, { status: 502 });
  }

  const result = await runOrgBackup({
    orgId: id,
    namespace: org.namespace,
    projectName,
    tier: tierResult.data,
  });

  writeAuditLogEntry({
    orgId: id,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/orgs/${id}/backups`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ backup: result.data }, { status: 201 });
}
