/**
 * Real Policy-as-Code / Organization Policy surface (AWS Config Rules /
 * GCP Org Policy equivalent) -- read-only. This module lists the real,
 * live `admissionregistration.k8s.io/v1` ValidatingAdmissionPolicy and
 * ValidatingAdmissionPolicyBinding objects on this cluster (via the same
 * in-cluster ServiceAccount k8sRequest primitive every other lib/k8s.ts
 * module uses) and returns their real CEL rule text for display.
 *
 * The ENFORCEMENT itself does not live here or anywhere in this app: it
 * lives entirely at the k8s API server, which evaluates a
 * ValidatingAdmissionPolicy's CEL expression against every matching
 * admission request natively, in-process, before the object is ever
 * persisted. Applying `k8s/admission-policy.yaml`
 * (`kubectl apply -f k8s/admission-policy.yaml`) is what turns enforcement
 * on; this module only reads back what a cluster operator already applied
 * -- deleting the real object makes this page show nothing, exactly as it
 * should, because there would be nothing left to surface.
 *
 * "Recent denials": Kubernetes has no built-in "denial log" API --
 * `auditAnnotations` on a ValidatingAdmissionPolicy are written into the
 * API server's own audit log stream (if audit logging is enabled and
 * configured to capture them), not into any object this app can GET.
 * This cluster (kind-platform-eng-colima) does not currently ingest
 * kube-apiserver's audit log anywhere queryable from here -- so a live
 * "recent denials" list is honestly NOT currently buildable from this
 * app; see listActivePolicies' return shape and app/app/policy/page.tsx's
 * own disclosure of this gap.
 */
import { k8sRequest, type K8sResult } from "@/lib/k8s";

export interface PolicyValidation {
  expression: string;
  message: string | null;
  reason: string | null;
}

export interface PolicyMatchConstraint {
  apiGroups: string[];
  apiVersions: string[];
  operations: string[];
  resources: string[];
}

export interface ActiveValidatingAdmissionPolicy {
  name: string;
  failurePolicy: string | null;
  matchConstraints: PolicyMatchConstraint[];
  validations: PolicyValidation[];
  createdAt: string;
}

export interface PolicyBindingNamespaceRule {
  key: string;
  operator: string;
  values: string[];
}

export interface ActiveValidatingAdmissionPolicyBinding {
  name: string;
  policyName: string;
  validationActions: string[];
  namespaceSelectorRules: PolicyBindingNamespaceRule[];
  createdAt: string;
}

interface RawValidatingAdmissionPolicy {
  metadata: { name: string; creationTimestamp: string };
  spec?: {
    failurePolicy?: string;
    matchConstraints?: {
      resourceRules?: Array<{
        apiGroups?: string[];
        apiVersions?: string[];
        operations?: string[];
        resources?: string[];
      }>;
    };
    validations?: Array<{ expression: string; message?: string; reason?: string }>;
  };
}

interface RawValidatingAdmissionPolicyBinding {
  metadata: { name: string; creationTimestamp: string };
  spec?: {
    policyName?: string;
    validationActions?: string[];
    matchResources?: {
      namespaceSelector?: {
        matchExpressions?: Array<{ key: string; operator: string; values?: string[] }>;
      };
    };
  };
}

interface RawListResponse<T> {
  items?: T[];
}

/**
 * Lists the real, live ValidatingAdmissionPolicy objects cluster-wide,
 * exactly as the API server stores them -- CEL expression text included
 * verbatim (never reformatted or re-derived), so what this page shows is
 * provably the same text kube-apiserver itself evaluates.
 */
export async function listActiveValidatingAdmissionPolicies(): Promise<
  K8sResult<ActiveValidatingAdmissionPolicy[]>
> {
  const result = await k8sRequest<RawListResponse<RawValidatingAdmissionPolicy>>(
    "/apis/admissionregistration.k8s.io/v1/validatingadmissionpolicies",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      failurePolicy: item.spec?.failurePolicy ?? null,
      matchConstraints: (item.spec?.matchConstraints?.resourceRules ?? []).map((r) => ({
        apiGroups: r.apiGroups ?? [],
        apiVersions: r.apiVersions ?? [],
        operations: r.operations ?? [],
        resources: r.resources ?? [],
      })),
      validations: (item.spec?.validations ?? []).map((v) => ({
        expression: v.expression,
        message: v.message ?? null,
        reason: v.reason ?? null,
      })),
      createdAt: item.metadata.creationTimestamp,
    })),
  };
}

/**
 * Lists the real, live ValidatingAdmissionPolicyBinding objects
 * cluster-wide -- the object that actually scopes a policy down to which
 * namespaces/resources it applies to (`validationActions`,
 * `namespaceSelector`). A policy with zero bindings enforces nothing;
 * this is deliberately a separate list (mirroring the real, separate k8s
 * object kind) rather than merged into the policy above, so the page can
 * show the real relationship -- one policy, one or more bindings -- as-is.
 */
export async function listActiveValidatingAdmissionPolicyBindings(): Promise<
  K8sResult<ActiveValidatingAdmissionPolicyBinding[]>
> {
  const result = await k8sRequest<RawListResponse<RawValidatingAdmissionPolicyBinding>>(
    "/apis/admissionregistration.k8s.io/v1/validatingadmissionpolicybindings",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      policyName: item.spec?.policyName ?? "",
      validationActions: item.spec?.validationActions ?? [],
      namespaceSelectorRules: (
        item.spec?.matchResources?.namespaceSelector?.matchExpressions ?? []
      ).map((r) => ({ key: r.key, operator: r.operator, values: r.values ?? [] })),
      createdAt: item.metadata.creationTimestamp,
    })),
  };
}

export interface ActivePolicyBundle {
  policies: ActiveValidatingAdmissionPolicy[];
  bindings: ActiveValidatingAdmissionPolicyBinding[];
}

/**
 * Combines both real lists above in one call -- what app/app/policy/page.tsx
 * actually renders. Fails closed the same way listServicesWithEndpoints
 * (lib/k8s.ts) does: if either real GET fails, the whole call fails rather
 * than showing a partial, possibly-misleading picture of what's enforced.
 */
export async function listActivePolicies(): Promise<K8sResult<ActivePolicyBundle>> {
  const [policiesResult, bindingsResult] = await Promise.all([
    listActiveValidatingAdmissionPolicies(),
    listActiveValidatingAdmissionPolicyBindings(),
  ]);
  if (!policiesResult.ok) return policiesResult;
  if (!bindingsResult.ok) return bindingsResult;
  return {
    ok: true,
    data: { policies: policiesResult.data, bindings: bindingsResult.data },
  };
}
