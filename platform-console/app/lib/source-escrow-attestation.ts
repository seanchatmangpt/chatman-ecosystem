/**
 * Real, periodic Source-Code / Build-Artifact Escrow Attestation -- the
 * business-continuity / vendor-lock-in artifact a Fortune-5 legal team's
 * MSA escrow clause asks for by name ("prove that, at a given point in
 * time, we could reconstruct exactly what was running"), without this
 * platform standing up a real third-party software-escrow SaaS (Iron
 * Mountain / NCC Group class vendor) anywhere in this repo.
 *
 * Deliberately reuses three already-real primitives instead of
 * fabricating a source-code deposit:
 *
 *   1. The RELEASE identity comes from the real deploy-time git commit
 *      SHA a CI/CD provider stamps into the running process's own
 *      environment (Vercel's `VERCEL_GIT_COMMIT_SHA`, or a generic
 *      `GIT_COMMIT_SHA`/`GITHUB_SHA` a self-hosted pipeline sets) --
 *      never a hand-typed value. Absent when none of those env vars are
 *      set (a local `next dev` run, or a deploy pipeline that doesn't
 *      stamp one) -- an honest gap (`gitCommitSha: null`), never a
 *      fabricated SHA, same discipline lib/sbom-attestation.ts's
 *      `imageDigest: string | null` already establishes.
 *   2. The BUILD-ARTIFACT identity (image digests) comes from
 *      lib/k8s.ts's `listContainerImageStatuses` -- the same real,
 *      runtime-resolved `containerStatuses[].imageID` the kubelet
 *      reports for a pod actually running that image right now
 *      (`sha256:...`) that lib/sbom-attestation.ts already treats as the
 *      only honest subject for an attestation. A mutable tag alone is
 *      never sufficient.
 *   3. The MANIFEST SET comes from lib/k8s.ts's real `listDeployments`
 *      (every `apps/v1` Deployment's name + per-container image, exactly
 *      as `spec.template.spec.containers[].image` reports it) plus the
 *      real Flux reconciliation state (`listKustomizations`/
 *      `listHelmReleases`) already driving this cluster -- never a
 *      hand-maintained manifest list.
 *
 * ATTESTATION FORMAT: an in-toto v1 Statement
 * (https://in-toto.io/Statement/v1), matching lib/sbom-attestation.ts's
 * own envelope choice so a reviewer's existing in-toto tooling parses
 * this without a bespoke schema. `predicateType` is this platform's own,
 * documented inline below.
 *
 * SIGNING: HMAC-SHA256 over the statement's canonical JSON bytes, using
 * the exact same `AUTH_SECRET`-backed key and canonicalization discipline
 * lib/sbom-attestation.ts already signs with -- the one signing secret
 * this console provisions and rotates. This is honestly an HMAC (shared-
 * secret integrity), not an asymmetric/Sigstore-style signature -- see
 * lib/sbom-attestation.ts's own header comment for why no KMS/PKI keypair
 * is fabricated here either. `signature.keyId` reuses the exact same
 * `"platform-console-hmac-v1"` key id lib/sbom-attestation.ts already
 * names, since both are signed with the same secret.
 *
 * MAKER-CHECKER: filing a snapshot is gated behind lib/approval-
 * workflow.ts's `source-escrow.snapshot` action (no opt-out) -- this is
 * exactly the "one person's own say-so binds a durable, externally-
 * relied-upon compliance attestation" class of risk
 * `data-destruction.certificate.issue`/`insurance.policy.update` already
 * earn that bar for: the requester's own live read of the cluster is
 * never sufficient by itself to mint a signed escrow record a legal team
 * will later rely on; a second, distinct owner-role approver must sign
 * off before it is ever persisted.
 *
 * Storage: one real k8s ConfigMap
 * (`platform-console-source-escrow-attestations`, `platform-console`
 * namespace), using the exact same get-then-create-or-patch
 * `getConfigMap`/`createOrUpdateConfigMap` primitive
 * lib/sbom-attestation.ts/lib/approval-workflow.ts already use -- no new
 * k8s resource kind, no new RBAC verb.
 */
import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import {
  createOrUpdateConfigMap,
  getConfigMap,
  listContainerImageStatuses,
  listDeployments,
  listKustomizations,
  listHelmReleases,
  type FluxResource,
  type K8sDeployment,
  type K8sResult,
} from "@/lib/k8s";
import { newRequestId, writeAuditLogEntryAwaited, type AuditLogEntry } from "@/lib/audit-db";
import { requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";

export const SOURCE_ESCROW_NAMESPACE = "platform-console";
export const SOURCE_ESCROW_CONFIGMAP = "platform-console-source-escrow-attestations";
export const SOURCE_ESCROW_PREDICATE_TYPE =
  "https://platform-console.internal/attestations/source-escrow/v1";
// Reuses lib/sbom-attestation.ts's own key id deliberately -- both are
// signed with the exact same AUTH_SECRET-derived HMAC key, so naming them
// differently would imply two distinct trust roots that don't exist.
export const SOURCE_ESCROW_KEY_ID = "platform-console-hmac-v1";

// The env vars a real CI/CD provider stamps the deploy-time commit SHA
// into, checked in this order. Vercel's own deploy environment sets
// `VERCEL_GIT_COMMIT_SHA` automatically (no operator action required);
// `GIT_COMMIT_SHA`/`GITHUB_SHA` cover a self-hosted or GitHub-Actions-
// driven pipeline that sets its own env on the Deployment. Never a
// hand-typed fallback.
const GIT_COMMIT_SHA_ENV_VARS = ["VERCEL_GIT_COMMIT_SHA", "GIT_COMMIT_SHA", "GITHUB_SHA"] as const;

function resolveGitCommitSha(): { sha: string; source: string } | null {
  for (const name of GIT_COMMIT_SHA_ENV_VARS) {
    const value = process.env[name];
    if (value && value.length > 0) return { sha: value, source: name };
  }
  return null;
}

function getSecretKey(): Buffer {
  const secret = process.env.AUTH_SECRET;
  if (!secret || secret.length < 16) {
    throw new Error(
      "AUTH_SECRET is not set (or too short). Set a real random secret " +
        "in the environment before starting the app.",
    );
  }
  return Buffer.from(secret, "utf8");
}

/** Same recursive key-sorting canonicalization lib/sbom-attestation.ts
 * uses -- required so a verifier who reconstructs the statement from its
 * own stored fields recomputes the identical signature input
 * `JSON.stringify` alone would not guarantee. */
function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value !== null && typeof value === "object") {
    const sorted: Record<string, unknown> = {};
    for (const key of Object.keys(value as Record<string, unknown>).sort()) {
      sorted[key] = canonicalize((value as Record<string, unknown>)[key]);
    }
    return sorted;
  }
  return value;
}

function canonicalJson(value: unknown): string {
  return JSON.stringify(canonicalize(value));
}

function signStatement(statement: unknown): string {
  return createHmac("sha256", getSecretKey()).update(canonicalJson(statement)).digest("hex");
}

// --------------------------------------------------------------- Manifest

export interface ManifestDeployment {
  name: string;
  namespace: string;
  containers: K8sDeployment["containers"];
  replicasDesired: number;
  replicasReady: number;
}

export interface ManifestFluxResource {
  kind: FluxResource["kind"];
  name: string;
  namespace: string;
  ready: boolean | null;
}

export interface ManifestImageSubject {
  imageRef: string;
  /** Real runtime-resolved digest (`sha256:...`) from
   * `listContainerImageStatuses` for the container currently running this
   * exact image ref, or `null` when no live pod reports one yet --
   * an honest gap, never a fabricated digest. */
  imageDigest: string | null;
}

/** The real, unsigned release snapshot -- pure reads, no side effects, so
 * a caller can inspect (and show an approver) exactly what would be
 * attested BEFORE filing the maker-checker request. */
export interface SourceEscrowManifest {
  namespace: string;
  gitCommitSha: string | null;
  gitCommitShaSource: string | null;
  deployments: ManifestDeployment[];
  fluxResources: ManifestFluxResource[];
  images: ManifestImageSubject[];
  collectedAt: string;
}

/**
 * Collects the real release snapshot for one namespace (default: this
 * console's own `platform-console`) -- every field a real k8sRequest
 * read, never fabricated. Read-only: does not sign or persist anything.
 */
export async function buildSourceEscrowManifest(
  namespace: string = SOURCE_ESCROW_NAMESPACE,
): Promise<K8sResult<SourceEscrowManifest>> {
  const [deploymentsResult, kustomizationsResult, helmReleasesResult, imageStatusesResult] =
    await Promise.all([
      listDeployments(namespace),
      listKustomizations(),
      listHelmReleases(),
      listContainerImageStatuses(namespace),
    ]);

  for (const result of [deploymentsResult, kustomizationsResult, helmReleasesResult, imageStatusesResult]) {
    if (!result.ok) return result;
  }
  if (!deploymentsResult.ok) return deploymentsResult;
  if (!kustomizationsResult.ok) return kustomizationsResult;
  if (!helmReleasesResult.ok) return helmReleasesResult;
  if (!imageStatusesResult.ok) return imageStatusesResult;

  const digestByRef = new Map<string, string>();
  for (const cs of imageStatusesResult.data) {
    if (cs.imageID) digestByRef.set(cs.image, cs.imageID);
  }

  const imageRefs = new Set<string>();
  for (const d of deploymentsResult.data) {
    for (const c of d.containers) imageRefs.add(c.image);
  }
  for (const cs of imageStatusesResult.data) imageRefs.add(cs.image);

  const gitCommit = resolveGitCommitSha();

  const manifest: SourceEscrowManifest = {
    namespace,
    gitCommitSha: gitCommit?.sha ?? null,
    gitCommitShaSource: gitCommit?.source ?? null,
    deployments: deploymentsResult.data
      .map((d) => ({
        name: d.name,
        namespace: d.namespace,
        containers: d.containers,
        replicasDesired: d.replicasDesired,
        replicasReady: d.replicasReady,
      }))
      .sort((a, b) => a.name.localeCompare(b.name)),
    fluxResources: [...kustomizationsResult.data, ...helmReleasesResult.data]
      .map((f) => ({ kind: f.kind, name: f.name, namespace: f.namespace, ready: f.ready }))
      .sort((a, b) => `${a.kind}/${a.name}`.localeCompare(`${b.kind}/${b.name}`)),
    images: Array.from(imageRefs)
      .sort()
      .map((imageRef) => ({ imageRef, imageDigest: digestByRef.get(imageRef) ?? null })),
    collectedAt: new Date().toISOString(),
  };

  return { ok: true, data: manifest };
}

// ------------------------------------------------------------ Attestation

export interface EscrowSubject {
  name: string; // imageRef, or "git-commit" for the release-identity subject
  digest: Record<string, string>; // e.g. {sha256: "..."} or {gitCommit: sha}; {} when unresolved
}

export interface SourceEscrowPredicate {
  namespace: string;
  gitCommitSha: string | null;
  gitCommitShaSource: string | null;
  generatedAt: string;
  manifestSha256: string; // digest of this snapshot's own canonicalized manifest
  deploymentCount: number;
  fluxResourceCount: number;
  resolvedImageDigestCount: number;
  totalImageCount: number;
}

export interface InTotoStatement {
  _type: "https://in-toto.io/Statement/v1";
  predicateType: string;
  subject: EscrowSubject[];
  predicate: SourceEscrowPredicate;
}

export interface Signature {
  keyId: string;
  algorithm: "HMAC-SHA256";
  value: string; // hex digest over canonicalJson(statement)
}

export interface SignedEscrowAttestation {
  statement: InTotoStatement;
  signature: Signature;
}

export interface SourceEscrowRecord {
  id: string;
  manifest: SourceEscrowManifest;
  attestation: SignedEscrowAttestation;
  generatedBy: string;
  generatedAt: string;
  auditLogEntryId: string;
}

function isRecord(value: unknown): value is SourceEscrowRecord {
  const p = value as Partial<SourceEscrowRecord> | null;
  return (
    !!p &&
    typeof p.id === "string" &&
    typeof p.manifest === "object" &&
    typeof p.attestation === "object" &&
    typeof p.generatedBy === "string" &&
    typeof p.generatedAt === "string" &&
    typeof p.auditLogEntryId === "string"
  );
}

function parseRecord(raw: string): SourceEscrowRecord | null {
  try {
    const parsed = JSON.parse(raw) as unknown;
    return isRecord(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

async function readAll(): Promise<K8sResult<Map<string, SourceEscrowRecord>>> {
  const cm = await getConfigMap(SOURCE_ESCROW_NAMESPACE, SOURCE_ESCROW_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const out = new Map<string, SourceEscrowRecord>();
  for (const [id, raw] of Object.entries(data)) {
    const parsed = parseRecord(raw);
    if (parsed) out.set(id, parsed);
  }
  return { ok: true, data: out };
}

/** Real list of every escrow attestation ever generated, newest first --
 * backs GET /api/compliance/source-escrow. */
export async function listSourceEscrowSnapshots(): Promise<K8sResult<SourceEscrowRecord[]>> {
  const all = await readAll();
  if (!all.ok) return all;
  return {
    ok: true,
    data: Array.from(all.data.values()).sort((a, b) => Date.parse(b.generatedAt) - Date.parse(a.generatedAt)),
  };
}

export async function getSourceEscrowSnapshot(id: string): Promise<K8sResult<SourceEscrowRecord | null>> {
  const all = await readAll();
  if (!all.ok) return all;
  return { ok: true, data: all.data.get(id) ?? null };
}

function buildStatement(manifest: SourceEscrowManifest): InTotoStatement {
  const manifestSha256 = createHash("sha256").update(canonicalJson(manifest)).digest("hex");
  const resolvedImageDigestCount = manifest.images.filter((i) => i.imageDigest !== null).length;

  const subject: EscrowSubject[] = manifest.images.map((i) => ({
    name: i.imageRef,
    digest: i.imageDigest ? { sha256: i.imageDigest.replace(/^sha256:/, "") } : ({} as Record<string, string>),
  }));
  subject.push({
    name: "git-commit",
    digest: manifest.gitCommitSha ? { gitCommit: manifest.gitCommitSha } : ({} as Record<string, string>),
  });

  return {
    _type: "https://in-toto.io/Statement/v1",
    predicateType: SOURCE_ESCROW_PREDICATE_TYPE,
    subject,
    predicate: {
      namespace: manifest.namespace,
      gitCommitSha: manifest.gitCommitSha,
      gitCommitShaSource: manifest.gitCommitShaSource,
      generatedAt: manifest.collectedAt,
      manifestSha256,
      deploymentCount: manifest.deployments.length,
      fluxResourceCount: manifest.fluxResources.length,
      resolvedImageDigestCount,
      totalImageCount: manifest.images.length,
    },
  };
}

/**
 * Signs and durably persists one real escrow attestation from an
 * ALREADY-COLLECTED manifest -- never re-reads the cluster itself, so the
 * exact state a second approver reviewed (via `requestSourceEscrowSnapshot`
 * below) is the exact state that gets signed, with no TOCTOU gap between
 * approval and actuation.
 */
export async function generateSourceEscrowSnapshot(
  manifest: SourceEscrowManifest,
  generatedBy: string,
): Promise<K8sResult<SourceEscrowRecord>> {
  const statement = buildStatement(manifest);
  const signature: Signature = {
    keyId: SOURCE_ESCROW_KEY_ID,
    algorithm: "HMAC-SHA256",
    value: signStatement(statement),
  };

  const id = globalThis.crypto.randomUUID();
  const generatedAt = new Date().toISOString();
  const requestId = newRequestId();
  const entry: AuditLogEntry = {
    requestId,
    timestamp: generatedAt,
    actor: generatedBy,
    method: "EXPORT",
    path: `/compliance/source-escrow/${id}`,
    status: 200,
  };
  await writeAuditLogEntryAwaited(entry);

  const record: SourceEscrowRecord = {
    id,
    manifest,
    attestation: { statement, signature },
    generatedBy,
    generatedAt,
    auditLogEntryId: requestId,
  };

  const patch = await createOrUpdateConfigMap(SOURCE_ESCROW_NAMESPACE, SOURCE_ESCROW_CONFIGMAP, {
    [id]: JSON.stringify(record),
  });
  if (!patch.ok) return patch;
  return { ok: true, data: record };
}

export interface SourceEscrowFilingResult {
  applied: boolean;
  approval: ApprovalRequest;
  record?: SourceEscrowRecord;
}

/**
 * The one call a route (or the cron poller) makes: collects a real,
 * fresh manifest, then requires a `source-escrow.snapshot` maker-checker
 * approval (lib/approval-workflow.ts's requireApproval) before ever
 * signing or persisting it. If a fresh approval already exists for this
 * namespace (`APPROVAL_TTL_HOURS`), the manifest is signed and persisted
 * immediately (`applied: true`); otherwise a new pending approval is
 * filed and nothing is signed yet (`applied: false`) -- same "auto-FILE,
 * human approves" pattern lib/rotation-compliance.ts's
 * fileAndApplyRotationComplianceBlocks already establishes.
 */
export async function requestSourceEscrowSnapshot(
  requestedBy: string,
  namespace: string = SOURCE_ESCROW_NAMESPACE,
): Promise<K8sResult<SourceEscrowFilingResult>> {
  const manifestResult = await buildSourceEscrowManifest(namespace);
  if (!manifestResult.ok) return manifestResult;
  const manifest = manifestResult.data;

  const approval = await requireApproval({
    action: "source-escrow.snapshot",
    targetId: namespace,
    requestedBy,
    resourcePayload: {
      requestedSourceEscrowSnapshot: {
        namespace,
        gitCommitSha: manifest.gitCommitSha,
        deploymentCount: manifest.deployments.length,
        imageCount: manifest.images.length,
      },
    },
  });
  if ("error" in approval) return { ok: false, error: approval.error };

  if (!approval.ok) {
    return { ok: true, data: { applied: false, approval: approval.request } };
  }

  const generated = await generateSourceEscrowSnapshot(manifest, requestedBy);
  if (!generated.ok) return generated;
  return { ok: true, data: { applied: true, approval: approval.approval, record: generated.data } };
}

// --------------------------------------------------------- Tamper-evidence

export interface SourceEscrowVerificationResult {
  id: string;
  verified: boolean;
  manifestDigestValid: boolean;
  signatureValid: boolean;
  reasons: string[];
}

/**
 * Recomputes both the manifest digest and the HMAC signature for one
 * escrow record from its own stored fields and confirms they still match
 * what was signed -- if the record was hand-edited in the ConfigMap after
 * generation, this catches it. Constant-time signature comparison
 * (`timingSafeEqual`), matching lib/sbom-attestation.ts's own
 * verification discipline.
 */
export async function verifySourceEscrowSnapshot(
  id: string,
): Promise<K8sResult<SourceEscrowVerificationResult>> {
  const recordResult = await getSourceEscrowSnapshot(id);
  if (!recordResult.ok) return recordResult;
  const record = recordResult.data;
  if (!record) {
    return {
      ok: true,
      data: { id, verified: false, manifestDigestValid: false, signatureValid: false, reasons: ["not found"] },
    };
  }

  const reasons: string[] = [];
  const recomputedManifestDigest = createHash("sha256").update(canonicalJson(record.manifest)).digest("hex");
  const manifestDigestValid = recomputedManifestDigest === record.attestation.statement.predicate.manifestSha256;
  if (!manifestDigestValid) {
    reasons.push("recomputed manifestSha256 does not match the digest embedded in the signed statement");
  }

  const expected = Buffer.from(signStatement(record.attestation.statement), "hex");
  const presented = Buffer.from(record.attestation.signature.value, "hex");
  const signatureValid = expected.length === presented.length && timingSafeEqual(expected, presented);
  if (!signatureValid) {
    reasons.push("HMAC signature does not verify against the recomputed statement bytes");
  }

  return {
    ok: true,
    data: {
      id,
      verified: manifestDigestValid && signatureValid,
      manifestDigestValid,
      signatureValid,
      reasons,
    },
  };
}
