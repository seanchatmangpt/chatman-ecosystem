/**
 * Security Questionnaire Evidence Bundle Export (CAIQ/SIG-style) -- the
 * single downloadable package a Fortune-5 procurement/security review
 * board asks for instead of a manual back-and-forth: "answer our standard
 * vendor security questionnaire with real evidence, not a slide deck."
 *
 * This module fabricates NOTHING new. It is purely an aggregator over five
 * already-real, already-shipped evidence primitives this platform
 * generates for other reasons, reframed into one CAIQ/SIG-style bundle:
 *
 *   1. SBOM / CVE provenance -- lib/sbom-attestation.ts's
 *      `listSbomAttestations`. The most recently generated signed
 *      in-toto attestation bundle (never re-triggers a scan or a fresh
 *      attestation itself -- POST /api/security-scan/sbom is the one real
 *      place that happens; this only reads what already exists).
 *   2. Secret/certificate rotation compliance -- lib/rotation-
 *      compliance.ts's `scanRotationCompliance`, a fresh live read against
 *      real k8s Secrets and real parsed X.509 certificates every call
 *      (cheap, read-only -- unlike the SBOM section there is no expensive
 *      scan Job to avoid re-running).
 *   3. Data residency attestation -- lib/data-residency-attestation.ts's
 *      `listResidencyAttestations`, this org's most recent immutable,
 *      already-persisted attestation row (never runs a fresh scan here
 *      either -- POST /api/orgs/[id]/residency-attestations is that real
 *      entry point; an evidence EXPORT should reflect the last attested
 *      period, not silently trigger a new one).
 *   4. SSO/SCIM role-mapping drift -- lib/sso-role-drift.ts's
 *      `computeSsoRoleDrift`, given this org's real configured
 *      `SsoGroupRoleMapping[]` (lib/orgs.ts's `getOrgSsoGroupMappings`)
 *      and its real, live `OrgRoleAssignment[]` (lib/authz.ts's
 *      `getOrgRoleAssignmentsIn`) -- always computed fresh, it is a pure
 *      diff over two cheap reads.
 *   5. Audit-log hash-chain integrity -- lib/audit-integrity.ts's
 *      `verifyHashChain`, a fresh live per-row re-derivation over this
 *      org's own audit_log slice.
 *
 * Sections 3-5 require a real org (they are meaningless platform-wide --
 * residency/SSO/audit integrity are per-tenant claims). When no `orgId` is
 * given, or the org has never produced a given artifact, that section is
 * included with an honest `available: false` + reason rather than either
 * omitted silently or backfilled with fabricated data -- a reviewer
 * reading the manifest sees exactly which questionnaire answers this
 * platform can back with evidence today and which it cannot yet.
 *
 * BUNDLING: reuses lib/zip.ts's dependency-free `buildZip` the same way
 * lib/export-all.ts already does -- one JSON evidence file per section
 * plus a `manifest.json` index, zipped into a single downloadable archive.
 * No new k8s resource kind, no new archiver dependency.
 *
 * HISTORY: one real ConfigMap record per generated bundle
 * (`platform-console-security-questionnaire-exports`,
 * `platform-console` namespace), same get-then-create-or-patch
 * `getConfigMap`/`createOrUpdateConfigMap` primitive
 * lib/sbom-attestation.ts already uses -- no new k8s resource kind, no new
 * RBAC verb. The archive bytes themselves are NOT persisted (a
 * questionnaire bundle is regenerated on demand from live/already-real
 * evidence, same "never persist what can be honestly recomputed"
 * discipline lib/audit-integrity.ts's own module doc states for its
 * verification result) -- only the generation record (who, when, for
 * which org, which sections were actually available) is durable, so a
 * reviewer can prove an export happened even after the archive itself was
 * downloaded and discarded.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  type K8sResult,
} from "@/lib/k8s";
import { newRequestId, writeAuditLogEntryAwaited, type AuditLogEntry } from "@/lib/audit-db";
import { getOrg, getOrgSsoGroupMappings, type Org } from "@/lib/orgs";
import { getOrgRoleAssignmentsIn } from "@/lib/authz";
import { listSbomAttestations, type SbomAttestationRecord } from "@/lib/sbom-attestation";
import { scanRotationCompliance, type OrgRotationComplianceReport } from "@/lib/rotation-compliance";
import { listResidencyAttestations, type ResidencyAttestation } from "@/lib/data-residency-attestation";
import { computeSsoRoleDrift, type SsoRoleDriftReport } from "@/lib/sso-role-drift";
import { verifyHashChain, type HashChainVerificationResult } from "@/lib/audit-integrity";
import { buildZip, type ZipEntryInput } from "@/lib/zip";

export const SECURITY_QUESTIONNAIRE_NAMESPACE = "platform-console";
export const SECURITY_QUESTIONNAIRE_CONFIGMAP = "platform-console-security-questionnaire-exports";

/** One evidence section of the bundle -- `available: false` is an honest,
 * typed gap (never a fabricated/backfilled answer), always paired with a
 * human-readable `reason` a reviewer can read straight off the manifest. */
export type EvidenceSection<T> =
  | { available: true; data: T }
  | { available: false; reason: string };

export interface SecurityQuestionnaireEvidence {
  sbom: EvidenceSection<SbomAttestationRecord>;
  rotationCompliance: EvidenceSection<OrgRotationComplianceReport>;
  dataResidency: EvidenceSection<ResidencyAttestation>;
  ssoRoleDrift: EvidenceSection<SsoRoleDriftReport>;
  auditIntegrity: EvidenceSection<HashChainVerificationResult>;
}

export interface SecurityQuestionnaireManifest {
  id: string;
  orgId: string | null;
  orgName: string | null;
  generatedAt: string;
  generatedBy: string;
  auditLogEntryId: string;
  /** Section name -> whether that section carried real evidence in this
   * bundle, so a reviewer (or this record's own history listing) can see
   * coverage at a glance without opening the archive. */
  sectionAvailability: Record<keyof SecurityQuestionnaireEvidence, boolean>;
}

export interface SecurityQuestionnaireBundle {
  manifest: SecurityQuestionnaireManifest;
  evidence: SecurityQuestionnaireEvidence;
}

function isRecord(value: unknown): value is SecurityQuestionnaireManifest {
  const p = value as Partial<SecurityQuestionnaireManifest> | null;
  return (
    !!p &&
    typeof p.id === "string" &&
    typeof p.generatedAt === "string" &&
    typeof p.generatedBy === "string" &&
    typeof p.auditLogEntryId === "string" &&
    typeof p.sectionAvailability === "object" &&
    p.sectionAvailability !== null
  );
}

function parseRecord(raw: string): SecurityQuestionnaireManifest | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isRecord(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/** Real, live-computed SBOM/CVE-provenance section: the most recently
 * generated signed attestation bundle, or an honest gap when none has
 * ever been generated (nudging the reviewer to POST
 * /api/security-scan/sbom first, never fabricating one here). */
async function buildSbomSection(): Promise<EvidenceSection<SbomAttestationRecord>> {
  const result = await listSbomAttestations();
  if (!result.ok) return { available: false, reason: `sbom attestation read failed: ${result.error}` };
  const latest = result.data[0];
  if (!latest) {
    return {
      available: false,
      reason: "no SBOM/CVE-provenance attestation has ever been generated -- run POST /api/security-scan/sbom against a completed vuln-scan job first",
    };
  }
  return { available: true, data: latest };
}

/** Real, live rotation-compliance section, scoped down to this one org's
 * own report out of the platform-wide scan -- `scanRotationCompliance`
 * itself has no per-org entry point, so the whole (cheap, read-only) scan
 * runs and this picks out the one org's slice. Platform-wide (no org)
 * requests get an honest "not org-scoped" gap: a rotation posture claim
 * only means something against one tenant's own Secrets/certificates. */
async function buildRotationSection(org: Org | null): Promise<EvidenceSection<OrgRotationComplianceReport>> {
  if (!org) {
    return { available: false, reason: "rotation compliance is an org-scoped claim -- pass orgId to include it" };
  }
  const scan = await scanRotationCompliance();
  const report = scan.orgs.find((o) => o.orgId === org.id);
  if (!report) {
    const err = scan.errors.find((e) => e.orgId === org.id || e.orgId === "*");
    return {
      available: false,
      reason: err ? `rotation compliance scan failed: ${err.error}` : `org '${org.id}' was not present in the rotation compliance scan`,
    };
  }
  return { available: true, data: report };
}

/** Real, already-persisted data-residency section: this org's newest
 * immutable attestation row, never a freshly triggered scan (see this
 * module's header comment for why). */
async function buildResidencySection(org: Org | null): Promise<EvidenceSection<ResidencyAttestation>> {
  if (!org) {
    return { available: false, reason: "data residency attestation is an org-scoped claim -- pass orgId to include it" };
  }
  const result = await listResidencyAttestations(org.id);
  if (!result.ok) return { available: false, reason: `residency attestation read failed: ${result.error}` };
  const latest = result.data[0];
  if (!latest) {
    return {
      available: false,
      reason: `org '${org.id}' has no residency attestation on record -- run POST /api/orgs/${org.id}/residency-attestations first`,
    };
  }
  return { available: true, data: latest };
}

/** Real, freshly computed SSO/SCIM role-mapping drift section, over this
 * org's real configured mappings and real live role assignments. */
async function buildSsoRoleDriftSection(org: Org | null): Promise<EvidenceSection<SsoRoleDriftReport>> {
  if (!org) {
    return { available: false, reason: "SSO role-mapping drift is an org-scoped claim -- pass orgId to include it" };
  }
  const [mappingsResult, assignmentsResult] = await Promise.all([
    getOrgSsoGroupMappings(org.id),
    getOrgRoleAssignmentsIn(org.namespace),
  ]);
  if (!mappingsResult.ok) return { available: false, reason: `SSO mapping read failed: ${mappingsResult.error}` };
  if (!assignmentsResult.ok) return { available: false, reason: `role assignment read failed: ${assignmentsResult.error}` };
  const report = computeSsoRoleDrift(org.id, mappingsResult.data, assignmentsResult.data);
  return { available: true, data: report };
}

/** Real, freshly re-derived audit-log hash-chain integrity section for
 * this org's own slice of `platform_console.audit_log`. */
async function buildAuditIntegritySection(org: Org | null): Promise<EvidenceSection<HashChainVerificationResult>> {
  if (!org) {
    return { available: false, reason: "audit hash-chain integrity is an org-scoped claim -- pass orgId to include it" };
  }
  const result = await verifyHashChain(org.id);
  if (!result.ok) return { available: false, reason: `hash-chain verification failed: ${result.error}` };
  return { available: true, data: result.data };
}

/**
 * Assembles the full evidence bundle for one org (or platform-wide, when
 * `orgId` is `null` -- only the SBOM section is meaningful without a
 * tenant boundary, every other section is an honest gap). Read-only:
 * touches no maker-checker workflow and mutates no cluster state -- it
 * only reads five already-real controls and writes one durable audit-log
 * row plus one history-record ConfigMap key, the same "generating an
 * export is itself an auditable read, not a sensitive mutation" posture
 * lib/sbom-attestation.ts's own `generateSbomAttestation` already
 * establishes.
 */
export async function generateSecurityQuestionnaireBundle(
  orgId: string | null,
  generatedBy: string,
): Promise<K8sResult<SecurityQuestionnaireBundle>> {
  let org: Org | null = null;
  if (orgId) {
    const orgResult = await getOrg(orgId);
    if (!orgResult.ok) return orgResult;
    org = orgResult.data;
    if (!org) return { ok: false, error: `org '${orgId}' not found` };
  }

  const [sbom, rotationCompliance, dataResidency, ssoRoleDrift, auditIntegrity] = await Promise.all([
    buildSbomSection(),
    buildRotationSection(org),
    buildResidencySection(org),
    buildSsoRoleDriftSection(org),
    buildAuditIntegritySection(org),
  ]);

  const evidence: SecurityQuestionnaireEvidence = {
    sbom,
    rotationCompliance,
    dataResidency,
    ssoRoleDrift,
    auditIntegrity,
  };

  const generatedAt = new Date().toISOString();
  const id = globalThis.crypto.randomUUID();
  const requestId = newRequestId();

  const entry: AuditLogEntry = {
    requestId,
    timestamp: generatedAt,
    actor: generatedBy,
    method: "EXPORT",
    path: `/security-questionnaire/${id}${org ? `?orgId=${encodeURIComponent(org.id)}` : ""}`,
    status: 200,
    ...(org ? { orgId: org.id } : {}),
  };
  await writeAuditLogEntryAwaited(entry);

  const manifest: SecurityQuestionnaireManifest = {
    id,
    orgId: org ? org.id : null,
    orgName: org ? org.name : null,
    generatedAt,
    generatedBy,
    auditLogEntryId: requestId,
    sectionAvailability: {
      sbom: sbom.available,
      rotationCompliance: rotationCompliance.available,
      dataResidency: dataResidency.available,
      ssoRoleDrift: ssoRoleDrift.available,
      auditIntegrity: auditIntegrity.available,
    },
  };

  const patch = await createOrUpdateConfigMap(SECURITY_QUESTIONNAIRE_NAMESPACE, SECURITY_QUESTIONNAIRE_CONFIGMAP, {
    [id]: JSON.stringify(manifest),
  });
  if (!patch.ok) return patch;

  return { ok: true, data: { manifest, evidence } };
}

/** Real, newest-first history of every bundle ever generated -- backs GET
 * /api/owner/security-questionnaire. Manifests only (no archive bytes are
 * ever persisted -- see this module's header comment). */
export async function listSecurityQuestionnaireExports(): Promise<K8sResult<SecurityQuestionnaireManifest[]>> {
  const cm = await getConfigMap(SECURITY_QUESTIONNAIRE_NAMESPACE, SECURITY_QUESTIONNAIRE_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const manifests: SecurityQuestionnaireManifest[] = [];
  for (const raw of Object.values(data)) {
    const parsed = parseRecord(raw);
    if (parsed) manifests.push(parsed);
  }
  manifests.sort((a, b) => Date.parse(b.generatedAt) - Date.parse(a.generatedAt));
  return { ok: true, data: manifests };
}

/** Renders a generated bundle into one downloadable ZIP archive: one JSON
 * file per evidence section (present or an honest `available: false`
 * gap), plus a `manifest.json` index. Pure/synchronous -- no I/O, mirrors
 * lib/export-all.ts's own "assemble entries, buildZip once" shape. */
export function buildSecurityQuestionnaireArchive(bundle: SecurityQuestionnaireBundle): {
  archive: Buffer;
  filename: string;
} {
  const entries: ZipEntryInput[] = [
    { name: "manifest.json", data: Buffer.from(JSON.stringify(bundle.manifest, null, 2) + "\n") },
    { name: "evidence/sbom-cve-provenance.json", data: Buffer.from(JSON.stringify(bundle.evidence.sbom, null, 2) + "\n") },
    { name: "evidence/secret-certificate-rotation-compliance.json", data: Buffer.from(JSON.stringify(bundle.evidence.rotationCompliance, null, 2) + "\n") },
    { name: "evidence/data-residency-attestation.json", data: Buffer.from(JSON.stringify(bundle.evidence.dataResidency, null, 2) + "\n") },
    { name: "evidence/sso-scim-role-mapping-drift.json", data: Buffer.from(JSON.stringify(bundle.evidence.ssoRoleDrift, null, 2) + "\n") },
    { name: "evidence/audit-log-hash-chain-integrity.json", data: Buffer.from(JSON.stringify(bundle.evidence.auditIntegrity, null, 2) + "\n") },
  ];
  const archive = buildZip(entries);
  const stamp = bundle.manifest.generatedAt.replace(/[:.]/g, "-");
  const orgSuffix = bundle.manifest.orgId ? `-${bundle.manifest.orgId}` : "";
  const filename = `security-questionnaire-evidence${orgSuffix}-${stamp}.zip`;
  return { archive, filename };
}
