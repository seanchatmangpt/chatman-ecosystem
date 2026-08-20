/**
 * Real Vendor Offboarding Data-Return/Destruction Attestation -- the
 * signed, timestamped document a Fortune-5 customer's procurement/legal
 * team requires at contract termination, closing the offboarding-gate
 * checklist item every such procurement process already has: "prove
 * every piece of our data was either exported back to us or destroyed,
 * within the SLA the contract promised."
 *
 * This module fabricates NOTHING new -- it is a real read-and-attest
 * layer over the two artifacts this repo already mints for the
 * underlying facts:
 *
 *   1. lib/export-custody.ts's `CustodyRecord`s: real, hash-chain-backed
 *      proof that a bulk export of this org's data actually happened,
 *      to a named destination, at a given time (the "returned to them"
 *      half of the requirement).
 *   2. lib/data-destruction-certificate.ts's `DataDestructionCertificate`:
 *      the real, fail-closed-issued proof that this org's live
 *      infrastructure (namespace/PVCs) and every backup record were
 *      actually torn down (the "destroyed" half).
 *
 * `computeVendorOffboardingEvidence` is the one function that decides
 * whether an attestation CAN be issued: it re-reads both of those real
 * stores fresh (never a cached/assumed summary) and is fail-closed --
 * `compliant` is only ever `true` when at least one of the two closing
 * events (a post-termination export, or an all-clear, tamper-verified
 * destruction certificate) is present AND landed on or before the
 * contract's own SLA deadline. `issueVendorOffboardingAttestation`
 * refuses (a real `{ok:false}`, never a partial attestation) unless the
 * evidence passed in reports `compliant: true` -- the same "callers MUST
 * pass the real, freshly-computed verification, never a hand-built one"
 * discipline `issueDataDestructionCertificate` already establishes.
 *
 * Mutation (issuing an attestation) is gated behind the SAME
 * maker-checker `vendor-offboarding.attestation.issue` approval workflow
 * `data-destruction.certificate.issue`/`insurance.policy.update` already
 * use -- one platform owner's own say-so is never sufficient by itself
 * to hand a customer's procurement team a signed compliance document.
 *
 * Storage: one real k8s ConfigMap
 * (`platform-vendor-offboarding-attestations`, `platform-console`
 * namespace), the exact same get-then-create-or-patch primitive
 * lib/export-custody.ts/lib/data-destruction-certificate.ts already use
 * -- no new k8s resource kind, no new RBAC verb.
 *
 * Chain-of-custody: mirrors lib/data-destruction-certificate.ts's own
 * pattern exactly -- writes ONE real audit_log entry via
 * lib/audit-db.ts's `writeAuditLogEntryAwaited` (awaited: the
 * attestation's whole job is to point at an already-committed,
 * hash-chained row) and stores the resulting `requestId` on the
 * attestation so `verifyVendorOffboardingAttestation` can later re-derive
 * that row's hash and catch tampering -- plus a `evidenceDigest` (sha256
 * of the canonical evidence snapshot) so a hand-edited ConfigMap row
 * claiming different evidence than what was actually attested is caught
 * too, the same two-layer check `verifyDataDestructionCertificate`
 * already performs.
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
import { listExportCustodyRecords, type CustodyRecord } from "@/lib/export-custody";
import {
  listDataDestructionCertificates,
  verifyDataDestructionCertificate,
  type DataDestructionCertificate,
} from "@/lib/data-destruction-certificate";

export const VENDOR_OFFBOARDING_NAMESPACE = "platform-console";
export const VENDOR_OFFBOARDING_CONFIGMAP = "platform-vendor-offboarding-attestations";

// ------------------------------------------------------------ Evidence

export interface VendorOffboardingEvidence {
  orgId: string;
  terminationDate: string; // RFC3339 -- when the contract actually terminated
  contractualSlaDays: number; // e.g. 30 -- the contract's own data-return/destruction window
  slaDeadline: string; // RFC3339 -- terminationDate + contractualSlaDays
  /** Every export-custody record for this org whose own timestamp is on
   * or after terminationDate -- i.e. an export that could plausibly BE
   * the contractual data-return, not an unrelated export that happened
   * mid-contract for an unrelated reason. */
  qualifyingExportRecordIds: string[];
  /** The single most recent data-destruction certificate for this org,
   * if one exists, re-verified fresh (tamper-evidence AND allClear) at
   * evidence-computation time. `null` when none has ever been issued. */
  destructionCertificateId: string | null;
  destructionCertificateAllClear: boolean;
  destructionCertificateVerified: boolean;
  destructionCertificateIssuedAt: string | null;
  /** True exactly when a qualifying export exists, or a verified/
   * all-clear destruction certificate exists (or both) -- the "returned
   * OR destroyed" half of the requirement. */
  dataAccountedFor: boolean;
  /** True exactly when whichever closing event(s) satisfied
   * dataAccountedFor happened on or before slaDeadline. Vacuously false
   * when dataAccountedFor itself is false. */
  withinSla: boolean;
  compliant: boolean; // dataAccountedFor && withinSla -- the fail-closed gate
  reasons: string[]; // populated exactly when compliant is false
}

/**
 * Real, live computation of whether this org's offboarding can be
 * truthfully attested -- the function both a GET status check and the
 * fail-closed gate before issuance call. Every field is a real read:
 * `listExportCustodyRecords`/`listDataDestructionCertificates` (k8s
 * ConfigMap reads under the hood) plus a fresh
 * `verifyDataDestructionCertificate` tamper-evidence re-check. Never
 * fabricates a clean result when a read itself fails -- a K8sResult
 * error here propagates as a real error, not a false "compliant".
 */
export async function computeVendorOffboardingEvidence(input: {
  orgId: string;
  terminationDate: string;
  contractualSlaDays: number;
}): Promise<K8sResult<VendorOffboardingEvidence>> {
  const { orgId, terminationDate, contractualSlaDays } = input;
  const terminationMs = Date.parse(terminationDate);
  const slaDeadlineMs = terminationMs + contractualSlaDays * 24 * 60 * 60 * 1000;
  const slaDeadline = new Date(slaDeadlineMs).toISOString();

  const exportsResult = await listExportCustodyRecords(orgId);
  if (!exportsResult.ok) return exportsResult;
  const qualifyingExports = exportsResult.data.filter(
    (r: CustodyRecord) => Date.parse(r.timestamp) >= terminationMs,
  );

  const certsResult = await listDataDestructionCertificates(orgId);
  if (!certsResult.ok) return certsResult;
  const latestCert: DataDestructionCertificate | null = certsResult.data[0] ?? null;

  let destructionCertificateAllClear = false;
  let destructionCertificateVerified = false;
  if (latestCert) {
    destructionCertificateAllClear = latestCert.verification.allClear;
    const tamperResult = await verifyDataDestructionCertificate(latestCert.id);
    if (!tamperResult.ok) return tamperResult;
    destructionCertificateVerified = tamperResult.data.verified;
  }

  const destructionClosesIt =
    latestCert !== null && destructionCertificateAllClear && destructionCertificateVerified;
  const exportClosesIt = qualifyingExports.length > 0;
  const dataAccountedFor = destructionClosesIt || exportClosesIt;

  const closingTimestampsMs: number[] = [];
  if (destructionClosesIt && latestCert) closingTimestampsMs.push(Date.parse(latestCert.issuedAt));
  if (exportClosesIt) {
    for (const r of qualifyingExports) closingTimestampsMs.push(Date.parse(r.timestamp));
  }
  const withinSla =
    dataAccountedFor && closingTimestampsMs.every((ms) => ms <= slaDeadlineMs);

  const reasons: string[] = [];
  if (!dataAccountedFor) {
    reasons.push(
      "no post-termination export-custody record and no all-clear, tamper-verified data-destruction " +
        "certificate exist for this org -- neither half of the return-or-destroy requirement is satisfied",
    );
  }
  if (dataAccountedFor && !withinSla) {
    reasons.push(
      `the closing event(s) landed after the contractual SLA deadline (${slaDeadline})`,
    );
  }
  if (latestCert && !destructionCertificateAllClear) {
    reasons.push(`the most recent data-destruction certificate (${latestCert.id}) is not all-clear`);
  }
  if (latestCert && !destructionCertificateVerified) {
    reasons.push(
      `the most recent data-destruction certificate (${latestCert.id}) failed its tamper-evidence check`,
    );
  }

  return {
    ok: true,
    data: {
      orgId,
      terminationDate,
      contractualSlaDays,
      slaDeadline,
      qualifyingExportRecordIds: qualifyingExports.map((r) => r.id),
      destructionCertificateId: latestCert?.id ?? null,
      destructionCertificateAllClear,
      destructionCertificateVerified,
      destructionCertificateIssuedAt: latestCert?.issuedAt ?? null,
      dataAccountedFor,
      withinSla,
      compliant: dataAccountedFor && withinSla,
      reasons,
    },
  };
}

// --------------------------------------------------------- Attestation

export interface VendorOffboardingAttestation {
  id: string;
  orgId: string;
  requestedBy: string; // actor who filed the request that led here (maker)
  issuedBy: string; // second, distinct owner-role approver (checker)
  issuedAt: string; // RFC3339
  evidence: VendorOffboardingEvidence;
  evidenceDigest: string; // sha256 hex of the canonical JSON of `evidence`, at issuance time
  auditLogEntryId: string; // requestId of the audit_log row minted for this attestation's issuance
}

function isEvidence(value: unknown): value is VendorOffboardingEvidence {
  const v = value as Partial<VendorOffboardingEvidence> | null;
  return (
    !!v &&
    typeof v.orgId === "string" &&
    typeof v.terminationDate === "string" &&
    typeof v.contractualSlaDays === "number" &&
    typeof v.slaDeadline === "string" &&
    Array.isArray(v.qualifyingExportRecordIds) &&
    (v.destructionCertificateId === null || typeof v.destructionCertificateId === "string") &&
    typeof v.destructionCertificateAllClear === "boolean" &&
    typeof v.destructionCertificateVerified === "boolean" &&
    (v.destructionCertificateIssuedAt === null || typeof v.destructionCertificateIssuedAt === "string") &&
    typeof v.dataAccountedFor === "boolean" &&
    typeof v.withinSla === "boolean" &&
    typeof v.compliant === "boolean" &&
    Array.isArray(v.reasons)
  );
}

function isAttestation(value: unknown): value is VendorOffboardingAttestation {
  const a = value as Partial<VendorOffboardingAttestation> | null;
  return (
    !!a &&
    typeof a.id === "string" &&
    typeof a.orgId === "string" &&
    typeof a.requestedBy === "string" &&
    typeof a.issuedBy === "string" &&
    typeof a.issuedAt === "string" &&
    typeof a.evidenceDigest === "string" &&
    typeof a.auditLogEntryId === "string" &&
    isEvidence(a.evidence)
  );
}

function parseAttestation(raw: string): VendorOffboardingAttestation | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isAttestation(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, VendorOffboardingAttestation>>> {
  const cm = await getConfigMap(VENDOR_OFFBOARDING_NAMESPACE, VENDOR_OFFBOARDING_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, VendorOffboardingAttestation>();
  for (const [id, raw] of Object.entries(data)) {
    const parsed = parseAttestation(raw);
    if (parsed) out.set(id, parsed);
  }
  return { ok: true, data: out };
}

/** Real list of every vendor-offboarding attestation for one org, newest
 * first. */
export async function listVendorOffboardingAttestations(
  orgId: string,
): Promise<K8sResult<VendorOffboardingAttestation[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  const rows = Array.from(all.data.values())
    .filter((a) => a.orgId === orgId)
    .sort((a, b) => Date.parse(b.issuedAt) - Date.parse(a.issuedAt));
  return { ok: true, data: rows };
}

export async function getVendorOffboardingAttestation(
  id: string,
): Promise<K8sResult<VendorOffboardingAttestation | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(id) ?? null };
}

function canonicalDigest(evidence: VendorOffboardingEvidence): string {
  // Stable field order -- never `JSON.stringify(evidence)` directly, whose
  // key order follows insertion order and would silently change the
  // digest if this interface's field declaration order ever changes.
  const canonical = {
    orgId: evidence.orgId,
    terminationDate: evidence.terminationDate,
    contractualSlaDays: evidence.contractualSlaDays,
    slaDeadline: evidence.slaDeadline,
    qualifyingExportRecordIds: [...evidence.qualifyingExportRecordIds].sort(),
    destructionCertificateId: evidence.destructionCertificateId,
    destructionCertificateAllClear: evidence.destructionCertificateAllClear,
    destructionCertificateVerified: evidence.destructionCertificateVerified,
    destructionCertificateIssuedAt: evidence.destructionCertificateIssuedAt,
    dataAccountedFor: evidence.dataAccountedFor,
    withinSla: evidence.withinSla,
    compliant: evidence.compliant,
  };
  return createHash("sha256").update(JSON.stringify(canonical)).digest("hex");
}

export type IssueVendorOffboardingAttestationError = "not_compliant";

/**
 * Mints one real, durable Vendor Offboarding Attestation. FAILS CLOSED:
 * refuses with `"not_compliant"` unless the passed-in `evidence` itself
 * reports `compliant: true` -- this function never re-derives looseness
 * from a caller's own summary, callers MUST pass the real,
 * freshly-computed `computeVendorOffboardingEvidence` result, not a
 * cached or hand-built one, so the attestation always attests to what
 * was checked moments before issuance.
 */
export async function issueVendorOffboardingAttestation(input: {
  orgId: string;
  requestedBy: string;
  issuedBy: string;
  evidence: VendorOffboardingEvidence;
}): Promise<
  K8sResult<VendorOffboardingAttestation> | { ok: false; error: IssueVendorOffboardingAttestationError }
> {
  if (!input.evidence.compliant) {
    return { ok: false, error: "not_compliant" };
  }

  const id = globalThis.crypto.randomUUID();
  const issuedAt = new Date().toISOString();
  const requestId = newRequestId();

  const entry: AuditLogEntry = {
    requestId,
    timestamp: issuedAt,
    actor: input.issuedBy,
    method: "ISSUE",
    path: `/vendor-offboarding/${input.orgId}/${id}`,
    status: 200,
    orgId: input.orgId,
    vendorOffboardingAction: "attestation_issued",
    vendorOffboardingAttestationId: id,
  };
  await writeAuditLogEntryAwaited(entry);

  const attestation: VendorOffboardingAttestation = {
    id,
    orgId: input.orgId,
    requestedBy: input.requestedBy,
    issuedBy: input.issuedBy,
    issuedAt,
    evidence: input.evidence,
    evidenceDigest: canonicalDigest(input.evidence),
    auditLogEntryId: requestId,
  };

  const write = await createOrUpdateConfigMap(VENDOR_OFFBOARDING_NAMESPACE, VENDOR_OFFBOARDING_CONFIGMAP, {
    [id]: JSON.stringify(attestation),
  });
  if (!write.ok) return write;
  return { ok: true, data: attestation };
}

// --------------------------------------------------------- Tamper-evidence

export interface VendorOffboardingAttestationVerification {
  verified: boolean;
  attestationId: string;
  reasons: string[];
}

/**
 * Real tamper-evidence check for one attestation -- the same
 * `computeRowHash`-anchored pattern lib/export-custody.ts's
 * `verifyExportCustody` and lib/data-destruction-certificate.ts's
 * `verifyDataDestructionCertificate` already establish: re-fetches the
 * exact audit_log row this attestation's `auditLogEntryId` points at,
 * recomputes ITS `row_hash` from its own stored `prev_hash` and fields,
 * confirms it still matches the stored `row_hash`, cross-checks the
 * row's own `orgId`/`actor` still agree with the attestation, AND
 * recomputes `evidenceDigest` from the attestation's own stored
 * `evidence` object to catch a hand-edited ConfigMap row (e.g. one
 * edited to claim `compliant: true` after the fact) that a bare
 * audit-row hash check alone would miss.
 */
export async function verifyVendorOffboardingAttestation(
  attestationId: string,
): Promise<K8sResult<VendorOffboardingAttestationVerification>> {
  const attResult = await getVendorOffboardingAttestation(attestationId);
  if (!attResult.ok) return attResult;
  const attestation = attResult.data;
  if (!attestation) {
    return {
      ok: true,
      data: { verified: false, attestationId, reasons: ["no such vendor-offboarding attestation"] },
    };
  }

  const reasons: string[] = [];

  const recomputedDigest = canonicalDigest(attestation.evidence);
  if (recomputedDigest !== attestation.evidenceDigest) {
    reasons.push(
      "the stored evidence does not match this attestation's own evidenceDigest -- the record was modified after issuance",
    );
  }

  const segmentResult = await getAuditLogChainSegmentByRequestId(attestation.auditLogEntryId);
  if (!segmentResult.ok) return segmentResult;
  const segment = segmentResult.data;

  if (!segment) {
    reasons.push(
      "the audit_log row this attestation points at no longer exists (or predates hash-chaining) -- not verifiable",
    );
    return { ok: true, data: { verified: false, attestationId, reasons } };
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
  if (segment.orgId !== attestation.orgId) {
    reasons.push(
      `audit_log row ${segment.id}'s org_id ("${segment.orgId ?? "none"}") no longer matches this attestation's orgId ("${attestation.orgId}")`,
    );
  }
  if (segment.actor !== attestation.issuedBy) {
    reasons.push(
      `audit_log row ${segment.id}'s actor ("${segment.actor}") no longer matches this attestation's issuedBy ("${attestation.issuedBy}")`,
    );
  }

  return { ok: true, data: { verified: reasons.length === 0, attestationId, reasons } };
}
