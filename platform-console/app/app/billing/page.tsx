import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import ChangePlanButton from "@/components/ChangePlanButton";
import OverageBillButton from "@/components/OverageBillButton";
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
import {
  hasStripeCredentials,
  isStripeTestMode,
  listStoredSubscriptions,
} from "@/lib/stripe-billing";
import { estimateAllNamespaceOverages, OVERAGE_PLATFORM_NAMESPACES } from "@/lib/overage-billing";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { getRoleFor, type Role } from "@/lib/authz";

export const dynamic = "force-dynamic";

const ROLE_RANK: Record<Role, number> = { viewer: 0, member: 1, owner: 2 };

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
  const stripeConfigured = hasStripeCredentials();

  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  const role: Role = session ? await getRoleFor(session) : "viewer";
  const canBillOverage = ROLE_RANK[role] >= ROLE_RANK.owner;

  const preview = clusterConfigured
    ? await getInvoicePreview(PLATFORM_NAMESPACES, WINDOW_LABEL, WINDOW_HOURS)
    : null;

  const subscriptions =
    clusterConfigured && stripeConfigured
      ? await listStoredSubscriptions(PLATFORM_NAMESPACES)
      : null;

  const overage = clusterConfigured
    ? await estimateAllNamespaceOverages(OVERAGE_PLATFORM_NAMESPACES)
    : null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Billing</h1>

        <Card className="mb-6 p-4">
          <h2 className="mb-1 text-sm font-semibold text-foreground">
            Payment provider (Stripe {stripeConfigured && isStripeTestMode() ? "test mode" : "not configured"})
          </h2>
          {!stripeConfigured && (
            <p className="text-xs text-muted-foreground">
              No <code>STRIPE_SECRET_KEY</code> configured for this deployment --
              no Stripe Customer/Subscription objects can be created and no real
              payment method can be collected until an operator sets one. This is
              the genuine remaining gap: the illustrative cost table below has
              real usage math behind it, but nothing here charges anyone until a
              Stripe test-mode (or live) key is wired in.
            </p>
          )}
          {stripeConfigured && !isStripeTestMode() && (
            <p className="text-xs text-amber-400">
              Configured key is not a <code>sk_test_</code> key -- this deployment
              is wired to real Stripe (live mode), not test mode.
            </p>
          )}
          {stripeConfigured && subscriptions && subscriptions.ok && (
            <div className="mt-3 overflow-x-auto">
              <Table className="min-w-[700px]">
                <TableHeader>
                  <TableRow>
                    <TableHead>Tenant namespace</TableHead>
                    <TableHead>Stripe customer</TableHead>
                    <TableHead>Stripe subscription</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last event</TableHead>
                    {canBillOverage && <TableHead>Action</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {PLATFORM_NAMESPACES.map((ns) => {
                    const sub = subscriptions.data[ns];
                    const hasLiveSubscription =
                      sub?.status === "active" || sub?.status === "trialing" || sub?.status === "past_due";
                    return (
                      <TableRow key={ns}>
                        <TableCell className="text-foreground">
                          <code>{ns}</code>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {sub ? <code>{sub.stripeCustomerId}</code> : "—"}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {sub?.stripeSubscriptionId ? <code>{sub.stripeSubscriptionId}</code> : "—"}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {sub?.status ?? "no_subscription"}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {sub?.lastEventType ?? "—"}
                        </TableCell>
                        {canBillOverage && (
                          <TableCell>
                            <ChangePlanButton namespace={ns} />
                            {!hasLiveSubscription && (
                              <p className="mt-1 max-w-[10rem] text-[10px] text-muted-foreground">
                                No live subscription -- this will start one via Checkout.
                              </p>
                            )}
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
          {stripeConfigured && subscriptions && !subscriptions.ok && (
            <Alert variant="destructive" className="mt-3">
              <AlertDescription>{subscriptions.error}</AlertDescription>
            </Alert>
          )}
        </Card>

        <Card className="mb-6 p-4">
          <h2 className="mb-1 text-sm font-semibold text-foreground">
            Overage (usage-based, metered Stripe billing)
          </h2>
          <p className="mb-3 text-xs text-muted-foreground">
            Real CPU-core-hours/memory-GiB-hours consumed above each
            namespace&apos;s <code>TIER_RESOURCE_QUOTAS</code> baseline over
            the trailing {overage?.estimates[0]?.windowLabel ?? "24h"}, at
            the same illustrative rate table as the line items below. Will
            be invoiced on next Stripe cycle once billed -- an owner commits
            a real Stripe InvoiceItem via the button, no automatic charge
            fires from a background poll.
          </p>
          {overage && overage.errors.length > 0 && (
            <div className="mb-3 space-y-2">
              {overage.errors.map((e) => (
                <Alert key={e.namespace} variant="destructive">
                  <AlertDescription>
                    {e.namespace}: {e.error}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}
          {overage && overage.estimates.length > 0 && (
            <div className="overflow-x-auto">
              <Table className="min-w-[900px]">
                <TableHeader>
                  <TableRow>
                    <TableHead>Namespace</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>CPU overage (core-hours)</TableHead>
                    <TableHead>Memory overage (GiB-hours)</TableHead>
                    <TableHead>Overage this period</TableHead>
                    <TableHead>Last invoice item</TableHead>
                    {canBillOverage && <TableHead>Action</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {overage.estimates.map((e) => (
                    <TableRow key={e.namespace}>
                      <TableCell className="text-foreground">
                        <code>{e.namespace}</code>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{e.tier}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {e.cpuCoreHoursOverage.toFixed(6)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {e.memoryGiBHoursOverage.toFixed(6)}
                      </TableCell>
                      <TableCell className="font-medium text-foreground">
                        {formatUsd(e.overageCostUsd)}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {e.stored?.lastInvoiceItemId ? (
                          <code>{e.stored.lastInvoiceItemId}</code>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                      {canBillOverage && (
                        <TableCell>
                          {e.overageCostUsd > 0 && !stripeConfigured ? (
                            <span className="text-[11px] text-muted-foreground">
                              Stripe not configured
                            </span>
                          ) : (
                            <OverageBillButton namespace={e.namespace} />
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          {!overage && (
            <p className="text-xs text-muted-foreground">
              {clusterConfigured ? "No overage data." : "—"}
            </p>
          )}
        </Card>

        <Alert className="mb-6 border-blue-900 bg-blue-950/30 text-blue-200">
          <AlertDescription className="text-blue-200">
            <strong>Illustrative cost calculation from real resource metrics.</strong>{" "}
            Not an invoice. The line items below are not tied to the real
            Stripe subscription state shown above -- that is real Stripe
            test-mode object state; this table remains a separate,
            unbilled usage estimate. Line items below are real
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

        <Card className="mt-6 mb-6 overflow-x-auto">
          <div className="p-4 pb-0">
            <h2 className="mb-1 text-sm font-semibold text-foreground">
              Network egress (real cross-namespace mesh byte metering)
            </h2>
            <p className="mb-3 text-xs text-muted-foreground">
              Real bytes read from this cluster&apos;s live Istio sidecar
              proxies (<code>istio_tcp_sent_bytes_total</code>), for traffic
              that crosses a Kubernetes namespace boundary over the last{" "}
              {preview?.windowLabel ?? WINDOW_LABEL}, x an illustrative{" "}
              <code>${ILLUSTRATIVE_RATES.egressPerGb}/GB</code> rate. Every
              namespace in this cluster runs on one physical host, so this is
              a real, live-measured stand-in for hyperscaler Data Transfer
              Out billing (a shape claim: traffic crossing a billing
              boundary), not a claim of real inter-region/internet egress
              (a scale claim this single-cluster deployment cannot make) --
              see <code>lib/network-usage.ts</code> for the full disclosure.
            </p>
          </div>
          {preview && preview.networkErrors.length > 0 && (
            <div className="px-4 pb-2 space-y-2">
              {preview.networkErrors.map((e) => (
                <Alert key={e.namespace} variant="destructive">
                  <AlertDescription>
                    {e.namespace}: {e.error}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          )}
          <Table className="min-w-[700px]">
            <TableHeader>
              <TableRow>
                <TableHead>Namespace</TableHead>
                <TableHead>Egress bytes (real)</TableHead>
                <TableHead>Egress GB (real)</TableHead>
                <TableHead>Egress cost (illustrative)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(!preview || preview.networkLineItems.length === 0) && (
                <TableRow>
                  <TableCell colSpan={4} className="py-6 text-sm text-muted-foreground">
                    {clusterConfigured ? "No namespaces measured." : "—"}
                  </TableCell>
                </TableRow>
              )}
              {preview?.networkLineItems.map((li) => (
                <TableRow key={li.namespace}>
                  <TableCell className="text-foreground">
                    <code>{li.namespace}</code>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {li.egressBytes.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {li.egressGb.toFixed(6)}
                  </TableCell>
                  <TableCell className="font-medium text-foreground">
                    {formatUsd(li.egressCost)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
            {preview && preview.networkLineItems.length > 0 && (
              <tfoot>
                <TableRow>
                  <TableCell colSpan={3} className="text-right font-medium text-foreground">
                    Total egress (illustrative)
                  </TableCell>
                  <TableCell className="font-semibold text-foreground">
                    {formatUsd(preview.networkTotalCost)}
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
