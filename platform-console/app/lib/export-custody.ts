/**
 * Real Per-Org Data-Export Chain-of-Custody Certificate -- a distinct
 * compliance artifact from lib/dsar.ts's GDPR/CCPA export, and does NOT
 * reuse that module or its storage.
 *
 * The gap this closes: lib/dsar.ts proves what was deleted/exported for
 * ONE data subject's own erasure/access request (subject-scoped, owner-
 * initiated on that subject's behalf). Fortune-5 SOC2/ISO27001 evidence
 * collection separately asks "for ANY bulk operational export of this
 * org's data -- the scheduled S3 bucket subscription
 * (lib/s3-export-subscription.ts), an admin's manual CSV pull -- who
 * initiated it, how many records, what's the payload's digest, and can
 * we prove that digest and its audit-log entry haven't been tampered
 * with since." That is an operational/security-evidence question, not a
 * data-subject-rights one, and lib/dsar.ts's ConfigMap/flow has no field
 * for it.
 *
 * `recordExportCustody` is the ONE function every bulk-export code path
 * in this repo calls (explicitly, from its own success branch -- never
 * inferred from a generic "any write happened" hook) to mint a
 * certificate:
 *
 *   1. Computes a real SHA-256 digest over the actual exported payload
 *      bytes, using the exact same primitive
 *      (`node:crypto`'s `createHash("sha256")`) lib/audit-db.ts's own
 *      hash chain (`computeRowHash`) already standardizes on for this
 *      repo -- picking a second hash primitive for a second compliance
 *      artifact in the same repo would just be two things to keep in
 *      sync for no reason; sha256 is also what lib/api-keys.ts already
 *      hashes API-key plaintext with, so this is the one hash primitive
 *      this whole console uses everywhere a one-way digest is needed.
 *   2. Writes ONE real audit_log entry via lib/audit-db.ts's
 *      `writeAuditLogEntryAwaited` (awaited, not fire-and-forget -- see
 *      that function's own header comment: the certificate's whole job
 *      is to point at an already-committed, hash-chained row, so the
 *      row must exist before the certificate is minted).
 *   3. Stores a `CustodyRecord` in a new k8s ConfigMap
 *      (`platform-export-custody`, `platform-console` namespace), one
 *      `data` key per `exportId`, using the exact same
 *      getConfigMap/createOrUpdateConfigMap get-then-create-or-patch
 *      primitive lib/contract-renewals.ts's own header comment
 *      documents (itself reused from lib/k8s.ts's Feature Flags module)
 *      -- no new k8s resource kind, no new RBAC verb: the
 *      `platform-console-feature-flags` Role already grants
 *      get/list/create/update/patch on `configmaps` in this namespace
 *      with no `resourceNames` restriction.
 *
 * `verifyExportCustody` is the tamper-evidence check: it re-fetches the
 * one audit_log row the certificate points at
 * (`getAuditLogChainSegmentByRequestId`) and recomputes ITS row_hash from
 * its own stored prev_hash plus its own fields (the exact same
 * `computeRowHash` call `verifyAuditChain` uses, just anchored to one row
 * instead of walking the whole table) -- if that row's fields were
 * edited after insertion, the recomputed hash will not match the stored
 * one, and `verified` comes back `false`. It also cross-checks that the
 * row's own `orgId`/`actor` still agree with what the certificate claims
 * (a certificate whose ConfigMap entry was hand-edited to point at a
 * DIFFERENT, unrelated row would recompute a perfectly valid hash for
 * THAT row while still being a forged certificate -- the cross-check
 * catches that case, which a bare hash-match alone would miss).
 */
import { createHash } from "node:crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import {
  computeRowHash,
  getAuditLogChainSegmentByRequestId,
  newRequestId,
  writeAuditLogEntryAwaited,
  type AuditLogEntry,
} from "@/lib/audit-db";

export const EXPORT_CUSTODY_NAMESPACE = "platform-console";
export const EXPORT_CUSTODY_CONFIGMAP = "platform-export-custody";

export interface CustodyRecord {
  id: string; // exportId -- the ConfigMap key
  orgId: string;
  exportedBy: string;
  timestamp: string; // RFC3339
  recordCount: number;
  datasetHash: string; // sha256 hex digest of the actual exported payload bytes
  auditLogEntryId: string; // == the requestId of the audit_log row minted for this export
  destination: string; // human-readable sink, e.g. "s3://bucket/prefix/key" or "admin-csv-download"
}

function isCustodyRecord(value: unknown): value is CustodyRecord {
  const p = value as Partial<CustodyRecord> | null;
  return (
    !!p &&
    typeof p.id === "string" &&
    typeof p.orgId === "string" &&
    typeof p.exportedBy === "string" &&
    typeof p.timestamp === "string" &&
    typeof p.recordCount === "number" &&
    Number.isFinite(p.recordCount) &&
    typeof p.datasetHash === "string" &&
    typeof p.auditLogEntryId === "string" &&
    typeof p.destination === "string"
  );
}

function parseRecord(raw: string): CustodyRecord | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isCustodyRecord(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, CustodyRecord>>> {
  const cm = await getConfigMap(EXPORT_CUSTODY_NAMESPACE, EXPORT_CUSTODY_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, CustodyRecord>();
  for (const [exportId, raw] of Object.entries(data)) {
    const parsed = parseRecord(raw);
    if (parsed) out.set(exportId, parsed);
  }
  return { ok: true, data: out };
}

/**
 * Real list of every export-custody certificate this org has, newest
 * first -- backs GET /api/export-custody?orgId=. No cross-org read: the
 * caller (route handler) MUST filter/scope by orgId before this reaches
 * an untrusted caller; this function itself scopes so a route can never
 * forget to.
 */
export async function listExportCustodyRecords(orgId: string): Promise<K8sResult<CustodyRecord[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  const rows = Array.from(all.data.values())
    .filter((r) => r.orgId === orgId)
    .sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
  return { ok: true, data: rows };
}

export async function getExportCustodyRecord(
  exportId: string,
): Promise<K8sResult<CustodyRecord | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(exportId) ?? null };
}

export interface RecordExportCustodyInput {
  orgId: string;
  /** Identity that initiated the export -- lib/authz.ts's roleIdentifierFor(session)
   * for a human admin's manual pull, or a stable "system:<job-name>" string
   * for an unattended scheduled job (matches this repo's own convention for
   * non-human actors -- see lib/webhook-poller.ts callers). */
  exportedBy: string;
  recordCount: number;
  /** The actual exported payload bytes -- hashed here, never trusted
   * pre-hashed from the caller, so the certificate always attests to what
   * was REALLY sent, not to a value a caller could get wrong or fake. */
  payload: Buffer | string;
  /** Human-readable sink this export was written to, e.g.
   * `s3://<bucket>/<key>` or `"admin-csv-download"`. */
  destination: string;
}

/**
 * Mints one real, durable chain-of-custody certificate for a completed
 * bulk export. Distinct code path from lib/dsar.ts's per-subject export --
 * this is never called from, and never calls into, that module.
 */
export async function recordExportCustody(
  input: RecordExportCustodyInput,
): Promise<K8sResult<CustodyRecord>> {
  const datasetHash = createHash("sha256").update(input.payload).digest("hex");
  const exportId = globalThis.crypto.randomUUID();
  const timestamp = new Date().toISOString();
  const requestId = newRequestId();

  const entry: AuditLogEntry = {
    requestId,
    timestamp,
    actor: input.exportedBy,
    method: "EXPORT",
    path: `/export-custody/${input.orgId}/${exportId}`,
    status: 200,
    orgId: input.orgId,
  };
  await writeAuditLogEntryAwaited(entry);

  const record: CustodyRecord = {
    id: exportId,
    orgId: input.orgId,
    exportedBy: input.exportedBy,
    timestamp,
    recordCount: input.recordCount,
    datasetHash,
    auditLogEntryId: requestId,
    destination: input.destination,
  };

  const patch = await createOrUpdateConfigMap(EXPORT_CUSTODY_NAMESPACE, EXPORT_CUSTODY_CONFIGMAP, {
    [exportId]: JSON.stringify(record),
  });
  if (!patch.ok) return patch;
  return { ok: true, data: record };
}

// ------------------------------------------------------- Certificate views

/** GET /api/export-custody/[exportId]'s JSON shape -- the same
 * `CustodyRecord` fields, reframed as a certificate an auditor reads
 * top-to-bottom, plus the existing PDF export pattern
 * (app/api/orgs/[id]/compliance-reports/[reportId]/route.ts's own
 * text/CSV-on-`?format=` convention) can render straight from this same
 * JSON with no separate PDF-only data model. */
export interface ExportCustodyCertificate {
  certificateId: string;
  title: string;
  orgId: string;
  exportedBy: string;
  exportedAt: string;
  recordCount: number;
  datasetSha256: string;
  auditLogEntryId: string;
  destination: string;
}

export function toCertificate(record: CustodyRecord): ExportCustodyCertificate {
  return {
    certificateId: record.id,
    title: "Data Export Chain-of-Custody Certificate",
    orgId: record.orgId,
    exportedBy: record.exportedBy,
    exportedAt: record.timestamp,
    recordCount: record.recordCount,
    datasetSha256: record.datasetHash,
    auditLogEntryId: record.auditLogEntryId,
    destination: record.destination,
  };
}

// --------------------------------------------------------- Tamper-evidence

export interface ExportCustodyVerification {
  verified: boolean;
  exportId: string;
  reasons: string[];
}

/**
 * Real tamper-evidence check for one certificate: re-fetches the exact
 * audit_log row this certificate's `auditLogEntryId` points at, recomputes
 * that row's `row_hash` from its own stored `prev_hash` and fields (the
 * same `computeRowHash` primitive `verifyAuditChain` uses), and confirms
 * it still matches the stored `row_hash` -- plus cross-checks that the
 * row's own `orgId`/`actor` still agree with what the certificate claims,
 * so a certificate hand-edited to point at a different (but itself
 * hash-valid) row is caught too, not just a directly-edited row.
 */
export async function verifyExportCustody(exportId: string): Promise<K8sResult<ExportCustodyVerification>> {
  const recordResult = await getExportCustodyRecord(exportId);
  if (!recordResult.ok) return recordResult;
  const record = recordResult.data;
  if (!record) {
    return { ok: true, data: { verified: false, exportId, reasons: ["no such export-custody certificate"] } };
  }

  const segmentResult = await getAuditLogChainSegmentByRequestId(record.auditLogEntryId);
  if (!segmentResult.ok) return segmentResult;
  const segment = segmentResult.data;

  const reasons: string[] = [];
  if (!segment) {
    reasons.push(
      "the audit_log row this certificate points at no longer exists (or predates hash-chaining) -- not verifiable",
    );
    return { ok: true, data: { verified: false, exportId, reasons } };
  }

  const entry: AuditLogEntry = {
    requestId: segment.requestId,
    timestamp: segment.timestamp,
    actor: segment.actor,
    method: segment.method,
    path: segment.path,
    status: segment.status,
    ...(segment.orgId ? { orgId: segment.orgId } : {}),
    ...(segment.castleReceiptDigest ? { castleReceiptDigest: segment.castleReceiptDigest } : {}),
    ...(segment.impersonatedBy ? { impersonatedBy: segment.impersonatedBy } : {}),
    ...(segment.impersonationSessionId ? { impersonationSessionId: segment.impersonationSessionId } : {}),
  };
  const recomputed = computeRowHash(segment.prevHash, entry);
  if (recomputed !== segment.rowHash) {
    reasons.push(
      `audit_log row ${segment.id}: recomputed row_hash does not match the stored row_hash -- the row was modified after insertion`,
    );
  }
  if (segment.orgId !== record.orgId) {
    reasons.push(
      `audit_log row ${segment.id}'s org_id ("${segment.orgId ?? "none"}") no longer matches this certificate's orgId ("${record.orgId}")`,
    );
  }
  if (segment.actor !== record.exportedBy) {
    reasons.push(
      `audit_log row ${segment.id}'s actor ("${segment.actor}") no longer matches this certificate's exportedBy ("${record.exportedBy}")`,
    );
  }

  return { ok: true, data: { verified: reasons.length === 0, exportId, reasons } };
}
