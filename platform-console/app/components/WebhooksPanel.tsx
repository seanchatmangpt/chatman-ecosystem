"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { WebhookEventType, WebhookSubscription } from "@/lib/webhooks";
import WebhookDeliveryLog from "@/components/WebhookDeliveryLog";

// `WEBHOOK_EVENT_TYPES` is re-declared here (rather than a runtime
// import from @/lib/webhooks) deliberately: lib/webhooks.ts pulls in
// node:crypto and lib/k8s.ts (fs/https), which must never end up in the
// client bundle. Only `import type` (erased at compile time, same
// pattern components/OrgRolesPanel.tsx already uses for @/lib/authz) is
// safe to pull from that module here.
const EVENT_TYPES: WebhookEventType[] = [
  "project.created",
  "backup.completed",
  "alert.firing",
  "budget.threshold_crossed",
];

/**
 * Reads/writes the real platform-console-webhooks ConfigMap via
 * /api/webhooks -> lib/webhooks.ts. No client-side simulation of
 * "created"/"deleted" -- a row only changes after a real 200/201 from
 * the API route (router.refresh() re-reads the live ConfigMap
 * server-side, the same "no optimistic UI" convention every other
 * mutating form in this console already follows).
 */
export default function WebhooksPanel({ subscriptions }: { subscriptions: WebhookSubscription[] }) {
  const router = useRouter();
  const [eventType, setEventType] = useState<WebhookEventType>(EVENT_TYPES[0]);
  const [url, setUrl] = useState("");
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [justCreated, setJustCreated] = useState<WebhookSubscription | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const res = await fetch("/api/webhooks", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ eventType, url }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setJustCreated(body.subscription as WebhookSubscription);
      setUrl("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Delete this webhook subscription? This cannot be undone.")) return;
    setDeletingId(id);
    setError(null);
    try {
      const res = await fetch(`/api/webhooks?id=${encodeURIComponent(id)}`, { method: "DELETE" });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      if (justCreated?.id === id) setJustCreated(null);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-6">
      {justCreated && (
        <div className="card space-y-2 border-emerald-900 bg-emerald-950/30 p-6">
          <p className="text-sm font-medium text-white">Subscription created</p>
          <p className="text-xs text-gray-400">
            Signing secret -- use it to verify <code>x-platform-webhook-signature-256</code> on
            every delivered payload:
          </p>
          <code className="block break-all rounded-md bg-black/40 px-3 py-2 text-xs text-emerald-300">
            {justCreated.secret}
          </code>
        </div>
      )}

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Subscriptions</h2>
        {subscriptions.length === 0 && (
          <p className="text-sm text-gray-500">No webhook subscriptions yet. Add one below.</p>
        )}
        {subscriptions.length > 0 && (
          <div className="divide-y divide-border">
            {subscriptions.map((s) => (
              <div key={s.id} className="py-3">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white">
                      <code>{s.eventType}</code>
                    </p>
                    <p className="truncate text-xs text-gray-500">{s.url}</p>
                    <p className="text-xs text-gray-600">
                      created {new Date(s.createdAt).toLocaleString()} by {s.createdBy}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setExpandedId(expandedId === s.id ? null : s.id)}
                      className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-300 hover:bg-white/5"
                    >
                      {expandedId === s.id ? "Hide deliveries" : "View deliveries"}
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(s.id)}
                      disabled={deletingId === s.id}
                      className="rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                    >
                      {deletingId === s.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </div>
                {expandedId === s.id && <WebhookDeliveryLog subscriptionId={s.id} />}
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onCreate} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Add subscription</h2>
        <p className="text-xs text-gray-500">
          A real HTTP POST fires to this URL when the chosen real platform event happens, signed
          with a real HMAC-SHA256 header (
          <code>x-platform-webhook-signature-256: sha256=&lt;hex&gt;</code>) computed over the
          exact request body -- the same convention GitHub/Stripe webhooks use.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Event type</span>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value as WebhookEventType)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Subscriber URL</span>
            <input
              required
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="http://receiver.namespace.svc.cluster.local:8080/webhook"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {creating ? "Saving..." : "Subscribe"}
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
