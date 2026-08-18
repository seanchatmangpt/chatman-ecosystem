"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

interface BatchJobDetail {
  name: string;
  namespace: string;
  commandId: string | null;
  parallelism: number;
  completions: number;
  active: number;
  succeeded: number;
  failed: number;
  status: "Pending" | "Running" | "Complete" | "Failed";
  startTime: string | null;
  completionTime: string | null;
  completedIndexes: string | null;
}

interface BatchJobPod {
  name: string;
  index: number | null;
  phase: string;
  startTime: string | null;
  containerStartedAt: string | null;
  containerFinishedAt: string | null;
  ready: boolean;
}

interface BatchResultsSummary {
  results: Array<{ index: number; value: string }>;
  expectedCount: number;
  missingIndices: number[];
  duplicateIndices: number[];
  complete: boolean;
}

const POLL_MS = 2000;

/**
 * Watches ONE real batch Job live -- polls GET /api/batch-jobs?namespace&name
 * (lib/batch-jobs.ts's getBatchJob + listBatchJobPods + collectBatchResults)
 * every 2s while the Job hasn't reached a terminal state, so the page shows
 * whatever the k8s API actually reports at each tick: real per-index Pod
 * phase/startTime (the genuine concurrency evidence -- overlapping
 * `startTime`/`containerFinishedAt` windows across indices), and the real
 * aggregated results collected from the shared ConfigMap so far. No
 * client-side simulation of progress -- every number here comes from a real
 * server response.
 */
export default function BatchJobMonitor({ namespace, name }: { namespace: string; name: string }) {
  const router = useRouter();
  const [job, setJob] = useState<BatchJobDetail | null>(null);
  const [pods, setPods] = useState<BatchJobPod[]>([]);
  const [results, setResults] = useState<BatchResultsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const poll = useCallback(async () => {
    try {
      const res = await fetch(
        `/api/batch-jobs?namespace=${encodeURIComponent(namespace)}&name=${encodeURIComponent(name)}`,
        { cache: "no-store" },
      );
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setError(null);
      setJob(body.job);
      setPods(body.pods);
      setResults(body.results);

      const terminal = body.job.status === "Complete" || body.job.status === "Failed";
      if (!terminal) {
        timerRef.current = setTimeout(poll, POLL_MS);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      timerRef.current = setTimeout(poll, POLL_MS);
    }
  }, [namespace, name]);

  useEffect(() => {
    poll();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [poll]);

  async function onDelete() {
    if (!confirm(`Delete Job/${name} in namespace ${namespace}? This removes the Job and its collected results.`)) {
      return;
    }
    setDeleting(true);
    try {
      const res = await fetch(
        `/api/batch-jobs?namespace=${encodeURIComponent(namespace)}&name=${encodeURIComponent(name)}`,
        { method: "DELETE" },
      );
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      if (timerRef.current) clearTimeout(timerRef.current);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeleting(false);
    }
  }

  if (error && !job) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {error}
      </p>
    );
  }
  if (!job) {
    return <p className="text-sm text-gray-500">Loading real job status...</p>;
  }

  const statusColor =
    job.status === "Complete"
      ? "bg-emerald-950/60 text-emerald-300"
      : job.status === "Failed"
        ? "bg-red-950/60 text-red-300"
        : "bg-amber-950/60 text-amber-300";

  return (
    <div className="space-y-4 border-t border-border pt-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-white">
            {job.name}{" "}
            <span className={`ml-1 rounded px-1.5 py-0.5 text-[10px] ${statusColor}`}>{job.status}</span>
          </p>
          <p className="text-xs text-gray-500">
            parallelism={job.parallelism} · completions={job.completions} · active={job.active} ·
            succeeded={job.succeeded} · failed={job.failed} · command=<code>{job.commandId ?? "?"}</code>
          </p>
          <p className="text-xs text-gray-500">
            completedIndexes (real, from the Job controller itself):{" "}
            <code>{job.completedIndexes ?? "(none yet)"}</code>
          </p>
        </div>
        <button
          type="button"
          onClick={onDelete}
          disabled={deleting}
          className="rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
        >
          {deleting ? "Deleting..." : "Delete job"}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-xs">
          <thead className="text-gray-500">
            <tr>
              <th className="py-1 pr-4">Index</th>
              <th className="py-1 pr-4">Pod</th>
              <th className="py-1 pr-4">Phase</th>
              <th className="py-1 pr-4">Pod startTime</th>
              <th className="py-1 pr-4">Container started</th>
              <th className="py-1 pr-4">Container finished</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border text-gray-300">
            {pods.map((p) => (
              <tr key={p.name}>
                <td className="py-1 pr-4">{p.index ?? "?"}</td>
                <td className="py-1 pr-4">{p.name}</td>
                <td className="py-1 pr-4">{p.phase}</td>
                <td className="py-1 pr-4">{p.startTime ?? "-"}</td>
                <td className="py-1 pr-4">{p.containerStartedAt ?? "-"}</td>
                <td className="py-1 pr-4">{p.containerFinishedAt ?? "-"}</td>
              </tr>
            ))}
            {pods.length === 0 && (
              <tr>
                <td colSpan={6} className="py-2 text-gray-500">
                  No pods reported yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {results && (
        <div>
          <p className="mb-2 text-xs text-gray-500">
            Aggregated results (from the real, shared{" "}
            <code>platform-batch-results</code> ConfigMap): {results.results.length}/
            {results.expectedCount} collected
            {results.missingIndices.length > 0 && (
              <span className="text-amber-300"> · missing: {results.missingIndices.join(", ")}</span>
            )}
            {results.duplicateIndices.length > 0 && (
              <span className="text-red-300"> · duplicates: {results.duplicateIndices.join(", ")}</span>
            )}
            {results.complete && <span className="text-emerald-300"> · complete, no gaps/duplicates</span>}
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[400px] text-left text-xs">
              <thead className="text-gray-500">
                <tr>
                  <th className="py-1 pr-4">Index</th>
                  <th className="py-1 pr-4">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-gray-300">
                {results.results.map((r) => (
                  <tr key={r.index}>
                    <td className="py-1 pr-4">{r.index}</td>
                    <td className="py-1 pr-4">
                      <code>{r.value}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
