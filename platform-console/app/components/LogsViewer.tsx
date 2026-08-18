"use client";

import { useCallback, useEffect, useState } from "react";

interface PodOption {
  name: string;
  phase: string;
  containers: string[];
  ready: boolean;
}

/**
 * Picks a real namespace + pod (dropdowns populated from a live
 * GET /api/logs?namespace=X -> lib/k8s.ts's listPods) and shows the last N
 * real log lines from GET /api/logs?namespace=X&pod=Y -> lib/k8s.ts's
 * getPodLogs. No streaming/websockets -- a manual refresh button re-fetches
 * the current tail, which is an honest primitive on top of a subresource
 * that is itself a point-in-time (or chunked) read, not a subscription.
 * Every pane shows exactly what the API server returned, including a real
 * 502 (RBAC denial, pod not found, container not found) -- never a
 * fabricated "no logs" fallback.
 */
export default function LogsViewer({ namespaces }: { namespaces: string[] }) {
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [pods, setPods] = useState<PodOption[]>([]);
  const [podsError, setPodsError] = useState<string | null>(null);
  const [podsLoading, setPodsLoading] = useState(false);

  const [pod, setPod] = useState("");
  const [container, setContainer] = useState("");
  const [tailLines, setTailLines] = useState(200);

  const [logs, setLogs] = useState<string | null>(null);
  const [logsError, setLogsError] = useState<string | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [lastFetchedAt, setLastFetchedAt] = useState<string | null>(null);

  const loadPods = useCallback(async (ns: string) => {
    setPodsLoading(true);
    setPodsError(null);
    setPods([]);
    setPod("");
    setContainer("");
    try {
      const res = await fetch(`/api/logs?namespace=${encodeURIComponent(ns)}`);
      const body = await res.json();
      if (!res.ok) {
        setPodsError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      const podList: PodOption[] = body.pods ?? [];
      setPods(podList);
      if (podList.length > 0) {
        setPod(podList[0].name);
        setContainer(podList[0].containers[0] ?? "");
      }
    } catch (err) {
      setPodsError(err instanceof Error ? err.message : String(err));
    } finally {
      setPodsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (namespace) loadPods(namespace);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namespace]);

  async function fetchLogs() {
    if (!namespace || !pod) return;
    setLogsLoading(true);
    setLogsError(null);
    try {
      const params = new URLSearchParams({
        namespace,
        pod,
        tailLines: String(tailLines),
      });
      if (container) params.set("container", container);
      const res = await fetch(`/api/logs?${params.toString()}`);
      const body = await res.json();
      if (!res.ok) {
        setLogsError(body.error ?? `HTTP ${res.status}`);
        setLogs(null);
        return;
      }
      setLogs(body.logs ?? "");
      setLastFetchedAt(new Date().toLocaleTimeString());
    } catch (err) {
      setLogsError(err instanceof Error ? err.message : String(err));
      setLogs(null);
    } finally {
      setLogsLoading(false);
    }
  }

  const selectedPod = pods.find((p) => p.name === pod);

  return (
    <div className="card p-6">
      <div className="mb-4 grid gap-4 sm:grid-cols-4">
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
          <span className="mb-1 block text-gray-400">Pod</span>
          <select
            value={pod}
            onChange={(e) => {
              const nextPod = e.target.value;
              setPod(nextPod);
              const match = pods.find((p) => p.name === nextPod);
              setContainer(match?.containers[0] ?? "");
            }}
            disabled={podsLoading || pods.length === 0}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {pods.length === 0 && <option value="">(no pods)</option>}
            {pods.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name} ({p.phase})
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Container</span>
          <select
            value={container}
            onChange={(e) => setContainer(e.target.value)}
            disabled={!selectedPod || selectedPod.containers.length <= 1}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {(selectedPod?.containers ?? []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Tail lines</span>
          <input
            type="number"
            min={1}
            max={5000}
            value={tailLines}
            onChange={(e) => setTailLines(Number(e.target.value) || 200)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
      </div>

      {podsError && (
        <p className="mb-4 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {podsError}
        </p>
      )}

      <div className="mb-4 flex items-center gap-3">
        <button
          type="button"
          onClick={fetchLogs}
          disabled={logsLoading || !pod}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {logsLoading ? "Loading..." : "Refresh logs"}
        </button>
        {lastFetchedAt && (
          <span className="text-xs text-gray-500">last fetched {lastFetchedAt}</span>
        )}
      </div>

      {logsError && (
        <p className="mb-4 break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {logsError}
        </p>
      )}

      <pre className="max-h-[32rem] overflow-auto rounded-md border border-border bg-bg p-4 text-xs leading-relaxed text-gray-200">
        {logs === null
          ? "No logs fetched yet -- pick a namespace and pod, then press Refresh logs."
          : logs.length === 0
            ? "(empty log output)"
            : logs}
      </pre>
    </div>
  );
}
