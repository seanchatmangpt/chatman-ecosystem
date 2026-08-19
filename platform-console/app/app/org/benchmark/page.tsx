import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import { getUsageBenchmark, orgMeetsBenchmarkTier, MIN_COHORT_SIZE } from "@/lib/usage-benchmarks";

export const dynamic = "force-dynamic";

// Anonymized Cross-Org Usage Benchmarking Marketplace page, for this
// deployment's one real single-tenant org -- same "platform-console"
// fallback ORG_ID convention app/org/compliance/page.tsx already
// establishes. Server component: every number below is computed live by
// lib/usage-benchmarks.ts at render time (no client fetch, no stale
// cache) via the same real per-org data GET /api/orgs/[id]/usage-benchmark
// serves to a programmatic caller.
const ORG_ID = "platform-console";

export default async function OrgBenchmarkPage() {
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

  const orgResult = await getOrg(ORG_ID);
  const namespace = orgResult.ok && orgResult.data ? orgResult.data.namespace : ORG_ID;

  const viewerAccess = await requireRoleIn(session, namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Cross-org usage benchmarking</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          A real, pro-tier-and-above add-on report (Flexera/CloudHealth, Databricks cost
          benchmarking equivalent): where this org&apos;s real cost-per-pod-hour falls among every
          other org on this platform&apos;s own real, live-computed cost-per-pod-hour, over the
          same trailing window this console&apos;s own cost dashboard already trends. Every other
          org&apos;s name, id, and namespace is stripped before this page ever sees it -- only the
          anonymized numeric percentile band is returned. Cohorts smaller than{" "}
          {MIN_COHORT_SIZE} orgs refuse to answer rather than return a deanonymizable percentile.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only returns
            real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !viewerAccess.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{viewerAccess.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this org&apos;s usage benchmark.
            </p>
          </div>
        )}

        {clusterConfigured && viewerAccess.ok && (
          <BenchmarkPanelServerBoundary orgId={ORG_ID} namespace={namespace} />
        )}
      </main>
    </>
  );
}

async function BenchmarkPanelServerBoundary({
  orgId,
  namespace,
}: {
  orgId: string;
  namespace: string;
}) {
  const tierCheck = await orgMeetsBenchmarkTier(namespace, "pro");
  if (!tierCheck.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read tier: {tierCheck.error}
      </p>
    );
  }
  if (!tierCheck.eligible) {
    return (
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        <p className="font-medium">Pro tier required</p>
        <p className="mt-1 text-amber-300/80">
          Cross-org usage benchmarking is a pro-and-above add-on report. This org&apos;s current
          Project tier is <code>{tierCheck.tier}</code>. Upgrade a Project&apos;s tier to unlock
          this report.
        </p>
      </div>
    );
  }

  const result = await getUsageBenchmark(orgId);
  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to compute benchmark: {result.error}
      </p>
    );
  }

  const benchmark = result.data;

  if (benchmark.insufficientData) {
    return (
      <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
        <p className="font-medium">Insufficient peer data</p>
        <p className="mt-1 text-amber-300/80">
          Only {benchmark.sampleSize} org{benchmark.sampleSize === 1 ? "" : "s"} on this platform
          currently have a real cost-per-pod-hour figure -- fewer than the {benchmark.minRequired}{" "}
          required to publish an anonymized percentile without risking re-identifying a specific
          peer org.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-md border border-gray-800 bg-gray-950/40 px-6 py-6">
        <p className="text-sm text-gray-400">
          You are in the{" "}
          <span className="font-semibold text-white">{benchmark.yourPercentileRank}th</span>{" "}
          percentile of cost-per-pod among orgs on this tier
        </p>
        <p className="mt-2 text-3xl font-semibold text-white">
          ${benchmark.yourValue.toFixed(4)}
          <span className="ml-2 text-base font-normal text-gray-500">/ pod-hour</span>
        </p>
        <p className="mt-1 text-xs text-gray-500">
          trailing {benchmark.windowLabel} window &middot; {benchmark.sampleSize} orgs in cohort
          &middot; generated {benchmark.generatedAt}
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {(
          [
            ["p25", benchmark.p25],
            ["p50 (median)", benchmark.p50],
            ["p75", benchmark.p75],
            ["p90", benchmark.p90],
          ] as const
        ).map(([label, value]) => (
          <div key={label} className="rounded-md border border-gray-800 bg-gray-950/40 px-4 py-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
            <p className="mt-1 text-lg font-semibold text-white">${value.toFixed(4)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
