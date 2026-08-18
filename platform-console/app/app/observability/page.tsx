import Nav from "@/components/Nav";
import { queryPrometheus, grafanaPortForwardCommand } from "@/lib/prometheus";

export const dynamic = "force-dynamic";

export default async function ObservabilityPage() {
  const upResult = await queryPrometheus("up");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Observability</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real data from the monitoring stack already running in the{" "}
          <code>monitoring</code> namespace (kube-prometheus-stack) -- no
          synthetic metrics.
        </p>

        <div className="card mb-6 p-6">
          <h2 className="mb-2 text-base font-medium text-white">Grafana</h2>
          <p className="mb-3 text-sm text-gray-400">
            No public ingress exists for Grafana yet, so it&apos;s reached
            via a real port-forward to the live Service (
            <code>monitoring-grafana.monitoring.svc.cluster.local:80</code>):
          </p>
          <pre className="overflow-x-auto rounded-md border border-border bg-bg p-3 text-xs text-gray-200">
            {grafanaPortForwardCommand()}
          </pre>
          <p className="mt-2 text-xs text-gray-500">
            Then open http://localhost:3001 (default kube-prometheus-stack
            Grafana credentials, or those configured for this cluster).
          </p>
        </div>

        <div className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">
            Prometheus: <code>up</code>
          </h2>
          <p className="mb-4 text-xs text-gray-500">
            Live query proxied server-side to{" "}
            <code>monitoring-kube-prometheus-prometheus.monitoring.svc:9090/api/v1/query</code>
            {" "}via <code>/api/prometheus?query=up</code>.
          </p>

          {!upResult.ok && (
            <div className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
              {upResult.error}
            </div>
          )}

          {upResult.ok && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-gray-400">
                    <th className="py-2 pr-4 font-normal">job</th>
                    <th className="py-2 pr-4 font-normal">instance</th>
                    <th className="py-2 font-normal">value</th>
                  </tr>
                </thead>
                <tbody>
                  {(upResult.data.data?.result ?? []).map((series, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-gray-100">{series.metric.job ?? "-"}</td>
                      <td className="py-2 pr-4 break-all text-gray-100">{series.metric.instance ?? "-"}</td>
                      <td className="py-2 text-gray-100">{series.value[1]}</td>
                    </tr>
                  ))}
                  {(upResult.data.data?.result ?? []).length === 0 && (
                    <tr>
                      <td colSpan={3} className="py-4 text-gray-500">
                        no series returned
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
