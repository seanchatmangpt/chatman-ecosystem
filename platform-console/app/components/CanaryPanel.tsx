"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CanaryState } from "@/lib/canary";

/**
 * Reads/writes the real autofde-lab-status VirtualService via
 * /api/deployments/canary -> lib/canary.ts. Both GET and POST on that
 * route are owner-gated server-side (requireRole) -- this panel only ever
 * renders after the server-rendered page has already confirmed the viewer
 * is an owner, but the real enforcement boundary is the route, not this
 * component. No client-side simulation of "weight changed" -- the
 * displayed weight only changes after a real 200 (router.refresh()
 * re-reads the live VirtualService server-side), same "no optimistic UI"
 * convention OrgRolesPanel/FeatureFlagsPanel already follow.
 */
export default function CanaryPanel({ initialState }: { initialState: CanaryState }) {
  const router = useRouter();
  const [state, setState] = useState(initialState);
  const [sliderValue, setSliderValue] = useState(initialState.weights.canary);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function post(body: Record<string, unknown>, busyKey: string) {
    setBusy(busyKey);
    setError(null);
    try {
      const res = await fetch("/api/deployments/canary", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await res.json();
      if (!res.ok) {
        setError(payload.error ?? payload.reason ?? `HTTP ${res.status}`);
        return;
      }
      setState(payload as CanaryState);
      setSliderValue((payload as CanaryState).weights.canary);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  async function applyWeight() {
    const canaryWeight = sliderValue;
    const stableWeight = 100 - canaryWeight;
    await post({ action: "set-weight", stableWeight, canaryWeight }, "weight");
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Live traffic split</h2>
        <p className="mb-4 text-xs text-gray-500">
          Real <code>networking.istio.io/v1</code> <code>VirtualService</code>{" "}
          (<code>autofde-lab-status</code>, <code>autofde-lab</code> namespace) --{" "}
          <code>spec.http[0].route[].weight</code>, read live on every page load.
        </p>
        <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
          <div className="rounded-md border border-border px-4 py-3">
            <p className="text-xs text-gray-500">stable subset</p>
            <p className="text-2xl font-semibold text-white">{state.weights.stable}%</p>
            <p className="mt-1 text-xs text-gray-500">
              {state.stableDeployment.exists
                ? `${state.stableDeployment.replicasReady}/${state.stableDeployment.replicasDesired} ready`
                : "Deployment absent"}
            </p>
          </div>
          <div className="rounded-md border border-border px-4 py-3">
            <p className="text-xs text-gray-500">canary subset</p>
            <p className="text-2xl font-semibold text-white">{state.weights.canary}%</p>
            <p className="mt-1 text-xs text-gray-500">
              {state.canaryDeployment.exists
                ? `${state.canaryDeployment.replicasReady}/${state.canaryDeployment.replicasDesired} ready`
                : "Deployment absent"}
            </p>
          </div>
        </div>

        <label className="mb-2 block text-sm">
          <span className="mb-1 flex justify-between text-gray-400">
            <span>Canary weight</span>
            <span>{sliderValue}%</span>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={sliderValue}
            onChange={(e) => setSliderValue(Number(e.target.value))}
            className="w-full"
          />
        </label>
        <div className="mb-4 flex items-center gap-2">
          <input
            type="number"
            min={0}
            max={100}
            value={sliderValue}
            onChange={(e) =>
              setSliderValue(Math.max(0, Math.min(100, Number(e.target.value) || 0)))
            }
            className="w-24 rounded-md border border-border bg-bg px-3 py-1.5 text-sm text-white"
          />
          <span className="text-xs text-gray-500">% canary (stable = 100 - this)</span>
        </div>
        <button
          type="button"
          disabled={busy !== null}
          onClick={applyWeight}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy === "weight" ? "Applying..." : "Apply weight split"}
        </button>
      </div>

      <div className="card p-6">
        <h2 className="mb-2 text-base font-medium text-white">Promote / rollback</h2>
        <p className="mb-4 text-xs text-gray-500">
          Promote: shift to 100% canary, then delete the stable Deployment. Rollback: shift to
          100% stable, then delete the canary Deployment. Both are real, consequential, owner-only
          actions -- not simulated.
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            disabled={busy !== null}
            onClick={() => post({ action: "promote" }, "promote")}
            className="rounded-md border border-green-800 bg-green-950/40 px-4 py-2 text-sm font-medium text-green-300 disabled:opacity-50"
          >
            {busy === "promote" ? "Promoting..." : "Promote canary to 100%"}
          </button>
          <button
            type="button"
            disabled={busy !== null}
            onClick={() => post({ action: "rollback" }, "rollback")}
            className="rounded-md border border-red-800 bg-red-950/40 px-4 py-2 text-sm font-medium text-red-300 disabled:opacity-50"
          >
            {busy === "rollback" ? "Rolling back..." : "Rollback to 100% stable"}
          </button>
        </div>
      </div>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
