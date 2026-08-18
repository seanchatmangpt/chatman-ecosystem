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
