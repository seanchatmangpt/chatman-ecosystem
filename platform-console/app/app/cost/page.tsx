import Nav from "@/components/Nav";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import CostExportButton, { type CostExportRow } from "@/components/CostExportButton";
import { getCostDashboardRows, getCostTrend, type BudgetStatus } from "@/lib/cost";
import { ILLUSTRATIVE_RATES } from "@/lib/invoice-preview";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Same platform-namespace roster as /usage, /billing, /budget-alerts, plus
// istio-system -- where ocel-accumulator and the OTel Collector actually run
// (see lib/ocel-log.ts, k8s/otel-collector.yaml, k8s/ocel-accumulator.yaml).
// Without this entry those two real workloads' CPU/memory never appeared in
// the cost dashboard even though getCostDashboardRows/getCostTrend already
// resolve any namespace given to them via real Prometheus queries.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
  "istio-system",
];

const WINDOW_LABEL = "1h";
const WINDOW_HOURS = 1;

function formatUsd(amount: number | null): string {
  if (amount === null) return "—";
  return `$${amount.toFixed(4)}`;
}

function StatusChip({ status }: { status: BudgetStatus }) {
  switch (status) {
    case "over":
      return <Badge variant="destructive">over budget</Badge>;
    case "ok":
      return (
        <Badge variant="secondary" className="bg-emerald-950/60 text-emerald-300">
          within budget
        </Badge>
      );
    case "unknown":
      return <Badge variant="outline">budget check failed</Badge>;
    case "no-budget":
    default:
      return <Badge variant="outline">no budget set</Badge>;
  }
}

export default async function CostPage() {
  const clusterConfigured = hasClusterCredentials();

  const dashboard = clusterConfigured
    ? await getCostDashboardRows(PLATFORM_NAMESPACES, WINDOW_LABEL, WINDOW_HOURS)
    : null;
  const trend = clusterConfigured ? await getCostTrend(PLATFORM_NAMESPACES) : null;

  const maxTrendCost = trend ? Math.max(0.000001, ...trend.map((p) => p.totalCost)) : 1;

  const exportRows: CostExportRow[] = (dashboard?.rows ?? []).map((r) => ({
    namespace: r.namespace,
    cpuCoreHours: r.lineItem?.cpuCoreHours ?? null,
    memoryGiBHours: r.lineItem?.memoryGiBHours ?? null,
    totalCost: r.lineItem?.totalCost ?? null,
    budgetThreshold: r.budget?.threshold ?? null,
    status: r.status,
  }));

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-foreground">Cost</h1>
          {dashboard && dashboard.rows.length > 0 && (
            <CostExportButton rows={exportRows} windowLabel={WINDOW_LABEL} />
          )}
        </div>

        <Alert className="mb-6 border-blue-900 bg-blue-950/30 text-blue-200">
          <AlertDescription className="text-blue-200">
            <strong>QBR-ready cost screen: purely a presentation layer, no new billing math.</strong>{" "}
            Every dollar figure below is the exact same real arithmetic{" "}
            <code>/billing</code> already computes and the{" "}
            <code>usage-billing-math-verified-real</code> evidence control already
            verifies (real CPU-core-hours / memory-GiB-hours from this cluster&apos;s
            own Prometheus x the illustrative rate table{" "}
            <code>${ILLUSTRATIVE_RATES.cpuPerCoreHour}/CPU-core-hour</code>,{" "}
            <code>${ILLUSTRATIVE_RATES.memoryPerGiBHour}/GiB-hour</code>). Budget
            status chips reuse the exact same threshold-crossing check{" "}
            <code>/budget-alerts</code> and the{" "}
            <code>budget-alert-fires-once-on-real-threshold-crossing</code> control
            already verify -- this page only renders that status, it does not
            recompute it. No payment processor is connected anywhere in this
            platform; these are illustrative dollars over real infrastructure
            consumption, the AWS Cost Explorer / GCP Billing / Azure Cost
            Management equivalent screen.
          </AlertDescription>
        </Alert>

        {!clusterConfigured && (
          <Alert className="mb-6 border-amber-900 bg-amber-950/40 text-amber-300">
            <AlertDescription className="text-amber-300">
              not configured: no in-cluster ServiceAccount credentials found.
              This page only returns real data when running as the
              platform-console pod.
            </AlertDescription>
          </Alert>
        )}

        {dashboard && dashboard.errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {dashboard.errors.map((e) => (
              <Alert key={e.namespace} variant="destructive">
                <AlertDescription>
                  {e.namespace}: {e.error}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {dashboard && dashboard.rows.length > 0 && (
          <p className="mb-4 text-xs text-muted-foreground">
            Window: last {WINDOW_LABEL}, generated{" "}
            {new Date(dashboard.generatedAt).toLocaleString()}. Total current-period
            spend across {dashboard.rows.length} namespaces:{" "}
            <span className="font-medium text-foreground">
              {formatUsd(dashboard.totalCost)}
            </span>{" "}
            (illustrative).
          </p>
        )}

        <h2 className="mb-2 mt-8 text-sm font-medium text-foreground">
          Current-period spend by namespace, vs. budget
        </h2>
        <Card className="overflow-x-auto">
          <Table className="min-w-[900px]">
            <TableHeader>
              <TableRow>
                <TableHead>Namespace</TableHead>
                <TableHead>Spend ({WINDOW_LABEL}, illustrative)</TableHead>
                <TableHead>Share of total</TableHead>
                <TableHead>Budget threshold (cost-usd)</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(!dashboard || dashboard.rows.length === 0) && (
                <TableRow>
                  <TableCell colSpan={5} className="py-6 text-sm text-muted-foreground">
                    {clusterConfigured ? "No namespaces measured." : "—"}
                  </TableCell>
                </TableRow>
              )}
              {dashboard?.rows.map((r) => {
                const cost = r.lineItem?.totalCost ?? null;
                const share =
                  cost !== null && dashboard.totalCost > 0
                    ? (cost / dashboard.totalCost) * 100
                    : null;
                return (
                  <TableRow key={r.namespace}>
                    <TableCell className="text-foreground">
                      <code>{r.namespace}</code>
                    </TableCell>
                    <TableCell className="font-medium text-foreground">
                      {formatUsd(cost)}
                    </TableCell>
                    <TableCell>
                      {share !== null ? (
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
                            <div
                              className="h-full bg-sky-500"
                              style={{ width: `${Math.min(100, Math.max(0, share))}%` }}
                            />
                          </div>
                          <span className="w-12 text-right text-xs text-muted-foreground">
                            {share.toFixed(1)}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {r.budget ? formatUsd(r.budget.threshold) : "—"}
                    </TableCell>
                    <TableCell>
                      <StatusChip status={r.status} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
            {dashboard && dashboard.rows.length > 0 && (
              <tfoot>
                <TableRow>
                  <TableCell colSpan={1} className="text-right font-medium text-foreground">
                    Total (illustrative)
                  </TableCell>
                  <TableCell className="font-semibold text-foreground">
                    {formatUsd(dashboard.totalCost)}
                  </TableCell>
                  <TableCell colSpan={3} />
                </TableRow>
              </tfoot>
            )}
          </Table>
        </Card>

        <h2 className="mb-2 mt-8 text-sm font-medium text-foreground">
          Trend: real cumulative trailing spend, across all namespaces
        </h2>
        <p className="mb-3 text-xs text-muted-foreground">
          Each bar is an independent, live query ending now (e.g. &quot;real spend
          accrued in the last 6h&quot;), not a discrete calendar period -- this
          cluster keeps no persisted monthly billing history to draw one from. Read
          this directionally (is trailing spend accelerating as the window widens
          faster than the window itself grows), not as month-over-month actuals.
        </p>
        <Card className="p-4">
          {trend && trend.length > 0 ? (
            <div className="flex items-end gap-6" style={{ height: 160 }}>
              {trend.map((p) => (
                <div key={p.windowLabel} className="flex flex-1 flex-col items-center gap-2">
                  <div className="flex h-full w-full items-end">
                    <div
                      className="w-full rounded-t bg-sky-500"
                      style={{
                        height: `${Math.max(2, (p.totalCost / maxTrendCost) * 100)}%`,
                      }}
                      title={formatUsd(p.totalCost)}
                    />
                  </div>
                  <span className="text-xs font-medium text-foreground">
                    {formatUsd(p.totalCost)}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    trailing {p.windowLabel}
                  </span>
                  {p.errors.length > 0 && (
                    <span className="text-[10px] text-red-400">
                      {p.errors.length} namespace query error(s)
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="py-6 text-sm text-muted-foreground">
              {clusterConfigured ? "No trend data." : "—"}
            </p>
          )}
        </Card>

        <p className="mt-4 text-xs text-muted-foreground">
          All figures sourced from <code>lib/invoice-preview.ts</code> (real
          Prometheus <code>increase()</code>/<code>avg_over_time()</code> over{" "}
          <code>container_cpu_usage_seconds_total</code> /{" "}
          <code>container_memory_working_set_bytes</code>) and{" "}
          <code>lib/budget-alerts.ts</code> (real ConfigMap-persisted thresholds
          and threshold-crossing checks). See <code>lib/cost.ts</code> for the
          exact join/reshape this page applies -- no independent calculation
          exists here.
        </p>
      </main>
    </>
  );
}
