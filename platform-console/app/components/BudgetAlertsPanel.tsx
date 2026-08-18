"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { BudgetMetric, BudgetThreshold, BudgetUsage } from "@/lib/budget-alerts";

// Re-declared here (rather than a runtime import from @/lib/budget-alerts)
// deliberately -- lib/budget-alerts.ts pulls in lib/k8s.ts (fs/https) and
// lib/invoice-preview.ts, which must never end up in the client bundle.
// Only `import type` (erased at compile time) is safe to pull from those
// modules here, same pattern components/WebhooksPanel.tsx already uses.
const METRICS: BudgetMetric[] = ["cpu-core-hours", "cost-usd"];

function formatValue(metric: BudgetMetric, value: number | null): string {
  if (value === null) return "—";
  return metric === "cost-usd" ? `$${value.toFixed(4)}` : value.toFixed(6);
}

/**
 * Reads/writes the real platform-budget-thresholds ConfigMap via
 * /api/budget-alerts -> lib/budget-alerts.ts. No client-side simulation of
 * "threshold set"/"threshold deleted" or of the real usage figures -- a
 * row only changes after a real 200/201 from the API route
 * (router.refresh() re-reads the live ConfigMap + live Prometheus data
 * server-side), same "no optimistic UI" convention every other mutating
 * panel in this console follows (WebhooksPanel, OrgRolesPanel).
 */
export default function BudgetAlertsPanel({
  namespaces,
  thresholds,
  usages,
  windowLabel,
}: {
  namespaces: string[];
  thresholds: BudgetThreshold[];
  usages: BudgetUsage[];
  windowLabel: string;
}) {
  const router = useRouter();
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [metric, setMetric] = useState<BudgetMetric>(METRICS[0]);
  const [threshold, setThreshold] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingNamespace, setDeletingNamespace] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const usageByKey = new Map(usages.map((u) => [`${u.namespace}:${u.metric}`, u]));

  async function onSet(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/budget-alerts", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ namespace, metric, threshold: Number(threshold) }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setThreshold("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function onDelete(ns: string) {
    if (!confirm(`Remove the budget threshold for "${ns}"? This cannot be undone.`)) return;
    setDeletingNamespace(ns);
    setError(null);
    try {
      const res = await fetch(`/api/budget-alerts?namespace=${encodeURIComponent(ns)}`, {
        method: "DELETE",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeletingNamespace(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">
          Configured thresholds ({windowLabel} trailing window, same window <code>/billing</code> uses)
        </h2>
        {thresholds.length === 0 && (
          <p className="text-sm text-gray-500">No budget thresholds configured yet. Add one below.</p>
        )}
        {thresholds.length > 0 && (
          <div className="divide-y divide-border">
            {thresholds.map((t) => {
              const usage = usageByKey.get(`${t.namespace}:${t.metric}`);
              const over = usage?.overThreshold ?? false;
              return (
                <div key={`${t.namespace}:${t.metric}`} className="flex items-center justify-between gap-4 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">
                      <code>{t.namespace}</code> — <code>{t.metric}</code>
                    </p>
                    <p className="text-xs text-gray-500">
                      threshold: {formatValue(t.metric, t.threshold)} · current:{" "}
                      <span className={over ? "text-red-400" : "text-gray-400"}>
                        {usage ? formatValue(t.metric, usage.currentValue) : "—"}
                      </span>{" "}
                      {over && (
                        <span className="font-medium text-red-400">
                          OVER {usage?.alreadyAlerted ? "(alerted)" : "(alert pending next poll)"}
                        </span>
                      )}
                      {usage?.error && <span className="text-amber-400"> · {usage.error}</span>}
                    </p>
                    <p className="text-xs text-gray-600">
                      set {new Date(t.setAt).toLocaleString()} by {t.setBy}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onDelete(t.namespace)}
                    disabled={deletingNamespace === t.namespace}
                    className="shrink-0 rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                  >
                    {deletingNamespace === t.namespace ? "Removing..." : "Remove"}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <form onSubmit={onSet} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Set threshold</h2>
        <p className="text-xs text-gray-500">
          One threshold per namespace. Setting a new threshold for a namespace that already has
          one replaces it and resets its alert state. A real{" "}
          <code>budget.threshold_crossed</code> webhook (HMAC-SHA256 signed, same as{" "}
          <code>project.created</code>/<code>backup.completed</code>/<code>alert.firing</code>)
          fires the moment real measured usage next crosses this number -- see{" "}
          <code>/webhooks</code> to subscribe.
        </p>
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Namespace</span>
            <select
              value={namespace}
              onChange={(e) => setNamespace(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {namespaces.map((ns) => (
                <option key={ns} value={ns}>
                  {ns}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Metric</span>
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value as BudgetMetric)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {METRICS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">
              Threshold ({metric === "cost-usd" ? "USD" : "CPU-core-hours"})
            </span>
            <input
              required
              type="number"
              step="any"
              min="0"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder={metric === "cost-usd" ? "0.05" : "0.01"}
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={saving || !namespace}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {saving ? "Saving..." : "Set threshold"}
        </button>
      </form>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
