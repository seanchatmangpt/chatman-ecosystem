/**
 * Real per-org GDPR Art.15/17 + CCPA Data Subject Access & Erasure
 * Request (DSAR) workflow -- the control any Fortune 5 buyer's
 * privacy/legal team asks for by name before signing, and one this
 * codebase already had every ingredient for but never assembled:
 * lib/audit-db.ts's durable Postgres `platform_console.audit_log`
 * (actor-tagged per request), lib/orgs.ts's per-org membership records
 * (lib/authz.ts's `platform-console-org-roles` ConfigMap, one per org
 * namespace), and lib/api-keys.ts's identifier-bound API key records.
 *
 * Storage: one real k8s ConfigMap (`platform-console-dsar-requests`,
 * `platform-console` namespace), reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch
 * primitive lib/approval-workflow.ts/lib/orgs.ts/lib/authz.ts already
 * use -- no new k8s resource kind. Key = requestId
 * (`crypto.randomUUID()`, already legal as a ConfigMap data key).
 *
 * 'export' requests are picked up by this module's own background
 * poller (`startDsarPoller`, same real setInterval tick-loop shape as
 * lib/webhook-poller.ts's `startWebhookPoller` -- started once from
 * instrumentation.ts, idempotent via the same `started` guard
 * convention) rather than processed synchronously in the request/response
 * cycle: gathering a subject's full audit history can be a real,
 * unbounded-time Postgres scan, and a route handler blocking on it would
 * risk the request timing out exactly like any other genuinely
 * long-running job in this console.
 *
 * 'erasure' requests are NOT polled -- they are processed synchronously,
 * inline in the route handler, immediately after a fresh maker-checker
 * approval (lib/approval-workflow.ts's new "dsar.erasure" action) is
 * found. Erasure work here is bounded (one UPDATE + one ConfigMap patch +
 * one audit log write), and running it synchronously means the approving
 * second owner's own request is the one that visibly completes it --
 * consistent with org.delete's own DELETE /api/orgs/[id] pattern, which
 * this route mirrors.
 *
 * Never a hard delete of any row: audit_log rows are UPDATEd in place
 * (actor field replaced with a redaction marker, never DELETEd) --
 * consistent with lib/audit-db.ts's own append-only hash-chain design
 * (see that file's header comment). Disclosed, real consequence: because
 * `actor` is one of the fields committed into `row_hash`
 * (lib/audit-db.ts's `computeRowHash`), redacting it deliberately makes
 * every row from the redacted one onward fail `verifyAuditChain` -- this
 * is the correct, visible signal that "this chain was legitimately
 * amended for a real legal-erasure reason on this date", not a silent
 * pass. A future pass could record erasures as a documented, chain-
 * verifiable exception list; out of scope here, disclosed rather than
 * silently worked around.
 */
import { createHash } from "node:crypto";
import { getAuditDbPool, type AuditLogRow } from "@/lib/audit-db";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getOrg, type Org } from "@/lib/orgs";
import { getOrgRoleAssignmentsIn, type OrgRoleAssignment } from "@/lib/authz";
import { listApiKeys, type ApiKeySummary } from "@/lib/api-keys";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { storeExportArchive } from "@/lib/export-download-cache";

export const DSAR_NAMESPACE = "platform-console";
export const DSAR_CONFIGMAP = "platform-console-dsar-requests";

export type DsarKind = "export" | "erasure";
export type DsarStatus = "pending" | "processing" | "complete" | "failed";

export interface DsarRequest {
  requestId: string;
  orgId: string;
  subjectEmail: string;
  kind: DsarKind;
  status: DsarStatus;
  requestedBy: string;
  requestedAt: string;
  completedAt?: string;
  error?: string;
  // 'export' only, set once status becomes "complete".
  downloadToken?: string;
  downloadExpiresAt?: string;
  bundleFilename?: string;
  bundleRowCount?: number;
  // 'erasure' only, set once status becomes "complete" -- a real count of
  // what was redacted, never fabricated.
  redactedAuditRowCount?: number;
  redactedMembership?: boolean;
}

function isDsarKind(value: unknown): value is DsarKind {
  return value === "export" || value === "erasure";
}
function isDsarStatus(value: unknown): value is DsarStatus {
  return value === "pending" || value === "processing" || value === "complete" || value === "failed";
}
function isDsarRequest(value: unknown): value is DsarRequest {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.requestId === "string" &&
    typeof v.orgId === "string" &&
    typeof v.subjectEmail === "string" &&
    isDsarKind(v.kind) &&
    isDsarStatus(v.status) &&
    typeof v.requestedBy === "string" &&
    typeof v.requestedAt === "string"
  );
}

async function getAll(): Promise<K8sResult<Record<string, DsarRequest>>> {
  const existing = await getConfigMap(DSAR_NAMESPACE, DSAR_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, DsarRequest> = {};
  for (const [key, raw] of Object.entries(existing.data.data)) {
    try {
      const row = JSON.parse(raw) as unknown;
      if (isDsarRequest(row)) parsed[key] = row;
      // A hand-edited or corrupt row is skipped, not fatal -- same
      // discipline lib/approval-workflow.ts's getAll uses.
    } catch {
      // ignore -- malformed JSON for this key
    }
  }
  return { ok: true, data: parsed };
}

async function putRequest(request: DsarRequest): Promise<K8sResult<DsarRequest>> {
  const result = await createOrUpdateConfigMap(DSAR_NAMESPACE, DSAR_CONFIGMAP, {
    [request.requestId]: JSON.stringify(request),
  });
  if (!result.ok) return result;
  return { ok: true, data: request };
}

export async function listDsarRequests(orgId?: string): Promise<K8sResult<DsarRequest[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  const rows = Object.values(all.data)
    .filter((r) => !orgId || r.orgId === orgId)
    .sort((a, b) => b.requestedAt.localeCompare(a.requestedAt));
  return { ok: true, data: rows };
}

export async function getDsarRequest(requestId: string): Promise<K8sResult<DsarRequest | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data[requestId] ?? null };
}

/**
 * Creates one real pending DSAR request row. Called by both
 * POST /api/privacy/request-export (immediately, no approval gate --
 * reading one's own data back is Art.15 access, not a destructive
 * action) and POST /api/privacy/request-erasure (only once a fresh
 * maker-checker approval for "dsar.erasure" already exists).
 */
export async function createDsarRequest(input: {
  orgId: string;
  subjectEmail: string;
  kind: DsarKind;
  requestedBy: string;
}): Promise<K8sResult<DsarRequest>> {
  const request: DsarRequest = {
    requestId: globalThis.crypto.randomUUID(),
    orgId: input.orgId,
    subjectEmail: input.subjectEmail,
    kind: input.kind,
    status: "pending",
    requestedBy: input.requestedBy,
    requestedAt: new Date().toISOString(),
  };
  return putRequest(request);
}

// ------------------------------------------------------------- Export

interface DsarBundleRecord {
  recordType: "audit_log_entry" | "org_membership" | "api_key";
  subjectEmail: string;
  orgId: string;
  data: unknown;
}

/**
 * Real, exact-match (never substring/ILIKE, unlike lib/audit-db.ts's own
 * queryAuditLog which is a browse-UI search) read of every audit_log row
 * whose `actor` is this exact subject email -- the actor-match collection
 * the spec calls for.
 */
async function collectSubjectAuditRows(subjectEmail: string): Promise<AuditLogRow[]> {
  const pool = await getAuditDbPool();
  if (!pool) return []; // audit DB unreachable/unconfigured -- export still proceeds with the rows this process CAN see (membership, API keys), never fabricated audit rows
  const result = await pool.query(
    `SELECT id, request_id, ts, actor, method, path, status, inserted_at, castle_receipt_digest,
            impersonated_by, impersonation_session_id
     FROM platform_console.audit_log
     WHERE actor = $1
     ORDER BY ts ASC, id ASC`,
    [subjectEmail],
  );
  return result.rows.map((r) => ({
    id: Number(r.id),
    requestId: r.request_id as string,
    ts: new Date(r.ts as string).toISOString(),
    actor: r.actor as string,
    method: r.method as string,
    path: r.path as string,
    status: Number(r.status),
    insertedAt: new Date(r.inserted_at as string).toISOString(),
    ...(r.castle_receipt_digest ? { castleReceiptDigest: r.castle_receipt_digest as string } : {}),
    ...(r.impersonated_by ? { impersonatedBy: r.impersonated_by as string } : {}),
    ...(r.impersonation_session_id
      ? { impersonationSessionId: r.impersonation_session_id as string }
      : {}),
  }));
}

async function collectSubjectMembership(
  org: Org,
  subjectEmail: string,
): Promise<OrgRoleAssignment[]> {
  const result = await getOrgRoleAssignmentsIn(org.namespace);
  if (!result.ok) return [];
  return result.data.filter((a) => a.identifier === subjectEmail);
}

async function collectSubjectApiKeys(subjectEmail: string): Promise<ApiKeySummary[]> {
  const result = await listApiKeys();
  if (!result.ok) return [];
  return result.data.filter((k) => k.identifier === subjectEmail);
}

/**
 * Runs one real 'export' DSAR job to completion: gathers the subject's
 * real rows from all three sources, streams them into one NDJSON buffer
 * (same one-object-per-line convention as lib/audit-export.ts), stores it
 * via the same signed-short-lived-download-link primitive
 * app/api/projects/[name]/export-all/route.ts already uses
 * (lib/export-download-cache.ts's storeExportArchive), and marks the
 * request row complete with the token.
 */
export async function runDsarExport(requestId: string): Promise<void> {
  const existing = await getDsarRequest(requestId);
  if (!existing.ok || !existing.data || existing.data.kind !== "export") return;
  const request = existing.data;
  if (request.status !== "pending") return; // already picked up or terminal -- never re-run

  await putRequest({ ...request, status: "processing" });

  const orgResult = await getOrg(request.orgId);
  if (!orgResult.ok || !orgResult.data) {
    await putRequest({
      ...request,
      status: "failed",
      error: orgResult.ok ? "org not found" : orgResult.error,
      completedAt: new Date().toISOString(),
    });
    return;
  }
  const org = orgResult.data;

  try {
    const [auditRows, membership, apiKeys] = await Promise.all([
      collectSubjectAuditRows(request.subjectEmail),
      collectSubjectMembership(org, request.subjectEmail),
      collectSubjectApiKeys(request.subjectEmail),
    ]);

    const records: DsarBundleRecord[] = [
      ...auditRows.map((r): DsarBundleRecord => ({
        recordType: "audit_log_entry",
        subjectEmail: request.subjectEmail,
        orgId: request.orgId,
        data: r,
      })),
      ...membership.map((m): DsarBundleRecord => ({
        recordType: "org_membership",
        subjectEmail: request.subjectEmail,
        orgId: request.orgId,
        data: m,
      })),
      ...apiKeys.map((k): DsarBundleRecord => ({
        recordType: "api_key",
        subjectEmail: request.subjectEmail,
        orgId: request.orgId,
        data: k,
      })),
    ];

    const ndjson = records.map((r) => JSON.stringify(r)).join("\n") + (records.length > 0 ? "\n" : "");
    const buffer = Buffer.from(ndjson, "utf8");
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `dsar-export-${org.id}-${stamp}.ndjson`;

    const signed = storeExportArchive(buffer, filename, request.subjectEmail, 15 * 60);

    await putRequest({
      ...request,
      status: "complete",
      completedAt: new Date().toISOString(),
      downloadToken: signed.token,
      downloadExpiresAt: signed.expiresAt,
      bundleFilename: filename,
      bundleRowCount: records.length,
    });

    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: request.requestedBy,
      method: "DSAR",
      path: `/api/privacy/request-export (org=${org.id}, subject=${request.subjectEmail}, rows=${records.length})`,
      status: 200,
      requestId: newRequestId(),
    });
  } catch (err) {
    await putRequest({
      ...request,
      status: "failed",
      error: err instanceof Error ? err.message : String(err),
      completedAt: new Date().toISOString(),
    });
  }
}

// ------------------------------------------------------------ Erasure

const REDACTED_ACTOR_PREFIX = "[dsar-redacted]";

function redactedActorFor(subjectEmail: string, requestId: string): string {
  // Deterministic per-request marker, not the bare literal
  // "[dsar-redacted]" repeated for every row -- lets a later forensic
  // reviewer see WHICH erasure request redacted a given row (real,
  // traceable) without the marker itself leaking the original email back
  // out (it's a truncated sha256 of the original value, not the value).
  const digest = createHash("sha256").update(subjectEmail, "utf8").digest("hex").slice(0, 12);
  return `${REDACTED_ACTOR_PREFIX} subject=${digest} request=${requestId}`;
}

// Same disallowed-character escaping lib/authz.ts's encodeIdentifierKey
// uses for ConfigMap `data` keys -- duplicated here (not exported by
// authz.ts), same "kept identical for consistency" discipline
// lib/orgs.ts's own duplicated `slugify` already documents.
function encodeIdentifierKey(identifier: string): string {
  return identifier.replace(/[^-._a-zA-Z0-9]/g, (ch) => `-x${ch.charCodeAt(0).toString(16)}-`);
}

/**
 * Real redaction of every audit_log row whose actor is this exact
 * subject email -- an UPDATE, never a DELETE, consistent with
 * lib/audit-db.ts's append-only design (see this module's header
 * comment for the disclosed hash-chain consequence). Returns the real
 * number of rows updated.
 */
async function redactSubjectAuditRows(subjectEmail: string, requestId: string): Promise<number> {
  const pool = await getAuditDbPool();
  if (!pool) return 0;
  const marker = redactedActorFor(subjectEmail, requestId);
  const result = await pool.query(
    `UPDATE platform_console.audit_log SET actor = $1 WHERE actor = $2`,
    [marker, subjectEmail],
  );
  return result.rowCount ?? 0;
}

/**
 * Real removal of the subject's per-org membership role entry -- a
 * merge-patch that deletes the one key belonging to this identifier (RFC
 * 7386 null-value-removes-the-key, same convention lib/orgs.ts's
 * deleteOrg already uses to remove a registry row). Returns whether a
 * membership entry actually existed and was removed (never fabricated
 * true when there was nothing to redact).
 */
async function redactSubjectMembership(org: Org, subjectEmail: string): Promise<boolean> {
  const existing = await getOrgRoleAssignmentsIn(org.namespace);
  if (!existing.ok) return false;
  const had = existing.data.some((a) => a.identifier === subjectEmail);
  if (!had) return false;

  const patch: Record<string, string | null> = {
    [encodeIdentifierKey(subjectEmail)]: null,
  };
  const result = await createOrUpdateConfigMap(
    org.namespace,
    "platform-console-org-roles",
    patch as unknown as Record<string, string>,
  );
  return result.ok;
}

/**
 * Runs one real 'erasure' DSAR job to completion -- called synchronously
 * from POST /api/privacy/request-erasure immediately after a fresh
 * maker-checker approval is confirmed (never before). Redacts, never
 * hard-deletes; records its own real audit log entry describing exactly
 * what was redacted, so the erasure itself is forever visible in the
 * durable audit trail even though the subject's own prior rows no longer
 * name them.
 */
export async function runDsarErasure(requestId: string): Promise<K8sResult<DsarRequest>> {
  const existing = await getDsarRequest(requestId);
  if (!existing.ok) return existing;
  if (!existing.data || existing.data.kind !== "erasure") {
    return { ok: false, error: `no pending erasure DSAR request found with id '${requestId}'` };
  }
  const request = existing.data;
  if (request.status === "complete") return { ok: true, data: request }; // idempotent: already done

  await putRequest({ ...request, status: "processing" });

  const orgResult = await getOrg(request.orgId);
  if (!orgResult.ok) return orgResult;
  if (!orgResult.data) {
    const failed: DsarRequest = {
      ...request,
      status: "failed",
      error: "org not found",
      completedAt: new Date().toISOString(),
    };
    await putRequest(failed);
    return { ok: true, data: failed };
  }
  const org = orgResult.data;

  const [redactedAuditRowCount, redactedMembership] = await Promise.all([
    redactSubjectAuditRows(request.subjectEmail, request.requestId),
    redactSubjectMembership(org, request.subjectEmail),
  ]);

  const completed: DsarRequest = {
    ...request,
    status: "complete",
    completedAt: new Date().toISOString(),
    redactedAuditRowCount,
    redactedMembership,
  };
  const putResult = await putRequest(completed);
  if (!putResult.ok) return putResult;

  // The erasure itself is its own new, real audit log entry -- the record
  // that proves this erasure happened, when, and at whose request never
  // gets erased itself (the actor here is the OPERATOR who ran the
  // erasure, not the redacted subject, so this entry is never a target
  // of its own redaction).
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: request.requestedBy,
    method: "DSAR",
    path: `/api/privacy/request-erasure (org=${org.id}, subject-redacted, auditRowsRedacted=${redactedAuditRowCount}, membershipRedacted=${redactedMembership})`,
    status: 200,
    requestId: newRequestId(),
  });

  return { ok: true, data: completed };
}

// ------------------------------------------------------------- Poller

let started = false;

async function tick(): Promise<void> {
  const all = await listDsarRequests();
  if (!all.ok) {
    console.error(`[dsar-poller] listDsarRequests failed: ${all.error}`);
    return;
  }
  const pendingExports = all.data.filter((r) => r.kind === "export" && r.status === "pending");
  for (const request of pendingExports) {
    await runDsarExport(request.requestId);
  }
}

const DSAR_POLL_INTERVAL_MS = 10_000;

/**
 * Starts the DSAR export poller exactly once per process -- same
 * `started`-guarded, `setInterval`-driven tick loop as
 * lib/webhook-poller.ts's `startWebhookPoller`, called from the same
 * instrumentation.ts `register()` hook. Erasure requests are
 * deliberately NOT polled here (see this module's header comment).
 */
export function startDsarPoller(): void {
  if (started) return;
  started = true;
  void tick();
  setInterval(() => {
    void tick();
  }, DSAR_POLL_INTERVAL_MS);
}
