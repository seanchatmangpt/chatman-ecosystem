import Nav from "@/components/Nav";
import { hasClusterCredentials, listHelmReleases, listKustomizations } from "@/lib/k8s";

export const dynamic = "force-dynamic";

function ReadyBadge({ ready }: { ready: boolean | null }) {
  if (ready === null) {
    return <span className="text-xs text-gray-500">no status yet</span>;
  }
  return ready ? (
    <span className="flex items-center gap-1 rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
      ready
    </span>
  ) : (
    <span className="flex items-center gap-1 rounded-full border border-amber-900 bg-amber-950/40 px-2 py-0.5 text-xs text-amber-300">
      <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
      not ready
    </span>
  );
}

export default async function GitOpsPage() {
  const clusterConfigured = hasClusterCredentials();
  const [kustomizations, helmReleases] = await Promise.all([
    listKustomizations(),
    listHelmReleases(),
  ]);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">GitOps</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Flux <code>Kustomization</code> and <code>HelmRelease</code>{" "}
          status, read cluster-wide from the Kubernetes API. Flux&apos;s
          CRDs are installed on this cluster; an empty list below means no
          objects currently exist, not a fetch failure.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
          </div>
        )}

        <div className="card mb-6">
          <h2 className="border-b border-border px-6 py-4 text-base font-medium text-white">
            Kustomizations
          </h2>
          {!kustomizations.ok && (
            <p className="px-6 py-4 text-sm text-red-300">{kustomizations.error}</p>
          )}
          {kustomizations.ok && kustomizations.data.length === 0 && (
            <p className="px-6 py-4 text-sm text-gray-400">None found.</p>
          )}
          {kustomizations.ok &&
            kustomizations.data.map((k) => (
              <div key={`${k.namespace}/${k.name}`} className="flex items-center justify-between gap-4 border-b border-border/50 px-6 py-3 last:border-b-0">
                <div>
                  <p className="text-sm text-gray-100">{k.name}</p>
                  <p className="text-xs text-gray-500">
                    <code>{k.namespace}</code>
                    {k.message && <> &middot; {k.message}</>}
                  </p>
                </div>
                <ReadyBadge ready={k.ready} />
              </div>
            ))}
        </div>

        <div className="card">
          <h2 className="border-b border-border px-6 py-4 text-base font-medium text-white">
            HelmReleases
          </h2>
          {!helmReleases.ok && (
            <p className="px-6 py-4 text-sm text-red-300">{helmReleases.error}</p>
          )}
          {helmReleases.ok && helmReleases.data.length === 0 && (
            <p className="px-6 py-4 text-sm text-gray-400">None found.</p>
          )}
          {helmReleases.ok &&
            helmReleases.data.map((h) => (
              <div key={`${h.namespace}/${h.name}`} className="flex items-center justify-between gap-4 border-b border-border/50 px-6 py-3 last:border-b-0">
                <div>
                  <p className="text-sm text-gray-100">{h.name}</p>
                  <p className="text-xs text-gray-500">
                    <code>{h.namespace}</code>
                    {h.message && <> &middot; {h.message}</>}
                  </p>
                </div>
                <ReadyBadge ready={h.ready} />
              </div>
            ))}
        </div>
      </main>
    </>
  );
}
