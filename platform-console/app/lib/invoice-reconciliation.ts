/**
 * Real Invoice / Purchase-Order Reconciliation Ledger: closes the gap
 * between two capabilities this codebase already has and never joined --
 * lib/overage-billing.ts's real, Stripe-billed usage overage
 * (`StoredOverage.overageCostUsd`, computed from real Prometheus-derived
 * consumption) and lib/contract-renewals.ts's real Stripe-derived
 * contract period. Neither module has ever known the customer's own
 * procurement-side reference (a PO number) or the dollar cap their signed
 * contract actually authorizes for a billing period -- today that
 * reconciliation happens off-platform, in a spreadsheet finance/
 * procurement keeps by hand, with no auditable link back to the real
 * overage number this console already computed. This module IS that
 * link: it reads the real `StoredOverage` for an org's namespace, takes
 * the customer's submitted PO number + asserted contract cap, computes a
 * real signed variance, and produces a durable, auditable reconciliation
 * record finance/procurement can point to when approving (or declining)
 * payment.
 *
 * Storage: one real k8s ConfigMap (`platform-invoice-reconciliation`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo (lib/approval-
 * workflow.ts, lib/contract-renewals.ts, lib/budget-alerts.ts) already
 * uses -- no new k8s resource kind, no new RBAC verb: the same
 * `platform-console-feature-flags` Role already grants get/list/create/
 * update/patch on `configmaps` in this namespace with no `resourceNames`
 * restriction.
 *
 * Key shape: one key per reconciliation record, `<orgId>.<periodStart>`
 * (periodStart is the real StoredOverage window this record reconciled
 * against -- see lib/overage-billing.ts's own header comment on why that
 * value, not a fabricated calendar-period anchor, is the real period
 * identity). A k8s ConfigMap `data` key must match `[-._a-zA-Z0-9]+`; an
 * org id (already namespace-safe, see lib/orgs.ts) and an ISO timestamp
 * (colons replaced with `-`, the same escaping discipline
 * lib/authz.ts's encodeIdentifierKey documents for its own key material)
 * both satisfy that with no further escaping needed.
 *
 * Two-person integrity for approval is the SAME maker-checker primitive
 * `pricing.override`/`sla.credit.apply` already use
 * (lib/approval-workflow.ts's requireApproval /
 * recordApprovalDecision): filing a reconciliation (`recordInvoiceReconciliation`,
 * called from POST /api/orgs/[id]/invoice-reconciliation) never itself
 * authorizes payment -- it only computes and stores the real numbers. A
 * SEPARATE, distinct owner-role approver must sign off
 * (`invoice.reconciliation.approve`) before `decideInvoiceReconciliation`
 * ever marks a record `"approved_for_payment"`. Every state-mutating call
 * this module makes is also durably audit-logged
 * (`writeAuditLogEntryAwaited`, awaited not fire-and-forget -- a
 * reconciliation's whole purpose is to be provable at audit time, so the
 * durable row must exist before the call returns), same discipline
 * lib/orgs.ts's setOrgPricingOverride establishes for the same class of
 * money-moving action.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getStoredOverage, type StoredOverage } from "@/lib/overage-billing";
import { newRequestId, writeAuditLogEntryAwaited } from "@/lib/audit-db";

export const INVOICE_RECONCILIATION_NAMESPACE = "platform-console";
export const INVOICE_RECONCILIATION_CONFIGMAP = "platform-invoice-reconciliation";

export type InvoiceReconciliationStatus =
  | "pending_review"
  | "pending_approval"
  | "approved_for_payment"
  | "rejected";

export interface InvoiceReconciliation {
  id: string; // `<orgId>.<periodStart-with-colons-replaced>`
  orgId: string;
  namespace: string;
  poNumber: string;
  contractCapUsd: number;
  /** Real overage amount reconciled against -- lib/overage-billing.ts's
   * own StoredOverage.overageCostUsd for this exact periodStart, never a
   * fabricated or re-derived number. `null` when no overage has ever been
   * computed for this namespace yet (the reconciliation still records the
   * customer's PO/cap submission, with a $0 overage baseline). */
  overageCostUsd: number;
  /** overageCostUsd - contractCapUsd. Positive means the customer was
   * billed more than their asserted contract cap covers (the case that
   * actually needs a human financial decision); zero or negative means
   * the real overage stayed within the customer's own asserted cap. */
  varianceUsd: number;
  /** The real StoredOverage.periodStart this record reconciled against --
   * see lib/overage-billing.ts's header comment: a real trailing-window
   * start, not a fabricated calendar-period anchor. */
  periodStart: string;
  status: InvoiceReconciliationStatus;
  filedBy: string;
  filedAt: string;
  decidedBy?: string;
  decidedAt?: string;
  decisionReason?: string;
}

function reconciliationKey(orgId: string, periodStart: string): string {
  // k8s ConfigMap data keys must match [-._a-zA-Z0-9]+ -- an ISO
  // timestamp's colons are the only character that violates that, so
  // this is the entire escaping step required (mirrors
  // lib/authz.ts's encodeIdentifierKey discipline of "escape exactly the
  // characters the k8s key-charset regex forbids, nothing more").
  return `${orgId}.${periodStart.replace(/:/g, "-")}`;
}

function isStatus(value: unknown): value is InvoiceReconciliationStatus {
  return (
    value === "pending_review" ||
    value === "pending_approval" ||
    value === "approved_for_payment" ||
    value === "rejected"
  );
}

function parseRecord(raw: string): InvoiceReconciliation | null {
  try {
    const p = JSON.parse(raw) as Partial<InvoiceReconciliation>;
    if (
      typeof p.id === "string" &&
      typeof p.orgId === "string" &&
      typeof p.namespace === "string" &&
      typeof p.poNumber === "string" &&
      typeof p.contractCapUsd === "number" &&
      typeof p.overageCostUsd === "number" &&
      typeof p.varianceUsd === "number" &&
      typeof p.periodStart === "string" &&
      isStatus(p.status) &&
      typeof p.filedBy === "string" &&
      typeof p.filedAt === "string"
    ) {
      return {
        id: p.id,
        orgId: p.orgId,
        namespace: p.namespace,
        poNumber: p.poNumber,
        contractCapUsd: p.contractCapUsd,
        overageCostUsd: p.overageCostUsd,
        varianceUsd: p.varianceUsd,
        periodStart: p.periodStart,
        status: p.status,
        filedBy: p.filedBy,
        filedAt: p.filedAt,
        decidedBy: typeof p.decidedBy === "string" ? p.decidedBy : undefined,
        decidedAt: typeof p.decidedAt === "string" ? p.decidedAt : undefined,
        decisionReason: typeof p.decisionReason === "string" ? p.decisionReason : undefined,
      };
    }
    return null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, InvoiceReconciliation>>> {
  const cm = await getConfigMap(INVOICE_RECONCILIATION_NAMESPACE, INVOICE_RECONCILIATION_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, InvoiceReconciliation>();
  for (const [key, raw] of Object.entries(data)) {
    const parsed = parseRecord(raw);
    // A hand-edited or corrupt row is skipped, not fatal -- same
    // "don't let one bad row break the whole list" discipline
    // lib/approval-workflow.ts's getAll / lib/orgs.ts's getRegistry use.
    if (parsed) out.set(key, parsed);
  }
  return { ok: true, data: out };
}

/**
 * Real list of every reconciliation record for one org, most recently
 * filed first -- backs GET /api/orgs/[id]/invoice-reconciliation.
 */
export async function listInvoiceReconciliations(
  orgId: string,
): Promise<K8sResult<InvoiceReconciliation[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  const rows = Array.from(all.data.values())
    .filter((r) => r.orgId === orgId)
    .sort((a, b) => b.filedAt.localeCompare(a.filedAt));
  return { ok: true, data: rows };
}

export async function getInvoiceReconciliation(
  id: string,
): Promise<K8sResult<InvoiceReconciliation | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(id) ?? null };
}

/**
 * Fail-closed validation -- same discipline as lib/orgs.ts's
 * validatePricingOverride: reject and return a real, specific error
 * string (never a fabricated silent default/clamp) on anything that
 * doesn't meet the contract, so a bad reconciliation row can never reach
 * the ConfigMap or a pending approval.
 */
export function validateInvoiceReconciliationInput(input: {
  poNumber: string;
  contractCapUsd: number;
}): string | null {
  if (!input.poNumber.trim()) {
    return "poNumber is required";
  }
  if (!Number.isFinite(input.contractCapUsd) || input.contractCapUsd < 0) {
    return "contractCapUsd must be a finite number >= 0";
  }
  return null;
}

/**
 * Real reconciliation: reads the real StoredOverage for `namespace`
 * (lib/overage-billing.ts's getStoredOverage -- never a fabricated
 * number) and files ONE new record comparing it against the customer's
 * submitted `poNumber`/`contractCapUsd`. Filing a record is itself never
 * a money-moving action -- it only computes and durably stores the real
 * numbers a second approver will review -- so this function requires no
 * approval gate of its own; the caller (POST /api/orgs/[id]/invoice-
 * reconciliation) is responsible only for the "member and up" role floor
 * every other mutating route in this console requires. `status` starts
 * `"pending_review"` when the real overage stayed within the asserted
 * cap (varianceUsd <= 0 -- nothing for finance to authorize) or
 * `"pending_approval"` when it didn't (varianceUsd > 0 -- a real
 * over-cap amount that needs the maker-checker sign-off
 * decideInvoiceReconciliation enforces).
 */
export async function recordInvoiceReconciliation(input: {
  orgId: string;
  namespace: string;
  poNumber: string;
  contractCapUsd: number;
  filedBy: string;
}): Promise<K8sResult<InvoiceReconciliation>> {
  const overageResult: K8sResult<StoredOverage | null> = await getStoredOverage(input.namespace);
  if (!overageResult.ok) return overageResult;

  const overageCostUsd = overageResult.data?.overageCostUsd ?? 0;
  const periodStart = overageResult.data?.periodStart ?? new Date().toISOString();
  const varianceUsd = Number((overageCostUsd - input.contractCapUsd).toFixed(2));

  const record: InvoiceReconciliation = {
    id: reconciliationKey(input.orgId, periodStart),
    orgId: input.orgId,
    namespace: input.namespace,
    poNumber: input.poNumber.trim(),
    contractCapUsd: input.contractCapUsd,
    overageCostUsd,
    varianceUsd,
    periodStart,
    status: varianceUsd > 0 ? "pending_approval" : "pending_review",
    filedBy: input.filedBy,
    filedAt: new Date().toISOString(),
  };

  const result = await createOrUpdateConfigMap(
    INVOICE_RECONCILIATION_NAMESPACE,
    INVOICE_RECONCILIATION_CONFIGMAP,
    { [record.id]: JSON.stringify(record) },
  );
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    orgId: input.orgId,
    timestamp: new Date().toISOString(),
    actor: input.filedBy,
    method: "POST",
    path: `/api/orgs/${input.orgId}/invoice-reconciliation`,
    status: 201,
    requestId: newRequestId(),
    reconciliationAction: "filed",
    reconciliationPoNumber: record.poNumber,
    reconciliationVarianceUsd: record.varianceUsd,
  });

  return { ok: true, data: record };
}

export type DecideInvoiceReconciliationError = "not_found" | "not_decidable";

/**
 * Real approve/reject decision write: backs PUT /api/orgs/[id]/invoice-
 * reconciliation. Callers (the route handler) MUST gate this behind a
 * fresh `invoice.reconciliation.approve` approval
 * (lib/approval-workflow.ts's requireApproval, same maker-checker
 * primitive `pricing.override` already uses) before ever calling this
 * with `decision: "approved"` -- this function itself performs no
 * approval check, same "module exposes the setter, the route decides who
 * may call it" division of labor as lib/orgs.ts's setOrgPricingOverride.
 * Refuses (`"not_decidable"`) a record that is not currently
 * `"pending_approval"` -- a decision is recorded exactly once, never
 * silently overwritten, same discipline lib/approval-workflow.ts's
 * recordApprovalDecision already enforces for the approval row itself.
 * Because this action authorizes a real invoiced dollar amount for
 * payment, every decision is durably audit-logged
 * (writeAuditLogEntryAwaited) here, distinct from the route's own
 * per-request access-log entry -- same "the setter, not just the route,
 * writes the durable financial-action row" discipline
 * lib/orgs.ts's setOrgPricingOverride establishes.
 */
export async function decideInvoiceReconciliation(input: {
  id: string;
  decision: "approved_for_payment" | "rejected";
  decidedBy: string;
  reason?: string;
}): Promise<K8sResult<InvoiceReconciliation> | { ok: false; error: DecideInvoiceReconciliationError }> {
  const existing = await getInvoiceReconciliation(input.id);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "not_found" };
  if (existing.data.status !== "pending_approval") return { ok: false, error: "not_decidable" };

  const updated: InvoiceReconciliation = {
    ...existing.data,
    status: input.decision,
    decidedBy: input.decidedBy,
    decidedAt: new Date().toISOString(),
    decisionReason: input.reason,
  };

  const result = await createOrUpdateConfigMap(
    INVOICE_RECONCILIATION_NAMESPACE,
    INVOICE_RECONCILIATION_CONFIGMAP,
    { [updated.id]: JSON.stringify(updated) },
  );
  if (!result.ok) return result;

  await writeAuditLogEntryAwaited({
    orgId: updated.orgId,
    timestamp: new Date().toISOString(),
    actor: input.decidedBy,
    method: "PUT",
    path: `/api/orgs/${updated.orgId}/invoice-reconciliation`,
    status: 200,
    requestId: newRequestId(),
    reconciliationAction: input.decision === "approved_for_payment" ? "approved_for_payment" : "rejected",
    reconciliationPoNumber: updated.poNumber,
    reconciliationVarianceUsd: updated.varianceUsd,
  });

  return { ok: true, data: updated };
}
