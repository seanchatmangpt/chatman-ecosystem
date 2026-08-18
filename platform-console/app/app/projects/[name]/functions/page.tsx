import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import InvokeFunctionButton from "@/components/InvokeFunctionButton";
import { getProject, listNamespaceServices } from "@/lib/k8s";

export const dynamic = "force-dynamic";

export default async function ProjectFunctionsPage({
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
  const functionsService = servicesResult.ok
    ? servicesResult.data.find(
        (s) =>
          s.labels["app.kubernetes.io/component"] === "functions" &&
          s.labels["app.kubernetes.io/instance"] === project.name,
      )
    : undefined;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{project.name}</h1>
        <p className="mb-6 text-sm text-gray-500">namespace <code>{project.namespace}</code></p>
        <ProjectSubNav name={project.name} active="functions" />

        <div className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">Functions</h2>

          {!functionsService && (
            <p className="text-sm text-gray-500">
              not found: no functions Service in namespace <code>{project.namespace}</code>.
            </p>
          )}

          {functionsService && (
            <>
              <dl className="mb-4 divide-y divide-border text-sm">
                <div className="grid grid-cols-3 gap-4 py-2">
                  <dt className="text-gray-400">Service DNS</dt>
                  <dd className="col-span-2 break-all text-gray-100">{functionsService.dns}</dd>
                </div>
                <div className="grid grid-cols-3 gap-4 py-2">
                  <dt className="text-gray-400">Port</dt>
                  <dd className="col-span-2 text-gray-100">{functionsService.ports[0]?.port ?? "-"}</dd>
                </div>
              </dl>
              <p className="mb-4 text-xs text-gray-500">
                not configured: the Supabase edge-functions runtime exposes
                no admin introspection API (no endpoint lists deployed
                function slugs), so this module never fabricates a
                deployed-function count. What it does do for real: POST a
                function slug straight to this Service&apos;s real port and show
                the real HTTP response that comes back -- the round-trip
                itself is the proof a slug is (or isn&apos;t) actually deployed.
              </p>
              <InvokeFunctionButton projectName={project.name} />
            </>
          )}
        </div>
      </main>
    </>
  );
}
