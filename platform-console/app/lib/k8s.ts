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

const SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount";
const REQUEST_TIMEOUT_MS = 5000;

export type K8sResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

interface InClusterConfig {
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

async function k8sRequest<T>(
  path: string,
  method: "GET" | "POST" | "DELETE" = "GET",
  body?: unknown,
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
                "Content-Type": "application/json",
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
}

interface K8sListMeta {
  items?: Array<{
    metadata: { name: string; namespace: string; creationTimestamp: string };
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
  };
}

export async function listProjects(): Promise<K8sResult<SupabaseProject[]>> {
  const result = await k8sRequest<K8sListMeta>(
    "/apis/core.supabase.io/v1alpha1/projects",
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

export interface CreateProjectInput {
  name: string;
  namespace: string;
  databaseRefName: string;
  hostname: string;
  protocol: "http" | "https";
  /** PVC size for the paired SingleDatabase, e.g. "1Gi". Defaults to "1Gi". */
  dbStorageSize: string;
}

interface SingleDatabaseItem {
  metadata: { name: string; namespace: string };
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
}): Promise<K8sResult<SingleDatabaseItem>> {
  const manifest = {
    apiVersion: "core.supabase.io/v1alpha1",
    kind: "SingleDatabase",
    metadata: { name: input.name, namespace: input.namespace },
    spec: {
      storage: { accessModes: ["ReadWriteOnce"], size: input.storageSize },
    },
  };
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
 */
export async function createProject(
  input: Omit<CreateProjectInput, "dbStorageSize">,
): Promise<K8sResult<SupabaseProject>> {
  const manifest = {
    apiVersion: "core.supabase.io/v1alpha1",
    kind: "Project",
    metadata: { name: input.name, namespace: input.namespace },
    spec: {
      databaseRef: { kind: "SingleDatabase", name: input.databaseRefName },
      http: { hostname: input.hostname, protocol: input.protocol },
    },
  };
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
  });
  if (!dbResult.ok) return dbResult;

  const projectResult = await createProject(input);
  return projectResult;
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

// -------------------------------------------------------------- Namespaces

interface NamespaceListResponse {
  items?: Array<{ metadata: { name: string } }>;
}

export async function listNamespaces(): Promise<K8sResult<string[]>> {
  const result = await k8sRequest<NamespaceListResponse>("/api/v1/namespaces");
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map((ns) => ns.metadata.name) };
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
}

interface NetworkPolicyListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string };
    spec?: { policyTypes?: string[] };
  }>;
}

export async function listNetworkPolicies(): Promise<K8sResult<IamNetworkPolicy[]>> {
  const result = await k8sRequest<NetworkPolicyListResponse>(
    "/apis/networking.k8s.io/v1/networkpolicies",
  );
  if (!result.ok) return result;
  return {
    ok: true,
    data: (result.data.items ?? []).map((item) => ({
      name: item.metadata.name,
      namespace: item.metadata.namespace,
      policyTypes: item.spec?.policyTypes ?? [],
    })),
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

export async function listPods(namespace: string): Promise<K8sResult<K8sPod[]>> {
  const result = await k8sRequest<PodListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
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
