/**
 * Real, durable Law-Enforcement / Government Data Request Register
 * (transparency log) -- the specific control Fortune 5 legal/privacy
 * teams ask for by name before signing an enterprise DPA: a logged,
 * auditable record of every subpoena, warrant, court order, or other
 * government/law-enforcement demand for customer data this platform
 * received, and exactly how it was handled, exportable for regulatory
 * and customer-trust review. This module is the register itself; the
 * public aggregate counts a buyer sees pre-signature live in
 * lib/trust-page.ts, sourced from `summarizeLeRequestsForTrustPage`
 * below -- never the underlying per-request detail, which stays behind
 * session auth (see app/api/owner/le-requests/route.ts's own header
 * comment for why).
 *
 * Storage: one real k8s ConfigMap (`platform-console-le-requests`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch
 * primitive lib/dsar.ts/lib/approval-workflow.ts/lib/subprocessors.ts
 * already use -- no new k8s resource kind. Key = requestId
 * (`crypto.randomUUID()`, already legal as a ConfigMap data key), same
 * convention lib/dsar.ts's DSAR_CONFIGMAP uses.
 *
 * Two distinct write paths, same "ingest vs. act" split
 * lib/dsar.ts/lib/subprocessors.ts already establish elsewhere in this
 * repo:
 *   - Logging that a request was RECEIVED (POST
 *     /api/internal/le-requests) is never itself the sensitive action --
 *     it is the transparency-log control existing FOR ITS OWN SAKE, so it
 *     is intentionally NOT gated behind maker-checker (an unlogged
 *     government request would defeat the entire point of a register that
 *     is supposed to be complete). It IS gated behind the same
 *     shared-secret-header pattern every other unattended
 *     app/api/internal/* route uses (see that route's own header
 *     comment), since the legal team's own intake tooling -- not a
 *     browser session -- is the expected caller.
 *   - Recording this platform's DISCLOSURE/RESPONSE decision (PUT
 *     /api/owner/le-requests, session-authed) IS the sensitive,
 *     state-mutating action -- it is the one place a single compromised
 *     or coerced employee could quietly hand over customer data (or
 *     quietly under-report having done so) -- so it goes through the
 *     SAME maker-checker two-person-integrity bar
 *     `subprocessor.registry.update`/`dsar.erasure` already set: one
 *     owner's own say-so is never sufficient by itself to mark a request
 *     as "data disclosed".
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const LE_REQUESTS_NAMESPACE = "platform-console";
export const LE_REQUESTS_CONFIGMAP = "platform-console-le-requests";

export type LeRequestType = "subpoena" | "warrant" | "court_order" | "national_security_letter" | "other";
export type LeRequestStatus = "received" | "under_review" | "disclosed" | "narrowed" | "objected" | "rejected";

/**
 * requestingAuthority/jurisdiction are the specific fields a regulatory
 * or customer-trust reviewer (and this register's own public transparency-
 * report rollup) actually needs -- WHO asked, and under which
 * jurisdiction's legal process -- without ever requiring the underlying
 * subject data itself to be entered here (this register logs the demand
 * and the platform's response to it, never a copy of the disclosed data).
 */
export interface LeRequest {
  requestId: string;
  requestType: LeRequestType;
  requestingAuthority: string;
  jurisdiction: string;
  /** The government's own case/docket/subpoena reference number, if given. */
  referenceNumber?: string;
  /** Org this request names, when it resolves to one of this platform's
   * own orgs -- absent for a request that is still ambiguous/unresolved
   * at intake time (never fabricated). */
  orgId?: string;
  /** Free-text, non-PII summary of what data/records were demanded --
   * deliberately a summary, never the raw legal document text, so this
   * register itself never becomes a second place the underlying
   * subject's personal data lives. */
  summary: string;
  receivedAt: string;
  /** Who/what logged the intake -- an intake-tooling identifier for the
   * shared-secret ingest path, or the session actor for a rare
   * owner-filed manual entry. */
  loggedBy: string;
  status: LeRequestStatus;
  /** Set once a disclosure/response decision has been recorded via the
   * maker-checker-gated PUT route. */
  respondedBy?: string;
  respondedAt?: string;
  responseSummary?: string;
  /** True only once a real maker-checker approval
   * (`le-request.respond`) has actually been granted for this exact
   * response -- never client-asserted, always derived from
   * lib/approval-workflow.ts's own stored decision. */
  requiredApproval?: boolean;
  approvedBy?: string;
}

function isLeRequestType(value: unknown): value is LeRequestType {
  return (
    value === "subpoena" ||
    value === "warrant" ||
    value === "court_order" ||
    value === "national_security_letter" ||
    value === "other"
  );
}

function isLeRequestStatus(value: unknown): value is LeRequestStatus {
  return (
    value === "received" ||
    value === "under_review" ||
    value === "disclosed" ||
    value === "narrowed" ||
    value === "objected" ||
    value === "rejected"
  );
}

function isLeRequest(value: unknown): value is LeRequest {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.requestId === "string" &&
    isLeRequestType(v.requestType) &&
    typeof v.requestingAuthority === "string" &&
    typeof v.jurisdiction === "string" &&
    typeof v.summary === "string" &&
    typeof v.receivedAt === "string" &&
    typeof v.loggedBy === "string" &&
    isLeRequestStatus(v.status)
  );
}

async function getAll(): Promise<K8sResult<Record<string, LeRequest>>> {
  const existing = await getConfigMap(LE_REQUESTS_NAMESPACE, LE_REQUESTS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, LeRequest> = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      if (isLeRequest(row)) parsed[key] = row;
      // A hand-edited or corrupt row is skipped, not fatal -- same
      // discipline lib/dsar.ts's/lib/approval-workflow.ts's getAll use.
    } catch {
      // ignore -- malformed JSON for this key
    }
  }
  return { ok: true, data: parsed };
}

async function putRequest(request: LeRequest): Promise<K8sResult<LeRequest>> {
  const result = await createOrUpdateConfigMap(LE_REQUESTS_NAMESPACE, LE_REQUESTS_CONFIGMAP, {
    [request.requestId]: JSON.stringify(request),
  });
  if (!result.ok) return result;
  return { ok: true, data: request };
}

export async function listLeRequests(orgId?: string): Promise<K8sResult<LeRequest[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  const rows = Object.values(all.data)
    .filter((r) => !orgId || r.orgId === orgId)
    .sort((a, b) => b.receivedAt.localeCompare(a.receivedAt));
  return { ok: true, data: rows };
}

export async function getLeRequest(requestId: string): Promise<K8sResult<LeRequest | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data[requestId] ?? null };
}

/**
 * Logs one real, immutable-at-intake entry into the register. Called by
 * POST /api/internal/le-requests (the legal team's own shared-secret
 * intake tooling) -- never gated behind maker-checker (see this module's
 * header comment for why logging receipt is deliberately not the
 * sensitive action here).
 */
export async function logLeRequest(input: {
  requestType: LeRequestType;
  requestingAuthority: string;
  jurisdiction: string;
  referenceNumber?: string;
  orgId?: string;
  summary: string;
  loggedBy: string;
}): Promise<K8sResult<LeRequest>> {
  const request: LeRequest = {
    requestId: globalThis.crypto.randomUUID(),
    requestType: input.requestType,
    requestingAuthority: input.requestingAuthority,
    jurisdiction: input.jurisdiction,
    ...(input.referenceNumber ? { referenceNumber: input.referenceNumber } : {}),
    ...(input.orgId ? { orgId: input.orgId } : {}),
    summary: input.summary,
    receivedAt: new Date().toISOString(),
    loggedBy: input.loggedBy,
    status: "received",
  };
  return putRequest(request);
}

export type RecordResponseError = "not_found" | "already_responded";

/**
 * Records this platform's real disclosure/response decision for a
 * request already in the register -- called only from PUT
 * /api/owner/le-requests immediately after a fresh maker-checker
 * `le-request.respond` approval is confirmed (never before). Refuses a
 * second response on an already-`disclosed`/`rejected`/`narrowed`/
 * `objected` row -- a response is recorded exactly once, never silently
 * overwritten, same "decide once" discipline
 * lib/approval-workflow.ts's recordApprovalDecision already applies to
 * its own rows.
 */
export async function recordLeRequestResponse(input: {
  requestId: string;
  status: Extract<LeRequestStatus, "disclosed" | "narrowed" | "objected" | "rejected">;
  responseSummary: string;
  respondedBy: string;
  approvedBy: string;
}): Promise<K8sResult<LeRequest> | { ok: false; error: RecordResponseError }> {
  const existing = await getLeRequest(input.requestId);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "not_found" };
  if (existing.data.status !== "received" && existing.data.status !== "under_review") {
    return { ok: false, error: "already_responded" };
  }

  const updated: LeRequest = {
    ...existing.data,
    status: input.status,
    respondedBy: input.respondedBy,
    respondedAt: new Date().toISOString(),
    responseSummary: input.responseSummary,
    requiredApproval: true,
    approvedBy: input.approvedBy,
  };
  return putRequest(updated);
}

/**
 * Marks a request "under_review" -- a real, non-sensitive status
 * transition (no disclosure decision made yet) legal/privacy staff use
 * to signal active triage, so it is not gated behind maker-checker
 * either, same "logging progress is not the sensitive action" boundary
 * `logLeRequest` documents. Refuses to move a request already past
 * `received`/`under_review` (a final response is never silently
 * reopened via this path).
 */
export async function markLeRequestUnderReview(
  requestId: string,
): Promise<K8sResult<LeRequest> | { ok: false; error: RecordResponseError }> {
  const existing = await getLeRequest(requestId);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "not_found" };
  if (existing.data.status !== "received" && existing.data.status !== "under_review") {
    return { ok: false, error: "already_responded" };
  }
  return putRequest({ ...existing.data, status: "under_review" });
}

/**
 * Public, aggregate-only transparency-report rollup for
 * lib/trust-page.ts -- counts by request type and by real response
 * status, and a total, NEVER any per-request field (requestingAuthority,
 * jurisdiction, orgId, summary) -- same "aggregate counts only on the
 * public surface" discipline lib/trust-page.ts's own header comment
 * already documents for vuln/cert posture. A source that is genuinely
 * unreachable reports `reachable: false`, never a fabricated all-zero
 * report.
 */
export interface LeTransparencyReport {
  reachable: boolean;
  error: string | null;
  totalRequests: number;
  byType: Record<LeRequestType, number>;
  byStatus: Record<LeRequestStatus, number>;
  disclosedCount: number;
  rejectedOrObjectedCount: number;
}

function emptyByType(): Record<LeRequestType, number> {
  return { subpoena: 0, warrant: 0, court_order: 0, national_security_letter: 0, other: 0 };
}

function emptyByStatus(): Record<LeRequestStatus, number> {
  return { received: 0, under_review: 0, disclosed: 0, narrowed: 0, objected: 0, rejected: 0 };
}

export async function summarizeLeRequestsForTrustPage(): Promise<LeTransparencyReport> {
  const all = await listLeRequests();
  if (!all.ok) {
    return {
      reachable: false,
      error: all.error,
      totalRequests: 0,
      byType: emptyByType(),
      byStatus: emptyByStatus(),
      disclosedCount: 0,
      rejectedOrObjectedCount: 0,
    };
  }

  const byType = emptyByType();
  const byStatus = emptyByStatus();
  for (const request of all.data) {
    byType[request.requestType] += 1;
    byStatus[request.status] += 1;
  }

  return {
    reachable: true,
    error: null,
    totalRequests: all.data.length,
    byType,
    byStatus,
    disclosedCount: byStatus.disclosed,
    rejectedOrObjectedCount: byStatus.rejected + byStatus.objected,
  };
}
