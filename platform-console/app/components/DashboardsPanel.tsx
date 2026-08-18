"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
// Type-only imports -- lib/dashboards.ts pulls in lib/k8s.ts (fs/https)
// and lib/audit-db.ts (the `pg` driver), which must never end up in the
// client bundle. Only `import type` (erased at compile time) is safe to
// pull from it here, same pattern components/BudgetAlertsPanel.tsx already
// establishes for lib/budget-alerts.ts.
import type { Widget, WidgetExecutionResult, WidgetType } from "@/lib/dashboards";

export interface WidgetWithResult extends Widget {
  result: WidgetExecutionResult;
}

const TYPE_LABEL: Record<WidgetType, string> = {
  promql: "PromQL",
  "audit-query": "Audit query",
};

const TYPE_HINT: Record<WidgetType, string> = {
  promql: 'one of the allowlisted queries, e.g. "up"',
  "audit-query": 'URL params: actor, path, window (e.g. "1h"), from, to -- e.g. "actor=admin&window=1h"',
};

function WidgetResultView({ result }: { result: WidgetExecutionResult }) {
  if (!result.ok) {
    return (
      <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
        {result.error}
      </p>
    );
  }
  if (result.type === "promql") {
    if (result.series.length === 0) {
      return <p className="text-xs text-gray-500">no series returned</p>;
    }
    return (
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-border text-gray-500">
            <th className="py-1 pr-2 font-normal">labels</th>
            <th className="py-1 font-normal">value</th>
          </tr>
        </thead>
        <tbody>
          {result.series.map((s, i) => (
            <tr key={i} className="border-b border-border/50 last:border-0">
              <td className="py-1 pr-2 text-gray-300">
                {Object.entries(s.metric)
                  .map(([k, v]) => `${k}=${v}`)
                  .join(", ") || "(no labels)"}
              </td>
              <td className="py-1 font-mono text-gray-100">{s.value[1]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  return (
    <div>
      <p className="mb-2 text-sm text-gray-200">
        <span className="font-medium text-white">{result.total}</span> matching entr
        {result.total === 1 ? "y" : "ies"}
      </p>
      {result.rows.length > 0 && (
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-border text-gray-500">
              <th className="py-1 pr-2 font-normal">ts</th>
              <th className="py-1 pr-2 font-normal">actor</th>
              <th className="py-1 pr-2 font-normal">method</th>
              <th className="py-1 font-normal">path</th>
              <th className="py-1 pl-2 font-normal">status</th>
            </tr>
          </thead>
          <tbody>
            {result.rows.slice(0, 10).map((r) => (
              <tr key={r.id} className="border-b border-border/50 last:border-0">
                <td className="py-1 pr-2 text-gray-400">{new Date(r.ts).toLocaleTimeString()}</td>
                <td className="py-1 pr-2 text-gray-300">{r.actor}</td>
                <td className="py-1 pr-2 text-gray-300">{r.method}</td>
                <td className="py-1 text-gray-300">{r.path}</td>
                <td className="py-1 pl-2 text-gray-400">{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

/**
 * Reads/writes the real platform-console-dashboards ConfigMap via
 * /api/dashboards -> lib/dashboards.ts. No client-side simulation of a
 * widget's result -- every result rendered here is exactly what the
 * server just returned from a fresh execution against the real
 * Prometheus proxy or the real durable audit log, same "no optimistic UI"
 * convention every other mutating panel in this console follows
 * (BudgetAlertsPanel, WebhooksPanel). "Refresh" re-fetches the whole page
 * server-side (router.refresh()), which re-runs every widget's real query
 * again -- there is no cache to invalidate because there is no cache.
 */
export default function DashboardsPanel({
  initialWidgets,
  creatableTypes,
}: {
  initialWidgets: WidgetWithResult[];
  creatableTypes: WidgetType[];
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [type, setType] = useState<WidgetType>(creatableTypes[0] ?? "promql");
  const [query, setQuery] = useState("");
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/dashboards", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ title, type, query }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? body.reason ?? `HTTP ${res.status}`);
        return;
      }
      setTitle("");
      setQuery("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Remove this widget? This cannot be undone.")) return;
    setDeletingId(id);
    setError(null);
    try {
      const res = await fetch(`/api/dashboards?id=${encodeURIComponent(id)}`, { method: "DELETE" });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeletingId(null);
    }
  }

  function onRefresh() {
    setRefreshing(true);
    router.refresh();
    setTimeout(() => setRefreshing(false), 500);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-medium text-white">
          Your widgets ({initialWidgets.length})
        </h2>
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-200 hover:border-gray-500 disabled:opacity-50"
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {initialWidgets.length === 0 && (
        <p className="text-sm text-gray-500">No widgets yet. Add one below.</p>
      )}

      {initialWidgets.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {initialWidgets.map((w) => (
            <div key={w.id} className="card space-y-3 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white">{w.title}</p>
                  <p className="text-xs text-gray-500">
                    {TYPE_LABEL[w.type]} · <code className="break-all">{w.query}</code>
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(w.id)}
                  disabled={deletingId === w.id}
                  className="shrink-0 rounded-md border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                >
                  {deletingId === w.id ? "..." : "Remove"}
                </button>
              </div>
              <WidgetResultView result={w.result} />
            </div>
          ))}
        </div>
      )}

      <form onSubmit={onCreate} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Add widget</h2>
        {creatableTypes.length === 0 && (
          <p className="text-xs text-amber-400">
            Your current role cannot create any widget type -- promql widgets require at least{" "}
            <code>member</code>, audit-query widgets require <code>owner</code>.
          </p>
        )}
        {creatableTypes.length > 0 && (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              <label className="block text-sm">
                <span className="mb-1 block text-gray-400">Title</span>
                <input
                  required
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  maxLength={120}
                  className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
                  placeholder="up (all targets)"
                />
              </label>
              <label className="block text-sm">
                <span className="mb-1 block text-gray-400">Type</span>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value as WidgetType)}
                  className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
                >
                  {creatableTypes.map((t) => (
                    <option key={t} value={t}>
                      {TYPE_LABEL[t]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm sm:col-span-1">
                <span className="mb-1 block text-gray-400">Query</span>
                <input
                  required
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
                  placeholder={type === "promql" ? "up" : "actor=admin&window=1h"}
                />
              </label>
            </div>
            <p className="text-xs text-gray-500">{TYPE_HINT[type]}</p>
            <button
              type="submit"
              disabled={saving || !title || !query}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? "Saving..." : "Add widget"}
            </button>
          </>
        )}
      </form>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
