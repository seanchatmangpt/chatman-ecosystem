import Nav from "@/components/Nav";
import {
  hasClusterCredentials,
  listServicesWithEndpoints,
  type ServiceDiscoveryRecord,
} from "@/lib/k8s";

export const dynamic = "force-dynamic";

// The platform's own namespaces -- the 4 project namespaces, supabase-demo,
// and platform-console's own namespace. Same list app/registry/page.tsx,
// app/logs/page.tsx, and app/usage/page.tsx use.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

function formatPorts(ports: ServiceDiscoveryRecord["ports"]): string {
  if (ports.length === 0) return "—";
  return ports
    .map((p) => {
      const name = p.name ? `${p.name}:` : "";
      const target = p.targetPort !== undefined ? `→${p.targetPort}` : "";
      return `${name}${p.port}/${p.protocol}${target}`;
    })
    .join(", ");
}

function EndpointsBadge({ ready, total }: { ready: number | null; total: number | null }) {
  if (ready === null || total === null) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-gray-700 bg-gray-900/40 px-2 py-0.5 text-xs text-gray-400">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-500" />
        no Endpoints object
      </span>
    );
  }
  if (total === 0) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-red-900 bg-red-950/40 px-2 py-0.5 text-xs text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
        0/0
      </span>
    );
  }
  if (ready === 0) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-red-900 bg-red-950/40 px-2 py-0.5 text-xs text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
        0/{total} ready
      </span>
    );
  }
  if (ready < total) {
    return (
      <span className="flex items-center gap-1 rounded-full border border-amber-900 bg-amber-950/40 px-2 py-0.5 text-xs text-amber-300">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        {ready}/{total} ready
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 rounded-full border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 text-xs text-emerald-300">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
      {ready}/{total} ready
    </span>
  );
}

export default async function ServiceDiscoveryPage() {
  const clusterConfigured = hasClusterCredentials();

  const rows: Array<{ namespace: string; records: ServiceDiscoveryRecord[] }> = [];
  const errors: Array<{ namespace: string; error: string }> = [];

  if (clusterConfigured) {
    const results = await Promise.all(
      PLATFORM_NAMESPACES.map(async (namespace) => ({
        namespace,
        result: await listServicesWithEndpoints(namespace),
      })),
    );
    for (const { namespace, result } of results) {
      if (result.ok) {
        rows.push({ namespace, records: result.data });
      } else {
        errors.push({ namespace, error: result.error });
      }
    }
  }

  const allRecords = rows.flatMap((r) => r.records);
  const zeroReadyCount = allRecords.filter(
    (r) => r.totalEndpoints !== null && r.totalEndpoints > 0 && r.readyEndpoints === 0,
  ).length;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Service Discovery</h1>

        <div className="mb-6 rounded-md border border-blue-900 bg-blue-950/30 px-4 py-3 text-sm text-blue-200">
          <strong>Real cluster-internal DNS, not a decorative view.</strong>{" "}
          The AWS Route53 private hosted zone / GCP Cloud DNS internal zone /
          Azure Private DNS equivalent here is CoreDNS plus every real k8s{" "}
          <code>Service</code>/<code>Endpoints</code> object -- the exact
          mechanism every other module&apos;s cluster-internal URLs already
          depend on (the Database module&apos;s Postgres/PostgREST hosts, the
          Backups module&apos;s <code>pg_dump</code> target). CoreDNS answers{" "}
          <code>&lt;svc&gt;.&lt;namespace&gt;.svc.cluster.local</code> from
          these same two objects, read live below via the k8s API -- never a
          separate DNS-specific API or a fabricated record.{" "}
          <strong>Ready endpoints</strong> is the load-bearing signal: how
          many backing Pod IPs are actually passing readiness right now, i.e.
          whether that DNS name currently resolves to something healthy.
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

        {clusterConfigured && allRecords.length > 0 && (
          <p className="mb-4 text-xs text-gray-500">
            {allRecords.length} Service(s) across {rows.length} namespaces --{" "}
            {zeroReadyCount === 0 ? (
              <span className="text-emerald-400">0 with zero ready endpoints</span>
            ) : (
              <span className="text-red-400">
                {zeroReadyCount} with zero ready endpoints
              </span>
            )}
            .
          </p>
        )}

        <div className="card overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wide text-gray-500">
                <th className="px-4 py-3 font-medium">Namespace</th>
                <th className="px-4 py-3 font-medium">Service</th>
                <th className="px-4 py-3 font-medium">DNS name</th>
                <th className="px-4 py-3 font-medium">ClusterIP</th>
                <th className="px-4 py-3 font-medium">Ports</th>
                <th className="px-4 py-3 font-medium">Ready endpoints</th>
              </tr>
            </thead>
            <tbody>
              {allRecords.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-sm text-gray-400">
                    {clusterConfigured ? "No Services found." : "—"}
                  </td>
                </tr>
              )}
              {rows.map(({ namespace, records }) =>
                records.map((r) => (
                  <tr
                    key={`${namespace}/${r.name}`}
                    className="border-b border-border/50 last:border-b-0"
                  >
                    <td className="px-4 py-3 text-gray-300">
                      <code>{namespace}</code>
                    </td>
                    <td className="px-4 py-3 text-gray-100">{r.name}</td>
                    <td className="px-4 py-3">
                      <code className="text-xs text-gray-100">{r.dns}</code>
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      <code className="text-xs">{r.clusterIP ?? "—"}</code>
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      <code className="text-xs">{formatPorts(r.ports)}</code>
                    </td>
                    <td className="px-4 py-3">
                      <EndpointsBadge ready={r.readyEndpoints} total={r.totalEndpoints} />
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-xs text-gray-500">
          &quot;Ready endpoints&quot; is <code>subsets[].addresses.length</code>{" "}
          on the real <code>core/v1 Endpoints</code> object matching each
          Service&apos;s name (the endpoint-controller&apos;s own naming
          convention); &quot;total&quot; adds{" "}
          <code>subsets[].notReadyAddresses.length</code> -- Pod IPs the
          Service selects but that have not yet passed a readiness probe.
          &quot;no Endpoints object&quot; means no Endpoints resource exists
          for that Service name at all (a selector matching nothing), distinct
          from a real 0/0.
        </p>
      </main>
    </>
  );
}
