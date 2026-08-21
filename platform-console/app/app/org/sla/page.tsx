"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

type SlaTier = "standard" | "priority" | "enterprise-247";

interface OrgSlaResponse {
  slaTier: SlaTier;
  slaResponseTimeHours: number;
  slaUptimeTargetPct: number;
  currentlyMeetingSla: boolean;
  uptimeDataSource: string;
}

const SLA_TIERS: { value: SlaTier; label: string }[] = [
  { value: "standard", label: "Standard" },
  { value: "priority", label: "Priority" },
  { value: "enterprise-247", label: "Enterprise 24/7" },
];

// Real per-org contractual SLA / support-priority tier settings page:
// the line item enterprise procurement will not sign without a
// documented uptime target and support response-time commitment.
// Same query-param-scoped `?orgId=` interim as app/org/branding/page.tsx
// and app/org/region/page.tsx -- this app has no session-wide "current
// org" concept yet (see those pages' own comments for why).
function OrgSlaPageInner() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [sla, setSla] = useState<OrgSlaResponse | null>(null);
  const [selectedTier, setSelectedTier] = useState<SlaTier>("standard");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/sla`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        const current: OrgSlaResponse = body;
        setSla(current);
        setSelectedTier(current.slaTier);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [orgId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/sla`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ slaTier: selectedTier }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      const refreshed = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/sla`);
      const refreshedBody = await refreshed.json();
      if (refreshed.ok) {
        setSla(refreshedBody);
        setSelectedTier(refreshedBody.slaTier);
      }
      setSaved(true);
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
        <h1 className="mb-2 text-2xl font-semibold text-white">Support SLA</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real per-org contractual SLA / support-priority tier -- a line item Sales prices
          separately from compute tier. Stored on this org&apos;s own entry in the{" "}
          <code>platform-console-orgs</code> registry ConfigMap. Owner-only to change --
          enforced server-side by <code>PUT /api/orgs/[id]/sla</code>, not just this page.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to manage that
            org&apos;s SLA tier (org ids are returned by <code>POST /api/orgs</code> and listed
            by <code>GET /api/orgs</code>, owner-only).
          </div>
        )}

        {orgId && (
          <>
            {loading && <p className="mb-4 text-sm text-gray-400">loading current SLA...</p>}

            {sla && (
              <div className="mb-8 rounded-md border border-gray-800 bg-gray-950 px-5 py-4">
                <p className="mb-3 text-sm font-medium text-gray-300">Current commitment</p>
                <dl className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Tier</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">{sla.slaTier}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">
                      Uptime target
                    </dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {sla.slaUptimeTargetPct}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">
                      Response time
                    </dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {sla.slaResponseTimeHours}hr
                    </dd>
                  </div>
                </dl>
                <div className="mt-4 flex items-center gap-2">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      sla.currentlyMeetingSla ? "bg-emerald-500" : "bg-red-500"
                    }`}
                  />
                  <span className="text-sm text-gray-300">
                    {sla.currentlyMeetingSla ? "Currently meeting SLA" : "Currently in breach"}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({sla.uptimeDataSource === "no-incident-tracking"
                      ? "no incident/downtime tracking wired up yet -- shown as compliant by default"
                      : sla.uptimeDataSource})
                  </span>
                </div>
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-6">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-300">SLA tier</label>
                <select
                  value={selectedTier}
                  onChange={(e) => setSelectedTier(e.target.value as SlaTier)}
                  className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                >
                  {SLA_TIERS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Response time and uptime target are recomputed server-side from a fixed
                  lookup table -- never entered directly.
                </p>
              </div>

              {error && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {error}
                </p>
              )}
              {saved && !error && (
                <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
                  SLA tier saved.
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save SLA tier"}
              </button>
            </form>
          </>
        )}
      </main>
    </>
  );
}

export default function OrgSlaPage() {
  return (
    <Suspense fallback={null}>
      <OrgSlaPageInner />
    </Suspense>
  );
}
