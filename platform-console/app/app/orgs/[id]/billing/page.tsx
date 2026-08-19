import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import SpendHistoryChart from "@/components/SpendHistoryChart";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import { estimateNamespaceOverage } from "@/lib/overage-billing";

export const dynamic = "force-dynamic";

// Real customer-facing, org-scoped billing dashboard: this org's current
// point-in-time overage estimate (lib/overage-billing.ts's
// estimateNamespaceOverage -- the same real Prometheus-usage-vs-tier-
// baseline arithmetic app/billing/page.tsx's platform-wide overage
// widget shows, scoped to just this org's own namespace) alongside the
// new historical, exportable spend/usage time series
// (SpendHistoryChart, GET /api/orgs/[id]/billing/spend-history) --
// closing the "show me 12 months of spend trend, not just today's
// estimate" gap Fortune 5 FinOps procurement asks for. Gated the same
// way every other /orgs/[id]/* page in this app is: a server-side
// requireRoleIn(viewer) check before rendering, re-checked independently
// by every underlying route handler regardless of what this page shows.

export default async function OrgBillingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const orgResult = await getOrg(id);
  if (!orgResult.ok || !orgResult.data) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {orgResult.ok ? "org not found" : orgResult.error}
          </p>
        </main>
      </>
    );
  }
  const org = orgResult.data;

  const viewerAccess = await requireRoleIn(session, org.namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Billing</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          {org.name} -- current overage estimate plus historical spend trend, reconciled against
          real Stripe invoice history and real metered usage.
        </p>

        {!viewerAccess.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{viewerAccess.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this org&apos;s billing.
            </p>
          </div>
        )}

        {viewerAccess.ok && (
          <div className="space-y-6">
            <OverageEstimateCard namespace={org.namespace} clusterConfigured={clusterConfigured} />
            <SpendHistoryChart orgId={org.id} />
          </div>
        )}
      </main>
    </>
  );
}

async function OverageEstimateCard({
  namespace,
  clusterConfigured,
}: {
  namespace: string;
  clusterConfigured: boolean;
}) {
  if (!clusterConfigured) {
    return (
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        not configured: no in-cluster ServiceAccount credentials found. The overage estimate only
        returns real data when running as the platform-console pod.
      </div>
    );
  }

  const estimate = await estimateNamespaceOverage(namespace);

  return (
    <div className="rounded-md border border-gray-800 bg-gray-900/20 p-5">
      <h3 className="mb-1 text-sm font-semibold text-white">Current overage estimate</h3>
      <p className="mb-3 text-xs text-gray-500">
        Real CPU-core-hours/memory-GiB-hours consumed above this org&apos;s tier baseline over the
        trailing {estimate.ok ? estimate.data.windowLabel : "24h"} -- a point-in-time snapshot, not
        a bill. See the spend history below for the reconciled, exportable trend.
      </p>
      {!estimate.ok && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {estimate.error}
        </p>
      )}
      {estimate.ok && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-gray-500">Tier</p>
            <p className="mt-1 text-lg font-semibold text-white">{estimate.data.tier}</p>
          </div>
          <div className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-gray-500">CPU overage</p>
            <p className="mt-1 text-lg font-semibold text-white">
              {estimate.data.cpuCoreHoursOverage.toFixed(4)} core-hrs
            </p>
          </div>
          <div className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-gray-500">Memory overage</p>
            <p className="mt-1 text-lg font-semibold text-white">
              {estimate.data.memoryGiBHoursOverage.toFixed(4)} GiB-hrs
            </p>
          </div>
          <div className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-gray-500">Overage this period</p>
            <p className="mt-1 text-lg font-semibold text-white">
              ${estimate.data.overageCostUsd.toFixed(4)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
