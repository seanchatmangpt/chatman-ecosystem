import Nav from "@/components/Nav";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
  if (percent === null) return "bg-muted-foreground/40";
  if (percent >= 90) return "bg-red-500";
  if (percent >= 70) return "bg-amber-500";
  return "bg-emerald-500";
}

function UsageBar({ percent }: { percent: number | null }) {
  if (percent === null) {
    return <span className="text-xs text-muted-foreground">no quota set</span>;
  }
  const clampedWidth = Math.min(100, Math.max(0, percent));
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-32 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full ${barColor(percent)}`}
          style={{ width: `${clampedWidth}%` }}
        />
      </div>
      <span className="w-14 text-right text-xs text-muted-foreground">
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
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Cost &amp; Usage</h1>

        <Alert className="mb-6 border-blue-900 bg-blue-950/30 text-blue-200">
          <AlertDescription className="text-blue-200">
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

        {errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {errors.map((e) => (
              <Alert key={e.namespace} variant="destructive">
                <AlertDescription>
                  {e.namespace}: {e.error}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {clusterConfigured && rows.length > 0 && (
          <p className="mb-4 text-xs text-muted-foreground">
            Cluster-wide across these {rows.length} namespaces: real live
            total {formatCpu(totalCpu)} CPU / {formatMemory(totalMemory)}{" "}
            memory in use right now.
          </p>
        )}

        <Card className="overflow-x-auto">
          <Table className="min-w-[900px]">
            <TableHeader>
              <TableRow>
                <TableHead>Namespace</TableHead>
                <TableHead>CPU usage</TableHead>
                <TableHead>CPU quota (limits.cpu)</TableHead>
                <TableHead>CPU % of quota</TableHead>
                <TableHead>Memory usage</TableHead>
                <TableHead>Memory quota (limits.memory)</TableHead>
                <TableHead>Memory % of quota</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="py-6 text-sm text-muted-foreground">
                    {clusterConfigured ? "No namespaces measured." : "—"}
                  </TableCell>
                </TableRow>
              )}
              {rows.map(({ namespace, usage }) => (
                <TableRow key={namespace}>
                  <TableCell className="text-foreground">
                    <code>{namespace}</code>
                    {usage.podsMeasured === 0 && (
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        no pods with a fresh metrics-server reading
                      </p>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatCpu(usage.cpuUsageMillicores)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {usage.quota?.hardCpuMillicores !== null &&
                    usage.quota?.hardCpuMillicores !== undefined
                      ? formatCpu(usage.quota.hardCpuMillicores)
                      : usage.quota
                        ? "—"
                        : "no quota"}
                  </TableCell>
                  <TableCell>
                    <UsageBar percent={usage.cpuPercentOfQuota} />
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatMemory(usage.memoryUsageMiB)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {usage.quota?.hardMemoryMiB !== null &&
                    usage.quota?.hardMemoryMiB !== undefined
                      ? formatMemory(usage.quota.hardMemoryMiB)
                      : usage.quota
                        ? "—"
                        : "no quota"}
                  </TableCell>
                  <TableCell>
                    <UsageBar percent={usage.memoryPercentOfQuota} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>

        <p className="mt-4 text-xs text-muted-foreground">
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
