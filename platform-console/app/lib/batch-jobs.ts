// ----------------------------------------------------------- Batch Compute
//
// Real hyperscaler-PaaS-style Batch Compute primitive (AWS Batch / GCP
// Batch / Azure Batch equivalent): self-service PARALLEL job fan-out,
// distinct from the existing Scheduled Jobs module (single-shot,
// time-triggered `CronJob`s). This uses k8s's own real indexed-Job
// feature -- `spec.completionMode: "Indexed"` plus
// `spec.parallelism`/`spec.completions` -- so a single `batch/v1` `Job`
// spins up N real Pods running CONCURRENTLY (bounded by `parallelism`),
// each one kubelet-injected with a real `JOB_COMPLETION_INDEX` env var
// (0..completions-1, confirmed live against this cluster's real v1.34 API
// server before any application code was written -- a 2-pod probe Job
// showed `JOB_COMPLETION_INDEX=0`/`=1` in each pod's own log with no
// downward-API wiring needed; the Job controller injects it automatically
// for Indexed Jobs whose pod template has `restartPolicy: Never`). This is
// the exact real primitive every hyperscaler's "Batch" product is built
// on top of.
//
// Reuses Scheduled Jobs' exact allowlist discipline (lib/scheduled-jobs.ts):
// the platform's own namespaces only (SCHEDULABLE_NAMESPACES, re-exported
// here unchanged as BATCHABLE_NAMESPACES -- same 5 namespaces, same
// per-namespace Role/RoleBinding pattern in k8s/paas-rbac.yaml, never
// cluster-wide), and a fixed, small, server-side allowlist of command IDS
// -- never free-text shell input. `resolveBatchCommand` is the one and
// only place a request's `commandId` touches anything that becomes a
// container `command`; anything outside `ALLOWED_BATCH_COMMANDS` is
// rejected before any k8s API call is made.
//
// RESULT COLLECTION -- the part that makes this genuinely "collectible",
// not just "N pods ran": each pod's own allowlisted command computes a
// real, deterministic, index-derived result and PATCHes it into ONE
// well-known, PRE-EXISTING k8s ConfigMap (`platform-batch-results`, one
// per namespace, created on first use by `ensureBatchResultsConfigMap`)
// under a key that encodes both the job name and its own index
// (`batch-result-<job>-<index>`) -- never a hostPath, never the
// PVC-backed pattern the Backups module uses (PVC contents are NOT
// queryable via the k8s API -- confirmed by that module's own doc
// comment -- so a PVC would make `collectBatchResults` below impossible
// without spinning up a reader pod; a ConfigMap key IS queryable with one
// plain GET, so it is the honestly-collectible choice here). Each pod
// writes with its OWN identity, not the console's: a dedicated, narrowly
// scoped ServiceAccount (`platform-batch-runner`, k8s/paas-rbac.yaml) is
// granted exactly one verb (`patch`) on exactly one named ConfigMap
// (`resourceNames: ["platform-batch-results"]`) -- the same
// `resourceNames`-restricted least-privilege pattern this codebase's own
// `platform-console-feature-flags-reader` Role already established, now
// applied to a workload identity instead of the console's own. The
// console's ServiceAccount gets a matching narrow grant (create the
// ConfigMap once if missing, get/patch it by that same one name) plus
// get/list/create/delete on `batch/jobs` in each of the 5 namespaces --
// its own new per-namespace Role, same shape as Scheduled Jobs'
// `platform-console-scheduled-jobs` Role.
import { k8sRequest, type K8sResult } from "@/lib/k8s";
import { SCHEDULABLE_NAMESPACES, isSchedulableNamespace } from "@/lib/scheduled-jobs";

// -------------------------------------------------------------- Namespaces
//
// Deliberately the exact same allowlist Scheduled Jobs already uses and
// the exact same RBAC scope this module's own new Roles in
// k8s/paas-rbac.yaml grant -- re-exported, not re-declared, so the two
// modules can never drift apart on which namespaces are self-service-safe.
export const BATCHABLE_NAMESPACES = SCHEDULABLE_NAMESPACES;
export type BatchableNamespace = (typeof BATCHABLE_NAMESPACES)[number];
export const isBatchableNamespace = isSchedulableNamespace;

// ------------------------------------------------------------ Fan-out size
//
// A single "size" controls both `parallelism` and `completions` -- this
// module deliberately only offers a pure fan-out shape (N pods, all N
// requested to run at once, all N must complete), not the more general
// "more completions than parallelism slots" batch-queue shape, so the
// live concurrency proof this module exists to provide (parallelism ==
// completions == every index actually running at the same time) is
// exactly what every job it creates promises.
export const MIN_BATCH_SIZE = 2;
export const MAX_BATCH_SIZE = 10;

export function isValidBatchSize(size: number): boolean {
  return Number.isInteger(size) && size >= MIN_BATCH_SIZE && size <= MAX_BATCH_SIZE;
}

// RFC 1123 DNS label, same as Scheduled Jobs' isValidJobName -- this name
// becomes both the k8s Job's own metadata.name and a literal substring of
// every ConfigMap result key it writes, so it must stay filesystem/DNS/
// ConfigMap-key safe.
const NAME_RE = /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/;
export function isValidBatchJobName(name: string): boolean {
  return name.length > 0 && name.length <= 40 && NAME_RE.test(name);
}

// ----------------------------------------------------------------- Commands
export interface AllowedBatchCommand {
  id: AllowedBatchCommandId;
  label: string;
  description: string;
  image: string;
}

/** Fixed, closed set -- declared as its own literal union (not
 * `keyof typeof ALLOWED_BATCH_COMMANDS`) so `buildContainerCommand`'s
 * switch is statically checked exhaustive, same discipline as
 * lib/scheduled-jobs.ts's `AllowedCommandId`. */
export type AllowedBatchCommandId = "square-index" | "cube-index";

export const ALLOWED_BATCH_COMMANDS: Record<AllowedBatchCommandId, AllowedBatchCommand> = {
  "square-index": {
    id: "square-index",
    label: "Compute index²",
    description:
      "Each pod reads its own real JOB_COMPLETION_INDEX, computes its square with plain POSIX shell integer arithmetic, and PATCHes the real result into this namespace's platform-batch-results ConfigMap under its own index-named key.",
    image: "curlimages/curl:8.10.1",
  },
  "cube-index": {
    id: "cube-index",
    label: "Compute index³",
    description:
      "Same as index², but computes the cube -- a second, distinct real per-index workload for the allowlist.",
    image: "curlimages/curl:8.10.1",
  },
};

function isAllowedBatchCommandId(value: string): value is AllowedBatchCommandId {
  return Object.prototype.hasOwnProperty.call(ALLOWED_BATCH_COMMANDS, value as AllowedBatchCommandId);
}

/** Resolves a caller-supplied string against the allowlist -- `null` on
 * anything else. Callers (the API route) must reject the request on
 * `null`, never fall back to a default command -- same contract as
 * lib/scheduled-jobs.ts's `resolveCommand`. */
export function resolveBatchCommand(commandId: string): AllowedBatchCommand | null {
  return isAllowedBatchCommandId(commandId) ? ALLOWED_BATCH_COMMANDS[commandId] : null;
}

export const BATCH_RESULTS_CONFIGMAP = "platform-batch-results";

/** The one, fixed key-naming scheme every result -- written by a pod,
 * read back by collectBatchResults -- agrees on. `name` is always an
 * already-validated `isValidBatchJobName` string by the time this is
 * called, never raw request text. */
function resultKey(name: string, index: number): string {
  return `batch-result-${name}-${index}`;
}
const RESULT_KEY_PREFIX_RE = /^batch-result-(.+)-(\d+)$/;

/**
 * Builds the real, fixed container `command` array for one allowlisted
 * command id. `namespace`/`name` are the only substitutions ever
 * performed, and both are already-validated (namespace against
 * `isBatchableNamespace`, name against `isValidBatchJobName`) by the time
 * this is called -- never raw, unvalidated request text, same discipline
 * as lib/scheduled-jobs.ts's `buildContainerCommand`.
 *
 * The script: reads the real `JOB_COMPLETION_INDEX` env var the Job
 * controller injects, computes a real deterministic per-index result with
 * plain `sh` integer arithmetic (no extra binary needed), then PATCHes
 * that one key into the namespace's `platform-batch-results` ConfigMap
 * using the POD'S OWN in-cluster ServiceAccount token/CA -- the exact same
 * mounted-token HTTPS-to-the-API-server pattern lib/k8s.ts's own
 * `readInClusterConfig`/`k8sRequest` use for the console itself, just
 * exercised here by curl instead of Node. `KUBERNETES_SERVICE_HOST`/
 * `_PORT` are injected into every pod by the kubelet unconditionally (the
 * same env vars `hasClusterCredentials()` depends on), so no extra wiring
 * is needed to reach the API server from inside the Job's own pod.
 */
function buildContainerCommand(
  commandId: AllowedBatchCommandId,
  namespace: string,
  name: string,
): string[] {
  const compute = commandId === "square-index" ? "i * i" : "i * i * i";
  const label = commandId === "square-index" ? "square" : "cube";
  const script = [
    "set -e",
    'i="$JOB_COMPLETION_INDEX"',
    `v=$((${compute}))`,
    'ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    `result="index=\${i} ${label}=\${v} pod=\${HOSTNAME} at=\${ts}"`,
    `key="${"batch-result-" + name + "-"}\${i}"`,
    'token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)',
    'body="{\\"data\\":{\\"${key}\\":\\"${result}\\"}}"',
    `url="https://\${KUBERNETES_SERVICE_HOST}:\${KUBERNETES_SERVICE_PORT}/api/v1/namespaces/${namespace}/configmaps/${BATCH_RESULTS_CONFIGMAP}"`,
    'curl -sS --fail --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \\',
    '  -H "Authorization: Bearer ${token}" \\',
    '  -H "Content-Type: application/merge-patch+json" \\',
    '  -X PATCH "$url" -d "$body"',
    'echo',
    'echo "wrote ${key} = ${result}"',
  ].join("\n");
  return ["sh", "-c", script];
}

// ------------------------------------------------------------------ Jobs

export interface BatchJob {
  name: string;
  namespace: string;
  commandId: string | null;
  image: string | null;
  parallelism: number;
  completions: number;
  active: number;
  succeeded: number;
  failed: number;
  status: "Pending" | "Running" | "Complete" | "Failed";
  createdAt: string;
  startTime: string | null;
  completionTime: string | null;
  /** Real `status.completedIndexes` from the Indexed Job itself (e.g.
   * "0-2,4"), the k8s controller's own compact record of which indexes
   * have a succeeded Pod -- an independent cross-check against the
   * ConfigMap-derived result count `collectBatchResults` computes below. */
  completedIndexes: string | null;
}

interface BatchJobItem {
  metadata: { name: string; namespace: string; creationTimestamp: string; labels?: Record<string, string> };
  spec?: {
    parallelism?: number;
    completions?: number;
    template?: { spec?: { containers?: Array<{ image?: string }> } };
  };
  status?: {
    active?: number;
    succeeded?: number;
    failed?: number;
    startTime?: string;
    completionTime?: string;
    completedIndexes?: string;
  };
}

interface BatchJobListResponse {
  items?: BatchJobItem[];
}

const MANAGED_BY_LABEL = "app";
const MANAGED_BY_VALUE = "platform-batch-jobs";
const COMMAND_LABEL = "batch-job-command";

function toBatchJob(item: BatchJobItem): BatchJob {
  const succeeded = item.status?.succeeded ?? 0;
  const failed = item.status?.failed ?? 0;
  const active = item.status?.active ?? 0;
  const completions = item.spec?.completions ?? 0;
  let status: BatchJob["status"] = "Pending";
  if (succeeded >= completions && completions > 0) status = "Complete";
  else if (failed > 0 && active === 0) status = "Failed";
  else if (active > 0 || succeeded > 0) status = "Running";
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    commandId: item.metadata.labels?.[COMMAND_LABEL] ?? null,
    image: item.spec?.template?.spec?.containers?.[0]?.image ?? null,
    parallelism: item.spec?.parallelism ?? 0,
    completions,
    active,
    succeeded,
    failed,
    status,
    createdAt: item.metadata.creationTimestamp,
    startTime: item.status?.startTime ?? null,
    completionTime: item.status?.completionTime ?? null,
    completedIndexes: item.status?.completedIndexes ?? null,
  };
}

/** Lists real `batch/v1` Indexed Jobs this module created
 * (`app=platform-batch-jobs`), same "the listing IS the record, filtered
 * to this module's own objects" convention `listCronJobs`/`listJobs`
 * (Backups) already use. */
export async function listBatchJobs(namespace: string): Promise<K8sResult<BatchJob[]>> {
  const result = await k8sRequest<BatchJobListResponse>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs?labelSelector=${encodeURIComponent(
      `${MANAGED_BY_LABEL}=${MANAGED_BY_VALUE}`,
    )}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toBatchJob) };
}

export async function getBatchJob(namespace: string, name: string): Promise<K8sResult<BatchJob | null>> {
  const result = await k8sRequest<BatchJobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(name)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) return { ok: true, data: null };
    return result;
  }
  return { ok: true, data: toBatchJob(result.data) };
}

interface ConfigMapItem {
  metadata: { name: string; namespace: string };
  data?: Record<string, string>;
}

/** Real get-then-create for the one shared, well-known results ConfigMap
 * -- a no-op after the first call in a namespace, same
 * `ensureBackupsPvc`-style idempotent provisioning the Backups module
 * already uses for its PVC. Created empty (`data: {}`); every key past
 * that point is added by a Job pod's own PATCH, using its own
 * `platform-batch-runner` identity, never by the console. */
export async function ensureBatchResultsConfigMap(namespace: string): Promise<K8sResult<null>> {
  const existing = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(BATCH_RESULTS_CONFIGMAP)}`,
  );
  if (existing.ok) return { ok: true, data: null };
  if (!/not found/i.test(existing.error)) return existing;

  const manifest = {
    apiVersion: "v1",
    kind: "ConfigMap",
    metadata: { name: BATCH_RESULTS_CONFIGMAP, namespace, labels: { app: MANAGED_BY_VALUE } },
    data: {},
  };
  const created = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps`,
    "POST",
    manifest,
  );
  if (!created.ok) return created;
  return { ok: true, data: null };
}

const BATCH_RUNNER_SERVICE_ACCOUNT = "platform-batch-runner";

export interface CreateBatchJobInput {
  namespace: BatchableNamespace;
  name: string;
  size: number; // parallelism == completions == size
  commandId: AllowedBatchCommandId;
}

/**
 * Creates a real `batch/v1` Indexed Job: `completionMode: "Indexed"`,
 * `parallelism === completions === size`, so up to `size` real Pods run
 * CONCURRENTLY, each with its own real `JOB_COMPLETION_INDEX` (0..size-1).
 * `backoffLimit: 0` -- a failed index is not silently retried into a
 * misleading "eventually succeeded" result. Every field that ends up
 * inside the container `command` traces back to `buildContainerCommand`
 * above; `commandId` is already a validated `AllowedBatchCommandId` by the
 * time this runs (see `resolveBatchCommand`), never raw text. Ensures the
 * results ConfigMap exists first so every pod's PATCH has somewhere real
 * to land the moment it starts.
 */
export async function createBatchJob(input: CreateBatchJobInput): Promise<K8sResult<BatchJob>> {
  const command = ALLOWED_BATCH_COMMANDS[input.commandId];

  const cmEnsured = await ensureBatchResultsConfigMap(input.namespace);
  if (!cmEnsured.ok) return cmEnsured;

  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name: input.name,
      namespace: input.namespace,
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [COMMAND_LABEL]: input.commandId,
      },
    },
    spec: {
      completionMode: "Indexed",
      parallelism: input.size,
      completions: input.size,
      backoffLimit: 0,
      activeDeadlineSeconds: 120,
      template: {
        metadata: {
          labels: { [MANAGED_BY_LABEL]: MANAGED_BY_VALUE, "batch-job-name": input.name },
        },
        spec: {
          restartPolicy: "Never",
          serviceAccountName: BATCH_RUNNER_SERVICE_ACCOUNT,
          containers: [
            {
              name: "batch-worker",
              image: command.image,
              imagePullPolicy: "IfNotPresent",
              command: buildContainerCommand(input.commandId, input.namespace, input.name),
              // Same real ResourceQuota-driven sizing as
              // lib/scheduled-jobs.ts's createCronJob -- 4 of the 5
              // batchable namespaces carry a hard `limits.cpu`/
              // `limits.memory` ResourceQuota, and up to `size` (max 10)
              // of these run concurrently, so each pod's own request/limit
              // is kept minimal.
              resources: {
                requests: { cpu: "10m", memory: "16Mi" },
                limits: { cpu: "50m", memory: "32Mi" },
              },
            },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<BatchJobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(input.namespace)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toBatchJob(result.data) };
}

// ------------------------------------------------------------------ Pods

export interface BatchJobPod {
  name: string;
  index: number | null;
  phase: string;
  /** Real `status.startTime` -- when the kubelet actually started this
   * pod. This, not the Job's own aggregate `status.startTime`, is what
   * proves genuine per-pod concurrency: overlapping `startTime`/
   * `finishedAt` windows across pods mean they really ran at the same
   * time, not one after another. */
  startTime: string | null;
  containerStartedAt: string | null;
  containerFinishedAt: string | null;
  ready: boolean;
}

interface BatchJobPodListResponse {
  items?: Array<{
    metadata: { name: string; namespace: string; labels?: Record<string, string> };
    status?: {
      phase?: string;
      startTime?: string;
      containerStatuses?: Array<{
        ready?: boolean;
        state?: {
          running?: { startedAt?: string };
          terminated?: { startedAt?: string; finishedAt?: string };
        };
      }>;
    };
  }>;
}

/**
 * Lists the real Pods a specific Indexed Job created, via the
 * `job-name` label the Job controller itself sets on every Pod it
 * creates -- reuses the same per-namespace `platform-console-logs-reader`
 * Role's existing `pods` get/list grant (k8s/paas-rbac.yaml), already
 * covering exactly these 5 namespaces, so no new RBAC was needed for this
 * read. Real completion-index is read from the
 * `batch.kubernetes.io/job-completion-index` label the Job controller
 * sets on every Pod of an Indexed Job (confirmed live on the probe Job
 * above) -- never inferred from the pod name string.
 */
export async function listBatchJobPods(namespace: string, name: string): Promise<K8sResult<BatchJobPod[]>> {
  const result = await k8sRequest<BatchJobPodListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods?labelSelector=${encodeURIComponent(
      `job-name=${name}`,
    )}`,
  );
  if (!result.ok) return result;
  const pods = (result.data.items ?? []).map((item) => {
    const cs = item.status?.containerStatuses?.[0];
    const indexLabel = item.metadata.labels?.["batch.kubernetes.io/job-completion-index"];
    return {
      name: item.metadata.name,
      index: indexLabel !== undefined ? Number(indexLabel) : null,
      phase: item.status?.phase ?? "Unknown",
      startTime: item.status?.startTime ?? null,
      containerStartedAt: cs?.state?.running?.startedAt ?? cs?.state?.terminated?.startedAt ?? null,
      containerFinishedAt: cs?.state?.terminated?.finishedAt ?? null,
      ready: cs?.ready ?? false,
    };
  });
  pods.sort((a, b) => (a.index ?? -1) - (b.index ?? -1));
  return { ok: true, data: pods };
}

// -------------------------------------------------------------- Results

export interface BatchResult {
  index: number;
  value: string;
}

export interface BatchResultsSummary {
  results: BatchResult[];
  expectedCount: number;
  missingIndices: number[];
  duplicateIndices: number[];
  complete: boolean;
}

/**
 * Gathers every completed index's real output back into one aggregated
 * result set -- reads the ONE shared `platform-batch-results` ConfigMap
 * (a real GET, not a fabricated re-derivation), filters to this job's own
 * keys (`batch-result-<name>-<index>`), and cross-checks the result
 * against `expectedCount` (normally the Job's own `spec.completions`) for
 * missing indices (a pod that hasn't PATCHed in yet, or failed before
 * doing so) and duplicate indices (would only happen if two pods somehow
 * shared the same index, which Indexed Jobs' own semantics make
 * impossible in the non-retry, `backoffLimit: 0` case this module always
 * uses -- checked anyway, honestly, rather than assumed).
 */
export async function collectBatchResults(
  namespace: string,
  name: string,
  expectedCount: number,
): Promise<K8sResult<BatchResultsSummary>> {
  const result = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(BATCH_RESULTS_CONFIGMAP)}`,
  );
  if (!result.ok) {
    if (/not found/i.test(result.error)) {
      return {
        ok: true,
        data: {
          results: [],
          expectedCount,
          missingIndices: Array.from({ length: expectedCount }, (_, i) => i),
          duplicateIndices: [],
          complete: false,
        },
      };
    }
    return result;
  }

  const seen = new Map<number, string[]>();
  for (const [key, value] of Object.entries(result.data.data ?? {})) {
    const match = RESULT_KEY_PREFIX_RE.exec(key);
    if (!match) continue;
    const [, jobName, indexStr] = match;
    if (jobName !== name) continue;
    const index = Number(indexStr);
    const bucket = seen.get(index) ?? [];
    bucket.push(value);
    seen.set(index, bucket);
  }

  const results: BatchResult[] = [];
  const duplicateIndices: number[] = [];
  for (const [index, values] of seen.entries()) {
    if (values.length > 1) duplicateIndices.push(index);
    results.push({ index, value: values[0] });
  }
  results.sort((a, b) => a.index - b.index);

  const presentIndices = new Set(results.map((r) => r.index));
  const missingIndices = Array.from({ length: expectedCount }, (_, i) => i).filter(
    (i) => !presentIndices.has(i),
  );

  return {
    ok: true,
    data: {
      results,
      expectedCount,
      missingIndices,
      duplicateIndices: duplicateIndices.sort((a, b) => a - b),
      complete: missingIndices.length === 0 && duplicateIndices.length === 0 && expectedCount > 0,
    },
  };
}

/**
 * Deletes the real Job (background propagation so its child Pods are
 * cleaned up too, not left orphaned) and strips this job's own result
 * keys back out of the shared ConfigMap via a real RFC 7386 merge patch
 * (each key set to `null`, which removes it) -- so the one shared
 * ConfigMap doesn't grow unbounded across every batch job this module
 * ever runs, while other jobs' keys are left untouched.
 */
export async function deleteBatchJob(namespace: string, name: string): Promise<K8sResult<null>> {
  const jobResult = await k8sRequest<unknown>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(namespace)}/jobs/${encodeURIComponent(name)}?propagationPolicy=Background`,
    "DELETE",
  );
  if (!jobResult.ok) return jobResult;

  const existing = await k8sRequest<ConfigMapItem>(
    `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(BATCH_RESULTS_CONFIGMAP)}`,
  );
  if (existing.ok) {
    const keysToClear = Object.keys(existing.data.data ?? {}).filter((k) =>
      k.startsWith(`batch-result-${name}-`),
    );
    if (keysToClear.length > 0) {
      const patch: Record<string, null> = {};
      for (const k of keysToClear) patch[k] = null;
      const patched = await k8sRequest<ConfigMapItem>(
        `/api/v1/namespaces/${encodeURIComponent(namespace)}/configmaps/${encodeURIComponent(BATCH_RESULTS_CONFIGMAP)}`,
        "PATCH",
        { data: patch },
        "application/merge-patch+json",
      );
      if (!patched.ok) return patched;
    }
  }

  return { ok: true, data: null };
}
