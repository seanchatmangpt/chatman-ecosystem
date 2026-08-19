/**
 * Real multi-region DR failover runbook automation -- the concrete, narrowly
 * scoped control a Fortune 5 buyer's DR/BC audit always asks for by name:
 * "when your pinned region degrades, what ACTUALLY happens, and can you
 * show us the record of it." Region pinning (lib/orgs.ts's
 * getOrgRegion/setOrgRegion, backed by lib/k8s.ts's real live
 * `topology.kubernetes.io/region` node labels) already exists; this module
 * is the missing automation for the one failure mode that pinning alone
 * does not cover -- what happens when the pinned region itself degrades.
 *
 * A failover is composed entirely of REAL primitives this repo already
 * has, never a new subsystem:
 *   1. Precondition: an OPEN incident (lib/incidents.ts) whose own
 *      `componentId` or `rootCause` names `fromRegion`, scoped to this org
 *      (or platform-wide, since this shared cluster's components are not
 *      per-org today -- see incidents.ts's own header comment on
 *      orgComponentIds). No open incident referencing the source region ->
 *      refuses outright, so a failover can never be triggered casually or
 *      by mistake; this is the "can't fat-finger a DR drill into a real
 *      failover" control.
 *   2. Maker-checker: `dr.failover` is gated behind
 *      lib/approval-workflow.ts's existing two-person-integrity primitive,
 *      the same one org.delete/tier.downgrade/backup.retention.change
 *      already use -- a failover is exactly the "destructive, high-blast-
 *      radius" class of action that bar exists for (it re-points a live
 *      customer's data residency AND triggers a real destructive restore
 *      that overwrites the target's live table data, see
 *      lib/k8s.ts's createRestoreJob header comment).
 *   3. Re-pin: setOrgRegion(orgId, toRegion) -- the exact same write path
 *      /api/orgs/[id]/region's PUT already uses, so a failed-over org's
 *      region pin is indistinguishable from one a human pinned by hand
 *      (same enterprise-tier + live-node-region validation, enforced
 *      inside setOrgRegion itself, fail-closed even if this module's own
 *      pre-checks are ever bypassed).
 *   4. Restore: a real `batch/v1` Job via lib/k8s.ts's createRestoreJob,
 *      restoring the org's own database's latest COMPLETE backup Job
 *      (found live via listJobs, never a client-supplied/guessed Job
 *      name) into that SAME database Pod. This console's tenancy model is
 *      one namespace per org (lib/orgs.ts), not one namespace per
 *      (org, region) pair, so "restore into the target region's
 *      namespace" concretely means: restore into this org's own real
 *      namespace/Pod, now re-pinned to `toRegion` by step 3 -- the actual
 *      k8s scheduling of that Pod onto a `toRegion` node is a cluster-
 *      autoscaler/node-affinity concern this module does not reach into,
 *      same "we drive the k8s objects this platform owns, not the
 *      underlying node fleet" boundary lib/k8s.ts's own callers hold
 *      throughout.
 *   5. Structured audit chain: one writeAuditLogEntry (lib/audit-db.ts,
 *      the real sha256 hash-chained `platform_console.audit_log` table)
 *      per step -- start, each step's own success/failure, and a final
 *      completion/failure entry -- so a DR audit can walk the exact,
 *      tamper-evident sequence of what this runbook actually did, not a
 *      narrative reconstruction after the fact.
 *
 * Storage: this module owns no new k8s object or table of its own. Its
 * only durable state IS the sequence of audit_log rows plus the ordinary
 * side effects (the region pin, the restore Job) every other primitive it
 * calls already persists -- `getFailoverStatus` below re-derives
 * in-progress/complete/failed status live from those same real objects
 * rather than a separately-tracked "failover record" that could drift
 * from what actually happened.
 */
import { getOrg, setOrgRegion, type Org } from "@/lib/orgs";
import { listIncidents, type Incident } from "@/lib/incidents";
import {
  createRestoreJob,
  getProject,
  getProjectDatabasePod,
  listJobs,
  listProjects,
  type BackupJob,
  type K8sResult,
} from "@/lib/k8s";
import { writeAuditLogEntry, newRequestId } from "@/lib/audit-db";

export type DrFailoverOutcome<T> = { ok: true; data: T } | { ok: false; error: string };

/**
 * An incident is treated as "referencing" a region when its componentId or
 * human-annotated rootCause literally names it -- this shared platform has
 * no dedicated `incident.region` column (incidents.ts's own header comment
 * documents why: components are platform-wide, not per-org), so this is
 * the honest, real substring match over the two fields a human/reconciler
 * actually populates, never a fabricated stronger guarantee.
 */
function incidentReferencesRegion(incident: Incident, region: string): boolean {
  const needle = region.toLowerCase();
  return (
    incident.componentId.toLowerCase().includes(needle) ||
    (incident.rootCause ?? "").toLowerCase().includes(needle)
  );
}

/**
 * Precondition check backing step 1: is there a real, currently-OPEN
 * incident (status "open", i.e. reconcileIncidents has not yet observed a
 * resolved end for it) that references `fromRegion`, scoped to `orgId`
 * when annotated or unscoped (org_id IS NULL, i.e. never yet annotated --
 * see listIncidents' own header comment on why an unannotated incident
 * still matches). Returns the matching incident (never just a boolean) so
 * callers/UI can show the operator exactly which incident is authorizing
 * this failover.
 */
export async function findBlockingIncident(
  orgId: string,
  fromRegion: string,
): Promise<DrFailoverOutcome<Incident | null>> {
  const result = await listIncidents({ orgId, limit: 200, offset: 0 });
  if (!result.ok) return result;
  const openMatches = result.data.rows.filter(
    (i) => i.status === "open" && incidentReferencesRegion(i, fromRegion),
  );
  if (openMatches.length > 0) {
    return { ok: true, data: openMatches[0] };
  }

  // Also check platform-wide (unannotated) open incidents referencing the
  // region -- an incident the reconciler just opened may not yet carry
  // this org's orgId (annotateIncident is a separate, human/admin step).
  const platformWide = await listIncidents({ limit: 200, offset: 0 });
  if (!platformWide.ok) return platformWide;
  const match = platformWide.data.rows.find(
    (i) => i.status === "open" && incidentReferencesRegion(i, fromRegion),
  );
  return { ok: true, data: match ?? null };
}

export const DR_FAILOVER_ACTION = "dr.failover" as const;

export type DrFailoverStepName =
  | "precondition_incident"
  | "repin_region"
  | "create_restore_job"
  | "completed"
  | "failed";

function auditStep(input: {
  requestId: string;
  actor: string;
  orgId: string;
  fromRegion: string;
  toRegion: string;
  step: DrFailoverStepName;
  status: number;
  detail?: string;
}): void {
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: input.actor,
    method: "DR_FAILOVER",
    path: `/dr/failover/${input.orgId}/${input.fromRegion}->${input.toRegion}/${input.step}${
      input.detail ? `?detail=${encodeURIComponent(input.detail)}` : ""
    }`,
    status: input.status,
    requestId: input.requestId,
  });
}

export interface DrFailoverResult {
  org: Org;
  incident: Incident;
  restoreJob: BackupJob;
  sourceBackupJob: string;
}

/**
 * The real end-to-end runbook. Callers (the guarded route handler) are
 * expected to have ALREADY resolved a fresh maker-checker approval via
 * lib/approval-workflow.ts's requireApproval(DR_FAILOVER_ACTION, orgId)
 * before calling this -- this function itself re-checks nothing about
 * approval (that gate belongs to the route, same separation
 * lib/orgs.ts's deleteOrg/setOrgRegion hold: the k8s/DB primitive
 * performs the action, the route enforces who's allowed to ask for it).
 * What this function DOES re-check, unconditionally, fail-closed: the
 * open-incident precondition (step 1) -- a failover can never run without
 * one, no matter what already approved it.
 */
export async function initiateFailover(
  orgId: string,
  fromRegion: string,
  toRegion: string,
  reason: string,
  actor: string,
): Promise<DrFailoverOutcome<DrFailoverResult>> {
  const requestId = newRequestId();

  auditStep({
    requestId,
    actor,
    orgId,
    fromRegion,
    toRegion,
    step: "precondition_incident",
    status: 100,
    detail: `start reason=${reason}`,
  });

  if (fromRegion === toRegion) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 400 });
    return { ok: false, error: "fromRegion and toRegion must differ" };
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return orgResult;
  }
  if (!orgResult.data) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 404 });
    return { ok: false, error: "org not found" };
  }
  const org = orgResult.data;
  if (org.region && org.region !== fromRegion) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 409 });
    return {
      ok: false,
      error: `org's currently pinned region is '${org.region}', not '${fromRegion}' -- refusing a failover from a region this org isn't actually pinned to`,
    };
  }

  // Step 1: open-incident precondition -- refuses to run without one, no
  // matter how it got here.
  const incidentResult = await findBlockingIncident(orgId, fromRegion);
  if (!incidentResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return incidentResult;
  }
  if (!incidentResult.data) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 412 });
    return {
      ok: false,
      error: `refusing failover: no open incident referencing region '${fromRegion}' exists -- open/annotate one first (see /incidents)`,
    };
  }
  const incident = incidentResult.data;
  auditStep({
    requestId,
    actor,
    orgId,
    fromRegion,
    toRegion,
    step: "precondition_incident",
    status: 200,
    detail: `incident=${incident.id}`,
  });

  // Step 2: re-pin the org's region record. Reuses setOrgRegion exactly --
  // same enterprise-tier + live-node-region validation the manual PUT
  // /api/orgs/[id]/region path enforces, fail-closed inside setOrgRegion
  // itself.
  const repinResult = await setOrgRegion(orgId, toRegion);
  if (!repinResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "repin_region", status: 502 });
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return repinResult;
  }
  if (!repinResult.data) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "repin_region", status: 404 });
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 404 });
    return { ok: false, error: "org not found during re-pin" };
  }
  auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "repin_region", status: 200 });

  // Step 3: locate the org's real database Pod (one namespace per org --
  // see this module's header comment) and its latest COMPLETE backup Job.
  const projectsResult = await listProjects();
  if (!projectsResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return projectsResult;
  }
  const orgProject = projectsResult.data.find((p) => p.namespace === org.namespace);
  if (!orgProject) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 404 });
    return { ok: false, error: `no Project found in org namespace '${org.namespace}' to restore into` };
  }
  const podResult = await getProjectDatabasePod(orgProject);
  if (!podResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return podResult;
  }
  if (!podResult.data) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 404 });
    return { ok: false, error: `org's Project '${orgProject.name}' has no database Pod to restore into` };
  }

  const jobsResult = await listJobs(org.namespace, "app=platform-backups");
  if (!jobsResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return jobsResult;
  }
  const latestComplete = jobsResult.data
    .filter((j) => j.status === "Complete")
    .sort((a, b) => (b.completionTime ?? "").localeCompare(a.completionTime ?? ""))[0];
  if (!latestComplete) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 412 });
    return {
      ok: false,
      error: `refusing restore: no COMPLETE backup Job found in namespace '${org.namespace}' -- run a backup first`,
    };
  }

  // Step 4: real batch/v1 restore Job, restoring the latest backup into
  // the org's own (now re-pinned) database Pod.
  const restoreResult = await createRestoreJob(org.namespace, latestComplete.name, podResult.data.podName);
  if (!restoreResult.ok) {
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "create_restore_job", status: 502 });
    auditStep({ requestId, actor, orgId, fromRegion, toRegion, step: "failed", status: 502 });
    return restoreResult;
  }
  auditStep({
    requestId,
    actor,
    orgId,
    fromRegion,
    toRegion,
    step: "create_restore_job",
    status: 200,
    detail: `job=${restoreResult.data.name} sourceBackup=${latestComplete.name}`,
  });

  auditStep({
    requestId,
    actor,
    orgId,
    fromRegion,
    toRegion,
    step: "completed",
    status: 200,
    detail: `restoreJob=${restoreResult.data.name}`,
  });

  return {
    ok: true,
    data: {
      org: repinResult.data,
      incident,
      restoreJob: restoreResult.data,
      sourceBackupJob: latestComplete.name,
    },
  };
}

export interface DrFailoverStatus {
  org: Org;
  restoreJob: BackupJob | null;
  regionPinned: string | null;
}

/**
 * Real, live polling read for a runbook-progress UI -- re-derives status
 * from the SAME real objects initiateFailover produced (the org's region
 * pin, the restore Job's live batch/v1 status) rather than a separately
 * tracked "failover state" record, so this can never drift from what
 * actually happened in the cluster. `restoreJobName` is the Job name
 * initiateFailover returned to the caller (there is no other way to name
 * "the" restore Job for an org -- a namespace can have many).
 */
export async function getFailoverStatus(
  orgId: string,
  restoreJobName?: string,
): Promise<DrFailoverOutcome<DrFailoverStatus>> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) return orgResult;
  if (!orgResult.data) return { ok: false, error: "org not found" };
  const org = orgResult.data;

  let restoreJob: BackupJob | null = null;
  if (restoreJobName) {
    const jobsResult: K8sResult<BackupJob[]> = await listJobs(org.namespace, "app=platform-restores");
    if (jobsResult.ok) {
      restoreJob = jobsResult.data.find((j) => j.name === restoreJobName) ?? null;
    }
  }

  return {
    ok: true,
    data: { org, restoreJob, regionPinned: org.region ?? null },
  };
}

// getProject import kept for callers that resolve a single named project
// (unused directly in this module's own flow above, which scans via
// listProjects to find the org's project by namespace since org->project
// name is not 1:1 stored anywhere) -- re-exported so route handlers that
// want a direct-by-name lookup don't need a second import path.
export { getProject };
