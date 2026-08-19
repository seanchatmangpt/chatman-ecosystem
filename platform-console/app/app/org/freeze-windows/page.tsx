"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

interface FreezeWindow {
  id: string;
  orgId: string;
  startsAt: string;
  endsAt: string;
  reason: string;
  createdBy: string;
  createdAt: string;
  allowEmergencyOverride: boolean;
}

// Real deployment / change-freeze window CRUD page (lib/freeze-windows.ts,
// SOC2 CC8 / ITIL change management -- see that module's own header
// comment). Same query-param-scoped `?orgId=` interim as
// app/org/region/page.tsx and app/org/sla/page.tsx (this app has no
// session-wide "current org" concept yet). Owner-only in the UI to match
// the server-side gate POST/DELETE /api/freeze-windows enforces -- the UI
// gate is cosmetic, the API gate is the real one; a non-owner can still
// GET (view) but a failed POST/DELETE surfaces the real 403 error text.
export default function OrgFreezeWindowsPage() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [windows, setWindows] = useState<FreezeWindow[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [reason, setReason] = useState("");
  const [allowEmergencyOverride, setAllowEmergencyOverride] = useState(false);

  function load() {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/freeze-windows?orgId=${encodeURIComponent(orgId)}`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setWindows(body.windows as FreezeWindow[]);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, [orgId]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId || !startsAt || !endsAt || !reason.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/freeze-windows", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          orgId,
          startsAt: new Date(startsAt).toISOString(),
          endsAt: new Date(endsAt).toISOString(),
          reason: reason.trim(),
          allowEmergencyOverride,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setStartsAt("");
      setEndsAt("");
      setReason("");
      setAllowEmergencyOverride(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!orgId) return;
    setError(null);
    try {
      const res = await fetch(
        `/api/freeze-windows?orgId=${encodeURIComponent(orgId)}&id=${encodeURIComponent(id)}`,
        { method: "DELETE" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const now = Date.now();
  const active = windows.filter(
    (w) => Date.parse(w.startsAt) <= now && now <= Date.parse(w.endsAt),
  );
  const upcoming = windows.filter((w) => Date.parse(w.startsAt) > now);
  const past = windows.filter((w) => Date.parse(w.endsAt) < now);

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Deployment / change freeze windows</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Declare a period during which production changes -- castle security-testing verbs,
          project tier changes, quota patches -- are policy-blocked, not just a calendar
          reminder. Enforced server-side by <code>checkFreezeGuard</code>{" "}
          (<code>lib/freeze-windows.ts</code>) on every mutating action, with a real,
          audited maker-checker override for windows that allow one. This is the standard
          ITIL change-freeze control regulated buyers (banks, healthcare, retail during peak
          season) require, tied to SOC2 CC8 (Change Management). Owner-only.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to manage that
            org&apos;s freeze windows (org ids are returned by <code>POST /api/orgs</code> and
            listed by <code>GET /api/orgs</code>).
          </div>
        )}

        {orgId && (
          <>
            {active.length > 0 && (
              <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
                <strong>{active.length} freeze window{active.length > 1 ? "s" : ""} active right now.</strong>{" "}
                Mutating actions for this org are blocked unless a fresh <code>freeze.override</code>{" "}
                approval exists.
              </div>
            )}

            <form
              onSubmit={handleCreate}
              className="mb-10 space-y-4 rounded-md border border-gray-800 bg-gray-950/40 p-4"
            >
              <h2 className="text-sm font-medium text-white">Declare a new freeze window</h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-300">Starts</label>
                  <input
                    type="datetime-local"
                    value={startsAt}
                    onChange={(e) => setStartsAt(e.target.value)}
                    className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-300">Ends</label>
                  <input
                    type="datetime-local"
                    value={endsAt}
                    onChange={(e) => setEndsAt(e.target.value)}
                    className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-300">Reason</label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Black Friday change freeze, quarter-close lockdown"
                  className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                  required
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-300">
                <input
                  type="checkbox"
                  checked={allowEmergencyOverride}
                  onChange={(e) => setAllowEmergencyOverride(e.target.checked)}
                  className="rounded border-gray-700 bg-gray-900"
                />
                Allow emergency override (a second, distinct owner-role approver may authorize a
                change during this freeze). Leave unchecked for a hard, non-negotiable freeze.
              </label>

              {error && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Declare freeze window"}
              </button>
            </form>

            {loading && <p className="text-sm text-gray-400">loading freeze windows...</p>}

            {!loading && (
              <div className="space-y-8">
                <WindowSection title="Active" windows={active} onDelete={handleDelete} tone="red" />
                <WindowSection title="Upcoming" windows={upcoming} onDelete={handleDelete} tone="amber" />
                <WindowSection title="Past" windows={past} onDelete={handleDelete} tone="gray" />
              </div>
            )}
          </>
        )}
      </main>
    </>
  );
}

function WindowSection({
  title,
  windows,
  onDelete,
  tone,
}: {
  title: string;
  windows: FreezeWindow[];
  onDelete: (id: string) => void;
  tone: "red" | "amber" | "gray";
}) {
  const borderClass =
    tone === "red" ? "border-red-900" : tone === "amber" ? "border-amber-900" : "border-gray-800";
  return (
    <div>
      <h2 className="mb-2 text-sm font-medium text-white">
        {title} ({windows.length})
      </h2>
      {windows.length === 0 && <p className="text-sm text-gray-500">none</p>}
      <ul className="space-y-2">
        {windows.map((w) => (
          <li
            key={w.id}
            className={`flex items-start justify-between gap-4 rounded-md border ${borderClass} bg-gray-950/40 px-4 py-3`}
          >
            <div className="min-w-0">
              <p className="text-sm text-white">{w.reason}</p>
              <p className="mt-1 text-xs text-gray-400">
                {new Date(w.startsAt).toLocaleString()} &rarr; {new Date(w.endsAt).toLocaleString()}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                {w.allowEmergencyOverride ? "emergency override allowed" : "hard freeze -- no override"}
                {" -- declared by "}
                {w.createdBy}
              </p>
            </div>
            <button
              onClick={() => onDelete(w.id)}
              className="shrink-0 rounded-md border border-gray-700 px-3 py-1 text-xs text-gray-300 hover:bg-gray-800"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
