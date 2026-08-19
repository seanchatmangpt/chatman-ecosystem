/**
 * Real, enforced change-freeze windows -- the specific ITIL / SOC2 CC8
 * (Change Management) control regulated Fortune-5 buyers (banks,
 * healthcare, retail during peak season) mandate by name: a declared
 * period during which production changes are policy-blocked, not just a
 * calendar reminder somebody has to remember to honor. Before this
 * module, nothing in this repo actually stopped a castle verb
 * (lib/castle.ts's runCastleVerb) or a project tier/quota mutation
 * (lib/k8s.ts's setProjectTier/patchResourceQuotaHard, called from
 * app/api/orgs/[id]/tier and app/api/projects/[name]/quota) from
 * executing during a declared freeze -- docs/SOC2-CONTROL-MAPPING.md
 * already tracks CC8 but had no enforcement mechanism for it.
 *
 * Storage: one real k8s ConfigMap (`platform-console-freeze-windows`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo (lib/authz.ts,
 * lib/ip-allowlist.ts, lib/approval-workflow.ts) already uses -- no new
 * k8s resource kind, no new RBAC verb: the same
 * `platform-console-feature-flags` Role already grants
 * get/list/create/update/patch on `configmaps` in this namespace with no
 * `resourceNames` restriction.
 *
 * One key per org: `data[orgId]` = JSON array of FreezeWindow -- same
 * one-key-per-org-namespace shape lib/ip-allowlist.ts already
 * establishes for a per-org list stored in a single shared ConfigMap.
 *
 * Enforcement model, deliberately fail-OPEN on infrastructure failure
 * (a k8s outage must never itself become an unplanned, undeclared
 * freeze) but fail-CLOSED on a declared freeze: `isFrozenNow`/
 * `getActiveFreeze` read live off this ConfigMap on every call (no
 * caching -- a freeze window's start/end boundary must take effect the
 * instant the clock crosses it, not on some stale interval), and
 * `checkFreezeGuard` is the one call a mutating route/module makes
 * before performing a real change: it returns `{blocked:false}` when no
 * freeze is active OR a fresh `freeze.override` approval already covers
 * this org (reusing lib/approval-workflow.ts's maker-checker flow --
 * same class of "a second, distinct human must sign off" gate
 * `tier.downgrade`/`quota.override` already use), and
 * `{blocked:true, freeze, overrideRequest?}` otherwise so the caller can
 * build the real structured 403 the spec requires.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { findApprovedRequest, requireApproval } from "@/lib/approval-workflow";

export const FREEZE_WINDOWS_NAMESPACE = "platform-console";
export const FREEZE_WINDOWS_CONFIGMAP = "platform-console-freeze-windows";

export interface FreezeWindow {
  id: string;
  orgId: string;
  startsAt: string; // RFC3339
  endsAt: string; // RFC3339
  reason: string;
  createdBy: string;
  createdAt: string;
  /** When true, a fresh `freeze.override` approval (maker-checker, same
   * TTL as every other approval-workflow.ts action) lets a mutating
   * action proceed anyway during this window. When false, this window
   * is a hard block -- no override is ever possible, the same
   * "regulated buyer's quarter-close freeze is genuinely non-negotiable"
   * requirement the spec names. */
  allowEmergencyOverride: boolean;
}

function isFreezeWindow(value: unknown): value is FreezeWindow {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.orgId === "string" &&
    typeof v.startsAt === "string" &&
    !Number.isNaN(Date.parse(v.startsAt)) &&
    typeof v.endsAt === "string" &&
    !Number.isNaN(Date.parse(v.endsAt)) &&
    typeof v.reason === "string" &&
    typeof v.createdBy === "string" &&
    typeof v.createdAt === "string" &&
    typeof v.allowEmergencyOverride === "boolean"
  );
}

function parseEntries(raw: string): FreezeWindow[] {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    // A hand-edited or corrupt row is skipped, not fatal -- same
    // "don't let one bad row break the whole list" discipline
    // lib/orgs.ts's getRegistry and lib/authz.ts's toAssignments use.
    return parsed.filter(isFreezeWindow);
  } catch {
    return [];
  }
}

/** Real read of one org's configured freeze windows, past and future
 * alike -- `[]` both when the ConfigMap/key genuinely doesn't exist yet
 * and when the cluster is unreachable, same fail-OPEN-on-infrastructure
 * convention lib/ip-allowlist.ts's getIpAllowlist documents. */
export async function listFreezeWindows(orgId: string): Promise<K8sResult<FreezeWindow[]>> {
  const result = await getConfigMap(FREEZE_WINDOWS_NAMESPACE, FREEZE_WINDOWS_CONFIGMAP);
  if (!result.ok) return { ok: true, data: [] };
  const raw = result.data?.data?.[orgId];
  if (!raw) return { ok: true, data: [] };
  return { ok: true, data: parseEntries(raw) };
}

/** Real replace-all write for one org's freeze window list -- same
 * "the UI edits the whole displayed set" convention
 * lib/ip-allowlist.ts's setIpAllowlist already establishes, RFC 7386
 * merge-patched into just this one ConfigMap key (every other org's key
 * is untouched). */
async function setFreezeWindows(
  orgId: string,
  windows: FreezeWindow[],
): Promise<K8sResult<FreezeWindow[]>> {
  const patch: Record<string, string> = { [orgId]: JSON.stringify(windows) };
  const result = await createOrUpdateConfigMap(FREEZE_WINDOWS_NAMESPACE, FREEZE_WINDOWS_CONFIGMAP, patch);
  if (!result.ok) return result;
  return { ok: true, data: windows };
}

export interface CreateFreezeWindowInput {
  orgId: string;
  startsAt: string;
  endsAt: string;
  reason: string;
  createdBy: string;
  allowEmergencyOverride: boolean;
}

/** Real validation the API route runs before ever storing a window --
 * same "reject and 400, never a partial/best-effort parse" discipline
 * lib/ip-allowlist.ts's isValidCidr and lib/custom-domains.ts's SAN
 * check already use. */
export function validateFreezeWindowInput(input: {
  startsAt: string;
  endsAt: string;
  reason: string;
}): string | null {
  const starts = Date.parse(input.startsAt);
  const ends = Date.parse(input.endsAt);
  if (Number.isNaN(starts)) return "startsAt must be a valid RFC3339 timestamp";
  if (Number.isNaN(ends)) return "endsAt must be a valid RFC3339 timestamp";
  if (ends <= starts) return "endsAt must be after startsAt";
  if (!input.reason.trim()) return "reason is required";
  return null;
}

export async function createFreezeWindow(
  input: CreateFreezeWindowInput,
): Promise<K8sResult<FreezeWindow>> {
  const existing = await listFreezeWindows(input.orgId);
  if (!existing.ok) return existing;

  const window: FreezeWindow = {
    id: globalThis.crypto.randomUUID(),
    orgId: input.orgId,
    startsAt: input.startsAt,
    endsAt: input.endsAt,
    reason: input.reason,
    createdBy: input.createdBy,
    createdAt: new Date().toISOString(),
    allowEmergencyOverride: input.allowEmergencyOverride,
  };
  const result = await setFreezeWindows(input.orgId, [...existing.data, window]);
  if (!result.ok) return result;
  return { ok: true, data: window };
}

export type DeleteFreezeWindowError = "not_found";

export async function deleteFreezeWindow(
  orgId: string,
  id: string,
): Promise<K8sResult<null> | { ok: false; error: DeleteFreezeWindowError }> {
  const existing = await listFreezeWindows(orgId);
  if (!existing.ok) return existing;
  if (!existing.data.some((w) => w.id === id)) return { ok: false, error: "not_found" };
  const remaining = existing.data.filter((w) => w.id !== id);
  const result = await setFreezeWindows(orgId, remaining);
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/** Is `window` active at `at` (default: now)? Both boundaries inclusive
 * -- a change attempted at the exact `startsAt`/`endsAt` instant is
 * still inside the declared window. */
export function isFreezeActive(window: FreezeWindow, at: Date = new Date()): boolean {
  const t = at.getTime();
  return t >= Date.parse(window.startsAt) && t <= Date.parse(window.endsAt);
}

/** Real live lookup of the org's currently-active freeze window, if any
 * -- reads the ConfigMap fresh on every call, never cached, so a window
 * takes effect/expires exactly on its declared boundary. `null` (not an
 * error) when nothing is active right now, same not-found-is-not-an-
 * error convention getCastleDeployment already uses. When more than one
 * window somehow overlaps, the one with the furthest `endsAt` wins (the
 * most conservative choice -- a caller must stay blocked through the
 * LONGEST applicable freeze, not the shortest). */
export async function getActiveFreeze(orgId: string): Promise<K8sResult<FreezeWindow | null>> {
  const all = await listFreezeWindows(orgId);
  if (!all.ok) return all;
  const now = new Date();
  const active = all.data
    .filter((w) => isFreezeActive(w, now))
    .sort((a, b) => Date.parse(b.endsAt) - Date.parse(a.endsAt))[0];
  return { ok: true, data: active ?? null };
}

/** Boolean convenience wrapper over getActiveFreeze -- fails OPEN (`false`)
 * on a k8s read error, same disclosed fail-open-on-infrastructure
 * default as lib/ip-allowlist.ts's checkIpAllowed: a cluster outage must
 * never itself manufacture an undeclared freeze. */
export async function isFrozenNow(orgId: string): Promise<boolean> {
  const result = await getActiveFreeze(orgId);
  return result.ok && result.data !== null;
}

export interface FreezeGuardBlocked {
  blocked: true;
  freeze: FreezeWindow;
  /** Present only when this window allows emergency override and no
   * fresh approval exists yet -- the caller (an API route) surfaces this
   * as part of the real 202/403 payload so the actor knows exactly which
   * pending request to get a second owner to approve. */
  overrideRequest?: import("@/lib/approval-workflow").ApprovalRequest;
}

export type FreezeGuardResult = { blocked: false } | FreezeGuardBlocked;

/**
 * The one call a guarded mutating action makes before executing:
 * lib/castle.ts's runCastleVerb and the tier/quota routes call this with
 * the org id the action targets. Returns `{blocked:false}` when no
 * freeze window covers `orgId` right now, OR when one does but a fresh
 * (<=24h, lib/approval-workflow.ts's APPROVAL_TTL_HOURS) approved
 * `freeze.override` row already exists for this exact org id.
 *
 * When a freeze is active with no fresh override approval:
 *   - If the window does not allow emergency override at all
 *     (`allowEmergencyOverride: false`), returns `{blocked:true, freeze}`
 *     with no `overrideRequest` -- there is nothing to approve, this
 *     freeze is a hard block, matching a regulated buyer's genuinely
 *     non-negotiable quarter-close freeze.
 *   - Otherwise, creates a real pending `freeze.override` approval
 *     request (via requireApproval, same maker-checker primitive
 *     tier.downgrade/quota.override already use) and returns it as
 *     `overrideRequest` so the caller can surface it.
 */
export async function checkFreezeGuard(
  orgId: string,
  requestedBy: string,
): Promise<K8sResult<FreezeGuardResult>> {
  const activeResult = await getActiveFreeze(orgId);
  if (!activeResult.ok) return activeResult;
  const freeze = activeResult.data;
  if (!freeze) return { ok: true, data: { blocked: false } };

  const approved = await findApprovedRequest("freeze.override", orgId);
  if (!approved.ok) return approved;
  if (approved.data) return { ok: true, data: { blocked: false } };

  if (!freeze.allowEmergencyOverride) {
    return { ok: true, data: { blocked: true, freeze } };
  }

  const approval = await requireApproval({
    action: "freeze.override",
    targetId: orgId,
    requestedBy,
    resourcePayload: { requestedFreezeId: freeze.id, requestedFreezeReason: freeze.reason },
  });
  if ("error" in approval) return { ok: false, error: approval.error };
  if (approval.ok) return { ok: true, data: { blocked: false } };
  return { ok: true, data: { blocked: true, freeze, overrideRequest: approval.request } };
}
