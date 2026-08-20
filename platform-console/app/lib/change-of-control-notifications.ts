/**
 * Real Change-of-Control / M&A Notification Register: implements the
 * contractual obligation Fortune 5 MSAs routinely carry -- "Vendor shall
 * notify Customer within N days of any acquisition, merger, or change of
 * ownership of Vendor" -- which today lives nowhere but legal's own
 * memory and a scattered email trail. This module gives legal a real,
 * queryable ledger: one durable "trigger" event (the M&A event itself),
 * one per-org notification row recording exactly when (if ever) that org
 * was actually notified, and a computed breach-risk view derived from
 * each org's own contractual notice-window (mirrors lib/contract-
 * renewals.ts's `daysUntilRenewal`/`inNoticeWindow` computed-not-
 * persisted discipline: "still within the window" must never itself be a
 * stored fact that can drift from `now`).
 *
 * Storage: two real k8s ConfigMaps (`platform-change-of-control-triggers`
 * and `platform-change-of-control-notifications`, `platform-console`
 * namespace), reusing the exact getConfigMap/createOrUpdateConfigMap
 * get-then-create-or-patch primitive every other ConfigMap-backed module
 * in this repo (lib/contract-renewals.ts, lib/approval-workflow.ts,
 * lib/invoice-reconciliation.ts) already uses -- no new k8s resource
 * kind, no new RBAC verb: the same `platform-console-feature-flags` Role
 * already grants get/list/create/update/patch on `configmaps` in this
 * namespace with no `resourceNames` restriction. Two separate ConfigMaps
 * (not one, keyed by a compound id) because a single trigger fans out to
 * MANY per-org notification rows and the two have genuinely different
 * write cadences: a trigger is filed once and rarely touched again, while
 * notification rows are written one at a time, per org, as legal actually
 * sends each notice -- mirrors lib/subprocessors.ts's own
 * SubprocessorEvent-log-vs.-per-org-view split.
 *
 * Two-person integrity: filing a trigger (`fileChangeOfControlTrigger`)
 * is itself never sufficient to notify anyone -- it only records that an
 * M&A event happened and starts the clock. Recording that a customer org
 * was actually notified (`recordOrgNotification`) is the action gated
 * behind the SAME maker-checker `change-of-control.notify` approval
 * workflow (lib/approval-workflow.ts's requireApproval)
 * `le-request.respond`/`subprocessor.registry.update` already use -- one
 * owner's own say-so is never sufficient by itself to assert, in a
 * compliance ledger legal relies on, that a Fortune 5 customer's
 * contractual notice was actually delivered. Every state-mutating call
 * this module makes is durably audit-logged (`writeAuditLogEntryAwaited`,
 * awaited not fire-and-forget -- this ledger's whole purpose is to be
 * provable at audit time, so the durable row must exist before the call
 * returns), same discipline lib/invoice-reconciliation.ts's
 * recordInvoiceReconciliation/decideInvoiceReconciliation establish for
 * the same class of compliance-critical action.
 *
 * Breach-risk computation: for each org named in a trigger's
 * `affectedOrgIds`, `daysRemainingInWindow` = trigger.noticeWindowDays -
 * (now - trigger.triggerDate, in days). An org with no notification row
 * yet and `daysRemainingInWindow <= 0` is `inBreach: true` -- the
 * contractual deadline has passed with no recorded notice. An org that
 * HAS been notified is never `inBreach`, regardless of when the notice
 * was sent relative to the window (a late notice is a separate legal
 * question this ledger surfaces via `notifiedAfterWindow`, not something
 * this module silently launders into "not in breach").
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { newRequestId, writeAuditLogEntryAwaited } from "@/lib/audit-db";

export const CHANGE_OF_CONTROL_NAMESPACE = "platform-console";
export const CHANGE_OF_CONTROL_TRIGGERS_CONFIGMAP = "platform-change-of-control-triggers";
export const CHANGE_OF_CONTROL_NOTIFICATIONS_CONFIGMAP = "platform-change-of-control-notifications";

/** Default contractual notice window (days) applied to a newly-filed
 * trigger when the filer doesn't specify one -- the common Fortune 5 MSA
 * "notify within 30 days of change of control" term this capability
 * exists to implement. Always overridable per-trigger (different
 * customers negotiate different windows), same
 * DEFAULT_NOTICE_THRESHOLD_DAYS-is-a-default-not-a-floor discipline
 * lib/contract-renewals.ts documents for its own default. */
export const DEFAULT_NOTICE_WINDOW_DAYS = 30;

export type ChangeOfControlEventType = "acquisition" | "merger" | "ownership_change";

export interface ChangeOfControlTrigger {
  id: string; // crypto.randomUUID()
  eventType: ChangeOfControlEventType;
  /** Human-readable description of the actual event (acquirer name,
   * transaction name, etc.) -- free text, this module never parses it. */
  description: string;
  /** ISO 8601 date the change of control legally occurred (deal close),
   * NOT the date this row was filed -- the contractual clock always runs
   * from the real event date, so a trigger filed a few days after close
   * (e.g. while legal finalizes the notification list) does not silently
   * grant every org extra notice time it was never contractually owed. */
  triggerDate: string;
  /** Contractual notice window in days -- see DEFAULT_NOTICE_WINDOW_DAYS. */
  noticeWindowDays: number;
  /** Every org id this event obligates the vendor to notify. Set once at
   * filing time; see addAffectedOrgs for the only supported way to widen
   * it later (e.g. legal discovers an org was missed from the initial
   * list). */
  affectedOrgIds: string[];
  filedBy: string;
  filedAt: string;
}

export type OrgNotificationStatus = "pending" | "notified";

export interface OrgNotification {
  /** `<triggerId>.<orgId>` */
  id: string;
  triggerId: string;
  orgId: string;
  status: OrgNotificationStatus;
  /** ISO 8601 timestamp the notice was actually sent to this org, set
   * exactly once by recordOrgNotification. */
  notifiedAt?: string;
  /** The real approving identity from the change-of-control.notify
   * maker-checker approval this write was gated behind. */
  approvedBy?: string;
  /** Free-text record of how notice was delivered (e.g. "certified mail
   * to General Counsel per MSA notice clause 14.2") -- legal's own
   * evidentiary record, never validated beyond non-empty. */
  notificationMethod?: string;
  recordedBy?: string;
}

/** GET view model: one row per (trigger, affected org) pair, with the
 * breach-risk fields computed fresh on every read -- see this module's
 * header comment for the exact `daysRemainingInWindow`/`inBreach`/
 * `notifiedAfterWindow` semantics. Never persisted, so it is never stale
 * relative to "now" -- same discipline lib/contract-renewals.ts's
 * ContractRenewalWithStatus establishes. */
export interface ChangeOfControlOrgStatus {
  triggerId: string;
  eventType: ChangeOfControlEventType;
  description: string;
  triggerDate: string;
  noticeWindowDays: number;
  orgId: string;
  status: OrgNotificationStatus;
  notifiedAt?: string;
  notificationMethod?: string;
  daysRemainingInWindow: number;
  inBreach: boolean;
  notifiedAfterWindow: boolean;
}

function isEventType(value: unknown): value is ChangeOfControlEventType {
  return value === "acquisition" || value === "merger" || value === "ownership_change";
}

function isNotificationStatus(value: unknown): value is OrgNotificationStatus {
  return value === "pending" || value === "notified";
}

function parseTrigger(raw: string): ChangeOfControlTrigger | null {
  try {
    const p = JSON.parse(raw) as Partial<ChangeOfControlTrigger>;
    if (
      typeof p.id === "string" &&
      isEventType(p.eventType) &&
      typeof p.description === "string" &&
      typeof p.triggerDate === "string" &&
      typeof p.noticeWindowDays === "number" &&
      Number.isFinite(p.noticeWindowDays) &&
      Array.isArray(p.affectedOrgIds) &&
      p.affectedOrgIds.every((o) => typeof o === "string") &&
      typeof p.filedBy === "string" &&
      typeof p.filedAt === "string"
    ) {
      return {
        id: p.id,
        eventType: p.eventType,
        description: p.description,
        triggerDate: p.triggerDate,
        noticeWindowDays: p.noticeWindowDays,
        affectedOrgIds: p.affectedOrgIds,
        filedBy: p.filedBy,
        filedAt: p.filedAt,
      };
    }
    return null;
  } catch {
    return null;
  }
}

function parseNotification(raw: string): OrgNotification | null {
  try {
    const p = JSON.parse(raw) as Partial<OrgNotification>;
    if (
      typeof p.id === "string" &&
      typeof p.triggerId === "string" &&
      typeof p.orgId === "string" &&
      isNotificationStatus(p.status)
    ) {
      return {
        id: p.id,
        triggerId: p.triggerId,
        orgId: p.orgId,
        status: p.status,
        notifiedAt: typeof p.notifiedAt === "string" ? p.notifiedAt : undefined,
        approvedBy: typeof p.approvedBy === "string" ? p.approvedBy : undefined,
        notificationMethod: typeof p.notificationMethod === "string" ? p.notificationMethod : undefined,
        recordedBy: typeof p.recordedBy === "string" ? p.recordedBy : undefined,
      };
    }
    return null;
  } catch {
    return null;
  }
}

function notificationKey(triggerId: string, orgId: string): string {
  return `${triggerId}.${orgId}`;
}

async function readAllTriggers(): Promise<K8sResult<Map<string, ChangeOfControlTrigger>>> {
  const cm = await getConfigMap(CHANGE_OF_CONTROL_NAMESPACE, CHANGE_OF_CONTROL_TRIGGERS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, ChangeOfControlTrigger>();
  for (const [id, raw] of Object.entries(data)) {
    const parsed = parseTrigger(raw);
    // A hand-edited or corrupt row is skipped, not fatal -- same
    // "don't let one bad row break the whole list" discipline
    // lib/approval-workflow.ts's getAll / lib/orgs.ts's getRegistry use.
    if (parsed) out.set(id, parsed);
  }
  return { ok: true, data: out };
}

async function readAllNotifications(): Promise<K8sResult<Map<string, OrgNotification>>> {
  const cm = await getConfigMap(CHANGE_OF_CONTROL_NAMESPACE, CHANGE_OF_CONTROL_NOTIFICATIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, OrgNotification>();
  for (const [key, raw] of Object.entries(data)) {
    const parsed = parseNotification(raw);
    if (parsed) out.set(key, parsed);
  }
  return { ok: true, data: out };
}

/**
 * Fail-closed validation, same discipline as lib/invoice-
 * reconciliation.ts's validateInvoiceReconciliationInput: reject and
 * return a real, specific error string rather than a fabricated silent
 * default, so a malformed trigger can never reach the ConfigMap.
 */
export function validateChangeOfControlTriggerInput(input: {
  eventType: unknown;
  description: string;
  triggerDate: string;
  noticeWindowDays?: number;
  affectedOrgIds: string[];
}): string | null {
  if (!isEventType(input.eventType)) {
    return "eventType must be one of 'acquisition' | 'merger' | 'ownership_change'";
  }
  if (!input.description.trim()) {
    return "description is required";
  }
  if (!Number.isFinite(Date.parse(input.triggerDate))) {
    return "triggerDate must be a valid ISO 8601 date";
  }
  if (
    input.noticeWindowDays !== undefined &&
    (!Number.isFinite(input.noticeWindowDays) || input.noticeWindowDays <= 0)
  ) {
    return "noticeWindowDays must be a finite number > 0 when provided";
  }
  if (!Array.isArray(input.affectedOrgIds) || input.affectedOrgIds.length === 0) {
    return "affectedOrgIds must be a non-empty array of org ids";
  }
  return null;
}

/**
 * Real trigger-filing: records one M&A event and starts the notice-
 * window clock for every named org. Filing a trigger is itself never a
 * customer-facing action -- it only records that the event happened and
 * creates a `pending` notification row per affected org -- so this
 * function requires no approval gate of its own; the caller (POST
 * /api/owner/change-of-control) is responsible only for the "owner" role
 * floor every other platform-wide compliance-register write in this
 * console requires (mirrors lib/le-requests.ts's own ingest-vs-act
 * split: filing/ingesting is unprivileged-relative-to-owner, ACTING --
 * here, recordOrgNotification -- is the maker-checker-gated step).
 */
export async function fileChangeOfControlTrigger(input: {
  eventType: ChangeOfControlEventType;
  description: string;
  triggerDate: string;
  noticeWindowDays?: number;
  affectedOrgIds: string[];
  filedBy: string;
}): Promise<K8sResult<ChangeOfControlTrigger>> {
  const trigger: ChangeOfControlTrigger = {
    id: globalThis.crypto.randomUUID(),
    eventType: input.eventType,
    description: input.description.trim(),
    triggerDate: input.triggerDate,
    noticeWindowDays: input.noticeWindowDays ?? DEFAULT_NOTICE_WINDOW_DAYS,
    affectedOrgIds: Array.from(new Set(input.affectedOrgIds)),
    filedBy: input.filedBy,
    filedAt: new Date().toISOString(),
  };

  const triggerResult = await createOrUpdateConfigMap(
    CHANGE_OF_CONTROL_NAMESPACE,
    CHANGE_OF_CONTROL_TRIGGERS_CONFIGMAP,
    { [trigger.id]: JSON.stringify(trigger) },
  );
  if (!triggerResult.ok) return triggerResult;

  const notificationPatch: Record<string, string> = {};
  for (const orgId of trigger.affectedOrgIds) {
    const notification: OrgNotification = {
      id: notificationKey(trigger.id, orgId),
      triggerId: trigger.id,
      orgId,
      status: "pending",
    };
    notificationPatch[notification.id] = JSON.stringify(notification);
  }
  const notificationResult = await createOrUpdateConfigMap(
    CHANGE_OF_CONTROL_NAMESPACE,
    CHANGE_OF_CONTROL_NOTIFICATIONS_CONFIGMAP,
    notificationPatch,
  );
  if (!notificationResult.ok) return notificationResult;

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor: input.filedBy,
    method: "POST",
    path: "/api/owner/change-of-control",
    status: 201,
    requestId: newRequestId(),
    changeOfControlAction: "trigger_filed",
    changeOfControlTriggerId: trigger.id,
    changeOfControlAffectedOrgCount: trigger.affectedOrgIds.length,
  });

  return { ok: true, data: trigger };
}

/**
 * Widens an existing trigger's affected-org list (legal discovers an org
 * was missed from the initial notification list) and creates a
 * `pending` notification row for each newly-added org -- orgs already
 * present are left untouched (never re-created, never demoted from
 * `notified` back to `pending`). Not approval-gated for the same reason
 * fileChangeOfControlTrigger isn't: it only records who still needs
 * notice, it never itself asserts anyone was notified.
 */
export async function addAffectedOrgs(input: {
  triggerId: string;
  orgIds: string[];
  actor: string;
}): Promise<K8sResult<ChangeOfControlTrigger | null>> {
  const triggers = await readAllTriggers();
  if (!triggers.ok) return triggers;
  const existing = triggers.data.get(input.triggerId);
  if (!existing) return { ok: true, data: null };

  const newOrgIds = input.orgIds.filter((id) => !existing.affectedOrgIds.includes(id));
  if (newOrgIds.length === 0) return { ok: true, data: existing };

  const updated: ChangeOfControlTrigger = {
    ...existing,
    affectedOrgIds: [...existing.affectedOrgIds, ...newOrgIds],
  };
  const triggerResult = await createOrUpdateConfigMap(
    CHANGE_OF_CONTROL_NAMESPACE,
    CHANGE_OF_CONTROL_TRIGGERS_CONFIGMAP,
    { [updated.id]: JSON.stringify(updated) },
  );
  if (!triggerResult.ok) return triggerResult;

  const notificationPatch: Record<string, string> = {};
  for (const orgId of newOrgIds) {
    const notification: OrgNotification = {
      id: notificationKey(updated.id, orgId),
      triggerId: updated.id,
      orgId,
      status: "pending",
    };
    notificationPatch[notification.id] = JSON.stringify(notification);
  }
  const notificationResult = await createOrUpdateConfigMap(
    CHANGE_OF_CONTROL_NAMESPACE,
    CHANGE_OF_CONTROL_NOTIFICATIONS_CONFIGMAP,
    notificationPatch,
  );
  if (!notificationResult.ok) return notificationResult;

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor: input.actor,
    method: "PATCH",
    path: "/api/owner/change-of-control",
    status: 200,
    requestId: newRequestId(),
    changeOfControlAction: "affected_orgs_added",
    changeOfControlTriggerId: updated.id,
    changeOfControlAffectedOrgCount: newOrgIds.length,
  });

  return { ok: true, data: updated };
}

export async function listChangeOfControlTriggers(): Promise<K8sResult<ChangeOfControlTrigger[]>> {
  const all = await readAllTriggers();
  if (!all.ok) return all;
  return {
    ok: true,
    data: Array.from(all.data.values()).sort((a, b) => b.filedAt.localeCompare(a.filedAt)),
  };
}

export async function getChangeOfControlTrigger(
  triggerId: string,
): Promise<K8sResult<ChangeOfControlTrigger | null>> {
  const all = await readAllTriggers();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(triggerId) ?? null };
}

function withOrgStatus(
  trigger: ChangeOfControlTrigger,
  notification: OrgNotification | undefined,
  now: Date,
): ChangeOfControlOrgStatus {
  const triggerMs = Date.parse(trigger.triggerDate);
  const elapsedDays = Number.isFinite(triggerMs)
    ? (now.getTime() - triggerMs) / (24 * 60 * 60 * 1000)
    : Number.POSITIVE_INFINITY;
  const daysRemainingInWindow = Math.floor(trigger.noticeWindowDays - elapsedDays);

  const status = notification?.status ?? "pending";
  const notifiedAt = notification?.notifiedAt;
  const notifiedAfterWindow =
    status === "notified" && typeof notifiedAt === "string"
      ? (Date.parse(notifiedAt) - triggerMs) / (24 * 60 * 60 * 1000) > trigger.noticeWindowDays
      : false;
  const inBreach = status === "pending" && daysRemainingInWindow <= 0;

  return {
    triggerId: trigger.id,
    eventType: trigger.eventType,
    description: trigger.description,
    triggerDate: trigger.triggerDate,
    noticeWindowDays: trigger.noticeWindowDays,
    orgId: notification?.orgId ?? "",
    status,
    notifiedAt,
    notificationMethod: notification?.notificationMethod,
    daysRemainingInWindow,
    inBreach,
    notifiedAfterWindow,
  };
}

/**
 * Real compliance ledger view: one row per (trigger, affected org) pair
 * across every trigger ever filed, with breach-risk computed fresh --
 * backs GET /api/owner/change-of-control. Rows currently in breach (or
 * closest to breach) sort first, so legal sees the highest-risk rows
 * without having to scan the whole ledger. Optionally filtered to a
 * single trigger.
 */
export async function listChangeOfControlStatus(
  triggerId?: string,
): Promise<K8sResult<ChangeOfControlOrgStatus[]>> {
  const [triggers, notifications] = await Promise.all([readAllTriggers(), readAllNotifications()]);
  if (!triggers.ok) return triggers;
  if (!notifications.ok) return notifications;

  const now = new Date();
  const rows: ChangeOfControlOrgStatus[] = [];
  for (const trigger of triggers.data.values()) {
    if (triggerId && trigger.id !== triggerId) continue;
    for (const orgId of trigger.affectedOrgIds) {
      const notification = notifications.data.get(notificationKey(trigger.id, orgId));
      rows.push(withOrgStatus(trigger, notification, now));
    }
  }

  rows.sort((a, b) => {
    if (a.inBreach !== b.inBreach) return a.inBreach ? -1 : 1;
    return a.daysRemainingInWindow - b.daysRemainingInWindow;
  });

  return { ok: true, data: rows };
}

export type RecordOrgNotificationError = "not_found" | "already_notified";

/**
 * Real notification write: backs PUT /api/owner/change-of-control.
 * Callers (the route handler) MUST gate this behind a fresh
 * `change-of-control.notify` approval (lib/approval-workflow.ts's
 * requireApproval, same maker-checker primitive `le-request.respond`
 * already uses) before ever calling this -- this function itself
 * performs no approval check, same "module exposes the setter, the
 * route decides who may call it" division of labor as lib/invoice-
 * reconciliation.ts's decideInvoiceReconciliation. Refuses
 * (`"already_notified"`) a row that has already recorded a
 * notification -- a notification is recorded exactly once per
 * (trigger, org) pair, never silently overwritten (a genuinely wrong
 * notification date is a data-correction the ConfigMap can still be
 * hand-patched for, same as every other append-mostly ledger in this
 * repo; this function's job is to prevent an accidental double-write,
 * not to be un-overridable). Because this action is the one this whole
 * ledger exists to make provable, every write is durably audit-logged
 * here, distinct from the route's own per-request access-log entry --
 * same "the setter, not just the route, writes the durable compliance
 * row" discipline lib/invoice-reconciliation.ts establishes.
 */
export async function recordOrgNotification(input: {
  triggerId: string;
  orgId: string;
  notificationMethod: string;
  recordedBy: string;
  approvedBy: string;
}): Promise<K8sResult<OrgNotification> | { ok: false; error: RecordOrgNotificationError }> {
  const [triggers, notifications] = await Promise.all([readAllTriggers(), readAllNotifications()]);
  if (!triggers.ok) return triggers;
  if (!notifications.ok) return notifications;

  const trigger = triggers.data.get(input.triggerId);
  if (!trigger || !trigger.affectedOrgIds.includes(input.orgId)) {
    return { ok: false, error: "not_found" };
  }

  const key = notificationKey(input.triggerId, input.orgId);
  const existing = notifications.data.get(key);
  if (existing?.status === "notified") {
    return { ok: false, error: "already_notified" };
  }

  const updated: OrgNotification = {
    id: key,
    triggerId: input.triggerId,
    orgId: input.orgId,
    status: "notified",
    notifiedAt: new Date().toISOString(),
    approvedBy: input.approvedBy,
    notificationMethod: input.notificationMethod.trim(),
    recordedBy: input.recordedBy,
  };

  const result = await createOrUpdateConfigMap(
    CHANGE_OF_CONTROL_NAMESPACE,
    CHANGE_OF_CONTROL_NOTIFICATIONS_CONFIGMAP,
    { [key]: JSON.stringify(updated) },
  );
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    orgId: input.orgId,
    timestamp: new Date().toISOString(),
    actor: input.recordedBy,
    method: "PUT",
    path: "/api/owner/change-of-control",
    status: 200,
    requestId: newRequestId(),
    changeOfControlAction: "org_notified",
    changeOfControlTriggerId: input.triggerId,
  });

  return { ok: true, data: updated };
}
