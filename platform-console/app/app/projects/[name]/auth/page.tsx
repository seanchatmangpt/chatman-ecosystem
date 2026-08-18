import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import { getProject, listNamespaceServices } from "@/lib/k8s";
import { fetchGoTrueUserCount } from "@/lib/gotrue";

export const dynamic = "force-dynamic";

export default async function ProjectAuthPage({
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
  const servicesResult = await listNamespaceServices(project.namespace);
  const authService = servicesResult.ok
    ? servicesResult.data.find(
        (s) =>
          s.labels["app.kubernetes.io/component"] === "auth" &&
          s.labels["app.kubernetes.io/instance"] === project.name,
      )
    : undefined;

  const adminResult = authService
    ? await fetchGoTrueUserCount(authService.dns, authService.ports[0]?.port ?? 9999)
    : null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{project.name}</h1>
        <p className="mb-6 text-sm text-gray-500">namespace <code>{project.namespace}</code></p>
        <ProjectSubNav name={project.name} active="auth" />

        <div className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">GoTrue (Auth)</h2>

          {!authService && (
            <p className="text-sm text-gray-500">
              not found: no auth Service in namespace <code>{project.namespace}</code>.
            </p>
          )}

          {authService && (
            <dl className="mb-4 divide-y divide-border text-sm">
              <div className="grid grid-cols-3 gap-4 py-2">
                <dt className="text-gray-400">Service DNS</dt>
                <dd className="col-span-2 break-all text-gray-100">{authService.dns}</dd>
              </div>
              <div className="grid grid-cols-3 gap-4 py-2">
                <dt className="text-gray-400">Port</dt>
                <dd className="col-span-2 text-gray-100">{authService.ports[0]?.port ?? "-"}</dd>
              </div>
            </dl>
          )}

          {adminResult && adminResult.ok && (
            <div className="flex items-center gap-2 rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              {adminResult.userCount} user(s) (live from GoTrue admin API)
            </div>
          )}

          {adminResult && !adminResult.ok && adminResult.notConfigured && (
            <div className="rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-sm text-amber-300">
              requires service-role key (not configured) -- set{" "}
              <code>SUPABASE_SERVICE_ROLE_KEY</code> to enable a real user
              count from GoTrue&apos;s admin API.
            </div>
          )}

          {adminResult && !adminResult.ok && !adminResult.notConfigured && (
            <div className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
              {adminResult.error}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
