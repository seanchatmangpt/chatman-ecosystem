import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import { listResidencyAttestations, type ResidencyAttestation } from "@/lib/data-residency-attestation";

export const dynamic = "force-dynamic";

// Real Scheduled Data-Residency Compliance Attestation history page for
// this deployment's one real single-tenant org -- same "platform-console"
// single-tenant fallback convention app/org/compliance/page.tsx already
// uses for its own sibling report. Server component gates rendering the
// same way: a non-member sees a real 403 message, not the table; the
// actual scan-now mutation (POST) is re-checked by the API route
// regardless of what this page renders.
const ORG_ID = "platform-console";

function DriftBadge({ count }: { count: number }) {
  const clean = count === 0;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs ${
        clean
          ? "border-emerald-900 bg-emerald-950/40 text-emerald-300"
          : "border-red-900 bg-red-950/40 text-red-300"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${clean ? "bg-emerald-500" : "bg-red-500"}`} />
      {clean ? "no drift" : `${count} drift event${count === 1 ? "" : "s"}`}
    </span>
  );
}

function AttestationRow({ attestation }: { attestation: ResidencyAttestation }) {
  return (
    <div className="border-b border-border py-3 last:border-0">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-sm text-white">{attestation.period}</p>
          <p className="text-xs text-gray-500">
            region <code>{attestation.region}</code> &middot; {attestation.workloadsChecked} workload
            {attestation.workloadsChecked === 1 ? "" : "s"} checked &middot; attested{" "}
            {attestation.attestedAt}
          </p>
        </div>
        <DriftBadge count={attestation.driftCount} />
      </div>
      {attestation.driftEvents.length > 0 && (
        <div className="mt-2 overflow-x-auto rounded-md border border-red-900/60 bg-red-950/20">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-red-900/40 text-red-300/70">
                <th className="px-3 py-1.5 font-normal">pod</th>
                <th className="px-3 py-1.5 font-normal">node</th>
                <th className="px-3 py-1.5 font-normal">actual region</th>
                <th className="px-3 py-1.5 font-normal">expected region</th>
              </tr>
            </thead>
            <tbody>
              {attestation.driftEvents.map((e, i) => (
                <tr key={i} className="border-b border-red-900/20 text-red-200 last:border-0">
                  <td className="px-3 py-1.5 font-mono">{e.podName}</td>
                  <td className="px-3 py-1.5 font-mono">{e.nodeName ?? "(unscheduled)"}</td>
                  <td className="px-3 py-1.5 font-mono">{e.actualRegion ?? "(unlabeled)"}</td>
                  <td className="px-3 py-1.5 font-mono">{e.expectedRegion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default async function OrgResidencyAttestationPage() {
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
  const region = orgResult.ok && orgResult.data ? orgResult.data.region ?? null : null;

  const viewerAccess = await requireRoleIn(session, namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">
          Data-residency compliance attestation
        </h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          A real, periodic, immutable proof that this org&apos;s region pinning{" "}
          <em>held</em> over each audit period -- not just a point-in-time label check. Each row
          below is one real scan (<code>lib/data-residency-attestation.ts</code>) comparing every
          live Pod&apos;s actual scheduled node region against the org&apos;s pinned region,
          persisted append-only to <code>platform_console.residency_attestations</code> so a
          clean-history claim is provable from the row history itself, not a mutable status flag.
          Distinct from the general{" "}
          <a href="/org/compliance" className="underline hover:text-gray-300">
            scheduled compliance reports
          </a>{" "}
          module, which covers SOC2/access-control evidence, not region-specific drift.
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
              (<code>viewer</code>) to view this org&apos;s residency attestations.
            </p>
          </div>
        )}

        {clusterConfigured && viewerAccess.ok && !region && (
          <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
            This org has no pinned <code>region</code> set -- no residency attestation applies.
            Pin a region at <code>/org/security</code> (or PUT{" "}
            <code>/api/orgs/{ORG_ID}/region</code>) to start building attestation history.
          </p>
        )}

        {clusterConfigured && viewerAccess.ok && region && (
          <AttestationHistoryServerBoundary orgId={ORG_ID} region={region} />
        )}
      </main>
    </>
  );
}

async function AttestationHistoryServerBoundary({
  orgId,
  region,
}: {
  orgId: string;
  region: string;
}) {
  const historyResult = await listResidencyAttestations(orgId);

  if (!historyResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read attestation history: {historyResult.error}
      </p>
    );
  }

  const history = historyResult.data;
  const mostRecent = history[0] ?? null;
  const cleanHistory = history.length > 0 && history.every((a) => a.driftCount === 0);

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Current status</h2>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs text-gray-500">Pinned region</dt>
            <dd className="font-mono text-white">{region}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Attestations recorded</dt>
            <dd className="font-mono text-white">{history.length}</dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Most recent drift count</dt>
            <dd className="font-mono text-white">
              {mostRecent ? mostRecent.driftCount : "no scans yet"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-gray-500">Clean history</dt>
            <dd className="font-mono text-white">
              {history.length === 0 ? "no scans yet" : cleanHistory ? "yes" : "no"}
            </dd>
          </div>
        </dl>
      </div>

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Attestation history</h2>
        {history.length === 0 && (
          <p className="text-sm text-gray-500">
            No attestations scanned yet. A scheduled job authenticated with{" "}
            <code>x-residency-attestation-cron-secret</code>, or a member/owner calling POST{" "}
            <code>/api/orgs/{orgId}/residency-attestations</code> on demand, will record the first
            one.
          </p>
        )}
        {history.length > 0 && (
          <div className="divide-y divide-border">
            {history.map((a) => (
              <AttestationRow key={a.id} attestation={a} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
