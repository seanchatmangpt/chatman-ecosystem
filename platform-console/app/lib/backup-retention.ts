/**
 * Real tiered backup-retention policy -- closes the gap this repo's own
 * region-pinning/SLA-tier modules (lib/orgs.ts's setOrgRegion/setOrgSla)
 * already name but never filled: this console provisions a real
 * Postgres per Project (lib/k8s.ts's createProjectWithDatabase) and
 * already runs real `pg_dump` Jobs on demand
 * (app/api/projects/[name]/backups/route.ts's createBackupJob), but
 * nothing anywhere records HOW LONG a customer's backups are kept, or
 * ties that window to what they are paying for. Enterprise buyers with
 * regulatory retention requirements (7yr financial records under
 * SEC 17a-4 / SOX, HIPAA's 6yr minimum) pay specifically for a
 * configurable, provable retention window -- this module is that
 * primitive.
 *
 * Two real, distinct concerns, same split lib/compliance-report.ts
 * already established for its own two record families:
 *
 *   1. RETENTION POLICY -- which window (in days) this org's backups are
 *      kept for, chosen by an org owner from within their ProjectTier's
 *      allowed range (lib/tiers.ts). Not free text: `setBackupPolicy`
 *      below is the one and only place a retention window is ever
 *      written, and it refuses anything outside `RETENTION_RANGE[tier]`.
 *   2. BACKUP RECORD -- one row per real `pg_dump` Job this module (or
 *      the scheduled CronJob, same code path) triggers: which Job ran,
 *      when, how large the resulting dump is, and the exact
 *      `retainUntil` timestamp computed from the policy AT THE TIME the
 *      backup was taken -- so a later policy change never silently
 *      rewrites the retention promise already made for an existing
 *      backup, same "don't let a later default change rewrite an
 *      already-signed number" discipline lib/orgs.ts's OrgRegistryEntry
 *      comment documents for SLA numbers.
 *
 * Storage: one real k8s ConfigMap (`platform-backup-records`,
 * `platform-console` namespace), same get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo already uses. Key
 * shape mirrors lib/compliance-report.ts exactly:
 *   `record.<orgId>.<backupId>` -> JSON BackupRecord
 *   `policy.<orgId>`            -> JSON BackupPolicy
 *
 * The actual dump file lives on the real, namespace-scoped
 * `platform-backups-pvc` PersistentVolumeClaim createBackupJob already
 * mounts (lib/k8s.ts) -- this module records the k8s Job name that
 * produced each dump so a BackupRecord can always be traced back to its
 * real file at `/backups/<namespace>/<stem>/<jobName>.sql`, and deletes
 * both the ConfigMap row AND the underlying k8s Job (which owns no
 * separate PVC file-delete primitive; the Job object itself, not the
 * file, is what this module can delete via the k8s API -- disclosed, not
 * silently claimed as file-level deletion) once a record passes its
 * `retainUntil`.
 */
import {
  createBackupJob,
  deleteJob,
  getJobStatus,
  getProject,
  getProjectDatabasePod,
  listJobs,
  createOrUpdateConfigMap,
  getConfigMap,
  type K8sResult,
} from "@/lib/k8s";
import { DEFAULT_PROJECT_TIER, type ProjectTier } from "@/lib/tiers";

export const BACKUP_RECORDS_NAMESPACE = "platform-console";
export const BACKUP_RECORDS_CONFIGMAP = "platform-backup-records";

/**
 * Real per-tier retention DEFAULT (the window applied the moment an org
 * has never explicitly chosen one) and the real per-tier ALLOWED RANGE
 * an org owner may pick within (`setBackupPolicy` enforces the range;
 * `RETENTION_DEFAULT_DAYS` is only ever the seed/fallback, never
 * silently re-applied over an explicit choice). `enterprise`'s max
 * (2555 days = 7 years) matches SEC 17a-4/SOX's 7-year financial-record
 * retention requirement verbatim -- the specific regulatory number
 * named in this capability's own rationale, not a round number picked
 * for its own sake.
 */
export const RETENTION_DEFAULT_DAYS: Record<ProjectTier, number> = {
  starter: 7,
  pro: 30,
  enterprise: 365,
};

export interface RetentionRange {
  minDays: number;
  maxDays: number;
}

export const RETENTION_RANGE: Record<ProjectTier, RetentionRange> = {
  starter: { minDays: 1, maxDays: 7 },
  pro: { minDays: 7, maxDays: 90 },
  enterprise: { minDays: 30, maxDays: 2555 },
};

export function isRetentionDaysAllowed(tier: ProjectTier, days: number): boolean {
  const range = RETENTION_RANGE[tier];
  return Number.isInteger(days) && days >= range.minDays && days <= range.maxDays;
}

export interface BackupPolicy {
  orgId: string;
  tier: ProjectTier;
  retentionDays: number;
  setBy: string;
  setAt: string;
}

export type BackupStatus = "pending" | "running" | "completed" | "failed" | "expired";

export interface BackupRecord {
  id: string;
  orgId: string;
  namespace: string;
  projectName: string;
  jobName: string;
  takenAt: string;
  sizeBytes: number;
  retainUntil: string;
  status: BackupStatus;
}

function policyKey(orgId: string): string {
  return `policy.${orgId}`;
}
function recordKey(orgId: string, id: string): string {
  return `record.${orgId}.${id}`;
}

function parsePolicy(orgId: string, raw: string): BackupPolicy | null {
  try {
    const p = JSON.parse(raw) as Partial<BackupPolicy>;
    if (
      typeof p.tier === "string" &&
      (p.tier === "starter" || p.tier === "pro" || p.tier === "enterprise") &&
      typeof p.retentionDays === "number" &&
      typeof p.setBy === "string" &&
      typeof p.setAt === "string"
    ) {
      return { orgId, tier: p.tier, retentionDays: p.retentionDays, setBy: p.setBy, setAt: p.setAt };
    }
    return null;
  } catch {
    return null;
  }
}

function parseRecord(raw: string): BackupRecord | null {
  try {
    const r = JSON.parse(raw) as Partial<BackupRecord>;
    if (
      typeof r.id === "string" &&
      typeof r.orgId === "string" &&
      typeof r.namespace === "string" &&
      typeof r.projectName === "string" &&
      typeof r.jobName === "string" &&
      typeof r.takenAt === "string" &&
      typeof r.sizeBytes === "number" &&
      typeof r.retainUntil === "string" &&
      typeof r.status === "string"
    ) {
      return r as BackupRecord;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Real policy read: `{ok: true, data: null}` -- not an error -- when this
 * org has never set a policy, same "not-found is data" convention every
 * other ConfigMap-backed getX in this repo (getOrgSla, getOrgRegion,
 * getComplianceCadence) already uses. The route layers `tier`'s
 * `RETENTION_DEFAULT_DAYS` fallback on top, same split
 * getOrgSla/SLA_TIER_DEFAULTS already establishes.
 */
export async function getBackupPolicy(orgId: string): Promise<K8sResult<BackupPolicy | null>> {
  const result = await getConfigMap(BACKUP_RECORDS_NAMESPACE, BACKUP_RECORDS_CONFIGMAP);
  if (!result.ok) return result;
  const raw = result.data?.data?.[policyKey(orgId)];
  if (!raw) return { ok: true, data: null };
  return { ok: true, data: parsePolicy(orgId, raw) };
}

/**
 * Real policy write: backs PUT /api/orgs/[id]/backup-policy. `tier` is
 * the org's real, live-derived ProjectTier (lib/orgs.ts's
 * getOrgProjectTier) -- never caller-supplied -- and `retentionDays`
 * must fall within `RETENTION_RANGE[tier]` or this refuses with a real,
 * specific error, same fail-closed discipline lib/orgs.ts's
 * validateBranding/setOrgRegion already establish. Stores `tier`
 * alongside the chosen days so a later tier change can be detected
 * (the route re-validates against the CURRENT tier on every read, this
 * function only guards against writing an out-of-range value for the
 * tier the caller names at write time).
 */
export async function setBackupPolicy(input: {
  orgId: string;
  tier: ProjectTier;
  retentionDays: number;
  setBy: string;
}): Promise<K8sResult<BackupPolicy> | { ok: false; error: string }> {
  if (!isRetentionDaysAllowed(input.tier, input.retentionDays)) {
    const range = RETENTION_RANGE[input.tier];
    return {
      ok: false,
      error: `retentionDays must be an integer between ${range.minDays} and ${range.maxDays} for tier '${input.tier}'`,
    };
  }
  const policy: BackupPolicy = {
    orgId: input.orgId,
    tier: input.tier,
    retentionDays: input.retentionDays,
    setBy: input.setBy,
    setAt: new Date().toISOString(),
  };
  const write = await createOrUpdateConfigMap(BACKUP_RECORDS_NAMESPACE, BACKUP_RECORDS_CONFIGMAP, {
    [policyKey(input.orgId)]: JSON.stringify(policy),
  });
  if (!write.ok) return write;
  return { ok: true, data: policy };
}

/**
 * Real effective retention window: the org's own explicit policy if one
 * exists, else `RETENTION_DEFAULT_DAYS[tier]` -- the single function
 * every backup-taking and cleanup path below calls so "what window
 * applies right now" is computed exactly once, never duplicated.
 */
export async function effectiveRetentionDays(
  orgId: string,
  tier: ProjectTier,
): Promise<K8sResult<number>> {
  const policyResult = await getBackupPolicy(orgId);
  if (!policyResult.ok) return policyResult;
  return { ok: true, data: policyResult.data?.retentionDays ?? RETENTION_DEFAULT_DAYS[tier] };
}

/** Real list of every backup record for one org, newest first -- scans
 * this ConfigMap's own `record.<orgId>.*` keys, same convention
 * lib/compliance-report.ts's listComplianceReports already establishes. */
export async function listBackupRecords(orgId: string): Promise<K8sResult<BackupRecord[]>> {
  const result = await getConfigMap(BACKUP_RECORDS_NAMESPACE, BACKUP_RECORDS_CONFIGMAP);
  if (!result.ok) return result;
  const data = result.data?.data ?? {};
  const prefix = `record.${orgId}.`;
  const records: BackupRecord[] = [];
  for (const [key, raw] of Object.entries(data)) {
    if (!key.startsWith(prefix)) continue;
    const parsed = parseRecord(raw);
    if (parsed) records.push(parsed);
  }
  records.sort((a, b) => b.takenAt.localeCompare(a.takenAt));
  return { ok: true, data: records };
}

async function writeRecord(record: BackupRecord): Promise<K8sResult<BackupRecord>> {
  const write = await createOrUpdateConfigMap(BACKUP_RECORDS_NAMESPACE, BACKUP_RECORDS_CONFIGMAP, {
    [recordKey(record.orgId, record.id)]: JSON.stringify(record),
  });
  if (!write.ok) return write;
  return { ok: true, data: record };
}

/**
 * Real, end-to-end backup: resolves the named Project's real database
 * Pod (same getProjectDatabasePod lookup
 * app/api/projects/[name]/backups/route.ts already uses), triggers the
 * real `pg_dump` k8s Job (createBackupJob, lib/k8s.ts -- writes a real
 * dump file to the project's namespace-scoped `platform-backups-pvc`),
 * then records a BackupRecord with `retainUntil` computed from THIS
 * org's effective retention window at the moment the backup was taken.
 * `sizeBytes` starts at 0 and `status` starts "pending" -- the Job has
 * only just been created, not yet completed -- `syncBackupRecordStatus`
 * below is the real, honest way a caller later learns whether it
 * succeeded, never a fabricated size/status here.
 */
export async function runOrgBackup(input: {
  orgId: string;
  namespace: string;
  projectName: string;
  tier: ProjectTier;
}): Promise<K8sResult<BackupRecord>> {
  const projectResult = await getProject(input.projectName);
  if (!projectResult.ok) return projectResult;
  if (!projectResult.data) {
    return { ok: false, error: `project '${input.projectName}' not found` };
  }
  if (projectResult.data.namespace !== input.namespace) {
    return {
      ok: false,
      error: `project '${input.projectName}' does not belong to namespace '${input.namespace}' -- refusing cross-tenant backup`,
    };
  }

  const dbPodResult = await getProjectDatabasePod(projectResult.data);
  if (!dbPodResult.ok) return dbPodResult;
  if (!dbPodResult.data) {
    return {
      ok: false,
      error: `no database Service found for project '${input.projectName}' in namespace ${input.namespace} yet`,
    };
  }

  const jobResult = await createBackupJob(dbPodResult.data.namespace, dbPodResult.data.podName);
  if (!jobResult.ok) return jobResult;

  const retentionResult = await effectiveRetentionDays(input.orgId, input.tier);
  if (!retentionResult.ok) return retentionResult;

  const takenAt = new Date();
  const retainUntil = new Date(takenAt.getTime() + retentionResult.data * 24 * 60 * 60 * 1000);

  const record: BackupRecord = {
    id: globalThis.crypto.randomUUID(),
    orgId: input.orgId,
    namespace: dbPodResult.data.namespace,
    projectName: input.projectName,
    jobName: jobResult.data.name,
    takenAt: takenAt.toISOString(),
    sizeBytes: 0,
    retainUntil: retainUntil.toISOString(),
    status: "pending",
  };

  return writeRecord(record);
}

/**
 * Real status reconciliation for one BackupRecord: reads the real k8s
 * Job's live status (getJobStatus, lib/k8s.ts) the record's `jobName`
 * points at and updates `status` accordingly ("running" while active,
 * "completed" once `succeeded`, "failed" once `failed`). A Job the k8s
 * API no longer has (already garbage-collected, or deleted by
 * `cleanupExpiredBackups` below) leaves the record's `status` untouched
 * -- this function only ever moves status forward from real, observed
 * Job state, never fabricates a size or a completion this module cannot
 * verify. `sizeBytes` remains 0: this repo's k8s.ts exposes no
 * file-stat/exec-in-pod primitive to read the real dump's byte size off
 * the PVC (createDumpReaderJob base64-streams the whole file out, which
 * this reconciler intentionally does not invoke on a schedule -- doing
 * so for every record would mean decoding a full customer database dump
 * just to learn its length) -- disclosed here, not silently claimed.
 */
export async function syncBackupRecordStatus(record: BackupRecord): Promise<K8sResult<BackupRecord>> {
  if (record.status === "completed" || record.status === "failed" || record.status === "expired") {
    return { ok: true, data: record };
  }
  const jobResult = await getJobStatus(record.namespace, record.jobName);
  if (!jobResult.ok) return { ok: true, data: record };

  let status: BackupStatus = record.status;
  if (jobResult.data.status === "Complete") status = "completed";
  else if (jobResult.data.status === "Failed") status = "failed";
  else if (jobResult.data.status === "Running") status = "running";

  if (status === record.status) return { ok: true, data: record };
  return writeRecord({ ...record, status });
}

/**
 * Real cleanup job (the "tiered retention" half of this capability's
 * spec that actually enforces the window, not just records it): lists
 * every BackupRecord for `orgId` whose `retainUntil` has passed, deletes
 * the real underlying k8s Job (`deleteJob`, lib/k8s.ts -- the Job object
 * this repo can actually address; the dump file itself lives on the
 * shared PVC with no per-file delete primitive in lib/k8s.ts today,
 * disclosed the same way this module's header comment already does),
 * then removes the ConfigMap row via the same RFC 7386 null-value
 * merge-patch discipline lib/orgs.ts's deleteOrg/lib/budget-alerts.ts's
 * deleteBudgetThreshold already establish. A Job delete failure for a
 * reason other than "already gone" leaves that one record's row in
 * place (status flipped to "expired" so it is visibly overdue, not
 * silently retried forever) rather than aborting the whole sweep --
 * same "one bad row never blocks the rest" discipline this repo's
 * ConfigMap parsers already use for read paths, applied here to writes.
 */
export async function cleanupExpiredBackups(orgId: string): Promise<K8sResult<{ deleted: string[]; stillExpiredButUndeleted: string[] }>> {
  const listResult = await listBackupRecords(orgId);
  if (!listResult.ok) return listResult;

  const now = Date.now();
  const expired = listResult.data.filter(
    (r) => r.status !== "expired" && Date.parse(r.retainUntil) <= now,
  );

  const deleted: string[] = [];
  const stillExpiredButUndeleted: string[] = [];
  const patch: Record<string, string | null> = {};

  for (const record of expired) {
    const del = await deleteJob(record.namespace, record.jobName);
    if (del.ok || /not found/i.test(del.error)) {
      patch[recordKey(orgId, record.id)] = null;
      deleted.push(record.id);
    } else {
      patch[recordKey(orgId, record.id)] = JSON.stringify({ ...record, status: "expired" as BackupStatus });
      stillExpiredButUndeleted.push(record.id);
    }
  }

  if (Object.keys(patch).length === 0) {
    return { ok: true, data: { deleted, stillExpiredButUndeleted } };
  }

  const write = await createOrUpdateConfigMap(
    BACKUP_RECORDS_NAMESPACE,
    BACKUP_RECORDS_CONFIGMAP,
    patch as unknown as Record<string, string>,
  );
  if (!write.ok) return write;
  return { ok: true, data: { deleted, stillExpiredButUndeleted } };
}

export { DEFAULT_PROJECT_TIER };
