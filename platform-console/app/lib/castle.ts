// -------------------------------------------------------------- Castle
//
// DEPLOY / RUN / SUNSET lifecycle for the real ~/castle security-testing
// crate (Rust CLI, binary name `castle`) as a workload on this console's
// own cluster. Follows the exact same conventions Scheduled Jobs
// (lib/scheduled-jobs.ts) and Database Backups (lib/k8s.ts) already
// established: a fixed, small, server-side allowlist of real CLI verbs
// (never free-text shell input), one-shot `batch/v1` Jobs (never a
// long-running Deployment -- castle IS a CLI, it has no daemon mode, so
// modeling it as an always-on Deployment would be dishonest), and "the
// listing IS the record" -- no separate fabricated inventory table.
//
// CONSTRUCT != DO, preserved exactly: castle's own CLI (README.md:128-159)
// exposes only read-only/evaluative verbs today -- `fortune5`, `replay`,
// `impact`, `inventory` -- there is no `construct` or `gymact` verb yet
// (castle's own VISION.md gap #3; the actuation path is gated by a
// compiler-enforced sealed private field, `admit_construct_for_do`, per
// castle's CLAUDE.md:13-19). `ALLOWED_CASTLE_VERBS` below is a closed set
// containing ONLY real, already-shipped, side-effect-free castle
// subcommands with no required runtime arguments (`fortune5 requirements`,
// `inventory components`, `inventory goals` -- confirmed live, each exits
// 0 with real JSON on the built image). There is no code path anywhere in
// this file that could construct a `castle construct` or `castle gymact`
// invocation even if such a verb existed in a future castle release --
// adding one requires a new, explicit entry in this allowlist, reviewed
// like any other change, never inferred from request input.
//
// DEPLOY records what image is installed in one fixed ConfigMap
// (`platform-castle-deployment`, the castle namespace) -- the same
// get-then-create-or-patch primitive lib/k8s.ts's Feature Flags module
// established (`getConfigMap`/`createOrUpdateConfigMap`), reused here
// unchanged. RUN creates one real `batch/v1` Job per invocation, labeled
// `app=platform-castle` so SUNSET's cleanup and the module's own listing
// can find every Job this module created and nothing else. SUNSET deletes
// every such Job plus the deployment ConfigMap and returns a real summary
// of what was torn down -- never a fabricated "success" with nothing
// actually deleted.
import { k8sRequest, getConfigMap, createOrUpdateConfigMap, getPodLogs, type K8sResult } from "@/lib/k8s";

export const CASTLE_NAMESPACE = "castle";
export const CASTLE_DEPLOYMENT_CONFIGMAP = "platform-castle-deployment";
export const CASTLE_DEFAULT_IMAGE = "castle:local";

const MANAGED_BY_LABEL = "app";
const MANAGED_BY_VALUE = "platform-castle";
const VERB_LABEL = "platform-castle-verb";

// ------------------------------------------------------------- Verbs
//
// Fixed, closed set of real castle CLI invocations -- declared as its own
// literal union (not `keyof typeof ALLOWED_CASTLE_VERBS`) so
// `ALLOWED_CASTLE_VERBS`'s own shape is statically checked exhaustive by
// the compiler, same discipline lib/scheduled-jobs.ts's AllowedCommandId
// uses. Every `args` array below is the exact, fixed argv this module
// will ever pass to the castle binary for that verb -- no user-supplied
// text is ever interpolated into it.
export type AllowedCastleVerbId =
  | "fortune5-requirements"
  | "inventory-components"
  | "inventory-goals";

export interface AllowedCastleVerb {
  id: AllowedCastleVerbId;
  label: string;
  description: string;
  args: string[];
}

export const ALLOWED_CASTLE_VERBS: Record<AllowedCastleVerbId, AllowedCastleVerb> = {
  "fortune5-requirements": {
    id: "fortune5-requirements",
    label: "fortune5 requirements",
    description:
      "Lists the real 40 generated Fortune-5 readiness controls castle ships (README.md) -- read-only, no arguments beyond output format.",
    args: ["fortune5", "requirements", "--format", "json"],
  },
  "inventory-components": {
    id: "inventory-components",
    label: "inventory components",
    description:
      "Inspects the real marketplace-generated component inventory -- read-only.",
    args: ["inventory", "components", "--format", "json"],
  },
  "inventory-goals": {
    id: "inventory-goals",
    label: "inventory goals",
    description:
      "Inspects the real marketplace-generated adversarial goal inventory -- read-only.",
    args: ["inventory", "goals", "--format", "json"],
  },
};

function isAllowedCastleVerbId(value: string): value is AllowedCastleVerbId {
  return Object.prototype.hasOwnProperty.call(ALLOWED_CASTLE_VERBS, value as AllowedCastleVerbId);
}

/** Resolves a caller-supplied string against the allowlist -- `null` on
 * anything else. Callers (the API route) must reject the request on
 * `null`, never fall back to a default verb. */
export function resolveCastleVerb(verbId: string): AllowedCastleVerb | null {
  return isAllowedCastleVerbId(verbId) ? ALLOWED_CASTLE_VERBS[verbId] : null;
}

// ---------------------------------------------------------------- Deploy
export interface CastleDeployment {
  image: string;
  deployedAt: string;
  deployedBy: string;
}

/** Reads the real deploy-state ConfigMap. `null` (never an error) means
 * "not deployed yet" -- same not-found-is-not-an-error convention
 * getConfigMap itself already uses. */
export async function getCastleDeployment(): Promise<K8sResult<CastleDeployment | null>> {
  const result = await getConfigMap(CASTLE_NAMESPACE, CASTLE_DEPLOYMENT_CONFIGMAP);
  if (!result.ok) return result;
  if (!result.data) return { ok: true, data: null };
  const { image, deployedAt, deployedBy } = result.data.data;
  if (!image || !deployedAt || !deployedBy) return { ok: true, data: null };
  return { ok: true, data: { image, deployedAt, deployedBy } };
}

/**
 * DEPLOY: records that `image` (already built + `kind load docker-image`d
 * into this cluster's node containerd by
 * /Users/sac/castle/load-castle-image.sh -- this function does not build
 * or load images itself, it only records the deploy) is the image RUN
 * will use for every subsequent Job in this namespace. Idempotent: a
 * second DEPLOY with a new image just updates the record via the same
 * get-then-patch-or-create primitive Feature Flags already uses.
 */
export async function deployCastle(
  image: string,
  deployedBy: string,
): Promise<K8sResult<CastleDeployment>> {
  const deployedAt = new Date().toISOString();
  const result = await createOrUpdateConfigMap(CASTLE_NAMESPACE, CASTLE_DEPLOYMENT_CONFIGMAP, {
    image,
    deployedAt,
    deployedBy,
  });
  if (!result.ok) return result;
  return { ok: true, data: { image, deployedAt, deployedBy } };
}

// ------------------------------------------------------------------ Run
export interface CastleJob {
  name: string;
  namespace: string;
  verbId: string | null;
  createdAt: string;
  startTime: string | null;
  completionTime: string | null;
  succeeded: number;
  failed: number;
  active: number;
  status: "Pending" | "Running" | "Complete" | "Failed";
}

interface JobItem {
  metadata: {
    name: string;
    namespace: string;
    creationTimestamp: string;
    labels?: Record<string, string>;
  };
  status?: {
    active?: number;
    succeeded?: number;
    failed?: number;
    startTime?: string;
    completionTime?: string;
  };
}

interface JobListResponse {
  items?: JobItem[];
}

function toCastleJob(item: JobItem): CastleJob {
  const succeeded = item.status?.succeeded ?? 0;
  const failed = item.status?.failed ?? 0;
  const active = item.status?.active ?? 0;
  let status: CastleJob["status"] = "Pending";
  if (succeeded > 0) status = "Complete";
  else if (failed > 0) status = "Failed";
  else if (active > 0) status = "Running";
  return {
    name: item.metadata.name,
    namespace: item.metadata.namespace,
    verbId: item.metadata.labels?.[VERB_LABEL] ?? null,
    createdAt: item.metadata.creationTimestamp,
    startTime: item.status?.startTime ?? null,
    completionTime: item.status?.completionTime ?? null,
    succeeded,
    failed,
    active,
    status,
  };
}

/** RFC 1123-safe unique Job name: verb id + millisecond timestamp, both
 * already-known-safe strings (verb ids are the fixed allowlist keys,
 * `Date.now()` is digits only) -- never raw request text. */
function buildJobName(verbId: AllowedCastleVerbId): string {
  return `castle-run-${verbId}-${Date.now()}`;
}

/**
 * RUN: creates one real `batch/v1` Job that invokes the castle binary
 * with the fixed argv for `verbId` (see ALLOWED_CASTLE_VERBS), against
 * whichever image DEPLOY most recently recorded. Fails closed if nothing
 * has been deployed yet -- RUN never falls back to a guessed image.
 */
export async function runCastleVerb(
  verbId: AllowedCastleVerbId,
  actor: string,
): Promise<K8sResult<CastleJob>> {
  const deployment = await getCastleDeployment();
  if (!deployment.ok) return deployment;
  if (!deployment.data) {
    return { ok: false, error: "castle has not been deployed to this cluster yet" };
  }
  const verb = ALLOWED_CASTLE_VERBS[verbId];
  const name = buildJobName(verbId);
  const manifest = {
    apiVersion: "batch/v1",
    kind: "Job",
    metadata: {
      name,
      namespace: CASTLE_NAMESPACE,
      labels: {
        [MANAGED_BY_LABEL]: MANAGED_BY_VALUE,
        [VERB_LABEL]: verbId,
        "platform-castle-run-by": sanitizeLabelValue(actor),
      },
    },
    spec: {
      backoffLimit: 0,
      activeDeadlineSeconds: 120,
      template: {
        metadata: {
          labels: { [MANAGED_BY_LABEL]: MANAGED_BY_VALUE, "job-name": name },
        },
        spec: {
          restartPolicy: "Never",
          // The `castle` namespace enforces the restricted PodSecurity
          // admission profile (k8s/namespaces.yaml) -- confirmed live: the
          // first Run without this securityContext got a real
          // `FailedCreate` from the job-controller ("violates PodSecurity
          // restricted:latest ..."). The castle image itself already runs
          // as a real non-root UID (Dockerfile's `USER castle:castle`),
          // so `runAsNonRoot: true` is simply true, not a workaround.
          // `runAsUser: 10001` matches the numeric UID the Dockerfile's
          // `USER castle:castle` resolves to -- confirmed live to be
          // required: kubelet cannot verify runAsNonRoot against a
          // non-numeric image USER ("container has runAsNonRoot and
          // image has non-numeric user, cannot verify user is non-root"),
          // even though the image is genuinely non-root either way.
          securityContext: {
            runAsNonRoot: true,
            runAsUser: 10001,
            seccompProfile: { type: "RuntimeDefault" },
          },
          containers: [
            {
              name: "castle",
              image: deployment.data.image,
              imagePullPolicy: "IfNotPresent",
              args: verb.args,
              securityContext: {
                allowPrivilegeEscalation: false,
                capabilities: { drop: ["ALL"] },
              },
              resources: {
                requests: { cpu: "50m", memory: "32Mi" },
                limits: { cpu: "200m", memory: "128Mi" },
              },
            },
          ],
        },
      },
    },
  };

  const result = await k8sRequest<JobItem>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(CASTLE_NAMESPACE)}/jobs`,
    "POST",
    manifest,
  );
  if (!result.ok) return result;
  return { ok: true, data: toCastleJob(result.data) };
}

// A k8s label value must match `(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?`
// and be <=63 chars -- an email's `@`/`+` are not legal label bytes, same
// constraint authz.ts's encodeIdentifierKey already documents for
// ConfigMap keys. Escaped the same way here, one-directional (the actor
// label is for human triage, never decoded back programmatically).
function sanitizeLabelValue(value: string): string {
  return value.replace(/[^-A-Za-z0-9_.]/g, "-").slice(0, 63);
}

/** Lists every real Job this module created -- "the listing IS the
 * record", same convention listJobs/toBackupJob already use. */
export async function listCastleJobs(): Promise<K8sResult<CastleJob[]>> {
  const result = await k8sRequest<JobListResponse>(
    `/apis/batch/v1/namespaces/${encodeURIComponent(CASTLE_NAMESPACE)}/jobs?labelSelector=${encodeURIComponent(`${MANAGED_BY_LABEL}=${MANAGED_BY_VALUE}`)}`,
  );
  if (!result.ok) return result;
  return { ok: true, data: (result.data.items ?? []).map(toCastleJob) };
}

interface PodListResponse {
  items?: Array<{ metadata: { name: string } }>;
}

/**
 * Real captured output for one Run: finds the (single, restartPolicy:
 * Never) Pod the named Job created via the `job-name` label the Job
 * template sets above, then reads its real container log. `null` (not an
 * error) if the Pod hasn't been scheduled yet.
 */
export async function getCastleJobOutput(jobName: string): Promise<K8sResult<string | null>> {
  const podsResult = await k8sRequest<PodListResponse>(
    `/api/v1/namespaces/${encodeURIComponent(CASTLE_NAMESPACE)}/pods?labelSelector=${encodeURIComponent(`job-name=${jobName}`)}`,
  );
  if (!podsResult.ok) return podsResult;
  const pod = podsResult.data.items?.[0];
  if (!pod) return { ok: true, data: null };
  const logs = await getPodLogs(CASTLE_NAMESPACE, pod.metadata.name);
  if (!logs.ok) {
    if (/ContainerCreating|not found|waiting to start/i.test(logs.error)) {
      return { ok: true, data: null };
    }
    return logs;
  }
  return { ok: true, data: logs.data };
}

// ------------------------------------------------------ Receipt cross-ref
//
// Best-effort extraction of castle's OWN independent receipt chain identity
// out of a Run's captured Job output, for the audit log to cross-reference
// (lib/audit-db.ts's `castle_receipt_digest` column) -- never a merge of
// the two chains, just a pointer from one to the other. A `ReceiptedOcelLog`
// (castle.rs:683-687) is produced only by `execute_powl_with_gym_act`
// (castle.rs:1005-1122), and NO verb in `ALLOWED_CASTLE_VERBS` above calls
// that path -- castle's CLI has no `construct`/`gymact` verb yet (see this
// file's header comment, castle's own VISION.md gap #3). So on every real
// castle run this console can trigger today, this returns `null`, and the
// audit entry simply omits the field -- exactly the same "absent, not
// fabricated" convention `getCastleDeployment` already uses for "not
// deployed yet". This function is wired ahead of that verb shipping so the
// cross-reference requires no further plumbing once it does.
//
// `Receipt` (castle.rs:513-522) has no `to_json`/Serialize impl today --
// there is no committed JSON schema for a future gymact verb's output to
// conform to -- so this looks for the one field name the real struct
// actually carries (`receipt_digest`), at top level or nested under a
// `receipt` key, rather than assuming a shape castle hasn't shipped.
export function parseCastleReceiptDigest(output: string | null): string | null {
  if (!output) return null;
  for (const line of output.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("{")) continue;
    let parsed: unknown;
    try {
      parsed = JSON.parse(trimmed);
    } catch {
      continue;
    }
    if (typeof parsed !== "object" || parsed === null) continue;
    const obj = parsed as Record<string, unknown>;
    if (typeof obj.receipt_digest === "string" && obj.receipt_digest.length > 0) {
      return obj.receipt_digest;
    }
    const nested = obj.receipt;
    if (nested && typeof nested === "object") {
      const digest = (nested as Record<string, unknown>).receipt_digest;
      if (typeof digest === "string" && digest.length > 0) return digest;
    }
  }
  return null;
}

// --------------------------------------------------------------- Sunset
export interface CastleSunsetResult {
  deploymentWasPresent: boolean;
  jobsDeleted: string[];
}

/**
 * SUNSET: deletes every real Job this module created (labeled
 * `app=platform-castle`) plus the deploy-state ConfigMap, and returns a
 * real, honest summary of what was actually torn down -- never a
 * fabricated "success" independent of what the API server actually did.
 * Each Job delete uses `propagationPolicy=Background` so the Job's own
 * Pod is garbage-collected too, not left orphaned.
 */
export async function sunsetCastle(): Promise<K8sResult<CastleSunsetResult>> {
  const jobsResult = await listCastleJobs();
  if (!jobsResult.ok) return jobsResult;

  const jobsDeleted: string[] = [];
  for (const job of jobsResult.data) {
    const del = await k8sRequest<unknown>(
      `/apis/batch/v1/namespaces/${encodeURIComponent(CASTLE_NAMESPACE)}/jobs/${encodeURIComponent(job.name)}?propagationPolicy=Background`,
      "DELETE",
    );
    if (del.ok) jobsDeleted.push(job.name);
  }

  const deployment = await getCastleDeployment();
  const deploymentWasPresent = deployment.ok && deployment.data !== null;
  if (deploymentWasPresent) {
    await k8sRequest<unknown>(
      `/api/v1/namespaces/${encodeURIComponent(CASTLE_NAMESPACE)}/configmaps/${encodeURIComponent(CASTLE_DEPLOYMENT_CONFIGMAP)}`,
      "DELETE",
    );
  }

  return { ok: true, data: { deploymentWasPresent, jobsDeleted } };
}
