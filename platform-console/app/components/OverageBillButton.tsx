"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs to /api/billing/overage -> lib/overage-billing.ts's
 * billNamespaceOverage, which creates a real Stripe InvoiceItem (test-mode
 * honesty note identical to lib/stripe-billing.ts's own header) against
 * this namespace's real Stripe customer/subscription. No client-side
 * simulation of "billed" -- the success message only appears after a real
 * 200 naming whatever the route actually did (`billed: true` with the
 * real Stripe InvoiceItem id, or `billed: false` with the real reason --
 * already billed this period, or no overage this period).
 */
export default function OverageBillButton({ namespace }: { namespace: string }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onBill() {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/billing/overage", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ namespace }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(
        body.billed
          ? `Billed: ${body.reason}`
          : `Not billed: ${body.reason}`,
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={onBill}
        disabled={submitting}
        className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Billing..." : "Bill this overage"}
      </button>
      {error && (
        <p className="max-w-xs break-all rounded-md border border-red-900 bg-red-950/40 px-2 py-1 text-[11px] text-red-300">
          {error}
        </p>
      )}
      {success && (
        <p className="max-w-xs break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-2 py-1 text-[11px] text-emerald-300">
          {success}
        </p>
      )}
    </div>
  );
}
