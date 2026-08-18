import Nav from "@/components/Nav";
import { getResourceUsage, hasClusterCredentials, type NamespaceResourceUsage } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// The platform's own namespaces -- the 4 project namespaces, supabase-demo,
// and platform-console's own namespace. Same list app/registry/page.tsx and
// app/logs/page.tsx use.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

function formatCpu(millicores: number): string {
  return `${millicores.toFixed(millicores < 10 ? 2 : 0)}m`;
}

function formatMemory(mib: number): string {
  if (mib >= 1024) return `${(mib / 1024).toFixed(2)}Gi`;
  return `${mib.toFixed(1)}Mi`;
}

function barColor(percent: number | null): string {
  if (percent === null) return "bg-gray-700";
  if (percent >= 90) return "bg-red-500";
  if (percent >= 70) return "bg-amber-500";
  return "bg-emerald-500";
}

function UsageBar({ percent }: { percent: number | null }) {
  if (percent === null) {
    return <span className="text-xs text-gray-500">no quota set</span>;
  }
  const clampedWidth = Math.min(100, Math.max(0, percent));
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-32 overflow-hidden rounded-full bg-gray-800">
        <div
          className={`h-full ${barColor(percent)}`}
          style={{ width: `${clampedWidth}%` }}
        />
      </div>
      <span className="w-14 text-right text-xs text-gray-400">
        {percent.toFixed(1)}%
      </span>
    </div>
  );
}

export default async function UsagePage() {
  const clusterConfigured = hasClusterCredentials();

  const rows: Array<{ namespace: string; usage: NamespaceResourceUsage }> = [];
  const errors: Array<{ namespace: string; error: string }> = [];

  if (clusterConfigured) {
    const results = await Promise.all(
      PLATFORM_NAMESPACES.map(async (namespace) => ({
        namespace,
        result: await getResourceUsage(namespace),
      })),
    );
    for (const { namespace, result } of results) {
      if (result.ok) {
        rows.push({ namespace, usage: result.data });
      } else {
        errors.push({ namespace, error: result.error });
      }
    }
  }

  const totalCpu = rows.reduce((sum, r) => sum + r.usage.cpuUsageMillicores, 0);
  const totalMemory = rows.reduce((sum, r) => sum + r.usage.memoryUsageMiB, 0);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Cost &amp; Usage</h1>

        <div className="mb-6 rounded-md border border-blue-900 bg-blue-950/30 px-4 py-3 text-sm text-blue-200">
          <strong>Real-time resource consumption metrics.</strong> This is not
          a billing statement -- no payment processor is connected, and no
          dollar amount is computed or shown anywhere on this page. Every
          number below is read live from this cluster&apos;s own
          metrics-server (<code>metrics.k8s.io</code>, the same source{" "}
          <code>kubectl top pods</code> reads) and the real{" "}
          <code>ResourceQuota</code> object for each namespace -- the AWS
          Cost Explorer / GCP Billing Reports / Azure Cost Management
          equivalent, grounded in measured infrastructure consumption
          instead of currency.
        </div>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found.
            This page only returns real data when running as the
            platform-console pod.
          </div>
        )}

        {errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {errors.map((e) => (
              <p
                key={e.namespace}
                className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300"
              >
                {e.namespace}: {e.error}
              </p>
            ))}
          </div>
        )}

        {clusterConfigured && rows.length > 0 && (
          <p className="mb-4 text-xs text-gray-500">
            Cluster-wide across these {rows.length} namespaces: real live
            total {formatCpu(totalCpu)} CPU / {formatMemory(totalMemory)}{" "}
            memory in use right now.
          </p>
        )}

        <div className="card overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3 font-medium">Namespace</th>
                <th className="px-4 py-3 font-medium">CPU usage</th>
                <th className="px-4 py-3 font-medium">CPU quota (limits.cpu)</th>
                <th className="px-4 py-3 font-medium">CPU % of quota</th>
                <th className="px-4 py-3 font-medium">Memory usage</th>
                <th className="px-4 py-3 font-medium">Memory quota (limits.memory)</th>
                <th className="px-4 py-3 font-medium">Memory % of quota</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-sm text-gray-400">
                    {clusterConfigured ? "No namespaces measured." : "—"}
                  </td>
                </tr>
              )}
              {rows.map(({ namespace, usage }) => (
                <tr key={namespace} className="border-b border-border/50 last:border-b-0">
                  <td className="px-4 py-3 text-gray-100">
                    <code>{namespace}</code>
                    {usage.podsMeasured === 0 && (
                      <p className="mt-1 text-[11px] text-gray-500">
                        no pods with a fresh metrics-server reading
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {formatCpu(usage.cpuUsageMillicores)}
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {usage.quota?.hardCpuMillicores !== null &&
                    usage.quota?.hardCpuMillicores !== undefined
                      ? formatCpu(usage.quota.hardCpuMillicores)
                      : usage.quota
                        ? "—"
                        : "no quota"}
                  </td>
                  <td className="px-4 py-3">
                    <UsageBar percent={usage.cpuPercentOfQuota} />
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {formatMemory(usage.memoryUsageMiB)}
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {usage.quota?.hardMemoryMiB !== null &&
                    usage.quota?.hardMemoryMiB !== undefined
                      ? formatMemory(usage.quota.hardMemoryMiB)
                      : usage.quota
                        ? "—"
                        : "no quota"}
                  </td>
                  <td className="px-4 py-3">
                    <UsageBar percent={usage.memoryPercentOfQuota} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-xs text-gray-500">
          &quot;% of quota&quot; compares live usage against each
          namespace&apos;s <code>ResourceQuota.status.hard[&quot;limits.cpu&quot;
          / &quot;limits.memory&quot;]</code> -- the real ceiling live usage
          is bound by (CPU throttling / OOM-kill), not the separate{" "}
          <code>requests.*</code> reservation ceiling. A namespace with no
          <code> ResourceQuota</code> object at all shows &quot;no
          quota&quot; rather than a fabricated percentage.
        </p>
      </main>
    </>
  );
}
