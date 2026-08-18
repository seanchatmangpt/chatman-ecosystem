import Nav from "@/components/Nav";
import CreateBatchJobForm from "@/components/CreateBatchJobForm";
import BatchJobMonitor from "@/components/BatchJobMonitor";
import { hasClusterCredentials } from "@/lib/k8s";
import {
  ALLOWED_BATCH_COMMANDS,
  BATCHABLE_NAMESPACES,
  MAX_BATCH_SIZE,
  MIN_BATCH_SIZE,
  listBatchJobs,
} from "@/lib/batch-jobs";

export const dynamic = "force-dynamic";

const COMMAND_OPTIONS = Object.values(ALLOWED_BATCH_COMMANDS).map((c) => ({
  id: c.id,
  label: c.label,
  description: c.description,
}));

export default async function BatchJobsPage() {
  const clusterConfigured = hasClusterCredentials();

  const results = await Promise.all(
    BATCHABLE_NAMESPACES.map(async (ns) => ({ namespace: ns, result: await listBatchJobs(ns) })),
  );

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Batch Compute</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Batch Compute (AWS Batch / GCP Batch / Azure Batch equivalent): self-service parallel
          job fan-out using a real Kubernetes Indexed <code>batch/v1</code> <code>Job</code> (
          <code>completionMode: Indexed</code>, <code>parallelism</code> == <code>completions</code>
          ), distinct from the single-shot, time-triggered <code>/scheduled-jobs</code> module. Each
          of the up to {MAX_BATCH_SIZE} pods it launches gets its own real{" "}
          <code>JOB_COMPLETION_INDEX</code> env var (injected by the Job controller itself) and
          writes its own real, deterministic result into a shared{" "}
          <code>platform-batch-results</code> ConfigMap, using its own narrowly-scoped
          ServiceAccount -- collected back here into one aggregated result set. Scoped to the
          platform&apos;s own namespaces only, same per-namespace <code>Role</code>/
          <code>RoleBinding</code> pattern as Scheduled Jobs (<code>k8s/paas-rbac.yaml</code>). The
          command a job runs always comes from a fixed, server-validated allowlist -- see the
          launch form below.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && (
          <div className="mb-8 space-y-6">
            {results.map(({ namespace, result }) => (
              <div key={namespace} className="card p-6">
                <h2 className="mb-4 text-base font-medium text-white">
                  <code>{namespace}</code>
                </h2>

                {!result.ok && (
                  <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                    {result.error}
                  </p>
                )}

                {result.ok && result.data.length === 0 && (
                  <p className="text-sm text-gray-500">No batch jobs in this namespace.</p>
                )}

                {result.ok && result.data.length > 0 && (
                  <div className="space-y-6">
                    {result.data.map((job) => (
                      <BatchJobMonitor key={job.name} namespace={job.namespace} name={job.name} />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <CreateBatchJobForm
          namespaces={[...BATCHABLE_NAMESPACES]}
          commands={COMMAND_OPTIONS}
          minSize={MIN_BATCH_SIZE}
          maxSize={MAX_BATCH_SIZE}
        />
      </main>
    </>
  );
}
