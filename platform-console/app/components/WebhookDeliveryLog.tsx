"use client";

import { useEffect, useState } from "react";
import type { WebhookDeliveryRow } from "@/lib/webhook-deliveries";

// `WebhookDeliveryRow` is imported as a type-only import (erased at
// compile time) -- same convention components/WebhooksPanel.tsx already
// uses for @/lib/webhooks, since lib/webhook-deliveries.ts pulls in `pg`
// which must never end up in the client bundle.

const STATUS_STYLES: Record<WebhookDeliveryRow["status"], string> = {
  delivered: "border-emerald-900 bg-emerald-950/40 text-emerald-300",
  pending_retry: "border-amber-900 bg-amber-950/40 text-amber-300",
  dead_letter: "border-red-900 bg-red-950/40 text-red-300",
};

/**
 * Real delivery history + replay panel for one webhook subscription --
 * reads /api/webhooks/[id]/deliveries (lib/webhook-deliveries.ts, the
 * real Postgres-backed delivery log), and lets an owner replay any
 * dead-lettered row via POST /api/webhooks/deliveries/[deliveryId]/replay.
 * No client-side simulation of delivery state: a row's status only
 * changes here after a real re-fetch of the live table, same
 * no-optimistic-UI convention WebhooksPanel.tsx already follows.
 */
export default function WebhookDeliveryLog({ subscriptionId }: { subscriptionId: string }) {
  const [deliveries, setDeliveries] = useState<WebhookDeliveryRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replayingId, setReplayingId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/webhooks/${encodeURIComponent(subscriptionId)}/deliveries`);
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setDeliveries(body.deliveries as WebhookDeliveryRow[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subscriptionId]);

  async function onReplay(deliveryId: string) {
    setReplayingId(deliveryId);
    setError(null);
    try {
      const res = await fetch(`/api/webhooks/deliveries/${encodeURIComponent(deliveryId)}/replay`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setReplayingId(null);
    }
  }

  return (
    <div className="mt-3 rounded-md border border-border bg-black/20 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-medium text-gray-400">Delivery history</p>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="text-xs text-gray-500 hover:text-gray-300 disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <p className="mb-2 break-all rounded-md border border-red-900 bg-red-950/40 px-2 py-1 text-xs text-red-300">
          {error}
        </p>
      )}

      {!loading && deliveries !== null && deliveries.length === 0 && (
        <p className="text-xs text-gray-600">No deliveries yet for this subscription.</p>
      )}

      {deliveries !== null && deliveries.length > 0 && (
        <div className="space-y-1.5">
          {deliveries.map((d) => (
            <div
              key={d.deliveryId}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border/60 px-2 py-1.5"
            >
              <div className="min-w-0 text-xs">
                <span
                  className={`mr-2 inline-block rounded border px-1.5 py-0.5 font-medium ${STATUS_STYLES[d.status]}`}
                >
                  {d.status}
                </span>
                <span className="text-gray-400">
                  attempt {d.attemptNumber}/{d.maxAttempts}
                  {d.httpStatus !== null ? ` · HTTP ${d.httpStatus}` : ""}
                  {d.error ? ` · ${d.error}` : ""}
                  {d.durationMs !== null ? ` · ${d.durationMs}ms` : ""}
                </span>
                <span className="ml-2 text-gray-600">{new Date(d.updatedAt).toLocaleString()}</span>
                {d.status === "pending_retry" && d.nextAttemptAt && (
                  <span className="ml-2 text-amber-400/80">
                    next retry {new Date(d.nextAttemptAt).toLocaleString()}
                  </span>
                )}
              </div>
              {d.status === "dead_letter" && (
                <button
                  type="button"
                  onClick={() => onReplay(d.deliveryId)}
                  disabled={replayingId === d.deliveryId}
                  className="shrink-0 rounded-md border border-accent/60 px-2 py-1 text-xs text-accent hover:bg-accent/10 disabled:opacity-50"
                >
                  {replayingId === d.deliveryId ? "Replaying..." : "Replay"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
