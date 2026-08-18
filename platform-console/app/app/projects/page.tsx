import Link from "next/link";
import Nav from "@/components/Nav";
import CreateProjectForm from "@/components/CreateProjectForm";
import { hasClusterCredentials, listNamespaces, listProjects } from "@/lib/k8s";

export const dynamic = "force-dynamic";

function ReadyBadge({ ready }: { ready: boolean | null }) {
  if (ready === null) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-gray-700 bg-gray-900/40 px-2 py-0.5 text-xs text-gray-400">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-500" />
        no status yet
      </span>
    );
  }
  if (ready) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        ready
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 rounded-full border border-amber-900 bg-amber-950/40 px-2 py-0.5 text-xs text-amber-300">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
      not ready
    </span>
  );
}

export default async function ProjectsPage() {
  const clusterConfigured = hasClusterCredentials();
  const [projectsResult, namespacesResult] = await Promise.all([
    listProjects(),
    listNamespaces(),
  ]);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Projects</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real <code>Project</code> custom resources (
          <code>core.supabase.io/v1alpha1</code>) read cluster-wide from the
          Kubernetes API via the console&apos;s ServiceAccount (
          <code>k8s/paas-rbac.yaml</code>), reconciled by the
          supabase-operator running in <code>supabase-system</code>.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
            This page only returns real data when running as the
            platform-console pod.
          </div>
        )}

        {clusterConfigured && !projectsResult.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {projectsResult.error}
          </div>
        )}

        {clusterConfigured && projectsResult.ok && (
          <div className="card mb-8 divide-y divide-border">
            {projectsResult.data.length === 0 && (
              <p className="p-6 text-sm text-gray-400">
                No Project custom resources found on the cluster.
              </p>
            )}
            {projectsResult.data.map((p) => (
              <div key={`${p.namespace}/${p.name}`} className="flex items-center justify-between gap-4 p-5">
                <div>
                  <Link
                    href={`/projects/${p.name}/database`}
                    className="text-sm font-medium text-white hover:text-accent"
                  >
                    {p.name}
                  </Link>
                  <p className="text-xs text-gray-500">
                    namespace <code>{p.namespace}</code>
                    {p.hostname && <> &middot; {p.hostname}</>}
                  </p>
                  {p.message && (
                    <p className="mt-1 max-w-xl break-all text-xs text-gray-500">{p.message}</p>
                  )}
                </div>
                <ReadyBadge ready={p.ready} />
              </div>
            ))}
          </div>
        )}

        <CreateProjectForm
          namespaces={namespacesResult.ok ? namespacesResult.data : []}
        />
      </main>
    </>
  );
}
