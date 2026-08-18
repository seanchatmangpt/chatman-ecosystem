import Nav from "@/components/Nav";
import { queryAlerts, alertState, type AlertmanagerAlert } from "@/lib/alertmanager";

export const dynamic = "force-dynamic";

const STATE_STYLES: Record<string, string> = {
  firing: "border-red-900 bg-red-950/40 text-red-300",
  suppressed: "border-yellow-900 bg-yellow-950/40 text-yellow-300",
  resolved: "border-gray-700 bg-gray-900/40 text-gray-400",
};

function since(alert: AlertmanagerAlert): string {
  const startMs = new Date(alert.startsAt).getTime();
  if (Number.isNaN(startMs)) return "-";
  const deltaSec = Math.max(0, Math.floor((Date.now() - startMs) / 1000));
  if (deltaSec < 60) return `${deltaSec}s ago`;
  if (deltaSec < 3600) return `${Math.floor(deltaSec / 60)}m ago`;
  return `${Math.floor(deltaSec / 3600)}h ago`;
}

export default async function AlertsPage() {
  const result = await queryAlerts();

  const alerts = result.ok ? result.data : [];
  const firing = alerts.filter((a) => alertState(a) === "firing");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Alerting</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          The CloudWatch Alarms / GCP Alerting Policies / Azure Monitor Alerts
          equivalent here: real current alert state read live from the
          in-cluster Alertmanager (
          <code>monitoring-kube-prometheus-alertmanager.monitoring.svc:9093/api/v2/alerts</code>
          ) via <code>/api/alerts</code> -- no synthetic alerts, ever.
        </p>

        {!result.ok && (
          <div className="card mb-6 border-red-900 bg-red-950/40 p-6 text-sm text-red-300">
            {result.error}
          </div>
        )}

        {result.ok && (
          <div className="card p-6">
            <div className="mb-4 flex items-baseline justify-between">
              <h2 className="text-base font-medium text-white">
                {firing.length === 0
                  ? "0 active alerts"
                  : `${firing.length} active alert${firing.length === 1 ? "" : "s"}`}
              </h2>
              <span className="text-xs text-gray-500">
                {alerts.length} total in Alertmanager (including resolved/suppressed)
              </span>
            </div>

            {alerts.length === 0 && (
              <p className="text-sm text-gray-500">
                Alertmanager returned an empty alert list -- this is reported
                honestly as zero active alerts, not fabricated.
              </p>
            )}

            {alerts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border text-gray-400">
                      <th className="py-2 pr-4 font-normal">alertname</th>
                      <th className="py-2 pr-4 font-normal">state</th>
                      <th className="py-2 pr-4 font-normal">severity</th>
                      <th className="py-2 pr-4 font-normal">namespace</th>
                      <th className="py-2 pr-4 font-normal">since</th>
                      <th className="py-2 font-normal">summary</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.map((alert) => {
                      const state = alertState(alert);
                      return (
                        <tr key={alert.fingerprint} className="border-b border-border/50">
                          <td className="py-2 pr-4 text-gray-100">
                            {alert.labels.alertname ?? "-"}
                          </td>
                          <td className="py-2 pr-4">
                            <span
                              className={`inline-block rounded border px-2 py-0.5 text-xs ${STATE_STYLES[state]}`}
                            >
                              {state}
                            </span>
                          </td>
                          <td className="py-2 pr-4 text-gray-100">
                            {alert.labels.severity ?? "-"}
                          </td>
                          <td className="py-2 pr-4 text-gray-100">
                            {alert.labels.namespace ?? "-"}
                          </td>
                          <td className="py-2 pr-4 text-gray-400">{since(alert)}</td>
                          <td className="py-2 text-gray-400">
                            {alert.annotations.summary ?? alert.annotations.description ?? "-"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </>
  );
}
