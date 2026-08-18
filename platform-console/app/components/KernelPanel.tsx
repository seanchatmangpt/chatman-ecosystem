"use client";

import { useEffect, useState } from "react";

interface KernelApiResponse {
  health: { ok: true; data: { status: string; version: string; contract_digest: string } } | { ok: false; error: string };
  providers: { ok: true; data: { providers: string[] } } | { ok: false; error: string };
  evidence:
    | { ok: true; data: { verified: boolean; records: Array<{ sequence: number; receipt_digest: string }> } }
    | { ok: false; error: string };
  probe:
    | null
    | {
        ok: true;
        data: {
          materialize: {
            episode: { episode_id: string; provider: string; environment_id: string; standing: string };
            receipt: { receipt_id: string; operation: string; standing: string; occurred_at: string };
          };
          verify: { verification_id: string; passed: boolean; episode_id: string; state_digest: string };
        };
      }
    | { ok: false; error: string };
}

function Dot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-red-500"}`}
      aria-hidden
    />
  );
}

/**
 * Live episode/receipt panel over the real gymact FastAPI kernel (/api/gymact-kernel,
 * see lib/gymact-kernel.ts) -- distinct from the static facts.json StatusPanel above it
 * on the same page. Fetches client-side so the reader can trigger a real materialize+
 * verify probe on demand without a full page reload; every field shown is either a
 * kernel-returned fact or an honest "unreachable"/error string, same fail-closed
 * discipline as the rest of this console.
 */
export default function KernelPanel() {
  const [data, setData] = useState<KernelApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [probing, setProbing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(probe: boolean) {
    probe ? setProbing(true) : setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/gymact-kernel${probe ? "?probe=1" : ""}`, {
        cache: "no-store",
      });
      const body = (await res.json()) as KernelApiResponse;
      setData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      probe ? setProbing(false) : setLoading(false);
    }
  }

  useEffect(() => {
    load(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const health = data?.health;
  const providers = data?.providers;
  const evidence = data?.evidence;
  const probe = data?.probe;

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-medium text-white">Kernel (live episode/receipt state)</h2>
          {health && (
            <span
              className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${
                health.ok
                  ? "border-emerald-900 bg-emerald-950/40 text-emerald-300"
                  : "border-red-900 bg-red-950/40 text-red-300"
              }`}
            >
              <Dot ok={health.ok} />
              {health.ok ? "reachable" : "unreachable"}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => load(false)}
            disabled={loading}
            className="rounded-md border border-border px-3 py-1 text-xs text-gray-300 hover:bg-white/5 disabled:opacity-50"
          >
            {loading ? "refreshing..." : "refresh"}
          </button>
          <button
            onClick={() => load(true)}
            disabled={probing}
            className="rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-300 hover:bg-emerald-950/70 disabled:opacity-50"
          >
            {probing ? "materializing + verifying..." : "run live episode probe"}
          </button>
        </div>
      </div>

      {error && <p className="mb-3 text-xs text-red-400">{error}</p>}

      {!data && !error && <p className="text-sm text-gray-400">loading...</p>}

      {data && (
        <div className="space-y-4 text-sm">
          <div>
            <h3 className="mb-1 text-xs uppercase tracking-wide text-gray-500">Health</h3>
            {health?.ok ? (
              <dl className="grid grid-cols-3 gap-2">
                <dt className="text-gray-400">status</dt>
                <dd className="col-span-2 text-gray-100">{health.data.status}</dd>
                <dt className="text-gray-400">version</dt>
                <dd className="col-span-2 text-gray-100">{health.data.version}</dd>
                <dt className="text-gray-400">contract_digest</dt>
                <dd className="col-span-2 break-all font-mono text-xs text-gray-100">
                  {health.data.contract_digest}
                </dd>
              </dl>
            ) : (
              <p className="break-all text-xs text-red-400">{health?.error}</p>
            )}
          </div>

          <div>
            <h3 className="mb-1 text-xs uppercase tracking-wide text-gray-500">
              Registered providers
            </h3>
            {providers?.ok ? (
              <p className="text-gray-100">{providers.data.providers.join(", ") || "(none)"}</p>
            ) : (
              <p className="break-all text-xs text-red-400">{providers?.error}</p>
            )}
          </div>

          <div>
            <h3 className="mb-1 text-xs uppercase tracking-wide text-gray-500">
              Evidence chain
            </h3>
            {evidence?.ok ? (
              <p className="text-gray-100">
                verified: <span className={evidence.data.verified ? "text-emerald-400" : "text-red-400"}>
                  {String(evidence.data.verified)}
                </span>
                {" -- "}
                {evidence.data.records.length} receipt(s)
              </p>
            ) : (
              <p className="break-all text-xs text-red-400">{evidence?.error}</p>
            )}
          </div>

          <div>
            <h3 className="mb-1 text-xs uppercase tracking-wide text-gray-500">
              Live episode probe (materialize + verify, memory provider)
            </h3>
            {probe === null && (
              <p className="text-xs text-gray-500">
                Not run yet -- click &quot;run live episode probe&quot; to materialize a real
                episode and verify it.
              </p>
            )}
            {probe && probe.ok && (
              <dl className="grid grid-cols-3 gap-2">
                <dt className="text-gray-400">episode_id</dt>
                <dd className="col-span-2 break-all font-mono text-xs text-gray-100">
                  {probe.data.materialize.episode.episode_id}
                </dd>
                <dt className="text-gray-400">episode standing</dt>
                <dd className="col-span-2 text-gray-100">{probe.data.materialize.episode.standing}</dd>
                <dt className="text-gray-400">receipt_id</dt>
                <dd className="col-span-2 break-all font-mono text-xs text-gray-100">
                  {probe.data.materialize.receipt.receipt_id}
                </dd>
                <dt className="text-gray-400">receipt occurred_at</dt>
                <dd className="col-span-2 text-gray-100">{probe.data.materialize.receipt.occurred_at}</dd>
                <dt className="text-gray-400">verification passed</dt>
                <dd className="col-span-2">
                  <span className={probe.data.verify.passed ? "text-emerald-400" : "text-red-400"}>
                    {String(probe.data.verify.passed)}
                  </span>
                </dd>
                <dt className="text-gray-400">state_digest</dt>
                <dd className="col-span-2 break-all font-mono text-xs text-gray-100">
                  {probe.data.verify.state_digest}
                </dd>
              </dl>
            )}
            {probe && !probe.ok && (
              <p className="break-all text-xs text-red-400">{probe.error}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
