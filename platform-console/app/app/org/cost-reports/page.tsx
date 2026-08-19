"use client";

import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import type { CostReportSnapshot } from "@/lib/cost-report-history";

// Real cost & usage report snapshot trend page for this deployment's one
// real single-tenant org -- same "platform-console" fallback convention
// app/org/compliance/page.tsx and app/org/sla/page.tsx already use.
// Client component (same shape as app/orgs/[id]/export-subscription/
// page.tsx): fetches GET /api/orgs/[id]/cost-reports, which itself
// enforces the real viewer-role gate server-side -- this page renders
// whatever that route returns (including its own 401/403 JSON error),
// never a client-side-only access check.
const ORG_ID = "platform-console";

function toCsv(snapshots: CostReportSnapshot[]): string {
  const header = [
    "namespace",
    "windowStart",
    "windowEnd",
    "cpuCoreHours",
    "memoryGiBHours",
    "illustrativeCost",
    "capturedAt",
  ];
  const rows = snapshots.map((s) =>
    [
      s.namespace,
      s.windowStart,
      s.windowEnd,
      s.cpuCoreHours.toFixed(6),
      s.memoryGiBHours.toFixed(6),
      s.illustrativeCost.toFixed(4),
      s.capturedAt,
    ].join(","),
  );
  return [header.join(","), ...rows].join("\n");
}

export default function CostReportsPage() {
  const [snapshots, setSnapshots] = useState<CostReportSnapshot[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(ORG_ID)}/cost-reports`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setSnapshots(body.snapshots as CostReportSnapshot[]);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  function handleDownloadCsv() {
    if (!snapshots || snapshots.length === 0) return;
    const csv = toCsv(snapshots);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${ORG_ID}-cost-reports.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  const maxCost = snapshots ? Math.max(0, ...snapshots.map((s) => s.illustrativeCost)) : 0;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Cost &amp; usage report snapshots</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          A real, persisted history of this org&apos;s metered usage and illustrative cost -- each
          row is one point-in-time snapshot captured by the{" "}
          <code>cost-report-snapshot</code> Scheduled Job (see <code>/scheduled-jobs</code>),
          computed from the exact same live Prometheus-metered CPU-core-hours /
          memory-GiB-hours figures the on-demand cost preview already exposes, applied against
          the same explicitly-illustrative rate table. Stored in the real{" "}
          <code>platform-console-cost-reports</code> ConfigMap (<code>platform-console</code>{" "}
          namespace), capped at the most recent 200 snapshots per namespace.
        </p>

        {error && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {loading && <p className="text-sm text-gray-400">Loading...</p>}

        {!loading && snapshots && snapshots.length === 0 && (
          <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
            No snapshots captured yet. Create a <code>cost-report-snapshot</code> Scheduled Job on
            this namespace at <code>/scheduled-jobs</code> to start building history.
          </p>
        )}

        {!loading && snapshots && snapshots.length > 0 && (
          <>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-gray-400">
                {snapshots.length} snapshot{snapshots.length === 1 ? "" : "s"}
              </p>
              <button
                type="button"
                onClick={handleDownloadCsv}
                className="rounded-md border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm text-gray-200 hover:bg-gray-800"
              >
                Download CSV
              </button>
            </div>

            <div className="mb-6 flex items-end gap-1 rounded-md border border-gray-800 bg-gray-900/40 p-4" style={{ height: 140 }}>
              {snapshots.map((s) => (
                <div
                  key={s.capturedAt}
                  title={`${s.capturedAt}: $${s.illustrativeCost.toFixed(4)}`}
                  className="flex-1 rounded-t bg-emerald-700/70"
                  style={{
                    height: maxCost > 0 ? `${Math.max(2, (s.illustrativeCost / maxCost) * 100)}%` : "2%",
                  }}
                />
              ))}
            </div>

            <div className="overflow-x-auto rounded-md border border-gray-800">
              <table className="min-w-full divide-y divide-gray-800 text-sm">
                <thead className="bg-gray-900/60 text-left text-gray-400">
                  <tr>
                    <th className="px-4 py-2 font-medium">Captured at</th>
                    <th className="px-4 py-2 font-medium">Window</th>
                    <th className="px-4 py-2 font-medium">CPU core-hours</th>
                    <th className="px-4 py-2 font-medium">Memory GiB-hours</th>
                    <th className="px-4 py-2 font-medium">Illustrative cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {snapshots
                    .slice()
                    .reverse()
                    .map((s) => (
                      <tr key={s.capturedAt} className="text-gray-200">
                        <td className="px-4 py-2 text-gray-400">{new Date(s.capturedAt).toLocaleString()}</td>
                        <td className="px-4 py-2 text-gray-400">
                          {new Date(s.windowStart).toLocaleString()} &rarr;{" "}
                          {new Date(s.windowEnd).toLocaleString()}
                        </td>
                        <td className="px-4 py-2">{s.cpuCoreHours.toFixed(4)}</td>
                        <td className="px-4 py-2">{s.memoryGiBHours.toFixed(4)}</td>
                        <td className="px-4 py-2 font-medium text-emerald-300">
                          ${s.illustrativeCost.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </>
  );
}
