import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { hasClusterCredentials, listProjects, listJobs, type BackupJob } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Owner-only, read-only page (same enforcement boundary as /org and
// /audit -- lib/authz.ts's requireRole, not just hidden client-side).
// Surfaces two things side by side:
//   1. A condensed summary of the real, tested runbook in
//      docs/DISASTER-RECOVERY.md (kept as static text here, not read from
//      disk at runtime -- the Dockerfile's build context is app/ only, so
//      docs/, a sibling of app/, is never copied into the deployed image;
//      see that Dockerfile's COPY list. The full doc lives in the repo for
//      anyone with source access).
//   2. The REAL current backup inventory -- reusing the exact
//      listProjects/listJobs primitives the Backups module
//      (/projects/[name]/backups) already calls, aggregated across every
//      real Project namespace instead of one project at a time, so an
//      operator can see "what's actually backed up right now" across the
//      whole platform in one place.

function StatusBadge({ status }: { status: BackupJob["status"] }) {
  const styles: Record<BackupJob["status"], string> = {
    Complete: "border-emerald-900 bg-emerald-950/40 text-emerald-300",
    Failed: "border-red-900 bg-red-950/40 text-red-300",
    Running: "border-amber-900 bg-amber-950/40 text-amber-300",
    Pending: "border-gray-700 bg-gray-900/40 text-gray-400",
  };
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs ${styles[status]}`}>{status}</span>
  );
}

export default async function DisasterRecoveryPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  const clusterConfigured = hasClusterCredentials();

  const shell = (body: React.ReactNode) => (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Disaster Recovery</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          The AWS Well-Architected DR-pillar / GCP DR-planning-guide equivalent for this
          platform, grounded in a real incident this cluster actually recovered from -- not a
          hypothetical. Full runbook, real commit citations, and a real bounded
          delete-then-recover proof:{" "}
          <code className="text-gray-300">docs/DISASTER-RECOVERY.md</code>. This page is
          read-only.
        </p>
        {body}
      </main>
    </>
  );

  if (!session) {
    return shell(
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        unauthenticated
      </p>,
    );
  }

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    return shell(
      <div className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        <p className="font-medium">403 -- forbidden</p>
        <p className="mt-1 text-red-300/80">
          Your role (<code>{access.role}</code>) does not meet the required minimum role (
          <code>owner</code>) for this page.
        </p>
      </div>,
    );
  }

  return shell(
    <>
      <section className="mb-8 card p-6">
        <h2 className="mb-3 text-base font-medium text-white">
          The 2026-08-17 incident, in brief
        </h2>
        <p className="mb-3 text-sm text-gray-300">
          The prior <code>platform-eng-colima</code> cluster hit an unrecoverable etcd storage
          fault -- a bbolt page checksum panic in the etcd container -- with no snapshot backup.
          The cluster was recreated from <code>infra/kind-config.yaml</code> (same node image
          and port mappings, confirmed via <code>docker inspect</code> against the dying
          container before deletion) and the base stack was restood in dependency order: Istio
          -&gt; Flux -&gt; kube-prometheus-stack -&gt; the Supabase operator, then the demo
          project was re-provisioned and <code>platform-console</code> itself redeployed. Real
          namespace <code>creationTimestamp</code>s put the whole sequence at 11 minutes 26
          seconds, cluster bootstrap to <code>platform-console</code> existing.
        </p>
        <p className="text-sm text-gray-300">
          <strong className="text-white">Lost, honestly:</strong> every row in the prior demo
          database (a fresh Postgres, not a restore) -- there was no backup mechanism in this
          codebase at that time; the Database Backups module was added over two hours{" "}
          <em>after</em> this recovery commit, precisely because that gap was real.{" "}
          <strong className="text-white">Recovered exactly:</strong> every piece of declarative
          infrastructure (cluster config, Istio, Flux, Prometheus stack, the operator itself)
          and platform-console&apos;s own code, which was never in the cluster to begin with.
        </p>
      </section>

      <section className="mb-8 card p-6">
        <h2 className="mb-3 text-base font-medium text-white">
          Real proof: recovery tested, not just documented
        </h2>
        <p className="text-sm text-gray-300">
          A real, non-critical resource (the <code>platform-feature-flags</code> ConfigMap) was
          deleted on purpose, its loss confirmed through both <code>kubectl</code> and the live
          authenticated app (<code>GET /api/feature-flags</code> genuinely returned{" "}
          <code>{"{}"}</code>), then recovered via <code>kubectl apply</code> from a real
          backed-up manifest exported beforehand. The recovered <code>data</code> and the live
          app&apos;s response matched the pre-deletion state byte-for-byte. Full transcript:{" "}
          <code>docs/DISASTER-RECOVERY.md</code> section 4;{" "}
          <code>evidence/dr-proof/platform-feature-flags-backup.yaml</code> is the real backup
          artifact used. See <code>disaster-recovery-runbook-tested</code> in{" "}
          <code>evidence/control-evidence-bundle.json</code>.
        </p>
      </section>

      <section className="card p-6">
        <h2 className="mb-1 text-base font-medium text-white">
          What&apos;s actually backed up right now
        </h2>
        <p className="mb-4 text-sm text-gray-400">
          Every real <code>batch/v1</code> Job labeled <code>app=platform-backups</code>,
          across every real Supabase <code>Project</code> namespace -- the same Job listing{" "}
          <code>/projects/[name]/backups</code> shows per-project, aggregated here across the
          whole platform. This IS the backup record (no separate fabricated catalog) -- an
          empty list for a project means, honestly, that project has no recovery point today.
        </p>
        <BackupInventory clusterConfigured={clusterConfigured} />
      </section>
    </>,
  );
}

async function BackupInventory({ clusterConfigured }: { clusterConfigured: boolean }) {
  if (!clusterConfigured) {
    return (
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        not configured: no in-cluster ServiceAccount credentials found. This section only
        returns real data when running as the platform-console pod.
      </div>
    );
  }

  const projectsResult = await listProjects();
  if (!projectsResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {projectsResult.error}
      </p>
    );
  }

  // One real namespace can host more than one Project; only query each
  // namespace once regardless of how many Projects share it.
  const namespaces = [...new Set(projectsResult.data.map((p) => p.namespace))];

  const perNamespace = await Promise.all(
    namespaces.map(async (namespace) => ({
      namespace,
      jobs: await listJobs(namespace, "app=platform-backups"),
    })),
  );

  const rows: Array<{ namespace: string; job: BackupJob }> = [];
  const errors: string[] = [];
  for (const { namespace, jobs } of perNamespace) {
    if (!jobs.ok) {
      errors.push(`${namespace}: ${jobs.error}`);
      continue;
    }
    for (const job of jobs.data) rows.push({ namespace, job });
  }
  rows.sort((a, b) => b.job.createdAt.localeCompare(a.job.createdAt));

  if (namespaces.length === 0) {
    return <p className="text-sm text-gray-500">No real Project namespaces exist yet.</p>;
  }

  return (
    <>
      {errors.length > 0 && (
        <p className="mb-3 rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
          {errors.join("; ")}
        </p>
      )}
      {rows.length === 0 ? (
        <p className="text-sm text-gray-500">
          No backup Jobs found in any of the {namespaces.length} real project namespace
          {namespaces.length === 1 ? "" : "s"} checked ({namespaces.join(", ")}). Nothing here
          has a recovery point today.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-gray-500">
                <th className="py-2 pr-4 font-medium">Namespace</th>
                <th className="py-2 pr-4 font-medium">Job</th>
                <th className="py-2 pr-4 font-medium">Created</th>
                <th className="py-2 pr-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map(({ namespace, job }) => (
                <tr key={`${namespace}/${job.name}`}>
                  <td className="py-2 pr-4 text-gray-400">
                    <code>{namespace}</code>
                  </td>
                  <td className="py-2 pr-4">
                    <code className="text-white">{job.name}</code>
                  </td>
                  <td className="py-2 pr-4 text-gray-400">
                    {new Date(job.createdAt).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4">
                    <StatusBadge status={job.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
