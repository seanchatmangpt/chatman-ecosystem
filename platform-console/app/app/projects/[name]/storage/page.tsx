import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ProjectSubNav from "@/components/ProjectSubNav";
import StorageSignedUrlPanel from "@/components/StorageSignedUrlPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { getProject, listNamespaceServices } from "@/lib/k8s";
import { fetchStorageBuckets } from "@/lib/storage-api";

export const dynamic = "force-dynamic";

export default async function ProjectStoragePage({
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
  const storageService = servicesResult.ok
    ? servicesResult.data.find(
        (s) =>
          s.labels["app.kubernetes.io/component"] === "storage" &&
          s.labels["app.kubernetes.io/instance"] === project.name,
      )
    : undefined;

  const adminResult = storageService
    ? await fetchStorageBuckets(storageService.dns, storageService.ports[0]?.port ?? 5000)
    : null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-1 text-2xl font-semibold text-white">{project.name}</h1>
        <p className="mb-6 text-sm text-gray-500">namespace <code>{project.namespace}</code></p>
        <ProjectSubNav name={project.name} active="storage" />

        <div className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">Storage</h2>

          {!storageService && (
            <p className="text-sm text-gray-500">
              not found: no storage Service in namespace <code>{project.namespace}</code>.
            </p>
          )}

          {storageService && (
            <dl className="mb-4 divide-y divide-border text-sm">
              <div className="grid grid-cols-3 gap-4 py-2">
                <dt className="text-gray-400">Service DNS</dt>
                <dd className="col-span-2 break-all text-gray-100">{storageService.dns}</dd>
              </div>
              <div className="grid grid-cols-3 gap-4 py-2">
                <dt className="text-gray-400">Port</dt>
                <dd className="col-span-2 text-gray-100">{storageService.ports[0]?.port ?? "-"}</dd>
              </div>
            </dl>
          )}

          {adminResult && adminResult.ok && (
            <div className="rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300">
              {adminResult.bucketCount} bucket(s){adminResult.bucketNames.length > 0 && `: ${adminResult.bucketNames.join(", ")}`}
            </div>
          )}

          {adminResult && !adminResult.ok && adminResult.notConfigured && (
            <div className="rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-sm text-amber-300">
              requires service-role key (not configured) -- set{" "}
              <code>SUPABASE_SERVICE_ROLE_KEY</code> to enable a real bucket
              listing from the Storage API.
            </div>
          )}

          {adminResult && !adminResult.ok && !adminResult.notConfigured && (
            <div className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
              {adminResult.error}
            </div>
          )}
        </div>

        <StorageSignedUrlPanelServerBoundary projectName={project.name} />
      </main>
    </>
  );
}

// Member+ gated, same convention every mutating panel in this console
// follows (e.g. app/api-keys/page.tsx's ApiKeysPanelServerBoundary): the
// real enforcement boundary is POST /api/projects/[name]/storage's own
// requireRole(session, "member") check, but this page hides the form
// entirely for a viewer-only session rather than showing controls that
// would just 403.
async function StorageSignedUrlPanelServerBoundary({ projectName }: { projectName: string }) {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) return null;

  const access = await requireRole(session, "member");
  if (!access.ok) return null;

  return <StorageSignedUrlPanel projectName={projectName} />;
}
