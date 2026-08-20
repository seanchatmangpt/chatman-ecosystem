/**
 * Real Certificate of Data Destruction -- backs a Fortune-5 offboarding/
 * contract-termination requirement lib/export-custody.ts's own header
 * comment already distinguishes from: that module (and lib/dsar.ts before
 * it) proves what was EXPORTED or erased for a SUBJECT; finance/legal/
 * security at contract termination instead ask "for this ENTIRE ORG, was
 * every real piece of infrastructure it ever held -- PVCs, backups,
 * exports, logs -- actually torn down, per the retention terms the
 * contract promised, and can we get a signed artifact proving it." That is
 * an org-wide teardown-attestation question neither existing module
 * answers.
 *
 * What this module can truthfully attest, and what it deliberately
 * cannot, stated up front (never silently overclaimed):
 *
 *   1. PVCs -- verified LIVE against the real k8s API
 *      (lib/k8s.ts's listNamespacePvcs): confirms the org's own Namespace
 *      (lib/orgs.ts's deleteOrg -- cascades every Project/Database/
 *      Secret/ConfigMap/PVC k8s owns inside it) is actually gone, or, if
 *      the namespace is somehow still present, that zero PVCs remain in
 *      it. This is a real, live cluster read, never a cached/assumed
 *      value.
 *   2. Backups -- verified against lib/backup-retention.ts's own
 *      BackupRecord ledger: every record for this org must be
 *      `"expired"` (cleanupExpiredBackups already deleted the real
 *      underlying pg_dump Job for each) or simply absent. A record still
 *      `"completed"`/`"pending"`/`"running"` fails the check -- a live
 *      backup Job/dump still exists somewhere this module can see.
 *   3. Exports -- app/api/projects/[name]/export-all's own archives
 *      (lib/export-download-cache.ts) are already NEVER durably
 *      persisted: they live only in an in-process Map, evicted within
 *      MAX_TTL_SECONDS (1h) of creation or on the next server restart,
 *      whichever comes first. There is no durable export-payload store
 *      in this repo to purge -- disclosed here, not silently claimed as
 *      "verified deleted", because there was never anything to delete.
 *      lib/export-custody.ts's own CustodyRecord rows are PROOF an export
 *      once happened (a chain-of-custody receipt), not the export payload
 *      itself, and are deliberately NOT torn down by this module -- doing
 *      so would destroy the very evidence a security review later asks
 *      for. Retained by design, disclosed here.
 *   4. Logs -- platform_console.audit_log (lib/audit-db.ts) is an
 *      intentionally immutable, hash-chained ledger (verifyAuditChain);
 *      SOC2/ISO27001 evidence retention requires this record survive an
 *      org's own deletion (it is what proves the deletion happened at
 *      all). This module does not delete or redact audit_log rows for a
 *      terminated org -- disclosed here as an explicit, deliberate scope
 *      boundary, the same way lib/dsar.ts's own erasure path only
 *      redacts an ACTOR's identity, never the row itself.
 *
 * Storage: one real k8s ConfigMap (`platform-data-destruction-certificates`,
 * `platform-console` namespace), same get-then-create-or-patch primitive
 * lib/export-custody.ts/lib/approval-workflow.ts already use -- no new k8s
 * resource kind, no new RBAC verb. Key shape: one key per certificate,
 * `certificateId` (a `crypto.randomUUID()`) -> JSON DestructionCertificate.
 *
 * Issuance is FAIL CLOSED: `issueDataDestructionCertificate` refuses (a
 * real `{ok:false}`, never a partial/best-effort certificate) unless
 * `verifyDataDestruction` reports every real check clear. A certificate
 * can never be minted while a live PVC or an undeleted backup still
 * exists -- the whole point of the artifact is that it is true.
 *
 * Chain-of-custody: mirrors lib/export-custody.ts's own pattern exactly --
 * writes ONE real audit_log entry via lib/audit-db.ts's
 * `writeAuditLogEntryAwaited` (awaited: the certificate's job is to point
 * at an already-committed, hash-chained row) and stores the resulting
 * `requestId` on the certificate so `verifyDataDestructionCertificate`
 * can later re-derive that row's hash and catch tampering, the same
 * `computeRowHash`-anchored check `verifyExportCustody` already performs.
 */
import { createHash } from "node:crypto";
import {
  createOrUpdateConfigMap,
  getConfigMap,
  k8sRequest,
  listNamespacePvcs,
  type K8sResult,
} from "@/lib/k8s";
import { listBackupRecords, type BackupRecord } from "@/lib/backup-retention";
import {
  computeRowHash,
  getAuditLogChainSegmentByRequestId,
  newRequestId,
  writeAuditLogEntryAwaited,
  type AuditLogEntry,
} from "@/lib/audit-db";

export const DATA_DESTRUCTION_NAMESPACE = "platform-console";
export const DATA_DESTRUCTION_CONFIGMAP = "platform-data-destruction-certificates";

// ------------------------------------------------------------ Verification

export interface DataDestructionVerification {
  orgId: string;
  namespace: string;
  namespaceExists: boolean;
  remainingPvcNames: string[];
  backupRecordsTotal: number;
  backupRecordsUndeleted: string[]; // BackupRecord.id values not yet "expired"
  allClear: boolean;
  reasons: string[]; // populated exactly when allClear is false
}

interface NamespaceGetResponse {
  metadata: { name: string };
}

/**
 * Real, live verification of org-wide teardown -- the function both
 * GET /api/internal/data-destruction (a status check) and
 * POST /api/owner/data-destruction (the fail-closed gate before minting)
 * call. Every field is a real read: `listNamespacePvcs`
 * (k8sRequest under the hood) for PVCs, `listBackupRecords` for backups.
 * Never fabricates a clean result when a read itself fails -- a K8sResult
 * error here propagates as a real error, not a false "allClear".
 */
export async function verifyDataDestruction(
  orgId: string,
  namespace: string,
): Promise<K8sResult<DataDestructionVerification>> {
  const nsResult = await k8sRequest<NamespaceGetResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}`,
  );
  let namespaceExists: boolean;
  if (nsResult.ok) {
    namespaceExists = true;
  } else if (/not found/i.test(nsResult.error)) {
    namespaceExists = false;
  } else {
    return nsResult;
  }

  let remainingPvcNames: string[] = [];
  if (namespaceExists) {
    const pvcResult = await listNamespacePvcs(namespace);
    if (!pvcResult.ok) return pvcResult;
    remainingPvcNames = pvcResult.data.map((p) => p.name);
  }

  const backupsResult = await listBackupRecords(orgId);
  if (!backupsResult.ok) return backupsResult;
  const backupRecordsUndeleted = backupsResult.data
    .filter((r: BackupRecord) => r.status !== "expired")
    .map((r) => r.id);

  const reasons: string[] = [];
  if (namespaceExists) {
    reasons.push(`namespace '${namespace}' still exists in the cluster`);
  }
  if (remainingPvcNames.length > 0) {
    reasons.push(
      `${remainingPvcNames.length} PersistentVolumeClaim(s) still present: ${remainingPvcNames.join(", ")}`,
    );
  }
  if (backupRecordsUndeleted.length > 0) {
    reasons.push(
      `${backupRecordsUndeleted.length} backup record(s) not yet purged: ${backupRecordsUndeleted.join(", ")}`,
    );
  }

  return {
    ok: true,
    data: {
      orgId,
      namespace,
      namespaceExists,
      remainingPvcNames,
      backupRecordsTotal: backupsResult.data.length,
      backupRecordsUndeleted,
      allClear: reasons.length === 0,
      reasons,
    },
  };
}

// ------------------------------------------------------------- Certificate

export interface DataDestructionCertificate {
  id: string;
  orgId: string;
  namespace: string;
  requestedBy: string; // actor who filed the request that led here (maker)
  issuedBy: string; // second, distinct owner-role approver (checker) -- see lib/approval-workflow.ts
  issuedAt: string; // RFC3339
  contractRetentionTermsDays?: number; // the org's contractual retention window at time of issuance, if known (lib/backup-retention.ts's BackupPolicy.retentionDays)
  verification: DataDestructionVerification;
  verificationDigest: string; // sha256 hex of the canonical JSON of `verification`, at issuance time
  auditLogEntryId: string; // requestId of the audit_log row minted for this certificate's issuance
}

function isVerification(value: unknown): value is DataDestructionVerification {
  const v = value as Partial<DataDestructionVerification> | null;
  return (
    !!v &&
    typeof v.orgId === "string" &&
    typeof v.namespace === "string" &&
    typeof v.namespaceExists === "boolean" &&
    Array.isArray(v.remainingPvcNames) &&
    typeof v.backupRecordsTotal === "number" &&
    Array.isArray(v.backupRecordsUndeleted) &&
    typeof v.allClear === "boolean" &&
    Array.isArray(v.reasons)
  );
}

function isCertificate(value: unknown): value is DataDestructionCertificate {
  const c = value as Partial<DataDestructionCertificate> | null;
  return (
    !!c &&
    typeof c.id === "string" &&
    typeof c.orgId === "string" &&
    typeof c.namespace === "string" &&
    typeof c.requestedBy === "string" &&
    typeof c.issuedBy === "string" &&
    typeof c.issuedAt === "string" &&
    typeof c.verificationDigest === "string" &&
    typeof c.auditLogEntryId === "string" &&
    isVerification(c.verification)
  );
}

function parseCertificate(raw: string): DataDestructionCertificate | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isCertificate(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, DataDestructionCertificate>>> {
  const cm = await getConfigMap(DATA_DESTRUCTION_NAMESPACE, DATA_DESTRUCTION_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, DataDestructionCertificate>();
  for (const [id, raw] of Object.entries(data)) {
    const parsed = parseCertificate(raw);
    if (parsed) out.set(id, parsed);
  }
  return { ok: true, data: out };
}

/** Real list of every destruction certificate for one org, newest first. */
export async function listDataDestructionCertificates(
  orgId: string,
): Promise<K8sResult<DataDestructionCertificate[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  const rows = Array.from(all.data.values())
    .filter((c) => c.orgId === orgId)
    .sort((a, b) => Date.parse(b.issuedAt) - Date.parse(a.issuedAt));
  return { ok: true, data: rows };
}

export async function getDataDestructionCertificate(
  id: string,
): Promise<K8sResult<DataDestructionCertificate | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(id) ?? null };
}

function canonicalDigest(verification: DataDestructionVerification): string {
  // Stable field order -- never `JSON.stringify(verification)` directly,
  // whose key order follows insertion order and would silently change the
  // digest if this interface's field declaration order ever changes.
  const canonical = {
    orgId: verification.orgId,
    namespace: verification.namespace,
    namespaceExists: verification.namespaceExists,
    remainingPvcNames: [...verification.remainingPvcNames].sort(),
    backupRecordsTotal: verification.backupRecordsTotal,
    backupRecordsUndeleted: [...verification.backupRecordsUndeleted].sort(),
    allClear: verification.allClear,
  };
  return createHash("sha256").update(JSON.stringify(canonical)).digest("hex");
}

export type IssueCertificateError = "not_all_clear";

/**
 * Mints one real, durable Certificate of Data Destruction. FAILS CLOSED:
 * refuses with `"not_all_clear"` unless the passed-in `verification`
 * itself reports `allClear: true` -- this function never re-derives
 * looseness from a caller's own summary, callers MUST pass the real,
 * freshly-computed `verifyDataDestruction` result, not a cached or
 * hand-built one, so the certificate always attests to what was checked
 * moments before issuance.
 */
export async function issueDataDestructionCertificate(input: {
  orgId: string;
  namespace: string;
  requestedBy: string;
  issuedBy: string;
  verification: DataDestructionVerification;
  contractRetentionTermsDays?: number;
}): Promise<K8sResult<DataDestructionCertificate> | { ok: false; error: IssueCertificateError }> {
  if (!input.verification.allClear) {
    return { ok: false, error: "not_all_clear" };
  }

  const id = globalThis.crypto.randomUUID();
  const issuedAt = new Date().toISOString();
  const requestId = newRequestId();

  const entry: AuditLogEntry = {
    requestId,
    timestamp: issuedAt,
    actor: input.issuedBy,
    method: "ISSUE",
    path: `/data-destruction/${input.orgId}/${id}`,
    status: 200,
    orgId: input.orgId,
  };
  await writeAuditLogEntryAwaited(entry);

  const certificate: DataDestructionCertificate = {
    id,
    orgId: input.orgId,
    namespace: input.namespace,
    requestedBy: input.requestedBy,
    issuedBy: input.issuedBy,
    issuedAt,
    ...(input.contractRetentionTermsDays !== undefined
      ? { contractRetentionTermsDays: input.contractRetentionTermsDays }
      : {}),
    verification: input.verification,
    verificationDigest: canonicalDigest(input.verification),
    auditLogEntryId: requestId,
  };

  const write = await createOrUpdateConfigMap(DATA_DESTRUCTION_NAMESPACE, DATA_DESTRUCTION_CONFIGMAP, {
    [id]: JSON.stringify(certificate),
  });
  if (!write.ok) return write;
  return { ok: true, data: certificate };
}

// --------------------------------------------------------- Tamper-evidence

export interface DataDestructionCertificateVerification {
  verified: boolean;
  certificateId: string;
  reasons: string[];
}

/**
 * Real tamper-evidence check for one certificate -- the same
 * `computeRowHash`-anchored pattern lib/export-custody.ts's
 * `verifyExportCustody` already establishes: re-fetches the exact
 * audit_log row this certificate's `auditLogEntryId` points at,
 * recomputes ITS `row_hash` from its own stored `prev_hash` and fields,
 * confirms it still matches the stored `row_hash`, cross-checks the
 * row's own `orgId`/`actor` still agree with the certificate, AND
 * recomputes `verificationDigest` from the certificate's own stored
 * `verification` object to catch a hand-edited check result (e.g. a
 * ConfigMap row edited to claim `allClear: true` after the fact) that a
 * bare audit-row hash check alone would miss.
 */
export async function verifyDataDestructionCertificate(
  certificateId: string,
): Promise<K8sResult<DataDestructionCertificateVerification>> {
  const certResult = await getDataDestructionCertificate(certificateId);
  if (!certResult.ok) return certResult;
  const certificate = certResult.data;
  if (!certificate) {
    return {
      ok: true,
      data: { verified: false, certificateId, reasons: ["no such data-destruction certificate"] },
    };
  }

  const reasons: string[] = [];

  const recomputedDigest = canonicalDigest(certificate.verification);
  if (recomputedDigest !== certificate.verificationDigest) {
    reasons.push(
      "the stored verification checks do not match this certificate's own verificationDigest -- the record was modified after issuance",
    );
  }

  const segmentResult = await getAuditLogChainSegmentByRequestId(certificate.auditLogEntryId);
  if (!segmentResult.ok) return segmentResult;
  const segment = segmentResult.data;

  if (!segment) {
    reasons.push(
      "the audit_log row this certificate points at no longer exists (or predates hash-chaining) -- not verifiable",
    );
    return { ok: true, data: { verified: false, certificateId, reasons } };
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
  const recomputedRowHash = computeRowHash(segment.prevHash, entry);
  if (recomputedRowHash !== segment.rowHash) {
    reasons.push(
      `audit_log row ${segment.id}: recomputed row_hash does not match the stored row_hash -- the row was modified after insertion`,
    );
  }
  if (segment.orgId !== certificate.orgId) {
    reasons.push(
      `audit_log row ${segment.id}'s org_id ("${segment.orgId ?? "none"}") no longer matches this certificate's orgId ("${certificate.orgId}")`,
    );
  }
  if (segment.actor !== certificate.issuedBy) {
    reasons.push(
      `audit_log row ${segment.id}'s actor ("${segment.actor}") no longer matches this certificate's issuedBy ("${certificate.issuedBy}")`,
    );
  }

  return { ok: true, data: { verified: reasons.length === 0, certificateId, reasons } };
}
