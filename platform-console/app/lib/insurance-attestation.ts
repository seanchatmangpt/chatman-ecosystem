/**
 * Real Certificate of Insurance (COI) On-Demand Attestation -- closes the
 * one pre-signature evidence gap none of this repo's other compliance
 * exports (lib/security-questionnaire-export.ts's CAIQ/SIG bundle,
 * lib/subprocessors.ts's DPA Schedule, lib/data-destruction-certificate.ts's
 * teardown proof) cover: a Fortune-5 procurement/legal reviewer's
 * standing pre-signature ask, "prove you actually carry cyber/E&O/general
 * liability coverage, in what amounts, from whom, and that it hasn't
 * lapsed" -- a claim that requires this platform's OWN insurance policy
 * metadata to be stored somewhere durable and versioned, not a PDF
 * someone in finance emails around by hand.
 *
 * Storage: one real k8s ConfigMap
 * (`platform-console-insurance-policies`, `platform-console` namespace),
 * the exact get-then-create-or-patch getConfigMap/createOrUpdateConfigMap
 * primitive lib/subprocessors.ts/lib/data-destruction-certificate.ts
 * already use -- no new k8s resource kind, no new RBAC verb. Key shape:
 * one key per coverage type (`InsuranceCoverageType`, already
 * ConfigMap-key-safe) -> JSON APPEND-ONLY array of
 * InsurancePolicyVersion, the exact same
 * append-only-array-in-one-ConfigMap-value versioning pattern
 * lib/subprocessors.ts's SubprocessorChangeEvent history and
 * lib/dpa-records.ts's own per-org record history already establish --
 * a policy's carrier, limits, or expiry changing is always visible
 * history, never a silent overwrite, which is exactly what "versioned"
 * in this capability's own name requires: a reviewer can see not just
 * today's coverage but what it was as of any past renewal.
 *
 * Maker-checker: every mutation (recording a new or renewed policy
 * version) goes through the exact same lib/approval-workflow.ts
 * `requireApproval` gate `subprocessor.registry.update`/
 * `pricing.override` already use -- the metadata this module stores is
 * what a Fortune-5 counterparty's legal team will rely on before they
 * sign a contract; a single owner unilaterally widening/narrowing a
 * declared coverage limit or silently shortening an expiry is exactly
 * the "can quietly change a real compliance/security posture claim this
 * platform makes to a THIRD PARTY" class of risk those two actions
 * already earn this bar for. One owner's own say-so is never sufficient;
 * a second, distinct owner-role approver must sign off before a policy
 * record is ever recorded.
 *
 * PDF generation: `generateInsuranceAttestationPdf` renders the
 * platform's own CURRENT (most recent, non-lapsed-as-of-generation-time)
 * policy per coverage type into a real, minimal, standards-conformant
 * single-page PDF -- built by hand from Node's standard library only
 * (this repo has no PDF library installed anywhere in
 * app/node_modules), the same "no new third-party archiver dependency,
 * build the real file format directly" discipline lib/zip.ts's own
 * header comment documents for ZIP. Per-org branding (lib/orgs.ts's
 * `OrgBranding.productName`/`accentColor`) is applied to the header when
 * an org is given, same "reads already-real branding fields, never
 * fabricates new ones" discipline every other per-org-branded artifact
 * in this repo already follows; the accent color governs a single title
 * bar rectangle, drawn with the real PDF `re`/`f` fill operators, not a
 * decorative flourish requiring an image asset.
 *
 * Every generation (like lib/security-questionnaire-export.ts's own
 * bundle generation) is itself an auditable READ, not a mutation: it
 * writes one durable audit-log row and one history-record ConfigMap key
 * so a reviewer can prove an attestation was produced, by whom, and
 * against which policy versions, even after the PDF bytes themselves
 * were downloaded and discarded -- the PDF bytes are never persisted,
 * same "never persist what can be honestly recomputed from durable
 * state" discipline lib/security-questionnaire-export.ts's own header
 * comment states.
 */
import { createHash } from "node:crypto";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getOrg, type Org } from "@/lib/orgs";
import { newRequestId, writeAuditLogEntryAwaited, type AuditLogEntry } from "@/lib/audit-db";

export const INSURANCE_POLICIES_NAMESPACE = "platform-console";
export const INSURANCE_POLICIES_CONFIGMAP = "platform-console-insurance-policies";
export const INSURANCE_ATTESTATIONS_CONFIGMAP = "platform-console-insurance-attestations";

export type InsuranceCoverageType = "cyber" | "errors_omissions" | "general_liability";

export const INSURANCE_COVERAGE_TYPES: InsuranceCoverageType[] = [
  "cyber",
  "errors_omissions",
  "general_liability",
];

function isInsuranceCoverageType(value: unknown): value is InsuranceCoverageType {
  return value === "cyber" || value === "errors_omissions" || value === "general_liability";
}

/** The non-secret shape of one insurance policy's metadata -- never the
 * policy DOCUMENT itself (no PDF of the underlying carrier policy is
 * ever stored here), only the facts a COI summary states: who
 * underwrites it, the policy number, the coverage limit, and the window
 * it is in force for. */
export interface InsurancePolicyRecord {
  coverageType: InsuranceCoverageType;
  carrier: string;
  policyNumber: string;
  coverageLimitUsd: number;
  effectiveDate: string; // RFC3339 date
  expiryDate: string; // RFC3339 date
  /** Optional carrier financial-strength rating (e.g. "A+ (Superior)",
   * AM Best) a procurement reviewer sometimes asks for alongside the
   * limit -- omitted when not on file, never fabricated. */
  amBestRating?: string;
}

/** One real, immutable version of a policy record -- the unit this
 * module's ConfigMap value append-only array actually stores, one per
 * (coverageType, mutation). Mirrors lib/subprocessors.ts's
 * SubprocessorChangeEvent shape field-for-field. */
export interface InsurancePolicyVersion {
  record: InsurancePolicyRecord;
  recordedByIdentifier: string; // the second, distinct approver who signed off
  requestedByIdentifier: string; // the maker who filed the request
  recordedAt: string; // RFC3339
}

export interface InsurancePolicyCurrent {
  coverageType: InsuranceCoverageType;
  record: InsurancePolicyRecord | null;
  history: InsurancePolicyVersion[];
}

function isInsurancePolicyRecord(value: unknown): value is InsurancePolicyRecord {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    isInsuranceCoverageType(v.coverageType) &&
    typeof v.carrier === "string" &&
    typeof v.policyNumber === "string" &&
    typeof v.coverageLimitUsd === "number" &&
    typeof v.effectiveDate === "string" &&
    typeof v.expiryDate === "string" &&
    (v.amBestRating === undefined || typeof v.amBestRating === "string")
  );
}

function isInsurancePolicyVersion(value: unknown): value is InsurancePolicyVersion {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    isInsurancePolicyRecord(v.record) &&
    typeof v.recordedByIdentifier === "string" &&
    typeof v.requestedByIdentifier === "string" &&
    typeof v.recordedAt === "string"
  );
}

function isInsurancePolicyVersionArray(value: unknown): value is InsurancePolicyVersion[] {
  return Array.isArray(value) && value.every(isInsurancePolicyVersion);
}

async function getAll(): Promise<K8sResult<Record<string, InsurancePolicyVersion[]>>> {
  const existing = await getConfigMap(INSURANCE_POLICIES_NAMESPACE, INSURANCE_POLICIES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, InsurancePolicyVersion[]> = {};
  for (const [coverageType, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (isInsurancePolicyVersionArray(rows)) parsed[coverageType] = rows;
      // A hand-edited or corrupt value is skipped, not fatal -- same
      // discipline lib/subprocessors.ts's getAll uses for its own
      // ConfigMap.
    } catch {
      // ignore -- malformed JSON for this coverage type's key
    }
  }
  return { ok: true, data: parsed };
}

function toCurrent(coverageType: InsuranceCoverageType, history: InsurancePolicyVersion[]): InsurancePolicyCurrent {
  const sorted = [...history].sort((a, b) => a.recordedAt.localeCompare(b.recordedAt));
  const last = sorted[sorted.length - 1] ?? null;
  return { coverageType, record: last ? last.record : null, history: sorted };
}

/** Every coverage type this registry knows about, each with its current
 * (most recently recorded) policy record and its full version history --
 * backs GET /api/owner/insurance-attestation. Coverage types with no
 * version ever recorded still appear, with `record: null`, so a
 * reviewer sees the full, honest 3-type checklist rather than only
 * whatever happens to already be on file. */
export async function listInsurancePolicies(): Promise<K8sResult<InsurancePolicyCurrent[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  return {
    ok: true,
    data: INSURANCE_COVERAGE_TYPES.map((t) => toCurrent(t, all.data[t] ?? [])),
  };
}

export async function getInsurancePolicy(
  coverageType: InsuranceCoverageType,
): Promise<K8sResult<InsurancePolicyCurrent>> {
  const all = await getAll();
  if (!all.ok) return all;
  return { ok: true, data: toCurrent(coverageType, all.data[coverageType] ?? []) };
}

/**
 * Appends one real, approved policy version. Called ONLY after a fresh
 * `insurance.policy.update` approval already exists (the caller, PUT
 * /api/owner/insurance-attestation, binds exactly the approved
 * `resourcePayload.requestedInsurancePolicy`, same "bind exactly what
 * was approved" discipline PUT /api/orgs/[id]/pricing-override already
 * establishes) -- this function itself performs no approval check, same
 * separation of concerns lib/subprocessors.ts's applySubprocessorChange
 * (writer) vs. its route (approval gate) already establishes.
 */
export async function recordInsurancePolicyVersion(input: {
  record: InsurancePolicyRecord;
  recordedByIdentifier: string;
  requestedByIdentifier: string;
}): Promise<K8sResult<InsurancePolicyVersion>> {
  const all = await getAll();
  if (!all.ok) return all;

  const existingHistory = all.data[input.record.coverageType] ?? [];
  const version: InsurancePolicyVersion = {
    record: input.record,
    recordedByIdentifier: input.recordedByIdentifier,
    requestedByIdentifier: input.requestedByIdentifier,
    recordedAt: new Date().toISOString(),
  };
  const updatedHistory = [...existingHistory, version];

  const write = await createOrUpdateConfigMap(INSURANCE_POLICIES_NAMESPACE, INSURANCE_POLICIES_CONFIGMAP, {
    [input.record.coverageType]: JSON.stringify(updatedHistory),
  });
  if (!write.ok) return write;
  return { ok: true, data: version };
}

// ------------------------------------------------------------ Attestation

export interface InsuranceAttestationManifest {
  id: string;
  orgId: string | null;
  orgName: string | null;
  generatedAt: string;
  generatedBy: string;
  auditLogEntryId: string;
  /** Which coverage types actually had a current, non-expired-as-of-
   * generation-time record included -- an honest per-section coverage
   * indicator, mirroring lib/security-questionnaire-export.ts's own
   * `sectionAvailability` field. */
  coverageIncluded: Record<InsuranceCoverageType, boolean>;
}

function isManifest(value: unknown): value is InsuranceAttestationManifest {
  const v = value as Partial<InsuranceAttestationManifest> | null;
  return (
    !!v &&
    typeof v.id === "string" &&
    typeof v.generatedAt === "string" &&
    typeof v.generatedBy === "string" &&
    typeof v.auditLogEntryId === "string" &&
    typeof v.coverageIncluded === "object" &&
    v.coverageIncluded !== null
  );
}

function parseManifest(raw: string): InsuranceAttestationManifest | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isManifest(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/** Real, newest-first history of every attestation PDF ever generated --
 * backs GET /api/owner/insurance-attestation?history=1. Manifests only
 * (no PDF bytes are ever persisted, see this module's header comment). */
export async function listInsuranceAttestations(): Promise<K8sResult<InsuranceAttestationManifest[]>> {
  const cm = await getConfigMap(INSURANCE_POLICIES_NAMESPACE, INSURANCE_ATTESTATIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const manifests: InsuranceAttestationManifest[] = [];
  for (const raw of Object.values(data)) {
    const parsed = parseManifest(raw);
    if (parsed) manifests.push(parsed);
  }
  manifests.sort((a, b) => Date.parse(b.generatedAt) - Date.parse(a.generatedAt));
  return { ok: true, data: manifests };
}

/**
 * Assembles the manifest for a fresh attestation, writes the durable
 * audit-log row + history record, and returns both the manifest and the
 * live current policy records the PDF renderer will use -- read-only
 * against the policy registry itself (no maker-checker gate: reading and
 * summarizing already-recorded, already-approved policy state is not a
 * mutation, same "generating an export is itself an auditable read, not
 * a sensitive mutation" posture lib/security-questionnaire-export.ts's
 * own generateSecurityQuestionnaireBundle already establishes).
 */
export async function generateInsuranceAttestation(
  orgId: string | null,
  generatedBy: string,
): Promise<K8sResult<{ manifest: InsuranceAttestationManifest; policies: InsurancePolicyCurrent[] }>> {
  let org: Org | null = null;
  if (orgId) {
    const orgResult = await getOrg(orgId);
    if (!orgResult.ok) return orgResult;
    org = orgResult.data;
    if (!org) return { ok: false, error: `org '${orgId}' not found` };
  }

  const policiesResult = await listInsurancePolicies();
  if (!policiesResult.ok) return policiesResult;
  const policies = policiesResult.data;

  const now = Date.now();
  const coverageIncluded = Object.fromEntries(
    INSURANCE_COVERAGE_TYPES.map((t) => {
      const current = policies.find((p) => p.coverageType === t);
      const included = !!current?.record && Date.parse(current.record.expiryDate) >= now;
      return [t, included];
    }),
  ) as Record<InsuranceCoverageType, boolean>;

  const generatedAt = new Date().toISOString();
  const id = globalThis.crypto.randomUUID();
  const requestId = newRequestId();

  const entry: AuditLogEntry = {
    requestId,
    timestamp: generatedAt,
    actor: generatedBy,
    method: "EXPORT",
    path: `/insurance-attestation/${id}${org ? `?orgId=${encodeURIComponent(org.id)}` : ""}`,
    status: 200,
    ...(org ? { orgId: org.id } : {}),
  };
  await writeAuditLogEntryAwaited(entry);

  const manifest: InsuranceAttestationManifest = {
    id,
    orgId: org ? org.id : null,
    orgName: org ? org.name : null,
    generatedAt,
    generatedBy,
    auditLogEntryId: requestId,
    coverageIncluded,
  };

  const write = await createOrUpdateConfigMap(INSURANCE_POLICIES_NAMESPACE, INSURANCE_ATTESTATIONS_CONFIGMAP, {
    [id]: JSON.stringify(manifest),
  });
  if (!write.ok) return write;

  return { ok: true, data: { manifest, policies } };
}

// -------------------------------------------------------- PDF rendering

const COVERAGE_LABEL: Record<InsuranceCoverageType, string> = {
  cyber: "Cyber Liability",
  errors_omissions: "Errors & Omissions (E&O)",
  general_liability: "Commercial General Liability",
};

function pdfEscape(text: string): string {
  // The three characters the PDF literal-string syntax (`( ... )`)
  // requires escaped -- real PDF spec (ISO 32000-1 7.3.4.2), not a
  // heuristic.
  return text.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

function usd(cents_or_dollars: number): string {
  return `$${cents_or_dollars.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function hexColorToRgbUnit(hex: string): [number, number, number] {
  const m = /^#?([0-9a-fA-F]{6})$/.exec(hex.trim());
  if (!m) return [0.1, 0.1, 0.4]; // honest fallback for a malformed/unset accent color
  const n = parseInt(m[1], 16);
  return [((n >> 16) & 0xff) / 255, ((n >> 8) & 0xff) / 255, (n & 0xff) / 255];
}

/**
 * Renders one real, minimal, single-page PDF (ISO 32000-1) entirely by
 * hand from Node's standard library -- one Catalog, one Pages tree, one
 * Page with a Contents stream drawing a title bar rectangle (per-org
 * accent color, when known) and left-aligned Helvetica text lines, plus
 * the one Type1/Helvetica Font resource every line references. No
 * compression, no external assets (a logo URL is disclosed as text, not
 * fetched/embedded -- fetching an arbitrary customer-supplied URL into a
 * generated compliance PDF would be a real SSRF surface this module
 * deliberately does not open), no third-party PDF library -- this repo
 * has none installed, same "build the real file format directly"
 * discipline lib/zip.ts's own header comment documents for ZIP.
 */
export function renderInsuranceAttestationPdf(input: {
  manifest: InsuranceAttestationManifest;
  policies: InsurancePolicyCurrent[];
  org: Org | null;
}): Buffer {
  const { manifest, policies, org } = input;
  const [r, g, b] = hexColorToRgbUnit(org?.branding?.accentColor ?? "#1F2A44");
  const productName = org?.branding?.productName ?? "Platform Console";
  const title = org ? `Certificate of Insurance -- ${org.name}` : "Certificate of Insurance -- Platform-Wide";

  const lines: string[] = [];
  let y = 700;
  const emit = (text: string, size = 11) => {
    lines.push(`BT /F1 ${size} Tf 56 ${y} Td (${pdfEscape(text)}) Tj ET`);
    y -= size + 8;
  };

  const content: string[] = [];
  // Title bar rectangle, filled with the org's own accent color (or the
  // honest fallback above).
  content.push(`${r.toFixed(3)} ${g.toFixed(3)} ${b.toFixed(3)} rg 0 760 612 32 re f`);
  content.push(`1 1 1 rg BT /F1 16 Tf 56 768 Td (${pdfEscape(title)}) Tj ET`);
  content.push(`0 0 0 rg`);

  y = 730;
  emit(`Issued by: ${productName}`, 10);
  emit(`Generated: ${manifest.generatedAt}`, 10);
  emit(`Generated by: ${manifest.generatedBy}`, 10);
  emit(`Attestation ID: ${manifest.id}`, 10);
  emit(`Audit log entry: ${manifest.auditLogEntryId}`, 10);
  y -= 10;

  for (const type of INSURANCE_COVERAGE_TYPES) {
    const current = policies.find((p) => p.coverageType === type);
    const record = current?.record ?? null;
    emit(COVERAGE_LABEL[type], 13);
    if (!record) {
      emit("  No policy on file for this coverage type.", 10);
      y -= 6;
      continue;
    }
    const expired = Date.parse(record.expiryDate) < Date.now();
    emit(`  Carrier: ${record.carrier}`, 10);
    emit(`  Policy Number: ${record.policyNumber}`, 10);
    emit(`  Coverage Limit: ${usd(record.coverageLimitUsd)}`, 10);
    emit(`  Effective: ${record.effectiveDate}    Expires: ${record.expiryDate}${expired ? "  (LAPSED)" : ""}`, 10);
    if (record.amBestRating) emit(`  Carrier Rating: ${record.amBestRating}`, 10);
    y -= 6;
  }
  content.push(...lines);

  const contentStream = content.join("\n");

  const objects: string[] = [];
  objects.push("<< /Type /Catalog /Pages 2 0 R >>"); // 1
  objects.push("<< /Type /Pages /Kids [3 0 R] /Count 1 >>"); // 2
  objects.push(
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
  ); // 3
  objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"); // 4
  objects.push(
    `<< /Length ${Buffer.byteLength(contentStream, "utf8")} >>\nstream\n${contentStream}\nendstream`,
  ); // 5

  const header = "%PDF-1.4\n";
  const chunks: string[] = [header];
  const offsets: number[] = [];
  let offset = Buffer.byteLength(header, "utf8");
  objects.forEach((body, i) => {
    offsets.push(offset);
    const obj = `${i + 1} 0 obj\n${body}\nendobj\n`;
    chunks.push(obj);
    offset += Buffer.byteLength(obj, "utf8");
  });

  const xrefStart = offset;
  const xrefLines = [`xref`, `0 ${objects.length + 1}`, `0000000000 65535 f `];
  for (const off of offsets) {
    xrefLines.push(`${off.toString().padStart(10, "0")} 00000 n `);
  }
  chunks.push(xrefLines.join("\n") + "\n");
  chunks.push(
    `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefStart}\n%%EOF`,
  );

  return Buffer.from(chunks.join(""), "utf8");
}

/** sha256 digest of the rendered PDF bytes -- lets a caller (or a later
 * audit-log reader) cite a stable content hash for a given attestation's
 * output without the platform persisting the PDF bytes themselves. */
export function digestInsuranceAttestationPdf(pdf: Buffer): string {
  return createHash("sha256").update(pdf).digest("hex");
}
