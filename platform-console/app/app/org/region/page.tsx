"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

interface RegionState {
  region: string | null;
  availableRegions: string[];
  tier: string;
  enterpriseEligible: boolean;
}

// Real data residency / region pinning settings page. Same
// query-param-scoped multi-org routing interim as app/org/branding/page.tsx
// (this app has no session-wide "current org" concept -- see
// lib/session.ts's SessionPayload). Enterprise-tier-gated in the UI to
// match the server-side gate PUT /api/orgs/[id]/region enforces --
// the UI gate is cosmetic (disabled control, explanatory copy), the API
// gate is the real one.
export default function OrgRegionPage() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [state, setState] = useState<RegionState | null>(null);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  function load() {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/region`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        const next: RegionState = {
          region: body.region,
          availableRegions: body.availableRegions,
          tier: body.tier,
          enterpriseEligible: body.enterpriseEligible,
        };
        setState(next);
        setSelectedRegion(next.region ?? next.availableRegions[0] ?? "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, [orgId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId || !selectedRegion) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/region`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ region: selectedRegion }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setSaved(true);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Data residency / region pinning</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Pin this org&apos;s workloads and paired database to a named region for GDPR
          data-localization or US financial data-residency compliance. When set, every new
          Project and its paired database are scheduled with a real
          <code> nodeSelector: {"{"}topology.kubernetes.io/region: &lt;region&gt;{"}"}</code> --
          a genuine, k8s-scheduler-enforced constraint. A Pod that cannot be scheduled in the
          pinned region stays honestly Pending, not silently placed elsewhere. Enterprise-tier
          only, owner-only -- enforced server-side by{" "}
          <code>PUT /api/orgs/[id]/region</code>, not just this page.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to manage that
            org&apos;s region pin (org ids are returned by <code>POST /api/orgs</code> and
            listed by <code>GET /api/orgs</code>, owner-only).
          </div>
        )}

        {orgId && (
          <form onSubmit={handleSave} className="space-y-6">
            {loading && <p className="text-sm text-gray-400">loading current pinning...</p>}

            {state && !state.enterpriseEligible && (
              <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
                This org&apos;s current Project tier is <code>{state.tier}</code>. Region pinning
                requires at least one <code>enterprise</code>-tier Project in this org (see the
                Project tier module) before a region may be set.
              </div>
            )}

            {state && (
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-300">
                  Current pin
                </label>
                <p className="text-sm text-gray-400">
                  {state.region ? (
                    <code>{state.region}</code>
                  ) : (
                    <span className="text-gray-500">unpinned -- scheduled cluster-wide</span>
                  )}
                </p>
              </div>
            )}

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">
                Pin to region
              </label>
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                disabled={!state?.enterpriseEligible || (state?.availableRegions.length ?? 0) === 0}
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white disabled:opacity-50"
              >
                {(state?.availableRegions ?? []).length === 0 && (
                  <option value="">no regions detected on this cluster&apos;s nodes</option>
                )}
                {state?.availableRegions.map((region) => (
                  <option key={region} value={region}>
                    {region}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Live-detected from this cluster&apos;s real{" "}
                <code>topology.kubernetes.io/region</code> node labels -- never a fabricated
                static list.
              </p>
            </div>

            {error && (
              <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                {error}
              </p>
            )}
            {saved && !error && (
              <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
                Region pin saved.
              </p>
            )}

            <button
              type="submit"
              disabled={saving || !state?.enterpriseEligible || !selectedRegion}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save region pin"}
            </button>
          </form>
        )}
      </main>
    </>
  );
}
