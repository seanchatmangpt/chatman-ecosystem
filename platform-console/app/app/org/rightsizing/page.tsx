"use client";

import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import type { RightsizingDigest, RightsizingRecommendation } from "@/lib/rightsizing";

// Real reserved-capacity / idle-waste rightsizing digest page for this
// deployment's one real single-tenant org -- same "platform-console"
// fallback convention app/org/cost-reports/page.tsx already uses. Client
// component fetching GET /api/orgs/[id]/rightsizing, which itself enforces
// the real viewer-role gate server-side; this page renders whatever that
// route returns (including its own 401/403/502 JSON error), never a
// client-side-only access check. Computed live on every load -- nothing
// here is persisted, matching lib/rightsizing.ts's own header comment.
const ORG_ID = "platform-console";

function resourceLabel(resource: RightsizingRecommendation["resource"]): string {
  return resource === "cpu" ? "CPU" : "Memory";
}

function formatAmount(resource: RightsizingRecommendation["resource"], amount: number): string {
  return resource === "cpu" ? `${(amount / 1000).toFixed(2)} cores` : `${(amount / 1024).toFixed(2)} GiB`;
}

export default function RightsizingPage() {
  const [digest, setDigest] = useState<RightsizingDigest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(ORG_ID)}/rightsizing`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setDigest(body as RightsizingDigest);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const recommendations = (digest?.results ?? []).flatMap((r) =>
    r.recommendations.map((rec) => ({ ...rec, windowLabel: r.windowLabel })),
  );

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Rightsizing recommendations</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          A real, live comparison of what this org&apos;s namespace currently reserves --
          <code>sum(container.resources.requests)</code> across every live Pod -- against what it
          actually used on average over the trailing window, read from the same live Prometheus
          queries the cost preview already issues. A resource is only flagged here when it has
          been idle by more than {digest ? `${(0.4 * 100).toFixed(0)}%` : "40%"} of its own
          reservation across the whole window -- a momentary dip is not a recommendation.
          Estimated savings use the same explicitly illustrative rate table as the cost preview,
          not a real contracted price. Nothing on this page is persisted; it is recomputed on
          every load.
        </p>

        {error && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {loading && <p className="text-sm text-gray-400">Loading...</p>}

        {!loading && digest && digest.errors.length > 0 && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/30 px-4 py-3 text-sm text-amber-300">
            {digest.errors.map((e) => (
              <p key={e.namespace}>
                {e.namespace}: {e.error}
              </p>
            ))}
          </div>
        )}

        {!loading && digest && (
          <>
            <div className="mb-6 rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3">
              <p className="text-sm text-gray-400">
                Trailing window: <span className="text-gray-200">{digest.windowLabel}</span>
              </p>
              <p className="mt-1 text-2xl font-semibold text-emerald-300">
                ${digest.totalEstimatedMonthlySavingsUsd.toFixed(2)}
                <span className="ml-2 text-sm font-normal text-gray-400">estimated / month</span>
              </p>
            </div>

            {recommendations.length === 0 && (
              <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
                No sustained idle reservation found over the trailing {digest.windowLabel} window --
                this namespace&apos;s live requests are well-matched to its actual usage.
              </p>
            )}

            {recommendations.length > 0 && (
              <div className="overflow-x-auto rounded-md border border-gray-800">
                <table className="min-w-full divide-y divide-gray-800 text-sm">
                  <thead className="bg-gray-900/60 text-left text-gray-400">
                    <tr>
                      <th className="px-4 py-2 font-medium">Namespace</th>
                      <th className="px-4 py-2 font-medium">Resource</th>
                      <th className="px-4 py-2 font-medium">Requested</th>
                      <th className="px-4 py-2 font-medium">Actual avg used</th>
                      <th className="px-4 py-2 font-medium">Idle</th>
                      <th className="px-4 py-2 font-medium">Est. savings / month</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {recommendations.map((rec) => (
                      <tr key={`${rec.namespace}-${rec.resource}`} className="text-gray-200">
                        <td className="px-4 py-2">{rec.namespace}</td>
                        <td className="px-4 py-2">{resourceLabel(rec.resource)}</td>
                        <td className="px-4 py-2">{formatAmount(rec.resource, rec.requestedAmount)}</td>
                        <td className="px-4 py-2">{formatAmount(rec.resource, rec.actualUsedAvg)}</td>
                        <td className="px-4 py-2 text-amber-300">{(rec.idleFraction * 100).toFixed(0)}%</td>
                        <td className="px-4 py-2 font-medium text-emerald-300">
                          ${rec.estimatedMonthlySavingsUsd.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </>
  );
}
