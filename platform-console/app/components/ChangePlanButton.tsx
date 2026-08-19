"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs to /api/billing/stripe/change-plan -> lib/stripe-billing.ts's
 * changeSubscriptionPlan, which swaps this namespace's EXISTING Stripe
 * subscription to the new price with real Stripe-computed proration
 * (`stripe.subscriptions.update`) instead of re-running Checkout (which
 * would create a second, independently-billed subscription). Shown only
 * for a namespace that already has a subscription on file -- see
 * app/billing/page.tsx, which renders this in place of a "start
 * subscription" link precisely because a live subscription already exists
 * to swap.
 */
export default function ChangePlanButton({ namespace }: { namespace: string }) {
  const router = useRouter();
  const [newPriceId, setNewPriceId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onChangePlan() {
    if (!newPriceId.startsWith("price_")) {
      setError("Enter a real Stripe Price id (price_...)");
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/billing/stripe/change-plan", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ tenantNamespace: namespace, newPriceId }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      if (body.mode === "swapped") {
        setSuccess(
          `Swapped ${body.oldPriceId ?? "none"} -> ${body.newPriceId} with proration (status: ${body.subscription.status})`,
        );
        router.refresh();
      } else {
        setSuccess("No existing subscription -- redirecting to Stripe Checkout to start one");
        window.location.href = body.checkoutUrl;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1">
        <input
          type="text"
          value={newPriceId}
          onChange={(e) => setNewPriceId(e.target.value)}
          placeholder="price_..."
          className="w-32 rounded-md border border-border bg-background px-2 py-1 text-[11px] text-foreground"
        />
        <button
          type="button"
          onClick={onChangePlan}
          disabled={submitting}
          className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Changing..." : "Change plan"}
        </button>
      </div>
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
