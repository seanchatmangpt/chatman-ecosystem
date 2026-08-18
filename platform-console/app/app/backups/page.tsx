import Nav from "@/components/Nav";
import RunBackupButton from "@/components/RunBackupButton";
import RestoreBackupButton from "@/components/RestoreBackupButton";
import { getBackupsPvc, hasClusterCredentials, listJobs, type BackupJob } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Matches app/api/backups/route.ts -- the only real backup target on this
// cluster, and the only namespace k8s/paas-rbac.yaml's
// platform-console-backups Role grants batch/jobs + persistentvolumeclaims
// verbs in.
const BACKUP_NAMESPACE = "supabase-demo";
const BACKUP_DB_POD = "demo-db-postgres-0";
const BACKUPS_PVC_NAME = "platform-backups-pvc";

function StatusBadge({ status }: { status: BackupJob["status"] }) {
  if (status === "Complete") {
    return (
      <span className="flex items-center gap-1 rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        Complete
      </span>
    );
  }
  if (status === "Failed") {
    return (
      <span className="flex items-center gap-1 rounded-full border border-red-900 bg-red-950/40 px-2 py-0.5 text-xs text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
        Failed
      </span>
    );
  }
  if (status === "Running") {
    return (
      <span className="flex items-center gap-1 rounded-full border border-amber-900 bg-amber-950/40 px-2 py-0.5 text-xs text-amber-300">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        Running
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 rounded-full border border-gray-700 bg-gray-900/40 px-2 py-0.5 text-xs text-gray-400">
      <span className="h-1.5 w-1.5 rounded-full bg-gray-500" />
      Pending
    </span>
  );
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "-";
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
}

export default async function BackupsPage() {
  const clusterConfigured = hasClusterCredentials();

  const [jobsResult, restoreJobsResult, pvcResult] = clusterConfigured
    ? await Promise.all([
        listJobs(BACKUP_NAMESPACE, "app=platform-backups"),
        listJobs(BACKUP_NAMESPACE, "app=platform-restores"),
        getBackupsPvc(BACKUP_NAMESPACE, BACKUPS_PVC_NAME),
      ])
    : [null, null, null];

  const jobs = jobsResult?.ok
    ? [...jobsResult.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    : [];
  const restoreJobs = restoreJobsResult?.ok
    ? [...restoreJobsResult.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    : [];

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Database Backups</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          The RDS/Cloud SQL/Cloud Spanner automated-backup equivalent for the
          real Postgres running as <code>{BACKUP_DB_POD}</code> in{" "}
          <code>{BACKUP_NAMESPACE}</code>. &quot;Run backup now&quot; creates a
          real Kubernetes <code>Job</code> that runs <code>pg_dump</code>{" "}
          against that database&apos;s real Service, using the exact image
          and password Secret the database Pod itself already uses. PVC
          contents aren&apos;t directly queryable via the Kubernetes API, so
          the list below -- real Jobs, real completion status, real duration
          -- <em>is</em> the backup inventory, not a separate catalog that
          could drift out of sync with what actually ran.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
            This page only returns real data when running as the
            platform-console pod.
          </div>
        )}

        {clusterConfigured && (
          <>
            <div className="mb-6 card p-6">
              <h2 className="mb-3 text-base font-medium text-white">Storage</h2>
              {pvcResult && !pvcResult.ok && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {pvcResult.error}
                </p>
              )}
              {pvcResult && pvcResult.ok && !pvcResult.data && (
                <p className="text-sm text-gray-500">
                  <code>{BACKUPS_PVC_NAME}</code> not yet provisioned -- it is
                  created automatically the first time a backup runs.
                </p>
              )}
              {pvcResult && pvcResult.ok && pvcResult.data && (
                <dl className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <dt className="text-gray-500">PVC</dt>
                    <dd className="text-white">
                      <code>{pvcResult.data.name}</code>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Phase</dt>
                    <dd className="text-white">{pvcResult.data.phase ?? "Unknown"}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Capacity</dt>
                    <dd className="text-white">{pvcResult.data.capacity ?? "-"}</dd>
                  </div>
                  <div className="col-span-3">
                    <dt className="text-gray-500">Storage class</dt>
                    <dd className="text-white">
                      {pvcResult.data.storageClassName ?? "(cluster default)"}
                    </dd>
                  </div>
                </dl>
              )}
            </div>

            <div className="mb-6 card p-6">
              <h2 className="mb-4 text-base font-medium text-white">Backup jobs</h2>

              {jobsResult && !jobsResult.ok && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {jobsResult.error}
                </p>
              )}

              {jobsResult && jobsResult.ok && jobs.length === 0 && (
                <p className="text-sm text-gray-500">
                  No backups yet. Run one below.
                </p>
              )}

              {jobsResult && jobsResult.ok && jobs.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-border text-gray-500">
                        <th className="py-2 pr-4 font-medium">Job</th>
                        <th className="py-2 pr-4 font-medium">Created</th>
                        <th className="py-2 pr-4 font-medium">Status</th>
                        <th className="py-2 pr-4 font-medium">Duration</th>
                        <th className="py-2 pr-4 font-medium">Restore</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {jobs.map((job) => (
                        <tr key={job.name}>
                          <td className="py-2 pr-4">
                            <code className="text-white">{job.name}</code>
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {new Date(job.createdAt).toLocaleString()}
                          </td>
                          <td className="py-2 pr-4">
                            <StatusBadge status={job.status} />
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {formatDuration(job.durationSeconds)}
                          </td>
                          <td className="py-2 pr-4">
                            {job.status === "Complete" ? (
                              <RestoreBackupButton backupJobName={job.name} />
                            ) : (
                              <span className="text-xs text-gray-600">
                                only Complete backups can be restored
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="mb-6 card p-6">
              <h2 className="mb-4 text-base font-medium text-white">Restore jobs</h2>
              <p className="mb-4 text-xs text-gray-500">
                The RDS/Cloud SQL point-in-time-restore equivalent: each row is a
                real <code>batch/v1</code> Job that dropped{" "}
                <code>{BACKUP_DB_POD}</code>&apos;s schemas and replayed a backup&apos;s
                real <code>pg_dump</code> SQL back into it via <code>psql</code>, reading
                the same <code>{BACKUPS_PVC_NAME}</code> (mounted read-only) that the
                backup Jobs above wrote into.
              </p>

              {restoreJobsResult && !restoreJobsResult.ok && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {restoreJobsResult.error}
                </p>
              )}

              {restoreJobsResult && restoreJobsResult.ok && restoreJobs.length === 0 && (
                <p className="text-sm text-gray-500">
                  No restores yet. Use &quot;Restore&quot; next to a Complete backup above.
                </p>
              )}

              {restoreJobsResult && restoreJobsResult.ok && restoreJobs.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-border text-gray-500">
                        <th className="py-2 pr-4 font-medium">Job</th>
                        <th className="py-2 pr-4 font-medium">Created</th>
                        <th className="py-2 pr-4 font-medium">Status</th>
                        <th className="py-2 pr-4 font-medium">Duration</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {restoreJobs.map((job) => (
                        <tr key={job.name}>
                          <td className="py-2 pr-4">
                            <code className="text-white">{job.name}</code>
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {new Date(job.createdAt).toLocaleString()}
                          </td>
                          <td className="py-2 pr-4">
                            <StatusBadge status={job.status} />
                          </td>
                          <td className="py-2 pr-4 text-gray-400">
                            {formatDuration(job.durationSeconds)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        <div className="card p-6">
          <h2 className="mb-3 text-base font-medium text-white">Run backup now</h2>
          <p className="mb-4 text-xs text-gray-500">
            Submits a real <code>batch/v1</code> Job to the cluster via the
            console&apos;s ServiceAccount (scoped to <code>{BACKUP_NAMESPACE}</code>{" "}
            only -- see <code>k8s/paas-rbac.yaml</code>). The Job runs{" "}
            <code>pg_dump</code> against the live database and writes the
            dump to <code>{BACKUPS_PVC_NAME}</code>; its real status will
            appear in the table above on refresh.
          </p>
          <RunBackupButton />
        </div>
      </main>
    </>
  );
}
