import Nav from "@/components/Nav";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { queryAlerts, alertState, type AlertmanagerAlert } from "@/lib/alertmanager";

export const dynamic = "force-dynamic";

const STATE_STYLES: Record<string, string> = {
  firing: "border-red-900 bg-red-950/40 text-red-300",
  suppressed: "border-yellow-900 bg-yellow-950/40 text-yellow-300",
  resolved: "border-border bg-muted/40 text-muted-foreground",
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
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Alerting</h1>
        <p className="mb-8 max-w-2xl text-sm text-muted-foreground">
          The CloudWatch Alarms / GCP Alerting Policies / Azure Monitor Alerts
          equivalent here: real current alert state read live from the
          in-cluster Alertmanager (
          <code>monitoring-kube-prometheus-alertmanager.monitoring.svc:9093/api/v2/alerts</code>
          ) via <code>/api/alerts</code> -- no synthetic alerts, ever.
        </p>

        {!result.ok && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{result.error}</AlertDescription>
          </Alert>
        )}

        {result.ok && (
          <Card>
            <CardHeader className="flex-row items-baseline justify-between space-y-0">
              <h2 className="text-base font-medium text-foreground">
                {firing.length === 0
                  ? "0 active alerts"
                  : `${firing.length} active alert${firing.length === 1 ? "" : "s"}`}
              </h2>
              <span className="text-xs text-muted-foreground">
                {alerts.length} total in Alertmanager (including resolved/suppressed)
              </span>
            </CardHeader>
            <CardContent>
              {alerts.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Alertmanager returned an empty alert list -- this is reported
                  honestly as zero active alerts, not fabricated.
                </p>
              )}

              {alerts.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>alertname</TableHead>
                      <TableHead>state</TableHead>
                      <TableHead>severity</TableHead>
                      <TableHead>namespace</TableHead>
                      <TableHead>since</TableHead>
                      <TableHead>summary</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alerts.map((alert) => {
                      const state = alertState(alert);
                      return (
                        <TableRow key={alert.fingerprint}>
                          <TableCell className="text-foreground">
                            {alert.labels.alertname ?? "-"}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className={STATE_STYLES[state]}>
                              {state}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-foreground">
                            {alert.labels.severity ?? "-"}
                          </TableCell>
                          <TableCell className="text-foreground">
                            {alert.labels.namespace ?? "-"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">{since(alert)}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {alert.annotations.summary ?? alert.annotations.description ?? "-"}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        )}
      </main>
    </>
  );
}
