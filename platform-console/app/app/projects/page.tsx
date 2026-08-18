import Link from "next/link";
import Nav from "@/components/Nav";
import CreateProjectForm from "@/components/CreateProjectForm";
import TagEditor from "@/components/TagEditor";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { hasClusterCredentials, listNamespaces, listProjects } from "@/lib/k8s";
import { extractTags } from "@/lib/tags";

export const dynamic = "force-dynamic";

function ReadyBadge({ ready }: { ready: boolean | null }) {
  if (ready === null) {
    return (
      <Badge variant="outline" className="gap-1.5 text-muted-foreground">
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
        no status yet
      </Badge>
    );
  }
  if (ready) {
    return (
      <Badge variant="outline" className="gap-1.5 border-emerald-900 bg-emerald-950/40 text-emerald-300">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        ready
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="gap-1.5 border-amber-900 bg-amber-950/40 text-amber-300">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
      not ready
    </Badge>
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
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Projects</h1>
        <p className="mb-8 max-w-2xl text-sm text-muted-foreground">
          Real <code>Project</code> custom resources (
          <code>core.supabase.io/v1alpha1</code>) read cluster-wide from the
          Kubernetes API via the console&apos;s ServiceAccount (
          <code>k8s/paas-rbac.yaml</code>), reconciled by the
          supabase-operator running in <code>supabase-system</code>.
        </p>

        {!clusterConfigured && (
          <Alert className="mb-6 border-amber-900 bg-amber-950/40 text-amber-300">
            <AlertDescription className="text-amber-300">
              not configured: no in-cluster ServiceAccount credentials found.
              This page only returns real data when running as the
              platform-console pod.
            </AlertDescription>
          </Alert>
        )}

        {clusterConfigured && !projectsResult.ok && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{projectsResult.error}</AlertDescription>
          </Alert>
        )}

        {clusterConfigured && projectsResult.ok && (
          <Card className="mb-8 divide-y divide-border">
            {projectsResult.data.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">
                No Project custom resources found on the cluster.
              </p>
            )}
            {projectsResult.data.map((p) => (
              <div key={`${p.namespace}/${p.name}`} className="flex items-center justify-between gap-4 p-5">
                <div>
                  <Link
                    href={`/projects/${p.name}/database`}
                    className="text-sm font-medium text-foreground hover:text-accent"
                  >
                    {p.name}
                  </Link>
                  <p className="text-xs text-muted-foreground">
                    namespace <code>{p.namespace}</code>
                    {p.hostname && <> &middot; {p.hostname}</>}
                  </p>
                  {p.message && (
                    <p className="mt-1 max-w-xl break-all text-xs text-muted-foreground">{p.message}</p>
                  )}
                  <TagEditor
                    resourceType="project"
                    namespace={p.namespace}
                    name={p.name}
                    initialTags={extractTags(p.labels)}
                  />
                </div>
                <ReadyBadge ready={p.ready} />
              </div>
            ))}
          </Card>
        )}

        <CreateProjectForm
          namespaces={namespacesResult.ok ? namespacesResult.data : []}
        />
      </main>
    </>
  );
}
