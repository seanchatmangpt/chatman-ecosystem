/**
 * Real Legal Hold on the retention purge / DSAR erasure pipeline -- the
 * control litigation/legal teams require before Fortune 5 legal signs
 * off on ANY automated deletion: a named, durable flag that suspends
 * both lib/retention.ts's scheduled `platform_console.audit_log` purge
 * and lib/dsar.ts's Art.17/CCPA erasure flow for a declared scope (one
 * org, or the entire platform) until a second, distinct owner-role
 * approver releases it.
 *
 * Storage: one real k8s ConfigMap (`platform-console-legal-holds`,
 * `platform-console` namespace), the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch
 * primitive lib/approval-workflow.ts/lib/dsar.ts/lib/insurance-
 * attestation.ts already use -- no new k8s resource kind. Key =
 * `holdId` (`crypto.randomUUID()`).
 *
 * Two-directional maker-checker, deliberately asymmetric:
 *   - PLACING a hold is never gated behind approval. A hold only ever
 *     RESTRICTS destruction -- the same "declaring a freeze/pausing a
 *     schedule is the safe direction, only lifting it is gated" posture
 *     lib/freeze-windows.ts already establishes for change-freeze
 *     windows (a freeze window is declared unilaterally;
 *     `freeze.override` is the gated action). One legal team member
 *     acting alone must always be able to stop an automated deletion
 *     immediately -- requiring a second approver first would defeat the
 *     entire point of an emergency litigation hold.
 *   - RELEASING a hold goes through the exact same
 *     lib/approval-workflow.ts `requireApproval` maker-checker gate
 *     `dsar.erasure`/`dr.failover` already use: releasing a hold is what
 *     RESUMES eligibility for irreversible destruction, so one person's
 *     own say-so that litigation has concluded is never sufficient by
 *     itself.
 *
 * Enforcement: `isPurgeBlockedByLegalHold` and `isErasureBlockedByLegalHold`
 * are the two real predicates lib/retention.ts's `purgeExpiredAuditRows`
 * and lib/dsar.ts's `createDsarRequest`/`runDsarErasure` call BEFORE
 * doing any destructive work -- never advisory, never checked only by a
 * UI. A platform-wide hold (`scope: "platform"`) blocks every purge and
 * every org's erasure; an org-scoped hold (`scope: "org"`, a specific
 * `orgId`) blocks that org's erasure requests outright, and narrows the
 * platform-wide purge to skip only that org's own `org_id`-tagged
 * `audit_log` rows (via `purgeAuditLogRowsOlderThan`'s real
 * `excludeOrgIds` predicate) rather than blocking the whole table --
 * disclosed, real limitation: `platform_console.audit_log.org_id` is
 * nullable and not populated on every historical row (see
 * lib/retention.ts's own header comment on why this table has no
 * complete per-row org scoping), so an org-scoped hold's guarantee is
 * "every row this platform successfully tagged with this org's id is
 * preserved," not "every row that ever touched this org." A legal team
 * that needs a stronger guarantee should place a `scope: "platform"`
 * hold instead, which blocks the purge unconditionally.
 *
 * Every placement, release, and blocked-destruction attempt is written
 * as its own durable, `writeAuditLogEntryAwaited` audit row -- the
 * receipt that proves, to opposing counsel, exactly when the hold was
 * placed, that a since-attempted purge/erasure was actually refused
 * while it was active, and exactly who released it and when.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { newRequestId, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";

export const LEGAL_HOLDS_NAMESPACE = "platform-console";
export const LEGAL_HOLDS_CONFIGMAP = "platform-console-legal-holds";

export type LegalHoldScope = "platform" | "org";
export type LegalHoldStatus = "active" | "released";

export interface LegalHold {
  holdId: string;
  scope: LegalHoldScope;
  /** The org this hold restricts. Required (and only meaningful) when
   * `scope === "org"`; `null` when `scope === "platform"` (restricts
   * every org and the platform-wide purge). */
  orgId: string | null;
  /** The litigation matter / hold name a legal team names it by, e.g.
   * "Doe v. Acme Corp -- Case No. 3:26-cv-01234". */
  name: string;
  /** The human-supplied reason/justification recorded at placement
   * time -- never inferred, never fabricated. */
  reason: string;
  status: LegalHoldStatus;
  createdBy: string;
  createdAt: string; // RFC3339
  releasedBy?: string;
  releasedAt?: string; // RFC3339
  releaseReason?: string;
}

function isLegalHoldScope(value: unknown): value is LegalHoldScope {
  return value === "platform" || value === "org";
}
function isLegalHoldStatus(value: unknown): value is LegalHoldStatus {
  return value === "active" || value === "released";
}
function isLegalHold(value: unknown): value is LegalHold {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.holdId === "string" &&
    isLegalHoldScope(v.scope) &&
    (v.orgId === null || typeof v.orgId === "string") &&
    typeof v.name === "string" &&
    typeof v.reason === "string" &&
    isLegalHoldStatus(v.status) &&
    typeof v.createdBy === "string" &&
    typeof v.createdAt === "string"
  );
}

async function getAll(): Promise<K8sResult<Record<string, LegalHold>>> {
  const existing = await getConfigMap(LEGAL_HOLDS_NAMESPACE, LEGAL_HOLDS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, LegalHold> = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      if (isLegalHold(row)) parsed[key] = row;
      // A hand-edited or corrupt row is skipped, not fatal -- same
      // discipline lib/approval-workflow.ts's/lib/dsar.ts's getAll uses.
    } catch {
      // ignore -- malformed JSON for this key
    }
  }
  return { ok: true, data: parsed };
}

async function putHold(hold: LegalHold): Promise<K8sResult<LegalHold>> {
  const result = await createOrUpdateConfigMap(LEGAL_HOLDS_NAMESPACE, LEGAL_HOLDS_CONFIGMAP, {
    [hold.holdId]: JSON.stringify(hold),
  });
  if (!result.ok) return result;
  return { ok: true, data: hold };
}

/**
 * Real, chronological read of every recorded legal hold -- optionally
 * narrowed to holds that would restrict a given org (its own org-scoped
 * holds plus any platform-wide hold), which is exactly what a legal
 * team's own per-matter review screen, and this module's own purge/
 * erasure enforcement predicates below, both need.
 */
export async function listLegalHolds(orgId?: string): Promise<K8sResult<LegalHold[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  const rows = Object.values(all.data)
    .filter((h) => !orgId || h.scope === "platform" || h.orgId === orgId)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { ok: true, data: rows };
}

export async function getLegalHold(holdId: string): Promise<K8sResult<LegalHold | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data[holdId] ?? null };
}

/**
 * Every currently-active hold, platform-wide -- the one real read both
 * `purgeExpiredAuditRows` and this module's own `isErasureBlockedByLegalHold`
 * call against, so a caller never has to re-derive "active" filtering
 * itself.
 */
export async function listActiveLegalHolds(): Promise<K8sResult<LegalHold[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  const rows = Object.values(all.data)
    .filter((h) => h.status === "active")
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { ok: true, data: rows };
}

/**
 * Places one real, immediately-active legal hold. Never approval-gated
 * (see this module's header comment) -- a legal team member acting
 * alone can always stop scheduled destruction. Audited immediately and
 * durably (`writeAuditLogEntryAwaited`, not the fire-and-forget
 * `writeAuditLogEntry`): the placement record itself is part of the
 * evidence a litigation hold was actually in force starting at this
 * exact timestamp.
 */
export async function placeLegalHold(input: {
  scope: LegalHoldScope;
  orgId: string | null;
  name: string;
  reason: string;
  createdBy: string;
}): Promise<K8sResult<LegalHold>> {
  const hold: LegalHold = {
    holdId: globalThis.crypto.randomUUID(),
    scope: input.scope,
    orgId: input.scope === "platform" ? null : input.orgId,
    name: input.name,
    reason: input.reason,
    status: "active",
    createdBy: input.createdBy,
    createdAt: new Date().toISOString(),
  };
  const result = await putHold(hold);
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    ...(hold.orgId ? { orgId: hold.orgId } : {}),
    timestamp: new Date().toISOString(),
    actor: input.createdBy,
    method: "POST",
    path: `/api/owner/legal-hold (holdId=${hold.holdId})`,
    status: 200,
    requestId: newRequestId(),
    legalHoldAction: "placed",
    legalHoldId: hold.holdId,
    legalHoldScope: hold.scope,
    ...(hold.orgId ? { legalHoldOrgId: hold.orgId } : {}),
  });

  return result;
}

/**
 * requireApproval gate for RELEASING a hold -- the resource payload a
 * second, distinct owner-role approver reviews before the hold is ever
 * actually lifted (`targetId` is the hold's own id). Mirrors the exact
 * `requireApproval` call shape every other maker-checker route in this
 * repo (PUT /api/owner/insurance-attestation, POST /api/privacy/
 * request-erasure) already uses.
 */
export async function requireLegalHoldReleaseApproval(input: {
  hold: LegalHold;
  releaseReason: string;
  requestedBy: string;
}): Promise<
  | { ok: true; approval: ApprovalRequest }
  | { ok: false; request: ApprovalRequest }
  | { ok: false; error: string }
> {
  return requireApproval({
    action: "legal-hold.release",
    targetId: input.hold.holdId,
    requestedBy: input.requestedBy,
    resourcePayload: {
      requestedLegalHoldRelease: {
        holdId: input.hold.holdId,
        scope: input.hold.scope,
        orgId: input.hold.orgId,
        releaseReason: input.releaseReason,
      },
    },
  });
}

/**
 * Real release of a legal hold -- called only once a fresh
 * `legal-hold.release` approval already exists (never before). Marks
 * the hold `released`, never deletes the row: a released hold's full
 * history (who placed it, why, who released it, why, when) stays
 * permanently readable via `listLegalHolds`, same "never a hard delete,
 * status transitions only" discipline lib/approval-workflow.ts's own
 * ApprovalRequest rows already establish.
 */
export async function releaseLegalHold(input: {
  holdId: string;
  releasedBy: string;
  releaseReason: string;
}): Promise<K8sResult<LegalHold>> {
  const existing = await getLegalHold(input.holdId);
  if (!existing.ok) return existing;
  if (!existing.data) {
    return { ok: false, error: `no legal hold found with id '${input.holdId}'` };
  }
  if (existing.data.status === "released") {
    return { ok: true, data: existing.data }; // idempotent: already released
  }

  const released: LegalHold = {
    ...existing.data,
    status: "released",
    releasedBy: input.releasedBy,
    releasedAt: new Date().toISOString(),
    releaseReason: input.releaseReason,
  };
  const result = await putHold(released);
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    ...(released.orgId ? { orgId: released.orgId } : {}),
    timestamp: new Date().toISOString(),
    actor: input.releasedBy,
    method: "POST",
    path: `/api/owner/legal-hold (holdId=${released.holdId}, action=release)`,
    status: 200,
    requestId: newRequestId(),
    legalHoldAction: "released",
    legalHoldId: released.holdId,
    legalHoldScope: released.scope,
    ...(released.orgId ? { legalHoldOrgId: released.orgId } : {}),
  });

  return result;
}

export interface LegalHoldPurgeGuard {
  /** true when at least one active `scope: "platform"` hold exists --
   * the whole platform-wide purge must be refused outright, not merely
   * narrowed. */
  blockedEntirely: boolean;
  /** The real org ids `purgeAuditLogRowsOlderThan` must exclude from its
   * DELETE -- every org with an active `scope: "org"` hold, deduplicated. */
  excludeOrgIds: string[];
  /** The full list of active holds this guard was computed from, for the
   * caller's own audit-log/receipt annotation. */
  activeHolds: LegalHold[];
}

/**
 * The one real read `purgeExpiredAuditRows` calls before ever touching
 * `platform_console.audit_log` -- never advisory. See this module's
 * header comment for the disclosed org_id-nullability limitation on the
 * org-scoped narrowing.
 */
export async function computeLegalHoldPurgeGuard(): Promise<K8sResult<LegalHoldPurgeGuard>> {
  const active = await listActiveLegalHolds();
  if (!active.ok) return active;

  const blockedEntirely = active.data.some((h) => h.scope === "platform");
  const excludeOrgIds = Array.from(
    new Set(
      active.data
        .filter((h) => h.scope === "org" && h.orgId)
        .map((h) => h.orgId as string),
    ),
  );

  return { ok: true, data: { blockedEntirely, excludeOrgIds, activeHolds: active.data } };
}

/**
 * The one real read POST /api/privacy/request-erasure and
 * lib/dsar.ts's `createDsarRequest`/`runDsarErasure` call before ever
 * erasing a subject's rows for `orgId` -- returns the blocking hold (so
 * the caller can echo its id/name/reason back) or `null` when erasure
 * for this org is not currently restricted.
 */
export async function isErasureBlockedByLegalHold(
  orgId: string,
): Promise<K8sResult<LegalHold | null>> {
  const active = await listActiveLegalHolds();
  if (!active.ok) return active;
  const blocking = active.data.find((h) => h.scope === "platform" || h.orgId === orgId);
  return { ok: true, data: blocking ?? null };
}
