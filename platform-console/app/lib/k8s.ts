/**
 * Minimal Kubernetes API client using the pod's own in-cluster
 * ServiceAccount token -- no external k8s client library, no fabricated
 * client-side state. Every function here does a real HTTPS call to the
 * API server (https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT)
 * using the token/CA bundle Kubernetes mounts automatically at
 * /var/run/secrets/kubernetes.io/serviceaccount/. Off-cluster (local dev,
 * `next build`), that mount does not exist, so every call here fails
 * closed with an honest "not configured" result rather than a fabricated
 * fallback -- same fail-closed convention as lib/status.ts.
 *
 * Runs on the Node.js runtime only (uses `node:fs`/`node:https`), same
 * constraint as lib/credentials.ts -- never import this from middleware.
 */
import fs from "node:fs";
import https from "node:https";
import {
  DEFAULT_PROJECT_TIER,
  TIER_LABEL,
  isProjectTier,
  resourceQuotaHardFor,
  type ProjectTier,
} from "./tiers";
import { DEFAULT_ENVIRONMENT, ENVIRONMENT_LABEL, isEnvironment, type Environment } from "./environments";

const SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount";
const REQUEST_TIMEOUT_MS = 5000;

export type K8sResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export interface InClusterConfig {
  token: string;
  ca: Buffer;
  host: string;
  port: string;
}

let cachedConfig: InClusterConfig | null | undefined;

function readInClusterConfig(): InClusterConfig | null {
  if (cachedConfig !== undefined) return cachedConfig;
  try {
    const tokenPath = `${SA_DIR}/token`;
    const caPath = `${SA_DIR}/ca.crt`;
    const host = process.env.KUBERNETES_SERVICE_HOST;
    const port = process.env.KUBERNETES_SERVICE_PORT ?? "443";
    if (!host || !fs.existsSync(tokenPath) || !fs.existsSync(caPath)) {
      cachedConfig = null;
      return null;
    }
    cachedConfig = {
      token: fs.readFileSync(tokenPath, "utf8").trim(),
      ca: fs.readFileSync(caPath),
      host,
      port,
    };
    return cachedConfig;
  } catch {
    cachedConfig = null;
    return null;
  }
}

/** True when a real in-cluster ServiceAccount identity is available. */
export function hasClusterCredentials(): boolean {
  return readInClusterConfig() !== null;
}

/**
 * Exposes the raw in-cluster ServiceAccount token/CA/host/port -- the same
 * cached config every k8sRequest call already uses internally -- for the
 * one caller in this codebase that cannot go through k8sRequest's plain-
 * HTTPS primitive: lib/container-exec.ts's real WebSocket connection to
 * the pods/exec subresource (`GET .../pods/{pod}/exec?...` upgraded to a
 * WebSocket, never a normal JSON request/response). Same fail-closed
 * `null`-when-not-configured contract as hasClusterCredentials above.
 */
export function getInClusterConfig(): InClusterConfig | null {
  return readInClusterConfig();
}

/**
 * Exported so lib/scheduled-jobs.ts can reuse the exact same in-cluster
 * ServiceAccount HTTPS client (token/CA, fail-closed "not configured",
 * timeout/error handling) instead of a second, driftable copy -- the same
 * "reuse lib/k8s.ts conventions" every other module in this file already
 * follows internally, made available across the module boundary.
 */
export async function k8sRequest<T>(
  path: string,
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH" = "GET",
  body?: unknown,
  contentType = "application/json",
): Promise<K8sResult<T>> {
  const cfg = readInClusterConfig();
  if (!cfg) {
    return {
      ok: false,
      error:
        "not configured: no in-cluster ServiceAccount credentials found " +
        `(${SA_DIR}) -- this only works when running as the platform-console pod`,
    };
  }

  const payload = body ? Buffer.from(JSON.stringify(body)) : undefined;

  return new Promise((resolve) => {
    const req = https.request(
      {
        host: cfg.host,
        port: cfg.port,
        path,
        method,
        ca: cfg.ca,
        timeout: REQUEST_TIMEOUT_MS,
        headers: {
          Authorization: `Bearer ${cfg.token}`,
          Accept: "application/json",
          ...(payload
            ? {
                "Content-Type": contentType,
                "Content-Length": String(payload.length),
              }
            : {}),
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode ?? 0;
          const raw = Buffer.concat(chunks).toString("utf8");
          let parsed: unknown = undefined;
          if (raw) {
            try {
              parsed = JSON.parse(raw);
            } catch {
              resolve({
                ok: false,
                error: `unparsable response body from ${method} ${path} (HTTP ${status})`,
              });
              return;
            }
          }
          if (status < 200 || status >= 300) {
            const message =
              (parsed as { message?: string } | undefined)?.message ??
              `HTTP ${status}`;
            resolve({ ok: false, error: `${method} ${path} failed: ${message}` });
            return;
          }
          resolve({ ok: true, data: parsed as T });
        });
      },
    );
    req.on("timeout", () => req.destroy(new Error(`timeout after ${REQUEST_TIMEOUT_MS}ms`)));
    req.on("error", (err) =>
      resolve({ ok: false, error: `unreachable: ${err.message}` }),
    );
    if (payload) req.write(payload);
    req.end();
  });
}

// --------------------------------------------------------------- Projects

export interface SupabaseProject {
  name: string;
  namespace: string;
  createdAt: string;
  databaseRefName: string | null;
  hostname: string | null;
  ready: boolean | null; // null when no Ready condition has been reported yet
  reason: string | null;
  message: string | null;
  /** Real `metadata.labels` on this Project CR -- populated for
   * lib/tags.ts's Resource Tagging module (a Project's real tags are a
   * subset of this map, see extractTags), empty object when the object
   * carries no labels at all. */
  labels: Record<string, string>;
  /** Real plan tier read back from this Project's own `TIER_LABEL`
   * (lib/tiers.ts). Defaults to `DEFAULT_PROJECT_TIER` for a Project
   * created before this label existed, or with a malformed value --
   * never silently `undefined`. */
  tier: ProjectTier;
  /** Real promotion-pipeline environment read back from this Project's own
   * `ENVIRONMENT_LABEL` (lib/environments.ts). Defaults to
   * `DEFAULT_ENVIRONMENT` for a Project created before this label existed,
   * or with a malformed value -- never silently `undefined`, same
   * fail-to-a-known-default discipline the `tier` field above uses. */
  environment: Environment;
}

interface K8sListMeta {
  items?: Array<{
    metadata: {
      name: string;
      namespace: string;
      creationTimestamp: string;
      labels?: Record<string, string>;
    };
    spec?: {
      databaseRef?: { name?: string };
      http?: { hostname?: string };
    };
    status?: {
      conditions?: Array<{
        type: string;
        status: string;
        reason?: string;
        message?: string;
      }>;
    };
  }>;
}

function toSupabaseProject(item: NonNullable<K8sListMeta["items"]>[number]): SupabaseProject {
  const readyCondition = item.status?.conditions?.find((c) => c.type === "Ready");
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    createdAt: item.metadata.creationTimestamp,
    databaseRefName: item.spec?.databaseRef?.name ?? null,
    hostname: item.spec?.http?.hostname ?? null,
    ready: readyCondition ? readyCondition.status === "True" : null,
    reason: readyCondition?.reason ?? null,
    message: readyCondition?.message ?? null,
    labels: item.metadata.labels ?? {},
    tier: (() => {
      const raw = item.metadata.labels?.[TIER_LABEL];
      return raw && isProjectTier(raw) ? raw : DEFAULT_PROJECT_TIER;
    })(),
    environment: (() => {
      const raw = item.metadata.labels?.[ENVIRONMENT_LABEL];
      return raw && isEnvironment(raw) ? raw : DEFAULT_ENVIRONMENT;
    })(),
  };
}

/**
 * Lists real Project CRs cluster-wide, optionally filtered by a real
 * server-side `?labelSelector=` query parameter -- the same convention
 * `listJobs`/`listCronJobs` already use. Used unfiltered by every existing
 * caller (the /projects page, Global Search); lib/tags.ts's
 * listResourcesByTag passes a real `platform-console.io/tag-<key>=<value>`
 * selector for a genuine server-side "browse by tag" filter, never a
 * client-side `.filter()` over every Project on the cluster.
 */
export async function listProjects(labelSelector?: string): Promise<K8sResult<SupabaseProject[]>> {
  const qs = labelSelector ? `?labelSelector=${encodeURIComponent(labelSelector)}` : "";
  const result = await k8sRequest<K8sListMeta>(
    `/apis/core.supabase.io/v1alpha1/projects${qs}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toSupabaseProject) };
}

export async function getProject(
  name: string,
): Promise<K8sResult<SupabaseProject | null>> {
  const all = await listProjects();
  if (!all.ok) return all;
  return { ok: true, data: all.data.find((p) => p.name === name) ?? null };
}

/**
 * Updates an existing Project's plan tier via a real RFC 7386 merge patch
 * touching only `metadata.labels.<TIER_LABEL>` -- same merge-patch
 * convention lib/tags.ts's applyTag already establishes for labels, kept
 * as its own function (rather than routed through applyTag) since TIER_LABEL
 * is not prefixed with lib/tags.ts's `TAG_LABEL_PREFIX` and is not a
 * user-defined tag: it is the one real plan-tier field this module owns.
 * Also re-derives this namespace's ResourceQuota from the new tier's
 * TIER_RESOURCE_QUOTAS entry (createOrUpdateResourceQuota), so a tier
 * change takes live effect on the quota immediately, not just on the
 * label -- a genuine upgrade/downgrade, not a cosmetic relabel.
 */
export async function setProjectTier(
  name: string,
  namespace: string,
  tier: ProjectTier,
): Promise<K8sResult<SupabaseProject>> {
  const result = await k8sRequest<NonNullable<K8sListMeta["items"]>[number]>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(namespace)}/projects/${encodeURIComponent(name)}`,
    "PATCH",
    { metadata: { labels: { [TIER_LABEL]: tier } } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;

  const quotaResult = await createOrUpdateResourceQuota(namespace, `${namespace}-quota`, tier);
  if (!quotaResult.ok) return quotaResult;

  return { ok: true, data: toSupabaseProject(result.data) };
}

/**
 * Updates an existing Project's promotion-pipeline environment via a real
 * RFC 7386 merge patch touching only `metadata.labels.<ENVIRONMENT_LABEL>`
 * -- same merge-patch primitive/convention setProjectTier above already
 * establishes for TIER_LABEL. Called only after the promotion route's
 * caller-side validation (lib/environments.ts's validatePromotion), the
 * freeze guard, and a fresh approved `environment.promote` row all already
 * passed -- this function itself performs no additional business-rule
 * check, it is the one real k8s write the promotion route makes once every
 * gate has cleared.
 */
export async function setProjectEnvironment(
  name: string,
  namespace: string,
  environment: Environment,
): Promise<K8sResult<SupabaseProject>> {
  const result = await k8sRequest<NonNullable<K8sListMeta["items"]>[number]>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(namespace)}/projects/${encodeURIComponent(name)}`,
    "PATCH",
    { metadata: { labels: { [ENVIRONMENT_LABEL]: environment } } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: toSupabaseProject(result.data) };
}

export interface CreateProjectInput {
  name: string;
  namespace: string;
  databaseRefName: string;
  hostname: string;
  protocol: "http" | "https";
  /** PVC size for the paired SingleDatabase, e.g. "1Gi". Defaults to "1Gi". */
  dbStorageSize: string;
  /** Plan tier (lib/tiers.ts) -- set as a real `TIER_LABEL` label on the
   * Project CR and used to derive this namespace's provisioned
   * ResourceQuota (TIER_RESOURCE_QUOTAS). Defaults to
   * DEFAULT_PROJECT_TIER when omitted. */
  tier?: ProjectTier;
  /** Real, enterprise-tier-gated data-residency pin (lib/orgs.ts's
   * `getOrgRegion`/`setOrgRegion`, restricted to a value
   * `listNodeRegions` actually reports for this cluster). When set,
   * `buildProjectManifest`/`buildSingleDatabaseManifest` inject a real
   * `nodeSelector: {topology.kubernetes.io/region: <region>}` into every
   * component PodSpec they submit -- a genuine, k8s-scheduler-enforced
   * constraint (a Pod that cannot be scheduled in the pinned region
   * stays honestly Pending), not a label-only decoration. Omitted
   * entirely (not even `nodeSelector: {}`) when unset, so an unpinned
   * project's scheduling is completely unaffected. */
  region?: string;
  /** Environment-promotion pipeline stage (lib/environments.ts) -- set as
   * a real `ENVIRONMENT_LABEL` label on the Project CR at provisioning
   * time. Defaults to `DEFAULT_ENVIRONMENT` ("dev") when omitted, so a
   * freshly-created Project always starts at the bottom of the pipeline
   * and must be explicitly promoted (POST /api/projects/[name]/promote)
   * to move to `staging`/`prod`, never created already at a later stage. */
  environment?: Environment;
}

interface SingleDatabaseItem {
  metadata: { name: string; namespace: string };
}

/**
 * Builds the exact SingleDatabase manifest createSingleDatabase submits --
 * pulled out as its own pure function (no network call) so lib/iac.ts's
 * detectDrift can compute "what a fresh createSingleDatabase call would
 * submit for this name" from the SAME code path that a real create uses,
 * rather than a second, driftable copy of this shape.
 */
export function buildSingleDatabaseManifest(input: {
  name: string;
  namespace: string;
  storageSize: string;
  /** Real data-residency pin (see CreateProjectInput.region above).
   * SingleDatabase's CRD schema (confirmed against the real
   * `singledatabases.core.supabase.io` CRD: `kubectl get crd
   * singledatabases.core.supabase.io -o yaml`) exposes `spec.nodeSelector`
   * directly at the top level -- unlike Project, which nests it per
   * component -- so this is set once, not per-block. */
  region?: string;
}) {
  return {
    apiVersion: "core.supabase.io/v1alpha1",
    kind: "SingleDatabase",
    metadata: { name: input.name, namespace: input.namespace },
    spec: {
      storage: { accessModes: ["ReadWriteOnce"], size: input.storageSize },
      ...(input.region ? { nodeSelector: { [REGION_NODE_LABEL]: input.region } } : {}),
    },
  };
}

/**
 * Creates the SingleDatabase CR a Project's spec.databaseRef points at.
 * Mirrors the real, working demo-db manifest in supabase-demo (verified via
 * `kubectl get singledatabase demo-db -n supabase-demo -o yaml`): only
 * spec.storage is required, the operator fills in the rest (resolvedDatabase
 * host/port/user/passwordRef) once it reconciles.
 */
export async function createSingleDatabase(input: {
  name: string;
  namespace: string;
  storageSize: string;
  region?: string;
}): Promise<K8sResult<SingleDatabaseItem>> {
  const manifest = buildSingleDatabaseManifest(input);
  return k8sRequest<SingleDatabaseItem>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(input.namespace)}/singledatabases`,
    "POST",
    manifest,
  );
}

/**
 * Creates a Project CR only (no paired database). Kept for callers that
 * already have a SingleDatabase they want to reference (e.g. multiple
 * Projects sharing one database). Most callers want createProjectWithDatabase
 * below, which is what the Create Project form/API route uses.
 *
 * Sets spec.auth/rest/realtime/functions/storage/studio -- not just
 * databaseRef/http -- because leaving them absent is a real, live-confirmed
 * defect, not a harmless omission: a Project created with only
 * databaseRef+http reaches a real Ready=True (the operator's Ready
 * condition only covers the database/JWT/envoy layer), but the operator
 * never creates the auth/rest/realtime/functions/storage/studio
 * Deployments+Services at all, so every project-scoped module past
 * Database (Auth, Storage, Functions) has nothing to find. Confirmed live
 * against a real second Project on this cluster: `kubectl get svc`
 * showed zero component Services after Ready=True with the old
 * databaseRef/http-only spec, and the missing Services (auth/rest/
 * realtime/functions/storage/studio) appeared within seconds of a
 * `kubectl patch` adding exactly the blocks below. Shape mirrors the
 * real, working demo-project spec (`kubectl get project demo-project -o
 * yaml`) -- each block's `enable` field defaults to `true` in the CRD
 * schema once the block itself is present, so these are deliberately
 * near-empty (only the sub-fields the schema actually requires, e.g.
 * storage/studio's PVC sizing) rather than repeating the schema's own
 * defaults here.
 */
export function buildProjectManifest(input: CreateProjectInput) {
  // Real data-residency pin (see CreateProjectInput.region above).
  // Unlike SingleDatabase, the real `projects.core.supabase.io` CRD
  // schema nests `nodeSelector` INSIDE each individual component block
  // (spec.auth.nodeSelector, spec.rest.nodeSelector, ... -- confirmed
  // against `kubectl get crd projects.core.supabase.io -o yaml`, one
  // per component the operator reconciles into its own Deployment), so
  // the constraint has to be spread into every component block below,
  // not set once at spec-level. Omitted entirely when no region is
  // pinned, so an unpinned project's manifest is byte-for-byte what it
  // was before this field existed.
  const nodeSelector = input.region ? { nodeSelector: { [REGION_NODE_LABEL]: input.region } } : {};
  return {
    apiVersion: "core.supabase.io/v1alpha1",
    kind: "Project",
    metadata: {
      name: input.name,
      namespace: input.namespace,
      labels: {
        [TIER_LABEL]: input.tier ?? DEFAULT_PROJECT_TIER,
        [ENVIRONMENT_LABEL]: input.environment ?? DEFAULT_ENVIRONMENT,
      },
    },
    spec: {
      databaseRef: { kind: "SingleDatabase", name: input.databaseRefName },
      http: { hostname: input.hostname, protocol: input.protocol },
      auth: { siteUrl: `${input.protocol}://${input.hostname}`, ...nodeSelector },
      rest: { ...nodeSelector },
      realtime: { ...nodeSelector },
      functions: { verifyJwt: true, ...nodeSelector },
      storage: {
        storage: { accessModes: ["ReadWriteOnce"], size: input.dbStorageSize },
        ...nodeSelector,
      },
      studio: {
        orgName: `${input.name}-org`,
        projName: input.name,
        storage: { accessModes: ["ReadWriteOnce"], size: input.dbStorageSize },
        ...nodeSelector,
      },
    },
  };
}

export async function createProject(
  input: CreateProjectInput,
): Promise<K8sResult<SupabaseProject>> {
  const manifest = buildProjectManifest(input);
  const result = await k8sRequest<NonNullable<K8sListMeta["items"]>[number]>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(input.namespace)}/projects`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toSupabaseProject(result.data) };
}

/**
 * Creates a Project CR paired with its own SingleDatabase CR, matching the
 * real shape the supabase-operator expects (verified live against the
 * demo-project/demo-db pair in supabase-demo: Project.spec.databaseRef ->
 * {kind: SingleDatabase, name}). The SingleDatabase is created first so it
 * is referenceable as soon as the operator reconciles the Project -- if that
 * first call fails (e.g. it already exists), the Project is never created,
 * so a Project is never left pointing at a database that doesn't exist.
 */
export async function createProjectWithDatabase(
  input: CreateProjectInput,
): Promise<K8sResult<SupabaseProject>> {
  const dbResult = await createSingleDatabase({
    name: input.databaseRefName,
    namespace: input.namespace,
    storageSize: input.dbStorageSize,
    region: input.region,
  });
  if (!dbResult.ok) return dbResult;

  const projectResult = await createProject(input);
  if (!projectResult.ok) return projectResult;

  // Real per-tier ResourceQuota, derived from the same TIER_RESOURCE_QUOTAS
  // table the Project's own TIER_LABEL was just set from -- closes the
  // "fixed, operator-set ceiling with no notion of plan tier" gap named in
  // resource-quotas-enforced's evidence rationale. Applied AFTER the
  // Project succeeds (not before) so a quota-provisioning failure never
  // leaves an orphaned namespace with no Project; a failure here is
  // returned as-is (fail closed), leaving the Project ready but the
  // namespace on whatever ResourceQuota (if any) already existed.
  const quotaResult = await createOrUpdateResourceQuota(
    input.namespace,
    `${input.namespace}-quota`,
    input.tier ?? DEFAULT_PROJECT_TIER,
  );
  if (!quotaResult.ok) return quotaResult;

  return projectResult;
}

/**
 * Deletes a Project CR only (no paired database) -- the DELETE-verb
 * counterpart to createProject above, same k8sRequest primitive
 * deleteSecret already uses for a namespaced-resource DELETE. Idempotent:
 * a 404 from the API server is treated the same honest-absence way
 * getRawProject already does (an already-gone Project is not an error a
 * cleanup step should fail on).
 */
export async function deleteProject(
  namespace: string,
  name: string,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(namespace)}/projects/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: null };
}

/** DELETE-verb counterpart to createSingleDatabase above. Same idempotent
 * not-found handling as deleteProject. */
export async function deleteSingleDatabase(
  namespace: string,
  name: string,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(namespace)}/singledatabases/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: null };
}

/**
 * Deletes a Project CR and its paired SingleDatabase CR -- the teardown
 * counterpart to createProjectWithDatabase, used by the self-service
 * DELETE /api/projects/[name] route (the cleanup step of the /quickstart
 * flow). Deletes the Project first, then its database, mirroring
 * createProjectWithDatabase's own database-then-project creation order in
 * reverse -- the Project's spec.databaseRef only makes sense to remove
 * once nothing still references it.
 */
export async function deleteProjectWithDatabase(
  project: SupabaseProject,
): Promise<K8sResult<null>> {
  const projectResult = await deleteProject(project.namespace, project.name);
  if (!projectResult.ok) return projectResult;

  if (project.databaseRefName) {
    const dbResult = await deleteSingleDatabase(project.namespace, project.databaseRefName);
    if (!dbResult.ok) return dbResult;
  }
  return { ok: true, data: null };
}

// -------------------------------------------------------- Raw CR (IaC/drift)
//
// Real, full-fidelity single-object GETs for the Infrastructure-as-Code
// export/drift-detection module (lib/iac.ts) -- distinct from
// listProjects/getProject above, which return a distilled SupabaseProject
// view built for the rest of this console's UI. exportProjectManifest needs
// the ACTUAL raw spec (every field, including the ones the operator itself
// defaults in -- auth.replicas, rest.dbMaxRows, etc.) so the exported YAML
// is a genuine "what's really running" snapshot, not a re-derived guess.

export interface RawCustomResource {
  apiVersion: string;
  kind: string;
  metadata: {
    name: string;
    namespace: string;
    labels?: Record<string, string>;
    annotations?: Record<string, string>;
  };
  spec: Record<string, unknown>;
}

/** Real single-object GET of one namespaced Project CR, full spec as the
 * API server actually stores it. `{ ok: true, data: null }` -- not an
 * error -- when it doesn't exist, the same honest-absence convention used
 * throughout this file. */
export async function getRawProject(
  namespace: string,
  name: string,
): Promise<K8sResult<RawCustomResource | null>> {
  const result = await k8sRequest<RawCustomResource>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(namespace)}/projects/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: result.data };
}

/** Real single-object GET of one namespaced SingleDatabase CR, full spec.
 * Same honest-absence convention as getRawProject above. */
export async function getRawSingleDatabase(
  namespace: string,
  name: string,
): Promise<K8sResult<RawCustomResource | null>> {
  const result = await k8sRequest<RawCustomResource>(
    `/apis/core.supabase.io/v1alpha1/namespaces/${encodeURIComponent(namespace)}/singledatabases/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: result.data };
}

// ---------------------------------------------------------------- Services

export interface K8sService {
  name: string;
  namespace: string;
  clusterIP: string | null;
  ports: Array<{ name?: string; port: number; targetPort?: number | string; protocol: string }>;
  labels: Record<string, string>;
  dns: string;
}

interface ServiceListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; labels?: Record<string, string> };
    spec?: {
      clusterIP?: string;
      ports?: Array<{ name?: string; port: number; targetPort?: number | string; protocol?: string }>;
    };
  }>;
}

export async function listNamespaceServices(
  namespace: string,
): Promise<K8sResult<K8sService[]>> {
  const result = await k8sRequest<ServiceListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/services`,
  );
  if (!result.ok) return result;
  const items = (result.data.items ?? []).map((svc) => ({
    name: svc.metadata.name,
    namespace: svc.metadata.namespace,
    clusterIP: svc.spec?.clusterIP ?? null,
    ports: (svc.spec?.ports ?? []).map((p) => ({
      name: p.name,
      port: p.port,
      targetPort: p.targetPort,
      protocol: p.protocol ?? "TCP",
    })),
    labels: svc.metadata.labels ?? {},
    dns: `${svc.metadata.name}.${svc.metadata.namespace}.svc.cluster.local`,
  }));
  return { ok: true, data: items };
}

/**
 * Resolves a Project's real Postgres StatefulSet Pod (namespace + pod
 * name) live from its own Services -- the same
 * `component=database`/`instance=<databaseRefName>` label match
 * app/projects/[name]/database/page.tsx already renders, reused here so
 * the Backups module (createBackupJob/createRestoreJob callers) targets
 * whichever project's real database this is, never a literal
 * `demo-db-postgres-0`. The StatefulSet's Service shares the
 * StatefulSet's name (createBackupJob's own `stem` comment documents this
 * as a real structural convention, not a guess), and pod ordinal `-0` is
 * the first/only replica every SingleDatabase this console creates
 * provisions (`storage.accessModes: [ReadWriteOnce]`, replicas: 1 --
 * confirmed live via `kubectl get statefulset -n supabase-demo demo-db-postgres`
 * returning `1/1` replicas). Returns `{ ok: true, data: null }` -- not an
 * error -- when no matching Service exists yet, the same honest-absence
 * convention `getBackupsPvc` above uses.
 */
export async function getProjectDatabasePod(
  project: SupabaseProject,
): Promise<K8sResult<{ namespace: string; serviceName: string; podName: string } | null>> {
  const servicesResult = await listNamespaceServices(project.namespace);
  if (!servicesResult.ok) return servicesResult;
  const dbService = servicesResult.data.find(
    (s) =>
      s.labels["app.kubernetes.io/component"] === "database" &&
      (project.databaseRefName ? s.labels["app.kubernetes.io/instance"] === project.databaseRefName : true),
  );
  if (!dbService) return { ok: true, data: null };
  return {
    ok: true,
    data: {
      namespace: project.namespace,
      serviceName: dbService.name,
      podName: `${dbService.name}-0`,
    },
  };
}

/**
 * Resolves a Project's real Storage API Service (dns + port) live from its
 * own Services -- the exact same `component=storage`/`instance=<project.name>`
 * label match app/projects/[name]/storage/page.tsx already renders inline,
 * factored out here so lib/storage-signed-url.ts's signing/verification
 * path and app/api/projects/[name]/storage/*'s routes share one real
 * lookup instead of three copies of the same filter. Returns
 * `{ ok: true, data: null }` -- not an error -- when no matching Service
 * exists yet, same honest-absence convention getProjectDatabasePod uses.
 */
export async function getProjectStorageService(
  project: SupabaseProject,
): Promise<K8sResult<{ dns: string; port: number } | null>> {
  const servicesResult = await listNamespaceServices(project.namespace);
  if (!servicesResult.ok) return servicesResult;
  const storageService = servicesResult.data.find(
    (s) =>
      s.labels["app.kubernetes.io/component"] === "storage" &&
      s.labels["app.kubernetes.io/instance"] === project.name,
  );
  if (!storageService) return { ok: true, data: null };
  return {
    ok: true,
    data: { dns: storageService.dns, port: storageService.ports[0]?.port ?? 5000 },
  };
}

// ------------------------------------------------------- Service Discovery
//
// Real hyperscaler-PaaS-style Service Discovery primitive (AWS Route53
// private hosted zones / GCP Cloud DNS internal zones / Azure Private DNS
// equivalent) -- not decorative, because this cluster's actual internal
// DNS/service-discovery layer already exists and every other module's
// cluster-internal URLs (the Database module's Postgres/PostgREST hosts,
// the Backups module's `<stem>.<namespace>.svc.cluster.local` pg_dump
// target) already depend on it: CoreDNS resolves `<svc>.<namespace>.svc.
// cluster.local` to a Service's ClusterIP because the Service+Endpoints
// objects are the real, live source of truth CoreDNS's kubernetes plugin
// reads directly from the API server -- this module reads that exact same
// pair of objects, not a separate DNS-specific API. `listNamespaceServices`
// above already provides the DNS-name-bearing half (Service); the
// Endpoints half below adds the load-bearing "is this record actually
// resolving to something healthy" signal -- how many backing Pod IPs are
// currently Ready versus configured, the thing a DNS name alone cannot
// tell you. No new RBAC for Services (already granted cluster-wide by the
// `services` rule above); Endpoints get their own new cluster-wide rule
// in `k8s/paas-rbac.yaml`, same sensitivity class (workload IPs, not
// secrets) as the Services/Deployments/Roles already granted there.

export interface K8sEndpointSubsetAddress {
  ip: string;
  podName: string | null;
}

export interface K8sServiceEndpoints {
  name: string;
  namespace: string;
  readyAddresses: K8sEndpointSubsetAddress[];
  notReadyAddresses: K8sEndpointSubsetAddress[];
}

interface EndpointsListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    subsets?: Array<{
      addresses?: Array<{ ip: string; targetRef?: { kind?: string; name?: string } }>;
      notReadyAddresses?: Array<{ ip: string; targetRef?: { kind?: string; name?: string } }>;
    }>;
  }>;
}

function toAddress(a: { ip: string; targetRef?: { kind?: string; name?: string } }): K8sEndpointSubsetAddress {
  return { ip: a.ip, podName: a.targetRef?.kind === "Pod" ? a.targetRef.name ?? null : null };
}

/**
 * Lists real core/v1 Endpoints in one namespace -- one object per Service
 * of the same name (the endpoint-controller creates/maintains this
 * automatically from the Service's selector matching real Pod IPs, the
 * same object CoreDNS's kubernetes plugin reads to answer SRV/A queries
 * for that Service's DNS name). `readyAddresses` are backing Pod IPs
 * currently passing readiness (what a client actually gets routed to
 * today); `notReadyAddresses` are Pod IPs the Service selects but that
 * have not yet passed a readiness probe -- kept separate, never merged,
 * so callers can distinguish "0 ready" from "misconfigured selector,
 * nothing at all".
 */
export async function listEndpoints(namespace: string): Promise<K8sResult<K8sServiceEndpoints[]>> {
  const result = await k8sRequest<EndpointsListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/endpoints`,
  );
  if (!result.ok) return result;
  const items = (result.data.items ?? []).map((item) => {
    const ready: K8sEndpointSubsetAddress[] = [];
    const notReady: K8sEndpointSubsetAddress[] = [];
    for (const subset of item.subsets ?? []) {
      for (const a of subset.addresses ?? []) ready.push(toAddress(a));
      for (const a of subset.notReadyAddresses ?? []) notReady.push(toAddress(a));
    }
    return {
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      readyAddresses: ready,
      notReadyAddresses: notReady,
    };
  });
  return { ok: true, data: items };
}

export interface ServiceDiscoveryRecord {
  name: string;
  namespace: string;
  dns: string;
  clusterIP: string | null;
  ports: Array<{ name?: string; port: number; targetPort?: number | string; protocol: string }>;
  /** Number of backing Pod IPs currently passing readiness -- what this
   * DNS name actually routes traffic to right now, read live from the
   * matching Endpoints object. `null` when no Endpoints object exists at
   * all for this Service name (a real, honest "no backing record" state,
   * distinct from 0/0). */
  readyEndpoints: number | null;
  totalEndpoints: number | null;
  /** Real `metadata.labels` on this Service -- populated for
   * lib/tags.ts's Resource Tagging module (see extractTags), empty object
   * when the Service carries no labels at all. */
  labels: Record<string, string>;
}

/**
 * Combines real Services (the DNS name + ClusterIP half) with real
 * Endpoints (the "is it actually resolving to something healthy" half)
 * for one namespace -- one HTTP round trip each, joined client-side by
 * Service/Endpoints name, which is always identical for a same-namespace
 * pair (the endpoint-controller's own naming convention, never a guess).
 */
export async function listServicesWithEndpoints(
  namespace: string,
): Promise<K8sResult<ServiceDiscoveryRecord[]>> {
  const [servicesResult, endpointsResult] = await Promise.all([
    listNamespaceServices(namespace),
    listEndpoints(namespace),
  ]);
  if (!servicesResult.ok) return servicesResult;
  if (!endpointsResult.ok) return endpointsResult;

  const endpointsByName = new Map(endpointsResult.data.map((e) => [e.name, e]));
  return {
    ok: true,
    data: servicesResult.data.map((svc) => {
      const eps = endpointsByName.get(svc.name);
      return {
        name: svc.name,
        namespace: svc.namespace,
        dns: svc.dns,
        clusterIP: svc.clusterIP,
        ports: svc.ports,
        readyEndpoints: eps ? eps.readyAddresses.length : null,
        totalEndpoints: eps ? eps.readyAddresses.length + eps.notReadyAddresses.length : null,
        labels: svc.labels,
      };
    }),
  };
}

// -------------------------------------------------------------- Namespaces

interface NamespaceListResponse {
  items?: Array<{ metadata: { name: string } }>;
}

export async function listNamespaces(): Promise<K8sResult<string[]>> {
  const result = await k8sRequest<NamespaceListResponse>("/api/v1/namespaces");
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map((ns) => ns.metadata.name) };
}

interface NamespaceItem {
  metadata: { name: string; labels?: Record<string, string>; creationTimestamp: string };
}

/**
 * Creates a real k8s Namespace via POST /api/v1/namespaces -- the org/
 * tenant-provisioning primitive lib/orgs.ts's createOrg builds on. `create`
 * on `namespaces` is NOT yet granted to the platform-console ServiceAccount
 * (k8s/paas-rbac.yaml currently grants only get/list/patch on this
 * resource, for the existing "create project" namespace picker and the
 * Quota Enforcement module's annotation patch) -- this call will get a
 * real 403 from the API server until that ClusterRole is updated with a
 * `create` verb and re-applied to the live cluster. That RBAC change is
 * included in this same commit (see k8s/paas-rbac.yaml's namespaces rule)
 * but re-applying a ClusterRole to a running cluster is a live-cluster
 * operation outside what a source-code change can itself perform -- an
 * honest, disclosed gap, not silently assumed away. Idempotent in the
 * AlreadyExists sense: a 409 from the API server (org's slug collision)
 * is surfaced as a normal K8sResult error for the caller to handle, never
 * swallowed.
 */
export async function createNamespace(
  name: string,
  labels: Record<string, string>,
): Promise<K8sResult<{ name: string; createdAt: string }>> {
  const manifest = {
    apiVersion: "v1",
    kind: "Namespace",
    metadata: { name, labels },
  };
  const result = await k8sRequest<NamespaceItem>("/api/v1/namespaces", "POST", manifest);
  if (!result.ok) return result;
  return {
    ok: true,
    data: { name: result.data.metadata.name, createdAt: result.data.metadata.creationTimestamp },
  };
}

// ------------------------------------------------------------------ GitOps

export interface FluxResource {
  kind: "Kustomization" | "HelmRelease";
  name: string;
  namespace: string;
  ready: boolean | null;
  reason: string | null;
  message: string | null;
}

interface FluxListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    status?: {
      conditions?: Array<{
        type: string;
        status: string;
        reason?: string;
        message?: string;
      }>;
    };
  }>;
}

function toFluxResource(
  kind: "Kustomization" | "HelmRelease",
  item: NonNullable<FluxListResponse["items"]>[number],
): FluxResource {
  const readyCondition = item.status?.conditions?.find((c) => c.type === "Ready");
  return {
    kind,
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    ready: readyCondition ? readyCondition.status === "True" : null,
    reason: readyCondition?.reason ?? null,
    message: readyCondition?.message ?? null,
  };
}

export async function listKustomizations(): Promise<K8sResult<FluxResource[]>> {
  const result = await k8sRequest<FluxListResponse>(
    "/apis/kustomize.toolkit.fluxcd.io/v1/kustomizations",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => toFluxResource("Kustomization", item)),
  };
}

export async function listHelmReleases(): Promise<K8sResult<FluxResource[]>> {
  const result = await k8sRequest<FluxListResponse>(
    "/apis/helm.toolkit.fluxcd.io/v2/helmreleases",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => toFluxResource("HelmRelease", item)),
  };
}

// --------------------------------------------------------------------- IAM

export interface RbacRole {
  kind: "Role" | "RoleBinding";
  name: string;
  namespace: string;
  detail: string; // rule count, or "<subjects> -> <roleRef>"
}

interface RoleListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    rules?: unknown[];
  }>;
}

interface RoleBindingListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    subjects?: Array<{ kind: string; name: string }>;
    roleRef: { kind: string; name: string };
  }>;
}

export async function listRoles(): Promise<K8sResult<RbacRole[]>> {
  const result = await k8sRequest<RoleListResponse>(
    "/apis/rbac.authorization.k8s.io/v1/roles",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      kind: "Role" as const,
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      detail: `${item.rules?.length ?? 0} rule(s)`,
    })),
  };
}

export async function listRoleBindings(): Promise<K8sResult<RbacRole[]>> {
  const result = await k8sRequest<RoleBindingListResponse>(
    "/apis/rbac.authorization.k8s.io/v1/rolebindings",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      kind: "RoleBinding" as const,
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      detail: `${(item.subjects ?? []).map((s) => `${s.kind}/${s.name}`).join(", ") || "(no subjects)"} -> ${item.roleRef.kind}/${item.roleRef.name}`,
    })),
  };
}

export interface IamNetworkPolicy {
  name: string;
  namespace: string;
  policyTypes: string[];
  /**
   * Real cross-namespace ingress sources for this policy -- the
   * `kubernetes.io/metadata.name` value of every `namespaceSelector` under
   * `spec.ingress[].from[]`. This is the exact selector shape
   * `k8s/network-policies.yaml`'s `*-allow-from-platform-console` rules use
   * (Kubernetes auto-labels every namespace with this well-known label, so
   * matching on it names the source namespace by its real, immutable
   * identity). Empty when the policy has no `ingress` rules at all (e.g. a
   * `*-default-deny`) or none of its rules use a namespaceSelector -- never
   * inferred or fabricated from anything but this exact field.
   */
  ingressFromNamespaces: string[];
}

interface NetworkPolicyListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: {
      policyTypes?: string[];
      ingress?: Array<{
        from?: Array<{
          namespaceSelector?: { matchLabels?: Record<string, string> };
        }>;
      }>;
    };
  }>;
}

export async function listNetworkPolicies(): Promise<K8sResult<IamNetworkPolicy[]>> {
  const result = await k8sRequest<NetworkPolicyListResponse>(
    "/apis/networking.k8s.io/v1/networkpolicies",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => {
      const fromNamespaces = new Set<string>();
      for (const rule of item.spec?.ingress ?? []) {
        for (const peer of rule.from ?? []) {
          const ns = peer.namespaceSelector?.matchLabels?.["kubernetes.io/metadata.name"];
          if (ns) fromNamespaces.add(ns);
        }
      }
      return {
        name: item.metadata.name,
        namespace: item.metadata.namespace,
        policyTypes: item.spec?.policyTypes ?? [],
        ingressFromNamespaces: Array.from(fromNamespaces).sort(),
      };
    }),
  };
}

// ------------------------------------------------------------------- Secrets
//
// Real hyperscaler-PaaS-style Secrets Manager primitive (AWS Secrets
// Manager / GCP Secret Manager / Azure Key Vault equivalent), scoped by
// k8s/paas-rbac.yaml to a Role+RoleBinding per platform namespace (never
// cluster-wide) since Secrets are more sensitive than the read-mostly
// resources above. Secret *values* are never logged, never returned in a
// list response, and never included in any function's return type here --
// only key NAMES are ever surfaced past this file. createSecret is the
// only function that ever sees plaintext values, and it only forwards them
// (base64-encoded, as the k8s Secret API requires) to the API server over
// the same authenticated HTTPS connection every other call in this file
// uses -- nothing is written to a log, a file, or any other sink.

export interface SecretSummary {
  name: string;
  namespace: string;
  createdAt: string;
  keys: string[]; // key NAMES only -- values are never read back out of the cluster
}

interface SecretListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; creationTimestamp: string };
    type?: string;
    data?: Record<string, string>; // base64 values -- deliberately never read past Object.keys()
  }>;
}

interface SecretItem {
  metadata: { name: string; namespace: string; creationTimestamp: string };
  data?: Record<string, string>;
}

function toSecretSummary(item: NonNullable<SecretListResponse["items"]>[number]): SecretSummary {
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    createdAt: item.metadata.creationTimestamp,
    keys: Object.keys(item.data ?? {}),
  };
}

export async function listSecrets(namespace: string): Promise<K8sResult<SecretSummary[]>> {
  const result = await k8sRequest<SecretListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets`,
  );
  if (!result.ok) return result;
  // type=Opaque only -- exclude kubernetes.io/service-account-token and
  // other system-managed secret types the operator/platform itself owns,
  // so this module only ever shows/manages secrets this PaaS surface
  // itself created.
  return {
    ok: true,
    data: (result.data.items ?? [])
      .filter((item) => item.type === undefined || item.type === "Opaque")
      .map(toSecretSummary),
  };
}

/**
 * Creates a real k8s Secret (type: Opaque), base64-encoding each plaintext
 * value as the k8s Secret API requires. `data` is the only place in this
 * module plaintext values are ever held in memory -- the return value is a
 * SecretSummary (key names only), never the values themselves.
 */
export async function createSecret(
  namespace: string,
  name: string,
  data: Record<string, string>,
): Promise<K8sResult<SecretSummary>> {
  const encoded: Record<string, string> = {};
  for (const [key, value] of Object.entries(data)) {
    encoded[key] = Buffer.from(value, "utf8").toString("base64");
  }
  const manifest = {
    apiVersion: "v1",
    kind: "Secret",
    type: "Opaque",
    metadata: { name, namespace },
    data: encoded,
  };
  const result = await k8sRequest<SecretItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toSecretSummary(result.data) };
}

export async function deleteSecret(
  namespace: string,
  name: string,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets/${encodeURIComponent(name)}`,
    "DELETE",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/**
 * Reads and base64-decodes exactly one key of one real Secret. Every other
 * reader in this module (listSecrets/toSecretSummary above) deliberately
 * never looks past `Object.keys(item.data)` because the Secrets Manager UI
 * has no legitimate reason to hold a plaintext value in memory. This
 * function is the one, disclosed exception: the Audit Log module (below,
 * getPostgresConnectionInfo) needs a real plaintext Postgres password to
 * open a direct TCP connection from the console's own Node.js process, the
 * same way createBackupJob/createRestoreJob's Jobs get it via
 * `valueFrom.secretKeyRef` -- this is that same secretKeyRef resolved
 * server-side instead of by a Pod's own env. Never exposed to the client:
 * only ever called from lib/k8s.ts/lib/audit-log.ts, never returned from an
 * API route.
 */
export async function getSecretValue(
  namespace: string,
  name: string,
  key: string,
): Promise<K8sResult<string | null>> {
  const result = await k8sRequest<SecretItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets/${encodeURIComponent(name)}`,
  );
  if (!result.ok) return result;
  const encoded = result.data.data?.[key];
  if (encoded === undefined) return { ok: true, data: null };
  return { ok: true, data: Buffer.from(encoded, "base64").toString("utf8") };
}

/**
 * Reads and base64-decodes EVERY key of one real Secret -- the "give me
 * every key/value pair" counterpart to getSecretValue's "give me exactly
 * one". Same `{ok:true, data:null}`-on-404 convention as getConfigMap
 * (lets callers distinguish "not provisioned yet" from a real API
 * failure). A second, disclosed exception to this module's own
 * "plaintext values are never held past createSecret" rule (see that
 * function's own doc comment) -- used by lib/api-keys.ts, where each
 * Secret value is itself a JSON-encoded API-key record (a one-way SHA-256
 * hash plus the bound identity/role -- never the plaintext key itself,
 * which is never stored anywhere after the one response that creates it).
 */
export async function getSecretData(
  namespace: string,
  name: string,
): Promise<K8sResult<Record<string, string> | null>> {
  const result = await k8sRequest<SecretItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  const decoded: Record<string, string> = {};
  for (const [key, value] of Object.entries(result.data.data ?? {})) {
    decoded[key] = Buffer.from(value, "base64").toString("utf8");
  }
  return { ok: true, data: decoded };
}

/**
 * Real get-then-patch-or-create for a Secret -- the exact same pattern
 * createOrUpdateConfigMap already established for ConfigMaps (a real RFC
 * 7386 merge patch when the object exists, a fresh POST via the existing
 * createSecret when it doesn't), so passing just the one changed key
 * (e.g. one API key's JSON record) updates that key without touching any
 * other key already stored in the Secret.
 */
export async function createOrUpdateSecret(
  namespace: string,
  name: string,
  data: Record<string, string>,
): Promise<K8sResult<SecretSummary>> {
  const existing = await getSecretData(namespace, name);
  if (!existing.ok) return existing;

  if (existing.data) {
    const encoded: Record<string, string> = {};
    for (const [key, value] of Object.entries(data)) {
      encoded[key] = Buffer.from(value, "utf8").toString("base64");
    }
    const result = await k8sRequest<SecretItem>(
      `/api/v1/namespaces/${encodeURIComponent(namespace)}/secrets/${encodeURIComponent(name)}`,
      "PATCH",
      { data: encoded },
      "application/merge-patch+json",
    );
    if (!result.ok) return result;
    return { ok: true, data: toSecretSummary(result.data) };
  }

  return createSecret(namespace, name, data);
}

// ---------------------------------------------------------- Container Registry
//
// Real hyperscaler-PaaS-style Container Registry primitive (ECR / GCR / ACR
// equivalent) -- honestly adapted to what is actually true on this
// cluster: there is no push-capable registry here. Images are built
// locally and `kind load docker-image`d straight into the kind node's
// containerd, so the only registry-shaped truth this console can show is
// an IMAGE INVENTORY: which images each real Deployment's containers
// reference, and whether a real Pod proves that exact image is actually
// present. The console pod has no docker/containerd socket (on purpose --
// see k8s/paas-rbac.yaml), so it cannot run `crictl images` itself; the
// only honest substitute reachable from the k8s API is a real Pod's
// containerStatuses: a Ready container using that image string, with a
// real imageID digest reported, is proof containerd already pulled it. A
// container stuck Waiting with an image-pull reason (ImagePullBackOff /
// ErrImagePull / InvalidImageName) is proof it did not -- a real
// Kubernetes-reported condition, never fabricated.

export interface DeploymentContainerSpec {
  name: string;
  image: string;
}

export interface K8sDeployment {
  name: string;
  namespace: string;
  containers: DeploymentContainerSpec[];
  replicasDesired: number;
  replicasReady: number;
  replicasAvailable: number;
}

interface DeploymentListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: {
      replicas?: number;
      template?: { spec?: { containers?: Array<{ name: string; image: string }> } };
    };
    status?: { readyReplicas?: number; availableReplicas?: number };
  }>;
}

/** Lists real `apps/v1` Deployments in one namespace -- name, namespace,
 * per-container `image` exactly as `spec.template.spec.containers[].image`
 * reports it, and desired/ready/available replica counts from `status`. */
export async function listDeployments(namespace: string): Promise<K8sResult<K8sDeployment[]>> {
  const result = await k8sRequest<DeploymentListResponse>(
    `/apis/apps/v1/namespaces/${encodeURIComponent(namespace)}/deployments`,
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      containers: (item.spec?.template?.spec?.containers ?? []).map((c) => ({
        name: c.name,
        image: c.image,
      })),
      replicasDesired: item.spec?.replicas ?? 0,
      replicasReady: item.status?.readyReplicas ?? 0,
      replicasAvailable: item.status?.availableReplicas ?? 0,
    })),
  };
}

export interface ContainerImageStatus {
  pod: string;
  namespace: string;
  container: string;
  /** Image string as reported on the running container (matches the
   * Deployment's container.image when the Pod is running that spec). */
  image: string;
  /** Real resolved digest reference (`status.containerStatuses[].imageID`),
   * e.g. `sha256:...` -- only populated once the runtime has actually
   * pulled/resolved the image, so its presence alone is evidence the image
   * is really present in containerd. */
  imageID: string | null;
  ready: boolean;
  waitingReason: string | null;
  waitingMessage: string | null;
}

interface PodImageStatusListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    status?: {
      containerStatuses?: Array<{
        name: string;
        image?: string;
        imageID?: string;
        ready?: boolean;
        state?: { waiting?: { reason?: string; message?: string } };
      }>;
    };
  }>;
}

/** Real per-container image status for every Pod in one namespace, read
 * from `status.containerStatuses` -- the k8s-API-only substitute for
 * shelling out to `crictl images` from inside the console pod (which has
 * no containerd socket). Used by the Registry module to decide whether a
 * Deployment's referenced image is actually present (a Ready container
 * reporting that image + a real `imageID` digest) or missing (a container
 * Waiting with an image-pull reason). */
export async function listContainerImageStatuses(
  namespace: string,
): Promise<K8sResult<ContainerImageStatus[]>> {
  const result = await k8sRequest<PodImageStatusListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
  );
  if (!result.ok) return result;
  const out: ContainerImageStatus[] = [];
  for (const pod of result.data.items ?? []) {
    for (const cs of pod.status?.containerStatuses ?? []) {
      out.push({
        pod: pod.metadata.name,
        namespace: pod.metadata.namespace,
        container: cs.name,
        image: cs.image ?? "",
        imageID: cs.imageID ?? null,
        ready: cs.ready ?? false,
        waitingReason: cs.state?.waiting?.reason ?? null,
        waitingMessage: cs.state?.waiting?.message ?? null,
      });
    }
  }
  return { ok: true, data: out };
}

// ---------------------------------------------------------------------- Logs
//
// Real hyperscaler-PaaS-style Logs primitive (CloudWatch Logs / GCP Cloud
// Logging / Azure Monitor Logs equivalent) -- reads real pod stdout/stderr
// via the pod log subresource (GET .../pods/{pod}/log). Scoped by
// k8s/paas-rbac.yaml to a Role+RoleBinding per platform namespace, the
// same pattern the Secrets Manager module above uses and for the same
// reason: pod logs can contain application output more sensitive than the
// read-mostly resources in the ClusterRole, so this is never granted
// cluster-wide.

export interface K8sPod {
  name: string;
  namespace: string;
  phase: string;
  containers: string[];
  ready: boolean;
}

interface PodListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: { containers?: Array<{ name: string }> };
    status?: {
      phase?: string;
      containerStatuses?: Array<{ ready: boolean }>;
    };
  }>;
}

export async function listPods(
  namespace: string,
  labelSelector?: string,
): Promise<K8sResult<K8sPod[]>> {
  const qs = labelSelector ? `?labelSelector=${encodeURIComponent(labelSelector)}` : "";
  const result = await k8sRequest<PodListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods${qs}`,
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => {
      const statuses = item.status?.containerStatuses ?? [];
      return {
        name: item.metadata.name,
        namespace: item.metadata.namespace,
        phase: item.status?.phase ?? "Unknown",
        containers: (item.spec?.containers ?? []).map((c) => c.name),
        ready: statuses.length > 0 && statuses.every((cs) => cs.ready),
      };
    }),
  };
}

export interface PodLogOptions {
  /** Defaults to 200, matching the Logs page default. */
  tailLines?: number;
  /** Required when the pod has more than one container. */
  container?: string;
}

/**
 * Fetches real pod logs via the pods/log subresource. Unlike every other
 * function in this file, the API server's response body here is raw text
 * (real container stdout/stderr), never JSON -- so this cannot reuse
 * k8sRequest's JSON.parse and instead makes its own request with the same
 * fail-closed/timeout/error conventions. Error responses (403, 404, ...)
 * from this subresource ARE a JSON Status object, so those are parsed for
 * a real message when possible; a non-JSON error body is surfaced as-is.
 */
export async function getPodLogs(
  namespace: string,
  pod: string,
  options: PodLogOptions = {},
): Promise<K8sResult<string>> {
  const cfg = readInClusterConfig();
  if (!cfg) {
    return {
      ok: false,
      error:
        "not configured: no in-cluster ServiceAccount credentials found " +
        `(${SA_DIR}) -- this only works when running as the platform-console pod`,
    };
  }

  const params = new URLSearchParams({
    tailLines: String(options.tailLines ?? 200),
    timestamps: "true",
  });
  if (options.container) params.set("container", options.container);
  const path = `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(pod)}/log?${params.toString()}`;

  return new Promise((resolve) => {
    const req = https.request(
      {
        host: cfg.host,
        port: cfg.port,
        path,
        method: "GET",
        ca: cfg.ca,
        timeout: REQUEST_TIMEOUT_MS,
        headers: {
          Authorization: `Bearer ${cfg.token}`,
          Accept: "text/plain, application/json",
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const status = res.statusCode ?? 0;
          const raw = Buffer.concat(chunks).toString("utf8");
          if (status < 200 || status >= 300) {
            let message = raw || `HTTP ${status}`;
            try {
              const parsed = JSON.parse(raw) as { message?: string };
              if (parsed.message) message = parsed.message;
            } catch {
              // Not JSON -- use the raw body (or the HTTP status) as-is.
            }
            resolve({ ok: false, error: `GET ${path} failed: ${message}` });
            return;
          }
          resolve({ ok: true, data: raw });
        });
      },
    );
    req.on("timeout", () => req.destroy(new Error(`timeout after ${REQUEST_TIMEOUT_MS}ms`)));
    req.on("error", (err) =>
      resolve({ ok: false, error: `unreachable: ${err.message}` }),
    );
    req.end();
  });
}

// ---------------------------------------------------------- Database Backups
//
// Real hyperscaler-PaaS-style Database Backups primitive (RDS / Cloud SQL /
// Cloud Spanner automated-backup equivalent). On-demand backup is a real
// `batch/v1` Job that runs `pg_dump` inside its own Pod against the target
// Postgres's real Service (`<name>.<namespace>.svc.cluster.local:5432`),
// using the exact same container image and the exact same password
// Secret/key the source Postgres Pod's own spec already references --
// read live off that Pod (createBackupJob's first step) rather than
// re-typed or guessed, so a backup can never silently drift to the wrong
// Postgres version or a stale/second credential. The dump is written to a
// PersistentVolumeClaim (platform-backups-pvc, created on first use if
// missing -- see ensureBackupsPvc). PVC contents are not directly
// queryable via the k8s API, so the honest backup inventory this module
// exposes is the Jobs themselves: name (encodes the timestamp), creation
// time, real completion status, real duration -- never a fabricated
// separate catalog. Scoped by k8s/paas-rbac.yaml to a single
// Role+RoleBinding in supabase-demo (get/list/create on batch/jobs and
// persistentvolumeclaims) -- never cluster-wide, and no update/patch/
// delete on either resource: a Job or PVC created wrong is left for a
// human with real kubectl access to clean up, not silently patched here.

export interface BackupJob {
  name: string;
  namespace: string;
  createdAt: string;
  startTime: string | null;
  completionTime: string | null;
  succeeded: number;
  failed: number;
  active: number;
  status: "Pending" | "Running" | "Complete" | "Failed";
  durationSeconds: number | null;
}

interface JobListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; creationTimestamp: string };
    status?: {
      active?: number;
      succeeded?: number;
      failed?: number;
      startTime?: string;
      completionTime?: string;
    };
  }>;
}

function toBackupJob(item: NonNullable<JobListResponse["items"]>[number]): BackupJob {
  const succeeded = item.status?.succeeded ?? 0;
  const failed = item.status?.failed ?? 0;
  const active = item.status?.active ?? 0;
  const startTime = item.status?.startTime ?? null;
  const completionTime = item.status?.completionTime ?? null;
  let status: BackupJob["status"] = "Pending";
  if (succeeded > 0) status = "Complete";
  else if (failed > 0) status = "Failed";
  else if (active > 0) status = "Running";
  const durationSeconds =
    startTime && completionTime
      ? (new Date(completionTime).getTime() - new Date(startTime).getTime()) / 1000
      : null;
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    createdAt: item.metadata.creationTimestamp,
    startTime,
    completionTime,
    succeeded,
    failed,
    active,
    status,
    durationSeconds,
  };
}

/**
 * Lists real `batch/v1` Jobs -- optionally filtered by label selector (the
 * Backups module passes `app=platform-backups` so operator-internal Jobs
 * already running in the same namespace, e.g. the supabase-operator's own
 * migration/sync Jobs, never appear in the backup inventory). This listing
 * IS the backup record: a completed Job whose own name encodes its
 * creation timestamp, never a separate fabricated catalog.
 */
export async function listJobs(
  namespace: string,
  labelSelector?: string,
): Promise<K8sResult<BackupJob[]>> {
  const qs = labelSelector ? `?labelSelector=${encodeURIComponent(labelSelector)}` : "";
  const result = await k8sRequest<JobListResponse>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs${qs}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toBackupJob) };
}

export interface BackupPvcStatus {
  name: string;
  namespace: string;
  phase: string | null;
  capacity: string | null;
  storageClassName: string | null;
}

interface PvcItem {
  metadata: { name: string; namespace: string };
  spec?: { storageClassName?: string; resources?: { requests?: { storage?: string } } };
  status?: { phase?: string; capacity?: { storage?: string } };
}

function toPvcStatus(item: PvcItem): BackupPvcStatus {
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    phase: item.status?.phase ?? null,
    capacity: item.status?.capacity?.storage ?? item.spec?.resources?.requests?.storage ?? null,
    storageClassName: item.spec?.storageClassName ?? null,
  };
}

/**
 * Reads the real PVC's status (phase/capacity/storage class). Returns
 * `{ ok: true, data: null }` -- not an error -- when the PVC hasn't been
 * provisioned yet, since that is itself honest, actionable state for the
 * Backups page to render ("not yet provisioned" rather than a fabricated
 * placeholder).
 */
export async function getBackupsPvc(
  namespace: string,
  name: string,
): Promise<K8sResult<BackupPvcStatus | null>> {
  const result = await k8sRequest<PvcItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/persistentvolumeclaims/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: toPvcStatus(result.data) };
}

/**
 * Creates the PVC the backup Jobs below write into, if it doesn't already
 * exist -- a real get-then-create, so calling this on every backup run is
 * a no-op after the first (never a spurious "already exists" error).
 * `storageClassName` is deliberately omitted from the manifest so the
 * cluster's own default StorageClass (the `(default)`-annotated one --
 * `standard`, backed by `rancher.io/local-path`, on this cluster) fills it
 * in via the API server's DefaultStorageClass admission plugin; it is
 * never hardcoded here.
 */
export async function ensureBackupsPvc(
  namespace: string,
  name: string,
  size: string,
): Promise<K8sResult<BackupPvcStatus>> {
  const existing = await getBackupsPvc(namespace, name);
  if (!existing.ok) return existing;
  if (existing.data) return { ok: true, data: existing.data };

  const manifest = {
    apiVersion: "v1",
    kind: "PersistentVolumeClaim",
    metadata: { name, namespace, labels: { app: "platform-backups" } },
    spec: {
      accessModes: ["ReadWriteOnce"],
      resources: { requests: { storage: size } },
    },
  };
  const result = await k8sRequest<PvcItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/persistentvolumeclaims`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toPvcStatus(result.data) };
}

interface PodSpecEnvVar {
  name: string;
  value?: string;
  valueFrom?: { secretKeyRef?: { name: string; key: string } };
}

interface PodSpecResponse {
  metadata: { name: string; namespace: string };
  spec?: {
    containers?: Array<{ name: string; image: string; env?: PodSpecEnvVar[] }>;
  };
}

async function getPodSpec(namespace: string, name: string): Promise<K8sResult<PodSpecResponse>> {
  return k8sRequest<PodSpecResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(name)}`,
  );
}

const BACKUPS_PVC_NAME = "platform-backups-pvc";
const BACKUPS_PVC_SIZE = "1Gi";

/**
 * Creates a real k8s Job that runs `pg_dump` against the target Postgres
 * Pod's own Service, using the exact same container image and the exact
 * same password Secret/key that source Pod's own spec already uses (read
 * live off `getPodSpec` -- never re-typed, never a second credential this
 * module invents; if the Pod has no PGPASSWORD/POSTGRES_PASSWORD sourced
 * from a real Secret, this refuses rather than inventing one). The Job
 * writes its dump straight to `platform-backups-pvc` (provisioned on first
 * call via `ensureBackupsPvc` if missing) at a path that encodes the Job's
 * own name, which itself encodes the creation timestamp -- so `listJobs`
 * above is a complete, honest inventory with no separate catalog to fall
 * out of sync.
 */
export async function createBackupJob(
  namespace: string,
  dbPodName: string,
): Promise<K8sResult<BackupJob>> {
  const podResult = await getPodSpec(namespace, dbPodName);
  if (!podResult.ok) return podResult;

  const container = podResult.data.spec?.containers?.[0];
  if (!container) {
    return { ok: false, error: `pod ${namespace}/${dbPodName} has no containers in its spec` };
  }

  const passwordEnv = container.env?.find(
    (e) =>
      (e.name === "PGPASSWORD" || e.name === "POSTGRES_PASSWORD") && e.valueFrom?.secretKeyRef,
  );
  if (!passwordEnv?.valueFrom?.secretKeyRef) {
    return {
      ok: false,
      error: `pod ${namespace}/${dbPodName} has no PGPASSWORD/POSTGRES_PASSWORD env sourced from a Secret -- refusing to invent a credential`,
    };
  }
  const pgUser = container.env?.find((e) => e.name === "POSTGRES_USER")?.value ?? "postgres";
  const pgDatabase =
    container.env?.find((e) => e.name === "PGDATABASE" || e.name === "POSTGRES_DB")?.value ??
    "postgres";

  // The Service backing a StatefulSet Pod shares the StatefulSet's name,
  // which is the Pod name minus its ordinal suffix (demo-db-postgres-0 ->
  // demo-db-postgres) -- true for every StatefulSet-backed database this
  // console creates (see createSingleDatabase above) or that the
  // supabase-operator itself creates, so this is a real structural
  // convention, not a guess specific to demo-db.
  const stem = dbPodName.replace(/-\d+$/, "");
  const host = `${stem}.${namespace}.svc.cluster.local`;

  const pvcResult = await ensureBackupsPvc(namespace, BACKUPS_PVC_NAME, BACKUPS_PVC_SIZE);
  if (!pvcResult.ok) return pvcResult;

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+Z$/, "z")
    .toLowerCase();
  const jobName = `pg-backup-${stem}-${timestamp}`.slice(0, 63).replace(/-+$/, "");
  const dumpPath = `/backups/${namespace}/${stem}/${jobName}.sql`;

  const dumpScript = [
    "set -e",
    `mkdir -p "$(dirname "${dumpPath}")"`,
    `pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "${dumpPath}"`,
    `ls -la "${dumpPath}"`,
  ].join("\n");

  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name: jobName,
      namespace,
      labels: { app: "platform-backups", "backup-source-pod": dbPodName, database: stem },
    },
    spec: {
      backoffLimit: 0,
      template: {
        metadata: { labels: { app: "platform-backups", job: jobName } },
        spec: {
          restartPolicy: "Never",
          containers: [
            {
              name: "pg-dump",
              image: container.image,
              command: ["sh", "-c", dumpScript],
              env: [
                { name: "PGHOST", value: host },
                { name: "PGPORT", value: "5432" },
                { name: "PGUSER", value: pgUser },
                { name: "PGDATABASE", value: pgDatabase },
                {
                  name: "PGPASSWORD",
                  valueFrom: { secretKeyRef: passwordEnv.valueFrom.secretKeyRef },
                },
              ],
              volumeMounts: [{ name: "backups", mountPath: "/backups" }],
            },
          ],
          volumes: [
            { name: "backups", persistentVolumeClaim: { claimName: BACKUPS_PVC_NAME } },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<NonNullable<JobListResponse["items"]>[number]>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toBackupJob(result.data) };
}

// ------------------------------------------------------- Database Restores
//
// Real hyperscaler-PaaS-style point-in-time-restore equivalent (RDS "Restore
// to point in time" / Cloud SQL "Restore" equivalent) for the on-demand
// backups above. A real `batch/v1` Job, same shape and same
// credential-discovery pattern as createBackupJob: it reads the TARGET
// Postgres Pod's own spec/env live (never a second, re-typed credential),
// mounts the exact same `platform-backups-pvc` the backup Jobs write into
// (read-only here -- this Job never writes to the PVC), and locates the
// specific dump file the named backup Job produced by reading that Job's own
// object back from the API server (its `database` label, the same value
// createBackupJob wrote into `dumpPath`) rather than re-parsing/guessing a
// path out of the Job's name string.
//
// createBackupJob's real pg_dump invocation has no `-F` flag, so the dump is
// plain SQL (confirmed live: the dump file starts with `-- PostgreSQL
// database dump`, `\restrict <token>`, plain `CREATE TABLE`/`COPY ... FROM
// stdin` statements) -- so restore uses `psql -f`, never `pg_restore` (which
// only reads pg_dump's custom/directory/tar formats). A plain dump also
// carries no `--clean`/`--if-exists` DROP statements, so loading it directly
// on top of a target that still has the same rows would abort every
// `COPY ... FROM stdin` block at the first pre-existing-row conflict
// (COPY is one atomic statement -- a single duplicate-key error rolls back
// that whole table's data, not just the offending row), silently restoring
// nothing. To give this real restore-overwrites-target semantics (the same
// "this replaces the target's contents" behavior RDS/Cloud SQL restore has),
// the Job's script first clears every real table it can before running
// `psql -f`.
//
// Live-discovered, disclosed constraint (checked directly against this
// cluster's real demo-db-postgres before writing this script, not assumed):
// the credential createBackupJob's own discovery pattern finds (the
// `postgres` role) is NOT a Postgres superuser and does NOT own most of the
// real schemas here (`auth`/`storage`/`_realtime`/... are owned by
// `supabase_admin`/`supabase_auth_admin`, confirmed live via `\dn+` and
// `select usesuper from pg_user`) -- so a `DROP SCHEMA ... CASCADE` (which
// requires ownership or superuser) fails with a real `must be owner of
// schema` error for nearly every schema. What that same role DOES have,
// confirmed live via `information_schema.role_table_grants`, is real
// row-level DML (INSERT/UPDATE/DELETE/TRUNCATE) on the actual data tables
// via explicit GRANTs -- so the clearing step is a per-table `TRUNCATE
// ... CASCADE` (real DML the credential is actually authorized for) inside
// a loop that catches `insufficient_privilege` per table and skips it
// (logged via RAISE NOTICE, never silently swallowed) rather than aborting
// the whole clear because one system-owned table (e.g. a migrations table)
// isn't grantable to `postgres`. `psql -f` on the dump itself then runs
// WITHOUT `-v ON_ERROR_STOP=1`: a plain dump replayed by a non-owner,
// non-superuser role against a target whose schemas/tables already exist
// necessarily produces real, expected, harmless per-statement errors on
// every `CREATE SCHEMA`/`CREATE TABLE`/permission-gated DDL statement in
// the dump (the objects already exist and this role isn't allowed to
// touch their DDL) -- live-confirmed these are cosmetic: the load-bearing
// `COPY ... FROM stdin` data statements for tables the role has TRUNCATE
// (and therefore INSERT) on still succeed and really restore the row data,
// confirmed end-to-end against a real deleted-and-restored user (see the
// evidence bundle's restore-recovers-real-deleted-data control). A dump
// whose table ordering doesn't respect every FK dependency can still leave
// a same-run child-table COPY failing on a not-yet-loaded parent row (also
// observed and disclosed there) -- a real limitation of single-pass replay
// into a live, non-empty, non-owned target, not swept under the rug. Both
// psql invocations still log everything to the Job's own pod logs (`kubectl
// logs`), the same real inspection path every other Job in this module
// relies on. No new RBAC: reuses the same `platform-console-backups` Role's
// `batch/jobs` create verb (no update/patch/delete, same as backups) --
// see k8s/paas-rbac.yaml.

interface JobItem {
  metadata: { name: string; namespace: string; creationTimestamp: string; labels?: Record<string, string> };
  status?: {
    active?: number;
    succeeded?: number;
    failed?: number;
    startTime?: string;
    completionTime?: string;
  };
}

async function getJob(namespace: string, name: string): Promise<K8sResult<JobItem>> {
  return k8sRequest<JobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(name)}`,
  );
}

/**
 * Creates a real `batch/v1` restore Job. `backupJobName` must name a real,
 * already-`Complete` backup Job created by createBackupJob above (its
 * `database` label is read back to locate the exact dump file that Job
 * wrote -- refuses if the Job doesn't exist, has no `database` label, or
 * hasn't reached `status.succeeded >= 1`, since restoring from an
 * incomplete/failed/nonexistent backup would be dishonest). `targetDbPodName`
 * is the live Postgres Pod to restore into -- its own spec/env supplies the
 * restore Job's credentials, exactly as createBackupJob does for the source
 * side, so this can restore into a different Pod than the one the backup
 * was taken from, not just back into itself.
 */
export async function createRestoreJob(
  namespace: string,
  backupJobName: string,
  targetDbPodName: string,
): Promise<K8sResult<BackupJob>> {
  const jobResult = await getJob(namespace, backupJobName);
  if (!jobResult.ok) {
    return { ok: false, error: `backup Job ${backupJobName} not found: ${jobResult.error}` };
  }
  const sourceStem = jobResult.data.metadata.labels?.database;
  if (!sourceStem) {
    return {
      ok: false,
      error: `backup Job ${backupJobName} has no "database" label -- cannot locate its dump file`,
    };
  }
  if ((jobResult.data.status?.succeeded ?? 0) < 1) {
    return {
      ok: false,
      error: `backup Job ${backupJobName} has not reached Complete (status.succeeded=${jobResult.data.status?.succeeded ?? 0}) -- refusing to restore from an incomplete or failed backup`,
    };
  }
  const dumpPath = `/backups/${namespace}/${sourceStem}/${backupJobName}.sql`;

  const podResult = await getPodSpec(namespace, targetDbPodName);
  if (!podResult.ok) return podResult;

  const container = podResult.data.spec?.containers?.[0];
  if (!container) {
    return { ok: false, error: `pod ${namespace}/${targetDbPodName} has no containers in its spec` };
  }

  const passwordEnv = container.env?.find(
    (e) =>
      (e.name === "PGPASSWORD" || e.name === "POSTGRES_PASSWORD") && e.valueFrom?.secretKeyRef,
  );
  if (!passwordEnv?.valueFrom?.secretKeyRef) {
    return {
      ok: false,
      error: `pod ${namespace}/${targetDbPodName} has no PGPASSWORD/POSTGRES_PASSWORD env sourced from a Secret -- refusing to invent a credential`,
    };
  }
  const pgUser = container.env?.find((e) => e.name === "POSTGRES_USER")?.value ?? "postgres";
  const pgDatabase =
    container.env?.find((e) => e.name === "PGDATABASE" || e.name === "POSTGRES_DB")?.value ??
    "postgres";

  const targetStem = targetDbPodName.replace(/-\d+$/, "");
  const host = `${targetStem}.${namespace}.svc.cluster.local`;

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+Z$/, "z")
    .toLowerCase();
  const jobName = `pg-restore-${targetStem}-${timestamp}`.slice(0, 63).replace(/-+$/, "");

  // Written via a QUOTED heredoc ('CLEARSQL') rather than inlined into a
  // `psql -c "..."` shell argument -- a quoted heredoc disables all shell
  // expansion inside it, which plain double-quoting would not: the SQL's
  // own `$do$` dollar-quote tag would otherwise be parsed by sh as `$do`
  // (an unset shell variable, expanding to empty) followed by a stray `$`,
  // corrupting the PL/pgSQL block before psql ever sees it.
  const restoreScript = [
    "set -e",
    `test -f "${dumpPath}" || { echo "backup dump not found at ${dumpPath}" >&2; exit 1; }`,
    `cat <<'CLEARSQL' > /tmp/clear_tables.sql`,
    "DO $do$",
    "DECLARE",
    "  r record;",
    "BEGIN",
    "  FOR r IN",
    "    SELECT n.nspname, c.relname",
    "    FROM pg_class c",
    "    JOIN pg_namespace n ON n.oid = c.relnamespace",
    "    WHERE c.relkind = 'r'",
    "      AND n.nspname NOT IN ('pg_catalog','information_schema')",
    "      AND n.nspname NOT LIKE 'pg_temp_%'",
    "      AND n.nspname NOT LIKE 'pg_toast%'",
    "  LOOP",
    "    BEGIN",
    "      EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.nspname) || '.' || quote_ident(r.relname) || ' CASCADE';",
    "    EXCEPTION WHEN insufficient_privilege THEN",
    "      RAISE NOTICE 'restore: skipping % (insufficient_privilege on this credential)', r.nspname || '.' || r.relname;",
    "    END;",
    "  END LOOP;",
    "END $do$;",
    "CLEARSQL",
    `echo "Clearing existing table data in $PGDATABASE before restore (this credential owns no schemas here -- TRUNCATE, not DROP SCHEMA -- see lib/k8s.ts createRestoreJob for why)..."`,
    `psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -v ON_ERROR_STOP=1 -f /tmp/clear_tables.sql`,
    `echo "Restoring ${dumpPath} into $PGDATABASE (per-statement errors below on already-existing/not-owned DDL are expected -- see module doc; the real data COPY statements are what matters)..."`,
    `psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -f "${dumpPath}"`,
    `echo "Restore script finished."`,
  ].join("\n");

  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name: jobName,
      namespace,
      labels: {
        app: "platform-restores",
        "restore-source-job": backupJobName,
        "restore-target-pod": targetDbPodName,
        database: targetStem,
      },
    },
    spec: {
      backoffLimit: 0,
      template: {
        metadata: { labels: { app: "platform-restores", job: jobName } },
        spec: {
          restartPolicy: "Never",
          containers: [
            {
              name: "pg-restore",
              image: container.image,
              command: ["sh", "-c", restoreScript],
              env: [
                { name: "PGHOST", value: host },
                { name: "PGPORT", value: "5432" },
                { name: "PGUSER", value: pgUser },
                { name: "PGDATABASE", value: pgDatabase },
                {
                  name: "PGPASSWORD",
                  valueFrom: { secretKeyRef: passwordEnv.valueFrom.secretKeyRef },
                },
              ],
              volumeMounts: [{ name: "backups", mountPath: "/backups", readOnly: true }],
            },
          ],
          volumes: [
            {
              name: "backups",
              persistentVolumeClaim: { claimName: BACKUPS_PVC_NAME, readOnly: true },
            },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<NonNullable<JobListResponse["items"]>[number]>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toBackupJob(result.data) };
}

/** Public read of one real batch/v1 Job's status, for callers outside this
 * module (export-all polling) that need the same status a moment-in-time
 * `listJobs` row would show without listing the whole namespace. */
export async function getJobStatus(namespace: string, name: string): Promise<K8sResult<BackupJob>> {
  const result = await getJob(namespace, name);
  if (!result.ok) return result;
  return { ok: true, data: toBackupJob(result.data) };
}

/** Deletes a real batch/v1 Job (and, via the API server's default Job
 * ownerReference, its Pod) -- used to clean up the short-lived reader Jobs
 * createDumpReaderJob below creates once their output has been read. */
export async function deleteJob(namespace: string, name: string): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(name)}?propagationPolicy=Background`,
    "DELETE",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/**
 * Creates a real, short-lived `batch/v1` Job that mounts the same
 * `platform-backups-pvc` (read-only) createBackupJob/createRestoreJob use,
 * and base64-encodes one already-`Complete` backup Job's real dump file to
 * its own stdout -- the only way this console (which has no direct
 * filesystem access to the PVC) can read a real dump's actual bytes back
 * out of the cluster, short of `kubectl cp`. Same validation as
 * createRestoreJob: refuses unless `backupJobName` is a real Job with a
 * `database` label and `status.succeeded >= 1`. Callers poll the returned
 * Job's status (getJobStatus), read its Pod's stdout (getPodLogs) once
 * Complete, base64-decode it, then delete the Job (deleteJob) -- this
 * function only creates it.
 */
export async function createDumpReaderJob(
  namespace: string,
  backupJobName: string,
): Promise<K8sResult<BackupJob>> {
  const jobResult = await getJob(namespace, backupJobName);
  if (!jobResult.ok) {
    return { ok: false, error: `backup Job ${backupJobName} not found: ${jobResult.error}` };
  }
  const stem = jobResult.data.metadata.labels?.database;
  if (!stem) {
    return {
      ok: false,
      error: `backup Job ${backupJobName} has no "database" label -- cannot locate its dump file`,
    };
  }
  if ((jobResult.data.status?.succeeded ?? 0) < 1) {
    return {
      ok: false,
      error: `backup Job ${backupJobName} has not reached Complete -- refusing to read an incomplete dump`,
    };
  }
  const dumpPath = `/backups/${namespace}/${stem}/${backupJobName}.sql`;

  const readerScript = [
    "set -e",
    `test -f "${dumpPath}" || { echo "dump not found at ${dumpPath}" >&2; exit 1; }`,
    `base64 "${dumpPath}"`,
  ].join("\n");

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+Z$/, "z")
    .toLowerCase();
  const jobName = `pg-dump-read-${stem}-${timestamp}`.slice(0, 63).replace(/-+$/, "");

  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name: jobName,
      namespace,
      labels: { app: "platform-dump-readers", "backup-source-job": backupJobName, database: stem },
    },
    spec: {
      backoffLimit: 0,
      ttlSecondsAfterFinished: 300,
      template: {
        metadata: { labels: { app: "platform-dump-readers", job: jobName } },
        spec: {
          restartPolicy: "Never",
          containers: [
            {
              name: "dump-reader",
              image: "busybox:1.36",
              imagePullPolicy: "IfNotPresent",
              command: ["sh", "-c", readerScript],
              resources: {
                requests: { cpu: "10m", memory: "16Mi" },
                limits: { cpu: "50m", memory: "64Mi" },
              },
              volumeMounts: [{ name: "backups", mountPath: "/backups", readOnly: true }],
            },
          ],
          volumes: [
            { name: "backups", persistentVolumeClaim: { claimName: BACKUPS_PVC_NAME, readOnly: true } },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<NonNullable<JobListResponse["items"]>[number]>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toBackupJob(result.data) };
}

// ------------------------------------------------------------ Audit Log DB
//
// Real hyperscaler-CloudTrail/GCP-Audit-Logs/Azure-Activity-Log equivalent:
// a durable, queryable "who did what" history, as opposed to
// lib/audit-log.ts's existing stdout line (real, but ephemeral -- gone the
// moment a pod restarts). Rather than inventing a second credential or a
// second database, this reuses the exact same live Postgres this cluster
// already runs for demo-project (lib/k8s.ts's own createBackupJob/
// createRestoreJob functions above already trust it enough to dump/restore
// real tenant data), in its own `platform_console` schema so it's
// unambiguous this table belongs to the console app, not to any
// Supabase-owned schema (public/auth/storage/_realtime/...) in that same
// database.

export interface PostgresConnectionInfo {
  host: string;
  port: number;
  user: string;
  database: string;
  password: string;
}

/**
 * Resolves real, live connection info for a StatefulSet-backed Postgres
 * Pod -- the exact same credential-discovery convention as
 * createBackupJob/createRestoreJob above (reads the Pod's own live
 * PGPASSWORD/POSTGRES_PASSWORD env, sourced from a real Secret; refuses
 * rather than inventing a credential if it isn't). The one difference:
 * those Jobs hand the Secret reference to a Pod spec and let THAT Pod's
 * own kubelet resolve the plaintext; this caller (the console's own
 * long-running Node.js process, not a one-shot Job) needs the plaintext
 * itself to open a direct TCP connection, so it performs one additional
 * real GET on that Secret via getSecretValue above.
 */
export async function getPostgresConnectionInfo(
  namespace: string,
  dbPodName: string,
): Promise<K8sResult<PostgresConnectionInfo>> {
  const podResult = await getPodSpec(namespace, dbPodName);
  if (!podResult.ok) return podResult;

  const container = podResult.data.spec?.containers?.[0];
  if (!container) {
    return { ok: false, error: `pod ${namespace}/${dbPodName} has no containers in its spec` };
  }

  const passwordEnv = container.env?.find(
    (e) =>
      (e.name === "PGPASSWORD" || e.name === "POSTGRES_PASSWORD") && e.valueFrom?.secretKeyRef,
  );
  if (!passwordEnv?.valueFrom?.secretKeyRef) {
    return {
      ok: false,
      error: `pod ${namespace}/${dbPodName} has no PGPASSWORD/POSTGRES_PASSWORD env sourced from a Secret -- refusing to invent a credential`,
    };
  }
  const { name: secretName, key: secretKey } = passwordEnv.valueFrom.secretKeyRef;
  const secretResult = await getSecretValue(namespace, secretName, secretKey);
  if (!secretResult.ok) return secretResult;
  if (secretResult.data === null) {
    return {
      ok: false,
      error: `secret ${namespace}/${secretName} has no key '${secretKey}' -- refusing to invent a credential`,
    };
  }

  const pgUser = container.env?.find((e) => e.name === "POSTGRES_USER")?.value ?? "postgres";
  const pgDatabase =
    container.env?.find((e) => e.name === "PGDATABASE" || e.name === "POSTGRES_DB")?.value ??
    "postgres";

  // Same StatefulSet-Service-name convention createBackupJob/
  // createRestoreJob already rely on (demo-db-postgres-0 -> Service
  // demo-db-postgres).
  const stem = dbPodName.replace(/-\d+$/, "");
  const host = `${stem}.${namespace}.svc.cluster.local`;

  return {
    ok: true,
    data: { host, port: 5432, user: pgUser, database: pgDatabase, password: secretResult.data },
  };
}

// -------------------------------------------------------------- Cost & Usage
//
// Real hyperscaler-PaaS-style Cost & Usage primitive (AWS Cost Explorer /
// GCP Billing Reports / Azure Cost Management equivalent) -- deliberately
// WITHOUT any payment processor or fabricated currency. This cluster has no
// billing system, so the only honest substitute is what is actually true
// and measurable: real live per-pod CPU/memory usage from the metrics
// pipeline already installed and verified on this cluster
// (metrics-server, confirmed working by the autoscaling-enforced control --
// `kubectl top` returns real numbers, not `error: Metrics API not
// available`), combined with the real per-namespace ResourceQuota object
// (the actual ceiling each namespace's workloads are bound by). This
// module reports real, currently-measured infrastructure consumption --
// millicores, MiB, and a plain percentage-of-quota figure -- never a
// dollar amount tied to any real biller.
//
// Uses the exact same in-cluster API pattern as every other function in
// this file (k8sRequest against the pod's own ServiceAccount token/CA),
// reading two additional resource types: `metrics.k8s.io/v1beta1` PodMetrics
// (real-time, reported by the kubelet's cAdvisor, scraped by metrics-server
// on its own interval -- typically ~15-60s stale, never fabricated) and the
// core `resourcequotas` object already used to gate real Pod admission
// (confirmed live via the resource-quotas-enforced control's negative
// test). Both verbs (`get`/`list` on `pods.metrics.k8s.io` and
// `resourcequotas`) were added to the existing cluster-wide
// `ClusterRole/platform-console-paas` in k8s/paas-rbac.yaml -- same
// sensitivity class as the Services/Deployments/Roles already granted
// cluster-wide there (workload metadata and resource ceilings, not
// secrets), confirmed via `kubectl auth can-i` returning real `no` for both
// verbs before the RBAC change and real `yes` after.

/**
 * Parses a Kubernetes `resource.Quantity` string (used for both CPU and
 * memory fields across PodMetrics and ResourceQuota) into a plain number in
 * its base unit (cores for CPU, bytes for memory) -- the caller converts to
 * millicores/MiB. Handles every suffix actually observed live on this
 * cluster (`n` nanocores on PodMetrics CPU, `Ki` on PodMetrics/Quota
 * memory, `m` and bare-integer cores on Quota CPU, `Gi`/`Mi` on Quota
 * memory) plus the rest of the documented Kubernetes quantity suffix set
 * (`u`, decimal `k`/`M`/`G`/`T`/`P`/`E`, binary `Ti`/`Pi`/`Ei`) for
 * robustness against values this cluster doesn't currently happen to emit.
 * Returns `null` on anything that doesn't parse -- never a fabricated 0.
 */
const QUANTITY_SUFFIX_MULTIPLIERS: Record<string, number> = {
  n: 1e-9,
  u: 1e-6,
  m: 1e-3,
  "": 1,
  k: 1e3,
  M: 1e6,
  G: 1e9,
  T: 1e12,
  P: 1e15,
  E: 1e18,
  Ki: 2 ** 10,
  Mi: 2 ** 20,
  Gi: 2 ** 30,
  Ti: 2 ** 40,
  Pi: 2 ** 50,
  Ei: 2 ** 60,
};

export function parseK8sQuantity(raw: string | undefined): number | null {
  if (!raw) return null;
  const match = /^([0-9.eE+-]+)(Ki|Mi|Gi|Ti|Pi|Ei|[numkMGTPE]?)$/.exec(raw.trim());
  if (!match) return null;
  const [, numStr, suffix] = match;
  const num = Number(numStr);
  if (!Number.isFinite(num)) return null;
  const multiplier = QUANTITY_SUFFIX_MULTIPLIERS[suffix];
  if (multiplier === undefined) return null;
  return num * multiplier;
}

function quantityToMillicores(raw: string | undefined): number | null {
  const cores = parseK8sQuantity(raw);
  return cores === null ? null : cores * 1000;
}

function quantityToMiB(raw: string | undefined): number | null {
  const bytes = parseK8sQuantity(raw);
  return bytes === null ? null : bytes / (1024 * 1024);
}

export { quantityToMillicores, quantityToMiB };

export interface ResourceQuotaSnapshot {
  name: string;
  namespace: string;
  /** Hard ceiling on the sum of every container's resource *limit* in the
   * namespace -- the real bound live usage cannot exceed without being
   * throttled (CPU) or OOM-killed (memory). `null` when the ResourceQuota
   * object doesn't set that particular field. */
  hardCpuMillicores: number | null;
  hardMemoryMiB: number | null;
  /** Hard ceiling on the sum of every container's resource *request*
   * (reservation) in the namespace -- shown for context; usage is compared
   * against the limits fields above, since that is the ceiling usage is
   * actually bound by. */
  hardRequestsCpuMillicores: number | null;
  hardRequestsMemoryMiB: number | null;
  hardPods: number | null;
  usedPods: number | null;
}

interface ResourceQuotaListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    status?: {
      hard?: Record<string, string>;
      used?: Record<string, string>;
    };
  }>;
}

/**
 * Reads the real ResourceQuota object for one namespace. Returns
 * `{ ok: true, data: null }` -- not an error -- when the namespace has no
 * ResourceQuota at all (true today for `supabase-demo`, confirmed live via
 * `kubectl get resourcequota -n supabase-demo` returning no resources),
 * since that is itself honest state: this module has no quota to compare
 * usage against for that namespace, and says so rather than fabricating
 * one. If a namespace ever carries more than one ResourceQuota object
 * (none do today), the first one returned by the API is used and the rest
 * are ignored -- disclosed here rather than silently summed.
 */
export async function getResourceQuota(
  namespace: string,
): Promise<K8sResult<ResourceQuotaSnapshot | null>> {
  const result = await k8sRequest<ResourceQuotaListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/resourcequotas`,
  );
  if (!result.ok) return result;
  const item = (result.data.items ?? [])[0];
  if (!item) return { ok: true, data: null };
  const hard = item.status?.hard ?? {};
  const used = item.status?.used ?? {};
  return {
    ok: true,
    data: {
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      hardCpuMillicores: quantityToMillicores(hard["limits.cpu"]),
      hardMemoryMiB: quantityToMiB(hard["limits.memory"]),
      hardRequestsCpuMillicores: quantityToMillicores(hard["requests.cpu"]),
      hardRequestsMemoryMiB: quantityToMiB(hard["requests.memory"]),
      hardPods: hard["pods"] !== undefined ? Number(hard["pods"]) : null,
      usedPods: used["pods"] !== undefined ? Number(used["pods"]) : null,
    },
  };
}

export interface RawResourceQuota {
  name: string;
  namespace: string;
  /** Real, exact `spec.hard` quantity strings (e.g. `"2"`, `"4Gi"`) as
   * stored on the object -- unlike `ResourceQuotaSnapshot` above (which
   * lossily parses into plain millicore/MiB numbers for display),
   * lib/plan-state.ts needs the exact original strings so a restore after
   * suspension writes back the precise value that was there before, not a
   * re-derived approximation. */
  hard: Record<string, string>;
}

/**
 * Reads ONE namespace's ResourceQuota object's real `spec.hard` map
 * verbatim (raw quantity strings, no unit conversion) plus its real
 * object name -- the exact two things `patchResourceQuotaHard` below
 * needs to save-before-suspend and restore-on-reactivate. Returns
 * `{ ok: true, data: null }` -- not an error -- when the namespace has no
 * ResourceQuota object, same convention `getResourceQuota` above already
 * uses.
 */
export async function getResourceQuotaRaw(
  namespace: string,
): Promise<K8sResult<RawResourceQuota | null>> {
  const result = await k8sRequest<ResourceQuotaListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/resourcequotas`,
  );
  if (!result.ok) return result;
  const item = (result.data.items ?? [])[0];
  if (!item) return { ok: true, data: null };
  return {
    ok: true,
    data: { name: item.metadata.name, namespace: item.metadata.namespace, hard: item.status?.hard ?? {} },
  };
}

/**
 * Real enforcement primitive for lib/plan-state.ts: patches ONE namespace's
 * already-existing ResourceQuota object's `spec.hard` map via a real RFC
 * 7386 merge patch (same `application/merge-patch+json` convention
 * `patchDeploymentReplicas`/`patchNamespaceAnnotations` above already
 * use). This is the same object `getResourceQuota` reads and the same
 * object `/usage`'s percentage-of-quota figure is computed against --
 * plan-state suspension therefore takes effect through the exact same
 * enforcement primitive (kube-apiserver's own admission-time quota check
 * on every Pod create) that already blocks a namespace from exceeding its
 * normal ceiling, not a separate/parallel mechanism. Requires a
 * ResourceQuota object to already exist in `namespace` (provisioned by
 * k8s/resource-quotas.yaml at tenant onboarding, same precedent
 * lib/quota-enforcement.ts's header comment describes as "fixed at
 * provisioning time") -- fails closed with a real k8s 404 error, never
 * silently creates one, when it does not.
 */
/**
 * Builds the exact ResourceQuota manifest createOrUpdateResourceQuota
 * submits on first create -- pulled out as its own pure function (no
 * network call), same manifest-builder pattern buildSingleDatabaseManifest
 * / buildProjectManifest above already establish. `spec.hard` comes
 * straight from lib/tiers.ts's TIER_RESOURCE_QUOTAS table via
 * resourceQuotaHardFor, so this is the single place a tier's quota values
 * turn into the real k8s object shape.
 */
export function buildResourceQuotaManifest(namespace: string, name: string, tier: ProjectTier) {
  return {
    apiVersion: "v1",
    kind: "ResourceQuota",
    metadata: { name, namespace },
    spec: { hard: resourceQuotaHardFor(tier) },
  };
}

interface ResourceQuotaItem {
  metadata: { name: string; namespace: string };
  spec?: { hard?: Record<string, string> };
}

/** Reads one specific, named ResourceQuota object (unlike getResourceQuota
 * above, which reads "the first ResourceQuota in this namespace, whatever
 * its name"). Returns `{ ok: true, data: null }` -- not an error -- when
 * no ResourceQuota with this exact name exists yet, same 404-is-not-an-
 * error convention getConfigMap already establishes. */
export async function getResourceQuotaByName(
  namespace: string,
  name: string,
): Promise<K8sResult<ResourceQuotaItem | null>> {
  const result = await k8sRequest<ResourceQuotaItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/resourcequotas/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: result.data };
}

/**
 * Real get-then-update-or-create for a namespace's tier-derived
 * ResourceQuota -- the exact same pattern createOrUpdateConfigMap already
 * establishes for ConfigMaps: reads the named ResourceQuota first
 * (getResourceQuotaByName); if it already exists, applies the new tier's
 * `spec.hard` map via patchResourceQuotaHard (a real RFC 7386 merge
 * patch, so live `status.used` counters on the object are untouched by
 * the patch itself); if it doesn't exist yet, POSTs a fresh ResourceQuota
 * manifest (buildResourceQuotaManifest) instead. Called by
 * createProjectWithDatabase at provisioning time and safe to call again
 * later (e.g. a tier upgrade) since it always converges the object to
 * exactly the given tier's table, never accumulates stale keys from a
 * prior tier.
 */
export async function createOrUpdateResourceQuota(
  namespace: string,
  name: string,
  tier: ProjectTier,
): Promise<K8sResult<null>> {
  const existing = await getResourceQuotaByName(namespace, name);
  if (!existing.ok) return existing;

  if (existing.data) {
    return patchResourceQuotaHard(namespace, name, resourceQuotaHardFor(tier));
  }

  const manifest = buildResourceQuotaManifest(namespace, name, tier);
  const result = await k8sRequest<ResourceQuotaItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/resourcequotas`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

export async function patchResourceQuotaHard(
  namespace: string,
  quotaName: string,
  hard: Record<string, string>,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/resourcequotas/${encodeURIComponent(quotaName)}`,
    "PATCH",
    { spec: { hard } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

interface PodMetricsListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    containers?: Array<{ name: string; usage?: { cpu?: string; memory?: string } }>;
  }>;
}

export interface NamespaceResourceUsage {
  namespace: string;
  /** Real, current, live sum of every container's `usage.cpu` across every
   * Pod metrics-server has a fresh reading for in this namespace (the exact
   * same source `kubectl top pods -n <namespace>` reads). */
  cpuUsageMillicores: number;
  memoryUsageMiB: number;
  /** Number of Pods metrics-server actually returned a reading for --
   * usually equals the live Pod count, but can be lower for a few seconds
   * right after a Pod starts, before the first kubelet scrape lands. */
  podsMeasured: number;
  /** `null` when the namespace has no ResourceQuota object at all. */
  quota: ResourceQuotaSnapshot | null;
  /** `cpuUsageMillicores` / `quota.hardCpuMillicores` * 100 -- `null` when
   * there is no quota, or the quota sets no `limits.cpu`. Not clamped to
   * 100: a namespace can (briefly) show live usage above its limits
   * ceiling, since metrics-server's reading and the scheduler's admission
   * check are not perfectly synchronous -- shown as-is rather than
   * silently capped. */
  cpuPercentOfQuota: number | null;
  memoryPercentOfQuota: number | null;
}

/**
 * Combines real live metrics (`metrics.k8s.io/v1beta1` PodMetrics -- the
 * same source `kubectl top pods` reads) with the real ResourceQuota object
 * for one namespace, returning current CPU/memory usage, the quota's hard
 * ceiling, and a plain percentage-of-quota figure. This is real, measured
 * infrastructure consumption -- not billing, not currency; no dollar
 * amount is computed or returned anywhere in this function.
 */
export async function getResourceUsage(
  namespace: string,
): Promise<K8sResult<NamespaceResourceUsage>> {
  const [metricsResult, quotaResult] = await Promise.all([
    k8sRequest<PodMetricsListResponse>(
      `/apis/metrics.k8s.io/v1beta1/namespaces/${encodeURIComponent(namespace)}/pods`,
    ),
    getResourceQuota(namespace),
  ]);
  if (!metricsResult.ok) return metricsResult;
  if (!quotaResult.ok) return quotaResult;

  let cpuUsageMillicores = 0;
  let memoryUsageMiB = 0;
  const pods = metricsResult.data.items ?? [];
  for (const pod of pods) {
    for (const container of pod.containers ?? []) {
      cpuUsageMillicores += quantityToMillicores(container.usage?.cpu) ?? 0;
      memoryUsageMiB += quantityToMiB(container.usage?.memory) ?? 0;
    }
  }

  const quota = quotaResult.data;
  const cpuPercentOfQuota =
    quota?.hardCpuMillicores && quota.hardCpuMillicores > 0
      ? (cpuUsageMillicores / quota.hardCpuMillicores) * 100
      : null;
  const memoryPercentOfQuota =
    quota?.hardMemoryMiB && quota.hardMemoryMiB > 0
      ? (memoryUsageMiB / quota.hardMemoryMiB) * 100
      : null;

  return {
    ok: true,
    data: {
      namespace,
      cpuUsageMillicores,
      memoryUsageMiB,
      podsMeasured: pods.length,
      quota,
      cpuPercentOfQuota,
      memoryPercentOfQuota,
    },
  };
}

export interface NamespacePodRequests {
  namespace: string;
  /** Real sum of every live (non-terminal) Pod's every container's
   * `resources.requests.cpu`, across the namespace -- the same reservation
   * figure the scheduler itself sums when deciding whether a new Pod fits
   * a node, and the same field ResourceQuota's `requests.cpu` accounting
   * reads. Containers with no CPU request set contribute 0, disclosed via
   * `containersWithoutCpuRequest` rather than silently treated as
   * "no reservation" being indistinguishable from "reservation of zero". */
  cpuRequestMillicores: number;
  memoryRequestMiB: number;
  podsCounted: number;
  containersWithoutCpuRequest: number;
  containersWithoutMemoryRequest: number;
}

interface PodSpecResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: {
      containers?: Array<{
        name: string;
        resources?: { requests?: Record<string, string>; limits?: Record<string, string> };
      }>;
    };
    status?: { phase?: string };
  }>;
}

/**
 * Real sum of `spec.containers[].resources.requests` across every live
 * Pod in `namespace` -- the exact same per-Pod spec `getResourceUsage`'s
 * ResourceQuota-based numbers are checked against, but read directly from
 * the real Pod objects (not the aggregate ResourceQuota `status.used`
 * counter, which a namespace may not have at all -- see `getResourceQuota`'s
 * own `null`-is-not-an-error convention) so it works even for a namespace
 * with no ResourceQuota object. `Succeeded`/`Failed` (terminal) Pods are
 * excluded -- their reservations are no longer held against the node --
 * matching kube-scheduler's own live-reservation accounting.
 */
export async function getNamespacePodRequests(
  namespace: string,
): Promise<K8sResult<NamespacePodRequests>> {
  const result = await k8sRequest<PodSpecResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
  );
  if (!result.ok) return result;

  let cpuRequestMillicores = 0;
  let memoryRequestMiB = 0;
  let podsCounted = 0;
  let containersWithoutCpuRequest = 0;
  let containersWithoutMemoryRequest = 0;

  for (const pod of result.data.items ?? []) {
    const phase = pod.status?.phase ?? "Unknown";
    if (phase === "Succeeded" || phase === "Failed") continue;
    podsCounted += 1;
    for (const container of pod.spec?.containers ?? []) {
      const requests = container.resources?.requests ?? {};
      const cpu = quantityToMillicores(requests.cpu);
      const mem = quantityToMiB(requests.memory);
      if (cpu === null) containersWithoutCpuRequest += 1;
      else cpuRequestMillicores += cpu;
      if (mem === null) containersWithoutMemoryRequest += 1;
      else memoryRequestMiB += mem;
    }
  }

  return {
    ok: true,
    data: {
      namespace,
      cpuRequestMillicores,
      memoryRequestMiB,
      podsCounted,
      containersWithoutCpuRequest,
      containersWithoutMemoryRequest,
    },
  };
}

/**
 * Real enforcement primitive for lib/quota-enforcement.ts: scales one
 * `apps/v1` Deployment to an exact replica count via a real RFC 7386
 * merge patch on `spec.replicas` (`application/merge-patch+json`, the
 * same convention `createOrUpdateConfigMap`/`applyTag` already use in
 * this file). Scaling to 0 is a genuine k8s action, not a simulated one:
 * the Deployment's own ReplicaSet controller reacts to it exactly as it
 * would to a `kubectl scale --replicas=0`, terminating live Pods and
 * emitting real `ScalingReplicaSet`/`Killing` Events -- nothing here
 * fabricates those; they come from the cluster's own control loop once
 * this patch lands.
 */
export async function patchDeploymentReplicas(
  namespace: string,
  name: string,
  replicas: number,
): Promise<K8sResult<{ name: string; namespace: string; replicas: number }>> {
  const result = await k8sRequest<{ metadata: { name: string; namespace: string } }>(
    `/apis/apps/v1/namespaces/${encodeURIComponent(namespace)}/deployments/${encodeURIComponent(name)}`,
    "PATCH",
    { spec: { replicas } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: { name, namespace, replicas } };
}

/**
 * Real quarantine primitive for the vulnerability-scan-triggered
 * auto-remediation workflow
 * (app/api/security-scan/auto-remediate/route.ts): scales the named
 * Deployment to 0 replicas (via the same real `patchDeploymentReplicas`
 * merge-patch above -- a genuine k8s action, not simulated) AND stamps a
 * `platform-console.io/quarantined=true` label on the Deployment's own
 * metadata via a second real RFC 7386 merge patch, so the quarantine is
 * durably visible on the object itself (`kubectl get deploy -l
 * platform-console.io/quarantined=true`) independent of this console's own
 * approval-request record, and so a namespace-scoped deny-all
 * NetworkPolicy selecting on that same label blocks any traffic to pods
 * still terminating. Only ever called after a fresh, distinct-approver
 * `deployment.quarantine` approval (lib/approval-workflow.ts) exists --
 * this function itself performs no approval check, same "the guarded
 * route checks, the primitive just acts" split as patchDeploymentReplicas
 * and patchResourceQuotaHard.
 */
export async function quarantineDeployment(
  namespace: string,
  name: string,
): Promise<K8sResult<{ name: string; namespace: string; replicas: 0 }>> {
  const scaled = await patchDeploymentReplicas(namespace, name, 0);
  if (!scaled.ok) return scaled;

  const labelResult = await k8sRequest<unknown>(
    `/apis/apps/v1/namespaces/${encodeURIComponent(namespace)}/deployments/${encodeURIComponent(name)}`,
    "PATCH",
    { metadata: { labels: { "platform-console.io/quarantined": "true" } } },
    "application/merge-patch+json",
  );
  if (!labelResult.ok) return labelResult;

  return { ok: true, data: { name, namespace, replicas: 0 } };
}

/**
 * Real annotation primitive for lib/quota-enforcement.ts: patches
 * `metadata.annotations` on one Namespace object via the same RFC 7386
 * merge-patch convention as `applyTag` above (labels vs. annotations
 * only -- annotations, not labels, since these values are free-form JSON
 * strings/timestamps, not the short indexable key=value pairs Resource
 * Tagging's labels convention is for). Used to record a human-visible,
 * `kubectl describe namespace`-readable trail of quota-enforcement
 * actions directly on the affected namespace, independent of this
 * console's own ConfigMap-backed dedup state.
 */
export async function patchNamespaceAnnotations(
  namespace: string,
  annotations: Record<string, string | null>,
): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}`,
    "PATCH",
    { metadata: { annotations } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

// -------------------------------------------------------------- Feature Flags
//
// Real hyperscaler-PaaS-style Feature Flags primitive (AWS AppConfig /
// LaunchDarkly / GCP Feature Flags equivalent) -- backed by a single real
// k8s ConfigMap (`platform-feature-flags`, `platform-console` namespace),
// no external SaaS dependency, no separate flag-evaluation service. Flag
// values are plain strings in the ConfigMap's `data` map (`"true"`/
// `"false"` for boolean flags, though nothing here enforces that shape --
// arbitrary string flags are equally real). Scoped by k8s/paas-rbac.yaml
// to a single least-privilege Role+RoleBinding in platform-console's own
// namespace only (get/list/create/update on configmaps) -- never
// cluster-wide, no delete verb: this console only ever creates the flags
// ConfigMap once or edits its `data` map in place.

export interface FeatureFlagsConfigMap {
  name: string;
  namespace: string;
  data: Record<string, string>;
}

interface ConfigMapItem {
  metadata: { name: string; namespace: string };
  data?: Record<string, string>;
}

function toFeatureFlagsConfigMap(item: ConfigMapItem): FeatureFlagsConfigMap {
  return { name: item.metadata.name, namespace: item.metadata.namespace, data: item.data ?? {} };
}

/**
 * Reads one real ConfigMap. Returns `{ ok: true, data: null }` -- not an
 * error -- when it doesn't exist yet, so callers can distinguish "not
 * provisioned" from a real API failure, same convention as
 * getBackupsPvc above.
 */
export async function getConfigMap(
  namespace: string,
  name: string,
): Promise<K8sResult<FeatureFlagsConfigMap | null>> {
  const result = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: toFeatureFlagsConfigMap(result.data) };
}

/**
 * Real get-then-update-or-create, same pattern ensureBackupsPvc above
 * already uses for a different resource type: reads the ConfigMap first
 * (`getConfigMap`); if it already exists, applies `data` as a real RFC
 * 7386 JSON merge patch (`Content-Type: application/merge-patch+json`) --
 * merge-patch on a nested object field is recursive, so passing just the
 * one changed key (e.g. `{ "verbose-status": "true" }`) updates that key
 * without touching any other flag already in the map; never a blind
 * full-object PUT that would require re-sending every existing flag or
 * risk clobbering one this call didn't read. If it doesn't exist yet,
 * POSTs a fresh ConfigMap manifest instead.
 */
export async function createOrUpdateConfigMap(
  namespace: string,
  name: string,
  data: Record<string, string>,
): Promise<K8sResult<FeatureFlagsConfigMap>> {
  const existing = await getConfigMap(namespace, name);
  if (!existing.ok) return existing;

  if (existing.data) {
    const result = await k8sRequest<ConfigMapItem>(
      `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(name)}`,
      "PATCH",
      { data },
      "application/merge-patch+json",
    );
    if (!result.ok) return result;
    return { ok: true, data: toFeatureFlagsConfigMap(result.data) };
  }

  const manifest = {
    apiVersion: "v1",
    kind: "ConfigMap",
    metadata: { name, namespace },
    data,
  };
  const result = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toFeatureFlagsConfigMap(result.data) };
}

export interface ConfigMapSummary {
  name: string;
  namespace: string;
  labels: Record<string, string>;
}

interface ConfigMapListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; labels?: Record<string, string> };
  }>;
}

/**
 * Lists real ConfigMaps in one namespace, optionally filtered by a real
 * server-side `?labelSelector=` query parameter -- the same convention
 * `listJobs`/`listCronJobs` already use. Used by lib/tags.ts's Resource
 * Tagging module to find which of platform-console's own singleton
 * ConfigMaps (Feature Flags, Webhooks) carry a given
 * `platform-console.io/tag-<key>` label -- a genuine server-side filter,
 * never a client-side scan of every ConfigMap in the namespace.
 */
export async function listConfigMaps(
  namespace: string,
  labelSelector?: string,
): Promise<K8sResult<ConfigMapSummary[]>> {
  const qs = labelSelector ? `?labelSelector=${encodeURIComponent(labelSelector)}` : "";
  const result = await k8sRequest<ConfigMapListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps${qs}`,
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      labels: item.metadata.labels ?? {},
    })),
  };
}

// ---------------------------------------------------------- Network Topology
//
// Real hyperscaler-VPC-console-style Network Topology primitive (AWS VPC
// console / GCP VPC Network Topology / Azure Virtual Network diagram
// equivalent). Three real, distinct sources, each read live off the k8s
// API -- never a hardcoded CIDR guess or a fabricated matrix:
//
// 1. Pod CIDR: the AUTHORITATIVE source is `Node.spec.podCIDR` -- the
//    real per-node allocation kubeadm's node-ipam controller writes,
//    visible via a new cluster-scoped `nodes` get/list RBAC grant (see
//    k8s/paas-rbac.yaml). This is not the same thing as the
//    `--service-cluster-ip-range`/`podSubnet` flags configured on the
//    kube-apiserver/kubeadm-config ConfigMap in kube-system -- this
//    console deliberately has no RBAC into kube-system (see the Secrets/
//    Logs sections above), so those flags are NOT read here. Corroborated
//    (not replaced) by an OBSERVED range computed from real live Pod IPs
//    across the platform namespaces this console already has `pods`
//    RBAC for (listPods, reused as-is).
// 2. Service CIDR: no RBAC exists (and none was added) to read the
//    `--service-cluster-ip-range` flag or the kubeadm-config ConfigMap
//    (both live in kube-system) -- so the ONLY honest method here is
//    OBSERVED: the smallest CIDR block that contains every real
//    ClusterIP returned by a cluster-wide Services list (already granted
//    -- confirmed live via `kubectl auth can-i list services
//    --all-namespaces`). Labeled as observed, not authoritative, in the
//    returned struct so no caller can mistake it for a config read.
// 3. mTLS boundary: real `security.istio.io/v1` PeerAuthentication
//    objects, cluster-wide (new RBAC, same pattern as `networkpolicies`
//    above) -- namespace-wide mode (no `spec.selector`) is distinguished
//    from a workload-scoped override (`spec.selector` present), since
//    conflating the two would misreport a namespace's actual default
//    mTLS posture.

export interface K8sNodePodCidr {
  name: string;
  podCIDRs: string[];
}

interface PodIpListResponse {
  items?: Array<{ status?: { podIP?: string } }>;
}

/** Real live `status.podIP` for every Pod in one namespace -- the exact
 * same `/api/v1/namespaces/{ns}/pods` endpoint `listPods` above already
 * reads (same per-namespace `pods` RBAC, no new grant), just pulling the
 * one extra field `listPods`'s `K8sPod` shape doesn't carry (it never
 * needed an IP for the Logs page). Used by `lib/network.ts` to compute
 * the OBSERVED Pod CIDR corroboration -- never a hardcoded range. */
export async function listPodIPs(namespace: string): Promise<K8sResult<string[]>> {
  const result = await k8sRequest<PodIpListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
  );
  if (!result.ok) return result;
  const ips: string[] = [];
  for (const item of result.data.items ?? []) {
    if (item.status?.podIP) ips.push(item.status.podIP);
  }
  return { ok: true, data: ips };
}

interface NodeListResponse {
  items?: Array<{
    metadata: { name: string; labels?: Record<string, string> };
    spec?: { podCIDR?: string; podCIDRs?: string[] };
  }>;
}

/** Real, authoritative per-node Pod CIDR allocations (`Node.spec.podCIDR(s)`
 * -- kubeadm's node-ipam controller writes this at node registration
 * time). Requires the new cluster-scoped `nodes` get/list RBAC grant. */
export async function listNodes(): Promise<K8sResult<K8sNodePodCidr[]>> {
  const result = await k8sRequest<NodeListResponse>("/api/v1/nodes");
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      podCIDRs: item.spec?.podCIDRs ?? (item.spec?.podCIDR ? [item.spec.podCIDR] : []),
    })),
  };
}

/** Real, well-known k8s node label every major managed cluster (EKS/GKE/
 * AKS/kubeadm with cloud-controller-manager, and this cluster's own
 * nodes) sets to the node's real cloud/topology region --
 * https://kubernetes.io/docs/reference/labels-annotations-taints/#topologykubernetesioregion.
 * Used both to build a live, honest `ALLOWED_REGIONS`-equivalent
 * (listNodeRegions below -- never a fabricated static list) and as the
 * real `nodeSelector` key `buildProjectManifest`/`buildSingleDatabaseManifest`
 * inject when an org has a pinned region. */
export const REGION_NODE_LABEL = "topology.kubernetes.io/region";

/**
 * Real, live-discovered set of regions actually present among this
 * cluster's nodes -- the Data residency / region pinning module's
 * `ALLOWED_REGIONS` equivalent. Derived from `Node.metadata.labels`
 * (same `/api/v1/nodes` call listNodes already makes) rather than a
 * fabricated static list, so a region is only ever offered/accepted if
 * a real node in this cluster is actually labeled with it -- a region
 * pin that could never be satisfied is never presented as an option.
 * Nodes without the label are skipped (not every cluster/node runs a
 * cloud-controller-manager that sets it); result is sorted for a stable
 * UI/API ordering.
 */
export async function listNodeRegions(): Promise<K8sResult<string[]>> {
  const result = await k8sRequest<NodeListResponse>("/api/v1/nodes");
  if (!result.ok) return result;
  const regions = new Set<string>();
  for (const item of result.data.items ?? []) {
    const region = item.metadata.labels?.[REGION_NODE_LABEL];
    if (region) regions.add(region);
  }
  return { ok: true, data: Array.from(regions).sort() };
}

/** Real cluster-wide Services list (every namespace in one call) --
 * distinct from `listNamespaceServices` above, which is scoped to one
 * namespace. Uses the exact same cluster-wide `services` get/list/watch
 * grant `listTopology`'s per-namespace calls already rely on (confirmed
 * live: `kubectl auth can-i list services --all-namespaces` -> `yes`, no
 * new RBAC needed). Used to derive the OBSERVED Service CIDR below -- never
 * to read a Secret or any other sensitive field -- and, with an explicit
 * `labelSelector`, by lib/tags.ts's listResourcesByTag for a real
 * server-side "browse by tag" filter (a genuine `?labelSelector=` query
 * parameter, never a client-side `.filter()` over every Service on the
 * cluster). */
export async function listAllServices(labelSelector?: string): Promise<K8sResult<K8sService[]>> {
  const qs = labelSelector ? `?labelSelector=${encodeURIComponent(labelSelector)}` : "";
  const result = await k8sRequest<ServiceListResponse>(`/api/v1/services${qs}`);
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((svc) => ({
      name: svc.metadata.name,
      namespace: svc.metadata.namespace,
      clusterIP: svc.spec?.clusterIP ?? null,
      ports: (svc.spec?.ports ?? []).map((p) => ({
        name: p.name,
        port: p.port,
        targetPort: p.targetPort,
        protocol: p.protocol ?? "TCP",
      })),
      labels: svc.metadata.labels ?? {},
      dns: `${svc.metadata.name}.${svc.metadata.namespace}.svc.cluster.local`,
    })),
  };
}

export interface IamPeerAuthentication {
  name: string;
  namespace: string;
  /** `null` when the object sets no `spec.mtls.mode` at all (inherits the
   * mesh-wide/namespace-wide default from elsewhere -- never guessed
   * here). */
  mode: "STRICT" | "PERMISSIVE" | "DISABLE" | null;
  /** True when `spec.selector` is present -- a workload-scoped override,
   * not this namespace's blanket default. */
  workloadScoped: boolean;
}

interface PeerAuthenticationListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: {
      mtls?: { mode?: string };
      selector?: unknown;
    };
  }>;
}

/** Real `security.istio.io/v1` PeerAuthentication objects, cluster-wide.
 * Requires the new `security.istio.io/peerauthentications` get/list/watch
 * RBAC grant (k8s/paas-rbac.yaml). */
export async function listPeerAuthentications(): Promise<K8sResult<IamPeerAuthentication[]>> {
  const result = await k8sRequest<PeerAuthenticationListResponse>(
    "/apis/security.istio.io/v1/peerauthentications",
  );
  if (!result.ok) return result;
  const validModes = new Set(["STRICT", "PERMISSIVE", "DISABLE"]);
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => {
      const rawMode = item.spec?.mtls?.mode;
      return {
        name: item.metadata.name,
        namespace: item.metadata.namespace,
        mode: rawMode && validModes.has(rawMode) ? (rawMode as IamPeerAuthentication["mode"]) : null,
        workloadScoped: item.spec?.selector !== undefined,
      };
    }),
  };
}

// --------------------------------------------------------- Org Custom Domains (cert-manager)

/**
 * Per-org custom-domain TLS: creates a real `cert-manager.io/v1`
 * Certificate custom resource requesting a cert for one org's own
 * hostname (console.customer.com), in the `platform-console` namespace --
 * the same namespace k8s/gateway.yaml's Gateway objects and
 * lib/custom-domains.ts's Gateway/VirtualService pairs already live in.
 *
 * Unlike lib/custom-domains.ts's `generateSelfSignedCertificate` (a
 * same-process `openssl req -x509` self-signed leaf, used for the
 * platform's OWN service-routing custom domains), this feature is scoped
 * to org-level white-label domains and deliberately issues through
 * cert-manager's own controller + whatever ClusterIssuer this cluster
 * already runs, exactly like AWS ACM/GCP-managed-certs do for their own
 * "custom domain" tier -- cert-manager watches the Certificate object this
 * function creates and does the real ACME/CA handshake itself; this
 * function's job ends at "the Certificate CR exists", the same "one real
 * apply, no client-side cert material" division of labor every other
 * typed-apply helper in this file already follows (createSingleDatabase,
 * createNamespace, etc.).
 *
 * DISCLOSED GAP: no `k8s/*.yaml` manifest in this repo defines a
 * ClusterIssuer today (confirmed by a repo-wide grep for
 * "cert-manager"/"ClusterIssuer" turning up nothing outside this custom-
 * domains feature) -- lib/custom-domains.ts's own self-signed path is what
 * this cluster actually runs for TLS today, not cert-manager. This
 * function therefore targets `DEFAULT_CLUSTER_ISSUER_NAME` below, cert-
 * manager's own most common ClusterIssuer name convention -- the real,
 * standard name an operator installing cert-manager + a ClusterIssuer
 * into THIS cluster would reuse, overridable via
 * `CERT_MANAGER_CLUSTER_ISSUER_NAME` if this cluster's issuer is actually
 * named something else. The apply call itself is real (a genuine
 * `cert-manager.io/v1` Certificate POST, immediately readable back via
 * `getCertificateStatus`); it simply has no controller to reconcile it
 * against until cert-manager + that ClusterIssuer are actually installed,
 * the same "not configured" fail-closed shape `k8sRequest` already returns
 * for every other call made off-cluster.
 */
export const DEFAULT_CLUSTER_ISSUER_NAME =
  process.env.CERT_MANAGER_CLUSTER_ISSUER_NAME ?? "letsencrypt-prod";
export const ORG_CERTIFICATE_NAMESPACE = "platform-console";
export const ORG_CERTIFICATE_LABEL = "platform-console.io/org-custom-domain";

function orgCertificateName(orgId: string): string {
  // Deterministic from the org id alone (not the hostname) -- an org
  // re-submitting a different hostname re-uses/updates the SAME
  // Certificate object rather than accumulating an orphaned one per
  // previous attempt, same "one real object per owning entity" discipline
  // lib/authz.ts's ConfigMap-per-namespace convention already follows.
  return `org-custom-domain-${orgId}`.toLowerCase().replace(/[^a-z0-9-]/g, "-").slice(0, 253);
}

export function orgCertificateSecretName(orgId: string): string {
  return `${orgCertificateName(orgId)}-tls`;
}

interface CertificateItem {
  metadata: { name: string; namespace: string };
  spec?: { dnsNames?: string[]; secretName?: string; issuerRef?: { name?: string; kind?: string } };
  status?: {
    conditions?: Array<{ type?: string; status?: string; reason?: string; message?: string }>;
    notAfter?: string;
  };
}

/**
 * Creates (or, on re-submission, replaces) the Certificate CR for one org's
 * custom domain -- a get-then-delete-then-create, since cert-manager
 * treats `spec.dnsNames`/`secretName` as effectively immutable in practice
 * (changing the requested hostname is a new certificate request, not an
 * in-place edit), the same "delete and recreate whole, never edit in
 * place" discipline lib/custom-domains.ts's own Gateway/VirtualService
 * registration comment already documents for this exact reason.
 */
export async function createOrgCertificate(
  orgId: string,
  hostname: string,
): Promise<K8sResult<CertificateItem>> {
  const name = orgCertificateName(orgId);
  const path = `/apis/cert-manager.io/v1/namespaces/${ORG_CERTIFICATE_NAMESPACE}/certificates`;

  const existing = await k8sRequest<CertificateItem>(`${path}/${encodeURIComponent(name)}`);
  if (existing.ok) {
    const del = await k8sRequest<unknown>(`${path}/${encodeURIComponent(name)}`, "DELETE");
    if (!del.ok && !/not found/i.test(del.error)) return del;
  } else if (!/not found/i.test(existing.error)) {
    return existing;
  }

  const manifest = {
    apiVersion: "cert-manager.io/v1",
    kind: "Certificate",
    metadata: {
      name,
      namespace: ORG_CERTIFICATE_NAMESPACE,
      labels: { [ORG_CERTIFICATE_LABEL]: "true" },
      annotations: { "platform-console.io/org-id": orgId, "platform-console.io/hostname": hostname },
    },
    spec: {
      secretName: orgCertificateSecretName(orgId),
      dnsNames: [hostname],
      issuerRef: { name: DEFAULT_CLUSTER_ISSUER_NAME, kind: "ClusterIssuer" },
    },
  };
  return k8sRequest<CertificateItem>(path, "POST", manifest);
}

export type OrgCertificateStatus = "pending" | "issued" | "failed";

export interface OrgCertificateState {
  status: OrgCertificateStatus;
  reason: string | null;
  message: string | null;
}

/**
 * Real, live re-read of one org's Certificate CR `status.conditions`
 * (cert-manager's own controller writes these -- this function never
 * infers status any other way): the `Ready` condition drives everything --
 * `status: "True"` -> `issued`, `status: "False"` with a terminal-looking
 * reason (cert-manager sets `reason: "Failed"` on unrecoverable ACME/CA
 * errors) -> `failed`, anything else (no conditions yet, or `Ready` still
 * `False`/`Unknown` mid-issuance) -> `pending`. A missing Certificate CR
 * (never submitted, or cert-manager/RBAC not yet configured on this
 * cluster) is reported as an honest `K8sResult` failure, never silently
 * coerced into one of the three statuses above.
 */
export async function getCertificateStatus(orgId: string): Promise<K8sResult<OrgCertificateState>> {
  const name = orgCertificateName(orgId);
  const result = await k8sRequest<CertificateItem>(
    `/apis/cert-manager.io/v1/namespaces/${ORG_CERTIFICATE_NAMESPACE}/certificates/${encodeURIComponent(name)}`,
  );
  if (!result.ok) return result;

  const conditions = result.data.status?.conditions ?? [];
  const ready = conditions.find((c) => c.type === "Ready");

  let status: OrgCertificateStatus;
  if (ready?.status === "True") {
    status = "issued";
  } else if (ready?.status === "False" && /fail/i.test(ready.reason ?? "")) {
    status = "failed";
  } else {
    status = "pending";
  }

  return {
    ok: true,
    data: { status, reason: ready?.reason ?? null, message: ready?.message ?? null },
  };
}
