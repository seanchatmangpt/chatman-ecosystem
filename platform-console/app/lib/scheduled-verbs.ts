// --------------------------------------------- Maintenance-Window-Gated
// Castle Verb Scheduling
//
// lib/castle.ts's runCastleVerb executes an allowlisted castle actuation
// verb immediately on request -- there is no way to queue one for a
// pre-approved maintenance window and have it fire unattended, later,
// exactly when that window opens. Regulated customers (banking,
// healthcare) commonly require infra changes to execute ONLY inside a
// pre-announced maintenance window, with the actual execution verified
// after the fact against who approved it and when -- the specific
// change-execution control a Fortune-5 change-advisory-board process
// expects by name. This module adds exactly that.
//
// Storage: one real k8s ConfigMap (SCHEDULED_VERBS_CONFIGMAP, in
// lib/castle.ts's own CASTLE_NAMESPACE), reusing the exact
// getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
// every other ConfigMap-backed module in this repo already uses -- no new
// k8s resource kind. Key shape: one key per scheduled verb,
// `scheduledVerbId` (a crypto.randomUUID()) -> JSON ScheduledVerb, same
// one-key-per-row convention lib/approval-workflow.ts's ApprovalRequest
// storage already establishes.
//
// Approval gate: scheduleCastleVerb never runs anything itself -- it
// validates the verb against ALLOWED_CASTLE_VERBS, stores a real "pending"
// ScheduledVerb row, and files a real lib/approval-workflow.ts maker-
// checker request (action "castle.verb.schedule", targetId = the
// ScheduledVerb's own id) via the SAME requireApproval primitive
// lib/dr-failover.ts's initiateFailover route already uses. A second,
// distinct owner-role approver signs off through the existing generic
// POST /api/approvals/[id] route -- no new approval mechanism.
//
// Execution: runDueScheduledVerbs (called by the real CronJob
// lib/batch-jobs.ts's createCastleScheduleCronJob creates, polling every
// few minutes) is the ONLY code path that ever calls runCastleVerb for a
// scheduled entry. For each "pending" row whose requestedFor has already
// passed, it re-checks findApprovedRequest itself -- never trusting a
// cached "approved" flag -- and only actually runs the verb if a fresh
// approval is on file; otherwise the row is left "pending" for the next
// poll. This is the same "the guarded action re-checks its own
// precondition at execution time, not just at request time" discipline
// lib/dr-failover.ts's initiateFailover already documents.
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import {
  ALLOWED_CASTLE_VERBS,
  CASTLE_NAMESPACE,
  isCastleRunFrozenError,
  resolveCastleVerb,
  runCastleVerb,
  type AllowedCastleVerbId,
  type CastleJob,
} from "@/lib/castle";
import { findApprovedRequest, requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";

export const SCHEDULED_VERBS_CONFIGMAP = "platform-castle-scheduled-verbs";

export type ScheduledVerbStatus = "pending" | "executed" | "cancelled";

export interface ScheduledVerb {
  id: string;
  orgId: string;
  verbId: AllowedCastleVerbId;
  requestedFor: string; // ISO timestamp -- the maintenance window this verb is gated to
  requestedBy: string;
  requestedAt: string;
  approvedBy?: string;
  approvedAt?: string;
  status: ScheduledVerbStatus;
  executedAt?: string;
  jobName?: string;
  cancelledBy?: string;
  cancelledAt?: string;
}

// castle itself has no per-org scoping today (one shared cluster-wide
// `castle` namespace -- see lib/castle.ts's own header comment; there is
// no per-org castle namespace or deployment record anywhere in this
// module). `orgId` is carried on every ScheduledVerb per this
// capability's own spec so a future org-scoped castle deployment can
// filter by it with no storage migration, but until that day every real
// row this module writes uses this one honest, disclosed constant rather
// than fabricating a per-caller org id castle cannot actually enforce.
export const PLATFORM_ORG_ID = "platform";

function isAllowedVerbIdValue(value: unknown): value is AllowedCastleVerbId {
  return typeof value === "string" && resolveCastleVerb(value) !== null;
}

function isScheduledVerbStatus(value: unknown): value is ScheduledVerbStatus {
  return value === "pending" || value === "executed" || value === "cancelled";
}

function isScheduledVerb(value: unknown): value is ScheduledVerb {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.orgId === "string" &&
    isAllowedVerbIdValue(v.verbId) &&
    typeof v.requestedFor === "string" &&
    typeof v.requestedBy === "string" &&
    typeof v.requestedAt === "string" &&
    isScheduledVerbStatus(v.status)
  );
}

async function getAll(): Promise<K8sResult<Record<string, ScheduledVerb>>> {
  const existing = await getConfigMap(CASTLE_NAMESPACE, SCHEDULED_VERBS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, ScheduledVerb> = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      // A hand-edited or corrupt row is skipped, not fatal -- same
      // "don't let one bad row break the whole list" discipline
      // lib/approval-workflow.ts's getAll already uses.
      if (isScheduledVerb(row)) parsed[key] = row;
    } catch {
      // ignore -- malformed JSON for this key.
    }
  }
  return { ok: true, data: parsed };
}

async function putRow(row: ScheduledVerb): Promise<K8sResult<ScheduledVerb>> {
  const result = await createOrUpdateConfigMap(CASTLE_NAMESPACE, SCHEDULED_VERBS_CONFIGMAP, {
    [row.id]: JSON.stringify(row),
  });
  if (!result.ok) return result;
  return { ok: true, data: row };
}

/** Real listing, newest-requested-first -- "the listing IS the record",
 * same convention lib/castle.ts's listCastleJobs and
 * lib/approval-workflow.ts's listApprovals already use. */
export async function listScheduledVerbs(): Promise<K8sResult<ScheduledVerb[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  return {
    ok: true,
    data: Object.values(all.data).sort((a, b) => b.requestedAt.localeCompare(a.requestedAt)),
  };
}

export async function getScheduledVerb(id: string): Promise<K8sResult<ScheduledVerb | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data[id] ?? null };
}

export type ScheduleCastleVerbError = "invalid_verb" | "invalid_requested_for" | "in_the_past";

/**
 * Files a real ScheduledVerb ("pending") plus its own maker-checker
 * approval request. Never runs anything -- runDueScheduledVerbs (below)
 * is the only path that ever calls runCastleVerb. `verbId` must already
 * resolve against ALLOWED_CASTLE_VERBS (lib/castle.ts) and `requestedFor`
 * must be a real, parseable ISO timestamp strictly in the future --
 * refused, not clamped, exactly as this repo's other schedule-validating
 * modules (lib/scheduled-jobs.ts's isValidCronSchedule) refuse rather
 * than guess.
 */
export async function scheduleCastleVerb(input: {
  verbId: string;
  requestedFor: string;
  requestedBy: string;
  orgId?: string;
}): Promise<
  | { ok: true; scheduled: ScheduledVerb; approval: ApprovalRequest }
  | { ok: false; error: ScheduleCastleVerbError | string }
> {
  const verb = resolveCastleVerb(input.verbId);
  if (!verb) {
    return { ok: false, error: "invalid_verb" };
  }

  const requestedForMs = Date.parse(input.requestedFor);
  if (!Number.isFinite(requestedForMs)) {
    return { ok: false, error: "invalid_requested_for" };
  }
  if (requestedForMs <= Date.now()) {
    return { ok: false, error: "in_the_past" };
  }
  const requestedFor = new Date(requestedForMs).toISOString();

  const id = globalThis.crypto.randomUUID();
  const row: ScheduledVerb = {
    id,
    orgId: input.orgId ?? PLATFORM_ORG_ID,
    verbId: verb.id,
    requestedFor,
    requestedBy: input.requestedBy,
    requestedAt: new Date().toISOString(),
    status: "pending",
  };

  const written = await putRow(row);
  if (!written.ok) return written;

  const approval = await requireApproval({
    action: "castle.verb.schedule",
    targetId: id,
    requestedBy: input.requestedBy,
    resourcePayload: { requestedScheduledVerb: { verbId: verb.id, requestedFor } },
  });

  if ("error" in approval) {
    return { ok: false, error: approval.error };
  }
  // requireApproval only ever returns `ok: true` here if a FRESH approved
  // row already existed for this exact (action, targetId) pair -- which
  // cannot happen for a targetId that is a brand-new crypto.randomUUID()
  // this function just minted. So in practice this branch is unreached
  // on the create path; handled anyway rather than assumed away.
  return {
    ok: true,
    scheduled: written.data,
    approval: approval.ok ? approval.approval : approval.request,
  };
}

export type CancelScheduledVerbError = "not_found" | "not_pending";

/** Cancels a real pending ScheduledVerb -- refused (not silently
 * ignored) once it has already executed or was already cancelled, same
 * "a decision is recorded exactly once" discipline
 * lib/approval-workflow.ts's recordApprovalDecision already enforces. */
export async function cancelScheduledVerb(
  id: string,
  cancelledBy: string,
): Promise<K8sResult<ScheduledVerb> | { ok: false; error: CancelScheduledVerbError }> {
  const existing = await getScheduledVerb(id);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "not_found" };
  if (existing.data.status !== "pending") return { ok: false, error: "not_pending" };

  const updated: ScheduledVerb = {
    ...existing.data,
    status: "cancelled",
    cancelledBy,
    cancelledAt: new Date().toISOString(),
  };
  return putRow(updated);
}

export interface ScheduledVerbRunResult {
  scheduledVerbId: string;
  verbId: AllowedCastleVerbId;
  ran: boolean;
  reason?: "not_yet_approved" | "run_failed" | "frozen";
  job?: CastleJob;
  error?: string;
}

/**
 * The real, unattended execution path -- called by the CronJob
 * lib/batch-jobs.ts's createCastleScheduleCronJob polls with (via POST
 * /api/castle/schedule/run-due). For every "pending" row whose
 * requestedFor has already passed: re-checks findApprovedRequest itself
 * (never trusting the ScheduledVerb's own `approvedBy`, which does not
 * exist until this function sets it), and only calls runCastleVerb --
 * lib/castle.ts's own real, already-allowlist-checked actuation path --
 * if a fresh approval is on file. An unapproved-but-due row is left
 * "pending" untouched, picked up again on the next poll once (if ever)
 * a second approver signs off. `actor` identifies the poller itself in
 * runCastleVerb's own Job label (`platform-castle-run-by`) and, on
 * success, is recorded as the ScheduledVerb's `executedAt` actor -- the
 * real approving human identity is recorded separately as `approvedBy`,
 * sourced from the approval row itself, never fabricated.
 */
export async function runDueScheduledVerbs(
  actor: string,
): Promise<K8sResult<ScheduledVerbRunResult[]>> {
  const all = await listScheduledVerbs();
  if (!all.ok) return all;

  const now = Date.now();
  const due = all.data.filter(
    (row) => row.status === "pending" && Date.parse(row.requestedFor) <= now,
  );

  const results: ScheduledVerbRunResult[] = [];
  for (const row of due) {
    const approved = await findApprovedRequest("castle.verb.schedule", row.id);
    if (!approved.ok) {
      results.push({
        scheduledVerbId: row.id,
        verbId: row.verbId,
        ran: false,
        reason: "run_failed",
        error: approved.error,
      });
      continue;
    }
    if (!approved.data) {
      results.push({ scheduledVerbId: row.id, verbId: row.verbId, ran: false, reason: "not_yet_approved" });
      continue;
    }

    // Passes this row's own orgId through so lib/castle.ts's own
    // checkFreezeGuard (lib/freeze-windows.ts) is re-checked at the
    // moment of execution, not just at schedule time -- a maintenance
    // window approved days ago must not blindly override a freeze
    // declared AFTER the schedule request was filed. A frozen result is
    // NOT a failure: the row is left "pending" for a later poll (after
    // the freeze lifts, or a freeze.override is separately approved),
    // exactly like an unapproved-but-due row above.
    const runResult = await runCastleVerb(row.verbId, actor, row.orgId);
    if (!runResult.ok) {
      if (isCastleRunFrozenError(runResult)) {
        results.push({
          scheduledVerbId: row.id,
          verbId: row.verbId,
          ran: false,
          reason: "frozen",
          error: `blocked by freeze window '${runResult.freeze.id}'`,
        });
        continue;
      }
      results.push({
        scheduledVerbId: row.id,
        verbId: row.verbId,
        ran: false,
        reason: "run_failed",
        error: runResult.error,
      });
      continue;
    }

    const executed: ScheduledVerb = {
      ...row,
      status: "executed",
      approvedBy: approved.data.approvedBy,
      approvedAt: approved.data.approvedAt,
      executedAt: new Date().toISOString(),
      jobName: runResult.data.name,
    };
    await putRow(executed);
    results.push({ scheduledVerbId: row.id, verbId: row.verbId, ran: true, job: runResult.data });
  }

  return { ok: true, data: results };
}

/** Re-exported so callers (the API route, the UI) don't need a second
 * import from lib/castle.ts just to render the allowlist. */
export { ALLOWED_CASTLE_VERBS };
