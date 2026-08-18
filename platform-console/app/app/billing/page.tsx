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
import { getInvoicePreview, ILLUSTRATIVE_RATES } from "@/lib/invoice-preview";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Same platform-namespace roster as /usage (app/usage/page.tsx) and
// /registry, /logs -- the 4 project namespaces, supabase-demo, and
// platform-console's own namespace.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

// How far back the illustrative preview looks. Kept short (1h) because
// this cluster's Prometheus has been running for a few hours, not weeks --
// a longer window would silently degrade to whatever real history exists
// rather than the requested window; PromQL just returns fewer real samples
// for the parts of the window before Prometheus started scraping.
const WINDOW_LABEL = "1h";
const WINDOW_HOURS = 1;

function formatUsd(amount: number): string {
  return `$${amount.toFixed(4)}`;
}

export default async function BillingPage() {
  const clusterConfigured = hasClusterCredentials();

  const preview = clusterConfigured
    ? await getInvoicePreview(PLATFORM_NAMESPACES, WINDOW_LABEL, WINDOW_HOURS)
    : null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Billing</h1>

        <Alert className="mb-6 border-blue-900 bg-blue-950/30 text-blue-200">
          <AlertDescription className="text-blue-200">
            <strong>Illustrative cost calculation from real resource metrics.</strong>{" "}
            Not an invoice. No payment method is connected -- this platform
            never collects payment information. Line items below are real
            arithmetic (real accumulated CPU-core-hours and memory-GiB-hours,
            computed live from this cluster&apos;s own Prometheus over the
            last {WINDOW_LABEL}) multiplied by a fixed illustrative rate
            table (<code>${ILLUSTRATIVE_RATES.cpuPerCoreHour}/CPU-core-hour</code>,{" "}
            <code>${ILLUSTRATIVE_RATES.memoryPerGiBHour}/GiB-hour</code>) --
            arbitrary numbers chosen to demonstrate the calculation, not a
            real contracted price. The AWS Cost Explorer &quot;forecasted
            bill&quot; / GCP Billing cost-breakdown equivalent, grounded in
            the same measured infrastructure consumption <code>/usage</code>{" "}
            shows, with a plain rate table applied on top -- still no
            currency actually changes hands anywhere in this platform.
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

        {preview && preview.errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {preview.errors.map((e) => (
              <Alert key={e.namespace} variant="destructive">
                <AlertDescription>
                  {e.namespace}: {e.error}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {preview && preview.lineItems.length > 0 && (
          <p className="mb-4 text-xs text-muted-foreground">
            Window: last {preview.windowLabel}, generated{" "}
            {new Date(preview.generatedAt).toLocaleString()}. Rate table:{" "}
            {formatUsd(preview.rates.cpuPerCoreHour)}/CPU-core-hour,{" "}
            {formatUsd(preview.rates.memoryPerGiBHour)}/GiB-hour (illustrative).
          </p>
        )}

        <Card className="overflow-x-auto">
          <Table className="min-w-[900px]">
            <TableHeader>
              <TableRow>
                <TableHead>Namespace</TableHead>
                <TableHead>CPU-core-hours (real)</TableHead>
                <TableHead>CPU cost (illustrative)</TableHead>
                <TableHead>Memory-GiB-hours (real)</TableHead>
                <TableHead>Memory cost (illustrative)</TableHead>
                <TableHead>Line total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(!preview || preview.lineItems.length === 0) && (
                <TableRow>
                  <TableCell colSpan={6} className="py-6 text-sm text-muted-foreground">
                    {clusterConfigured ? "No namespaces measured." : "—"}
                  </TableCell>
                </TableRow>
              )}
              {preview?.lineItems.map((li) => (
                <TableRow key={li.namespace}>
                  <TableCell className="text-foreground">
                    <code>{li.namespace}</code>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {li.cpuCoreHours.toFixed(6)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatUsd(li.cpuCost)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {li.memoryGiBHours.toFixed(6)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatUsd(li.memoryCost)}
                  </TableCell>
                  <TableCell className="font-medium text-foreground">
                    {formatUsd(li.totalCost)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
            {preview && preview.lineItems.length > 0 && (
              <tfoot>
                <TableRow>
                  <TableCell colSpan={5} className="text-right font-medium text-foreground">
                    Total (illustrative)
                  </TableCell>
                  <TableCell className="font-semibold text-foreground">
                    {formatUsd(preview.totalCost)}
                  </TableCell>
                </TableRow>
              </tfoot>
            )}
          </Table>
        </Card>

        <p className="mt-4 text-xs text-muted-foreground">
          CPU-core-hours = real <code>increase()</code> of the cumulative{" "}
          <code>container_cpu_usage_seconds_total</code> cAdvisor counter
          over the window, summed across every real container in the
          namespace, /3600. Memory-GiB-hours = real{" "}
          <code>avg_over_time()</code> of{" "}
          <code>container_memory_working_set_bytes</code> over the window
          (the real time-weighted average working set), x the window&apos;s
          own duration in hours. Both read from this cluster&apos;s real
          in-cluster Prometheus -- same instance <code>/observability</code>{" "}
          and <code>/usage</code> read. See <code>lib/invoice-preview.ts</code>{" "}
          for the exact PromQL and arithmetic.
        </p>
      </main>
    </>
  );
}
