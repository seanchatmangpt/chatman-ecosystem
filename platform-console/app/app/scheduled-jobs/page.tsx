import Nav from "@/components/Nav";
import CreateScheduledJobForm from "@/components/CreateScheduledJobForm";
import DeleteScheduledJobButton from "@/components/DeleteScheduledJobButton";
import { hasClusterCredentials } from "@/lib/k8s";
import {
  ALLOWED_COMMANDS,
  listCronJobs,
  SCHEDULABLE_NAMESPACES,
  type ScheduledJob,
} from "@/lib/scheduled-jobs";

export const dynamic = "force-dynamic";

const COMMAND_OPTIONS = Object.values(ALLOWED_COMMANDS).map((c) => ({
  id: c.id,
  label: c.label,
  description: c.description,
}));

export default async function ScheduledJobsPage() {
  const clusterConfigured = hasClusterCredentials();

  const results = await Promise.all(
    SCHEDULABLE_NAMESPACES.map(async (ns) => ({ namespace: ns, result: await listCronJobs(ns) })),
  );

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Scheduled Jobs</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Scheduled Jobs (AWS EventBridge Scheduler / GCP Cloud Scheduler /
          Azure Logic Apps recurring-trigger equivalent): real Kubernetes{" "}
          <code>batch/v1</code> <code>CronJob</code> objects, scoped to the
          platform&apos;s own namespaces only via a per-namespace{" "}
          <code>Role</code>/<code>RoleBinding</code> pair (
          <code>k8s/paas-rbac.yaml</code>) -- never cluster-wide, never
          kube-system. The command a job runs always comes from a fixed,
          server-validated allowlist (never free-text user input) -- see
          the create form below.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
            This page only returns real data when running as the
            platform-console pod.
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
                  <p className="text-sm text-gray-500">No scheduled jobs in this namespace.</p>
                )}

                {result.ok && result.data.length > 0 && (
                  <div className="divide-y divide-border">
                    {result.data.map((job: ScheduledJob) => (
                      <div
                        key={job.name}
                        className="flex items-center justify-between gap-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-medium text-white">
                            {job.name}{" "}
                            {job.suspend && (
                              <span className="ml-1 rounded bg-amber-950/60 px-1.5 py-0.5 text-[10px] text-amber-300">
                                suspended
                              </span>
                            )}
                          </p>
                          <p className="text-xs text-gray-500">
                            schedule: <code>{job.schedule}</code> · command:{" "}
                            <code>{job.commandId ?? "(unrecognized)"}</code>
                          </p>
                          <p className="text-xs text-gray-500">
                            last scheduled:{" "}
                            {job.lastScheduleTime ? (
                              <code>{job.lastScheduleTime}</code>
                            ) : (
                              <span>never yet</span>
                            )}{" "}
                            · last successful:{" "}
                            {job.lastSuccessfulTime ? (
                              <code>{job.lastSuccessfulTime}</code>
                            ) : (
                              <span>none yet</span>
                            )}
                          </p>
                        </div>
                        <DeleteScheduledJobButton namespace={job.namespace} name={job.name} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <CreateScheduledJobForm
          namespaces={[...SCHEDULABLE_NAMESPACES]}
          commands={COMMAND_OPTIONS}
        />
      </main>
    </>
  );
}
