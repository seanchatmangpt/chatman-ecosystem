import Nav from "@/components/Nav";
import CreateSecretForm from "@/components/CreateSecretForm";
import DeleteSecretButton from "@/components/DeleteSecretButton";
import { hasClusterCredentials, listSecrets, type SecretSummary } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// The platform's own namespaces only -- the 4 project namespaces plus
// supabase-demo -- matching exactly the Role+RoleBinding pairs granted in
// k8s/paas-rbac.yaml's Secrets Manager section. Never cluster-wide, never
// kube-system: this list IS the scope, both here and in the RBAC that
// backs it.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
];

export default async function SecretsPage() {
  const clusterConfigured = hasClusterCredentials();

  const results = await Promise.all(
    PLATFORM_NAMESPACES.map(async (ns) => ({ namespace: ns, result: await listSecrets(ns) })),
  );

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Secrets</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real Kubernetes <code>Secret</code> objects (<code>type: Opaque</code>
          ), scoped to the platform&apos;s own namespaces only via a
          per-namespace <code>Role</code>/<code>RoleBinding</code> pair (
          <code>k8s/paas-rbac.yaml</code>) -- never cluster-wide, never
          kube-system. Only secret NAMES and KEY names are ever shown here;
          decoded values are never rendered by this console.
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
                  <p className="text-sm text-gray-500">No secrets in this namespace.</p>
                )}

                {result.ok && result.data.length > 0 && (
                  <div className="divide-y divide-border">
                    {result.data.map((secret: SecretSummary) => (
                      <div
                        key={secret.name}
                        className="flex items-center justify-between gap-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-medium text-white">{secret.name}</p>
                          <p className="text-xs text-gray-500">
                            keys:{" "}
                            {secret.keys.length > 0 ? (
                              secret.keys.map((k) => (
                                <code key={k} className="mr-1.5">
                                  {k}
                                </code>
                              ))
                            ) : (
                              <span>(none)</span>
                            )}
                          </p>
                        </div>
                        <DeleteSecretButton namespace={secret.namespace} name={secret.name} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <CreateSecretForm namespaces={PLATFORM_NAMESPACES} />
      </main>
    </>
  );
}
