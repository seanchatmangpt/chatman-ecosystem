import Nav from "@/components/Nav";
import LogsViewer from "@/components/LogsViewer";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// The platform's own namespaces only -- the 4 project namespaces,
// supabase-demo, and platform-console's own namespace -- matching exactly
// the Role+RoleBinding pairs granted in k8s/paas-rbac.yaml's Logs section.
// Never cluster-wide, never kube-system: this list IS the scope, both here
// and in the RBAC that backs it (same convention app/secrets/page.tsx uses
// for its own per-namespace RBAC).
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

export default async function LogsPage() {
  const clusterConfigured = hasClusterCredentials();

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Logs</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real pod stdout/stderr, read live via the Kubernetes pod log
          subresource (<code>GET /api/v1/namespaces/&#123;ns&#125;/pods/&#123;pod&#125;/log</code>
          ) -- the same primitive CloudWatch Logs / GCP Cloud Logging / Azure
          Monitor Logs are built on. Scoped to the platform&apos;s own
          namespaces only via a per-namespace <code>Role</code>/
          <code>RoleBinding</code> pair (<code>k8s/paas-rbac.yaml</code>) --
          never cluster-wide, never kube-system. This is a manual-refresh
          tail, not a live stream -- press Refresh to fetch the current last
          N lines.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
            This page only returns real data when running as the
            platform-console pod.
          </div>
        )}

        {clusterConfigured && <LogsViewer namespaces={PLATFORM_NAMESPACES} />}
      </main>
    </>
  );
}
