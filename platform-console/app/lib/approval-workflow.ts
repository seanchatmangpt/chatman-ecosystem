/**
 * Real role-based multi-party (maker-checker) approval workflow for
 * high-risk provisioning actions -- the specific human-in-the-loop
 * control SOC2/ISO27001 auditors and enterprise security review
 * checklists ask for by name that this repo did not previously provide.
 * lib/authz.ts gates by a single actor's OWN role rank (an owner can act
 * entirely alone); lib/policy.ts is read-only; lib/quota-enforcement.ts
 * enforces automatically. None of the three ever requires a SECOND,
 * DISTINCT human identity to sign off before a destructive or
 * money-moving action executes. This module adds exactly that, as a real
 * gate a guarded route handler calls BEFORE performing the action -- not
 * a UI-only affordance.
 *
 * Storage: one real k8s ConfigMap (`platform-console-approvals`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo (lib/authz.ts,
 * lib/budget-alerts.ts, lib/orgs.ts) already uses -- no new k8s resource
 * kind, no new RBAC verb: the same `platform-console-feature-flags` Role
 * already grants get/list/create/update/patch on `configmaps` in this
 * namespace with no `resourceNames` restriction.
 *
 * Key shape: one key per approval request, `requestId` (a
 * `crypto.randomUUID()`) -> JSON ApprovalRequest. A k8s ConfigMap `data`
 * key must match `[-._a-zA-Z0-9]+` -- a UUID already satisfies that, so
 * no escaping step like lib/authz.ts's encodeIdentifierKey is ever
 * needed here.
 *
 * Two-person integrity is enforced at TWO points, neither of which trusts
 * the client:
 *   1. recordApprovalDecision refuses (403, enforced by the caller) a
 *      decision from the same identifier that created the request --
 *      approver !== requester is checked against the REQUEST'S OWN
 *      stored `requestedBy`, never a client-supplied claim.
 *   2. findApprovedRequest only matches rows with status "approved" AND
 *      approvedAt within the last APPROVAL_TTL_HOURS hours -- a stale
 *      approval (or one for a different target) can never silently
 *      satisfy a new attempt at the guarded action.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { ProjectTier } from "@/lib/tiers";

export const APPROVALS_NAMESPACE = "platform-console";
export const APPROVALS_CONFIGMAP = "platform-console-approvals";

// Freshness window an approval remains valid for after being granted --
// same "trailing window" discipline lib/budget-alerts.ts's
// BUDGET_WINDOW_HOURS documents: a 24h-old "approved" no longer proves
// the second approver would still say yes to retrying the SAME action
// today, so it must not silently authorize it.
export const APPROVAL_TTL_HOURS = 24;

export type ApprovalAction =
  | "org.delete"
  | "quota.override"
  | "tier.downgrade"
  | "backup.retention.change"
  | "export-subscription.update"
  | "dr.failover"
  | "dsar.erasure"
  | "castle.verb.schedule"
  | "freeze.override";
export const ACTIONS_REQUIRING_APPROVAL: ApprovalAction[] = [
  "org.delete",
  "quota.override",
  "tier.downgrade",
  "backup.retention.change",
  // A scheduled export subscription is a real, standing data-
  // exfiltration control: once saved, it recurringly ships this org's
  // audit log or full export bundle to a bucket a THIRD PARTY (the
  // customer's own SIEM/data-lake pipeline) controls, completely
  // unattended. That is exactly the "can quietly move data out of the
  // platform on an ongoing basis" class of change org.delete's own
  // header comment already documents the bar for -- one owner acting
  // alone (lib/authz.ts's requireRoleIn) is not sufficient; a second,
  // distinct owner-role approver must sign off before bucket
  // credentials + schedule are ever accepted.
  "export-subscription.update",
  // Multi-region DR failover: re-pins an org's real data-residency region
  // AND triggers a real destructive restore Job that overwrites the
  // target database Pod's live table data (lib/k8s.ts's createRestoreJob
  // header comment) -- the same "destructive, high-blast-radius,
  // requires a second distinct human" bar org.delete already sets. See
  // lib/dr-failover.ts.
  "dr.failover",
  // GDPR Art.17 / CCPA erasure: redacts a real data subject's identity
  // out of the durable audit trail and their per-org membership record.
  // Irreversible (a redacted actor value cannot be un-redacted -- the
  // original email is gone, by design) and, unlike a plain access
  // export, changes durable state -- the same "irreversible,
  // destructive, one owner acting alone is not enough" bar org.delete
  // and dr.failover already set. See lib/dsar.ts.
  "dsar.erasure",
  // Maintenance-Window-Gated Castle Verb Scheduling
  // (lib/scheduled-verbs.ts): scheduleCastleVerb queues a real castle
  // actuation verb (a real batch/v1 Job -- see lib/castle.ts's
  // runCastleVerb) to run unattended, later, inside a pre-announced
  // maintenance window, with no human present to review the actual
  // moment it fires. That is exactly the "can execute later, unattended,
  // with no one watching" class of risk org.delete and dr.failover's own
  // header comments already set the bar for -- the requester's own
  // maker-checker sign-off is not sufficient; a second, distinct
  // owner-role approver must sign off BEFORE the entry is ever eligible
  // for the poller to run it, same as every other action in this list.
  "castle.verb.schedule",
  // Declared change-freeze window override (lib/freeze-windows.ts, ITIL
  // / SOC2 CC8 change-management control): a freeze window whose
  // `allowEmergencyOverride` is true lets a mutating action (a castle
  // verb Run, a project tier change, a quota patch) still execute during
  // the window, but only after a SECOND, distinct owner-role approver
  // signs off on breaking a freeze the org itself declared -- the
  // requester's own judgment that "this is an emergency" is not
  // sufficient by itself, same maker-checker bar every other action in
  // this list sets. A freeze window with `allowEmergencyOverride: false`
  // never reaches this at all -- checkFreezeGuard refuses to create an
  // override request for it, it is a hard block.
  "freeze.override",
];

export type ApprovalStatus = "pending" | "approved" | "rejected";

/**
 * Real, action-specific detail carried alongside the generic
 * requester/target/status fields every ApprovalRequest already had --
 * lets an approver see WHAT they're signing off on (the exact new quota
 * ceiling, or the exact tier the org would move to) instead of just an
 * opaque targetId. Optional and additive: `org.delete` (the original
 * guarded action) sets neither field and round-trips through
 * JSON.parse/stringify unchanged, same forward-compatible-optional-field
 * discipline lib/orgs.ts's OrgBranding/region fields already establish.
 */
export interface ApprovalResourcePayload {
  /** quota.override: the requested `ResourceQuota.spec.hard` map --
   * same key shape (`pods`, `requests.cpu`, `limits.memory`, ...)
   * lib/tiers.ts's resourceQuotaHardFor/lib/k8s.ts's patchResourceQuotaHard
   * already use. */
  requestedHard?: Record<string, string>;
  /** tier.downgrade: the tier the Project would move to once approved. */
  requestedTier?: ProjectTier;
  /** backup.retention.change: the retention window (in days) the org's
   * backup policy would move to once approved. */
  requestedRetentionDays?: number;
  /** export-subscription.update: the non-secret shape of the requested
   * bucket subscription -- bucket endpoint/name/prefix/cadence/scope --
   * so a second approver can see WHERE this org's data would be shipped
   * and how often before signing off. Deliberately excludes the access
   * key id and secret access key: an approval request row lives in the
   * same platform-console-approvals ConfigMap every other approval type
   * does, and credential material must never be readable there even in
   * transit through a pending approval -- lib/s3-export-subscription.ts's
   * own encrypted-at-rest storage is the only place those two fields are
   * ever persisted. */
  requestedExportSubscription?: {
    bucketEndpoint: string;
    bucketName: string;
    prefix: string;
    cadence: string;
    scope: string;
    enabled: boolean;
  };
  /** dr.failover: the non-secret shape of the requested failover -- which
   * region this org would move FROM/TO and the human-supplied reason --
   * so a second approver can see exactly what they're authorizing before
   * signing off on a destructive, live-data-overwriting restore. */
  requestedFailover?: {
    fromRegion: string;
    toRegion: string;
    reason: string;
  };
  /** castle.verb.schedule: the non-secret shape of the requested
   * scheduled castle verb -- which allowlisted verb, and the exact ISO
   * timestamp it is requested to fire at -- so a second approver can see
   * exactly what will run, and when, before signing off. `targetId` on
   * the ApprovalRequest itself is the ScheduledVerb's own id
   * (lib/scheduled-verbs.ts), not the verb id, so this is the field an
   * approver actually reads to know which castle verb is in play. */
  /** freeze.override: the non-secret shape of the freeze window being
   * overridden -- which window (by id) and its human-supplied reason --
   * so a second approver can see exactly which declared freeze they are
   * being asked to authorize breaking. */
  requestedFreezeId?: string;
  requestedFreezeReason?: string;
  requestedScheduledVerb?: {
    verbId: string;
    requestedFor: string;
  };
}

export interface ApprovalRequest {
  requestId: string;
  action: ApprovalAction;
  targetId: string;
  requestedBy: string;
  requestedAt: string;
  status: ApprovalStatus;
  approvedBy?: string;
  approvedAt?: string;
  reason?: string;
  resourcePayload?: ApprovalResourcePayload;
}

function isApprovalAction(value: string): value is ApprovalAction {
  return (ACTIONS_REQUIRING_APPROVAL as string[]).includes(value);
}

function isApprovalStatus(value: string): value is ApprovalStatus {
  return value === "pending" || value === "approved" || value === "rejected";
}

function isApprovalRequest(value: unknown): value is ApprovalRequest {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.requestId === "string" &&
    typeof v.action === "string" &&
    isApprovalAction(v.action) &&
    typeof v.targetId === "string" &&
    typeof v.requestedBy === "string" &&
    typeof v.requestedAt === "string" &&
    typeof v.status === "string" &&
    isApprovalStatus(v.status)
  );
}

async function getAll(): Promise<K8sResult<Record<string, ApprovalRequest>>> {
  const existing = await getConfigMap(APPROVALS_NAMESPACE, APPROVALS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, ApprovalRequest> = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      if (isApprovalRequest(row)) parsed[key] = row;
      // A hand-edited or corrupt row is skipped, not fatal -- same
      // "don't let one bad row break the whole list" discipline
      // lib/orgs.ts's getRegistry and lib/authz.ts's toAssignments use.
    } catch {
      // ignore -- malformed JSON for this key, same skip discipline.
    }
  }
  return { ok: true, data: parsed };
}

export async function listApprovals(): Promise<K8sResult<ApprovalRequest[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  return {
    ok: true,
    data: Object.values(all.data).sort((a, b) => b.requestedAt.localeCompare(a.requestedAt)),
  };
}

export async function getApproval(requestId: string): Promise<K8sResult<ApprovalRequest | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data[requestId] ?? null };
}

/**
 * Creates one real pending approval request. Called internally by every
 * guarded route (e.g. DELETE /api/orgs/[id]) the moment it detects no
 * fresh approved row exists for the target, and directly by POST
 * /api/approvals for the same purpose.
 */
export async function createApprovalRequest(input: {
  action: ApprovalAction;
  targetId: string;
  requestedBy: string;
  resourcePayload?: ApprovalResourcePayload;
}): Promise<K8sResult<ApprovalRequest>> {
  const requestId = globalThis.crypto.randomUUID();
  const request: ApprovalRequest = {
    requestId,
    action: input.action,
    targetId: input.targetId,
    requestedBy: input.requestedBy,
    requestedAt: new Date().toISOString(),
    status: "pending",
    ...(input.resourcePayload ? { resourcePayload: input.resourcePayload } : {}),
  };
  const result = await createOrUpdateConfigMap(APPROVALS_NAMESPACE, APPROVALS_CONFIGMAP, {
    [requestId]: JSON.stringify(request),
  });
  if (!result.ok) return result;
  return { ok: true, data: request };
}

export type RecordDecisionError = "not_found" | "already_decided" | "self_approval";

/**
 * Records a real approve/reject decision via the same one-key-at-a-time
 * merge-patch every other ConfigMap writer in this repo uses. Enforces
 * real two-person integrity server-side: an approver identifier equal to
 * the request's OWN stored `requestedBy` is refused with
 * "self_approval" -- the caller (POST /api/approvals/[id]) turns that
 * into the real 403 the spec requires, never a client-trusted check.
 * Also refuses a decision on a request that is no longer "pending" --
 * a decision is recorded exactly once, never silently overwritten.
 */
export async function recordApprovalDecision(input: {
  requestId: string;
  decision: "approved" | "rejected";
  approvedBy: string;
  reason?: string;
}): Promise<K8sResult<ApprovalRequest> | { ok: false; error: RecordDecisionError }> {
  const existing = await getApproval(input.requestId);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "not_found" };
  if (existing.data.status !== "pending") return { ok: false, error: "already_decided" };
  if (existing.data.requestedBy === input.approvedBy) return { ok: false, error: "self_approval" };

  const updated: ApprovalRequest = {
    ...existing.data,
    status: input.decision,
    approvedBy: input.approvedBy,
    approvedAt: new Date().toISOString(),
    reason: input.reason,
  };
  const result = await createOrUpdateConfigMap(APPROVALS_NAMESPACE, APPROVALS_CONFIGMAP, {
    [input.requestId]: JSON.stringify(updated),
  });
  if (!result.ok) return result;
  return { ok: true, data: updated };
}

/**
 * The real enforcement primitive a guarded route calls: is there a
 * status:"approved" row for this exact (action, targetId) pair, approved
 * within the last APPROVAL_TTL_HOURS hours? Returns the matching request
 * (most recently approved first) or null -- never a boolean alone, so the
 * caller can echo the approving identity/timestamp back if it wants to.
 */
export async function findApprovedRequest(
  action: ApprovalAction,
  targetId: string,
): Promise<K8sResult<ApprovalRequest | null>> {
  const all = await listApprovals();
  if (!all.ok) return all;

  const cutoff = Date.now() - APPROVAL_TTL_HOURS * 60 * 60 * 1000;
  const match = all.data
    .filter(
      (r) =>
        r.action === action &&
        r.targetId === targetId &&
        r.status === "approved" &&
        r.approvedAt !== undefined &&
        Date.parse(r.approvedAt) >= cutoff,
    )
    .sort((a, b) => (b.approvedAt ?? "").localeCompare(a.approvedAt ?? ""))[0];

  return { ok: true, data: match ?? null };
}

/**
 * requireApproval: the one call a guarded route handler makes. If a
 * fresh approved row already exists for this (action, targetId), returns
 * `{ok: true}` and the route proceeds with the real action. Otherwise it
 * creates a new pending request (idempotent-ish -- a second call while
 * one is already pending just creates a second row visible in the
 * approvals list; it does not synthesize a fake "approved") and returns
 * `{ok: false, request}` so the route can return the real 202 the spec
 * requires instead of performing the action.
 */
export async function requireApproval(input: {
  action: ApprovalAction;
  targetId: string;
  requestedBy: string;
  resourcePayload?: ApprovalResourcePayload;
}): Promise<
  | { ok: true; approval: ApprovalRequest }
  | { ok: false; request: ApprovalRequest }
  | { ok: false; error: string }
> {
  const approved = await findApprovedRequest(input.action, input.targetId);
  if (!approved.ok) return { ok: false, error: approved.error };
  if (approved.data) return { ok: true, approval: approved.data };

  const created = await createApprovalRequest(input);
  if (!created.ok) return { ok: false, error: created.error };
  return { ok: false, request: created.data };
}
