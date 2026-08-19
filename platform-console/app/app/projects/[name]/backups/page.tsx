import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import RunBackupButton from "@/components/RunBackupButton";
import RestoreBackupButton from "@/components/RestoreBackupButton";
import ExportAllButton from "@/components/ExportAllButton";
import {
  getProject,
  getProjectDatabasePod,
  getBackupsPvc,
  hasClusterCredentials,
  listJobs,
  type BackupJob,
} from "@/lib/k8s";

export const dynamic = "force-dynamic";

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

export default async function ProjectBackupsPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = await params;
  const projectResult = await getProject(name);

  if (!projectResult.ok || !projectResult.data) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <h1 className="mb-4 text-2xl font-semibold text-white">{name}</h1>
          <p className="text-sm text-gray-400">
            {!projectResult.ok ? projectResult.error : "Project not found."}
          </p>
        </main>
      </>
    );
  }

  const project = projectResult.data;
  const clusterConfigured = hasClusterCredentials();
  const dbPodResult = clusterConfigured ? await getProjectDatabasePod(project) : null;

  const shell = (body: React.ReactNode) => (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{project.name}</h1>
        <p className="mb-6 text-sm text-gray-500">
          namespace <code>{project.namespace}</code>
        </p>
        <ProjectSubNav name={project.name} active="backups" />
        {body}
      </main>
    </>
  );

  if (!clusterConfigured) {
    return shell(
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        not configured: no in-cluster ServiceAccount credentials found. This
        page only returns real data when running as the platform-console
        pod.
      </div>,
    );
  }

  if (!dbPodResult || !dbPodResult.ok) {
    return shell(
      <div className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        {dbPodResult && !dbPodResult.ok ? dbPodResult.error : "unknown error resolving database pod"}
      </div>,
    );
  }
  if (!dbPodResult.data) {
    return shell(
      <p className="text-sm text-gray-500">
        not found: no database Service in namespace <code>{project.namespace}</code>{" "}
        matched this project yet.
      </p>,
    );
  }

  const { namespace, podName, serviceName: stem } = dbPodResult.data;

  const [jobsResult, restoreJobsResult, pvcResult] = await Promise.all([
    listJobs(namespace, `app=platform-backups,database=${stem}`),
    listJobs(namespace, `app=platform-restores,database=${stem}`),
    getBackupsPvc(namespace, BACKUPS_PVC_NAME),
  ]);

  const jobs = jobsResult.ok
    ? [...jobsResult.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    : [];
  const restoreJobs = restoreJobsResult.ok
    ? [...restoreJobsResult.data].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    : [];

  return shell(
    <>
      <p className="mb-8 max-w-2xl text-sm text-gray-400">
        The RDS/Cloud SQL/Cloud Spanner automated-backup equivalent for this
        project&apos;s real Postgres, running as <code>{podName}</code> in{" "}
        <code>{namespace}</code>. &quot;Run backup now&quot; creates a real
        Kubernetes <code>Job</code> that runs <code>pg_dump</code> against
        that database&apos;s real Service, using the exact image and
        password Secret the database Pod itself already uses. Jobs are
        labeled <code>database={stem}</code> so this list shows only{" "}
        {project.name}&apos;s own backups, even when another project shares
        this namespace.
      </p>

      <div className="mb-6 card p-6">
        <h2 className="mb-3 text-base font-medium text-white">Storage</h2>
        {!pvcResult.ok && (
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {pvcResult.error}
          </p>
        )}
        {pvcResult.ok && !pvcResult.data && (
          <p className="text-sm text-gray-500">
            <code>{BACKUPS_PVC_NAME}</code> not yet provisioned -- it is
            created automatically the first time a backup runs.
          </p>
        )}
        {pvcResult.ok && pvcResult.data && (
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

        {!jobsResult.ok && (
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {jobsResult.error}
          </p>
        )}

        {jobsResult.ok && jobs.length === 0 && (
          <p className="text-sm text-gray-500">No backups yet. Run one below.</p>
        )}

        {jobsResult.ok && jobs.length > 0 && (
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
                        <RestoreBackupButton
                          projectName={project.name}
                          backupJobName={job.name}
                          dbPodName={podName}
                        />
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
          real <code>batch/v1</code> Job that dropped <code>{podName}</code>
          &apos;s schemas and replayed a backup&apos;s real{" "}
          <code>pg_dump</code> SQL back into it via <code>psql</code>,
          reading the same <code>{BACKUPS_PVC_NAME}</code> (mounted
          read-only) that the backup Jobs above wrote into.
        </p>

        {!restoreJobsResult.ok && (
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
            {restoreJobsResult.error}
          </p>
        )}

        {restoreJobsResult.ok && restoreJobs.length === 0 && (
          <p className="text-sm text-gray-500">
            No restores yet. Use &quot;Restore&quot; next to a Complete backup above.
          </p>
        )}

        {restoreJobsResult.ok && restoreJobs.length > 0 && (
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

      <div className="card p-6">
        <h2 className="mb-3 text-base font-medium text-white">Run backup now</h2>
        <p className="mb-4 text-xs text-gray-500">
          Submits a real <code>batch/v1</code> Job to the cluster via the
          console&apos;s ServiceAccount (scoped to <code>{namespace}</code>{" "}
          only -- see <code>k8s/paas-rbac.yaml</code>). The Job runs{" "}
          <code>pg_dump</code> against the live database and writes the
          dump to <code>{BACKUPS_PVC_NAME}</code>; its real status will
          appear in the table above on refresh.
        </p>
        <RunBackupButton projectName={project.name} />
      </div>

      <div className="mt-6 card p-6">
        <h2 className="mb-3 text-base font-medium text-white">
          Export everything (offboarding)
        </h2>
        <p className="mb-4 max-w-2xl text-xs text-gray-500">
          The real &quot;if we leave, how do we get our data out&quot; bundle -- unlike the IaC export
          (which only re-exports the Project/SingleDatabase Kubernetes manifest shape, never row
          data), this triggers a real <code>pg_dump</code> backup, downloads every real object
          across every real storage bucket, and pulls the real durable audit-log NDJSON export,
          then zips all three into one archive and hands back one signed, time-boxed download
          link -- owner-only, and every access to the link is written to the audit trail.
        </p>
        <ExportAllButton projectName={project.name} />
      </div>
    </>,
  );
}
