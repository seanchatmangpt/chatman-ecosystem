/**
 * Real Contract Renewal Reminder + auto-renewal workflow, tied to Stripe
 * subscription end dates (lib/stripe-billing.ts). Enterprise procurement
 * teams need two things this console did not previously track anywhere:
 *
 *   1. Visibility into WHEN an org's contract actually ends -- derived
 *      from the real Stripe subscription's `current_period_end`
 *      (lib/stripe-billing.ts's `StoredSubscription.currentPeriodEnd`),
 *      never a second, hand-entered date that can drift from what Stripe
 *      actually bills.
 *   2. A documented renewal/non-renewal decision trail (SOC2 /
 *      vendor-management requirement) -- who set `autoRenew`, who
 *      recorded `decision`, and when, all through the same hash-chained
 *      audit_log every other org.* mutation in this repo writes through
 *      (lib/audit-db.ts).
 *
 * Storage: one real k8s ConfigMap (`platform-contract-renewals`,
 * `platform-console` namespace), reusing the exact
 * get-then-create-or-patch primitive lib/k8s.ts's Feature Flags module
 * established (`getConfigMap`/`createOrUpdateConfigMap`) -- the same
 * primitive lib/budget-alerts.ts and lib/stripe-billing.ts already reuse
 * for their own ConfigMaps. No new k8s resource kind, no new RBAC verb:
 * the `platform-console-feature-flags` Role (k8s/paas-rbac.yaml) already
 * grants get/list/create/update/patch on `configmaps` in this namespace
 * with no `resourceNames` restriction, so it already covers this
 * ConfigMap with zero YAML changes.
 *
 * One `data` key per org, keyed by the org's own `id` (== tenant
 * namespace, the same identifier lib/stripe-billing.ts's
 * `StoredSubscription.tenantNamespace` already uses as its ConfigMap
 * key) -- never a second, independently-assigned id for the same org.
 *
 * `syncRenewalDateFromStripe` is the ONLY function that ever writes
 * `renewalDate` -- called from the real Stripe webhook receiver
 * (app/api/billing/stripe/webhook/route.ts) every time a
 * `customer.subscription.*` event lands, so the renewal date shown to
 * procurement is always re-derived from Stripe's own real
 * `current_period_end`, never a value this module invents. A renewal
 * date that genuinely changed (a real Stripe period rollover, or a
 * plan change moving the period boundary) resets `decision` back to
 * `"pending"` and clears `lastReminderSentAt` -- a past renewal/decline
 * decision was made about the PRIOR period's end date and does not
 * carry forward to a new one; a stale `lastReminderSentAt` from the
 * prior period must not suppress a reminder that is genuinely about a
 * new date.
 *
 * `scanContractRenewalReminders` is the daily reminder-scan job (invoked
 * from lib/webhook-poller.ts's existing tick, the same real
 * "scheduled job" primitive this console's other daily/periodic checks
 * -- lib/support-tickets.ts's SLA-breach scan, lib/cost-anomaly.ts's
 * anomaly scan -- already run on, rather than a second cron subsystem).
 * It finds every org where `renewalDate - now <= noticeThresholdDays`
 * AND `lastReminderSentAt` is stale (never sent, or sent >=
 * `REMINDER_RECHECK_HOURS` ago), and is the ONLY function that ever
 * writes `lastReminderSentAt` -- same single-writer-for-the-dedup-marker
 * discipline lib/budget-alerts.ts's `checkBudgets` documents for its own
 * `alerted.*` keys, so a dashboard page view can never itself suppress a
 * reminder the scan was about to record. No external email/webhook is
 * sent from here -- this repo's own convention (see
 * lib/support-tickets.ts's SLA-breach handling) is to log an auditable
 * event via lib/audit-db.ts and let the admin dashboard (GET
 * /api/contract-renewals) surface it, never a fabricated "email sent"
 * claim this module cannot back up.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const CONTRACT_RENEWALS_NAMESPACE = "platform-console";
export const CONTRACT_RENEWALS_CONFIGMAP = "platform-contract-renewals";

/** Default notice window for a newly-synced org with no prior record --
 * 30 days is the common enterprise SaaS "auto-renewal notice" contractual
 * term this capability exists to implement. An existing record's
 * operator-configured `noticeThresholdDays` is always preserved across a
 * resync (see `syncRenewalDateFromStripe`); this default only applies the
 * very first time an org's renewal date is ever synced. */
export const DEFAULT_NOTICE_THRESHOLD_DAYS = 30;

/** How stale `lastReminderSentAt` must be before `scanContractRenewalReminders`
 * will record another reminder for the same org while still inside the
 * notice window -- gives this in-process 10s-tick poller (see
 * lib/webhook-poller.ts) real once-per-day semantics without a second,
 * OS-level cron subsystem: an org inside its notice window gets exactly
 * one reminder recorded per real 24h period, not one per poll tick. */
export const REMINDER_RECHECK_HOURS = 24;

export type ContractRenewalDecision = "pending" | "renewed" | "declined";

export interface ContractRenewal {
  orgId: string;
  renewalDate: string; // ISO 8601 -- always the real Stripe current_period_end
  autoRenew: boolean;
  noticeThresholdDays: number;
  lastReminderSentAt: string | null;
  decision: ContractRenewalDecision;
  updatedAt: string;
  updatedBy: string;
}

/** GET /api/contract-renewals view model: the raw record plus the one
 * derived field an admin dashboard actually sorts/filters on. Computed
 * fresh on every read from `renewalDate`, never persisted (so it is
 * never stale relative to "now"). */
export interface ContractRenewalWithStatus extends ContractRenewal {
  daysUntilRenewal: number;
  inNoticeWindow: boolean;
}

function isDecision(value: unknown): value is ContractRenewalDecision {
  return value === "pending" || value === "renewed" || value === "declined";
}

function parseRenewal(orgId: string, raw: string): ContractRenewal | null {
  try {
    const p = JSON.parse(raw) as Partial<ContractRenewal>;
    if (
      typeof p.renewalDate === "string" &&
      typeof p.autoRenew === "boolean" &&
      typeof p.noticeThresholdDays === "number" &&
      Number.isFinite(p.noticeThresholdDays) &&
      (p.lastReminderSentAt === null || typeof p.lastReminderSentAt === "string") &&
      isDecision(p.decision) &&
      typeof p.updatedAt === "string" &&
      typeof p.updatedBy === "string"
    ) {
      return {
        orgId,
        renewalDate: p.renewalDate,
        autoRenew: p.autoRenew,
        noticeThresholdDays: p.noticeThresholdDays,
        lastReminderSentAt: p.lastReminderSentAt ?? null,
        decision: p.decision,
        updatedAt: p.updatedAt,
        updatedBy: p.updatedBy,
      };
    }
    return null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, ContractRenewal>>> {
  const cm = await getConfigMap(CONTRACT_RENEWALS_NAMESPACE, CONTRACT_RENEWALS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, ContractRenewal>();
  for (const [orgId, raw] of Object.entries(data)) {
    const parsed = parseRenewal(orgId, raw);
    if (parsed) out.set(orgId, parsed);
  }
  return { ok: true, data: out };
}

function withStatus(record: ContractRenewal, now: Date): ContractRenewalWithStatus {
  const renewalMs = Date.parse(record.renewalDate);
  const daysUntilRenewal = Number.isFinite(renewalMs)
    ? Math.ceil((renewalMs - now.getTime()) / (24 * 60 * 60 * 1000))
    : Number.POSITIVE_INFINITY;
  return {
    ...record,
    daysUntilRenewal,
    inNoticeWindow: daysUntilRenewal <= record.noticeThresholdDays,
  };
}

/**
 * Real list of every org with a synced renewal date, sorted by
 * days-until-renewal ascending (the org closest to churn risk first) --
 * exactly the admin-dashboard ordering GET /api/contract-renewals
 * promises. Read-only: never writes `lastReminderSentAt` (see this
 * module's header comment on why that write is scan-only).
 */
export async function listContractRenewals(): Promise<K8sResult<ContractRenewalWithStatus[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  const now = new Date();
  const rows = Array.from(all.data.values())
    .map((r) => withStatus(r, now))
    .sort((a, b) => a.daysUntilRenewal - b.daysUntilRenewal);
  return { ok: true, data: rows };
}

export async function getContractRenewal(
  orgId: string,
): Promise<K8sResult<ContractRenewalWithStatus | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  const record = all.data.get(orgId);
  return { ok: true, data: record ? withStatus(record, new Date()) : null };
}

/**
 * Real refresh of `renewalDate` from the Stripe subscription object's own
 * `current_period_end` -- called from the Stripe webhook receiver
 * (app/api/billing/stripe/webhook/route.ts) alongside its existing
 * applyStripeEvent/applyEntitlementEvent calls, every time a
 * `customer.subscription.*` event lands. `currentPeriodEnd: null` (e.g. a
 * canceled subscription with no future period) is a real no-op: there is
 * no future renewal date to track, so the existing record (if any) is
 * left untouched rather than being overwritten with a fabricated date.
 *
 * First-ever sync for an org creates a `pending`-decision record with
 * `autoRenew: true` and `noticeThresholdDays: DEFAULT_NOTICE_THRESHOLD_DAYS`
 * -- enterprise SaaS' own default posture (renew unless the customer
 * affirmatively declines), matching this repo's fail-open-on-continuity /
 * fail-closed-on-risk convention elsewhere. A resync that finds the SAME
 * renewalDate as before (e.g. a `customer.subscription.updated` event
 * that didn't move the period boundary) leaves `decision` and
 * `lastReminderSentAt` untouched -- an admin's prior decision about this
 * exact period, and any reminder already recorded about it, both still
 * apply. A resync that finds a genuinely DIFFERENT renewalDate (a real
 * period rollover or plan-change boundary move) resets `decision` back
 * to `"pending"` and clears `lastReminderSentAt`: the prior decision was
 * about the old period's end date, not this new one.
 */
export async function syncRenewalDateFromStripe(
  orgId: string,
  currentPeriodEnd: string | null,
): Promise<K8sResult<ContractRenewal | null>> {
  if (!currentPeriodEnd) return { ok: true, data: null };

  const all = await readAll();
  if (!all.ok) return all;
  const existing = all.data.get(orgId) ?? null;

  if (existing && existing.renewalDate === currentPeriodEnd) {
    // Same period boundary already on file -- nothing to write.
    return { ok: true, data: existing };
  }

  const now = new Date().toISOString();
  const record: ContractRenewal = existing
    ? {
        ...existing,
        renewalDate: currentPeriodEnd,
        decision: "pending",
        lastReminderSentAt: null,
        updatedAt: now,
        updatedBy: "system:stripe-webhook",
      }
    : {
        orgId,
        renewalDate: currentPeriodEnd,
        autoRenew: true,
        noticeThresholdDays: DEFAULT_NOTICE_THRESHOLD_DAYS,
        lastReminderSentAt: null,
        decision: "pending",
        updatedAt: now,
        updatedBy: "system:stripe-webhook",
      };

  const result = await createOrUpdateConfigMap(CONTRACT_RENEWALS_NAMESPACE, CONTRACT_RENEWALS_CONFIGMAP, {
    [orgId]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: record };
}

/**
 * Real admin decision write: `autoRenew`, `noticeThresholdDays`, and/or
 * `decision`, each independently optional (a partial update, matching
 * lib/orgs.ts's own setOrgSla/setOrgRegion single-field-update
 * convention) -- undefined fields keep their existing value. Fails
 * closed with `data: null` when no record exists yet for this org (no
 * Stripe subscription has ever synced a renewal date for it) rather than
 * fabricating one from admin input alone; POST /api/contract-renewals/
 * [orgId] surfaces that as 404. The caller (the route handler) is
 * responsible for the audit-log entry, same division of labor
 * lib/orgs.ts's own setters use -- this function only ever performs the
 * one real k8s write.
 */
export async function setContractRenewalPolicy(
  orgId: string,
  updates: {
    autoRenew?: boolean;
    noticeThresholdDays?: number;
    decision?: ContractRenewalDecision;
  },
  actor: string,
): Promise<K8sResult<ContractRenewal | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  const existing = all.data.get(orgId);
  if (!existing) return { ok: true, data: null };

  const record: ContractRenewal = {
    ...existing,
    autoRenew: updates.autoRenew ?? existing.autoRenew,
    noticeThresholdDays: updates.noticeThresholdDays ?? existing.noticeThresholdDays,
    decision: updates.decision ?? existing.decision,
    updatedAt: new Date().toISOString(),
    updatedBy: actor,
  };

  const result = await createOrUpdateConfigMap(CONTRACT_RENEWALS_NAMESPACE, CONTRACT_RENEWALS_CONFIGMAP, {
    [orgId]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: record };
}

/**
 * Real reminder record: {org, day} pair scanContractRenewalReminders just
 * marked, returned so the caller (lib/webhook-poller.ts) can write one
 * `contract.renewal_reminder_sent` audit-db.ts entry per org -- matching
 * this repo's audit-log-not-external-email convention (see
 * lib/support-tickets.ts's SLA-breach handling) rather than this module
 * reaching into lib/audit-db.ts itself, the same separation-of-concerns
 * lib/budget-alerts.ts's `checkBudgets` (data-layer detection) /
 * lib/webhook-poller.ts's `pollBudgetThresholds` (delivery/audit side
 * effects) already establishes.
 */
export interface ContractRenewalReminder {
  orgId: string;
  renewalDate: string;
  daysUntilRenewal: number;
  noticeThresholdDays: number;
  autoRenew: boolean;
  decision: ContractRenewalDecision;
}

/**
 * Real daily reminder scan -- see this module's header comment for the
 * full single-writer / staleness contract. Finds every org where
 * `renewalDate - now <= noticeThresholdDays` (real days-until-renewal,
 * via `withStatus`'s own `daysUntilRenewal`/`inNoticeWindow` computation
 * -- the exact same arithmetic `listContractRenewals` exposes to the
 * dashboard, never a second definition of "in the notice window") AND
 * `lastReminderSentAt` is stale (`null`, or older than
 * `REMINDER_RECHECK_HOURS`), writes a fresh `lastReminderSentAt` for
 * each, and returns exactly the set that was just marked -- the set the
 * caller should audit-log. An org whose contract already has a final
 * `decision` ("renewed" or "declined") is skipped: the decision trail
 * this capability exists to produce is already complete for it, and a
 * reminder about a decision already made would be noise, not signal.
 */
export async function scanContractRenewalReminders(): Promise<K8sResult<ContractRenewalReminder[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  if (all.data.size === 0) return { ok: true, data: [] };

  const now = new Date();
  const patch: Record<string, string> = {};
  const reminders: ContractRenewalReminder[] = [];

  for (const record of all.data.values()) {
    if (record.decision !== "pending") continue;
    const status = withStatus(record, now);
    if (!status.inNoticeWindow) continue;

    const lastSentMs = record.lastReminderSentAt ? Date.parse(record.lastReminderSentAt) : NaN;
    const stale =
      !Number.isFinite(lastSentMs) || now.getTime() - lastSentMs >= REMINDER_RECHECK_HOURS * 60 * 60 * 1000;
    if (!stale) continue;

    const updated: ContractRenewal = {
      ...record,
      lastReminderSentAt: now.toISOString(),
    };
    patch[record.orgId] = JSON.stringify(updated);
    reminders.push({
      orgId: record.orgId,
      renewalDate: record.renewalDate,
      daysUntilRenewal: status.daysUntilRenewal,
      noticeThresholdDays: record.noticeThresholdDays,
      autoRenew: record.autoRenew,
      decision: record.decision,
    });
  }

  if (Object.keys(patch).length > 0) {
    const result = await createOrUpdateConfigMap(CONTRACT_RENEWALS_NAMESPACE, CONTRACT_RENEWALS_CONFIGMAP, patch);
    if (!result.ok) return result;
  }

  return { ok: true, data: reminders };
}
