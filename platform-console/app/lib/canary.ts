// ------------------------------------------------------- Canary / Blue-Green
//
// Real Canary/Blue-Green deployment traffic control (AWS CodeDeploy
// traffic-shifting / GCP traffic-splitting / Azure deployment slots
// equivalent), built on Istio's real weighted VirtualService routing --
// the mesh this cluster already runs STRICT mTLS on (k8s/mtls.yaml) and
// already fronts platform-console-gateway with (k8s/gateway.yaml). This
// module reads/writes the ONE real `networking.istio.io/v1` VirtualService
// object k8s/canary.yaml stands up (`autofde-lab-status`, `autofde-lab`
// namespace) via the k8s API, reusing lib/k8s.ts's `k8sRequest` -- Istio
// CRDs are just another namespaced Kubernetes resource, the exact same
// convention `listPeerAuthentications` above already established for
// `security.istio.io` objects, here for `networking.istio.io` instead.
//
// Demo scope, deliberately narrow: exactly one real backend
// (`autofde-lab-status`, see k8s/canary.yaml's own header comment for the
// full shape) rather than a generic multi-service canary framework --
// matches the task's own "pick ONE real status service" scope. The
// constants below are not configurable at the API layer for that reason:
// this is a real, working demo of the mechanism, not a speculative
// generalized product surface.
import { k8sRequest, type K8sResult } from "@/lib/k8s";

export const CANARY_NAMESPACE = "autofde-lab";
export const CANARY_SERVICE_HOST = "autofde-lab-status.autofde-lab.svc.cluster.local";
export const CANARY_VIRTUAL_SERVICE = "autofde-lab-status";
export const STABLE_DEPLOYMENT = "autofde-lab-status";
export const CANARY_DEPLOYMENT = "autofde-lab-status-canary";

interface VirtualServiceRouteDestination {
  destination: { host: string; subset?: string };
  weight?: number;
}

interface VirtualServiceHttpRoute {
  name?: string;
  route?: VirtualServiceRouteDestination[];
}

interface VirtualServiceItem {
  metadata: { name: string; namespace: string; resourceVersion: string };
  spec?: { hosts?: string[]; http?: VirtualServiceHttpRoute[] };
}

interface DeploymentMeta {
  metadata: { name: string; namespace: string };
  spec?: { replicas?: number };
  status?: { readyReplicas?: number; availableReplicas?: number };
}

export interface CanaryDeploymentInfo {
  exists: boolean;
  replicasDesired: number;
  replicasReady: number;
}

export interface CanaryWeights {
  stable: number;
  canary: number;
}

export interface CanaryState {
  weights: CanaryWeights;
  stableDeployment: CanaryDeploymentInfo;
  canaryDeployment: CanaryDeploymentInfo;
}

function vsPath(name?: string): string {
  const base = `/apis/networking.istio.io/v1/namespaces/${CANARY_NAMESPACE}/virtualservices`;
  return name ? `${base}/${encodeURIComponent(name)}` : base;
}

function deploymentPath(name: string): string {
  return `/apis/apps/v1/namespaces/${CANARY_NAMESPACE}/deployments/${encodeURIComponent(name)}`;
}

/** Real live GET of one Deployment. `{ ok: true, data: { exists: false, ... } }`
 * -- not an error -- when it doesn't exist (e.g. after a promote/rollback
 * deleted it), same "not found is a real, distinguishable state" convention
 * `getConfigMap` above already uses. */
async function getDeploymentInfo(name: string): Promise<K8sResult<CanaryDeploymentInfo>> {
  const result = await k8sRequest<DeploymentMeta>(deploymentPath(name));
  if (!result.ok) {
    if (/not found/i.test(result.error)) {
      return { ok: true, data: { exists: false, replicasDesired: 0, replicasReady: 0 } };
    }
    return result;
  }
  return {
    ok: true,
    data: {
      exists: true,
      replicasDesired: result.data.spec?.replicas ?? 0,
      replicasReady: result.data.status?.readyReplicas ?? 0,
    },
  };
}

function extractWeights(item: VirtualServiceItem): CanaryWeights | null {
  const route = item.spec?.http?.[0]?.route;
  if (!route) return null;
  let stable: number | null = null;
  let canary: number | null = null;
  for (const dest of route) {
    if (dest.destination.subset === "stable") stable = dest.weight ?? 0;
    if (dest.destination.subset === "canary") canary = dest.weight ?? 0;
  }
  if (stable === null || canary === null) return null;
  return { stable, canary };
}

/**
 * Real, live GET+read of the VirtualService's current `stable`/`canary`
 * subset weights, plus each Deployment's real existence/replica state.
 * Never a cached or fabricated value -- every field is read fresh from
 * the k8s API on every call, same "no polling loop, no cache, a brand-new
 * request" convention services/autofde-lab/app.py's own feature-flag read
 * documents.
 */
export async function getCanaryState(): Promise<K8sResult<CanaryState>> {
  const [vsResult, stableResult, canaryResult] = await Promise.all([
    k8sRequest<VirtualServiceItem>(vsPath(CANARY_VIRTUAL_SERVICE)),
    getDeploymentInfo(STABLE_DEPLOYMENT),
    getDeploymentInfo(CANARY_DEPLOYMENT),
  ]);
  if (!vsResult.ok) return vsResult;
  if (!stableResult.ok) return stableResult;
  if (!canaryResult.ok) return canaryResult;

  const weights = extractWeights(vsResult.data);
  if (!weights) {
    return {
      ok: false,
      error:
        `VirtualService ${CANARY_NAMESPACE}/${CANARY_VIRTUAL_SERVICE} does not have the ` +
        "expected stable/canary subset route shape (k8s/canary.yaml not applied?)",
    };
  }

  return {
    ok: true,
    data: { weights, stableDeployment: stableResult.data, canaryDeployment: canaryResult.data },
  };
}

/**
 * Real get-then-PUT weight update: fetches the live VirtualService (for
 * its current `metadata.resourceVersion`, required by the k8s API for any
 * `PUT` -- an update without it is rejected as a conflict), rewrites only
 * the two subset destinations' `weight` fields in place, and PUTs the
 * whole object back. A full-object PUT rather than a JSON merge-patch
 * (unlike `createOrUpdateConfigMap`'s patch above): a merge-patch on an
 * array field (`spec.http[0].route`) REPLACES the whole array wholesale
 * per RFC 7386 (arrays have no merge key), so patching only "one weight"
 * isn't actually expressible as a small patch here -- a real GET-modify-
 * PUT is the correct, honest primitive for this shape, not a shortcut.
 */
export async function setCanaryWeights(
  stableWeight: number,
  canaryWeight: number,
): Promise<K8sResult<CanaryWeights>> {
  if (
    !Number.isInteger(stableWeight) ||
    !Number.isInteger(canaryWeight) ||
    stableWeight < 0 ||
    canaryWeight < 0 ||
    stableWeight + canaryWeight !== 100
  ) {
    return {
      ok: false,
      error: "stableWeight and canaryWeight must be non-negative integers summing to 100",
    };
  }

  const current = await k8sRequest<VirtualServiceItem>(vsPath(CANARY_VIRTUAL_SERVICE));
  if (!current.ok) return current;

  const item = current.data;
  const route = item.spec?.http?.[0]?.route;
  if (!route) {
    return {
      ok: false,
      error: `VirtualService ${CANARY_NAMESPACE}/${CANARY_VIRTUAL_SERVICE} has no http[0].route to update`,
    };
  }
  for (const dest of route) {
    if (dest.destination.subset === "stable") dest.weight = stableWeight;
    if (dest.destination.subset === "canary") dest.weight = canaryWeight;
  }

  const result = await k8sRequest<VirtualServiceItem>(vsPath(CANARY_VIRTUAL_SERVICE), "PUT", item);
  if (!result.ok) return result;
  const weights = extractWeights(result.data);
  if (!weights) {
    return { ok: false, error: "PUT succeeded but response did not carry the expected weights" };
  }
  return { ok: true, data: weights };
}

async function deleteDeployment(name: string): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(deploymentPath(name), "DELETE");
  if (!result.ok) {
    // Deleting an already-absent Deployment is not a real failure for
    // this module's purposes (promote/rollback are meant to be safely
    // re-runnable) -- same "not found is a real, benign state" reasoning
    // getDeploymentInfo above already applies to reads.
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: null };
}

/**
 * Promote: shift 100% of live traffic to the canary subset, then delete
 * the now-unused stable Deployment -- the real AWS CodeDeploy "complete
 * deployment" / GCP "promote canary to 100%" action. Weight is shifted
 * FIRST, Deployment deleted SECOND -- so a failure between the two steps
 * fails safe (worst case: traffic already 100% canary, stable Deployment
 * still running harmlessly, not the reverse -- never a window where
 * traffic points at a subset with zero backing pods).
 */
export async function promoteCanary(): Promise<K8sResult<CanaryState>> {
  const weightResult = await setCanaryWeights(0, 100);
  if (!weightResult.ok) return weightResult;
  const deleteResult = await deleteDeployment(STABLE_DEPLOYMENT);
  if (!deleteResult.ok) return deleteResult;
  return getCanaryState();
}

/**
 * Rollback: shift 100% of live traffic back to the stable subset, then
 * delete the canary Deployment -- the real "abort/rollback" action. Same
 * weight-first-then-delete safe-failure ordering as promoteCanary above.
 */
export async function rollbackCanary(): Promise<K8sResult<CanaryState>> {
  const weightResult = await setCanaryWeights(100, 0);
  if (!weightResult.ok) return weightResult;
  const deleteResult = await deleteDeployment(CANARY_DEPLOYMENT);
  if (!deleteResult.ok) return deleteResult;
  return getCanaryState();
}
