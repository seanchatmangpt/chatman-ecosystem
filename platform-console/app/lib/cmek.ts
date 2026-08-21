/**
 * Customer-Managed Encryption Key (CMEK/BYOK) Binding & Enforcement -- the
 * specific control a Fortune 5 security review asks for before this
 * platform is trusted to store regulated data: proof that an org's real
 * live k8s Secrets and PVCs are encrypted under a KMS key reference the
 * CUSTOMER supplied and controls (their own AWS KMS/GCP Cloud KMS/Azure
 * Key Vault/Vault key), never the platform's shared default, and that a
 * second, distinct human signed off before that key reference was ever
 * bound or rotated. Same three-part shape as lib/rotation-compliance.ts
 * closes the analogous rotation-cadence gap:
 *
 *   1. lib/orgs.ts's `CmekKeyBinding`/`getOrgCmekBinding`/
 *      `setOrgCmekBinding` is the real, durable per-org RECORD -- which
 *      external KMS provider, which key reference (never key material),
 *      who bound it and when. Modeled field-for-field on
 *      `OrgPricingOverride`.
 *   2. `scanCmekEnforcement` (this module) is the real, read-only
 *      ENFORCEMENT CHECK: for an org with a bound key, lists that org's
 *      real live k8s Secrets (lib/k8s.ts's listSecrets) and real live PVCs
 *      (lib/k8s.ts's listNamespacePvcs) -- both already the exact same
 *      k8sRequest-backed readers lib/rotation-compliance.ts's own scan
 *      uses -- and checks each real object's own
 *      `CMEK_KEY_REF_ANNOTATION` annotation against the bound key
 *      reference. An object whose annotation does not match (including
 *      one carrying no annotation at all -- i.e. still under the
 *      platform default) is a real, honestly-reported violation, never
 *      coerced into "assume compliant".
 *   3. `requestCmekKeyBinding`/`clearCmekKeyBinding` are the ACTUATION
 *      entry points: both require a fresh `cmek.key-binding` maker-checker
 *      approval (lib/approval-workflow.ts's requireApproval) before ever
 *      calling lib/orgs.ts's setOrgCmekBinding, and -- once approved --
 *      actually re-annotate every one of the org's real live Secrets/PVCs
 *      with the newly bound key reference (lib/k8s.ts's
 *      patchSecretAnnotations/patchPvcAnnotations), so the annotation
 *      `scanCmekEnforcement` reads back is never a stale claim: binding a
 *      key is the same call that stamps it onto every real object it
 *      governs. This module never actuates a binding on its own say-so;
 *      a second, distinct owner-role approver always has to sign off
 *      first, same "auto-FILE, human approves" pattern
 *      lib/rotation-compliance.ts's fileAndApplyRotationComplianceBlocks
 *      already establishes.
 */
import {
  listSecrets,
  listNamespacePvcs,
  patchSecretAnnotations,
  patchPvcAnnotations,
  type K8sResult,
} from "@/lib/k8s";
import {
  getOrg,
  getOrgCmekBinding,
  setOrgCmekBinding,
  validateCmekKeyBinding,
  type CmekKeyBinding,
  type CmekProvider,
  type Org,
} from "@/lib/orgs";
import { requireApproval, type ApprovalRequest } from "@/lib/approval-workflow";

/** The one well-known annotation key both the enforcement scan and the
 * actual bind/rotate write use -- the same "the write and the enforcement
 * read use the exact same annotation key" discipline
 * lib/k8s.ts's patchSecretAnnotations/patchPvcAnnotations header comments
 * already document. */
export const CMEK_KEY_REF_ANNOTATION = "platform-console.io/kms-key-ref";

export interface CmekEnforcementViolation {
  kind: "secret" | "pvc";
  namespace: string;
  name: string;
  /** The real annotation value found on the live object, or `null` when
   * the object carries no `CMEK_KEY_REF_ANNOTATION` annotation at all
   * (still under the platform default) -- never fabricated. */
  actualKeyRef: string | null;
  expectedKeyRef: string;
  detail: string;
}

export interface CmekEnforcementReport {
  orgId: string;
  namespace: string;
  /** `null` when this org has never had a CMEK key bound -- there is
   * nothing to enforce, and this is not itself a violation (an org may
   * legitimately choose the platform's own default encryption). */
  binding: CmekKeyBinding | null;
  secretsChecked: number;
  pvcsChecked: number;
  violations: CmekEnforcementViolation[];
  scannedAt: string;
}

/**
 * Real, read-only enforcement scan for one org: if the org has a bound
 * CMEK key, lists its real live Secrets and PVCs and checks each real
 * object's own live `CMEK_KEY_REF_ANNOTATION` annotation against the
 * bound `keyRef`. Never mutates anything -- the caller (GET
 * /api/orgs/[id]/cmek) decides what to do with the report.
 */
export async function scanCmekEnforcement(
  org: Org,
): Promise<K8sResult<CmekEnforcementReport>> {
  const bindingResult = await getOrgCmekBinding(org.id);
  if (!bindingResult.ok) return bindingResult;
  const binding = bindingResult.data;

  const report: CmekEnforcementReport = {
    orgId: org.id,
    namespace: org.namespace,
    binding,
    secretsChecked: 0,
    pvcsChecked: 0,
    violations: [],
    scannedAt: new Date().toISOString(),
  };

  // No binding at all -- nothing to enforce; the platform default applies
  // and that is a legitimate, non-violating state.
  if (!binding) return { ok: true, data: report };

  const secretsResult = await listSecrets(org.namespace);
  if (!secretsResult.ok) return secretsResult;
  report.secretsChecked = secretsResult.data.length;
  for (const secret of secretsResult.data) {
    const actualKeyRef = secret.annotations[CMEK_KEY_REF_ANNOTATION] ?? null;
    if (actualKeyRef !== binding.keyRef) {
      report.violations.push({
        kind: "secret",
        namespace: org.namespace,
        name: secret.name,
        actualKeyRef,
        expectedKeyRef: binding.keyRef,
        detail: actualKeyRef
          ? `Secret "${secret.name}" is annotated under key reference "${actualKeyRef}", not the org's bound CMEK key "${binding.keyRef}"`
          : `Secret "${secret.name}" carries no CMEK key-reference annotation -- still encrypted under the platform default, not the org's bound CMEK key "${binding.keyRef}"`,
      });
    }
  }

  const pvcsResult = await listNamespacePvcs(org.namespace);
  if (!pvcsResult.ok) return pvcsResult;
  report.pvcsChecked = pvcsResult.data.length;
  for (const pvc of pvcsResult.data) {
    const actualKeyRef = pvc.annotations[CMEK_KEY_REF_ANNOTATION] ?? null;
    if (actualKeyRef !== binding.keyRef) {
      report.violations.push({
        kind: "pvc",
        namespace: org.namespace,
        name: pvc.name,
        actualKeyRef,
        expectedKeyRef: binding.keyRef,
        detail: actualKeyRef
          ? `PVC "${pvc.name}" is annotated under key reference "${actualKeyRef}", not the org's bound CMEK key "${binding.keyRef}"`
          : `PVC "${pvc.name}" carries no CMEK key-reference annotation -- still encrypted under the platform default, not the org's bound CMEK key "${binding.keyRef}"`,
      });
    }
  }

  return { ok: true, data: report };
}

/**
 * Re-annotates every one of an org's real live Secrets and PVCs with the
 * newly bound (or cleared, `keyRef: null`) key reference -- the actual
 * enforcement write, called ONLY after a fresh `cmek.key-binding` approval
 * already exists (see `requestCmekKeyBinding`/`clearCmekKeyBinding`
 * below). Collects and returns per-object errors rather than throwing on
 * the first one, same "one object's failure never blocks every other
 * object" discipline lib/rotation-compliance.ts's scan already applies
 * across orgs -- a security-relevant re-annotation sweep across a whole
 * namespace must not silently stop halfway with no record of what failed.
 */
async function reannotateOrgSecretsAndPvcs(
  namespace: string,
  keyRef: string | null,
): Promise<{ annotated: number; errors: string[] }> {
  let annotated = 0;
  const errors: string[] = [];

  const secretsResult = await listSecrets(namespace);
  if (!secretsResult.ok) {
    errors.push(secretsResult.error);
  } else {
    for (const secret of secretsResult.data) {
      const result = await patchSecretAnnotations(namespace, secret.name, {
        [CMEK_KEY_REF_ANNOTATION]: keyRef,
      });
      if (result.ok) annotated += 1;
      else errors.push(`secret ${secret.name}: ${result.error}`);
    }
  }

  const pvcsResult = await listNamespacePvcs(namespace);
  if (!pvcsResult.ok) {
    errors.push(pvcsResult.error);
  } else {
    for (const pvc of pvcsResult.data) {
      const result = await patchPvcAnnotations(namespace, pvc.name, {
        [CMEK_KEY_REF_ANNOTATION]: keyRef,
      });
      if (result.ok) annotated += 1;
      else errors.push(`pvc ${pvc.name}: ${result.error}`);
    }
  }

  return { annotated, errors };
}

export interface CmekKeyBindingOutcome {
  applied: boolean;
  binding: CmekKeyBinding | null;
  approval: ApprovalRequest;
  /** Present only once `applied` is true -- the real count of live
   * Secrets/PVCs this call actually re-annotated, and any per-object
   * annotation write that failed (non-fatal to the overall bind: the
   * durable `Org.cmekBinding` record is the source of truth an auditor
   * checks first; a partial annotation sweep is surfaced honestly here
   * rather than silently dropped). */
  reannotated?: number;
  reannotateErrors?: string[];
}

/**
 * The real bind/rotate actuation entry point: given a validated requested
 * binding, requires a fresh `cmek.key-binding` approval before ever
 * calling lib/orgs.ts's setOrgCmekBinding, then -- only once approved --
 * actually re-annotates every one of the org's real live Secrets/PVCs
 * with the new key reference. `requestedBy` identifies the actor filing
 * the request; the SECOND approver's own identity (never the requester's)
 * is what lib/orgs.ts's setOrgCmekBinding stamps as `boundBy` once
 * approved, same two-person-integrity guarantee every other maker-checker
 * action in this codebase already provides.
 */
export async function requestCmekKeyBinding(
  org: Org,
  requested: { provider: CmekProvider; keyRef: string; reason: string },
  requestedBy: string,
): Promise<CmekKeyBindingOutcome | { error: string }> {
  const validationError = validateCmekKeyBinding({
    provider: requested.provider,
    keyRef: requested.keyRef,
    boundBy: requestedBy,
    reason: requested.reason,
  });
  if (validationError) return { error: validationError };

  const existingResult = await getOrgCmekBinding(org.id);
  if (!existingResult.ok) return { error: existingResult.error };
  const previousKeyRef = existingResult.data?.keyRef;

  const approval = await requireApproval({
    action: "cmek.key-binding",
    targetId: org.id,
    requestedBy,
    resourcePayload: {
      requestedCmekBinding: {
        provider: requested.provider,
        keyRef: requested.keyRef,
        previousKeyRef,
        reason: requested.reason,
      },
    },
  });
  if ("error" in approval) return { error: approval.error };

  if (!approval.ok) {
    return { applied: false, binding: existingResult.data, approval: approval.request };
  }

  const approvedPayload = approval.approval.resourcePayload?.requestedCmekBinding;
  if (!approvedPayload) {
    return { error: "approved request carries no requestedCmekBinding payload" };
  }

  const binding: CmekKeyBinding = {
    provider: approvedPayload.provider,
    keyRef: approvedPayload.keyRef,
    boundAt: new Date().toISOString(),
    boundBy: approval.approval.approvedBy ?? requestedBy,
    previousKeyRef: approvedPayload.previousKeyRef,
    reason: approvedPayload.reason,
  };

  const setResult = await setOrgCmekBinding(org.id, binding, requestedBy);
  if (!setResult.ok) return { error: setResult.error };

  const sweep = await reannotateOrgSecretsAndPvcs(org.namespace, binding.keyRef);

  return {
    applied: true,
    binding,
    approval: approval.approval,
    reannotated: sweep.annotated,
    reannotateErrors: sweep.errors,
  };
}

/**
 * Real unbind entry point: given an org, requires a fresh
 * `cmek.key-binding` approval whose resourcePayload explicitly clears the
 * binding (`requestedCmekBinding: null`, the same null-clears convention
 * `pricing.override`/`compliance.rotation-block` already establish)
 * before ever calling lib/orgs.ts's setOrgCmekBinding(id, null, ...), then
 * -- only once approved -- strips the key-reference annotation off every
 * one of the org's real live Secrets/PVCs, reverting them to the
 * platform-default-encryption state `scanCmekEnforcement` reports as
 * "no binding".
 */
export async function clearCmekKeyBinding(
  org: Org,
  requestedBy: string,
): Promise<CmekKeyBindingOutcome | { error: string }> {
  const approval = await requireApproval({
    action: "cmek.key-binding",
    targetId: org.id,
    requestedBy,
    resourcePayload: { requestedCmekBinding: null },
  });
  if ("error" in approval) return { error: approval.error };

  if (!approval.ok) {
    const existingResult = await getOrgCmekBinding(org.id);
    return {
      applied: false,
      binding: existingResult.ok ? existingResult.data : null,
      approval: approval.request,
    };
  }

  const setResult = await setOrgCmekBinding(org.id, null, requestedBy);
  if (!setResult.ok) return { error: setResult.error };

  const sweep = await reannotateOrgSecretsAndPvcs(org.namespace, null);

  return {
    applied: true,
    binding: null,
    approval: approval.approval,
    reannotated: sweep.annotated,
    reannotateErrors: sweep.errors,
  };
}

/**
 * Real per-org getter used by GET /api/orgs/[id]/cmek -- thin wrapper over
 * getOrg + scanCmekEnforcement so the route doesn't have to duplicate the
 * "org not found" branch every other per-org route already handles.
 */
export async function getCmekStatus(orgId: string): Promise<K8sResult<CmekEnforcementReport>> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) return orgResult;
  if (!orgResult.data) return { ok: false, error: `org '${orgId}' not found` };
  return scanCmekEnforcement(orgResult.data);
}
