"use client";

import { useState } from "react";
import type { LoadTestResult } from "@/lib/load-test";

interface Target {
  id: string;
  label: string;
}

/**
 * Real Load Testing / performance benchmarking self-service. POSTs to
 * /api/load-test -> lib/load-test.ts's runLoadTestAgainstTarget, which fires
 * real concurrent HTTP requests against one allowlisted internal service and
 * returns real measured p50/p95/p99 latency and real success/error counts --
 * no client-side simulation of "test ran," the button stays disabled and
 * shows "Running..." for the test's real full duration (this is a real
 * blocking benchmark, not a fire-and-forget job).
 */
export default function LoadTestPanel({ targets }: { targets: Target[] }) {
  const [targetId, setTargetId] = useState(targets[0]?.id ?? "");
  const [concurrency, setConcurrency] = useState(20);
  const [durationSec, setDurationSec] = useState(10);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LoadTestResult | null>(null);

  async function runTest() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/load-test", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ targetId, concurrency, durationSec }),
      });
      const payload = await res.json();
      if (!res.ok) {
        setError(payload.error ?? `HTTP ${res.status}`);
        return;
      }
      setResult(payload as LoadTestResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Configure benchmark</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Target</span>
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              disabled={busy}
              className="w-full rounded-md border border-border bg-bg px-3 py-1.5 text-sm text-white"
            >
              {targets.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Concurrency (1-300)</span>
            <input
              type="number"
              min={1}
              max={300}
              value={concurrency}
              disabled={busy}
              onChange={(e) => setConcurrency(Number(e.target.value) || 1)}
              className="w-full rounded-md border border-border bg-bg px-3 py-1.5 text-sm text-white"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Duration (sec, 1-180)</span>
            <input
              type="number"
              min={1}
              max={180}
              value={durationSec}
              disabled={busy}
              onChange={(e) => setDurationSec(Number(e.target.value) || 1)}
              className="w-full rounded-md border border-border bg-bg px-3 py-1.5 text-sm text-white"
            />
          </label>
        </div>
        <p className="mt-4 text-xs text-gray-500">
          Fires real concurrent HTTP requests (Node <code>fetch</code>, a{" "}
          <code>Promise.all</code>-based worker pool) against the selected service for the full
          real duration below -- this generates real load against a real internal service and,
          at high enough concurrency/duration, can trigger that service&apos;s real{" "}
          <code>HorizontalPodAutoscaler</code>.
        </p>
        <button
          type="button"
          disabled={busy || !targetId}
          onClick={runTest}
          className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? `Running for ${durationSec}s...` : "Run load test"}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="card p-6">
          <h2 className="mb-4 text-base font-medium text-white">Results</h2>
          <p className="mb-4 text-xs text-gray-500">
            <code>{result.targetUrl}</code> -- concurrency {result.concurrency}, requested{" "}
            {result.durationSec}s (real wall time {(result.wallMs / 1000).toFixed(2)}s),{" "}
            {result.startedAt} &rarr; {result.finishedAt}
          </p>
          <div className="mb-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <Stat label="total requests" value={result.totalRequests.toLocaleString()} />
            <Stat label="req/sec" value={result.requestsPerSec.toFixed(1)} />
            <Stat label="success" value={result.successCount.toLocaleString()} />
            <Stat
              label="errors"
              value={`${result.errorCount.toLocaleString()} (${(result.errorRate * 100).toFixed(2)}%)`}
              warn={result.errorCount > 0}
            />
          </div>
          <div className="mb-2 grid grid-cols-3 gap-4 text-sm sm:grid-cols-6">
            <Stat label="min" value={`${result.latencyMs.min.toFixed(1)}ms`} />
            <Stat label="mean" value={`${result.latencyMs.mean.toFixed(1)}ms`} />
            <Stat label="p50" value={`${result.latencyMs.p50.toFixed(1)}ms`} />
            <Stat label="p95" value={`${result.latencyMs.p95.toFixed(1)}ms`} />
            <Stat label="p99" value={`${result.latencyMs.p99.toFixed(1)}ms`} />
            <Stat label="max" value={`${result.latencyMs.max.toFixed(1)}ms`} />
          </div>
          {result.sampleErrors.length > 0 && (
            <div className="mt-4 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-xs text-amber-300">
              <p className="mb-1 font-medium">sample errors observed</p>
              <ul className="list-inside list-disc space-y-0.5">
                {result.sampleErrors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="rounded-md border border-border px-3 py-2">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-lg font-semibold ${warn ? "text-amber-300" : "text-white"}`}>{value}</p>
    </div>
  );
}
