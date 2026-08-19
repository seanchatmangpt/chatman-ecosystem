"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

type ProjectTier = "starter" | "pro" | "enterprise";

interface CapacityReservation {
  orgId: string;
  namespace: string;
  tier: ProjectTier;
  committedCpuCores: number;
  committedMemoryGi: number;
  termMonths: number;
  discountPct: number;
  startDate: string;
  endDate: string;
  createdBy: string;
}

interface ReservationResponse {
  reservation: CapacityReservation | null;
  tier: ProjectTier;
  discountTable: Record<string, number>;
}

const TERM_OPTIONS = [6, 12, 24, 36];

// Real Committed-Use Capacity Reservations settings page (Reserved
// Capacity Tier -- AWS Reserved Instances / GCP Committed Use Discounts
// equivalent): the forward-commitment line item Fortune 5 procurement
// budgets against -- pre-pay for guaranteed compute headroom above the
// org's tier default in exchange for a discount on the overage rate.
// Same query-param-scoped `?orgId=` interim as app/org/sla/page.tsx and
// app/org/branding/page.tsx -- this app has no session-wide "current
// org" concept yet (see those pages' own comments for why).
export default function CapacityReservationsPage() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [data, setData] = useState<ReservationResponse | null>(null);
  const [committedCpuCores, setCommittedCpuCores] = useState("4");
  const [committedMemoryGi, setCommittedMemoryGi] = useState("8");
  const [termMonths, setTermMonths] = useState(12);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  function loadReservation() {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/capacity-reservations`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        const current: ReservationResponse = body;
        setData(current);
        if (current.reservation) {
          setCommittedCpuCores(String(current.reservation.committedCpuCores));
          setCommittedMemoryGi(String(current.reservation.committedMemoryGi));
          setTermMonths(current.reservation.termMonths);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadReservation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  async function handleCommit(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/capacity-reservations`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          committedCpuCores: Number(committedCpuCores),
          committedMemoryGi: Number(committedMemoryGi),
          termMonths,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setSaved(true);
      loadReservation();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleCancel() {
    if (!orgId) return;
    setCancelling(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/capacity-reservations`, {
        method: "DELETE",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      loadReservation();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCancelling(false);
    }
  }

  const previewDiscountPct = data?.discountTable?.[String(termMonths)] ?? 0;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Reserved Capacity</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Committed-Use Capacity Reservations -- pre-pay for guaranteed compute headroom above
          your tier&apos;s default ceiling in exchange for a discount on the overage rate. Raises
          your namespace&apos;s <code>ResourceQuota.spec.hard</code> immediately on commit; the
          discount applies automatically to usage-based invoice previews (
          <code>lib/invoice-preview.ts</code>) for as long as the commitment is active. Owner-only
          to change -- enforced server-side by{" "}
          <code>POST/DELETE /api/orgs/[id]/capacity-reservations</code>, not just this page.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to manage that
            org&apos;s capacity reservation (org ids are returned by <code>POST /api/orgs</code>{" "}
            and listed by <code>GET /api/orgs</code>, owner-only).
          </div>
        )}

        {orgId && (
          <>
            {loading && <p className="mb-4 text-sm text-gray-400">loading current reservation...</p>}

            {data?.reservation && (
              <div className="mb-8 rounded-md border border-gray-800 bg-gray-950 px-5 py-4">
                <p className="mb-3 text-sm font-medium text-gray-300">Active commitment</p>
                <dl className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Committed CPU</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {data.reservation.committedCpuCores} cores
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Committed memory</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {data.reservation.committedMemoryGi} GiB
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Discount</dt>
                    <dd className="mt-1 text-sm font-semibold text-emerald-400">
                      {data.reservation.discountPct}% off usage up to committed amount
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Term</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {data.reservation.termMonths} months
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Start</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {new Date(data.reservation.startDate).toLocaleDateString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-gray-500">Ends</dt>
                    <dd className="mt-1 text-sm font-semibold text-white">
                      {new Date(data.reservation.endDate).toLocaleDateString()}
                    </dd>
                  </div>
                </dl>
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={cancelling}
                  className="mt-4 rounded-md border border-red-900 bg-red-950/40 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-950/70 disabled:opacity-50"
                >
                  {cancelling ? "Cancelling..." : "Cancel reservation (revert to tier default)"}
                </button>
              </div>
            )}

            <form onSubmit={handleCommit} className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-300">
                    Committed CPU (cores)
                  </label>
                  <input
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={committedCpuCores}
                    onChange={(e) => setCommittedCpuCores(e.target.value)}
                    className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-300">
                    Committed memory (GiB)
                  </label>
                  <input
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={committedMemoryGi}
                    onChange={(e) => setCommittedMemoryGi(e.target.value)}
                    className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-300">Term</label>
                <select
                  value={termMonths}
                  onChange={(e) => setTermMonths(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                >
                  {TERM_OPTIONS.map((months) => (
                    <option key={months} value={months}>
                      {months} months
                      {data?.discountTable?.[String(months)] !== undefined
                        ? ` -- ${data.discountTable[String(months)]}% discount`
                        : ""}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-gray-500">
                  Discount is recomputed server-side from a fixed (tier, term) lookup table --
                  never entered directly. At your current{" "}
                  <span className="font-medium text-gray-300">{data?.tier ?? "..."}</span> tier,
                  this term commits at{" "}
                  <span className="font-medium text-emerald-400">{previewDiscountPct}%</span> off.
                </p>
              </div>

              {error && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {error}
                </p>
              )}
              {saved && !error && (
                <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
                  Reservation committed -- ResourceQuota raised immediately.
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {saving ? "Committing..." : "Commit reservation"}
              </button>
            </form>
          </>
        )}
      </main>
    </>
  );
}
