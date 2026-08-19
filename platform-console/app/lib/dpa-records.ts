/**
 * Real per-org Data Processing Agreement (DPA) e-signature RECORD store --
 * the compliance-artifact gap upstream of lib/dsar.ts's GDPR/CCPA request
 * workflow: a Fortune-5 buyer's legal/procurement team requires a signed
 * DPA on file BEFORE any personal data is sent to this platform at all,
 * and needs a queryable system-of-record proving it, separate from any
 * request-handling machinery.
 *
 * Deliberately does NOT perform e-signing -- that would require a new
 * paid third-party account (DocuSign/HelloSign/etc.), explicitly out of
 * scope. This module stores the RESULT of a signature executed elsewhere:
 * a `signatureReference` string field (that external system's document
 * ID or URL), never a signing flow of its own.
 *
 * Storage: one real k8s ConfigMap (`platform-dpa-records`,
 * `platform-console` namespace, same get-then-create-or-patch
 * getConfigMap/createOrUpdateConfigMap primitive lib/dsar.ts/lib/orgs.ts/
 * lib/authz.ts already use -- no new k8s resource kind), one key per org
 * (the org id, already ConfigMap-key-safe -- see lib/orgs.ts's id
 * generation), each value an APPEND-ONLY JSON array of DpaRecord --
 * the exact same append-only-array-in-one-ConfigMap-value pattern
 * lib/audit-db.ts's header comment documents for its own hash-chain
 * segments: a new record is appended, nothing already written is ever
 * mutated or removed, so re-signing on a new DPA version or superseding
 * a prior one is always visible history, never a silent overwrite.
 *
 * Tamper-evidence: `documentHash` is the sha256 of the DPA document text
 * (uploaded/pasted at record time), reusing the same
 * `createHash("sha256").update(...).digest("hex")` primitive
 * lib/audit-integrity.ts's per-row digest and lib/dsar.ts's
 * `redactedActorFor` marker both already use -- lets a later reviewer
 * confirm the exact text that was signed hasn't been altered, without
 * this module needing to retain the full document text itself.
 */
import { createHash } from "node:crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const DPA_NAMESPACE = "platform-console";
export const DPA_CONFIGMAP = "platform-dpa-records";

export interface DpaRecord {
  version: string;
  effectiveDate: string;
  signerName: string;
  signerEmail: string;
  /** External e-sign system's document ID/URL -- this repo stores the
   * reference, never performs signing. */
  signatureReference: string;
  /** sha256 hex digest of the signed DPA text, for tamper-evidence. */
  documentHash: string;
  /** Actor identifier of whoever recorded this entry (roleIdentifierFor
   * the recording session), distinct from signerName/signerEmail -- the
   * person who typed this into the console is not necessarily the
   * person who signed the DPA. */
  recordedByIdentifier: string;
  recordedAt: string;
}

export type DpaStatus = "signed" | "unsigned" | "superseded";

export interface DpaHistory {
  orgId: string;
  records: DpaRecord[];
  currentStatus: DpaStatus;
  /** The most recent record by recordedAt, if any -- the one the
   * `currentStatus` computation treats as "current". */
  current: DpaRecord | null;
}

function isDpaRecord(value: unknown): value is DpaRecord {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.version === "string" &&
    typeof v.effectiveDate === "string" &&
    typeof v.signerName === "string" &&
    typeof v.signerEmail === "string" &&
    typeof v.signatureReference === "string" &&
    typeof v.documentHash === "string" &&
    typeof v.recordedByIdentifier === "string" &&
    typeof v.recordedAt === "string"
  );
}

function isDpaRecordArray(value: unknown): value is DpaRecord[] {
  return Array.isArray(value) && value.every(isDpaRecord);
}

/** sha256 hex digest of a DPA document's text -- the exact
 * createHash("sha256") primitive lib/audit-integrity.ts/lib/dsar.ts
 * already use for tamper-evident digests elsewhere in this codebase. */
export function hashDpaDocumentText(documentText: string): string {
  return createHash("sha256").update(documentText, "utf8").digest("hex");
}

async function getAll(): Promise<K8sResult<Record<string, DpaRecord[]>>> {
  const existing = await getConfigMap(DPA_NAMESPACE, DPA_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, DpaRecord[]> = {};
  for (const [orgId, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (isDpaRecordArray(rows)) parsed[orgId] = rows;
      // A hand-edited or corrupt value is skipped, not fatal -- same
      // discipline lib/dsar.ts's getAll uses for its own ConfigMap.
    } catch {
      // ignore -- malformed JSON for this org's key
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Computes `currentStatus` from a record list, oldest-first as stored:
 *  - "unsigned": no records at all.
 *  - "superseded": at least one record exists, and the most recent
 *    (by recordedAt) is not the CURRENT version -- i.e. a newer version
 *    string has already been recorded after it. In practice with
 *    append-only ordering the most recent recordedAt entry IS the
 *    current one, so "superseded" only appears if a later append
 *    happened with an effectiveDate in the past relative to an earlier
 *    append (a real, if rare, backfill/correction case) -- computed
 *    from effectiveDate ordering, not assumed from array position, so a
 *    corrected append still resolves the true current record.
 *  - "signed": the most recent-by-effectiveDate record is also the most
 *    recently recorded one.
 */
function computeStatus(records: DpaRecord[]): { status: DpaStatus; current: DpaRecord | null } {
  if (records.length === 0) return { status: "unsigned", current: null };

  const byEffectiveDate = [...records].sort((a, b) =>
    b.effectiveDate.localeCompare(a.effectiveDate),
  );
  const current = byEffectiveDate[0];

  const byRecordedAt = [...records].sort((a, b) => b.recordedAt.localeCompare(a.recordedAt));
  const mostRecentlyRecorded = byRecordedAt[0];

  const status: DpaStatus = current === mostRecentlyRecorded ? "signed" : "superseded";
  return { status, current };
}

/**
 * Full DPA history for one org, plus the computed `currentStatus` GET
 * /api/dpa/[orgId] returns. Never fabricates history for an org with no
 * ConfigMap key -- an org that has simply never had a DPA recorded
 * resolves to `{records: [], currentStatus: "unsigned", current: null}`,
 * not a 404 (the org itself may still be real; "no DPA recorded yet" is
 * a real, queryable state, not an error).
 */
export async function getDpaHistory(orgId: string): Promise<K8sResult<DpaHistory>> {
  const all = await getAll();
  if (!all.ok) return all;
  const records = (all.data[orgId] ?? []).slice().sort((a, b) => a.recordedAt.localeCompare(b.recordedAt));
  const { status, current } = computeStatus(records);
  return { ok: true, data: { orgId, records, currentStatus: status, current } };
}

/**
 * Appends one new DPA record for an org -- APPEND ONLY, never mutates or
 * removes a prior entry in the array. Read-modify-write against the
 * live ConfigMap value (same single-key JSON-array append lib/audit-db.ts's
 * header comment documents for its own hash-chain segments); a
 * concurrent double-append under real k8s API server contention is
 * possible but rare and non-corrupting -- worst case is a lost update
 * requiring a re-POST, never a value that fails to parse as an array.
 */
export async function appendDpaRecord(
  orgId: string,
  record: DpaRecord,
): Promise<K8sResult<DpaHistory>> {
  const all = await getAll();
  if (!all.ok) return all;
  const existingRecords = all.data[orgId] ?? [];
  const updatedRecords = [...existingRecords, record];

  const result = await createOrUpdateConfigMap(DPA_NAMESPACE, DPA_CONFIGMAP, {
    [orgId]: JSON.stringify(updatedRecords),
  });
  if (!result.ok) return result;

  const { status, current } = computeStatus(updatedRecords);
  return { ok: true, data: { orgId, records: updatedRecords, currentStatus: status, current } };
}

/**
 * Every org id (from lib/orgs.ts's real org registry) that has no
 * "signed" current DPA record -- i.e. `currentStatus` is "unsigned" or
 * "superseded" -- for GET /api/dpa's compliance-dashboard-widget listing.
 * Callers pass the live org id list rather than this module reaching
 * into lib/orgs.ts itself, keeping this module's only k8s dependency the
 * one ConfigMap it owns.
 */
export async function listOrgsMissingCurrentDpa(
  orgIds: string[],
): Promise<K8sResult<{ orgId: string; currentStatus: DpaStatus }[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  const missing = orgIds
    .map((orgId) => {
      const records = all.data[orgId] ?? [];
      const { status } = computeStatus(records);
      return { orgId, currentStatus: status };
    })
    .filter((r) => r.currentStatus !== "signed");
  return { ok: true, data: missing };
}
