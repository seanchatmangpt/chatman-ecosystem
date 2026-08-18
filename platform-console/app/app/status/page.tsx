import { getStatusPageData, type StatusComponent } from "@/lib/status-page";

// Public status page -- no session check, no Nav (this is meant to be
// reachable the same way status.aws.amazon.com or a statuspage.io page is:
// no login). Listed in middleware.ts's PUBLIC_PATHS. force-dynamic + a
// short meta-refresh means every render (and every 15s while the tab is
// open) re-runs the real Prometheus queries in lib/status-page.ts -- this
// is never a statically-baked "all systems operational" page.
export const dynamic = "force-dynamic";

const STATE_STYLE: Record<StatusComponent["state"], { dot: string; label: string; text: string }> = {
  operational: { dot: "bg-emerald-400", label: "Operational", text: "text-emerald-300" },
  degraded: { dot: "bg-amber-400", label: "Degraded performance", text: "text-amber-300" },
  down: { dot: "bg-red-500", label: "Down", text: "text-red-300" },
  unknown: { dot: "bg-gray-500", label: "No data yet", text: "text-gray-400" },
};

const OVERALL_COPY: Record<string, string> = {
  operational: "All systems operational",
  degraded: "Degraded performance on one or more components",
  down: "Active outage on one or more components",
  unknown: "Insufficient data",
};

function formatPercent(v: number | null): string {
  if (v === null) return "no data";
  return `${v.toFixed(2)}%`;
}

export default async function StatusPage() {
  const data = await getStatusPageData();

  return (
    <>
      <meta httpEquiv="refresh" content="15" />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-white">Platform Status</h1>
          <p className="mt-2 text-sm text-gray-400">
            Real uptime, computed live from Prometheus <code>up{"{"}component=&quot;...&quot;{"}"}</code>{" "}
            samples collected by <code>platform-prober</code> (see{" "}
            <code>services/platform-prober</code>) -- no static placeholder. This
            page is public: no login required, matching AWS Service Health
            Dashboard / statuspage.io.
          </p>
        </div>

        {!data.reachable && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            Prometheus is unreachable ({data.prometheusError}). The status
            below cannot be computed from real data right now, so no
            component state is shown.
          </div>
        )}

        {data.reachable && (
          <>
            <div className="card mb-6 flex items-center gap-3 p-6">
              <span className={`h-3 w-3 rounded-full ${STATE_STYLE[data.overall].dot}`} />
              <span className="text-lg font-medium text-white">
                {OVERALL_COPY[data.overall]}
              </span>
            </div>

            <div className="card overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-gray-400">
                    <th className="px-6 py-3 font-normal">Component</th>
                    <th className="px-6 py-3 font-normal">Current state</th>
                    <th className="px-6 py-3 font-normal">Uptime ({data.windowLabel})</th>
                    <th className="px-6 py-3 font-normal">Uptime (24h)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.components.map((c) => {
                    const style = STATE_STYLE[c.state];
                    return (
                      <tr key={c.id} className="border-b border-border/50">
                        <td className="px-6 py-4">
                          <div className="text-gray-100">{c.label}</div>
                          <div className="text-xs text-gray-500">{c.namespace}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center gap-2 ${style.text}`}>
                            <span className={`h-2 w-2 rounded-full ${style.dot}`} />
                            {style.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-100">
                          {formatPercent(c.uptimePercentWindow)}
                        </td>
                        <td className="px-6 py-4 text-gray-100">
                          {formatPercent(c.uptimePercentDay)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        <p className="mt-6 text-xs text-gray-500">
          Generated {data.generatedAt} · JSON at{" "}
          <a href="/api/status" className="underline">
            /api/status
          </a>{" "}
          · refreshes every 15s
        </p>
      </main>
    </>
  );
}
